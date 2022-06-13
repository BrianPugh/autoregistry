import pytest

from autoregistry import Registry
from autoregistry.exceptions import InvalidNameError, KeyCollisionError


def test_decorator_case_sensitive():
    registry = Registry(case_sensitive=True)

    @registry
    def foo():
        pass

    assert list(registry) == ["foo"]

    with pytest.raises(KeyError):
        registry["FOO"]


def test_decorator_called():
    registry = Registry()

    @registry()
    def foo():
        pass

    assert list(registry) == ["foo"]


def test_decorator_invalid_name():
    registry = Registry(suffix="_baz")

    with pytest.raises(InvalidNameError):

        @registry
        def foo():
            pass


def test_decorator_called_name_override():
    registry = Registry()

    @registry(name="bar")
    def foo():
        pass

    assert list(registry) == ["bar"]
    assert registry["bar"] == foo


def test_decorator_called_name_override_dont_follow_rules():
    registry = Registry(suffix="_baz")

    # "bar" doesn't end with "_baz"
    @registry(name="bar")
    def foo_baz():
        pass

    assert list(registry) == ["bar"]
    assert registry["bar"] == foo_baz


def test_decorator_called_aliases_str():
    registry = Registry()

    @registry(aliases="bar")
    def foo():
        pass

    assert list(registry) == ["foo", "bar"]
    assert registry["bar"] == registry["foo"] == foo


def test_decorator_called_aliases_str_dont_follow_rules():
    registry = Registry(suffix="_baz")

    @registry
    def foo_baz():
        pass

    # "bop" doesn't end with "_baz"
    @registry(aliases="bop")
    def bar_baz():
        pass

    assert list(registry) == ["foo", "bar", "bop"]
    assert registry["bar"] == registry["bop"] == bar_baz


def test_decorator_called_aliases_list():
    registry = Registry()

    @registry(aliases=["bar", "baz"])
    def foo():
        pass

    assert list(registry) == ["foo", "bar", "baz"]
    assert registry["bar"] == registry["foo"] == registry["baz"] == foo


def test_decorator_aliases_collision():
    registry = Registry()

    @registry
    def bar():
        pass

    with pytest.raises(KeyCollisionError):

        @registry(aliases="bar")
        def foo():
            pass


def test_decorator_aliases_overwrite():
    registry = Registry(overwrite=True)

    @registry
    def bar():
        pass

    @registry(aliases="bar")
    def foo():
        pass

    assert list(registry) == ["bar", "foo"]
    assert registry["bar"] == registry["foo"] == foo


def test_module_non_recursive():
    import fake_module

    registry = Registry(recursive=False)
    registry(fake_module)
    assert list(registry) == ["bar2", "foo2"]
