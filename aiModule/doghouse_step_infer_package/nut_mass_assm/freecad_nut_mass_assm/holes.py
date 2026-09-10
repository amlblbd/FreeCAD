"""Detect clearance holes on a folded sheet and pick the seating mouth.

Hole walls are internal cylinders whose diameter matches a weld-nut spec.
Fragments of the same through-hole are merged when they share an axis.
No ranking/sorting is applied: every matching hole is returned.

The selected planar face defines sheet side A. After stripping hole walls and
thickness-edge faces, the remaining skin splits into two components (front /
back). Each hole is seated on the mouth that belongs to the A-side component.
"""
from __future__ import annotations

import math
from collections import OrderedDict, defaultdict, deque
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

import FreeCAD  # type: ignore

try:
    import geometry as geo
    from geometry import CylFace, PlaneFace, ShapeModel, project_scalar, unit
except ImportError:
    from . import geometry as geo
    from .geometry import CylFace, PlaneFace, ShapeModel, project_scalar, unit

Vector = FreeCAD.Vector

# Spec diameter in millimetres (clearance holes on the sheet).
SPEC_DIAMETERS = {
    "M6": 7.0,
    "M8": 9.0,
}
DIAMETER_TOL = 0.25          # mm on radius (~0.5 mm on diameter)
HOLE_MERGE_COLLINEAR = 0.25  # mm; looser than fastener clustering
DEFAULT_THICKNESS = 1.5
FULL_CIRCLE_TOL = 0.08       # radians missing from a complete 2*pi wall
THICKNESS_SEARCH_MM = 25.0   # how far below the reference face to look


@dataclass
class DetectedHole:
    hole_id: int
    spec: str
    diameter: float
    hole_cyl: CylFace
    cyl_indices: List[int]
    mouth_plane: PlaneFace
    enabled: bool = True


@dataclass
class SheetSides:
    side_a: Set[int]
    side_b: Set[int]
    thickness: float


@dataclass
class _SheetTopology:
    """Reusable per-shape data behind the side split (cached, see ``_topology``)."""
    thickness: float
    skin: Set[int]
    graph: Dict[int, Set[int]]
    full_graph: Optional[Dict[int, Set[int]]] = None


_TOPOLOGY_CACHE: "OrderedDict[tuple, _SheetTopology]" = OrderedDict()
_TOPOLOGY_CACHE_SIZE = 4


def clear_cache() -> None:
    _TOPOLOGY_CACHE.clear()


def spec_for_radius(radius: float, specs: Iterable[str]) -> Optional[str]:
    diameter = 2.0 * radius
    best = None
    best_err = None
    for spec in specs:
        target = SPEC_DIAMETERS.get(spec)
        if target is None:
            continue
        err = abs(diameter - target)
        if err <= 2.0 * DIAMETER_TOL and (best_err is None or err < best_err):
            best = spec
            best_err = err
    return best


def _wanted_radii(specs: Iterable[str]) -> List[float]:
    """Hole radii worth fitting, so canonical recovery skips unrelated patches."""
    return [
        0.5 * SPEC_DIAMETERS[spec] for spec in specs if spec in SPEC_DIAMETERS
    ]


