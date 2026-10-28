"""Four names located no covenant exhibit at all, and it was one regex written to one convention.

THE DEFECT. `ex-?10\\d` requires a DIGIT immediately after "10", so it matches only the compacted
filename form (`ex102` = exhibit 10.2). Measured against the real filenames in the fleet's own
filings, that is the MINORITY convention:

    ex102_q425.htm                    NFLX   compact       matched
    vitl-ex10_10.htm                  VITL   underscore    MISSED
    aort-20251231xexx1032.htm         AORT   double-x      MISSED
    fubo-20241231exx1026.htm          FUBO   double-x      MISSED
    f8k032018ex10-1_simplygood.htm    SMPL   hyphen        MISSED
    a19-22146_1ex10d1.htm             SMPL   d-separator   MISSED
    tm2136016d1_ex10-1.htm            SMPL   hyphen        MISSED

NFLX was the ONLY name it matched, and only by its filing agent's naming style.

WHY THE FAILURE WAS TOTAL RATHER THAN PARTIAL. The fragment appears in BOTH pointer passes — the
10-K exhibit index filter and the efts hit filter (`_AGREEMENT_EXHIBIT_RE`) — so one flaw closed
both routes on the same names. That is why FUBO/SMPL/UBER/VITL located NOTHING rather than fewer.

WHAT IT WAS NOT, each checked before landing on the regex: the efts search works (UBER 17 hits,
SMPL 46, AORT 16); the instruments do qualify for a query (all four generate one); and the exhibits
exist — SMPL's 8-K hits carry `f8k032018ex10-1_simplygood.htm`, a real credit agreement, rejected
by the filter. Nothing about company type; purely filing-agent filename convention.

MEASURED AFTER THE FIX, live against EDGAR for all 14 names: FUBO 0→6, SMPL 0→3, UBER 0→8,
VITL 0→3, and seven already-working names gained pointers too (AORT 9→13, CNXC 5→9, MVST 6→9).
"""
from __future__ import annotations

import re

from vinci.dossier.mechanical import _AGREEMENT_EXHIBIT_RE, _EX10_RE, _covenant_query

#: (source, filename, should_match) — every one taken from a real filing in this fleet.
REAL_FILENAMES: tuple[tuple[str, str, bool], ...] = (
    ("NFLX 10-K", "ex102_q425.htm", True),                    # compact — the only one that matched
    ("VITL 10-K", "vitl-ex10_10.htm", True),                  # underscore separator
    ("AORT 10-K", "aort-20251231xexx1032.htm", True),         # double-x prefix
    ("FUBO 10-K", "fubo-20241231exx1026.htm", True),          # double-x prefix
    ("SMPL 8-K", "f8k032018ex10-1_simplygood.htm", True),     # hyphen separator
    ("SMPL 8-K", "a19-22146_1ex10d1.htm", True),              # 'd' as the decimal separator
    ("SMPL 8-K", "tm2136016d1_ex10-1.htm", True),             # hyphen separator
    # …and the two that must NOT match: exhibit 19.1 is a clawback policy, 21.1 a subsidiary list.
    # Widening the pattern until everything matches would be the opposite defect.
    ("UBER 10-K", "uber12312025exhibit191.htm", False),
    ("SMPL 10-K", "exhibit211-10k2025.htm", False),
)


def test_every_real_filename_convention_in_the_fleet_is_matched() -> None:
    """THE CASE THAT STARTED THIS, as a table of real filenames rather than invented ones. A
    convention this misses is a name whose covenant exhibits cannot be located at all."""
    wrong = [f"{src} {name} → {bool(re.search(_EX10_RE, name, re.I))}, expected {want}"
             for src, name, want in REAL_FILENAMES
             if bool(re.search(_EX10_RE, name, re.I)) is not want]
    assert not wrong, "\n  ".join(["exhibit-filename matching regressed:", *wrong])


def test_ten_stays_pinned_so_the_pattern_does_not_match_any_exhibit() -> None:
    """THE NEGATIVE HALF, and it is what stops this becoming a worse bug. Exhibit 10.x is the
    MATERIAL-CONTRACT class; 19.1 (clawback policy) and 21.1 (subsidiaries) are not contracts, and
    a pattern loose enough to take them would fill the pointer table with noise."""
    for junk in ("uber12312025exhibit191.htm", "exhibit211-10k2025.htm",
                 "aort-20251231xexx991.htm", "ex321_cert.htm"):
        assert not re.search(_EX10_RE, junk, re.I), junk


