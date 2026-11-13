import pygame

from game.components.ai import AI
from game.components.ai.charger import ChargerAI
from game.components.ai.follow_target import FollowTargetAI
from game.components.ai.hover_around_target import HoverAroundTargetAI
from game.components.enemy import Enemy
from game.components.mover import Mover
from game.components.rigid_body import RigidBody, inertia_of_box, mass_of_box
from game.components.shape import Shape
from game.components.transform import Transform
from game.core_ecs.entity import Entity
from game.core_ecs.world import World
from game.game import ConvexCollider
from game.systems.health import Health
from game.util.geometry import regular_polygon

CHARGER_RADIUS = 16


def spawn_charger(world: World, pos: pygame.Vector2, player: Entity):
    vertices = regular_polygon(5, CHARGER_RADIUS)

    charger_ai = ChargerAI(component_mask=Enemy, charge_distance_sqr=800**2)

    mass = mass_of_box(0.4, CHARGER_RADIUS, CHARGER_RADIUS)
    return world.create_entity(
        AI(target=player),
        Enemy(),
        charger_ai,
        HoverAroundTargetAI(),
        Mover(move_speed=150),
        Health(maximum=60),
        RigidBody(
            mass=mass,
            drag=0.4,
            inertia=inertia_of_box(mass, CHARGER_RADIUS, CHARGER_RADIUS),
            angular_drag=0.4,
        ),
        Transform(position=pygame.Vector2(pos)),
        Shape(vertices=vertices, color=charger_ai.base_color),
        ConvexCollider(vertices=vertices),
    )