def detect_holes(
    obj,
    face_index: int,
    specs: Sequence[str],
    sides: Optional[SheetSides] = None,
) -> List[DetectedHole]:
    """Identify Ø7/Ø9 holes on ``obj`` and pick A-side mouths from ``face_index``."""
    shape = getattr(obj, "Shape", None)
    if shape is None or not getattr(shape, "Faces", None):
        raise RuntimeError("Target object has no shape.")
    faces = shape.Faces
    if face_index < 0 or face_index >= len(faces):
        raise RuntimeError("Selected face is not on the target part.")
    ref_face = faces[face_index]
    if not geo.is_planar_face(ref_face):
        raise RuntimeError("Select a planar face as the sheet-side reference.")

    wanted = [s for s in specs if s in SPEC_DIAMETERS]
    if not wanted:
        raise RuntimeError("Select at least one nut spec (M6 / M8).")

    model = geo.detect_shape(obj, recover_radii=_wanted_radii(wanted))
    sides = sides or classify_sheet_sides(obj, face_index)
    topology = _topology(obj, shape, faces, face_index, ref_face)

    groups = _merge_hole_cylinders(model, wanted)
    holes: List[DetectedHole] = []
    for hole_id, group in enumerate(groups, start=1):
        cyl = _representative_cylinder(group)
        spec = spec_for_radius(cyl.radius, wanted)
        if spec is None:
            continue
        mouths = find_usable_mouth_planes(model, cyl)
        mouth = _pick_side_a_mouth(mouths, sides.side_a, shape, topology, faces)
        if mouth is None:
            continue
        holes.append(
            DetectedHole(
                hole_id=hole_id,
                spec=spec,
                diameter=2.0 * cyl.radius,
                hole_cyl=cyl,
                cyl_indices=[c.index for c in group],
                mouth_plane=mouth,
            )
        )
    return holes


def classify_sheet_sides(obj, face_index: int) -> SheetSides:
    """Split a folded sheet into skins after removing thickness-width faces.

    Hole walls and outside rims connect the two sides topologically.  Their
    effective width is approximately one sheet thickness, so remove them first
    and then diffuse from the reference face over the remaining broad faces.
    This also crosses genuine sharp bends that an angle-only rule would split.
    """
    shape = getattr(obj, "Shape", None)
    if shape is None or not getattr(shape, "Faces", None):
        raise RuntimeError("Target object has no shape.")
    if face_index < 0 or face_index >= len(shape.Faces):
        raise RuntimeError("Selected face is not on the target part.")
    ref_face = shape.Faces[face_index]
    if not geo.is_planar_face(ref_face):
        raise RuntimeError("Select a planar face as the sheet-side reference.")

    faces = shape.Faces
    topology = _topology(obj, shape, faces, face_index, ref_face)
    if face_index not in topology.skin:
        raise RuntimeError(
            "The selected face looks like a thickness edge. "
            "Pick a broad face on one side of the sheet."
        )
    side_a = _graph_component(topology.graph, face_index)

    # The opposite skin is normally the largest remaining broad component.
    components = _graph_components(topology.graph, topology.skin - side_a)
    side_b = max(
        components,
        key=lambda comp: sum(float(faces[i].Area) for i in comp),
        default=set(),
    )
    return SheetSides(
        side_a=side_a, side_b=side_b, thickness=topology.thickness
    )


def _shape_key(obj, shape, face_index: int) -> tuple:
    try:
        digest = shape.hashCode()
    except Exception:
        digest = len(shape.Faces)
    return (getattr(obj, "Name", ""), digest, face_index)


def _topology(obj, shape, faces, face_index: int, ref_face) -> _SheetTopology:
    """Thickness, skin faces and their adjacency; cached per shape and reference."""
    key = _shape_key(obj, shape, face_index)
    cached = _TOPOLOGY_CACHE.get(key)
    if cached is not None:
        _TOPOLOGY_CACHE.move_to_end(key)
        return cached

    thickness = measure_thickness(shape, ref_face, faces=faces)
    skin = {
        idx
        for idx, face in enumerate(faces)
        if not _is_thickness_edge(face, thickness)
    }
    topology = _SheetTopology(
        thickness=thickness, skin=skin, graph=_adjacency(shape, skin, faces)
    )
    _TOPOLOGY_CACHE[key] = topology
    while len(_TOPOLOGY_CACHE) > _TOPOLOGY_CACHE_SIZE:
        _TOPOLOGY_CACHE.popitem(last=False)
    return topology


