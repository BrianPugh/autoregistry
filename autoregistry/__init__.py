# Don't manually change, let poetry-dynamic-versioning-plugin handle it.
__version__ = "0.0.0"

from abc import abstractmethod

from .config import InvalidNameError, RegistryConfig
from .registry import Registry, RegistryDecorator, RegistryMeta
