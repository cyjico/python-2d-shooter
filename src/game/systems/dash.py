import pygame

from game.components.breakable import Breakable
from game.components.buffs import Flag, Stat
from game.components.dash import Dash, DashIntent
from game.components.health import Health
from game.components.mover import Mover
from game.components.rigid_body import RigidBody
from game.components.stamina import Stamina
from game.components.transform import Transform
from game.constants.perks import DASH_STRIKE_DAMAGE
from game.core_ecs.world import World
from game.events.collision import CollisionEvent, directed
from game.events.combat import DamageEvent, DashStartedEvent
from game.resources.event_bus import EventBus
from game.util.buffs import has_flag, stat_multiplier
from game.util.factions import is_hostile
from game.util.geometry import rot_to_vec2


def _dash_direction(
    requested: pygame.Vector2 | None, mover: Mover | None, transform: Transform
):
    """The requested direction, else where the mover is heading, else where it
    faces, else its rotation."""
    if requested is not None and requested.length_squared() > 0:
        return requested.normalize()
    if mover is not None:
        if mover.move_dir.length_squared() > 0:
            return mover.move_dir.normalize()
        if mover.face_angle is not None:
            return rot_to_vec2(mover.face_angle)
    return rot_to_vec2(transform.rotation)


def dash_system(world: World, dt: float):
    """Starts and drives dashes for anything with Dash + DashIntent."""
    events = world.get_resource(EventBus)

    for entity, (dash, intent, rigidbody, transform) in world.query(
        Dash, DashIntent, RigidBody, Transform
    ):
        dash.cooldown_left = max(0.0, dash.cooldown_left - dt)
        dash.moving = False

        wants_dash = intent.requested
        requested_direction = intent.direction
        intent.requested = False
        intent.direction = None

        if wants_dash and dash.ready:
            stamina = world.try_get_component(entity, Stamina)
            if stamina is None or stamina.try_spend(dash.stamina_cost):
                dash.direction = _dash_direction(
                    requested_direction,
                    world.try_get_component(entity, Mover),
                    transform,
                )
                dash.time_left = dash.duration
                dash.cooldown_left = dash.cooldown
                dash.hit.clear()
                events.emit(DashStartedEvent(entity))

        if dash.active:
            dash.moving = True
            # Override whatever mover_system queued this frame.
            rigidbody.accumulated_acceleration.update(0, 0)
            rigidbody.linear_velocity = dash.direction * dash.speed
            dash.time_left = max(0.0, dash.time_left - dt)


def dash_impact_system(world: World):
    """A dash damages each Breakable it runs into, once. With Tempest, it
    damages enemies too."""
    events = world.get_resource(EventBus)

    for me, other in directed(events.read(CollisionEvent)):
        dash = world.try_get_component(me, Dash)
        if dash is None or not dash.moving or other in dash.hit:
            continue

        if world.has_component(other, Breakable):
            dash.hit.add(other)
            events.emit(DamageEvent(other, dash.impact_damage, me))
        elif (
            world.has_component(other, Health)
            and is_hostile(world, me, other)
            and has_flag(world, me, Flag.DASH_STRIKE)
        ):
            dash.hit.add(other)
            damage = DASH_STRIKE_DAMAGE * stat_multiplier(world, me, Stat.DAMAGE)
            events.emit(DamageEvent(other, damage, me))
