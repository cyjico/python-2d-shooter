import math
import random

from game.components.ai import AI
from game.components.ai.random_dash import RandomDashAI
from game.components.dash import Dash, DashIntent
from game.components.shape import Shape
from game.components.transform import Transform
from game.core_ecs.world import World
from game.systems.ai.util import open_direction_near
from game.util.geometry import angle_of, distance_to_segment
from game.util.rng import resolve_rng


def random_dash_ai_system(world: World, dt: float, rng: random.Random | None = None):
    """Requests dashes for RandomDashAI."""
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

        target_transform = world.get_component(ai.target, Transform)
        target_pos = target_transform.position
        toward = target_pos - transform.position
        dist_sqr = toward.length_squared()
        if dist_sqr > dasher.max_target_dist_sqr:
            continue

        # Far = full circle (random). Near = narrow cone around the target.
        closeness = 1.0 - min(1.0, math.sqrt(dist_sqr) / dasher.aim_range)
        spread = math.pi - (math.pi - dasher.min_spread) * closeness
        center = angle_of(toward) if dist_sqr > 0 else 0.0

        direction = open_direction_near(
            world,
            ai,
            transform.position,
            dash.distance + ai.body_radius,
            center,
            spread,
            rng,
        )
        if direction is None:
            continue

        # Don't dash into the target: that's the contact damage's job.
        target_shape = world.try_get_component(ai.target, Shape)
        target_radius = (
            0.0
            if target_shape is None
            else target_shape.radius * target_transform.max_scale
        )
        path_end = transform.position + direction * dash.distance
        if (
            distance_to_segment(target_pos, transform.position, path_end)
            <= target_radius + ai.body_radius
        ):
            continue

        intent.requested = True
        intent.direction = direction
