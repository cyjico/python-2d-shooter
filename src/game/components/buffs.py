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

    # Mostly from perks (see `constants.perks`).
    MAX_HEALTH = auto()
    """Bonus: extra max health. Applied once, when the perk is picked."""
    HEALTH_REGEN = auto()
    """Bonus: health regained per second."""
    LIFESTEAL = auto()
    """Bonus: fraction of damage dealt to enemies that heals the dealer."""
    DAMAGE_TAKEN = auto()
    """Multiplier on incoming damage."""
    CRIT_CHANCE = auto()
    """Bonus: added to every gun's crit chance."""
    CRIT_DAMAGE = auto()
    """Bonus: added to every gun's crit multiplier."""
    PIERCE = auto()
    """Bonus: extra targets each bullet passes through."""
    FIRE_RATE = auto()
    RELOAD_SPEED = auto()
    EXTRA_PROJECTILES = auto()
    """Bonus: extra bullets fanned out around every shot."""
    AMMO_ON_KILL = auto()
    """Bonus: rounds put back into the magazine per kill."""
    DASH_HEAL = auto()
    """Bonus: health regained per dash."""
    DRONES = auto()
    """Bonus: drones orbiting the entity."""
    DRONE_FIRE_RATE = auto()
    DRONE_DAMAGE = auto()
    DRONE_PIERCE = auto()
    """Bonus: extra targets each drone bullet passes through."""
    DRONE_REGEN = auto()
    """Bonus: health regained per second, per drone."""


class Flag(Enum):
    """Yes/no effects a buff or perk can grant."""

    IMMUNE = auto()
    DASH_IMMUNE = auto()
    """No damage while dashing."""
    DASH_STRIKE = auto()
    """Dashing into an enemy damages it."""
    DASH_RELOAD = auto()
    """Starting a dash finishes the gun's reload instantly."""
    CARNAGE = auto()
    """Enemies this entity kills explode, damaging enemies around them."""
    UNDYING = auto()
    """Once per wave, a killing blow leaves 1 health instead."""
    BERSERK = auto()
    """More damage the lower this entity's health."""
    DRONE_SPREAD = auto()
    """Drones fire three bullets at once."""


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
    shield: float = 0.0
    """Extra health that absorbs damage first. Whatever is left is lost when the buff ends."""

    def __post_init__(self):
        # Copy so later changes to the caller's dicts can't alter this spec.
        object.__setattr__(
            self, "multipliers", MappingProxyType(dict(self.multipliers))
        )
        object.__setattr__(self, "bonuses", MappingProxyType(dict(self.bonuses)))


@dataclass(slots=True)
class ActiveBuff:
    """**NOT** a component for an entity."""

    spec: BuffSpec
    time_left: float
    shield: float
    """What is left of `spec.shield`."""


@dataclass(slots=True)
class ActiveBuffs:
    """The buffs an entity currently has."""

    buffs: list[ActiveBuff] = field(default_factory=list)

    @property
    def shield(self):
        """Total shield left across all active buffs."""
        return sum(buff.shield for buff in self.buffs)

    def add(self, spec: BuffSpec):
        """Starts `spec`, or restarts it if it is already active."""
        self.buffs = [b for b in self.buffs if b.spec.id != spec.id]
        self.buffs.append(ActiveBuff(spec, spec.duration, spec.shield))

    def multiplier(self, stat: Stat):
        result = 1.0
        for buff in self.buffs:
            result *= buff.spec.multipliers.get(stat, 1.0)
        return result

    def bonus(self, stat: Stat):
        return sum(buff.spec.bonuses.get(stat, 0.0) for buff in self.buffs)

    def has(self, flag: Flag):
        return any(flag in buff.spec.flags for buff in self.buffs)

    def absorb(self, amount: float):
        """Spends shield on `amount` damage. Returns the damage left over."""
        for buff in self.buffs:
            taken = min(buff.shield, amount)
            buff.shield -= taken
            amount -= taken
        return amount

    def tick(self, dt: float):
        for buff in self.buffs:
            buff.time_left -= dt
        self.buffs = [b for b in self.buffs if b.time_left > 0]
