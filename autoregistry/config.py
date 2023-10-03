import dataclasses
import re
from dataclasses import asdict, dataclass
from typing import Callable, Optional

from .exceptions import InvalidNameError
from .regex import hyphenate, key_split, to_snake_case


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

    # Convert PascalCase names to snake_case.
    snake_case: bool = False

    # Convert underscores _ to hyphens -
    hyphen: bool = False

    # Custom user-provided name transform.
    transform: Optional[Callable[[str], str]] = None

    # Allow registry keys to be overwritten.
    overwrite: bool = False

    # Redirect vanilla methods that would collide with the dict-like interface.
    redirect: bool = True

    def __post_init__(self):
        if self.regex:
            self._regex_validator = re.compile(self.regex)
        else:
            self._regex_validator = None

    def asdict(self):
        return asdict(self)

    def copy(self):
        obj = dataclasses.replace(self)
        return obj

    def update(self, new: dict) -> None:
        for key, value in new.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise TypeError(f"Unexpected configuration value {key}={value}")

    def getitem(self, registry: dict, key: str):
        """Key/Value lookup with keysplitting and optional case-insensitivity."""
        keys = key_split(key)
        for key in keys:
            if not self.case_sensitive:
                key = key.lower()

            registry = registry[key]
        return registry

    def format(self, name: str) -> str:
        """Convert and validate a function or class name to a registry key.

        Operations are performed in the following order (if configured):
            1. ``regex`` validator
            2. ``prefix`` validation, then stripping.
            3. ``suffix`` validation, then stripping.
            4. ``snake_case`` transform (``FooBar`` -> ``foo_bar``).
            5. ``hyphen`` transform (``foo_bar`` -> ``foo-bar``).
            6. ``transform`` arbitrary user-provided string transform.
            7.  The lookup string representation is then stored as all
                lowercase if ``case_sensitive=False``.

        Parameters
        ----------
        name: str
            Name to convert to a registry key.

        Raises
        ------
        InvalidNameError
            If the provided name fails a validation check (``prefix``, ``suffix``, ``regex``).

        Returns
        -------
        str
            New name after applying all transformation and validation rules.
        """
        if self._regex_validator and not self._regex_validator.match(name):
            raise InvalidNameError(f"{name} name must match regex {self.regex}")

        if not name.startswith(self.prefix):
            raise InvalidNameError(f'"{name}" name must start with "{self.prefix}"')

        if not name.endswith(self.suffix):
            raise InvalidNameError(f'"{name}" name must end with "{self.suffix}"')

        if self.strip_prefix and self.prefix:
            name = name[len(self.prefix) :]

        if self.strip_suffix and self.suffix:
            name = name[: -len(self.suffix)]

        if self.snake_case:
            name = to_snake_case(name)

        if self.hyphen:
            name = hyphenate(name)

        if self.transform:
            name = self.transform(name)

        if not self.case_sensitive:
            name = name.lower()

        return name
