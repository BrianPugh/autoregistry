"""
Tests for module re-import scenarios.

These tests address: https://github.com/BrianPugh/belay/issues/181

When a module containing a Registry subclass is imported multiple times
(e.g., via importlib.util.module_from_spec with different module names),
the class definition is executed multiple times. Each execution creates
a new class object that attempts to register to the parent registry.

The _is_reimport() function detects this scenario by checking if both
classes come from the same source file, allowing the re-import to
silently update the registry reference.
"""
import sys
import textwrap
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from autoregistry import KeyCollisionError
from autoregistry._registry import _is_reimport


def load_module_from_file(file_path: Path, module_name: str):
    """Load a Python module from a file path.

    Uses manual compile/exec to avoid Python's loader caching,
    which would otherwise return stale bytecode when the same
    file path is loaded multiple times with modifications.
    """
    import types

    source = file_path.read_text()
    code = compile(source, str(file_path), "exec")

    module = types.ModuleType(module_name)
    module.__file__ = str(file_path)
    module.__loader__ = None
    sys.modules[module_name] = module
    exec(code, module.__dict__)
    return module


# ------------------------------------------------------------------------------
# Tests for _is_reimport() helper function
# ------------------------------------------------------------------------------


def test_is_reimport_same_object():
    """Same object has same __module__, so it's not a reimport."""

    class MyClass:
        pass

    # Same object = same __module__, not a reimport
    assert _is_reimport(MyClass, MyClass) is False


def test_is_reimport_same_module():
    """Two classes in the same module are not reimports (same __module__)."""

    class ClassA:
        pass

    class ClassB:
        pass

    # Even with same name, same __module__ means not a reimport
    ClassB.__name__ = "ClassA"
    ClassB.__qualname__ = "ClassA"
    assert _is_reimport(ClassA, ClassB) is False


def test_is_reimport_different_names():
    """Classes with different names are not reimports."""

    class ClassA:
        pass

    class ClassB:
        pass

    assert _is_reimport(ClassA, ClassB) is False


def test_is_reimport_non_classes():
    """Non-class objects (that aren't functions) are not reimports."""
    assert _is_reimport("string", "string") is False
    assert _is_reimport(123, 456) is False


def test_is_reimport_different_qualnames():
    """Classes with different qualnames are not reimports."""

    class Outer1:
        class Inner:
            pass

    class Outer2:
        class Inner:
            pass

    # Both have __name__ == "Inner" but different __qualname__
    assert Outer1.Inner.__name__ == Outer2.Inner.__name__
    assert Outer1.Inner.__qualname__ != Outer2.Inner.__qualname__
    assert _is_reimport(Outer1.Inner, Outer2.Inner) is False


def test_is_reimport_getfile_failure():
    """When inspect.getfile fails, objects are not considered reimports."""
    import types

    class ClassA:
        pass

    class ClassB:
        pass

    # Make them look like reimport candidates
    ClassB.__name__ = ClassA.__name__
    ClassB.__qualname__ = ClassA.__qualname__
    ClassB.__module__ = "different_module"

    # Mock __file__ removal to simulate built-in-like behavior
    # inspect.getfile will raise TypeError for objects without source
    original_module = ClassA.__module__

    # Create a class that will fail getfile by removing module from sys.modules
    # and clearing __file__ references
    fake_module = types.ModuleType("fake_module_no_file")
    # Don't set __file__ attribute - this causes TypeError in inspect.getfile
    ClassA.__module__ = "fake_module_no_file"
    sys.modules["fake_module_no_file"] = fake_module

    try:
        # Should return False because getfile will fail
        assert _is_reimport(ClassA, ClassB) is False
    finally:
        ClassA.__module__ = original_module
        del sys.modules["fake_module_no_file"]


