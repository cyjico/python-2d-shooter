import pygame
import math
from dataclasses import dataclass


@dataclass(slots=True)
class Transform:
    position: tuple[float, float] = (0.0, 0.0)
    """World position of the entity."""
    rotation: float = 0.0
    """Rotation in degrees, clockwise."""
    scale: tuple[float, float] = (1.0, 1.0)
    """Scale factors along the x and y axes."""

    @staticmethod
    def apply(vector: pygame.Vector2, transform: Transform) -> pygame.Vector2:
        # NOTE:
        # For the following comments, let v = [x, y] be a vector in R^2

        # Derived by multiplying the scale matrix by v
        scaled_x = vector.x * transform.scale[0]
        scaled_y = vector.y * transform.scale[1]

        # Derived by multiplying the rotation matrix (clockwise version) by v
        # then adding the translation vector
        rot = transform.rotation * (math.pi / 180.0) 
        return pygame.Vector2(
            scaled_x * math.cos(rot)
            + scaled_y * math.sin(rot)
            + transform.position[0],
            scaled_y * math.cos(rot)
            - scaled_x * math.sin(rot)
            + transform.position[1],
        )
