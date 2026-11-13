from dataclasses import dataclass, field

import pygame


@dataclass(slots=True)
class DamageNumber:
    """Floating text showing damage dealt. Rises, then fades out. Positioned by
    the entity's Transform, in world space."""

    text: str
    color: tuple[int, int, int]
    size: int
    """Font size once any pop-in has settled."""
    lifetime: float
    """Seconds."""
    critical: bool = False
    """Critical hits pop in larger and shrink to `size`."""
    velocity: pygame.Vector2 = field(default_factory=pygame.Vector2)
    """px/s. Slows down over time."""

    age: float = 0.0
    """Seconds since spawned. Runtime state."""
