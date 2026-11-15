import math
import random

from game.components.buffs import Stat
from game.components.loadout import FireMode, Gun, Loadout
from game.components.transform import Transform
from game.components.weapon_intent import WeaponIntent
from game.constants.perks import EXTRA_PROJECTILE_SPREAD
from game.core_ecs.entity import Entity
from game.core_ecs.world import World
from game.prefabs.gun_projectile import spawn_gun_projectile
from game.util.buffs import stat_bonus, stat_multiplier
from game.util.perks import berserk_multiplier


def weapon_system(world: World, dt: float):
    for entity, (loadout, intent, transform) in world.query(
        Loadout, WeaponIntent, Transform
    ):
        # Holstered weapons still cool down.
        for weapon in loadout.slots:
            weapon.cooldown = max(0.0, weapon.cooldown - dt)

        if intent.select is not None:
            loadout.equip(intent.select)
        if intent.switch:
            loadout.cycle(intent.switch)

        weapon = loadout.equipped
        if weapon is None:
            continue

        if weapon.reloading:
            # Counts down faster instead of starting shorter, so the reload
            # ring still goes from empty to full.
            weapon.reload_remaining -= dt * stat_multiplier(
                world, entity, Stat.RELOAD_SPEED
            )

            if weapon.reload_remaining <= 0:
                finish_reload(weapon)

            # No shooting mid-reload.
            continue

        if intent.reload and weapon.can_reload:
            _start_reload(weapon)
            continue

        wants_fire = (
            intent.fire_held or intent.fire_pressed
            if weapon.spec.fire_mode is FireMode.AUTO
            else intent.fire_pressed
        )
        if wants_fire and weapon.can_fire:
            _fire(world, entity, transform, loadout, weapon)


def _start_reload(gun: Gun):
    gun.reload_remaining = gun.spec.reload_time


def finish_reload(gun: Gun):
    """Moves ammo from the reserve into the magazine, ending any reload."""
    gun.reload_remaining = 0.0
    taken = min(gun.spec.magazine_size - gun.magazine, gun.reserve)
    gun.magazine += taken
    gun.reserve -= taken


def _fan_offsets(count: int):
    """Angles, in degrees, of `count` extra bullets: alternating sides,
    widening (+10, -10, +20, -20, ...)."""
    return [
        EXTRA_PROJECTILE_SPREAD * (i // 2 + 1) * (1 if i % 2 == 0 else -1)
        for i in range(count)
    ]


def _fire(
    world: World, shooter: Entity, transform: Transform, loadout: Loadout, gun: Gun
):
    spec = gun.spec
    gun.magazine -= 1
    fire_rate = (
        spec.fire_rate
        * loadout.fire_rate_scale
        * stat_multiplier(world, shooter, Stat.FIRE_RATE)
    )
    gun.cooldown = 1.0 / fire_rate

    origin = transform.apply(loadout.muzzle)
    damage_scale = (
        loadout.damage_scale
        * stat_multiplier(world, shooter, Stat.DAMAGE)
        * berserk_multiplier(world, shooter)
    )
    pierce = (
        spec.pierce
        + loadout.pierce_bonus
        + round(stat_bonus(world, shooter, Stat.PIERCE))
    )
    crit_chance = min(
        1.0, spec.crit_chance + stat_bonus(world, shooter, Stat.CRIT_CHANCE)
    )
    crit_multiplier = spec.crit_multiplier + stat_bonus(
        world, shooter, Stat.CRIT_DAMAGE
    )

    def shoot(angle: float):
        spawn_gun_projectile(
            world,
            shooter,
            origin,
            angle,
            spec,
            damage_scale,
            loadout.knockback_scale,
            pierce=pierce,
            crit_chance=crit_chance,
            crit_multiplier=crit_multiplier,
        )

    for _ in range(spec.pellets):
        deviation = math.radians(random.uniform(-spec.spread, spec.spread))
        shoot(transform.rotation + deviation)

    # Extra bullets (Bullet Hell, drone spread): one each, fanned out.
    extra = loadout.extra_projectiles + round(
        stat_bonus(world, shooter, Stat.EXTRA_PROJECTILES)
    )
    for offset in _fan_offsets(extra):
        shoot(transform.rotation + math.radians(offset))

    # Auto-reload when the magazine runs dry.
    if gun.magazine == 0 and gun.can_reload:
        _start_reload(gun)
