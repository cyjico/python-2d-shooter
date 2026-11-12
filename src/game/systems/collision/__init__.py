import pygame

from game.components.convex_collider import ConvexCollider
from game.components.rigid_body import RigidBody
from game.components.transform import Transform
from game.core_ecs.entity import Entity
from game.core_ecs.world import World
from game.events.collision import CollisionEvent
from game.resources.event_bus import EventBus

from .aabb import get_aabb
from .resolve_collision import resolve_collision
from .sat import test_sat


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
            result = test_sat(
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

            resolve_collision(
                world,
                (entity_a, transform_a, collider_a),
                (entity_b, transform_b, collider_b),
                normal,
                depth,
            )


__all__ = ["collision_system"]
