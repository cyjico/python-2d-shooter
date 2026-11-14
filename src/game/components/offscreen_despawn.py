from dataclasses import dataclass


@dataclass(slots=True)
class OffscreenDespawn:
    """Destroys its entity once it has been out of the camera's view for
    `timeout` seconds in a row. Coming back into view restarts the count.

    This is not a death: no bounty, no splitting, no death events.
    """

    timeout: float
    """Seconds out of view before giving up."""
    relocate: bool = False
    """Instead of destroying it, move it to a fresh spot just off screen
    (e.g. wave enemies, which must all be killed to end the wave)."""

    # Runtime state
    offscreen_time: float = 0.0
