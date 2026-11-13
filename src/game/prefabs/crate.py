import pygame

from game.components.convex_collider import ConvexCollider
from game.components.rigid_body import RigidBody, inertia_of_box, mass_of_box
from game.components.shape import Shape
from game.components.transform import Transform
from game.constants.crate import CRATE_COLOR, CRATE_SIZE
from game.core_ecs.world import World
from game.util.geometry import rectangle


def spawn_crate(world: World, center: pygame.Vector2):
    vertices = rectangle(CRATE_SIZE, CRATE_SIZE)
    mass = mass_of_box(0.2, CRATE_SIZE, CRATE_SIZE)
    return world.create_entity(
        RigidBody(
            mass=mass,
            drag=0.4,
            inertia=inertia_of_box(mass, CRATE_SIZE, CRATE_SIZE),
            angular_drag=0.4,
        ),
        Transform(position=pygame.Vector2(center)),
        Shape(vertices=vertices, color=CRATE_COLOR),
        ConvexCollider(vertices=vertices, bounciness=0.5),
    )