def test_both_passes_share_one_pattern() -> None:
    """THE REASON THE FAILURE WAS TOTAL — and the shape of the next regression if the two ever
    drift. The 10-K exhibit filter and the efts hit filter must not be able to disagree about what
    a material-contract exhibit looks like: fixing one and missing the other would leave exactly
    the half-working state that made this hard to see."""
    import inspect

    import vinci.dossier.mechanical as mech
    src = inspect.getsource(mech._covenant_pointers)
    assert "re.search(_EX10_RE, n, re.I)" in src, (
        "the 10-K exhibit pass no longer uses the shared pattern — it can drift from the efts pass")
    for _s, name, want in REAL_FILENAMES:
        if want:
            assert _AGREEMENT_EXHIBIT_RE.search(name), (
                f"{name} matches the shared pattern but not the efts filter that embeds it")


# ─── the query class ──────────────────────────────────────────────────────────────────────────

def test_a_note_queries_its_indenture_not_a_loan_agreement() -> None:
    """A NOTE IS AN INDENTURE INSTRUMENT, like a bond. Without a branch for it, "2025 Convertible
    Notes" fell through to the "Loan Agreement" default — the wrong contract class, and the query
    UBER's and FUBO's convertible notes were actually searched under.

    Secondary to the regex, and worth saying so: querying "Indenture" for UBER still returned zero
    exhibit-bearing hits before the regex fix, because the exhibit filter was the binding
    constraint. This one matters for what the search ASKS; that one decided what it could accept."""
    assert _covenant_query("2025 Convertible Notes") == "Indenture"
    assert _covenant_query("3.000% Senior Notes") == "Indenture"
    assert _covenant_query("Convertible Bond") == "Indenture"


def test_the_other_classes_are_unchanged() -> None:
    """The note branch must not capture instruments that are genuinely loans or credit lines — a
    'Term Loan Note' is executed under a loan agreement, not an indenture."""
    assert _covenant_query("Credit Agreement With Barclays Bank PLC") == "Credit Agreement"
    assert _covenant_query("Term Loan") == "Loan Agreement"
    assert _covenant_query("Secured Note Purchase Loan") == "Loan Agreement"
    assert _covenant_query("Facility B") == "Facility Agreement"


# ─── the two failures that must not read alike ────────────────────────────────────────────────

def test_the_digest_distinguishes_nothing_located_from_extraction_failed() -> None:
    """FOUR NAMES SHIPPED A PAGE ASSERTING BOTH. `covenant_pointers` said "no CIK-scoped agreement
    exhibit located" while `covenant_terms`, two fields away, said "extraction failed: no covenant
    terms extracted from LOCATED exhibits". They point a reader at opposite remedies — the LLM
    phase versus the pointer search — and only one of them was true."""
    from vinci.dossier.covenant_extract import covenant_digest

    located = covenant_digest([], None, fail_reason="no covenant terms extracted from located "
                                                    "exhibits")
    nothing = covenant_digest([], None, fail_reason="no agreement exhibit was located to extract "
                                                    "from — the gap is in the pointer search, not "
                                                    "in extraction")
    assert "located exhibits" in located
    assert "pointer search" in nothing and "located exhibits" not in nothing
    assert located != nothing, "the two failure states render identically again"


def test_the_reason_is_chosen_from_whether_a_pointer_exists() -> None:
    """The wiring, pinned at the seat: the choice must key on whether any pointer was LOCATED, not
    on the extraction result alone — which is what produced the contradiction."""
    import inspect

    import vinci.dossier.assemble as asm
    src = inspect.getsource(asm.assemble_one)
    assert "located_any = ptrs is not None and bool(ptrs.value)" in src, (
        "the digest no longer distinguishes 'nothing located' from 'extraction failed'")


# ─── as-of bounding ───────────────────────────────────────────────────────────────────────────

