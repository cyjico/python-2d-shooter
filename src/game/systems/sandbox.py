"""Sandbox mode: the map and its crates with no waves. A panel in the top right
spawns enemies on demand and has a few testing toggles."""

import random

import pygame

from game.components.faction import Faction, Team
from game.components.hud import SandboxUI
from game.components.invulnerable import Invulnerable
from game.components.player import Player
from game.components.projectile import Projectile
from game.components.transform import Transform
from game.components.ui import UIButton, UILabel, UIPanel, UIRect
from game.components.wallet import Wallet
from game.constants.enemy_spawning import EnemySpawn
from game.core_ecs.entity import Entity
from game.core_ecs.world import World
from game.events.ui import ButtonClickedEvent
from game.prefabs.enemies import (
    spawn_charger,
    spawn_chaser,
    spawn_shooter,
    spawn_splitter,
)
from game.resources.event_bus import EventBus
from game.resources.sandbox import Sandbox
from game.util.raycast import raycast_static_bundle
from game.util.rng import resolve_rng
from game.util.roman import to_roman

MENU_ACTION = "sandbox_menu"
"""Leaves the sandbox for the main menu. Handled by the game."""

SPAWN_ACTION = "sandbox_spawn_{}"
COUNT_ACTION = "sandbox_count"
LEVEL_DOWN_ACTION = "sandbox_level_down"
LEVEL_UP_ACTION = "sandbox_level_up"
GOD_ACTION = "sandbox_god"
CASH_ACTION = "sandbox_cash"
CLEAR_ACTION = "sandbox_clear"
COLLAPSE_ACTION = "sandbox_collapse"

ENEMIES: dict[str, EnemySpawn] = {
    "Chaser": spawn_chaser,
    "Splitter": spawn_splitter,
    "Charger": spawn_charger,
    "Shooter": spawn_shooter,
}
"""Button text -> prefab, in panel order."""
SPAWN_COUNTS = (1, 3, 5, 10)
"""The amount button cycles through these."""
MAX_LEVEL = 30
CASH_AMOUNT = 1000

SPAWN_DIST = (160.0, 280.0)
"""Px from the player, so enemies appear on screen but not on top of them."""
SPAWN_CLEARANCE = 24.0
"""Half-width of the wall check toward a spawn spot, and room left past it."""
SPAWN_TRIES = 12

PANEL_LAYER = 15
PANEL_WIDTH = 176
PANEL_MARGIN = 16
"""Px from the screen's top right corner."""
PADDING = 8
ROW_HEIGHT = 28
ROW_GAP = 4
SMALL_BUTTON_WIDTH = 32
PANEL_COLOR = (25, 25, 32)
PANEL_ALPHA = 215
WHITE = (255, 255, 255)
MUTED = (150, 150, 160)
ON_COLOR = (120, 230, 120)
CASH_COLOR = (230, 180, 50)
DANGER_COLOR = (255, 120, 120)


def sandbox_system(world: World, rng: random.Random | None = None):
    """Reacts to the panel's buttons. Builds the panel on its first run."""
    sandbox = world.get_resource(Sandbox)
    player = next((e for e, _ in world.query(Player)), None)
    if player is None:
        return

    if not any(True for _ in world.query(SandboxUI)):
        _show(world, sandbox, player)

    clicked = [e.action for e in world.get_resource(EventBus).read(ButtonClickedEvent)]
    changed = False
    for action in clicked:
        changed |= _handle(world, sandbox, player, action, resolve_rng(rng))
    if changed:
        _show(world, sandbox, player)


def _handle(
    world: World, sandbox: Sandbox, player: Entity, action: str, rng: random.Random
):
    """Returns True if the panel needs redrawing."""
    for name, spawn in ENEMIES.items():
        if action == SPAWN_ACTION.format(name):
            spawn_enemies(world, spawn, SPAWN_COUNTS[sandbox.count_index], player, rng)
            return False

    if action == CASH_ACTION:
        world.get_component(player, Wallet).balance += CASH_AMOUNT
    elif action == CLEAR_ACTION:
        clear_enemies(world)
    elif action == COUNT_ACTION:
        sandbox.count_index = (sandbox.count_index + 1) % len(SPAWN_COUNTS)
        return True
    elif action == LEVEL_DOWN_ACTION:
        sandbox.level = max(1, sandbox.level - 1)
        return True
    elif action == LEVEL_UP_ACTION:
        sandbox.level = min(MAX_LEVEL, sandbox.level + 1)
        return True
    elif action == GOD_ACTION:
        if world.try_remove_component(player, Invulnerable) is None:
            world.add_component(player, Invulnerable())
        return True
    elif action == COLLAPSE_ACTION:
        sandbox.collapsed = not sandbox.collapsed
        return True
    return False


def spawn_enemies(
    world: World,
    spawn: EnemySpawn,
    count: int,
    player: Entity,
    rng: random.Random | None = None,
):
    """`count` enemies around the player, on spots it can see.
    wave_scaling_system makes them as strong as the sandbox's level."""
    rng = resolve_rng(rng)
    origin = world.get_component(player, Transform).position
    return [
        spawn(world, _spawn_point(world, origin, rng), player) for _ in range(count)
    ]


