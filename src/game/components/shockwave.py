from dataclasses import dataclass


@dataclass(slots=True)
class Shockwave:
    """A ring that grows to `radius` and fades over its Lifetime (Carnage)."""

    radius: float
    color: tuple[int, int, int]
