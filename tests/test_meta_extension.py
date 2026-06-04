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

    foo_attr = foo.extended_attribute  # pyright: ignore[reportAttributeAccessIssue]
    bar_attr = bar.extended_attribute  # pyright: ignore[reportAttributeAccessIssue]
    assert foo_attr == "Foo"
    assert bar_attr == "Bar"

    assert list(Foo) == ["bar"]
