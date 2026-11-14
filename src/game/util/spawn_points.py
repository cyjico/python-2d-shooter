import random
from collections.abc import Collection, Iterable

import pygame

from game.components.relocatable import Relocatable
from game.components.rigid_body import RigidBody
from game.components.transform import Transform
from game.core_ecs.entity import Entity
from game.core_ecs.world import World

_default_rng = random.Random()


def free_points(
    world: World,
    points: Iterable[pygame.Vector2],
    clearance: float,
    ignore: Collection[Entity] = (),
    also_avoid: Iterable[Entity] = (),
):
    """Spots with no physics body within `clearance`.

    `also_avoid` adds entities to keep clear of even without a RigidBody
    (e.g. earlier spawns). `ignore` entities never block.
    """
    blockers = [
        t.position for e, (t, _) in world.query(Transform, RigidBody) if e not in ignore
    ]
    blockers += [
        world.get_component(e, Transform).position
        for e in also_avoid
        if e not in ignore and world.has_component(e, Transform)
    ]

    return [p for p in points if all(p.distance_to(b) >= clearance for b in blockers)]


def relocate(world: World, entity: Entity, rng: random.Random | None = None):
    """Move `entity` to a random free spot from its Relocatable.

    Returns False and stays put if no listed spot is free and far enough away.
    """
    relocatable = world.try_get_component(entity, Relocatable)
    if relocatable is None:
        return False

    transform = world.get_component(entity, Transform)
    old = pygame.Vector2(transform.position)
    candidates = [
        p
        for p in free_points(
            world, relocatable.points, relocatable.clearance, ignore=(entity,)
        )
        if p.distance_to(old) >= relocatable.min_distance
    ]
    if not candidates:
        return False

    transform.position = pygame.Vector2((rng or _default_rng).choice(candidates))
    return True
