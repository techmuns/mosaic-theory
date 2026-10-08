"""Forward consensus: FY+0..FY+2 paths, spreads and revision counts, outside the synthesis.

THE SHAPE THIS GUARDS. The analyst review of AMZN (2026-10-07) asked for the forward distributions
and revision history a scenario is struck on. The obvious read was wrong in three measured ways:
- `consensus_rows` searches for a metric's first title after the company-level block, so AMZN's
  'EPS (GAAP)' read a quarterly block from 2005 — FY2026 median 0.01 against a true 12.91 — and a
  low/median/high check passed it;
- `_market_summary_current_year` scans 60 rows past the Market Summary, so a label the summary does
  not carry is answered from the section below (BRBR 'EPS (GAAP)' → 3.12);
- `horizon_read` bounds a Revisions block by the next metric on its own list, so its window scan
  runs on through every block in between.

The CIQ-backed tests read the licensed workbooks on disk and SKIP without them — they are never
committed. The rest run anywhere.
"""
from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from vinci.dossier import ciq_sheets as cs
from vinci.dossier.anchor import replace_anchor_block
from vinci.dossier.ciq import CiqBundle, clean_num
from vinci.dossier.schemas import (
    ConsensusPath,
    ConsensusPoint,
    Dossier,
    ForwardConsensus,
    MechanicalLayer,
    dossier_json,
)

ROOT = Path(__file__).resolve().parents[1]
COMMITTED = sorted(p.parent.name for p in (ROOT / "data" / "dossiers").glob("*/dossier.json"))


def _bundle(ticker: str) -> CiqBundle:
    """The name's bundle, or SKIP — the licensed workbooks are never committed."""
    from vinci.config import get_config
    from vinci.dossier.manual_store import LocalFolderStore

    files = LocalFolderStore(get_config().data_dir / "manual" / "ciq").files(ticker)
    if not files:
        pytest.skip(f"licensed CIQ bundle for {ticker} unavailable (never committed)")
    return CiqBundle.from_files(ticker, files)


def _trends_current(fc: ForwardConsensus) -> dict[tuple[str, str], float]:
    return {(p.metric, p.period): p.points[-1].value for p in fc.paths
            if p.points and p.points[-1].months_ago == 0}


# --- the reads, on the real workbooks -----------------------------------------------------------


def test_eps_comes_from_the_annual_per_share_section_never_a_quarterly_one() -> None:
    """THE PREVIOUSLY BROKEN CASE. AMZN's FY+0 'EPS (GAAP)' spread is the per-share section's figure
    — the one the sheet's own Market Summary carries — not the 2005 quarterly block's 0.01, which
    sits under a header with no fiscal years and so can never be vouched for."""
    b = _bundle("AMZN")
    fc = cs.forward_consensus(b)
    assert fc is not None
    cons = b.sheet("estimates", "Consensus")
    summary = cs._market_summary(cons)
    fy0 = fc.periods[0]
    eps = next(s for s in fc.spreads if s.metric == "EPS (GAAP)" and s.period == fy0)
    assert abs(eps.mean - summary["EPS (GAAP)"]) < 0.01, (eps.mean, summary["EPS (GAAP)"])
    trend = _trends_current(fc)[("EPS (GAAP)", fy0)]
    assert abs(eps.mean - trend) <= 0.02 * abs(trend), (eps.mean, trend)
    # the quarterly block that the positional read landed on is never vouched for
    quarterly = [i for i, r in enumerate(cons) if r and str(r[0]).strip() == "EPS (GAAP)"
                 and (h := cs._governing_header(cons, i)) is not None
                 and not cs._header_years(cons[h])]
    assert quarterly, "AMZN's quarterly EPS block is gone — re-check the pin's premise"


