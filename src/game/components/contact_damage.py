from dataclasses import dataclass, field

from game.components.player import Player
from game.core_ecs.entity import Entity


@dataclass(slots=True)
class ContactDamage:
    """Damages entities it touches. Each victim is hit at most once per `cooldown`."""

    amount: float
    cooldown: float = 0.75
    """Seconds before the same victim can be hit again."""
    hits: type = Player
    """Component type a victim must have (e.g. Player, Enemy). It also needs Health."""

    # Runtime state
    cooldowns: dict[Entity, float] = field(default_factory=dict)
    """Seconds until each recently hit victim can be hit again."""
