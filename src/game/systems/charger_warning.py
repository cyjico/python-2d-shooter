"""Warns the player of a charger about to charge: the lane it will charge down,
filling up as the windup runs out, and an arrow at the screen edge when the
charger itself is off screen."""

import math

import pygame

from game.components.ai.charger import ChargerAI, ChargerAIState
from game.components.shape import Shape
from game.components.transform import Transform
from game.core_ecs.world import World
from game.resources.camera import Camera
from game.util.draw import draw_edge_arrow
from game.util.geometry import rot_to_vec2
from game.util.raycast import raycast_static_bundle

COLOR = (255, 60, 40)
LANE_ALPHA = 40
"""The whole lane, from the start of the windup."""
FILL_ALPHA = 110
"""The part that fills up as the charge gets closer."""
EDGE_ALPHA = 170
WALL_SEARCH_STEPS = 6
"""Binary search steps to find where a wall cuts the lane short."""
EDGE_INSET = 24
ARROW_LENGTH = 26
ARROW_HALF_WIDTH = 14
PULSE_SPEED = 14.0
"""Radians per second of the arrow's pulse. Fast: it's urgent."""


def _winding_up(world: World):
    for _, (charger, transform, shape) in world.query(ChargerAI, Transform, Shape):
        if charger.state is ChargerAIState.WINDUP:
            yield charger, transform, shape


def _lane_length(world: World, start: pygame.Vector2, direction, max_length, radius):
    """How far the charge can go before the first wall."""
    if not raycast_static_bundle(world, start, direction, max_length, radius):
        return max_length
    low, high = 0.0, max_length
    for _ in range(WALL_SEARCH_STEPS):
        mid = (low + high) / 2
        if raycast_static_bundle(world, start, direction, mid, radius):
            high = mid
        else:
            low = mid
    return high


def charger_lane_render_system(world: World, surface: pygame.Surface):
    """Draws under the world's shapes, so walls and bodies sit on top of it."""
    chargers = list(_winding_up(world))
    if not chargers:
        return

    camera = world.get_resource(Camera)
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

    for charger, transform, shape in chargers:
        start = pygame.Vector2(transform.position)
        direction = rot_to_vec2(transform.rotation)
        radius = shape.radius * transform.max_scale
        length = _lane_length(
            world, start, direction, math.sqrt(charger.charge_distance_sqr), radius
        )
        progress = 1.0 - max(0.0, charger.timer) / charger.windup_time

        lane = _lane_quad(camera, start, direction, radius, length)
        pygame.draw.polygon(overlay, (*COLOR, LANE_ALPHA), lane)
        if progress > 0:
            filled = _lane_quad(camera, start, direction, radius, length * progress)
            pygame.draw.polygon(overlay, (*COLOR, FILL_ALPHA), filled)
        pygame.draw.lines(overlay, (*COLOR, EDGE_ALPHA), True, lane, width=2)

    surface.blit(overlay, (0, 0))


def _lane_quad(
    camera: Camera,
    start: pygame.Vector2,
    direction: pygame.Vector2,
    half_width: float,
    reach: float,
):
    """Screen-space corners of a lane `reach` px long, `2 * half_width` wide."""
    side = pygame.Vector2(-direction.y, direction.x) * half_width
    end = start + direction * reach
    return [
        camera.world_to_screen(p)
        for p in (start + side, end + side, end - side, start - side)
    ]


def charger_edge_warning_render_system(world: World, surface: pygame.Surface):
    """Arrows at the screen edge toward chargers winding up off screen."""
    camera = world.get_resource(Camera)
    pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 1000 * PULSE_SPEED)

    for _, transform, shape in _winding_up(world):
        radius = shape.radius * transform.max_scale
        if camera.is_circle_visible(transform.position, radius):
            continue
        draw_edge_arrow(
            surface,
            camera.world_to_screen(transform.position),
            COLOR,
            EDGE_INSET,
            ARROW_LENGTH + 6 * pulse,
            ARROW_HALF_WIDTH,
            bob=3 * pulse,
        )
