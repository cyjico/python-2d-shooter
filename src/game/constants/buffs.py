import random

from game.components.buffs import BuffSpec, Flag, Stat

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

ALL_BUFFS: dict[str, BuffSpec] = {
    b.id: b for b in (SPEED_BOOST, DAMAGE_BOOST, IMMUNITY, OVERHEAL)
}
"""Everything a BuffDrop can roll."""


def roll_buff(rng: random.Random | None = None) -> BuffSpec:
    """Uniform over ALL_BUFFS."""
    rng = rng or random.Random()
    return rng.choice(list(ALL_BUFFS.values()))
