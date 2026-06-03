from abc import abstractmethod
from dataclasses import dataclass
from typing import cast

from autoregistry import Registry, RegistryDecorator


def construct_pokemon_classes(**kwargs):
    @dataclass
    class Pokemon(Registry, **kwargs):  # type: ignore[reportGeneralTypeIssues]
        level: int
        hp: int

        @abstractmethod
        def attack(self, target) -> int:
            """Attack another Pokemon."""

    class Charmander(Pokemon):
        def attack(self, target):
            return 1

    class Pikachu(Pokemon):
        def attack(self, target) -> int:
            return 2

    class SurfingPikachu(Pikachu):
        def attack(self, target):
            return 3

    return Pokemon, Charmander, Pikachu, SurfingPikachu


def construct_functions(**kwargs):
    # ``Registry()`` is typed as ``Registry``; cast to the decorator interface
    # it returns at runtime so the ``@registry`` usage type-checks.
    registry = cast(RegistryDecorator, Registry(**kwargs))

    @registry
    def foo(x):
        return x

    @registry
    def bar(x):
        return x

    return registry, foo, bar
