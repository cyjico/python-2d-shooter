from dataclasses import dataclass, field
import pygame


@dataclass(slots=True, frozen=True)
class ConvexCollider:
    vertices: tuple[pygame.Vector2, ...]
    """Local to the entity's transform."""
    is_trigger: bool = False
    """Triggers report collisions but are never pushed apart."""
    bounciness: float = 0.2
    """0 = no bounce, 1 = perfectly elastic. The higher of the two colliders is used."""

    laabb: tuple[pygame.Vector2, pygame.Vector2] = field(init=False)
    """Local to the entity's transform (local axis-aligned bounding box)."""

    centroid: pygame.Vector2 = field(init=False)
    """Local to the entity's transform. The average of the bounds."""

    def __post_init__(self):
        xs = [v[0] for v in self.vertices]
        ys = [v[1] for v in self.vertices]

        minp = pygame.Vector2(min(xs), min(ys))
        maxp = pygame.Vector2(max(xs), max(ys))
        object.__setattr__(
            self,
            "laabb",
            (
                minp,
                maxp,
            ),
        )
        object.__setattr__(
            self,
            "centroid",
            (minp + maxp) / 2,
        )
