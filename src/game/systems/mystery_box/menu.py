"""Builds and tears down the mystery box's UI entities."""

from game.components.hud import InteractPromptLabel, MysteryBoxUI
from game.components.loadout import Gun, Loadout
from game.components.mystery_box import PRICE_STEP
from game.components.ui import UIButton, UILabel, UIPanel, UIRect
from game.components.wallet import Wallet
from game.constants.gun_buffs import describe_buff
from game.constants.rarity import RARITIES, rarity_color
from game.core_ecs.world import World
from game.resources.mystery_box_session import BoxPhase, MysteryBoxSession

MENU_LAYER = 10
PANEL_SIZE = (380, 220)
PANEL_COLOR = (35, 35, 45)
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
            _offer_menu(world, session, wallet)
        case BoxPhase.CHOOSE_SLOT:
            _slot_menu(world, session, loadout)


# Menus


def _rolling_menu(world: World, session: MysteryBoxSession):
    _panel(world)
    _label(world, "Mystery Box", -80, 28, TITLE_COLOR)
    session.rolling_label = _label(world, "", -20, 32)
    _label(world, f"Paid ${session.last_paid}", 40, 20, MUTED_COLOR)


def _offer_menu(world: World, session: MysteryBoxSession, wallet: Wallet):
    gun = session.offer
    assert gun is not None and gun.rarity is not None
    spec = gun.spec
    reroll_cost = session.last_paid + PRICE_STEP

    _panel(world)
    _label(world, "Mystery Box", -85, 24, TITLE_COLOR)
    _label(world, spec.name, -50, 32, RARITIES[gun.rarity].color)
    _label(world, describe_buff(spec.id, gun.rarity), -18, 22)
    _label(world, _stats(gun), 10, 18, MUTED_COLOR)

    _button(world, "Take [E]", "box_take", (-120, 65), BUTTON_SIZE)
    _button(
        world,
        f"Reroll ${reroll_cost} [R]",
        "box_reroll",
        (0, 65),
        BUTTON_SIZE,
        enabled=wallet.can_afford(reroll_cost),
    )
    _button(world, "Leave [Esc]", "box_leave", (120, 65), BUTTON_SIZE)


def _slot_menu(world: World, session: MysteryBoxSession, loadout: Loadout):
    assert session.offer is not None

    _panel(world)
    _label(world, "Replace which slot?", -85, 24, TITLE_COLOR)
    _label(world, session.offer.spec.name, -55, 26, rarity_color(session.offer.rarity))

    for i, gun in enumerate(loadout.slots):
        slot_name = "Primary" if i == 0 else "Secondary"
        _button(
            world,
            f"{i + 1}: {slot_name} - {gun.spec.name}",
            f"box_slot_{i}",
            (0, -15 + i * 42),
            (320, 36),
            color=rarity_color(gun.rarity),
        )

    _button(world, "Back [Esc]", "box_back", (0, 82), (120, 30))


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
    """A menu element positioned relative to the screen's center."""
    return world.create_entity(
        UIRect(
            anchor=(0.5, 0.5),
            pivot=(0.5, 0.5),
            offset=offset,
            size=size,
            layer=layer,
        ),
        MysteryBoxUI(),
        *components,
    )


def _panel(world: World):
    _element(
        world, UIPanel(PANEL_COLOR), offset=(0, 0), size=PANEL_SIZE, layer=MENU_LAYER
    )


def _label(world: World, text: str, y: float, size=20, color=WHITE):
    return _element(
        world, UILabel(text, size, color), offset=(0, y), size=(PANEL_SIZE[0], 30)
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
        UIButton(action, enabled=enabled),
        UILabel(text, 18, color if enabled else DISABLED_COLOR),
        offset=offset,
        size=size,
    )
