import pygame

from game.components.transform import Transform


def get_aabb(
    transform: Transform,
    laabb: tuple[pygame.Vector2, pygame.Vector2],
):
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
