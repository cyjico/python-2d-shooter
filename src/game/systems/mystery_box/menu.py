"""Builds and tears down the mystery box's UI entities."""

from game.components.hud import InteractPromptLabel, MysteryBoxUI
from game.components.loadout import Gun, Loadout
from game.components.ui import UIButton, UILabel, UIPanel, UIRect
from game.components.wallet import Wallet
from game.constants.gun_buffs import describe_buff
from game.constants.mystery_box import stepped_price
from game.constants.rarity import rarity_color, rarity_stars
from game.core_ecs.world import World
from game.resources.mystery_box_session import BoxPhase, MysteryBoxSession
from game.resources.ui_state import UIState

INPUT_OWNER = "mystery_box"
"""Key this menu uses to block gameplay input in UIState."""

MENU_LAYER = 10
PANEL_SIZE = (380, 220)
PANEL_TOP = 44
"""Gap between the top of the screen and the panel, px. Clears the buff list."""
PANEL_COLOR = (35, 35, 45)
PANEL_ALPHA = 170
"""See-through, so the menu doesn't hide what's happening behind it."""
BUTTON_ALPHA = 210
TITLE_COLOR = (230, 180, 50)
MUTED_COLOR = (150, 150, 150)
DISABLED_COLOR = (110, 110, 130)
WHITE = (255, 255, 255)

BUTTON_SIZE = (112, 34)


# Public API


def set_prompt(world: World, text: str):
    """Text of the "press E" prompt shown near the bottom of the screen."""
    for _, (label, _) in world.query(UILabel, InteractPromptLabel):
        label.text = text


def clear_menu(world: World):
    for entity, _ in world.query(MysteryBoxUI):
        world.destroy_entity(entity)
    world.get_resource(UIState).release_gameplay_input(INPUT_OWNER)


def show_menu(
    world: World,
    session: MysteryBoxSession,
    loadout: Loadout,
    wallet: Wallet,
):
    """Replace the current menu with the one for `session.phase`."""
    clear_menu(world)

    match session.phase:
        case BoxPhase.ROLLING:
            _rolling_menu(world, session)
        case BoxPhase.OFFER:
            _offer_menu(world, session, loadout, wallet)

    if session.is_open:
        world.get_resource(UIState).block_gameplay_input(INPUT_OWNER)


# Menus


def _rolling_menu(world: World, session: MysteryBoxSession):
    _panel(world)
    _label(world, "Mystery Box", -80, 28, TITLE_COLOR)
    session.rolling_label = _label(world, "", -20, 32)
    _label(world, f"Paid ${session.last_paid}", 40, 20, MUTED_COLOR)


def _offer_menu(
    world: World, session: MysteryBoxSession, loadout: Loadout, wallet: Wallet
):
    gun = session.offer
    assert gun is not None and gun.rarity is not None
    spec = gun.spec
    reroll_cost = stepped_price(session.last_paid)

    _panel(world)
    _label(world, "Mystery Box", -85, 24, TITLE_COLOR)
    _label(
        world, spec.name, -52, 32, rarity_color(gun.rarity), rarity_stars(gun.rarity)
    )
    _label(world, describe_buff(spec.id, gun.rarity), -22, 22)
    _label(world, _stats(gun), 2, 18, MUTED_COLOR)

    # Taking with full slots swaps out the gun in hand, so say which one.
    held = loadout.equipped
    if len(loadout.slots) >= loadout.max_slots and held is not None:
        _label(world, f"Replaces your {held.spec.name}", 26, 18, MUTED_COLOR)

    _button(world, "Take [E]", "box_take", (-120, 70), BUTTON_SIZE)
    _button(
        world,
        f"Reroll ${reroll_cost} [R]",
        "box_reroll",
        (0, 70),
        BUTTON_SIZE,
        enabled=wallet.can_afford(reroll_cost),
    )
    _button(world, "Leave [Q]", "box_leave", (120, 70), BUTTON_SIZE)


def _stats(gun: Gun):
    s = gun.spec
    damage = f"{s.damage:g} dmg" + (f" x{s.pellets}" if s.pellets > 1 else "")
    extra = f"  pierce {s.pierce}" if s.pierce else ""
    return f"{damage}  {s.fire_rate:g}/s  mag {s.magazine_size}{extra}"


# Element helpers


def _element(
    world: World,
    *components,
    offset: tuple[float, float],
    size: tuple[int, int],
    layer: int = MENU_LAYER + 1,
):
    """A menu element positioned relative to the panel's center, which sits
    near the top of the screen."""
    panel_center_y = PANEL_TOP + PANEL_SIZE[1] / 2
    return world.create_entity(
        UIRect(
            anchor=(0.5, 0.0),
            pivot=(0.5, 0.5),
            offset=(offset[0], panel_center_y + offset[1]),
            size=size,
            layer=layer,
        ),
        MysteryBoxUI(),
        *components,
    )


def _panel(world: World):
    _element(
        world,
        UIPanel(PANEL_COLOR, PANEL_ALPHA),
        offset=(0, 0),
        size=PANEL_SIZE,
        layer=MENU_LAYER,
    )


def _label(world: World, text: str, y: float, size=20, color=WHITE, stars=0):
    return _element(
        world,
        UILabel(text, size, color, stars),
        offset=(0, y),
        size=(PANEL_SIZE[0], 30),
    )


def _button(
    world: World,
    text: str,
    action: str,
    offset: tuple[float, float],
    size: tuple[int, int],
    enabled=True,
    color=WHITE,
):
    return _element(
        world,
        UIButton(action, enabled=enabled, alpha=BUTTON_ALPHA),
        UILabel(text, 18, color if enabled else DISABLED_COLOR),
        offset=offset,
        size=size,
    )