def test_is_reimport_lambdas_same_scope():
    """Multiple lambdas in same scope are not false-positive reimports.

    Lambdas in the same scope have identical __name__ and __qualname__,
    but they share the same __module__, so they're correctly identified
    as different definitions (not reimports).
    """
    lambda1 = lambda: 1  # noqa: E731
    lambda2 = lambda: 2  # noqa: E731

    # Both have same __name__ and __qualname__
    assert lambda1.__name__ == lambda2.__name__ == "<lambda>"
    assert lambda1.__qualname__ == lambda2.__qualname__

    # But same __module__ means they're from the same execution context
    assert lambda1.__module__ == lambda2.__module__

    # So they're NOT considered reimports (same module = collision, not reimport)
    assert _is_reimport(lambda1, lambda2) is False


# ------------------------------------------------------------------------------
# Tests for reimport behavior in Registry
# ------------------------------------------------------------------------------


def test_reimport_same_file_succeeds():
    """Importing the same file with different module names should succeed."""
    with TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        device_file = tmpdir / "my_device.py"
        device_file.write_text(
            textwrap.dedent(
                """
            from test_base import Device

            class MyDevice(Device):
                pass
            """
            ).strip()
        )

        base_file = tmpdir / "test_base.py"
        base_file.write_text(
            textwrap.dedent(
                """
            from autoregistry import Registry

            class Device(Registry):
                pass
            """
            ).strip()
        )

        old_path = sys.path.copy()
        sys.path.insert(0, str(tmpdir))

        try:
            # First import
            module1 = load_module_from_file(device_file, "my_device_v1")
            cls1 = module1.MyDevice
            assert "mydevice" in module1.Device

            # Second import - should succeed (re-import detected)
            module2 = load_module_from_file(device_file, "my_device_v2")
            cls2 = module2.MyDevice

            # Classes are different objects
            assert cls1 is not cls2

            # Registry should point to the new class
            assert module2.Device["mydevice"] is cls2

        finally:
            sys.path = old_path
            for mod_name in list(sys.modules.keys()):
                if mod_name.startswith(("my_device", "test_base")):
                    del sys.modules[mod_name]


def test_reimport_modified_file_succeeds():
    """Re-importing after modifying the file should succeed (hot-reload)."""
    with TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        device_file = tmpdir / "my_device.py"
        base_file = tmpdir / "test_base.py"

        base_file.write_text(
            textwrap.dedent(
                """
            from autoregistry import Registry

            class Device(Registry):
                pass
            """
            ).strip()
        )

        # Version 1: Simple class
        device_file.write_text(
            textwrap.dedent(
                """
            from test_base import Device

            class MyDevice(Device):
                version = 1
            """
            ).strip()
        )

        old_path = sys.path.copy()
        sys.path.insert(0, str(tmpdir))

        try:
            # First import
            module1 = load_module_from_file(device_file, "my_device_v1")
            cls1 = module1.MyDevice
            assert cls1.version == 1

            # Modify the file (hot reload scenario)
            device_file.write_text(
                textwrap.dedent(
                    """
                from test_base import Device

                class MyDevice(Device):
                    version = 2

                    def new_method(self):
                        return 42
                """
                ).strip()
            )

            # Second import - should succeed
            module2 = load_module_from_file(device_file, "my_device_v2")
            cls2 = module2.MyDevice

            # New class has updated implementation
            assert cls2.version == 2
            assert hasattr(cls2, "new_method")

            # Registry points to new class
            assert module2.Device["mydevice"] is cls2

        finally:
            sys.path = old_path
            for mod_name in list(sys.modules.keys()):
                if mod_name.startswith(("my_device", "test_base")):
                    del sys.modules[mod_name]


