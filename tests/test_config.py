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


def test_the_committed_corpora_are_not_empty() -> None:
    """CORPUS FLOOR — queue item 31(b). Measured 2026-07-28, not reasoned.

    Thirteen tests across the suite iterate a committed corpus and **pass when that corpus is
    empty**. Emptying `data/dossiers` + `scenarios/` in a throwaway worktree and re-running left
    them green: five scenario-driven (`test_every_committed_scenario_record_is_register_clean`,
    `test_new_fields_are_additive_so_existing_records_still_validate`,
    `test_every_committed_record_is_class_compliant_and_seal_clean`,
    `test_committed_records_that_opened_a_position_carry_their_entry`,
    `test_every_committed_record_result_matches_its_own_facts`) and eight dossier-driven
    (`test_committed_own_history_agrees_with_its_sibling_range_position`, both
    `test_committed_peer_rosters_*`, `test_download_menu_offers_three_scopes_*`,
    `test_13_fields_reach_both_twins_and_the_mirrors_e2e`,
    `test_card_verdict_keys_read_by_js_are_emitted_by_build`, `test_ref_value_py_js_parity`,
    `test_committed_dossiers_carry_no_ratio_as_a_currency_amount`). Most are named
    `test_every_committed_…` — a name promising fleet coverage the assertion does not enforce.

    This is the cheap half of the fix: ONE loud red for the EMPTYING case, which is the mode all
    thirteen share. It does NOT cover the other mode — a full corpus where a test's own FILTER
    matches nothing (how the pre-#238 fixture decayed on CNXC's re-assembly). That needs a
    per-test floor and a per-test judgement, which stays open under 31(b).
    """
    root = Path(__file__).resolve().parents[1]
    dossiers = [p for p in (root / "data" / "dossiers").iterdir() if (p / "dossier.json").exists()]
    records = [p for p in (root / "scenarios").glob("*.json") if not p.name.startswith("_")]

    assert len(dossiers) >= 10, (
        f"the committed dossier corpus holds {len(dossiers)} names — thirteen fleet tests pass "
        "VACUOUSLY on an empty corpus, so a corpus that shrank unexpectedly must red HERE, loudly, "
        "rather than turn a dozen assertions into no-ops quietly")
    assert len(records) >= 5, (
        f"the committed scenario corpus holds {len(records)} records — same reason: five "
        "record-driven tests go green-and-hollow when it empties")


def test_every_preview_server_serves_an_absolute_directory() -> None:
    """A preview config must name the tree it serves — the incident, 2026-07-28.

    The repo is checked out in several worktrees at once. ``.claude/launch.json``'s ``frontend``
    entry passed a RELATIVE ``--directory frontend``, so it served whichever checkout the server
    process happened to start in — in practice the PRIMARY repo, i.e. another session's working
    tree. The first preview of the 26a extraction stamp rendered THAT tree's CNXC and showed no
    stamp, which reads exactly like "the feature does not work". Trusted, that is an hour spent
    debugging working code; the reverse case is worse — a broken render previewing as fine because
    the bytes on screen came from a different branch.

    Every other entry already uses an absolute path and names its tree. This keeps it that way."""
    import json

    cfg = json.loads((Path(__file__).resolve().parents[1] / ".claude" / "launch.json").read_text())
    relative = []
    for c in cfg.get("configurations", []):
        args = c.get("runtimeArgs", [])
        if "--directory" not in args:
            continue                                    # not a static-file server; nothing to bind
        d = args[args.index("--directory") + 1]
        if not d.startswith("/"):
            relative.append(f"{c.get('name')} -> {d!r}")
    assert not relative, (
        "preview server(s) with a RELATIVE --directory, which resolve against whatever CWD the "
        f"server starts in rather than a named tree: {relative}. Use an absolute path — a preview "
        "that silently reads the wrong worktree can only ever mislead.")
