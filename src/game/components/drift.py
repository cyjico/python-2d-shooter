from dataclasses import dataclass, field

import pygame


@dataclass(slots=True)
class Drift:
    """Moves its entity without physics (no collisions, no mass), for effects.
    Slows down by `drag` per second."""

    velocity: pygame.Vector2 = field(default_factory=pygame.Vector2)
    """px/s."""
    drag: float = 0.0
