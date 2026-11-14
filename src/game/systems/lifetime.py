from game.components.lifetime import Lifetime
from game.core_ecs.world import World


def lifetime_system(world: World, dt: float):
    """Ages every Lifetime and destroys the expired ones."""
    for entity, (life,) in world.query(Lifetime):
        life.age += dt
        if life.age >= life.duration:
            world.destroy_entity(entity)
