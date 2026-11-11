from pathlib import Path
import pygame


class AssetStore:
    def __init__(self, root: Path):
        self.root = root
        self._images: dict[tuple[str, tuple[int, int] | None], pygame.Surface] = {}
        self._fonts: dict[int, pygame.font.Font] = {}
        self._text: dict[tuple, pygame.Surface] = {}

    def image(self, name: str, size: tuple[int, int] | None = None) -> pygame.Surface:
        key = (name, size)
        if key not in self._images:
            surf = pygame.image.load(self.root / name).convert_alpha()
            if size is not None:
                surf = pygame.transform.smoothscale(surf, size)
            self._images[key] = surf
        return self._images[key]

    def font(self, size: int) -> pygame.font.Font:
        if size not in self._fonts:
            self._fonts[size] = pygame.font.Font(None, size)
        return self._fonts[size]

    def text(self, text: str, size: int, color) -> pygame.Surface:
        key = (text, size, color)
        if key not in self._text:
            self._text[key] = self.font(size).render(text, True, color)
        return self._text[key]
