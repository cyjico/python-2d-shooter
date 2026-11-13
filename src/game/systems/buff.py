import random

from game.components.buff_drop import BuffDrop
from game.components.buffs import ActiveBuffs
from game.constants.buffs import roll_buff
from game.core_ecs.world import World
from game.events.combat import BrokenEvent
from game.resources.event_bus import EventBus
from game.util.buffs import grant_buff


def buff_tick_system(world: World, dt: float):
    for _, (buffs,) in world.query(ActiveBuffs):
        buffs.tick(dt)


def buff_drop_system(world: World, rng: random.Random | None = None):
    """Gives the breaker a random buff. Run after breakable_system, before break_cleanup_system."""
    for broken in world.get_resource(EventBus).read(BrokenEvent):
        if world.has_component(broken.entity, BuffDrop):
            grant_buff(world, broken.breaker, roll_buff(rng))
