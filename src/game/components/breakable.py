from dataclasses import dataclass

from game.components.player import Player


@dataclass(slots=True)
class Breakable:
    """Destroyed once its durability runs out, but only by damage from a `broken_by` entity."""

    durability: float
    broken_by: type = Player
    """Component type the damage source must have (e.g. Player, Enemy)."""
