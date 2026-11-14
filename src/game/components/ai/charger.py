import random
from dataclasses import dataclass, field
from enum import Enum, auto

import pygame

from game.components.ai.hover_around_target import HoverAroundTargetAI


class ChargerAIState(Enum):
    HOVER = auto()
    WINDUP = auto()
    CHARGE = auto()
    STUNNED = auto()


@dataclass(slots=True)
class ChargerAI:
    hover_time: tuple[float, float] = (4.0, 5.0)
    """Random seconds spent in range before winding up."""
    windup_time: float = 2
    charge_speed: float = 600.0
    charge_acceleration: float = 4000.0
    charge_distance_sqr: float = 400.0**2
    """Maximum charge distance."""
    stun_time: float = 3.0

    contact_damage: float = 20.0

    base_color: tuple[int, int, int] = (230, 150, 40)
    windup_color: tuple[int, int, int] = (255, 40, 40)
    stunned_color: tuple[int, int, int] = (110, 110, 130)

    # Runtime state
    hover_behavior: HoverAroundTargetAI | None = None
    """Store for hover component."""
    state: ChargerAIState = ChargerAIState.HOVER
    timer: float = 0.0
    charge_origin: pygame.Vector2 = field(default_factory=pygame.Vector2)

    normal_stats: tuple[float, float, float] | None = None
    """(`move_speed`, `move_accel`, `turn_speed`) saved while the charger isn't
    hovering."""

    def __post_init__(self):
        self.timer = random.uniform(*self.hover_time)
