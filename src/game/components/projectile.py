from dataclasses import dataclass, field

from game.core_ecs.entity import Entity


@dataclass(slots=True)
class Projectile:
    owner: Entity
    """Never hits this entity."""
    damage: float
    lifetime: float
    """Seconds left before despawning."""
    pierce_left: int = 0
    knockback: float = 0.0
    hit: set[Entity] = field(default_factory=set)
    """Entities already hit, so one projectile can't hit the same target twice."""
