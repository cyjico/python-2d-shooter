from dataclasses import dataclass

from game.core_ecs.entity import Entity


@dataclass(slots=True)
class DamageEvent:
    target: Entity
    amount: float
    source: Entity | None = None
    critical: bool = False


@dataclass(slots=True)
class DamageTakenEvent:
    """Damage that reached an entity's Health (i.e. not blocked by immunity).
    Bonus health may still have absorbed some or all of it."""

    target: Entity
    amount: float
    critical: bool = False


@dataclass(slots=True)
class EntityDiedEvent:
    entity: Entity
    killer: Entity | None = None


@dataclass(slots=True)
class BrokenEvent:
    entity: Entity
    breaker: Entity
