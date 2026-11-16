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


@dataclass(slots=True)
class BuffStatusLabel:
    """Marks a UILabel that lists the player's active buffs."""


@dataclass(slots=True)
class ScreenUI:
    """Marks UI of a full-screen menu (main menu, game over)."""


@dataclass(slots=True)
class PerkDraftUI:
    """Marks UI elements of the perk pick menu, destroyed when it changes."""


@dataclass(slots=True)
class SandboxUI:
    """Marks UI elements of the sandbox panel, destroyed when it changes."""


@dataclass(slots=True)
class PerkHudRow:
    """Marks a UILabel listing one perk path's stars (or a fusion), top left."""

    index: int


@dataclass(slots=True)
class WaveLabel:
    """Marks a UILabel that shows the wave number in roman numerals."""


@dataclass(slots=True)
class WaveRemainingLabel:
    """Marks a UILabel that shows how many enemies are left in the wave."""


@dataclass(slots=True)
class WaveBannerLabel:
    """Marks the big centered UILabel announcing the next wave during a break."""


@dataclass(slots=True)
class WaveBannerSubLabel:
    """Marks the smaller UILabel under the wave banner (countdown, last enemy)."""
