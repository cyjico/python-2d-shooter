import math

import pygame

from game.components.loadout import Loadout
from game.components.player import Player
from game.core_ecs.world import World
from game.resources.input_state import InputState

RING_RADIUS = 14
RING_COLOR = (255, 255, 255)
RELOAD_COLOR = (150, 150, 150)
"""While reloading, the ring refills in grey as the reload progresses."""
CROSSHAIR_COLOR = (255, 255, 255)
CROSSHAIR_INNER = 3
"""Gap around the center, px."""
CROSSHAIR_OUTER = 8
ARC_STEPS = 72
"""Line segments in a full ring."""


def _arc(surface: pygame.Surface, color, center: pygame.Vector2, fraction: float):
    """A 2px ring starting at the top and running clockwise for `fraction` of
    a full turn."""
    if fraction <= 0:
        return
    if fraction >= 1:
        pygame.draw.circle(surface, color, center, RING_RADIUS, width=2)
        return

    steps = max(2, round(ARC_STEPS * fraction))
    for radius in (RING_RADIUS, RING_RADIUS - 1):
        points = [
            center
            + pygame.Vector2(math.cos(angle), math.sin(angle)) * radius
            for i in range(steps + 1)
            # y points down, so increasing angles go clockwise on screen.
            for angle in [-math.pi / 2 + math.tau * fraction * i / steps]
        ]
        pygame.draw.aalines(surface, color, False, points)


def cursor_render_system(world: World, surface: pygame.Surface):
    """Replaces the mouse cursor: a crosshair inside a ring that empties as
    the magazine does."""
    center = world.get_resource(InputState).mouse_pos
    loadout = next((l for _, (_, l) in world.query(Player, Loadout)), None)
    gun = loadout.equipped if loadout is not None else None

    if gun is not None and gun.reloading:
        done = 1.0 - gun.reload_remaining / gun.spec.reload_time
        _arc(surface, RELOAD_COLOR, center, done)
    elif gun is not None:
        _arc(surface, RING_COLOR, center, gun.magazine / gun.spec.magazine_size)

    x, y = round(center.x), round(center.y)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        pygame.draw.line(
            surface,
            CROSSHAIR_COLOR,
            (x + dx * CROSSHAIR_INNER, y + dy * CROSSHAIR_INNER),
            (x + dx * CROSSHAIR_OUTER, y + dy * CROSSHAIR_OUTER),
        )
