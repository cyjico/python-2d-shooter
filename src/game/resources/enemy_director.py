from dataclasses import dataclass, field
from enum import Enum, auto

from game.constants.enemy_spawning import FIRST_BREAK_TIME, EnemySpawn


class WavePhase(Enum):
    BREAK = auto()
    """Between waves. `timer` counts down to the next one."""
    ACTIVE = auto()
    """A wave is being fought. `timer` counts down to the next spawn."""


@dataclass(slots=True)
class EnemyDirector:
    """Wave spawning state. Tuning lives in `constants.enemy_spawning`."""

    wave: int = 0
    """The current wave, from 1. 0 = before the first one."""
    phase: WavePhase = WavePhase.BREAK
    timer: float = FIRST_BREAK_TIME
    roster: list[EnemySpawn] = field(default_factory=list)
    """Enemies of the current wave still waiting to spawn."""
    just_cleared: bool = False
    """True during the break right after a wave was cleared (not before wave I)."""
    held: bool = False
    """Stops the break's countdown (e.g. while the player picks a perk)."""
