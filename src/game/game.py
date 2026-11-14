import math
import random
from enum import Enum, auto
from pathlib import Path

import pygame

from game.components.camera_target import CameraTarget
from game.components.convex_collider import ConvexCollider
from game.components.dash import Dash, DashIntent
from game.components.faction import Team
from game.components.health import Health
from game.components.hud import (
    BuffStatusLabel,
    InteractPromptLabel,
    InventorySlotUI,
    MoneyLabel,
    WaveBannerLabel,
    WaveBannerSubLabel,
    WaveLabel,
    WaveRemainingLabel,
    WeaponStatusLabel,
)
from game.components.loadout import Gun, Loadout
from game.components.mover import Mover
from game.components.player import Player
from game.components.relocatable import Relocatable
from game.components.rigid_body import RigidBody, inertia_of_box
from game.components.shape import Shape
from game.components.spawner import Spawner
from game.components.stamina import Stamina
from game.components.transform import Transform
from game.components.ui import UILabel, UIPanel, UIRect
from game.components.wallet import Wallet
from game.components.weapon_intent import WeaponIntent
from game.constants.guns import PISTOL
from game.constants.mystery_box import MIN_MOVE_DISTANCE
from game.constants.spawning import (
    CRATE_INTERVAL,
)
from game.core.settings import DEFAULT_SETTINGS
from game.core_ecs.world import World
from game.events.ui import ButtonClickedEvent
from game.intro import Intro
from game.map_loader import TILE_SIZE, MapSpawns, load_map
from game.prefabs.crate import spawn_crate
from game.prefabs.mystery_box import spawn_mystery_box
from game.resources.asset_store import AssetStore
from game.resources.camera import Camera
from game.resources.enemy_director import EnemyDirector
from game.resources.event_bus import EventBus
from game.resources.input_state import InputState
from game.resources.mystery_box_session import MysteryBoxSession
from game.resources.run_stats import RunStats
from game.resources.ui_state import UIState
from game.screens import PLAY_ACTION, build_game_over, build_main_menu
from game.systems.ai.charger import charger_ai_collision_system, charger_ai_system
from game.systems.ai.follow_target import follow_target_ai_system
from game.systems.ai.hover_around_target import hover_around_target_ai_system
from game.systems.ai.random_dash import random_dash_ai_system
from game.systems.ai.shooter import shooter_ai_system
from game.systems.bounty import bounty_system
from game.systems.breakable import break_cleanup_system, breakable_system
from game.systems.buff import buff_drop_system, buff_tick_system
from game.systems.buff_hud import buff_hud_system
from game.systems.camera_follow import camera_follow_system
from game.systems.collision import collision_system
from game.systems.contact_damage import contact_damage_system
from game.systems.cursor import cursor_render_system
from game.systems.damage_numbers import (
    damage_number_render_system,
    damage_number_spawn_system,
)
from game.systems.dash import dash_impact_system, dash_system
from game.systems.death_sequence import (
    DeathSequence,
    death_sequence_system,
    run_stats_system,
    start_death_sequence,
)
from game.systems.drift import drift_system
from game.systems.enemy_spawn import enemy_spawn_system
from game.systems.health import death_cleanup_system, health_system
from game.systems.health_bars import health_bar_render_system
from game.systems.input import input_system
from game.systems.inventory_hud import inventory_hud_system
from game.systems.last_enemy_cue import last_enemy_cue_render_system
from game.systems.lifetime import lifetime_system
from game.systems.mover import mover_system
from game.systems.mystery_box import (
    close_session,
    mystery_box_price_render_system,
    mystery_box_system,
)
from game.systems.offscreen_despawn import offscreen_despawn_system
from game.systems.physics import physics_system
from game.systems.player_control import player_control_system
from game.systems.player_dash_input import player_dash_input_system
from game.systems.player_weapon_input import player_weapon_input_system
from game.systems.projectile import projectile_system
from game.systems.rendering import render_system
from game.systems.spawner import spawner_system
from game.systems.split_on_death import split_on_death_system
from game.systems.stamina import stamina_system
from game.systems.stamina_dots import stamina_dots_render_system
from game.systems.ui.interaction import ui_interaction_system
from game.systems.ui.layout import ui_layout_system
from game.systems.ui.render import ui_render_system
from game.systems.vfx import (
    gib_spawn_system,
    particle_system,
    spark_render_system,
    spark_spawn_system,
)
from game.systems.wave_hud import wave_hud_system
from game.systems.wave_scaling import wave_scaling_system
from game.systems.weapon import weapon_system
from game.systems.weapon_status_hud import weapon_status_hud_system
from game.util.factions import Faction


