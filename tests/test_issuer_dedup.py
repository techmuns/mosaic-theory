"""ONE ISSUER, ONE LINE (2026-09-01) — the same company must not enter the spread twice.

MEASURED on the 2026-08-24 build, after per-class sizing (#546) had already stopped the CAPS
double-counting. Sizing did not stop the POPULATION double-counting: 12 duplicate lines in the
primary band and 7 in the theme band, so one issuer's forward return could enter the BUY-AVOID
spread twice and count double in the only number that proves this fund works.

    ZG + Z | RUSHA + RUSHB | CENT + CENTA | UA + UAA | BF.A + BF.B | GEF + GEF.B ...
    GOOGL + GOOG + GOOGM + GOOGN | BRK.A + BRK.B | HEI + HEI.A | FOXA + FOX | PBR + PBR.A

THE SURVIVOR IS THE HIGHEST-ADV LINE — a face-validity choice, measured against the alternative
and never tuned on returns. A position can only ever be taken in the line the fund can actually
trade. Against "keep the largest cap" the rules disagree on 4 of the 17 issuers and ADV is right
on all four; the ADAMAS case settles it, because a cap rule would have deleted the real common and
kept a mistyped senior note as the issuer's only representative.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.test_dual_class_caps import _CIK, _run
from vinci.universe import DROP_STAGES


def test_one_issuer_contributes_one_line(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The whole point: two classes of one issuer, one admitted name."""
    assert "duplicate_class" in DROP_STAGES        # so retention emits its row
    stats, rows = _run(monkeypatch, tmp_path, lines=[("AAA", _CIK), ("AAB", _CIK)],
                       closes={"AAA": 100.0, "AAB": 100.0},
                       class_counts={"AAA": 20_000_000.0, "AAB": 10_000_000.0},
                       xbrl_shares={_CIK: 30_000_000.0},
                       volumes={"AAA": 50_000_000.0, "AAB": 1_000_000.0})
    assert stats["in_universe"] == 1
    assert stats["duplicate_class"] == 1
    assert set(rows) == {"AAA"}


def test_the_survivor_is_the_tradeable_line_not_the_larger_one(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """THE ADAMAS CASE, which is why the rule is ADV and not market cap. ADAMK carried the larger
    cap ($2.3B against ADAM's $0.9B) and is a BOND — "Adamas Trust, Inc. 9.600% Senior Notes",
    typed CS by the reference feed. Ranking on cap would have deleted the real common and left the
    note as the issuer's only representative in the validation population."""
    stats, rows = _run(monkeypatch, tmp_path, lines=[("COMMON", _CIK), ("NOTE", _CIK)],
                       closes={"COMMON": 10.0, "NOTE": 100.0},
                       class_counts={"COMMON": 90_000_000.0},     # the note publishes none
                       xbrl_shares={_CIK: 90_000_000.0},
                       volumes={"COMMON": 8_000_000.0, "NOTE": 400_000.0})
    assert set(rows) == {"COMMON"}, "the larger-cap line is the bond; ADV must not pick it"
    assert rows["COMMON"]["market_cap"] < 10.0 * 90_000_000.0 + 1
    assert stats["duplicate_class"] == 1


def test_a_single_class_issuer_is_never_touched(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """NO OVER-REACH — the pass must be invisible to the 99.4% of the population with one line."""
    stats, rows = _run(monkeypatch, tmp_path, lines=[("SOLO", "0000000009")],
                       closes={"SOLO": 25.0}, class_counts={},
                       xbrl_shares={"0000000009": 40_000_000.0})
    assert stats["in_universe"] == 1
    assert stats.get("duplicate_class", 0) == 0
    assert rows["SOLO"]["market_cap"] == 25.0 * 40_000_000.0


def test_two_issuers_that_merely_look_alike_both_survive(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The pass keys on CIK, not on ticker shape. Two DIFFERENT issuers whose tickers share a stem
    are not siblings and both must be admitted — otherwise de-duplication silently deletes a real
    company, which is the failure mode that costs most and shows least."""
    stats, rows = _run(monkeypatch, tmp_path,
                       lines=[("ABC", "0000000001"), ("ABCD", "0000000002")],
                       closes={"ABC": 50.0, "ABCD": 50.0}, class_counts={},
                       xbrl_shares={"0000000001": 20_000_000.0, "0000000002": 20_000_000.0})
    assert stats["in_universe"] == 2
    assert stats.get("duplicate_class", 0) == 0
    assert set(rows) == {"ABC", "ABCD"}


def test_the_drop_names_the_line_that_won(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """THE RETENTION ROW IS THE EVIDENCE TRAIL. A name that leaves the population must say which
    line replaced it and on what number, or the exclusion cannot be audited later."""
    stats, _ = _run(monkeypatch, tmp_path, lines=[("AAA", _CIK), ("AAB", _CIK)],
                    closes={"AAA": 100.0, "AAB": 100.0},
                    class_counts={"AAA": 20_000_000.0, "AAB": 10_000_000.0},
                    xbrl_shares={_CIK: 30_000_000.0},
                    volumes={"AAA": 50_000_000.0, "AAB": 1_000_000.0},
                    retain=True)
    assert stats["duplicate_class"] == 1
    from vinci.screens.retention import run_path
    rows = [json.loads(x) for x in
            run_path("2026-06-12-01", tmp_path / "retain").read_text().splitlines() if x.strip()]
    dupes = [r for r in rows if r["stage"] == "duplicate_class"]
    assert len(dupes) == 1, f"the drop must emit exactly one retention row, got {rows}"
    row = dupes[0]
    assert row["ticker"] == "AAB"
    assert "AAA" in row["reason"], "the row must NAME the line that replaced this one"
    assert row["deciding_input"]["source"] == "Polygon ADV"


def test_the_choice_is_deterministic_when_liquidity_ties(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Ties break on cap then ticker. A re-run that silently swapped which class the ledger
    accumulates against would break the forward record it exists to keep."""
    seen = set()
    for _ in range(3):
        _, rows = _run(monkeypatch, tmp_path, lines=[("AAA", _CIK), ("AAB", _CIK)],
                       closes={"AAA": 100.0, "AAB": 100.0},
                       class_counts={"AAA": 20_000_000.0, "AAB": 10_000_000.0},
                       xbrl_shares={_CIK: 30_000_000.0})      # identical volumes -> ADV ties
        seen.add(tuple(sorted(rows)))
    assert len(seen) == 1, f"the survivor changed between identical runs: {seen}"
    assert seen == {("AAA",)}, "the tie must break to the larger cap"
