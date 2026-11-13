from game.components.ai import AI
from game.components.ai.follow_target import FollowTargetAI
from game.components.mover import Mover
from game.components.transform import Transform
from game.core_ecs.world import World
from game.systems.ai.util import correct_want_dir
from game.util.geometry import angle_of


def follow_target_ai_system(world: World, dt: float):
    for ent, (follower,) in world.query(FollowTargetAI):
        ai = world.get_component(ent, AI)
        mover = world.get_component(ent, Mover)
        transform = world.get_component(ent, Transform)

        if ai.target is None:
            continue

        toward = world.get_component(ai.target, Transform).position - transform.position
        if toward.length_squared() == 0:
            mover.move_dir.update()
            continue

        final_want_dir = correct_want_dir(
            world, ai, transform.position, toward.normalize()
        )

        if final_want_dir.length_squared() > 0:
            mover.face_angle = angle_of(final_want_dir)
        mover.move_dir = final_want_dir
