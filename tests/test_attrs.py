from attrs import frozen

from autoregistry import Registry


def test_attrs_root():
    @frozen
    class Media(Registry, snake_case=True):
        name: str
        year: int

    class Movie(Media):
        pass

    class MusicVideo(Media):
        pass

    assert list(Media) == ["movie", "music_video"]
    assert Media["movie"] == Movie
    assert Media["music_video"] == MusicVideo


def test_attrs_children():
    @frozen
    class Media(Registry, snake_case=True):
        name: str
        year: int

    @frozen
    class Movie(Media):
        director: str

    @frozen
    class HorrorMovie(Movie):
        antagonist: str

    assert list(Media) == ["movie", "horror_movie"]
    assert Media["movie"] is Movie
    assert Media["horror_movie"] is HorrorMovie
    assert Movie["horror_movie"] is HorrorMovie

    horror_movie = Media["horror_movie"](
        name="Nosferatu",
        year=1922,
        director="Murnau",
        antagonist="Count Orlok",
    )
    assert (
        str(horror_movie)
        == "HorrorMovie(name='Nosferatu', year=1922, director='Murnau', antagonist='Count Orlok')"
    )
