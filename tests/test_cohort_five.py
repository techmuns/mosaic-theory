"""(phase 4) The cohort five — per-name declarations, and cost of borrowing.

LAYERING: value pins sit on FROZEN inputs (the instrument rows and the committed FilingSummary
fixture); the living corpus is asserted only for invariants. Which names declare which panels is a
fact about `followed.json`, not a rule, so it is never pinned by count.
"""
from __future__ import annotations

import json
import pathlib
import re

import pytest

from vinci.borrowing import (
    _NOT_FLOATING,
    Borrowing,
    BorrowingUnavailableError,
    borrowing,
)
from vinci.panels import default_registry
from vinci.panels_declare import (
    PanelDeclarationError,
    config_for,
    declared_for,
    read_declarations,
)
from vinci.panels_resolve import resolve_cohort

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIX = ROOT / "tests" / "fixtures" / "commissioning"
ACC = "0001652044-26-000071"

# FROZEN, and SHAPED LIKE THE CORPUS. The third row is AORT's real Secured Term Loan: a FLOATING
# tranche that states its current EFFECTIVE rate (8.410%) beside its benchmark. An earlier fixture
# gave every floating row coupon "NA", so deleting the floating guard changed nothing and the
# mutation passed — the coupon-is-None check was doing the exclusion. Eight corpus tranches have
# this shape, so the fixture must too.
ROWS = [
    {"principal_musd": 1000.0, "coupon": "5.000%", "floating_rate": "NA"},
    {"principal_musd": 3000.0, "coupon": "NA", "floating_rate": "SOFR + 85"},
    {"principal_musd": 1000.0, "coupon": "3.000%", "floating_rate": ""},
    {"principal_musd": 190.0, "coupon": "8.410%", "floating_rate": "SOFR + 4.750%"},
]


def test_a_floating_tranche_stating_its_current_rate_stays_out_of_the_fixed_average() -> None:
    """THE MUTATION GAP, closed. AORT's Secured Term Loan states 8.410% against SOFR + 4.750%.

    Averaging a RESETTABLE rate into the CONTRACTED one conflates two bases — the defect class that
    already cost this repo a table with two EBITDA rows on different bases. It belongs to the all-in
    figure, which is reported separately and says so.
    """
    b = borrowing(ROWS, source_ref="s")
    # Fixed average is unchanged by the 190musd floating tranche at 8.41%...
    assert b.weighted_avg_coupon_pct == pytest.approx(4.0)
    assert b.covered_musd == pytest.approx(2000.0)
    # ...but the all-in rate includes it, over more of the stack, and is HIGHER.
    assert b.all_in_rate_pct is not None
    assert b.all_in_rate_pct == pytest.approx((1000 * 5 + 1000 * 3 + 190 * 8.41) / 2190)
    assert b.all_in_rate_pct > b.weighted_avg_coupon_pct
    assert b.all_in_coverage > b.coverage


def test_the_weighted_average_is_struck_on_principal_not_on_tranche_count() -> None:
    b = borrowing(ROWS, source_ref="s")
    # (1000×5.0 + 1000×3.0) / 2000 = 4.0 — NOT the unweighted mean of 5 and 3, which is also 4.
    # So the pin uses an asymmetric case to tell the two apart.
    uneven = [dict(ROWS[0], principal_musd=3000.0), ROWS[2]]
    assert borrowing(uneven, source_ref="s").weighted_avg_coupon_pct == pytest.approx(4.5)
    assert b.weighted_avg_coupon_pct == pytest.approx(4.0)


def test_a_floating_tranche_is_never_averaged_in_at_zero() -> None:
    """THE FABRICATION THIS GUARD EXISTS FOR.

    A floating tranche's coupon cell is 'NA'. Counting it as 0% would drag the average down in
    proportion to how much floating debt a name carries — a made-up number that looks most
    authoritative exactly where it is most wrong. WERN carries 95% floating principal, so this is
    not a hypothetical shape.
    """
    b = borrowing(ROWS, source_ref="s")
    assert b.weighted_avg_coupon_pct == pytest.approx(4.0), "the 3000musd floating tranche is out"
    assert b.floating_musd == pytest.approx(3190.0)
    assert b.covered_musd == pytest.approx(2000.0)
    assert b.total_musd == pytest.approx(5190.0)
    # And the coverage is REPORTED, so a reader sees what share the average actually covers.
    assert b.coverage == pytest.approx(2000 / 5190)
    assert b.floating_share == pytest.approx(3190 / 5190)


