from dataclasses import dataclass
import pygame


@dataclass(slots=True)
class ConvexShape:
    vertices: tuple[pygame.Vector2, ...]
    """Local to the entity's transform."""
    color: tuple[int, int, int] = (80, 200, 120)
    """From 0 to 255 in RGB format."""
