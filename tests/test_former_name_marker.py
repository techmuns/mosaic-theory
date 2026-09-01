"""The former-registrant-name marker — the reverse-merger vintage caveat.

A CIK's multi-year financial blocks can silently span a DIFFERENT underlying business filed under
the same number: FUBO's dossier history rides a CIK that was FaceBank Group (and three shells
before that), TECX's XBRL back to 2018 is AvroBio's, ORKA's is ARCA biopharma's, and MVST's is
Tuscan Holdings — a SPAC. The marker states the filed fact (name + span, source-bound to the
submissions ``formerNames`` array) and directs verification; it never asserts a mechanism, because
the SAME array also records pure restyles (casing, word order, EDGAR's filer suffix, diacritics)
which are NOT predecessors and must never flag.

Every fixture below is the REAL ``formerNames`` payload fetched live from the submissions endpoint
on 2026-09-01 — never a hand-rolled shape (CLAUDE.md fixture rule). The check was swept over all
17 committed dossier CIKs before these pins were written (corpus before synthetic).

REVIEW FIXES PINNED HERE (#558). Six defects the first cut shipped, each with a regression pin
named below: lookahead on backdated assemblies, a stale current-name baseline, a lookback shorter
than the deepest window the page reads, "group" stripped as a style token, EDGAR's closed ``/DE/``
filer suffix unmatched, and a blanket catch that reported a parse break as a fetch failure.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from vinci.dossier.flags import partition
from vinci.dossier.mechanical import (
    _FORMER_NAME_LOOKBACK_DAYS,
    _former_name_flags,
    _registrant_key,
)
from vinci.dossier.midcycle import MIN_YEARS as MIDCYCLE_MIN_YEARS
from vinci.edgar.submissions import (
    FormerName,
    parse_former_names,
    parse_registrant_history,
)
from vinci.netcache import HttpError

TODAY = date(2026, 9, 1)
BACKDATED = date(2022, 6, 1)


def _fn(name: str, to: str, frm: str | None = None) -> FormerName:
    return FormerName(name=name, from_date=date.fromisoformat(frm) if frm else None,
                      to_date=date.fromisoformat(to))


class _StubEdgar:
    """Delivery stub only — the ROWS it serves are the real fetched payloads."""

    def __init__(self, current: str, rows: list[FormerName] | Exception) -> None:
        self._current, self._rows = current, rows

    def registrant_history(self, cik: int | str) -> Any:
        if isinstance(self._rows, Exception):
            raise self._rows
        return parse_registrant_history({
            "name": self._current,
            "formerNames": [
                {"name": r.name, "to": r.to_date.isoformat(),
                 "from": r.from_date.isoformat() if r.from_date else None} for r in self._rows],
        })


# --- the real payloads (fetched 2026-09-01) ------------------------------------------------------
TECX = [_fn("AvroBio, Inc.", "2024-06-18", "2018-02-02"),
        _fn("AVROBIO, Inc.", "2024-06-18", "2018-02-02")]
ORKA = [_fn("ARCA biopharma, Inc.", "2024-08-30", "2009-01-28"),
        _fn("NUVELO INC", "2009-01-27", "2003-02-04"),
        _fn("HYSEQ INC", "2003-01-28", "1997-07-17")]
AAPL = [_fn("APPLE INC", "2019-08-05", "2007-01-10"),
        _fn("APPLE COMPUTER INC", "2007-01-04", "1994-01-26"),
        _fn("APPLE COMPUTER INC/ FA", "1997-07-28", "1997-07-28")]
LLY = [_fn("LILLY ELI & CO", "2019-10-25"), _fn("LILLY ELI & CO ET AL", "1994-10-14")]
AORT = [_fn("CRYOLIFE INC", "2022-01-06", "1996-06-10")]
MVST = [_fn("Tuscan Holdings Corp.", "2021-07-21", "2018-12-07")]
FUBO = [_fn("fuboTV Inc. /FL", "2025-10-30"),
        _fn("FaceBank Group, Inc.", "2020-08-12"),
        _fn("Pulse Evolution Group, Inc.", "2019-09-25"),
        _fn("Recall Studios, Inc.", "2019-02-07"),
        _fn("CAROLCO PICTURES, INC.", "2017-11-21"),
        _fn("Brick Top Productions, Inc.", "2014-12-31"),
        _fn("York Entertainment, Inc.", "2010-02-25")]


def _flags(current: str, rows: list[FormerName] | Exception, ref: date) -> list[str]:
    return _former_name_flags(_StubEdgar(current, rows), "0000000000", ref)  # type: ignore[arg-type]


def _names(flags: list[str]) -> list[str]:
    return [f.split('"')[1] for f in flags]


# --- true predecessors flag, once each, with their span ------------------------------------------
def test_tecx_flags_avrobio_exactly_once_with_its_span() -> None:
    """The two casing variants of AvroBio are ONE former registrant — a per-row flag would print
    the same predecessor twice and read as two different businesses."""
    out = _flags("Tectonic Therapeutic, Inc.", TECX, TODAY)
    assert len(out) == 1, out
    assert "AvroBio" in out[0] and "2024-06-18" in out[0] and "2018-02-02" in out[0], out[0]


def test_orka_flags_only_the_in_window_predecessor() -> None:
    """ARCA (to 2024) marks the page; Nuvelo (2009) and Hyseq (2003) predate every rendered
    vintage even at an 11-year lookback."""
    out = _flags("Oruka Therapeutics, Inc.", ORKA, TODAY)
    assert _names(out) == ["ARCA biopharma, Inc."], out


def test_mvst_the_committed_corpus_hit_flags_its_spac_shell() -> None:
    """The live corpus case: MVST's committed dossier rides Tuscan Holdings' CIK."""
    assert _names(_flags("Microvast Holdings, Inc.", MVST, TODAY)) == ["Tuscan Holdings Corp."]


# --- AS-OF DISCIPLINE: no lookahead (review fix, the #416/#426 class) ----------------------------
def test_a_rename_after_the_reference_date_is_not_announced() -> None:
    """THE CONFIRMED BUG. Assembling AORT at a 2021 reference used to print 'this CIK filed as
    CRYOLIFE INC (… → 2022-01-06)' — telling a reader about a rename in their own future, on a
    page whose every other number is bounded by the reference date. Backdated assembly is a
    supported mode; the PR's own verification ran one."""
    assert _flags("ARTIVION, INC.", AORT, date(2021, 6, 1)) == []
    assert _flags("ARTIVION, INC.", AORT, date(2022, 1, 5)) == []
    assert _names(_flags("ARTIVION, INC.", AORT, TODAY)) == ["CRYOLIFE INC"]


