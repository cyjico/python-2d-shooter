import pygame

from game.components.breakable import Breakable
from game.components.dash import Dash, DashIntent
from game.components.mover import Mover
from game.components.rigid_body import RigidBody
from game.components.stamina import Stamina
from game.components.transform import Transform
from game.core_ecs.world import World
from game.events.collision import CollisionEvent
from game.events.combat import DamageEvent
from game.resources.event_bus import EventBus
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
    """Starts and drives dashes for anything with Dash + DashIntent. Run after
    mover_system and stamina_system."""
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

        if dash.active:
            dash.moving = True
            # Override whatever mover_system queued this frame.
            rigidbody.accumulated_acceleration.update(0, 0)
            rigidbody.linear_velocity = dash.direction * dash.speed
            dash.time_left = max(0.0, dash.time_left - dt)


def dash_impact_system(world: World):
    """A dash damages each Breakable it runs into, once. Run after collision_system."""
    events = world.get_resource(EventBus)

    for collision in events.read(CollisionEvent):
        for me, other in (
            (collision.entity_a, collision.entity_b),
            (collision.entity_b, collision.entity_a),
        ):
            dash = world.try_get_component(me, Dash)
            if dash is None or not dash.moving or other in dash.hit:
                continue
            if not world.has_component(other, Breakable):
                continue

            dash.hit.add(other)
            events.emit(DamageEvent(other, dash.impact_damage, me))
