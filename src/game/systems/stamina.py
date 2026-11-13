from game.components.stamina import Stamina
from game.core_ecs.world import World


def stamina_system(world: World, dt: float):
    """Regenerates stamina. Run before anything that spends it."""
    for _, (stamina,) in world.query(Stamina):
        stamina.regen(dt)
