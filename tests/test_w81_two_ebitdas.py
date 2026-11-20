"""W81 (defect SP-D20): CIQ'S TWO EBITDAs, EACH NAMED ONE WAY WHEREVER IT PRINTS, AND THE CAUSE OF
THEIR DIFFERENCE NAMED WHERE ONE CIQ ROW RECONCILES IT (operator 2026-11-19, "Approve with
correction").

THE DEFECT. A page carries two CIQ EBITDAs. One is the LTM column of CIQ's ANNUAL export. The
other is the QUARTERLY export's four quarters summed. On MORN (a scratch page, 2026-11-19) they read
719.4 and 822.1: the annual figure leaves out the Cash Flow's 'Other Amortization' (102.7). The page
called the annual figure "reported LTM EBITDA", which reads as the company's filed figure. It sat
beyond 2% of the filing-rebuilt EBITDA on 10 of the 17 committed pages carrying both (main
6e03501f). And the LTM-quarters check flagged the difference with no cause.

THE FIX, IN THREE PARTS, each pinned here.
* The annual figure is "CIQ's annual LTM EBITDA" and the quarters' sum is "CIQ's four-quarter
  EBITDA", wherever either prints. "After rent" is only a qualifier, where the rent contrast is
  drawn. Pinned end to end on the committed pages, through the builders that write each line.
* The LTM check names the cause of an EBITDA DIFFER when 'Other Amortization' reconciles it, at the
  check's own tolerance, and otherwise says the cause was not read. Pinned on frozen cells of four
  pages' own exports (`tests/fixtures/ciq_ltm_ebitda_cause.json`), through the real check.
* `refresh.refreshed_ltm_flags` carries that cause to a committed page at $0, and refuses unless the
  cause is all that moves. Pinned on the four pages as frozen at the cut (`cut-4889ddba`, the same
  recorded exports, LTM flags and annual table as the living pages at `bc1c0e16`).
"""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

import pytest

from tests.frozen_support import frozen_doc
from vinci.dossier import ebitda_recon as er
from vinci.dossier import ev_ebitda_basis as eb
from vinci.dossier import ltm_quarters as lq
from vinci.dossier import refresh as rf
from vinci.dossier.ciq import CiqBundle, CiqFormat, CiqWorkbook
from vinci.dossier.schemas import MechanicalLayer

ROOT = Path(__file__).resolve().parents[1]
PAGES = sorted((ROOT / "data" / "dossiers").glob("*/dossier.json"))
FIX: dict[str, Any] = json.loads(
    (ROOT / "tests" / "fixtures" / "ciq_ltm_ebitda_cause.json").read_text())
CF = "financials|annual|Cash Flow"
EBITDA_FLAG = f"{lq.FLAG_PREFIX} EBITDA ($M)"
#: The approved names, as literals: the pins read the operator's words, not a constant's.
ANNUAL = "CIQ's annual LTM EBITDA"
FOUR_Q = "CIQ's four-quarter EBITDA"

#: The old words of the basis line and the new, in the order they apply. The ONLY change W81 makes
#: to that stored sentence (`w81_relabel`); every figure, ratio and date in it is untouched.
_RELABEL: tuple[tuple[str, str], ...] = (
    ("which reproduces reported LTM EBITDA (", f"which reproduces {ANNUAL} ("),
    (") and EBITDA plus rent alike", ") and that plus rent alike"),
    ("It is NOT a multiple of reported EBITDA (",
     f"It is NOT a multiple of {ANNUAL}, after rent ("),
    ("— a multiple of reported EBITDA.", "— a multiple of that figure, after rent."),
    ("before comparing it with a multiple of reported EBITDA.",
     "before comparing it with a multiple struck after rent."),
    ("reported LTM EBITDA $", f"{ANNUAL} $"),
)


def w81_relabel(line: str) -> str:
    """A basis line written before W81, as W81's code writes it: the words moved, nothing else."""
    for old, new in _RELABEL:
        line = line.replace(old, new)
    return line


def _doc(path: Path) -> dict[str, Any]:
    loaded: dict[str, Any] = json.loads(path.read_text())
    return loaded


