from dataclasses import dataclass
from enum import Enum, auto

from game.components.loadout import Gun
from game.core_ecs.entity import Entity


class BoxPhase(Enum):
    CLOSED = auto()
    ROLLING = auto()
    """Paid; cycling gun names before revealing the result."""
    OFFER = auto()
    """Showing the rolled gun: take, reroll or leave."""
    CHOOSE_SLOT = auto()
    """Taking the gun with full slots: pick which one to replace."""


@dataclass(slots=True)
class MysteryBoxSession:
    """The player's current interaction with a mystery box."""

    phase: BoxPhase = BoxPhase.CLOSED
    box: Entity | None = None
    offer: Gun | None = None
    last_paid: int = 0
    """Price paid for the current roll."""
    roll_timer: float = 0.0
    """Seconds left in the ROLLING phase."""
    flicker_timer: float = 0.0
    """Seconds until the rolling label shows the next random name."""
    rolling_label: Entity | None = None

    @property
    def is_open(self):
        return self.phase is not BoxPhase.CLOSED
