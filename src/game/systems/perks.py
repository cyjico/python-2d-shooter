"""Perk effects that don't live inside another system: regeneration, on-kill
effects, dash perks and Carnage's explosions."""

import pygame

from game.components.buffs import Flag, Stat
from game.components.drone import Drone
from game.components.faction import Faction, Team
from game.components.health import Health
from game.components.lifetime import Lifetime
from game.components.loadout import Loadout
from game.components.perks import Perks
from game.components.shockwave import Shockwave
from game.components.transform import Transform
from game.constants.perks import (
    CARNAGE_DAMAGE_FRACTION,
    CARNAGE_MIN_DAMAGE,
    CARNAGE_RADIUS,
)
from game.core_ecs.entity import Entity
from game.core_ecs.world import World
from game.events.combat import DamageEvent, DashStartedEvent, EntityDiedEvent
from game.resources.camera import Camera
from game.resources.deferred_damage import DeferredDamage
from game.resources.enemy_director import EnemyDirector, WavePhase
from game.resources.event_bus import EventBus
from game.systems.weapon import finish_reload
from game.util.buffs import has_flag, stat_bonus
from game.util.factions import team_of
from game.util.ownership import owner_of
from game.util.perks import heal

SHOCKWAVE_COLOR = (255, 120, 60)
SHOCKWAVE_TIME = 0.35


def perk_upkeep_system(world: World, dt: float):
    """Regeneration, and Undying recharging between waves."""
    director = world.try_get_resource(EnemyDirector)
    between_waves = director is not None and director.phase is WavePhase.BREAK
    drones = _drone_counts(world)

    for entity, (perks,) in world.query(Perks):
        if between_waves:
            perks.undying_ready = True

        regen = stat_bonus(world, entity, Stat.HEALTH_REGEN) + stat_bonus(
            world, entity, Stat.DRONE_REGEN
        ) * drones.get(entity, 0)
        heal(world, entity, regen * dt)


def _drone_counts(world: World):
    counts: dict[Entity, int] = {}
    for _, (drone,) in world.query(Drone):
        counts[drone.owner] = counts.get(drone.owner, 0) + 1
    return counts


def deferred_damage_system(world: World):
    """Emits last frame's deferred damage (Carnage explosions)."""
    deferred = world.try_get_resource(DeferredDamage)
    if deferred is None or not deferred.pending:
        return
    events = world.get_resource(EventBus)
    for damage in deferred.pending:
        if world.is_alive(damage.target):
            events.emit(damage)
    deferred.pending.clear()


def perk_kill_system(world: World):
    """Scavenger refills the magazine; Carnage blows the dead enemy up.
    Runs before cleanup, while the dead still have their components."""
    for died in world.get_resource(EventBus).read(EntityDiedEvent):
        killer = owner_of(world, died.killer)
        if killer is None or not world.is_alive(killer):
            continue
        if not world.has_component(killer, Perks):
            continue
        if not team_of(world, died.entity) & Team.ENEMY:
            continue

        ammo = round(stat_bonus(world, killer, Stat.AMMO_ON_KILL))
        loadout = world.try_get_component(killer, Loadout)
        gun = loadout.equipped if loadout is not None else None
        if ammo > 0 and gun is not None and not gun.reloading:
            gun.magazine = min(gun.spec.magazine_size, gun.magazine + ammo)

        if has_flag(world, killer, Flag.CARNAGE):
            _explode(world, died.entity, killer)


def _explode(world: World, victim: Entity, killer: Entity):
    transform = world.try_get_component(victim, Transform)
    health = world.try_get_component(victim, Health)
    if transform is None or health is None:
        return
    center = pygame.Vector2(transform.position)
    damage = max(CARNAGE_MIN_DAMAGE, health.maximum * CARNAGE_DAMAGE_FRACTION)

    deferred = world.try_get_resource(DeferredDamage)
    if deferred is None:
        deferred = DeferredDamage()
        world.add_resource(deferred)

    for other, (faction, other_transform, other_health) in world.query(
        Faction, Transform, Health
    ):
        if other == victim or other_health.current <= 0:
            continue
        if not faction.team & Team.ENEMY:
            continue
        if center.distance_squared_to(other_transform.position) <= CARNAGE_RADIUS**2:
            deferred.pending.append(DamageEvent(other, damage, killer))

    world.create_entity(
        Transform(position=center),
        Shockwave(CARNAGE_RADIUS, SHOCKWAVE_COLOR),
        Lifetime(SHOCKWAVE_TIME),
    )


def perk_dash_system(world: World):
    """Blood Rush heals on a dash; Tactical Roll reloads."""
    for started in world.get_resource(EventBus).read(DashStartedEvent):
        entity = started.entity
        heal(world, entity, stat_bonus(world, entity, Stat.DASH_HEAL))

        if has_flag(world, entity, Flag.DASH_RELOAD):
            loadout = world.try_get_component(entity, Loadout)
            gun = loadout.equipped if loadout is not None else None
            if gun is not None and gun.magazine < gun.spec.magazine_size:
                finish_reload(gun)


def shockwave_render_system(world: World, surface: pygame.Surface):
    camera = world.get_resource(Camera)
    for _, (wave, transform, life) in world.query(Shockwave, Transform, Lifetime):
        t = life.progress
        radius = round(wave.radius * (0.3 + 0.7 * t))
        if radius <= 0 or not camera.is_circle_visible(transform.position, radius):
            continue
        size = 2 * radius + 8
        ring = pygame.Surface((size, size), pygame.SRCALPHA)
        alpha = round(220 * (1.0 - t))
        width = max(2, round(6 * (1.0 - t)))
        pygame.draw.circle(
            ring, (*wave.color, alpha), (size // 2, size // 2), radius, width=width
        )
        center = camera.world_to_screen(transform.position)
        surface.blit(ring, ring.get_rect(center=(round(center.x), round(center.y))))
