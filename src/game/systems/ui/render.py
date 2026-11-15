import pygame

from game.components.ui import (
    ButtonState,
    UIButton,
    UIGauge,
    UIImage,
    UILabel,
    UIPanel,
    UIRect,
)
from game.core_ecs.world import World
from game.resources.asset_store import AssetStore
from game.util.draw import draw_bar, draw_stars, fill_rect

STAR_SCALE = 0.32
"""Star radius relative to the label's font size."""
STAR_TEXT_GAP = 6
"""Space between a label's text and its stars, px."""


def _draw_gauge(surface: pygame.Surface, rect: pygame.Rect, gauge: UIGauge):
    draw_bar(
        surface,
        rect,
        [(gauge.value, gauge.fill_color)],
        gauge.empty_color,
        gauge.border_color,
        border_radius=4,
        segments=gauge.segments,
        marker_color=gauge.marker_color,
    )


def ui_render_system(world: World, surface: pygame.Surface):
    assets = world.get_resource(AssetStore)

    for entity, (ui,) in sorted(world.query(UIRect), key=lambda item: item[1][0].layer):
        rect = ui.rect

        button = world.try_get_component(entity, UIButton)
        panel = world.try_get_component(entity, UIPanel)
        if button is not None:
            color = {
                ButtonState.NORMAL: button.normal_color,
                ButtonState.HOVERED: button.hovered_color,
                ButtonState.PRESSED: button.pressed_color,
            }[button.state]
            fill_rect(surface, color, rect, button.alpha, border_radius=4)
        elif panel is not None:
            fill_rect(surface, panel.color, rect, panel.alpha, border_radius=4)

        gauge = world.try_get_component(entity, UIGauge)
        if gauge is not None:
            _draw_gauge(surface, rect, gauge)

        image = world.try_get_component(entity, UIImage)
        if image is not None:
            surface.blit(assets.image(image.image, rect.size), rect)

        label = world.try_get_component(entity, UILabel)
        if label is not None:
            _draw_label(surface, assets, rect, label)


def _draw_label(
    surface: pygame.Surface, assets: AssetStore, rect: pygame.Rect, label: UILabel
):
    """Text centered in `rect`, followed by the label's stars if it has any."""
    text = assets.text(label.text, label.size, label.color)
    if label.stars <= 0:
        if label.align_left:
            surface.blit(text, text.get_rect(midleft=rect.midleft))
        else:
            surface.blit(text, text.get_rect(center=rect.center))
        return

    radius = max(3.0, label.size * STAR_SCALE)
    stars_width = label.stars * (2 * radius + 2) - 2
    gap = STAR_TEXT_GAP if label.text else 0
    total = text.get_width() + gap + stars_width

    left = rect.left if label.align_left else rect.centerx - total / 2
    surface.blit(text, text.get_rect(midleft=(round(left), rect.centery)))
    draw_stars(
        surface,
        label.color,
        left + text.get_width() + gap,
        rect.centery,
        label.stars,
        radius,
    )
