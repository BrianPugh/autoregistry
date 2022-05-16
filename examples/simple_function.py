from autoregistry import Registry

pokeballs = Registry()


@pokeballs
def masterball(target):
    return 1.0


@pokeballs
def ultraball(target):
    return 0.5


@pokeballs
def greatball(target):
    return 0.3


@pokeballs
def pokeball(target):
    return 0.1


print("")
for ball in ["pokeball", "greatball", "ultraball", "masterball"]:
    success_rate = pokeballs[ball](None)
    print(f"Ash used {ball} and had {success_rate=}")
print("")
