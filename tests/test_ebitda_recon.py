"""CIQ's EBITDA against the filings — the quarterly reconciliation, pinned (2026-10-21).

THE DEFECT (a review of TJX's page). Every EV/EBITDA on the page divides CIQ's EBITDA, and the page
called it "GAAP basis". TJX's Q2 FY27 reads $1,996M at CIQ and $2,327M rebuilt from the 10-Q
(pre-tax $2,018M − net interest income $31M + D&A $340M): $331M apart, the gross tariff refund the
release states to the million; the three earlier quarters agree to the dollar.

THE FLEET, measured before any pin (2026-10-21, main 4b514dca, the 27 committed pages): TJX −$331M
and ROST −$253M each quote their release's matching sentence; V's +$708M quotes "$707 million for a
litigation provision"; TGT's −$956M finds no amount within 2% (its release states $994M) and quotes
nothing; AMZN's LTM matches while two quarters swap $2,500M; NFLX, UBER and TECX match; BURL, CNXC
and five others cannot be rebuilt (no quarterly D&A or operating-income tag) and say so.

The fixture is TJX's REAL filed figures, frozen — Q4 is the 10-K year less the nine-month YTD.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from tests.test_release_adjusted_eps import _rel
from vinci.dossier import ebitda_recon as er

_PRETAX = ("IncomeLossFromContinuingOperationsBeforeIncomeTaxes"
           "ExtraordinaryItemsNoncontrollingInterest")
_NII = "InterestRevenueExpenseNet"
_DA = "DepreciationDepletionAndAmortization"
#: TJX's companyfacts points, as filed ($), for the four quarters of CIQ's LTM to 2026-08-01
_TJX_POINTS: dict[str, list[tuple[str, str, int, str, str]]] = {
    _PRETAX: [("2025-02-02", "2025-11-01", 4909000000, "2025-12-02", "10-Q"),
              ("2025-02-02", "2026-01-31", 7299000000, "2026-03-31", "10-K"),
              ("2025-08-03", "2025-11-01", 1916000000, "2025-12-02", "10-Q"),
              ("2026-02-01", "2026-05-02", 1721000000, "2026-05-29", "10-Q"),
              ("2026-05-03", "2026-08-01", 2018000000, "2026-08-28", "10-Q")],
    _NII: [("2025-02-02", "2025-11-01", 85000000, "2025-12-02", "10-Q"),
           ("2025-02-02", "2026-01-31", 121000000, "2026-03-31", "10-K"),
           ("2025-08-03", "2025-11-01", 28000000, "2025-12-02", "10-Q"),
           ("2026-02-01", "2026-05-02", 35000000, "2026-05-29", "10-Q"),
           ("2026-05-03", "2026-08-01", 31000000, "2026-08-28", "10-Q")],
    _DA: [("2025-02-02", "2025-11-01", 920000000, "2025-12-02", "10-Q"),
          ("2025-02-02", "2026-01-31", 1247000000, "2026-03-31", "10-K"),
          ("2025-08-03", "2025-11-01", 316000000, "2025-12-02", "10-Q"),
          ("2026-02-01", "2026-05-02", 336000000, "2026-05-29", "10-Q"),
          ("2026-05-03", "2026-08-01", 340000000, "2026-08-28", "10-Q")],
}
_CIQ = {"Nov-01-2025": 2204.0, "Jan-31-2026": 2681.0, "May-02-2026": 2022.0, "Aug-01-2026": 1996.0}
#: TJX 8-K 0000109198-26-000045 EX-99.1, the refund sentence, verbatim
_RELEASE = ("3 IEEPA Tariff Refunds and Related Expense Accruals During the second quarter of "
            "Fiscal 2027, the Company received aggregate refunds of $331 million for a portion of"
            " the IEEPA tariffs it previously paid. As a result, these tariff refunds benefitted "
            "the Company's second quarter Fiscal 2027 cost of sales.")


def _facts(points: dict[str, list[tuple[str, str, int, str, str]]]) -> dict[str, Any]:
    return {"facts": {"us-gaap": {tag: {"units": {"USD": [
        {"start": s, "end": e, "val": v, "filed": f, "form": fm, "accn": "x"}
        for s, e, v, f, fm in rows]}} for tag, rows in points.items()}}}


class _Bundle:
    """The one sheet `reconcile` reads, shaped as CIQ exports it (header row + EBITDA row)."""

    def __init__(self, ciq: dict[str, float]) -> None:
        self._rows = [["For the Fiscal Period Ending", *ciq], ["EBITDA", *ciq.values()]]

    def workbook(self, kind: str, freq: str | None = None) -> object:
        return object()

    def sheet(self, kind: str, name: str, freq: str | None = None) -> list[list[Any]]:
        return self._rows


def _tjx(release_text: str | None = _RELEASE) -> Any:
    rel = _rel("0000109198-26-000045", "2026-08-19", [])
    return er.reconcile(_Bundle(_CIQ), _facts(_TJX_POINTS), [rel],  # type: ignore[arg-type]
                        lambda r: release_text)


def test_tjx_q2_is_331m_below_its_10q_and_the_release_states_it() -> None:
    """THE RED. Three quarters agree to the dollar; Q2 is −$331M, DIFFERENT, and the quarter's
    release sentence stating $331 million rides beside it verbatim."""
    rec = _tjx()
    assert [(r.period_end, r.filing_ebitda) for r in rec.quarters] == [
        ("2025-11-01", 2204.0), ("2026-01-31", 2681.0), ("2026-05-02", 2022.0),
        ("2026-08-01", 2327.0)]
    q2 = rec.quarters[-1]
    assert q2.gap == pytest.approx(-331.0) and q2.different
    assert q2.matching_amount is not None and "$331 million" in q2.matching_amount
    assert not any(r.different for r in rec.quarters[:3])
    assert rec.ciq_ltm == pytest.approx(8903.0) and rec.filing_ltm == pytest.approx(9234.0)
    assert "−$331M" in rec.line and "Every EV/EBITDA on this page divides CIQ's" in rec.line


def test_the_fourth_quarter_is_the_year_less_nine_months() -> None:
    """A 10-K tags the YEAR; Q4 is FY − the nine-month YTD from the same start (2,390 − 36 + 327),
    never the year itself read as a quarter."""
    assert _tjx().quarters[1].filing_ebitda == pytest.approx(2681.0)


def test_a_quarter_without_a_net_interest_line_is_not_rebuilt() -> None:
    """NO GUESSED CONSTRUCTION: without operating income, pre-tax needs a NET interest line whose
    sign is unambiguous. Remove it and every quarter is stated as unrebuildable, with why."""
    pts = {k: v for k, v in _TJX_POINTS.items() if k != _NII}
    rec = er.reconcile(_Bundle(_CIQ), _facts(pts), [], lambda r: None)  # type: ignore[arg-type]
    assert all(r.filing_ebitda is None and r.note for r in rec.quarters)
    assert rec.filing_ltm is None and not rec.any_different
    assert rec.line.startswith("CIQ's quarterly EBITDA could not be set against the filings")


def test_only_an_amount_within_two_percent_is_quoted() -> None:
    """POSITIVE above. NEGATIVE: TGT's shape — a $956M gap beside a release stating $994M (3.9%
    off) quotes nothing; the gap stands, unattributed."""
    assert er._matching_sentence("tariff refund benefits of $994 million within gross margin.",
                                 -956.0) is None
    assert er._matching_sentence(_RELEASE, -331.0) is not None
    rec = _tjx("refunds of $345 million were received.")
    assert rec.quarters[-1].different and rec.quarters[-1].matching_amount is None


def test_an_ltm_that_matches_while_quarters_swap_says_so() -> None:
    """AMZN's shape: the LTM agrees to the dollar while two quarters move $2,500M between them.
    The line says the LTM matches AND that the quarters do not — neither claim hides the other."""
    pts = _facts({"OperatingIncomeLoss": [
        ("2025-07-01", "2025-09-30", 30000000000, "2025-10-30", "10-Q"),
        ("2025-10-01", "2025-12-31", 40000000000, "2026-02-06", "10-K"),
        ("2026-01-01", "2026-03-31", 35000000000, "2026-04-30", "10-Q"),
        ("2026-04-01", "2026-06-30", 38000000000, "2026-07-31", "10-Q")],
        _DA: [("2025-07-01", "2025-09-30", 4000000000, "2025-10-30", "10-Q"),
              ("2025-10-01", "2025-12-31", 4000000000, "2026-02-06", "10-K"),
              ("2026-01-01", "2026-03-31", 4000000000, "2026-04-30", "10-Q"),
              ("2026-04-01", "2026-06-30", 4000000000, "2026-07-31", "10-Q")]})
    ciq = {"Sep-30-2025": 36500.0, "Dec-31-2025": 41500.0, "Mar-31-2026": 39000.0,
           "Jun-30-2026": 42000.0}
    rec = er.reconcile(_Bundle(ciq), pts, [], lambda r: None)  # type: ignore[arg-type]
    assert rec.ltm_gap == pytest.approx(0.0)
    assert "its LTM matches the filings" in rec.line and "+$2,500M" in rec.line
    assert "−$2,500M" in rec.line


def test_every_committed_reconciliation_is_internally_consistent_e2e() -> None:
    """On every committed page that carries one: each quarter's gap IS ciq − filing; `different`
    IS the stated threshold; a quoted sentence states an amount within the tolerance of the gap;
    the LTM is the four quarters' sum. Invariants only — a living page's figures move."""
    seen = 0
    for p in sorted(Path("data/dossiers").glob("*/dossier.json")):
        rec = (json.loads(p.read_text())["mechanical"].get("financial_summary") or {}).get(
            "ebitda_reconciliation")
        if not rec:
            continue
        seen += 1
        qs = rec["quarters"]
        assert len(qs) == 4 and rec["ciq_ltm"] == pytest.approx(sum(q["ciq_ebitda"] for q in qs))
        for q in qs:
            if q["filing_ebitda"] is None:
                assert q["note"] and not q["different"], (p.parent.name, q)
                continue
            assert q["gap"] == pytest.approx(q["ciq_ebitda"] - q["filing_ebitda"], abs=1e-3)
            want = abs(q["gap"]) > er.DIFFERENT_SHARE * abs(q["filing_ebitda"]) and abs(
                q["gap"]) >= 1.0
            assert q["different"] == want, (p.parent.name, q)
            if q["matching_amount"]:
                assert er._matching_sentence(q["matching_amount"], q["gap"]) is not None
        assert rec["any_different"] == any(q["different"] for q in qs)
    assert seen >= 15, f"only {seen} pages carry the reconciliation — the pass did not land"


def test_no_committed_page_calls_ciqs_ebitda_gaap_e2e() -> None:
    """The label the review flagged, on every committed page: the triangulation rows and the
    leverage caveat name CIQ's EBITDA as the vendor's."""
    for p in sorted(Path("data/dossiers").glob("*/dossier.json")):
        text = p.read_text()
        assert "(CIQ, GAAP basis)" not in text and "(CIQ comps, GAAP basis)" not in text, p
        assert "(CIQ / consolidated GAAP)" not in text, p


def test_the_brief_prints_the_reconciliation_where_quarters_differ_md_e2e() -> None:
    """Both directions, on the committed pages: a page whose reconciliation finds a different
    quarter prints its sentence in the brief; one that matches prints nothing of it."""
    from vinci.dossier import render as dr
    from vinci.dossier import schemas as ds
    from vinci.dossier.assemble import _read_scenario_card

    shown = quiet = 0
    for p in sorted(Path("data/dossiers").glob("*/dossier.json")):
        doc = ds.Dossier.model_validate_json(p.read_text())
        fs = doc.mechanical.financial_summary
        rec = fs.ebitda_reconciliation if fs is not None else None
        if rec is None:
            continue
        brief = dr.render_markdown(doc, card=_read_scenario_card(doc.ticker)).split(
            "# Analysis — full dossier", 1)[0]
        if rec.any_different:
            assert f"> **CIQ's EBITDA against the filings.** {rec.line}" in brief, doc.ticker
            shown += 1
        else:
            assert "CIQ's EBITDA against the filings" not in brief, doc.ticker
            quiet += 1
    assert shown >= 5 and quiet >= 1, (shown, quiet)


def test_period_ends_are_iso_dates() -> None:
    assert all(date.fromisoformat(r.period_end) for r in _tjx().quarters)


# --- the leverage caveat, regenerated on a kept synthesis -----------------------------------------

#: TGT's caveat VERBATIM as main 4b514dca committed it — the one sentence that called CIQ's EBITDA
#: "REPORTED … (CIQ / consolidated GAAP)".
_OLD_TGT_CAVEAT = (
    "Net debt/EBITDA (1.6x) is on REPORTED EBITDA (CIQ / consolidated GAAP), not the covenant "
    "basis; management and credit covenants typically define leverage on adjusted EBITDA (a "
    "larger denominator → a lower ratio), reconciled in the earnings release/transcript "
    "(currently UNAVAILABLE) — do not read 1.6x as the covenant-basis leverage.")


def test_the_leverage_caveat_is_regenerated_never_string_edited() -> None:
    """(+) TGT's page with main's caveat put back: the transform rebuilds exactly that one, through
    the assembler's `_leverage_basis_flag`, into the caveat the committed page carries. (0) The
    committed page — nothing to regenerate. (−) Two candidates: refused, never a guess at which."""
    from vinci.dossier.refresh import leverage_caveat_transform

    doc = json.loads(Path("data/dossiers/TGT/dossier.json").read_text())
    now = list(doc["caveats"])
    i = next(i for i, c in enumerate(now) if c.startswith("Net debt/EBITDA ("))
    assert "CIQ's EBITDA (vendor-normalised" in now[i]
    old = dict(doc, caveats=[*now[:i], _OLD_TGT_CAVEAT, *now[i + 1:]])
    assert leverage_caveat_transform()(old) == {"caveats": now}
    assert leverage_caveat_transform()(doc) == {}
    with pytest.raises(ValueError, match="cannot be regenerated"):
        leverage_caveat_transform()(dict(doc, caveats=[_OLD_TGT_CAVEAT, _OLD_TGT_CAVEAT]))


def test_a_stated_amount_matches_only_at_its_own_precision() -> None:
    """(−) SIMPLY GOOD, verbatim (8-K 0001702744-26-000021): +$95.5M is an $82.0M impairment with
    integration and restructuring costs; the 2% window alone quoted the marketing line, 1.6% away.
    (+) VISA, verbatim (8-K 0001403161-26-000044): "$707 million" against +$708.0M — one unit of
    its stated precision, the rounding of a figure stated to the million."""
    smpl = ("Selling and marketing expenses of $97.0 million decreased 4.8% versus the comparable "
            "year ago period driven by planned marketing declines for Atkins.")
    assert er._matching_sentence(smpl, 95.5) is None
    assert er._matching_sentence(smpl, 97.05) is not None          # within its 0.1 unit
    visa = ("Current year's results included special items of $707 million for a litigation "
            "provision associated with the interchange multidistrict litigation (\"MDL\") case.")
    assert er._matching_sentence(visa, 708.0) is not None
    assert er._matching_sentence(visa, 709.0) is None              # two units off
