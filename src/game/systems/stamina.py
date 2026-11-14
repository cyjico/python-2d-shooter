from game.components.stamina import Stamina
from game.core_ecs.world import World
from game.util.buffs import Stat, stat_bonus, stat_multiplier


def stamina_system(world: World, dt: float):
    """Applies buffs to Stamina, then regenerates it."""
    for entity, (stamina,) in world.query(Stamina):
        stamina.bonus_segments = round(stat_bonus(world, entity, Stat.STAMINA_SEGMENTS))
        stamina.regen(stat_multiplier(world, entity, Stat.STAMINA_REGEN), dt)
