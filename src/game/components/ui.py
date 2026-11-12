from dataclasses import dataclass, field
from enum import Enum, auto

import pygame


@dataclass(slots=True)
class UIRect:
    anchor: tuple[float, float] = (0.0, 0.0)
    """Point on the screen, 0..1 (0.5, 0.5 = center)."""
    pivot: tuple[float, float] = (0.0, 0.0)
    """Point on this element that sits at the anchor, 0..1."""
    offset: tuple[float, float] = (0.0, 0.0)
    size: tuple[int, int] = (100, 30)
    layer: int = 0
    """Higher draws on top and wins hit tests."""
    rect: pygame.Rect = field(default_factory=pygame.Rect)
    """Computed by the layout system. Don't set manually."""


@dataclass(slots=True)
class UIPanel:
    color: tuple[int, int, int] = (50, 50, 50)


@dataclass(slots=True)
class UIImage:
    image: str
    """Key/path understood by AssetStore."""


@dataclass(slots=True)
class UILabel:
    text: str
    size: int = 20
    color: tuple[int, int, int] = (255, 255, 255)


class ButtonState(Enum):
    NORMAL = auto()
    HOVERED = auto()
    PRESSED = auto()


@dataclass(slots=True)
class UIButton:
    action: str
    """Identifier carried by ButtonClicked, e.g. "start", "quit"."""
    enabled: bool = True
    state: ButtonState = ButtonState.NORMAL
    normal_color: tuple[int, int, int] = (70, 70, 70)
    hovered_color: tuple[int, int, int] = (100, 100, 100)
    pressed_color: tuple[int, int, int] = (40, 40, 40)
