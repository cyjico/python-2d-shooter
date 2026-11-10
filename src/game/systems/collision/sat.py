import math
from collections.abc import Iterator, Sequence

import pygame


def _get_edge_normals(points: Sequence[pygame.Vector2]) -> Iterator[pygame.Vector2]:
    count = len(points)

    for i in range(count):
        edge = points[(i + 1) % count] - points[i]

        if edge.length_squared() == 0:
            continue

        yield pygame.Vector2(-edge.y, edge.x).normalize()


def _project_all(
    points: Sequence[pygame.Vector2], axis: pygame.Vector2
) -> tuple[float, float]:
    dots = [point.dot(axis) for point in points]
    return min(dots), max(dots)


def test_sat(
    points_a: Sequence[pygame.Vector2],
    centroid_a: pygame.Vector2,
    points_b: Sequence[pygame.Vector2],
    centroid_b: pygame.Vector2,
) -> tuple[pygame.Vector2, float] | None:
    """
    Separating Axis Theorem test between two convex polygons in world space.

    Returns `None` if they don't overlap. Otherwise returns `(normal, depth)`,
    where `normal` is a unit vector pointing from A toward B and `depth` is the
    minimum translation distance needed to separate them.
    """
    best_axis = pygame.Vector2()
    min_depth = math.inf

    for points in (points_a, points_b):
        for axis in _get_edge_normals(points):
            min_a, max_a = _project_all(points_a, axis)
            min_b, max_b = _project_all(points_b, axis)

            overlap = min(max_a, max_b) - max(min_a, min_b)

            # A single separating axis proves the shapes don't collide.
            if overlap <= 0:
                return None

            if overlap < min_depth:
                min_depth = overlap
                best_axis = axis

    # Degenerate shapes (no valid edges)
    if min_depth is math.inf:
        return None

    # Make sure the normal points from A to B.
    if (centroid_b - centroid_a).dot(best_axis) < 0:
        best_axis = -best_axis

    return best_axis, min_depth
