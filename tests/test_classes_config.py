import pytest
from common import construct_pokemon_classes

from autoregistry import InvalidNameError, Registry


def test_case_sensitive():
    Pokemon, Charmander, Pikachu, SurfingPikachu = construct_pokemon_classes(
        case_sensitive=True,
    )

    assert list(Pokemon.keys()) == ["Charmander", "Pikachu", "SurfingPikachu"]
    assert Pokemon["Charmander"] == Charmander
    with pytest.raises(KeyError):
        Pokemon["CHARMANDER"]


def test_suffix_no_strip():
    class Sensor(Registry, suffix="Sensor", strip_suffix=False):
        pass

    class OxygenSensor(Sensor):
        pass

    class TemperatureSensor(Sensor):
        pass

    assert list(Sensor.keys()) == ["oxygensensor", "temperaturesensor"]

    with pytest.raises(InvalidNameError):

        class Foo(Sensor):
            pass


def test_suffix_yes_strip():
    class Sensor(Registry, suffix="Sensor"):
        pass

    class OxygenSensor(Sensor):
        pass

    class TemperatureSensor(Sensor):
        pass

    assert list(Sensor.keys()) == ["oxygen", "temperature"]


def test_register_self():
    Pokemon, Charmander, Pikachu, SurfingPikachu = construct_pokemon_classes(
        register_self=True,
    )
    assert list(Pokemon.keys()) == [
        "pokemon",
        "charmander",
        "pikachu",
        "surfingpikachu",
    ]


def test_no_recursive():
    Pokemon, Charmander, Pikachu, SurfingPikachu = construct_pokemon_classes(
        recursive=False,
    )
    assert list(Pokemon.keys()) == ["charmander", "pikachu"]
    assert list(Charmander.keys()) == []
    assert list(Pikachu.keys()) == ["surfingpikachu"]
    assert list(SurfingPikachu.keys()) == []


def test_snake_case():
    Pokemon, Charmander, Pikachu, SurfingPikachu = construct_pokemon_classes(
        snake_case=True,
    )
    assert list(Pokemon.keys()) == [
        "charmander",
        "pikachu",
        "surfing_pikachu",
    ]


def test_config_hierarchy():
    class Pokemon(Registry, suffix="Type", strip_suffix=True, recursive=False):
        pass

    class RockType(Pokemon, suffix=""):
        pass

    class Geodude(RockType):
        pass

    class GrassType(Pokemon):
        pass

    with pytest.raises(InvalidNameError):
        # Because "Oddish" doesn't end in "Type"
        class Oddish(GrassType):
            pass
