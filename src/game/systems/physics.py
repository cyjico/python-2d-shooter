import pygame

from ..core_ecs.world import World
from ..components.transform import Transform
from ..components.rigid_body import RigidBody


def physics_system(world: World, dt: float):
    for entity, (transform, rigidbody) in world.query(Transform, RigidBody):
        if rigidbody.mass <= 0:
            rigidbody.clear_accumulators()
            continue

        # Apply force, acceleration, and impulse.
        rigidbody.linear_velocity += (
            rigidbody.accumulated_force / rigidbody.mass
            + rigidbody.accumulated_acceleration
        ) * dt + rigidbody.accumulated_impulse / rigidbody.mass

        # Apply drag.
        drag_factor = max(0.0, 1.0 - rigidbody.drag * dt)
        rigidbody.linear_velocity *= drag_factor

        # Update position.
        transform.position += rigidbody.linear_velocity * dt

        # Clear accumulated values.
        rigidbody.clear_accumulators()
