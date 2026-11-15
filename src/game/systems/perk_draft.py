"""After every cleared wave: pick one of three perks before the next wave."""

import random
import textwrap

from game.components.hud import PerkDraftUI
from game.components.perks import MAX_STARS, Perks, PerkSpec
from game.components.player import Player
from game.components.ui import UIButton, UILabel, UIRect
from game.components.wallet import Wallet
from game.constants.perks import (
    PATHS,
    perk_color,
    reroll_price,
    roll_offer,
    stars_color,
)
from game.core_ecs.entity import Entity
from game.core_ecs.world import World
from game.events.ui import ButtonClickedEvent
from game.resources.enemy_director import EnemyDirector, WavePhase
from game.resources.event_bus import EventBus
from game.resources.input_state import InputState
from game.resources.mystery_box_session import MysteryBoxSession
from game.resources.perk_draft import PerkDraft
from game.resources.ui_state import UIState
from game.util.perks import apply_perk
from game.util.rng import resolve_rng

INPUT_OWNER = "perk_draft"
PICK_ACTION = "perk_pick_{}"
REROLL_ACTION = "perk_reroll"

DRAFT_LAYER = 20
CARD_SIZE = (230, 230)
CARD_SPACING = 244
"""Px between card centers."""
CARD_CENTER_Y = 65
"""Below the screen's center, leaving room for the wave banner above."""
CARD_COLORS = ((40, 40, 54), (66, 66, 88), (28, 28, 38))
"""Normal, hovered, pressed."""
CARD_ALPHA = 255
DESCRIPTION_WIDTH = 25
"""Characters per description line."""
REROLL_SIZE = (200, 34)
WHITE = (255, 255, 255)
MUTED = (150, 150, 160)
DISABLED = (110, 110, 130)


def perk_draft_system(world: World, rng: random.Random | None = None):
    """Opens the menu once a wave is cleared and holds the break's countdown
    until a perk is picked. Rerolls cost money."""
    draft = world.get_resource(PerkDraft)
    player = next(iter(world.query(Player, Perks, Wallet)), None)
    if player is None:
        return
    entity, (_, perks, wallet) = player
    rng = resolve_rng(rng)

    if not draft.is_open:
        if _should_open(world, draft):
            director = world.get_resource(EnemyDirector)
            draft.drafted_wave = director.wave
            draft.rerolls = 0
            draft.offer = roll_offer(perks, rng)
            draft.is_open = True
            director.held = True
            _show(world, draft, wallet)
        return

    inputs = world.get_resource(InputState)
    clicked = {e.action for e in world.get_resource(EventBus).read(ButtonClickedEvent)}

    choice = next(
        (i for i in range(len(draft.offer)) if PICK_ACTION.format(i) in clicked),
        None,
    )
    if inputs.number_pressed is not None and inputs.number_pressed < len(draft.offer):
        choice = inputs.number_pressed

    price = reroll_price(draft.rerolls)
    if choice is not None:
        apply_perk(world, entity, draft.offer[choice])
        close_draft(world)
        # The key that picked the perk shouldn't also switch guns.
        inputs.slot_pressed = inputs.number_pressed = None
    elif (REROLL_ACTION in clicked or inputs.reroll_pressed) and wallet.can_afford(
        price
    ):
        wallet.spend(price)
        draft.rerolls += 1
        draft.offer = roll_offer(perks, rng)
        _show(world, draft, wallet)


def _should_open(world: World, draft: PerkDraft):
    director = world.get_resource(EnemyDirector)
    if director.phase is not WavePhase.BREAK or not director.just_cleared:
        return False
    if draft.drafted_wave >= director.wave:
        return False
    # Wait for the mystery box menu to close rather than stacking menus.
    session = world.try_get_resource(MysteryBoxSession)
    return session is None or not session.is_open


def close_draft(world: World):
    """Removes the menu and lets the next wave's countdown run. Safe anytime."""
    draft = world.get_resource(PerkDraft)
    draft.is_open = False
    draft.offer = []
    director = world.try_get_resource(EnemyDirector)
    if director is not None:
        director.held = False
    _clear(world)


def _clear(world: World):
    for entity, _ in world.query(PerkDraftUI):
        world.destroy_entity(entity)
    world.get_resource(UIState).release_gameplay_input(INPUT_OWNER)


def _show(world: World, draft: PerkDraft, wallet: Wallet):
    _clear(world)
    world.get_resource(UIState).block_gameplay_input(INPUT_OWNER)

    count = len(draft.offer)
    for i, spec in enumerate(draft.offer):
        x = (i - (count - 1) / 2) * CARD_SPACING
        _card(world, i, spec, x)

    price = reroll_price(draft.rerolls)
    affordable = wallet.can_afford(price)
    _element(
        world,
        UIButton(REROLL_ACTION, enabled=affordable, alpha=CARD_ALPHA),
        UILabel(f"Reroll ${price} [R]", 18, WHITE if affordable else DISABLED),
        offset=(0, CARD_CENTER_Y + CARD_SIZE[1] / 2 + 29),
        size=REROLL_SIZE,
        layer=DRAFT_LAYER,
    )


def _header(spec: PerkSpec):
    if spec.path is not None:
        name = PATHS[spec.path].name.upper()
        return f"{name} - LEGENDARY" if spec.stars == MAX_STARS else name
    if spec.is_fusion:
        return "FUSION  " + " + ".join(PATHS[p].short for p in spec.requires)
    return "BONUS"


def _card(world: World, index: int, spec: PerkSpec, x: float):
    normal, hovered, pressed = CARD_COLORS
    _element(
        world,
        UIButton(
            PICK_ACTION.format(index),
            alpha=CARD_ALPHA,
            normal_color=normal,
            hovered_color=hovered,
            pressed_color=pressed,
        ),
        offset=(x, CARD_CENTER_Y),
        size=CARD_SIZE,
        layer=DRAFT_LAYER,
    )

    def line(text: str, y: float, size: int, color=WHITE, stars=0):
        _element(
            world,
            UILabel(text, size, color, stars),
            offset=(x, CARD_CENTER_Y + y),
            size=(CARD_SIZE[0] - 16, 24),
            layer=DRAFT_LAYER + 1,
        )

    line(_header(spec), -94, 16, perk_color(spec))
    if spec.permanent:
        line("", -68, 24, stars_color(spec.stars), spec.stars)
    line(spec.name, -36, 27)
    for row, text in enumerate(textwrap.wrap(spec.description, DESCRIPTION_WIDTH)):
        line(text, -4 + row * 22, 18, (215, 215, 225))
    line(f"[{index + 1}]", 96, 16, MUTED)


def _element(
    world: World,
    *components,
    offset: tuple[float, float],
    size: tuple[int, int],
    layer: int,
) -> Entity:
    return world.create_entity(
        UIRect(
            anchor=(0.5, 0.5), pivot=(0.5, 0.5), offset=offset, size=size, layer=layer
        ),
        PerkDraftUI(),
        *components,
    )
