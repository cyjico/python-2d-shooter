import pygame

from ..core_ecs.world import World
from ..resources.camera import Camera
from ..resources.input_state import InputState


def input_system(world: World):
    inputs = world.get_resource(InputState)

    keys = pygame.key.get_pressed()

    # Movement
    movement = pygame.Vector2(
        int(keys[pygame.K_d]) - int(keys[pygame.K_a]),
        int(keys[pygame.K_s]) - int(keys[pygame.K_w]),
    )

    # Convert to unit vector to prevent faster diagonal movement
    if movement.length_squared() > 0:
        movement = movement.normalize()

    inputs.movement = movement

    # Mouse
    inputs.aim_position = pygame.Vector2(pygame.mouse.get_pos())
    inputs.primary_down = pygame.mouse.get_pressed()[0]
