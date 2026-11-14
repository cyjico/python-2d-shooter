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
    SPAWN_MARGIN_MAX,
    SPAWN_MARGIN_MIN,
    max_enemies,
    spawn_interval,
)
from game.constants.gun_buffs import buffed_spec
from game.constants.guns import ALL_GUNS
from game.game import Game
from game.prefabs.enemies import spawn_charger, spawn_chaser, spawn_splitter
from game.prefabs.gun_projectile import spawn_gun_projectile
from game.resources.camera import Camera
from game.resources.enemy_director import EnemyDirector
from game.resources.mystery_box_session import BoxPhase, MysteryBoxSession
from game.resources.ui_state import UIState
from game.systems.enemy_spawn import enemy_spawn_system
from game.systems.offscreen_despawn import offscreen_despawn_system
from game.util.buffs import grant_buff, stat_bonus, stat_multiplier
from game.util.factions import is_hostile
from game.util.rng import DEFAULT_RNG

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

game = Game()

world = game.world
session = world.get_resource(MysteryBoxSession)
loadout = world.get_component(game.player, Loadout)
wallet = world.get_component(game.player, Wallet)
box = world.get_component(game.mystery_box, MysteryBox)
ui_state = world.get_resource(UIState)
director = world.get_resource(EnemyDirector)
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

# Pistol-only start, 800 money, box costs 200.
assert [g.spec.id for g in loadout.slots] == ["pistol"], loadout.slots
assert wallet.balance == 800 and box.price == 200

# Open the box.
stand_next_to_box()
press(pygame.K_e)
assert session.phase is BoxPhase.ROLLING and wallet.balance == 600
assert ui_state.blocks_gameplay_input
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

# Number keys switch slots.
press(pygame.K_2)
assert loadout.active == 1
press(pygame.K_1)
assert loadout.active == 0

# Full slots: taking asks which slot to replace.
wallet.balance = 10_000
stand_next_to_box()
press(pygame.K_e)
wait_for_offer()
offered = session.offer
primary = loadout.slots[0]
press(pygame.K_e)
assert session.phase is BoxPhase.CHOOSE_SLOT
press(pygame.K_ESCAPE)  # back
assert session.phase is BoxPhase.OFFER
press(pygame.K_e)
press(pygame.K_2)
assert session.phase is BoxPhase.CLOSED
assert loadout.slots == [primary, offered] and loadout.active == 1
assert box.price == round((570 + 200) * 0.95)

# Walking away loses the gun and steps the price.
stand_next_to_box()
price = box.price
press(pygame.K_e)
wait_for_offer()
press(pygame.K_ESCAPE)
assert session.phase is BoxPhase.CLOSED
assert loadout.slots == [primary, offered]
assert box.price == price + 200


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
bounty = kill_charger()
assert wallet.balance == before + bounty, wallet.balance

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

for e in enemies():
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

print("Smoke test passed")
