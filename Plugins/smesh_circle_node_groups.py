# -*- coding: utf-8 -*-
# Create one NODE group per circular hole, pairing semi-circles / arcs
# that belong to the same circle. Optionally insert the center node.
#
# Typical Code_Aster use:
#   LIAISON_SOLIDE  -> GROUP_NO with circle nodes + center
#   LIAISON_RBE2    -> GROUP_NO_MAIT = center, GROUP_NO_ESCL = circle
#
# Autor: Lucio Gomez (psicofil@gmail.com)
# Creation Date: 29/08/2026

from __future__ import print_function

import os
import sys
import traceback

_PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
if _PLUGIN_DIR not in sys.path:
    sys.path.insert(0, _PLUGIN_DIR)

import salome
import SMESH
from salome.geom import geomBuilder
from salome.smesh import smeshBuilder

from circle_pairing import (
    TWO_PI,
    cluster_circular_edges,
    linear_tolerance,
    mean_axis,
    mean_center,
    mean_radius,
    normalize,
    vec_dot,
    vec_len,
    vec_sub,
)

try:
    from qtsalome import (
        QCheckBox,
        QDialog,
        QDoubleSpinBox,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QMessageBox,
        QPushButton,
        QVBoxLayout,
        Qt,
    )
except ImportError:
    try:
        from PyQt5.QtCore import Qt
        from PyQt5.QtWidgets import (
            QCheckBox,
            QDialog,
            QDoubleSpinBox,
            QFormLayout,
            QGroupBox,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QListWidget,
            QMessageBox,
            QPushButton,
            QVBoxLayout,
        )
    except ImportError:
        from PySide2.QtCore import Qt
        from PySide2.QtWidgets import (
            QCheckBox,
            QDialog,
            QDoubleSpinBox,
            QFormLayout,
            QGroupBox,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QListWidget,
            QMessageBox,
            QPushButton,
            QVBoxLayout,
        )

try:
    import SalomePyQt
except ImportError:
    SalomePyQt = None


_OPEN_DIALOGS = []


# ---------------------------------------------------------------------------
# Selection helpers (same strategy as add_geom_points_plugin)
# ---------------------------------------------------------------------------

def _get_selected_entries(context=None):
    candidates = []
    if context is not None:
        ctx_salome = getattr(context, "salome", None)
        ctx_salome_sg = getattr(ctx_salome, "sg", None)
        if ctx_salome_sg is not None:
            candidates.append(ctx_salome_sg)
    global_sg = getattr(salome, "sg", None)
    if global_sg is not None and all(global_sg is not c for c in candidates):
        candidates.append(global_sg)
    for sg_api in candidates:
        try:
            return list(sg_api.getAllSelected())
        except Exception:
            pass
        try:
            count = int(sg_api.SelectedCount())
            return [sg_api.getSelected(i) for i in range(count)]
        except Exception:
            pass
    try:
        import libSALOME_Swig
        sg_api = libSALOME_Swig.SALOMEGUI_Swig()
        try:
            return list(sg_api.getAllSelected())
        except Exception:
            count = int(sg_api.SelectedCount())
            return [sg_api.getSelected(i) for i in range(count)]
    except Exception as exc:
        raise RuntimeError(
            "Unable to read the current SALOME Object Browser selection."
        ) from exc


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


def _is_geom_object(obj):
    if obj is None:
        return False
    try:
        obj.GetShapeType()
        return True
    except Exception:
        return False


def _is_top_mesh(obj):
    if obj is None:
        return False
    try:
        obj.GetShapeToMesh()
        return True
    except Exception:
        return False


def _object_from_entry(study, entry):
    sobj = study.FindObjectID(entry)
    if sobj is None:
        return None, None
    try:
        return sobj, sobj.GetObject()
    except Exception:
        return sobj, None


# ---------------------------------------------------------------------------
# Geometry: circular edges, pairing of semi-circles / arcs
# ---------------------------------------------------------------------------

def _kind_name(kind):
    text = str(kind)
    if "." in text:
        text = text.rsplit(".", 1)[-1]
    return text


