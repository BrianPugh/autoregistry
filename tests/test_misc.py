import pytest

import autoregistry
from autoregistry.regex import key_split, to_snake_case
from autoregistry.registry import _Registry


def test_to_snake():
    assert to_snake_case("FooBar") == "foo_bar"
    assert to_snake_case("foo_bar") == "foo_bar"
    assert to_snake_case("FOOBar") == "foo_bar"
    assert to_snake_case("fooBar") == "foo_bar"
    assert to_snake_case("fooBAR") == "foo_bar"
    assert to_snake_case("FOOBAR") == "foobar"
    assert to_snake_case("Foo_Bar") == "foo_bar"


def test_registry_config_update():
    config = autoregistry.RegistryConfig()
    config.update(
        {
            "suffix": "test",
            "not_valid_config_key": None,  # This should be ignored.
        }
    )

    assert config.suffix == "test"


def test_registry_config_cannot_derive_name():
    __registry__ = _Registry(autoregistry.RegistryConfig())
    foo = "foo"
    with pytest.raises(autoregistry.CannotDeriveNameError):
        __registry__.register(foo)


def test_key_split():
    assert key_split("foo") == [
        "foo",
    ]
    assert key_split("foo.") == ["foo", ""]
    assert key_split("foo/") == ["foo", ""]
    assert key_split("foo.bar") == ["foo", "bar"]
    assert key_split("foo.bar.") == ["foo", "bar", ""]
    assert key_split("foo/bar") == ["foo", "bar"]
    assert key_split("foo.bar/baz") == ["foo", "bar", "baz"]
