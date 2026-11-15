from dataclasses import dataclass

import pygame

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
    Shield may still have absorbed some or all of it."""

    target: Entity
    amount: float
    critical: bool = False


@dataclass(slots=True)
class EntityDiedEvent:
    entity: Entity
    killer: Entity | None = None


@dataclass(slots=True)
class ProjectileHitEvent:
    """A projectile struck something solid (wall, crate, enemy, ...)."""

    shooter: Entity
    target: Entity
    position: pygame.Vector2
    """Roughly where the projectile met the target's surface."""
    direction: pygame.Vector2
    """Unit vector the projectile was travelling in."""


@dataclass(slots=True)
class BrokenEvent:
    entity: Entity
    breaker: Entity


@dataclass(slots=True)
class DashStartedEvent:
    entity: Entity
