import pygame

from game.components.convex_collider import ConvexCollider
from game.components.rigid_body import RigidBody
from game.components.transform import Transform
from game.core_ecs.entity import Entity
from game.core_ecs.world import World

BOUNCE_THRESHOLD = 20.0
"""Impacts slower than this (px/s) don't bounce, which stops resting contacts from jittering."""


def resolve_collision(
    world: World,
    a: tuple[Entity, Transform, ConvexCollider],
    b: tuple[Entity, Transform, ConvexCollider],
    normal: pygame.Vector2,
    depth: float,
):
    entity_a, transform_a, collider_a = a
    entity_b, transform_b, collider_b = b

    body_a = world.try_get_component(entity_a, RigidBody)
    body_b = world.try_get_component(entity_b, RigidBody)

    inv_a = body_a is not None and body_a.inverse_mass or 0.0
    inv_b = body_b is not None and body_b.inverse_mass or 0.0
    total = inv_a + inv_b

    if total == 0:
        return

    # Positional correction: heavier objects move less, static ones don't move.
    transform_a.position -= normal * depth * (inv_a / total)
    transform_b.position += normal * depth * (inv_b / total)

    # How fast B moves relative to A along the normal.
    approach_speed = (
        (body_b.linear_velocity if body_b and inv_b > 0 else pygame.Vector2())
        - (body_a.linear_velocity if body_a and inv_a > 0 else pygame.Vector2())
    ).dot(normal)

    # If `approach_speed` >= 0 then B is already separating.
    if approach_speed >= 0:
        return
    approach_speed = -approach_speed

    bounciness = max(collider_a.bounciness, collider_b.bounciness)
    if approach_speed < BOUNCE_THRESHOLD:
        bounciness = 0.0

    impulse = (1.0 + bounciness) * approach_speed / total

    if body_a is not None and inv_a > 0:
        body_a.apply_impulse(-normal * impulse * inv_a)

    if body_b is not None and inv_b > 0:
        body_b.apply_impulse(normal * impulse * inv_b)
