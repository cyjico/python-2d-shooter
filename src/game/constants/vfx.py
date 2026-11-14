"""Tuning for visual effects: sparks, gibs and the player's death."""

import math

# --- Sparks: a player bullet hitting something solid ---

SPARK_COUNT = (2, 3)
"""Random count per hit, inclusive."""
SPARK_CONE = math.radians(35)
"""Max angle either side of the cone's center. The cone points back the way
the bullet came, toward the player."""
SPARK_SPEED = (260.0, 480.0)
SPARK_LENGTH = (7.0, 13.0)
"""px, at spawn. Shrinks to nothing over the spark's life."""
SPARK_DURATION = (0.12, 0.22)
SPARK_DRAG = 6.0
SPARK_WIDTH = 2
SPARK_COLOR = (255, 230, 150)

# --- Gibs: an enemy dying ---

GIB_COUNT = (6, 9)
GIB_AREA = (0.04, 0.08)
"""Each gib's area as a fraction of the enemy's area (its bounding circle)."""
GIB_SPEED = (60.0, 170.0)
"""px/s. Short splatter; drag stops them quickly."""
GIB_DRAG = 5.0
GIB_SPIN = 6.0
"""Max radians per second either way."""
GIB_DURATION = (0.7, 1.1)
GIB_SHRINK_START = 0.6
GIB_DARKEN = 0.75
"""Gib color = enemy color x this."""

# --- Player death ---

SHAKE_DURATION = 1.0
"""Seconds of shaking before the player shatters."""
SHAKE_MAX_OFFSET = 7.0
"""px, reached at the very end of the shake."""
SHAKE_MAX_ROTATION = math.radians(14)
SHAKE_EASE_POWER = 3
"""Shake strength = (t / duration) ** power: slow start, violent end (ease in)."""

SHARD_SPLITS = 2
"""Each slice of the player is halved this many times: 5 sides -> 5 x 2^2 = 20 shards."""
SHARD_SPEED = (120.0, 320.0)
SHARD_DRAG = 2.0
SHARD_SPIN = 9.0
SHARD_DURATION = (1.6, 2.4)
SHARD_SHRINK_START = 0.7

STATS_DELAY = 3.0
"""Seconds between shattering and the run stats appearing."""
