import pygame

from game.core.camera import Camera
from game.core_ecs.world import World
from game.components.transform import Transform
from game.components.convex_shape import ConvexShape


def render_system(world: World, surface: pygame.Surface, camera: Camera):
    for entity, (transform, shape) in world.query(Transform, ConvexShape):
        points = []

        for vertex in shape.vertices:
            screen_position = camera.world_to_screen(
                Transform.apply(pygame.Vector2(vertex), transform)
            )

            points.append((round(screen_position.x), round(screen_position.y)))

        pygame.draw.polygon(surface, shape.color, points)
