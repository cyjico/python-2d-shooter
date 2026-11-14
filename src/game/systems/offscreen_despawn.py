import random

from game.components.offscreen_despawn import OffscreenDespawn
from game.components.rigid_body import RigidBody
from game.components.shape import Shape
from game.components.transform import Transform
from game.constants.enemy_spawning import SPAWN_MARGIN_MAX, SPAWN_MARGIN_MIN
from game.core_ecs.world import World
from game.resources.camera import Camera
from game.util.rng import resolve_rng


def offscreen_despawn_system(world: World, dt: float, rng: random.Random | None = None):
    """Destroys (or relocates) entities that have stayed out of the camera's
    view too long."""
    camera = world.get_resource(Camera)

    for entity, (despawn, transform) in world.query(OffscreenDespawn, Transform):
        shape = world.try_get_component(entity, Shape)
        radius = 0.0 if shape is None else shape.radius * transform.max_scale

        if camera.is_circle_visible(transform.position, radius):
            despawn.offscreen_time = 0.0
            continue

        despawn.offscreen_time += dt
        if despawn.offscreen_time < despawn.timeout:
            continue

        if not despawn.relocate:
            world.destroy_entity(entity)
            continue

        despawn.offscreen_time = 0.0
        transform.position = camera.random_point_outside_view(
            SPAWN_MARGIN_MIN, SPAWN_MARGIN_MAX, resolve_rng(rng)
        )
        body = world.try_get_component(entity, RigidBody)
        if body is not None:
            body.linear_velocity.update()
