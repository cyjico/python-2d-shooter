from dataclasses import dataclass


@dataclass(slots=True)
class DamageNumber:
    """Floating text showing damage dealt. Spawned with a Lifetime (when it
    fades) and a Drift (how it moves)."""

    text: str
    color: tuple[int, int, int]
    size: int
    """Font size once any pop-in has settled."""
    critical: bool = False
    """Critical hits pop in larger and shrink to `size`."""
