import pygame

from game.components.convex_collider import ConvexCollider
from game.components.mystery_box import MysteryBox
from game.components.shape import Shape
from game.components.transform import Transform
from game.core_ecs.entity import Entity
from game.core_ecs.world import World

BOX_SIZE = 36
BOX_COLOR = (230, 180, 50)


def spawn_mystery_box(world: World, position: pygame.Vector2) -> Entity:
    half = BOX_SIZE / 2
    vertices = (
        pygame.Vector2(-half, -half),
        pygame.Vector2(half, -half),
        pygame.Vector2(half, half),
        pygame.Vector2(-half, half),
    )

    return world.create_entity(
        MysteryBox(),
        Transform(position=pygame.Vector2(position)),
        Shape(vertices=vertices, color=BOX_COLOR),
        ConvexCollider(vertices=vertices),
    )
