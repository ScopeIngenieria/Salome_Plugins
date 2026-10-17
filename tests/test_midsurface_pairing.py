# -*- coding: utf-8 -*-
"""Unit tests for thin-solid face pairing (no SALOME runtime required)."""

import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Plugins"))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from midsurface_pairing import (
    auto_t_max,
    bbox_diagonal,
    forced_pair,
    greedy_match,
    pair_compatible,
    source_face_index,
)


def _face(kind, area, normal, center, **extra):
    data = {
        "kind": kind,
        "area": area,
        "normal": normal,
        "center": center,
        "origin": extra.pop("origin", center),
        "axis": extra.pop("axis", normal),
        "radius": extra.pop("radius", None),
        "radius2": extra.pop("radius2", None),
    }
    data.update(extra)
    return data


def _dist_map(pairs):
    table = {}
    for i, j, value in pairs:
        table[(min(i, j), max(i, j))] = value

    def distance_fn(i, j):
        return table.get((min(i, j), max(i, j)), 0.0)

    return distance_fn


class ThresholdTests(unittest.TestCase):
    def test_auto_t_max_is_ten_percent_of_diagonal(self):
        diag = bbox_diagonal(0.0, 100.0, 0.0, 100.0, 0.0, 5.0)
        self.assertAlmostEqual(diag, (100.0 ** 2 + 100.0 ** 2 + 25.0) ** 0.5)
        self.assertAlmostEqual(auto_t_max(diag), 0.10 * diag)


class PlateTests(unittest.TestCase):
    def setUp(self):
        self.faces = [
            _face("PLANAR", 10000.0, (0.0, 0.0, 1.0), (50.0, 50.0, 5.0)),
            _face("PLANAR", 10000.0, (0.0, 0.0, -1.0), (50.0, 50.0, 0.0)),
            _face("PLANAR", 500.0, (1.0, 0.0, 0.0), (100.0, 50.0, 2.5)),
            _face("PLANAR", 500.0, (-1.0, 0.0, 0.0), (0.0, 50.0, 2.5)),
            _face("PLANAR", 500.0, (0.0, 1.0, 0.0), (50.0, 100.0, 2.5)),
            _face("PLANAR", 500.0, (0.0, -1.0, 0.0), (50.0, 0.0, 2.5)),
        ]
        self.dist = _dist_map(
            (
                (0, 1, 5.0),
                (2, 3, 100.0),
                (4, 5, 100.0),
            )
        )
        self.t_max = auto_t_max(bbox_diagonal(0.0, 100.0, 0.0, 100.0, 0.0, 5.0))

    def test_pairs_only_the_thin_skins(self):
        pairs = greedy_match(self.faces, self.dist, t_max=self.t_max)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(sorted((pairs[0]["i"], pairs[0]["j"])), [0, 1])
        self.assertEqual(pairs[0]["kind"], "planar")
        self.assertAlmostEqual(pairs[0]["t"], 5.0)

    def test_adjacent_faces_are_rejected(self):
        ok, reason, _kind = pair_compatible(
            self.faces[0], self.faces[2], 0.0, t_max=self.t_max
        )
        self.assertFalse(ok)
        self.assertEqual(reason, "below t_min")

    def test_same_direction_plane_axes_still_pair(self):
        top = _face("PLANAR", 10000.0, (0.0, 0.0, 1.0), (50.0, 50.0, 5.0))
        bottom = _face("PLANAR", 10000.0, (0.0, 0.0, 1.0), (50.0, 50.0, 0.0))
        ok, reason, kind = pair_compatible(top, bottom, 5.0, t_max=self.t_max)
        self.assertTrue(ok, reason)
        self.assertEqual(kind, "planar")

    def test_perpendicular_planes_do_not_pair(self):
        base = _face("PLANAR", 10000.0, (0.0, 0.0, 1.0), (50.0, 50.0, 0.0))
        wall = _face("PLANAR", 10000.0, (1.0, 0.0, 0.0), (0.0, 50.0, 50.0))
        ok, reason, kind = pair_compatible(base, wall, 5.0, t_max=self.t_max)
        self.assertFalse(ok)
        self.assertEqual(kind, "planar")
        self.assertEqual(reason, "not parallel")


class TeeTests(unittest.TestCase):
    def test_two_independent_walls(self):
        faces = [
            _face("PLANAR", 3200.0, (0.0, 0.0, 1.0), (40.0, 20.0, 24.0)),
            _face("PLANAR", 3200.0, (0.0, 0.0, -1.0), (40.0, 20.0, 20.0)),
            _face("PLANAR", 1600.0, (0.0, -1.0, 0.0), (40.0, 18.0, 10.0)),
            _face("PLANAR", 1600.0, (0.0, 1.0, 0.0), (40.0, 22.0, 10.0)),
        ]
        dist = _dist_map(((0, 1, 4.0), (2, 3, 4.0)))
        t_max = auto_t_max(bbox_diagonal(0.0, 80.0, 0.0, 40.0, 0.0, 24.0))
        pairs = greedy_match(faces, dist, t_max=t_max)
        matched = sorted(tuple(sorted((p["i"], p["j"]))) for p in pairs)
        self.assertEqual(matched, [(0, 1), (2, 3)])


