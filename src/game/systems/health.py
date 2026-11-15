from game.components.buffs import Flag, Stat
from game.components.health import Health
from game.components.invulnerable import Invulnerable
from game.components.player import Player
from game.constants.rewards import HIT_CASH, KILL_HEAL
from game.core_ecs.entity import Entity
from game.core_ecs.world import World
from game.events.combat import DamageEvent, DamageTakenEvent, EntityDiedEvent
from game.resources.event_bus import EventBus
from game.util.buffs import absorb_damage, has_flag, stat_bonus, stat_multiplier
from game.util.factions import is_hostile
from game.util.money import earn_money
from game.util.ownership import owner_of
from game.util.perks import heal, is_dash_immune, try_undying


def health_system(world: World):
    """Applies DamageEvents to Health, emitting DamageTakenEvent and EntityDiedEvent."""
    events = world.get_resource(EventBus)

    for damage in events.read(DamageEvent):
        health = world.try_get_component(damage.target, Health)
        if health is None:
            continue

        if (
            world.has_component(damage.target, Invulnerable)
            or has_flag(world, damage.target, Flag.IMMUNE)
            or is_dash_immune(world, damage.target)
        ):
            continue

        amount = damage.amount * stat_multiplier(
            world, damage.target, Stat.DAMAGE_TAKEN
        )
        events.emit(DamageTakenEvent(damage.target, amount, damage.critical))

        # Shield soaks first; only the overflow reaches real health.
        amount = absorb_damage(world, damage.target, amount)
        if amount <= 0:
            continue

        was_alive = health.current > 0
        dealt = min(amount, max(0.0, health.current))
        health.current -= amount

        died = was_alive and health.current <= 0
        if died and try_undying(world, damage.target, health):
            died = False
        _reward_dealer(world, damage.source, damage.target, dealt, died)

        if died:
            events.emit(EntityDiedEvent(damage.target, damage.source))


def _reward_dealer(
    world: World, source: Entity | None, target: Entity, dealt: float, killed: bool
):
    """Lifesteal for anyone; the player also earns money per hit and health
    per kill. Drones' hits count as their owner's."""
    dealer = owner_of(world, source)
    if dealer is None or dealt <= 0 or not is_hostile(world, dealer, target):
        return
    heal(world, dealer, dealt * stat_bonus(world, dealer, Stat.LIFESTEAL))

    if world.has_component(dealer, Player):
        earn_money(world, dealer, HIT_CASH)
        if killed:
            heal(world, dealer, KILL_HEAL)


def death_cleanup_system(world: World):
    """Destroys what died."""
    for died in world.get_resource(EventBus).read(EntityDiedEvent):
        # TODO: player death should be game-over.
        if world.is_alive(died.entity) and not world.has_component(died.entity, Player):
            world.destroy_entity(died.entity)
