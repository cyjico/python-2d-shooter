import math

from game.components.mover import Mover
from game.components.player import Player
from game.components.rigid_body import RigidBody
from game.components.transform import Transform
from game.core_ecs.world import World
from game.resources.camera import Camera
from game.resources.input_state import InputState
from game.util.numerics import wrap_angle


def mover_system(world: World, dt: float):
    for entity, (mover,) in world.query(Mover):
        rigidbody = world.get_component(entity, RigidBody)
        transform = world.get_component(entity, Transform)

        acceleration = (
            (mover.move_dir * mover.move_speed) - rigidbody.linear_velocity
        ) / dt
        if acceleration.length_squared() > mover.move_accel**2:
            acceleration.scale_to_length(mover.move_accel)

        rigidbody.accumulated_acceleration += acceleration

        if mover.face_angle is not None:
            desired_velocity = max(
                -mover.turn_speed,
                min(
                    mover.turn_speed,
                    wrap_angle(mover.face_angle - transform.rotation) * mover.turn_gain,
                ),
            )

            angular_acceleration = max(
                -mover.turn_accel,
                min(
                    mover.turn_accel,
                    (desired_velocity - rigidbody.angular_velocity) / dt,
                ),
            )

            rigidbody.accumulated_angular_acceleration += angular_acceleration
