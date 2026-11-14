import math
from typing import Sequence

import pygame

from game.components.transform import Transform
from game.core_ecs.world import World


def get_aabb(
    transform: Transform,
    laabb: tuple[pygame.Vector2, pygame.Vector2],
):
    """Returns the axis-aligned bounding box based on the **local** axis-aligned
    bounding box.

    Args:
        transform (Transform): Transform to apply to the local axis-aligned bounding box.
        laabb (tuple[pygame.Vector2, pygame.Vector2]): Local axis-aligned bounding box to base on.

    Returns:
        tuple[float, float, float, float]: Values are as follows: min x, min y, max x, max y.
    """

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
        points_a (Sequence[pygame.Vector2]): Points of convex polygon A.
        centroid_a (pygame.Vector2): Centroid of convex polygon A.
        points_b (Sequence[pygame.Vector2]): Points of convex polygon B.
        centroid_b (pygame.Vector2): Centroid of convex polygon B.

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


def regular_polygon(sides: int, radius: float):
    """Vertices of a regular polygon centred on (0, 0).

    The first vertex points along +x, which is an entity's "forward".
    """
    return tuple(
        pygame.Vector2(math.cos(math.tau * i / sides), math.sin(math.tau * i / sides))
        * radius
        for i in range(sides)
    )


def segment_hits_polygon(
    start: pygame.Vector2, end: pygame.Vector2, polygon: list[pygame.Vector2]
):
    """Cyrus-Beck clipping: does the segment touch this convex polygon?"""
    delta = end - start

    # Winding sign, so every edge normal can be made to point outward.
    winding = sum(a.cross(b) for a, b in zip(polygon, polygon[1:] + polygon[:1]))
    sign = 1.0 if winding > 0 else -1.0

    t_in, t_out = 0.0, 1.0
    for i, a in enumerate(polygon):
        edge = polygon[(i + 1) % len(polygon)] - a
        normal = pygame.Vector2(edge.y, -edge.x) * sign

        dist = normal.dot(start - a)  # > 0 means outside this edge
        speed = normal.dot(delta)

        if speed == 0:
            if dist > 0:
                return False
            continue

        t = -dist / speed
        if speed < 0:
            t_in = max(t_in, t)
        else:
            t_out = min(t_out, t)

        if t_in > t_out:
            return False

    return True


def segment_hits_aabb(
    start: pygame.Vector2,
    end: pygame.Vector2,
    aabb: tuple[float, float, float, float],
):
    x1, y1, x2, y2 = aabb

    return not (
        max(start.x, end.x) < x1
        or min(start.x, end.x) > x2
        or max(start.y, end.y) < y1
        or min(start.y, end.y) > y2
    )


def angle_of(vec2: pygame.Vector2):
    return math.atan2(vec2.y, vec2.x)


def rot_to_vec2(rot: float):
    return pygame.Vector2(math.cos(rot), math.sin(rot))


def rectangle(width: float, height: float):
    """Four corners of a rectangle centred on (0, 0), clockwise."""
    half_w, half_h = width / 2, height / 2
    return (
        pygame.Vector2(-half_w, -half_h),
        pygame.Vector2(half_w, -half_h),
        pygame.Vector2(half_w, half_h),
        pygame.Vector2(-half_w, half_h),
    )