def test_an_all_floating_stack_refuses_rather_than_returning_zero() -> None:
    """A name with debt it cannot price is a refusal, not a 0.0% that reads as free money."""
    with pytest.raises(BorrowingUnavailableError, match="no tranche states both"):
        borrowing([ROWS[1]], source_ref="s")
    with pytest.raises(BorrowingUnavailableError, match="lists no instruments"):
        borrowing([], source_ref="s")


def test_a_tranche_with_no_principal_is_excluded_from_the_denominator_too() -> None:
    """Counting it in the denominator only would understate coverage; counting it in the numerator
    would need a weight it does not have. It is out of both, and coverage stays truthful."""
    rows = [*ROWS, {"principal_musd": None, "coupon": "9.000%", "floating_rate": "NA"}]
    assert borrowing(rows, source_ref="s").total_musd == pytest.approx(5190.0)


def test_the_coupon_cell_is_read_through_the_shared_ciq_helper() -> None:
    """`coupon` is a DISPLAY string ("4.500%"). The house rule allows one shared, tested helper and
    forbids an ad-hoc regex; `clean_num` is that helper and it returns None — never 0 — for an
    unavailable cell, which is what keeps 'NM' out of the average."""
    from vinci.dossier.ciq import clean_num

    assert clean_num("4.500%") == 4.5
    assert clean_num("NA") is None and clean_num("NM") is None
    assert borrowing([{"principal_musd": 10.0, "coupon": "NM", "floating_rate": "NA"},
                      ROWS[0]], source_ref="s").n_covered == 1


def test_lease_liabilities_are_not_borrowings_and_leave_every_figure_alone() -> None:
    """REVIEW FINDING, and the largest one. The CIQ panel lists operating- and finance-lease
    liabilities as tranches typed 'Capital Lease' whose `coupon` is the ASC-842 discount rate the
    filer imputed — not a cost of borrowed money.

    Including them did not shade the figure, it REPLACED it. Measured on the committed corpus: the
    whole of SMPL's 6.00%, WERN's 4.70%, EPAM's 4.80% and VITL's figures were lease rates and
    nothing else, and TECX — which has no borrowings at all — reported 15.47%, the corpus's highest,
    off a $0.4M finance lease and a $0.9M operating lease.
    """
    lease = {"principal_musd": 900.0, "coupon": "17.620%", "floating_rate": "NA",
             "type": "Capital Lease", "description": "Operating Lease Liability"}
    b = borrowing([*ROWS, lease], source_ref="s")
    assert b.weighted_avg_coupon_pct == pytest.approx(4.0), "a lease rate entered the average"
    assert b.total_musd == pytest.approx(5190.0), "lease principal entered the denominator"
    assert b.floating_musd == pytest.approx(3190.0)
    assert b.lease_musd == pytest.approx(900.0), "the fact must survive, on its own field"
    assert b.all_in_rate_pct == pytest.approx(
        borrowing(ROWS, source_ref="s").all_in_rate_pct), "a lease rate entered the all-in basis"


def test_a_stack_whose_only_priced_tranches_are_leases_refuses() -> None:
    """TECX's shape exactly: two lease liabilities and no borrowings. A 15.47% cost of borrowing for
    a name that has not borrowed is worse than a blank tile, because it is believed."""
    with pytest.raises(BorrowingUnavailableError, match="lease liabilities excluded"):
        borrowing([{"principal_musd": 0.4, "coupon": "10.640%", "floating_rate": "NA",
                    "type": "Capital Lease"},
                   {"principal_musd": 0.9, "coupon": "17.620%", "floating_rate": "NA",
                    "type": "Capital Lease"}], source_ref="s")


def test_a_tranche_with_no_floating_flag_at_all_leans_floating_as_documented() -> None:
    """REVIEW FINDING. `str(row.get("floating_rate") or "")` collapsed an ABSENT/NULL field onto
    CIQ's explicit empty "not floating" cell, so a failed extraction read as FIXED and put a
    possibly-resettable coupon into the contracted average — the module's stated default, inverted.
    """
    with pytest.raises(BorrowingUnavailableError):
        borrowing([{"principal_musd": 500.0, "coupon": "4.500%"}], source_ref="s")
    with pytest.raises(BorrowingUnavailableError):
        borrowing([{"principal_musd": 500.0, "coupon": "4.500%", "floating_rate": None}],
                  source_ref="s")
    # ...while CIQ's own empty cell still means fixed, which is what ROWS[2] pins.
    assert borrowing([ROWS[2]], source_ref="s").covered_musd == pytest.approx(1000.0)