def _extract_edges(geompy, obj):
    """Return EDGE sub-shapes of a GEOM object (group, compound, face, wire, edge)."""
    shape_type = str(obj.GetShapeType())
    if shape_type == "EDGE":
        return [obj]
    edges = geompy.ExtractShapes(obj, geompy.ShapeType["EDGE"], True)
    if edges:
        return list(edges)
    if shape_type == "FACE":
        wires = geompy.ExtractShapes(obj, geompy.ShapeType["WIRE"], True) or [obj]
        found = []
        for wire in wires:
            found.extend(geompy.ExtractShapes(wire, geompy.ShapeType["EDGE"], True) or [])
        return found
    return []


def _circle_descriptor(geompy, edge):
    """Return a descriptor dict for CIRCLE / ARC_CIRCLE edges, else None."""
    info = geompy.KindOfShape(edge)
    if not info:
        return None
    kind = _kind_name(info[0])
    if kind not in ("CIRCLE", "ARC_CIRCLE"):
        return None
    if len(info) < 8:
        return None
    center = (float(info[1]), float(info[2]), float(info[3]))
    axis = normalize((float(info[4]), float(info[5]), float(info[6])))
    radius = float(info[7])
    length = 0.0
    try:
        length = float(geompy.BasicProperties(edge)[0])
    except Exception:
        length = 0.0
    expected = TWO_PI * radius if radius > 0.0 else 0.0
    is_full = kind == "CIRCLE" or (
        expected > 0.0 and abs(length - expected) <= max(1.0e-6, 0.02 * expected)
    )
    return {
        "edge": edge,
        "kind": kind,
        "center": center,
        "axis": axis,
        "radius": radius,
        "length": length,
        "is_full": is_full,
    }


def collect_circular_clusters(geompy, geom_objects, abs_tol, rel_tol=1.0e-6):
    descriptors = []
    skipped = 0
    seen = set()
    for obj in geom_objects:
        for edge in _extract_edges(geompy, obj):
            marker = id(edge)
            try:
                marker = (edge.GetEntry(),)
            except Exception:
                try:
                    marker = (id(edge), tuple(geompy.PointCoordinates(geompy.MakeCDG(edge))))
                except Exception:
                    marker = (id(edge),)
            if marker in seen:
                continue
            seen.add(marker)
            desc = _circle_descriptor(geompy, edge)
            if desc is None:
                skipped += 1
                continue
            descriptors.append(desc)
    clusters = cluster_circular_edges(descriptors, abs_tol, rel_tol)
    return clusters, skipped


# ---------------------------------------------------------------------------
# Mesh: node groups, center node, 0D element
# ---------------------------------------------------------------------------

def _unique_ids(ids):
    return list(dict.fromkeys(int(i) for i in ids))


def _node_xyz(mesh, node_id):
    xyz = mesh.GetNodeXYZ(node_id)
    return (float(xyz[0]), float(xyz[1]), float(xyz[2]))


def _find_or_add_node(mesh, point, tolerance, reuse):
    x, y, z = point
    if reuse and mesh.NbNodes() > 0:
        candidate = mesh.FindNodeClosestTo(x, y, z)
        if candidate:
            existing = _node_xyz(mesh, candidate)
            if vec_len(vec_sub(existing, point)) <= tolerance:
                return candidate, True
    node_id = mesh.AddNode(x, y, z)
    if not node_id:
        raise RuntimeError(
            "SMESH failed to create a node at ({:.12g}, {:.12g}, {:.12g}).".format(x, y, z)
        )
    return node_id, False


def _nodes_by_geom(smesh, mesh, geom_obj, tolerance):
    """Collect NODE ids lying on a GEOM edge / group."""
    ids = []
    try:
        tmp = mesh.GroupOnGeom(geom_obj, "_tmp_circle_nodes", SMESH.NODE)
        try:
            ids = list(tmp.GetIDs())
        finally:
            try:
                mesh.RemoveGroup(tmp)
            except Exception:
                pass
        if ids:
            return _unique_ids(ids)
    except Exception:
        pass

    for functor in (SMESH.FT_BelongToGeom, SMESH.FT_LyingOnGeom):
        try:
            filtr = smesh.GetFilter(SMESH.NODE, functor, geom_obj, Tolerance=tolerance)
            ids = list(filtr.GetElementsId(mesh.GetMesh()))
            if ids:
                return _unique_ids(ids)
        except Exception:
            try:
                criterion = smesh.GetCriterion(
                    SMESH.NODE, functor, SMESH.FT_Undefined, geom_obj, Tolerance=tolerance
                )
                filtr = smesh.GetFilterFromCriteria([criterion])
                filtr.SetMesh(mesh.GetMesh())
                tmp = mesh.CreateGroupFromFilter(SMESH.NODE, "_tmp_circle_nodes", filtr)
                try:
                    ids = list(tmp.GetIDs())
                finally:
                    try:
                        mesh.RemoveGroup(tmp)
                    except Exception:
                        pass
                if ids:
                    return _unique_ids(ids)
            except Exception:
                pass
    return []


