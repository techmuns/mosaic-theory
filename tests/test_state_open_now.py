"""§5.0 OPEN NOW must stay short, dated, and free of items the record elsewhere calls done.

THE FAILURE THIS EXISTS FOR (2026-08-25). §5 "Next steps" is append-only and had reached ~9,900
lines across 804 bold headers, of which 51 carried a done-marker — the rest largely NARRATIVE
rather than to-dos. "What is still open" was not answerable by reading it, and the record
CONTRADICTED ITSELF: an entry reading "STILL OPEN — the queue has not actually advanced" sat below
a later entry recording that same run as DONE. An agent that had verified the run itself that
morning then proposed re-triggering it.

So the fix is not "read more carefully" — it is that there must be ONE short place that answers the
question, and it must be cheap enough to read every time. These pins keep it that way: a block that
grows without bound, loses its date, or lists something the file elsewhere calls finished has
stopped being the answer and become more of the problem.
"""
from __future__ import annotations

import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
STATE = ROOT / "STATE.md"

#: Past this the block stops being readable-every-time, which is its only purpose.
MAX_LINES = 60


def _block() -> list[str]:
    lines = STATE.read_text().splitlines()
    # match the NAME, not just the number: renaming the heading to "archive notes" while leaving
    # "### 5.0" in place passed an earlier version of this, which would have let the block quietly
    # stop being the open list while every pin below it still went green.
    start = next((i for i, line in enumerate(lines)
                  if line.startswith("### 5.0") and "OPEN NOW" in line), None)
    assert start is not None, (
        "§5.0 OPEN NOW is gone. It is the only short answer to 'what is next'; without it the "
        "question needs 800 headers of append-only prose, which is how the weekly screen came to "
        "be proposed hours after it had run.")
    end = next((i for i, line in enumerate(lines[start + 1:], start + 1)
                if line.startswith("### ") or line.startswith("## ")), len(lines))
    return lines[start:end]


def test_the_open_block_stays_short_enough_to_actually_read() -> None:
    """It earns its place by being read EVERY time. §5 itself is the counter-example: 9,900 lines
    that nobody re-reads, so its contents stop being load-bearing."""
    block = _block()
    assert len(block) <= MAX_LINES, (
        f"§5.0 OPEN NOW is {len(block)} lines, over the {MAX_LINES} cap. Close items and delete "
        f"their rows, or move the explanation to §2 Built and verified — do not let this become a "
        f"second archive.")


def test_the_open_block_is_dated() -> None:
    """An undated list of open items cannot be distinguished from a stale one — which is exactly
    the state the entry it replaced was in."""
    assert re.search(r"20\d\d-\d\d-\d\d", _block()[0]), (
        "§5.0's heading carries no restamp date, so a reader cannot tell whether it is current")


def test_no_open_row_claims_a_run_the_record_says_already_happened() -> None:
    """THE SELF-CONTRADICTION GUARD — narrowed to what actually caused the defect.

    A first cut flagged any DONE reference anywhere in the block and immediately false-positived on
    a row that CITES a merged PR as background for an open follow-up. Citing finished work is not a
    contradiction; claiming that finished work is still to-do is. The defect was specifically about
    a RUN: "STILL OPEN — the queue has not actually advanced" sitting under a record of that run
    completing. So the check is on run ids inside TABLE ROWS, which is where open items live.
    """
    rows = [ln for ln in _block() if ln.startswith("|") and "---" not in ln]
    body = STATE.read_text()
    for row in rows:
        for run_id in re.findall(r"\b(\d{9,})\b", row):
            done = [ln for ln in body.splitlines()
                    if run_id in ln and not ln.startswith("|")
                    and re.search(r"\bDONE\b|\bGREEN END TO END\b|\bsuccess\b", ln)]
            assert not done, (
                f"§5.0 lists an OPEN item citing run {run_id}, which the record already reports as "
                f"completed:\n    {done[0].strip()[:120]}\nOne of the two is wrong.")


def test_the_closed_weekly_screen_entry_stays_struck() -> None:
    """The specific contradiction that caused this. Regression-pinned rather than merely corrected:
    the entry is struck AND names the run that closed it, so it cannot read as open again."""
    body = STATE.read_text()
    stale = "STILL OPEN — the queue has not actually advanced"
    if stale not in body:
        pytest.skip("the entry has since been removed entirely")
    # THE ENTRY, NOT THE FIRST QUOTE OF IT (review, #503). `next(...)` took whichever line
    # mentioned the phrase first, and passed only because §5.0's narrative happens to wrap it
    # across two lines today. A reflow — or any new prose quoting the incident, which this record
    # invites — would point the assertion at the narrative while the real entry sat unstruck. An
    # ENTRY starts its own line with bold; a quotation of it does not.
    entries = [x for x in body.splitlines()
               if stale in x and x.lstrip().startswith("**")]
    assert entries, (
        f"the phrase {stale!r} appears only inside prose, never as an entry heading — if the "
        f"entry was removed, drop this pin; if it was reworded, update it")
    for line in entries:
        assert line.lstrip().startswith("**~~"), (
        "the 'queue has not advanced' entry is no longer struck — it contradicts the run recorded "
        "green on 2026-08-25 and a reader gets two answers")
