import pytest
from common import construct_pokemon_classes


def test_case_sensitive():
    Pokemon, Charmander, Pikachu, SurfingPikachu = construct_pokemon_classes(
        case_sensitive=True,
    )

    assert list(Pokemon.keys()) == ["Charmander", "Pikachu", "SurfingPikachu"]
    assert Pokemon["Charmander"] == Charmander
    with pytest.raises(KeyError):
        Pokemon["CHARMANDER"]
