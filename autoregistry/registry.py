from abc import ABCMeta
from copy import copy
from typing import Callable

from .config import RegistryConfig


class _DictMixin:
    """Dict-like methods for a registry-based class."""

    __registry__: dict
    __registry_config__: RegistryConfig

    def __getitem__(self, key: str):
        return self.__registry_config__.getitem(self.__registry__, key)

    def __len__(self):
        return len(self.__registry__)

    def __contains__(self, val: str):
        val = self.__registry_config__.format(val)
        return val in self.__registry__

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
        if cls in Registry.__subclasses__():
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
    __call__: Callable  # For decorating
    __getitem__: Callable
    __len__: Callable
    __contains__: Callable
    keys: Callable
    values: Callable
    items: Callable

    def __new__(cls, *args, **kwargs):
        if cls is Registry:
            # A Registry is being explicitly created for decorating
            return super().__new__(RegistryDecorator, *args, **kwargs)
        else:
            # Registry is being subclassed
            return super().__new__(cls)


class RegistryDecorator(Registry, _DictMixin):
    def __init__(self, /, **config):
        """Create a Registry for decorating."""
        # overwrite the registry datas so its independent
        # of the Registry object.
        self.__registry__ = {}
        self.__registry_config__ = RegistryConfig(**config)

    def __call__(self, obj):
        """For decorator."""
        self.__registry_config__.register(self.__registry__, obj)
        return obj

    def __repr__(self):
        return f"<{type(self).__name__}: {list(self.__registry__.keys())}>"