def _mech(raw: dict[str, Any]) -> MechanicalLayer:
    return MechanicalLayer.model_validate(raw["mechanical"])


def _basis_pages() -> list[Path]:
    return [p for p in PAGES
            if (_doc(p)["mechanical"].get("valuation") or {}).get("ev_ebitda_basis")]


# --- the basis line: CIQ's annual LTM EBITDA, named as what it is --------------------------------

def test_one_name_per_figure_in_the_code() -> None:
    """(+) Each figure's name is held once, as approved, and every line that prints it reads the
    one constant. (−) The two names are different words: SP-D20 was one name for two figures."""
    assert (eb.ANNUAL_LTM, eb.FOUR_QUARTER) == (ANNUAL, FOUR_Q)
    assert ANNUAL != FOUR_Q


def test_the_population_is_the_twenty_pages_the_probe_counted() -> None:
    """The pins below walk every committed page carrying the block: 20 at main 6e03501f. A walk
    that found none would pass every assertion below vacuously."""
    assert len(_basis_pages()) >= 20


@pytest.mark.parametrize("path", _basis_pages(), ids=lambda p: p.parent.name)
def test_the_basis_line_names_the_annual_figure_and_never_reported(path: Path) -> None:
    """(+) END TO END, the committed page through the builder that writes the line (the one the
    refresh runs): where a pairing is measured, the line names CIQ's annual LTM EBITDA, followed by
    the page's own stored figure. (−) The word "reported" is gone from the line. Main wrote
    "reported LTM EBITDA $8,903M" on TJX and every other measured page."""
    raw = _doc(path)
    got = eb.headline_basis(_mech(raw))
    assert got is not None
    assert not re.search(r"\breported\b", got.line, re.I), got.line
    if got.reading in eb.DATE_READINGS:
        return                                   # no pairing measured, so no EBITDA is named
    figure = f"${got.reported_ltm_ebitda:,.0f}M"
    assert (f"{ANNUAL} {figure}" in got.line
            or f"{ANNUAL} ({figure})" in got.line), got.line


#: A committed block written before W65 (#1136) carries no `multiple_close`; where the head code
#: reads its TEV and multiple more than four days apart it measures no pairing, so that page's line
#: moves by more than W81's words. Derived from the page, never a list of names: GOOGL left the set
#: when it was rebuilt under W73 (51c84843), and AMZN (a watch page) is in it until it is rebuilt.
def _same_reading(path: Path) -> bool:
    raw = _doc(path)
    got = eb.headline_basis(_mech(raw))
    return got is not None and got.reading == raw["mechanical"]["valuation"]["ev_ebitda_basis"][
        "reading"]


def test_a_page_whose_reading_changes_is_a_pre_w65_block_moving_to_a_date_reading() -> None:
    """The pin below skips the pages whose reading the head code changes. Each one is a block
    written before W65 (no `multiple_close`) whose rebuild is a W65 date reading, never a page this
    change moved; and at least one page keeps its reading, so the pin below is not empty."""
    moved = [p for p in _basis_pages() if not _same_reading(p)]
    for p in moved:
        block = _doc(p)["mechanical"]["valuation"]["ev_ebitda_basis"]
        got = eb.headline_basis(_mech(_doc(p)))
        assert "multiple_close" not in block and got is not None, p.parent.name
        assert got.reading in eb.DATE_READINGS, (p.parent.name, got.reading)
    assert len(moved) < len(_basis_pages())


@pytest.mark.parametrize("path", [p for p in _basis_pages() if _same_reading(p)],
                         ids=lambda p: p.parent.name)
def test_only_the_words_move_every_figure_stays(path: Path) -> None:
    """(−) The rebuilt line is the committed one with W81's words moved and nothing else: every
    figure, ratio and date as stored. (+) `w81_relabel` changes the committed line wherever a
    pairing is measured, so the equality is not two old lines agreeing."""
    raw = _doc(path)
    committed = raw["mechanical"]["valuation"]["ev_ebitda_basis"]["line"]
    got = eb.headline_basis(_mech(raw))
    assert got is not None
    assert got.line == w81_relabel(committed)
    if got.reading not in eb.DATE_READINGS:
        assert w81_relabel(committed) != committed


