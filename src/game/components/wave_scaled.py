from dataclasses import dataclass


@dataclass(slots=True)
class WaveScaled:
    """Marks an enemy whose stats were already scaled for its wave."""

    wave: int
