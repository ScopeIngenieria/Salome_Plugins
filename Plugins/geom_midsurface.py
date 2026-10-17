# -*- coding: utf-8 -*-
# Extract mid surfaces from thin solids by pairing opposite faces.
# Autor: Lucio Gomez (psicofil@gmail.com)
# Creation Date: 01/09/2026

from __future__ import print_function

import math
import os
import sys
import time
import traceback

_PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
if _PLUGIN_DIR not in sys.path:
    sys.path.insert(0, _PLUGIN_DIR)

import salome
from salome.geom import geomBuilder

from midsurface_pairing import (
    DEFAULT_T_MAX_FRACTION,
    DEFAULT_T_MIN,
    auto_t_max,
    bbox_diagonal,
    forced_pair,
    greedy_match,
    is_cone_kind,
    is_cylinder_kind,
    is_planar_kind,
    is_torus_kind,
    kind_name,
    normalize,
    vec_dot,
    vec_len,
    vec_scale,
    vec_sub,
)

try:
    from qtsalome import (
        QApplication,
        QButtonGroup,
        QCheckBox,
        QDialog,
        QDoubleSpinBox,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QMessageBox,
        QProgressBar,
        QPushButton,
        QRadioButton,
        QVBoxLayout,
        Qt,
    )
except ImportError:
    try:
        from PyQt5.QtCore import Qt
        from PyQt5.QtWidgets import (
            QApplication,
            QButtonGroup,
            QCheckBox,
            QDialog,
            QDoubleSpinBox,
            QFormLayout,
            QGroupBox,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QListWidget,
            QListWidgetItem,
            QMessageBox,
            QProgressBar,
            QPushButton,
            QRadioButton,
            QVBoxLayout,
        )
    except ImportError:
        from PySide2.QtCore import Qt
        from PySide2.QtWidgets import (
            QApplication,
            QButtonGroup,
            QCheckBox,
            QDialog,
            QDoubleSpinBox,
            QFormLayout,
            QGroupBox,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QListWidget,
            QListWidgetItem,
            QMessageBox,
            QProgressBar,
            QPushButton,
            QRadioButton,
            QVBoxLayout,
        )

try:
    import SalomePyQt
except ImportError:
    SalomePyQt = None

try:
    import SALOMEDS
except ImportError:
    SALOMEDS = None


_OPEN_DIALOGS = []
_MID_COLOR = (0, 170, 0)
_MIN_AREA_FRACTION = 0.01


# ---------------------------------------------------------------------------
# Selection helpers
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
    raise RuntimeError("Unable to read the current SALOME Object Browser selection.")


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


def _object_from_entry(study, entry):
    sobj = study.FindObjectID(entry)
    if sobj is None:
        return None, None
    try:
        return sobj, sobj.GetObject()
    except Exception:
        return sobj, None


def _shape_type(obj):
    try:
        return str(obj.GetShapeType())
    except Exception:
        return ""


def _object_name(obj, fallback="Shape"):
    try:
        name = obj.GetName()
        if name:
            return name
    except Exception:
        pass
    return fallback


def _update_browser(sg):
    for api in (sg, getattr(salome, "sg", None)):
        if api is None:
            continue
        try:
            api.updateObjBrowser()
            return
        except Exception:
            pass


def _set_green(obj):
    if obj is None or SALOMEDS is None:
        return
    try:
        obj.SetColor(
            SALOMEDS.Color(_MID_COLOR[0] / 255.0, _MID_COLOR[1] / 255.0, _MID_COLOR[2] / 255.0)
        )
    except Exception:
        pass


# ---------------------------------------------------------------------------
# GEOM: descriptors, clipping, generation
# ---------------------------------------------------------------------------

def _bbox_center(geompy, shape):
    box = geompy.BoundingBox(shape)
    return (
        0.5 * (float(box[0]) + float(box[1])),
        0.5 * (float(box[2]) + float(box[3])),
        0.5 * (float(box[4]) + float(box[5])),
    )


def _bbox_diag(geompy, shape):
    box = geompy.BoundingBox(shape)
    return bbox_diagonal(box[0], box[1], box[2], box[3], box[4], box[5])


def _shape_area(geompy, shape):
    if shape is None:
        return 0.0
    try:
        return float(geompy.BasicProperties(shape)[1])
    except Exception:
        return 0.0


def _vector_xyz(geompy, vector_obj):
    coords = geompy.VectorCoordinates(vector_obj)
    return (float(coords[0]), float(coords[1]), float(coords[2]))


def _face_normal(geompy, face):
    vector = geompy.GetNormal(face)
    return normalize(_vector_xyz(geompy, vector))


