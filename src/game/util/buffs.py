from game.components.buffs import ActiveBuffs, BuffSpec, Flag, Stat
from game.components.perks import Perks
from game.core_ecs.entity import Entity
from game.core_ecs.world import World


def stat_multiplier(world: World, entity: Entity, stat: Stat):
    """Timed buffs and permanent perks, multiplied together."""
    result = 1.0
    buffs = world.try_get_component(entity, ActiveBuffs)
    if buffs is not None:
        result *= buffs.multiplier(stat)
    perks = world.try_get_component(entity, Perks)
    if perks is not None:
        result *= perks.multiplier(stat)
    return result


def stat_bonus(world: World, entity: Entity, stat: Stat):
    """Timed buffs and permanent perks, added together."""
    result = 0.0
    buffs = world.try_get_component(entity, ActiveBuffs)
    if buffs is not None:
        result += buffs.bonus(stat)
    perks = world.try_get_component(entity, Perks)
    if perks is not None:
        result += perks.bonus(stat)
    return result


def has_flag(world: World, entity: Entity, flag: Flag):
    buffs = world.try_get_component(entity, ActiveBuffs)
    if buffs is not None and buffs.has(flag):
        return True
    perks = world.try_get_component(entity, Perks)
    return perks is not None and perks.has(flag)


def absorb_damage(world: World, entity: Entity, amount: float):
    """Damage left after the entity's shield took its share."""
    buffs = world.try_get_component(entity, ActiveBuffs)
    return amount if buffs is None else buffs.absorb(amount)


def shield(world: World, entity: Entity):
    """Shield the entity has left."""
    buffs = world.try_get_component(entity, ActiveBuffs)
    return 0.0 if buffs is None else buffs.shield


def grant_buff(world: World, entity: Entity, spec: BuffSpec):
    buffs = world.try_get_component(entity, ActiveBuffs)
    if buffs is None:
        buffs = ActiveBuffs()
        world.add_component(entity, buffs)
    buffs.add(spec)
