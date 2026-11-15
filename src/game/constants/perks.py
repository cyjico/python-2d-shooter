"""Roguelike perks: after every cleared wave the player picks one of a few.

Each path has 5 perks, from 1 star (common) to 5 stars (legendary, a unique
passive), offered in order: a path's Nth pick is its N-star perk. Fusions
unlock once two paths both have enough stars.
"""

import random
from dataclasses import dataclass

from game.components.buffs import Flag, Stat
from game.components.loadout import FireMode, GunSpec, Rarity
from game.components.perks import MAX_STARS, PerkPath, Perks, PerkSpec
from game.constants.rarity import rarity_color
from game.util.rng import resolve_rng


@dataclass(frozen=True, slots=True)
class PathInfo:
    name: str
    short: str
    """For the HUD."""
    color: tuple[int, int, int]


PATHS: dict[PerkPath, PathInfo] = {
    PerkPath.STRENGTH: PathInfo("Strength", "STR", (235, 80, 70)),
    PerkPath.AGILITY: PathInfo("Agility", "AGI", (80, 210, 240)),
    PerkPath.VITALITY: PathInfo("Vitality", "VIT", (110, 220, 110)),
    PerkPath.TECH: PathInfo("Tech", "TEC", (180, 120, 255)),
    PerkPath.ARSENAL: PathInfo("Arsenal", "ARS", (245, 165, 60)),
}

FUSION_COLOR = (255, 120, 210)
FILLER_COLOR = (200, 200, 200)


def stars_color(stars: int):
    """Same tiers as gun rarity: 1 star = common grey ... 5 = legendary gold."""
    return rarity_color(Rarity(stars - 1))


def perk_color(spec: PerkSpec):
    if spec.path is not None:
        return PATHS[spec.path].color
    return FUSION_COLOR if spec.is_fusion else FILLER_COLOR


def _path(path: PerkPath, *perks: PerkSpec):
    for stars, perk in enumerate(perks, start=1):
        if perk.path is not path or perk.stars != stars:
            raise ValueError(f"{perk.id}: expected {path.name} {stars} stars")
    return list(perks)


S, A, V, T, R = (
    PerkPath.STRENGTH,
    PerkPath.AGILITY,
    PerkPath.VITALITY,
    PerkPath.TECH,
    PerkPath.ARSENAL,
)

