import random
from dataclasses import dataclass

import pygame

from game.components.loadout import Loadout
from game.components.mystery_box import MysteryBox
from game.components.player import Player
from game.components.transform import Transform
from game.components.ui import UILabel
from game.components.wallet import Wallet
from game.constants.gun_buffs import make_gun, roll_gun
from game.constants.guns import ALL_GUNS
from game.constants.mystery_box import (
    FLICKER_INTERVAL,
    ROLL_DURATION,
    keep_price,
    stepped_price,
)
from game.core_ecs.world import World
from game.events.ui import ButtonClickedEvent
from game.resources.event_bus import EventBus
from game.resources.input_state import InputState
from game.resources.mystery_box_session import BoxPhase, MysteryBoxSession
from game.systems.mystery_box.menu import clear_menu, set_prompt, show_menu
from game.systems.mystery_box.placement import nearest_box
from game.util.spawn_points import relocate

_default_rng = random.Random()


@dataclass(slots=True)
class _Frame:
    """Everything a phase handler needs for this frame."""

    world: World
    dt: float
    rng: random.Random
    session: MysteryBoxSession
    inputs: InputState
    clicked: set[str]
    """Actions of the buttons clicked this frame."""
    transform: Transform
    loadout: Loadout
    wallet: Wallet


def mystery_box_system(world: World, dt: float, rng: random.Random | None = None):
    """Buying, rolling, taking and rerolling guns. Run after ui_interaction_system."""
    player = next(iter(world.query(Player, Transform, Loadout, Wallet)), None)
    if player is None:
        return
    _, (_, transform, loadout, wallet) = player

    f = _Frame(
        world=world,
        dt=dt,
        rng=rng or _default_rng,
        session=world.get_resource(MysteryBoxSession),
        inputs=world.get_resource(InputState),
        clicked={
            e.action for e in world.get_resource(EventBus).read(ButtonClickedEvent)
        },
        transform=transform,
        loadout=loadout,
        wallet=wallet,
    )

    match f.session.phase:
        case BoxPhase.CLOSED:
            _closed(f)
        case BoxPhase.ROLLING:
            _rolling(f)
        case BoxPhase.OFFER:
            _offer(f)
        case BoxPhase.CHOOSE_SLOT:
            _choose_slot(f)


# Phases


def _closed(f: _Frame):
    nearest = nearest_box(f.world, f.transform.position)
    if nearest is None:
        set_prompt(f.world, "")
        return

    entity, box = nearest
    if not f.wallet.can_afford(box.price):
        short = box.price - f.wallet.balance
        set_prompt(f.world, f"Mystery Box  ${box.price}  (need ${short} more)")
        return

    set_prompt(f.world, f"[E] Mystery Box  ${box.price}")
    if f.inputs.interact_pressed:
        f.wallet.spend(box.price)
        f.session.box = entity
        f.session.last_paid = box.price
        set_prompt(f.world, "")
        _start_roll(f)


def _rolling(f: _Frame):
    session = f.session
    session.roll_timer -= f.dt
    session.flicker_timer -= f.dt

    if session.roll_timer <= 0:
        spec, rarity = roll_gun(f.rng)
        session.offer = make_gun(spec, rarity)
        _set_phase(f, BoxPhase.OFFER)
        return

    if session.flicker_timer <= 0 and session.rolling_label is not None:
        session.flicker_timer = FLICKER_INTERVAL
        label = f.world.try_get_component(session.rolling_label, UILabel)
        if label is not None:
            # Cosmetic only, so it doesn't touch the roll's rng.
            label.text = random.choice(list(ALL_GUNS.values())).name


def _offer(f: _Frame):
    session = f.session
    assert session.box is not None and session.offer is not None
    box = f.world.get_component(session.box, MysteryBox)
    reroll_cost = stepped_price(session.last_paid)

    if "box_take" in f.clicked or f.inputs.interact_pressed:
        if len(f.loadout.slots) < f.loadout.max_slots:
            f.loadout.put_primary(session.offer)
            _finish(f)
        else:
            _set_phase(f, BoxPhase.CHOOSE_SLOT)

    elif ("box_reroll" in f.clicked or f.inputs.reload_pressed) and f.wallet.can_afford(
        reroll_cost
    ):
        f.wallet.spend(reroll_cost)
        session.last_paid = reroll_cost
        box.price = reroll_cost
        _start_roll(f)

    elif "box_leave" in f.clicked or f.inputs.cancel_pressed:
        # Walking away loses the gun, same price penalty as a reroll.
        box.price = stepped_price(session.last_paid)
        _close(f)


def _choose_slot(f: _Frame):
    assert f.session.offer is not None

    index = f.inputs.slot_pressed
    for i in range(len(f.loadout.slots)):
        if f"box_slot_{i}" in f.clicked:
            index = i

    if index is not None and 0 <= index < len(f.loadout.slots):
        f.loadout.replace(index, f.session.offer)
        _finish(f)
    elif "box_back" in f.clicked or f.inputs.cancel_pressed:
        _set_phase(f, BoxPhase.OFFER)


# Transitions


def _set_phase(f: _Frame, phase: BoxPhase):
    f.session.phase = phase
    show_menu(f.world, f.session, f.loadout, f.wallet)


def _start_roll(f: _Frame):
    f.session.offer = None
    f.session.roll_timer = ROLL_DURATION
    f.session.flicker_timer = 0.0
    _set_phase(f, BoxPhase.ROLLING)


def _finish(f: _Frame):
    """The gun was taken: discount the price and move the box."""
    assert f.session.box is not None
    box = f.world.get_component(f.session.box, MysteryBox)
    box.price = keep_price(f.session.last_paid)
    relocate(f.world, f.session.box, f.rng)
    _close(f)


def _close(f: _Frame):
    session = f.session
    session.phase = BoxPhase.CLOSED
    session.box = None
    session.offer = None
    session.rolling_label = None
    clear_menu(f.world)
