import math

import pygame

from game.components.faction import Faction, Team
from game.components.shape import Shape
from game.components.transform import Transform
from game.core_ecs.world import World
from game.resources.camera import Camera
from game.resources.enemy_director import EnemyDirector, WavePhase
from game.util.draw import draw_edge_arrow

COLOR = (255, 90, 90)
PULSE_SPEED = 6.0
"""Radians per second of the pulse."""
RING_GAP = 10
"""Px between the enemy's bounding circle and the ring."""
EDGE_INSET = 24
"""Px between the screen edge and the arrow's tip."""
ARROW_LENGTH = 30
ARROW_HALF_WIDTH = 15


def last_enemy_cue_render_system(world: World, surface: pygame.Surface):
    """Points out the last enemy of a wave: a pulsing ring around it on screen,
    an arrow at the screen edge toward it off screen."""
    director = world.get_resource(EnemyDirector)
    if director.phase is not WavePhase.ACTIVE or director.roster:
        return

    enemies = [e for e, (f,) in world.query(Faction) if f.team & Team.ENEMY]
    if len(enemies) != 1:
        return
    transform = world.try_get_component(enemies[0], Transform)
    if transform is None:
        return

    camera = world.get_resource(Camera)
    shape = world.try_get_component(enemies[0], Shape)
    radius = 0.0 if shape is None else shape.radius * transform.max_scale
    # 0..1, smooth.
    pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 1000 * PULSE_SPEED)

    screen_pos = camera.world_to_screen(transform.position)
    w, h = camera.viewport_size
    # Only a ring once it's well inside the view; one peeking in at the edge
    # still gets the arrow, or the ring would be mostly cut off.
    if EDGE_INSET <= screen_pos.x <= w - EDGE_INSET and (
        EDGE_INSET <= screen_pos.y <= h - EDGE_INSET
    ):
        _draw_ring(surface, screen_pos, radius, pulse)
    else:
        draw_edge_arrow(
            surface,
            screen_pos,
            COLOR,
            EDGE_INSET,
            ARROW_LENGTH,
            ARROW_HALF_WIDTH,
            bob=4 * pulse,
        )


def _draw_ring(
    surface: pygame.Surface, center: pygame.Vector2, radius: float, pulse: float
):
    ring_radius = round(radius + RING_GAP + 4 * pulse)
    size = 2 * ring_radius + 4
    ring = pygame.Surface((size, size), pygame.SRCALPHA)
    alpha = round(140 + 115 * pulse)
    pygame.draw.circle(
        ring, (*COLOR, alpha), (size // 2, size // 2), ring_radius, width=3
    )
    surface.blit(ring, ring.get_rect(center=(round(center.x), round(center.y))))
