import pygame

from game.components.rigid_body import RigidBody
from game.components.transform import Transform
from game.core_ecs.world import World


def physics_system(world: World, dt: float):
    for entity, (transform, rigidbody) in world.query(Transform, RigidBody):
        if rigidbody.mass <= 0:
            rigidbody.clear_accumulators()
            continue

        # Apply force, acceleration, and impulse. Then, apply drag.
        rigidbody.linear_velocity += (
            rigidbody.accumulated_force * rigidbody.inverse_mass
            + rigidbody.accumulated_acceleration
        ) * dt + rigidbody.accumulated_impulse * rigidbody.inverse_mass
        rigidbody.linear_velocity *= max(0.0, 1.0 - rigidbody.drag * dt)

        # Same idea as above but angular.
        rigidbody.angular_velocity += (
            rigidbody.accumulated_torque * rigidbody.inverse_inertia
            + rigidbody.accumulated_angular_acceleration
        ) * dt + rigidbody.accumulated_angular_impulse * rigidbody.inverse_inertia
        rigidbody.angular_velocity *= max(0.0, 1.0 - rigidbody.angular_drag * dt)

        # Update position and rotation.
        transform.position += rigidbody.linear_velocity * dt
        transform.rotation += rigidbody.angular_velocity * dt

        # Clear accumulated values.
        rigidbody.clear_accumulators()
