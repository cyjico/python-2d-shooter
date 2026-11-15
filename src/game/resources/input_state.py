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
    """Right click or R."""
    weapon_switch: int = 0
    """-1 / 0 / +1, from the mouse wheel or F."""
    dash_pressed: bool = False
    slot_pressed: int | None = None
    """Loadout slot picked with the number keys this frame (1 -> 0, 2 -> 1)."""
    number_pressed: int | None = None
    """Any number key pressed this frame, as an index (1 -> 0 ... 9 -> 8).
    Used by menus (e.g. picking a perk)."""
    interact_pressed: bool = False
    """E."""
    reroll_pressed: bool = False
    """R, used by menus (mystery box, perk pick). Outside menus, R reloads."""
    cancel_pressed: bool = False
    """Q, used to decline the mystery box."""
