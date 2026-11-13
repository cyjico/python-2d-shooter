import random

import pygame

from game.components.damage_number import DamageNumber
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


def damage_number_spawn_system(world: World):
    """Spawns a DamageNumber per DamageTakenEvent. Run after health_system and
    before death_cleanup_system, so the damaged entity still exists."""
    events = world.get_resource(EventBus)

    for taken in events.read(DamageTakenEvent):
        transform = world.try_get_component(taken.target, Transform)
        if transform is None:
            continue

        shape = world.try_get_component(taken.target, Shape)
        top = 0.0 if shape is None else shape.radius * max(map(abs, transform.scale))

        # Never show 0 for a hit that did damage.
        value = max(1, round(taken.amount))

        if taken.critical:
            text, color, size = f"{value}!", CRIT_COLOR, CRIT_SIZE
        elif world.has_component(taken.target, Player):
            text, color, size = str(value), PLAYER_HURT_COLOR, NORMAL_SIZE
        else:
            text, color, size = str(value), NORMAL_COLOR, NORMAL_SIZE

        position = transform.position + pygame.Vector2(
            random.uniform(-SPAWN_JITTER, SPAWN_JITTER), -(top + SPAWN_HEIGHT)
        )

        world.create_entity(
            Transform(position=position),
            DamageNumber(
                text=text,
                color=color,
                size=size,
                lifetime=CRIT_LIFETIME if taken.critical else NORMAL_LIFETIME,
                critical=taken.critical,
                velocity=pygame.Vector2(
                    random.uniform(-DRIFT_SPEED, DRIFT_SPEED), -RISE_SPEED
                ),
            ),
        )


def damage_number_system(world: World, dt: float):
    """Moves DamageNumbers and destroys expired ones."""
    for entity, (number, transform) in world.query(DamageNumber, Transform):
        number.age += dt
        if number.age >= number.lifetime:
            world.destroy_entity(entity)
            continue

        transform.position += number.velocity * dt
        number.velocity *= max(0.0, 1.0 - SLOWDOWN * dt)


def damage_number_render_system(world: World, surface: pygame.Surface):
    camera = world.get_resource(Camera)
    assets = world.get_resource(AssetStore)

    for _, (number, transform) in world.query(DamageNumber, Transform):
        progress = number.age / number.lifetime

        scale = 1.0
        if number.critical and number.age < CRIT_POP_TIME:
            scale += (CRIT_POP_SCALE - 1.0) * (1.0 - number.age / CRIT_POP_TIME)
        size = round(number.size * scale)

        alpha = 255
        if progress > FADE_START:
            alpha = round(255 * (1.0 - progress) / (1.0 - FADE_START))
            alpha = max(0, min(255, alpha))

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
