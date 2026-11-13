from game.components.buffs import Stat
from game.components.wallet import Wallet
from game.core_ecs.entity import Entity
from game.core_ecs.world import World
from game.util.buffs import stat_multiplier


def earn_money(world: World, entity: Entity, base_amount: int) -> int:
    """Pays `entity` its money multiplier x `base_amount`. Returns what was paid
    (0 if the entity has no Wallet)."""
    wallet = world.try_get_component(entity, Wallet)
    if wallet is None:
        return 0

    amount = round(base_amount * stat_multiplier(world, entity, Stat.MONEY))
    wallet.earn(amount)
    return amount