def _parse_kind_info(info):
    kind = kind_name(info[0]) if info else "FACE"
    nums = []
    for value in info[1:]:
        try:
            nums.append(float(value))
        except Exception:
            continue
    data = {
        "kind": kind,
        "origin": None,
        "axis": None,
        "radius": None,
        "radius2": None,
        "r1": None,
        "r2": None,
        "height": None,
    }
    if kind in ("PLANE", "PLANAR", "POLYGON", "DISK_CIRCLE", "DISK_ELLIPSE") and len(nums) >= 6:
        data["origin"] = (nums[0], nums[1], nums[2])
        data["axis"] = normalize((nums[3], nums[4], nums[5]))
        if kind == "DISK_CIRCLE" and len(nums) >= 7:
            data["radius"] = nums[6]
        if kind == "DISK_ELLIPSE" and len(nums) >= 8:
            data["radius"] = nums[6]
            data["radius2"] = nums[7]
    elif kind in ("CYLINDER2D", "CYLINDER") and len(nums) >= 7:
        data["origin"] = (nums[0], nums[1], nums[2])
        data["axis"] = normalize((nums[3], nums[4], nums[5]))
        data["radius"] = nums[6]
        if len(nums) >= 8:
            data["height"] = nums[7]
    elif kind in ("SPHERE2D", "SPHERE") and len(nums) >= 4:
        data["origin"] = (nums[0], nums[1], nums[2])
        data["radius"] = nums[3]
    elif kind in ("CONE2D", "CONE") and len(nums) >= 8:
        data["origin"] = (nums[0], nums[1], nums[2])
        data["axis"] = normalize((nums[3], nums[4], nums[5]))
        data["r1"] = nums[6]
        data["r2"] = nums[7]
        data["radius"] = 0.5 * (nums[6] + nums[7])
        data["radius2"] = nums[7]
        if len(nums) >= 9:
            data["height"] = nums[8]
    elif kind in ("TORUS2D", "TORUS") and len(nums) >= 8:
        data["origin"] = (nums[0], nums[1], nums[2])
        data["axis"] = normalize((nums[3], nums[4], nums[5]))
        data["radius2"] = nums[6]
        data["radius"] = nums[7]
        data["r1"] = nums[6]
        data["r2"] = nums[7]
    return data


def _radial_normal(origin, axis, point):
    axis = normalize(axis)
    offset = vec_sub(point, origin)
    radial = vec_sub(offset, vec_scale(axis, vec_dot(offset, axis)))
    if vec_len(radial) <= 1.0e-16:
        return axis
    return normalize(radial)


def build_face_descriptor(geompy, face):
    info = geompy.KindOfShape(face)
    parsed = _parse_kind_info(info)
    center = _bbox_center(geompy, face)
    kind = parsed["kind"]
    if is_planar_kind(kind) and parsed["axis"] is not None:
        normal = parsed["axis"]
    elif (
        (is_cylinder_kind(kind) or is_cone_kind(kind) or is_torus_kind(kind))
        and parsed["axis"] is not None
    ):
        normal = _radial_normal(parsed["origin"] or center, parsed["axis"], center)
    else:
        try:
            normal = _face_normal(geompy, face)
        except Exception:
            normal = parsed["axis"] or (0.0, 0.0, 1.0)
    return {
        "kind": kind,
        "area": _shape_area(geompy, face),
        "normal": normal,
        "center": center,
        "origin": parsed["origin"] or center,
        "axis": parsed["axis"] or normal,
        "radius": parsed["radius"],
        "radius2": parsed["radius2"],
        "r1": parsed["r1"],
        "r2": parsed["r2"],
        "height": parsed["height"],
        "face": face,
    }


def extract_solids(geompy, obj):
    shape_type = _shape_type(obj)
    if shape_type == "SOLID":
        return [obj]
    solids = geompy.ExtractShapes(obj, geompy.ShapeType["SOLID"], True) or []
    return list(solids)


def extract_faces(geompy, obj):
    shape_type = _shape_type(obj)
    if shape_type == "FACE":
        return [obj]
    faces = geompy.ExtractShapes(obj, geompy.ShapeType["FACE"], True) or []
    return list(faces)


def _is_volume(obj):
    return _shape_type(obj) in ("SOLID", "COMPSOLID")


