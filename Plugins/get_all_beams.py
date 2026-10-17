# -*- coding: utf-8 -*-
"""
Extract centerline EDGEs (beams) from selected 3D solids or compounds.

Used by the Get All Beams GEOM plugin (geom_get_all_beams.py).
"""

from __future__ import print_function

import math
import salome
import GEOM
from salome.geom import geomBuilder

salome.salome_init()
geompy = geomBuilder.New()
gg = salome.ImportComponentGUI("GEOM")


def _refresh_geom():
    global geompy, gg
    salome.salome_init()
    geompy = geomBuilder.New()
    try:
        gg = salome.ImportComponentGUI("GEOM")
    except Exception:
        gg = None
    return geompy


def _entry_to_geom(entry):
    if not entry:
        return None
    obj = None
    try:
        obj = salome.IDToObject(entry)
    except Exception:
        obj = None
    if obj is not None:
        return obj
    try:
        sobj = salome.myStudy.FindObjectID(str(entry))
        if sobj is not None:
            obj = sobj.GetObject()
    except Exception:
        obj = None
    return obj


def get_selected_geom_objects():
    entries = []
    try:
        all_sel = salome.sg.getAllSelected()
        if all_sel:
            entries = list(all_sel)
    except Exception:
        entries = []

    if not entries:
        try:
            n = salome.sg.SelectedCount()
        except Exception:
            n = 0
        for i in range(n):
            try:
                entries.append(salome.sg.getSelected(i))
            except Exception:
                pass

    objects = []
    seen = set()
    for entry in entries:
        if not entry or entry in seen:
            continue
        obj = _entry_to_geom(entry)
        if obj is None:
            print("  [warn] Could not resolve selection:", entry)
            continue
        seen.add(entry)
        objects.append(obj)
    return objects


def object_name(obj, fallback="Shape"):
    try:
        name = obj.GetName()
        if name:
            return name
    except Exception:
        pass
    return fallback


def _nb_shapes(shape, type_name):
    try:
        return geompy.NbShapes(shape, geompy.ShapeType[type_name])
    except Exception:
        return 0


def explode_beam_parts(shape):
    """
    ExtractShapes does not return the main shape if it already matches
    the requested type, so a single SOLID would yield [].
    """
    n_solid = _nb_shapes(shape, "SOLID")
    if n_solid > 1:
        parts = geompy.ExtractShapes(shape, geompy.ShapeType["SOLID"], False)
        if parts:
            return parts
    if n_solid == 1:
        parts = geompy.ExtractShapes(shape, geompy.ShapeType["SOLID"], False)
        return parts if parts else [shape]

    n_shell = _nb_shapes(shape, "SHELL")
    if n_shell > 1:
        parts = geompy.ExtractShapes(shape, geompy.ShapeType["SHELL"], False)
        if parts:
            return parts
    if n_shell == 1:
        parts = geompy.ExtractShapes(shape, geompy.ShapeType["SHELL"], False)
        return parts if parts else [shape]

    n_shape = _nb_shapes(shape, "SHAPE")
    if n_shape > 1:
        parts = geompy.ExtractShapes(shape, geompy.ShapeType["SHAPE"], False)
        if parts:
            return parts

    return [shape]


def _xyz(point):
    return geompy.PointCoordinates(point)


def _normalize(vec):
    x, y, z = vec
    n = math.sqrt(x * x + y * y + z * z)
    if n == 0:
        raise ValueError("Zero-length direction.")
    return (x / n, y / n, z / n)


