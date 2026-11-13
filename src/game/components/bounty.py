from dataclasses import dataclass


@dataclass(slots=True)
class Bounty:
    """Money paid to whoever kills this entity (before multipliers)."""

    amount: int
