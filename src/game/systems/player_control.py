from ..core_ecs.world import World
from ..resources.input_state import InputState
from ..components.player import Player
from ..components.rigid_body import RigidBody


def player_control_system(world: World, dt: float):
    inputs = world.get_resource(InputState)

    for entity, (player,) in world.query(Player):
        rigidbody = world.get_component(entity, RigidBody)

        acceleration = (
            (inputs.movement * player.move_speed) - rigidbody.linear_velocity
        ) / dt

        # Clamp acceleration to the player's maximum acceleration.
        if acceleration.length_squared() > player.move_acceleration**2:
            acceleration.scale_to_length(player.move_acceleration)

        rigidbody.apply_acceleration(acceleration)
