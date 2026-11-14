from dataclasses import dataclass

from game.constants.enemy_spawning import INITIAL_ENEMIES, START_INTERVAL


@dataclass(slots=True)
class EnemyDirector:
    """Survival spawning state. Tuning lives in `constants.enemy_spawning`."""

    elapsed: float = 0.0
    """Seconds survived. Drives difficulty."""
    timer: float = START_INTERVAL
    """Seconds until the next spawn."""
    backlog: int = INITIAL_ENEMIES
    """Enemies owed right away. Spawned on the next update, ignoring the cap."""
