import math

import pygame

from game.components.mover import Mover
from game.components.player import Player
from game.components.transform import Transform
from game.core_ecs.world import World
from game.resources.camera import Camera
from game.resources.input_state import InputState
from game.resources.ui_state import UIState


def player_control_system(world: World, dt: float):
    inputs = world.get_resource(InputState)
    camera = world.get_resource(Camera)

    mouse_world = camera.screen_to_world(inputs.mouse_pos)
    # Stand still while a menu has the input.
    blocked = world.get_resource(UIState).blocks_gameplay_input

    for ent, _ in world.query(Player):
        mover = world.get_component(ent, Mover)
        transform = world.get_component(ent, Transform)

        if blocked:
            mover.move_dir = pygame.Vector2()
            mover.face_angle = None
            continue

        mover.move_dir = inputs.movement

        to_mouse = mouse_world - transform.position
        if to_mouse.length_squared() < 1.0:
            continue

        # Both pygame's y-down axes and Transform's rotation are clockwise-positive.
        mover.face_angle = math.atan2(to_mouse.y, to_mouse.x)
