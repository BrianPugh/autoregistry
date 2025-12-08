try:
    from ._version import __version__
except ImportError:
    # Package not installed (editable install without build)
    __version__ = "0.0.0"

__all__ = [
    "CannotDeriveNameError",
    "CannotRegisterPythonBuiltInError",
    "InvalidNameError",
    "KeyCollisionError",
    "ModuleAliasError",
    "Registry",
    "RegistryError",
    "RegistryMeta",
    "InternalError",
]

from ._registry import Registry, RegistryMeta
from .exceptions import (
    CannotDeriveNameError,
    CannotRegisterPythonBuiltInError,
    InternalError,
    InvalidNameError,
    KeyCollisionError,
    ModuleAliasError,
    RegistryError,
)
