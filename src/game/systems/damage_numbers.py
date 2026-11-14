import random

import pygame

from game.components.damage_number import DamageNumber
from game.components.drift import Drift
from game.components.lifetime import Lifetime
from game.components.player import Player
from game.components.shape import Shape
from game.components.transform import Transform
from game.core_ecs.world import World
from game.events.combat import DamageTakenEvent
from game.resources.asset_store import AssetStore
from game.resources.camera import Camera
from game.resources.event_bus import EventBus

NORMAL_COLOR = (255, 255, 255)
PLAYER_HURT_COLOR = (255, 90, 90)
CRIT_COLOR = (255, 200, 40)
SHADOW_COLOR = (0, 0, 0)

NORMAL_SIZE = 22
CRIT_SIZE = 34

NORMAL_LIFETIME = 0.7
CRIT_LIFETIME = 1.0

RISE_SPEED = 90.0
"""Initial upward speed, px/s."""
DRIFT_SPEED = 25.0
"""Max initial sideways speed either way, px/s."""
SPAWN_HEIGHT = 24.0
"""How far above the entity's top a number appears, px. Clears the health bar."""
SPAWN_JITTER = 8.0
"""Max sideways offset either way, px, so simultaneous hits (shotgun pellets) don't stack."""
SLOWDOWN = 3.0
"""Fraction of velocity lost per second."""

FADE_START = 0.6
"""Fraction of the lifetime after which the number fades out."""
CRIT_POP_SCALE = 1.7
"""A critical hit's number starts this much larger..."""
CRIT_POP_TIME = 0.15
"""...and shrinks to its normal size over this many seconds."""


def _style(world: World, taken: DamageTakenEvent):
    """(text, color, size) for a hit."""
    # Never show 0 for a hit that did damage.
    value = max(1, round(taken.amount))

    if taken.critical:
        return f"{value}!", CRIT_COLOR, CRIT_SIZE
    if world.has_component(taken.target, Player):
        return str(value), PLAYER_HURT_COLOR, NORMAL_SIZE
    return str(value), NORMAL_COLOR, NORMAL_SIZE


def damage_number_spawn_system(world: World):
    """Spawns a DamageNumber per DamageTakenEvent."""
    events = world.get_resource(EventBus)

    for taken in events.read(DamageTakenEvent):
        transform = world.try_get_component(taken.target, Transform)
        if transform is None:
            continue

        shape = world.try_get_component(taken.target, Shape)
        top = 0.0 if shape is None else shape.radius * transform.max_scale

        text, color, size = _style(world, taken)
        position = transform.position + pygame.Vector2(
            random.uniform(-SPAWN_JITTER, SPAWN_JITTER), -(top + SPAWN_HEIGHT)
        )

        world.create_entity(
            Transform(position=position),
            DamageNumber(text, color, size, taken.critical),
            Lifetime(CRIT_LIFETIME if taken.critical else NORMAL_LIFETIME),
            Drift(
                velocity=pygame.Vector2(
                    random.uniform(-DRIFT_SPEED, DRIFT_SPEED), -RISE_SPEED
                ),
                drag=SLOWDOWN,
            ),
        )


def _pop_scale(number: DamageNumber, age: float):
    if not number.critical or age >= CRIT_POP_TIME:
        return 1.0
    return 1.0 + (CRIT_POP_SCALE - 1.0) * (1.0 - age / CRIT_POP_TIME)


def _alpha(progress: float):
    if progress <= FADE_START:
        return 255
    return max(0, min(255, round(255 * (1.0 - progress) / (1.0 - FADE_START))))


def damage_number_render_system(world: World, surface: pygame.Surface):
    camera = world.get_resource(Camera)
    assets = world.get_resource(AssetStore)

    for _, (number, transform, life) in world.query(DamageNumber, Transform, Lifetime):
        size = round(number.size * _pop_scale(number, life.age))
        alpha = _alpha(life.progress)

        text = assets.text(number.text, size, number.color)
        shadow = assets.text(number.text, size, SHADOW_COLOR)
        if alpha < 255:
            # Cached surfaces are shared, so fade copies instead.
            text = text.copy()
            shadow = shadow.copy()
            text.set_alpha(alpha)
            shadow.set_alpha(alpha)

        rect = text.get_rect(center=camera.world_to_screen(transform.position))
        offset = 3 if number.critical else 2
        surface.blit(shadow, rect.move(offset, offset))
        surface.blit(text, rect)
