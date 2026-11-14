from game.components.drift import Drift
from game.components.transform import Transform
from game.core_ecs.world import World


def drift_system(world: World, dt: float):
    for _, (drift, transform) in world.query(Drift, Transform):
        transform.position += drift.velocity * dt
        drift.velocity *= max(0.0, 1.0 - drift.drag * dt)
