import pygame

from game.components.convex_collider import ConvexCollider
from game.components.rigid_body import RigidBody
from game.components.transform import Transform
from game.core_ecs.entity import Entity
from game.core_ecs.world import World
from game.events.collision import CollisionEvent
from game.resources.event_bus import EventBus
from game.util.geometry import find_contact_point, get_aabb, solve_sat

BOUNCE_THRESHOLD = 20.0
"""Impacts slower than this (px/s) don't bounce, which stops resting contacts from jittering."""


def _center_of_mass(transform: Transform, body: RigidBody | None):
    if body is None:
        return pygame.Vector2(transform.position)

    return transform.apply(body.center_of_mass)


def _resolve_collision(
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

    inv_m_a = body_a.inverse_mass if body_a is not None else 0.0
    inv_m_b = body_b.inverse_mass if body_b is not None else 0.0
    total_inv_m = inv_m_a + inv_m_b

    if total_inv_m == 0:
        return

    contact = find_contact_point(
        transform_a.apply_all(collider_a.vertices),
        transform_b.apply_all(collider_b.vertices),
        normal,
    )

    # Lever arms are measured from each body's center of mass.
    lr_a = contact - _center_of_mass(transform_a, body_a)
    lr_b = contact - _center_of_mass(transform_b, body_b)

    # Positional correction.
    transform_a.position -= normal * depth * (inv_m_a / total_inv_m)
    transform_b.position += normal * depth * (inv_m_b / total_inv_m)

    # Relative velocity at the contact point.
    vel_a = body_a.velocity_at(lr_a) if body_a and inv_m_a > 0 else pygame.Vector2()
    vel_b = body_b.velocity_at(lr_b) if body_b and inv_m_b > 0 else pygame.Vector2()
    relative = vel_b - vel_a

    # approach being negative means B is going opposite of the normal.
    approach = relative.dot(normal)
    if approach >= 0:
        return

    bounciness = max(collider_a.bounciness, collider_b.bounciness)
    if -approach < BOUNCE_THRESHOLD:
        bounciness = 0.0

    inv_eff_a = (
        body_a.inverse_effective_resistance(lr_a, normal)
        if body_a and inv_m_a > 0
        else 0.0
    )
    inv_eff_b = (
        body_b.inverse_effective_resistance(lr_b, normal)
        if body_b and inv_m_b > 0
        else 0.0
    )

    j = (1.0 + bounciness) * -approach / (inv_eff_a + inv_eff_b)

    # Applied immediately so later contacts this frame see the updated velocity.
    if body_a is not None and inv_m_a > 0:
        body_a.apply_instant_impulse_at(lr_a, -normal * j)

    if body_b is not None and inv_m_b > 0:
        body_b.apply_instant_impulse_at(lr_b, normal * j)


def collision_system(world: World):
    events = world.get_resource(EventBus)

    bodies = list(world.query(Transform, ConvexCollider))

    for i in range(len(bodies)):
        for j in range(i + 1, len(bodies)):
            entity_a, (transform_a, collider_a) = bodies[i]
            entity_b, (transform_b, collider_b) = bodies[j]

            # Cheap AABB test because I will explode if I don't do this
            ax1, ay1, ax2, ay2 = get_aabb(transform_a, collider_a.laabb)
            bx1, by1, bx2, by2 = get_aabb(transform_b, collider_b.laabb)

            if ax2 < bx1 or bx2 < ax1 or ay2 < by1 or by2 < ay1:
                continue

            # Recompute because earlier resolutions may have moved things
            result = solve_sat(
                transform_a.apply_all(collider_a.vertices),
                transform_a.apply(collider_a.centroid),
                transform_b.apply_all(collider_b.vertices),
                transform_b.apply(collider_b.centroid),
            )

            if result is None:
                continue

            normal, depth = result
            events.emit(CollisionEvent(entity_a, entity_b, normal, depth))

            if collider_a.is_trigger or collider_b.is_trigger:
                continue

            _resolve_collision(
                world,
                (entity_a, transform_a, collider_a),
                (entity_b, transform_b, collider_b),
                normal,
                depth,
            )
