import math


def wrap_angle(angle: float):
    """Wrap to [-pi, pi] so we always turn the short way around."""
    return (angle + math.pi) % math.tau - math.pi
