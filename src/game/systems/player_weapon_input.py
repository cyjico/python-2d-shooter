from game.components.player import Player
from game.components.weapon_intent import WeaponIntent
from game.core_ecs.world import World
from game.resources.input_state import InputState
from game.resources.mystery_box_session import MysteryBoxSession
from game.resources.ui_state import UIState


def player_weapon_input_system(world: World):
    """Turns raw input into the player's WeaponIntent. Run after ui_interaction."""

    inputs = world.get_resource(InputState)
    over_ui = world.get_resource(UIState).is_pointer_over_ui
    # The mystery box menu owns the keyboard and mouse while it's open.
    in_menu = world.get_resource(MysteryBoxSession).is_open

    for _, (_, intent) in world.query(Player, WeaponIntent):
        if in_menu:
            intent.fire_held = intent.fire_pressed = intent.reload = False
            intent.switch = 0
            intent.select = None
            continue

        intent.fire_held = inputs.primary_down and not over_ui
        intent.fire_pressed = inputs.primary_pressed and not over_ui
        intent.reload = inputs.reload_pressed
        intent.switch = inputs.weapon_switch
        intent.select = inputs.slot_pressed
