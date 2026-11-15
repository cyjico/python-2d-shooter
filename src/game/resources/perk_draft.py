from dataclasses import dataclass, field

from game.components.perks import PerkSpec


@dataclass(slots=True)
class PerkDraft:
    """The pick-a-perk menu shown after each cleared wave."""

    offer: list[PerkSpec] = field(default_factory=list)
    is_open: bool = False
    rerolls: int = 0
    """Rerolls bought during the current pick. Each costs more."""
    drafted_wave: int = 0
    """Last wave whose clear already gave a pick, so each clear gives one."""
