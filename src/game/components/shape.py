from dataclasses import dataclass, field
import pygame


@dataclass(slots=True)
class Shape:
    vertices: tuple[pygame.Vector2, ...]
    """Local to the entity's transform."""
    color: tuple[int, int, int] = (80, 200, 120)
    """From 0 to 255 in RGB format."""
    
    radius: float = field(init = False)
    """Bounding-circle radius around the transform origin. Computed once."""
    
    def __post_init__(self):
        self.radius = max((v.length() for v in self.vertices), default=0.0)

