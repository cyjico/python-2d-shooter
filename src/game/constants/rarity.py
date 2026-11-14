import random
from dataclasses import dataclass

from game.components.loadout import Rarity
from game.util.rng import resolve_rng


@dataclass(frozen=True, slots=True)
class RarityInfo:
    stars: int
    """How many stars the tier shows next to a gun's name."""
    color: tuple[int, int, int]
    weight: float
    """Relative chance of rolling this tier from the mystery box."""


RARITIES: dict[Rarity, RarityInfo] = {
    Rarity.COMMON: RarityInfo(1, (200, 200, 200), 40),
    Rarity.UNCOMMON: RarityInfo(2, (90, 210, 90), 28),
    Rarity.RARE: RarityInfo(3, (80, 150, 255), 18),
    Rarity.EPIC: RarityInfo(4, (185, 95, 255), 10),
    Rarity.LEGENDARY: RarityInfo(5, (255, 175, 40), 4),
}

PLAIN_COLOR = (255, 255, 255)
"""Text color for guns without a rarity."""


def rarity_color(rarity: Rarity | None):
    return PLAIN_COLOR if rarity is None else RARITIES[rarity].color


def rarity_stars(rarity: Rarity | None):
    """Stars shown for a gun. Plain guns (no rarity) show none."""
    return 0 if rarity is None else RARITIES[rarity].stars


def roll_rarity(rng: random.Random | None = None):
    """Rarity weighted by RARITIES."""
    tiers = list(RARITIES)
    return resolve_rng(rng).choices(tiers, weights=[RARITIES[t].weight for t in tiers])[
        0
    ]
