import math

from game.components.camera_target import CameraTarget
from game.components.transform import Transform
from game.core_ecs.world import World
from game.resources.camera import Camera


def camera_follow_system(world: World, dt: float):
    camera = world.get_resource(Camera)

    for _, (target, transform) in world.query(CameraTarget, Transform):
        goal = transform.position - camera.viewport_size / 2

        # Reminder that lim x->inf e^-x = 0.
        t = 1.0 - math.exp(-target.smoothing * dt)
        camera.position = camera.position.lerp(goal, t)
        # Only one target is followed.
        break
