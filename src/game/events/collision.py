from dataclasses import dataclass

import pygame

from ..core_ecs.entity import Entity


@dataclass(slots=True)
class CollisionEvent:
    entity_a: Entity
    entity_b: Entity
    normal: pygame.Vector2
    """Unit vector pointing from `entity_a` toward `entity_b`."""
    depth: float
    """How far the two shapes overlap along `normal`."""
