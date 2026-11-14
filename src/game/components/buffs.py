from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum, auto
from types import MappingProxyType


class Stat(Enum):
    """Numbers a buff can scale. Systems ask for the multiplier where they use the stat."""

    MOVE_SPEED = auto()
    DAMAGE = auto()
    MONEY = auto()
    STAMINA_SEGMENTS = auto()
    """Used with `bonuses`: extra stamina bars."""
    STAMINA_REGEN = auto()


class Flag(Enum):
    """Yes/no effects a buff can grant."""

    IMMUNE = auto()


@dataclass(frozen=True, slots=True)
class BuffSpec:
    """Static, shareable definition of a buff. Never mutated at runtime. **NOT** a
    component for an entity."""

    id: str
    name: str
    duration: float
    """Seconds."""
    multipliers: Mapping[Stat, float] = field(default_factory=dict)
    """Scale a stat. Stacks by multiplying."""
    bonuses: Mapping[Stat, float] = field(default_factory=dict)
    """Flat amounts added to a stat. Stacks by adding."""
    flags: frozenset[Flag] = frozenset()
    bonus_health: float = 0.0
    """Extra health that absorbs damage first. Whatever is left is lost when the buff ends."""

    def __post_init__(self):
        # Copy so later changes to the caller's dict can't alter this spec.
        object.__setattr__(
            self, "multipliers", MappingProxyType(dict(self.multipliers))
        )


@dataclass(slots=True)
class ActiveBuff:
    """**NOT** a component for an entity."""

    spec: BuffSpec
    time_left: float
    bonus_health: float
    """What is left of `spec.bonus_health`."""


@dataclass(slots=True)
class ActiveBuffs:
    """The buffs an entity currently has."""

    buffs: list[ActiveBuff] = field(default_factory=list)

    def add(self, spec: BuffSpec):
        """Starts `spec`, or restarts it if it is already active."""
        self.buffs = [b for b in self.buffs if b.spec.id != spec.id]
        self.buffs.append(ActiveBuff(spec, spec.duration, spec.bonus_health))

    def multiplier(self, stat: Stat) -> float:
        result = 1.0
        for buff in self.buffs:
            result *= buff.spec.multipliers.get(stat, 1.0)
        return result

    def bonus(self, stat: Stat) -> float:
        return sum(buff.spec.bonuses.get(stat, 0.0) for buff in self.buffs)

    def has(self, flag: Flag) -> bool:
        return any(flag in buff.spec.flags for buff in self.buffs)

    def absorb(self, amount: float) -> float:
        """Spends bonus health on `amount` damage. Returns the damage left over."""
        for buff in self.buffs:
            taken = min(buff.bonus_health, amount)
            buff.bonus_health -= taken
            amount -= taken
        return amount

    def tick(self, dt: float):
        for buff in self.buffs:
            buff.time_left -= dt
        self.buffs = [b for b in self.buffs if b.time_left > 0]
