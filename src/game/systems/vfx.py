"""Particles: bullet sparks, enemy gibs and the player's death shards."""

import math
import random

import pygame

from game.components.faction import Team
from game.components.particle import Particle, Spark
from game.components.player import Player
from game.components.shape import Shape
from game.components.transform import Transform
from game.constants import layers, vfx
from game.core_ecs.world import World
from game.events.combat import EntityDiedEvent, ProjectileHitEvent
from game.resources.camera import Camera
from game.resources.event_bus import EventBus
from game.util.factions import team_of
from game.util.geometry import regular_polygon, rot_to_vec2
from game.util.ownership import owner_of
from game.util.rng import resolve_rng


def particle_system(world: World, dt: float, frozen: bool = False):
    """Moves, spins, shrinks and expires particles.

    While `frozen`, only particles marked `keeps_moving_when_frozen` update.
    """
    for entity, (particle, transform) in world.query(Particle, Transform):
        if frozen and not particle.keeps_moving_when_frozen:
            continue

        particle.age += dt
        if particle.age >= particle.duration:
            world.destroy_entity(entity)
            continue

        transform.position += particle.velocity * dt
        transform.rotation += particle.spin * dt
        particle.velocity *= max(0.0, 1.0 - particle.drag * dt)

        if particle.progress > particle.shrink_start:
            remaining = (1.0 - particle.progress) / (1.0 - particle.shrink_start)
            transform.scale = (remaining, remaining)


# --- Sparks ---


def spark_spawn_system(world: World, rng: random.Random | None = None):
    """A few sparks where a player's bullet hits something, flying back
    toward the shooter."""
    rng = resolve_rng(rng)

    for hit in world.get_resource(EventBus).read(ProjectileHitEvent):
        # Drones count: their sparks are the player's too.
        if not world.has_component(owner_of(world, hit.shooter), Player):
            continue

        back = -hit.direction
        for _ in range(rng.randint(*vfx.SPARK_COUNT)):
            angle = rng.uniform(-vfx.SPARK_CONE, vfx.SPARK_CONE)
            world.create_entity(
                Transform(position=pygame.Vector2(hit.position)),
                Particle(
                    duration=rng.uniform(*vfx.SPARK_DURATION),
                    velocity=back.rotate_rad(angle) * rng.uniform(*vfx.SPARK_SPEED),
                    drag=vfx.SPARK_DRAG,
                ),
                Spark(length=rng.uniform(*vfx.SPARK_LENGTH), color=vfx.SPARK_COLOR),
            )


def spark_render_system(world: World, surface: pygame.Surface):
    camera = world.get_resource(Camera)

    for _, (spark, particle, transform) in world.query(Spark, Particle, Transform):
        if particle.velocity.length_squared() == 0:
            continue

        length = spark.length * (1.0 - particle.progress)
        if length < 0.5 or not camera.is_circle_visible(transform.position, length):
            continue

        head = camera.world_to_screen(transform.position)
        tail = head - particle.velocity.normalize() * length
        pygame.draw.line(surface, spark.color, head, tail, vfx.SPARK_WIDTH)


# --- Gibs ---


def gib_spawn_system(world: World, rng: random.Random | None = None):
    """Splatters small hexagons and circles when an enemy dies.

    Must run while the dead still exist (before death cleanup).
    """
    rng = resolve_rng(rng)

    for died in world.get_resource(EventBus).read(EntityDiedEvent):
        if not team_of(world, died.entity) & Team.ENEMY:
            continue
        transform = world.try_get_component(died.entity, Transform)
        shape = world.try_get_component(died.entity, Shape)
        if transform is None or shape is None:
            continue

        enemy_radius = shape.radius * transform.max_scale
        color = tuple(round(c * vfx.GIB_DARKEN) for c in shape.color)

        for _ in range(rng.randint(*vfx.GIB_COUNT)):
            # Area scales with radius squared.
            radius = enemy_radius * math.sqrt(rng.uniform(*vfx.GIB_AREA))
            sides = rng.choice((6, 12))  # hexagon or (near enough) circle
            direction = rot_to_vec2(rng.uniform(0, math.tau))

            world.create_entity(
                Transform(
                    position=transform.position + direction * enemy_radius * 0.3,
                    rotation=rng.uniform(0, math.tau),
                ),
                Shape(regular_polygon(sides, radius), color, layer=layers.GIBS),
                Particle(
                    duration=rng.uniform(*vfx.GIB_DURATION),
                    velocity=direction * rng.uniform(*vfx.GIB_SPEED),
                    drag=vfx.GIB_DRAG,
                    spin=rng.uniform(-vfx.GIB_SPIN, vfx.GIB_SPIN),
                    shrink_start=vfx.GIB_SHRINK_START,
                ),
            )


# --- Shattering ---


def _split(triangle: list[pygame.Vector2]):
    """Halves a triangle through the midpoint of its longest side."""
    a, b, c = triangle
    # Rotate so (a, b) is the longest side.
    for _ in range(3):
        if (b - a).length_squared() >= max(
            (c - b).length_squared(), (a - c).length_squared()
        ):
            break
        a, b, c = b, c, a
    mid = (a + b) / 2
    return [[a, mid, c], [mid, b, c]]


def shatter(world: World, entity, rng: random.Random | None = None):
    """Replaces `entity`'s look with shards flying outward, and hides it.

    The shards keep moving while the world is frozen.
    """
    rng = resolve_rng(rng)
    transform = world.get_component(entity, Transform)
    shape = world.get_component(entity, Shape)

    corners = transform.apply_all(shape.vertices)
    center = sum(corners, pygame.Vector2()) / len(corners)

    # Fan of triangles from the center, each halved a few times.
    pieces = [
        [center, corners[i], corners[(i + 1) % len(corners)]]
        for i in range(len(corners))
    ]
    for _ in range(vfx.SHARD_SPLITS):
        pieces = [half for piece in pieces for half in _split(piece)]

    for piece in pieces:
        middle = sum(piece, pygame.Vector2()) / 3
        outward = middle - center
        if outward.length_squared() == 0:
            outward = rot_to_vec2(rng.uniform(0, math.tau))
        outward = outward.normalize().rotate_rad(rng.uniform(-0.4, 0.4))

        world.create_entity(
            Transform(position=middle),
            Shape(tuple(p - middle for p in piece), shape.color, shape.layer),
            Particle(
                duration=rng.uniform(*vfx.SHARD_DURATION),
                velocity=outward * rng.uniform(*vfx.SHARD_SPEED),
                drag=vfx.SHARD_DRAG,
                spin=rng.uniform(-vfx.SHARD_SPIN, vfx.SHARD_SPIN),
                shrink_start=vfx.SHARD_SHRINK_START,
                keeps_moving_when_frozen=True,
            ),
        )

    world.remove_component(entity, Shape)
