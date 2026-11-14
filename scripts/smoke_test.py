import math
import os
import random
from dataclasses import replace

import pygame

from game.components.ai.random_dash import RandomDashAI
from game.components.bounty import Bounty
from game.components.buffs import ActiveBuffs, Stat
from game.components.dash import Dash
from game.components.health import Health
from game.components.loadout import Loadout, Rarity
from game.components.mystery_box import MysteryBox
from game.components.offscreen_despawn import OffscreenDespawn
from game.components.relocatable import Relocatable
from game.components.rigid_body import RigidBody
from game.components.split_on_death import SplitOnDeath
from game.components.stamina import Stamina
from game.components.transform import Transform
from game.components.wallet import Wallet
from game.constants.buffs import EXTRA_STAMINA, MONEY_BOOSTS, QUICK_RECOVERY
from game.constants.enemy_spawning import (
    INITIAL_ENEMIES,
    SPAWN_MARGIN_MAX,
    SPAWN_MARGIN_MIN,
    max_enemies,
    spawn_interval,
)
from game.constants.gun_buffs import buffed_spec
from game.constants.guns import ALL_GUNS
from game.components.particle import Particle, Spark
from game.components.shape import Shape
from game.constants.rarity import rarity_stars
from game.game import Game, GameState
from game.prefabs.enemies import spawn_charger, spawn_chaser, spawn_splitter
from game.components.projectile import Projectile
from game.prefabs.gun_projectile import spawn_gun_projectile
from game.resources.camera import Camera
from game.resources.enemy_director import EnemyDirector
from game.resources.mystery_box_session import BoxPhase, MysteryBoxSession
from game.resources.run_stats import RunStats
from game.resources.ui_state import UIState
from game.systems.enemy_spawn import enemy_spawn_system
from game.systems.offscreen_despawn import offscreen_despawn_system
from game.util.buffs import grant_buff, stat_bonus, stat_multiplier
from game.util.factions import is_hostile
from game.util.rng import DEFAULT_RNG

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

# Every launch plays the intro, timed to its audio, then the main menu.
first = Game()
assert first.state is GameState.INTRO
timeline = first.intro.timeline
assert 0 < timeline.impact < timeline.duration
assert timeline.text_fade_in[0] == timeline.impact, "name lands on the hit"
assert timeline.fade_out[1] <= timeline.duration
for _ in range(round(timeline.duration * 60) + 5):
    first.handle_events()
    first.update(1 / 60)
    first.render()
assert first.state is GameState.MENU, first.state

# A keypress skips it.
skipped = Game()
pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
skipped.handle_events()
skipped.update(1 / 60)
assert skipped.state is GameState.MENU

game = Game(play_intro=False)

# The game opens on the main menu; its Play button starts a run.
assert game.state is GameState.MENU and game.player is None
pygame.mouse.get_pos = lambda: (400, 300)  # the dummy driver has no real mouse
pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(400, 300)))
pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(400, 300)))
game.handle_events()
game.update(1 / 60)
assert game.state is GameState.PLAYING and game.player is not None

world = game.world
session = world.get_resource(MysteryBoxSession)
loadout = world.get_component(game.player, Loadout)
wallet = world.get_component(game.player, Wallet)
box = world.get_component(game.mystery_box, MysteryBox)
ui_state = world.get_resource(UIState)
director = world.get_resource(EnemyDirector)
director.backlog = 0
director.timer = math.inf


random.seed(1234)
DEFAULT_RNG.seed(1234)


def step(frames: int = 1):
    for _ in range(frames):
        game.handle_events()
        game.update(1 / 60)
        game.render()


def press(key: int):
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))
    step()


def click(button: int):
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=button))
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, button=button))
    step()


def wait_for_offer():
    for _ in range(120):
        if session.phase is BoxPhase.OFFER:
            return
        step()
    raise AssertionError(f"Box never finished rolling (phase {session.phase})")


def stand_next_to_box():
    box_pos = game.world.get_component(game.mystery_box, Transform).position
    player = game.world.get_component(game.player, Transform)
    player.position = box_pos + pygame.Vector2(45, 0)
    step()


step(120)  # about 2 seconds of game time

