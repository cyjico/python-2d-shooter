import random
from collections.abc import Callable
from dataclasses import dataclass, field

import pygame

from game.constants.spawning import SPAWN_CLEARANCE
from game.core_ecs.entity import Entity
from game.core_ecs.world import World


@dataclass(slots=True)
class Spawner:
    """Periodically spawns something at a random free spot from `points`."""

    points: list[pygame.Vector2]
    """World positions the map lists as valid spots."""
    spawn: Callable[[World, pygame.Vector2], Entity]
    interval: tuple[float, float]
    """Random seconds between spawns."""
    max_alive: int
    """No spawning while this many of its spawns still exist."""
    clearance: float = SPAWN_CLEARANCE

    # Runtime state
    spawned: list[Entity] = field(default_factory=list)
    timer: float = 0.0

    def __post_init__(self):
        self.timer = random.uniform(*self.interval)
