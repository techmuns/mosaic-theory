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
from datetime import UTC, date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from tests.test_operator_decision import _process_zone
from vinci.cli import _cmd_themes_draft, _cmd_themes_review
from vinci.graph.llm import LlmClient, LlmError
from vinci.themes.drafts import (
    PROMPT_VERSION,
    DraftAbortedError,
    _cluster_prompt,
    _drafts_current,
    _recent_precedent,
    draft_cluster,
    draft_targets,
    draft_unreviewed,
    unreviewed_clusters,
)


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


# --- v2 rubric: few-shot precedent, targeting, versioned idempotency -----------------------------

class _CapturingLlm(LlmClient):
    """Records the last user prompt so a test can assert what precedent reached the model."""

    def __init__(self) -> None:
        self.last_user = ""

    def extract(self, *, system: str, user: str, tool: dict[str, Any]) -> dict[str, Any]:
        self.last_user = user
        return {"draft_name": "X", "hypothesis": "h", "suggested": "park", "reason": "r"}

    @property
    def model(self) -> str:
        return "stub"


def test_precedent_injected_and_self_excluded() -> None:
    """draft_cluster injects the fund's recent decisions into the prompt as few-shot precedent, but
    EXCLUDES the drafted cluster's own recorded decision (member overlap) — no self-leak."""
    cluster = _cluster("T004", ["CLSK", "RIOT"])
    reviews = [
        _review("2026-07-14:T004", ["CLSK", "RIOT"], decision="park", reason="coin-price proxy"),
        _review("2026-06-17:R1", ["AAA", "BBB"], decision="reject", reason="collapsed gimmicks"),
        _review("2026-07-15:R2", ["CCC", "DDD"], decision="park", reason="metal proxy"),
    ]
    llm = _CapturingLlm()
    draft_cluster(cluster, "2026-07-14:T004", llm, reviews)
    assert "collapsed gimmicks" in llm.last_user      # OTHER precedent injected
    assert "metal proxy" in llm.last_user
    assert "coin-price proxy" not in llm.last_user     # SELF-EXCLUDED (same members) — no self-leak


def test_recent_precedent_orders_by_date_and_excludes_self() -> None:
    cluster = _cluster("T004", ["CLSK", "RIOT"])
    older = _review("k2", ["A", "B"], decision="reject", reason="old")
    newer = _review("k3", ["C", "D"], decision="park", reason="new")
    older["reviewed"], newer["reviewed"] = "2026-06-17", "2026-07-15"
    selfrev = _review("k1", ["CLSK", "RIOT"], reason="self")
    pairs = _recent_precedent([selfrev, older, newer], cluster)
    assert all(reason != "self" for _, reason in pairs)   # self excluded
    assert pairs[0] == ("park", "new")                    # most recent first


def test_draft_targets_normal_vs_include_reviewed() -> None:
    """Normal targets the UNREVIEWED set; include_reviewed targets the clusters reviewed FOR THIS
    scan (the face-validity re-check set)."""
    clusters = [_cluster("T004", ["CLSK", "RIOT"]), _cluster("T099", ["ZZ", "YY"])]
    reviews = [_review("2026-07-14:T004", ["CLSK", "RIOT"])]  # T004 reviewed for this scan
    normal = draft_targets(clusters, reviews, "2026-07-14", include_reviewed=False)
    reviewed = draft_targets(clusters, reviews, "2026-07-14", include_reviewed=True)
    assert [c["cluster_id"] for c in normal] == ["T099"]      # unreviewed only
    assert [c["cluster_id"] for c in reviewed] == ["T004"]    # reviewed-for-this-scan only


def test_drafts_current_gates_on_source_and_version() -> None:
    src, ver = "20260714T162125Z__x.jsonl", PROMPT_VERSION
    assert _drafts_current({"source": src, "prompt_version": ver}, src, ver)
    assert not _drafts_current({"source": src, "prompt_version": "old"}, src, ver)  # version bump
    assert not _drafts_current({"source": "other", "prompt_version": ver}, src, ver)  # src change
    assert not _drafts_current({"source": src}, src, ver)  # legacy pointer, no version


def test_cluster_prompt_formats_stats_as_percent() -> None:
    """rel-strength / momentum fractions render as signed percents so the model can cite them."""
    prompt = _cluster_prompt(_cluster("T004", ["A", "B"]))  # rel12=0.2, mom12=0.1 in the helper
    assert "+20%" in prompt and "+10%" in prompt


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


