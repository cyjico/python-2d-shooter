"""The player's death: shake harder and harder, shatter, then wait for the stats."""

import random
from dataclasses import dataclass

import pygame

from game.components.faction import Team
from game.components.transform import Transform
from game.constants import vfx
from game.core_ecs.entity import Entity
from game.core_ecs.world import World
from game.events.combat import EntityDiedEvent
from game.resources.event_bus import EventBus
from game.resources.run_stats import RunStats
from game.systems.vfx import shatter
from game.util.factions import team_of
from game.util.rng import resolve_rng


@dataclass(slots=True)
class DeathSequence:
    """Resource added when the player dies."""

    player: Entity
    origin: pygame.Vector2
    """Where the player died. The shake is centered here."""
    rotation: float
    elapsed: float = 0.0
    shattered: bool = False

    @property
    def finished(self):
        """True once the stats should be shown."""
        return self.elapsed >= vfx.SHAKE_DURATION + vfx.STATS_DELAY


def start_death_sequence(world: World, player: Entity):
    transform = world.get_component(player, Transform)
    world.add_resource(
        DeathSequence(player, pygame.Vector2(transform.position), transform.rotation)
    )


def death_sequence_system(world: World, dt: float, rng: random.Random | None = None):
    rng = resolve_rng(rng)
    seq = world.get_resource(DeathSequence)
    seq.elapsed += dt

    if seq.shattered:
        return

    transform = world.get_component(seq.player, Transform)
    if seq.elapsed >= vfx.SHAKE_DURATION:
        transform.position = pygame.Vector2(seq.origin)
        transform.rotation = seq.rotation
        shatter(world, seq.player, rng)
        seq.shattered = True
        return

    # Ease in: barely moving at first, violent right before it breaks.
    strength = (seq.elapsed / vfx.SHAKE_DURATION) ** vfx.SHAKE_EASE_POWER
    offset = pygame.Vector2(rng.uniform(-1, 1), rng.uniform(-1, 1))
    transform.position = seq.origin + offset * vfx.SHAKE_MAX_OFFSET * strength
    transform.rotation = (
        seq.rotation + rng.uniform(-1, 1) * vfx.SHAKE_MAX_ROTATION * strength
    )


def run_stats_system(world: World):
    """Counts enemy deaths for the run stats."""
    stats = world.get_resource(RunStats)
    for died in world.get_resource(EventBus).read(EntityDiedEvent):
        if team_of(world, died.entity) & Team.ENEMY:
            stats.enemies_killed += 1
