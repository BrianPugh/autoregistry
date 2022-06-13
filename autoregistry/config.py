import dataclasses
import re
from dataclasses import dataclass
from typing import Any, List, Union

from .exceptions import CannotDeriveNameError, InvalidNameError, KeyCollisionError
from .regex import key_split, to_snake_case


@dataclass
class RegistryConfig:
    case_sensitive: bool = False
    prefix: str = ""
    suffix: str = ""
    strip_prefix: bool = True
    strip_suffix: bool = True

    # Registered objects name must conform to this regex.
    regex: str = ""

    # Classes only; Register to its own registry
    register_self: bool = False

    # If ``True``, register new entries in all parent registries.
    # Otherwise, only register in parent.
    recursive: bool = True

    snake_case: bool = False

    overwrite: bool = False

    def __post_init__(self):
        if self.regex:
            self._regex_validator = re.compile(self.regex)
        else:
            self._regex_validator = None

    def copy(self):
        obj = dataclasses.replace(self)
        return obj

    def update(self, new: dict):
        for key, value in new.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def getitem(self, registry: dict, key: str):
        keys = key_split(key)
        for key in keys:
            if not self.case_sensitive:
                key = key.lower()

            registry = registry[key]
        return registry

    def register(
        self,
        registry: dict,
        obj: Any,
        name: Union[str, None] = None,
        aliases: Union[str, None, List[str]] = None,
    ):
        """Register an object to a registry, subject to configuration.

        Parameters
        ----------
        registry: dict
            Dictionary to store key/value pair.
        obj: object
            object to store and attempt to auto-derive name from.
        name: str
            If provided, register ``obj`` to this name.
            If not provided, name will be auto-derived from ``obj``.
        aliases: Union[str, None, List[str]]
            If provided, also register ``obj`` to these strings.
            Not subject to configuration rules.
        """
        validate = False
        if name is None:
            validate = True
            try:
                name = str(obj.__name__)
            except AttributeError:
                raise CannotDeriveNameError(
                    f"Cannot derive name from a bare {type(obj)}."
                )

        if validate:
            if self._regex_validator and not self._regex_validator.match(name):
                raise InvalidNameError(f"{obj} name must match regex {self.regex}")

            if not name.startswith(self.prefix):
                raise InvalidNameError(f'"{obj}" name must start with "{self.prefix}"')

            if not name.endswith(self.suffix):
                raise InvalidNameError(f'"{obj}" name must end with "{self.suffix}"')

            if self.strip_prefix and self.prefix:
                name = name[len(self.prefix) :]

            if self.strip_suffix and self.suffix:
                name = name[: -len(self.suffix)]

            name = self.format(name)

        if not self.overwrite and name in registry:
            raise KeyCollisionError(f'"{name}" already registered to {registry}')

        registry[name] = obj

        if aliases is None:
            aliases = []
        elif isinstance(aliases, str):
            aliases = [aliases]

        for alias in aliases:
            if not self.overwrite and alias in registry:
                raise KeyCollisionError(f'"{alias}" already registered to {registry}')

            registry[alias] = obj

    def format(self, name):
        if self.snake_case:
            name = to_snake_case(name)

        if not self.case_sensitive:
            name = name.lower()

        return name
