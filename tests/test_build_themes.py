"""Pin the theme viewer's build.py display-transform to the backend it MIRRORS.

frontend/build.py stays stdlib-only (deploy-safe — Cloudflare Pages runs it with no pydantic/vinci),
so it re-declares the zero-RATIFIED honesty label, the UNDEFINED-spread reasons, and the driver-tie
gate as literals. This test runs where the backend IS importable and asserts those literals have NOT
drifted from vinci.themes.forward / vinci.themes.exposure — the honest-framing strings are
load-bearing (the viewer must not oversell the theme edge), so a silent divergence is a real defect.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

from vinci.themes.exposure import _BASIS_FOR, _effective_rank
from vinci.themes.forward import HOLD_NONE_HONESTY, FrozenBaskets, undefined_ratified_measures
from vinci.themes.schemas import DriverTie, ExposureConcreteness

_BUILD_PY = Path(__file__).resolve().parents[1] / "frontend" / "build.py"


def _load_build() -> Any:
    """Load frontend/build.py by path (frontend/ is not a package). Importing does NOT run main()
    (guarded by __main__), and the module body does only path math — no I/O."""
    spec = importlib.util.spec_from_file_location("_viewer_build", _BUILD_PY)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_BUILD: Any = _load_build()


def test_honesty_label_matches_backend() -> None:
    assert _BUILD._HOLD_NONE_HONESTY == HOLD_NONE_HONESTY


def test_undefined_measures_match_backend() -> None:
    baskets = FrozenBaskets(
        driver="d", freeze_timestamp="2026-07-03T00:00:00", ratified=(), passed=("A",),
        all_committed=("A",), entry_dates={"A": "2026-07-03"}, layer_of={"A": "x"})
    backend = [[m, r] for m, r in undefined_ratified_measures(baskets)]
    assert backend == _BUILD._UNDEFINED_MEASURES
    # and the empty BUY leg is what makes them undefined (guards the premise)
    assert baskets.ratified == ()


def test_tie_gate_matches_backend() -> None:
    """build._eff_basis(grade, tie) must equal the backend's _BASIS_FOR[_effective_rank(...)] for
    every (concreteness, tie) — so the viewer's tier shape derives identically to exposure_basis."""
    for conc in ExposureConcreteness:
        for tie in DriverTie:
            backend_basis = _BASIS_FOR[_effective_rank(conc, tie)].value  # e.g. committed-capacity…
            short = _BUILD._eff_basis(conc.value, tie.value)
            # map the backend's long ExposureBasis to the viewer's short bucket for comparison
            expect = {
                "binding-contracts-with-terms": "binding",
                "quantified-revenue-share": "quantified",
                "committed-capacity-or-capex": "committed",
                "aspirational-intent-only": "aspirational",
                "no-theme-exposure-disclosed": "none",
            }[backend_basis]
            assert short == expect, f"tie-gate drift at ({conc.value}, {tie.value})"


def test_eff_basis_caps_by_tie() -> None:
    # a binding-contract fact: driver-specific keeps it binding, indirect caps at committed,
    # not-driver caps at aspirational (the direction the tie gate encodes)
    assert _BUILD._eff_basis("binding-contract", "driver-specific") == "binding"
    assert _BUILD._eff_basis("binding-contract", "indirect") == "committed"
    assert _BUILD._eff_basis("binding-contract", "not-driver") == "aspirational"


def test_naive_cohort_is_committed_tier_not_surfaced_universe() -> None:
    """The NAIVE forward cohort = the equal-weight baseline over the WHOLE committed tier
    (len(all_committed)), NOT the surfaced universe — mirrors the backend's NAIVE-N where
    N = len(baskets.all_committed) (forward.py:505, cli.py:689). Regression: build.py fed `surfaced`
    (scan breadth) into cohorts.naive, so a theme that froze a SUBSET of surfaced rendered an
    ~8x-overstated cohort (ai-datacenter shipped naive=450 beside a 56-name committed tier)."""
    baskets = {
        "driver": "AI-datacenter value chain", "freeze_timestamp": "2026-07-03T00:00:00",
        "ratified": [], "passed": ["A", "B"], "all_committed": ["A", "B"],
        "watchlist": [], "avoid_controls": [], "real_tier": [],
    }
    ledger = [
        {"ticker": t, "machine_grade": "committed-capacity", "driver_tie": "indirect",
         "source_ref": "", "rationale": ""} for t in ("A", "B")
    ]
    # a WIDE scan: 8 names carry exposure, 2 disclose none → surfaced = 8; the frozen committed tier
    # is only 2. The naive baseline must track the tier (2), never the universe (8).
    scan = ([{"exposure_basis": "committed-capacity-or-capex"}] * 8
            + [{"exposure_basis": "no-theme-exposure-disclosed"}] * 2)
    disp = _BUILD._theme_display(baskets, ledger, scan)
    assert disp["surfacedCount"] == 8   # scan breadth (legitimately the surfaced universe)
    assert disp["frozenCount"] == 2     # the committed tier that was frozen
    assert disp["forward"]["cohorts"]["naive"] == 2         # == len(all_committed), NOT surfaced
    assert disp["forward"]["cohorts"]["naive"] != disp["surfacedCount"]
    # fallback: a freeze predating the all_committed field → naive tracks the frozen ledger size
    legacy = {k: v for k, v in baskets.items() if k != "all_committed"}
    assert _BUILD._theme_display(legacy, ledger, scan)["forward"]["cohorts"]["naive"] == 2


