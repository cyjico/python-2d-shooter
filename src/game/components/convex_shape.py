from dataclasses import dataclass


@dataclass(slots=True)
class ConvexShape:
    vertices: tuple[tuple[float, float], ...]
    """These are expected to be local to the entity's transform."""
    color: tuple[int, int, int] = (80, 200, 120)
    """From 0 to 255 in RGB format."""
