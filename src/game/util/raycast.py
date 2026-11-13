import pygame

from game.components.transform import Transform
from game.core_ecs.world import World
from game.game import ConvexCollider, RigidBody
from game.util.geometry import get_aabb, segment_hits_aabb, segment_hits_polygon


def raycast_static_bundle(
    world: World,
    origin: pygame.Vector2,
    direction: pygame.Vector2,
    distance: float,
    half_span: float = 0.0,
):
    """True if a static collider (no RigidBody, same rule as the collision
    system) is within `distance` along `direction`.

    Casts three rays (centre and both edges of the body) so he doesn't clip corners.
    """
    side = pygame.Vector2(-direction.y, direction.x) * half_span
    tip = direction * distance

    segments = [
        (origin + offset, origin + offset + tip)
        for offset in (pygame.Vector2(), side, -side)
    ]

    for entity, (transform, collider) in world.query(Transform, ConvexCollider):
        if collider.is_trigger or world.has_component(entity, RigidBody):
            continue

        polygon = None

        for start, end in segments:
            if not segment_hits_aabb(origin, end, get_aabb(transform, collider.laabb)):
                continue

            if polygon is None:
                polygon = transform.apply_all(collider.vertices)

            if segment_hits_polygon(start, end, polygon):
                return True

    return False
