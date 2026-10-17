# -*- coding: utf-8 -*-
"""Unit tests for circular-edge pairing (no SALOME runtime required)."""

import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Plugins"))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from circle_pairing import cluster_circular_edges, same_circle


class PairingTests(unittest.TestCase):
    def test_pairs_two_semicircles(self):
        a = {"center": (0.0, 0.0, 0.0), "axis": (0.0, 0.0, 1.0), "radius": 10.0}
        b = {"center": (1.0e-9, 0.0, 0.0), "axis": (0.0, 0.0, -1.0), "radius": 10.0}
        self.assertTrue(same_circle(a, b, abs_tol=1.0e-6))

    def test_does_not_pair_different_centers(self):
        a = {"center": (0.0, 0.0, 0.0), "axis": (0.0, 0.0, 1.0), "radius": 10.0}
        b = {"center": (30.0, 0.0, 0.0), "axis": (0.0, 0.0, 1.0), "radius": 10.0}
        self.assertFalse(same_circle(a, b, abs_tol=1.0e-6))

    def test_does_not_pair_different_radii(self):
        a = {"center": (0.0, 0.0, 0.0), "axis": (0.0, 0.0, 1.0), "radius": 10.0}
        b = {"center": (0.0, 0.0, 0.0), "axis": (0.0, 0.0, 1.0), "radius": 12.0}
        self.assertFalse(same_circle(a, b, abs_tol=1.0e-6))

    def test_clusters_five_holes_from_ten_arcs(self):
        descriptors = []
        for i in range(5):
            cy = 20.0 * i
            descriptors.append(
                {"center": (0.0, cy, 0.0), "axis": (0.0, 0.0, 1.0), "radius": 5.0}
            )
            descriptors.append(
                {"center": (0.0, cy, 0.0), "axis": (0.0, 0.0, 1.0), "radius": 5.0}
            )
        clusters = cluster_circular_edges(descriptors, abs_tol=1.0e-6)
        self.assertEqual(len(clusters), 5)
        self.assertTrue(all(len(c) == 2 for c in clusters))

    def test_full_circle_stays_alone(self):
        descriptors = [
            {"center": (1.0, 2.0, 0.0), "axis": (0.0, 0.0, 1.0), "radius": 3.0},
            {"center": (10.0, 2.0, 0.0), "axis": (0.0, 0.0, 1.0), "radius": 3.0},
        ]
        clusters = cluster_circular_edges(descriptors, abs_tol=1.0e-6)
        self.assertEqual(len(clusters), 2)
        self.assertEqual([len(c) for c in clusters], [1, 1])

    def test_quarters_of_same_hole(self):
        descriptors = [
            {"center": (5.0, 5.0, 0.0), "axis": (0.0, 0.0, 1.0), "radius": 2.5}
            for _ in range(4)
        ]
        clusters = cluster_circular_edges(descriptors, abs_tol=1.0e-6)
        self.assertEqual(len(clusters), 1)
        self.assertEqual(len(clusters[0]), 4)


if __name__ == "__main__":
    unittest.main()
