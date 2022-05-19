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


def test_module_non_recursive():
    import fake_module

    registry = Registry(recursive=False)
    registry(fake_module)
    assert list(registry) == ["bar2", "foo2"]
