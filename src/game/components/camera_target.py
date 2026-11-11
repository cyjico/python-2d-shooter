from dataclasses import dataclass


@dataclass(slots=True)
class CameraTarget:
    """Marks the entity the camera follows.

    Only one entity should have this at a time. If several do, the camera
    follows whichever the world returns first. To switch targets, remove this
    component from the old entity and add it to the new one.
    """

    smoothing: float = 8.0
    """Higher = tighter follow."""
