from dataclasses import dataclass, field

from game.events.combat import DamageEvent


@dataclass(slots=True)
class DeferredDamage:
    """Damage caused by a death (e.g. Carnage explosions). Deaths are known only
    after damage was applied this frame, so it lands on the next one, which
    also lets explosions chain."""

    pending: list[DamageEvent] = field(default_factory=list)
