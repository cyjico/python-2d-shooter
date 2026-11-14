import random

from game.components.buffs import BuffSpec, Flag, Stat
from game.components.loadout import Rarity
from game.constants.rarity import roll_rarity

SPEED_BOOST = BuffSpec(
    id="speed",
    name="Speed Boost",
    duration=10.0,
    multipliers={Stat.MOVE_SPEED: 1.5},
)

DAMAGE_BOOST = BuffSpec(
    id="damage",
    name="Damage Boost",
    duration=10.0,
    multipliers={Stat.DAMAGE: 1.5},
)

IMMUNITY = BuffSpec(
    id="immunity",
    name="Immunity",
    duration=5.0,
    flags=frozenset({Flag.IMMUNE}),
)

OVERHEAL = BuffSpec(
    id="overheal",
    name="Overheal",
    duration=15.0,
    bonus_health=300.0,
)

EXTRA_STAMINA = BuffSpec(
    id="extra_stamina",
    name="Extra Stamina",
    duration=15.0,
    bonuses={Stat.STAMINA_SEGMENTS: 2},
)

QUICK_RECOVERY = BuffSpec(
    id="quick_recovery",
    name="Quick Recovery",
    duration=15.0,
    multipliers={Stat.STAMINA_REGEN: 2.0},
)

ALL_BUFFS: dict[str, BuffSpec] = {
    b.id: b
    for b in (
        SPEED_BOOST,
        DAMAGE_BOOST,
        IMMUNITY,
        OVERHEAL,
        EXTRA_STAMINA,
        QUICK_RECOVERY,
    )
}
"""Everything a BuffDrop can roll (no rarities)."""

MONEY_BOOST_ID = "money"
MONEY_BOOST_DURATION = 15.0

MONEY_MULTIPLIERS: dict[Rarity, float] = {
    Rarity.COMMON: 1.25,
    Rarity.UNCOMMON: 1.5,
    Rarity.RARE: 1.75,
    Rarity.EPIC: 2.0,
    Rarity.LEGENDARY: 4.0,
}

MONEY_BOOSTS: dict[Rarity, BuffSpec] = {
    rarity: BuffSpec(
        id=MONEY_BOOST_ID,
        name=f"Money x{mult:g}",
        duration=MONEY_BOOST_DURATION,
        multipliers={Stat.MONEY: mult},
    )
    for rarity, mult in MONEY_MULTIPLIERS.items()
}
"""One money buff per rarity tier."""


def roll_buff(rng: random.Random | None = None):
    """Uniform over the fixed buffs and the money boost; money's tier is
    weighted by RARITIES."""
    rng = rng or random.Random()
    kind = rng.choice([*ALL_BUFFS, MONEY_BOOST_ID])
    if kind == MONEY_BOOST_ID:
        return MONEY_BOOSTS[roll_rarity(rng)]
    return ALL_BUFFS[kind]
