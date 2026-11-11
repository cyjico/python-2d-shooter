from dataclasses import dataclass

from game.core_ecs.entity import Entity


@dataclass(slots=True)
class ButtonClicked:
    entity: Entity
    action: str
