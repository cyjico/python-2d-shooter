from dataclasses import dataclass
from enum import Enum, auto


class PowerUpKind(Enum):
    MED_KIT = auto()
    MAX_AMMO = auto()
    SHIELD = auto()
    NUKE = auto()


@dataclass(slots=True)
class PowerUp:
    """A pickup lying in the world, dropped by a killed enemy. The player
    collects it by walking over it. Expires with its Lifetime."""

    kind: PowerUpKind


@dataclass(slots=True)
class ScreenFlash:
    """Tints the whole screen, fading over its Lifetime (e.g. a nuke)."""

    color: tuple[int, int, int]
    alpha: int = 200
    """At the start; fades to 0."""
