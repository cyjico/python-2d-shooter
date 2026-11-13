import random

import pygame

from game.components.rigid_body import RigidBody
from game.components.spawner import Spawner
from game.components.transform import Transform
from game.constants.spawning import SPAWN_RETRY
from game.core_ecs.world import World


def spawner_system(world: World, dt: float):
    """Counts down each Spawner and spawns at a random unblocked spot."""
    for _, (spawner,) in world.query(Spawner):
        spawner.spawned = [e for e in spawner.spawned if world.is_alive(e)]

        spawner.timer -= dt
        if spawner.timer > 0:
            continue

        spawner.timer = random.uniform(*spawner.interval)
        if len(spawner.spawned) >= spawner.max_alive:
            continue

        free = _free_points(world, spawner)
        if not free:
            spawner.timer = SPAWN_RETRY
            continue

        spawner.spawned.append(spawner.spawn(world, random.choice(free)))


def _free_points(world: World, spawner: Spawner) -> list[pygame.Vector2]:
    """Spots with no physics body (player, enemies, crates) or earlier spawn nearby."""
    blockers = [t.position for _, (t, _) in world.query(Transform, RigidBody)]
    blockers += [
        world.get_component(e, Transform).position
        for e in spawner.spawned
        if world.has_component(e, Transform)
    ]

    return [
        point
        for point in spawner.points
        if all(point.distance_to(b) >= spawner.clearance for b in blockers)
    ]
