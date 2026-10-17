# -*- coding: utf-8 -*-
"""Pair opposite faces of a thin solid for mid-surface extraction.

No SALOME / Qt imports: matching, scoring and thresholds are unit-tested
without a SALOME session. GEOM only supplies face descriptors and distances.
"""

from __future__ import print_function

import math


DEFAULT_T_MIN = 1.0e-4
DEFAULT_T_MAX_FRACTION = 0.10
OPPOSITE_DOT = -0.95
AXIS_DOT = 0.98
ALIGN_DOT = 0.85
SLENDERNESS_MAX = 0.30
RADIUS_GAP = 0.20
COAXIAL_FRACTION = 0.20

PLANAR_KINDS = frozenset(
    ("PLANE", "PLANAR", "POLYGON", "DISK_CIRCLE", "DISK_ELLIPSE")
)
CYLINDER_KINDS = frozenset(("CYLINDER2D", "CYLINDER"))
SPHERE_KINDS = frozenset(("SPHERE2D", "SPHERE"))
CONE_KINDS = frozenset(("CONE2D", "CONE"))
TORUS_KINDS = frozenset(("TORUS2D", "TORUS"))
CANONICAL_KINDS = CYLINDER_KINDS | SPHERE_KINDS | CONE_KINDS | TORUS_KINDS

KIND_LABEL = {
    "planar": "planar",
    "cylinder": "cylinder",
    "sphere": "sphere",
    "cone": "cone",
    "torus": "torus",
    "generic": "generic",
}


def vec_len(v):
    return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


def vec_dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def vec_sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vec_add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vec_scale(v, s):
    return (v[0] * s, v[1] * s, v[2] * s)


def vec_cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def normalize(v, default=(0.0, 0.0, 1.0)):
    n = vec_len(v)
    if n <= 1.0e-16:
        return default
    return (v[0] / n, v[1] / n, v[2] / n)


def kind_name(kind):
    text = str(kind)
    if "." in text:
        text = text.rsplit(".", 1)[-1]
    return text


def is_planar_kind(kind):
    return kind_name(kind) in PLANAR_KINDS


def is_cylinder_kind(kind):
    return kind_name(kind) in CYLINDER_KINDS


def is_sphere_kind(kind):
    return kind_name(kind) in SPHERE_KINDS


def is_cone_kind(kind):
    return kind_name(kind) in CONE_KINDS


def is_torus_kind(kind):
    return kind_name(kind) in TORUS_KINDS


def bbox_diagonal(xmin, xmax, ymin, ymax, zmin, zmax):
    dx = float(xmax) - float(xmin)
    dy = float(ymax) - float(ymin)
    dz = float(zmax) - float(zmin)
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def auto_t_max(diagonal, fraction=DEFAULT_T_MAX_FRACTION):
    diag = max(float(diagonal), 0.0)
    frac = float(fraction) if fraction is not None else DEFAULT_T_MAX_FRACTION
    return max(frac * diag, DEFAULT_T_MIN)


def _axis_of(face):
    axis = face.get("axis")
    if axis is None:
        axis = face.get("normal")
    return normalize(axis)


def _origin_of(face):
    origin = face.get("origin")
    if origin is None:
        origin = face.get("center")
    return origin


def _radius_of(face, key="radius"):
    value = face.get(key)
    if value is None:
        return None
    return float(value)


def line_line_distance(origin_a, axis_a, origin_b, axis_b):
    """Distance between two 3D lines (axes are unit vectors)."""
    d1 = normalize(axis_a)
    d2 = normalize(axis_b)
    w = vec_sub(origin_b, origin_a)
    cross = vec_cross(d1, d2)
    cl = vec_len(cross)
    if cl < 1.0e-8:
        return vec_len(vec_cross(w, d1))
    return abs(vec_dot(w, cross)) / cl


def classify_pair_kind(face_a, face_b):
    ka = kind_name(face_a.get("kind", "FACE"))
    kb = kind_name(face_b.get("kind", "FACE"))
    if is_planar_kind(ka) and is_planar_kind(kb):
        return "planar"
    if is_cylinder_kind(ka) and is_cylinder_kind(kb):
        return "cylinder"
    if is_sphere_kind(ka) and is_sphere_kind(kb):
        return "sphere"
    if is_cone_kind(ka) and is_cone_kind(kb):
        return "cone"
    if is_torus_kind(ka) and is_torus_kind(kb):
        return "torus"
    return "generic"


def opposite_quality(normal_a, normal_b):
    """1 when normals are opposite, 0 when they point the same way."""
    return 0.5 * (1.0 - vec_dot(normalize(normal_a), normalize(normal_b)))


def slenderness(thickness, area_a, area_b):
    span = math.sqrt(max(min(float(area_a), float(area_b)), 1.0e-16))
    return float(thickness) / span


def _radius_gap_ok(face_a, face_b, thickness, gap_tol):
    ra = _radius_of(face_a)
    rb = _radius_of(face_b)
    if ra is None or rb is None:
        return False
    expected = abs(ra - rb)
    return abs(expected - float(thickness)) <= gap_tol * max(float(thickness), 1.0e-12)


def _coaxial_ok(face_a, face_b, thickness):
    axis_a = _axis_of(face_a)
    axis_b = _axis_of(face_b)
    if abs(vec_dot(axis_a, axis_b)) < AXIS_DOT:
        return False
    dist = line_line_distance(_origin_of(face_a), axis_a, _origin_of(face_b), axis_b)
    scale = max(
        float(thickness),
        abs((_radius_of(face_a) or 0.0) - (_radius_of(face_b) or 0.0)),
        1.0e-9,
    )
    return dist <= COAXIAL_FRACTION * scale + 1.0e-9


