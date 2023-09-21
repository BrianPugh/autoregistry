from attrs import frozen

from autoregistry import Registry


def test_attrs_compatability():
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
