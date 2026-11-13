from dataclasses import dataclass, field

import pygame


@dataclass(slots=True)
class InputState:
    movement: pygame.Vector2 = field(default_factory=pygame.Vector2)
    mouse_pos: pygame.Vector2 = field(default_factory=pygame.Vector2)
    primary_down: bool = False
    primary_pressed: bool = False
    primary_released: bool = False
    reload_pressed: bool = False
    weapon_switch: int = 0
    """-1 / 0 / +1, from the mouse wheel or Q."""
    slot_pressed: int | None = None
    """Loadout slot picked with the number keys this frame (1 -> 0, 2 -> 1)."""
    interact_pressed: bool = False
    cancel_pressed: bool = False
