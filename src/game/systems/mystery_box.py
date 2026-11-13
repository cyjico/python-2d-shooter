import random

import pygame

from game.components.hud import InteractPromptLabel, MysteryBoxUI
from game.components.loadout import Gun, Loadout
from game.components.mystery_box import KEEP_DISCOUNT, PRICE_STEP, MysteryBox
from game.components.player import Player
from game.components.rigid_body import RigidBody
from game.components.transform import Transform
from game.components.ui import UIButton, UILabel, UIPanel, UIRect
from game.components.wallet import Wallet
from game.constants.gun_buffs import describe_buff, make_gun, roll_gun
from game.constants.guns import ALL_GUNS
from game.constants.rarity import RARITIES, rarity_color
from game.core_ecs.entity import Entity
from game.core_ecs.world import World
from game.events.ui import ButtonClickedEvent
from game.resources.event_bus import EventBus
from game.resources.input_state import InputState
from game.resources.map_layout import MapLayout
from game.resources.mystery_box_session import BoxPhase, MysteryBoxSession

INTERACT_RANGE = 70.0
"""Max distance (px) between the player's and the box's centers to use it."""
ROLL_DURATION = 0.9
FLICKER_INTERVAL = 0.08
"""Seconds between random names while rolling."""

MIN_MOVE_DISTANCE = 240.0
"""How far (px) the box must move after a gun is taken."""
SPAWN_CLEARANCE = 60.0
"""Min distance (px) from any physics body (player, crates) when relocating."""

MENU_LAYER = 10
PANEL_SIZE = (380, 220)
PANEL_COLOR = (35, 35, 45)
TITLE_COLOR = (230, 180, 50)
MUTED_COLOR = (150, 150, 150)
DISABLED_COLOR = (110, 110, 110)

_default_rng = random.Random()


def mystery_box_system(world: World, dt: float, rng: random.Random | None = None):
    """Buying, rolling, taking and rerolling guns. Run after ui_interaction_system."""
    rng = rng or _default_rng
    session = world.get_resource(MysteryBoxSession)
    inputs = world.get_resource(InputState)
    clicked = {e.action for e in world.get_resource(EventBus).read(ButtonClickedEvent)}

    player = next(iter(world.query(Player, Transform, Loadout, Wallet)), None)
    if player is None:
        return
    _, (_, transform, loadout, wallet) = player

    match session.phase:
        case BoxPhase.CLOSED:
            _closed(world, session, inputs, transform, wallet)
        case BoxPhase.ROLLING:
            _rolling(world, session, dt, rng)
        case BoxPhase.OFFER:
            _offer(world, session, inputs, clicked, transform, loadout, wallet, rng)
        case BoxPhase.CHOOSE_SLOT:
            _choose_slot(world, session, inputs, clicked, transform, loadout, rng)


# Phases


def _closed(
    world: World,
    session: MysteryBoxSession,
    inputs: InputState,
    transform: Transform,
    wallet: Wallet,
):
    nearest = _nearest_box(world, transform.position)

    if nearest is None:
        _set_prompt(world, "")
        return

    entity, box = nearest
    if not wallet.can_afford(box.price):
        _set_prompt(
            world,
            f"Mystery Box  ${box.price}  (need ${box.price - wallet.balance} more)",
        )
        return

    _set_prompt(world, f"[E] Mystery Box  ${box.price}")
    if inputs.interact_pressed:
        wallet.spend(box.price)
        session.box = entity
        session.last_paid = box.price
        _set_prompt(world, "")
        _start_roll(world, session)


def _rolling(world: World, session: MysteryBoxSession, dt: float, rng: random.Random):
    session.roll_timer -= dt
    session.flicker_timer -= dt

    if session.roll_timer <= 0:
        spec, rarity = roll_gun(rng)
        session.offer = make_gun(spec, rarity)
        _set_phase(world, session, BoxPhase.OFFER)
        return

    if session.flicker_timer <= 0 and session.rolling_label is not None:
        session.flicker_timer = FLICKER_INTERVAL
        label = world.try_get_component(session.rolling_label, UILabel)
        if label is not None:
            # Cosmetic only, so it doesn't touch the roll's rng.
            label.text = random.choice(list(ALL_GUNS.values())).name


def _offer(
    world: World,
    session: MysteryBoxSession,
    inputs: InputState,
    clicked: set[str],
    transform: Transform,
    loadout: Loadout,
    wallet: Wallet,
    rng: random.Random,
):
    assert session.box is not None and session.offer is not None
    box = world.get_component(session.box, MysteryBox)
    reroll_cost = session.last_paid + PRICE_STEP

    if "box_take" in clicked or inputs.interact_pressed:
        if len(loadout.slots) < loadout.max_slots:
            loadout.put_primary(session.offer)
            _finish(world, session, transform, rng)
        else:
            _set_phase(world, session, BoxPhase.CHOOSE_SLOT)

    elif ("box_reroll" in clicked or inputs.reload_pressed) and wallet.can_afford(
        reroll_cost
    ):
        wallet.spend(reroll_cost)
        session.last_paid = reroll_cost
        box.price = reroll_cost
        _start_roll(world, session)

    elif "box_leave" in clicked or inputs.cancel_pressed:
        # Walking away loses the gun, same price penalty as a reroll.
        box.price = session.last_paid + PRICE_STEP
        _close(world, session)


