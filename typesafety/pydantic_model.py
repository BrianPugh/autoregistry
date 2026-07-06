"""Static type-safety assertions for the pydantic integration.

Checked by pyright only (see ``registry.py``'s module docstring for the
conventions used in this directory). These guard that the class-mode
self-type overrides on ``RegistryMeta`` survive the combined
``PydanticRegistryMeta`` metaclass.
"""

from typing import Optional, assert_type

from autoregistry.pydantic import BaseModel


class Sensor(BaseModel):
    reading: float


class Thermometer(Sensor):
    pass


def test_class_mode_lookup_returns_subclass_type() -> None:
    assert_type(Sensor["thermometer"], type[Sensor])
    assert_type(Sensor["thermometer"](reading=1.5), Sensor)
    assert_type(Sensor.get("thermometer"), Optional[type[Sensor]])


def test_iteration_is_typed() -> None:
    for name, cls in Sensor.items():
        assert_type(name, str)
        assert_type(cls, type[Sensor])


def test_pydantic_fields_stay_typed() -> None:
    # Registry's dict-like interface must not degrade normal model typing.
    thermometer = Thermometer(reading=2.0)
    assert_type(thermometer.reading, float)
