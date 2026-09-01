"""The former-registrant-name marker — the reverse-merger vintage caveat.

A CIK's multi-year financial blocks can silently span a DIFFERENT underlying business filed under
the same number: FUBO's dossier history rides a CIK that was FaceBank Group (and four shells before
that), TECX's XBRL back to 2018 is AvroBio's, ORKA's is ARCA biopharma's, and MVST's is Tuscan
Holdings — a SPAC. The marker states the filed fact (name + span, source-bound to the submissions
``formerNames`` array) and directs verification; it never asserts a mechanism, because the SAME
array also records pure restyles (AAPL 2019, LLY's word-order row, FUBO's "/FL" reincorporation)
which are NOT predecessors and must never flag.

Every fixture below is the REAL ``formerNames`` payload fetched live from the submissions endpoint
on 2026-09-01 — never a hand-rolled shape (CLAUDE.md fixture rule). The check was swept over all
17 committed dossier CIKs before these pins were written (corpus before synthetic); the sweep is
what surfaced the three restyle classes the key must collapse.
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
from vinci.edgar.client import EdgarClient, FormerName

TODAY = date(2026, 9, 1)
BACKDATED = date(2022, 6, 1)  # a reference date at which the 2020-21 merger wave is in-window


def _fn(name: str, to: str, frm: str | None = None) -> FormerName:
    return FormerName(name=name, from_date=date.fromisoformat(frm) if frm else None,
                      to_date=date.fromisoformat(to))


class _StubEdgar:
    """Delivery stub only — the ROWS it serves are the real fetched payloads."""

    def __init__(self, rows: list[FormerName] | Exception) -> None:
        self._rows = rows

    def former_names(self, cik: int | str) -> list[FormerName]:
        if isinstance(self._rows, Exception):
            raise self._rows
        return self._rows


# --- the real payloads (fetched 2026-09-01) ------------------------------------------------------
TECX = [_fn("AvroBio, Inc.", "2024-06-18", "2018-02-02"),
        _fn("AVROBIO, Inc.", "2024-06-18", "2018-02-02")]
ORKA = [_fn("ARCA biopharma, Inc.", "2024-08-30", "2009-01-28"),
        _fn("NUVELO INC", "2009-01-27", "2003-02-04"),
        _fn("HYSEQ INC", "2003-01-28", "1997-07-17")]
AAPL = [_fn("APPLE INC", "2019-08-05", "2007-01-10"),
        _fn("APPLE COMPUTER INC", "2007-01-04", "1994-01-26"),
        _fn("APPLE COMPUTER INC/ FA", "1997-07-28", "1997-07-28")]
LLY = [_fn("LILLY ELI & CO", "2019-10-25"),
       _fn("LILLY ELI & CO ET AL", "1994-10-14")]
FUBO = [_fn("fuboTV Inc. /FL", "2025-10-30"),
        _fn("FaceBank Group, Inc.", "2020-08-12"),
        _fn("Pulse Evolution Group, Inc.", "2019-09-25"),
        _fn("Recall Studios, Inc.", "2019-02-07"),
        _fn("CAROLCO PICTURES, INC.", "2017-11-21"),
        _fn("Brick Top Productions, Inc.", "2014-12-31"),
        _fn("York Entertainment, Inc.", "2010-02-25")]
MVST = [_fn("Tuscan Holdings Corp.", "2021-07-21", "2018-12-07")]


def _flags(rows: list[FormerName] | Exception, current: str, ref: date) -> list[str]:
    return _former_name_flags(_StubEdgar(rows), "0000000000", current, ref)  # type: ignore[arg-type]


# --- true predecessors flag, once each, with their span ------------------------------------------
def test_tecx_flags_avrobio_exactly_once_with_its_span() -> None:
    """The two casing variants of AvroBio are ONE former registrant — a per-row flag would print
    the same predecessor twice and read as two different businesses."""
    out = _flags(TECX, "Tectonic Therapeutic, Inc.", TODAY)
    assert len(out) == 1, out
    assert '"AvroBio, Inc."' in out[0] or '"AVROBIO, Inc."' in out[0], out[0]
    assert "2024-06-18" in out[0] and "2018-02-02" in out[0], out[0]


def test_orka_flags_only_the_in_window_predecessor() -> None:
    """ARCA (to 2024) marks the page; Nuvelo and Hyseq predate every rendered vintage and would
    only be noise — three predecessor lines on a 2026 dossier caption rows that no longer exist."""
    out = _flags(ORKA, "Oruka Therapeutics, Inc.", TODAY)
    assert len(out) == 1, out
    assert "ARCA biopharma" in out[0], out[0]
    assert "NUVELO" not in out[0] and "HYSEQ" not in out[0]


def test_mvst_the_committed_corpus_hit_flags_its_spac_shell() -> None:
    """The live corpus case: MVST's committed dossier rides Tuscan Holdings' CIK. 'holdings' is
    deliberately NOT a style token — stripping it would erase exactly this class of shell."""
    out = _flags(MVST, "Microvast Holdings, Inc.", TODAY)
    assert len(out) == 1, out
    assert "Tuscan Holdings" in out[0], out[0]


# --- restyles are NOT predecessors (each class observed live) ------------------------------------
def test_aapl_never_flags_casing_or_filer_suffix_restyles() -> None:
    """'APPLE INC' -> 'Apple Inc.' is a restyle; 'APPLE COMPUTER INC/ FA' carries EDGAR's own
    trailing filer suffix. Neither is a predecessor at any reference date new enough to matter."""
    assert _flags(AAPL, "Apple Inc.", TODAY) == []


def test_lly_word_order_restyle_never_flags() -> None:
    """LLY filed as 'LILLY ELI & CO' until 2019 — the same registrant with the words reordered.
    At a 2022 reference that row is IN window, so a string-compare key would caption Eli Lilly's
    history as a different company's. The token-set key must collapse it."""
    assert _flags(LLY, "ELI LILLY & Co", BACKDATED) == []
    assert _flags(LLY, "ELI LILLY & Co", TODAY) == []


