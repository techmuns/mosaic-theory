"""The queue's EVIDENCE STRIP — inform-only context, and the fence that keeps it inform-only.

The strip exists because the queue could say where a name ranks but not whether anyone was DOING
anything — issuing stock, buying, shorting. The 2026-08-12 panel killed the price-based answer
(every trend state was one regime measured nine ways), so this renders positioning instead, as each
leg lands. Net share issuance is the first: evidence-backed (Pontiff-Woodgate), directional, and
free — it reads companyfacts the screen already fetches.

Two things must stay true and are pinned here: it can never reach a weight/gate/sort, and it never
names a mechanism its input cannot support (the "heavy distribution" lesson).
"""

from __future__ import annotations

import ast
import pathlib
from datetime import date

from vinci.edgar.concepts import SHARES_WINDOW_DAYS, share_count_change
from vinci.evidence import evidence_strip
from vinci.schemas.data_record import (
    CoverageTier,
    DataRecord,
    Fundamentals,
    Identity,
    PriceFeatures,
    StressSignals,
)
from vinci.schemas.envelope import DataField, SourceTier

REF = date(2026, 8, 12)
ROOT = pathlib.Path(__file__).resolve().parents[1] / "vinci"


def _f(v: float | None) -> DataField[float]:
    if v is None:
        return DataField.unknown(source="EDGAR", tier=SourceTier.EDGAR, note="n/a")
    return DataField.present(v, as_of=REF, source="EDGAR", tier=SourceTier.EDGAR)


def _rec(*, shares_change: float | None, dist_from_low: float | None) -> DataRecord:
    """Built from the REAL types — never a hand-rolled shape (CLAUDE.md fixture rule)."""
    u: DataField[float] = DataField.unknown(source="EOD", tier=SourceTier.DERIVED, note="n/a")
    return DataRecord(
        identity=Identity(
            internal_id="SEC-X-FOO", issuer_id="ISS-X", cik="0000000001", ticker="FOO",
            mic="XNAS", exchange="Nasdaq", eod_symbol="FOO", name="Foo Inc."),
        market_cap=u,
        prices=PriceFeatures(
            last=_f(10.0), high_52w=_f(30.0), low_52w=_f(8.0),
            drawdown_from_high=_f(-0.66), dist_from_low=_f(dist_from_low),
            ret_3m=u, ret_6m=u, ret_12m=u, rel_ret_vs_market=u,
            adv_90d_shares=u, adv_90d_usd=u, turnover=u, volume_spike=u),
        fundamentals=Fundamentals(
            ev_ebitda=u, ev_ebitda_pctile_vs_history=u, pe=u, pe_pctile_vs_history=u,
            fcf_sign=DataField.unknown(source="EDGAR", tier=SourceTier.EDGAR, note="n/a"),
            op_income_sign=DataField.unknown(source="EDGAR", tier=SourceTier.EDGAR, note="n/a"),
            net_leverage=u, share_count_change_730d=_f(shares_change)),
        stress=StressSignals(iv_pctile=u, short_interest=u),
        overall_coverage_tier=CoverageTier.US_FULL, as_of=REF,
    )


# --- the strip itself ---------------------------------------------------------------------------
def test_the_strip_shows_issuance_direction_and_distance_off_the_low() -> None:
    """Both legs, both signed. Direction is the whole point of the issuance leg — 'shares 42%' with
    no arrow is unreadable, and a buyback and a raise are opposite facts."""
    out = evidence_strip(_rec(shares_change=-0.014, dist_from_low=0.18))
    assert out is not None
    assert "shares ↓1.4% 2y" in out, out
    assert "+18% off low" in out, out


def test_a_share_raise_and_a_buyback_read_opposite() -> None:
    up = evidence_strip(_rec(shares_change=0.42, dist_from_low=0.05)) or ""
    down = evidence_strip(_rec(shares_change=-0.42, dist_from_low=0.05)) or ""
    assert "↑42.0%" in up and "↓42.0%" in down, (up, down)


def test_the_drawdown_is_not_repeated_from_the_depth_column() -> None:
    """The queue's `Depth (52w)` column already shows drawdown-from-high. Printing it again in the
    strip makes a dense table worse and lets two copies of one number disagree — so the plan's
    'price tail' ships as distance-off-low ONLY. Deliberate divergence from the plan, pinned."""
    out = evidence_strip(_rec(shares_change=-0.01, dist_from_low=0.18)) or ""
    assert "from high" not in out, f"drawdown duplicated into the strip: {out}"
    assert "-66%" not in out and "−66%" not in out, out


