from dataclasses import dataclass

from game.core_ecs.entity import Entity


@dataclass(slots=True)
class HoverAroundTargetAI:
    target: Entity

    preferred_dist_sqr: float = 220.0**2
    """Distance from the target the AI tries to hold."""
    dist_tolerance_sqr: float = 40.0**2
    """Inside preferred +/- `this`."""

    strafing: bool = False
    strafe_side: int = 1
