from dataclasses import dataclass


@dataclass(slots=True)
class RunStats:
    """Totals for the current run, shown on the game over screen.

    Money earned is tracked by the player's `Wallet.total_earned`.
    """

    enemies_killed: int = 0
    boxes_opened: int = 0
    """Paid mystery box openings. Rerolls don't count as new openings."""
    time_survived: float = 0.0
    """Seconds."""
    wave: int = 0
    """Highest wave reached."""