def test_after_rent_qualifies_and_never_names() -> None:
    """(+/−) "after rent" appears only as a qualifier on a named figure or a multiple, never as a
    figure's name in place of one, on every committed page's rebuilt line. TJX is the shape: "It is
    NOT a multiple of CIQ's annual LTM EBITDA, after rent ($8,903M, …)"."""
    seen = 0
    for path in _basis_pages():
        got = eb.headline_basis(_mech(_doc(path)))
        assert got is not None
        for m in re.finditer(r"after rent", got.line):
            seen += 1
            before = got.line[:m.start()]
            assert before.endswith((f"{ANNUAL}, ", "that figure, ", "struck ")), got.line
        assert "EBITDA after rent" not in got.line, got.line
    assert seen > 0


# --- the four-quarter figure: the at-price line and the reconciliation --------------------------

def _recon_pages() -> list[Path]:
    out = []
    for p in PAGES:
        rec = ((_doc(p)["mechanical"].get("financial_summary") or {})
               .get("ebitda_reconciliation") or {})
        if (rec.get("quarters") and rec.get("ciq_ltm") is not None
                and rec.get("filing_ltm") is not None):
            out.append(p)
    return out


@pytest.mark.parametrize("path", _recon_pages(), ids=lambda p: p.parent.name)
def test_the_reconciliation_names_the_four_quarter_figure(path: Path) -> None:
    """(+) END TO END, the committed reconciliation through its own sentence builder
    (`ebitda_recon._line`, a pure function of the stored quarters): where it states the quarters'
    sum, it calls it CIQ's four-quarter EBITDA, with the stored figure. (−) "its LTM" is gone. On
    MCK main said "its LTM matches the filings ($7,518M …)" beside an annual LTM column of 7,350."""
    rec = _mech(_doc(path)).financial_summary.ebitda_reconciliation  # type: ignore[union-attr]
    assert rec is not None and rec.ciq_ltm is not None
    line = er._line(list(rec.quarters), rec.ciq_ltm, rec.filing_ltm, rec.ltm_gap)
    assert "its LTM" not in line, line
    if any(q.different for q in rec.quarters):
        assert (f"{FOUR_Q} ${rec.ciq_ltm:,.0f}M" in line
                or f"{FOUR_Q} matches the filings (${rec.ciq_ltm:,.0f}M" in line), line


def test_the_reconciliation_population_includes_mck() -> None:
    """The walk above is not empty, and it holds MCK, the page whose two figures differ by 168."""
    assert "MCK" in {p.parent.name for p in _recon_pages()}


# --- the cause of an EBITDA DIFFER, on frozen cells of four pages' own exports -------------------

def _bundle(name: str, sheets: dict[str, list[list[str]]] | None = None) -> CiqBundle:
    """The frozen cells as a REAL bundle, one workbook per period type."""
    src = sheets or FIX["names"][name]["sheets"]
    workbooks, cache = [], {}
    for key, rows in src.items():
        _kind, freq, sheet = key.split("|")
        path = Path("/frozen") / f"{name}-{freq}.xls"
        if path not in cache:
            workbooks.append(CiqWorkbook(kind="financials", path=path, fmt=CiqFormat.BIFF_XLS,
                                         freq=freq))
            cache[path] = {}
        cache[path][sheet] = copy.deepcopy(rows)
    return CiqBundle(ticker=name, workbooks=tuple(workbooks), _cache=cache)


def _table(name: str) -> Any:
    fs = _mech(frozen_doc(name)).financial_summary
    assert fs is not None
    return fs.annual.value


def _ebitda(name: str, sheets: dict[str, list[list[str]]] | None = None) -> lq.LtmCheck:
    read = lq.check(_bundle(name, sheets), _table(name))
    return next(r for r in read.rows if r.label == "EBITDA ($M)")


def _cf_row(name: str, label: str) -> int:
    rows = FIX["names"][name]["sheets"][CF]
    return next(i for i, r in enumerate(rows) if r and r[0].strip() == label)


