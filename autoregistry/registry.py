from abc import ABCMeta
from functools import partial
from inspect import ismodule
from pathlib import Path
from typing import Callable, List, Union

from .config import RegistryConfig
from .exceptions import CannotRegisterPythonBuiltInError, ModuleAliasError


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
    __registry_name__: str

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
        namespace["__registry__"] = {}

        try:
            Registry
        except NameError:
            # Should only happen the very first time that
            # Registry is being defined.
            cls = super().__new__(mcls, cls_name, bases, namespace)
            cls.__registry_config__ = RegistryConfig(**config)
            return cls

        # Copy the nearest parent config, then update it with new params
        for parent_cls in bases:
            try:
                namespace["__registry_config__"] = parent_cls.__registry_config__.copy()
                break
            except AttributeError:
                pass

        # Set __registry_name__ before updating __registry_config__, since a classes own name is
        # subject to it's parents configuration, not its own.
        if name is None:
            namespace["__registry_name__"] = namespace["__registry_config__"].format(
                cls_name
            )
        else:
            namespace["__registry_name__"] = name

        namespace["__registry_config__"].update(config)

        # We cannot defer class creation any further.
        # This will call hooks like __init_subclass__
        cls = super().__new__(mcls, cls_name, bases, namespace)

        if skip:
            return cls

        # Register direct subclasses of Register to Register
        if cls in Registry.__subclasses__() and cls_name != "RegistryDecorator":
            Registry.__registry_config__.register(
                Registry.__registry__, cls, name=cls.__registry_name__
            )

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

            config.register(
                parent_cls.__registry__,
                cls,
                name=cls.__registry_name__,
                aliases=aliases,
            )  # type: ignore

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
        self.__registry__ = {}
        self.__registry_config__ = RegistryConfig(**config)

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
        config = self.__registry_config__

        if obj is None:
            # Was called @my_registry(**config_params)
            # Maybe copy config and update and pass it through
            return partial(self.__call__, name=name, aliases=aliases)

        if not ismodule(obj):
            config.register(self.__registry__, obj, name=name, aliases=aliases)
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
