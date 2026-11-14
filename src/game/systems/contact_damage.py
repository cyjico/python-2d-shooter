from game.components.contact_damage import ContactDamage
from game.components.health import Health
from game.core_ecs.world import World
from game.events.collision import CollisionEvent
from game.events.combat import DamageEvent
from game.resources.event_bus import EventBus


def contact_damage_system(world: World, dt: float):
    """Emits a DamageEvent when a ContactDamage touches a valid victim. Run after
    collision_system, before health_system."""
    events = world.get_resource(EventBus)

    for _, (contact,) in world.query(ContactDamage):
        contact.cooldowns = {
            e: left - dt for e, left in contact.cooldowns.items() if left - dt > 0
        }

    for collision in events.read(CollisionEvent):
        for me, other in (
            (collision.entity_a, collision.entity_b),
            (collision.entity_b, collision.entity_a),
        ):
            contact = world.try_get_component(me, ContactDamage)
            if contact is None or other in contact.cooldowns:
                continue
            if not world.has_component(other, contact.hits):
                continue
            if not world.has_component(other, Health):
                continue

            contact.cooldowns[other] = contact.cooldown
            events.emit(DamageEvent(other, contact.amount, me))
