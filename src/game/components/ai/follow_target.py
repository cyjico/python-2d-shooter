from dataclasses import dataclass

import pygame

from game.core_ecs.entity import Entity


@dataclass(slots=True)
class FollowTargetAI:
    target: Entity
