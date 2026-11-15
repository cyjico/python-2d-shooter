"""Wave spawning tuning: how many enemies each wave has, which ones, and how
much stronger they get per wave."""

import random
from collections.abc import Callable
from dataclasses import dataclass

import pygame

from game.core_ecs.entity import Entity
from game.core_ecs.world import World
from game.prefabs.enemies import (
    spawn_charger,
    spawn_chaser,
    spawn_shooter,
    spawn_splitter,
)
from game.util.rng import resolve_rng

EnemySpawn = Callable[[World, pygame.Vector2, Entity], Entity]

# Where
SPAWN_MARGIN_MIN = 50.0
"""Spawn points are at least this far (px) outside the camera view..."""
SPAWN_MARGIN_MAX = 250.0
"""...and at most this far, so enemies arrive "just" off screen."""
GIVE_UP_TIME = 10.0
"""Seconds a wave enemy may stay off screen before it is moved back near the
player. Must comfortably exceed the time to walk in from SPAWN_MARGIN_MAX."""

# Pacing
FIRST_BREAK_TIME = 2.0
"""Seconds before wave I, long enough to read its banner."""
BREAK_TIME = 8.0
"""Seconds between clearing a wave and the next one starting."""
WAVE_CLEAR_HEAL = 0.3
"""Fraction of max health the player gets back for clearing a wave."""
OPENING_SPAWNS = 2
"""Enemies spawned the moment a wave starts. The rest trickle in."""

# How many
BASE_WAVE_SIZE = 6
WAVE_SIZE_STEP = 3
"""Enemies added per wave."""
MAX_WAVE_SIZE = 80


@dataclass(frozen=True, slots=True)
class EnemySpawnEntry:
    spawn: EnemySpawn
    weight: float
    """Relative chance among the unlocked special enemies."""
    unlock_wave: int = 1
    """First wave this can appear in."""


EASY_ENEMY: EnemySpawn = spawn_chaser
"""Fills every slot of a wave that isn't special."""

SPECIAL_ENEMIES: tuple[EnemySpawnEntry, ...] = (
    EnemySpawnEntry(spawn_splitter, weight=5, unlock_wave=1),
    EnemySpawnEntry(spawn_charger, weight=5, unlock_wave=2),
    EnemySpawnEntry(spawn_shooter, weight=4, unlock_wave=3),
)
"""At least one entry must unlock on wave 1."""


@dataclass(frozen=True, slots=True)
class WaveScaling:
    """Stat multipliers for enemies of a wave."""

    health: float
    damage: float
    move_speed: float
    bounty: float


def wave_size(wave: int):
    """Enemies in `wave` (not counting splitter offspring)."""
    return min(MAX_WAVE_SIZE, BASE_WAVE_SIZE + WAVE_SIZE_STEP * (wave - 1))


def special_count(wave: int, size: int):
    """How many of a wave's `size` enemies are special: few at first, up to 60%."""
    share = min(0.6, 0.1 + 0.08 * (wave - 1))
    return min(size, max(1, round(size * share)))


def wave_scaling(wave: int):
    step = wave - 1
    return WaveScaling(
        health=1 + 0.15 * step,
        damage=1 + 0.10 * step,
        move_speed=min(1.35, 1 + 0.03 * step),
        bounty=1 + 0.10 * step,
    )


def spawn_interval(wave: int):
    """Seconds between spawns while a wave is trickling in."""
    return max(0.5, 2.0 - 0.1 * (wave - 1))


def max_alive(wave: int):
    """Wave enemies alive at once; the rest wait their turn."""
    return 4 + wave


def wave_roster(wave: int, rng: random.Random | None = None) -> list[EnemySpawn]:
    """Every enemy of `wave`, in spawn order."""
    rng = resolve_rng(rng)
    size = wave_size(wave)
    specials = special_count(wave, size)

    unlocked = [e for e in SPECIAL_ENEMIES if e.unlock_wave <= wave]
    roster = [
        e.spawn
        for e in rng.choices(unlocked, weights=[e.weight for e in unlocked], k=specials)
    ]
    roster += [EASY_ENEMY] * (size - specials)
    rng.shuffle(roster)
    return roster
