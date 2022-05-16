import re
from dataclasses import dataclass
from typing import Callable


class InvalidNameError(Exception):
    """"""


_to_snake_case_pattern1 = re.compile("(.)([A-Z][a-z]+)")
_to_snake_case_pattern2 = re.compile("__([A-Z])")
_to_snake_case_pattern3 = re.compile("([a-z0-9])([A-Z])")


def to_snake_case(name: str) -> str:
    """Convert PascalCase to snake_case.

    Based on:
        https://stackoverflow.com/a/1176023

    Parameters
    ----------
    name : str

    Returns
    -------
    str
    """
    name = _to_snake_case_pattern1.sub(r"\1_\2", name)
    name = _to_snake_case_pattern2.sub(r"_\1", name)
    name = _to_snake_case_pattern3.sub(r"\1_\2", name)
    return name.lower()


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
            raise InvalidNameError(f'"{func}" name must end with "{self.suffix}"')

        if self.strip_suffix and self.suffix:
            name = name[: -len(self.suffix)]

        name = self.format(name)

        registry[name] = func

    def format(self, name):
        if self.snake_case:
            name = to_snake_case(name)

        if not self.case_sensitive:
            name = name.lower()

        return name
