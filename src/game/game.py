import math
import random
from pathlib import Path

import pygame

from game.components.camera_target import CameraTarget
from game.components.convex_collider import ConvexCollider
from game.components.dash import Dash, DashIntent
from game.components.health import Health
from game.components.hud import (
    BuffStatusLabel,
    InteractPromptLabel,
    InventorySlotUI,
    MoneyLabel,
    StaminaGauge,
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
from game.components.ui import UIGauge, UILabel, UIPanel, UIRect
from game.components.wallet import Wallet
from game.components.weapon_intent import WeaponIntent
from game.constants.guns import PISTOL
from game.constants.mystery_box import MIN_MOVE_DISTANCE
from game.constants.spawning import (
    CRATE_INTERVAL,
)
from game.core.settings import DEFAULT_SETTINGS
from game.core_ecs.world import World
from game.map_loader import TILE_SIZE, MapSpawns, load_map
from game.prefabs.crate import spawn_crate
from game.prefabs.mystery_box import spawn_mystery_box
from game.resources.asset_store import AssetStore
from game.resources.camera import Camera
from game.resources.event_bus import EventBus
from game.resources.input_state import InputState
from game.resources.mystery_box_session import MysteryBoxSession
from game.resources.ui_state import UIState
from game.systems.ai.charger import charger_ai_collision_system, charger_ai_system
from game.systems.ai.follow_target import follow_target_ai_system
from game.systems.ai.hover_around_target import hover_around_target_ai_system
from game.systems.bounty import bounty_system
from game.systems.breakable import break_cleanup_system, breakable_system
from game.systems.buff import buff_drop_system, buff_tick_system
from game.systems.buff_hud import buff_hud_system
from game.systems.camera_follow import camera_follow_system
from game.systems.collision import collision_system
from game.systems.dash import dash_impact_system, dash_system
from game.systems.health import death_cleanup_system, health_system
from game.systems.input import input_system
from game.systems.inventory_hud import inventory_hud_system
from game.systems.mover import mover_system
from game.systems.mystery_box import mystery_box_system
from game.systems.physics import physics_system
from game.systems.player_control import player_control_system
from game.systems.player_dash_input import player_dash_input_system
from game.systems.player_weapon_input import player_weapon_input_system
from game.systems.projectile import projectile_system
from game.systems.rendering import render_system
from game.systems.spawner import spawner_system
from game.systems.stamina import stamina_system
from game.systems.stamina_hud import stamina_hud_system
from game.systems.ui.interaction import ui_interaction_system
from game.systems.ui.layout import ui_layout_system
from game.systems.ui.render import ui_render_system
from game.systems.weapon import weapon_system
from game.systems.weapon_status_hud import weapon_status_hud_system


class Game:
    def __init__(self):
        pygame.init()

        self.settings = DEFAULT_SETTINGS

        # --- Window ---
        self.screen = pygame.display.set_mode(self.settings.window_size)
        pygame.display.set_caption(self.settings.window_title)

        # --- Timing ---
        self.clock = pygame.time.Clock()

        # --- ECS ---
        self.world = World()

        # --- Resources ---
        self.world.add_resource(Camera(self.settings.window_size))
        self.world.add_resource(InputState())
        self.world.add_resource(EventBus())
        self.world.add_resource(AssetStore(Path(__file__).parent / "assets"))
        self.world.add_resource(UIState())
        self.world.add_resource(MysteryBoxSession())

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

        # Inventory slots, bottom center: 1 = primary, 2 = secondary.
        slot_w, slot_gap = 190, 6
        for index in range(2):
            x = (index - 0.5) * (slot_w + slot_gap)
            self.world.create_entity(
                UIRect(
                    anchor=(0.5, 1), pivot=(0.5, 1), offset=(x, -16), size=(slot_w, 36)
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
            UIRect(anchor=(0.5, 1), pivot=(0.5, 1), offset=(0, -60), size=(500, 24)),
            UILabel(""),
            InteractPromptLabel(),
        )

        self.world.create_entity(
            UIRect(anchor=(0.5, 0), pivot=(0.5, 0), offset=(0, 12), size=(500, 24)),
            UILabel("", 18),
            BuffStatusLabel(),
        )

        self.world.create_entity(
            UIRect(anchor=(0, 1), pivot=(0, 1), offset=(16, -16), size=(180, 16)),
            UIGauge(segments=2),
            StaminaGauge(),
        )

        # --- Game state ---
        self.running = True
        self.events: list[pygame.event.Event] = []

    def handle_events(self):
        self.events = pygame.event.get()
        for event in self.events:
            if event.type == pygame.QUIT:
                self.running = False
                continue

    def update(self, dt: float):
        self.world.get_resource(EventBus).clear()

        input_system(self.world, self.events)
        buff_tick_system(self.world, dt)
        stamina_system(self.world, dt)
        ui_layout_system(self.world)
        ui_interaction_system(self.world)

        mystery_box_system(self.world, dt)
        spawner_system(self.world, dt)

        camera_follow_system(self.world, dt)
        player_control_system(self.world, dt)
        player_weapon_input_system(self.world)
        player_dash_input_system(self.world)

        charger_ai_system(self.world, dt)

        # Generic AI Movement
        follow_target_ai_system(self.world, dt)
        hover_around_target_ai_system(self.world, dt)

        mover_system(self.world, dt)
        dash_system(self.world, dt)

        weapon_system(self.world, dt)

        physics_system(self.world, dt)
        collision_system(self.world)

        dash_impact_system(self.world)
        charger_ai_collision_system(self.world)

        projectile_system(self.world, dt)

        health_system(self.world)
        bounty_system(self.world)

        breakable_system(self.world)
        buff_drop_system(self.world)
        break_cleanup_system(self.world)
        death_cleanup_system(self.world)

        weapon_status_hud_system(self.world)
        inventory_hud_system(self.world)
        stamina_hud_system(self.world)
        buff_hud_system(self.world)

        # UI created this frame (e.g. the mystery box menu) needs its rect before rendering.
        ui_layout_system(self.world)

    def render(self):
        self.screen.fill(self.settings.background_color)

        render_system(self.world, self.screen)
        ui_render_system(self.world, self.screen)

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


def main():
    game = Game()
    game.run()
