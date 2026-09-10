"""FreeCAD Workbench registration for weld-nut batch assembly."""
from __future__ import annotations

try:
    import FreeCADGui

    _WorkbenchBase = FreeCADGui.Workbench
except Exception:
    _WorkbenchBase = object


class WeldNutAssembleCommand:
    def GetResources(self):
        return {
            "MenuText": "Weld Nut Batch Assembly",
            "ToolTip": "Detect Ø7/Ø9 holes, match M6/M8 weld nuts, and assemble them",
        }

    def IsActive(self):
        return True

    def Activated(self):
        import FreeCADGui

        try:
            from task_panel import WeldNutTaskPanel
        except ImportError:
            from .task_panel import WeldNutTaskPanel

        FreeCADGui.Control.showDialog(WeldNutTaskPanel())


class WeldNutAssemblyWorkbench(_WorkbenchBase):
    MenuText = "Weld Nut Assembly"
    ToolTip = "Detect sheet-metal holes and batch-assemble weld nuts"
    Icon = ""

    def Initialize(self):
        import FreeCADGui

        FreeCADGui.addCommand("WeldNut_Batch_Assemble", WeldNutAssembleCommand())
        commands = ["WeldNut_Batch_Assemble"]
        self.appendToolbar("Weld Nut Assembly", commands)
        self.appendMenu("Weld Nut Assembly", commands)

    def Activated(self):
        pass

    def Deactivated(self):
        pass

    def GetClassName(self):
        return "Gui::PythonWorkbench"