# Every gun x rarity builds a valid, never-weaker spec.
for base in ALL_GUNS.values():
    for rarity in Rarity:
        spec = buffed_spec(base, rarity)
        assert spec.id == base.id
        assert spec.damage >= base.damage and spec.fire_rate >= base.fire_rate
        assert spec.magazine_size >= base.magazine_size
        assert spec.pellets >= base.pellets and spec.pierce >= base.pierce
        assert spec.name == base.name  # rarity shows as stars, not in the name

# One star per tier, plain guns none.
assert [rarity_stars(r) for r in Rarity] == [1, 2, 3, 4, 5]
assert rarity_stars(None) == 0

# Pistol-only start, 800 money, box costs 200.
assert [g.spec.id for g in loadout.slots] == ["pistol"], loadout.slots
assert wallet.balance == 800 and box.price == 200

# Open the box.
stand_next_to_box()
press(pygame.K_e)
assert session.phase is BoxPhase.ROLLING and wallet.balance == 600
assert ui_state.blocks_gameplay_input
assert world.get_resource(RunStats).boxes_opened == 1
wait_for_offer()

# Reroll costs 200 more.
press(pygame.K_r)
assert session.phase is BoxPhase.ROLLING and wallet.balance == 200, wallet.balance
assert box.price == 400
wait_for_offer()

# Take with one gun: new gun becomes primary, pistol moves to secondary.
offered = session.offer
old_box_pos = pygame.Vector2(world.get_component(game.mystery_box, Transform).position)
press(pygame.K_e)
assert session.phase is BoxPhase.CLOSED
assert not ui_state.blocks_gameplay_input
assert loadout.slots[0] is offered and loadout.active == 0
assert loadout.slots[1].spec.id == "pistol" and loadout.slots[1].rarity is None
assert box.price == 570, box.price  # (400 + 200) * 0.95

new_box_pos = world.get_component(game.mystery_box, Transform).position
assert new_box_pos.distance_to(old_box_pos) >= 240
points = world.get_component(game.mystery_box, Relocatable).points
assert new_box_pos in points

# Number keys switch slots; F cycles.
press(pygame.K_2)
assert loadout.active == 1
press(pygame.K_1)
assert loadout.active == 0
press(pygame.K_f)
assert loadout.active == 1
press(pygame.K_f)
assert loadout.active == 0

# Full slots: taking swaps out the gun in hand, no questions asked.
wallet.balance = 10_000
press(pygame.K_2)  # hold the pistol
primary = loadout.slots[0]
stand_next_to_box()
press(pygame.K_e)
wait_for_offer()
offered = session.offer
press(pygame.K_e)
assert session.phase is BoxPhase.CLOSED
assert loadout.slots == [primary, offered] and loadout.active == 1
assert box.price == round((570 + 200) * 0.95)

# Walking away (Q) loses the gun and steps the price.
stand_next_to_box()
price = box.price
press(pygame.K_e)
wait_for_offer()
press(pygame.K_q)
assert session.phase is BoxPhase.CLOSED
assert loadout.slots == [primary, offered]
assert box.price == price + 200
assert world.get_resource(RunStats).boxes_opened == 3

# Right click reloads.
gun = loadout.equipped
gun.magazine = 0
gun.reserve = gun.spec.max_reserve
click(3)
assert gun.reloading, "right click should reload"
gun.reload_remaining = 0.001
step()
assert gun.magazine == gun.spec.magazine_size

# Bullets start at the player's center and draw underneath the player.
player_t = world.get_component(game.player, Transform)
before = {e for e, _ in world.query(Projectile)}
gun.cooldown = 0.0
click(1)
(bullet,) = {e for e, _ in world.query(Projectile)} - before
assert world.get_component(bullet, Shape).layer < world.get_component(game.player, Shape).layer
world.destroy_entity(bullet)

# A player bullet hitting something spawns 2-3 sparks.
sparks_before = sum(1 for _ in world.query(Spark))
slow = replace(ALL_GUNS["pistol"], projectile_speed=1.0)
crate_pos = pygame.Vector2(260, 220)
from game.prefabs.crate import spawn_crate  # noqa: E402

crate = spawn_crate(world, crate_pos)
spawn_gun_projectile(world, game.player, crate_pos, 0.0, slow)
step()
assert 2 <= sum(1 for _ in world.query(Spark)) - sparks_before <= 3
if world.is_alive(crate):
    world.destroy_entity(crate)


