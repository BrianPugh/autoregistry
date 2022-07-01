from abc import ABCMeta
from functools import partial
from inspect import isclass, ismodule
from pathlib import Path
from typing import Any, Callable, List, Optional, Union

from .config import RegistryConfig
from .exceptions import (
    CannotDeriveNameError,
    CannotRegisterPythonBuiltInError,
    KeyCollisionError,
    ModuleAliasError,
)


class _Registry(dict):
    """Unified container object for __registry__."""

    def __init__(self, config: RegistryConfig, name: Optional[str] = None):
        super().__init__()
        self.config = config
        self.name = name

        # These will be populated later
        self.cls: Any = None

    def register(
        self,
        obj: Any,
        name: Union[str, None] = None,
        aliases: Union[str, None, List[str]] = None,
        recursive: bool = False,
    ):
        """Register an object to a registry, subject to configuration.

        Parameters
        ----------
        obj: object
            object to store and attempt to auto-derive name from.
        name: str
            If provided, register ``obj`` to this name; overrides checks.
            If not provided, name will be auto-derived from ``obj`` via ``format``.
        aliases: Union[str, None, List[str]]
            If provided, also register ``obj`` to these strings.
            Not subject to configuration rules.
        recursive: bool
            Force register to immediate parent(s).
            Gets logical or'd with ``config.recursive``.
        """
        if name is None:
            try:
                name = str(obj.__name__)
            except AttributeError:
                raise CannotDeriveNameError(
                    f"Cannot derive name from a bare {type(obj)}."
                )
            name = self.config.format(name)

        if not self.config.overwrite and name in self:
            raise KeyCollisionError(f'"{name}" already registered to {self}')

        # Check if should register self
        if obj == self.cls:
            if self.config.register_self:
                self[name] = obj
        else:
            self[name] = obj

        # Register aliases
        if aliases is None:
            aliases = []
        elif isinstance(aliases, str):
            aliases = [aliases]

        for alias in aliases:
            if not self.config.overwrite and alias in self:
                raise KeyCollisionError(f'"{alias}" already registered to {self}')

            self[alias] = obj

        # Register to parents
        if (recursive or self.config.recursive) and self.cls is not None:
            for parent_cls in self.cls.__bases__:
                if parent_cls == Registry:
                    break

                try:
                    parent_registry = parent_cls.__registry__
                except AttributeError:
                    # Not a Registry object
                    continue
                parent_registry.register(obj, name=name, aliases=aliases)


class _DictMixin:
    """Dict-like methods for a registry-based class."""

    __registry__: _Registry

    def __getitem__(self, key: str):
        return self.__registry__.config.getitem(self.__registry__, key)

    def __iter__(self):
        for val in self.__registry__:
            yield val

    def __len__(self):
        return len(self.__registry__)

    def __contains__(self, key: str):
        try:
            self.__registry__.config.getitem(self.__registry__, key)
        except KeyError:
            return False
        return True

    def keys(self):
        return self.__registry__.keys()

    def values(self):
        return self.__registry__.values()

    def items(self):
        for item in self.__registry__.items():
            yield item

    def get(self, key: str, default=None):
        try:
            return self[key]
        except KeyError:
            pass
        if isinstance(default, str):
            return self[default]
        else:
            return default

    def clear(self):
        self.__registry__.clear()


class _RedirectMethod(object):
    """Dispatches call depending if it was called from a Class or an instance."""

    def __init__(self, obj_method, name):
        self.obj_method = obj_method
        self.cls_method = name

    def __get__(self, obj, cls):
        if obj is None:
            # invoked directly from Class
            def redirect(*args, **kwargs):
                return self.cls_method(cls, *args, **kwargs)

            return redirect
        else:
            # invoked from instance
            def redirect(*args, **kwargs):
                return self.obj_method(obj, *args, **kwargs)

            return redirect