def _main_solid(geompy, face, fallback=None):
    candidates = []
    for getter in (getattr(face, "GetMainShape", None),):
        if getter is None:
            continue
        try:
            main = getter()
            if main is not None:
                candidates.append(main)
        except Exception:
            pass
    try:
        main = geompy.GetMainShape(face)
        if main is not None:
            candidates.append(main)
    except Exception:
        pass
    if fallback is not None:
        candidates.append(fallback)
    for candidate in candidates:
        if _is_volume(candidate):
            return candidate
        solids = extract_solids(geompy, candidate)
        if solids:
            return solids[0]
    return None


def _closest_dir(geompy, face_a, face_b, center_a, center_b):
    try:
        nb, coords = geompy.ClosestPoints(face_a, face_b)
        if coords and len(coords) >= 6:
            pa = (float(coords[0]), float(coords[1]), float(coords[2]))
            pb = (float(coords[3]), float(coords[4]), float(coords[5]))
            return vec_sub(pb, pa)
    except Exception:
        pass
    return vec_sub(center_b, center_a)


def offset_sign(geompy, src, dst, src_desc, dst_desc):
    direction = _closest_dir(
        geompy, src, dst, src_desc["center"], dst_desc["center"]
    )
    if vec_dot(src_desc["normal"], direction) >= 0.0:
        return 1.0
    return -1.0


def _faces_of_kind(geompy, shape, kinds):
    faces = extract_faces(geompy, shape)
    matched = []
    for face in faces:
        try:
            kind = kind_name(geompy.KindOfShape(face)[0])
        except Exception:
            kind = ""
        if kind in kinds:
            matched.append(face)
    return matched or faces


def _biggest_face(geompy, faces):
    best = None
    best_area = -1.0
    for face in faces:
        area = _shape_area(geompy, face)
        if area > best_area:
            best = face
            best_area = area
    return best


def _normalize_result(geompy, shape, min_area):
    if shape is None:
        return None
    shape_type = _shape_type(shape)
    if shape_type == "FACE":
        return shape if _shape_area(geompy, shape) >= min_area else None
    faces = [
        face
        for face in extract_faces(geompy, shape)
        if _shape_area(geompy, face) >= min_area
    ]
    if not faces:
        return None
    if len(faces) == 1:
        return faces[0]
    try:
        fused = geompy.MakeFuseList(faces, True)
        if _shape_area(geompy, fused) >= min_area:
            return fused
    except Exception:
        pass
    try:
        return geompy.MakeCompound(faces)
    except Exception:
        return faces[0]


def _clip(geompy, solid, surface, min_area):
    """Clip with a real solid when possible; keep the raw face if Common is empty.

    MakeCommon(solid, interior-face) often returns nothing in OCCT, and exploded
    FACE compounds are not volumes. The translated/offset face is still valid.
    """
    if surface is None:
        return None
    unclipped = _normalize_result(geompy, surface, min_area)
    if not _is_volume(solid):
        return unclipped
    try:
        common = geompy.MakeCommon(solid, surface)
    except Exception:
        return unclipped
    clipped = _normalize_result(geompy, common, min_area)
    if clipped is not None:
        return clipped
    return unclipped


def _try_offset(geompy, solid, face, distance, min_area):
    for maker in (geompy.MakeOffset, geompy.MakeOffsetIntersectionJoin):
        try:
            offset = maker(face, distance)
        except Exception:
            continue
        clipped = _clip(geompy, solid, offset, min_area)
        if clipped is not None:
            return clipped
    return None


def _try_translate_toward(geompy, solid, src_face, dst_face, src_desc, dst_desc, distance, min_area):
    direction = normalize(
        _closest_dir(geompy, src_face, dst_face, src_desc["center"], dst_desc["center"])
    )
    if vec_len(direction) <= 1.0e-16:
        return None
    try:
        axis = geompy.MakeVectorDXDYDZ(direction[0], direction[1], direction[2])
        moved = geompy.MakeTranslationVectorDistance(src_face, axis, distance)
    except Exception:
        return None
    return _clip(geompy, solid, moved, min_area)


def _try_translate(geompy, solid, face, normal, distance, min_area):
    try:
        axis = geompy.MakeVectorDXDYDZ(normal[0], normal[1], normal[2])
        moved = geompy.MakeTranslationVectorDistance(face, axis, distance)
    except Exception:
        return None
    return _clip(geompy, solid, moved, min_area)


def _mid_radius(desc_a, desc_b, key="radius"):
    ra = desc_a.get(key)
    rb = desc_b.get(key)
    if ra is None or rb is None:
        return None
    return 0.5 * (float(ra) + float(rb))


