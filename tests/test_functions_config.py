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
