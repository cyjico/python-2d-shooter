import random

import pygame

from game.components.mystery_box import MysteryBox
from game.components.rigid_body import RigidBody
from game.components.transform import Transform
from game.core_ecs.entity import Entity
from game.core_ecs.world import World
from game.resources.map_layout import MapLayout
from game.systems.mystery_box.constants import (
    INTERACT_RANGE,
    MIN_MOVE_DISTANCE,
    SPAWN_CLEARANCE,
)


def nearest_box(world: World, position: pygame.Vector2):
    """The closest box within interact range, as (entity, box), or None."""
    best: tuple[Entity, MysteryBox] | None = None
    best_dist = INTERACT_RANGE
    for entity, (box, transform) in world.query(MysteryBox, Transform):
        dist = transform.position.distance_to(position)
        if dist <= best_dist:
            best, best_dist = (entity, box), dist
    return best


def relocate(
    world: World, box: Entity, player_pos: pygame.Vector2, rng: random.Random
):
    """Move the box to a random open spot elsewhere in the map."""
    transform = world.get_component(box, Transform)
    old = pygame.Vector2(transform.position)
    tiles = world.get_resource(MapLayout).spawnable_tiles()
    if not tiles:
        return

    bodies = [t.position for _, (t, _) in world.query(Transform, RigidBody)]
    bodies.append(player_pos)

    candidates = [
        tile
        for tile in tiles
        if tile.distance_to(old) >= MIN_MOVE_DISTANCE
        and all(tile.distance_to(b) >= SPAWN_CLEARANCE for b in bodies)
    ]
    transform.position = pygame.Vector2(rng.choice(candidates or tiles))