PATH_PERKS: dict[PerkPath, list[PerkSpec]] = {
    S: _path(
        S,
        PerkSpec(
            "str_heavy",
            "Heavy Rounds",
            "+20% damage.",
            1,
            S,
            multipliers={Stat.DAMAGE: 1.2},
        ),
        PerkSpec(
            "str_hollow",
            "Hollow Points",
            "+10% crit chance.",
            2,
            S,
            bonuses={Stat.CRIT_CHANCE: 0.10},
        ),
        PerkSpec(
            "str_brutal",
            "Brutal Crits",
            "Critical hits deal +1x more damage.",
            3,
            S,
            bonuses={Stat.CRIT_DAMAGE: 1.0},
        ),
        PerkSpec(
            "str_pierce",
            "Penetrator",
            "Bullets pierce 1 more enemy. +10% damage.",
            4,
            S,
            multipliers={Stat.DAMAGE: 1.1},
            bonuses={Stat.PIERCE: 1},
        ),
        PerkSpec(
            "str_carnage",
            "Carnage",
            "Enemies you kill explode, hurting every enemy around them.",
            5,
            S,
            flags=frozenset({Flag.CARNAGE}),
        ),
    ),
    A: _path(
        A,
        PerkSpec(
            "agi_feet",
            "Light Feet",
            "+15% move speed.",
            1,
            A,
            multipliers={Stat.MOVE_SPEED: 1.15},
        ),
        PerkSpec(
            "agi_wind",
            "Second Wind",
            "Stamina recovers 50% faster.",
            2,
            A,
            multipliers={Stat.STAMINA_REGEN: 1.5},
        ),
        PerkSpec(
            "agi_bar",
            "Extra Bar",
            "+1 stamina bar, so one more dash.",
            3,
            A,
            bonuses={Stat.STAMINA_SEGMENTS: 1},
        ),
        PerkSpec(
            "agi_evasive",
            "Evasive",
            "Nothing can hurt you while you dash.",
            4,
            A,
            flags=frozenset({Flag.DASH_IMMUNE}),
        ),
        PerkSpec(
            "agi_tempest",
            "Tempest",
            "Dashes slam enemies for heavy damage. +1 stamina bar.",
            5,
            A,
            bonuses={Stat.STAMINA_SEGMENTS: 1},
            flags=frozenset({Flag.DASH_STRIKE}),
        ),
    ),
    V: _path(
        V,
        PerkSpec(
            "vit_tough",
            "Tough Skin",
            "+30 max health.",
            1,
            V,
            bonuses={Stat.MAX_HEALTH: 30},
        ),
        PerkSpec(
            "vit_regen",
            "Regeneration",
            "Regenerate 2 health per second.",
            2,
            V,
            bonuses={Stat.HEALTH_REGEN: 2},
        ),
        PerkSpec(
            "vit_vampire",
            "Vampire Rounds",
            "Heal 6% of the damage you deal.",
            3,
            V,
            bonuses={Stat.LIFESTEAL: 0.06},
        ),
        PerkSpec(
            "vit_iron",
            "Iron Body",
            "Take 20% less damage. +20 max health.",
            4,
            V,
            multipliers={Stat.DAMAGE_TAKEN: 0.8},
            bonuses={Stat.MAX_HEALTH: 20},
        ),
        PerkSpec(
            "vit_undying",
            "Undying",
            "Once per wave, a killing blow leaves you at 1 health instead.",
            5,
            V,
            flags=frozenset({Flag.UNDYING}),
        ),
    ),
    T: _path(
        T,
        PerkSpec(
            "tec_drone",
            "Drone",
            "A drone orbits you and shoots nearby enemies.",
            1,
            T,
            bonuses={Stat.DRONES: 1},
        ),
        PerkSpec(
            "tec_wingman",
            "Wingman",
            "+1 drone.",
            2,
            T,
            bonuses={Stat.DRONES: 1},
        ),
        PerkSpec(
            "tec_overclock",
            "Overclock",
            "Drones fire 50% faster.",
            3,
            T,
            multipliers={Stat.DRONE_FIRE_RATE: 1.5},
        ),
        PerkSpec(
            "tec_bay",
            "Drone Bay",
            "+1 drone. Drones deal 25% more damage.",
            4,
            T,
            multipliers={Stat.DRONE_DAMAGE: 1.25},
            bonuses={Stat.DRONES: 1},
        ),
        PerkSpec(
            "tec_hive",
            "Hive Mind",
            "+2 drones, and every drone fires three bullets at once.",
            5,
            T,
            bonuses={Stat.DRONES: 2},
            flags=frozenset({Flag.DRONE_SPREAD}),
        ),
    ),
    R: _path(
        R,
        PerkSpec(
            "ars_hands",
            "Quick Hands",
            "Reload 30% faster.",
            1,
            R,
            multipliers={Stat.RELOAD_SPEED: 1.3},
        ),
        PerkSpec(
            "ars_trigger",
            "Hair Trigger",
            "+15% fire rate.",
            2,
            R,
            multipliers={Stat.FIRE_RATE: 1.15},
        ),
        PerkSpec(
            "ars_scavenger",
            "Scavenger",
            "Every kill puts 2 rounds back in your magazine.",
            3,
            R,
            bonuses={Stat.AMMO_ON_KILL: 2},
        ),
        PerkSpec(
            "ars_rapid",
            "Rapid Fire",
            "+20% fire rate. Reload 20% faster.",
            4,
            R,
            multipliers={Stat.FIRE_RATE: 1.2, Stat.RELOAD_SPEED: 1.2},
        ),
        PerkSpec(
            "ars_hell",
            "Bullet Hell",
            "Every shot fires 2 extra bullets in a fan.",
            5,
            R,
            bonuses={Stat.EXTRA_PROJECTILES: 2},
        ),
    ),
}

FUSION_STARS = 3
"""Stars needed in both paths of a fusion."""

FUSIONS: list[PerkSpec] = [
    PerkSpec(
        "fus_gunship",
        "Gunship",
        "Drones deal double damage and pierce an enemy.",
        5,
        requires={S: FUSION_STARS, T: FUSION_STARS},
        multipliers={Stat.DRONE_DAMAGE: 2.0},
        bonuses={Stat.DRONE_PIERCE: 1},
    ),
    PerkSpec(
        "fus_berserker",
        "Berserker",
        "Up to +60% damage the lower your health is.",
        5,
        requires={S: FUSION_STARS, V: FUSION_STARS},
        flags=frozenset({Flag.BERSERK}),
    ),
    PerkSpec(
        "fus_predator",
        "Predator",
        "+15% crit chance and +10% move speed.",
        5,
        requires={S: FUSION_STARS, A: FUSION_STARS},
        multipliers={Stat.MOVE_SPEED: 1.1},
        bonuses={Stat.CRIT_CHANCE: 0.15},
    ),
    PerkSpec(
        "fus_blood_rush",
        "Blood Rush",
        "Every dash heals 8 health.",
        5,
        requires={A: FUSION_STARS, V: FUSION_STARS},
        bonuses={Stat.DASH_HEAL: 8},
    ),
    PerkSpec(
        "fus_tactical_roll",
        "Tactical Roll",
        "Dashing instantly reloads your gun.",
        5,
        requires={A: FUSION_STARS, R: FUSION_STARS},
        flags=frozenset({Flag.DASH_RELOAD}),
    ),
    PerkSpec(
        "fus_linked_fire",
        "Linked Fire",
        "+1 drone. Drones fire 40% faster.",
        5,
        requires={T: FUSION_STARS, R: FUSION_STARS},
        multipliers={Stat.DRONE_FIRE_RATE: 1.4},
        bonuses={Stat.DRONES: 1},
    ),
    PerkSpec(
        "fus_repair_drones",
        "Repair Drones",
        "Regenerate 1 health per second for each drone.",
        5,
        requires={T: FUSION_STARS, V: FUSION_STARS},
        bonuses={Stat.DRONE_REGEN: 1},
    ),
]

