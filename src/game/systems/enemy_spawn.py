import random

from game.components.faction import Faction, Team
from game.components.health import Health
from game.components.player import Player
from game.constants.enemy_spawning import (
    BREAK_TIME,
    OPENING_SPAWNS,
    SPAWN_MARGIN_MAX,
    SPAWN_MARGIN_MIN,
    WAVE_CLEAR_HEAL,
    EnemySpawn,
    max_alive,
    spawn_interval,
    wave_roster,
)
from game.core_ecs.world import Entity, World
from game.resources.camera import Camera
from game.resources.enemy_director import EnemyDirector, WavePhase
from game.resources.run_stats import RunStats
from game.systems.damage_numbers import HEAL_COLOR, spawn_floating_number
from game.util.perks import heal
from game.util.rng import resolve_rng


def enemy_count(world: World):
    """Living enemies, splitter offspring included."""
    return sum(1 for _, (f,) in world.query(Faction) if f.team & Team.ENEMY)


def wave_remaining(world: World):
    """Enemies left in the current wave: alive plus not yet spawned.
    0 between waves."""
    director = world.get_resource(EnemyDirector)
    if director.phase is not WavePhase.ACTIVE:
        return 0
    return len(director.roster) + enemy_count(world)


def _spawn_enemy(world: World, spawn: EnemySpawn, player: Entity, rng: random.Random):
    camera = world.get_resource(Camera)
    position = camera.random_point_outside_view(SPAWN_MARGIN_MIN, SPAWN_MARGIN_MAX, rng)
    # wave_scaling_system makes it as strong as the wave and brings it back if
    # it gets stranded (outside the map, behind walls).
    spawn(world, position, player)


def _start_wave(world: World, director: EnemyDirector, rng: random.Random):
    director.wave += 1
    director.phase = WavePhase.ACTIVE
    director.just_cleared = False
    director.roster = wave_roster(director.wave, rng)
    world.get_resource(RunStats).wave = director.wave


def _heal_on_clear(world: World, player: Entity):
    """Clearing a wave gives back part of the player's health."""
    health = world.try_get_component(player, Health)
    if health is None or health.current <= 0:
        return
    before = health.current
    heal(world, player, health.maximum * WAVE_CLEAR_HEAL)
    gained = round(health.current - before)
    if gained > 0:
        spawn_floating_number(world, player, f"+{gained}", HEAL_COLOR)


def enemy_spawn_system(world: World, dt: float, rng: random.Random | None = None):
    """Runs the waves: a break, then a fixed roster of enemies spawned just off
    screen, then a break again once every one of them (and their offspring) died.

    The spot isn't checked against the map: one inside a wall is pushed out by
    collision resolution, and off screen nobody sees it happen.
    """
    rng = resolve_rng(rng)
    director = world.get_resource(EnemyDirector)

    player = next((e for e, _ in world.query(Player)), None)
    if player is None:
        return

    if director.phase is WavePhase.BREAK and director.held:
        return
    director.timer -= dt

    if director.phase is WavePhase.BREAK:
        if director.timer > 0:
            return
        _start_wave(world, director, rng)
        for _ in range(min(OPENING_SPAWNS, len(director.roster))):
            _spawn_enemy(world, director.roster.pop(), player, rng)
        director.timer = spawn_interval(director.wave)
        return

    alive = enemy_count(world)
    if not director.roster:
        if alive == 0:
            director.phase = WavePhase.BREAK
            director.timer = BREAK_TIME
            director.just_cleared = True
            _heal_on_clear(world, player)
        return

    if alive >= max_alive(director.wave):
        return
    # An empty field means no waiting: there's nothing to fight in the meantime.
    if director.timer > 0 and alive > 0:
        return
    director.timer = spawn_interval(director.wave)
    _spawn_enemy(world, director.roster.pop(), player, rng)
