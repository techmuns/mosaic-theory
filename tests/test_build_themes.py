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


def _cluster(cid: str, members: list[str], rel12: float = 0.0) -> dict[str, Any]:
    return {"cluster_id": cid, "members": [{"ticker": t} for t in members],
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


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
