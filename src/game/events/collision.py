from collections.abc import Iterable, Iterator
from dataclasses import dataclass

import pygame

from game.core_ecs.entity import Entity


@dataclass(slots=True)
class CollisionEvent:
    entity_a: Entity
    entity_b: Entity
    normal: pygame.Vector2
    """Unit vector pointing from `entity_a` toward `entity_b`."""
    depth: float
    """How far the two shapes overlap along `normal`."""


def directed(collisions: Iterable[CollisionEvent]):
    """Each collision seen from both sides, as (me, other)."""
    for collision in collisions:
        yield collision.entity_a, collision.entity_b
        yield collision.entity_b, collision.entity_a