def test_the_market_summary_is_read_only_inside_its_own_block() -> None:
    """NEGATIVE: BRBR's summary carries 'EPS Normalized' and not 'EPS (GAAP)'. The old unbounded
    reader still answers for 'EPS (GAAP)' from the section below; the bounded one does not — and
    what it does carry is the per-share section's own figure for the current year."""
    cons = _bundle("BRBR").sheet("estimates", "Consensus")
    summary = cs._market_summary(cons)
    assert "EPS (GAAP)" not in summary, summary
    assert cs._market_summary_current_year(cons, "EPS (GAAP)") is not None, (
        "the old reader no longer over-reads — the premise of this pin has moved")
    sec = cs._identified_section(cons, "EPS Normalized", summary["EPS Normalized"])
    assert sec is not None, "the summary's per-share figure vouches for no section"


@pytest.mark.parametrize("ticker", COMMITTED)
def test_every_spread_sits_on_its_own_trends_figure(ticker: str) -> None:
    """ACROSS THE CORPUS. Consensus and Trends are separate sheets and can differ by a fraction of a
    percent (ROST EBITDA 0.9%), but a wrong-section read is off by orders of magnitude — 0.01
    against 12.89. Measured 2026-10-07: 624 spreads, all within max(0.01, 2%) of their Trends
    current figure."""
    fc = cs.forward_consensus(_bundle(ticker))
    if fc is None:
        pytest.skip(f"{ticker}: no Trends sheet")
    current = _trends_current(fc)
    for s in fc.spreads:
        c = current.get((s.metric, s.period))
        if c is not None:
            assert abs(s.mean - c) <= max(0.01, 0.02 * abs(c)), (s.metric, s.period, s.mean, c)
        assert min(s.low, s.high) <= s.median <= max(s.low, s.high), s
        # the ordering is READ OFF THE VALUES (capex is ordered by size on 60 of 62 cells)
        assert s.ordered_by == ("magnitude" if s.high < s.low else "value"), s


@pytest.mark.parametrize("ticker", COMMITTED)
def test_revision_counts_are_bounded_by_their_own_block(ticker: str) -> None:
    """Each count is read inside its own block. The structural pin is AMZN's: 'EPS Normalized' ends
    at the very next block ('Cash Earnings / Share'), where `horizon_read`'s bounding runs on to
    'Revenue'. The corpus pin is what any within-block read must satisfy (1,971 counts, 0 breaches,
    2026-10-07)."""
    b = _bundle(ticker)
    fc = cs.forward_consensus(b)
    if fc is None:
        pytest.skip(f"{ticker}: no Trends sheet")
    for r in fc.revisions:
        if r.analysts is not None:
            assert r.up + r.down <= r.analysts, r
            if r.analysts_in_consensus is not None:
                assert r.analysts_in_consensus <= r.analysts, r
    if ticker == "AMZN":
        rev = b.sheet("estimates", "Revisions")
        bi = cs._find_row(rev, "EPS Normalized")
        assert bi is not None
        nxt = next(s for s in cs._block_starts(rev) if s > bi)
        assert str(rev[nxt][0]).strip() == "Cash Earnings / Share", str(rev[nxt][0])
        # the written counts are the ones INSIDE that block — read here independently, by label:
        # the first 'Last Month' window between the title and the next block
        fy0 = fc.periods[0]
        col = next(j for j, c in enumerate(rev[bi + 1]) if str(c).strip() == fy0)
        start = next(k for k in range(bi + 1, nxt) if str(rev[k][0]).strip() == "Last Month")
        labels: dict[str, float | None] = {}
        for k in range(start + 1, nxt):
            lbl = str(rev[k][0]).strip()
            if lbl.startswith("Last "):
                break
            labels[lbl] = clean_num(rev[k][col])
        got = next(r for r in fc.revisions
                   if r.metric == "EPS Normalized" and r.period == fy0 and r.window == "1m")
        assert (got.up, got.down, got.analysts, got.analysts_in_consensus) == (
            labels.get("Upward"), labels.get("Downward"), labels.get("# of Analysts"),
            labels.get("# of Analysts still in Consensus")), (got, labels)


# --- where the layer lives, and how it is written -----------------------------------------------