def _planar_normal(face) -> Optional["Vector"]:
    """Outward normal of a face that is planar, whether analytic or recovered."""
    if geo.surface_type(face) == "Plane":
        return geo.plane_outward_normal(face)
    frame = geo.planar_frame(face)
    return frame[0] if frame is not None else None


def measure_thickness(shape, face, normal: "Vector" = None, faces=None) -> float:
    """Sheet thickness under ``face``, from the nearest anti-parallel plane.

    Sampling points with ``Shape.isInside`` needs a fresh solid classification
    per point and costs seconds on a sheet with a few thousand faces, while the
    opposite skin of a sheet is simply the closest plane facing back at this one.

    Freeform skins count as planes here, so a sheet whose panels were exported
    as B-spline patches still reports its real thickness. Flatness testing is
    not free, hence the bounding-box gate: only faces close enough to sit under
    the reference footprint are worth examining.
    """
    faces = faces if faces is not None else shape.Faces
    if normal is None:
        normal = _planar_normal(face)
        if normal is None:
            return DEFAULT_THICKNESS
    n = unit(normal)
    origin = Vector(face.CenterOfMass)
    inward = geo.scaled(n, -1.0)
    best = None
    for other in faces:
        if _bbox_distance(origin, other.BoundBox) > THICKNESS_SEARCH_MM + 1.0:
            continue
        other_normal = _planar_normal(other)
        if other_normal is None or other_normal.dot(n) > -0.9:
            continue
        distance = (Vector(other.CenterOfMass) - origin).dot(inward)
        if distance < 0.05 or distance > THICKNESS_SEARCH_MM:
            continue
        if best is not None and distance >= best:
            continue
        # Only planes actually sitting under the reference footprint qualify.
        probe = origin + geo.scaled(inward, distance)
        if _bbox_distance(probe, other.BoundBox) > 1.0:
            continue
        best = distance
    return best if best is not None else DEFAULT_THICKNESS


def _inplane_spans(face, normal: "Vector") -> Tuple[float, float]:
    n = unit(normal)
    helper = Vector(1, 0, 0) if abs(n.x) < 0.9 else Vector(0, 1, 0)
    u = unit(helper.cross(n))
    v = unit(n.cross(u))
    pts = [Vector(vtx.Point) for vtx in getattr(face, "Vertexes", [])]
    if not pts:
        return 0.0, 0.0
    us = [p.dot(u) for p in pts]
    vs = [p.dot(v) for p in pts]
    return abs(max(us) - min(us)), abs(max(vs) - min(vs))


def _is_thickness_edge(face, thickness: float) -> bool:
    edges = list(getattr(face, "Edges", []) or [])
    longest = max((float(edge.Length) for edge in edges), default=0.0)
    if longest > 1e-9:
        # For an extruded sheet edge (including a circular hole wall),
        # area / longest boundary length is approximately sheet thickness.
        effective_width = float(face.Area) / longest
        if effective_width <= 1.8 * thickness:
            return True
    stype = geo.surface_type(face)
    if stype == "Plane":
        n = geo.plane_outward_normal(face)
        a, b = _inplane_spans(face, n)
        short, long_ = (a, b) if a <= b else (b, a)
        return short <= 2.2 * thickness and long_ >= 3.0 * thickness
    return False


def _edge_key(edge) -> tuple:
    verts = getattr(edge, "Vertexes", [])
    if len(verts) < 2:
        p = Vector(verts[0].Point) if verts else Vector()
        coord = (round(p.x, 4), round(p.y, 4), round(p.z, 4))
        return (coord, coord)
    a = Vector(verts[0].Point)
    b = Vector(verts[-1].Point)
    ka = (round(a.x, 4), round(a.y, 4), round(a.z, 4))
    kb = (round(b.x, 4), round(b.y, 4), round(b.z, 4))
    return (ka, kb) if ka <= kb else (kb, ka)


