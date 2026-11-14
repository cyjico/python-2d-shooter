import math
import random

from game.components.ai import AI
from game.components.rigid_body import RigidBody
from game.components.split_on_death import SplitOnDeath
from game.components.transform import Transform
from game.core_ecs.world import World
from game.events.combat import EntityDiedEvent
from game.resources.event_bus import EventBus
from game.util.geometry import rot_to_vec2
from game.util.rng import resolve_rng


def split_on_death_system(world: World, rng: random.Random | None = None):
    """Spawns the offspring of everything with SplitOnDeath that just died."""
    rng = resolve_rng(rng)

    for died in world.get_resource(EventBus).read(EntityDiedEvent):
        split = world.try_get_component(died.entity, SplitOnDeath)
        transform = world.try_get_component(died.entity, Transform)
        if split is None or transform is None:
            continue

        # Offspring inherit whoever the parent was chasing.
        ai = world.try_get_component(died.entity, AI)
        target = ai.target if ai is not None else None

        # Random start angle so the ring doesn't look stamped out.
        start = rng.uniform(0.0, math.tau)
        for i in range(split.count):
            direction = rot_to_vec2(start + math.tau * i / split.count)
            child = split.spawn(
                world, transform.position + direction * split.spread_distance, target
            )

            body = world.try_get_component(child, RigidBody)
            if body is not None:
                body.linear_velocity = direction * split.burst_speed
