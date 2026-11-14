from dataclasses import dataclass


@dataclass(slots=True)
class Lifetime:
    """Destroys its entity once `duration` seconds have passed."""

    duration: float
    age: float = 0.0
    """Seconds since spawned. Runtime state."""

    @property
    def progress(self):
        """0 when spawned, 1 when expired."""
        return min(1.0, self.age / self.duration) if self.duration > 0 else 1.0
