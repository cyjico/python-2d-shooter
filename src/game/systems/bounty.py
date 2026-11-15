from game.components.bounty import Bounty
from game.core_ecs.world import World
from game.events.combat import EntityDiedEvent
from game.resources.event_bus import EventBus
from game.util.money import earn_money
from game.util.ownership import owner_of


def bounty_system(world: World):
    """Pays killers the bounty of what they killed (a drone's kill pays its owner)."""
    for death in world.get_resource(EventBus).read(EntityDiedEvent):
        killer = owner_of(world, death.killer)
        if killer is None:
            continue

        bounty = world.try_get_component(death.entity, Bounty)
        if bounty is not None:
            earn_money(world, killer, bounty.amount)