@pytest.mark.parametrize(("name", "oa", "annual_plus", "left"), [
    ("MCK", "164.0", "7,514.0", "4.0 $M (0.05%) left"),
    ("IT", "73.5", "1,494.4", "9.8 $M (0.65%) left"),
])
def test_other_amortization_is_named_where_it_reconciles(name: str, oa: str, annual_plus: str,
                                                         left: str) -> None:
    """(+) VALUES ON FROZEN CELLS. CIQ's annual LTM EBITDA is EBIT plus 'Depreciation & Amort.,
    Total', and adding the Cash Flow's 'Other Amortization' brings it within the check's own 2% of
    the quarters. The flag names the row, its 1-based position in the export, the reconciled
    figure, and the remainder in $M and as a share. Main stated no cause at all."""
    r = _ebitda(name)
    assert r.outcome == "differ"
    assert r.cause is not None and r.cause.startswith("The cause, read:"), r.cause
    row = _cf_row(name, "Other Amortization") + 1
    assert f"'Other Amortization' ({oa}, row {row})" in r.cause
    assert f"reads {annual_plus}" in r.cause and left in r.cause
    assert r.flag().endswith(r.cause)


@pytest.mark.parametrize(("name", "why"), [
    ("VITL", "which does not reconcile with"),                # −13.6 + 2.8 is 1.5 $M off −12.3
    ("WLK", f"{FOUR_Q} is below {ANNUAL}"),   # quarters 1,169.0 under 1,236.0
])
def test_elsewhere_the_flag_says_the_cause_was_not_read(name: str, why: str) -> None:
    """(−) Where the row does not reconcile the gap, or cannot (the quarters are the lower figure),
    the flag says the cause was not read, and why. It never names a cause it did not measure."""
    r = _ebitda(name)
    assert r.outcome == "differ"
    assert r.cause is not None and r.cause.startswith("Its cause was not read:"), r.cause
    assert why in r.cause, r.cause


def _with_cf(name: str, label: str, value: str) -> dict[str, list[list[str]]]:
    """``name``'s frozen cells with ONE annual Cash Flow LTM cell moved — a real shape, one fact
    changed."""
    sheets = copy.deepcopy(FIX["names"][name]["sheets"])
    rows = sheets[CF]
    i = _cf_row(name, label)
    j = next(k for k, c in enumerate(rows[i]) if k and c.strip())
    rows[i][j] = value
    return sheets


def test_a_row_that_closes_less_than_half_the_gap_is_not_the_cause() -> None:
    """(−) MCK with 'Other Amortization' at 80.0: the annual figure plus it (7,430.0) still agrees
    with the quarters (7,518.0) within 2%, but it leaves 88.0 of a 168.0 gap, more than it closes.
    (+) At 90.0 it leaves 78.0, less than half, and is named."""
    small = _ebitda("MCK", _with_cf("MCK", "Other Amortization", "80.0"))
    assert small.cause is not None and small.cause.startswith("Its cause was not read:")
    enough = _ebitda("MCK", _with_cf("MCK", "Other Amortization", "90.0"))
    assert enough.cause is not None and enough.cause.startswith("The cause, read:")


def test_an_annual_figure_not_shown_to_leave_the_row_out_names_no_cause() -> None:
    """(−) MCK with 'Depreciation & Amort., Total' at 600.0: EBIT plus it (7,307.0) is not the
    annual figure (7,350.0), so the annual is not shown to leave 'Other Amortization' out."""
    r = _ebitda("MCK", _with_cf("MCK", "Depreciation & Amort., Total", "600.0"))
    assert r.cause is not None and "is not shown to be EBIT plus" in r.cause, r.cause


def test_a_row_with_no_positive_figure_is_said_so() -> None:
    """(−) MCK with 'Other Amortization' at 0.0: the flag says the row carries no positive figure,
    the reason, never that a zero "does not reconcile" (which is true of it but not why)."""
    r = _ebitda("MCK", _with_cf("MCK", "Other Amortization", "0.0"))
    assert r.cause is not None and "carries no positive figure" in r.cause, r.cause


