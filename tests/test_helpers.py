import autoregistry


def test_to_snake():
    convert = autoregistry.config.to_snake_case
    assert convert("FooBar") == "foo_bar"
    assert convert("foo_bar") == "foo_bar"
    assert convert("FOOBar") == "foo_bar"
    assert convert("fooBar") == "foo_bar"
    assert convert("fooBAR") == "foo_bar"
    assert convert("FOOBAR") == "foobar"
    assert convert("Foo_Bar") == "foo_bar"
