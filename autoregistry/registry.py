from abc import ABCMeta
from copy import copy
from inspect import ismodule
from pathlib import Path
from typing import Callable, Union

from .config import RegistryConfig
from .exceptions import CannotRegisterPythonBuiltInError


class _DictMixin:
    """Dict-like methods for a registry-based class."""

    __registry__: dict
    __registry_config__: RegistryConfig

    def __getitem__(self, key: str):
        return self.__registry_config__.getitem(self.__registry__, key)

    def __iter__(self):
        for val in self.__registry__:
            yield val

    def __len__(self):
        return len(self.__registry__)

    def __contains__(self, key: str):
        try:
            self.__registry_config__.getitem(self.__registry__, key)
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


class RegistryMeta(ABCMeta, _DictMixin):
    __registry__: dict
    __registry_config__: RegistryConfig

    def __new__(mcls, name, bases, namespace, **config):
        cls = super().__new__(mcls, name, bases, namespace)

        # Each subclass gets its own registry.
        cls.__registry__ = {}

        try:
            Registry
        except NameError:
            # Should only happen the very first time that
            # Registry is being defined.
            cls.__registry_config__ = RegistryConfig(**config)
            return cls

        # Copy the nearest parent config, then update it with new params
        for parent_cls in cls.mro()[1:]:
            try:
                cls.__registry_config__ = copy(parent_cls.__registry_config__)  # type: ignore
                cls.__registry_config__.update(config)
                break
            except AttributeError:
                pass

        # Register direct subclasses of Register to Register
        if cls in Registry.__subclasses__() and name != "RegistryDecorator":
            Registry.__registry_config__.register(Registry.__registry__, cls)

        # otherwise, register it in own registry and all parent registries.
        for parent_cls in cls.mro():
            if parent_cls == Registry:
                continue

            if (
                not cls.__registry_config__.recursive
                and cls not in parent_cls.__subclasses__()
            ):
                continue

            try:
                config = parent_cls.__registry_config__  # type: ignore
            except AttributeError:
                # Not a Registry object
                continue

            if not config.register_self and parent_cls == cls:
                continue

            config.register(parent_cls.__registry__, cls)  # type: ignore

        return cls

    def __repr__(self):
        return f"<{self.__name__}: {list(self.keys())}>"


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
        self.__registry__ = {}
        self.__registry_config__ = RegistryConfig(**config)

        if objs is None:
            objs = []
        elif not isinstance(objs, (tuple, list)):
            objs = [objs]

        for obj in objs:
            self(obj)

    def __call__(self, obj, name=None):
        config = self.__registry_config__
        if ismodule(obj):
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

                    subregistry = RegistryDecorator()
                    subregistry(handle)
                    self(subregistry, elem_name)
                else:
                    self(handle, elem_name)
        else:
            config.register(self.__registry__, obj, name=name)
        return obj

    def __repr__(self):
        return f"<Registry: {list(self.__registry__.keys())}>"
