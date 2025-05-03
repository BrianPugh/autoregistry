"""For test_registry_overwrite_no_key_collision_repeated_import()."""

from autoregistry import Registry


class MyRegistry(Registry):
    pass


class MyRegistryA(MyRegistry):
    pass
