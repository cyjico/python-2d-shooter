from dataclasses import dataclass, field

import pygame


@dataclass(slots=True)
class InputState:
    movement: pygame.Vector2 = field(default_factory=pygame.Vector2)
    aim_position: pygame.Vector2 = field(default_factory=pygame.Vector2)
    primary_down: bool = False
