from random import random

from autoregistry import Registry

pokeballs = Registry()


@pokeballs
def masterball(target):
    return 1.0


@pokeballs
def ultraball(target):
    return random() * 0.5 + 0.5


@pokeballs
def greatball(target):
    return random() * 0.75 + 0.25


@pokeballs
def pokeball(target):
    return random()


print()
for ball in ["pokeball", "greatball", "ultraball", "masterball"]:
    success_rate = pokeballs[ball](None)
    print(f"Ash used {ball} and had {success_rate=}")
print()
