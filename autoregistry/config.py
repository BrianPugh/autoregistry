from dataclasses import dataclass
from typing import Callable


class InvalidClassnameError(Exception):
    """"""


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

    def update(self, new: dict):
        for key, value in new.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def getitem(self, registry: dict, key: str):
        if not self.case_sensitive:
            key = key.lower()

        return registry[key]

    def register(self, registry: dict, func: Callable):
        name = func.__name__

        if not name.endswith(self.suffix):
            raise InvalidClassnameError(f'"{func}" name must end with "{self.suffix}"')

        if self.strip_suffix and self.suffix:
            name = name[: -len(self.suffix)]

        name = self.format(name)

        registry[name] = func

    def format(self, name):
        if not self.case_sensitive:
            name = name.lower()

        return name
