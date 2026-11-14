"""Splitter enemy tuning. Each tier splits into the next until the last one."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SplitterTier:
    """Static, shareable definition of one size of splitter."""

    health: float
    radius: float
    move_speed: float
    contact_damage: float
    bounty: int
    color: tuple[int, int, int]

    children: int = 0
    """How many offspring it leaves on death."""
    child_tier: SplitterTier | None = None
    """What the offspring are. `None` = does not split."""

    def __post_init__(self):
        if self.children < 0:
            raise ValueError("children must not be negative")
        if (self.children > 0) != (self.child_tier is not None):
            raise ValueError("children and child_tier must be set together")


LARGE_HEALTH = 80.0
MEDIUM_HEALTH_FRACTION = 0.25
"""Of the large one's health."""
SMALL_HEALTH_FRACTION = 0.5
"""Of the medium one's health."""

MEDIUM_HEALTH = LARGE_HEALTH * MEDIUM_HEALTH_FRACTION
SMALL_HEALTH = MEDIUM_HEALTH * SMALL_HEALTH_FRACTION

SPLITTER_SMALL = SplitterTier(
    health=SMALL_HEALTH,
    radius=9,
    move_speed=190,
    contact_damage=6,
    bounty=5,
    color=(215, 160, 245),
)

SPLITTER_MEDIUM = SplitterTier(
    health=MEDIUM_HEALTH,
    radius=14,
    move_speed=150,
    contact_damage=10,
    bounty=10,
    color=(190, 120, 235),
    children=2,
    child_tier=SPLITTER_SMALL,
)

SPLITTER_LARGE = SplitterTier(
    health=LARGE_HEALTH,
    radius=20,
    move_speed=120,
    contact_damage=15,
    bounty=30,
    color=(160, 80, 215),
    children=4,
    child_tier=SPLITTER_MEDIUM,
)