def test_only_the_ebitda_row_carries_a_cause() -> None:
    """(−) MCK's EBIT also differs from its quarters (by 168.0); W81 explains EBITDA only, so every
    other row's flag is as the check always wrote it."""
    read = lq.check(_bundle("MCK"), _table("MCK"))
    others = [r for r in read.rows if r.label != "EBITDA ($M)"]
    assert any(r.label == "EBIT ($M)" and r.outcome == "differ" for r in others)
    assert all(r.cause is None for r in others)


# --- carrying the cause to a committed page at $0 -----------------------------------------------

def _shas(name: str) -> dict[str, str]:
    return {freq: w["sha256"] for freq, w in FIX["names"][name]["workbooks"].items()}


@pytest.mark.parametrize(("name", "lead"), [("IT", "The cause, read:"),
                                            ("VITL", "Its cause was not read:")])
def test_the_refresh_moves_only_the_ebitda_flag(name: str, lead: str) -> None:
    """(+) The committed page, re-run on frozen cells of its own recorded exports: exactly one flag
    moves, the EBITDA one, and only by gaining its cause; every other flag keeps its text and
    place."""
    doc = frozen_doc(name)
    new = rf.refreshed_ltm_flags(doc, _bundle(name), _shas(name))
    old = doc["qa_flags"]
    moved = [(a, b) for a, b in zip(old, new, strict=True) if a != b]
    assert len(moved) == 1
    a, b = moved[0]
    assert a.startswith(EBITDA_FLAG) and b.startswith(a + f". {lead}")


def test_another_export_is_refused() -> None:
    """(−) An export whose sha256 is not the one the page records is never read under it."""
    doc = frozen_doc("IT")
    wrong = {**_shas("IT"), "annual": "0" * 64}
    with pytest.raises(rf.RefreshRefusedError, match="not the one the page records"):
        rf.refreshed_ltm_flags(doc, _bundle("IT"), wrong)


def test_a_page_recording_no_export_is_refused() -> None:
    """(−) A page that records no Financials export cannot show the re-run reads its own."""
    doc = frozen_doc("IT")
    doc["inputs"]["ciq"] = [c for c in doc["inputs"]["ciq"] if c.get("kind") != "financials"]
    with pytest.raises(rf.RefreshRefusedError, match="records no annual Financials export"):
        rf.refreshed_ltm_flags(doc, _bundle("IT"), _shas("IT"))


def test_a_re_run_that_moves_more_than_the_cause_is_refused() -> None:
    """(−) IT with one quarter's EBITDA moved in the frozen cells: the re-run's DIFFER text no
    longer matches the page's, so more than the cause would move, and nothing is written."""
    sheets = copy.deepcopy(FIX["names"]["IT"]["sheets"])
    q = sheets["financials|quarterly|Income Statement"]
    i = next(k for k, r in enumerate(q) if r and r[0].strip() == "EBITDA")
    j = next(k for k, c in enumerate(q[i]) if k and c.strip())
    q[i][j] = str(float(q[i][j]) + 10.0)
    doc = frozen_doc("IT")
    with pytest.raises(rf.RefreshRefusedError, match="more than the cause would move"):
        rf.refreshed_ltm_flags(doc, _bundle("IT", sheets), _shas("IT"))


def test_the_seam_admits_qa_flags() -> None:
    """(+) `refresh_dossier` lets a top-level step set `qa_flags`, the one key this transform
    writes. (−) The seam stays closed to the synthesis and the anchor."""
    assert "qa_flags" in rf._TOP_LEVEL_REFRESHABLE
    assert not {"synthesis", "anchor", "mechanical"} & rf._TOP_LEVEL_REFRESHABLE


# --- the at-price line: CIQ's four-quarter EBITDA ------------------------------------------------

@pytest.mark.parametrize("t", ["TJX", "PARR"])
def test_the_at_price_line_names_the_four_quarter_figure(t: str) -> None:
    """(+) TJX's and PARR's frozen pages with their frozen companyfacts, through the builder: the
    at-price multiple divides CIQ's four-quarter EBITDA, named, with the ex-lease history's latest
    figure. (−) It no longer prints a bare "LTM EBITDA", the word the annual figure also carries."""
    from tests.test_ev_ebitda_basis import _fixture, _frozen_doc

    d = _frozen_doc(t)
    at = eb.ex_lease_at_price(d.mechanical, _fixture(t))
    assert at is not None
    assert f"÷ {FOUR_Q} ${at.ltm_ebitda:,.0f}M (to {at.ltm_through})" in at.line, at.line
    assert "÷ LTM EBITDA" not in at.line


