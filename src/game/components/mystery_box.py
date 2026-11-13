from dataclasses import dataclass

from game.constants.mystery_box import STARTING_PRICE


@dataclass(slots=True)
class MysteryBox:
    """Interact to buy a random gun of random rarity."""

    price: int = STARTING_PRICE
    """Cost of the next roll."""
