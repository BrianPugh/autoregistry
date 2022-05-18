import autoregistry
import autoregistry.regex


def test_to_snake():
    convert = autoregistry.regex.to_snake_case
    assert convert("FooBar") == "foo_bar"
    assert convert("foo_bar") == "foo_bar"
    assert convert("FOOBar") == "foo_bar"
    assert convert("fooBar") == "foo_bar"
    assert convert("fooBAR") == "foo_bar"
    assert convert("FOOBAR") == "foobar"
    assert convert("Foo_Bar") == "foo_bar"


def test_registry_config_update():
    config = autoregistry.RegistryConfig()
    config.update(
        {
            "suffix": "test",
            "not_valid_config_key": None,  # This should be ignored.
        }
    )

    assert config.suffix == "test"
