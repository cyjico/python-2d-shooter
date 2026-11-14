import pygame

from game.components.player import Player
from game.components.shape import Shape
from game.components.stamina import Stamina
from game.components.transform import Transform
from game.core_ecs.world import World
from game.resources.camera import Camera

DOT_RADIUS = 4
DOT_SPACING = 12
"""Center to center, px."""
GAP = 9
"""Space between the bottom of the player's bounding circle and the dots, px."""
FULL_COLOR = (90, 170, 255)
EMPTY_COLOR = (40, 60, 90)
"""Outline of a dot that isn't full yet."""


def stamina_dots_render_system(world: World, surface: pygame.Surface):
    """One blue dot per stamina segment (one dash each), centered under the
    player. A refilling dot grows from the middle."""
    camera = world.get_resource(Camera)

    for _, (_, stamina, transform, shape) in world.query(
        Player, Stamina, Transform, Shape
    ):
        count = stamina.maximum
        if count <= 0:
            continue

        center = camera.world_to_screen(transform.position)
        y = round(center.y + shape.radius * transform.max_scale + GAP)
        left = center.x - (count - 1) * DOT_SPACING / 2

        for i in range(count):
            dot = (round(left + i * DOT_SPACING), y)
            fill = min(1.0, max(0.0, stamina.current - i))

            if fill >= 1.0:
                pygame.draw.circle(surface, FULL_COLOR, dot, DOT_RADIUS)
                continue

            pygame.draw.circle(surface, EMPTY_COLOR, dot, DOT_RADIUS, width=1)
            if fill > 0:
                pygame.draw.circle(
                    surface, FULL_COLOR, dot, max(1, round(DOT_RADIUS * fill))
                )
