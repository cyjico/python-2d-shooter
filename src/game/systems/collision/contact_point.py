import pygame


def find_contact_point(
    points_a: list[pygame.Vector2],
    points_b: list[pygame.Vector2],
    normal: pygame.Vector2,
    tolerance=1.0,
):
    """Approximate contact point between two overlapping convex polygons.

    `normal` points from A to B. Takes the vertices of each shape that lie
    within `tolerance` of the contact plane:
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
