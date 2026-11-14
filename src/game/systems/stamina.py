from game.components.stamina import Stamina
from game.core_ecs.world import World
from game.util.buffs import Stat, stat_bonus, stat_multiplier


def stamina_system(world: World, dt: float):
    """Applies buffs to Stamina, then regenerates it. Run after buff_tick_system
    and before anything that spends stamina."""
    for entity, (stamina,) in world.query(Stamina):
        bonus_segments = round(stat_bonus(world, entity, Stat.STAMINA_SEGMENTS))
        regen_multiplier = stat_multiplier(world, entity, Stat.STAMINA_REGEN)
        stamina.regen(bonus_segments, regen_multiplier, dt)
