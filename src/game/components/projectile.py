from dataclasses import dataclass, field

from game.components.faction import Team
from game.core_ecs.entity import Entity


@dataclass(slots=True)
class Projectile:
    owner: Entity
    """Never hits this entity."""
    damage: float
    team: Team = Team.NONE
    """The owner's team when fired. Passes through allies of that team."""
    pierce_left: int = 0
    knockback: float = 0.0
    crit_chance: float = 0.0
    """Chance, from 0 to 1, that a hit is critical. Rolled per hit."""
    crit_multiplier: float = 1.0
    hit: set[Entity] = field(default_factory=set)
    """Entities already hit, so one projectile can't hit the same target twice."""
