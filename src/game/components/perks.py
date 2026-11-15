from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum, auto
from types import MappingProxyType

from game.components.buffs import Flag, Stat


class PerkPath(Enum):
    """A line of perks. Each pick in a path earns one of its 5 stars."""

    STRENGTH = auto()
    AGILITY = auto()
    VITALITY = auto()
    TECH = auto()
    ARSENAL = auto()


MAX_STARS = 5


@dataclass(frozen=True, slots=True)
class PerkSpec:
    """Static definition of a permanent perk. **NOT** a component."""

    id: str
    name: str
    description: str
    stars: int
    """1 (common) to 5 (legendary). A path's perk with N stars is its Nth pick."""
    path: PerkPath | None = None
    """None = a fusion (or a one-off filler), which needs other paths' stars."""
    requires: Mapping[PerkPath, int] = field(default_factory=dict)
    """Stars needed in each path before this perk can be offered."""
    multipliers: Mapping[Stat, float] = field(default_factory=dict)
    """Scale a stat. Stacks by multiplying, with buffs and other perks."""
    bonuses: Mapping[Stat, float] = field(default_factory=dict)
    """Flat amounts added to a stat. Stacks by adding."""
    flags: frozenset[Flag] = frozenset()
    heal_fraction: float = 0.0
    """Fraction of max health healed when picked."""
    cash: int = 0
    """Money paid when picked."""
    permanent: bool = True
    """False = a one-off (heal, cash) that isn't kept or shown."""

    def __post_init__(self):
        if not 1 <= self.stars <= MAX_STARS:
            raise ValueError(f"{self.id}: stars must be 1..{MAX_STARS}")
        # Copy so later changes to the caller's dicts can't alter this spec.
        for name in ("requires", "multipliers", "bonuses"):
            object.__setattr__(self, name, MappingProxyType(dict(getattr(self, name))))

    @property
    def is_fusion(self):
        return self.path is None and self.permanent


@dataclass(slots=True)
class Perks:
    """The permanent perks an entity picked this run."""

    owned: list[PerkSpec] = field(default_factory=list)
    undying_ready: bool = True
    """Whether Undying can still save the entity this wave."""

    def add(self, spec: PerkSpec):
        if spec.permanent:
            self.owned.append(spec)

    def has_perk(self, perk_id: str):
        return any(p.id == perk_id for p in self.owned)

    def stars(self, path: PerkPath):
        return sum(1 for p in self.owned if p.path is path)

    def meets(self, requires: Mapping[PerkPath, int]):
        return all(self.stars(path) >= n for path, n in requires.items())

    def multiplier(self, stat: Stat):
        result = 1.0
        for perk in self.owned:
            result *= perk.multipliers.get(stat, 1.0)
        return result

    def bonus(self, stat: Stat):
        return sum(perk.bonuses.get(stat, 0.0) for perk in self.owned)

    def has(self, flag: Flag):
        return any(flag in perk.flags for perk in self.owned)
