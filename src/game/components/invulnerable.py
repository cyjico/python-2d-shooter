from dataclasses import dataclass


@dataclass(slots=True)
class Invulnerable:
    """Takes no damage while present, regardless of buffs."""