def test_reimport_genuine_collision_raises_error():
    """Two different classes with the same name from different files should raise."""
    with TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        base_file = tmpdir / "test_base.py"
        base_file.write_text(
            textwrap.dedent(
                """
            from autoregistry import Registry

            class Device(Registry):
                pass
            """
            ).strip()
        )

        # Two different files with same class name
        device_file_a = tmpdir / "device_a.py"
        device_file_a.write_text(
            textwrap.dedent(
                """
            from test_base import Device

            class MyDevice(Device):
                source = "file_a"
            """
            ).strip()
        )

        device_file_b = tmpdir / "device_b.py"
        device_file_b.write_text(
            textwrap.dedent(
                """
            from test_base import Device

            class MyDevice(Device):
                source = "file_b"
            """
            ).strip()
        )

        old_path = sys.path.copy()
        sys.path.insert(0, str(tmpdir))

        try:
            # First import from file A
            module_a = load_module_from_file(device_file_a, "device_a")
            assert module_a.MyDevice.source == "file_a"

            # Second import from file B - should raise KeyCollisionError
            with pytest.raises(KeyCollisionError, match="mydevice"):
                load_module_from_file(device_file_b, "device_b")

        finally:
            sys.path = old_path
            for mod_name in list(sys.modules.keys()):
                if mod_name.startswith(("device_", "test_base")):
                    del sys.modules[mod_name]


def test_reimport_overwrite_true_still_works():
    """Setting overwrite=True should still work as before."""
    with TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        base_file = tmpdir / "test_base.py"
        base_file.write_text(
            textwrap.dedent(
                """
            from autoregistry import Registry

            class Device(Registry, overwrite=True):
                pass
            """
            ).strip()
        )

        device_file_a = tmpdir / "device_a.py"
        device_file_a.write_text(
            textwrap.dedent(
                """
            from test_base import Device

            class MyDevice(Device):
                source = "file_a"
            """
            ).strip()
        )

        device_file_b = tmpdir / "device_b.py"
        device_file_b.write_text(
            textwrap.dedent(
                """
            from test_base import Device

            class MyDevice(Device):
                source = "file_b"
            """
            ).strip()
        )

        old_path = sys.path.copy()
        sys.path.insert(0, str(tmpdir))

        try:
            # First import from file A
            load_module_from_file(device_file_a, "device_a")

            # Second import from file B - should succeed with overwrite=True
            module_b = load_module_from_file(device_file_b, "device_b")

            # Registry should point to class from file B
            assert module_b.Device["mydevice"].source == "file_b"

        finally:
            sys.path = old_path
            for mod_name in list(sys.modules.keys()):
                if mod_name.startswith(("device_", "test_base")):
                    del sys.modules[mod_name]


def test_reimport_function_succeeds():
    """Re-importing a module with decorated functions should succeed."""
    with TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        registry_file = tmpdir / "my_registry.py"
        registry_file.write_text(
            textwrap.dedent(
                """
            from autoregistry import Registry

            handlers = Registry()
            """
            ).strip()
        )

        handlers_file = tmpdir / "handlers.py"
        handlers_file.write_text(
            textwrap.dedent(
                """
            from my_registry import handlers

            @handlers
            def process():
                return "v1"
            """
            ).strip()
        )

        old_path = sys.path.copy()
        sys.path.insert(0, str(tmpdir))

        try:
            # First import
            module1 = load_module_from_file(handlers_file, "handlers_v1")
            func1 = module1.process
            assert "process" in module1.handlers
            assert module1.handlers["process"]() == "v1"

            # Modify the file (hot reload scenario)
            handlers_file.write_text(
                textwrap.dedent(
                    """
                from my_registry import handlers

                @handlers
                def process():
                    return "v2"
                """
                ).strip()
            )

            # Second import - should succeed (re-import detected)
            module2 = load_module_from_file(handlers_file, "handlers_v2")
            func2 = module2.process

            # Functions are different objects
            assert func1 is not func2

            # Registry should point to the new function
            assert module2.handlers["process"]() == "v2"

        finally:
            sys.path = old_path
            for mod_name in list(sys.modules.keys()):
                if mod_name.startswith(("handlers", "my_registry")):
                    del sys.modules[mod_name]
