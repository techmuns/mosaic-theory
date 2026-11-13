"""THE SDK IS PINNED EXACTLY, AND EVERY CI INSTALL READS THE LOCK (operator, 2026-11-13: "Check,
then pin newest (Recommended)"; the coordinator's default 7).

WHY. `pyproject.toml` asked for `anthropic>=0.112`, so each GitHub Actions run installed the newest
SDK of its day: the theme desk's four runs there installed 1.16.0, 1.17.0, 2.3.0 and 2.6.0 between
2026-10-20 and 2026-11-09, three of them paid ($4.445, $5.8203, $13.2633), while local builds ran
0.112.0. Nothing recorded which. The pin is now exact, `requirements.lock` holds every package
with its hashes, and the five workflows that install packages install from it.

THE UPGRADE RULE, which this file cannot check: a bump repeats the $0 byte check first
(`docs/records/2026-11-13-the-anthropic-sdk-is-pinned-at-2-6-0-behind-a-byte-check.md`). What it
does check is that a bump cannot land half-done: a pyproject pin the lock disagrees with, or a
workflow that installs around the lock, fails here.
"""
from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "requirements.lock"
WORKFLOWS = sorted((ROOT / ".github" / "workflows").glob("*.yml"))

#: The install lines a workflow may run: pip itself, the lock with its hashes, and the package
#: itself with nothing added. Anything else installs a version the lock did not choose.
ALLOWED = (
    re.compile(r"python -m pip install --upgrade pip$"),
    re.compile(r"python -m pip install --require-hashes -r requirements\.lock$"),
    re.compile(r"python -m pip install --no-deps -e \.$"),
)


def _name(spec: str) -> str:
    return re.split(r"[\s\[<>=!~;]", spec, maxsplit=1)[0].lower().replace("_", "-")


def locked() -> dict[str, str]:
    """`name -> version` for every package the lock pins."""
    return {m[1].lower(): m[2] for m in re.finditer(r"^([A-Za-z0-9._-]+)==([^\s;\\]+)",
                                                    LOCK.read_text(), re.M)}


def declared() -> list[str]:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    return [*project["dependencies"], *project["optional-dependencies"]["dev"]]


#: Any pip install, however spelled (`pip3 install`, `pip3.12 install`, `uv pip install`).
INSTALL = re.compile(r"\bpip[\d.]*\s+install\b")


def unlocked_installs(workflow_text: str) -> list[str]:
    """Each `pip install` a workflow runs that is not one of `ALLOWED`. The WHOLE line must be
    an allowed install: an allowed one chained after another (`&&`, `;`) still installs it."""
    out = []
    for raw in workflow_text.splitlines():
        line = raw.strip().removeprefix("run:").strip()
        if INSTALL.search(line) and not line.startswith("#") \
                and not any(rx.fullmatch(line) for rx in ALLOWED):
            out.append(line)
    return out


def test_the_sdk_is_pinned_exactly_and_the_lock_agrees() -> None:
    (sdk,) = [d for d in declared() if _name(d) == "anthropic"]
    assert re.fullmatch(r"anthropic==\d+\.\d+\.\d+", sdk), sdk
    assert locked()["anthropic"] == sdk.split("==")[1]


def test_every_exact_pin_in_pyproject_is_the_locks_version() -> None:
    """`pyarrow==26.0.1` (its bytes embed the version) and the SDK: a pin the lock disagrees with
    is a bump done in one file only."""
    pins = {_name(d): d.split("==")[1].split(";")[0].strip() for d in declared() if "==" in d}
    assert {"anthropic", "pyarrow"} <= set(pins), pins
    lock = locked()
    assert {n: v for n, v in pins.items() if lock.get(n) != v} == {}


def test_the_lock_holds_every_package_pyproject_asks_for() -> None:
    lock = locked()
    assert [d for d in declared() if _name(d) not in lock] == []


def test_every_package_in_the_lock_carries_a_hash() -> None:
    """`--require-hashes` refuses a lock entry without one; this says which, before CI does."""
    entries = re.split(r"\n(?=[A-Za-z0-9])", LOCK.read_text().split("\n", 2)[2])
    bare = [e.split()[0] for e in entries if e.strip() and "--hash=sha256:" not in e]
    assert bare == []


@pytest.mark.parametrize("wf", WORKFLOWS, ids=lambda p: p.name)
def test_every_workflow_installs_from_the_lock(wf: Path) -> None:
    assert unlocked_installs(wf.read_text()) == [], wf.name


@pytest.mark.parametrize("line", [
    'python -m pip install -e ".[dev]"',                     # gate.yml's install until 2026-11-13
    "run: python -m pip install --upgrade pip anthropic httpx",   # validate-keys.yml's
    "python -m pip install -r requirements.lock",            # the lock without its hashes
    "python -m pip install -e .",                             # the package re-resolving its deps
    # an allowed install chained after one that is not
    "python -m pip install anthropic==3.0 && python -m pip install --no-deps -e .",
    "python -m pip install foo; python -m pip install --upgrade pip",
    "pip3 install anthropic",                                 # pip spelled another way
])
def test_an_install_around_the_lock_is_caught(line: str) -> None:
    text = f"      - name: Install\n        run: |\n          {line}\n"
    assert unlocked_installs(text) == [line.removeprefix("run: ")]


def test_the_locked_installs_pass() -> None:
    text = ("        run: |\n"
            "          python -m pip install --upgrade pip\n"
            "          python -m pip install --require-hashes -r requirements.lock\n"
            "          python -m pip install --no-deps -e .\n"
            "          # a comment naming pip install -e \".[dev]\" is not an install\n")
    assert unlocked_installs(text) == []
