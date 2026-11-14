from functools import partial

import pygame

from game.components.ai import AI
from game.components.ai.charger import ChargerAI
from game.components.ai.follow_target import FollowTargetAI
from game.components.ai.hover_around_target import HoverAroundTargetAI
from game.components.ai.random_dash import RandomDashAI
from game.components.bounty import Bounty
from game.components.contact_damage import ContactDamage
from game.components.convex_collider import ConvexCollider
from game.components.dash import Dash, DashIntent
from game.components.faction import Team
from game.components.health import Health
from game.components.mover import Mover
from game.components.rigid_body import box_body
from game.components.shape import Shape
from game.components.split_on_death import SplitOnDeath
from game.components.transform import Transform
from game.constants.splitter import SPLITTER_LARGE, SplitterTier
from game.core_ecs.entity import Entity
from game.core_ecs.world import World
from game.util.factions import Faction
from game.util.geometry import regular_polygon

CHARGER_RADIUS = 16
CHARGER_BOUNTY = 40

CHASER_RADIUS = 14
CHASER_BOUNTY = 25
CHASER_COLOR = (220, 70, 70)


def spawn_charger(world: World, pos: pygame.Vector2, player: Entity):
    vertices = regular_polygon(5, CHARGER_RADIUS)

    charger_ai = ChargerAI(charge_distance_sqr=800**2)

    return world.create_entity(
        AI(target=player),
        Faction(Team.ENEMY),
        charger_ai,
        HoverAroundTargetAI(),
        Mover(move_speed=150),
        Health(maximum=60),
        Bounty(CHARGER_BOUNTY),
        box_body(0.4, CHARGER_RADIUS, CHARGER_RADIUS, drag=0.4, angular_drag=0.4),
        Transform(position=pygame.Vector2(pos)),
        Shape(vertices=vertices, color=charger_ai.base_color),
        ConvexCollider(vertices=vertices),
    )


def spawn_chaser(world: World, pos: pygame.Vector2, player: Entity):
    vertices = regular_polygon(3, CHASER_RADIUS)

    return world.create_entity(
        AI(target=player, body_radius=CHASER_RADIUS),
        Faction(Team.ENEMY),
        FollowTargetAI(),
        RandomDashAI(),
        Mover(move_speed=160),
        Dash(speed=650, cooldown=0.5),
        DashIntent(),
        ContactDamage(amount=10),
        Health(maximum=40),
        Bounty(CHASER_BOUNTY),
        box_body(0.4, CHASER_RADIUS, CHASER_RADIUS, drag=0.4, angular_drag=0.4),
        Transform(position=pygame.Vector2(pos)),
        Shape(vertices=vertices, color=CHASER_COLOR),
        ConvexCollider(vertices=vertices),
    )


def spawn_splitter(
    world: World,
    pos: pygame.Vector2,
    target: Entity | None,
    tier: SplitterTier = SPLITTER_LARGE,
):
    """A chaser that splits into `tier.children` of `tier.child_tier` on death."""
    vertices = regular_polygon(4, tier.radius)

    entity = world.create_entity(
        AI(target=target, body_radius=tier.radius),
        Faction(Team.ENEMY),
        FollowTargetAI(),
        Mover(move_speed=tier.move_speed),
        ContactDamage(amount=tier.contact_damage),
        Health(maximum=tier.health),
        Bounty(tier.bounty),
        box_body(0.4, tier.radius, tier.radius, drag=0.4, angular_drag=0.4),
        Transform(position=pygame.Vector2(pos)),
        Shape(vertices=vertices, color=tier.color),
        ConvexCollider(vertices=vertices),
    )

    if tier.child_tier is not None:
        world.add_component(
            entity,
            SplitOnDeath(
                count=tier.children,
                spawn=partial(spawn_splitter, tier=tier.child_tier),
                spread_distance=tier.radius,
            ),
        )

    return entity