def test_edgar_url_shape() -> None:
    u = _BUILD._edgar_url("0001493152", "0001493152-26-022095")
    assert u == ("https://www.sec.gov/Archives/edgar/data/1493152/"
                 "000149315226022095/0001493152-26-022095-index.htm")
    assert _BUILD._edgar_url("0001493152", "no accession here") is None  # no accession → no link


def test_radar_sweep_seeded_fallback_and_next_due() -> None:
    """No component-a manifest → seeded June-17 harvest; next_due = last_run + 30d; the command is
    single-sourced from build.py (the Radar screen renders it, never hardcodes it)."""
    p = _BUILD._radar_sweep_payload(Path("/no/such/manifest.jsonl"))
    assert p["last_run"] == _BUILD._SWEEP_SEED_DATE == "2026-06-17"
    assert p["source"] == "seeded"
    assert p["next_due"] == "2026-07-17"  # 2026-06-17 + 30 days
    assert p["command"] == "python -m vinci.cli themes"


def test_radar_sweep_reads_manifest_latest_ts(tmp_path: Path) -> None:
    """A multi-driver ROOT manifest → last_run = the latest COMPONENT-A ts; a LATER row from another
    driver is IGNORED (the sweep bar reports the co-movement sweep, not any driver's run)."""
    m = tmp_path / "manifest.jsonl"
    m.write_text(
        '{"ts": "2026-06-17T12:00:00Z", "driver_slug": "component-a"}\n'
        '{"ts": "2026-07-01T09:30:00Z", "driver_slug": "component-a"}\n'
        '{"ts": "2026-07-20T00:00:00Z", "driver_slug": "other-driver"}\n'  # later → MUST be ignored
    )
    p = _BUILD._radar_sweep_payload(m)
    assert p["last_run"] == "2026-07-01" and p["source"] == "manifest"  # NOT 2026-07-20
    assert p["next_due"] == "2026-07-31"  # 2026-07-01 + 30 days


def test_radar_sweep_seeds_when_manifest_has_no_component_a_row(tmp_path: Path) -> None:
    """A manifest that EXISTS but has only other drivers → seeded (never another driver's ts)."""
    m = tmp_path / "manifest.jsonl"
    m.write_text('{"ts": "2026-07-20T00:00:00Z", "driver_slug": "other-driver"}\n')
    p = _BUILD._radar_sweep_payload(m)
    assert p["last_run"] == _BUILD._SWEEP_SEED_DATE == "2026-06-17"
    assert p["source"] == "seeded"


