import math

import pygame

from game.components.convex_collider import ConvexCollider
from game.components.loadout import GunSpec
from game.components.projectile import Projectile
from game.components.rigid_body import RigidBody
from game.components.shape import Shape
from game.components.transform import Transform
from game.core_ecs.entity import Entity
from game.core_ecs.world import World


def spawn_gun_projectile(
    world: World,
    shooter: Entity,
    origin: pygame.Vector2,
    angle: float,
    spec: GunSpec,
    damage_scale: float = 1.0,
):
    length, width = spec.projectile_size
    hl, hw = length / 2, width / 2
    vertices = (
        pygame.Vector2(-hl, -hw),
        pygame.Vector2(hl, -hw),
        pygame.Vector2(hl, hw),
        pygame.Vector2(-hl, hw),
    )
    direction = pygame.Vector2(math.cos(angle), math.sin(angle))

    world.create_entity(
        Transform(position=pygame.Vector2(origin), rotation=angle),
        # Moved by the regular physics system. No inertia = no spin, no drag.
        RigidBody(mass=1.0, linear_velocity=direction * spec.projectile_speed),
        Shape(vertices=vertices, color=spec.projectile_color),
        ConvexCollider(vertices=vertices, bounciness=0.0, is_trigger=True),
        Projectile(
            owner=shooter,
            damage=spec.damage * damage_scale,
            lifetime=spec.max_range / spec.projectile_speed,
            pierce_left=spec.pierce,
            knockback=spec.knockback,
        ),
    )
