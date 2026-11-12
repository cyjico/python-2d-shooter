import math
import random

from game.components.loadout import FireMode, Gun, Loadout
from game.components.transform import Transform
from game.components.weapon_intent import WeaponIntent
from game.core_ecs.entity import Entity
from game.core_ecs.world import World
from game.prefabs.gun_projectile import spawn_gun_projectile


def weapon_system(world: World, dt: float):
    for entity, (loadout, intent, transform) in world.query(
        Loadout, WeaponIntent, Transform
    ):
        # Holstered weapons still cool down.
        for weapon in loadout.slots:
            weapon.cooldown = max(0.0, weapon.cooldown - dt)

        if intent.switch:
            loadout.cycle(intent.switch)

        weapon = loadout.equipped
        if weapon is None:
            continue

        if weapon.reloading:
            weapon.reload_remaining -= dt

            if weapon.reload_remaining <= 0:
                _finish_reload(weapon)

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


def _finish_reload(gun: Gun):
    gun.reload_remaining = 0.0
    taken = min(gun.spec.magazine_size - gun.magazine, gun.reserve)
    gun.magazine += taken
    gun.reserve -= taken


def _fire(
    world: World, shooter: Entity, transform: Transform, loadout: Loadout, gun: Gun
):
    spec = gun.spec
    gun.magazine -= 1
    gun.cooldown = 1.0 / spec.fire_rate

    origin = transform.apply(loadout.muzzle)
    for _ in range(spec.pellets):
        deviation = math.radians(random.uniform(-spec.spread, spec.spread))
        spawn_gun_projectile(
            world, shooter, origin, transform.rotation + deviation, spec
        )

    # Auto-reload when the magazine runs dry.
    if gun.magazine == 0 and gun.can_reload:
        _start_reload(gun)
