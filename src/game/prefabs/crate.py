import pygame

from game.components.breakable import Breakable
from game.components.buff_drop import BuffDrop
from game.components.convex_collider import ConvexCollider
from game.components.rigid_body import box_body
from game.components.shape import Shape
from game.components.transform import Transform
from game.core_ecs.world import World
from game.util.geometry import rectangle

CRATE_COLOR = (200, 200, 200)
CRATE_SIZE = 30
"""Crates are a bit smaller than a tile so they fit through 1-tile gaps."""
CRATE_DURABILITY = 30.0
"""One dash (30) or two pistol shots (20 each) breaks it."""


def spawn_crate(world: World, center: pygame.Vector2):
    vertices = rectangle(CRATE_SIZE, CRATE_SIZE)
    return world.create_entity(
        box_body(0.2, CRATE_SIZE, CRATE_SIZE, drag=0.4, angular_drag=0.4),
        Transform(position=pygame.Vector2(center)),
        Shape(vertices=vertices, color=CRATE_COLOR),
        ConvexCollider(vertices=vertices, bounciness=0.5),
        Breakable(durability=CRATE_DURABILITY),
        BuffDrop(),
    )
