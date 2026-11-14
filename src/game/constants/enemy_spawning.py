"""Survival spawning tuning: how fast, how many, and which enemies over time."""

import random
from collections.abc import Callable
from dataclasses import dataclass

import pygame

from game.core_ecs.entity import Entity
from game.core_ecs.world import World
from game.prefabs.enemies import spawn_charger, spawn_chaser, spawn_splitter
from game.util.rng import resolve_rng

EnemySpawn = Callable[[World, pygame.Vector2, Entity], Entity]

# Where
SPAWN_MARGIN_MIN = 50.0
"""Spawn points are at least this far (px) outside the camera view..."""
SPAWN_MARGIN_MAX = 250.0
"""...and at most this far, so enemies arrive "just" off screen."""
GIVE_UP_TIME = 10.0
"""Seconds a spawned enemy may stay off screen before it is despawned.
Must comfortably exceed the time to walk in from SPAWN_MARGIN_MAX."""

# How often
START_INTERVAL = 6.0
"""Seconds between spawns at the start."""
MIN_INTERVAL = 0.8
"""The interval never drops below this."""
INTERVAL_HALF_LIFE = 90.0
"""Seconds survived for the gap between START_INTERVAL and MIN_INTERVAL to halve."""

# How many
INITIAL_ENEMIES = 2
"""Enemies spawned off screen on the first update, ignoring the cap."""
START_MAX_ENEMIES = 8
"""Alive-enemy cap at the start (map-placed enemies count too)."""
EXTRA_ENEMY_EVERY = 20.0
"""One more enemy allowed per this many seconds survived."""
HARD_MAX_ENEMIES = 60


@dataclass(frozen=True, slots=True)
class EnemySpawnEntry:
    spawn: EnemySpawn
    weight: float
    """Relative chance among the unlocked entries."""
    unlock_time: float = 0.0
    """Seconds survived before this can spawn."""


ENEMY_TABLE: tuple[EnemySpawnEntry, ...] = (
    EnemySpawnEntry(spawn_chaser, weight=4, unlock_time=0.0),
    EnemySpawnEntry(spawn_splitter, weight=6, unlock_time=2.0),
    EnemySpawnEntry(spawn_charger, weight=5, unlock_time=8.0),
)
"""At least one entry must have `unlock_time` 0."""


def spawn_interval(elapsed: float):
    """Seconds until the next spawn, shrinking toward MIN_INTERVAL."""
    decay = 0.5 ** (elapsed / INTERVAL_HALF_LIFE)
    return MIN_INTERVAL + (START_INTERVAL - MIN_INTERVAL) * decay


def max_enemies(elapsed: float):
    return min(HARD_MAX_ENEMIES, START_MAX_ENEMIES + int(elapsed / EXTRA_ENEMY_EVERY))


def roll_enemy(elapsed: float, rng: random.Random | None = None):
    """Spawn function of a weighted pick among the enemies unlocked by `elapsed`."""
    unlocked = [e for e in ENEMY_TABLE if e.unlock_time <= elapsed]
    weights = [e.weight for e in unlocked]
    return resolve_rng(rng).choices(unlocked, weights=weights)[0].spawn