def _minimal() -> ForwardConsensus:
    return ForwardConsensus(periods=["FY 2027"], paths=[ConsensusPath(
        metric="EBIT", period="FY 2027", points=[ConsensusPoint(months_ago=0, value=1.0)])],
        spreads=[], revisions=[], source_ref="test")


def test_the_layer_is_never_synthesis_input() -> None:
    """`MechanicalLayer` is the ONLY input the synthesis is given; the layer sits beside it."""
    assert "forward_consensus" in Dossier.model_fields
    assert "forward_consensus" not in MechanicalLayer.model_fields


def test_absent_until_built_and_the_anchor_stays_the_last_field() -> None:
    """A page without the layer round-trips byte-identically — absent, never `null`. With it, the
    block sits before `anchor`, so the byte-preserving anchor writer still finds the anchor last."""
    path = ROOT / "data" / "dossiers" / "AMZN" / "dossier.json"
    if not path.exists():
        pytest.skip("no committed AMZN dossier")
    text = path.read_text()
    doc = Dossier.model_validate_json(text)
    if doc.forward_consensus is None:
        assert '"forward_consensus"' not in dossier_json(doc), "absent was written as a key"
    built = dossier_json(doc.model_copy(update={"forward_consensus": _minimal()}))
    assert built.index('\n  "forward_consensus": {') < built.index('\n  "anchor": {')
    assert doc.anchor is not None
    retagged = json.loads(replace_anchor_block(built, doc.anchor.model_copy(
        update={"reason": "re-tag after the layer landed"})))
    assert retagged["forward_consensus"]["source_ref"] == "test"
    assert retagged["anchor"]["reason"] == "re-tag after the layer landed"


def test_a_top_level_refresh_may_set_only_its_allowlisted_key(tmp_path: Path) -> None:
    """The top-level seam writes `forward_consensus` and nothing else: the synthesis, the anchor and
    the mechanical layer each have their own guarded path, and this one must not go around them."""
    from vinci.dossier.refresh import RefreshRefusedError, refresh_dossier

    src = ROOT / "data" / "dossiers" / "AMZN"
    if not (src / "dossier.json").exists():
        pytest.skip("no committed AMZN dossier")
    folder = tmp_path / "AMZN"
    folder.mkdir()
    for name in ("dossier.json", "dossier.md"):
        (folder / name).write_text((src / name).read_text())
    before = (folder / "dossier.json").read_text()
    with pytest.raises(ValueError, match="may set only"):
        refresh_dossier(folder / "dossier.json", top_level=lambda d: {"synthesis": None})
    assert (folder / "dossier.json").read_text() == before, "a refused key was written anyway"
    layer = json.loads(_minimal().model_dump_json())
    refresh_dossier(folder / "dossier.json", top_level=lambda d: {"forward_consensus": layer})
    written = json.loads((folder / "dossier.json").read_text())
    # compared as the MODEL: keys added later are written ABSENT, never null, so the dict the
    # model dumps and the dict the one serializer writes differ by design (TOP_DROP_WHEN_NONE)
    assert ForwardConsensus.model_validate(written["forward_consensus"]) == _minimal()
    assert written["mechanical"] == json.loads(before)["mechanical"], "the mechanical layer moved"
    (folder / "known_wrong.json").write_text("{}")
    with pytest.raises(RefreshRefusedError):
        refresh_dossier(folder / "dossier.json", top_level=lambda d: {"forward_consensus": layer})


def test_assembly_builds_the_layer_through_the_one_builder() -> None:
    """A SOURCE PIN, AND ITS LIMIT STATED: this asserts the call is written, not that it runs —
    assembly needs the network and an LLM, so no offline test can drive it. What catches the
    consequence is the artifact pass: a re-assembled page that lacks the layer while its export
    has one."""
    from vinci.dossier import assemble as asm

    src = inspect.getsource(asm.assemble_one)
    assert "forward_consensus = ciq_sheets.forward_consensus(bundle)" in src
    assert "forward_consensus=forward_consensus," in src
