import math

import pygame

from game.components.buffs import Flag, Stat
from game.components.drone import Drone
from game.components.faction import Faction, Team
from game.components.health import Health
from game.components.loadout import Gun, Loadout
from game.components.perks import Perks
from game.components.shape import Shape
from game.components.transform import Transform
from game.components.weapon_intent import WeaponIntent
from game.constants.perks import (
    DRONE_COLOR,
    DRONE_GUN,
    DRONE_ORBIT_RADIUS,
    DRONE_ORBIT_SPEED,
    DRONE_RANGE,
)
from game.core_ecs.entity import Entity
from game.core_ecs.world import World
from game.util.buffs import has_flag, stat_bonus, stat_multiplier
from game.util.geometry import angle_of
from game.util.raycast import raycast_static_bundle

DRONE_VERTICES = (
    pygame.Vector2(9, 0),
    pygame.Vector2(0, -6),
    pygame.Vector2(-6, 0),
    pygame.Vector2(0, 6),
)
DRONE_LAYER = 1
"""Over the player, so the ring stays visible when it passes in front."""
SPREAD_BULLETS = 2
"""Extra bullets per drone shot with Hive Mind."""


def drone_system(world: World, dt: float):
    """Keeps each owner's drone count in line with their perks, turns the ring,
    and aims and fires every drone at the nearest enemy in range."""
    rings = _rings(world)

    for owner, (_, owner_transform) in world.query(Perks, Transform):
        want = max(0, round(stat_bonus(world, owner, Stat.DRONES)))
        ring = rings.pop(owner, [])
        while len(ring) > want:
            world.destroy_entity(ring.pop())
        while len(ring) < want:
            phase = world.get_component(ring[0], Drone).phase if ring else 0.0
            ring.append(_spawn_drone(world, owner, len(ring), phase, owner_transform))

        for drone_entity in ring:
            world.get_component(drone_entity, Drone).phase += DRONE_ORBIT_SPEED * dt
        _place(world, ring, owner_transform)
        for drone_entity in ring:
            _aim_and_fire(world, owner, drone_entity, owner_transform)

    # Owners that are gone (or lost their perks) take their drones with them.
    for ring in rings.values():
        for drone_entity in ring:
            world.destroy_entity(drone_entity)


def drone_follow_system(world: World):
    """Puts drones back around their owner after the owner moved this frame."""
    for owner, ring in _rings(world).items():
        transform = world.try_get_component(owner, Transform)
        if transform is not None:
            _place(world, ring, transform)


def _rings(world: World):
    """Each owner's drones, ordered by index."""
    rings: dict[Entity, list[Entity]] = {}
    for entity, (drone,) in world.query(Drone):
        rings.setdefault(drone.owner, []).append(entity)
    for ring in rings.values():
        ring.sort(key=lambda e: world.get_component(e, Drone).index)
    return rings


def _spawn_drone(
    world: World, owner: Entity, index: int, phase: float, owner_transform: Transform
):
    return world.create_entity(
        Drone(owner, index, phase),
        Faction(Team.PLAYER),
        Transform(position=pygame.Vector2(owner_transform.position)),
        Shape(vertices=DRONE_VERTICES, color=DRONE_COLOR, layer=DRONE_LAYER),
        Loadout(slots=[Gun.full(DRONE_GUN)]),
        WeaponIntent(),
    )


def _place(world: World, ring: list[Entity], owner_transform: Transform):
    for slot, entity in enumerate(ring):
        drone = world.get_component(entity, Drone)
        drone.index = slot
        angle = drone.phase + math.tau * slot / len(ring)
        offset = pygame.Vector2(math.cos(angle), math.sin(angle)) * DRONE_ORBIT_RADIUS
        world.get_component(entity, Transform).position = (
            owner_transform.position + offset
        )


def _aim_and_fire(
    world: World, owner: Entity, entity: Entity, owner_transform: Transform
):
    transform = world.get_component(entity, Transform)
    loadout = world.get_component(entity, Loadout)
    intent = world.get_component(entity, WeaponIntent)

    # Drones fight with their owner's upgrades.
    loadout.damage_scale = stat_multiplier(world, owner, Stat.DAMAGE) * (
        stat_multiplier(world, owner, Stat.DRONE_DAMAGE)
    )
    loadout.fire_rate_scale = stat_multiplier(world, owner, Stat.DRONE_FIRE_RATE)
    loadout.pierce_bonus = round(stat_bonus(world, owner, Stat.DRONE_PIERCE))
    loadout.extra_projectiles = (
        SPREAD_BULLETS if has_flag(world, owner, Flag.DRONE_SPREAD) else 0
    )
    gun = loadout.equipped
    if gun is not None:
        # Never runs dry.
        gun.magazine = gun.spec.magazine_size

    target = _nearest_target(world, transform.position)
    intent.fire_held = intent.fire_pressed = target is not None
    if target is not None:
        transform.rotation = angle_of(target - transform.position)
    else:
        # Point along the orbit.
        outward = transform.position - owner_transform.position
        if outward.length_squared() > 0:
            transform.rotation = angle_of(outward) + math.pi / 2


def _nearest_target(world: World, position: pygame.Vector2):
    """Position of the closest enemy in range with nothing solid in the way."""
    in_range = []
    for entity, (faction, transform, _) in world.query(Faction, Transform, Health):
        if not faction.team & Team.ENEMY:
            continue
        dist_sqr = position.distance_squared_to(transform.position)
        if dist_sqr <= DRONE_RANGE**2:
            in_range.append((dist_sqr, transform.position))

    for dist_sqr, target in sorted(in_range, key=lambda item: item[0]):
        if dist_sqr == 0:
            continue
        toward = (target - position).normalize()
        if not raycast_static_bundle(world, position, toward, dist_sqr**0.5):
            return pygame.Vector2(target)
    return None