def calc_axes_from_face(face, use_longest_edge=True):
    normal_vec = geompy.GetNormal(face)
    dx, dy, dz = geompy.VectorCoordinates(normal_vec)
    Lz = math.sqrt(dx * dx + dy * dy + dz * dz)
    z = (dx / Lz, dy / Lz, dz / Lz)

    edges = geompy.ExtractShapes(face, geompy.ShapeType["EDGE"], True)
    if not edges:
        raise RuntimeError("The local face has no EDGE.")
    edge = edges[0]
    if use_longest_edge:
        best_len = -1.0
        for e in edges:
            vtx = geompy.ExtractShapes(e, geompy.ShapeType["VERTEX"], True)
            if len(vtx) < 2:
                continue
            d = geompy.MinDistance(vtx[0], vtx[1])
            if d > best_len:
                best_len = d
                edge = e

    vtx = geompy.ExtractShapes(edge, geompy.ShapeType["VERTEX"], True)
    if len(vtx) < 2:
        raise RuntimeError("Could not get 2 VERTEX from the chosen EDGE.")
    A, B = vtx[0], vtx[1]
    Lx = geompy.MinDistance(A, B)
    xa, ya, za = geompy.PointCoordinates(A)
    xb, yb, zb = geompy.PointCoordinates(B)
    x = ((xb - xa) / Lx, (yb - ya) / Lx, (zb - za) / Lx)

    y = (
        z[1] * x[2] - z[2] * x[1],
        z[2] * x[0] - z[0] * x[2],
        z[0] * x[1] - z[1] * x[0],
    )
    Ly = math.sqrt(y[0] ** 2 + y[1] ** 2 + y[2] ** 2)
    y = (y[0] / Ly, y[1] / Ly, y[2] / Ly)

    x = (
        y[1] * z[2] - y[2] * z[1],
        y[2] * z[0] - y[0] * z[2],
        y[0] * z[1] - y[1] * z[0],
    )
    Lx = math.sqrt(x[0] ** 2 + x[1] ** 2 + x[2] ** 2)
    x = (x[0] / Lx, x[1] / Lx, x[2] / Lx)

    L = 200
    origin = geompy.MakeCDG(face)
    ox, oy, oz = geompy.PointCoordinates(origin)
    px = geompy.MakeVector(
        origin, geompy.MakeVertex(ox + L * x[0], oy + L * x[1], oz + L * x[2])
    )
    py = geompy.MakeVector(
        origin, geompy.MakeVertex(ox + L * y[0], oy + L * y[1], oz + L * y[2])
    )
    pz = geompy.MakeVector(
        origin, geompy.MakeVertex(ox + L * z[0], oy + L * z[1], oz + L * z[2])
    )
    return px, py, pz


def _axis_from_extruded_vertex_edge(edge):
    verts = geompy.ExtractShapes(edge, geompy.ShapeType["VERTEX"], True)
    if len(verts) < 2:
        raise ValueError("Could not get 2 vertices from the EDGE.")
    p0, p1 = verts[0], verts[1]
    axis = geompy.MakeLineTwoPnt(p0, p1)
    x0, y0, z0 = _xyz(p0)
    x1, y1, z1 = _xyz(p1)
    ux, uy, uz = _normalize((x1 - x0, y1 - y0, z1 - z0))
    return axis, (x0, y0, z0), (ux, uy, uz), p0, p1


def max_distance_along_extruded_edge(vertices, extruded_edge):
    if len(vertices) < 2:
        return 0.0, None, None, None, None, None
    axis, P0, u, p0, p1 = _axis_from_extruded_vertex_edge(extruded_edge)
    x0, y0, z0 = P0
    ux, uy, uz = u
    s_list = []
    for v in vertices:
        vp = geompy.MakeProjection(v, axis)
        xp, yp, zp = _xyz(vp)
        s = (xp - x0) * ux + (yp - y0) * uy + (zp - z0) * uz
        s_list.append((s, v, vp))
    smin, vmin, pmin = min(s_list, key=lambda t: t[0])
    smax, vmax, pmax = max(s_list, key=lambda t: t[0])
    dist = smax - smin
    return dist, vmin, vmax, pmin, pmax, axis


