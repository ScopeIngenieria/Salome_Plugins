# -*- coding: utf-8 -*-
# Extract centerline edges (beams) from selected 3D solids or compounds.
# Autor: Lucio Gomez (psicofil@gmail.com)
# Creation Date: 03/09/2026

from __future__ import print_function

import os
import sys
import traceback

_PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
if _PLUGIN_DIR not in sys.path:
    sys.path.insert(0, _PLUGIN_DIR)

import salome

import get_all_beams

try:
    from qtsalome import (
        QApplication,
        QCheckBox,
        QDialog,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QMessageBox,
        QProgressBar,
        QPushButton,
        QVBoxLayout,
        Qt,
    )
except ImportError:
    try:
        from PyQt5.QtCore import Qt
        from PyQt5.QtWidgets import (
            QApplication,
            QCheckBox,
            QDialog,
            QFormLayout,
            QGroupBox,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QListWidget,
            QMessageBox,
            QProgressBar,
            QPushButton,
            QVBoxLayout,
        )
    except ImportError:
        from PySide2.QtCore import Qt
        from PySide2.QtWidgets import (
            QApplication,
            QCheckBox,
            QDialog,
            QFormLayout,
            QGroupBox,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QListWidget,
            QMessageBox,
            QProgressBar,
            QPushButton,
            QVBoxLayout,
        )

try:
    import SalomePyQt
except ImportError:
    SalomePyQt = None


_OPEN_DIALOGS = []


def _desktop(context):
    try:
        return context.sg.getDesktop()
    except Exception:
        if SalomePyQt is not None:
            try:
                return SalomePyQt.getDesktop()
            except Exception:
                pass
    return None


def _update_browser(sg):
    try:
        sg.updateObjBrowser()
    except Exception:
        pass
    try:
        sg.UpdateView()
    except Exception:
        pass


