import random

import pygame

from game.components.ai import AI
from game.components.ai.charger import ChargerAI, ChargerAIState
from game.components.ai.hover_around_target import HoverAroundTargetAI
from game.components.convex_collider import ConvexCollider
from game.components.enemy import Enemy
from game.components.health import Health
from game.components.mover import Mover
from game.components.player import Player
from game.components.rigid_body import RigidBody
from game.components.shape import Shape
from game.components.transform import Transform
from game.core_ecs.entity import Entity
from game.core_ecs.world import World
from game.events.collision import CollisionEvent
from game.events.combat import DamageEvent
from game.resources.event_bus import EventBus
from game.util.geometry import angle_of, rot_to_vec2


def _start_hover(
    world: World, ent: Entity, charger: ChargerAI, mover: Mover, shape: Shape
):
    if charger.normal_stats is not None:
        mover.move_speed, mover.move_accel, mover.turn_speed = charger.normal_stats
        charger.normal_stats = None

    shape.color = charger.base_color
    charger.state = ChargerAIState.HOVER
    charger.timer = random.uniform(*charger.hover_time)
    _resume_hover_behavior(world, ent, charger)


def _resume_hover_behavior(world: World, ent: Entity, charger: ChargerAI):
    if charger.hover_behavior is not None:
        world.add_component(ent, charger.hover_behavior)
        charger.hover_behavior = None


def _suspend_hover_behavior(world: World, ent: Entity, charger: ChargerAI):
    hover = world.try_get_component(ent, HoverAroundTargetAI)
    if hover is not None:
        charger.hover_behavior = world.remove_component(ent, HoverAroundTargetAI)


def _windup(
    charger: ChargerAI,
    mover: Mover,
    transform: Transform,
    shape: Shape,
    toward: pygame.Vector2,
    dt: float,
):
    shape.color = charger.windup_color
    mover.move_dir.update()
    mover.face_angle = angle_of(toward)

    charger.timer -= dt
    if charger.timer <= 0:
        charger.state = ChargerAIState.CHARGE
        charger.charge_origin = pygame.Vector2(transform.position)


def _charge(
    world: World,
    ent: Entity,
    charger: ChargerAI,
    mover: Mover,
    transform: Transform,
    shape: Shape,
):
    shape.color = charger.windup_color
    mover.move_dir = rot_to_vec2(transform.rotation)
    mover.move_speed = charger.charge_speed
    mover.move_accel = charger.charge_acceleration

    if (
        transform.position - charger.charge_origin
    ).magnitude_squared() >= charger.charge_distance_sqr:
        _start_hover(world, ent, charger, mover, shape)


def _stunned(
    world: World, ent: Entity, charger: ChargerAI, mover: Mover, shape: Shape, dt: float
):
    shape.color = charger.stunned_color
    mover.move_dir.update()
    mover.move_speed = 0
    mover.turn_speed = 0

    charger.timer -= dt
    if charger.timer <= 0:
        _start_hover(world, ent, charger, mover, shape)


def charger_ai_system(world: World, dt: float):
    for ent, (charger,) in world.query(ChargerAI):
        ai = world.get_component(ent, AI)
        mover = world.get_component(ent, Mover)
        transform = world.get_component(ent, Transform)
        shape = world.get_component(ent, Shape)

        if ai.target is None:
            continue

        targ_transform = world.get_component(ai.target, Transform)

        toward = targ_transform.position - transform.position

        match charger.state:
            # HOVER -> WINDUP -> CHARGE -> (hits wall) -> STUNNED -> HOVER
            case ChargerAIState.HOVER:
                charger.timer -= dt
                if charger.timer <= 0:
                    charger.state = ChargerAIState.WINDUP
                    charger.timer = charger.windup_time
                    charger.normal_stats = (
                        mover.move_speed,
                        mover.move_accel,
                        mover.turn_speed,
                    )
                    _suspend_hover_behavior(world, ent, charger)
            case ChargerAIState.WINDUP:
                _windup(charger, mover, transform, shape, toward, dt)
            case ChargerAIState.CHARGE:
                _charge(world, ent, charger, mover, transform, shape)
            case ChargerAIState.STUNNED:
                _stunned(world, ent, charger, mover, shape, dt)


def charger_ai_collision_system(world: World):
    """Stuns on walls, damages on contact. Run after collision_system, before health_system."""
    events = world.get_resource(EventBus)

    for collision in events.read(CollisionEvent):
        _on_contact(world, events, collision.entity_a, collision.entity_b)
        _on_contact(world, events, collision.entity_b, collision.entity_a)


def _on_contact(world: World, events: EventBus, me: Entity, other: Entity):
    charger = world.try_get_component(me, ChargerAI)
    if charger is None or charger.state is not ChargerAIState.CHARGE:
        return

    collider = world.try_get_component(other, ConvexCollider)
    if collider is None or collider.is_trigger:
        return

    if not world.has_component(other, RigidBody):
        charger.state = ChargerAIState.STUNNED
        charger.timer = charger.stun_time
    elif world.has_component(other, Health) and not world.has_component(
        other, charger.component_mask
    ):
        events.emit(DamageEvent(other, charger.contact_damage, me))
        _start_hover(
            world,
            me,
            charger,
            world.get_component(me, Mover),
            world.get_component(me, Shape),
        )