def _concentric_ok(face_a, face_b, thickness):
    delta = vec_len(vec_sub(_origin_of(face_a), _origin_of(face_b)))
    scale = max(float(thickness), 1.0e-9)
    return delta <= COAXIAL_FRACTION * scale + 1.0e-9


def pair_compatible(
    face_a,
    face_b,
    thickness,
    t_min=DEFAULT_T_MIN,
    t_max=None,
    opposite_dot=OPPOSITE_DOT,
    slenderness_max=SLENDERNESS_MAX,
    radius_gap=RADIUS_GAP,
    check_slenderness=True,
    check_t_max=True,
):
    """Return (ok, reason, kind) for an unordered face pair."""
    t = float(thickness)
    if t < float(t_min):
        return False, "below t_min", None

    if check_t_max:
        if t_max is None:
            return False, "t_max missing", None
        if t > float(t_max) + 1.0e-15:
            return False, "above t_max", None

    if check_slenderness:
        slim = slenderness(t, face_a["area"], face_b["area"])
        if slim > float(slenderness_max) + 1.0e-15:
            return False, "not slender", None

    kind = classify_pair_kind(face_a, face_b)
    na = normalize(face_a["normal"])
    nb = normalize(face_b["normal"])
    center_dir = normalize(vec_sub(face_b["center"], face_a["center"]))
    aligned = (
        abs(vec_dot(na, center_dir)) >= ALIGN_DOT
        or abs(vec_dot(nb, center_dir)) >= ALIGN_DOT
    )
    parallel = abs(vec_dot(na, nb)) >= abs(float(opposite_dot))

    if kind == "planar":
        # STEP/OCCT plane axes often point the same way on both skins.
        # Parallel + separation along the normal is enough; do not require
        # outward normals to be opposite.
        if not parallel:
            return False, "not parallel", kind
        if not aligned:
            return False, "not facing", kind
        return True, "ok", kind

    if kind in ("cylinder", "cone", "torus"):
        if not _coaxial_ok(face_a, face_b, t):
            return False, "not coaxial", kind
        if not _radius_gap_ok(face_a, face_b, t, radius_gap):
            return False, "radius gap mismatch", kind
        return True, "ok", kind

    if kind == "sphere":
        if not _concentric_ok(face_a, face_b, t):
            return False, "not concentric", kind
        if not _radius_gap_ok(face_a, face_b, t, radius_gap):
            return False, "radius gap mismatch", kind
        return True, "ok", kind

    if (parallel and aligned) or vec_dot(na, nb) <= float(opposite_dot):
        return True, "ok", kind
    return False, "faces do not face each other", kind


def score_pair(face_a, face_b, thickness, t_max):
    area_term = math.sqrt(max(float(face_a["area"]), 0.0) * max(float(face_b["area"]), 0.0))
    quality = opposite_quality(face_a["normal"], face_b["normal"])
    tmax = max(float(t_max), 1.0e-12)
    return area_term * max(quality, 0.05) / (1.0 + float(thickness) / tmax)


def source_face_index(face_a, face_b, index_a, index_b):
    """Prefer the larger face so the mid-surface keeps its contour."""
    if float(face_a["area"]) >= float(face_b["area"]):
        return index_a
    return index_b


def greedy_match(
    faces,
    distance_fn,
    t_min=DEFAULT_T_MIN,
    t_max=None,
    opposite_dot=OPPOSITE_DOT,
    slenderness_max=SLENDERNESS_MAX,
    radius_gap=RADIUS_GAP,
):
    """Greedy one-to-one matching of opposite thin-solid faces.

    `distance_fn(i, j)` must return the gap between faces i and j.
    Each face is used in at most one pair.
    """
    if t_max is None:
        raise ValueError("t_max is required for automatic pairing")

    candidates = []
    n_faces = len(faces)
    for i in range(n_faces):
        for j in range(i + 1, n_faces):
            thickness = float(distance_fn(i, j))
            ok, reason, kind = pair_compatible(
                faces[i],
                faces[j],
                thickness,
                t_min=t_min,
                t_max=t_max,
                opposite_dot=opposite_dot,
                slenderness_max=slenderness_max,
                radius_gap=radius_gap,
            )
            if not ok:
                continue
            candidates.append(
                {
                    "i": i,
                    "j": j,
                    "t": thickness,
                    "kind": kind,
                    "reason": reason,
                    "score": score_pair(faces[i], faces[j], thickness, t_max),
                    "source": source_face_index(faces[i], faces[j], i, j),
                    "status": "ok",
                    "forced": False,
                }
            )

    candidates.sort(key=lambda item: (-item["score"], item["i"], item["j"]))
    used = set()
    pairs = []
    for item in candidates:
        if item["i"] in used or item["j"] in used:
            continue
        used.add(item["i"])
        used.add(item["j"])
        pairs.append(item)
    pairs.sort(key=lambda item: (item["i"], item["j"]))
    return pairs


def forced_pair(face_a, face_b, thickness, t_min=DEFAULT_T_MIN):
    """Build a pair from two user-picked faces, ignoring t_max / slenderness."""
    t = float(thickness)
    if t < float(t_min):
        return None, "thickness is below t_min ({:g})".format(t_min)
    kind = classify_pair_kind(face_a, face_b)
    return (
        {
            "i": 0,
            "j": 1,
            "t": t,
            "kind": kind,
            "reason": "forced",
            "score": score_pair(face_a, face_b, t, max(t, 1.0)),
            "source": source_face_index(face_a, face_b, 0, 1),
            "status": "ok",
            "forced": True,
        },
        None,
    )
