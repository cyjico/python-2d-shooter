import pygame

from .core.settings import DEFAULT_SETTINGS
from .core.camera import Camera
from .core_ecs.world import World
from .components.transform import Transform
from .components.convex_shape import ConvexShape
from .systems.rendering import render_system


class Game:
    def __init__(self):
        pygame.init()

        self.settings = DEFAULT_SETTINGS

        # Window
        self.screen = pygame.display.set_mode(self.settings.window_size)

        pygame.display.set_caption(self.settings.window_title)

        # Timing
        self.clock = pygame.time.Clock()

        # Camera
        self.camera = Camera(self.settings.window_size)

        # ECS
        self.world = World()

        # TODO: Remove test entities when done
        self.world.create_entity(
            Transform(position=(50, 50), rotation=45, scale=(1, 2)),
            ConvexShape(
                vertices=(
                    (-15, -15),
                    (15, -15),
                    (15, 15),
                    (-15, 15),
                ),
                color=(255, 0, 120),
            ),
        )

        # Game state
        self.running = True

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def update(self, dt: float):
        pass

    def render(self):
        self.screen.fill(self.settings.background_color)

        render_system(self.world, self.screen, self.camera)

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
