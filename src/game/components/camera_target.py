from dataclasses import dataclass


@dataclass(slots=True)
class CameraTarget:
    """Marks the entity the camera follows."""

    smoothing: float = 8.0
    """Higher = tighter follow."""
