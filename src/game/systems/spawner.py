import random

from game.components.spawner import Spawner
from game.constants.spawning import SPAWN_RETRY
from game.core_ecs.world import World
from game.util.spawn_points import free_points


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

        free = free_points(
            world, spawner.points, spawner.clearance, also_avoid=spawner.spawned
        )
        if not free:
            spawner.timer = SPAWN_RETRY
            continue

        spawner.spawned.append(spawner.spawn(world, random.choice(free)))