def _adjacency(shape, allowed: Set[int], faces=None) -> Dict[int, Set[int]]:
    edge_faces: Dict[tuple, List[int]] = defaultdict(list)
    faces = faces if faces is not None else shape.Faces
    for idx in allowed:
        for edge in getattr(faces[idx], "Edges", []):
            edge_faces[_edge_key(edge)].append(idx)
    graph: Dict[int, Set[int]] = defaultdict(set)
    for idxs in edge_faces.values():
        unique = list(dict.fromkeys(idxs))
        for i, a in enumerate(unique):
            for b in unique[i + 1 :]:
                graph[a].add(b)
                graph[b].add(a)
    return graph


def _graph_component(graph: Dict[int, Set[int]], start: int) -> Set[int]:
    seen = {start}
    queue = deque([start])
    while queue:
        cur = queue.popleft()
        for nxt in graph.get(cur, ()):
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen


def _graph_components(
    graph: Dict[int, Set[int]], allowed: Set[int]
) -> List[Set[int]]:
    components = []
    unseen = set(allowed)
    while unseen:
        start = next(iter(unseen))
        component = {start}
        queue = deque([start])
        unseen.remove(start)
        while queue:
            cur = queue.popleft()
            for nxt in graph.get(cur, ()):
                if nxt in unseen:
                    unseen.remove(nxt)
                    component.add(nxt)
                    queue.append(nxt)
        components.append(component)
    return components


# This STEP export tags hole walls as non-internal; match Ø7/Ø9 by radius only.
def _merge_hole_cylinders(model: ShapeModel, specs: Sequence[str]) -> List[List[CylFace]]:
    candidates = []
    for cyl in model.cylinders:
        if spec_for_radius(cyl.radius, specs) is None:
            continue
        candidates.append(cyl)

    groups: List[List[CylFace]] = []
    used = [False] * len(candidates)
    for i, cyl in enumerate(candidates):
        if used[i]:
            continue
        group = [cyl]
        used[i] = True
        for j in range(i + 1, len(candidates)):
            if used[j]:
                continue
            other = candidates[j]
            if abs(other.radius - cyl.radius) > DIAMETER_TOL:
                continue
            parallel = abs(unit(cyl.axis).dot(unit(other.axis))) > 1.0 - geo.PARALLEL_TOL
            collinear = (cyl.anchor - other.anchor).Length < HOLE_MERGE_COLLINEAR
            if parallel and collinear:
                group.append(other)
                used[j] = True
        # Circular holes in this STEP are commonly split into two half-cylinder
        # faces.  A slot contributes only one or two separated partial cylinders.
        # Requiring complete angular coverage filters slot end caps robustly.
        angular_coverage = sum(_cylinder_angular_span(c) for c in group)
        if angular_coverage >= 2.0 * math.pi - FULL_CIRCLE_TOL:
            groups.append(group)
    return groups


def _cylinder_angular_span(cyl: CylFace) -> float:
    if cyl.angular_span > 0.0:
        return cyl.angular_span
    try:
        u0, u1, _v0, _v1 = cyl.face.ParameterRange
        return abs(float(u1) - float(u0))
    except Exception:
        span = abs(cyl.own_hi - cyl.own_lo)
        if cyl.radius <= 1e-9 or span <= 1e-9:
            return 0.0
        return min(2.0 * math.pi, cyl.area / (cyl.radius * span))


def _representative_cylinder(group: List[CylFace]) -> CylFace:
    primary = max(group, key=lambda c: c.area)
    # Each member measured its own extent along its own axis, and coaxial faces
    # of one hole may carry opposite axis directions. Re-project everything onto
    # the primary axis, otherwise the wall appears to span the whole part.
    extents = [
        geo._face_extent_along(c.face, primary.anchor, primary.axis)
        if c.face is not None
        else (c.own_lo, c.own_hi)
        for c in group
    ]
    own_lo = min(lo for lo, _hi in extents)
    own_hi = max(hi for _lo, hi in extents)
    return CylFace(
        index=primary.index,
        radius=primary.radius,
        axis=primary.axis,
        center=primary.center,
        anchor=primary.anchor,
        area=sum(c.area for c in group),
        is_internal=True,
        own_lo=own_lo,
        own_hi=own_hi,
        face=primary.face,
    )


