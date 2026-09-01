"""PER-CLASS CAPS (2026-09-01) — one share count per CLASS, not one per issuer.

MEASURED on the live 2026-08-24 snapshots before any of this was written. A filed XBRL count is
keyed by CIK, so every listed class of one issuer was sized with the SAME number and each line
carried the WHOLE company's market cap:

    GOOGL $4,256.8B + GOOG $4,214.3B + GOOGM $603.4B + GOOGN $597.8B = $9,672B for Alphabet,
    against $3,947B once each class is sized by its own count.

21 issuers were affected — 11 in the primary band (ZG/Z, RUSHA/RUSHB, CENT/CENTA, UA/UAA,
BATRA/BATRK, LBTYA/LBTYK, LILA/LILAK ...) and 10 in the theme band (Alphabet, MCHP/MCHPP,
FOXA/FOX, LEN/LEN.B, HEI/HEI.A, NWS/NWSA, UHAL/UHAL.B, BF.A/BF.B ...). The names already routed
through the reference (BRK.B $710.1B + BRK.A $369.1B = Berkshire) were correct all along, which is
what identified the filed count as the culprit rather than the pipeline.

NOT ALWAYS DEFLATIONARY, which is why this is a correctness fix and not a haircut: HEICO's HEI.A
was sized with HEI's 55.2M count and rises from $14.3B to $21.9B on its own 84.5M.

THE ABSENCE OF A PER-CLASS COUNT IS ITSELF THE SIGNAL. All three lines that fail to resolve are
not share classes at all — ADAMK is "Adamas Trust, Inc. 9.600% Senior Notes", GOOGM and GOOGN are
"Alphabet Inc. Depositary Shares" — each typed CS by the reference feed, and each admitted until
now on its issuer's common-stock count.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest

from vinci import universe as uni
from vinci.config import Config
from vinci.eod import RawBar
from vinci.schemas.data_record import Identity
from vinci.universe import build_universe

_REF = date(2026, 6, 12)
_CIK = "0000000001"


def _ident(ticker: str, cik: str = _CIK) -> Identity:
    return Identity(
        internal_id=f"SEC-{cik}-{ticker}", issuer_id=f"ISS-{cik}", cik=cik,
        ticker=ticker, mic="XNAS", exchange="Nasdaq", eod_symbol=ticker,
        name=f"{ticker} Inc.", sic=None, sic_description=None,
    )


def _run(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, *,
         lines: list[tuple[str, str]],                       # (ticker, cik)
         closes: dict[str, float],
         class_counts: dict[str, float],
         xbrl_shares: dict[str, float] | None = None,
         xbrl_tag: str = "dei:EntityCommonStockSharesOutstanding",
         sec_types: dict[str, str] | None = None) -> tuple[dict, dict[str, dict]]:
    """Run the REAL builder over several fake lines; return (stats, {ticker: exported row})."""
    idents = [_ident(t, c) for t, c in lines]
    consulted: list[tuple[str, ...]] = []
    types = sec_types or {t: "CS" for t, _ in lines}

    class _R:
        @classmethod
        def from_config(cls, cfg: object) -> _R: return cls()
        def iter_universe(self, exchanges: object) -> Iterator[Identity]: yield from idents
        def sic_for(self, cik: str) -> tuple[str, str]: return ("7372", "Software")

    class _E:
        @classmethod
        def from_config(cls, cfg: object) -> _E: return cls()
        def grouped_daily(self, day: date) -> dict[str, RawBar]:
            if day != _REF:
                return {}
            return {t: RawBar(ticker=t, open=p, high=p, low=p, close=p, volume=10_000_000)
                    for t, p in closes.items()}
        def security_types(self) -> dict[str, str]: return types
        def share_class_counts(self, tickers: object) -> dict[str, float]:
            asked = tuple(tickers)
            consulted.append(asked)
            return {t: class_counts[t] for t in asked if t in class_counts}

    class _Ed:
        @classmethod
        def from_config(cls, cfg: object) -> _Ed: return cls()
        def shares_outstanding_with_provenance(
            self, periods: object, *, include_period_average: bool = False
        ) -> tuple[dict[str, float], dict[str, str]]:
            filed = xbrl_shares if xbrl_shares is not None else {}
            return (dict(filed), dict.fromkeys(filed, xbrl_tag))

    monkeypatch.setattr(uni, "EntityResolver", _R)
    monkeypatch.setattr(uni, "PolygonEodClient", _E)
    monkeypatch.setattr(uni, "EdgarClient", _Ed)
    stats = build_universe(Config(data_dir=tmp_path), reference_date=_REF,
                           share_periods=["CY2026Q1I"])
    snap = tmp_path / "snapshots" / "universe_snapshot.jsonl"
    rows = [json.loads(x) for x in snap.read_text().splitlines() if x.strip()] \
        if snap.exists() else []
    _run.last_consulted = consulted     # type: ignore[attr-defined]
    return stats, {r["internal_id"].split("-", 2)[2]: r for r in rows}


def test_each_listed_class_is_sized_by_its_own_count_not_the_issuers_total(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """THE ALPHABET SHAPE, scaled down. One filed count of 30M covers both classes; each line must
    take its own 20M / 10M instead, so the two caps sum to the company rather than doubling it."""
    stats, rows = _run(
        monkeypatch, tmp_path, lines=[("AAA", _CIK), ("AAB", _CIK)],
        closes={"AAA": 100.0, "AAB": 100.0},
        class_counts={"AAA": 20_000_000.0, "AAB": 10_000_000.0},
        xbrl_shares={_CIK: 30_000_000.0})
    assert stats["in_universe"] == 2
    assert stats["dual_class_count_used"] == 2
    assert rows["AAA"]["market_cap"] == 100.0 * 20_000_000.0     # NOT 100 x 30,000,000
    assert rows["AAB"]["market_cap"] == 100.0 * 10_000_000.0     # NOT 100 x 30,000,000
    total = rows["AAA"]["market_cap"] + rows["AAB"]["market_cap"]
    assert total == 100.0 * 30_000_000.0, "the classes must sum to the issuer, not to double it"


def test_the_per_class_count_wins_over_a_filed_count_that_is_present(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """THE DEFECT IS A PRESENT-AND-WRONG NUMBER, not a missing one — which is why this branch sits
    BEFORE the `no filed count` fallback. Falling through to a filed count that exists is exactly
    the bug: it is the issuer's total, and for this line it is 3x too high."""
    _, rows = _run(monkeypatch, tmp_path, lines=[("AAA", _CIK), ("AAB", _CIK)],
                   closes={"AAA": 50.0, "AAB": 50.0},
                   class_counts={"AAA": 10_000_000.0, "AAB": 20_000_000.0},
                   xbrl_shares={_CIK: 30_000_000.0})
    assert rows["AAA"]["market_cap"] == 50.0 * 10_000_000.0
    assert "share_class_shares_outstanding" in rows["AAA"]["source"]
    assert "PER-CLASS" in rows["AAA"]["source"]
    assert "EDGAR" not in rows["AAA"]["source"], "a filed count must not be claimed as the input"


