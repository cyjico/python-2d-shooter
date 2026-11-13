import pygame

from game.components.mystery_box import MysteryBox
from game.components.transform import Transform
from game.constants.mystery_box import INTERACT_RANGE
from game.core_ecs.entity import Entity
from game.core_ecs.world import World


def nearest_box(world: World, position: pygame.Vector2):
    """The closest box within interact range, as (entity, box), or None."""
    best: tuple[Entity, MysteryBox] | None = None
    best_dist = INTERACT_RANGE
    for entity, (box, transform) in world.query(MysteryBox, Transform):
        dist = transform.position.distance_to(position)
        if dist <= best_dist:
            best, best_dist = (entity, box), dist
    return best
