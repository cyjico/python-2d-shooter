import math

import pygame

from game.components.ai import AI
from game.components.ai.follow_target import FollowTargetAI
from game.components.transform import Transform
from game.core_ecs.world import World
from game.game import Mover
from game.systems.ai.util import correct_want_dir
from game.util.geometry import angle_of, rot_to_vec2


def follow_target_ai_system(world: World, dt: float):
    for ent, (follower,) in world.query(FollowTargetAI):
        ai = world.get_component(ent, AI)
        mover = world.get_component(ent, Mover)
        transform = world.get_component(ent, Transform)

        targ_transform = world.get_component(follower.target, Transform)

        final_want_dir = correct_want_dir(
            world,
            ai,
            transform.position,
            (targ_transform.position - transform.position).normalize(),
        )

        mover.face_angle = angle_of(final_want_dir)
        mover.move_dir = final_want_dir
