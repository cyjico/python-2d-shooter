from game.components.buffs import ActiveBuffs, BuffSpec, Flag, Stat
from game.core_ecs.entity import Entity
from game.core_ecs.world import World


def stat_multiplier(world: World, entity: Entity, stat: Stat):
    buffs = world.try_get_component(entity, ActiveBuffs)
    return 1.0 if buffs is None else buffs.multiplier(stat)


def stat_bonus(world: World, entity: Entity, stat: Stat):
    buffs = world.try_get_component(entity, ActiveBuffs)
    return 0.0 if buffs is None else buffs.bonus(stat)


def has_flag(world: World, entity: Entity, flag: Flag):
    buffs = world.try_get_component(entity, ActiveBuffs)
    return buffs is not None and buffs.has(flag)


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
