"""Extract concentric + seating faces from a Q371-style weld nut."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import FreeCAD  # type: ignore

try:
    import geometry as geo
    from geometry import CylFace, PlaneFace, ShapeModel, unit
except ImportError:
    from . import geometry as geo
    from .geometry import CylFace, PlaneFace, ShapeModel, unit

Vector = FreeCAD.Vector


@dataclass
class WeldNutInfo:
    spec: str
    axis: "Vector"
    anchor: "Vector"
    shank_dir: "Vector"
    concentric_cyl: CylFace
    bearing_plane: PlaneFace
    frame_origin: "Vector"


def extract_weld_nut(obj, spec: str) -> Optional[WeldNutInfo]:
    """Main-axis bore plus the weld-projection end as the seating plane."""
    model = geo.detect_shape(obj)
    if model.main_axis is None or not model.cylinders:
        return None
    axis = unit(model.main_axis)
    anchor = model.main_anchor
    internals = [c for c in model.cylinders if c.is_internal]
    concentric = min(
        internals or model.cylinders,
        key=lambda c: (c.radius, -(c.own_hi - c.own_lo)),
    )
    bearing = _weld_bearing_plane(model, axis, concentric.radius)
    if bearing is None:
        return None
    mid = 0.5 * (model.bbox_min_t + model.bbox_max_t)
    away = 1.0 if bearing.axial_pos >= mid else -1.0
    shank_dir = geo.scaled(axis, away)
    frame_origin = _project_point_on_axis(bearing.point, anchor, axis)
    return WeldNutInfo(
        spec=spec,
        axis=axis,
        anchor=anchor,
        shank_dir=shank_dir,
        concentric_cyl=concentric,
        bearing_plane=bearing,
        frame_origin=frame_origin,
    )


def _weld_bearing_plane(
    model: ShapeModel, axis: "Vector", bore_radius: float
) -> Optional[PlaneFace]:
    """Select the recessed annular face behind the four weld projections.

    The four small off-axis end faces identify the projection side.  On that
    side, the seating datum requested by the assembly is the axis-centred
    annular plane immediately behind the projection tips, not the tips.
    """
    perp = [
        p for p in model.planes
        if abs(p.normal.dot(axis)) > 1.0 - geo.ANGLE_TOL
    ]
    if not perp:
        return None
    mid = 0.5 * (model.bbox_min_t + model.bbox_max_t)
    low = [p for p in perp if p.axial_pos < mid]
    high = [p for p in perp if p.axial_pos >= mid]

    def off_axis_count(planes):
        return sum(
            1
            for p in planes
            if geo.point_to_axis_distance(p.point, model.main_anchor, axis)
            > max(0.5, bore_radius)
        )

    projection_high = off_axis_count(high) > off_axis_count(low)
    side = high if projection_high else low
    centered = [
        p
        for p in side
        if geo.point_to_axis_distance(p.point, model.main_anchor, axis)
        <= max(0.5, 0.25 * bore_radius)
        and _circle_edge_count(p.face) >= 2
    ]
    if not centered:
        centered = [
            p
            for p in side
            if geo.point_to_axis_distance(p.point, model.main_anchor, axis)
            <= max(0.5, 0.25 * bore_radius)
        ]
    if not centered:
        return None
    return (
        max(centered, key=lambda p: p.axial_pos)
        if projection_high
        else min(centered, key=lambda p: p.axial_pos)
    )


def _circle_edge_count(face) -> int:
    if face is None:
        return 0
    return sum(
        1
        for edge in getattr(face, "Edges", [])
        if type(getattr(edge, "Curve", None)).__name__ == "Circle"
    )


def _project_point_on_axis(point: "Vector", anchor: "Vector", axis: "Vector") -> "Vector":
    d = unit(axis)
    return anchor + geo.scaled(d, (point - anchor).dot(d))
