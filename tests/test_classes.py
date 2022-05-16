import pytest
from common import construct_pokemon_classes


def test_defaults_basic_usecase():
    Pokemon, Charmander, Pikachu, SurfingPikachu = construct_pokemon_classes()
    charmander = Pokemon["cHaRmAnDer"](1, 2)
    assert isinstance(charmander, Charmander)


def test_defaults_contains():
    Pokemon, Charmander, Pikachu, SurfingPikachu = construct_pokemon_classes()
    for pokemon in ["charmander", "pikachu", "surfingpikachu"]:
        assert pokemon in Pokemon

    # Test for case insensitivity.
    for pokemon in ["charmander", "pikachu", "surfingpikachu"]:
        assert pokemon.upper() in Pokemon


def test_defaults_len():
    Pokemon, Charmander, Pikachu, SurfingPikachu = construct_pokemon_classes()
    assert len(Pokemon) == 3
    assert len(Charmander) == 0
    assert len(Pikachu) == 1
    assert len(SurfingPikachu) == 0


def test_defaults_keys():
    Pokemon, Charmander, Pikachu, SurfingPikachu = construct_pokemon_classes()
    assert list(Pokemon.keys()) == ["charmander", "pikachu", "surfingpikachu"]
    assert list(Charmander.keys()) == []
    assert list(Pikachu.keys()) == ["surfingpikachu"]
    assert list(SurfingPikachu.keys()) == []


def test_defaults_values():
    Pokemon, Charmander, Pikachu, SurfingPikachu = construct_pokemon_classes()
    expected_names = ["Charmander", "Pikachu", "SurfingPikachu"]
    f_handles = list(Pokemon.values())
    f_names = [x.__name__ for x in f_handles]
    assert expected_names == f_names


def test_defaults_items():
    Pokemon, Charmander, Pikachu, SurfingPikachu = construct_pokemon_classes()
    f_handles = list(Pokemon.items())

    actual_keys = [x[0] for x in f_handles]
    assert actual_keys == ["charmander", "pikachu", "surfingpikachu"]

    f_names = [x[1].__name__ for x in f_handles]
    expected_names = ["Charmander", "Pikachu", "SurfingPikachu"]
    assert expected_names == f_names

    assert len(list(Charmander.items())) == 0
    assert len(list(Pikachu.items())) == 1
    assert len(list(SurfingPikachu.items())) == 0


def test_defaults_get():
    Pokemon, Charmander, Pikachu, SurfingPikachu = construct_pokemon_classes()
    assert Pokemon.get("charmander") == Charmander
    assert Pokemon.get("foo") is None
    assert Pokemon.get("foo", "charmander") == Charmander
    assert Pokemon.get("foo", Charmander) == Charmander
