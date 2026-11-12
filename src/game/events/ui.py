from dataclasses import dataclass

from game.core_ecs.entity import Entity


@dataclass(slots=True)
class ButtonClickedEvent:
    entity: Entity
    action: str
