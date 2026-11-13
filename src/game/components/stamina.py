from dataclasses import dataclass, field


@dataclass(slots=True)
class Stamina:
    """A pool measured in segments. Spending takes whole segments; regeneration
    is continuous, so a segment fills gradually rather than all at once."""

    segments: int = 2
    """Number of segments. Also the maximum."""
    regen_rate: float = 0.3
    """Segments regained per second."""

    current: float = field(init=False)

    def __post_init__(self):
        self.current = float(self.segments)

    def fraction(self, bonus_segments: int):
        """0..1 fill level."""
        maximum = self.segments + bonus_segments
        return self.current / maximum if maximum > 0 else 0.0

    def can_afford(self, amount: float):
        return self.current >= amount

    def try_spend(self, amount: float):
        """Spends `amount` if affordable. Returns whether it did."""
        if not self.can_afford(amount):
            return False
        self.current -= amount
        return True

    def regen(self, bonus_segments: int, regen_multiplier: float, dt: float):
        self.current = min(
            float(self.segments + bonus_segments),
            self.current + self.regen_rate * regen_multiplier * dt,
        )