def _nodes_by_coordinates(mesh, center, axis, radius, tolerance):
    """Fallback: nodes whose coordinates lie on the circle."""
    n = normalize(axis)
    ids = []
    for node_id in mesh.GetNodesId():
        p = _node_xyz(mesh, node_id)
        rel = vec_sub(p, center)
        axial = abs(vec_dot(rel, n))
        proj = (
            rel[0] - vec_dot(rel, n) * n[0],
            rel[1] - vec_dot(rel, n) * n[1],
            rel[2] - vec_dot(rel, n) * n[2],
        )
        radial = vec_len(proj)
        if axial <= tolerance and abs(radial - radius) <= tolerance:
            ids.append(int(node_id))
    return _unique_ids(ids)


def _make_geom_edge_group(geompy, main_shape, edges, name):
    group = geompy.CreateGroup(main_shape, geompy.ShapeType["EDGE"])
    added = 0
    for edge in edges:
        try:
            sid = geompy.GetSubShapeID(main_shape, edge)
            geompy.AddObject(group, sid)
            added += 1
        except Exception:
            continue
    if added == 0:
        return None
    try:
        group.SetName(name)
    except Exception:
        pass
    return group


def _standalone_node_group(mesh, name, node_ids):
    existing = mesh.GetGroupByName(name, SMESH.NODE)
    for old in existing:
        try:
            mesh.RemoveGroup(old)
        except Exception:
            pass
    group = mesh.CreateEmptyGroup(SMESH.NODE, name)
    if node_ids:
        group.Add(_unique_ids(node_ids))
    return group


def _circle_nodes_for_cluster(smesh, mesh, geompy, cluster, geom_group, tolerance):
    node_ids = []
    if geom_group is not None:
        node_ids = _nodes_by_geom(smesh, mesh, geom_group, tolerance)
    if not node_ids:
        collected = []
        for item in cluster:
            collected.extend(_nodes_by_geom(smesh, mesh, item["edge"], tolerance))
        node_ids = _unique_ids(collected)
    if not node_ids:
        node_ids = _nodes_by_coordinates(
            mesh,
            mean_center(cluster),
            mean_axis(cluster),
            mean_radius(cluster),
            tolerance,
        )
    return _unique_ids(node_ids)


