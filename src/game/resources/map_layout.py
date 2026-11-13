from dataclasses import dataclass

import pygame

WALL = "#"


@dataclass(frozen=True, slots=True)
class MapLayout:
    """The loaded map's tile grid, for placing things at runtime."""

    lines: tuple[str, ...]
    tile_size: int

    def tile_center(self, col: int, row: int):
        return pygame.Vector2(
            col * self.tile_size + self.tile_size / 2,
            row * self.tile_size + self.tile_size / 2,
        )

    def _is_open(self, col: int, row: int):
        """In bounds and not a wall."""
        return (
            0 <= row < len(self.lines)
            and 0 <= col < len(self.lines[row])
            and self.lines[row][col] != WALL
        )

    def spawnable_tiles(self) -> list[pygame.Vector2]:
        """Centers of tiles whose whole 3x3 neighbourhood is open floor.

        Keeps spawns inside the room and off its walls and openings.
        """
        return [
            self.tile_center(col, row)
            for row in range(len(self.lines))
            for col in range(len(self.lines[row]))
            if all(
                self._is_open(col + dx, row + dy)
                for dy in (-1, 0, 1)
                for dx in (-1, 0, 1)
            )
        ]
