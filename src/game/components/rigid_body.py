from dataclasses import dataclass, field

import pygame


@dataclass(slots=True)
class RigidBody:
    mass: float = 1.0
    drag: float = 1.0

    inertia: float = 0.0
    """Informally known as 'angular mass'."""
    angular_drag: float = 2.0

    linear_velocity: pygame.Vector2 = field(default_factory=pygame.Vector2)
    angular_velocity: float = 0.0
    """Radians per second, clockwise."""

    accumulated_impulse: pygame.Vector2 = field(default_factory=pygame.Vector2)
    """Force applied over a short period of time (e.g. explosions, collisions)."""
    accumulated_angular_impulse: float = 0.0
    """Force applied over a short period of time (e.g. explosions, collisions)."""

    accumulated_force: pygame.Vector2 = field(default_factory=pygame.Vector2)
    """Push/pull that produces acceleration (e.g. thrusters)."""
    accumulated_torque: float = 0.0
    """Twist that produces angular acceleration (e.g. a spinning thruster)."""

    accumulated_acceleration: pygame.Vector2 = field(default_factory=pygame.Vector2)
    """How quickly velocity changes over time (e.g. gravity)."""
    accumulated_angular_acceleration: float = 0.0
    """How quickly angular velocity changes over time, clockwise."""

    @property
    def inverse_inertia(self):
        """Inverse inertia is a measure of how easily an object can be spun.

        Returns:
            float: If inertia is zero, returns 0; else 1 / mass.
        """
        return 0.0 if self.inertia == 0 else 1.0 / self.inertia

    @property
    def inverse_mass(self):
        """Inverse mass is a measure of how easily an object responds to force.

        Returns:
            float: If mass is zero, returns 0; else 1 / mass.
        """
        return 0.0 if self.mass == 0 else 1.0 / self.mass

    @staticmethod
    def velocity_at(p: pygame.Vector2, rb: RigidBody):
        """Velocity of a point `p` away from the center: linear + spin."""
        # [-r.y, r.x] is perpendicular to p.
        return rb.linear_velocity + rb.angular_velocity * pygame.Vector2(-p.y, p.x)

    def inverse_effective_resistance(
        self, p: pygame.Vector2, direction: pygame.Vector2
    ):
        """How easily a push at `r` along `direction` changes this body's motion."""

        # p.cross(direction) being positive => direction is clockwise from p.
        # p.cross(direction) being negative => direction is counterclockwise from p.
        return self.inverse_mass + p.cross(direction) ** 2 * self.inverse_inertia

    def apply_force(self, force: pygame.Vector2):
        self.accumulated_force += force

    def apply_acceleration(self, acceleration: pygame.Vector2):
        self.accumulated_acceleration += acceleration

    def apply_impulse(self, impulse: pygame.Vector2):
        self.accumulated_impulse += impulse

    def apply_impulse_at(self, p: pygame.Vector2, impulse: pygame.Vector2):
        self.apply_impulse(impulse)

        # p.cross(impulse) being positive => impulse is clockwise from p.
        # p.cross(impulse) being negative => impulse is counterclockwise from p.
        self.apply_angular_impulse(p.cross(impulse))

    def apply_angular_impulse(self, impulse: float):
        self.accumulated_angular_impulse += impulse

    def clear_accumulators(self):
        self.accumulated_force.update(0, 0)
        self.accumulated_torque = 0.0
        self.accumulated_impulse.update(0, 0)
        self.accumulated_angular_impulse = 0.0
        self.accumulated_acceleration.update(0, 0)
        self.accumulated_angular_acceleration = 0.0


def mass_of_box(density: float, width: float, height: float):
    return density * width * height / 12**2


def inertia_of_box(mass: float, width: float, height: float):
    """Inertia of a solid rectangle spinning around its center."""
    return mass * (width**2 + height**2) / 12
