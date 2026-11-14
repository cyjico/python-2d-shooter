from dataclasses import dataclass, field


@dataclass(slots=True)
class HoverAroundTargetAI:
    preferred_dist: float = 220.0
    """Distance from the target the AI tries to hold."""
    dist_tolerance: float = 40.0
    """Strafe while within preferred +/- this."""

    near_dist_sqr: float = field(init=False)
    """Squared inner edge of the strafe band. Computed once."""
    far_dist_sqr: float = field(init=False)
    """Squared outer edge of the strafe band. Computed once."""

    # Runtime state
    strafing: bool = False
    strafe_side: int = 1

    def __post_init__(self):
        self.near_dist_sqr = max(0.0, self.preferred_dist - self.dist_tolerance) ** 2
        self.far_dist_sqr = (self.preferred_dist + self.dist_tolerance) ** 2
