"""Import the 中央通道加强板 STEP files into the active document."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

import FreeCAD  # type: ignore
import Part  # type: ignore

TARGET_LABEL = "5100541001"
NUT_LABELS = {"M6": "Q37106", "M8": "Q37108"}
NUT_FILES = {"M6": "Q37106.stp", "M8": "Q37108.stp"}
TARGET_FILE = "5100541001.stp"
INPUT_DIRNAME = "中央通道加强板"


@dataclass
class ShapeTemplate:
    """In-memory STEP template; never appears in the FreeCAD document tree."""
    Shape: object
    Label: str
    Placement: object


def project_root() -> Path:
    env = os.environ.get("NUT_MASS_ASSM_ROOT", "").strip()
    if env:
        return Path(env)
    here = Path(__file__).resolve().parent
    if (here.parent / "input").is_dir():
        return here.parent
    if (here / "input").is_dir():
        return here
    return here.parent


def input_dir() -> Path:
    return project_root() / "input" / INPUT_DIRNAME


def _largest_solid(shape) -> "Part.Shape":
    solids = list(getattr(shape, "Solids", []) or [])
    if not solids:
        return shape
    solids.sort(key=lambda s: abs(float(s.Volume)), reverse=True)
    return solids[0]


def import_step(doc, path: Path, label: str):
    if not path.is_file():
        raise RuntimeError(f"STEP file not found: {path}")
    shape = Part.Shape()
    shape.read(str(path))
    shape = _largest_solid(shape)
    obj = doc.addObject("Part::Feature", label)
    obj.Label = label
    obj.Shape = shape
    return obj


def _offset_template(obj, target, index: int) -> None:
    tbb = target.Shape.BoundBox
    obb = obj.Shape.BoundBox
    gap = 20.0
    placement = obj.Placement
    placement.Base = FreeCAD.Vector(
        tbb.XMax + gap + (obb.XMax - obb.XMin) * index + index * gap,
        tbb.YMin,
        tbb.ZMin,
    )
    obj.Placement = placement


def load_sample(doc=None) -> Tuple[object, Dict[str, object]]:
    """Load the sample sheet; nut templates stay in memory."""
    doc = doc or FreeCAD.ActiveDocument
    if doc is None:
        doc = FreeCAD.newDocument("WeldNutDemo")
    target = import_step(doc, input_dir() / TARGET_FILE, TARGET_LABEL)
    templates = load_template_library()
    try:
        doc.recompute()
    except Exception:
        pass
    return target, templates


def load_template_library() -> Dict[str, ShapeTemplate]:
    """Read M6/M8 STEP files as transient Shapes, without document entities."""
    folder = input_dir()
    templates: Dict[str, ShapeTemplate] = {}
    for spec, filename in NUT_FILES.items():
        path = folder / filename
        if not path.is_file():
            raise RuntimeError(f"STEP file not found: {path}")
        shape = Part.Shape()
        shape.read(str(path))
        templates[spec] = ShapeTemplate(
            Shape=_largest_solid(shape),
            Label=NUT_LABELS[spec],
            Placement=FreeCAD.Placement(),
        )
    return templates


def ensure_templates(doc=None, target=None) -> Dict[str, ShapeTemplate]:
    """Backward-compatible alias; no entities are added to ``doc``."""
    return load_template_library()


def find_target(doc, preferred_name: Optional[str] = None):
    if preferred_name:
        obj = doc.getObject(preferred_name)
        if obj is not None:
            return obj
    for obj in getattr(doc, "Objects", []) or []:
        label = getattr(obj, "Label", "") or ""
        if TARGET_LABEL in label:
            return obj
    return None
