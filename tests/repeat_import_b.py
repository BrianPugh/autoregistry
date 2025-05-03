"""For test_registry_overwrite_no_key_collision_repeated_import()."""

from repeat_import_a import MyRegistry, MyRegistryA


class MyRegistryB(MyRegistry):
    pass