class CubeTests(unittest.TestCase):
    def test_solid_cube_has_no_pairs(self):
        faces = [
            _face("PLANAR", 100.0, (0.0, 0.0, 1.0), (5.0, 5.0, 10.0)),
            _face("PLANAR", 100.0, (0.0, 0.0, -1.0), (5.0, 5.0, 0.0)),
            _face("PLANAR", 100.0, (1.0, 0.0, 0.0), (10.0, 5.0, 5.0)),
            _face("PLANAR", 100.0, (-1.0, 0.0, 0.0), (0.0, 5.0, 5.0)),
            _face("PLANAR", 100.0, (0.0, 1.0, 0.0), (5.0, 10.0, 5.0)),
            _face("PLANAR", 100.0, (0.0, -1.0, 0.0), (5.0, 0.0, 5.0)),
        ]
        dist = _dist_map(((0, 1, 10.0), (2, 3, 10.0), (4, 5, 10.0)))
        t_max = auto_t_max(bbox_diagonal(0.0, 10.0, 0.0, 10.0, 0.0, 10.0))
        pairs = greedy_match(faces, dist, t_max=t_max)
        self.assertEqual(pairs, [])


class CylinderTests(unittest.TestCase):
    def test_coaxial_tube_pairs_inner_and_outer(self):
        outer = _face(
            "CYLINDER2D",
            2.0 * 3.1416 * 12.0 * 50.0,
            (1.0, 0.0, 0.0),
            (12.0, 0.0, 25.0),
            axis=(0.0, 0.0, 1.0),
            origin=(0.0, 0.0, 0.0),
            radius=12.0,
            height=50.0,
        )
        inner = _face(
            "CYLINDER2D",
            2.0 * 3.1416 * 10.0 * 50.0,
            (-1.0, 0.0, 0.0),
            (10.0, 0.0, 25.0),
            axis=(0.0, 0.0, 1.0),
            origin=(0.0, 0.0, 0.0),
            radius=10.0,
            height=50.0,
        )
        pairs = greedy_match([outer, inner], lambda i, j: 2.0, t_max=5.0)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0]["kind"], "cylinder")
        self.assertEqual(source_face_index(outer, inner, 0, 1), 0)

    def test_skew_cylinders_are_not_paired(self):
        a = _face(
            "CYLINDER2D",
            100.0,
            (1.0, 0.0, 0.0),
            (5.0, 0.0, 0.0),
            axis=(0.0, 0.0, 1.0),
            origin=(0.0, 0.0, 0.0),
            radius=5.0,
        )
        b = _face(
            "CYLINDER2D",
            80.0,
            (-1.0, 0.0, 0.0),
            (30.0, 4.0, 0.0),
            axis=(0.0, 1.0, 0.0),
            origin=(30.0, 0.0, 0.0),
            radius=4.0,
        )
        ok, reason, kind = pair_compatible(a, b, 1.0, t_max=5.0)
        self.assertFalse(ok)
        self.assertEqual(kind, "cylinder")
        self.assertEqual(reason, "not coaxial")


class GreedyTests(unittest.TestCase):
    def test_each_face_used_once(self):
        faces = [
            _face("PLANAR", 400.0, (0.0, 0.0, 1.0), (0.0, 0.0, 2.0)),
            _face("PLANAR", 400.0, (0.0, 0.0, -1.0), (0.0, 0.0, 0.0)),
            _face("PLANAR", 100.0, (0.0, 0.0, -1.0), (0.0, 0.0, 0.2)),
        ]
        dist = _dist_map(((0, 1, 2.0), (0, 2, 1.8)))
        pairs = greedy_match(faces, dist, t_max=5.0)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(sorted((pairs[0]["i"], pairs[0]["j"])), [0, 1])


class ForcedPairTests(unittest.TestCase):
    def test_ignores_t_max(self):
        a = _face("PLANAR", 100.0, (0.0, 0.0, 1.0), (0.0, 0.0, 40.0))
        b = _face("PLANAR", 100.0, (0.0, 0.0, -1.0), (0.0, 0.0, 0.0))
        pair, error = forced_pair(a, b, 40.0)
        self.assertIsNone(error)
        self.assertEqual(pair["kind"], "planar")
        self.assertTrue(pair["forced"])

    def test_rejects_zero_gap(self):
        a = _face("PLANAR", 100.0, (0.0, 0.0, 1.0), (0.0, 0.0, 0.0))
        b = _face("PLANAR", 100.0, (0.0, 0.0, -1.0), (0.0, 0.0, 0.0))
        pair, error = forced_pair(a, b, 0.0)
        self.assertIsNone(pair)
        self.assertIn("t_min", error)


if __name__ == "__main__":
    unittest.main()
