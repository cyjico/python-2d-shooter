from game.components.player import Player
from game.components.weapon_intent import WeaponIntent
from game.core_ecs.world import World
from game.resources.input_state import InputState
from game.resources.ui_state import UIState


def player_weapon_input_system(world: World):
    """Turns raw input into the player's WeaponIntent. Run after ui_interaction."""

    inputs = world.get_resource(InputState)
    over_ui = world.get_resource(UIState).is_pointer_over_ui

    for _, (_, intent) in world.query(Player, WeaponIntent):
        intent.fire_held = inputs.primary_down and not over_ui
        intent.fire_pressed = inputs.primary_pressed and not over_ui
        intent.reload = inputs.reload_pressed
        intent.switch = inputs.weapon_switch
