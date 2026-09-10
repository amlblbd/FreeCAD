"""Task panel: select a sheet face, detect holes, then batch-assemble weld nuts."""
from __future__ import annotations

try:
    from qt_compat import load_qt, message_box
    import assembler
    import holes
    import sample
except ImportError:
    from .qt_compat import load_qt, message_box
    from . import assembler, holes, sample

import FreeCAD  # type: ignore


class _SelectionObserver:
    """Mirrors the 3D-view selection into the panel's status line.

    It never starts a computation and never re-targets the panel: Detect holes
    reads the selection itself, so browsing the model stays free of side effects.
    """

    def __init__(self, panel):
        self._panel = panel

    def addSelection(self, *_args):
        self._refresh()

    def removeSelection(self, *_args):
        self._refresh()

    def clearSelection(self, *_args):
        self._refresh()

    def _refresh(self):
        try:
            self._panel.refresh_selection_status()
        except Exception as exc:
            FreeCAD.Console.PrintError(f"Weld-nut selection readout failed: {exc}\n")


class WeldNutTaskPanel:
    def __init__(self):
        QtCore, QtGui, QtWidgets = load_qt()
        self.QtCore = QtCore
        self.QtWidgets = QtWidgets
        self._observer = None
        self.target_name = None
        self.face_index = None
        self.holes = []
        self.sides = None
        self.previews = {}
        self._previews_finalized = False

        self.form = QtWidgets.QWidget()
        self.form.setWindowTitle("Weld Nut Batch Assembly")
        layout = QtWidgets.QVBoxLayout(self.form)

        layout.addWidget(QtWidgets.QLabel(
            "1. 勾选 M6 / M8, 然后在模型中选中一个平面，以该面的法向为参考的装配方向。\n"
            "2. 点击识别按钮，程序识别所选零件中所有的装配孔，\n包括每个识别到的孔直径、对应的焊接螺母规格。\n"
            "3. 选择列表项可高亮孔壁；勾选需要装配的孔，然后点击装配预览。\n"
            "4. 预览阶段可隐藏或高亮螺母；点击确认按钮保留勾选的螺母。"
        ))

        spec_row = QtWidgets.QHBoxLayout()
        self.m6_check = QtWidgets.QCheckBox("M6  (Ø7)")
        self.m8_check = QtWidgets.QCheckBox("M8  (Ø9)")
        self.m6_check.setChecked(True)
        self.m8_check.setChecked(True)
        spec_row.addWidget(self.m6_check)
        spec_row.addWidget(self.m8_check)
        spec_row.addStretch(1)
        layout.addLayout(spec_row)

        self.status_label = QtWidgets.QLabel()
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        action_row = QtWidgets.QHBoxLayout()
        self.detect_button = QtWidgets.QPushButton("识别装配孔")
        self.preview_button = QtWidgets.QPushButton("装配预览")
        self.confirm_button = QtWidgets.QPushButton("确认装配")
        action_row.addWidget(self.detect_button)
        action_row.addWidget(self.preview_button)
        action_row.addWidget(self.confirm_button)
        layout.addLayout(action_row)
        self.preview_button.setEnabled(False)
        self.confirm_button.setEnabled(False)

        self.hole_list = QtWidgets.QTreeWidget()
        self.hole_list.setHeaderLabels(["Use", "Hole", "Diameter", "Spec"])
        self.hole_list.setRootIsDecorated(False)
        self.hole_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        layout.addWidget(self.hole_list)

        self.report = QtWidgets.QPlainTextEdit()
        self.report.setReadOnly(True)
        self.report.setMinimumHeight(120)
        layout.addWidget(self.report)

        self.detect_button.clicked.connect(self.on_detect)
        self.preview_button.clicked.connect(self.on_preview)
        self.confirm_button.clicked.connect(self.on_confirm)
        self.hole_list.itemSelectionChanged.connect(self.on_list_selection)
        self.hole_list.itemChanged.connect(self.on_item_changed)

        self._start_observer()
        self.refresh_selection_status()

    def getStandardButtons(self):
        buttons = self.QtWidgets.QDialogButtonBox
        try:
            return int(buttons.Ok | buttons.Cancel)
        except (AttributeError, TypeError):
            standard = buttons.StandardButton
            return int(standard.Ok.value | standard.Cancel.value)

    # FreeCAD keeps the task dialog open unless these return True.
    def accept(self):
        self._finalize_previews()
        self._cleanup()
        return True

    def reject(self):
        self._discard_previews()
        self._cleanup()
        return True

    def _cleanup(self):
        self._stop_observer()

    def _discard_previews(self):
        doc = self._doc()
        if doc is not None and self.previews and not self._previews_finalized:
            assembler.delete_preview_objects(doc, self.previews)
        self.previews = {}
        self._previews_finalized = False

    def _finalize_previews(self):
        doc = self._doc()
        if (
            doc is None
            or not self.previews
            or self._previews_finalized
        ):
            return []
        kept = assembler.finalize_preview_objects(doc, self.previews, self.holes)
        self._previews_finalized = True
        return kept

    def _busy(self, busy: bool):
        """Wait cursor around the B-Rep passes, which take seconds on big sheets."""
        QtWidgets = self.QtWidgets
        app = QtWidgets.QApplication
        try:
            if busy:
                app.setOverrideCursor(self.QtCore.Qt.WaitCursor)
            else:
                app.restoreOverrideCursor()
            app.processEvents()
        except Exception:
            pass

    def _doc(self):
        return FreeCAD.ActiveDocument

    def _target(self):
        doc = self._doc()
        if doc is None or not self.target_name:
            return None
        return doc.getObject(self.target_name)

    def _selected_specs(self):
        specs = []
        if self.m6_check.isChecked():
            specs.append("M6")
        if self.m8_check.isChecked():
            specs.append("M8")
        return specs

    def _start_observer(self):
        if self._observer is not None:
            return
        try:
            import FreeCADGui
        except Exception:
            return
        self._observer = _SelectionObserver(self)
        FreeCADGui.Selection.addObserver(self._observer)

    def _stop_observer(self):
        if self._observer is None:
            return
        try:
            import FreeCADGui
            FreeCADGui.Selection.removeObserver(self._observer)
        except Exception:
            pass
        self._observer = None

    def _resolve_selection(self):
        """(object, face index) of the first face in the 3D-view selection."""
        try:
            import FreeCADGui
        except Exception:
            return None
        for sel in FreeCADGui.Selection.getSelectionEx():
            obj = sel.Object
            if obj is None or getattr(obj, "Shape", None) is None:
                continue
            # Nuts we placed sit right on the sheet, so they are easy to hit by
            # accident once previews exist; they are never a valid target.
            if hasattr(obj, "WeldNutPreview"):
                continue
            for sub in sel.SubElementNames or ():
                name = str(sub)
                if not name.startswith("Face"):
                    continue
                try:
                    index = int(name[4:]) - 1
                except ValueError:
                    continue
                return obj, index
        return None

    def refresh_selection_status(self):
        picked = self._resolve_selection()
        if picked is None:
            self.status_label.setText(
                "No face selected. Click a planar face on the sheet, then Detect holes."
            )
            return
        obj, index = picked
        self.status_label.setText(
            f"Selected {obj.Label}   Face{index + 1}. Click Detect holes."
        )

    def on_detect(self):
        picked = self._resolve_selection()
        if picked is None:
            message_box(
                self.form,
                "Detect holes",
                "Select a planar face on the sheet in the 3D view first.",
                critical=True,
            )
            return
        specs = self._selected_specs()
        if not specs:
            message_box(self.form, "Detect holes", "Check M6 and/or M8.", critical=True)
            return
        target, face_index = picked
        self._discard_previews()
        self.target_name = target.Name
        self.face_index = face_index
        self.holes = []
        self.sides = None
        self.hole_list.clear()
        self.preview_button.setEnabled(False)
        self.confirm_button.setEnabled(False)
        self._busy(True)
        try:
            self.sides = holes.classify_sheet_sides(target, self.face_index)
            self.holes = holes.detect_holes(
                target, self.face_index, specs, sides=self.sides
            )
        except Exception as exc:
            message_box(self.form, "Detect holes", str(exc), critical=True)
            return
        finally:
            self._busy(False)
        self._fill_list()
        assembler.color_holes(target, self.holes, sides=self.sides)
        self.preview_button.setEnabled(bool(self.holes))
        counts = {}
        for hole in self.holes:
            counts[hole.spec] = counts.get(hole.spec, 0) + 1
        summary = ", ".join(f"{k}: {v}" for k, v in sorted(counts.items())) or "none"
        self._log(
            f"Detected {len(self.holes)} hole(s) ({summary}) from {target.Label} "
            f"Face{self.face_index + 1}; select holes, then create an assembly preview."
        )

    def on_preview(self):
        doc = self._doc()
        target = self._target()
        if doc is None or target is None or not self.holes:
            message_box(
                self.form,
                "Assembly preview",
                "Detect holes first.",
                critical=True,
            )
            return
        self._discard_previews()
        self._busy(True)
        try:
            templates = sample.load_template_library()
            created = assembler.assemble_holes(
                doc, target, templates, self.holes, include_disabled=True
            )
            self.previews = {
                hole.hole_id: obj for hole, obj in zip(self.holes, created)
            }
            self._previews_finalized = False
        except Exception as exc:
            message_box(self.form, "Assembly preview", str(exc), critical=True)
            return
        finally:
            self._busy(False)
        selected = self.hole_list.selectedItems()
        highlight = (
            selected[0].data(0, self.QtCore.Qt.UserRole) if selected else None
        )
        assembler.update_preview_objects(
            self.previews, self.holes, highlight_id=highlight
        )
        self.preview_button.setEnabled(False)
        self.confirm_button.setEnabled(bool(self.previews))
        self._log(f"Created {len(self.previews)} weld-nut preview(s).")

    def _fill_list(self):
        self.hole_list.blockSignals(True)
        self.hole_list.clear()
        ordered = sorted(self.holes, key=lambda hole: (hole.spec, hole.hole_id))
        for hole in ordered:
            item = self.QtWidgets.QTreeWidgetItem(
                [
                    "",
                    f"#{hole.hole_id:03d}",
                    f"{hole.diameter:.3f} mm",
                    hole.spec,
                ]
            )
            item.setFlags(
                item.flags()
                | self.QtCore.Qt.ItemIsUserCheckable
                | self.QtCore.Qt.ItemIsSelectable
                | self.QtCore.Qt.ItemIsEnabled
            )
            item.setCheckState(
                0,
                self.QtCore.Qt.Checked if hole.enabled else self.QtCore.Qt.Unchecked,
            )
            item.setData(0, self.QtCore.Qt.UserRole, hole.hole_id)
            self.hole_list.addTopLevelItem(item)
        self.hole_list.blockSignals(False)
        for col in range(4):
            self.hole_list.resizeColumnToContents(col)

    def on_list_selection(self):
        items = self.hole_list.selectedItems()
        if not items:
            return
        hole_id = items[0].data(0, self.QtCore.Qt.UserRole)
        if self.previews:
            assembler.update_preview_objects(
                self.previews, self.holes, highlight_id=hole_id
            )
        else:
            target = self._target()
            if target is not None:
                assembler.color_holes(
                    target, self.holes, highlight_id=hole_id, sides=self.sides
                )

    def on_item_changed(self, item, column):
        if column != 0:
            return
        hole_id = item.data(0, self.QtCore.Qt.UserRole)
        checked = item.checkState(0) == self.QtCore.Qt.Checked
        for hole in self.holes:
            if hole.hole_id == hole_id:
                hole.enabled = bool(checked)
                break
        selected = self.hole_list.selectedItems()
        highlight = None
        if selected:
            highlight = selected[0].data(0, self.QtCore.Qt.UserRole)
        if self.previews:
            assembler.update_preview_objects(
                self.previews, self.holes, highlight_id=highlight
            )
        else:
            target = self._target()
            if target is not None:
                assembler.color_holes(
                    target, self.holes, highlight_id=highlight, sides=self.sides
                )

    def on_confirm(self):
        doc = self._doc()
        target = self._target()
        if doc is None or target is None or not self.previews:
            message_box(
                self.form,
                "Confirm assembly",
                "Create an assembly preview first.",
                critical=True,
            )
            return
        self._busy(True)
        try:
            kept = self._finalize_previews()
        except Exception as exc:
            message_box(self.form, "Confirm assembly", str(exc), critical=True)
            return
        finally:
            self._busy(False)
        self._log(
            f"Confirmed {len(kept)} weld nut(s); hidden previews were deleted."
        )
        self.confirm_button.setEnabled(False)

    def _log(self, text):
        self.report.appendPlainText(text)
