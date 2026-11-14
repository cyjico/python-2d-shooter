from game.components.hud import StaminaGauge
from game.components.player import Player
from game.components.stamina import Stamina
from game.components.ui import UIGauge
from game.core_ecs.world import World


def stamina_hud_system(world: World):
    """Feeds the player's stamina into the stamina gauge."""
    stamina = next((s for _, (_, s) in world.query(Player, Stamina)), None)

    for _, (_, gauge) in world.query(StaminaGauge, UIGauge):
        if stamina is None:
            gauge.value = 0.0
        else:
            gauge.value = stamina.fraction
            gauge.segments = stamina.maximum
