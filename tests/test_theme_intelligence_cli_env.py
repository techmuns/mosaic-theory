"""The CLI loads the repo-root `.env` ONCE, at its entry point
(`python -m vinci.theme_intelligence`).

2026-10-16, the live pilot's catch-up: `market --as-of 2026-10-15` failed with "Required
environment variable 'POLYGON_API_KEY' is not set" although the key was in `.env`. The CLI loaded
`.env` only inside the model-client setup (`_client`), which `market` never reaches; Actions was
unaffected because it injects its secrets. Now `entry` loads it before any command, and `main`
never does, so a test that calls `main` stays hermetic.

Every `.env` here is a temporary file written by the test; values are placeholders, never keys.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pytest

import vinci.theme_intelligence.__main__ as cli
from vinci.config import load_local_env

KEYS = ("POLYGON_API_KEY", "TIINGO_API_KEY")
MARKET = ["market", "--as-of", "2026-10-15"]


def _unset(monkeypatch: pytest.MonkeyPatch, *names: str) -> None:
    """Unset `names` so that whatever the test loads is removed again at teardown (a bare
    `delenv` of an absent variable records nothing to undo)."""
    for n in names:
        monkeypatch.setenv(n, "placeholder")
        monkeypatch.delenv(n)


def _dotenv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env = tmp_path / ".env"
    env.write_text("POLYGON_API_KEY=offline-polygon\nTIINGO_API_KEY=offline-tiingo\n")
    monkeypatch.setattr(cli, "load_local_env", lambda: load_local_env(env_path=env))


def _seen(monkeypatch: pytest.MonkeyPatch) -> dict[str, str | None]:
    """`cmd_market` replaced by a probe: what the command would see in the environment."""
    seen: dict[str, str | None] = {}

    def probe(a: argparse.Namespace) -> int:
        seen.update({k: os.environ.get(k) for k in KEYS})
        return 0

    monkeypatch.setattr(cli, "cmd_market", probe)
    return seen


def test_the_entry_point_loads_dotenv_before_the_market_command_runs(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _unset(monkeypatch, *KEYS)
    _dotenv(tmp_path, monkeypatch)
    seen = _seen(monkeypatch)
    assert cli.entry(["--data-dir", str(tmp_path / "ti"), *MARKET]) == 0
    assert seen == {"POLYGON_API_KEY": "offline-polygon", "TIINGO_API_KEY": "offline-tiingo"}


def test_a_secret_already_in_the_environment_wins_over_dotenv(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """NEGATIVE: on Actions the injected secret is set before the CLI starts; `.env` never
    overrides it."""
    _unset(monkeypatch, "TIINGO_API_KEY")
    monkeypatch.setenv("POLYGON_API_KEY", "from-actions")
    _dotenv(tmp_path, monkeypatch)
    seen = _seen(monkeypatch)
    assert cli.entry(["--data-dir", str(tmp_path / "ti"), *MARKET]) == 0
    assert seen["POLYGON_API_KEY"] == "from-actions" and seen["TIINGO_API_KEY"] == "offline-tiingo"


def test_main_and_the_model_client_never_read_dotenv(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """NEGATIVE: a test that calls `main` (or reaches `_client`) must not read the real `.env` —
    `load_dotenv` sets variables for the whole process, so one such call would hand every later
    test the real keys."""
    def refuse() -> None:
        raise AssertionError("`.env` read outside the CLI entry point")

    monkeypatch.setattr(cli, "load_local_env", refuse)
    import vinci.config
    monkeypatch.setattr(vinci.config, "load_local_env", refuse)
    _unset(monkeypatch, "ANTHROPIC_API_KEY", *KEYS)
    seen = _seen(monkeypatch)
    assert cli.main(["--data-dir", str(tmp_path / "ti"), *MARKET]) == 0
    assert seen == {"POLYGON_API_KEY": None, "TIINGO_API_KEY": None}
    assert cli._client(required=False) is None
