from collections.abc import Iterator
from typing import Any, TypeVar, cast, overload

from .entity import Entity


class World:
    def __init__(self):
        self._next_entity = 0
        self._entities: set[Entity] = set()
        self._components: dict[type, dict[Entity, object]] = {}
        """`component type` -> [`entity id` -> `component instance`]."""

        self._resources: dict[type, object] = {}

    def create_entity(self, *components) -> Entity:
        entity = self._next_entity
        self._next_entity += 1

        self._entities.add(entity)

        for component in components:
            self.add_component(entity, component)

        return entity

    def destroy_entity(self, entity: Entity):
        self._entities.remove(entity)

        for pool in self._components.values():
            pool.pop(entity, None)

    def is_alive(self, entity: Entity) -> bool:
        return entity in self._entities

    def add_component(self, entity: Entity, component):
        if entity not in self._entities:
            raise KeyError(f"Entity {entity} does not exist")

        component_type = type(component)

        if component_type not in self._components:
            self._components[component_type] = {}

        self._components[component_type][entity] = component

    def remove_component[C](self, entity: Entity, component_type: type[C]) -> C:
        pool = self._components.get(component_type)

        if pool is None or entity not in pool:
            raise KeyError(f"Entity {entity} does not have {component_type.__name__}")

        return cast(C, pool.pop(entity))

    def get_component[C](self, entity: Entity, component_type: type[C]) -> C:
        return cast(C, self._components[component_type][entity])

    def has_component[C](self, entity: Entity, component_type: type[C]):
        return entity in self._components.get(component_type, {})

    def try_get_component[C](self, entity: Entity, component_type: type[C]) -> C | None:
        pool = self._components.get(component_type)

        if pool is None or entity not in pool:
            return None

        return cast(C, pool[entity])

    @overload
    def query[C1](self, c1: type[C1], /) -> Iterator[tuple[Entity, tuple[C1]]]: ...

    @overload
    def query[C1, C2](
        self, c1: type[C1], c2: type[C2], /
    ) -> Iterator[tuple[Entity, tuple[C1, C2]]]: ...

    @overload
    def query[C1, C2, C3](
        self, c1: type[C1], c2: type[C2], c3: type[C3], /
    ) -> Iterator[tuple[Entity, tuple[C1, C2, C3]]]: ...

    @overload
    def query[C1, C2, C3, C4](
        self, c1: type[C1], c2: type[C2], c3: type[C3], c4: type[C4], /
    ) -> Iterator[tuple[Entity, tuple[C1, C2, C3, C4]]]: ...

    def query(
        self, *component_types: type[Any]
    ) -> Iterator[tuple[Entity, tuple[Any, ...]]]:
        """Queries the components of entities that have all of components listed.

        It is *RECCOMENDED* to query only for a single component, if possible,
        for performance reasons.
        """
        if not component_types:
            return

        first_pool = self._components.get(component_types[0])

        if first_pool is None:
            return

        for entity, first_component in tuple(first_pool.items()):
            components = [first_component]

            for component_type in component_types[1:]:
                pool = self._components.get(component_type, {})

                if entity not in pool:
                    break

                components.append(pool[entity])
            else:
                yield entity, tuple(components)

    def add_resource(self, resource):
        self._resources[type(resource)] = resource

    def get_resource[T](self, resource_type: type[T]) -> T:
        try:
            return cast(T, self._resources[resource_type])
        except KeyError:
            raise KeyError(f"Resource {resource_type.__name__} not found")
