from abc import abstractmethod
from dataclasses import dataclass

from autoregistry import Registry


@dataclass
class Pokemon(Registry):
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


print("")
print(f"{len(Pokemon)} Pokemon registered:")
print(f"    {list(Pokemon.keys())}")
# By default, lookup is case-insensitive
charmander = Pokemon["cHaRmAnDer"](level=7, hp=31)
print(f"Created Pokemon: {charmander}")
print("")
