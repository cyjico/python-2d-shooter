from dataclasses import dataclass

import pygame

from game.constants.spawning import SPAWN_CLEARANCE


@dataclass(slots=True)
class Relocatable:
    """Can be moved to another of `points` by `relocate()`."""

    points: list[pygame.Vector2]
    """World positions the map lists as valid spots."""
    min_distance: float = 0.0
    """How far (px) a move must take the entity from where it is now."""
    clearance: float = SPAWN_CLEARANCE
