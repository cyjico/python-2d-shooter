import random
from dataclasses import dataclass

from game.components.loadout import Rarity


@dataclass(frozen=True, slots=True)
class RarityInfo:
    name: str
    color: tuple[int, int, int]
    weight: float
    """Relative chance of rolling this tier from the mystery box."""


RARITIES: dict[Rarity, RarityInfo] = {
    Rarity.COMMON: RarityInfo("Common", (200, 200, 200), 40),
    Rarity.UNCOMMON: RarityInfo("Uncommon", (90, 210, 90), 28),
    Rarity.RARE: RarityInfo("Rare", (80, 150, 255), 18),
    Rarity.EPIC: RarityInfo("Epic", (185, 95, 255), 10),
    Rarity.LEGENDARY: RarityInfo("Legendary", (255, 175, 40), 4),
}

PLAIN_COLOR = (255, 255, 255)
"""Text color for guns without a rarity."""


def rarity_color(rarity: Rarity | None):
    return PLAIN_COLOR if rarity is None else RARITIES[rarity].color


def roll_rarity(rng: random.Random | None = None):
    """Rarity weighted by RARITIES."""
    rng = rng or random.Random()
    tiers = list(RARITIES)
    return rng.choices(tiers, weights=[RARITIES[t].weight for t in tiers])[0]
