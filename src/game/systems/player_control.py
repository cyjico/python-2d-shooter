import math

from ..components.player import Player
from ..components.rigid_body import RigidBody
from ..components.transform import Transform
from ..core_ecs.world import World
from ..resources.camera import Camera
from ..resources.input_state import InputState


def _wrap_angle(angle: float):
    """Wrap to [-pi, pi] so we always turn the short way around."""
    return (angle + math.pi) % math.tau - math.pi


def player_control_system(world: World, dt: float):
    inputs = world.get_resource(InputState)
    camera = world.get_resource(Camera)

    mouse_world = camera.screen_to_world(inputs.mouse_pos)

    for entity, (player,) in world.query(Player):
        rigidbody = world.get_component(entity, RigidBody)
        transform = world.get_component(entity, Transform)

        # Movement
        acceleration = (
            (inputs.movement * player.move_speed) - rigidbody.linear_velocity
        ) / dt

        # Clamp acceleration to the player's maximum acceleration.
        if acceleration.length_squared() > player.move_acceleration**2:
            acceleration.scale_to_length(player.move_acceleration)

        rigidbody.accumulated_acceleration += acceleration

        # Aim at the mouse
        to_mouse = mouse_world - transform.position
        if to_mouse.length_squared() < 1.0:
            continue

        # Both pygame's y-down axes and Transform's rotation are clockwise-positive,
        # so a plain atan2 gives the rotation that points local +x at the cursor.
        error = _wrap_angle(math.atan2(to_mouse.y, to_mouse.x) - transform.rotation)

        desired_velocity = max(
            -player.turn_speed, min(player.turn_speed, error * player.turn_gain)
        )

        angular_acceleration = (desired_velocity - rigidbody.angular_velocity) / dt
        angular_acceleration = max(
            -player.turn_acceleration,
            min(player.turn_acceleration, angular_acceleration),
        )

        rigidbody.accumulated_angular_acceleration += angular_acceleration
