from dataclasses import dataclass, field

import pygame


@dataclass(slots=True)
class Dash:
    speed: float = 700.0
    """Velocity while dashing. Distance is roughly speed * duration."""
    duration: float = 0.15
    cooldown: float = 0.8

    time_left: float = 0.0
    cooldown_left: float = 0.0
    direction: pygame.Vector2 = field(default_factory=pygame.Vector2)

    @property
    def active(self) -> bool:
        return self.time_left > 0.0