def test_on_the_changeover_day_the_old_name_is_still_the_current_one() -> None:
    """The boundary, stated rather than left to chance: on the span's own end date the registrant
    was still filing under it, so it is the name IN FORCE, not a predecessor."""
    assert _flags("ARTIVION, INC.", AORT, date(2022, 1, 6)) == []


def test_the_baseline_is_the_name_in_force_at_the_reference_date() -> None:
    """A backdated assembly compares against the name that WAS current then, not today's. With the
    reference inside CryoLife's span, CryoLife is the baseline — so it cannot be its own
    predecessor, and today's name is irrelevant to that page."""
    rows = [_fn("CRYOLIFE INC", "2022-01-06", "1996-06-10"),
            _fn("OLD SHELL CORP", "1996-06-09", "1990-01-01")]
    out = _flags("ARTIVION, INC.", rows, date(2000, 1, 1))
    assert _names(out) == ["OLD SHELL CORP"], out


def test_the_current_name_comes_from_the_payload_not_the_callers_record() -> None:
    """`identity.name` is resolver output persisted inside stored records, so a rename AFTER the
    record was screened would leave it holding the OLD name — which then matched the former row
    and silently suppressed the marker for the freshest, most consequential case. The marker now
    takes no name from the caller at all; this pins that the payload's own name is authoritative."""
    out = _flags("Tectonic Therapeutic, Inc.", TECX, TODAY)      # payload name is current
    assert len(out) == 1
    stale = _StubEdgar("AvroBio, Inc.", TECX)                    # a caller could only have lied
    assert _former_name_flags(stale, "x", TODAY) == []           # type: ignore[arg-type]


# --- restyles are NOT predecessors (each class observed live) ------------------------------------
def test_casing_and_open_filer_suffix_restyles_never_flag() -> None:
    assert _flags("Apple Inc.", AAPL, TODAY) == []


def test_word_order_restyle_never_flags() -> None:
    """LLY filed as 'LILLY ELI & CO' until 2019 — the same registrant, words reordered."""
    assert _flags("ELI LILLY & Co", LLY, TODAY) == []
    assert _flags("ELI LILLY & Co", LLY, BACKDATED) == []


