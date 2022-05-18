from dataclasses import dataclass
from typing import Any, Union

from .exceptions import CannotDeriveNameError, InvalidNameError, KeyCollisionError
from .regex import key_split, to_snake_case


@dataclass
class RegistryConfig:
    case_sensitive: bool = False
    suffix: str = ""
    strip_suffix: bool = True

    # Classes only; Register to its own registry
    register_self: bool = False

    # If ``True``, register new entries in all parent registries.
    # Otherwise, only register in parent.
    recursive: bool = True

    snake_case: bool = False

    overwrite: bool = False

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

    def register(self, registry: dict, obj: Any, name: Union[str, None] = None):
        if name is None:
            try:
                name = str(obj.__name__)
            except AttributeError:
                raise CannotDeriveNameError(
                    f"Cannot derive name from a bare {type(obj)}."
                )

        if not name.endswith(self.suffix):
            raise InvalidNameError(f'"{obj}" name must end with "{self.suffix}"')

        if self.strip_suffix and self.suffix:
            name = name[: -len(self.suffix)]

        name = self.format(name)

        if not self.overwrite and name in registry:
            raise KeyCollisionError(f'"{name}" already registered to {registry}')

        registry[name] = obj

    def format(self, name):
        if self.snake_case:
            name = to_snake_case(name)

        if not self.case_sensitive:
            name = name.lower()

        return name
