from game.components.dash import DashIntent
from game.components.player import Player
from game.core_ecs.world import World
from game.resources.input_state import InputState
from game.resources.mystery_box_session import MysteryBoxSession


def player_dash_input_system(world: World):
    """Turns raw input into the player's DashIntent."""
    inputs = world.get_resource(InputState)
    # The mystery box menu owns the keyboard while it's open.
    in_menu = world.get_resource(MysteryBoxSession).is_open

    for _, (_, intent) in world.query(Player, DashIntent):
        intent.requested = inputs.dash_pressed and not in_menu
