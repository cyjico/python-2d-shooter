from dataclasses import dataclass, field

import pygame


@dataclass(slots=True)
class InputState:
    movement: pygame.Vector2 = field(default_factory=pygame.Vector2)
    mouse_pos: pygame.Vector2 = field(default_factory=pygame.Vector2)
    primary_down: bool = False
    primary_pressed: bool = False
    primary_released: bool = False
