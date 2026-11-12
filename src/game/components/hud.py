from dataclasses import dataclass


@dataclass(slots=True)
class WeaponStatusLabel:
    """Marks a UILabel that shows the player's current gun and ammo."""
