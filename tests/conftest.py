import pytest

from autoregistry import Registry


@pytest.fixture(autouse=True)
def clear_registry():
    # Code that will run before your test, for example:
    Registry.clear()

    # A test function will be run at this point
    yield

    # Code that will run after your test, for example:
    Registry.clear()
