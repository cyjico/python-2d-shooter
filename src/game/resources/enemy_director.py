from dataclasses import dataclass

from game.constants.enemy_spawning import START_INTERVAL


@dataclass(slots=True)
class EnemyDirector:
    """Survival spawning state. Tuning lives in `constants.enemy_spawning`."""

    elapsed: float = 0.0
    """Seconds survived. Drives difficulty."""
    timer: float = START_INTERVAL
    """Seconds until the next spawn."""
