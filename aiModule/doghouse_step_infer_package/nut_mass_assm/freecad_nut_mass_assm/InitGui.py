"""FreeCAD GUI bootstrap for the weld-nut mass-assembly workbench.

FreeCAD adds each Mod subfolder to sys.path before exec-ing InitGui.py, so the
sibling modules are importable by their top-level names. Avoid relying on
``__file__`` here: the addon loader does not always define it.
"""
import FreeCADGui as Gui

try:
    from nut_workbench import WeldNutAssemblyWorkbench
except ImportError:
    from freecad_nut_mass_assm.nut_workbench import WeldNutAssemblyWorkbench


Gui.addWorkbench(WeldNutAssemblyWorkbench())
