from dataclasses import dataclass


@dataclass(slots=True)
class WeaponIntent:
    """What the wielder wants to do this frame.

    The player's input fills this in; an AI could fill it the same way.
    """

    fire_held: bool = False
    fire_pressed: bool = False
    reload: bool = False
    switch: int = 0
    """-1 = previous weapon, +1 = next weapon, 0 = stay."""
    select: int | None = None
    """Loadout slot to equip directly. Applied before `switch`."""
