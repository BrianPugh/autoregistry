class RegistryError(Exception):
    """General autoregistry error."""


class InvalidNameError(RegistryError):
    """Registered object has an invalid name."""


class CannotDeriveNameError(RegistryError):
    """Cannot derive registry name from object."""


class KeyCollisionError(RegistryError):
    """Attempted to register an object to an already used key."""


class CannotRegisterPythonBuiltInError(RegistryError):
    """AutoRegistry doesn't work with python built-ins."""
