from dataclasses import dataclass


@dataclass(slots=True)
class Player:
    move_speed: float = 200.0
    move_acceleration: float = 1500.0
