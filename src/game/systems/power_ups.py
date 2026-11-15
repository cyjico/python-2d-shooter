"""Power-ups: killed enemies sometimes drop one; the player walks over it to
use it. Med Kit heals, Max Ammo refills every gun, Shield absorbs damage, Nuke
kills every enemy alive."""

import math
import random

import pygame

from game.components.faction import Faction, Team
from game.components.health import Health
from game.components.lifetime import Lifetime
from game.components.loadout import Loadout
from game.components.player import Player
from game.components.power_up import PowerUp, PowerUpKind, ScreenFlash
from game.components.transform import Transform
from game.constants.power_ups import (
    BLINK_TIME,
    DROP_CHANCE,
    LIFETIME,
    MAX_DROPS_PER_WAVE,
    MED_KIT_HEAL,
    NUKE_CASH,
    NUKE_FLASH_TIME,
    PICKUP_RADIUS,
    POWER_UPS,
    SHIELD_BUFF,
)
from game.core_ecs.entity import Entity
from game.core_ecs.world import World
from game.events.combat import EntityDiedEvent
from game.resources.asset_store import AssetStore
from game.resources.camera import Camera
from game.resources.enemy_director import EnemyDirector
from game.resources.event_bus import EventBus
from game.resources.power_up_drops import PowerUpDrops
from game.systems.damage_numbers import spawn_floating_number
from game.util.buffs import grant_buff
from game.util.factions import team_of
from game.util.money import earn_money
from game.util.ownership import owner_of
from game.util.perks import heal
from game.util.rng import resolve_rng

ICON_RADIUS = 13
BOB_HEIGHT = 3.0
BOB_SPEED = 3.0
BLINK_RATE = 8.0
"""On/off switches per second while blinking."""
OUTLINE_COLOR = (20, 20, 20)
SYMBOL_COLOR = (20, 20, 20)
ANNOUNCE_SIZE = 26


def roll_power_up(rng: random.Random):
    kinds = list(POWER_UPS)
    return rng.choices(kinds, weights=[POWER_UPS[k].weight for k in kinds])[0]


def spawn_power_up(world: World, kind: PowerUpKind, position: pygame.Vector2):
    return world.create_entity(
        Transform(position=pygame.Vector2(position)),
        PowerUp(kind),
        Lifetime(LIFETIME),
    )


def power_up_drop_system(world: World, rng: random.Random | None = None):
    """Enemies the player (or their drones) kill sometimes drop a power-up.
    Runs before cleanup, while the dead still have a Transform."""
    rng = resolve_rng(rng)
    drops = world.try_get_resource(PowerUpDrops)
    if drops is None:
        return
    director = world.try_get_resource(EnemyDirector)
    wave = director.wave if director is not None else 0
    if drops.wave != wave:
        drops.wave, drops.dropped = wave, 0

    for died in world.get_resource(EventBus).read(EntityDiedEvent):
        if drops.dropped >= MAX_DROPS_PER_WAVE:
            return
        killer = owner_of(world, died.killer)
        if killer is None or not world.has_component(killer, Player):
            continue
        if not team_of(world, died.entity) & Team.ENEMY:
            continue
        transform = world.try_get_component(died.entity, Transform)
        if transform is None or rng.random() >= DROP_CHANCE:
            continue
        spawn_power_up(world, roll_power_up(rng), transform.position)
        drops.dropped += 1


def power_up_pickup_system(world: World):
    """The player collects power-ups they touch. A nuke's deaths are emitted
    here, before the damage phase, so bounties, gibs and cleanup see them."""
    player = next(iter(world.query(Player, Transform)), None)
    if player is None:
        return
    entity, (_, player_transform) = player
    health = world.try_get_component(entity, Health)
    if health is not None and health.current <= 0:
        return

    for pickup, (power_up, transform) in world.query(PowerUp, Transform):
        if (
            player_transform.position.distance_squared_to(transform.position)
            > PICKUP_RADIUS**2
        ):
            continue
        _apply(world, entity, power_up.kind)
        world.destroy_entity(pickup)
        info = POWER_UPS[power_up.kind]
        spawn_floating_number(
            world, entity, f"{info.name.upper()}!", info.color, ANNOUNCE_SIZE
        )


def _apply(world: World, player: Entity, kind: PowerUpKind):
    match kind:
        case PowerUpKind.MED_KIT:
            health = world.try_get_component(player, Health)
            if health is not None:
                heal(world, player, health.maximum * MED_KIT_HEAL)
        case PowerUpKind.MAX_AMMO:
            loadout = world.try_get_component(player, Loadout)
            if loadout is not None:
                for gun in loadout.slots:
                    gun.refill()
        case PowerUpKind.SHIELD:
            grant_buff(world, player, SHIELD_BUFF)
        case PowerUpKind.NUKE:
            _nuke(world, player)


def _nuke(world: World, player: Entity):
    """Kills every enemy alive, even one that can't be hurt right now (a
    charger winding up). No killer: no bounties or drops, a flat payout instead."""
    events = world.get_resource(EventBus)
    for enemy, (faction, health) in world.query(Faction, Health):
        if faction.team & Team.ENEMY and health.current > 0:
            health.current = 0
            events.emit(EntityDiedEvent(enemy, None))
    earn_money(world, player, NUKE_CASH)
    world.create_entity(ScreenFlash((255, 240, 220)), Lifetime(NUKE_FLASH_TIME))


def power_up_render_system(world: World, surface: pygame.Surface):
    camera = world.get_resource(Camera)
    assets = world.get_resource(AssetStore)

    for _, (power_up, transform, life) in world.query(PowerUp, Transform, Lifetime):
        remaining = life.duration - life.age
        if remaining < BLINK_TIME and int(life.age * BLINK_RATE) % 2:
            continue
        if not camera.is_circle_visible(transform.position, ICON_RADIUS + 30):
            continue

        info = POWER_UPS[power_up.kind]
        center = camera.world_to_screen(transform.position)
        center.y += math.sin(life.age * BOB_SPEED) * BOB_HEIGHT
        x, y = round(center.x), round(center.y)

        # Pulsing glow.
        pulse = 0.5 + 0.5 * math.sin(life.age * 5)
        glow_radius = ICON_RADIUS + 5 + round(3 * pulse)
        glow = pygame.Surface((2 * glow_radius + 2,) * 2, pygame.SRCALPHA)
        pygame.draw.circle(
            glow,
            (*info.color, round(60 + 60 * pulse)),
            (glow_radius + 1,) * 2,
            glow_radius,
        )
        surface.blit(glow, glow.get_rect(center=(x, y)))

        pygame.draw.circle(surface, info.color, (x, y), ICON_RADIUS)
        pygame.draw.circle(surface, OUTLINE_COLOR, (x, y), ICON_RADIUS, width=2)
        symbol = assets.text(info.symbol, 20, SYMBOL_COLOR)
        surface.blit(symbol, symbol.get_rect(center=(x, y)))

        name = assets.text(info.name, 14, info.color)
        shadow = assets.text(info.name, 14, OUTLINE_COLOR)
        rect = name.get_rect(midtop=(x, y + ICON_RADIUS + 4))
        surface.blit(shadow, rect.move(1, 1))
        surface.blit(name, rect)


def screen_flash_render_system(world: World, surface: pygame.Surface):
    for _, (flash, life) in world.query(ScreenFlash, Lifetime):
        alpha = round(flash.alpha * (1.0 - life.progress))
        if alpha <= 0:
            continue
        overlay = pygame.Surface(surface.get_size())
        overlay.fill(flash.color)
        overlay.set_alpha(alpha)
        surface.blit(overlay, (0, 0))
