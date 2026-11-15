from game.components.hud import PerkHudRow
from game.components.perks import PerkPath, Perks
from game.components.player import Player
from game.components.ui import UILabel
from game.constants.perks import FUSION_COLOR, FUSIONS, PATHS
from game.core_ecs.world import World

HUD_ROWS = len(PerkPath) + len(FUSIONS)
"""Every path plus every fusion."""


def perk_hud_system(world: World):
    """Top left, under the money: each path with stars, then the fusions owned."""
    perks = next((p for _, (_, p) in world.query(Player, Perks)), None)

    rows: list[tuple[str, tuple[int, int, int], int]] = []
    if perks is not None:
        for path, info in PATHS.items():
            stars = perks.stars(path)
            if stars:
                rows.append((info.short, info.color, stars))
        rows += [(f"+ {p.name}", FUSION_COLOR, 0) for p in perks.owned if p.is_fusion]

    for _, (label, row) in world.query(UILabel, PerkHudRow):
        if row.index < len(rows):
            label.text, label.color, label.stars = rows[row.index]
        else:
            label.text, label.stars = "", 0