class GameState(Enum):
    INTRO = auto()
    """ASRP's startup intro, every time the game opens."""
    MENU = auto()
    """Main menu: only a Play button."""
    PLAYING = auto()
    DYING = auto()
    """The player died: the world is frozen while the player shakes and shatters."""
    GAME_OVER = auto()
    """Run stats and a Play button over the frozen world."""


class Game:
    def __init__(self, play_intro: bool = True):
        """`play_intro`: show ASRP's intro before the main menu."""
        # The intro's synthesized sound is built for this format.
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()

        self.settings = DEFAULT_SETTINGS

        # --- Window ---
        self.screen = pygame.display.set_mode(self.settings.window_size)
        pygame.display.set_caption(self.settings.window_title)

        # --- Timing ---
        self.clock = pygame.time.Clock()

        # --- Main menu ---
        self.world = self._new_world()
        build_main_menu(self.world)
        ui_layout_system(self.world)
        self.player = None
        self.mystery_box = None

        self.intro: Intro | None = None
        if play_intro:
            self.intro = Intro(self.settings.window_size)
            self._set_state(GameState.INTRO)
        else:
            self._set_state(GameState.MENU)

        # --- Game state ---
        self.running = True
        self.events: list[pygame.event.Event] = []

    def _new_world(self):
        """An empty world with the resources every screen needs."""
        world = World()
        world.add_resource(Camera(self.settings.window_size))
        world.add_resource(InputState())
        world.add_resource(EventBus())
        world.add_resource(AssetStore(Path(__file__).parent / "assets"))
        world.add_resource(UIState())
        return world

    def _set_state(self, state: GameState):
        self.state = state
        # The crosshair cursor replaces the system one during gameplay; the
        # intro shows no cursor at all.
        pygame.mouse.set_visible(state not in (GameState.PLAYING, GameState.INTRO))

    def start_run(self):
        """Starts a new run in a fresh world, replacing whatever was there."""
        self.world = self._new_world()
        self.world.add_resource(MysteryBoxSession())
        self.world.add_resource(RunStats())

        # --- Entities ---
        player_verts = (
            pygame.Vector2(-15, -15),
            pygame.Vector2(10, -15),
            pygame.Vector2(22, 0),
            pygame.Vector2(10, 15),
            pygame.Vector2(-15, 15),
        )

        self.player = self.world.create_entity(
            Player(),
            Faction(Team.PLAYER),
            Health(maximum=100),
            Loadout(slots=[Gun.full(PISTOL)]),
            WeaponIntent(),
            Wallet(balance=800),
            Mover(),
            Dash(),
            DashIntent(),
            Stamina(segments=2),
            RigidBody(inertia=inertia_of_box(1.0, 30, 30)),
            Transform(rotation=math.radians(45), scale=(1, 1)),
            Shape(
                vertices=player_verts,
                color=(255, 0, 120),
            ),
            ConvexCollider(
                vertices=player_verts,
            ),
            CameraTarget(),
        )

        # --- Map ---
        spawns = load_map(
            self.world,
            Path(__file__).parent.parent / "assets" / "maps" / "level1.txt",
            self.player,
        )

        self.world.get_component(self.player, Transform).position = spawns.player
        self.world.get_resource(Camera).center_on(spawns.player)
        self._setup_map_objects(spawns)

        # --- UI ---
        self.world.create_entity(
            UIRect(anchor=(1, 1), pivot=(1, 1), offset=(-16, -16), size=(160, 36)),
            UILabel(""),
            WeaponStatusLabel(),
        )
        # Wave, stacked above the ammo.
        self.world.create_entity(
            UIRect(anchor=(1, 1), pivot=(1, 1), offset=(-16, -54), size=(160, 22)),
            UILabel("", 18),
            WaveRemainingLabel(),
        )
        self.world.create_entity(
            UIRect(anchor=(1, 1), pivot=(1, 1), offset=(-16, -78), size=(160, 34)),
            UILabel("", 30),
            WaveLabel(),
        )
        # Next-wave banner (during breaks) and last-enemy callout.
        self.world.create_entity(
            UIRect(anchor=(0.5, 0.3), pivot=(0.5, 0.5), size=(500, 64)),
            UILabel("", 56),
            WaveBannerLabel(),
        )
        self.world.create_entity(
            UIRect(anchor=(0.5, 0.3), pivot=(0.5, 0.5), offset=(0, 46), size=(500, 28)),
            UILabel("", 24),
            WaveBannerSubLabel(),
        )

        # Inventory slots, bottom left, stacked: 1 = primary on top.
        slot_w, slot_h, slot_gap = 190, 36, 6
        slot_count = 2
        for index in range(slot_count):
            y = -16 - (slot_count - 1 - index) * (slot_h + slot_gap)
            self.world.create_entity(
                UIRect(
                    anchor=(0, 1), pivot=(0, 1), offset=(16, y), size=(slot_w, slot_h)
                ),
                UIPanel(),
                UILabel("", 18),
                InventorySlotUI(index),
            )

        self.world.create_entity(
            UIRect(anchor=(0, 0), pivot=(0, 0), offset=(16, 12), size=(120, 32)),
            UILabel("", 28, (230, 180, 50)),
            MoneyLabel(),
        )
        self.world.create_entity(
            UIRect(anchor=(0.5, 1), pivot=(0.5, 1), offset=(0, -20), size=(500, 24)),
            UILabel(""),
            InteractPromptLabel(),
        )

        self.world.create_entity(
            UIRect(anchor=(0.5, 0), pivot=(0.5, 0), offset=(0, 12), size=(500, 24)),
            UILabel("", 18),
            BuffStatusLabel(),
        )

        ui_layout_system(self.world)
        self._set_state(GameState.PLAYING)

    def handle_events(self):
        self.events = pygame.event.get()
        for event in self.events:
            if event.type == pygame.QUIT:
                self.running = False
                continue

    def update(self, dt: float):
        self.world.get_resource(EventBus).clear()

        match self.state:
            case GameState.INTRO:
                assert self.intro is not None
                if self.intro.update(dt, self.events):
                    self.intro = None
                    self._set_state(GameState.MENU)
            case GameState.MENU:
                self._screen_update()
            case GameState.PLAYING:
                self._play_update(dt)
            case GameState.DYING:
                self._dying_update(dt)
            case GameState.GAME_OVER:
                # Death shards may still be settling.
                particle_system(self.world, dt, frozen=True)
                self._screen_update()

    def _screen_update(self):
        """Main menu and game over: only the UI runs."""
        input_system(self.world, self.events)
        ui_layout_system(self.world)
        ui_interaction_system(self.world)

        clicks = self.world.get_resource(EventBus).read(ButtonClickedEvent)
        if any(click.action == PLAY_ACTION for click in clicks):
            self.start_run()

    def _play_update(self, dt: float):
        self._input_phase()
        self._upkeep_phase(dt)
        self._intent_phase(dt)
        self._action_phase(dt)
        self._physics_phase(dt)
        self._hit_phase(dt)
        self._damage_phase()
        self._cleanup_phase(dt)
        self._hud_phase()

        self.world.get_resource(RunStats).time_survived += dt
        if self._player_is_dead():
            self._begin_death()

    def _dying_update(self, dt: float):
        """Everything is frozen except the player's shake and shards."""
        input_system(self.world, self.events)
        death_sequence_system(self.world, dt)
        particle_system(self.world, dt, frozen=True)

        if self.world.get_resource(DeathSequence).finished:
            self._show_game_over()

    def _player_is_dead(self):
        assert self.player is not None
        health = self.world.try_get_component(self.player, Health)
        return health is not None and health.current <= 0

    def _begin_death(self):
        assert self.player is not None
        # Closes an open mystery box menu, which also hands input back.
        close_session(self.world)
        start_death_sequence(self.world, self.player)
        self._set_state(GameState.DYING)

    def _show_game_over(self):
        assert self.player is not None
        wallet = self.world.get_component(self.player, Wallet)
        build_game_over(
            self.world, self.world.get_resource(RunStats), wallet.total_earned
        )
        ui_layout_system(self.world)
        self._set_state(GameState.GAME_OVER)

    def _input_phase(self):
        """Raw input, then UI layout and hit-testing."""
        input_system(self.world, self.events)
        ui_layout_system(self.world)
        ui_interaction_system(self.world)

    def _upkeep_phase(self, dt: float):
        """Timers and spawning."""
        buff_tick_system(self.world, dt)
        # Reads buffs, so after the tick.
        stamina_system(self.world, dt)
        spawner_system(self.world, dt)
        enemy_spawn_system(self.world, dt)
        # After spawning, so new enemies are scaled before they ever act.
        wave_scaling_system(self.world)

    def _intent_phase(self, dt: float):
        """Players and AI decide what they want to do this frame."""
        # Aiming converts the mouse through the camera.
        camera_follow_system(self.world, dt)

        # Before the player's intents: opening the menu blocks gameplay input
        # on this same frame.
        mystery_box_system(self.world, dt)
        player_control_system(self.world, dt)
        player_weapon_input_system(self.world)
        player_dash_input_system(self.world)

        # The charger swaps the hover behavior in and out, so it goes before
        # the generic movement AIs.
        charger_ai_system(self.world, dt)
        follow_target_ai_system(self.world, dt)
        hover_around_target_ai_system(self.world, dt)
        random_dash_ai_system(self.world, dt)
        # Overrides the facing the movement AIs just set, to aim.
        shooter_ai_system(self.world, dt)

    def _action_phase(self, dt: float):
        """Intents become velocity changes and shots."""
        mover_system(self.world, dt)
        # An active dash overrides mover_system.
        dash_system(self.world, dt)
        weapon_system(self.world, dt)

    def _physics_phase(self, dt: float):
        physics_system(self.world, dt)
        collision_system(self.world)
        # Effects that skip physics.
        drift_system(self.world, dt)

    def _hit_phase(self, dt: float):
        """Collision results become DamageEvents."""
        dash_impact_system(self.world)
        charger_ai_collision_system(self.world)
        contact_damage_system(self.world, dt)
        projectile_system(self.world)
        # Reads the ProjectileHitEvents just emitted.
        spark_spawn_system(self.world)

    def _damage_phase(self):
        """Applies damage and reacts to it. The dead and broken still exist here
        so reward systems can read their components."""
        health_system(self.world)
        damage_number_spawn_system(self.world)
        bounty_system(self.world)
        run_stats_system(self.world)
        # Reads the dead enemy's shape, so before cleanup.
        gib_spawn_system(self.world)
        split_on_death_system(self.world)
        breakable_system(self.world)
        # Reads the BrokenEvents just emitted.
        buff_drop_system(self.world)

    def _cleanup_phase(self, dt: float):
        """Entities leave the world here, after everything above has read them."""
        break_cleanup_system(self.world)
        death_cleanup_system(self.world)
        lifetime_system(self.world, dt)
        particle_system(self.world, dt)
        offscreen_despawn_system(self.world, dt)

    def _hud_phase(self):
        weapon_status_hud_system(self.world)
        inventory_hud_system(self.world)
        buff_hud_system(self.world)
        wave_hud_system(self.world)

        # UI created this frame needs its rect before rendering on the next frame.
        ui_layout_system(self.world)

    def render(self):
        if self.intro is not None:
            self.intro.render(self.screen)
            pygame.display.flip()
            return

        self.screen.fill(self.settings.background_color)

        if self.state is not GameState.MENU:
            render_system(self.world, self.screen)
            spark_render_system(self.world, self.screen)
            mystery_box_price_render_system(self.world, self.screen)
            health_bar_render_system(self.world, self.screen)
            last_enemy_cue_render_system(self.world, self.screen)
            stamina_dots_render_system(self.world, self.screen)
            damage_number_render_system(self.world, self.screen)

        ui_render_system(self.world, self.screen)

        if self.state is GameState.PLAYING:
            cursor_render_system(self.world, self.screen)

        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(self.settings.target_fps) / 1000.0

            dt = min(dt, self.settings.max_frame_time)

            self.handle_events()
            self.update(dt)
            self.render()

        pygame.quit()

    def _setup_map_objects(self, spawns: MapSpawns):
        # Crates: only about half the spots start occupied, so the spawner has
        # free spots to use. One crate fits per spot, so that is also the cap.
        points = spawns.crates
        initial = random.sample(points, (len(points) + 1) // 2)
        crates = [spawn_crate(self.world, pos) for pos in initial]
        self.world.create_entity(
            Spawner(
                points=points,
                spawn=spawn_crate,
                interval=CRATE_INTERVAL,
                max_alive=max(1, len(points)),
                spawned=crates,
            )
        )

        # Mystery box: one box that hops between the map's `M` spots. Maps
        # without any `M` tile get a single box a few tiles from the player.
        box_points = spawns.mystery_boxes or [
            spawns.player + pygame.Vector2(3 * TILE_SIZE, 0)
        ]
        self.mystery_box = spawn_mystery_box(self.world, random.choice(box_points))
        self.world.add_component(
            self.mystery_box,
            Relocatable(points=box_points, min_distance=MIN_MOVE_DISTANCE),
        )

        # Waves: enemies appear just off screen, more and stronger every wave.
        self.world.add_resource(EnemyDirector())


def main():
    game = Game()
    game.run()
