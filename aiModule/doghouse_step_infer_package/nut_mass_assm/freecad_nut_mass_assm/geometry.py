"""B-Rep geometry detection: cylindrical faces, planar faces and main-axis clustering.

All geometry is read from ``obj.Shape`` which already carries the object's
placement, so every point / axis returned here is in world coordinates.

This module intentionally uses only the native FreeCAD ``Part`` API (no OCC
subprocess) to keep the demo runnable out of the box on FreeCAD 1.1.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

import FreeCAD  # type: ignore

Vector = FreeCAD.Vector

# Tolerances (mm / dimensionless) for the demo.
PARALLEL_TOL = 1e-3        # 1 - |dot| threshold for "parallel" axes
COLLINEAR_TOL = 1e-2       # max distance between axis anchor points (mm)
ANGLE_TOL = 1e-2           # planar normal parallelism tolerance

# Canonical-shape recovery for STEP files that export analytic faces as
# freeform patches (this demo's sample has 1263 B-spline faces vs 105 planes).
ANALYTIC_SURFACES = ("Plane", "Cylinder", "Cone", "Sphere", "Toroid")
FLATNESS_TOL_DEG = 0.5     # max normal spread for a face to pass as planar
CIRCLE_FIT_TOL = 0.05      # mm; how far an edge may stray from its fitted circle
RIM_RADIUS_TOL = 0.1       # mm; radius mismatch allowed between the two rims
RIM_OFFSET_MIN = 0.05      # mm; minimum rim-to-rim distance along the axis
RIM_OFFSET_LATERAL = 0.05  # mm; rim centers must be stacked along one axis
RECOVERY_RADIUS_TOL = 0.25  # mm; band around a wanted radius worth fitting

# Some STEP writers emit micro-sized stub solids (e.g. sphere shells standing in
# for construction points) alongside the real body. A solid is treated as such an
# artefact only when it is both absolutely too small to be a manufacturable body
# and negligible next to the largest solid of the same file, so genuinely small
# parts sitting next to a big one survive.
ARTEFACT_MAX_SIZE_MM = 0.1
ARTEFACT_MAX_VOLUME_RATIO = 1e-6


def unit(v: "Vector") -> "Vector":
    length = v.Length
    if length < 1e-12:
        return Vector(0.0, 0.0, 0.0)
    return Vector(v.x / length, v.y / length, v.z / length)


def scaled(v: "Vector", factor: float) -> "Vector":
    """Return v * factor as a NEW vector.

    FreeCAD's Vector.multiply() scales in place and returns self, so using it on a
    vector that is kept elsewhere silently mutates that one too (e.g. flipping an
    axis while deriving its opposite). Always scale through this helper.
    """
    return Vector(v.x * factor, v.y * factor, v.z * factor)


def axis_anchor(point: "Vector", direction: "Vector") -> "Vector":
    """Foot of the perpendicular from the origin onto the line (point, direction).

    Gives a canonical point on the axis line, independent of where along the
    axis the surface stores its reference point, so two collinear axes share it.
    """
    d = unit(direction)
    return point - scaled(d, point.dot(d))


def project_scalar(point: "Vector", origin: "Vector", direction: "Vector") -> float:
    """Signed coordinate of ``point`` along the axis ``direction`` from ``origin``."""
    return (point - origin).dot(unit(direction))


def point_to_axis_distance(point: "Vector", origin: "Vector", direction: "Vector") -> float:
    d = unit(direction)
    rel = point - origin
    along = scaled(d, rel.dot(d))
    perp = rel - along
    return perp.Length


def solid_volume(solid) -> float:
    try:
        return abs(float(solid.Volume))
    except Exception:
        return 0.0


def _bbox_diagonal(shape) -> float:
    try:
        return float(shape.BoundBox.DiagonalLength)
    except Exception:
        return float("inf")


def is_artefact_solid(solid, reference_volume: float) -> bool:
    """True when ``solid`` is an export stub rather than a real body.

    ``reference_volume`` is the volume of the largest solid the same STEP file
    produced; a non-positive value disables the test so nothing is dropped when
    volumes cannot be measured.
    """
    if reference_volume <= 0.0:
        return False
    if _bbox_diagonal(solid) >= ARTEFACT_MAX_SIZE_MM:
        return False
    return solid_volume(solid) <= reference_volume * ARTEFACT_MAX_VOLUME_RATIO


def surface_type(face) -> str:
    try:
        return type(face.Surface).__name__
    except Exception:
        return ""


def plane_outward_normal(face) -> "Vector":
    """Outward normal of a planar face, honoring the face orientation."""
    try:
        n = unit(Vector(face.Surface.Axis))
        if str(getattr(face, "Orientation", "Forward")) == "Reversed":
            n = scaled(n, -1.0)
        return n
    except Exception:
        return unit(Vector(face.Surface.Axis))


@dataclass
class CylFace:
    index: int
    radius: float
    axis: "Vector"          # unit direction (world)
    center: "Vector"        # a point on the axis (world)
    anchor: "Vector"        # canonical point on axis line
    area: float
    is_internal: bool       # True => concave (hole wall), best-effort
    axial_pos: float = 0.0  # coordinate of the cylinder center along the main axis
    ax_lo: float = 0.0      # min vertex coordinate along the main axis
    ax_hi: float = 0.0      # max vertex coordinate along the main axis
    own_lo: float = 0.0     # min extent along this cylinder's OWN axis (from its anchor)
    own_hi: float = 0.0     # max extent along this cylinder's OWN axis (from its anchor)
    angular_span: float = 0.0  # wall coverage in radians; 0 => ask the surface
    face: object = None     # the Part.Face itself (in-process use only)


@dataclass
class PlaneFace:
    index: int
    normal: "Vector"        # unit normal (world, surface orientation applied)
    point: "Vector"         # a point on the plane (center of mass)
    area: float
    axial_pos: float = 0.0
    face: object = None     # the Part.Face itself (in-process use only)


@dataclass
class AxisCluster:
    axis: "Vector"
    anchor: "Vector"
    cyl_indices: List[int] = field(default_factory=list)
    total_area: float = 0.0


@dataclass
class ShapeModel:
    """Detected geometry of a single part (fastener or target body)."""
    object_name: str
    cylinders: List[CylFace] = field(default_factory=list)
    planes: List[PlaneFace] = field(default_factory=list)
    clusters: List[AxisCluster] = field(default_factory=list)
    main_axis: Optional["Vector"] = None
    main_anchor: Optional["Vector"] = None
    centroid: "Vector" = field(default_factory=lambda: Vector(0, 0, 0))
    bbox_min_t: float = 0.0
    bbox_max_t: float = 0.0


def _face_extent_along(face, anchor: "Vector", axis: "Vector"):
    """Min/max coordinate of a face along a given axis, measured from ``anchor``."""
    points = [Vector(v.Point) for v in getattr(face, "Vertexes", [])]
    if not points:
        bb = face.BoundBox
        points = [
            Vector(bb.XMin, bb.YMin, bb.ZMin), Vector(bb.XMax, bb.YMin, bb.ZMin),
            Vector(bb.XMin, bb.YMax, bb.ZMin), Vector(bb.XMax, bb.YMax, bb.ZMin),
            Vector(bb.XMin, bb.YMin, bb.ZMax), Vector(bb.XMax, bb.YMin, bb.ZMax),
            Vector(bb.XMin, bb.YMax, bb.ZMax), Vector(bb.XMax, bb.YMax, bb.ZMax),
        ]
    ts = [project_scalar(p, anchor, axis) for p in points]
    return min(ts), max(ts)


def _face_is_internal(face, axis: "Vector", center: "Vector") -> bool:
    """Best-effort concave/convex test for a cylindrical face.

    A hole wall has its outward face normal pointing toward the axis.
    """
    try:
        pc = face.CenterOfMass
        u, v = face.Surface.parameter(pc)
        n = face.normalAt(u, v)
        if str(getattr(face, "Orientation", "Forward")) == "Reversed":
            n = scaled(n, -1.0)
        d = unit(axis)
        rel = pc - center
        along = scaled(d, rel.dot(d))
        radial_out = rel - along          # points from axis to surface
        if radial_out.Length < 1e-9:
            return False
        return n.dot(radial_out) < 0.0    # normal points inward => hole
    except Exception:
        return False


def _edge_point(edge, fraction: float) -> "Vector":
    lo = float(edge.FirstParameter)
    hi = float(edge.LastParameter)
    return Vector(edge.valueAt(lo + fraction * (hi - lo)))


def circle_from_edge(edge) -> Optional[Tuple["Vector", float, "Vector"]]:
    """Circle (center, radius, axis) through three points of ``edge``, else None.

    ``Edge.curvatureAt`` raises ``CurvatureNotDefined`` on the straight segments
    every wall also carries, and ``BSplineCurve.toBiArcs`` shatters one rim into
    dozens of arcs. Fitting and verifying by sample points handles the degree-5
    rims this STEP writes in place of exact circles.
    """
    try:
        p1 = _edge_point(edge, 0.15)
        p2 = _edge_point(edge, 0.5)
        p3 = _edge_point(edge, 0.85)
    except Exception:
        return None
    a = p2 - p1
    b = p3 - p1
    n = a.cross(b)
    if n.Length < 1e-9:
        return None
    offset = scaled(n.cross(a), b.Length ** 2) + scaled(b.cross(n), a.Length ** 2)
    center = p1 + scaled(offset, 1.0 / (2.0 * n.Length ** 2))
    radius = (center - p1).Length
    if radius < 1e-6:
        return None
    for fraction in (0.3, 0.7):
        try:
            probe = _edge_point(edge, fraction)
        except Exception:
            return None
        if abs((probe - center).Length - radius) > CIRCLE_FIT_TOL:
            return None
    return center, radius, unit(n)


def canonical_axis(axis: "Vector") -> "Vector":
    """Axis with a deterministic sign, so coaxial faces agree on one direction.

    A fitted axis inherits the orientation of the rim it came from, and the two
    halves of one hole routinely come out opposed. Any extent measured along
    such a pair would then span the whole part instead of the wall.
    """
    d = unit(axis)
    if abs(d.x) >= max(abs(d.y), abs(d.z)):
        lead = d.x
    elif abs(d.y) >= abs(d.z):
        lead = d.y
    else:
        lead = d.z
    return d if lead >= 0.0 else scaled(d, -1.0)


def cylinder_from_face(
    face, index: int, radii: Optional[Sequence[float]] = None
) -> Optional[CylFace]:
    """Recover a cylindrical wall that the STEP writer exported as a free patch.

    A wall is recognised by its two rims: equal radius, centers stacked along
    their common axis. ``radii`` limits the fit to the radii of interest.
    """
    rims = []
    for edge in getattr(face, "Edges", []) or []:
        fitted = circle_from_edge(edge)
        if fitted is None:
            continue
        if radii is not None and not any(
            abs(fitted[1] - r) <= RECOVERY_RADIUS_TOL for r in radii
        ):
            continue
        rims.append((fitted, float(edge.Length)))
        if len(rims) == 2:
            break
    if len(rims) < 2:
        return None

    (first_center, first_radius, first_axis), first_length = rims[0]
    (second_center, second_radius, _axis), second_length = rims[1]
    if abs(first_radius - second_radius) > RIM_RADIUS_TOL:
        return None
    axis = canonical_axis(first_axis)
    offset = second_center - first_center
    if abs(offset.dot(axis)) < RIM_OFFSET_MIN:
        return None
    if offset.cross(axis).Length > RIM_OFFSET_LATERAL:
        return None

    radius = 0.5 * (first_radius + second_radius)
    anchor = axis_anchor(first_center, axis)
    own_lo, own_hi = _face_extent_along(face, anchor, axis)
    return CylFace(
        index=index,
        radius=radius,
        axis=axis,
        center=first_center,
        anchor=anchor,
        area=float(face.Area),
        is_internal=_face_is_internal(face, axis, first_center),
        own_lo=own_lo,
        own_hi=own_hi,
        angular_span=0.5 * (first_length + second_length) / radius,
        face=face,
    )


def _parameter_grid(face, steps: int = 3) -> List[Tuple[float, float]]:
    u0, u1, v0, v1 = face.ParameterRange
    du = (u1 - u0) / float(steps - 1)
    dv = (v1 - v0) / float(steps - 1)
    return [
        (u0 + i * du, v0 + j * dv) for i in range(steps) for j in range(steps)
    ]


def planar_frame(face) -> Optional[Tuple["Vector", "Vector"]]:
    """(outward normal, point) when ``face`` is flat in practice, else None.

    Large panels are often exported as freeform patches; the sample's skins
    stray by 0.025 degrees. ``Face.normalAt`` already reports the orientation
    corrected outward normal, so reversed faces need no extra flip.
    """
    try:
        normals = [unit(Vector(face.normalAt(u, v))) for u, v in _parameter_grid(face)]
    except Exception:
        return None
    if not normals or normals[0].Length < 0.5:
        return None
    limit = math.cos(math.radians(FLATNESS_TOL_DEG))
    reference = normals[0]
    for normal in normals[1:]:
        if reference.dot(normal) < limit:
            return None
    try:
        return reference, Vector(face.CenterOfMass)
    except Exception:
        return None


def is_planar_face(face) -> bool:
    """True for analytic planes and for freeform patches that are flat anyway."""
    if surface_type(face) == "Plane":
        return True
    return planar_frame(face) is not None


def _cylinder_parameter_span(face) -> float:
    """Angular coverage of an analytic cylinder, from its U parameter range."""
    try:
        u0, u1, _v0, _v1 = face.ParameterRange
        return abs(float(u1) - float(u0))
    except Exception:
        return 0.0


def detect_shape(obj, recover_radii: Optional[Sequence[float]] = None) -> ShapeModel:
    """Enumerate cylindrical and planar faces of ``obj`` and cluster the main axis.

    Faces that are neither analytic planes nor analytic cylinders are put
    through canonical recovery, which is what makes B-spline hole walls and
    B-spline sheet skins visible to the rest of the pipeline.
    """
    shape = getattr(obj, "Shape", None)
    name = getattr(obj, "Label", "") or getattr(obj, "Name", "") or "part"
    model = ShapeModel(object_name=name)
    if shape is None or not getattr(shape, "Faces", None):
        return model

    try:
        model.centroid = shape.CenterOfMass
    except Exception:
        model.centroid = shape.BoundBox.Center

    # Shape.Faces rebuilds the whole face list on every access, so read it once
    # and pass it down; indexing it inside a loop is quadratic on big parts.
    faces = shape.Faces
    for idx, face in enumerate(faces):
        stype = surface_type(face)
        if stype == "Cylinder":
            surf = face.Surface
            axis = unit(Vector(surf.Axis))
            center = Vector(surf.Center)
            anchor = axis_anchor(center, axis)
            own_lo, own_hi = _face_extent_along(face, anchor, axis)
            model.cylinders.append(
                CylFace(
                    index=idx,
                    radius=float(surf.Radius),
                    axis=axis,
                    center=center,
                    anchor=anchor,
                    area=float(face.Area),
                    is_internal=_face_is_internal(face, axis, center),
                    own_lo=own_lo,
                    own_hi=own_hi,
                    angular_span=_cylinder_parameter_span(face),
                    face=face,
                )
            )
        elif stype == "Plane":
            normal = plane_outward_normal(face)
            model.planes.append(
                PlaneFace(
                    index=idx,
                    normal=normal,
                    point=Vector(face.CenterOfMass),
                    area=float(face.Area),
                    face=face,
                )
            )
        elif stype not in ANALYTIC_SURFACES:
            recovered = cylinder_from_face(face, idx, recover_radii)
            if recovered is not None:
                model.cylinders.append(recovered)
                continue
            frame = planar_frame(face)
            if frame is not None:
                normal, point = frame
                model.planes.append(
                    PlaneFace(
                        index=idx,
                        normal=normal,
                        point=point,
                        area=float(face.Area),
                        face=face,
                    )
                )

    _cluster_axes(model)
    _fill_axial_positions(model, shape, faces)
    return model


def _cluster_axes(model: ShapeModel) -> None:
    clusters: List[AxisCluster] = []
    for cyl in model.cylinders:
        placed = False
        for cluster in clusters:
            parallel = abs(cluster.axis.dot(cyl.axis)) > 1.0 - PARALLEL_TOL
            collinear = (cluster.anchor - cyl.anchor).Length < COLLINEAR_TOL
            if parallel and collinear:
                cluster.cyl_indices.append(cyl.index)
                cluster.total_area += cyl.area
                placed = True
                break
        if not placed:
            clusters.append(
                AxisCluster(
                    axis=cyl.axis,
                    anchor=cyl.anchor,
                    cyl_indices=[cyl.index],
                    total_area=cyl.area,
                )
            )
    clusters.sort(key=lambda c: (len(c.cyl_indices), c.total_area), reverse=True)
    model.clusters = clusters
    if clusters:
        model.main_axis = clusters[0].axis
        model.main_anchor = clusters[0].anchor


def _fill_axial_positions(model: ShapeModel, shape, faces=None) -> None:
    if model.main_axis is None:
        return
    axis = model.main_axis
    anchor = model.main_anchor
    faces = faces if faces is not None else shape.Faces
    for cyl in model.cylinders:
        cyl.axial_pos = project_scalar(cyl.center, anchor, axis)
        try:
            ts = [
                project_scalar(Vector(v.Point), anchor, axis)
                for v in faces[cyl.index].Vertexes
            ]
            if ts:
                cyl.ax_lo, cyl.ax_hi = min(ts), max(ts)
        except Exception:
            cyl.ax_lo = cyl.ax_hi = cyl.axial_pos
    for plane in model.planes:
        plane.axial_pos = project_scalar(plane.point, anchor, axis)
    bb = shape.BoundBox
    corners = [
        Vector(bb.XMin, bb.YMin, bb.ZMin), Vector(bb.XMax, bb.YMin, bb.ZMin),
        Vector(bb.XMin, bb.YMax, bb.ZMin), Vector(bb.XMax, bb.YMax, bb.ZMin),
        Vector(bb.XMin, bb.YMin, bb.ZMax), Vector(bb.XMax, bb.YMin, bb.ZMax),
        Vector(bb.XMin, bb.YMax, bb.ZMax), Vector(bb.XMax, bb.YMax, bb.ZMax),
    ]
    ts = [project_scalar(c, anchor, axis) for c in corners]
    model.bbox_min_t = min(ts)
    model.bbox_max_t = max(ts)


def cluster_of(model: ShapeModel, cyl_index: int) -> Optional[AxisCluster]:
    for cluster in model.clusters:
        if cyl_index in cluster.cyl_indices:
            return cluster
    return None
