import math
from collections.abc import Iterable

import pygame

Color = tuple[int, int, int]


def fill_rect(
    surface: pygame.Surface,
    color: Color,
    rect: pygame.Rect,
    alpha: int = 255,
    border_radius: int = 0,
):
    """Like pygame.draw.rect, but can be see-through (alpha < 255)."""
    if alpha >= 255:
        pygame.draw.rect(surface, color, rect, border_radius=border_radius)
        return
    if alpha <= 0 or rect.width <= 0 or rect.height <= 0:
        return

    layer = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(
        layer, (*color, alpha), layer.get_rect(), border_radius=border_radius
    )
    surface.blit(layer, rect)


def star_points(center: pygame.Vector2, radius: float):
    """The 10 corners of a five-pointed star pointing up."""
    inner = radius * 0.45
    return [
        center
        + pygame.Vector2(math.cos(angle), math.sin(angle))
        * (radius if i % 2 == 0 else inner)
        for i in range(10)
        for angle in [-math.pi / 2 + i * math.pi / 5]
    ]


def draw_stars(
    surface: pygame.Surface,
    color: Color,
    left: float,
    center_y: float,
    count: int,
    radius: float,
    gap: float = 2.0,
):
    """`count` stars in a row starting at `left`. Returns the row's width."""
    step = 2 * radius + gap
    for i in range(count):
        center = pygame.Vector2(left + radius + i * step, center_y)
        points = star_points(center, radius)
        pygame.draw.polygon(surface, color, points)
        pygame.draw.aalines(surface, color, True, points)
    return max(0.0, count * step - gap)


def draw_bar(
    surface: pygame.Surface,
    rect: pygame.Rect,
    fills: Iterable[tuple[float, Color]],
    empty_color: Color,
    border_color: Color,
    *,
    border_width: int = 2,
    border_radius: int = 0,
    segments: int = 1,
    marker_color: Color | None = None,
):
    """Draws a bar. `fills` sit side by side from the left; each is
    (fraction of the full width, color). Fractions past 100% are cut off.
    Markers split the bar into `segments` equal parts."""
    pygame.draw.rect(surface, empty_color, rect, border_radius=border_radius)

    covered = 0.0
    start = rect.left
    for fraction, color in fills:
        covered = min(1.0, covered + max(0.0, fraction))
        end = rect.left + round(rect.width * covered)
        if end > start:
            pygame.draw.rect(
                surface,
                color,
                (start, rect.top, end - start, rect.height),
                border_radius=border_radius,
            )
        start = end

    if marker_color is not None:
        for i in range(1, segments):
            x = rect.left + round(rect.width * i / segments)
            pygame.draw.line(
                surface, marker_color, (x, rect.top), (x, rect.bottom - 1), 2
            )

    pygame.draw.rect(
        surface, border_color, rect, width=border_width, border_radius=border_radius
    )
