from dataclasses import dataclass, field


@dataclass(slots=True)
class Stamina:
    """A pool measured in segments. Spending takes whole segments; regeneration
    is continuous, so a segment fills gradually rather than all at once."""

    segments: int = 2
    """Base number of segments."""
    regen_rate: float = 0.3
    """Segments regained per second."""

    # Runtime state
    current: float = field(init=False)
    bonus_segments: int = 0
    """Extra segments from buffs. Set every frame by stamina_system."""

    def __post_init__(self):
        self.current = float(self.segments)

    @property
    def maximum(self):
        return self.segments + self.bonus_segments

    @property
    def fraction(self):
        """0..1 fill level."""
        return self.current / self.maximum if self.maximum > 0 else 0.0

    def can_afford(self, amount: float):
        return self.current >= amount

    def try_spend(self, amount: float):
        """Spends `amount` if affordable. Returns whether it did."""
        if not self.can_afford(amount):
            return False
        self.current -= amount
        return True

    def regen(self, regen_multiplier: float, dt: float):
        """Regenerates, and clamps to `maximum` (which also handles a bonus expiring)."""
        self.current = min(
            float(self.maximum),
            self.current + self.regen_rate * regen_multiplier * dt,
        )
