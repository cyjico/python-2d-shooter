from game.components.breakable import Breakable
from game.core_ecs.world import World
from game.events.combat import BrokenEvent, DamageEvent
from game.resources.event_bus import EventBus


def breakable_system(world: World):
    """Wears down Breakables and emits BrokenEvent. Run after anything that emits DamageEvent."""
    events = world.get_resource(EventBus)

    for damage in events.read(DamageEvent):
        breakable = world.try_get_component(damage.target, Breakable)
        if breakable is None or breakable.durability <= 0:
            continue
        if damage.source is None or not world.has_component(
            damage.source, breakable.broken_by
        ):
            continue

        breakable.durability -= damage.amount
        if breakable.durability <= 0:
            events.emit(BrokenEvent(damage.target, damage.source))


def break_cleanup_system(world: World):
    """Destroys what broke. Run last, so drop systems can still read its components."""
    for broken in world.get_resource(EventBus).read(BrokenEvent):
        if world.is_alive(broken.entity):
            world.destroy_entity(broken.entity)
