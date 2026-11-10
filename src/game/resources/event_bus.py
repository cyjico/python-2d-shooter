from collections.abc import Sequence
from typing import cast


class EventBus:
    """Per-frame event buffer. Systems emit events; later systems read them."""

    def __init__(self):
        self._events: dict[type, list[object]] = {}

    def emit(self, event: object) -> None:
        self._events.setdefault(type(event), []).append(event)

    def read[E](self, event_type: type[E]) -> Sequence[E]:
        """Events of this type emitted so far this frame."""
        return cast(Sequence[E], tuple(self._events.get(event_type, ())))

    def clear(self) -> None:
        self._events.clear()
