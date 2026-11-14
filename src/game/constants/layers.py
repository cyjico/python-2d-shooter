"""Draw order of shapes in the world. Lower draws first (underneath)."""

GIBS = -2
"""Enemy remains, splattered on the floor under everything."""
PROJECTILES = -1
"""Bullets spawn at the player's center, so they draw under the player."""
DEFAULT = 0
