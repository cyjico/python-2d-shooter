from dataclasses import dataclass


@dataclass(slots=True)
class Sandbox:
    """Sandbox mode: no waves, enemies come from the panel's buttons.
    Tuning lives in `systems.sandbox`."""

    level: int = 1
    """Enemies spawn as strong as this wave."""
    count_index: int = 0
    """Index into SPAWN_COUNTS: how many enemies one button press spawns."""
    collapsed: bool = False
    """The panel shows only its header."""
