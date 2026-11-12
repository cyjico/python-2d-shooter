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

    def is_circle_visible(self, center: pygame.Vector2, radius: float) -> bool:
        sx = center.x - self.position.x
        sy = center.y - self.position.y
        w, h = self.viewport_size
        return (
            sx + radius >= 0
            and sx - radius <= w
            and sy + radius >= 0
            and sy - radius <= h
        )