def test_an_unknown_leg_is_omitted_rather_than_guessed() -> None:
    """UNKNOWN never becomes 0.0. A fabricated 'shares ↔0.0%' would read as a confirmed flat share
    count, which is the opposite of 'we could not tell'."""
    out = evidence_strip(_rec(shares_change=None, dist_from_low=0.18)) or ""
    assert "shares" not in out, out
    assert "+18% off low" in out, out


def test_a_name_with_nothing_known_gets_no_strip_at_all() -> None:
    """None, not '' and not '—': an empty strip should vacate the column, and a dash would read as
    a measured absence rather than a gap."""
    assert evidence_strip(_rec(shares_change=None, dist_from_low=None)) is None


def test_the_strip_names_no_mechanism_its_input_cannot_support() -> None:
    """The 'heavy distribution' lesson: a label that asserted WHO was trading from a number with no
    direction in it, wrong on 2 of 10 names. The strip reports measured quantities only."""
    out = evidence_strip(_rec(shares_change=0.42, dist_from_low=0.30)) or ""
    for word in ("dilution", "distribution", "accumulation", "insiders buying",
                 "bullish", "bearish", "recovering", "terminal"):
        assert word not in out.lower(), f"{word!r} asserted by the strip: {out}"


# --- ONE implementation of the share-count change ------------------------------------------------
def test_the_dilution_demote_and_the_strip_read_the_same_quantity() -> None:
    """The displayed issuance number and the dilution-spiral demote must be the same computation.
    Two implementations would agree today and diverge on the first edit to one — the twin-drift
    class this repo keeps finding. `vinci.rank.structural` must therefore consume the shared helper
    rather than re-deriving the window inline, which is what it did before."""
    src = (ROOT / "rank" / "structural.py").read_text()
    tree = ast.parse(src)
    imported = {
        n.name for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
        and node.module == "vinci.edgar.concepts" for n in node.names
    }
    assert "share_count_change" in imported, (
        "structural.py no longer imports the shared share-count helper — the demote and the "
        "displayed number can now drift apart")
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "_dilution_spiral")
    body = ast.unparse(fn)
    assert "share_count_change(" in body, "the dilution leg re-derives the window inline again"
    assert "timedelta" not in body, (
        "the dilution leg is computing its own window again instead of using the shared helper")


def test_the_shared_helper_refuses_to_invent_a_flat_share_count() -> None:
    """None, never 0.0, when the series cannot support an answer — the same rule the strip relies
    on to omit the leg rather than print a confident 'unchanged'."""
    assert share_count_change([]) is None
    assert share_count_change([(date(2025, 1, 1), 1_000.0)]) is None          # one point
    assert share_count_change([(date(2025, 1, 1), 0.0), (date(2026, 1, 1), 5.0)]) is None
    got = share_count_change([(date(2025, 1, 1), 100.0), (date(2026, 1, 1), 142.0)])
    assert got is not None and abs(got.change - 0.42) < 1e-9
    assert got.from_value == 100.0 and got.to_value == 142.0  # endpoints travel with the number


def test_the_window_is_anchored_on_the_last_point_not_on_today() -> None:
    """A name whose XBRL series ends early is measured over the span it actually has, rather than
    silently returning the whole history because 'today minus 2 years' caught nothing."""
    old = (date(2018, 1, 1), 50.0)          # far outside the window
    a = (date(2025, 1, 1), 100.0)
    b = (date(2026, 1, 1), 110.0)
    got = share_count_change([old, a, b])
    assert got is not None and got.from_date == a[0], (
        f"the pre-window point leaked into the change: {got}")
    assert SHARES_WINDOW_DAYS == 730


# --- the fence ----------------------------------------------------------------------------------
def test_the_scorer_and_the_screen_can_never_read_the_evidence_strip() -> None:
    """``vinci.evidence`` must NOT be imported by the ranker (``vinci.rank``) or the screen gate
    (``vinci.screens``). The strip is presented context attached by the WRITER after ranking is
    finished; the moment it reaches a weight / threshold / sort it becomes an unvalidated signal
    driving the queue. Same shape as the sector/label fence, and for the same reason.
    """
    scanned: set[str] = set()
    for pkg in ("rank", "screens"):
        for src in (ROOT / pkg).glob("*.py"):
            scanned.add(src.name)
            for node in ast.walk(ast.parse(src.read_text())):
                if isinstance(node, ast.ImportFrom) and node.module is not None:
                    assert not node.module.startswith("vinci.evidence"), (
                        f"{src.name} imports {node.module} — the evidence strip must never be "
                        "readable by the scorer or the gate")
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert not alias.name.startswith("vinci.evidence"), (
                            f"{src.name} imports {alias.name} — evidence must not gate/score")
    assert {"ranker.py", "structural.py"} <= scanned  # sanity: the scorer files were scanned
