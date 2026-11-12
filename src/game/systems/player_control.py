import math

from game.components.mover import Mover
from game.components.player import Player
from game.components.rigid_body import RigidBody
from game.components.transform import Transform
from game.core_ecs.world import World
from game.resources.camera import Camera
from game.resources.input_state import InputState
from game.util.math import wrap_angle


def player_control_system(world: World, dt: float):
    inputs = world.get_resource(InputState)
    camera = world.get_resource(Camera)

    mouse_world = camera.screen_to_world(inputs.mouse_pos)

    for ent, _ in world.query(Player):
        mover = world.get_component(ent, Mover)
        transform = world.get_component(ent, Transform)

        mover.move_dir = inputs.movement

        to_mouse = mouse_world - transform.position
        if to_mouse.length_squared() < 1.0:
            continue

        # Both pygame's y-down axes and Transform's rotation are clockwise-positive.
        mover.face_angle = math.atan2(to_mouse.y, to_mouse.x)