def process_circles(smesh, mesh, geompy, geom_objects, options):
    abs_tol = float(options["tolerance"])
    rel_tol = float(options.get("rel_tolerance", 1.0e-6))
    prefix = options["prefix"].strip() or "HOLE"
    publish = bool(options["publish_geom"])
    add_center = bool(options["add_center"])
    make_0d = bool(options["make_0d"])
    make_rbe2 = bool(options["make_rbe2"])
    reuse_nodes = bool(options["reuse_nodes"])

    clusters, skipped = collect_circular_clusters(geompy, geom_objects, abs_tol, rel_tol)
    if not clusters:
        raise RuntimeError(
            "No circular edges (CIRCLE / ARC_CIRCLE) were found in the selected geometry."
        )

    main_shape = None
    try:
        if mesh.HasShapeToMesh():
            main_shape = mesh.GetShape()
    except Exception:
        main_shape = None
    if main_shape is None:
        try:
            main_shape = geompy.GetMainShape(geom_objects[0])
        except Exception:
            main_shape = geom_objects[0]

    created = []
    warnings = []

    for index, cluster in enumerate(clusters, start=1):
        name = "{}_{:02d}".format(prefix, index)
        center = mean_center(cluster)
        axis = mean_axis(cluster)
        radius = mean_radius(cluster)
        edges = [item["edge"] for item in cluster]
        lin_tol = linear_tolerance(radius, abs_tol, rel_tol)

        geom_group = None
        if main_shape is not None:
            geom_group = _make_geom_edge_group(geompy, main_shape, edges, name)
        if geom_group is not None and publish:
            try:
                geompy.addToStudyInFather(main_shape, geom_group, name)
            except Exception:
                try:
                    geompy.addToStudy(geom_group, name)
                except Exception:
                    pass

        node_ids = _circle_nodes_for_cluster(
            smesh, mesh, geompy, cluster, geom_group, lin_tol
        )
        if not node_ids:
            warnings.append("{}: no mesh nodes found on the circle.".format(name))
            continue

        slave_ids = list(node_ids)
        center_id = None
        reused = False
        if add_center:
            center_id, reused = _find_or_add_node(mesh, center, lin_tol, reuse_nodes)
            if center_id not in node_ids:
                node_ids.append(center_id)
            if publish and main_shape is not None:
                try:
                    vertex = geompy.MakeVertex(center[0], center[1], center[2])
                    geompy.addToStudyInFather(main_shape, vertex, name + "_CENTER")
                except Exception:
                    pass

        group_all = _standalone_node_group(mesh, name, node_ids)
        result = {
            "name": name,
            "arcs": len(cluster),
            "paired": len(cluster) > 1,
            "full": any(item["is_full"] for item in cluster) or len(cluster) > 1,
            "radius": radius,
            "center": center,
            "nodes": len(node_ids),
            "center_id": center_id,
            "center_reused": reused,
            "group": group_all.GetName(),
        }

        if add_center and make_rbe2 and center_id:
            _standalone_node_group(mesh, name + "_ESCL", slave_ids)
            _standalone_node_group(mesh, name + "_MAIT", [center_id])
            result["escl"] = name + "_ESCL"
            result["mait"] = name + "_MAIT"

        if add_center and make_0d and center_id:
            try:
                mesh.Add0DElement(center_id, False)
            except Exception:
                try:
                    mesh.Add0DElement(center_id)
                except Exception:
                    warnings.append("{}: could not create a 0D element on the center node.".format(name))

        created.append(result)

        if len(cluster) == 1 and not cluster[0]["is_full"]:
            warnings.append(
                "{}: only one circular arc was found; the other half may be missing.".format(name)
            )

    return {
        "created": created,
        "skipped_edges": skipped,
        "clusters": len(clusters),
    }


# ---------------------------------------------------------------------------
# Dialog
# ---------------------------------------------------------------------------

