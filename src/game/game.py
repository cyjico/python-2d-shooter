import math

import pygame

from game.components.ui import UIButton, UILabel, UIRect
from game.core.settings import DEFAULT_SETTINGS
from game.core_ecs.world import World
from game.components.transform import Transform
from game.components.shape import Shape
from game.components.convex_collider import ConvexCollider
from game.components.player import Player
from game.components.rigid_body import RigidBody, inertia_of_box
from game.map_loader import load_map
from game.events.ui import ButtonClicked
from game.resources.ui_state import UIState
from game.resources.asset_store import AssetStore, Path
from game.resources.camera import Camera
from game.resources.input_state import InputState
from game.resources.event_bus import EventBus
from game.systems.rendering import render_system
from game.systems.input import input_system
from game.systems.physics import physics_system
from game.systems.player_control import player_control_system
from game.systems.collision import collision_system
from game.systems.ui.interaction import ui_interaction_system
from game.systems.ui.layout import ui_layout_system
from game.systems.ui.render import ui_render_system
from game.components.camera_target import CameraTarget
from game.systems.camera_follow import camera_follow_system


class Game:
    def __init__(self):
        pygame.init()

        self.settings = DEFAULT_SETTINGS

        # Window
        self.screen = pygame.display.set_mode(self.settings.window_size)

        pygame.display.set_caption(self.settings.window_title)

        # Timing
        self.clock = pygame.time.Clock()

        # ECS
        self.world = World()

        # Resources
        self.world.add_resource(Camera(self.settings.window_size))
        self.world.add_resource(InputState())
        self.world.add_resource(EventBus())
        self.world.add_resource(AssetStore(Path(__file__).parent / "assets"))
        self.world.add_resource(UIState())

        # Map
        player_spawn = load_map(
            self.world, Path(__file__).parent / "assets" / "maps" / "level1.txt"
        )

        self.player = self.world.create_entity(
            Player(),
            CameraTarget(),
            RigidBody(inertia=inertia_of_box(1.0, 30, 30)),
            Transform(
                position=player_spawn, rotation=math.radians(45), scale=(1, 1)
            ),
            Shape(
                vertices=(
                    pygame.Vector2(-15, -15),
                    pygame.Vector2(10, -15),
                    pygame.Vector2(22, 0),
                    pygame.Vector2(10, 15),
                    pygame.Vector2(-15, 15),
                ),
                color=(255, 0, 120),
            ),
            ConvexCollider(
                vertices=(
                    pygame.Vector2(-15, -15),
                    pygame.Vector2(15, -15),
                    pygame.Vector2(22, 0),
                    pygame.Vector2(15, 15),
                    pygame.Vector2(-15, 15),
                ),
            ),
        )

        self.world.get_resource(Camera).center_on(player_spawn)

        # Game state
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
        ui_layout_system(self.world)
        ui_interaction_system(self.world)

        camera_follow_system(self.world, dt)
        player_control_system(self.world, dt)

        physics_system(self.world, dt)
        collision_system(self.world)

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


def main():
    game = Game()
    game.run()