def test_emit_radar_sweep_end_to_end(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """END-TO-END seam (the #125 path bug at the layer it failed): record_snapshot writes a REAL
    multi-driver manifest at data/scan_history/manifest.jsonl; emit_radar_sweep must read THAT path
    (not the never-written component-a/manifest.jsonl) and filter to component-a — so a later
    other-driver run does not masquerade as the sweep's last run."""
    from datetime import UTC, datetime

    from vinci.themes.scan_history import record_snapshot

    hist = tmp_path / "data" / "scan_history"
    record_snapshot([{"cluster_id": "T000"}], driver_slug="component-a", driver_desc="co-movement",
                    history_root=hist, now=datetime(2026, 7, 14, 16, 21, 25, tzinfo=UTC),
                    git_sha="119ecbb", n_scanned=1783, tier_field=None)
    record_snapshot([{"x": 1}], driver_slug="other-driver", driver_desc="decoy (later run)",
                    history_root=hist, now=datetime(2026, 7, 20, 0, 0, 0, tzinfo=UTC),
                    git_sha="deadbee", n_scanned=1, tier_field=None)
    monkeypatch.setattr(_BUILD, "ROOT", tmp_path)
    monkeypatch.setattr(_BUILD, "HERE", tmp_path / "frontend")
    _BUILD.emit_radar_sweep()
    payload = json.loads((tmp_path / "frontend" / "radar" / "sweep.json").read_text())
    assert payload["last_run"] == "2026-07-14"  # component-a ts, NOT other-driver's 2026-07-20
    assert payload["source"] == "manifest"
    assert payload["next_due"] == "2026-08-13"  # 2026-07-14 + 30 days
    assert payload["command"] == "python -m vinci.cli themes"


def _review(key: str, members: list[str], decision: str = "parked") -> dict[str, Any]:
    return {"key": key, "display_name": key, "decision": decision, "reviewed": "2026-07-13",
            "by": "analyst", "reason": "x", "members": members}


def _cluster(cid: str, members: list[str], rel12: float = 0.0,
             sics: list[str] | None = None) -> dict[str, Any]:
    mem = ([{"ticker": t} for t in members] if sics is None
           else [{"ticker": t, "sic": s} for t, s in zip(members, sics, strict=True)])
    return {"cluster_id": cid, "members": mem,
            "admissibility": {"coherence_value": 0.4},
            "strength_signals": {"momentum": {"h12mo": {"value": 0.1}},
                                 "rel_strength_vs_market": {"h12mo": {"value": rel12}},
                                 "breadth_expanding": {"value": 0.5},
                                 "crowding_overextension": {"value": -0.1}}}


def _run_inbox_log(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, reviews: list[dict[str, Any]],
                   clusters: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    ca = tmp_path / "data" / "scan_history" / "component-a"
    ca.mkdir(parents=True)
    (ca / "20260714T120000Z__t.jsonl").write_text("\n".join(json.dumps(c) for c in clusters))
    radar = tmp_path / "frontend" / "radar"
    radar.mkdir(parents=True)
    (radar / "reviews.json").write_text(json.dumps({"reviews": reviews}))
    monkeypatch.setattr(_BUILD, "ROOT", tmp_path)
    monkeypatch.setattr(_BUILD, "HERE", tmp_path / "frontend")
    _BUILD.emit_radar_inbox_log()
    return (json.loads((radar / "inbox.json").read_text()),
            json.loads((radar / "log.json").read_text()))


def test_radar_inbox_log_join(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The emitter's matcher: 50%-boundary is inclusive (matched), below-boundary drifts to inbox, a
    review with no ≥50% cluster is 'gone', deltas are recorded, and matching is by MEMBER OVERLAP
    (disjoint tickers → no accidental id match)."""
    reviews = [
        _review("2026-06-17:T000", ["A1", "A2", "A3", "A4"]),
        _review("2026-06-17:T001", ["B1", "B2"], "rejected"),   # 50% boundary vs K1
        _review("2026-06-17:T003", ["C1", "C2"]),               # GONE (no cluster)
        _review("2026-06-17:T005", ["D1", "D2", "D3"]),         # drifts below → GONE, K3 → inbox
    ]
    clusters = [
        _cluster("T000", ["A1", "A2", "A5"]),          # 2/3 = .67 ≥ .5 → matched; +A5 −A3,A4
        _cluster("T001", ["B1", "B9"]),                # 1/2 = .50 → matched (boundary INCLUSIVE)
        _cluster("T002", ["P1", "P2", "P3"], rel12=0.3),  # 0 overlap → inbox (new)
        _cluster("T004", ["D1", "D8", "D9"]),          # 1/3 = .33 < .5 → inbox (drifted below)
    ]
    inbox, log = _run_inbox_log(tmp_path, monkeypatch, reviews, clusters)
    assert inbox["scan_date"] == "2026-07-14"
    assert [e["cluster_id"] for e in inbox["inbox"]] == ["T002", "T004"]  # sorted, new + drifted
    t002 = inbox["inbox"][0]
    assert t002["label"] == "P1 P2 +1" and t002["rel12"] == 0.3 and t002["coherence"] == 0.4
    by_key = {r["key"]: r for r in log["reviews"]}
    assert [r["key"] for r in log["reviews"]] == [  # deterministic key order; every review present
        "2026-06-17:T000", "2026-06-17:T001", "2026-06-17:T003", "2026-06-17:T005"]
    assert by_key["2026-06-17:T001"]["match"]["status"] == "matched"          # 50% boundary
    assert by_key["2026-06-17:T000"]["match"]["added"] == ["A5"]              # changed counts
    assert by_key["2026-06-17:T000"]["match"]["dropped"] == ["A3", "A4"]
    assert by_key["2026-06-17:T003"]["match"]["status"] == "gone"             # no cluster
    assert by_key["2026-06-17:T005"]["match"]["status"] == "gone"             # drifted below → gone


def test_radar_inbox_log_deterministic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Inbox is sorted by cluster_id (not snapshot order) and re-running is byte-identical."""
    reviews = [_review("2026-06-17:T000", ["A", "B"])]
    clusters = [_cluster("T009", ["C", "D"]), _cluster("T002", ["E", "F"])]  # both new → inbox
    inbox, _ = _run_inbox_log(tmp_path, monkeypatch, reviews, clusters)
    assert [e["cluster_id"] for e in inbox["inbox"]] == ["T002", "T009"]  # sorted, not C,D order
    b1 = (tmp_path / "frontend" / "radar" / "inbox.json").read_bytes()
    _BUILD.emit_radar_inbox_log()  # re-run over the same inputs
    assert (tmp_path / "frontend" / "radar" / "inbox.json").read_bytes() == b1


def test_radar_inbox_log_non_destructive_without_snapshot(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Deploy-safe: reviews.json present but NO component-a snapshot → the emitter must NOT clobber
    the committed inbox.json/log.json (the deploy keeps serving the last real local emission)."""
    radar = tmp_path / "frontend" / "radar"
    radar.mkdir(parents=True)
    rv = {"reviews": [_review("2026-06-17:T000", ["A", "B"])]}
    (radar / "reviews.json").write_text(json.dumps(rv))
    (radar / "inbox.json").write_text('{"sentinel": true}')  # committed artifact — must survive
    (radar / "log.json").write_text('{"sentinel": true}')
    monkeypatch.setattr(_BUILD, "ROOT", tmp_path)  # no component-a snapshot dir under tmp_path
    monkeypatch.setattr(_BUILD, "HERE", tmp_path / "frontend")
    _BUILD.emit_radar_inbox_log()
    assert json.loads((radar / "inbox.json").read_text()) == {"sentinel": True}
    assert json.loads((radar / "log.json").read_text()) == {"sentinel": True}


def _sic_cluster(sics: list[str]) -> dict[str, Any]:
    members = [{"ticker": f"X{i}", "sic": s} for i, s in enumerate(sics)]
    return {"cluster_id": "T0", "members": members}


def test_industry_hint_majority() -> None:
    """A strict majority (3 of 5 share the SIC) → '<name> · N/total'."""
    h = _BUILD._industry_hint(_sic_cluster(["3674", "3674", "3674", "3825", "3827"]))
    assert h == "SIC 3674 · 3/5"   # sic-only fixture → pre-field degrade


def test_industry_hint_mixed() -> None:
    """No majority (all distinct) → 'mixed: <top> N · <second> M' (member order breaks the tie)."""
    h = _BUILD._industry_hint(_sic_cluster(["7370", "6282", "7389"]))
    assert h == "mixed: SIC 7370 1 · SIC 6282 1"   # pre-field degrade: raw codes, no name invented


def test_industry_hint_single_sic_non_majority() -> None:
    """One distinct SIC, not a majority (rest carry no SIC) → single industry + coverage, not
    the degenerate 'mixed: X · X 0'."""
    mem = [{"ticker": "A", "sic": "3674"}, {"ticker": "B"}, {"ticker": "C"}]
    assert _BUILD._industry_hint({"cluster_id": "T0", "members": mem}) == "SIC 3674 · 1/3"


def test_industry_hint_only_on_unreviewed_inbox(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The hint is emitted ONLY for unreviewed (inbox) clusters; a matched group goes to the log
    with no industry_hint (reviewed rows keep the analyst's name)."""
    reviews = [_review("2026-06-17:T000", ["A1", "A2"])]  # matches cluster T000
    clusters = [_cluster("T000", ["A1", "A2"], sics=["3674", "3674"]),  # matched → log (no hint)
                _cluster("T002", ["P1", "P2"], sics=["7372", "7372"])]  # unreviewed → inbox (hint)
    inbox, log = _run_inbox_log(tmp_path, monkeypatch, reviews, clusters)
    assert inbox["inbox"][0]["cluster_id"] == "T002"
    assert inbox["inbox"][0]["industry_hint"] == "SIC 7372 · 2/2"   # sic-only fixture → degrade
    assert all("industry_hint" not in r for r in log["reviews"])


def _draft_rec(cid: str, members: list[str], *, name: str = "Coin proxies",
               suggested: str = "park", reason: str = "coin-price proxy",
               status: str = "drafted") -> dict[str, Any]:
    drafted = status == "drafted"
    return {"key": f"2026-07-14:{cid}", "cluster_id": cid, "members": members, "status": status,
            "draft_name": name if drafted else None,
            "hypothesis": "these track the coin price" if drafted else None,
            "suggested": suggested if drafted else None,
            "reason": reason if drafted else None,
            "error": None if drafted else "LlmError: quota", "model": "m"}


def _run_inbox_with_drafts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                           reviews: list[dict[str, Any]], clusters: list[dict[str, Any]],
                           drafts: list[dict[str, Any]]) -> dict[str, Any]:
    ca = tmp_path / "data" / "scan_history" / "component-a"
    ca.mkdir(parents=True)
    (ca / "20260714T120000Z__t.jsonl").write_text("\n".join(json.dumps(c) for c in clusters))
    radar = tmp_path / "frontend" / "radar"
    radar.mkdir(parents=True)
    (radar / "reviews.json").write_text(json.dumps({"reviews": reviews}))
    (radar / "drafts.json").write_text(json.dumps(
        {"scan_date": "2026-07-14", "source": "20260714T120000Z__t.jsonl", "drafts": drafts}))
    monkeypatch.setattr(_BUILD, "ROOT", tmp_path)
    monkeypatch.setattr(_BUILD, "HERE", tmp_path / "frontend")
    _BUILD.emit_radar_inbox_log()
    inbox: dict[str, Any] = json.loads((radar / "inbox.json").read_text())
    return inbox


def test_radar_inbox_draft_join(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An advisory draft joins onto its unreviewed inbox row by MEMBER overlap (the draft's own
    cluster_id differs — ids are per-run), carrying draft_name / draft_read (the terse reason) /
    draft_suggested. The fuller hypothesis is NOT inlined (it stays in drafts.json)."""
    clusters = [_cluster("T002", ["P1", "P2", "P3"], rel12=0.3)]  # unreviewed → inbox
    drafts = [_draft_rec("K9", ["P1", "P2", "P3"], name="Coin proxies", suggested="park",
                         reason="coin-price proxy")]
    inbox = _run_inbox_with_drafts(tmp_path, monkeypatch, [], clusters, drafts)
    row = inbox["inbox"][0]
    assert row["cluster_id"] == "T002"
    assert row["draft_name"] == "Coin proxies"
    assert row["draft_suggested"] == "park"
    assert row["draft_read"] == "coin-price proxy"   # read == the terse advisory reason
    assert "hypothesis" not in row                    # the 25-word hypothesis is not inlined


def test_radar_inbox_draft_absent_or_errored_is_null(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The emitter never fabricates an advisory line: a row with no matching draft, and a row whose
    only candidate is an unassessed-error draft, both carry null draft fields."""
    clusters = [_cluster("T001", ["A1", "A2"]), _cluster("T002", ["B1", "B2"])]
    drafts = [_draft_rec("E", ["B1", "B2"], status="unassessed-error")]  # errored → not joinable
    inbox = _run_inbox_with_drafts(tmp_path, monkeypatch, [], clusters, drafts)
    by = {e["cluster_id"]: e for e in inbox["inbox"]}
    for cid in ("T001", "T002"):
        assert by[cid]["draft_name"] is None
        assert by[cid]["draft_read"] is None
        assert by[cid]["draft_suggested"] is None


def test_radar_draft_not_carried_onto_reviewed_log_rows(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A draft is an INBOX affordance only: a cluster matched to a review goes to the log, which
    carries no draft_* fields, even if a stale draft's members still overlap it."""
    reviews = [_review("2026-06-17:R0", ["A1", "A2"])]  # matches T000 → log
    clusters = [_cluster("T000", ["A1", "A2"]),          # reviewed → log
                _cluster("T002", ["P1", "P2"], rel12=0.2)]  # unreviewed → inbox
    drafts = [_draft_rec("Kx", ["A1", "A2"], name="stale draft", suggested="park", reason="r")]
    ca = tmp_path / "data" / "scan_history" / "component-a"
    ca.mkdir(parents=True)
    (ca / "20260714T120000Z__t.jsonl").write_text("\n".join(json.dumps(c) for c in clusters))
    radar = tmp_path / "frontend" / "radar"
    radar.mkdir(parents=True)
    (radar / "reviews.json").write_text(json.dumps({"reviews": reviews}))
    (radar / "drafts.json").write_text(json.dumps(
        {"scan_date": "2026-07-14", "source": "20260714T120000Z__t.jsonl", "drafts": drafts}))
    monkeypatch.setattr(_BUILD, "ROOT", tmp_path)
    monkeypatch.setattr(_BUILD, "HERE", tmp_path / "frontend")
    _BUILD.emit_radar_inbox_log()
    log = json.loads((radar / "log.json").read_text())
    assert [r["key"] for r in log["reviews"]] == ["2026-06-17:R0"]
    assert all("draft_name" not in r for r in log["reviews"])  # log rows carry no draft affordance


# --- ONE-RESOLVER pins (labels + radar vocab) ----------------------------------------------------
def test_dossier_index_labels_match_the_backend_resolver() -> None:
    """The stdlib twin: build.py's index `labels` map must equal vinci.labels.committed_gics_index
    over the real committed dossier tree — the build fence forbids the import, so the two
    implementations are pinned against each other instead."""
    from pathlib import Path

    from vinci.labels import committed_gics_index

    root = Path(__file__).resolve().parents[1]
    committed = json.loads((root / "frontend" / "dossiers" / "index.json").read_text())
    expect = {t: {"industry": v["industry"], "source": "ciq-gics", "source_ref": v["source_ref"]}
              for t, v in committed_gics_index(root / "data" / "dossiers").items()}
    assert committed.get("labels") == expect


def test_radar_decision_vocab_canonical_and_mirrored_in_js() -> None:
    """HIGH-1 pins: (a) every decision in the committed analyst record maps through
    _CANON_DECISION (an unmapped one fails the BUILD loud — this pin fails the SUITE loud);
    (b) the canonical value set equals radar.js's DECISION_LABEL keys (py↔JS source pin — the
    test_web_brief_proposal_mirror_static pattern)."""
    import re
    from pathlib import Path

    b = _load_build()
    root = Path(__file__).resolve().parents[1]
    reviews = json.loads((root / "frontend" / "radar" / "reviews.json").read_text())["reviews"]
    unknown = {str(r.get("decision")) for r in reviews} - set(b._CANON_DECISION)
    assert not unknown, f"reviews.json decisions outside _CANON_DECISION: {unknown}"
    js = (root / "frontend" / "views" / "themes" / "radar.js").read_text()
    m = re.search(r"DECISION_LABEL\s*=\s*\{([^}]*)\}", js)
    assert m, "DECISION_LABEL not found in radar.js"
    js_keys = set(re.findall(r"(\w+)\s*:", m.group(1)))
    assert js_keys == set(b._CANON_DECISION.values()), (
        f"radar.js DECISION_LABEL {js_keys} != canonical {set(b._CANON_DECISION.values())}")
    # the committed log.json is already canonical (regenerated through the seam)
    log = json.loads((root / "frontend" / "radar" / "log.json").read_text())
    assert {r["decision"] for r in log["reviews"]} <= set(b._CANON_DECISION.values())


def test_industry_hint_prefers_member_industry_and_degrades_to_raw_sic() -> None:
    """The hint counts the resolver-attached member.industry (official titles); a PRE-FIELD
    cluster degrades to raw `SIC <code>` — never a fabricated name (the _SIC_NAME map is dead)."""
    b = _load_build()
    named = {"members": [{"industry": "Services-Prepackaged Software", "sic": "7372"},
                         {"industry": "Services-Prepackaged Software", "sic": "7372"},
                         {"industry": "Semiconductors & Related Devices", "sic": "3674"}]}
    assert b._industry_hint(named) == "Services-Prepackaged Software · 2/3"
    prefield = {"members": [{"sic": "7372"}, {"sic": "7372"}, {"sic": "3674"}]}
    assert b._industry_hint(prefield) == "SIC 7372 · 2/3"
    assert b._industry_hint({"members": []}) is None
    src = (Path(__file__).resolve().parents[1] / "frontend" / "build.py").read_text()
    assert "_SIC_NAME" not in src, "the static SIC-name map must stay dead — one table"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