class RegistryMeta(ABCMeta, _DictMixin):
    __registry__: _Registry

    def __new__(
        mcls,
        cls_name,
        bases,
        namespace,
        name: Union[str, None] = None,
        aliases: Union[str, None, List[str]] = None,
        skip: bool = False,
        **config,
    ):
        """Create Class Constructor.

        Parameters
        ----------
        name : str or None
            Register to given ``name`` and skip validation checks.
            Otherwise, auto-derive name.
        aliases : str or list or None
            Additionally, register this class under these string(s).
        skip : bool
            Do **not** register this class to the appropriate registry(s).
        """
        # Manipulate namespace instead of modifying attributes after calling __new__ so
        # that hooks like __init_subclass__ have appropriately set registry attributes.
        # Each subclass gets its own registry.
        try:
            Registry
        except NameError:
            # Should only happen the very first time that
            # Registry is being defined.
            namespace["__registry__"] = _Registry(RegistryConfig(**config))
            cls = super().__new__(mcls, cls_name, bases, namespace)
            return cls

        # Copy the nearest parent config, then update it with new params
        for parent_cls in bases:
            try:
                registry_config = parent_cls.__registry__.config.copy()
                break
            except AttributeError:
                pass
        else:
            raise Exception("Should never happen.")

        # Set __registry_name__ before updating __registry_config__, since a classes own name is
        # subject to it's parents configuration, not its own.
        if name is None:
            registry_name = registry_config.format(cls_name)
        else:
            registry_name = name

        registry_config.update(config)

        namespace["__registry__"] = _Registry(registry_config, name=registry_name)

        if namespace["__registry__"].config.redirect:
            for key in [
                "__getitem__",
                "__iter__",
                "__len__",
                "__contains__",
                "keys",
                "values",
                "items",
                "get",
                "clear",
            ]:
                if key in namespace and not isinstance(
                    namespace[key], (staticmethod, classmethod)
                ):
                    namespace[key] = _RedirectMethod(namespace[key], getattr(mcls, key))

        # We cannot defer class creation any further.
        # This will call hooks like __init_subclass__
        cls = super().__new__(mcls, cls_name, bases, namespace)
        cls.__registry__.cls = cls

        if skip:
            return cls

        # Register to root Registry
        if cls in Registry.__subclasses__():
            if cls_name == "RegistryDecorator":
                return cls

            Registry.__registry__.register(
                cls,
                name=cls.__registry__.name,
                aliases=aliases,
            )

        # Register to parent(s)
        cls.__registry__.register(
            cls,
            name=cls.__registry__.name,
            aliases=aliases,
            recursive=True,  # Always register to direct parents
        )

        return cls

    def __repr__(self):
        try:
            return f"<{self.__name__}: {list(self.__registry__.keys())}>"
        except Exception:
            return super().__repr__()


class Registry(metaclass=RegistryMeta):
    __call__: Callable
    __contains__: Callable
    __getitem__: Callable
    __iter__: Callable
    __len__: Callable
    clear: Callable
    get: Callable
    items: Callable
    keys: Callable
    values: Callable

    def __new__(cls, *args, **kwargs):
        if cls is Registry:
            # A Registry is being explicitly created for decorating
            return super().__new__(RegistryDecorator)
        else:
            # Registry is being subclassed
            return super().__new__(cls)


class RegistryDecorator(Registry, _DictMixin):
    __name__: str

    def __init__(self, objs=None, /, **config):
        """Create a Registry for decorating."""
        # overwrite the registry data so its independent
        # of the Registry object.
        self.__registry__ = _Registry(RegistryConfig(**config))

        if objs is None:
            objs = []
        elif not isinstance(objs, (tuple, list)):
            objs = [objs]

        for obj in objs:
            self(obj)

    def __call__(
        self,
        obj=None,
        /,
        *,
        name=None,
        aliases: Union[str, None, List[str]] = None,
    ):
        config = self.__registry__.config

        if obj is None:
            # Was called @my_registry(**config_params)
            # Maybe copy config and update and pass it through
            return partial(self.__call__, name=name, aliases=aliases)

        if not ismodule(obj):
            self.__registry__.register(obj, name=name, aliases=aliases)
            return obj

        if aliases:
            raise ModuleAliasError

        try:
            obj_file = obj.__file__
            assert obj_file is not None
        except (AttributeError, AssertionError):
            raise CannotRegisterPythonBuiltInError(
                f"Cannot register Python BuiltIn {obj}"
            )
        obj_folder = str(Path(obj_file).parent)
        # Skip private and magic attributes
        elem_names = [x for x in dir(obj) if not x.startswith("_")]
        for elem_name in elem_names:
            handle = getattr(obj, elem_name)
            if ismodule(handle):
                if not config.recursive:
                    continue
                try:
                    handle_file = handle.__file__
                    assert handle_file is not None
                except (AttributeError, AssertionError):
                    # handle is a python built-in
                    continue

                handle_folder = str(Path(handle_file).parent)
                if not handle_folder.startswith(obj_folder):
                    # Only traverse direct submodules
                    continue

                subregistry = RegistryDecorator(**config.asdict())
                subregistry(handle)
                self(subregistry, name=elem_name)
            else:
                self(handle, name=elem_name)

        return obj

    def __repr__(self):
        return f"<Registry: {list(self.__registry__.keys())}>"
