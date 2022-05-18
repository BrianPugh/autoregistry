import re

_to_snake_case_pattern1 = re.compile("(.)([A-Z][a-z]+)")
_to_snake_case_pattern2 = re.compile("__([A-Z])")
_to_snake_case_pattern3 = re.compile("([a-z0-9])([A-Z])")


def to_snake_case(name: str) -> str:
    """Convert PascalCase to snake_case.

    Based on:
        https://stackoverflow.com/a/1176023

    Parameters
    ----------
    name : str

    Returns
    -------
    str
    """
    name = _to_snake_case_pattern1.sub(r"\1_\2", name)
    name = _to_snake_case_pattern2.sub(r"_\1", name)
    name = _to_snake_case_pattern3.sub(r"\1_\2", name)
    return name.lower()


def key_split(s: str) -> list[str]:
    return s.replace("/", ".").split(".")