def test_a_line_whose_per_class_count_will_not_resolve_is_left_exactly_as_it_was(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """STRICTLY NON-REGRESSIVE, and this pin is the retreat from a first draft that DROPPED such a
    line. The sibling test is a heuristic and it misfires: ACGL (Arch Capital, $34.5B of genuine
    common) publishes no per-class count while ACGLN — a PREFERRED depositary line typed CS by the
    same feed — publishes one, so the draft read two classes and excluded the common. A name
    wrongly EXCLUDED from the validation population is as damaging as one wrongly admitted.

    So the resolvable sibling is fixed and the unresolvable one keeps the sizing it already had."""
    stats, rows = _run(monkeypatch, tmp_path, lines=[("AAA", _CIK), ("AAB", _CIK)],
                       closes={"AAA": 100.0, "AAB": 100.0},
                       class_counts={"AAB": 10_000_000.0},          # AAA does not resolve
                       xbrl_shares={_CIK: 30_000_000.0})
    assert stats["in_universe"] == 2, "neither line may be dropped by this change"
    assert stats["dual_class_count_used"] == 1
    assert rows["AAB"]["market_cap"] == 100.0 * 10_000_000.0        # fixed
    assert rows["AAA"]["market_cap"] == 100.0 * 30_000_000.0        # untouched, as before
    assert "EDGAR" in rows["AAA"]["source"]


def test_a_single_class_issuer_still_uses_its_filed_xbrl_count(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """NO OVER-REACH. For a one-class issuer the filed count IS the class count, so nothing about
    its sizing may move — and the per-ticker reference call must never be spent on it."""
    stats, rows = _run(monkeypatch, tmp_path, lines=[("SOLO", "0000000009")],
                       closes={"SOLO": 25.0}, class_counts={"SOLO": 999.0},
                       xbrl_shares={"0000000009": 40_000_000.0})
    assert stats["in_universe"] == 1
    assert stats.get("dual_class_count_used", 0) == 0
    assert rows["SOLO"]["market_cap"] == 25.0 * 40_000_000.0     # the filed count, not 999
    assert "EDGAR" in rows["SOLO"]["source"]
    consulted = _run.last_consulted          # type: ignore[attr-defined]
    assert all("SOLO" not in c for c in consulted), consulted


def test_an_unpriced_sibling_does_not_make_a_single_class_name_multi_class(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A sibling with no close is dropped at `no_price` and never competes for the cap, so it must
    not route the surviving line down the per-class path — that would spend a call, and would drop
    the name outright if the reference had no count for it."""
    stats, rows = _run(monkeypatch, tmp_path, lines=[("AAA", _CIK), ("AAB", _CIK)],
                       closes={"AAA": 100.0},                      # AAB has no bar at all
                       class_counts={}, xbrl_shares={_CIK: 30_000_000.0})
    assert stats["no_price"] == 1
    assert stats.get("dual_class_count_used", 0) == 0
    assert rows["AAA"]["market_cap"] == 100.0 * 30_000_000.0


def test_a_multi_class_line_is_never_labelled_a_period_average(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The filed tag still says `WeightedAverage...`, but no XBRL tier decided this line — so the
    approximation counters and the `PERIOD AVERAGE` stamp must not claim it. Left uncorrected, an
    out-of-band drop would be attributed to an approximation that never ran."""
    stats, rows = _run(
        monkeypatch, tmp_path, lines=[("AAA", _CIK), ("AAB", _CIK)],
        closes={"AAA": 100.0, "AAB": 100.0},
        class_counts={"AAA": 20_000_000.0, "AAB": 10_000_000.0},
        xbrl_shares={_CIK: 30_000_000.0},
        xbrl_tag="us-gaap:WeightedAverageNumberOfSharesOutstandingBasic")
    assert stats.get("shares_period_average", 0) == 0
    assert stats.get("out_of_band_period_average", 0) == 0
    assert all("PERIOD AVERAGE" not in r["source"] for r in rows.values())


def test_a_depositary_line_of_a_multi_class_issuer_still_takes_the_ads_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """BRANCH ORDER. Both paths read the same reference field, but the ADR branch must keep
    precedence — its stamp is what says the count is ADS-denominated, and the drop stage it owns
    (`ads_count_unresolved`) is the one that names the real failure for a receipt."""
    _, rows = _run(monkeypatch, tmp_path, lines=[("AAA", _CIK), ("AAD", _CIK)],
                   closes={"AAA": 100.0, "AAD": 100.0},
                   class_counts={"AAA": 20_000_000.0, "AAD": 10_000_000.0},
                   xbrl_shares={_CIK: 30_000_000.0},
                   sec_types={"AAA": "CS", "AAD": "ADRC"})
    assert "ADS-denominated" in rows["AAD"]["source"]
    assert "PER-CLASS" in rows["AAA"]["source"]


def test_a_warrant_sibling_does_not_make_the_common_line_multi_class(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """MEASURED ON THE FIRST REAL RUN, and the reason this gate exists. Counting any two securities
    that share a CIK swept in every SPAC unit, warrant and note: 1,760 lines went down the
    per-class path (935 sized, 825 dropped) against the 46 that are real classes. Those lines still
    drop — they always did — but at the stage their exclusion is actually about. A stage that
    claims 825 warrants is a funnel that lies about why a name left."""
    stats, rows = _run(monkeypatch, tmp_path, lines=[("AAA", _CIK), ("AAAW", _CIK)],
                       closes={"AAA": 100.0, "AAAW": 2.0},
                       class_counts={},                       # neither line resolves per-class
                       xbrl_shares={_CIK: 30_000_000.0},
                       sec_types={"AAA": "CS", "AAAW": "WARRANT"})
    assert stats.get("dual_class_count_used", 0) == 0
    assert rows["AAA"]["market_cap"] == 100.0 * 30_000_000.0   # the common line is untouched
    assert "AAAW" not in rows                                  # still excluded, by its own gate
    consulted = _run.last_consulted        # type: ignore[attr-defined]
    assert all("AAAW" not in c for c in consulted), consulted
