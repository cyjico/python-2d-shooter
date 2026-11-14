import random
from functools import partial

import pygame

from game.components.ai import AI
from game.components.ai.charger import ChargerAI
from game.components.ai.follow_target import FollowTargetAI
from game.components.ai.hover_around_target import HoverAroundTargetAI
from game.components.ai.random_dash import RandomDashAI
from game.components.ai.shooter import ShooterAI
from game.components.bounty import Bounty
from game.components.contact_damage import ContactDamage
from game.components.convex_collider import ConvexCollider
from game.components.dash import Dash, DashIntent
from game.components.faction import Team
from game.components.health import Health
from game.components.loadout import Loadout
from game.components.mover import Mover
from game.components.rigid_body import box_body
from game.components.shape import Shape
from game.components.split_on_death import SplitOnDeath
from game.components.transform import Transform
from game.components.weapon_intent import WeaponIntent
from game.constants.gun_buffs import make_gun, roll_gun
from game.constants.rarity import rarity_color
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

SHOOTER_VERTICES = (
    # A kite pointing along +x, so it's clear where it's aiming.
    pygame.Vector2(18, 0),
    pygame.Vector2(-8, -13),
    pygame.Vector2(-12, 0),
    pygame.Vector2(-8, 13),
)
SHOOTER_BOUNTY = 45
SHOOTER_DAMAGE_SCALE = 0.25
"""Enemies carry the player's guns at this fraction of their damage..."""
SHOOTER_KNOCKBACK_SCALE = 0.05
"""...and this fraction of their knockback, so hits nudge the player instead of
launching them."""
SHOOTER_HOVER_DIST = (160.0, 320.0)
"""Preferred distance from the target, clamped to stay on screen."""


def spawn_charger(world: World, pos: pygame.Vector2, player: Entity):
    vertices = regular_polygon(5, CHARGER_RADIUS)

    charger_ai = ChargerAI(
        charge_speed=1750,
        charge_acceleration=50_000,
        charge_distance_sqr=800**2,
        contact_damage=35,
    )

    return world.create_entity(
        AI(target=player),
        Faction(Team.ENEMY),
        charger_ai,
        HoverAroundTargetAI(),
        Mover(move_speed=180),
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
        Mover(move_speed=210),
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


def spawn_shooter(
    world: World,
    pos: pygame.Vector2,
    player: Entity,
    rng: random.Random | None = None,
):
    """Keeps its distance and shoots. Rolls its gun like the mystery box does,
    and its body takes the gun's rarity color."""
    spec, rarity = roll_gun(rng)
    gun = make_gun(spec, rarity)

    low, high = SHOOTER_HOVER_DIST
    hover_dist = min(high, max(low, gun.spec.max_range * 0.6))
    radius = max(v.length() for v in SHOOTER_VERTICES)

    return world.create_entity(
        AI(target=player, body_radius=radius),
        Faction(Team.ENEMY),
        HoverAroundTargetAI(preferred_dist=hover_dist),
        ShooterAI(),
        Loadout(
            slots=[gun],
            damage_scale=SHOOTER_DAMAGE_SCALE,
            knockback_scale=SHOOTER_KNOCKBACK_SCALE,
        ),
        WeaponIntent(),
        Mover(move_speed=160),
        Health(maximum=50),
        Bounty(SHOOTER_BOUNTY),
        box_body(0.4, 15, 15, drag=0.4, angular_drag=0.4),
        Transform(position=pygame.Vector2(pos)),
        Shape(vertices=SHOOTER_VERTICES, color=rarity_color(rarity)),
        ConvexCollider(vertices=SHOOTER_VERTICES),
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
