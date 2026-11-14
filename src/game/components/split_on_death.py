from collections.abc import Callable
from dataclasses import dataclass

import pygame

from game.core_ecs.entity import Entity
from game.core_ecs.world import World


@dataclass(slots=True)
class SplitOnDeath:
    """When this entity dies, `count` others appear where it was (see
    `split_on_death_system`)."""

    count: int
    spawn: Callable[[World, pygame.Vector2, Entity | None], Entity]
    """Creates one offspring at a position, aimed at the given target."""
    spread_distance: float = 20.0
    """How far (px) from the death spot the offspring appear."""
    burst_speed: float = 150.0
    """Initial speed (px/s) of each offspring, directly away from the death spot."""
