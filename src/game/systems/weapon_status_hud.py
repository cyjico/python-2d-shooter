from game.components.hud import WeaponStatusLabel
from game.components.loadout import Loadout
from game.components.player import Player
from game.components.ui import UILabel
from game.core_ecs.world import World


def weapon_status_hud_system(world: World):
    loadout = next((l for _, (_, l) in world.query(Player, Loadout)), None)
    gun = loadout.equipped if loadout is not None else None

    if gun is None:
        text = ""
    elif gun.reloading:
        text = "reloading..."
    else:
        text = f"{gun.magazine} / {gun.reserve}"

    for _, (label, _) in world.query(UILabel, WeaponStatusLabel):
        label.text = text