def test_pointer_discovery_cannot_reach_past_the_records_own_as_of() -> None:
    """REVIEW FINDING (P1, #426) — the #416 lookahead class, in the pointer search this time.

    `recent_filings` returns TODAY's submissions index and efts returns today's hits, so an
    unbounded search attaches whatever exists when the code RUNS. Re-assembling a historical
    dossier would hang an agreement on it that its own reference date could not have seen, and the
    artifact stops being reproducible. THE WIDENED MATCHER MADE THIS REACHABLE: the four names that
    previously located nothing at all now locate exhibits, so a latent hazard became a live one.

    Both passes are bounded — the 10-K index and the efts hits — and this drives them together."""
    from datetime import date as _d

    from vinci.dossier.mechanical import _covenant_pointers
    from vinci.dossier.schemas import CapitalInstrument

    ref = _d(2026, 7, 6)

    class _F:
        # `form` as the real `Filing` carries it: the step names the annual report it read
        def __init__(self, d: _d, acc: str) -> None:
            self.filing_date, self.accession, self.form = d, acc, "10-K"

    class _Hit:
        def __init__(self, d: _d, acc: str) -> None:
            self.file_date, self.accession, self.cik = d, acc, "0000000001"

    class _Edgar:
        def recent_filings(self, cik: str, *, forms: tuple[str, ...] = ()) -> list[_F]:
            # newest FIRST, as the real index returns — and the newest postdates the as-of
            return [_F(_d(2026, 9, 1), "AFTER-THE-ASOF"), _F(_d(2026, 2, 1), "BEFORE-0001")]

        def fulltext_search(self, phrase: str, *, forms: str = "", ciks: str = "") -> list[_Hit]:
            return [_Hit(_d(2026, 9, 9), "EFTS-AFTER"), _Hit(_d(2026, 1, 5), "EFTS-BEFORE")]

    seen_accessions: list[str] = []

    def _names(http: object, cik: str, acc: str) -> list[str]:
        seen_accessions.append(acc)
        return ["ex10-1_agreement.htm"]        # always exhibit-bearing, so only the DATE can gate

    import vinci.dossier.mechanical as mech
    orig = mech._exhibit_names
    mech._exhibit_names = _names                                          # type: ignore[assignment]
    try:
        # A REAL committed instrument (SMPL's revolver), not a hand-rolled one — every field the
        # model requires, so the fixture cannot dictate a shape the production type does not have.
        inst = CapitalInstrument.model_validate({
            "description": "Credit Agreement With Barclays Bank PLC - Revolving Credit Facility",
            "type": "Revolving Credit", "principal_musd": None, "coupon": "4.200%",
            "floating_rate": "Benchmark", "maturity_date": "2029-12-16", "seniority": "Senior",
            "secured": True, "convertible": False, "currency": "USD"})
        out = _covenant_pointers(_Edgar(), None, "0000000001", [inst], ref)
    finally:
        mech._exhibit_names = orig                                        # type: ignore[assignment]

    accs = [r.accession for r in (out.value or [])]
    assert "AFTER-THE-ASOF" not in accs, f"a 10-K filed after the as-of was attached: {accs}"
    assert "EFTS-AFTER" not in accs, f"an 8-K filed after the as-of was attached: {accs}"
    assert "BEFORE-0001" in accs or "EFTS-BEFORE" in accs, (
        f"the bound rejected everything, including filings the as-of could see: {accs}")


# ─── three states, not two ────────────────────────────────────────────────────────────────────

def test_a_search_that_could_not_run_is_not_a_search_that_found_nothing() -> None:
    """REVIEW FINDING (P2, #426), and it was introduced WHILE fixing a two-states bug.

    `_covenant_pointers` returns UNKNOWN with a null value for BOTH "the search ran and located
    nothing" AND "the search could not run" (no CIK, or EDGAR unreachable). Keying the digest on
    `bool(ptrs.value)` therefore reported a COMPLETED search that never happened — the reassuring
    answer being the dangerous one. The two are told apart by the search's own note constant, so
    they cannot drift into a shared literal."""
    from vinci.dossier.mechanical import COVENANT_SEARCH_FOUND_NOTHING, _covenant_pointers

    no_cik = _covenant_pointers(None, None, "", [], __import__("datetime").date(2026, 7, 6))
    assert no_cik.value is None
    assert no_cik.note != COVENANT_SEARCH_FOUND_NOTHING, (
        "a lookup that never ran carries the same note as one that completed — the digest cannot "
        "tell them apart again")
    assert "no CIK" in (no_cik.note or "")


def test_the_digest_reports_all_three_states_distinctly() -> None:
    """located / searched-and-empty / could-not-search each point at a different remedy: the LLM
    phase, the pointer search, and the data pipeline. Rendering any two alike sends a reader after
    the wrong one."""
    import inspect

    import vinci.dossier.assemble as asm
    src = inspect.getsource(asm.assemble_one)
    assert "searched = (ptrs is not None" in src, "the third state was collapsed away again"
    assert "COVENANT_SEARCH_FOUND_NOTHING" in src, (
        "the digest matches a literal rather than the search's own constant — they will drift")
    assert "could not run" in src
