CRATE_INTERVAL = (120.0, 240.0)
"""Random seconds between crate spawns."""
CRATE_MAX_PER_SPOT = 2
"""Crate cap = this x the number of `C` tiles in the map."""

BOX_INTERVAL = (180.0, 300.0)
"""Random seconds between mystery box spawns."""
BOX_MAX_ALIVE = 2

SPAWN_CLEARANCE = 60.0
"""Min distance (px) between a spawn spot and any physics body or earlier spawn."""
SPAWN_RETRY = 5.0
"""Seconds before retrying when every spot was blocked."""