def test_the_closed_slash_filer_suffix_collapses_too() -> None:
    """REVIEW FIX. EDGAR's conformed form usually CLOSES the suffix — this repo's own
    `data/graph_coverage.json` carries "PITNEY BOWES INC /DE/". The first regex required the name
    to end in letters, so the closed form produced a false predecessor; the FUBO "/FL" pin passed
    only because that sampled row happened to lack the trailing slash."""
    assert _registrant_key("PITNEY BOWES INC /DE/") == _registrant_key("Pitney Bowes Inc")
    assert _flags("Pitney Bowes Inc", [_fn("PITNEY BOWES INC /DE/", "2024-01-01")], TODAY) == []


def test_diacritics_collapse() -> None:
    """REVIEW FIX. ASCII-only tokenising shredded accented names into fragments, so any filer with
    a diacritic in an older conformed name got a false predecessor. Invisible to a US-only sweep —
    and NU, an onboarding candidate, is exactly the foreign-filer class."""
    assert _registrant_key("Société Générale de Foo") == _registrant_key("SOCIETE GENERALE DE FOO")


# --- "group" is a shell word, not a style word (review fix) --------------------------------------
def test_group_is_not_stripped_because_shells_are_named_that_way() -> None:
    """REVIEW FIX. "group" was briefly a style token on a justification traced to a MISIDENTIFIED
    CIK (Cowen Group, probed in place of Artivion). Stripping it silently erases the shell →
    successor case whenever the shell shares a base word — the exact miss "holdings" was excluded
    to avoid. Removing it changed no live corpus result."""
    assert _registrant_key("Ajax Capital Group, Inc.") != _registrant_key("Ajax Capital, Inc.")
    assert _registrant_key("Tuscan Holdings Corp.") != _registrant_key("Microvast Holdings, Inc.")
    out = _flags("Ajax Capital, Inc.", [_fn("Ajax Capital Group, Inc.", "2024-01-01")], TODAY)
    assert _names(out) == ["Ajax Capital Group, Inc."], out


# --- spans are filed facts, never merged ---------------------------------------------------------
def test_a_repeated_name_never_prints_a_span_it_did_not_hold() -> None:
    """REVIEW FIX. Merging duplicate keys as min(from) → max(to) asserted one continuous span
    across a middle period the registrant filed under a DIFFERENT name — a false filed-fact claim,
    and being source-bound to a literal span is the caveat's whole value."""
    rows = [_fn("Foo Corp", "2013-01-01", "2010-01-01"),
            _fn("Bar Inc", "2019-01-01", "2013-01-01"),
            _fn("Foo Corp.", "2021-01-01", "2019-01-01")]
    out = _flags("Baz Inc", rows, TODAY)
    assert len(out) == 2, out
    foo = next(f for f in out if "Foo" in f)
    assert "2019-01-01" in foo and "2010-01-01" not in foo, foo


# --- the lookback is bound to the deepest window the page reads ----------------------------------
def test_the_lookback_is_derived_from_the_deepest_rendered_window() -> None:
    """REVIEW FIX. The first cut used ~6y ("the 5-fiscal-year trend"), but `midcycle.MIN_YEARS`
    reads TEN fiscal years and feeds the R1 recipe's valuation — so a rename 7-9 years back went
    unmarked while the mid-cycle band averaged across two businesses, the exact error this marker
    exists to catch. Imported, not copied, so the two cannot drift."""
    assert _FORMER_NAME_LOOKBACK_DAYS == (MIDCYCLE_MIN_YEARS + 1) * 365


def test_a_rename_older_than_the_window_ages_out() -> None:
    assert _flags("FuboTV Inc.", [_fn("Ancient Shell Corp", "2009-01-01")], TODAY) == []


def test_fubos_shell_chain_is_reported_in_full_oldest_first() -> None:
    """FUBO's CIK genuinely filed under four other registrants inside the window the mid-cycle
    band reads — four lines is the honest record. The "/FL" reincorporation row is NOT among
    them."""
    out = _flags("FuboTV Inc.", FUBO, TODAY)
    assert _names(out) == ["CAROLCO PICTURES, INC.", "Recall Studios, Inc.",
                           "Pulse Evolution Group, Inc.", "FaceBank Group, Inc."], out
    assert not any("fuboTV" in f for f in out)
    assert not any("York Entertainment" in f for f in out)   # 2010 — outside the window


