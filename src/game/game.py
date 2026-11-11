import math

import pygame

from .core.settings import DEFAULT_SETTINGS
from .core_ecs.world import World
from .components.transform import Transform
from .components.convex_shape import ConvexShape
from .components.convex_collider import ConvexCollider
from .components.player import Player
from .components.rigid_body import RigidBody, inertia_of_box, mass_of_box
from .resources.camera import Camera
from .resources.input_state import InputState
from .resources.event_bus import EventBus
from .systems.rendering import render_system
from .systems.input import input_system
from .systems.physics import physics_system
from .systems.player_control import player_control_system
from .systems.collision import collision_system


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

        # TODO: Remove test entities when done.
        self.player = self.world.create_entity(
            Player(),
            RigidBody(inertia=inertia_of_box(1.0, 30, 30)),
            Transform(
                position=pygame.Vector2(0, 0), rotation=math.radians(45), scale=(1, 1)
            ),
            ConvexShape(
                vertices=(
                    pygame.Vector2(-15, -15),
                    pygame.Vector2(15, -15),
                    pygame.Vector2(15, 15),
                    pygame.Vector2(-15, 15),
                ),
                color=(255, 0, 120),
            ),
            ConvexCollider(
                vertices=(
                    pygame.Vector2(-15, -15),
                    pygame.Vector2(15, -15),
                    pygame.Vector2(15, 15),
                    pygame.Vector2(-15, 15),
                ),
            ),
        )

        test_width, test_height = 40, 160
        test_vertices = (
            pygame.Vector2(-test_width / 2, -test_height / 2),
            pygame.Vector2(test_width / 2, -test_height / 2),
            pygame.Vector2(test_width / 2, test_height / 2),
            pygame.Vector2(-test_width / 2, test_height / 2),
        )
        test_mass = mass_of_box(0.2, test_width, test_height)
        self.world.create_entity(
            RigidBody(
                mass=test_mass,
                inertia=inertia_of_box(test_mass, test_width, test_height),
                center_of_mass=pygame.Vector2(0, 0),
            ),
            Transform(position=pygame.Vector2(300, 100)),
            ConvexShape(
                vertices=test_vertices,
                color=(200, 200, 200),
            ),
            ConvexCollider(
                vertices=test_vertices,
                bounciness=0.5,
            ),
        )

        # Game state
        self.running = True

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                continue

    def update(self, dt: float):
        self.world.get_resource(EventBus).clear()

        input_system(self.world)
        player_control_system(self.world, dt)
        physics_system(self.world, dt)
        collision_system(self.world)

        # Add consumers of collision events after here.

    def render(self):
        self.screen.fill(self.settings.background_color)

        render_system(self.world, self.screen)

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
