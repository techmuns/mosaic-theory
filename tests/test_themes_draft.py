"""Component-A DRAFTING layer + the two CLIs (themes-draft / themes-review), network-free.

The machine DRAFTS (a name + hypothesis + an ADVISORY disposition, one LLM call per unreviewed
cluster); the human OWNS the decision (themes-review → reviews.json). These pins hold the line that
matters: a call error becomes an unassessed-error record, NEVER a fabricated draft (#123); the
drafter targets ONLY unreviewed clusters; the draft CLI is idempotent per snapshot (no double
spend); and a review is attributed "ratified advisor draft" ONLY when the analyst's decision+reason
match the draft — the advisory suggestion never becomes the decision on its own.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pytest

from vinci.cli import _cmd_themes_draft, _cmd_themes_review
from vinci.graph.llm import LlmClient, LlmError
from vinci.themes.drafts import DraftAbortedError, draft_unreviewed, unreviewed_clusters


def _cluster(cid: str, members: list[str]) -> dict[str, Any]:
    return {"cluster_id": cid, "members": [{"ticker": t, "sic": "7372"} for t in members],
            "admissibility": {"coherence_value": 0.4},
            "strength_signals": {"momentum": {"h12mo": {"value": 0.1}},
                                 "rel_strength_vs_market": {"h12mo": {"value": 0.2}},
                                 "breadth_expanding": {"value": 0.5},
                                 "crowding_overextension": {"value": -0.1}}}


def _review(key: str, members: list[str], decision: str = "park",
            reason: str = "x") -> dict[str, Any]:
    return {"key": key, "display_name": key, "decision": decision, "reviewed": "2026-06-17",
            "by": "analyst", "reason": reason, "members": members}


class _OkLlm(LlmClient):
    """Deterministic stub — returns a fixed valid draft, records how many calls it saw."""

    def __init__(self) -> None:
        self.calls = 0

    def extract(self, *, system: str, user: str, tool: dict[str, Any]) -> dict[str, Any]:
        self.calls += 1
        return {"draft_name": "Working label", "hypothesis": "these might share a driver",
                "suggested": "park", "reason": "coin-price proxy"}

    @property
    def model(self) -> str:
        return "stub-model"


class _Err4xxError(LlmError):
    status_code = 429  # what _client_error_status reads to classify a systemic 4xx (quota)


class _AlwaysFails(LlmClient):
    """Every call raises the SAME 4xx — drives the abort-fast streak."""

    def extract(self, *, system: str, user: str, tool: dict[str, Any]) -> dict[str, Any]:
        raise _Err4xxError("rate limited")

    @property
    def model(self) -> str:
        return "stub-model"


# --- drafts module -------------------------------------------------------------------------------

def test_draft_targets_only_unreviewed_clusters() -> None:
    """unreviewed_clusters / draft_unreviewed skip any cluster matched to a review by MEMBER overlap
    (ids are per-run) — the drafter never re-drafts a decided group."""
    clusters = [_cluster("T000", ["A1", "A2", "A3"]),   # reviewed (overlaps R0) → skip
                _cluster("T002", ["P1", "P2", "P3"])]    # unreviewed → drafted
    reviews = [_review("2026-06-17:R0", ["A1", "A2", "A9"])]  # 2/3 overlap ≥ .5
    assert [c["cluster_id"] for c in unreviewed_clusters(clusters, reviews)] == ["T002"]
    llm = _OkLlm()
    out = draft_unreviewed(clusters, reviews, "2026-07-14", llm)
    assert llm.calls == 1                          # ONE call — only the unreviewed cluster
    assert [d["cluster_id"] for d in out] == ["T002"]
    assert out[0]["key"] == "2026-07-14:T002" and out[0]["status"] == "drafted"
    assert out[0]["draft_name"] == "Working label" and out[0]["suggested"] == "park"


def test_draft_error_becomes_unassessed_never_fabricated() -> None:
    """A call error → an unassessed-error record carrying the reason, with draft fields None — NEVER
    a fabricated draft (the #123 pattern). A single 4xx does not abort (streak < 3)."""
    clusters = [_cluster("T002", ["P1", "P2"])]
    out = draft_unreviewed(clusters, [], "2026-07-14", _AlwaysFails())
    assert len(out) == 1
    rec = out[0]
    assert rec["status"] == "unassessed-error"
    assert rec["draft_name"] is None and rec["suggested"] is None and rec["hypothesis"] is None
    assert "_Err4xxError" in rec["error"] and rec["cluster_id"] == "T002"


def test_draft_aborts_fast_on_repeated_4xx() -> None:
    """3 consecutive same-4xx (quota/auth) → DraftAbortedError before burning the rest of the budget
    (the caller persists nothing). The partial records are carried on the exception for the log."""
    clusters = [_cluster(f"T{i:03d}", [f"M{i}"]) for i in range(6)]
    with pytest.raises(DraftAbortedError) as ei:
        draft_unreviewed(clusters, [], "2026-07-14", _AlwaysFails())
    assert ei.value.status == 429
    assert len(ei.value.drafted) == 3        # aborted AT the third failure, not after all six
    assert all(r["status"] == "unassessed-error" for r in ei.value.drafted)


def test_draft_invalid_suggested_is_unassessed_not_fabricated() -> None:
    """A tool result outside the suggested enum is rejected (fail-loud) → unassessed-error, never a
    silently-coerced draft."""
    class _BadEnum(LlmClient):
        def extract(self, *, system: str, user: str, tool: dict[str, Any]) -> dict[str, Any]:
            return {"draft_name": "X", "hypothesis": "y", "suggested": "buy", "reason": "z"}

        @property
        def model(self) -> str:
            return "stub"

    out = draft_unreviewed([_cluster("T002", ["P1"])], [], "2026-07-14", _BadEnum())
    assert out[0]["status"] == "unassessed-error" and out[0]["draft_name"] is None
    assert "invalid suggested" in out[0]["error"]


# --- CLI: themes-draft (idempotency) -------------------------------------------------------------

def _write_snapshot(tmp_path: Path, clusters: list[dict[str, Any]],
                    name: str = "20260714T120000Z__t.jsonl") -> str:
    ca = tmp_path / "data" / "scan_history" / "component-a"
    ca.mkdir(parents=True, exist_ok=True)
    (ca / name).write_text("\n".join(json.dumps(c) for c in clusters))
    return name


def _write_radar(tmp_path: Path, reviews: list[dict[str, Any]],
                 drafts: dict[str, Any] | None = None) -> Path:
    radar = tmp_path / "frontend" / "radar"
    radar.mkdir(parents=True, exist_ok=True)
    (radar / "reviews.json").write_text(json.dumps({"reviews": reviews}))
    if drafts is not None:
        (radar / "drafts.json").write_text(json.dumps(drafts))
    return radar


def test_draft_cli_idempotent_reuses_by_source(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """themes-draft reuses drafts already current for THIS snapshot (drafts.json.source == basename)
    → returns 0 and spends NO LLM call (from_config is never even constructed)."""
    monkeypatch.chdir(tmp_path)
    name = _write_snapshot(tmp_path, [_cluster("T002", ["P1", "P2"])])
    _write_radar(tmp_path, [], drafts={"scan_date": "2026-07-14", "source": name, "drafts": []})

    def _boom(*a: Any, **k: Any) -> Any:  # from_config must NOT be reached on the idempotent path
        raise AssertionError("LLM client constructed on an idempotent re-run")

    monkeypatch.setattr("vinci.graph.llm.AnthropicLlmClient.from_config", staticmethod(_boom))
    rc = _cmd_themes_draft(argparse.Namespace(force=False, scan_history_dir=None))
    assert rc == 0


# --- CLI: themes-review ---------------------------------------------------------------------------

def _review_ns(cluster: str, decision: str, reason: str, *, name: str | None = None,
               amend: bool = False) -> argparse.Namespace:
    return argparse.Namespace(cluster=cluster, decision=decision, reason=reason, name=name,
                              amend=amend)


def test_review_happy_writes_analyst_entry(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A valid key with no matching draft → by:'analyst', appended to reviews.json with the members
    resolved from the snapshot."""
    monkeypatch.chdir(tmp_path)
    _write_snapshot(tmp_path, [_cluster("T004", ["CLSK", "RIOT", "MARA"])])
    _write_radar(tmp_path, [])
    rc = _cmd_themes_review(_review_ns("2026-07-14:T004", "keep-for-checks", "worth a look"))
    assert rc == 0
    doc = json.loads((tmp_path / "frontend" / "radar" / "reviews.json").read_text())
    entry = doc["reviews"][-1]
    assert entry["key"] == "2026-07-14:T004" and entry["decision"] == "keep-for-checks"
    assert entry["by"] == "analyst" and entry["members"] == ["CLSK", "RIOT", "MARA"]
    assert entry["reviewed"] == "2026-07-14"


def test_review_ratified_when_decision_and_reason_match_draft(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """decision+reason both equal to the draft's suggested+reason → by:'analyst (ratified advisor
    draft)', and the draft name becomes the display name; a REASON mismatch falls back to 'analyst'
    (the analyst re-derived it, not merely ratified)."""
    monkeypatch.chdir(tmp_path)
    _write_snapshot(tmp_path, [_cluster("T004", ["CLSK", "RIOT"])])
    rec = {"key": "2026-07-14:T004", "cluster_id": "T004", "members": ["CLSK", "RIOT"],
           "status": "drafted", "draft_name": "Bitcoin miners", "hypothesis": "h",
           "suggested": "park", "reason": "coin-price proxy", "error": None, "model": "m"}
    drafts = {"scan_date": "2026-07-14", "source": "20260714T120000Z__t.jsonl", "drafts": [rec]}
    _write_radar(tmp_path, [], drafts=drafts)
    rc = _cmd_themes_review(_review_ns("2026-07-14:T004", "park", "coin-price proxy"))
    assert rc == 0
    doc = json.loads((tmp_path / "frontend" / "radar" / "reviews.json").read_text())
    entry = doc["reviews"][-1]
    assert entry["by"] == "analyst (ratified advisor draft)"
    assert entry["display_name"] == "Bitcoin miners"

    # a differing reason on the same decision → NOT a ratification
    _write_radar(tmp_path, [], drafts=drafts)  # reset reviews.json
    _cmd_themes_review(_review_ns("2026-07-14:T004", "park", "my own read"))
    e2 = json.loads((tmp_path / "frontend" / "radar" / "reviews.json").read_text())["reviews"][-1]
    assert e2["by"] == "analyst"


def test_review_bad_key_rejected_without_write(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A key absent from the latest snapshot → rc 2 and reviews.json is untouched (no fabricated
    review for a cluster that does not exist)."""
    monkeypatch.chdir(tmp_path)
    _write_snapshot(tmp_path, [_cluster("T004", ["CLSK"])])
    radar = _write_radar(tmp_path, [])
    before = (radar / "reviews.json").read_bytes()
    rc = _cmd_themes_review(_review_ns("2026-07-14:T999", "park", "r"))
    assert rc == 2
    assert (radar / "reviews.json").read_bytes() == before  # untouched


def test_review_dup_refused_without_amend_then_overwrites_with_amend(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An already-reviewed key is refused without --amend (rc 2, no change); --amend overwrites in
    place (no duplicate key)."""
    monkeypatch.chdir(tmp_path)
    _write_snapshot(tmp_path, [_cluster("T004", ["CLSK", "RIOT"])])
    existing = _review("2026-07-14:T004", ["CLSK", "RIOT"], decision="park", reason="first")
    radar = _write_radar(tmp_path, [existing])
    before = (radar / "reviews.json").read_bytes()

    rc = _cmd_themes_review(_review_ns("2026-07-14:T004", "reject", "second"))
    assert rc == 2 and (radar / "reviews.json").read_bytes() == before  # refused, untouched

    rc2 = _cmd_themes_review(_review_ns("2026-07-14:T004", "reject", "second", amend=True))
    assert rc2 == 0
    reviews = json.loads((radar / "reviews.json").read_text())["reviews"]
    keyed = [r for r in reviews if r["key"] == "2026-07-14:T004"]
    assert len(keyed) == 1 and keyed[0]["decision"] == "reject"  # overwritten, not duplicated


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