def find_usable_mouth_planes(
    target: ShapeModel, hole: CylFace
) -> List[Tuple[str, PlaneFace]]:
    """Find at most one actual circular opening at each axial end of a hole."""
    axis = unit(hole.axis)
    span = max(0.0, hole.own_hi - hole.own_lo)
    axial_tolerance = max(0.15, span * 0.25, 0.35)
    radial_tolerance = max(0.2, hole.radius * 0.2)
    best: dict = {}
    for plane in target.planes:
        dot = plane.normal.dot(axis)
        if abs(dot) <= 1.0 - geo.ANGLE_TOL:
            continue
        seat_t = project_scalar(plane.point, hole.anchor, axis)
        low_dist = abs(seat_t - hole.own_lo)
        high_dist = abs(seat_t - hole.own_hi)
        side = "low" if low_dist <= high_dist else "high"
        end_dist = min(low_dist, high_dist)
        if end_dist > axial_tolerance:
            continue
        if side == "low" and dot >= 0.0:
            continue
        if side == "high" and dot <= 0.0:
            continue
        seat_point = hole.anchor + geo.scaled(axis, seat_t)
        lateral = _distance_point_to_face(seat_point, plane, hole.radius)
        if abs(lateral - hole.radius) > radial_tolerance:
            continue
        key = (end_dist + abs(lateral - hole.radius), plane.index, plane)
        previous = best.get(side)
        if previous is None or key[:2] < previous[:2]:
            best[side] = key
    return [(side, best[side][2]) for side in ("low", "high") if side in best]


def _pick_side_a_mouth(
    mouths: List[Tuple[str, PlaneFace]],
    side_a: Set[int],
    shape,
    topology: Optional[_SheetTopology] = None,
    faces=None,
) -> Optional[PlaneFace]:
    if not mouths:
        return None
    for _side, plane in mouths:
        if plane.index in side_a:
            return plane
    # Mouth plane may be a small coplanar island; accept a face adjacent to A.
    graph = _full_adjacency(shape, topology, faces)
    scored = []
    for _side, plane in mouths:
        neighbors = graph.get(plane.index, set())
        score = sum(1 for n in neighbors if n in side_a)
        scored.append((score, plane))
    scored.sort(key=lambda row: row[0], reverse=True)
    if scored and scored[0][0] > 0:
        return scored[0][1]
    return mouths[0][1]


def _full_adjacency(
    shape, topology: Optional[_SheetTopology] = None, faces=None
) -> Dict[int, Set[int]]:
    """Adjacency over every face, built at most once per detection run."""
    if topology is not None and topology.full_graph is not None:
        return topology.full_graph
    faces = faces if faces is not None else shape.Faces
    graph = _adjacency(shape, set(range(len(faces))), faces)
    if topology is not None:
        topology.full_graph = graph
    return graph


def _bbox_distance(point: "Vector", bbox) -> float:
    dx = max(bbox.XMin - point.x, 0.0, point.x - bbox.XMax)
    dy = max(bbox.YMin - point.y, 0.0, point.y - bbox.YMax)
    dz = max(bbox.ZMin - point.z, 0.0, point.z - bbox.ZMax)
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def _distance_point_to_face(point: "Vector", plane: PlaneFace, hole_radius: float) -> float:
    face = plane.face
    if face is None:
        return (plane.point - point).Length
    lower_bound = _bbox_distance(point, face.BoundBox)
    if lower_bound > 4.0 * hole_radius + 5.0:
        return lower_bound
    try:
        import Part  # type: ignore

        return float(face.distToShape(Part.Vertex(point))[0])
    except Exception:
        return lower_bound
