import pygame

from game.components.health import Health
from game.components.shape import Shape
from game.components.transform import Transform
from game.core_ecs.world import World
from game.resources.camera import Camera
from game.util.buffs import bonus_health
from game.util.draw import draw_bar

MIN_WIDTH = 24
HEIGHT = 7
"""Includes the border."""
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
        radius = shape.radius * transform.max_scale
        if not camera.is_circle_visible(transform.position, radius + GAP + HEIGHT):
            continue

        current = max(0.0, health.current)
        bonus = bonus_health(world, entity)
        # The bar spans health + bonus, so bonus stays visible at full health.
        total = max(health.maximum, current + bonus)

        center = camera.world_to_screen(transform.position)
        bar = pygame.Rect(0, 0, max(MIN_WIDTH, round(2 * radius)), HEIGHT)
        bar.midbottom = (round(center.x), round(center.y - radius - GAP))

        draw_bar(
            surface,
            bar,
            [
                (current / total, _fill_color(min(1.0, current / health.maximum))),
                (bonus / total, BONUS_COLOR),
            ],
            BACKGROUND_COLOR,
            BORDER_COLOR,
            border_width=1,
        )
