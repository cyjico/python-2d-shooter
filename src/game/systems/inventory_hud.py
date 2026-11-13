from game.components.hud import InventorySlotUI, MoneyLabel
from game.components.loadout import Loadout
from game.components.player import Player
from game.components.ui import UILabel, UIPanel
from game.components.wallet import Wallet
from game.constants.rarity import rarity_color
from game.core_ecs.world import World

ACTIVE_SLOT_COLOR = (95, 95, 125)
INACTIVE_SLOT_COLOR = (45, 45, 55)
EMPTY_SLOT_COLOR = (120, 120, 120)


def inventory_hud_system(world: World):
    """Shows the player's loadout slots and wallet balance."""
    player = next(iter(world.query(Player, Loadout)), None)
    loadout = player[1][1] if player is not None else None

    for _, (slot, label, panel) in world.query(InventorySlotUI, UILabel, UIPanel):
        gun = (
            loadout.slots[slot.index]
            if loadout is not None and slot.index < len(loadout.slots)
            else None
        )
        if gun is None:
            label.text = f"{slot.index + 1}  Empty"
            label.color = EMPTY_SLOT_COLOR
        else:
            label.text = f"{slot.index + 1}  {gun.spec.name}"
            label.color = rarity_color(gun.rarity)

        is_active = (
            gun is not None and loadout is not None and loadout.active == slot.index
        )
        panel.color = ACTIVE_SLOT_COLOR if is_active else INACTIVE_SLOT_COLOR

    wallet = next((w for _, (_, w) in world.query(Player, Wallet)), None)
    for _, (label, _) in world.query(UILabel, MoneyLabel):
        label.text = f"${wallet.balance}" if wallet is not None else ""
