import math
import random
from dataclasses import dataclass


@dataclass(slots=True)
class ShooterAI:
    """Aims at the target and shoots in bursts while it has a clear line of fire.

    Needs AI, Loadout, WeaponIntent and Mover. Movement comes from another AI
    (e.g. HoverAroundTargetAI); this one only overrides where it faces.
    """

    burst_time: tuple[float, float] = (0.6, 1.1)
    """Random seconds spent shooting..."""
    rest_time: tuple[float, float] = (1.2, 2.2)
    """...then random seconds before the next burst, so there's room to fight back."""
    aim_tolerance: float = math.radians(10)
    """Only fires while facing within this many radians of the target."""
    range_fraction: float = 0.9
    """Fires once the target is within this fraction of the gun's range."""

    # Runtime state
    firing: bool = False
    timer: float = 0.0

    def __post_init__(self):
        # Start resting, so it doesn't open fire the moment it walks on screen.
        self.timer = random.uniform(*self.rest_time)
