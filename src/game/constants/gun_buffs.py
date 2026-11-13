"""Each gun type has one unique buff that grows stronger with rarity."""

import random
from collections.abc import Callable
from dataclasses import dataclass, replace

from game.components.loadout import Gun, GunSpec, Rarity
from game.constants.guns import ALL_GUNS
from game.constants.rarity import RARITIES, roll_rarity


@dataclass(frozen=True, slots=True)
class GunBuff:
    name: str
    values: tuple[float, float, float, float, float]
    """One value per Rarity, Common to Legendary."""
    apply: Callable[[GunSpec, float], GunSpec]
    describe: Callable[[float], str]


def _percent(value: float):
    return f"+{round((value - 1) * 100)}%"


GUN_BUFFS: dict[str, GunBuff] = {
    "pistol": GunBuff(
        name="Hair Trigger",
        values=(1.15, 1.3, 1.5, 1.75, 2.0),
        apply=lambda s, v: replace(s, fire_rate=s.fire_rate * v),
        describe=lambda v: f"{_percent(v)} fire rate",
    ),
    "smg": GunBuff(
        name="Drum Mag",
        values=(1.25, 1.5, 1.75, 2.0, 2.5),
        apply=lambda s, v: replace(
            s,
            magazine_size=round(s.magazine_size * v),
            max_reserve=round(s.max_reserve * v),
        ),
        describe=lambda v: f"{_percent(v)} magazine & reserve",
    ),
    "rifle": GunBuff(
        name="Hollow Points",
        values=(1.1, 1.2, 1.35, 1.5, 1.75),
        apply=lambda s, v: replace(s, damage=s.damage * v),
        describe=lambda v: f"{_percent(v)} damage",
    ),
    "shotgun": GunBuff(
        name="Buckshot",
        values=(1, 2, 3, 4, 6),
        apply=lambda s, v: replace(s, pellets=s.pellets + int(v)),
        describe=lambda v: f"+{int(v)} pellet" + ("s" if v > 1 else ""),
    ),
    "sniper": GunBuff(
        name="Overpenetration",
        values=(1, 2, 3, 4, 6),
        apply=lambda s, v: replace(s, pierce=s.pierce + int(v)),
        describe=lambda v: f"+{int(v)} pierce",
    ),
}


def buffed_spec(spec: GunSpec, rarity: Rarity) -> GunSpec:
    """`spec` with its gun type's buff applied at `rarity`, renamed e.g. "Rare Shotgun"."""
    buff = GUN_BUFFS[spec.id]
    buffed = buff.apply(spec, buff.values[rarity.value])
    return replace(buffed, name=f"{RARITIES[rarity].name} {spec.name}")


def make_gun(spec: GunSpec, rarity: Rarity) -> Gun:
    """A fully loaded gun of `spec`'s type with its rarity buff applied."""
    return Gun.full(buffed_spec(spec, rarity), rarity)


def describe_buff(spec_id: str, rarity: Rarity) -> str:
    """E.g. "Buckshot: +3 pellets"."""
    buff = GUN_BUFFS[spec_id]
    return f"{buff.name}: {buff.describe(buff.values[rarity.value])}"


def roll_gun(rng: random.Random | None = None) -> tuple[GunSpec, Rarity]:
    """Uniform gun type, rarity weighted by RARITIES."""
    rng = rng or random.Random()
    spec = rng.choice(list(ALL_GUNS.values()))
    return spec, roll_rarity(rng)
