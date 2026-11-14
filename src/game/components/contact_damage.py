from dataclasses import dataclass, field

from game.core_ecs.entity import Entity


@dataclass(slots=True)
class ContactDamage:
    """Damages hostile entities it touches (see `is_hostile`). Each victim is hit
    at most once per `cooldown`. Victims also need Health."""

    amount: float
    cooldown: float = 0.75
    """Seconds before the same victim can be hit again."""

    # Runtime state
    cooldowns: dict[Entity, float] = field(default_factory=dict)
    """Seconds until each recently hit victim can be hit again."""

    def tick(self, dt: float):
        self.cooldowns = {
            e: left - dt for e, left in self.cooldowns.items() if left - dt > 0
        }

    def try_hit(self, victim: Entity):
        """Starts the victim's cooldown. Returns False if it is still running."""
        if victim in self.cooldowns:
            return False
        self.cooldowns[victim] = self.cooldown
        return True