FILLERS: list[PerkSpec] = [
    PerkSpec(
        "patch_up",
        "Patch Up",
        "Heal 50% of your health.",
        1,
        heal_fraction=0.5,
        permanent=False,
    ),
    PerkSpec("payday", "Payday", "Get $250.", 1, cash=250, permanent=False),
]
"""Offered only once fewer real perks are left than cards to fill."""

ALL_PERKS: dict[str, PerkSpec] = {
    p.id: p
    for p in (
        *(perk for perks in PATH_PERKS.values() for perk in perks),
        *FUSIONS,
        *FILLERS,
    )
}

# --- Offers ---

OFFER_SIZE = 3
FUSION_WEIGHT = 3.0
"""A fusion is this much likelier to show up than a path with no stars."""
PATH_WEIGHT_PER_STAR = 0.5
"""Each star in a path makes its next perk this much likelier, so a path
you've committed to keeps showing up."""
REROLL_PRICE = 100
REROLL_PRICE_STEP = 100
"""Each reroll in the same pick costs this much more than the last."""


def next_path_perk(perks: Perks, path: PerkPath):
    """The path's next perk, or None once it has all 5 stars."""
    stars = perks.stars(path)
    return PATH_PERKS[path][stars] if stars < MAX_STARS else None


def perk_candidates(perks: Perks):
    """Every perk that can be offered right now."""
    candidates = [
        perk
        for path in PerkPath
        if (perk := next_path_perk(perks, path)) is not None
        and perks.meets(perk.requires)
    ]
    candidates += [
        f for f in FUSIONS if not perks.has_perk(f.id) and perks.meets(f.requires)
    ]
    return candidates


def offer_weight(perks: Perks, spec: PerkSpec):
    if spec.path is None:
        return FUSION_WEIGHT
    return 1.0 + PATH_WEIGHT_PER_STAR * perks.stars(spec.path)


def roll_offer(perks: Perks, rng: random.Random | None = None, count=OFFER_SIZE):
    """`count` different perks to choose from, topped up with fillers."""
    rng = resolve_rng(rng)
    pool = perk_candidates(perks)
    offer: list[PerkSpec] = []
    while pool and len(offer) < count:
        pick = rng.choices(pool, weights=[offer_weight(perks, p) for p in pool])[0]
        pool.remove(pick)
        offer.append(pick)
    offer += FILLERS[: count - len(offer)]
    return offer


def reroll_price(rerolls: int):
    """Price of the next reroll after `rerolls` in the same pick."""
    return REROLL_PRICE + REROLL_PRICE_STEP * rerolls


# --- Effect tuning ---

CARNAGE_RADIUS = 120.0
CARNAGE_DAMAGE_FRACTION = 0.5
"""Explosion damage, as a fraction of the dead enemy's max health."""
CARNAGE_MIN_DAMAGE = 20.0
DASH_STRIKE_DAMAGE = 60.0
"""Scaled by the dasher's damage multiplier."""
UNDYING_IMMUNITY = 2.0
"""Seconds of immunity after Undying saves you."""
BERSERK_MAX_BONUS = 0.6
"""Extra damage at (almost) no health."""
EXTRA_PROJECTILE_SPREAD = 10.0
"""Degrees between the fanned-out bullets of Bullet Hell (and the drones' spread)."""

# --- Drones ---

DRONE_GUN = GunSpec(
    id="drone",
    name="Drone",
    fire_mode=FireMode.AUTO,
    damage=8,
    fire_rate=2.5,
    magazine_size=1000,
    max_reserve=0,
    reload_time=1.0,
    projectile_speed=900,
    max_range=480,
    spread=3,
    knockback=20,
    projectile_size=(8, 3),
    projectile_color=(205, 160, 255),
)
DRONE_RANGE = 420.0
"""Drones only shoot at enemies this close to them."""
DRONE_ORBIT_RADIUS = 56.0
DRONE_ORBIT_SPEED = 1.8
"""Radians per second."""
DRONE_COLOR = (185, 125, 255)
