import random

from game.components.ai import AI
from game.components.ai.shooter import ShooterAI
from game.components.loadout import Gun, Loadout
from game.components.mover import Mover
from game.components.transform import Transform
from game.components.weapon_intent import WeaponIntent
from game.core_ecs.world import World
from game.util.geometry import angle_of
from game.util.numerics import wrap_angle
from game.util.raycast import raycast_static_bundle
from game.util.rng import resolve_rng


def shooter_ai_system(world: World, dt: float, rng: random.Random | None = None):
    """Faces the target and fills in the WeaponIntent for ShooterAI.

    Runs after the movement AIs: they face where they walk, this overrides it.
    """
    rng = resolve_rng(rng)

    for ent, (shooter, ai, loadout, intent) in world.query(
        ShooterAI, AI, Loadout, WeaponIntent
    ):
        intent.fire_held = intent.fire_pressed = intent.reload = False

        gun = loadout.equipped
        if ai.target is None or gun is None:
            continue

        _keep_stocked(gun)

        shooter.timer -= dt
        if shooter.timer <= 0:
            shooter.firing = not shooter.firing
            shooter.timer = rng.uniform(
                *(shooter.burst_time if shooter.firing else shooter.rest_time)
            )

        transform = world.get_component(ent, Transform)
        toward = world.get_component(ai.target, Transform).position - transform.position
        dist_sqr = toward.length_squared()
        if dist_sqr == 0:
            continue

        aim = angle_of(toward)
        world.get_component(ent, Mover).face_angle = aim

        # Top off between bursts instead of running dry mid-burst.
        if not shooter.firing:
            intent.reload = gun.magazine < gun.spec.magazine_size
            continue

        if dist_sqr > (gun.spec.max_range * shooter.range_fraction) ** 2:
            continue
        if abs(wrap_angle(aim - transform.rotation)) > shooter.aim_tolerance:
            continue
        # Don't waste the burst on a wall.
        if raycast_static_bundle(
            world, transform.position, toward.normalize(), dist_sqr**0.5
        ):
            continue

        intent.fire_held = True
        # Semi-auto guns fire on presses; the weapon's cooldown sets the pace.
        intent.fire_pressed = True


def _keep_stocked(gun: Gun):
    """Enemies never run out of reserve ammo."""
    gun.reserve = gun.spec.max_reserve
