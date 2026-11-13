from game.components.bounty import Bounty
from game.core_ecs.world import World
from game.events.combat import EntityDiedEvent
from game.resources.event_bus import EventBus
from game.util.money import earn_money


def bounty_system(world: World):
    """Pays killers the bounty of what they killed. Run after health_system,
    before death_cleanup_system."""
    for death in world.get_resource(EventBus).read(EntityDiedEvent):
        if death.killer is None:
            continue

        bounty = world.try_get_component(death.entity, Bounty)
        if bounty is not None:
            earn_money(world, death.killer, bounty.amount)
