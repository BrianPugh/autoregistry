from abc import abstractmethod
from dataclasses import dataclass

from autoregistry import Registry


def construct_pokemon_classes(**kwargs):
    @dataclass
    class Pokemon(Registry, **kwargs):  # type: ignore
        level: int
        hp: int

        @abstractmethod
        def attack(self, target):
            """Attack another Pokemon."""

    class Charmander(Pokemon):
        def attack(self, target):
            return 1

    class Pikachu(Pokemon):
        def attack(self, target):
            return 2

    class SurfingPikachu(Pikachu):
        def attack(self, target):
            return 3

    return Pokemon, Charmander, Pikachu, SurfingPikachu


def construct_functions(**kwargs):
    registry = Registry(**kwargs)

    @registry
    def foo(x):
        return x

    @registry
    def bar(x):
        return x

    return registry, foo, bar
