"""Pyright-based regression tests for autoregistry's public typing contract.

These tests run pyright as a subprocess against small snippets that exercise
the typing guarantees autoregistry tries to maintain. They guard against
regressions in the type-checker-visible surface (e.g., Issue 1: unknown
``__init_subclass__`` kwargs should NOT error; unknown kwargs SHOULD error).

The tests are skipped if pyright is not installed on PATH.
"""

import json
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

pyright = shutil.which("pyright")
pytestmark = pytest.mark.skipif(
    pyright is None,
    reason="pyright not installed",
)


def _run_pyright(snippet: str, tmp_path: Path) -> dict:
    """Write ``snippet`` to a temporary file and return pyright's JSON report."""
    file = tmp_path / "snippet.py"
    file.write_text(textwrap.dedent(snippet))
    assert pyright is not None
    proc = subprocess.run(
        [pyright, "--outputjson", str(file)],
        capture_output=True,
        text=True,
        check=False,
    )
    # pyright exits non-zero when errors are found; that's expected for
    # negative tests. The JSON is on stdout regardless.
    return json.loads(proc.stdout)


def _errors_on_line(report: dict, line_1_indexed: int) -> list:
    """Return the list of error diagnostics on a given 1-indexed source line."""
    return [
        d
        for d in report.get("generalDiagnostics", [])
        if d.get("severity") == "error"
        and d["range"]["start"]["line"] == line_1_indexed - 1
    ]


def test_init_subclass_accepts_known_kwargs(tmp_path: Path) -> None:
    """Known config kwargs on a Registry subclass must not produce errors.

    Regression for Issue 1 in ``autoregistry-issue.md``.
    """
    snippet = """
    from autoregistry import Registry

    class Pokemon(
        Registry,
        snake_case=True,
        prefix="Poke",
        suffix="",
        recursive=False,
        case_sensitive=False,
        register_self=False,
        overwrite=False,
        redirect=True,
        strip_prefix=True,
        strip_suffix=True,
        regex="",
        hyphen=False,
        base=False,
    ):
        pass
    """
    report = _run_pyright(snippet, tmp_path)
    errors = [
        d for d in report.get("generalDiagnostics", []) if d.get("severity") == "error"
    ]
    assert errors == [], f"Unexpected errors: {errors}"


def test_init_subclass_signature_declares_config_kwargs(tmp_path: Path) -> None:
    """``Registry.__init_subclass__`` must advertise the config kwargs.

    Verifies via ``reveal_type`` that the signature lists the known
    ``RegistryConfig`` parameters. This guards against regressions where
    someone removes ``__init_subclass__`` or forgets to add a new field.
    """
    snippet = """
    from autoregistry import Registry

    reveal_type(Registry.__init_subclass__)
    """
    report = _run_pyright(snippet, tmp_path)
    info_diags = [
        d
        for d in report.get("generalDiagnostics", [])
        if d.get("severity") == "information"
    ]
    revealed = " ".join(d["message"] for d in info_diags)
    assert "snake_case" in revealed, f"snake_case missing from signature: {revealed}"
    assert "prefix" in revealed, f"prefix missing from signature: {revealed}"
    assert "recursive" in revealed, f"recursive missing from signature: {revealed}"
    assert "base" in revealed, f"base missing from signature: {revealed}"


def test_base_kwarg_accepted(tmp_path: Path) -> None:
    """The ``base=True`` kwarg must not be flagged.

    Before Issue 1 was fixed, ``autoregistry/pydantic.py`` had a
    ``# type: ignore[call-arg]`` on ``base=True``. Confirm that's no longer
    needed.
    """
    snippet = """
    from autoregistry import Registry

    class BaseReg(Registry, base=True):
        pass
    """
    report = _run_pyright(snippet, tmp_path)
    errors = [
        d for d in report.get("generalDiagnostics", []) if d.get("severity") == "error"
    ]
    assert errors == [], f"Unexpected errors for base=True: {errors}"


def test_items_return_type_is_tuple_of_str_and_type(tmp_path: Path) -> None:
    """``.items()`` must reveal ``Generator[tuple[str, Type], ...]``.

    Regression for Issue 3: the bare ``items: Callable`` annotation left
    iteration types as Unknown. After the fix, ``items()`` has a concrete
    return type.

    Note: this asserts the class-level instance-method annotation (from
    ``_DictMixin``), which is what downstream users get when they iterate
    via ``MyReg.items()``.
    """
    snippet = """
    from autoregistry import Registry
    from autoregistry._registry import _DictMixin

    reveal_type(_DictMixin.items)
    """
    report = _run_pyright(snippet, tmp_path)
    info_diags = [
        d
        for d in report.get("generalDiagnostics", [])
        if d.get("severity") == "information"
    ]
    revealed = [d["message"] for d in info_diags if "Type of" in d["message"]]
    assert revealed, f"reveal_type produced no output. Report: {report}"
    joined = " ".join(revealed)
    # The reveal should mention the typed Generator return, with a
    # str-keyed tuple (pyright renders it as ``Tuple[str, Type[...]]``).
    assert (
        "Generator" in joined and "Tuple[str" in joined
    ), f"Expected items() to reveal Generator[Tuple[str, Type], ...]; got: {revealed}"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
