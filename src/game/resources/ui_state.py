from dataclasses import dataclass

from game.core_ecs.entity import Entity


@dataclass(slots=True)
class UIState:
    hovered: Entity | None = None
    pressed: Entity | None = None
    is_pointer_over_ui: bool = False
    """Gameplay systems should check this before reacting to clicks (e.g. shooting)."""
