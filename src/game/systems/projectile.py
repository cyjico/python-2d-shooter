from game.components.breakable import Breakable
from game.components.convex_collider import ConvexCollider
from game.components.health import Health
from game.components.projectile import Projectile
from game.components.rigid_body import RigidBody
from game.components.transform import Transform
from game.core_ecs.entity import Entity
from game.core_ecs.world import World
from game.events.collision import CollisionEvent
from game.events.combat import DamageEvent
from game.resources.event_bus import EventBus


def projectile_system(world: World, dt: float):
    """Emits a DamageEvent. Run after collision_system."""
    events = world.get_resource(EventBus)

    for collision in events.read(CollisionEvent):
        _handle_hit(world, events, collision.entity_a, collision.entity_b)
        _handle_hit(world, events, collision.entity_b, collision.entity_a)

    for entity, (projectile,) in world.query(Projectile):
        projectile.lifetime -= dt
        if projectile.lifetime <= 0:
            world.destroy_entity(entity)


def _handle_hit(world: World, events: EventBus, bullet: Entity, other: Entity):
    projectile = world.try_get_component(bullet, Projectile)
    # Ensure entity was not destroyed.
    if projectile is None:
        return

    if other == projectile.owner or other in projectile.hit:
        return
    if world.has_component(other, Projectile):
        return

    # Triggers don't stop projectiles.
    collider = world.try_get_component(other, ConvexCollider)
    if collider is None or collider.is_trigger:
        return

    projectile.hit.add(other)

    if world.has_component(other, Health) or world.has_component(other, Breakable):
        events.emit(DamageEvent(other, projectile.damage, projectile.owner))

    _apply_knockback(world, bullet, projectile, other)

    if projectile.pierce_left > 0:
        projectile.pierce_left -= 1
    else:
        world.destroy_entity(bullet)


def _apply_knockback(
    world: World, bullet: Entity, projectile: Projectile, other: Entity
):
    if projectile.knockback <= 0:
        return

    target_body = world.try_get_component(other, RigidBody)
    bullet_body = world.try_get_component(bullet, RigidBody)
    if target_body is None or bullet_body is None or target_body.inverse_mass == 0:
        return
    if bullet_body.linear_velocity.length_squared() == 0:
        return

    bullet_pos = world.get_component(bullet, Transform).position
    target_transform = world.get_component(other, Transform)

    # Off-center hits spin the target.
    lever = bullet_pos - target_transform.apply(target_body.center_of_mass)
    impulse = bullet_body.linear_velocity.normalize() * projectile.knockback
    target_body.apply_impulse_at(lever, impulse)