class CircleNodeGroupsDialog(QDialog):
    def __init__(self, context, mesh, mesh_ref, parent=None):
        super(CircleNodeGroupsDialog, self).__init__(parent)
        self.context = context
        self.study = context.study
        self.sg = context.sg
        self.mesh = mesh
        self.mesh_ref = mesh_ref
        self.geompy = geomBuilder.New(self.study)
        self.smesh = smeshBuilder.New()
        self.geom_objects = []

        self.setWindowTitle("Circle node groups")
        self.setModal(False)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.resize(560, 620)
        self._build_ui()
        self._connect()

    def _build_ui(self):
        main = QVBoxLayout(self)

        mesh_box = QGroupBox("Target mesh")
        mesh_form = QFormLayout(mesh_box)
        self.mesh_name = QLineEdit(self.mesh.GetName())
        self.mesh_name.setReadOnly(True)
        mesh_form.addRow("Mesh:", self.mesh_name)
        main.addWidget(mesh_box)

        geom_box = QGroupBox("Geometry group")
        geom_layout = QVBoxLayout(geom_box)
        hint = QLabel(
            "Select a GEOM group (or several shapes) that contains the circular "
            "hole edges. Semi-circles and quarter-arcs of the same hole are paired "
            "automatically into a single group."
        )
        hint.setWordWrap(True)
        geom_layout.addWidget(hint)
        self.capture_button = QPushButton("Capture geometry selection")
        geom_layout.addWidget(self.capture_button)
        self.selection_list = QListWidget()
        self.selection_list.setMinimumHeight(90)
        geom_layout.addWidget(self.selection_list)
        self.preview_list = QListWidget()
        self.preview_list.setMinimumHeight(110)
        geom_layout.addWidget(QLabel("Detected circles:"))
        geom_layout.addWidget(self.preview_list)
        self.preview_label = QLabel("No geometry captured yet.")
        self.preview_label.setWordWrap(True)
        geom_layout.addWidget(self.preview_label)
        main.addWidget(geom_box)

        opt_box = QGroupBox("Options")
        opt_form = QFormLayout(opt_box)
        self.prefix = QLineEdit("HOLE")
        opt_form.addRow("Group prefix:", self.prefix)

        self.tolerance = QDoubleSpinBox()
        self.tolerance.setDecimals(12)
        self.tolerance.setRange(0.0, 1.0e6)
        self.tolerance.setValue(1.0e-6)
        self.tolerance.setSingleStep(1.0e-6)
        opt_form.addRow("Pairing / node tolerance:", self.tolerance)

        self.add_center = QCheckBox("Create center node and add it to the circle group")
        self.add_center.setChecked(True)
        opt_form.addRow(self.add_center)

        self.reuse_nodes = QCheckBox("Reuse an existing coincident mesh node")
        self.reuse_nodes.setChecked(True)
        opt_form.addRow(self.reuse_nodes)

        self.make_0d = QCheckBox("Create a 0D element on the center node")
        self.make_0d.setChecked(True)
        opt_form.addRow(self.make_0d)

        self.make_rbe2 = QCheckBox(
            "Also create _MAIT / _ESCL groups (LIAISON_RBE2)"
        )
        self.make_rbe2.setChecked(True)
        opt_form.addRow(self.make_rbe2)

        self.publish_geom = QCheckBox("Publish a GEOM edge group per circle")
        self.publish_geom.setChecked(True)
        opt_form.addRow(self.publish_geom)
        main.addWidget(opt_box)

        self.status = QLabel("")
        self.status.setWordWrap(True)
        main.addWidget(self.status)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.apply_button = QPushButton("Apply")
        self.close_button = QPushButton("Close")
        buttons.addWidget(self.apply_button)
        buttons.addWidget(self.close_button)
        main.addLayout(buttons)
        self._update_apply()

    def _connect(self):
        self.capture_button.clicked.connect(self.capture_geometry)
        self.apply_button.clicked.connect(self.apply_changes)
        self.close_button.clicked.connect(self.close)
        self.prefix.textChanged.connect(self._update_apply)
        self.add_center.toggled.connect(self._sync_center_options)
        self._sync_center_options(self.add_center.isChecked())

    def closeEvent(self, event):
        try:
            if self in _OPEN_DIALOGS:
                _OPEN_DIALOGS.remove(self)
        finally:
            super(CircleNodeGroupsDialog, self).closeEvent(event)

    def _sync_center_options(self, checked):
        self.reuse_nodes.setEnabled(checked)
        self.make_0d.setEnabled(checked)
        self.make_rbe2.setEnabled(checked)

    def _update_apply(self):
        self.apply_button.setEnabled(
            bool(self.geom_objects) and bool(self.prefix.text().strip())
        )

    def capture_geometry(self):
        try:
            entries = _get_selected_entries(self.context)
        except Exception as exc:
            QMessageBox.warning(self, "Geometry selection", str(exc))
            return
        if not entries:
            QMessageBox.warning(
                self,
                "Geometry selection",
                "Select a GEOM group (or circular edges) in the Object Browser.",
            )
            return

        geom_objects = []
        names = []
        rejected = []
        for entry in entries:
            sobj, obj = _object_from_entry(self.study, entry)
            label = sobj.GetName() if sobj is not None else str(entry)
            if not _is_geom_object(obj):
                rejected.append(label)
                continue
            geom_objects.append(obj)
            names.append(label)

        if not geom_objects:
            QMessageBox.warning(
                self,
                "Geometry selection",
                "The current selection contains no valid GEOM object.\n"
                "Select a group of circular edges, a compound, or the hole faces.",
            )
            return

        try:
            clusters, skipped = collect_circular_clusters(
                self.geompy,
                geom_objects,
                float(self.tolerance.value()),
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Geometry analysis error",
                "{}\n\n{}".format(exc, traceback.format_exc()),
            )
            return

        self.geom_objects = geom_objects
        self.selection_list.clear()
        self.preview_list.clear()
        for name, obj in zip(names, geom_objects):
            self.selection_list.addItem("{}   [{}]".format(name, obj.GetShapeType()))
        if rejected:
            self.selection_list.addItem("Ignored non-GEOM objects: {}".format(len(rejected)))

        prefix = self.prefix.text().strip() or "HOLE"
        for index, cluster in enumerate(clusters, start=1):
            center = mean_center(cluster)
            radius = mean_radius(cluster)
            kinds = ", ".join(item["kind"] for item in cluster)
            paired = "paired" if len(cluster) > 1 else ("full circle" if cluster[0]["is_full"] else "single arc")
            self.preview_list.addItem(
                "{}_{:02d}: {} edge(s) [{}], R={:.6g}, C=({:.6g}, {:.6g}, {:.6g})".format(
                    prefix, index, len(cluster), paired, radius, center[0], center[1], center[2]
                )
            )
            self.preview_list.item(self.preview_list.count() - 1).setToolTip(kinds)

        self.preview_label.setText(
            "Circles: {}   |   Non-circular edges skipped: {}".format(len(clusters), skipped)
        )
        self.status.setText("Geometry captured. Review the detected circles, then Apply.")
        self._update_apply()

        if not clusters:
            QMessageBox.warning(
                self,
                "No circles",
                "No CIRCLE / ARC_CIRCLE edges were found in the selected geometry.",
            )

    def apply_changes(self):
        if not self.geom_objects:
            QMessageBox.warning(self, "No geometry", "Capture a geometry selection first.")
            return
        options = {
            "prefix": self.prefix.text().strip() or "HOLE",
            "tolerance": float(self.tolerance.value()),
            "add_center": self.add_center.isChecked(),
            "reuse_nodes": self.reuse_nodes.isChecked(),
            "make_0d": self.make_0d.isChecked(),
            "make_rbe2": self.make_rbe2.isChecked(),
            "publish_geom": self.publish_geom.isChecked(),
        }
        try:
            report = process_circles(
                self.smesh, self.mesh, self.geompy, self.geom_objects, options
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Circle node groups",
                "{}\n\nSee the SALOME Python console for the traceback.".format(exc),
            )
            traceback.print_exc()
            return

        try:
            self.sg.updateObjBrowser()
        except Exception:
            try:
                salome.sg.updateObjBrowser()
            except Exception:
                pass

        lines = [
            "Circles processed: {}".format(len(report["created"])),
            "Non-circular edges skipped: {}".format(report["skipped_edges"]),
        ]
        for item in report["created"]:
            extra = []
            if item.get("paired"):
                extra.append("{} arcs paired".format(item["arcs"]))
            if item.get("center_id"):
                extra.append(
                    "center node {}{}".format(
                        item["center_id"],
                        " (reused)" if item.get("center_reused") else "",
                    )
                )
            if item.get("mait"):
                extra.append("MAIT/ESCL")
            lines.append(
                "  {} : {} nodes{}".format(
                    item["name"],
                    item["nodes"],
                    "  [{}]".format(", ".join(extra)) if extra else "",
                )
            )
        self.status.setText("\n".join(lines))
        QMessageBox.information(self, "Circle node groups", "\n".join(lines))


# ---------------------------------------------------------------------------
# Plugin entry point
# ---------------------------------------------------------------------------

def CircleNodeGroups(context):
    try:
        selected = _get_selected_entries(context)
        mesh = None
        mesh_ref = None
        for entry in selected:
            sobj, obj = _object_from_entry(context.study, entry)
            if _is_top_mesh(obj):
                mesh_ref = obj
                break
        if mesh_ref is None:
            QMessageBox.warning(
                _desktop(context),
                "Circle node groups",
                "Select a top-level SMESH mesh in the Object Browser before launching "
                "the plugin.\n\nThe geometry group is captured afterwards from the dialog.",
            )
            return

        smesh = smeshBuilder.New()
        mesh = smesh.Mesh(mesh_ref)
        dialog = CircleNodeGroupsDialog(
            context=context,
            mesh=mesh,
            mesh_ref=mesh_ref,
            parent=_desktop(context),
        )
        _OPEN_DIALOGS.append(dialog)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
    except Exception as exc:
        QMessageBox.critical(
            _desktop(context),
            "Circle node groups",
            "{}\n\nSee the SALOME Python console for the traceback.".format(exc),
        )
        traceback.print_exc()
