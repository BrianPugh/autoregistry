from autoregistry import RegistryMeta


class ExtendedRegistryMeta(RegistryMeta):
    def __init__(cls, name, bases, dct):  # noqa: N805
        super().__init__(name, bases, dct)
        cls.extended_attribute = name


class Foo(metaclass=ExtendedRegistryMeta):
    pass


class Bar(Foo):
    pass


def test_extended_registry():
    assert Foo.extended_attribute == "Foo"
    assert Bar.extended_attribute == "Bar"

    assert list(Foo) == ["bar"]
