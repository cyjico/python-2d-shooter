import math
from typing import Sequence

import pygame

from game.components.transform import Transform


def get_aabb(
    transform: Transform,
    laabb: tuple[pygame.Vector2, pygame.Vector2],
):
    """Returns the axis-aligned bounding box based on the **local** axis-aligned
    bounding box."""
    obb = transform.apply_all(
        [
            laabb[0],
            pygame.Vector2(laabb[1].x, laabb[0].y),
            laabb[1],
            pygame.Vector2(laabb[0].x, laabb[1].y),
        ]
    )

    return (
        min(p.x for p in obb),
        min(p.y for p in obb),
        max(p.x for p in obb),
        max(p.y for p in obb),
    )


def find_contact_point(
    points_a: list[pygame.Vector2],
    points_b: list[pygame.Vector2],
    normal: pygame.Vector2,
    tolerance=1.0,
):
    """Approximate contact point between two overlapping convex polygons.

    Args:
        points_a (list[pygame.Vector2]): Vertcies of convex polygon A.
        points_b (list[pygame.Vector2]): Vertices of convex polygon B.
        normal (pygame.Vector2): Points from A to B.
        tolerance (float, optional): Tolerance for the contact plane. Defaults to 1.0.

    Returns:
        pygame.Vector2: Vertices of each shape that lie within `tolerance` of the
        contact plane (normal):
        - Corner vs. corner: returns the midpoint of the two corners.
        - Corner vs. face: returns the corner vertex.
        - Face vs. face: returns the midpoint of the overlapping portion of the two
            faces, midway between them along `normal`.
    """
    max_a = max(p.dot(normal) for p in points_a)
    deep_a = [p for p in points_a if p.dot(normal) >= max_a - tolerance]

    min_b = min(p.dot(normal) for p in points_b)
    deep_b = [p for p in points_b if p.dot(normal) <= min_b + tolerance]

    # Corner vs corner
    if len(deep_a) == 1 and len(deep_b) == 1:
        return (deep_a[0] + deep_b[0]) / 2

    # Corner vs face
    if len(deep_a) == 1:
        return deep_a[0]
    if len(deep_b) == 1:
        return deep_b[0]

    # Face vs. face: use the part of each face that overlaps along the tangent.
    tangent = pygame.Vector2(-normal.y, normal.x)

    ta = [p.dot(tangent) for p in deep_a]
    tb = [p.dot(tangent) for p in deep_b]

    low = max(min(ta), min(tb))
    high = min(max(ta), max(tb))

    if low > high:
        # Faces don't overlap along the tangent (shouldn't happen mid-collision).
        points = deep_a + deep_b
        return sum(points, pygame.Vector2()) / len(points)

    along_normal = (
        sum(p.dot(normal) for p in deep_a) / len(deep_a)
        + sum(p.dot(normal) for p in deep_b) / len(deep_b)
    ) / 2

    return normal * along_normal + tangent * ((low + high) / 2)


def get_edge_normals(points: Sequence[pygame.Vector2]):
    count = len(points)

    for i in range(count):
        edge = points[(i + 1) % count] - points[i]

        if edge.length_squared() == 0:
            continue

        yield pygame.Vector2(-edge.y, edge.x).normalize()


def project_all(points: Sequence[pygame.Vector2], axis: pygame.Vector2):
    """Projects all points unto the axis.

    Args:
        points (Sequence[pygame.Vector2]): Points to project.
        axis (pygame.Vector2): Axis to project unto.

    Returns:
        tuple[float, float]: Minimum and maximum signed distance along the axis, respectively.
    """
    dots = [point.dot(axis) for point in points]
    return min(dots), max(dots)


def solve_sat(
    points_a: Sequence[pygame.Vector2],
    centroid_a: pygame.Vector2,
    points_b: Sequence[pygame.Vector2],
    centroid_b: pygame.Vector2,
):
    """Separating Axis Theorem test between two convex polygons in world space.

    Args:
        points_a (Sequence[pygame.Vector2]): _description_
        centroid_a (pygame.Vector2): _description_
        points_b (Sequence[pygame.Vector2]): _description_
        centroid_b (pygame.Vector2): _description_

    Returns:
        None: Returned if they don't overlap.
        tuple[Vector2, float]: `Vector2` is a unit vector pointing from A toward B and `float` is the minimum translation distance needed to separate them.
    """
    best_axis = pygame.Vector2()
    min_depth = math.inf

    for points in (points_a, points_b):
        for axis in get_edge_normals(points):
            min_a, max_a = project_all(points_a, axis)
            min_b, max_b = project_all(points_b, axis)

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