KILL_SPOT = pygame.Vector2(260, 220)
"""Open floor away from walls, the boxes and the player's spawn."""


# Kills pay the killer's wallet, scaled by the money buff.
def kill_charger():
    enemy = spawn_charger(world, KILL_SPOT, game.player)
    bounty = world.get_component(enemy, Bounty).amount

    # A near-stationary, lethal bullet on top of the charger. Damage, bounty and
    # cleanup all run through Game.update, so a missing system fails the test.
    slow_pistol = replace(ALL_GUNS["pistol"], projectile_speed=1.0)
    spawn_gun_projectile(
        world, game.player, KILL_SPOT, 0.0, slow_pistol, damage_scale=1e9
    )
    step()
    assert not world.is_alive(enemy)
    return bounty


before = wallet.balance
earned_before = wallet.total_earned
kills_before = world.get_resource(RunStats).enemies_killed
gibs_before = sum(1 for _ in world.query(Particle))
bounty = kill_charger()
assert wallet.balance == before + bounty, wallet.balance
assert wallet.total_earned == earned_before + bounty
assert world.get_resource(RunStats).enemies_killed == kills_before + 1
assert sum(1 for _ in world.query(Particle)) - gibs_before >= 6, "enemy gibs"

grant_buff(world, game.player, MONEY_BOOSTS[Rarity.RARE])
before = wallet.balance
bounty = kill_charger()
assert wallet.balance == before + round(bounty * 1.75), wallet.balance

# Dashing spends stamina and stops when it runs out.
stamina = world.get_component(game.player, Stamina)
dash = world.get_component(game.player, Dash)
stamina.current = 2.0
press(pygame.K_SPACE)
assert dash.active, "affordable dash should start"
assert 0.9 < stamina.current < 1.2, stamina.current
step(20)
assert not dash.active, "dash should have ended"
press(pygame.K_SPACE)
assert dash.active, "second affordable dash should start"
assert stamina.current < 0.5, stamina.current
step(20)
press(pygame.K_SPACE)
assert not dash.active, "unaffordable dash should be refused"
assert stamina.current < 1.0

# Extra Stamina raises the regen cap above the base segments.
stamina.current = 2.0
grant_buff(world, game.player, EXTRA_STAMINA)
step(60)  # ~1s of regen at 0.3/s
assert stat_bonus(world, game.player, Stat.STAMINA_SEGMENTS) == 2
assert stamina.current > 2.0, stamina.current

# Expiry goes through ActiveBuffs.tick, then the cap clamps stamina back down.
stamina.current = 4.0
active = world.get_component(game.player, ActiveBuffs)
for buff in active.buffs:
    buff.time_left = 0.001
step()
assert not active.buffs, active.buffs
assert stat_bonus(world, game.player, Stat.STAMINA_SEGMENTS) == 0
assert stamina.current <= 2.0, stamina.current

# Quick Recovery doubles the regen rate.
grant_buff(world, game.player, QUICK_RECOVERY)
stamina.current = 0.0
step()
assert stat_multiplier(world, game.player, Stat.STAMINA_REGEN) == 2.0
assert abs(stamina.current - stamina.regen_rate * 2.0 / 60) < 1e-6, stamina.current

chaser = spawn_chaser(world, KILL_SPOT, game.player)
assert is_hostile(world, chaser, game.player) and is_hostile(world, game.player, chaser)
assert not is_hostile(world, chaser, chaser)
dasher = world.get_component(chaser, RandomDashAI)
dasher.chance, dasher.timer, dasher.max_target_dist_sqr = 1.0, 0.0, math.inf
step()
assert world.get_component(chaser, Dash).active, "chaser should dash"

health = world.get_component(game.player, Health)
before = health.current
world.get_component(chaser, Transform).position = pygame.Vector2(
    world.get_component(game.player, Transform).position
)
step()
assert health.current < before, "chaser contact should hurt"
world.destroy_entity(chaser)

# Splitter: 4 mediums at 25% health, each leaving 2 smalls at 50% of that.
slow_pistol = replace(ALL_GUNS["pistol"], projectile_speed=1.0)


