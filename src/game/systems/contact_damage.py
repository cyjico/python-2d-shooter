from game.components.contact_damage import ContactDamage
from game.components.health import Health
from game.core_ecs.world import World
from game.events.collision import CollisionEvent, directed
from game.events.combat import DamageEvent
from game.resources.event_bus import EventBus


def contact_damage_system(world: World, dt: float):
    """Emits a DamageEvent when a ContactDamage touches a valid victim. Run after
    collision_system, before health_system."""
    events = world.get_resource(EventBus)

    for _, (contact,) in world.query(ContactDamage):
        contact.tick(dt)

    for me, other in directed(events.read(CollisionEvent)):
        contact = world.try_get_component(me, ContactDamage)
        if contact is None:
            continue
        if not world.has_component(other, contact.hits):
            continue
        if not world.has_component(other, Health):
            continue

        if contact.try_hit(other):
            events.emit(DamageEvent(other, contact.amount, me))
