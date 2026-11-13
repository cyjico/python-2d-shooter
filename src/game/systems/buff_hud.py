import math

from game.components.buffs import ActiveBuffs
from game.components.hud import BuffStatusLabel
from game.components.player import Player
from game.components.ui import UILabel
from game.core_ecs.world import World


def buff_hud_system(world: World):
    """Lists the player's active buffs with their seconds left."""
    active = next((b for _, (_, b) in world.query(Player, ActiveBuffs)), None)
    text = (
        "   ".join(f"{b.spec.name} {math.ceil(b.time_left)}s" for b in active.buffs)
        if active is not None
        else ""
    )

    for _, (label, _) in world.query(UILabel, BuffStatusLabel):
        label.text = text
