import pytest

from autoregistry import Registry


def test_decorator_case_sensitive():
    registry = Registry(case_sensitive=True)

    @registry
    def foo():
        pass

    assert list(registry) == ["foo"]

    with pytest.raises(KeyError):
        registry["FOO"]


def test_decorator_called():
    registry = Registry(case_sensitive=True)

    @registry()
    def foo():
        pass

    assert list(registry) == ["foo"]


def test_decorator_called_name_override():
    registry = Registry(case_sensitive=True)

    @registry(name="bar")
    def foo():
        pass

    assert list(registry) == ["bar"]
    assert registry["bar"] == foo


def test_module_non_recursive():
    import fake_module

    registry = Registry(recursive=False)
    registry(fake_module)
    assert list(registry) == ["bar2", "foo2"]
