from game.components.drone import Drone
from game.core_ecs.entity import Entity
from game.core_ecs.world import World


def owner_of(world: World, entity: Entity | None):
    """Who gets credit for what `entity` does: a drone's owner, else itself."""
    if entity is None:
        return None
    drone = world.try_get_component(entity, Drone)
    return entity if drone is None else drone.owner
