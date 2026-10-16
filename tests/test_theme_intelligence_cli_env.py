"""The CLI loads the repo-root `.env` ONCE, when run as `python -m vinci.theme_intelligence` — and
BEFORE the modules it imports read the environment.

2026-10-16, the live pilot's catch-up: `market --as-of 2026-10-15` failed with "Required
environment variable 'POLYGON_API_KEY' is not set" although the key was in `.env`. The CLI loaded
`.env` only inside the model-client setup (`_client`), which `market` never reaches; Actions was
unaffected because it injects its secrets. The review of the first fix found that loading it after
the imports still missed `config.USER_AGENT`, read from SEC_USER_AGENT at import.

The `python -m` path is run for real (`runpy`, in a subprocess, so the import-time read happens
fresh), with the loader pointed at a temporary `.env`; values are placeholders, never keys.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import pytest

import vinci.theme_intelligence.__main__ as cli

REPO = Path(__file__).resolve().parents[1]
KEYS = ("POLYGON_API_KEY", "TIINGO_API_KEY", "SEC_USER_AGENT", "ANTHROPIC_API_KEY")
DOTENV = ("POLYGON_API_KEY=offline-polygon\nTIINGO_API_KEY=offline-tiingo\n"
          "SEC_USER_AGENT=Test Desk desk@example.invalid\n")


def _python_m(tmp_path: Path, *, env: dict[str, str] | None = None,
              loader: str = "_real(env_path=Path(ENV))") -> list[str]:
    """Run `python -m vinci.theme_intelligence --help` as the interpreter would — `runpy` with
    `run_name="__main__"` — with the CLI's REAL `load_local_env` pointed at a temporary `.env`
    (its `env_path` seam); print what the environment and the import-time User-Agent hold."""
    dotenv = tmp_path / ".env"
    dotenv.write_text(DOTENV)
    script = (
        "import os, runpy, sys\n"
        "from pathlib import Path\n"
        "import vinci.config as c\n"
        "_real = c.load_local_env\n"
        f"ENV = {str(dotenv)!r}\n"
        f"def _load(env_path=None):\n    {loader}\n"
        "c.load_local_env = _load\n"
        "sys.argv = ['python -m vinci.theme_intelligence', '--help']\n"
        "try:\n"
        "    runpy.run_module('vinci.theme_intelligence', run_name='__main__', alter_sys=True)\n"
        "except SystemExit:\n"
        "    pass\n"
        "import vinci.theme_intelligence.config as cfg\n"
        "print('UA=' + cfg.USER_AGENT)\n"
        "print('POLYGON=' + str(os.environ.get('POLYGON_API_KEY')))\n"
        "print('TIINGO=' + str(os.environ.get('TIINGO_API_KEY')))\n")
    base = {k: v for k, v in os.environ.items() if k not in KEYS}
    r = subprocess.run([sys.executable, "-c", script], cwd=tmp_path, capture_output=True,
                       text=True, env={**base, "PYTHONPATH": str(REPO), **(env or {})},
                       check=True)
    return [x for x in r.stdout.splitlines() if x.split("=", 1)[0] in ("UA", "POLYGON", "TIINGO")]


def test_python_m_loads_dotenv_before_the_config_reads_the_environment(tmp_path: Path) -> None:
    """The keys reach the command, AND the import-time User-Agent carries `.env`'s contact."""
    ua, polygon, tiingo = _python_m(tmp_path)
    assert ua.endswith("contact: desk@example.invalid)")
    assert polygon == "POLYGON=offline-polygon" and tiingo == "TIINGO=offline-tiingo"


def test_a_secret_already_in_the_environment_wins_over_dotenv(tmp_path: Path) -> None:
    """NEGATIVE: on Actions the injected secret is set before the CLI starts; `.env` never
    overrides it — through the CLI's real loader (`vinci.config.load_local_env`, override=False)."""
    _ua, polygon, tiingo = _python_m(tmp_path, env={"POLYGON_API_KEY": "from-actions"})
    assert polygon == "POLYGON=from-actions" and tiingo == "TIINGO=offline-tiingo"


def test_importing_the_cli_and_calling_main_never_read_dotenv(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """NEGATIVE: a test imports the module and calls `main` (or reaches `_client`) — none of it
    may read the real `.env`: `load_dotenv` sets variables for the whole process, so one such
    read would hand every later test the real keys."""
    def refuse(env_path: Path | None = None) -> None:
        raise AssertionError("`.env` read outside `python -m`")

    import vinci.config
    monkeypatch.setattr(vinci.config, "load_local_env", refuse)
    monkeypatch.setattr(cli, "load_local_env", refuse)
    for n in KEYS:
        monkeypatch.setenv(n, "placeholder")
        monkeypatch.delenv(n)
    seen: dict[str, str | None] = {}

    def probe(a: argparse.Namespace) -> int:
        seen.update({k: os.environ.get(k) for k in ("POLYGON_API_KEY", "TIINGO_API_KEY")})
        return 0

    monkeypatch.setattr(cli, "cmd_market", probe)
    assert cli.main(["--data-dir", str(tmp_path / "ti"), "market", "--as-of", "2026-10-15"]) == 0
    assert seen == {"POLYGON_API_KEY": None, "TIINGO_API_KEY": None}
    assert cli._client(required=False) is None
    # and a fresh import (not `python -m`) runs no load either
    script = ("import vinci.config as c\n"
              "def refuse(env_path=None):\n    raise SystemExit('loaded on import')\n"
              "c.load_local_env = refuse\n"
              "import vinci.theme_intelligence.__main__\n")
    r = subprocess.run([sys.executable, "-c", script], cwd=tmp_path, capture_output=True,
                       text=True, env={**os.environ, "PYTHONPATH": str(REPO)})
    assert r.returncode == 0, r.stderr[-500:]
