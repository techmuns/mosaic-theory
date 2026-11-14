"""A passage re-drawn in another case or spacing is the passage the spool holds (2026-11-14).

THE DEFECT. GOOGL's paid build (run `8d2e72e8`, $3.84, 7 calls) wrote no page. After every model
call, the write-once spool refused it with `EvidenceBytesDifferError` on
`driver-evidence/v1/cab0759d…/8/62fca102….json`, a passage of GOOGL's Q2 2026 call filed on
2026-11-10. The key hashes the quote FOLDED (case and whitespace, `quote_key`); the record held the
model's raw string. A draw quoting the passage with one letter's case or one space different shared
the key and not the bytes.

THE RULING (operator, relayed 2026-11-14: "Fix, then one build at $5.78 (Recommended)"; the
coordinator chose (b)). A row files the CALL'S words at its quote's folded match
(`driver_extract.as_the_call_prints_it`), and the spool holds a passage whose quote differs only
in the key's fold as the same passage: the first bytes stand, and the page names the record
(`driver_evidence.refolded_flag`).

FIXTURES (`tests/fixtures/evidence_same_passage/GOOGL.json`), never more than 12 consecutive
transcript words: the record's locator and hashes as the operator's spool holds it, and a cut of
the call, its speaker block and the quote's first 10 words as the call prints them. The real-call
pin reads the licensed call where it is on disk (`stripped_pages.ciq_root`) and skips elsewhere.
Nothing here reads or writes the operator's spool: a pytest folder plays it.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from tests.stripped_pages import ciq_root, committed_page
from vinci.dossier import driver_evidence as de
from vinci.dossier import driver_extract as dx
from vinci.dossier.schemas import Dossier, OperatingDriver

CASE: dict[str, Any] = json.loads(
    (Path(__file__).parent / "fixtures" / "evidence_same_passage" / "GOOGL.json").read_text())
SPAN: str = CASE["cut"]["span"]   # the quote's first 10 words, as the call prints them
#: The day the held record was filed, as its file's time: 2026-11-10 17:46:04Z
FILED_AT = datetime(2026, 11, 10, 17, 46, 4, tzinfo=UTC).timestamp()


def _case_flip(q: str) -> str:
    return q[0].swapcase() + q[1:]


def _space_flip(q: str) -> str:
    return q.replace(" ", "\n", 1)


REDRAWS = {"case": _case_flip, "spacing": _space_flip}


class _Llm:
    """Returns one driver row quoting ``quote``: the shape the extraction tool returns."""

    def __init__(self, quote: str) -> None:
        self.quote = quote

    def extract(self, *, system: str, user: str, tool: dict[str, Any],
                **_: object) -> dict[str, Any]:
        return {"drivers": [{"kind": "competitive_position", "metric": "positioning",
                             "value": "stated", "quote": self.quote, "period": ""}]}


def _cut_slice() -> str:
    """The call as `transcript_for_synthesis` labels it, cut to the speaker block and the span."""
    return f"--- {CASE['call']} ---\n" + "\n".join(CASE["cut"]["speaker_block"]) + f"\n\n{SPAN}\n"


def _row(quote: str, slice_text: str | None = None) -> OperatingDriver:
    rows, _flags, _ = dx.extract_transcript_drivers(
        slice_text or _cut_slice(), llm=_Llm(quote), ticker="GOOGL", name="Alphabet Inc.",
        transcript_sha256={CASE["call"]: CASE["transcript_sha256"]})
    (row,) = rows
    return row


def _record(row: OperatingDriver) -> de.EvidenceRecord:
    rec = de.record_for(row)
    assert rec is not None
    return rec


def _held(tmp_path: Path, rec: de.EvidenceRecord) -> tuple[de.EvidenceSpool, Path]:
    """A spool holding ``rec``, its file dated the day the real record was filed."""
    spool = de.EvidenceSpool(tmp_path)
    assert spool.put(rec) is True
    path = spool.path(de.key_of(rec))
    os.utime(path, (FILED_AT, FILED_AT))
    return spool, path


# --- the row files the call's words --------------------------------------------------------------

@pytest.mark.parametrize("redraw", sorted(REDRAWS))
def test_a_redraw_in_another_case_or_spacing_files_the_calls_own_words(redraw: str) -> None:
    """(-) On main the row filed the model's string, so the re-draw's record was another file's
    bytes under one key. It now files the call's words: the same bytes as a draw quoting the
    call exactly."""
    row = _row(REDRAWS[redraw](SPAN))
    assert row.verbatim == SPAN
    assert de.record_bytes(_record(row)) == de.record_bytes(_record(_row(SPAN)))
    assert row.locator is not None and row.locator.speaker == CASE["speaker"]


# --- the spool holds the same passage in another case or spacing ----------------------------------

@pytest.mark.parametrize("redraw", sorted(REDRAWS))
def test_a_held_passage_in_another_case_or_spacing_is_already_held_and_left_as_filed(
        tmp_path: Path, redraw: str) -> None:
    """(-) THE 3 RECORDS IN THE SPOOL THAT HOLD THE MODEL'S CAPITAL, and GOOGL's refusal: the held
    quote and the new one differ only in what the key folds. On main `put` raised; now the spool
    already holds it, and the held file's bytes and time are untouched."""
    held = _record(_row(SPAN))
    spool, path = _held(tmp_path, held)
    before = (path.read_bytes(), path.stat().st_mtime)
    again = held.model_copy(update={"verbatim": REDRAWS[redraw](SPAN)})
    assert spool.put(again) is False
    filed = spool.file(again)
    assert (filed.written, filed.held_refolded_on) == (False, CASE["filed"])
    assert (path.read_bytes(), path.stat().st_mtime) == before
    assert [p.name for p in tmp_path.iterdir()] == [path.name]
    assert spool.get(de.key_of(held)) == held


