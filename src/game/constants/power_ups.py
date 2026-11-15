"""Power-ups that enemies drop when killed."""

from dataclasses import dataclass

from game.components.buffs import BuffSpec
from game.components.power_up import PowerUpKind


@dataclass(frozen=True, slots=True)
class PowerUpInfo:
    name: str
    symbol: str
    """Drawn inside the pickup."""
    color: tuple[int, int, int]
    weight: float
    """Relative chance among drops."""


POWER_UPS: dict[PowerUpKind, PowerUpInfo] = {
    PowerUpKind.MED_KIT: PowerUpInfo("Med Kit", "+", (90, 220, 110), 30),
    PowerUpKind.MAX_AMMO: PowerUpInfo("Max Ammo", "A", (240, 200, 60), 30),
    PowerUpKind.SHIELD: PowerUpInfo("Shield", "S", (90, 190, 255), 25),
    PowerUpKind.NUKE: PowerUpInfo("Nuke", "N", (255, 90, 50), 10),
}

DROP_CHANCE = 0.15
"""Chance that a kill by the player (or their drones) drops a power-up."""
MAX_DROPS_PER_WAVE = 8
"""So a big wave doesn't rain power-ups."""
LIFETIME = 20.0
"""Seconds a power-up lies around before vanishing."""
BLINK_TIME = 5.0
"""It blinks for its last seconds."""
PICKUP_RADIUS = 34.0
"""Px between the player's center and the power-up's center to collect it."""

MED_KIT_HEAL = 0.5
"""Fraction of max health."""
SHIELD_BUFF = BuffSpec(id="shield_drop", name="Shield", duration=20.0, shield=150.0)
NUKE_CASH = 400
"""Paid on top of nothing: nuked enemies give no bounty."""
NUKE_FLASH_TIME = 0.6