def test_passing_the_fact_envelope_instead_of_the_list_is_loud_not_a_refusal() -> None:
    """REVIEW FINDING. The dossier holds the list inside `{value, source_ref, status}`, so the
    envelope is the shape a caller most easily passes by mistake — and the refusal branch then said
    "no debt to price" about a name with a nineteen-tranche stack. A wiring bug must not be able to
    render as an answer."""
    with pytest.raises(TypeError, match="instrument LIST"):
        borrowing({"value": ROWS, "source_ref": "x", "status": "present"}, source_ref="s")


def test_an_undeclared_panel_is_silent_and_a_declared_one_is_not() -> None:
    """Substance from the declaration. LLY and V publish no property-named report, so neither
    DECLARES commissioning — and a panel a name does not run renders nothing at all."""
    reg = default_registry()
    decl = read_declarations(root=ROOT, registry=reg)
    states = {d.key: d.state for d in resolve_cohort(
        "LLY", dossier=None, declarations=decl, registry=reg, note_probe=None)}
    assert states["commissioning"] == "not_in_set"
    assert states["segment_economics"] == "refused", "declared, but no probe to verify the note"


def test_without_a_filing_probe_a_note_requirement_refuses_rather_than_assuming() -> None:
    """A declaration is an intention, not evidence. Assuming the note exists because a human wrote
    its name down is how one filer's note gets read as another's."""
    reg = default_registry()
    decl = read_declarations(root=ROOT, registry=reg)
    got = {d.key: d for d in resolve_cohort(
        "GOOGL", dossier=None, declarations=decl, registry=reg, note_probe=None)}
    assert got["commissioning"].state == "refused"
    assert "no filing probe" in got["commissioning"].reason


def test_the_declared_note_name_resolves_what_the_repo_wide_pattern_cannot() -> None:
    """THE PHASE-4 PAYOFF, pinned on the committed FilingSummary.

    GOOGL's 10-Q carries TWO economics-matching segment (Details) reports, so the repo-wide pattern
    rightly refuses as ambiguous — choosing would file geography or revenue-only figures as segment
    economics. The name's own declaration names the report and resolves it. Measured live on five
    names (GOOGL, NFLX, LLY, V, UBER): all five went REFUSED → READY.
    """
    from vinci.edgar.segments import SegmentReportUnavailableError, _pick_report

    summary = (FIX / f"GOOGL-{ACC}-FilingSummary.xml").read_text()
    with pytest.raises(SegmentReportUnavailableError, match="more than one segment report"):
        _pick_report(summary)
    decl = read_declarations(root=ROOT, registry=default_registry())
    note = config_for("GOOGL", "segment_economics", decl)["note_name"]
    fname, short = _pick_report(
        summary, topic=re.compile(re.escape(note), re.I), refine=re.compile(r".", re.S),
        what="GOOGL segment note", absent_means="this filer renames reports between filings")
    assert note.lower() in short.lower()
    assert fname.endswith(".htm")


def test_a_declaration_naming_an_unregistered_panel_is_loud_at_read(
        tmp_path: pathlib.Path) -> None:
    """Validated at READ, not at render — a typo'd key would otherwise surface as a missing tile on
    a page nobody was watching.

    WRITES TO `tmp_path`, not into `tests/fixtures/`. The earlier cut built a real directory inside
    the repo and removed it in a `finally`, so an interrupt left an untracked, un-ignored
    `followed.json` in the working tree.
    """
    reg = default_registry()
    bad = {"X": {"followed_since": "2026-01-01", "sleeve": "quality",
                 "panels": {"no_such_panel": {}}}}
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data" / "followed.json").write_text(json.dumps(bad))
    with pytest.raises(PanelDeclarationError, match="not registered"):
        read_declarations(root=tmp_path, registry=reg)
    bad["X"]["panels"] = {"cost_of_borrowing": {"nope": "x"}}
    (tmp_path / "data" / "followed.json").write_text(json.dumps(bad))
    with pytest.raises(PanelDeclarationError, match="does not read"):
        read_declarations(root=tmp_path, registry=reg)


def test_an_absent_follow_list_raises_rather_than_declaring_nothing(
        tmp_path: pathlib.Path) -> None:
    """REVIEW FINDING. `{}` for a missing file is indistinguishable downstream from "nobody
    declared anything" — every cohort panel `not_in_set`, a grid of silent tiles — and the first of
    the two is a wiring bug (wrong root, wrong cwd). Absent-vs-broken at this module's own edge."""
    with pytest.raises(PanelDeclarationError, match="no follow list at"):
        read_declarations(root=tmp_path, registry=default_registry())


