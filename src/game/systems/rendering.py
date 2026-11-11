import pygame

from game.resources.camera import Camera
from game.core_ecs.world import World
from game.components.transform import Transform
from game.components.shape import Shape


def render_system(world: World, surface: pygame.Surface):
    camera = world.get_resource(Camera)

    for entity, (shape,) in world.query(Shape):
        transform = world.get_component(entity, Transform)

        radius = shape.radius * max(abs(transform.scale[0]), abs(transform.scale[1]))

        if not camera.is_circle_visible(transform.position, radius):
            continue

        pygame.draw.polygon(
            surface,
            shape.color,
            [camera.world_to_screen(v) for v in transform.apply_all(shape.vertices)],
        )
