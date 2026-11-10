import pygame

from game.resources.camera import Camera
from game.core_ecs.world import World
from game.components.transform import Transform
from game.components.convex_shape import ConvexShape


def render_system(world: World, surface: pygame.Surface):
    camera = world.get_resource(Camera)

    for entity, (transform, shape) in world.query(Transform, ConvexShape):
        pygame.draw.polygon(
            surface,
            shape.color,
            [camera.world_to_screen(v) for v in transform.apply_all(shape.vertices)],
        )
