from game.components.offscreen_despawn import OffscreenDespawn
from game.components.shape import Shape
from game.components.transform import Transform
from game.core_ecs.world import World
from game.resources.camera import Camera


def offscreen_despawn_system(world: World, dt: float):
    """Destroys entities that have stayed out of the camera's view too long."""
    camera = world.get_resource(Camera)

    for entity, (despawn, transform) in world.query(OffscreenDespawn, Transform):
        shape = world.try_get_component(entity, Shape)
        radius = 0.0 if shape is None else shape.radius * transform.max_scale

        if camera.is_circle_visible(transform.position, radius):
            despawn.offscreen_time = 0.0
            continue

        despawn.offscreen_time += dt
        if despawn.offscreen_time >= despawn.timeout:
            world.destroy_entity(entity)
