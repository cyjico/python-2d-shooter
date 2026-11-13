from game.components.hud import StaminaGauge
from game.components.player import Player
from game.components.stamina import Stamina
from game.components.ui import UIGauge
from game.core_ecs.world import World


def stamina_hud_system(world: World):
    """Feeds the player's stamina into the stamina gauge."""
    player = next((s for _, (_, s) in world.query(Player, Stamina)), None)

    for _, (gauge, _) in world.query(UIGauge, StaminaGauge):
        if player is None:
            gauge.value = 0.0
        else:
            gauge.value = player.fraction
            gauge.segments = player.segments
