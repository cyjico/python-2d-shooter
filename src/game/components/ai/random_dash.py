import random
from dataclasses import dataclass, field


@dataclass(slots=True)
class RandomDashAI:
    """Now and then dashes in a random direction that isn't blocked by a wall.

    Needs AI, Dash and DashIntent.
    """

    interval: tuple[float, float] = (1.5, 3.5)
    """Random seconds between dash rolls."""
    chance: float = 0.6
    """Chance, from 0 to 1, that a roll actually dashes."""
    max_target_distance: float = 450.0
    """Only dashes while the target is this close, so it looks like a reaction."""

    max_target_dist_sqr: float = field(init=False)
    """Squared `max_target_distance`. Computed once."""

    # Runtime state
    timer: float = 0.0

    def __post_init__(self):
        self.max_target_dist_sqr = self.max_target_distance**2
        self.timer = random.uniform(*self.interval)