def _draft_ns(*, force: bool = False, include_reviewed: bool = False) -> argparse.Namespace:
    return argparse.Namespace(force=force, include_reviewed=include_reviewed, scan_history_dir=None)


def test_draft_cli_idempotent_reuses_same_source_and_version(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """themes-draft reuses drafts current for THIS snapshot AND this prompt version → returns 0 and
    spends NO LLM call (from_config is never even constructed)."""
    monkeypatch.chdir(tmp_path)
    name = _write_snapshot(tmp_path, [_cluster("T002", ["P1", "P2"])])
    _write_radar(tmp_path, [], drafts={"scan_date": "2026-07-14", "source": name,
                                       "prompt_version": PROMPT_VERSION, "drafts": []})

    def _boom(*a: Any, **k: Any) -> Any:  # from_config must NOT be reached on the idempotent path
        raise AssertionError("LLM client constructed on an idempotent re-run")

    monkeypatch.setattr("vinci.graph.llm.AnthropicLlmClient.from_config", staticmethod(_boom))
    rc = _cmd_themes_draft(_draft_ns())
    assert rc == 0


def test_draft_cli_version_bump_regenerates(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A committed pointer at a DIFFERENT prompt version is NOT reused — themes-draft regenerates
    (constructs the client, drafts, and writes the new version into drafts.json)."""
    monkeypatch.chdir(tmp_path)
    name = _write_snapshot(tmp_path, [_cluster("T002", ["P1", "P2"])])
    # committed under an OLD version → must NOT be reused under the current PROMPT_VERSION
    _write_radar(tmp_path, [], drafts={"scan_date": "2026-07-14", "source": name,
                                       "prompt_version": "0-legacy", "drafts": [
                                           {"key": "x", "status": "drafted"}]})
    monkeypatch.setattr("vinci.graph.llm.AnthropicLlmClient.from_config",
                        staticmethod(lambda *a, **k: _OkLlm()))
    rc = _cmd_themes_draft(_draft_ns())
    assert rc == 0
    out = json.loads((tmp_path / "frontend" / "radar" / "drafts.json").read_text())
    assert out["prompt_version"] == PROMPT_VERSION            # regenerated at the current version
    assert out["drafts"][0]["cluster_id"] == "T002"           # real re-draft, not the stale pointer


def test_draft_cli_legacy_pointer_without_version_regenerates(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A #130-era pointer with NO prompt_version is stale → regenerate (never silently reused)."""
    monkeypatch.chdir(tmp_path)
    name = _write_snapshot(tmp_path, [_cluster("T002", ["P1", "P2"])])
    _write_radar(tmp_path, [], drafts={"scan_date": "2026-07-14", "source": name, "drafts": []})
    monkeypatch.setattr("vinci.graph.llm.AnthropicLlmClient.from_config",
                        staticmethod(lambda *a, **k: _OkLlm()))
    rc = _cmd_themes_draft(_draft_ns())
    assert rc == 0
    out = json.loads((tmp_path / "frontend" / "radar" / "drafts.json").read_text())
    assert out["prompt_version"] == PROMPT_VERSION


def _no_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(*a: Any, **k: Any) -> Any:
        raise AssertionError("LLM client constructed on an empty target set")
    monkeypatch.setattr("vinci.graph.llm.AnthropicLlmClient.from_config", staticmethod(_boom))


def test_draft_cli_include_reviewed_empty_fails_loud(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--include-reviewed with NO clusters reviewed for this scan → rc 2 (fail loud), NEVER a silent
    no-op, and NO LLM constructed — the operator-flagged failure mode the guard exists for."""
    monkeypatch.chdir(tmp_path)
    _write_snapshot(tmp_path, [_cluster("T002", ["P1", "P2"])])  # a cluster exists...
    _write_radar(tmp_path, [])                                   # ...but nothing reviewed this scan
    _no_llm(monkeypatch)
    assert _cmd_themes_draft(_draft_ns(include_reviewed=True)) == 2


def test_draft_cli_normal_empty_inbox_is_benign_not_error(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Normal path with every cluster already reviewed → empty unreviewed set is a SUCCESS state
    (inbox triaged): rc 0, no LLM, and the committed pointer is left untouched (not overwritten)."""
    monkeypatch.chdir(tmp_path)
    _write_snapshot(tmp_path, [_cluster("T002", ["P1", "P2"])])
    _write_radar(tmp_path, [_review("2026-07-14:T002", ["P1", "P2"])])  # T002 reviewed → none left
    _no_llm(monkeypatch)
    assert _cmd_themes_draft(_draft_ns()) == 0                # benign, NOT rc 2
    assert not (tmp_path / "frontend" / "radar" / "drafts.json").exists()  # pointer left untouched


# --- CLI: themes-review ---------------------------------------------------------------------------

def _review_ns(cluster: str, decision: str, reason: str, *, name: str | None = None,
               amend: bool = False) -> argparse.Namespace:
    return argparse.Namespace(cluster=cluster, decision=decision, reason=reason, name=name,
                              amend=amend)


def test_review_happy_writes_analyst_entry(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A valid key with no matching draft → by:'analyst', appended to reviews.json with the members
    resolved from the snapshot. `reviewed` is the DATE OF REVIEW (today), NOT the scan date — the
    scan date already lives in the key (the 'Reviewed' column means when-reviewed)."""
    monkeypatch.chdir(tmp_path)
    _write_snapshot(tmp_path, [_cluster("T004", ["CLSK", "RIOT", "MARA"])])
    _write_radar(tmp_path, [])
    rc = _cmd_themes_review(_review_ns("2026-07-14:T004", "keep-for-checks", "worth a look"))
    assert rc == 0
    doc = json.loads((tmp_path / "frontend" / "radar" / "reviews.json").read_text())
    entry = doc["reviews"][-1]
    assert entry["key"] == "2026-07-14:T004" and entry["decision"] == "keep-for-checks"
    assert entry["by"] == "analyst" and entry["members"] == ["CLSK", "RIOT", "MARA"]
    # today on the analyst's calendar, not the scan date (and not UTC's: see the real-zone pin)
    assert entry["reviewed"] == date.today().isoformat()
    assert entry["reviewed"] != "2026-07-14"  # NOT the scan date (regression pin)


def test_a_review_made_now_is_dated_on_the_local_calendar_under_a_real_zone(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A REVIEW IS A HUMAN DECISION, dated on the operator's calendar like every other one (#794):
    stamped on UTC's, a review recorded between local midnight and UTC's (00:00–05:30 IST) was
    dated the day before. Drives the real command under the process's REAL zone, always in the
    divergent case: UTC−12 reads yesterday until 12:00 UTC and UTC+14 reads tomorrow from 10:00
    UTC, and switching at 11:00 keeps the zone's own midnight an hour from the run."""
    now = datetime.now(UTC)
    offset = -12 if now.hour < 11 else 14
    monkeypatch.chdir(tmp_path)
    _write_snapshot(tmp_path, [_cluster("T004", ["CLSK", "RIOT", "MARA"])])
    _write_radar(tmp_path, [])
    with _process_zone(offset):
        local_today = datetime.now(timezone(timedelta(hours=offset))).date()
        assert date.today() == local_today != now.date(), "the run is not the divergent case"
        rc = _cmd_themes_review(_review_ns("2026-07-14:T004", "park", "a reason"))
    assert rc == 0
    doc = json.loads((tmp_path / "frontend" / "radar" / "reviews.json").read_text())
    assert doc["reviews"][-1]["reviewed"] == local_today.isoformat(), "dated on UTC's calendar"


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
    place (no duplicate key) and PRESERVES extra fields (map_ref) + the prior display_name when no
    new name is given — an amend must not silently drop data the Log view renders."""
    monkeypatch.chdir(tmp_path)
    _write_snapshot(tmp_path, [_cluster("T004", ["CLSK", "RIOT"])])
    existing = _review("2026-07-14:T004", ["CLSK", "RIOT"], decision="park", reason="first")
    existing["display_name"] = "Bitcoin miners"  # a curated name the amend must keep
    existing["map_ref"] = "bitcoin-miners"
    radar = _write_radar(tmp_path, [existing])
    before = (radar / "reviews.json").read_bytes()

    rc = _cmd_themes_review(_review_ns("2026-07-14:T004", "reject", "second"))
    assert rc == 2 and (radar / "reviews.json").read_bytes() == before  # refused, untouched

    rc2 = _cmd_themes_review(_review_ns("2026-07-14:T004", "reject", "second", amend=True))
    assert rc2 == 0
    reviews = json.loads((radar / "reviews.json").read_text())["reviews"]
    keyed = [r for r in reviews if r["key"] == "2026-07-14:T004"]
    assert len(keyed) == 1 and keyed[0]["decision"] == "reject"  # overwritten, not duplicated
    assert keyed[0]["map_ref"] == "bitcoin-miners"              # extra field preserved
    assert keyed[0]["display_name"] == "Bitcoin miners"        # prior name kept (no --name given)
    assert keyed[0]["reason"] == "second"                      # managed field updated


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
