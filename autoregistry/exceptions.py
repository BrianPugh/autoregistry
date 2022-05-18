class RegistryError(Exception):
    """General autoregistry error."""


class InvalidNameError(RegistryError):
    """Registered object has an invalid name."""


class CannotDeriveNameError(RegistryError):
    """Cannot derive registry name from object."""
