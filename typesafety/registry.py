"""Static type-safety assertions for ``Registry``.

These are checked by pyright, not executed at runtime. ``assert_type`` verifies
an expression's inferred type, and a ``# pyright: ignore`` comment asserts that
a static type error *is* expected on that line. This directory enables
``reportUnnecessaryTypeIgnoreComment`` (see ``[tool.pyright]`` in
``pyproject.toml``), so a negative assertion fails if its expected error ever
disappears.

A bare ``# pyright: ignore`` (no rule code) is used intentionally: the rule name
for that diagnostic varies across pyright versions.

``assert_type`` is imported from ``typing`` (3.11+) rather than
``typing_extensions``: this module is only ever analyzed by pyright (pytest does
not collect it), so the import is never executed and needs no runtime backport.
"""

from typing import Any, assert_type, cast

from autoregistry import Registry, RegistryDecorator


class Foo(Registry):
    pass


def test_subclass_instances_keep_their_type() -> None:
    # Instantiating a Registry subclass yields that subclass, not the internal
    # decorator type. This is the core guarantee of the typed public API.
    assert_type(Foo(), Foo)


def test_bare_registry_is_registry() -> None:
    assert_type(Registry(), Registry)


def test_decorator_interface_via_cast() -> None:
    registry = cast(RegistryDecorator, Registry())

    @registry
    def handler() -> None: ...

    # Registered lookups are intentionally ``Any``: a registry may hold
    # arbitrary classes or functions.
    assert_type(registry["handler"], Any)


def test_keys_must_be_strings() -> None:
    # Indexing with a non-str key is a static type error.
    Foo[None]  # pyright: ignore
