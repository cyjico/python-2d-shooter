from game.components.health import Health
from game.components.player import Player
from game.core_ecs.world import World
from game.events.combat import DamageEvent, EntityDiedEvent
from game.resources.event_bus import EventBus


def health_system(world: World):
    """Run after anything that emits DamageEvent."""
    events = world.get_resource(EventBus)

    for damage in events.read(DamageEvent):
        health = world.try_get_component(damage.target, Health)
        if health is None:
            continue

        was_alive = health.current > 0
        health.current -= damage.amount

        if was_alive and health.current <= 0:
            events.emit(EntityDiedEvent(damage.target, damage.source))

            # TODO: player death should be game-over.
            if not world.has_component(damage.target, Player):
                world.destroy_entity(damage.target)
