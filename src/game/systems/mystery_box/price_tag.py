import pygame

from game.components.mystery_box import MysteryBox
from game.components.player import Player
from game.components.shape import Shape
from game.components.transform import Transform
from game.components.wallet import Wallet
from game.core_ecs.world import World
from game.resources.asset_store import AssetStore
from game.resources.camera import Camera
from game.resources.mystery_box_session import MysteryBoxSession
from game.util.draw import fill_rect

TEXT_SIZE = 22
AFFORDABLE_COLOR = (255, 255, 255)
TOO_EXPENSIVE_COLOR = (255, 110, 110)
BACKGROUND_COLOR = (15, 15, 20)
BACKGROUND_ALPHA = 220
BORDER_COLOR = (230, 180, 50)
"""Matches the box, so the tag reads as belonging to it."""
PADDING = (7, 3)
GAP = 10
"""Space between the top of the box and the tag, px."""


def mystery_box_price_render_system(world: World, surface: pygame.Surface):
    """Draws each box's price above it: light text on a dark tag, red if the
    player can't afford it."""
    camera = world.get_resource(Camera)
    assets = world.get_resource(AssetStore)
    wallet = next((w for _, (_, w) in world.query(Player, Wallet)), None)
    # Already paid for; the menu shows the prices that matter now.
    in_use = world.get_resource(MysteryBoxSession).box

    for entity, (box, transform, shape) in world.query(MysteryBox, Transform, Shape):
        if entity == in_use:
            continue
        radius = shape.radius * transform.max_scale
        if not camera.is_circle_visible(transform.position, radius + 40):
            continue

        affordable = wallet is None or wallet.can_afford(box.price)
        color = AFFORDABLE_COLOR if affordable else TOO_EXPENSIVE_COLOR
        text = assets.text(f"${box.price}", TEXT_SIZE, color)

        # Half the box's height, not its bounding radius, so the tag sits close.
        half_height = max(abs(v.y) for v in shape.vertices) * abs(transform.scale[1])
        center = camera.world_to_screen(transform.position)
        tag = text.get_rect().inflate(2 * PADDING[0], 2 * PADDING[1])
        tag.midbottom = (round(center.x), round(center.y - half_height - GAP))

        fill_rect(surface, BACKGROUND_COLOR, tag, BACKGROUND_ALPHA, border_radius=5)
        pygame.draw.rect(surface, BORDER_COLOR, tag, width=2, border_radius=5)
        surface.blit(text, text.get_rect(center=tag.center))
