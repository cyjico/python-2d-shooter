from game.components.ai.charger import ChargerAI
from game.components.bounty import Bounty
from game.components.contact_damage import ContactDamage
from game.components.faction import Faction, Team
from game.components.health import Health
from game.components.loadout import Loadout
from game.components.mover import Mover
from game.components.offscreen_despawn import OffscreenDespawn
from game.components.wave_scaled import WaveScaled
from game.constants.enemy_spawning import GIVE_UP_TIME, wave_scaling
from game.core_ecs.entity import Entity
from game.core_ecs.world import World
from game.resources.enemy_director import EnemyDirector


def wave_scaling_system(world: World):
    """Makes new enemies as strong as the current wave, once each.

    A system rather than part of the prefabs, so offspring spawned mid-wave
    (splitters) are caught too, on the frame after they appear.
    """
    wave = world.get_resource(EnemyDirector).wave
    if wave < 1:
        return

    for entity, (faction,) in world.query(Faction):
        if not faction.team & Team.ENEMY or world.has_component(entity, WaveScaled):
            continue

        _scale(world, entity, wave)
        world.add_component(entity, WaveScaled(wave))
        # Every wave enemy has to die to end the wave, so stranded ones are
        # brought back instead of despawned.
        if not world.has_component(entity, OffscreenDespawn):
            world.add_component(entity, OffscreenDespawn(GIVE_UP_TIME, relocate=True))


def _scale(world: World, entity: Entity, wave: int):
    scaling = wave_scaling(wave)

    health = world.try_get_component(entity, Health)
    if health is not None:
        health.maximum *= scaling.health
        health.current *= scaling.health

    mover = world.try_get_component(entity, Mover)
    if mover is not None:
        mover.move_speed *= scaling.move_speed

    contact = world.try_get_component(entity, ContactDamage)
    if contact is not None:
        contact.amount *= scaling.damage

    charger = world.try_get_component(entity, ChargerAI)
    if charger is not None:
        charger.contact_damage *= scaling.damage

    loadout = world.try_get_component(entity, Loadout)
    if loadout is not None:
        loadout.damage_scale *= scaling.damage

    bounty = world.try_get_component(entity, Bounty)
    if bounty is not None:
        bounty.amount = round(bounty.amount * scaling.bounty)
