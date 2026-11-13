from dataclasses import dataclass


@dataclass(slots=True)
class BuffDrop:
    """When this entity is broken, its breaker gets a random buff."""