def _choose_slot(
    world: World,
    session: MysteryBoxSession,
    inputs: InputState,
    clicked: set[str],
    transform: Transform,
    loadout: Loadout,
    rng: random.Random,
):
    assert session.offer is not None

    index = inputs.slot_pressed
    for i in range(len(loadout.slots)):
        if f"box_slot_{i}" in clicked:
            index = i

    if index is not None and 0 <= index < len(loadout.slots):
        loadout.replace(index, session.offer)
        _finish(world, session, transform, rng)
    elif "box_back" in clicked or inputs.cancel_pressed:
        _set_phase(world, session, BoxPhase.OFFER)


# Transitions


def _start_roll(world: World, session: MysteryBoxSession):
    session.offer = None
    session.roll_timer = ROLL_DURATION
    session.flicker_timer = 0.0
    _set_phase(world, session, BoxPhase.ROLLING)


def _finish(
    world: World,
    session: MysteryBoxSession,
    player_transform: Transform,
    rng: random.Random,
):
    """The gun was taken: discount the price and move the box."""
    assert session.box is not None
    box = world.get_component(session.box, MysteryBox)
    box.price = keep_price(session.last_paid)
    _relocate(world, session.box, player_transform.position, rng)
    _close(world, session)


def keep_price(last_paid: int) -> int:
    """Next price after keeping a gun: step up, then 5% off."""
    return round((last_paid + PRICE_STEP) * (1 - KEEP_DISCOUNT))


def _close(world: World, session: MysteryBoxSession):
    session.phase = BoxPhase.CLOSED
    session.box = None
    session.offer = None
    session.rolling_label = None
    _clear_menu(world)


def _set_phase(world: World, session: MysteryBoxSession, phase: BoxPhase):
    session.phase = phase
    _clear_menu(world)

    match phase:
        case BoxPhase.ROLLING:
            _build_rolling_menu(world, session)
        case BoxPhase.OFFER:
            _build_offer_menu(world, session)
        case BoxPhase.CHOOSE_SLOT:
            _build_slot_menu(world, session)


def _relocate(
    world: World, box: Entity, player_pos: pygame.Vector2, rng: random.Random
):
    """Move the box to a random open spot elsewhere in the map."""
    transform = world.get_component(box, Transform)
    old = pygame.Vector2(transform.position)
    tiles = world.get_resource(MapLayout).spawnable_tiles()
    if not tiles:
        return

    bodies = [t.position for _, (t, _) in world.query(Transform, RigidBody)]
    bodies.append(player_pos)

    candidates = [
        tile
        for tile in tiles
        if tile.distance_to(old) >= MIN_MOVE_DISTANCE
        and all(tile.distance_to(b) >= SPAWN_CLEARANCE for b in bodies)
    ]
    transform.position = pygame.Vector2(rng.choice(candidates or tiles))


# Queries


def _nearest_box(world: World, position: pygame.Vector2):
    best: tuple[Entity, MysteryBox] | None = None
    best_dist = INTERACT_RANGE
    for entity, (box, transform) in world.query(MysteryBox, Transform):
        dist = transform.position.distance_to(position)
        if dist <= best_dist:
            best, best_dist = (entity, box), dist
    return best


def _set_prompt(world: World, text: str):
    for _, (label, _) in world.query(UILabel, InteractPromptLabel):
        label.text = text


# Menu UI


def _clear_menu(world: World):
    for entity, _ in world.query(MysteryBoxUI):
        world.destroy_entity(entity)


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


def _label(world: World, text: str, y: float, size=20, color=(255, 255, 255)):
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
    color=(255, 255, 255),
):
    return _element(
        world,
        UIButton(action, enabled=enabled),
        UILabel(text, 18, color if enabled else DISABLED_COLOR),
        offset=offset,
        size=size,
    )


def _panel(world: World):
    _element(
        world, UIPanel(PANEL_COLOR), offset=(0, 0), size=PANEL_SIZE, layer=MENU_LAYER
    )


def _build_rolling_menu(world: World, session: MysteryBoxSession):
    _panel(world)
    _label(world, "Mystery Box", -80, 28, TITLE_COLOR)
    session.rolling_label = _label(world, "", -20, 32)
    _label(world, f"Paid ${session.last_paid}", 40, 20, MUTED_COLOR)


def _build_offer_menu(world: World, session: MysteryBoxSession):
    gun = session.offer
    assert gun is not None and gun.rarity is not None
    spec = gun.spec
    wallet = next((w for _, (_, w) in world.query(Player, Wallet)), None)
    reroll_cost = session.last_paid + PRICE_STEP

    _panel(world)
    _label(world, "Mystery Box", -85, 24, TITLE_COLOR)
    _label(world, spec.name, -50, 32, RARITIES[gun.rarity].color)
    _label(world, describe_buff(spec.id, gun.rarity), -18, 22)
    _label(world, _stats(gun), 10, 18, MUTED_COLOR)

    _button(world, "Take [E]", "box_take", (-120, 65), (112, 34))
    _button(
        world,
        f"Reroll ${reroll_cost} [R]",
        "box_reroll",
        (0, 65),
        (112, 34),
        enabled=wallet is not None and wallet.can_afford(reroll_cost),
    )
    _button(world, "Leave [Esc]", "box_leave", (120, 65), (112, 34))


def _build_slot_menu(world: World, session: MysteryBoxSession):
    assert session.offer is not None
    loadout = next((l for _, (_, l) in world.query(Player, Loadout)), None)
    assert loadout is not None

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
