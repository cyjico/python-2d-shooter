import math

import pygame

from game.components.ai import AI
from game.components.ai.hover_around_target import HoverAroundTargetAI
from game.components.mover import Mover
from game.components.transform import Transform
from game.core_ecs.world import World
from game.systems.ai.util import correct_want_dir
from game.util.geometry import angle_of, rot_to_vec2


def hover_around_target_ai_system(world: World, dt: float):
    for ent, (hoverer,) in world.query(HoverAroundTargetAI):
        ai = world.get_component(ent, AI)
        mover = world.get_component(ent, Mover)
        transform = world.get_component(ent, Transform)

        if ai.target is None:
            continue

        targ_transform = world.get_component(ai.target, Transform)

        toward = targ_transform.position - transform.position

        error_sqr = toward.magnitude_squared() - hoverer.preferred_dist_sqr
        hoverer.strafing = False
        if error_sqr > hoverer.dist_tolerance_sqr:
            want_dir = toward
        elif error_sqr < -hoverer.dist_tolerance_sqr:
            want_dir = -toward
        else:
            hoverer.strafing = True
            want_dir = pygame.Vector2(-toward.y, toward.x) * hoverer.strafe_side
        want_dir = want_dir.normalize()

        final_want_dir = correct_want_dir(
            world,
            ai,
            transform.position,
            want_dir,
        )

        # If strafing into a wall, basically.
        if hoverer.strafing and final_want_dir.dot(want_dir) < 0.5:
            hoverer.strafe_side = -hoverer.strafe_side

        mover.face_angle = angle_of(final_want_dir)
        mover.move_dir = final_want_dir