def _try_primitive(geompy, solid, desc_a, desc_b, kind, min_area):
    src = desc_a if float(desc_a["area"]) >= float(desc_b["area"]) else desc_b
    origin = src.get("origin") or src["center"]
    axis = src.get("axis") or src["normal"]
    height = src.get("height")
    if not height:
        height = max(_bbox_diag(geompy, solid) if solid is not None else 1.0, 1.0)
    height = 1.2 * float(height)

    shape = None
    kinds = set()
    try:
        if kind == "cylinder":
            radius = _mid_radius(desc_a, desc_b)
            if radius is None:
                return None
            pnt = geompy.MakeVertex(origin[0], origin[1], origin[2])
            vec = geompy.MakeVectorDXDYDZ(axis[0], axis[1], axis[2])
            shape = geompy.MakeCylinder(pnt, vec, radius, height)
            kinds = {"CYLINDER2D", "CYLINDER"}
        elif kind == "sphere":
            radius = _mid_radius(desc_a, desc_b)
            if radius is None:
                return None
            center = desc_a.get("origin") or desc_a["center"]
            shape = geompy.MakeSphere(center[0], center[1], center[2], radius)
            kinds = {"SPHERE2D", "SPHERE"}
        elif kind == "cone":
            r1 = _mid_radius(desc_a, desc_b, "r1")
            r2 = _mid_radius(desc_a, desc_b, "r2")
            if r1 is None or r2 is None:
                return None
            pnt = geompy.MakeVertex(origin[0], origin[1], origin[2])
            vec = geompy.MakeVectorDXDYDZ(axis[0], axis[1], axis[2])
            h = src.get("height") or height
            shape = geompy.MakeCone(pnt, vec, r1, r2, float(h))
            kinds = {"CONE2D", "CONE"}
        elif kind == "torus":
            r_major = _mid_radius(desc_a, desc_b, "r1") or _mid_radius(desc_a, desc_b, "radius2")
            r_minor = _mid_radius(desc_a, desc_b, "r2") or _mid_radius(desc_a, desc_b, "radius")
            if r_major is None or r_minor is None:
                return None
            pnt = geompy.MakeVertex(origin[0], origin[1], origin[2])
            vec = geompy.MakeVectorDXDYDZ(axis[0], axis[1], axis[2])
            shape = geompy.MakeTorus(pnt, vec, r_major, r_minor)
            kinds = {"TORUS2D", "TORUS"}
        else:
            return None
    except Exception:
        return None

    face = _biggest_face(geompy, _faces_of_kind(geompy, shape, kinds))
    return _clip(geompy, solid, face, min_area)


def generate_pair(geompy, solid, desc_a, desc_b, thickness, kind):
    """Return (shape, method) or (None, 'failed')."""
    if float(desc_a["area"]) >= float(desc_b["area"]):
        src, dst = desc_a, desc_b
    else:
        src, dst = desc_b, desc_a
    min_area = _MIN_AREA_FRACTION * min(float(desc_a["area"]), float(desc_b["area"]))
    min_area = max(min_area, 1.0e-12)
    sign = offset_sign(geompy, src["face"], dst["face"], src, dst)
    half = 0.5 * float(thickness)

    if kind == "planar":
        for src_try, dst_try in ((src, dst), (dst, src)):
            result = _try_translate_toward(
                geompy,
                solid,
                src_try["face"],
                dst_try["face"],
                src_try,
                dst_try,
                half,
                min_area,
            )
            if result is not None:
                return result, "translate"

    for current_sign in (sign, -sign):
        result = _try_offset(geompy, solid, src["face"], current_sign * half, min_area)
        if result is not None:
            return result, "offset"
    for current_sign in (sign, -sign):
        result = _try_offset(geompy, solid, dst["face"], -current_sign * half, min_area)
        if result is not None:
            return result, "offset"

    if kind == "planar":
        for current_sign in (sign, -sign):
            result = _try_translate(
                geompy, solid, src["face"], src["normal"], current_sign * half, min_area
            )
            if result is not None:
                return result, "translate"

    if kind in ("cylinder", "sphere", "cone", "torus"):
        result = _try_primitive(geompy, solid, desc_a, desc_b, kind, min_area)
        if result is not None:
            return result, "primitive"

    return None, "failed"