# --- the renderer's words follow the page's vintage (B's ruling, 2026-11-19) ---------------------

LEASE = "- **Multiple basis — read before the level:**"


def _render(doc: dict[str, Any]) -> str:
    from vinci.dossier.assemble import _read_scenario_card
    from vinci.dossier.render import render_markdown
    from vinci.dossier.schemas import Dossier

    model = Dossier.model_validate(doc)
    return render_markdown(model, card=_read_scenario_card(model.ticker),
                           dossiers_root=ROOT / "data" / "dossiers")


def _lease_pages() -> list[Path]:
    return [p for p in PAGES if any(ln.startswith(LEASE) for ln in
                                    (p.parent / "dossier.md").read_text().splitlines())]


def _old_vintage(path: Path) -> bool:
    from vinci.dossier.render import names_ebitdas_apart
    from vinci.dossier.schemas import Dossier

    return not names_ebitdas_apart(Dossier.model_validate(_doc(path)))


def test_an_old_page_renders_byte_identical_to_its_committed_md() -> None:
    """(+) THE PROOF THE RULING ASKED FOR: every committed page built before W81 that prints the
    lease line renders, under this code, byte for byte as committed, and its lease line keeps the
    word it was built with. The watch pages keep the old wording until rebuilt (B, 2026-11-19), so
    this population holds them at least."""
    old = [p for p in _lease_pages() if _old_vintage(p)]
    assert old, "no committed page predates W81 and prints the lease line; retire this pin"
    worded = 0
    for p in old:
        md = (p.parent / "dossier.md").read_text()
        assert _render(_doc(p)) == md, p.parent.name
        line = next(ln for ln in md.splitlines() if ln.startswith(LEASE))
        assert ANNUAL not in line and FOUR_Q not in line, p.parent.name
        if "% EBITDA margin against" in line or "R1's earnings" in line:
            worded += 1
            assert "reported" in line, p.parent.name
    assert worded, "no old page's lease line names an EBITDA, so the old words went unexercised"


def _stamped(doc: dict[str, Any]) -> dict[str, Any]:
    """``doc`` as a refresh at this code leaves its record: one more `layer_refreshes` entry, at
    the declared extraction version (which holds W81's vintage). Nothing else moves."""
    from vinci.dossier import layer_refresh
    from vinci.dossier.schemas import Dossier

    model = layer_refresh.append(Dossier.model_validate(doc),
                                 layer_refresh.entry("refresh", ["mechanical.valuation"]))
    out: dict[str, Any] = json.loads(model.model_dump_json())
    return out


@pytest.mark.parametrize("path", _lease_pages(), ids=lambda p: p.parent.name)
def test_a_w81_page_names_both_figures_and_only_the_lease_line_moves(path: Path) -> None:
    """(+) Each committed page that prints the lease line, stamped as refreshed at this code: the
    margin is CIQ's annual LTM EBITDA's, and where an ex-lease history is built, its denominator is
    CIQ's four-quarter EBITDA. (−) The lease line no longer says "reported", and nothing else on
    the page moves but that line and the refresh stamp the new entry prints."""
    from vinci.dossier.render import names_ebitdas_apart
    from vinci.dossier.schemas import Dossier

    doc = _stamped(_doc(path))
    assert names_ebitdas_apart(Dossier.model_validate(doc))
    before, after = _render(_stamped_old(path)), _render(doc)
    new = next(ln for ln in after.splitlines() if ln.startswith(LEASE))
    assert not re.search(r"\breported\b", new, re.I), new
    if "% EBITDA margin against" in new:
        assert f"% on {ANNUAL}" in new, new
    if "R1's earnings" in new:
        assert ("R1's earnings are its mid-cycle EBITDA (EBIT + D&A), after rent; on that basis — "
                f"TEV less operating leases over {FOUR_Q} —") in new, new
    moved = [(a, b) for a, b in zip(before.splitlines(), after.splitlines(), strict=True)
             if a != b]
    lease = [m for m in moved if m[1].startswith(LEASE)]
    old = next(ln for ln in before.splitlines() if ln.startswith(LEASE))
    # a line naming no EBITDA (rent unmeasured and no history built: ORKA, TECX) has nothing to move
    named = "% EBITDA margin against" in old or "R1's earnings" in old
    assert lease == ([(old, new)] if named else [])
    # every other moved line is one that prints the vintage itself (the stamp and the refresh log)
    from vinci.dossier.render import W81_VINTAGE
    assert all(W81_VINTAGE in b for a, b in moved if not b.startswith(LEASE)), moved


