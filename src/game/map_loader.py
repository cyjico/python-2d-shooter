from dataclasses import dataclass
from pathlib import Path

import pygame

from game.components.convex_collider import ConvexCollider
from game.components.rigid_body import RigidBody, inertia_of_box, mass_of_box
from game.components.shape import Shape
from game.components.transform import Transform
from game.core_ecs.entity import Entity
from game.core_ecs.world import World
from game.prefabs.enemies import spawn_charger
from game.resources.map_layout import MapLayout

TILE_SIZE = 40
"""Width and height of one map character, in pixels."""

WALL_COLOR = (90, 90, 110)
CRATE_COLOR = (200, 200, 200)
CRATE_SIZE = 30
"""Crates are a bit smaller than a tile so they fit through 1-tile gaps."""

ENEMY_SPAWNERS = {
    "X": spawn_charger,
}


def _box_vertices(width: float, height: float):
    """Four corners of a rectangle centred on (0, 0), clockwise."""
    half_w, half_h = width / 2, height / 2
    return (
        pygame.Vector2(-half_w, -half_h),
        pygame.Vector2(half_w, -half_h),
        pygame.Vector2(half_w, half_h),
        pygame.Vector2(-half_w, half_h),
    )


def _spawn_wall(world: World, col: int, row: int, width: int, height: int):
    """Spawn one wall covering `width` x `height` tiles, top-left at (col, row)."""
    pixel_w, pixel_h = width * TILE_SIZE, height * TILE_SIZE
    center = pygame.Vector2(
        col * TILE_SIZE + pixel_w / 2,
        row * TILE_SIZE + pixel_h / 2,
    )
    vertices = _box_vertices(pixel_w, pixel_h)
    # No RigidBody => the collision system treats it as immovable.
    world.create_entity(
        Transform(position=center),
        Shape(vertices=vertices, color=WALL_COLOR),
        ConvexCollider(vertices=vertices),
    )


def _spawn_merged_walls(world: World, lines: list[str]):
    """Cover every `#` with as few rectangles as possible (greedy).

    Fewer colliders = far fewer pair checks in the collision system.
    """
    used: set[tuple[int, int]] = set()
    """(col, row) of wall tiles already covered by a rectangle."""

    def is_free_wall(col: int, row: int):
        # Rows can have different lengths, so check bounds first.
        return (
            0 <= row < len(lines)
            and 0 <= col < len(lines[row])
            and lines[row][col] == "#"
            and (col, row) not in used
        )

    for row in range(len(lines)):
        for col in range(len(lines[row])):
            if not is_free_wall(col, row):
                continue

            # 1. Stretch right as far as the walls go.
            width = 1
            while is_free_wall(col + width, row):
                width += 1

            # 2. Stretch down while the whole next row segment is wall too.
            height = 1
            while all(is_free_wall(col + dx, row + height) for dx in range(width)):
                height += 1

            # 3. Mark every tile in the rectangle as used.
            for dy in range(height):
                for dx in range(width):
                    used.add((col + dx, row + dy))

            _spawn_wall(world, col, row, width, height)


def _spawn_crate(world: World, center: pygame.Vector2):
    vertices = _box_vertices(CRATE_SIZE, CRATE_SIZE)
    mass = mass_of_box(0.2, CRATE_SIZE, CRATE_SIZE)
    world.create_entity(
        RigidBody(
            mass=mass,
            drag=0.4,
            inertia=inertia_of_box(mass, CRATE_SIZE, CRATE_SIZE),
            angular_drag=0.4,
        ),
        Transform(position=center),
        Shape(vertices=vertices, color=CRATE_COLOR),
        ConvexCollider(vertices=vertices, bounciness=0.5),
    )


@dataclass(slots=True)
class MapSpawns:
    player: pygame.Vector2
    """World position of the player spawn (`P`)."""
    mystery_box: pygame.Vector2 | None
    """World position of the mystery box (`M`), if the map has one."""


def load_map(world: World, path: Path, player: Entity) -> MapSpawns:
    """Create entities for every tile in a text map and add a MapLayout resource."""
    lines = path.read_text().splitlines()

    world.add_resource(MapLayout(tuple(lines), TILE_SIZE))
    _spawn_merged_walls(world, lines)

    player_spawn = None
    box_spawn = None

    # `row` is the line number (y), `col` is the character number (x).
    for row, line in enumerate(lines):
        for col, char in enumerate(line):
            # Centre of this tile in world pixels.
            center = pygame.Vector2(
                col * TILE_SIZE + TILE_SIZE / 2,
                row * TILE_SIZE + TILE_SIZE / 2,
            )

            # Walls ("#") were already handled by _spawn_merged_walls.
            if char == "C":
                _spawn_crate(world, center)
            elif char == "P":
                player_spawn = center
            elif char in ENEMY_SPAWNERS:
                ENEMY_SPAWNERS[char](world, center, player)
            elif char == "M":
                box_spawn = center
            # Anything else (like ".") is empty floor.

    if player_spawn is None:
        raise ValueError(f"Map {path.name} has no player spawn 'P'")

    return MapSpawns(player=player_spawn, mystery_box=box_spawn)
