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
    aim_range: float = 350.0
    """At this distance or farther, dashes are fully random. Closer, they aim more at the target."""
    min_spread: float = 0.35
    """Max deviation (radians) from the target direction when right next to it."""

    max_target_dist_sqr: float = field(init=False)
    """Squared `max_target_distance`. Computed once."""

    # Runtime state
    timer: float = 0.0

    def __post_init__(self):
        self.max_target_dist_sqr = self.max_target_distance**2
        self.timer = random.uniform(*self.interval)
