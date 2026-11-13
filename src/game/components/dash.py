from dataclasses import dataclass, field

import pygame

from game.core_ecs.entity import Entity


@dataclass(slots=True)
class Dash:
    speed: float = 700.0
    """Velocity while dashing. Distance is roughly speed * duration."""
    duration: float = 0.15
    cooldown: float = 0.8
    impact_damage: float = 30.0
    """Damage dealt to each Breakable the dash runs into."""

    time_left: float = 0.0
    cooldown_left: float = 0.0
    direction: pygame.Vector2 = field(default_factory=pygame.Vector2)
    hit: set[Entity] = field(default_factory=set)
    """Entities already hit by the current dash."""
    moving: bool = False
    """True on every frame the dash drove movement, including its last one.
    Unlike `active`, this is still set when collisions are checked."""

    @property
    def active(self) -> bool:
        return self.time_left > 0.0
