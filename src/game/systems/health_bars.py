import pygame

from game.components.buffs import ActiveBuffs
from game.components.health import Health
from game.components.shape import Shape
from game.components.transform import Transform
from game.core_ecs.world import World
from game.resources.camera import Camera

MIN_WIDTH = 24
HEIGHT = 5
GAP = 8
"""Space between the top of the entity and the bar, px."""

BACKGROUND_COLOR = (40, 40, 40)
BORDER_COLOR = (0, 0, 0)
HIGH_COLOR = (90, 220, 90)
MID_COLOR = (240, 200, 60)
LOW_COLOR = (230, 70, 60)
BONUS_COLOR = (90, 200, 255)
"""Bonus health from buffs, drawn after the regular health."""


def _fill_color(fraction: float):
    if fraction > 0.5:
        return HIGH_COLOR
    if fraction > 0.25:
        return MID_COLOR
    return LOW_COLOR


def health_bar_render_system(world: World, surface: pygame.Surface):
    """Draws a health bar above every entity with Health and a Shape."""
    camera = world.get_resource(Camera)

    for entity, (health, transform, shape) in world.query(Health, Transform, Shape):
        if health.maximum <= 0:
            continue

        # Bounding radius, so the bar doesn't bob as the shape rotates.
        radius = shape.radius * max(map(abs, transform.scale))
        if not camera.is_circle_visible(transform.position, radius + GAP + HEIGHT):
            continue

        center = camera.world_to_screen(transform.position)
        width = max(MIN_WIDTH, round(2 * radius))
        bar = pygame.Rect(0, 0, width, HEIGHT)
        bar.midbottom = (round(center.x), round(center.y - radius - GAP))

        buffs = world.try_get_component(entity, ActiveBuffs)
        bonus = 0.0 if buffs is None else sum(b.bonus_health for b in buffs.buffs)

        current = max(0.0, health.current)
        # With bonus health the bar spans health + bonus, so the bonus stays
        # visible even when regular health is full.
        total = max(health.maximum, current + bonus)

        pygame.draw.rect(surface, BACKGROUND_COLOR, bar)

        fraction = min(1.0, current / health.maximum)
        fill_width = round(width * current / total)
        if fill_width > 0:
            pygame.draw.rect(
                surface, _fill_color(fraction), (bar.x, bar.y, fill_width, HEIGHT)
            )

        bonus_width = min(width - fill_width, round(width * bonus / total))
        if bonus_width > 0:
            pygame.draw.rect(
                surface, BONUS_COLOR, (bar.x + fill_width, bar.y, bonus_width, HEIGHT)
            )

        pygame.draw.rect(surface, BORDER_COLOR, bar.inflate(2, 2), width=1)
