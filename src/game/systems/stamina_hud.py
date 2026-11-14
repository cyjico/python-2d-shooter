from game.components.buffs import ActiveBuffs
from game.components.hud import StaminaGauge
from game.components.player import Player
from game.components.stamina import Stamina
from game.components.ui import UIGauge
from game.core_ecs.world import World
from game.util.buffs import Stat, stat_bonus


def stamina_hud_system(world: World):
    """Feeds the player's stamina into the stamina gauge."""
    player = next(
        ((ent, stam) for ent, (_, stam) in world.query(Player, Stamina)), None
    )

    for _, (_, gauge) in world.query(StaminaGauge, UIGauge):
        if player is None:
            gauge.value = 0.0
        else:
            bonus_segments = round(stat_bonus(world, player[0], Stat.STAMINA_SEGMENTS))
            gauge.value = player[1].fraction(bonus_segments)
            gauge.segments = player[1].segments + bonus_segments