def _spawn_point(world: World, origin: pygame.Vector2, rng: random.Random):
    """A random spot near `origin` with no wall in between. Falls back to the
    last try; collision pushes anything inside a wall out of it."""
    point = pygame.Vector2(origin)
    for _ in range(SPAWN_TRIES):
        direction = pygame.Vector2(1, 0).rotate(rng.uniform(0, 360))
        distance = rng.uniform(*SPAWN_DIST)
        point = origin + direction * distance
        if not raycast_static_bundle(
            world, origin, direction, distance + SPAWN_CLEARANCE, SPAWN_CLEARANCE
        ):
            break
    return point


def clear_enemies(world: World):
    """Removes every enemy and enemy bullet. Not a kill: no bounty, no drops."""
    doomed = [e for e, (f,) in world.query(Faction) if f.team & Team.ENEMY]
    doomed += [e for e, (p,) in world.query(Projectile) if p.team & Team.ENEMY]
    for entity in doomed:
        if world.is_alive(entity):
            world.destroy_entity(entity)


def _show(world: World, sandbox: Sandbox, player: Entity):
    """(Re)builds the panel from scratch."""
    for entity, _ in list(world.query(SandboxUI)):
        world.destroy_entity(entity)

    rows: list[list[tuple]] = []
    """Each row: (width or None for the rest, components...) per element."""

    hint = "show" if sandbox.collapsed else "hide"
    rows.append([(None, UIButton(COLLAPSE_ACTION), UILabel(f"SANDBOX  [{hint}]", 18))])

    if not sandbox.collapsed:
        rows.append([(None, UILabel("Spawn", 16, MUTED))])
        for name in ENEMIES:
            rows.append(
                [(None, UIButton(SPAWN_ACTION.format(name)), UILabel(name, 18))]
            )

        count = SPAWN_COUNTS[sandbox.count_index]
        rows.append([(None, UIButton(COUNT_ACTION), UILabel(f"Amount: x{count}", 18))])
        rows.append(
            [
                (
                    SMALL_BUTTON_WIDTH,
                    UIButton(LEVEL_DOWN_ACTION, enabled=sandbox.level > 1),
                    UILabel("-", 22, WHITE if sandbox.level > 1 else MUTED),
                ),
                (None, UILabel(f"Level {to_roman(sandbox.level)}", 18)),
                (
                    SMALL_BUTTON_WIDTH,
                    UIButton(LEVEL_UP_ACTION, enabled=sandbox.level < MAX_LEVEL),
                    UILabel("+", 22, WHITE if sandbox.level < MAX_LEVEL else MUTED),
                ),
            ]
        )

        rows.append([(None, UILabel("Options", 16, MUTED))])
        god = world.has_component(player, Invulnerable)
        rows.append(
            [
                (
                    None,
                    UIButton(GOD_ACTION),
                    UILabel(
                        f"God Mode: {'ON' if god else 'OFF'}",
                        18,
                        ON_COLOR if god else WHITE,
                    ),
                )
            ]
        )
        rows.append(
            [(None, UIButton(CASH_ACTION), UILabel(f"+${CASH_AMOUNT}", 18, CASH_COLOR))]
        )
        rows.append(
            [(None, UIButton(CLEAR_ACTION), UILabel("Clear Enemies", 18, DANGER_COLOR))]
        )
        rows.append([(None, UIButton(MENU_ACTION), UILabel("Main Menu", 18))])

    inner = PANEL_WIDTH - 2 * PADDING
    height = 2 * PADDING + len(rows) * ROW_HEIGHT + (len(rows) - 1) * ROW_GAP
    _element(
        world, UIPanel(PANEL_COLOR, PANEL_ALPHA), x=0, y=0, w=PANEL_WIDTH, h=height
    )

    for index, row in enumerate(rows):
        y = PADDING + index * (ROW_HEIGHT + ROW_GAP)
        fixed = sum(w for w, *_ in row if w is not None)
        flexible = sum(1 for w, *_ in row if w is None)
        gaps = (len(row) - 1) * ROW_GAP
        rest = (inner - fixed - gaps) / max(1, flexible)
        # Laid out right to left, since the panel hangs off the right edge.
        x = PADDING
        for width, *components in reversed(row):
            w = rest if width is None else width
            _element(world, *components, x=x, y=y, w=w, h=ROW_HEIGHT, layer=1)
            x += w + ROW_GAP


def _element(
    world: World, *components, x: float, y: float, w: float, h: float, layer=0
):
    """Positioned from the screen's top right corner: `x` px left of the panel's
    right edge, `y` px below its top."""
    return world.create_entity(
        UIRect(
            anchor=(1, 0),
            pivot=(1, 0),
            offset=(-PANEL_MARGIN - x, PANEL_MARGIN + y),
            size=(round(w), round(h)),
            layer=PANEL_LAYER + layer,
        ),
        SandboxUI(),
        *components,
    )