class GetAllBeamsDialog(QDialog):
    def __init__(self, context, parent=None):
        super(GetAllBeamsDialog, self).__init__(parent)
        self.context = context
        self.sg = context.sg
        self.objects = []
        self.parts = []
        self.setWindowTitle("Get all beams")
        self.setModal(False)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self._build()
        self._connect()
        self.resize(420, 480)

    def _build(self):
        main = QVBoxLayout(self)

        help_label = QLabel(
            "Select prismatic solids (cylinders, extruded beams) or a compound "
            "in GEOM. The plugin explodes them and builds one centerline EDGE per solid."
        )
        help_label.setWordWrap(True)
        main.addWidget(help_label)

        geom_box = QGroupBox("Geometry")
        geom_layout = QVBoxLayout(geom_box)
        self.capture_button = QPushButton("Load selected")
        geom_layout.addWidget(self.capture_button)
        self.selection_list = QListWidget()
        self.selection_list.setMinimumHeight(70)
        geom_layout.addWidget(self.selection_list)
        self.parts_label = QLabel("Parts: 0")
        geom_layout.addWidget(self.parts_label)
        self.parts_list = QListWidget()
        self.parts_list.setMinimumHeight(120)
        geom_layout.addWidget(self.parts_list)
        main.addWidget(geom_box)

        opt_box = QGroupBox("Result")
        opt_form = QFormLayout(opt_box)
        self.result_name = QLineEdit("Beams")
        opt_form.addRow("Name:", self.result_name)
        self.cb_compound = QCheckBox("Compound result")
        self.cb_compound.setChecked(True)
        opt_form.addRow(self.cb_compound)
        self.cb_each = QCheckBox("Publish each beam")
        opt_form.addRow(self.cb_each)
        main.addWidget(opt_box)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setFormat("%p%")
        main.addWidget(self.progress)

        self.status = QLabel("Select geometry, then Load selected.")
        self.status.setWordWrap(True)
        main.addWidget(self.status)

        buttons = QHBoxLayout()
        self.apply_button = QPushButton("Apply")
        self.close_button = QPushButton("Close")
        buttons.addStretch(1)
        buttons.addWidget(self.apply_button)
        buttons.addWidget(self.close_button)
        main.addLayout(buttons)

    def _connect(self):
        self.capture_button.clicked.connect(self.capture_geometry)
        self.apply_button.clicked.connect(self.apply_changes)
        self.close_button.clicked.connect(self.close)

    def _set_busy(self, busy):
        self.capture_button.setEnabled(not busy)
        self.apply_button.setEnabled(not busy)
        if busy:
            QApplication.setOverrideCursor(Qt.WaitCursor)
        else:
            QApplication.restoreOverrideCursor()
        QApplication.processEvents()

    def _report_progress(self, i, n):
        if n <= 0:
            self.progress.setValue(0)
        else:
            self.progress.setValue(int(100.0 * i / float(n)))
        self.status.setText("Please wait. Processing part {} / {} ...".format(i, n))
        QApplication.processEvents()

    def capture_geometry(self):
        try:
            objects = get_all_beams.get_selected_geom_objects()
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Get all beams",
                "{}\n\nSee the SALOME Python console for the traceback.".format(exc),
            )
            traceback.print_exc()
            return
        if not objects:
            QMessageBox.warning(
                self,
                "Geometry selection",
                "Select 3D solids or a compound in GEOM, then click Load selected.",
            )
            return

        self.objects = objects
        self.selection_list.clear()
        for index, obj in enumerate(objects, start=1):
            self.selection_list.addItem(
                "{}. {}".format(index, get_all_beams.object_name(obj, "Shape_{}".format(index)))
            )

        self._set_busy(True)
        self.progress.setValue(0)
        self.status.setText("Please wait. Exploding solids...")
        QApplication.processEvents()
        try:
            get_all_beams._refresh_geom()
            parts = []
            for obj in objects:
                parts.extend(get_all_beams.explode_beam_parts(obj))
            self.parts = parts
            self.parts_list.clear()
            for index, part in enumerate(parts, start=1):
                self.parts_list.addItem(
                    "{}. {}".format(
                        index, get_all_beams.object_name(part, "Part_{}".format(index))
                    )
                )
            self.parts_label.setText("Parts: {}".format(len(parts)))
            self.progress.setValue(100)
            self.status.setText(
                "Loaded {} object(s), {} part(s). Review, then Apply.".format(
                    len(objects), len(parts)
                )
            )
        except Exception as exc:
            self.progress.setValue(0)
            QMessageBox.critical(
                self,
                "Get all beams",
                "{}\n\nSee the SALOME Python console for the traceback.".format(exc),
            )
            traceback.print_exc()
        finally:
            self._set_busy(False)

    def apply_changes(self):
        if not self.objects:
            QMessageBox.warning(
                self, "Get all beams", "Load a GEOM selection first."
            )
            return
        name = str(self.result_name.text()).strip() or "Beams"
        self._set_busy(True)
        self.progress.setValue(0)
        self.status.setText("Please wait. Extracting centerlines...")
        QApplication.processEvents()
        try:
            _beams, list_edges, errors = get_all_beams.extract_all_beams(
                publish=True,
                name=name,
                selected=self.objects,
                on_progress=self._report_progress,
                compound=self.cb_compound.isChecked(),
                publish_each=self.cb_each.isChecked(),
            )
            _update_browser(self.sg)
            self.progress.setValue(100)
            lines = ["Beams extracted: {}".format(len(list_edges))]
            if errors:
                lines.append("Parts skipped: {}".format(errors))
            lines.append("Published: {}".format(name))
            self.status.setText("\n".join(lines))
            QMessageBox.information(self, "Get all beams", "\n".join(lines))
        except Exception as exc:
            self.progress.setValue(0)
            QMessageBox.critical(
                self,
                "Get all beams",
                "{}\n\nSee the SALOME Python console for the traceback.".format(exc),
            )
            traceback.print_exc()
        finally:
            self._set_busy(False)


def GetAllBeams(context):
    try:
        dialog = GetAllBeamsDialog(context=context, parent=_desktop(context))
        _OPEN_DIALOGS.append(dialog)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
    except Exception as exc:
        QMessageBox.critical(
            _desktop(context),
            "Get all beams",
            "{}\n\nSee the SALOME Python console for the traceback.".format(exc),
        )
        traceback.print_exc()
