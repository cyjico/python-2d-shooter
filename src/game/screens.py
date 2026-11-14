"""Full-screen menus: the main menu and the game over screen."""

from game.components.hud import ScreenUI
from game.components.ui import UIButton, UILabel, UIPanel, UIRect
from game.core_ecs.world import World
from game.resources.camera import Camera
from game.resources.run_stats import RunStats

PLAY_ACTION = "play"
"""Action of the Play button on both screens. Starts a new run."""

SCREEN_LAYER = 50
PLAY_BUTTON_SIZE = (200, 56)

OVERLAY_COLOR = (0, 0, 0)
OVERLAY_ALPHA = 140
PANEL_SIZE = (360, 320)
PANEL_COLOR = (35, 35, 45)
PANEL_ALPHA = 235
TITLE_COLOR = (230, 70, 70)
STAT_COLOR = (230, 230, 230)


def _centered(world: World, *components, y: float, size, layer: int):
    """A UI element positioned relative to the screen's center."""
    return world.create_entity(
        UIRect(
            anchor=(0.5, 0.5), pivot=(0.5, 0.5), offset=(0, y), size=size, layer=layer
        ),
        ScreenUI(),
        *components,
    )


def _play_button(world: World, y: float):
    _centered(
        world,
        UIButton(PLAY_ACTION),
        UILabel("Play", 34),
        y=y,
        size=PLAY_BUTTON_SIZE,
        layer=SCREEN_LAYER + 2,
    )


def build_main_menu(world: World):
    _play_button(world, 0)


def format_time(seconds: float):
    """E.g. 125.4 -> "2:05"."""
    whole = int(seconds)
    return f"{whole // 60}:{whole % 60:02d}"


def build_game_over(world: World, stats: RunStats, cash_gained: int):
    """Dims the frozen world and shows the run's stats with a Play button."""
    viewport = world.get_resource(Camera).viewport_size
    _centered(
        world,
        UIPanel(OVERLAY_COLOR, OVERLAY_ALPHA),
        y=0,
        size=(round(viewport.x), round(viewport.y)),
        layer=SCREEN_LAYER,
    )
    _centered(
        world,
        UIPanel(PANEL_COLOR, PANEL_ALPHA),
        y=0,
        size=PANEL_SIZE,
        layer=SCREEN_LAYER + 1,
    )

    def line(text: str, y: float, size=26, color=STAT_COLOR):
        _centered(
            world,
            UILabel(text, size, color),
            y=y,
            size=(PANEL_SIZE[0], 30),
            layer=SCREEN_LAYER + 2,
        )

    line("You Died", -120, 44, TITLE_COLOR)
    line(f"Enemies Killed: {stats.enemies_killed}", -70)
    line(f"Mystery Boxes Opened: {stats.boxes_opened}", -38)
    line(f"Time Survived: {format_time(stats.time_survived)}", -6)
    line(f"Total Cash Gained: ${cash_gained}", 26)

    _play_button(world, 100)
