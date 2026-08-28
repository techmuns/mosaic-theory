"""The theme economics roll-up (brief Item 4, ruling R5 = build now, inform-only).

The load-bearing pins: NO COMPOSITE anywhere (a naive theme average would fabricate a number the
schema-level no-probabilities design forbids); a member without a record is a stated ``no
underwrite`` state, never a blank; an ``ev_gap`` never travels without its vintages (the
ev_gap-stale-after-supersede class — the vintage beside the number IS the honesty); a pre-ladder
record renders unstamped rather than letting absence read as passage; and a basket-less driver
yields a LOUD empty artifact (absent-vs-broken), never a missing block.

The committed-corpus test runs the real assembler over the real frozen basket — corpus before
synthetic — and asserts structural invariants only (never values that re-draw with the corpus).
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from vinci.themes import forward as fwd
from vinci.themes.rollup import (
    MemberEconomics,
    ThemeEconomicsRollup,
    build_rollup,
    economics_path,
    write_rollup,
)

_REPO = Path(__file__).resolve().parents[1]


def _seed_basket(data_dir: Path, tickers: list[str], layer_of: dict[str, str]) -> None:
    baskets = fwd.FrozenBaskets(
        driver="ai-datacenter", freeze_timestamp="2026-08-01T00:00:00",
        ratified=tuple(tickers), passed=(), all_committed=tuple(tickers),
        entry_dates=dict.fromkeys(tickers, "2026-08-01"), layer_of=layer_of)
    path = fwd.baskets_path("ai-datacenter", data_dir=data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(baskets.model_dump_json())


def _seed_record(root: Path, ticker: str, *, ladder: bool) -> None:
    result: dict[str, object] = {"ratio": 2.1}
    if ladder:
        result.update({"gate_regime": "tiered-2026-08-21", "asymmetry_tier": "target_met",
                       "return_tier": "preferred", "eligible": True})
    rec = {"ticker": ticker, "underwrite_date": "2026-07-20", "result": result,
           "verdict": {"status": "confirmed", "avoid_priced": False}}
    d = root / "scenarios"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{ticker}.json").write_text(json.dumps(rec))


def _seed_dossier(dossiers: Path, ticker: str) -> None:
    doc = {"mechanical": {"ev_gap": {
        "status": "computed", "ratios": {"ev_gap": 1.34},
        "vintages": {"tev_as_of": "2026-07-29", "consensus_as_of": "2026-06-30"}}}}
    d = dossiers / ticker
    d.mkdir(parents=True, exist_ok=True)
    (d / "dossier.json").write_text(json.dumps(doc))


def test_rollup_assembles_underwritten_and_bare_members(tmp_path: Path) -> None:
    data_dir, dossiers = tmp_path / "data", tmp_path / "data" / "dossiers"
    _seed_basket(data_dir, ["AAA", "BBB"], {"AAA": "chips/GPU", "BBB": "power/electrical"})
    _seed_record(tmp_path, "AAA", ladder=True)
    _seed_dossier(dossiers, "AAA")
    r = build_rollup("ai-datacenter", data_dir=data_dir, scenarios_root=tmp_path,
                     dossiers_dir=dossiers, as_of=date(2026, 8, 29))
    assert (r.n_members, r.n_underwritten) == (2, 1)
    aaa, bbb = r.rows  # sorted
    assert aaa.underwritten and aaa.asymmetry_tier == "target_met"
    assert aaa.gate_regime == "tiered-2026-08-21" and aaa.eligible is True
    assert aaa.substructure_tag == "chips/GPU"
    # the vintage travels WITH the number, always — the staleness honesty
    assert aaa.ev_gap == pytest.approx(1.34)
    assert aaa.ev_gap_vintages == {"tev_as_of": "2026-07-29", "consensus_as_of": "2026-06-30"}
    # a bare member is a STATED state, never a blank
    assert not bbb.underwritten and bbb.asymmetry_tier is None
    assert bbb.ev_gap_status == "no-dossier" and bbb.membership_source == "frozen-basket"


def test_pre_ladder_record_renders_unstamped_not_passing(tmp_path: Path) -> None:
    """A record without ``gate_regime`` was judged under the old booleans — the row must say so
    (regime None while underwritten) rather than letting absence read as a stamped tier."""
    data_dir = tmp_path / "data"
    _seed_basket(data_dir, ["CCC"], {})
    _seed_record(tmp_path, "CCC", ladder=False)
    r = build_rollup("ai-datacenter", data_dir=data_dir, scenarios_root=tmp_path,
                     dossiers_dir=data_dir / "dossiers", as_of=date(2026, 8, 29))
    row = r.rows[0]
    assert row.underwritten is True
    assert row.gate_regime is None and row.asymmetry_tier is None and row.eligible is None


def test_basketless_driver_yields_a_loud_empty_rollup(tmp_path: Path) -> None:
    r = build_rollup("ai-datacenter", data_dir=tmp_path / "data",
                     scenarios_root=tmp_path, dossiers_dir=tmp_path / "d",
                     as_of=date(2026, 8, 29))
    assert r.n_members == 0 and r.rows == ()
    assert "no frozen basket" in r.membership_note  # the page prints WHY, never a silent absence


def test_unknown_driver_refused() -> None:
    with pytest.raises(ValueError, match="unknown driver"):
        build_rollup("not-a-driver", data_dir=Path("x"), scenarios_root=Path("x"),
                     dossiers_dir=Path("x"), as_of=date(2026, 8, 29))


def test_no_composite_anywhere() -> None:
    """The roll-up assembles; concluding is the human's. No field may carry an aggregate."""
    forbidden = ("score", "rank", "composite", "mean", "average", "aggregate", "weighted",
                 "verdict", "recommendation", "priority", "total_ev", "theme_ev")
    fields = set(MemberEconomics.model_fields) | set(ThemeEconomicsRollup.model_fields)
    assert fields
    for n in fields:
        for tok in forbidden:
            assert tok not in n.lower(), f"field {n!r} smuggles a composite ({tok})"


def test_written_artifact_round_trips_and_carries_no_composite_keys(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _seed_basket(data_dir, ["AAA"], {})
    r = build_rollup("ai-datacenter", data_dir=data_dir, scenarios_root=tmp_path,
                     dossiers_dir=data_dir / "dossiers", as_of=date(2026, 8, 29))
    path = write_rollup(r, data_dir=data_dir)
    assert path == economics_path("ai-datacenter", data_dir=data_dir)
    back = ThemeEconomicsRollup.model_validate_json(path.read_text())
    assert back == r


def test_committed_corpus_rollup_structural_invariants() -> None:
    """CORPUS BEFORE SYNTHETIC — the real assembler over the real frozen basket. Invariants only
    (membership parity, source labels, no composite keys in the serialized artifact); never a
    value pin, because the corpus re-draws. Non-vacuity guarded."""
    data_dir = _REPO / "data"
    basket = fwd.load_baskets(fwd.baskets_path("ai-datacenter", data_dir=data_dir))
    r = build_rollup("ai-datacenter", data_dir=data_dir, scenarios_root=_REPO,
                     dossiers_dir=data_dir / "dossiers", as_of=date(2026, 8, 29))
    assert r.n_members == len(basket.all_committed) > 0  # non-vacuous
    assert {row.ticker for row in r.rows} == set(basket.all_committed)
    assert all(row.membership_source == "frozen-basket" for row in r.rows)
    assert all(row.ev_gap_vintages for row in r.rows if row.ev_gap is not None)
    blob = r.model_dump_json().lower()
    for tok in ('"theme_ev"', '"composite"', '"weighted"', '"average"'):
        assert tok not in blob
