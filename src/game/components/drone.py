from dataclasses import dataclass

from game.core_ecs.entity import Entity


@dataclass(slots=True)
class Drone:
    """Orbits `owner` and shoots enemies near it. What it kills counts as the
    owner's kill (bounty, lifesteal, on-kill perks)."""

    owner: Entity
    index: int
    """Place in the ring, from 0. Drones spread out evenly by index."""
    phase: float = 0.0
    """Radians the ring has turned. The same on every drone of an owner."""
