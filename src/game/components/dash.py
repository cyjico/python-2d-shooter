from dataclasses import dataclass, field

import pygame

from game.core_ecs.entity import Entity


@dataclass(slots=True)
class Dash:
    speed: float = 700.0
    """Velocity while dashing. Distance is roughly speed * duration."""
    duration: float = 0.15
    cooldown: float = 0.25
    """Minimum seconds between dash starts, regardless of stamina."""
    stamina_cost: float = 1.0
    """Stamina segments spent per dash. Ignored if the entity has no Stamina."""
    impact_damage: float = 30.0
    """Damage dealt to each Breakable the dash runs into."""

    # Runtime state
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


@dataclass(slots=True)
class DashIntent:
    """Whether the entity wants to dash.

    The player's input fills this in; an AI can fill it the same way.
    The dash direction comes from the entity's Mover, not from here.
    """

    requested: bool = False
    """Cleared by dash_system once read, so a one-off request can't repeat."""
