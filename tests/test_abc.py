from abc import ABC, abstractmethod

import pytest

from autoregistry import Registry


def test_abc_undefined_abstractmethod():
    class Pokemon(Registry):
        @abstractmethod
        def attack(self):
            pass

    class Charmander(Pokemon):
        def attack(self):
            return 1

    class Pikachu(Pokemon):
        pass

    with pytest.raises(TypeError):
        Pokemon()

    with pytest.raises(TypeError):
        Pokemon["pikachu"]()

    with pytest.raises(TypeError):
        Pikachu()

    Charmander()


def test_abc_multiple_inheritence_first():
    """The programmer doesn't know inheritting from ABC is superfluous."""

    class Pokemon(ABC, Registry):
        @abstractmethod
        def attack(self):
            pass

    class Charmander(Pokemon):
        def attack(self):
            return 1

    class Pikachu(Pokemon):
        pass

    with pytest.raises(TypeError):
        Pokemon()  # pyright: ignore[reportGeneralTypeIssues]

    with pytest.raises(TypeError):
        Pokemon["pikachu"]()

    with pytest.raises(TypeError):
        Pikachu()  # pyright: ignore[reportGeneralTypeIssues]

    Charmander()


def test_abc_multiple_inheritence_last():
    """The programmer doesn't know inheritting from ABC is superfluous."""

    class Pokemon(Registry, ABC):
        @abstractmethod
        def attack(self):
            pass

    class Charmander(Pokemon):
        def attack(self):
            return 1

    class Pikachu(Pokemon):
        pass

    with pytest.raises(TypeError):
        Pokemon()  # pyright: ignore[reportGeneralTypeIssues]

    with pytest.raises(TypeError):
        Pokemon["pikachu"]()

    with pytest.raises(TypeError):
        Pikachu()  # pyright: ignore[reportGeneralTypeIssues]

    Charmander()
