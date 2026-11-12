import math
from dataclasses import dataclass, field
from typing import Sequence, overload

import pygame


@dataclass(slots=True)
class Transform:
    position: pygame.Vector2 = field(default_factory=pygame.Vector2)
    """World position of the entity."""
    rotation: float = 0.0
    """Rotation in radians, clockwise."""
    scale: tuple[float, float] = (1.0, 1.0)
    """Scale factors along the x and y axes."""

    def apply_all(self, vectors: Sequence[pygame.Vector2]):
        return [self.apply(v) for v in vectors]

    def apply(self, vector: pygame.Vector2):
        # NOTE:
        # For the following comments, let v = [x, y] be a vector in R^2.

        # Derived by multiplying the scale matrix by v.
        scaled_x = vector.x * self.scale[0]
        scaled_y = vector.y * self.scale[1]

        # Derived by multiplying the rotation matrix by v then adding the
        # translation vector.
        cos_rot = math.cos(self.rotation)
        sin_rot = math.sin(self.rotation)

        # Despite the rotation matrix being counter-clockwise, pygame has it
        # going clockwise.
        return pygame.Vector2(
            scaled_x * cos_rot - scaled_y * sin_rot + self.position[0],
            scaled_x * sin_rot + scaled_y * cos_rot + self.position[1],
        )