def pick_longitudinal_vector(Vertex_C, vertexs, props, px, py, pz):
    vectors = [px, py, pz]
    distances = []
    for vec in vectors:
        extr = geompy.MakePrismVecH2Ways(Vertex_C, vec, props[0])
        dist, vA, vB, pA, pB, axis = max_distance_along_extruded_edge(vertexs, extr)
        distances.append(dist)
    idx = distances.index(max(distances))
    return vectors[idx], distances


def beam_from_solid(solid):
    LocalCS_1 = geompy.MakeMarkerFromShape(solid)
    Face_1 = geompy.MakeFaceWires([LocalCS_1], 1)
    vertexs = geompy.ExtractShapes(solid, geompy.ShapeType["VERTEX"], True)
    if len(vertexs) < 2:
        raise RuntimeError("The solid does not have enough VERTEX.")
    Vertex_C = geompy.MakeVertexOnSurface(Face_1, 0.5, 0.5)
    props = geompy.BasicProperties(solid)
    px, py, pz = calc_axes_from_face(Face_1)
    long_vec, dists = pick_longitudinal_vector(Vertex_C, vertexs, props, px, py, pz)
    Extrusion_1 = geompy.MakePrismVecH2Ways(Vertex_C, long_vec, props[0])
    dist, vA, vB, pA, pB, axis = max_distance_along_extruded_edge(vertexs, Extrusion_1)
    if pA is None or pB is None:
        raise RuntimeError("Could not project the axis end points.")
    return geompy.MakeLineTwoPnt(pA, pB)


def _is_edge(shape):
    try:
        return shape.GetShapeType() == geompy.ShapeType["EDGE"]
    except Exception:
        return False


def extract_all_beams(
    publish=True,
    name="Beams",
    selected=None,
    on_progress=None,
    compound=True,
    publish_each=False,
):
    _refresh_geom()

    if selected is None:
        selected = get_selected_geom_objects()
    print("Selected objects:", len(selected))
    if not selected:
        raise RuntimeError(
            "No GEOM objects selected. "
            "Select cylinders, beams, or the compound that contains them "
            "(GEOM module active) and try again."
        )

    parts = []
    for obj in selected:
        parts.extend(explode_beam_parts(obj))
    print("Parts to process (solids/shells):", len(parts))

    list_edges = []
    errors = 0
    n_parts = len(parts)
    for i, part in enumerate(parts, start=1):
        if on_progress is not None:
            try:
                on_progress(i - 1, n_parts)
            except Exception:
                pass
        try:
            if _is_edge(part):
                list_edges.append(part)
                continue
            seg = beam_from_solid(part)
            list_edges.append(seg)
        except Exception as exc:
            errors += 1
            print("  [error] part %d: %s" % (i, exc))

    if on_progress is not None:
        try:
            on_progress(n_parts, n_parts)
        except Exception:
            pass

    print("Beams extracted:", len(list_edges), "| errors:", errors)
    if not list_edges:
        raise RuntimeError(
            "Empty beam list. If you selected a compound, "
            "check that it contains SOLIDs. If you selected several "
            "objects in the 3D viewer that are not published, select "
            "the parent compound in the Object Browser."
        )

    result_name = (name or "Beams").strip() or "Beams"
    Beams = list_edges[0] if len(list_edges) == 1 else geompy.MakeCompound(list_edges)

    if publish:
        if compound or not publish_each or len(list_edges) == 1:
            Beams_gui = geompy.addToStudy(Beams, result_name)
            if salome.sg.hasDesktop():
                try:
                    if gg is not None:
                        gg.createAndDisplayGO(Beams_gui)
                except Exception:
                    pass
        if publish_each and len(list_edges) > 1:
            for i, edge in enumerate(list_edges, start=1):
                try:
                    geompy.addToStudy(edge, "%s_%d" % (result_name, i))
                except Exception:
                    pass
        if salome.sg.hasDesktop():
            salome.sg.updateObjBrowser()

    return Beams, list_edges, errors
