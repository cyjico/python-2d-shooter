from dataclasses import dataclass


@dataclass(slots=True)
class WeaponStatusLabel:
    """Marks a UILabel that shows the player's current gun and ammo."""


@dataclass(slots=True)
class InventorySlotUI:
    """Marks a UI element that shows one of the player's loadout slots."""

    index: int


@dataclass(slots=True)
class MoneyLabel:
    """Marks a UILabel that shows the player's wallet balance."""


@dataclass(slots=True)
class InteractPromptLabel:
    """Marks a UILabel that tells the player what they can interact with."""


@dataclass(slots=True)
class MysteryBoxUI:
    """Marks UI elements of the mystery box menu, destroyed when it changes."""