def _stamped_old(path: Path) -> dict[str, Any]:
    """The same stamp, at a version that predates W81 (W65's): the control, so the comparison
    above differs by the vintage alone."""
    doc = _stamped(_doc(path))
    doc["layer_refreshes"][-1]["extraction_version"] = (
        "2026-11-19.the-ev-ebitda-basis-divides-only-figures-of-one-date")
    return doc


# --- coherence: a W81 page carries no old name on any line the code owns (B, 2026-11-19) ---------
#
# The renderer's words follow the page's vintage, and ANY writer that records a layer refresh
# stamps the current version: `refresh_dossier` with any transform (price values, the EV gap,
# consensus…), `anchor-backfill`, `financials-backfill`, `caveat-reword`, `ciq-reread`,
# `driver-facts-pass`, `transcript-run-cut`. None of them rebuilds the stored basis, at-price or
# reconciliation lines, so a W81-stamped page can carry old stored lines beside new rendered ones:
# one figure, two names. This pin turns that red on the committed pages. The block's `source_ref`
# is exempt by design: it is a citation key the kept prose matches verbatim, and it prints only as
# the synthesis's own copy.

#: The old names, on the lines that name either CIQ EBITDA.
_OLD_WORDS = re.compile(r"reported LTM EBITDA|reported EBITDA|% reported\b|\bits LTM\b"
                        r"|÷ LTM EBITDA|is the reported figure")
#: The rendered lines the code words (md main body), by their leads.
_PRINTED = ("- **What CIQ's EV/EBITDA divides:**", LEASE,
            "- **R1's basis (ex-lease EV/EBITDA) at the page's price:**",
            "> **CIQ's EBITDA against the filings.**")


def incoherent(doc: dict[str, Any], mds: dict[str, str]) -> list[str]:
    """Every code-owned line of ``doc`` (stored) and of ``mds`` (rendered, by name) still carrying
    an old name. Empty for a coherent page."""
    mech = doc["mechanical"]
    v = mech.get("valuation") or {}
    rec = (mech.get("financial_summary") or {}).get("ebitda_reconciliation") or {}
    stored = (("valuation.ev_ebitda_basis.line", (v.get("ev_ebitda_basis") or {}).get("line")),
              ("valuation.ev_ebitda_ex_lease_at_price.line",
               (v.get("ev_ebitda_ex_lease_at_price") or {}).get("line")),
              ("financial_summary.ebitda_reconciliation.line", rec.get("line")))
    out = [where for where, line in stored if line and _OLD_WORDS.search(line)]
    for name, md in mds.items():
        out += [f"{name}: {ln[:70]}" for ln in md.splitlines()
                if ln.startswith(_PRINTED) and _OLD_WORDS.search(ln)]
    return out


def _is_w81(doc: dict[str, Any]) -> bool:
    from vinci.dossier.render import names_ebitdas_apart
    from vinci.dossier.schemas import Dossier

    return names_ebitdas_apart(Dossier.model_validate(doc))


def test_every_w81_committed_page_is_coherent() -> None:
    """(+) THE INVARIANT, on the committed tree: every page built or refreshed at W81 or later
    carries no old name on a code-owned line, stored or rendered (`dossier.md` and its
    `frontend/dossiers` mirror). Pages built before W81 are exempt: they keep the old words
    throughout, which `test_an_old_page_renders_byte_identical_to_its_committed_md` holds."""
    for path in PAGES:
        doc = _doc(path)
        if not _is_w81(doc):
            continue
        t = path.parent.name
        mds = {"dossier.md": (path.parent / "dossier.md").read_text()}
        mirror = ROOT / "frontend" / "dossiers" / f"{t}.md"
        if mirror.exists():
            mds["frontend md"] = mirror.read_text()
        assert not incoherent(doc, mds), (t, incoherent(doc, mds))


