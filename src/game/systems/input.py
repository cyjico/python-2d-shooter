from collections.abc import Iterable

import pygame

from game.core_ecs.world import World
from game.resources.input_state import InputState

SLOT_KEYS = {pygame.K_1: 0, pygame.K_2: 1}
"""Number key -> loadout slot index."""
NUMBER_KEYS = {key: i for i, key in enumerate(range(pygame.K_1, pygame.K_9 + 1))}
"""Number key -> menu choice index."""


def input_system(world: World, events: Iterable[pygame.event.Event]):
    inputs = world.get_resource(InputState)

    # Movement
    keys = pygame.key.get_pressed()
    movement = pygame.Vector2(
        int(keys[pygame.K_d]) - int(keys[pygame.K_a]),
        int(keys[pygame.K_s]) - int(keys[pygame.K_w]),
    )
    if movement.length_squared() > 0:
        movement = movement.normalize()

    inputs.movement = movement

    # Mouse
    inputs.mouse_pos = pygame.Vector2(pygame.mouse.get_pos())

    # Transitions come from events so a press+release between polls isn't lost
    pressed = released = reload = interact = reroll = cancel = dash_pressed = False
    switch = 0
    slot = number = None
    for event in events:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pressed = True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            reload = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            released = True
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f:
                switch += 1
            elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT, pygame.K_SPACE):
                dash_pressed = True
            elif event.key in NUMBER_KEYS:
                number = NUMBER_KEYS[event.key]
                slot = SLOT_KEYS.get(event.key, slot)
            elif event.key == pygame.K_e:
                interact = True
            elif event.key == pygame.K_r:
                # Menus read it as reroll; gameplay input is blocked while one
                # is open, so it only reloads outside them.
                reroll = reload = True
            elif event.key == pygame.K_q:
                cancel = True
        elif event.type == pygame.MOUSEWHEEL:
            switch -= event.y

    inputs.primary_down = pygame.mouse.get_pressed()[0]
    inputs.primary_pressed = pressed
    inputs.primary_released = released
    inputs.reload_pressed = reload
    inputs.weapon_switch = (switch > 0) - (switch < 0)
    inputs.slot_pressed = slot
    inputs.number_pressed = number
    inputs.interact_pressed = interact
    inputs.reroll_pressed = reroll
    inputs.cancel_pressed = cancel
    inputs.dash_pressed = dash_pressed
