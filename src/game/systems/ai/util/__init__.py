import pygame

from game.components.ai import AI
from game.core_ecs.world import World
from game.util.raycast import raycast_static_bundle


def correct_want_dir(
    world: World,
    ai: AI,
    pos: pygame.Vector2,
    want_dir: pygame.Vector2,
):
    """Corrects the wanted direction where it won't be blocked by static colliders.

    Args:
        world (World): World of the AI.
        ai (AI): AI that wants to
        pos (pygame.Vector2): Position of the AI.
        want_dir (pygame.Vector2): Unit direction the AI wants to go.

    Returns:
        pygame.Vector2: Corrected wanted direction to actually move to.
    """
    if want_dir.length_squared() == 0:
        return pygame.Vector2()

    if not raycast_static_bundle(
        world, pos, want_dir, ai.probe_distance, ai.body_radius
    ):
        return want_dir

    side = ai.avoid_side
    for _ in range(2):
        sideways = pygame.Vector2(-want_dir.y, want_dir.x) * side
        if not raycast_static_bundle(
            world, pos, sideways, ai.probe_distance, ai.body_radius
        ):
            ai.avoid_side = side
            return sideways

        side = -side

    return pygame.Vector2()
