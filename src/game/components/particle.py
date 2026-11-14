from dataclasses import dataclass, field

import pygame


@dataclass(slots=True)
class Particle:
    """A short-lived visual effect (gib, spark, shard) that moves without
    physics and removes itself after `duration` seconds."""

    duration: float
    velocity: pygame.Vector2 = field(default_factory=pygame.Vector2)
    """px/s."""
    drag: float = 0.0
    """Fraction of velocity lost per second."""
    spin: float = 0.0
    """Radians per second, clockwise."""
    shrink_start: float = 1.0
    """Fraction of `duration` after which the particle's scale shrinks to 0.
    1 = never shrinks."""
    keeps_moving_when_frozen: bool = False
    """True for effects that play while the rest of the world is frozen
    (the player's death shards)."""

    age: float = 0.0
    """Seconds since spawned. Runtime state."""

    @property
    def progress(self):
        """0 when spawned, 1 when expired."""
        return min(1.0, self.age / self.duration) if self.duration > 0 else 1.0


@dataclass(slots=True)
class Spark:
    """Drawn as a thin line trailing behind its Particle's velocity."""

    length: float
    color: tuple[int, int, int] = (255, 230, 150)
