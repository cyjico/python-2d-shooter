from dataclasses import dataclass

from game.components.faction import Team


@dataclass(slots=True)
class Breakable:
    """Destroyed once its durability runs out, but only by damage from a source on `broken_by`."""

    durability: float
    broken_by: Team = Team.PLAYER
    """Team the damage source must be on."""
