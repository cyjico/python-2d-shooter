import math

import pygame

from game.components.breakable import Breakable
from game.components.dash import Dash
from game.components.player import Player
from game.components.rigid_body import RigidBody
from game.components.transform import Transform
from game.core_ecs.world import World
from game.events.collision import CollisionEvent
from game.events.combat import DamageEvent
from game.resources.event_bus import EventBus
from game.resources.input_state import InputState


def dash_system(world: World, dt: float):
    inputs = world.get_resource(InputState)

    for _, (_, dash, rigidbody, transform) in world.query(
        Player, Dash, RigidBody, Transform
    ):
        dash.cooldown_left = max(0.0, dash.cooldown_left - dt)

        if inputs.dash_pressed and not dash.active and dash.cooldown_left == 0.0:
            if inputs.movement.length_squared() > 0:
                direction = inputs.movement.copy()
            else:
                # No movement keys held: dash the way the player is facing.
                direction = pygame.Vector2(
                    math.cos(transform.rotation), math.sin(transform.rotation)
                )

            dash.direction = direction
            dash.time_left = dash.duration
            dash.cooldown_left = dash.cooldown
            dash.hit.clear()

        if dash.active:
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
            if dash is None or not dash.active or other in dash.hit:
                continue
            if not world.has_component(other, Breakable):
                continue

            dash.hit.add(other)
            events.emit(DamageEvent(other, dash.impact_damage, me))
