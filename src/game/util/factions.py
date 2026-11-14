from game.components.faction import Faction, Team
from game.core_ecs.entity import Entity
from game.core_ecs.world import World


def team_of(world: World, entity: Entity):
    """The entity's team, or `None` if it is neutral."""
    faction = world.try_get_component(entity, Faction)
    return Team.NONE if faction is None else faction.team


def is_hostile(world: World, a: Entity, b: Entity):
    """True if both are on a team and the teams differ. Neutrals are hostile to no one."""
    team_a, team_b = team_of(world, a), team_of(world, b)
    return team_a and team_b and not (team_a & team_b)
