"""Color hole faces, highlight a selection, and copy weld nuts into place."""
from __future__ import annotations

from typing import Dict, List, Optional, Sequence

import FreeCAD  # type: ignore

try:
    from holes import DetectedHole, SheetSides
    from solver import solve_coincident
    from weld_nut import WeldNutInfo, extract_weld_nut
except ImportError:
    from .holes import DetectedHole, SheetSides
    from .solver import solve_coincident
    from .weld_nut import WeldNutInfo, extract_weld_nut

BASE_COLOR = (0.78, 0.78, 0.80)
M6_COLOR = (0.12, 0.42, 0.95)
M8_COLOR = (0.95, 0.50, 0.08)
HIGHLIGHT_COLOR = (0.15, 0.85, 0.25)
DISABLED_COLOR = (0.55, 0.55, 0.55)
SIDE_A_COLOR = (0.72, 0.90, 0.72)
SIDE_B_COLOR = (0.76, 0.78, 0.94)
SPEC_COLORS = {"M6": M6_COLOR, "M8": M8_COLOR}


def _set_face_colors(obj, color_map: dict) -> None:
    view = getattr(obj, "ViewObject", None)
    shape = getattr(obj, "Shape", None)
    if view is None or shape is None or not hasattr(view, "DiffuseColor"):
        return
    faces = shape.Faces
    colors = [BASE_COLOR for _ in faces]
    for idx, color in color_map.items():
        if 0 <= idx < len(colors):
            colors[idx] = color
    try:
        view.DisplayMode = "Flat Lines"
    except Exception:
        pass
    try:
        view.DiffuseColor = colors
    except Exception:
        pass


def color_holes(
    obj,
    holes: Sequence[DetectedHole],
    highlight_id: Optional[int] = None,
    sides: Optional[SheetSides] = None,
) -> None:
    color_map = _side_color_map(sides)
    for hole in holes:
        color = SPEC_COLORS.get(hole.spec, BASE_COLOR)
        if not hole.enabled:
            color = DISABLED_COLOR
        if highlight_id is not None and hole.hole_id == highlight_id:
            color = HIGHLIGHT_COLOR
        for idx in hole.cyl_indices:
            color_map[idx] = color
    _set_face_colors(obj, color_map)
    try:
        FreeCAD.ActiveDocument.recompute()
    except Exception:
        pass


def _side_color_map(sides: Optional[SheetSides]) -> dict:
    if sides is None:
        return {}
    color_map = {idx: SIDE_A_COLOR for idx in sides.side_a}
    color_map.update({idx: SIDE_B_COLOR for idx in sides.side_b})
    return color_map


def color_sheet_sides(obj, sides: SheetSides) -> None:
    """Show selected side A in green and the opposite side B in violet."""
    _set_face_colors(obj, _side_color_map(sides))
    try:
        FreeCAD.ActiveDocument.recompute()
    except Exception:
        pass


def assemble_holes(
    doc,
    target_obj,
    templates: Dict[str, object],
    holes: Sequence[DetectedHole],
    include_disabled: bool = False,
) -> List[object]:
    """Copy nut templates into place.

    Normal assembly skips disabled holes. The task panel's preview stage asks
    for all holes so unchecked rows can start hidden yet still be re-enabled.
    """
    infos: Dict[str, WeldNutInfo] = {}
    created = []
    for spec, template in templates.items():
        info = extract_weld_nut(template, spec)
        if info is None:
            raise RuntimeError(f"Could not extract weld-nut mating faces from '{template.Label}'.")
        infos[spec] = info

    for hole in holes:
        if not hole.enabled and not include_disabled:
            continue
        template = templates.get(hole.spec)
        if template is None:
            raise RuntimeError(f"No weld-nut template loaded for {hole.spec}.")
        nut = infos[hole.spec]
        solution = solve_coincident(nut, hole)
        clone = doc.addObject("Part::Feature", f"{hole.spec}_{hole.hole_id:03d}")
        clone.Label = f"{hole.spec}_{hole.hole_id:03d}"
        try:
            clone.Shape = template.Shape.copy()
        except Exception:
            clone.Shape = template.Shape
        clone.Placement = solution.placement.multiply(template.Placement)
        try:
            clone.addProperty("App::PropertyBool", "WeldNutPreview", "Assembly")
            clone.WeldNutPreview = True
        except Exception:
            pass
        created.append(clone)
    try:
        doc.recompute()
    except Exception:
        pass
    return created


def update_preview_objects(
    previews: Dict[int, object],
    holes: Sequence[DetectedHole],
    highlight_id: Optional[int] = None,
) -> None:
    """Checked rows are visible; the selected visible nut is green."""
    by_id = {hole.hole_id: hole for hole in holes}
    for hole_id, obj in previews.items():
        hole = by_id.get(hole_id)
        if hole is None:
            continue
        view = getattr(obj, "ViewObject", None)
        if view is None:
            continue
        try:
            view.Visibility = bool(hole.enabled)
            view.ShapeColor = (
                HIGHLIGHT_COLOR
                if hole.enabled and hole_id == highlight_id
                else SPEC_COLORS.get(hole.spec, BASE_COLOR)
            )
        except Exception:
            pass


def delete_preview_objects(doc, previews: Dict[int, object]) -> None:
    for obj in list(previews.values()):
        try:
            doc.removeObject(obj.Name)
        except Exception:
            pass
    doc.recompute()


def finalize_preview_objects(
    doc, previews: Dict[int, object], holes: Sequence[DetectedHole]
) -> List[object]:
    """Delete unchecked/hidden nuts and mark visible previews as final."""
    enabled = {hole.hole_id for hole in holes if hole.enabled}
    kept = []
    for hole_id, obj in list(previews.items()):
        if hole_id not in enabled:
            try:
                doc.removeObject(obj.Name)
            except Exception:
                pass
            continue
        try:
            obj.WeldNutPreview = False
        except Exception:
            pass
        try:
            obj.ViewObject.Visibility = True
            hole = next(h for h in holes if h.hole_id == hole_id)
            obj.ViewObject.ShapeColor = SPEC_COLORS.get(hole.spec, BASE_COLOR)
        except Exception:
            pass
        kept.append(obj)
    doc.recompute()
    return kept
