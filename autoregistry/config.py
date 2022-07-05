import dataclasses
import re
from dataclasses import asdict, dataclass

from .exceptions import InvalidNameError
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

    def getitem(self, registry: dict, key: str):
        keys = key_split(key)
        for key in keys:
            if not self.case_sensitive:
                key = key.lower()

            registry = registry[key]
        return registry

    def format(self, name: str) -> str:
        """Convert and validate a PascalCase class name to a registry key.

        Parameters
        ----------
        name: str
            Name to convert to a registry key. For example, converts ``FooBar``
            into ``foobar``.
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

        if not self.case_sensitive:
            name = name.lower()

        return name
