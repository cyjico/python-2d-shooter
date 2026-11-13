from dataclasses import dataclass

from game.core_ecs.entity import Entity


@dataclass(slots=True)
class AI:
    target: Entity | None = None

    body_radius: float = 16.0
    """Used to make wall probes as wide as the body."""
    probe_distance: float = 45.0
    """How far ahead the enemy looks for walls."""
    avoid_side: int = 1
    """Which way to sidestep a wall: +1 = right, -1 = left. Flips when that side is blocked."""
