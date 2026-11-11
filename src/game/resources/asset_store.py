import logging
from collections import OrderedDict
from pathlib import Path

import pygame

log = logging.getLogger(__name__)

MAX_TEXT_CACHE = 256
"""Rendered label surfaces kept before the least recently used is evicted."""

MISSING_IMAGE_SIZE = (32, 32)


def _missing_surface(size: tuple[int, int]):
    """Magenta/black checkerboard so a missing asset is obvious but harmless."""
    surf = pygame.Surface(size, pygame.SRCALPHA)
    cell = max(1, min(size) // 4)
    for y in range(0, size[1], cell):
        for x in range(0, size[0], cell):
            color = (255, 0, 255) if (x // cell + y // cell) % 2 == 0 else (0, 0, 0)
            surf.fill(color, (x, y, cell, cell))
    return surf


class AssetStore:
    def __init__(self, root: Path):
        self.root = root
        self._images: dict[tuple[str, tuple[int, int] | None], pygame.Surface] = {}
        self._fonts: dict[int, pygame.font.Font] = {}
        self._text: OrderedDict[tuple, pygame.Surface] = OrderedDict()

    def image(self, name: str, size: tuple[int, int] | None = None):
        key = (name, size)
        if key not in self._images:
            try:
                surf = pygame.image.load(self.root / name).convert_alpha()
                if size is not None:
                    surf = pygame.transform.smoothscale(surf, size)
            except (FileNotFoundError, pygame.error) as exc:
                log.warning("Could not load image %r: %s", name, exc)
                surf = _missing_surface(size or MISSING_IMAGE_SIZE)

            self._images[key] = surf
        return self._images[key]

    def font(self, size: int):
        if size not in self._fonts:
            self._fonts[size] = pygame.font.Font(None, size)
        return self._fonts[size]

    def text(self, text: str, size: int, color):
        key = (text, size, color)
        surf = self._text.get(key)
        if surf is None:
            surf = self.font(size).render(text, True, color)
            self._text[key] = surf

            # Remove recently least used.
            if len(self._text) > MAX_TEXT_CACHE:
                self._text.popitem(last=False)
        else:
            self._text.move_to_end(key)

        return surf
