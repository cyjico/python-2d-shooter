"""Mystery box tuning and pricing rules."""

STARTING_PRICE = 200
"""Cost of a fresh box's first roll."""
PRICE_STEP = 200
"""Added to the price on every reroll or walk-away, and before the keep discount."""
KEEP_DISCOUNT = 0.05
"""Taken off the (stepped) price when a gun is kept."""

INTERACT_RANGE = 70.0
"""Max distance (px) between the player's and the box's centers to use it."""
ROLL_DURATION = 0.9
FLICKER_INTERVAL = 0.08
"""Seconds between random names while rolling."""

MIN_MOVE_DISTANCE = 240.0
"""How far (px) the box must move after a gun is taken."""


def stepped_price(last_paid: int) -> int:
    """Price after a reroll or walking away."""
    return last_paid + PRICE_STEP


def keep_price(last_paid: int) -> int:
    """Next price after keeping a gun: step up, then 5% off."""
    return round(stepped_price(last_paid) * (1 - KEEP_DISCOUNT))
