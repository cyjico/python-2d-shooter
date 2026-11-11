from dataclasses import dataclass


@dataclass(slots=True)
class Player:
    move_speed: float = 200.0
    """Maximum linear velocity."""
    move_acceleration: float = 1125.0
    """Maximum linear acceleration."""

    turn_speed: float = 12.0
    """Maximum angular velocity, in radians."""
    turn_acceleration: float = 100.0
    """Maximum angular acceleration, in radians."""
    turn_gain: float = 11.25
    """Desired angular velocity per radian of aim error. Higher = snappier."""
