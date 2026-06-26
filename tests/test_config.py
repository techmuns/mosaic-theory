"""Tests for the shared local-secret loading path (``config.load_local_env``).

These pin the three behaviours every laptop + CI rely on: a repo-root ``.env`` seeds the
environment locally; an already-set var (a CI-injected secret) is NEVER clobbered; and a missing
``.env`` (the CI case) is a silent no-op, never a crash.
"""

from __future__ import annotations

import os
from pathlib import Path

from vinci.config import load_local_env


def _write_env(folder: Path, body: str) -> Path:
    env = folder / ".env"
    env.write_text(body)
    return env


def test_load_local_env_populates_from_file(tmp_path: Path) -> None:
    """A repo-root .env seeds os.environ for local runs."""
    env = _write_env(tmp_path, "VINCI_TEST_LOADED=from-dotenv\n")
    assert "VINCI_TEST_LOADED" not in os.environ
    try:
        load_local_env(env)
        assert os.environ["VINCI_TEST_LOADED"] == "from-dotenv"
    finally:
        os.environ.pop("VINCI_TEST_LOADED", None)


def test_load_local_env_never_overrides_an_already_set_var(tmp_path: Path) -> None:
    """CI injects secrets directly; a stray .env must never clobber an already-set var."""
    env = _write_env(tmp_path, "VINCI_TEST_OVERRIDE=from-dotenv\n")
    os.environ["VINCI_TEST_OVERRIDE"] = "from-ci"
    try:
        load_local_env(env)
        assert os.environ["VINCI_TEST_OVERRIDE"] == "from-ci"
    finally:
        os.environ.pop("VINCI_TEST_OVERRIDE", None)


def test_load_local_env_missing_file_is_a_noop(tmp_path: Path) -> None:
    """No .env (the CI / GitHub-Actions case) must not raise — just load nothing."""
    missing = tmp_path / ".env"
    assert not missing.exists()
    load_local_env(missing)  # must not raise
