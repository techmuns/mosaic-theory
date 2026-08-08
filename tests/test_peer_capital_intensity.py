"""Is this acquired-asset load unusual for the sector, or exactly what it looks like?

WHY. SMPL carries $1,508.9M of goodwill + intangibles having just written off $369M, and nothing
in the artifact could say whether that is remarkable. The trade rests on SMPL deserving a premium
to peer median, so this is the field that settles it.

TWO DENOMINATORS, AND THE CHOICE IS THE ARGUMENT. Against MARKET CAP a cheap stock shows a high
ratio on identical accounting — SMPL's 166% is partly $1.5bn of goodwill and partly a market cap
that halved, so reading it alone measures the de-rating the thesis calls an overshoot. Circular.
Against TOTAL ASSETS it measures how acquisitive the balance sheet IS.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from vinci.dossier.capital_allocation import PEER_SIZE_FLOOR_MUSD, build_peer_capital_intensity
from vinci.dossier.schemas import PeerRow

ROOT = pathlib.Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.network


def _grid(t: str) -> list[PeerRow]:
    doc = json.loads((ROOT / "data" / "dossiers" / t / "dossier.json").read_text())
    v = ((doc["mechanical"].get("peer_comps") or {}).get("peer_grid") or {}).get("value") or []
    return [PeerRow.model_validate(x) for x in v]


def _built(t: str):
    from vinci.edgar.client import EdgarClient
    from vinci.resolver import EntityResolver
    return build_peer_capital_intensity(
        _grid(t), resolve=EntityResolver.from_config().resolve_ticker,
        companyfacts=EdgarClient.from_config().companyfacts)


def test_the_two_denominators_disagree_and_that_is_the_point() -> None:
    """If they ranked SMPL the same way, one of them would be redundant. They do not: against
    ASSETS SMPL sits 15pp above the large-peer median; against MARKET CAP only 21pp above, because
    every de-rated packaged-food name shows a high ratio on unchanged accounting."""
    pc = _built("SMPL")
    assert pc.subject_pct_assets == pytest.approx(0.73, abs=0.02)
    assert pc.subject_pct_market_cap == pytest.approx(1.66, abs=0.03)
    assert pc.median_large_assets is not None and pc.median_all_assets is not None
    assert pc.median_large_assets > pc.median_all_assets, (
        "excluding sub-floor names did not raise the assets median — the size cut is doing nothing")


def test_the_size_floor_is_stated_and_actually_bites() -> None:
    """The set spans $49M to $30.1bn. HAIN at a $49M market cap reads 950% of market cap — a
    de-rating artifact, not a statement about its balance sheet — so a median across the whole
    range inherits the heterogeneity this metric exists to settle."""
    pc = _built("SMPL")
    assert pc.size_floor == PEER_SIZE_FLOOR_MUSD
    assert pc.n_large < pc.n_all, "the floor excluded nobody — it is not doing its job"
    small = [r for r in pc.rows if r.market_cap and r.market_cap < pc.size_floor]
    assert small, "no sub-floor peer in the set — this pin checked nothing"


def test_three_absences_are_three_different_sentences() -> None:
    """`no-tag` (the filer genuinely reports neither — Freshpet is an organic grower), `unresolved`
    (no CIK) and `fetch-failed` (EDGAR unreachable) must never collapse. #362 exactly: a failed
    fetch reading as "carries none" is the reassuring wrong answer."""
    pc = _built("SMPL")
    notag = [r for r in pc.rows if r.note and r.note.startswith("no-tag")]
    assert notag, "expected at least one genuinely tag-less peer (FRPT) — the corpus changed"
    for r in notag:
        assert r.acquired is None and "not a data gap" in (r.note or "")
    for r in pc.rows:
        if r.note and r.note.startswith("fetch-failed"):
            assert "NOT a statement" in r.note


def test_a_fetch_failure_never_renders_as_carries_none() -> None:
    """The #362 finding, one module over — pinned on the branch rather than hoped for."""
    def boom(_cik: str) -> dict:
        raise RuntimeError("EDGAR unreachable")

    class _Id:
        cik = "0000000001"

    pc = build_peer_capital_intensity(
        [PeerRow(name="X", ticker="XXX", market_cap=100.0)],
        resolve=lambda _t: _Id(), companyfacts=boom)
    row = pc.rows[0]
    assert row.acquired is None and row.note and row.note.startswith("fetch-failed")
    assert "NOT a statement that the filer reports no goodwill" in row.note
    assert pc.n_all == 0, "a failed fetch was counted into the median"


def test_the_median_excludes_rows_it_could_not_measure() -> None:
    """A peer with no figures must not silently count as zero — that would drag the median toward
    a number nobody reported."""
    pc = _built("SMPL")
    usable = [r for r in pc.rows[1:] if r.pct_assets is not None and r.pct_market_cap is not None]
    assert pc.n_all == len(usable), f"n_all {pc.n_all} != {len(usable)} measurable peers"


def test_the_subject_leads_the_rows() -> None:
    """The comparison is read against the subject, so it is row zero — not sorted into the pack."""
    pc = _built("SMPL")
    assert pc.rows and pc.rows[0].ticker == "SMPL"
