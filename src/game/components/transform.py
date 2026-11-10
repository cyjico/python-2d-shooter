import pygame
import math
from dataclasses import dataclass, field


@dataclass(slots=True)
class Transform:
    position: pygame.Vector2 = field(default_factory=pygame.Vector2)
    """World position of the entity."""
    rotation: float = 0.0
    """Rotation in degrees, clockwise."""
    scale: tuple[float, float] = (1.0, 1.0)
    """Scale factors along the x and y axes."""

    def apply(self, vector: pygame.Vector2) -> pygame.Vector2:
        # NOTE:
        # For the following comments, let v = [x, y] be a vector in R^2

        # Derived by multiplying the scale matrix by v
        scaled_x = vector.x * self.scale[0]
        scaled_y = vector.y * self.scale[1]

        # Derived by multiplying the rotation matrix (clockwise version) by v
        # then adding the translation vector
        rot = self.rotation * (math.pi / 180.0)
        return pygame.Vector2(
            scaled_x * math.cos(rot) + scaled_y * math.sin(rot) + self.position[0],
            scaled_y * math.cos(rot) - scaled_x * math.sin(rot) + self.position[1],
        )
