from game.components.dash import DashIntent
from game.components.player import Player
from game.core_ecs.world import World
from game.resources.input_state import InputState
from game.resources.ui_state import UIState


def player_dash_input_system(world: World):
    """Turns raw input into the player's DashIntent."""
    inputs = world.get_resource(InputState)
    blocked = world.get_resource(UIState).blocks_gameplay_input

    for _, (_, intent) in world.query(Player, DashIntent):
        intent.requested = inputs.dash_pressed and not blocked
