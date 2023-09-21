from abc import ABCMeta
from collections.abc import KeysView, ValuesView
from functools import partial
from inspect import ismodule
from pathlib import Path
from types import MethodType
from typing import Any, Callable, Generator, Iterable, Type, Union

from .config import RegistryConfig
from .exceptions import (
    CannotDeriveNameError,
    CannotRegisterPythonBuiltInError,
    InternalError,
    InvalidNameError,
    KeyCollisionError,
    ModuleAliasError,
)


class _Registry(dict):
    """Unified container object for __registry__."""

    def __init__(self, config: RegistryConfig, name: str = ""):
        super().__init__()
        self.config = config
        self.name = name

        # These will be populated later
        self.cls: Any = None

    def register(
        self,
        obj: Any,
        name: str = "",
        aliases: Union[str, None, Iterable[str]] = None,
        root: bool = False,
    ):
        """Register an object to a registry, subject to configuration.

        Parameters
        ----------
        obj: object
            object to store and attempt to auto-derive name from.
        name: str
            If provided, register ``obj`` to this name; overrides checks.
            If not provided, name will be auto-derived from ``obj`` via ``format``.
        aliases: Union[str, None, Iterable[str]]
            If provided, also register ``obj`` to these strings.
            Not subject to configuration rules.
        root: bool
            Set to ``True`` when calling initial ``__register__``.
            Force register to immediate parent(s).
        """
        # Derive/Validate Name
        if not name:
            try:
                name = str(obj.__name__)
            except AttributeError as e:
                raise CannotDeriveNameError(
                    f"Cannot derive name from a bare {type(obj)}."
                ) from e
            name = self.config.format(name)
        elif "." in name or "/" in name:
            raise InvalidNameError(f'Name "{name}" cannot contain "." or "/".')

        if not self.config.overwrite and name in self:
            raise KeyCollisionError(f'"{name}" already registered to {self}')

        # Validate aliases and massage it into a list.
        if aliases is None:
            aliases = []
        elif isinstance(aliases, str):
            aliases = [aliases]

        for alias in aliases:
            if "." in alias or "/" in alias:
                raise InvalidNameError(f'Alias "{alias}" cannot contain "." or "/".')
            if not self.config.overwrite and alias in self:
                raise KeyCollisionError(f'"{alias}" already registered to {self}')

        # Check if should register self
        if obj == self.cls:
            if self.config.register_self:
                self[name] = obj
        else:
            self[name] = obj

        # Register to parents if one of the following conditions are met:
        #     1. This is the root ``__recursive__`` call.
        #     2. Both this.recursive is True, and parent.recursive is True.
        if (root or self.config.recursive) and self.cls is not None:
            for parent_cls in self.cls.__bases__:
                try:
                    parent_registry = parent_cls.__registry__
                except AttributeError:
                    # Not a Registry object
                    continue

                if parent_cls is Registry:
                    # Never register to the base Registry class.
                    # Unwanted cross-library interactions may occur, otherwise.
                    continue

                if root or parent_registry.config.recursive:
                    parent_registry.register(obj, name=name, aliases=aliases)

        # Register aliases
        for alias in aliases:
            if not self.config.overwrite and alias in self:
                raise KeyCollisionError(f'"{alias}" already registered to {self}')

            self[alias] = obj


class _DictMixin:
    """Dict-like methods for a registry-based class."""

    __registry__: _Registry

    def __getitem__(self, key: str) -> Type:
        return self.__registry__.config.getitem(self.__registry__, key)

    def __iter__(self) -> Generator[str, None, None]:
        yield from self.__registry__

    def __len__(self) -> int:
        return len(self.__registry__)

    def __contains__(self, key: str) -> bool:
        try:
            self.__registry__.config.getitem(self.__registry__, key)
        except KeyError:
            return False
        return True

    def keys(self) -> KeysView:
        return self.__registry__.keys()

    def values(self) -> ValuesView:
        return self.__registry__.values()

    def items(self):
        yield from self.__registry__.items()

    def get(self, key: Union[str, Type], default=None) -> Type:
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


class MethodDescriptor:
    """
    Non-data-descriptor that dispatches depending if it was called from a Class or an instance.
    """

    def __init__(self, user_method, registry_method):
        self.user_method = user_method
        self.registry_method = registry_method

    def __get__(self, obj, objtype):
        if obj is None:
            # invoked from class
            return MethodType(self.registry_method, objtype)
        else:
            # invoked from instance of class
            return MethodType(self.user_method, obj)


class RegistryMeta(ABCMeta, _DictMixin):
    __registry__: _Registry

    def __new__(
        cls,
        cls_name,
        bases,
        namespace,
        name: Union[str, None] = None,
        aliases: Union[str, None, Iterable[str]] = None,
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

        # Copy the nearest parent config, then update it with new params.
        # Some class construction libraries, like ``attrs``, will recreate a class.
        # In these situations, the old-class will have it's attributes (like the __registry__
        # object) passed in via the ``namespace``.
        if "__registry__" in namespace:
            registry_config = namespace["__registry__"].config
        else:
            for parent_cls in bases:
                try:
                    registry_config = parent_cls.__registry__.config.copy()
                    break
                except AttributeError:
                    pass
            else:
                # No parent config, create a new one from scratch.
                namespace["__registry__"] = _Registry(RegistryConfig(**config))
                new_cls = super().__new__(cls, cls_name, bases, namespace)
                return new_cls

        # Derive registry name before updating registry config, since a classes own name is
        # subject to it's parents configuration, not its own.
        registry_name = registry_config.format(cls_name) if name is None else name

        registry_config.update(config)

        namespace["__registry__"] = _Registry(registry_config, name=registry_name)

        if namespace["__registry__"].config.redirect:
            for method_name in [
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
                if method_name in namespace and not isinstance(
                    namespace[method_name], (staticmethod, classmethod)
                ):
                    namespace[method_name] = MethodDescriptor(
                        namespace[method_name], getattr(cls, method_name)
                    )

        # We cannot defer class creation any further.
        # This will call hooks like __init_subclass__
        new_cls = super().__new__(cls, cls_name, bases, namespace)
        new_cls.__registry__.cls = new_cls

        if skip:
            return new_cls

        # Register to parent(s)
        new_cls.__registry__.register(
            new_cls,
            name=new_cls.__registry__.name,
            aliases=aliases,
            root=True,  # Always register to direct parents
        )

        return new_cls

    def __repr__(cls):
        try:
            return f"<{cls.__name__}: {list(cls.__registry__.keys())}>"
        except Exception:
            return super().__repr__()


class Registry(metaclass=RegistryMeta):
    __call__: Callable
    __contains__: Callable[..., bool]
    __getitem__: Callable[[str], Type]
    __iter__: Callable
    __len__: Callable[..., int]
    clear: Callable[[], None]
    get: Callable[..., Type]
    items: Callable
    keys: Callable[[], KeysView]
    values: Callable[[], ValuesView]

    def __new__(cls, *args, **kwargs):
        if cls is Registry:
            # A Registry is being explicitly created for decorating
            return super().__new__(RegistryDecorator)
        else:
            # Registry is being subclassed
            return super().__new__(cls)


class RegistryDecorator(Registry, _DictMixin, skip=True):
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
        obj: Any = None,
        /,
        *,
        name: str = "",
        aliases: Union[str, None, Iterable[str]] = None,
    ) -> Any:
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
        except AttributeError:
            obj_file = None
        if obj_file is None:
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
                except AttributeError:
                    handle_file = None

                if handle_file is None:  # handle is a python built-in
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