def test_a_w81_stamp_over_old_stored_lines_is_caught() -> None:
    """(−) TJX's page as frozen at the cut, stamped as refreshed at this code, its stored lines
    left as built (what any writer but `valuation_bases_transform` would do): the check names all
    three stored lines, and the rendered basis, at-price and reconciliation lines printing them."""
    from vinci.dossier.render import render_markdown
    from vinci.dossier.schemas import Dossier

    doc = _stamped(frozen_doc("TJX"))
    assert _is_w81(doc)
    found = incoherent(doc, {"dossier.md": render_markdown(Dossier.model_validate(doc))})
    assert {"valuation.ev_ebitda_basis.line", "valuation.ev_ebitda_ex_lease_at_price.line",
            "financial_summary.ebitda_reconciliation.line"} <= set(found), found
    printed = [f for f in found if f.startswith("dossier.md:")]
    assert len(printed) == 3 and not any(LEASE in f for f in printed), printed


def test_a_w81_page_with_its_lines_rebuilt_is_coherent() -> None:
    """(+) TJX's frozen page with its three stored lines rebuilt by this code (the basis block, the
    at-price line from its frozen companyfacts, the reconciliation's own sentence), then stamped:
    nothing old remains, stored or rendered."""
    from tests.test_ev_ebitda_basis import _fixture
    from vinci.dossier.render import render_markdown
    from vinci.dossier.schemas import Dossier

    raw = frozen_doc("TJX")
    mech = _mech(raw)
    v = raw["mechanical"]["valuation"]
    v["ev_ebitda_basis"] = json.loads(eb.headline_basis(mech).model_dump_json())  # type: ignore[union-attr]
    v["ev_ebitda_ex_lease_at_price"] = json.loads(
        eb.ex_lease_at_price(mech, _fixture("TJX")).model_dump_json())  # type: ignore[union-attr]
    rec = mech.financial_summary.ebitda_reconciliation  # type: ignore[union-attr]
    assert rec is not None and rec.ciq_ltm is not None
    raw["mechanical"]["financial_summary"]["ebitda_reconciliation"]["line"] = er._line(
        list(rec.quarters), rec.ciq_ltm, rec.filing_ltm, rec.ltm_gap)
    doc = _stamped(raw)
    assert incoherent(doc, {"dossier.md": render_markdown(Dossier.model_validate(doc))}) == []


def test_the_seam_refuses_a_qa_flags_write_that_moves_another_flag(tmp_path: Path) -> None:
    """(−) Review round 1. `refresh_dossier` admits `qa_flags` for one use, and enforces it: a
    top-level step that moves any flag but an LTM-quarters one is refused before anything is
    written, whatever transform sent it. (+) One that moves only an LTM-quarters flag passes the
    seam (`refresh._only_ltm_flags_moved`)."""
    page = tmp_path / "data" / "dossiers" / "IT" / "dossier.json"
    page.parent.mkdir(parents=True)
    page.write_text(json.dumps(frozen_doc("IT")))
    before = page.read_text()
    flags = frozen_doc("IT")["qa_flags"]
    other = next(i for i, f in enumerate(flags) if not f.startswith(lq.FLAG_PREFIX))
    dropped = flags[:other] + flags[other + 1:]
    with pytest.raises(ValueError, match="only an LTM-quarters flag"):
        rf.refresh_dossier(page, top_level=lambda _doc: {"qa_flags": dropped})
    assert page.read_text() == before
    ltm = next(i for i, f in enumerate(flags) if f.startswith(lq.FLAG_PREFIX))
    caused = [f + ". Its cause was not read: …" if i == ltm else f for i, f in enumerate(flags)]
    assert rf._only_ltm_flags_moved(flags, caused)
    assert not rf._only_ltm_flags_moved(flags, dropped)
