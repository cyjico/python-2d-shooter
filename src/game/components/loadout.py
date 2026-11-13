from dataclasses import dataclass, field
from enum import Enum, auto

import pygame


class FireMode(Enum):
    SEMI = auto()
    """One shot per click."""
    AUTO = auto()
    """Fires continuously while the trigger is held."""


@dataclass(frozen=True, slots=True)
class GunSpec:
    """Static, shareable definition of a gun type. Never mutated at runtime."""

    id: str
    name: str
    fire_mode: FireMode
    damage: float
    """Per projectile. Shotguns deal this per pellet."""
    fire_rate: float
    """Shots per second."""
    magazine_size: int
    max_reserve: int
    """Ammo carried outside the magazine."""
    reload_time: float
    """Seconds."""
    projectile_speed: float
    """px/s."""
    max_range: float
    """Px a projectile travels before despawning."""

    spread: float = 0.0
    """Max random deviation to either side of the aim direction, in degrees."""
    pellets: int = 1
    """Projectiles per shot."""
    pierce: int = 0
    """Extra targets a projectile passes through after the first."""
    knockback: float = 0.0
    """Impulse applied to whatever a projectile hits (depends on target mass)."""

    projectile_size: tuple[float, float] = (10.0, 4.0)
    projectile_color: tuple[int, int, int] = (255, 230, 120)

    def __post_init__(self):
        if self.fire_rate <= 0:
            raise ValueError(f"{self.id}: fire_rate must be positive")
        if self.magazine_size <= 0:
            raise ValueError(f"{self.id}: magazine_size must be positive")
        if self.projectile_speed <= 0:
            raise ValueError(f"{self.id}: projectile_speed must be positive")

        if self.pellets <= 0:
            raise ValueError(f"{self.id}: pellets must be positive")


@dataclass(slots=True)
class Gun:
    """A gun a character is carrying."""

    spec: GunSpec
    magazine: int
    reserve: int
    cooldown: float = 0.0
    """Seconds until the next shot is allowed."""
    reload_remaining: float = 0.0
    """Seconds left on the current reload. 0 = not reloading."""

    @classmethod
    def full(cls, spec: GunSpec):
        return cls(spec=spec, magazine=spec.magazine_size, reserve=spec.max_reserve)

    @property
    def reloading(self):
        return self.reload_remaining > 0

    @property
    def can_reload(self):
        return (
            not self.reloading
            and self.magazine < self.spec.magazine_size
            and self.reserve > 0
        )

    @property
    def can_fire(self):
        return self.magazine > 0 and self.cooldown <= 0

    def refill(self):
        """Refill the magazine and reserve."""
        self.magazine = self.spec.magazine_size
        self.reserve = self.spec.max_reserve
        self.reload_remaining = 0.0


@dataclass(slots=True)
class Loadout:
    """The guns an entity carries and which one is in hand."""

    slots: list[Gun] = field(default_factory=list)
    active: int = 0
    max_slots: int = 2
    muzzle: pygame.Vector2 = field(default_factory=lambda: pygame.Vector2(24, 0))
    """Where projectiles spawn. Local to the entity's transform."""

    @property
    def equipped(self):
        return self.slots[self.active] if self.slots else None

    def give(self, spec: GunSpec) -> Gun | None:
        """Hand over a gun (this is what the mystery box will call).

        - Already holding this gun type: refills its ammo.
        - Free slot: adds it and equips it.
        - Slots full: replaces the gun in hand.

        Returns the gun that was replaced, if any.
        """
        for gun in self.slots:
            if gun.spec.id == spec.id:
                gun.refill()
                return None

        new_gun = Gun.full(spec)
        if len(self.slots) < self.max_slots:
            self.slots.append(new_gun)
            self.active = len(self.slots) - 1
            return None

        replaced = self.slots[self.active]
        self.slots[self.active] = new_gun
        return replaced

    def cycle(self, step: int):
        if len(self.slots) < 2:
            return
        # Switching away cancels a reload in progress.
        self.slots[self.active].reload_remaining = 0.0
        self.active = (self.active + step) % len(self.slots)
