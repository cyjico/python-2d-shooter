from dataclasses import dataclass, field

from game.core_ecs.entity import Entity


@dataclass(slots=True)
class UIState:
    hovered: Entity | None = None
    pressed: Entity | None = None
    is_pointer_over_ui: bool = False
    """Gameplay systems should check this before reacting to clicks (e.g. shooting)."""
    input_blockers: set[str] = field(default_factory=set)
    """Owners of open menus that capture input. Don't edit directly; use
    `block_gameplay_input` / `release_gameplay_input`."""

    @property
    def blocks_gameplay_input(self):
        """True while any menu owns the keyboard and mouse. Gameplay systems
        (movement, weapons, dash, interaction) should do nothing while this is set."""
        return bool(self.input_blockers)

    def block_gameplay_input(self, owner: str):
        """Safe to call repeatedly. `owner` must be released by the same key."""
        self.input_blockers.add(owner)

    def release_gameplay_input(self, owner: str):
        """Does nothing if `owner` isn't blocking."""
        self.input_blockers.discard(owner)
