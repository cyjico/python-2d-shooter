import pygame


def find_contact_point(
    points_a: list[pygame.Vector2],
    points_b: list[pygame.Vector2],
    normal: pygame.Vector2,
    tolerance=1.0,
) -> pygame.Vector2:
    """Rough contact point: vertex that digs the deepest the into the other shape.

    `normal` points from A to B.
    """
    max_a = max(p.dot(normal) for p in points_a)
    deep_a = [p for p in points_a if p.dot(normal) >= max_a - tolerance]

    min_b = min(p.dot(normal) for p in points_b)
    deep_b = [p for p in points_b if p.dot(normal) <= min_b + tolerance]

    # A corner poking into a flat face has 1 deep vertex vs 2 on the face.
    # The corner is the real contact. If it's a tie, use both.
    # To illustrate, imagine a rotated square hitting a flat wall.
    if len(deep_a) < len(deep_b):
        points = deep_a
    elif len(deep_b) < len(deep_a):
        points = deep_b
    else:
        points = deep_a + deep_b

    return sum(points, pygame.Vector2()) / len(points)
