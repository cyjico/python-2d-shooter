from dataclasses import dataclass, field

import pygame


@dataclass(slots=True)
class Mover:
    move_speed: float = 200.0
    """Maximum linear velocity."""
    move_accel: float = 1125.0
    """Maximum linear acceleration."""

    turn_speed: float = 12.0
    """Maximum angular velocity, in radians."""
    turn_accel: float = 100.0
    """Maximum angular acceleration, in radians."""
    turn_gain: float = 11.25
    """Desired angular velocity per radian of aim error. Higher = snappier."""

    move_dir: pygame.Vector2 = field(default_factory=pygame.Vector2)
    """Direction to move towards. Expects vector to be normalized."""
    face_angle: float | None = None
    """Angle (radians) to turn toward, or `None` to keep the current rotation."""
