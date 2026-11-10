from dataclasses import dataclass, field

import pygame


@dataclass(slots=True)
class RigidBody:
    mass: float = 1.0
    drag: float = 0.0

    linear_velocity: pygame.Vector2 = field(default_factory=pygame.Vector2)

    accumulated_force: pygame.Vector2 = field(default_factory=pygame.Vector2)
    """Push/pull that produces acceleration (e.g. thrusters)."""
    accumulated_acceleration: pygame.Vector2 = field(default_factory=pygame.Vector2)
    """How quickly velocity changes over time (e.g. gravity)."""
    accumulated_impulse: pygame.Vector2 = field(default_factory=pygame.Vector2)
    """Force applied over a short period of time (e.g. explosions, collisions)."""

    @property
    def inverse_mass(self) -> float:
        if self.mass == 0:
            return 0.0
        
        return 1.0 / self.mass

    def apply_force(self, force: pygame.Vector2):
        self.accumulated_force += force

    def apply_acceleration(self, acceleration: pygame.Vector2):
        self.accumulated_acceleration += acceleration

    def apply_impulse(self, impulse: pygame.Vector2):
        self.accumulated_impulse += impulse

    def clear_accumulators(self):
        self.accumulated_force.update(0, 0)
        self.accumulated_acceleration.update(0, 0)
        self.accumulated_impulse.update(0, 0)
