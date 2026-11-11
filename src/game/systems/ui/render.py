import pygame

from game.components.ui import ButtonState, UIButton, UIImage, UILabel, UIPanel, UIRect
from game.core_ecs.world import World
from game.resources.asset_store import AssetStore


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
            pygame.draw.rect(surface, color, rect, border_radius=4)
        elif panel is not None:
            pygame.draw.rect(surface, panel.color, rect, border_radius=4)

        image = world.try_get_component(entity, UIImage)
        if image is not None:
            surface.blit(assets.image(image.image, rect.size), rect)

        label = world.try_get_component(entity, UILabel)
        if label is not None:
            text = assets.text(label.text, label.size, label.color)
            surface.blit(text, text.get_rect(center=rect.center))
