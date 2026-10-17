# -*- coding: utf-8 -*-
"""Pure geometry helpers for pairing circular hole edges.

No SALOME / Qt imports: these functions are unit-tested without a SALOME session.
"""

from __future__ import print_function

import math

TWO_PI = 2.0 * math.pi


def vec_len(v):
    return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


def vec_dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def vec_sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def normalize(v, default=(0.0, 0.0, 1.0)):
    n = vec_len(v)
    if n <= 1.0e-16:
        return default
    return (v[0] / n, v[1] / n, v[2] / n)


def linear_tolerance(radius, abs_tol, rel_tol):
    return max(float(abs_tol), float(rel_tol) * max(float(radius), 1.0e-12))


def same_circle(a, b, abs_tol, rel_tol=1.0e-6, ang_tol=1.0e-6):
    """Return True if two circular-edge descriptors belong to the same circle."""
    lin = linear_tolerance(max(a["radius"], b["radius"]), abs_tol, rel_tol)
    if abs(a["radius"] - b["radius"]) > lin:
        return False
    if vec_len(vec_sub(a["center"], b["center"])) > lin:
        return False
    n1 = normalize(a["axis"])
    n2 = normalize(b["axis"])
    return abs(abs(vec_dot(n1, n2)) - 1.0) <= max(ang_tol, 1.0e-8)


def cluster_circular_edges(descriptors, abs_tol, rel_tol=1.0e-6):
    """Group circular edges that share center, radius and plane."""
    clusters = []
    used = [False] * len(descriptors)
    for i, item in enumerate(descriptors):
        if used[i]:
            continue
        cluster = [item]
        used[i] = True
        for j in range(i + 1, len(descriptors)):
            if used[j]:
                continue
            if same_circle(item, descriptors[j], abs_tol, rel_tol):
                cluster.append(descriptors[j])
                used[j] = True
        clusters.append(cluster)
    clusters.sort(
        key=lambda c: (
            round(c[0]["center"][1], 8),
            round(c[0]["center"][0], 8),
            round(c[0]["center"][2], 8),
            round(c[0]["radius"], 8),
        )
    )
    return clusters


def mean_center(cluster):
    n = float(len(cluster))
    return (
        sum(item["center"][0] for item in cluster) / n,
        sum(item["center"][1] for item in cluster) / n,
        sum(item["center"][2] for item in cluster) / n,
    )


def mean_axis(cluster):
    ref = normalize(cluster[0]["axis"])
    acc = [0.0, 0.0, 0.0]
    for item in cluster:
        axis = normalize(item["axis"])
        if vec_dot(axis, ref) < 0.0:
            axis = (-axis[0], -axis[1], -axis[2])
        acc[0] += axis[0]
        acc[1] += axis[1]
        acc[2] += axis[2]
    return normalize(tuple(acc), ref)


def mean_radius(cluster):
    return sum(item["radius"] for item in cluster) / float(len(cluster))
