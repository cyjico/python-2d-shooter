import random

from game.components.faction import Faction, Team
from game.components.offscreen_despawn import OffscreenDespawn
from game.components.player import Player
from game.constants.enemy_spawning import (
    GIVE_UP_TIME,
    SPAWN_MARGIN_MAX,
    SPAWN_MARGIN_MIN,
    max_enemies,
    roll_enemy,
    spawn_interval,
)
from game.core_ecs.world import Entity, World
from game.resources.camera import Camera
from game.resources.enemy_director import EnemyDirector
from game.util.rng import resolve_rng


def _enemy_count(world: World):
    return sum(1 for _, (f,) in world.query(Faction) if f.team & Team.ENEMY)


def _spawn_enemy(world: World, player: Entity, elapsed: float, rng: random.Random):
    camera = world.get_resource(Camera)
    position = camera.random_point_outside_view(SPAWN_MARGIN_MIN, SPAWN_MARGIN_MAX, rng)
    enemy = roll_enemy(elapsed, rng)(world, position, player)
    # Stranded spawns (outside the map, behind walls) give up eventually.
    world.add_component(enemy, OffscreenDespawn(GIVE_UP_TIME))


def enemy_spawn_system(world: World, dt: float, rng: random.Random | None = None):
    """Spawns enemies just off screen, faster and in greater numbers over time.

    The spot isn't checked against the map: one inside a wall is pushed out by
    collision resolution, and off screen nobody sees it happen.
    """
    rng = resolve_rng(rng)
    director = world.get_resource(EnemyDirector)

    player = next((e for e, _ in world.query(Player)), None)
    if player is None:
        return

    while director.backlog > 0:
        director.backlog -= 1
        _spawn_enemy(world, player, director.elapsed, rng)

    director.elapsed += dt
    director.timer -= dt
    if director.timer > 0:
        return

    director.timer = spawn_interval(director.elapsed)
    if _enemy_count(world) >= max_enemies(director.elapsed):
        return

    _spawn_enemy(world, player, director.elapsed, rng)
