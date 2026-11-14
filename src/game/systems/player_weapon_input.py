from game.components.player import Player
from game.components.weapon_intent import WeaponIntent
from game.core_ecs.world import World
from game.resources.input_state import InputState
from game.resources.ui_state import UIState


def player_weapon_input_system(world: World):
    """Turns raw input into the player's WeaponIntent."""

    inputs = world.get_resource(InputState)
    ui_state = world.get_resource(UIState)
    over_ui = ui_state.is_pointer_over_ui
    blocked = ui_state.blocks_gameplay_input

    for _, (_, intent) in world.query(Player, WeaponIntent):
        if blocked:
            intent.fire_held = intent.fire_pressed = intent.reload = False
            intent.switch = 0
            intent.select = None
            continue

        intent.fire_held = inputs.primary_down and not over_ui
        intent.fire_pressed = inputs.primary_pressed and not over_ui
        intent.reload = inputs.reload_pressed
        intent.switch = inputs.weapon_switch
        intent.select = inputs.slot_pressed
