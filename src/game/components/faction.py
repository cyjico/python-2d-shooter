from dataclasses import dataclass
from enum import Flag, auto


class Team(Flag):
    NONE = 0
    PLAYER = auto()
    ENEMY = auto()

    # Composite masks
    ALL = PLAYER | ENEMY


@dataclass(slots=True)
class Faction:
    """Which side an entity is on. Entities without one are neutral: they are
    never hostile to anything (e.g. walls, crates, the mystery box)."""

    team: Team
