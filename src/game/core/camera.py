import pygame


class Camera:
    def __init__(self, viewport_size: tuple[int, int]):
        self.viewport_size = pygame.Vector2(viewport_size)

        self.position = pygame.Vector2(0, 0)

    def world_to_screen(self, position: pygame.Vector2) -> pygame.Vector2:
        return pygame.Vector2(position) - self.position

    def screen_to_world(self, position: pygame.Vector2) -> pygame.Vector2:
        return pygame.Vector2(position) + self.position

    def center_on(self, target: pygame.Vector2):
        self.position = pygame.Vector2(target) - self.viewport_size / 2
