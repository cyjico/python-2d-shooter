from collections.abc import Iterable

import pygame

Color = tuple[int, int, int]


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