def test_a_lowercase_ticker_key_declares_the_panel_rather_than_silently_nothing(
        tmp_path: pathlib.Path) -> None:
    """REVIEW FINDING. `vinci/followed.py` uppercases at this edge and this reader did not, so
    `{"googl": {...}}` declared nothing: `declared_for("GOOGL", …)` missed it and the panel rendered
    `not_in_set` — the blank tile that reads as "this name has no such question"."""
    reg = default_registry()
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data" / "followed.json").write_text(json.dumps(
        {"googl": {"followed_since": "2026-01-01", "sleeve": "quality",
                   "panels": {"cost_of_borrowing": {}}}}))
    decl = read_declarations(root=tmp_path, registry=reg)
    assert declared_for("GOOGL", decl) == frozenset({"cost_of_borrowing"})
    assert declared_for("googl", decl) == frozenset({"cost_of_borrowing"})


def test_a_case_colliding_pair_of_tickers_refuses_instead_of_dropping_one(
        tmp_path: pathlib.Path) -> None:
    reg = default_registry()
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    entry = {"followed_since": "2026-01-01", "sleeve": "quality",
             "panels": {"cost_of_borrowing": {}}}
    (tmp_path / "data" / "followed.json").write_text(json.dumps({"V": entry, "v": entry}))
    with pytest.raises(PanelDeclarationError, match="more than once"):
        read_declarations(root=tmp_path, registry=reg)


def test_an_unconfigured_note_panel_is_never_probed_with_the_default_note_name() -> None:
    """REVIEW FINDING. `decide` refuses an unfilled config BEFORE it looks at `have`, so probing
    first fetched a FilingSummary to ask about the DEFAULT note name — Alphabet's — against another
    filer's accounts, which is the one query this module's docstring says must never be sent. The
    answer was then discarded."""
    reg = default_registry()
    asked: list[str] = []

    def probe(detail: str) -> tuple[bool, str]:
        asked.append(detail)
        return True, ""

    # declared, note_name deliberately unset
    decl: dict[str, dict[str, dict[str, str]]] = {"ZZZZ": {"commissioning": {}}}
    got = {d.key: d for d in resolve_cohort(
        "ZZZZ", dossier=None, declarations=decl, registry=reg, note_probe=probe)}
    assert got["commissioning"].state == "refused"
    assert "config 'note_name' is not set" in got["commissioning"].reason
    # ...and `segment_economics`, which ZZZZ does not declare at all, is not probed either: an
    # undeclared panel renders nothing, so fetching a filing to decide its form is a round trip for
    # a tile that does not exist.
    assert got["segment_economics"].state == "not_in_set"
    assert asked == [], f"probed the default note name anyway: {asked}"


def test_every_declaration_in_the_live_file_validates() -> None:
    """Invariant over the living file — not a count, which would be a corpus-shaped assertion."""
    reg = default_registry()
    decl = read_declarations(root=ROOT, registry=reg)
    assert decl, "no declarations at all — this check would prove nothing"
    for ticker, panels in decl.items():
        for key in panels:
            assert key in reg, f"{ticker} declares unregistered {key}"
        assert declared_for(ticker, decl) == frozenset(panels)


def test_cost_of_borrowing_computes_for_every_dossier_that_lists_instruments() -> None:
    """Corpus invariant: where the capital panel lists priced tranches, the average is strikeable.
    Phrasing- and count-independent — it asserts the relationship, not today's 18."""
    seen = 0
    for d in sorted(p for p in (ROOT / "data" / "dossiers").iterdir() if p.is_dir()):
        cs = (json.loads((d / "dossier.json").read_text())["mechanical"]
              .get("capital_structure") or {})
        ins = (cs.get("instruments") or {}).get("value")
        if not isinstance(ins, list) or not ins:
            continue
        # `_NOT_FLOATING` IS IMPORTED, NOT RETYPED. A copy of the production set here would go stale
        # the moment the set changed and this invariant would then assert the old classification
        # while reporting green.
        priced = [r for r in ins if isinstance(r, dict) and r.get("principal_musd")
                  and str(r.get("type") or "").strip().lower() != "capital lease"
                  and str(r.get("floating_rate") or "").strip().lower() in _NOT_FLOATING]
        try:
            b = borrowing(ins, source_ref="corpus")
        except BorrowingUnavailableError:
            assert not any(_coupon_ok(r) for r in priced), f"{d.name}: refused with priced tranches"
            continue
        seen += 1
        assert isinstance(b, Borrowing)
        assert 0.0 < b.weighted_avg_coupon_pct < 40.0, f"{d.name}: {b.weighted_avg_coupon_pct}"
        assert 0.0 < b.coverage <= 1.0
    assert seen, "no name produced a cost of borrowing — this check proved nothing"


def _coupon_ok(row: dict[str, object]) -> bool:
    from vinci.dossier.ciq import clean_num

    return clean_num(row.get("coupon")) is not None
