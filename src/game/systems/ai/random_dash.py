import random

from game.components.ai import AI
from game.components.ai.random_dash import RandomDashAI
from game.components.dash import Dash, DashIntent
from game.components.transform import Transform
from game.core_ecs.world import World
from game.systems.ai.util import random_open_direction
from game.util.rng import resolve_rng


def random_dash_ai_system(world: World, dt: float, rng: random.Random | None = None):
    """Requests dashes for RandomDashAI. Run after the movement AIs, before dash_system."""
    rng = resolve_rng(rng)

    for ent, (dasher,) in world.query(RandomDashAI):
        ai = world.get_component(ent, AI)
        dash = world.get_component(ent, Dash)
        intent = world.get_component(ent, DashIntent)
        transform = world.get_component(ent, Transform)

        if ai.target is None:
            continue

        dasher.timer = max(0.0, dasher.timer - dt)
        if dasher.timer > 0 or not dash.ready:
            continue
        dasher.timer = rng.uniform(*dasher.interval)

        if rng.random() > dasher.chance:
            continue

        target_pos = world.get_component(ai.target, Transform).position
        if (
            transform.position.distance_squared_to(target_pos)
            > dasher.max_target_dist_sqr
        ):
            continue

        direction = random_open_direction(
            world, ai, transform.position, dash.distance + ai.body_radius, rng
        )
        if direction is None:
            continue

        intent.requested = True
        intent.direction = direction
