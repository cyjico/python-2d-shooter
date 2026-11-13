from dataclasses import dataclass

from game.core_ecs.entity import Entity


@dataclass(slots=True)
class DamageEvent:
    target: Entity
    amount: float
    source: Entity | None = None


@dataclass(slots=True)
class EntityDiedEvent:
    entity: Entity
    killer: Entity | None = None


@dataclass(slots=True)
class BrokenEvent:
    entity: Entity
    breaker: Entity