def test_fubo_reincorporation_suffix_never_flags_but_its_shell_chain_did() -> None:
    """The corpus pin pair. 'fuboTV Inc. /FL' (to 2025) is a state-of-incorporation restyle —
    flagging it would mark FUBO's page today over nothing. But at a 2022 reference the rendered
    lookback genuinely spans FOUR registrants (Carolco -> Recall -> Pulse Evolution -> FaceBank),
    and every one captions real rendered vintages — four lines is the honest record, not noise.
    By 2026 all four have aged out with the vintages they caption: aging out is designed."""
    today = _flags(FUBO, "FuboTV Inc.", TODAY)
    assert today == [], today
    back = _flags(FUBO, "FuboTV Inc.", BACKDATED)
    assert len(back) == 4, back
    assert [n for n in ("CAROLCO", "Recall Studios", "Pulse Evolution", "FaceBank Group")
            if not any(n in f for f in back)] == [], back
    assert "CAROLCO" in back[0] and "FaceBank" in back[-1]  # oldest first, like the history
    assert not any("York Entertainment" in f for f in back)  # to 2010 — out even backdated


def test_no_former_names_means_no_flag() -> None:
    assert _flags([], "Werner Enterprises Inc", TODAY) == []


# --- failure is loud, and the audience is the human ----------------------------------------------
def test_fetch_failure_says_not_checked_rather_than_staying_silent() -> None:
    """Silence on a failed fetch would read as a confirmed clean rename history — the same
    silent-absence shape the visible-absence rule prohibits."""
    out = _flags(RuntimeError("submissions down"), "Foo Inc.", TODAY)
    assert len(out) == 1 and "not checked" in out[0], out


def test_the_marker_is_a_human_caveat_not_machine_qa() -> None:
    """The partition at the schema boundary decides which renderer surface shows a flag. Both the
    marker and its failure note are decision caveats for the analyst — a QA routing would bury
    them in the dev JSON."""
    marker = _flags(TECX, "Tectonic Therapeutic, Inc.", TODAY)
    fail = _flags(RuntimeError("down"), "Foo Inc.", TODAY)
    caveats, qa = partition(marker + fail)
    assert len(caveats) == 2 and qa == [], (caveats, qa)


def test_the_marker_asserts_no_mechanism() -> None:
    """The 'heavy distribution' lesson: the input (a rename record) cannot support 'reverse
    merger', 'SPAC', or 'shell' as an assertion — the marker states the filed fact and hedges the
    implication ('may span')."""
    out = _flags(TECX, "Tectonic Therapeutic, Inc.", TODAY)[0].lower()
    for word in ("reverse merger", "spac", "shell", "predecessor company"):
        assert word not in out, f"{word!r} asserted by the marker: {out}"
    assert "may span" in out


# --- the client parse (real submissions shape) ---------------------------------------------------
def test_client_parses_and_skips_unreadable_rows() -> None:
    """A row missing its end date is SKIPPED, never guessed — an unreadable rename row must not
    fabricate a vintage. Shape is the real endpoint's (ISO timestamps with a time part)."""

    class _Http:
        def get_json(self, url: str, ttl_seconds: int = 0) -> dict[str, Any]:
            return {"formerNames": [
                {"name": "AvroBio, Inc.", "from": "2018-02-02T05:00:00.000Z",
                 "to": "2024-06-18T04:00:00.000Z"},
                {"name": "Broken Row", "from": "2018-01-01T00:00:00.000Z", "to": None},
                {"name": "", "to": "2020-01-01T00:00:00.000Z"},
            ]}

    client = EdgarClient(_Http())  # type: ignore[arg-type]
    rows = client.former_names("1681087")
    assert len(rows) == 1
    assert rows[0].name == "AvroBio, Inc."
    assert rows[0].from_date == date(2018, 2, 2) and rows[0].to_date == date(2024, 6, 18)


def test_the_lookback_matches_the_widest_rendered_block() -> None:
    """6y = 5 rendered fiscal years + up to a year of report/filing lag. A face-validity constant:
    if the dossier ever renders deeper history, this pin is the reminder to widen the marker."""
    assert _FORMER_NAME_LOOKBACK_DAYS == 2190


def test_the_key_is_style_insensitive_but_name_sensitive() -> None:
    assert _registrant_key("APPLE INC") == _registrant_key("Apple Inc.")
    assert _registrant_key("LILLY ELI & CO ET AL") == _registrant_key("ELI LILLY & Co")
    assert _registrant_key("fuboTV Inc. /FL") == _registrant_key("FuboTV Inc.")
    assert _registrant_key("Tuscan Holdings Corp.") != _registrant_key("Microvast Holdings, Inc.")
    assert _registrant_key("AvroBio, Inc.") != _registrant_key("Tectonic Therapeutic, Inc.")
