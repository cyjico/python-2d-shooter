from dataclasses import dataclass

STARTING_PRICE = 200
PRICE_STEP = 200
"""Added to the price on every reroll or walk-away, and before the keep discount."""
KEEP_DISCOUNT = 0.05
"""Taken off the (stepped) price when a gun is kept."""


@dataclass(slots=True)
class MysteryBox:
    """Interact to buy a random gun of random rarity."""

    price: int = STARTING_PRICE
    """Cost of the next roll."""