def _aabb_separation(box_a, box_b):
    """Minimum distance between two axis-aligned bounding boxes."""
    dx = max(0.0, float(box_a[0]) - float(box_b[1]), float(box_b[0]) - float(box_a[1]))
    dy = max(0.0, float(box_a[2]) - float(box_b[3]), float(box_b[2]) - float(box_a[3]))
    dz = max(0.0, float(box_a[4]) - float(box_b[5]), float(box_b[4]) - float(box_a[5]))
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def detect_pairs(geompy, objects, t_min, t_max_user, progress=None):
    """Return a list of pair dicts ready for generation / the preview list."""

    def report(percent, message):
        if progress is not None:
            progress(percent, message)

    work = []
    for obj in objects:
        parent_name = _object_name(obj, "Shape")
        for solid in extract_solids(geompy, obj):
            work.append((parent_name, solid))
    if not work:
        return []

    pairs = []
    n_solids = len(work)
    for solid_index, (parent_name, solid) in enumerate(work):
        base = 100.0 * solid_index / float(n_solids)
        span = 100.0 / float(n_solids)
        report(
            base + 0.02 * span,
            "Please wait. Extracting faces ({}/{})...".format(solid_index + 1, n_solids),
        )
        label = _object_name(solid, "") or parent_name
        faces = extract_faces(geompy, solid)
        n_faces = len(faces)
        if n_faces < 2:
            continue

        descriptors = []
        boxes = []
        for face_index, face in enumerate(faces):
            descriptors.append(build_face_descriptor(geompy, face))
            try:
                boxes.append(geompy.BoundingBox(face))
            except Exception:
                boxes.append((0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
            if face_index % 4 == 0 or face_index + 1 == n_faces:
                local = 5.0 + 25.0 * (face_index + 1) / float(n_faces)
                report(
                    base + span * local / 100.0,
                    "Please wait. Reading face {} / {} ...".format(face_index + 1, n_faces),
                )

        if t_max_user > 0.0:
            t_max = float(t_max_user)
        else:
            t_max = auto_t_max(_bbox_diag(geompy, solid), DEFAULT_T_MAX_FRACTION)

        n_cmp = n_faces * (n_faces - 1) // 2
        done = 0
        cache = {}
        for i in range(n_faces):
            for j in range(i + 1, n_faces):
                sep = _aabb_separation(boxes[i], boxes[j])
                if sep > t_max:
                    cache[(i, j)] = sep
                else:
                    cache[(i, j)] = float(geompy.MinDistance(faces[i], faces[j]))
                done += 1
                if done % 8 == 0 or done == n_cmp:
                    local = 30.0 + 60.0 * done / float(max(n_cmp, 1))
                    report(
                        base + span * local / 100.0,
                        "Please wait. Comparing faces {} / {} ...".format(done, n_cmp),
                    )

        report(
            base + 0.95 * span,
            "Please wait. Pairing opposite faces ({}/{})...".format(solid_index + 1, n_solids),
        )

        def distance_fn(i, j, _cache=cache):
            return _cache[(min(i, j), max(i, j))]

        found = greedy_match(descriptors, distance_fn, t_min=t_min, t_max=t_max)
        for item in found:
            item["solid"] = solid
            item["solid_name"] = label
            item["parent_name"] = parent_name
            item["desc_a"] = descriptors[item["i"]]
            item["desc_b"] = descriptors[item["j"]]
            item["t_max"] = t_max
            pairs.append(item)
    return pairs


def detect_manual_pair(geompy, objects, t_min):
    faces = []
    for obj in objects:
        faces.extend(extract_faces(geompy, obj))
    if len(faces) != 2:
        raise RuntimeError(
            "Manual mode needs exactly two faces (got {}).".format(len(faces))
        )
    desc_a = build_face_descriptor(geompy, faces[0])
    desc_b = build_face_descriptor(geompy, faces[1])
    thickness = float(geompy.MinDistance(faces[0], faces[1]))
    pair, error = forced_pair(desc_a, desc_b, thickness, t_min=t_min)
    if pair is None:
        raise RuntimeError(error)
    solid = _main_solid(geompy, faces[0]) or _main_solid(geompy, faces[1])
    pair["solid"] = solid
    pair["solid_name"] = _object_name(solid, _object_name(objects[0], "Manual"))
    pair["parent_name"] = pair["solid_name"]
    pair["desc_a"] = desc_a
    pair["desc_b"] = desc_b
    pair["t_max"] = thickness
    return [pair]


def _collect_faces(geompy, shape):
    if shape is None:
        return []
    if _shape_type(shape) == "FACE":
        return [shape]
    return [face for face in extract_faces(geompy, shape) if _shape_area(geompy, face) > 0.0]


def _surface_name(index, thickness):
    return "S{:02d}_t_{:.2f}".format(index, float(thickness))


def _assign_surface_names(pairs):
    for index, pair in enumerate(pairs, start=1):
        pair["surface_name"] = _surface_name(index, pair.get("t") or 0.0)
    return pairs


def publish_results(geompy, items, parent_name, publish_individual, glue):
    published = []
    if not items:
        return published
    faces = [face for face, _thickness in items]
    result = faces[0] if len(faces) == 1 else geompy.MakeCompound(faces)
    if glue and len(faces) > 1:
        try:
            result = geompy.MakeGlueFaces(faces, 1.0e-6, True)
        except Exception:
            pass
    geompy.addToStudy(result, parent_name)
    _set_green(result)
    children = _collect_faces(geompy, result)
    if len(children) != len(items):
        children = faces
    if publish_individual or len(items) > 1:
        for index, face in enumerate(children, start=1):
            thickness = items[min(index, len(items)) - 1][1]
            child_name = _surface_name(index, thickness)
            named = False
            try:
                geompy.addToStudyInFather(result, face, child_name)
                named = True
            except Exception:
                try:
                    geompy.addToStudy(face, child_name)
                    named = True
                except Exception:
                    try:
                        face.SetName(child_name)
                        named = True
                    except Exception:
                        pass
            _set_green(face)
            if named:
                published.append(child_name)
    if not published:
        if len(items) == 1:
            single_name = _surface_name(1, items[0][1])
            try:
                result.SetName(single_name)
            except Exception:
                pass
            published.append(single_name)
        else:
            published.append(parent_name)
    return published


def generate_selected_pairs(geompy, pairs, publish_individual, glue, progress=None):
    items = []
    failed = []
    parent_name = "MidSurface"
    n_pairs = max(len(pairs), 1)
    for index, pair in enumerate(pairs, start=1):
        if progress is not None:
            progress(
                int(5.0 + 90.0 * index / n_pairs),
                "Please wait. Creating mid surface {} / {} ...".format(index, n_pairs),
            )
        shape, method = generate_pair(
            geompy,
            pair.get("solid"),
            pair["desc_a"],
            pair["desc_b"],
            pair["t"],
            pair["kind"],
        )
        pair["method"] = method
        if shape is None:
            pair["status"] = "failed"
            failed.append(pair)
            continue
        pair["status"] = "ok"
        if not items:
            parent_name = "{}_M".format(
                pair.get("parent_name") or pair.get("solid_name") or "MidSurface"
            )
        thickness = float(pair.get("t") or 0.0)
        for face in _collect_faces(geompy, shape) or [shape]:
            items.append((face, thickness))

    published = publish_results(
        geompy, items, parent_name, publish_individual, glue
    )
    return {
        "ok": len(items),
        "failed": len(failed),
        "published": published,
        "failed_pairs": failed,
    }


# ---------------------------------------------------------------------------
# Dialog
# ---------------------------------------------------------------------------

class MidSurfaceDialog(QDialog):
    def __init__(self, context, parent=None):
        super(MidSurfaceDialog, self).__init__(parent)
        self.context = context
        self.study = context.study
        self.sg = context.sg
        self.geompy = geomBuilder.New(self.study)
        self.objects = []
        self.pairs = []
        self.setWindowTitle("Mid surface (SXX_t_yy.yy)")
        self.setModal(False)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.resize(560, 640)
        self._build_ui()
        self._connect()

    def _build_ui(self):
        main = QVBoxLayout(self)

        geom_box = QGroupBox("Geometry")
        geom_layout = QVBoxLayout(geom_box)
        self.capture_button = QPushButton("Load selected")
        geom_layout.addWidget(self.capture_button)
        self.selection_list = QListWidget()
        self.selection_list.setMinimumHeight(70)
        geom_layout.addWidget(self.selection_list)

        mode_row = QHBoxLayout()
        self.radio_auto = QRadioButton("Auto (solids / compounds)")
        self.radio_auto.setChecked(True)
        self.radio_manual = QRadioButton("Manual (two faces)")
        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.radio_auto)
        self.mode_group.addButton(self.radio_manual)
        mode_row.addWidget(self.radio_auto)
        mode_row.addWidget(self.radio_manual)
        geom_layout.addLayout(mode_row)
        main.addWidget(geom_box)

        opt_box = QGroupBox("Thickness")
        opt_form = QFormLayout(opt_box)
        self.t_max = QDoubleSpinBox()
        self.t_max.setDecimals(6)
        self.t_max.setRange(0.0, 1.0e9)
        self.t_max.setValue(0.0)
        self.t_max.setSingleStep(0.1)
        opt_form.addRow("Max thickness (0 = auto):", self.t_max)
        self.t_min = QDoubleSpinBox()
        self.t_min.setDecimals(8)
        self.t_min.setRange(0.0, 1.0e6)
        self.t_min.setValue(DEFAULT_T_MIN)
        self.t_min.setSingleStep(1.0e-4)
        opt_form.addRow("Min thickness:", self.t_min)
        self.publish_faces = QCheckBox("Publish individual faces")
        self.publish_faces.setChecked(True)
        opt_form.addRow(self.publish_faces)
        self.glue_faces = QCheckBox("Glue coincident faces")
        self.glue_faces.setChecked(False)
        opt_form.addRow(self.glue_faces)
        main.addWidget(opt_box)

        pair_box = QGroupBox("Pairs")
        pair_layout = QVBoxLayout(pair_box)
        self.preview_list = QListWidget()
        self.preview_list.setMinimumHeight(160)
        pair_layout.addWidget(self.preview_list)
        self.preview_label = QLabel("Load geometry, then Detect.")
        self.preview_label.setWordWrap(True)
        pair_layout.addWidget(self.preview_label)
        main.addWidget(pair_box)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setFormat("%p%")
        main.addWidget(self.progress)

        self.status = QLabel("")
        self.status.setWordWrap(True)
        main.addWidget(self.status)

        buttons = QHBoxLayout()
        self.detect_button = QPushButton("Detect")
        self.apply_button = QPushButton("Apply")
        self.close_button = QPushButton("Close")
        buttons.addWidget(self.detect_button)
        buttons.addStretch(1)
        buttons.addWidget(self.apply_button)
        buttons.addWidget(self.close_button)
        main.addLayout(buttons)

    def _connect(self):
        self.capture_button.clicked.connect(self.capture_geometry)
        self.detect_button.clicked.connect(self.detect_pairs_clicked)
        self.apply_button.clicked.connect(self.apply_changes)
        self.close_button.clicked.connect(self.close)
        self.radio_auto.toggled.connect(self._clear_pairs)
        self.radio_manual.toggled.connect(self._clear_pairs)
        self._last_ui = 0.0
        self._busy_cursor = False

    def _busy_widgets(self):
        return (
            self.capture_button,
            self.detect_button,
            self.apply_button,
            self.radio_auto,
            self.radio_manual,
            self.t_max,
            self.t_min,
            self.publish_faces,
            self.glue_faces,
        )

    def _set_busy(self, busy):
        for widget in self._busy_widgets():
            widget.setEnabled(not busy)
        if busy:
            if not self._busy_cursor:
                QApplication.setOverrideCursor(Qt.WaitCursor)
                self._busy_cursor = True
        elif self._busy_cursor:
            QApplication.restoreOverrideCursor()
            self._busy_cursor = False
        QApplication.processEvents()

    def _report_progress(self, percent, message=""):
        self.progress.setValue(max(0, min(100, int(percent))))
        if message:
            self.status.setText(message)
        now = time.time()
        if now - self._last_ui >= 0.05:
            self._last_ui = now
            QApplication.processEvents()

    def closeEvent(self, event):
        try:
            if self._busy_cursor:
                QApplication.restoreOverrideCursor()
                self._busy_cursor = False
            if self in _OPEN_DIALOGS:
                _OPEN_DIALOGS.remove(self)
        finally:
            super(MidSurfaceDialog, self).closeEvent(event)

    def _clear_pairs(self, _checked=False):
        self.pairs = []
        self.preview_list.clear()
        self.preview_label.setText("Load geometry, then Detect.")

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
                "Select a solid, compound, or two faces in the Object Browser.",
            )
            return

        objects = []
        names = []
        for entry in entries:
            sobj, obj = _object_from_entry(self.study, entry)
            label = sobj.GetName() if sobj is not None else str(entry)
            if not _is_geom_object(obj):
                continue
            objects.append(obj)
            names.append("{}   [{}]".format(label, _shape_type(obj)))

        if not objects:
            QMessageBox.warning(
                self, "Geometry selection", "The current selection contains no GEOM object."
            )
            return

        self.objects = objects
        self.selection_list.clear()
        for name in names:
            self.selection_list.addItem(name)
        self.status.setText("Geometry loaded. Starting detection...")
        QApplication.processEvents()
        self.detect_pairs_clicked()

    def _fill_preview(self):
        self.preview_list.clear()
        _assign_surface_names(self.pairs)
        for index, pair in enumerate(self.pairs):
            text = "{} | {} | F{}-F{} | {} | {} | {}".format(
                pair.get("surface_name", _surface_name(index + 1, pair.get("t") or 0.0)),
                pair.get("parent_name") or pair.get("solid_name", "?"),
                pair["i"] + 1,
                pair["j"] + 1,
                pair.get("kind", "?"),
                pair.get("method") or "-",
                pair.get("status", "ok"),
            )
            item = QListWidgetItem(text)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            item.setData(Qt.UserRole, index)
            self.preview_list.addItem(item)
        self.preview_label.setText("Pairs: {}".format(len(self.pairs)))

    def detect_pairs_clicked(self):
        if not self.objects:
            QMessageBox.warning(self, "No geometry", "Load a selection first.")
            return
        self._set_busy(True)
        self.progress.setValue(0)
        self.status.setText(
            "Please wait. Detection can take a few minutes on complex solids..."
        )
        QApplication.processEvents()
        try:
            if self.radio_manual.isChecked():
                self._report_progress(30, "Please wait. Measuring the selected faces...")
                self.pairs = detect_manual_pair(
                    self.geompy, self.objects, float(self.t_min.value())
                )
            else:
                self.pairs = detect_pairs(
                    self.geompy,
                    self.objects,
                    float(self.t_min.value()),
                    float(self.t_max.value()),
                    progress=self._report_progress,
                )
            self._report_progress(100, "Please wait. Updating the pair list...")
            self._fill_preview()
        except Exception as exc:
            self.progress.setValue(0)
            self.status.setText("Detection failed.")
            QMessageBox.critical(
                self,
                "Mid surface",
                "{}\n\nSee the SALOME Python console for the traceback.".format(exc),
            )
            traceback.print_exc()
            return
        finally:
            self._set_busy(False)
        if not self.pairs:
            self.progress.setValue(0)
            self.status.setText("No thin face pairs were found. Try Manual mode or raise Max thickness.")
            QMessageBox.warning(
                self,
                "Mid surface",
                "No opposite face pairs were found.\n\n"
                "Check that the selection contains thin solids, or pick two faces in Manual mode.",
            )
        else:
            self.progress.setValue(100)
            self.status.setText(
                "Detection finished. {} pair(s) found. Review them, then Apply.".format(
                    len(self.pairs)
                )
            )

    def _checked_pairs(self):
        selected = []
        for row in range(self.preview_list.count()):
            item = self.preview_list.item(row)
            if item.checkState() != Qt.Checked:
                continue
            try:
                index = int(item.data(Qt.UserRole))
            except Exception:
                continue
            if index < 0 or index >= len(self.pairs):
                continue
            selected.append(self.pairs[index])
        return selected

    def apply_changes(self):
        chosen = self._checked_pairs()
        if not chosen:
            QMessageBox.warning(self, "Mid surface", "Detect pairs and keep at least one checked.")
            return
        self._set_busy(True)
        self.progress.setValue(0)
        self.status.setText("Please wait. Creating mid surfaces...")
        QApplication.processEvents()
        try:
            report = generate_selected_pairs(
                self.geompy,
                chosen,
                self.publish_faces.isChecked(),
                self.glue_faces.isChecked(),
                progress=self._report_progress,
            )
            self._report_progress(100, "Please wait. Publishing results...")
            _update_browser(self.sg)
            self._fill_preview()
        except Exception as exc:
            self.progress.setValue(0)
            QMessageBox.critical(
                self,
                "Mid surface",
                "{}\n\nSee the SALOME Python console for the traceback.".format(exc),
            )
            traceback.print_exc()
            return
        finally:
            self._set_busy(False)
        lines = [
            "Mid faces created: {}".format(report["ok"]),
            "Pairs failed: {}".format(report["failed"]),
        ]
        if report["published"]:
            names = report["published"]
            if len(names) > 20:
                lines.append(
                    "Published: {} ... ({} surfaces)".format(
                        ", ".join(names[:15]), len(names)
                    )
                )
            else:
                lines.append("Published: {}".format(", ".join(names)))
        for pair in report["failed_pairs"]:
            lines.append(
                "  {} F{}-F{} ({}) failed".format(
                    pair.get("solid_name", "?"),
                    pair["i"] + 1,
                    pair["j"] + 1,
                    pair.get("kind", "?"),
                )
            )
        self.status.setText("\n".join(lines))
        self.progress.setValue(100)
        if report["ok"] <= 0:
            QMessageBox.warning(self, "Mid surface", "\n".join(lines))
        else:
            QMessageBox.information(self, "Mid surface", "\n".join(lines))


def MidSurface(context):
    try:
        dialog = MidSurfaceDialog(context=context, parent=_desktop(context))
        _OPEN_DIALOGS.append(dialog)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
    except Exception as exc:
        QMessageBox.critical(
            _desktop(context),
            "Mid surface",
            "{}\n\nSee the SALOME Python console for the traceback.".format(exc),
        )
        traceback.print_exc()
