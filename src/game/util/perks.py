from game.components.buffs import BuffSpec, Flag, Stat
from game.components.dash import Dash
from game.components.health import Health
from game.components.perks import Perks, PerkSpec
from game.components.wallet import Wallet
from game.constants.perks import BERSERK_MAX_BONUS, UNDYING_IMMUNITY
from game.core_ecs.entity import Entity
from game.core_ecs.world import World
from game.util.buffs import grant_buff, has_flag

UNDYING_BUFF = BuffSpec(
    id="undying",
    name="Undying",
    duration=UNDYING_IMMUNITY,
    flags=frozenset({Flag.IMMUNE}),
)


def heal(world: World, entity: Entity, amount: float):
    """Heals up to max health. The dead stay dead."""
    health = world.try_get_component(entity, Health)
    if health is None or health.current <= 0 or amount <= 0:
        return
    health.current = min(health.maximum, health.current + amount)


def apply_perk(world: World, entity: Entity, spec: PerkSpec):
    """Gives `entity` the perk, including its one-time effects."""
    perks = world.try_get_component(entity, Perks)
    if perks is None:
        perks = Perks()
        world.add_component(entity, perks)
    perks.add(spec)

    health = world.try_get_component(entity, Health)
    if health is not None:
        extra = spec.bonuses.get(Stat.MAX_HEALTH, 0.0)
        health.maximum += extra
        health.current += extra
        heal(world, entity, health.maximum * spec.heal_fraction)

    wallet = world.try_get_component(entity, Wallet)
    if wallet is not None and spec.cash > 0:
        wallet.earn(spec.cash)


def berserk_multiplier(world: World, entity: Entity):
    """Damage multiplier from Berserker: 1 at full health, up to
    1 + BERSERK_MAX_BONUS near death."""
    if not has_flag(world, entity, Flag.BERSERK):
        return 1.0
    health = world.try_get_component(entity, Health)
    if health is None or health.maximum <= 0:
        return 1.0
    missing = 1.0 - max(0.0, health.current) / health.maximum
    return 1.0 + BERSERK_MAX_BONUS * min(1.0, missing)


def is_dash_immune(world: World, entity: Entity):
    if not has_flag(world, entity, Flag.DASH_IMMUNE):
        return False
    dash = world.try_get_component(entity, Dash)
    return dash is not None and (dash.active or dash.moving)


def try_undying(world: World, entity: Entity, health: Health):
    """Undying: a killing blow leaves 1 health and a moment of immunity, once
    per wave. Returns whether it saved the entity."""
    perks = world.try_get_component(entity, Perks)
    if perks is None or not perks.undying_ready or not perks.has(Flag.UNDYING):
        return False
    perks.undying_ready = False
    health.current = 1.0
    grant_buff(world, entity, UNDYING_BUFF)
    return True
