import math

from game.components.hud import WeaponStatusLabel
from game.components.loadout import Loadout
from game.components.player import Player
from game.components.ui import UILabel
from game.core_ecs.world import World

NORMAL_COLOR = (255, 255, 255)
LOW_COLOR = (255, 170, 60)
EMPTY_COLOR = (255, 80, 80)
LOW_AMMO_FRACTION = 0.25
"""At or below this much of the magazine, the label suggests reloading."""


def weapon_status_hud_system(world: World):
    loadout = next((l for _, (_, l) in world.query(Player, Loadout)), None)
    gun = loadout.equipped if loadout is not None else None

    color = NORMAL_COLOR
    if gun is None:
        text = ""
    elif gun.reloading:
        text = "reloading..."
    elif gun.magazine == 0 and gun.reserve == 0:
        text, color = "out of ammo", EMPTY_COLOR
    elif gun.reserve > 0 and gun.magazine <= math.ceil(
        gun.spec.magazine_size * LOW_AMMO_FRACTION
    ):
        text, color = f"{gun.magazine} / {gun.reserve}  [R]", LOW_COLOR
    else:
        text = f"{gun.magazine} / {gun.reserve}"

    for _, (label, _) in world.query(UILabel, WeaponStatusLabel):
        label.text, label.color = text, color
