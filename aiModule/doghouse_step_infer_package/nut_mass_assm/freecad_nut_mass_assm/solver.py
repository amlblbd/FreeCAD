"""Concentric + coincident placement for a weld nut onto a hole mouth."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List

import FreeCAD  # type: ignore

try:
    from geometry import scaled, unit
    from holes import DetectedHole
    from weld_nut import WeldNutInfo
except ImportError:
    from .geometry import scaled, unit
    from .holes import DetectedHole
    from .weld_nut import WeldNutInfo

Vector = FreeCAD.Vector


@dataclass
class MateSolution:
    placement: "FreeCAD.Placement"
    matrix: List[List[float]]
    insertion_dir: "Vector"
    mouth_outward: "Vector"
    seat_origin: "Vector"
    residual_angle_deg: float
    residual_offset_mm: float


def _matrix_to_rows(m) -> List[List[float]]:
    return [
        [m.A11, m.A12, m.A13, m.A14],
        [m.A21, m.A22, m.A23, m.A24],
        [m.A31, m.A32, m.A33, m.A34],
        [m.A41, m.A42, m.A43, m.A44],
    ]


def solve_coincident(nut: WeldNutInfo, hole: DetectedHole) -> MateSolution:
    """Map nut weld-face onto the hole mouth, axis into the sheet."""
    cyl = hole.hole_cyl
    mouth = hole.mouth_plane
    outward = unit(mouth.normal)
    insertion_dir = scaled(outward, -1.0)
    hole_axis = unit(cyl.axis)
    seat_origin = cyl.center + scaled(hole_axis, (mouth.point - cyl.center).dot(hole_axis))
    rotation = FreeCAD.Rotation(nut.shank_dir, insertion_dir)
    rotated_origin = rotation.multVec(nut.frame_origin)
    translation = seat_origin - rotated_origin
    placement = FreeCAD.Placement(translation, rotation)

    new_axis = rotation.multVec(nut.shank_dir)
    dot = max(-1.0, min(1.0, new_axis.dot(insertion_dir)))
    residual_angle = math.degrees(math.acos(dot))
    new_bearing_pt = placement.multVec(nut.frame_origin)
    residual_offset = (new_bearing_pt - seat_origin).Length

    return MateSolution(
        placement=placement,
        matrix=_matrix_to_rows(placement.toMatrix()),
        insertion_dir=insertion_dir,
        mouth_outward=outward,
        seat_origin=seat_origin,
        residual_angle_deg=residual_angle,
        residual_offset_mm=residual_offset,
    )