def test_the_same_bytes_again_are_not_named_as_refolded(tmp_path: Path) -> None:
    """(+) NEGATIVE PIN: a draw of the call's own words is the held record itself."""
    held = _record(_row(SPAN))
    spool, _ = _held(tmp_path, held)
    assert spool.file(held) == de.Filing(de.key_of(held), written=False)


@pytest.mark.parametrize("change", ["speaker", "context", "call"])
def test_anything_else_that_differs_under_the_key_is_still_refused(
        tmp_path: Path, change: str) -> None:
    """(+) NEGATIVE PIN: the fold is the key's, nothing wider. The case flip with a changed speaker,
    context or call name is another record under the key, refused, and the held file stays."""
    held = _record(_row(SPAN))
    spool, path = _held(tmp_path, held)
    before = path.read_bytes()
    loc = held.locator
    other = {"speaker": {"locator": loc.model_copy(update={"speaker": "Ruth Porat"})},
             "context": {"following_context": "Another paragraph."},
             "call": {"locator": loc.model_copy(update={"call": "Another call.rtf"})}}[change]
    with pytest.raises(de.EvidenceBytesDifferError):
        spool.put(held.model_copy(update={"verbatim": _case_flip(SPAN), **other}))
    assert path.read_bytes() == before


def test_one_changed_word_under_the_key_is_refused_and_a_changed_paragraph_is_another_key(
        tmp_path: Path) -> None:
    """(+) NEGATIVE PIN: one changed word is not the passage its locator hashes, so it is refused
    before any comparison. A changed paragraph is part of the key, so it files beside the held
    record and never meets it."""
    held = _record(_row(SPAN))
    spool, path = _held(tmp_path, held)
    words = SPAN.split()
    with pytest.raises(de.EvidenceIntegrityError):
        spool.put(held.model_copy(update={"verbatim": " ".join([*words[:-1], "changed"])}))
    moved = held.model_copy(update={"locator": held.locator.model_copy(update={"paragraph": 9})})
    assert de.key_of(moved) != de.key_of(held)
    assert spool.put(moved) is True and path.exists()


# --- the page names every passage held in another case or spacing ---------------------------------

def _page(row: OperatingDriver) -> Dossier:
    """GOOGL's committed page with ``row`` as its one transcript row."""
    page = Dossier.model_validate(committed_page("GOOGL"))
    od = page.mechanical.operating_drivers
    assert od is not None
    mech = page.mechanical.model_copy(
        update={"operating_drivers": od.model_copy(update={"rows": [row]})})
    return page.model_copy(update={"mechanical": mech})


def test_the_page_names_a_passage_held_in_another_case_with_its_key_and_filed_day(
        tmp_path: Path) -> None:
    """(-) The re-draw is never silent. A page whose row meets a held record that holds the model's
    capital (the 3 the spool keeps) carries one QA flag naming the key and the day it was filed,
    with no word of the quote. On main the page was refused."""
    row = _row(SPAN)
    held = _record(row).model_copy(update={"verbatim": _case_flip(SPAN)})
    spool, _ = _held(tmp_path, held)
    page = _page(row)
    out, rep = de.spool_dossier(page, spool)
    key = de.key_of(held)
    assert rep.refolded == [(key, CASE["filed"])]
    new = [f for f in out.qa_flags if f not in page.qa_flags]
    assert new == [de.refolded_flag(key, CASE["filed"])]
    # built from the key and the day alone: no word of the quote can enter it
    assert new[0].replace(key, "K").replace(CASE["filed"], "D") == de.refolded_flag("K", "D")
    assert key in new[0] and CASE["filed"] in new[0]


def test_a_page_meeting_only_its_own_bytes_gains_no_flag(tmp_path: Path) -> None:
    """(+) NEGATIVE PIN: a passage held byte for byte adds nothing to the page."""
    row = _row(SPAN)
    spool, _ = _held(tmp_path, _record(row))
    page = _page(row)
    out, rep = de.spool_dossier(page, spool)
    assert rep.refolded == [] and out.qa_flags == page.qa_flags


# --- the real call, by hashes and locator (skips where the licensed call is not on disk) ---------

def test_the_real_redraw_files_the_bytes_the_spool_holds_for_googls_passage() -> None:
    """(-) GOOGL'S PASSAGE, END TO END. From the licensed call on disk, the quote is the paragraph's
    words at the fixture's span, checked against its hash, and the slice is the call as
    `transcript_for_synthesis` writes it. A re-draw in another case or spacing now files a record
    whose sha256 is the one the operator's spool holds for it, filed 2026-11-10. On main its bytes
    were another record's."""
    from vinci.dossier import ciq_sheets as cs
    from vinci.dossier.ciq import classify, read_text

    path = ciq_root() / "GOOGL" / CASE["call"]
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != (
            CASE["transcript_sha256"]):
        pytest.skip(f"the call {CASE['transcript_sha256'][:10]}… is not on disk")
    prose = cs._transcript_prose(read_text(path, classify(path)))
    slice_text = f"--- {path.name} ---\n{prose}"
    para = dx._PARAGRAPH_BREAK.split("\n" + prose)[CASE["paragraph"]]
    i, j = CASE["quote_word_span"]
    quote = " ".join(re.sub(r"\s+", " ", para).strip().split(" ")[i:j])
    assert dx.quote_key(quote) == CASE["quote_sha256"]
    for redraw in (_case_flip, _space_flip):
        row = _row(redraw(quote), slice_text)
        assert row.locator is not None and row.locator.paragraph == CASE["paragraph"]
        got = hashlib.sha256(de.record_bytes(_record(row))).hexdigest()
        assert got == CASE["record_sha256"], redraw.__name__