def enemies():
    return {e for e, _ in world.query(Health) if e != game.player}


def kill(entity):
    t = world.get_component(entity, Transform)
    t.position = pygame.Vector2(KILL_SPOT)
    world.get_component(entity, RigidBody).linear_velocity.update(0, 0)
    pos = pygame.Vector2(t.position)
    spawn_gun_projectile(world, game.player, pos, 0.0, slow_pistol, damage_scale=1e9)
    step()
    assert not world.is_alive(entity)


known = enemies()
large = spawn_splitter(world, KILL_SPOT, game.player)
large_hp = world.get_component(large, Health).maximum
kill(large)

mediums = enemies() - known
assert len(mediums) == 4, mediums
for e in mediums:
    assert world.get_component(e, Health).maximum == large_hp * 0.25
    assert world.has_component(e, SplitOnDeath)

kill(next(iter(mediums)))
smalls = enemies() - known - mediums
assert len(smalls) == 2, smalls
for e in smalls:
    assert world.get_component(e, Health).maximum == large_hp * 0.25 * 0.5
    assert not world.has_component(e, SplitOnDeath)

for e in enemies() - known:
    world.destroy_entity(e)

# Survival spawning: off screen, in the band, and ramping up.
assert spawn_interval(600) < spawn_interval(0) and max_enemies(600) > max_enemies(0)

# The opening burst ignores the cap and spawns everything at once.
for e in enemies():
    world.destroy_entity(e)
known = enemies()
director.backlog = INITIAL_ENEMIES
enemy_spawn_system(world, 1 / 60)
assert len(enemies() - known) == INITIAL_ENEMIES and director.backlog == 0
for e in enemies() - known:
    world.destroy_entity(e)
camera = world.get_resource(Camera)
for _ in range(200):  # the position is random, so sample it a lot
    known = enemies()
    director.elapsed, director.timer = 0.0, 0.0
    enemy_spawn_system(world, 1 / 60)
    (spawned,) = enemies() - known
    pos = world.get_component(spawned, Transform).position
    assert not camera.is_circle_visible(pos, SPAWN_MARGIN_MIN - 1)
    assert camera.is_circle_visible(pos, SPAWN_MARGIN_MAX)
    world.destroy_entity(spawned)

# Off-screen enemies give up after the timeout; coming into view resets it.
camera = world.get_resource(Camera)
far = camera.screen_to_world(pygame.Vector2(5000, 5000))
stuck = spawn_chaser(world, far, game.player)
world.add_component(stuck, OffscreenDespawn(timeout=1.0))

offscreen_despawn_system(world, 0.6)
assert world.is_alive(stuck)

world.get_component(stuck, Transform).position = camera.screen_to_world(
    camera.viewport_size / 2
)
offscreen_despawn_system(world, 0.6)
assert world.get_component(stuck, OffscreenDespawn).offscreen_time == 0.0

world.get_component(stuck, Transform).position = far
offscreen_despawn_system(world, 0.6)
assert world.is_alive(stuck)
offscreen_despawn_system(world, 0.6)
assert not world.is_alive(stuck)

step(60)

# Death: the world freezes, the player shakes, shatters, then the stats show.
enemy = spawn_chaser(world, KILL_SPOT, game.player)
world.get_component(enemy, RigidBody).linear_velocity.update(300, 0)
world.get_component(game.player, Health).current = 0
step()
assert game.state is GameState.DYING
frozen_at = pygame.Vector2(world.get_component(enemy, Transform).position)
step(30)
assert world.get_component(enemy, Transform).position == frozen_at, "world should freeze"
step(35)  # past the 1s shake
assert not world.has_component(game.player, Shape), "player should have shattered"
assert any(p.keeps_moving_when_frozen for _, (p,) in world.query(Particle))
step(60 * 3)
assert game.state is GameState.GAME_OVER

# Play (below the stats, at the screen's center + 100px) starts a fresh run.
old_world = world
pygame.mouse.get_pos = lambda: (400, 400)
click(1)
assert game.state is GameState.PLAYING
assert game.world is not old_world
assert game.world.get_resource(RunStats).enemies_killed == 0
assert game.world.has_component(game.player, Shape)
step(30)

print("Smoke test passed")