def test_no_former_names_means_no_flag() -> None:
    assert _flags("Werner Enterprises Inc", [], TODAY) == []


# --- failure is loud, and says WHICH failure -----------------------------------------------------
def test_a_fetch_failure_and_a_parse_failure_read_differently() -> None:
    """REVIEW FIX. A blanket catch reported a systematic EDGAR format change as "fetch failed", so
    an operator would retry and re-cache forever while every dossier silently reported its rename
    history unchecked. Both still fail LOUD — silence would read as a confirmed clean history."""
    fetch = _flags("Foo Inc.", HttpError("submissions 503"), TODAY)
    assert len(fetch) == 1 and "did not answer" in fetch[0] and "HttpError" in fetch[0], fetch
    parse = _flags("Foo Inc.", ValueError("bad date"), TODAY)
    assert len(parse) == 1 and "FAILED TO PARSE" in parse[0], parse
    assert "did not answer" not in parse[0]


def test_the_marker_is_a_human_caveat_not_machine_qa() -> None:
    """The partition at the schema boundary decides which renderer surface shows a flag. The
    marker and both failure notes are decision caveats for the analyst — routing them to QA would
    bury a data-integrity fact in the dev JSON."""
    caveats, qa = partition(_flags("Tectonic Therapeutic, Inc.", TECX, TODAY)
                            + _flags("Foo Inc.", HttpError("x"), TODAY)
                            + _flags("Foo Inc.", ValueError("x"), TODAY))
    assert len(caveats) == 3 and qa == [], (caveats, qa)


def test_the_marker_asserts_no_mechanism() -> None:
    """The 'heavy distribution' lesson: a rename record cannot support 'reverse merger'/'SPAC'/
    'shell' as an assertion — the marker states the filed fact and hedges the implication."""
    out = _flags("Tectonic Therapeutic, Inc.", TECX, TODAY)[0].lower()
    for word in ("reverse merger", "spac", "shell", "predecessor company"):
        assert word not in out, f"{word!r} asserted by the marker: {out}"
    assert "may span" in out


# --- the shared parser (ONE implementation, two consumers) ---------------------------------------
def test_the_resolver_and_the_marker_read_one_parser() -> None:
    """`EntityResolver._enrich_issuer` had its own inline comprehension over the same array — two
    parsers of one source is the twin-drift class (the `share_count_change` precedent). A change
    to either skip rule would have landed in only one, and the dossier's caveat could then
    disagree with the resolved issuer record for the same CIK."""
    import ast
    import pathlib
    src = (pathlib.Path(__file__).resolve().parents[1] / "vinci" / "resolver" / "resolver.py")
    tree = ast.parse(src.read_text())
    imported = {n.name for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
                and node.module == "vinci.edgar.submissions" for n in node.names}
    assert "parse_former_names" in imported, "the resolver re-derives its own formerNames parse"
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "_enrich_issuer")
    assert 'formerNames' not in ast.unparse(fn), "the resolver reads the raw array again"


def test_the_parser_skips_unreadable_rows_but_raises_on_a_malformed_date() -> None:
    """Shape is the real endpoint's (ISO timestamps with a time part). A missing name or end date
    is a SKIP — one bad row must not erase a whole history. A malformed DATE raises instead, so a
    systematic format change stays diagnosable rather than being swallowed as a skip."""
    rows = parse_former_names({"formerNames": [
        {"name": "AvroBio, Inc.", "from": "2018-02-02T05:00:00.000Z",
         "to": "2024-06-18T04:00:00.000Z"},
        {"name": "No End Date", "from": "2018-01-01T00:00:00.000Z", "to": None},
        {"name": "", "to": "2020-01-01T00:00:00.000Z"},
    ]})
    assert [r.name for r in rows] == ["AvroBio, Inc."]
    assert rows[0].from_date == date(2018, 2, 2) and rows[0].to_date == date(2024, 6, 18)

    import pytest
    with pytest.raises(ValueError):
        parse_former_names({"formerNames": [{"name": "Bad", "to": "not-a-date"}]})


def test_the_history_carries_the_current_name_alongside_the_former_ones() -> None:
    h = parse_registrant_history({"name": "  Artivion, Inc. ", "formerNames": [
        {"name": "CRYOLIFE INC", "to": "2022-01-06T00:00:00.000Z"}]})
    assert h.current == "Artivion, Inc." and [r.name for r in h.former] == ["CRYOLIFE INC"]
