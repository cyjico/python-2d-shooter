from dataclasses import dataclass


@dataclass(slots=True)
class PowerUpDrops:
    """How many power-ups dropped in the current wave."""

    wave: int = 0
    dropped: int = 0
