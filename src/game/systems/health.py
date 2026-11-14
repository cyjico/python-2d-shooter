from game.components.buffs import Flag
from game.components.health import Health
from game.components.player import Player
from game.core_ecs.world import World
from game.events.combat import DamageEvent, DamageTakenEvent, EntityDiedEvent
from game.resources.event_bus import EventBus
from game.util.buffs import absorb_damage, has_flag


def health_system(world: World):
    """Run after anything that emits DamageEvent."""
    events = world.get_resource(EventBus)

    for damage in events.read(DamageEvent):
        health = world.try_get_component(damage.target, Health)
        if health is None:
            continue

        if has_flag(world, damage.target, Flag.IMMUNE):
            continue

        events.emit(DamageTakenEvent(damage.target, damage.amount, damage.critical))

        # Shield soaks first; only the overflow reaches real health.
        amount = absorb_damage(world, damage.target, damage.amount)
        if amount <= 0:
            continue

        was_alive = health.current > 0
        health.current -= amount

        if was_alive and health.current <= 0:
            events.emit(EntityDiedEvent(damage.target, damage.source))


def death_cleanup_system(world: World):
    """Destroys what died. Run last, so reward systems can still read its components."""
    for died in world.get_resource(EventBus).read(EntityDiedEvent):
        # TODO: player death should be game-over.
        if world.is_alive(died.entity) and not world.has_component(died.entity, Player):
            world.destroy_entity(died.entity)
