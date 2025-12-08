import warnings

from pydantic import BaseModel as PydanticBaseModel
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from ._registry import DICT_METHODS, Registry, RegistryMeta

PydanticBaseModelMetaclass = type(PydanticBaseModel)


def _update_model_field(cls, field_name, field_info):
    """Update both model_fields and __pydantic_fields__ with given FieldInfo."""
    cls.model_fields[field_name] = field_info
    if hasattr(cls, "__pydantic_fields__"):
        cls.__pydantic_fields__[field_name] = field_info


def _remove_model_field(cls, field_name):
    """Remove field from both model_fields and __pydantic_fields__."""
    cls.model_fields.pop(field_name, None)
    if hasattr(cls, "__pydantic_fields__"):
        cls.__pydantic_fields__.pop(field_name, None)


class PydanticRegistryMeta(PydanticBaseModelMetaclass, RegistryMeta):
    """Metaclass that combines Pydantic's ModelMetaclass with AutoRegistry's RegistryMeta."""

    def __new__(mcs, cls_name, bases, namespace, **kwargs):  # noqa: N804
        """
        Clean up DICT_METHODS from Pydantic model_fields.

        Pydantic's metaclass scans for callable attributes and annotations
        to build model_fields. When it sees Registry's DICT_METHODS (keys,
        values, items, get, clear), it mistakenly treats them as field defaults.

        We remove these from model_fields after class creation UNLESS the user
        explicitly defined a field with that name (in which case we keep it
        but fix the annotation to use the user's type, not the method type).
        """
        # Save user's explicit field annotations and default values before super().__new__()
        # (RegistryMeta will wrap defaults in MethodDescriptor, so we need originals)
        if "__annotate_func__" in namespace:
            # Python 3.14+ (PEP 649): annotations are lazily evaluated via __annotate_func__
            try:
                user_annotations = namespace["__annotate_func__"](1)  # 1 = Format.VALUE
            except (NameError, TypeError):
                # NameError: annotation evaluation fails to resolve a name
                # TypeError: __annotate_func__ receives unexpected argument or has call issues
                user_annotations = {}
        else:
            # Python < 3.14: annotations stored directly in namespace
            user_annotations = namespace.get("__annotations__", {})
        user_defaults = {
            name: namespace[name]
            for name in DICT_METHODS
            if name in namespace and not callable(namespace[name])
        }

        # Suppress Pydantic's warnings about DICT_METHODS shadowing parent attributes
        with warnings.catch_warnings():
            for method_name in DICT_METHODS:
                warnings.filterwarnings(
                    "ignore",
                    message=rf'Field name "{method_name}" .* shadows an attribute in parent',
                    category=UserWarning,
                )
            # Call parent metaclasses (Pydantic and Registry)
            cls = super().__new__(mcs, cls_name, bases, namespace, **kwargs)

        if not hasattr(cls, "model_fields"):  # pragma: no cover
            # Defensive: model_fields always exists in Pydantic v2
            return cls

        # Clean up DICT_METHODS in model_fields
        for method_name in DICT_METHODS:
            if method_name not in cls.model_fields:
                continue

            if method_name in user_annotations:
                # User-defined field: recreate with correct type and default
                field_info = FieldInfo(
                    annotation=user_annotations[method_name],
                    default=user_defaults.get(method_name, PydanticUndefined),
                )
                _update_model_field(cls, method_name, field_info)
            else:
                # Not user-defined
                _remove_model_field(cls, method_name)

        # Rebuild Pydantic's core schema with corrected fields
        if hasattr(cls, "model_rebuild"):
            cls.model_rebuild(force=True)

        return cls

    def __call__(cls, *args, **kwargs):  # noqa: N805
        """Create an instance and ensure Registry methods stay at class level.

        With proper field cleanup in __new__, DICT_METHODS should only appear in
        instance __dict__ if the user explicitly defined them as fields. We only
        remove DICT_METHODS that are callable (actual methods that leaked through),
        not user field values.
        """
        instance = super().__call__(*args, **kwargs)

        # Remove any DICT_METHODS that are callable (methods that leaked through)
        # Keep DICT_METHODS that are user-defined field values (not callable)
        for method_name in DICT_METHODS:
            value = instance.__dict__.get(method_name)
            if value is not None and callable(value):  # pragma: no cover
                # Safety net: __new__ should prevent this, but we double-check
                instance.__dict__.pop(method_name, None)

        return instance


class BaseModel(
    PydanticBaseModel,
    Registry,
    metaclass=PydanticRegistryMeta,
    base=True,  # type: ignore[call-arg]
):
    """Base class combining Pydantic's BaseModel with AutoRegistry."""


# Remove DICT_METHODS from autoregistry's BaseModel's annotations and model_fields.
# Pydantic's metaclass has already processed BaseModel and baked DICT_METHODS
# into model_fields, so we need to clean up both places to prevent them from
# being inherited by subclasses as fields.
if hasattr(BaseModel, "__annotations__"):
    for method_name in DICT_METHODS:
        BaseModel.__annotations__.pop(method_name, None)

if hasattr(BaseModel, "model_fields"):
    for method_name in DICT_METHODS:
        BaseModel.model_fields.pop(method_name, None)


__all__ = ["PydanticRegistryMeta", "BaseModel"]
