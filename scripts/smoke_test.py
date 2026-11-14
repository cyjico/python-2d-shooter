import os
from dataclasses import replace

import pygame

from game.components.bounty import Bounty
from game.components.buffs import ActiveBuffs, Stat
from game.components.dash import Dash
from game.components.loadout import Loadout, Rarity
from game.components.mystery_box import MysteryBox
from game.components.relocatable import Relocatable
from game.components.stamina import Stamina
from game.components.transform import Transform
from game.components.wallet import Wallet
from game.constants.buffs import EXTRA_STAMINA, MONEY_BOOSTS, QUICK_RECOVERY
from game.constants.gun_buffs import buffed_spec
from game.constants.guns import ALL_GUNS
from game.game import Game
from game.prefabs.enemies import spawn_charger
from game.prefabs.gun_projectile import spawn_gun_projectile
from game.resources.mystery_box_session import BoxPhase, MysteryBoxSession
from game.resources.ui_state import UIState
from game.util.buffs import grant_buff, stat_bonus, stat_multiplier

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

game = Game()


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

world = game.world
session = world.get_resource(MysteryBoxSession)
loadout = world.get_component(game.player, Loadout)
wallet = world.get_component(game.player, Wallet)
box = world.get_component(game.mystery_box, MysteryBox)
ui_state = world.get_resource(UIState)

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


# Stamina buffs: expiring clamps bars back down.
before = stamina.current = 2.0
grant_buff(world, game.player, EXTRA_STAMINA)
step()
assert (
    stamina.segments + stat_bonus(world, game.player, Stat.STAMINA_SEGMENTS) == 4
), stamina.current

stamina.current = 4.0
world.get_component(game.player, ActiveBuffs).buffs.clear()
step()
assert (
    stamina.segments + stat_bonus(world, game.player, Stat.STAMINA_SEGMENTS) == 2
    and stamina.current <= 2.0
), stamina.current

# Quick Recovery doubles the regen rate.
grant_buff(world, game.player, QUICK_RECOVERY)
stamina.current = 0.0
step()
assert stat_multiplier(world, game.player, Stat.STAMINA_REGEN) == 2.0
assert abs(stamina.current - stamina.regen_rate * 2.0 / 60) < 1e-6, stamina.current

step(60)

print("Smoke test passed")
