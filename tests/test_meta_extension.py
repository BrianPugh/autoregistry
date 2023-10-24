from autoregistry import RegistryMeta


class ExtendedRegistryMeta(RegistryMeta):
    def __call__(cls, *args, **kwargs):  # noqa: N805
        out = super().__call__(*args, **kwargs)
        out.extended_attribute = cls.__name__
        return out


class Foo(metaclass=ExtendedRegistryMeta):
    pass


class Bar(Foo):
    pass


def test_extended_registry():
    foo = Foo()
    bar = Bar()

    assert foo.extended_attribute == "Foo"  # pyright: ignore[reportGeneralTypeIssues]
    assert bar.extended_attribute == "Bar"  # pyright: ignore[reportGeneralTypeIssues]

    assert list(Foo) == ["bar"]
