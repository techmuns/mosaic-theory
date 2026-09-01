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


def _rows() -> list[str]:
    """The item cell of every numbered row, in file order."""
    cells = []
    for line in _block():
        m = re.match(r"^\|\s*\d+[a-z]?\s*\|\s*(.+?)\s*\|", line)
        if m:
            cells.append(m.group(1))
    return cells


def test_no_open_item_is_listed_twice() -> None:
    """A duplicated row splits the reader's answer in two, which is this block's whole failure mode.

    OBSERVED 2026-08-28: Phase 2 stood as BOTH row 1 and row 2, in near-identical wording that
    diverged in its detail — so "is Phase 2 gated on a cost gate?" had two answers in the one place
    that promises a single one. It arrived the ordinary way: a row promoted up the list without the
    old one being removed.

    Keyed on the LEADING BOLD TITLE rather than the full cell, because the two rows' bodies had
    already drifted apart — a whole-cell comparison would have called them distinct and passed.
    """
    # MATCH-OR-SKIP, never `.match(...).group(...)`: a cell whose bold is left unclosed — the
    # ordinary typo in a hand-edited table — makes the chained call die with an AttributeError and
    # a traceback in place of the message below, so the pin stops explaining itself exactly when
    # the file is being edited by hand.
    titles = [m.group(1) for c in _rows() if (m := re.match(r"\*\*(.+?)\*\*", c))]
    dupes = {t for t in titles if titles.count(t) > 1}
    assert not dupes, (
        f"§5.0 lists the same item more than once: {sorted(dupes)}. Delete the stale row — two "
        f"rows for one item is two answers to 'what is next', which is what this block exists to "
        f"prevent.")


def test_every_open_row_says_who_owns_it() -> None:
    """A row nobody owns is a row nobody does.

    The owner column is what separates 'an agent may pick this up' from 'this waits on a human
    ruling' — rows 3-5 today are operator rulings an agent must NOT build past.
    """
    for line in _block():
        if not re.match(r"^\|\s*\d+[a-z]?\s*\|", line):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        assert len(cells) >= 3 and cells[2] in {"agent", "operator"}, (
            f"open row has no agent/operator owner: {line[:90]}")


def test_no_two_rows_share_a_number() -> None:
    """INVARIANT for a real incident (2026-08-30): a rebase resolved onto the merged main by
    KEEPING BOTH sides of a §5.0 conflict — right for a §2 capability bullet, where the two sides
    are different builds, and wrong here, where they were two VERSIONS of one row. The table came
    out with two rows numbered 6, and the suite stayed green: the sibling guard above keys on the
    leading bold TITLE, and the two versions had been retitled, so it read them as distinct items.

    The row NUMBER is the thing a reader points at ("row 6 is mine"), so a repeated number is a
    corrupted index however different the prose is."""
    seen: dict[str, str] = {}
    dupes: list[str] = []
    for line in _block():
        m = re.match(r"^\|\s*(\d+[a-z]?)\s*\|\s*(.+?)\s*\|", line)
        if not m:
            continue
        num, cell = m.group(1), m.group(2)
        if num in seen:
            dupes.append(f"row {num}: {seen[num][:60]!r} vs {cell[:60]!r}")
        seen[num] = cell
    assert not dupes, "§5.0 rows share a number:\n  " + "\n  ".join(dupes)


#: Whole-file ceiling for STATE.md — OPERATOR RULING 2026-08-31.
#:
#: WHY A NUMBER AT ALL. The knowledge-ledger plan took this file 19,241 -> 1,892 lines, and five
#: days later it was 2,085: roughly 38 lines a day, which doubles it in about seven weeks. P0
#: recorded the original growth as "doubling every ~4 weeks", so the same shape had already
#: returned. Two of eight sections were capped (§5.0 at 60 lines, §5's archive frozen); the other
#: six and the file as a whole were not, so nothing distinguished legitimate growth from the drift
#: that produced 19,241 lines until it was unreadable again.
#:
#: WHY 2,500 AND NOT SMALLER. Set by the OPERATOR, not derived here — and deliberately generous:
#: 415 lines of headroom over today. P3's lesson was that a number invented before knowing what
#: the file contains (the retracted ≤600 target) forces real information out to satisfy an
#: arbitrary bound. This one is a TRIPWIRE, not a diet: it fires long before the file stops being
#: readable in one sitting, which P3 named as the actual goal.
#:
#: WHAT TO DO WHEN IT TRIPS — and this is the whole point of the message below. **Move detail into
#: a record under `docs/records/`. Never delete it.** The snapshot keeps the one-line claim and a
#: pointer; the ledger keeps the full account forever. Raising this constant instead is a decision
#: to let the file grow, which is exactly the choice that has to be deliberate rather than silent.
STATE_MAX_LINES = 2500


def test_state_md_stays_readable_in_one_sitting() -> None:
    """The whole file, not just the sections that happen to be capped."""
    n = len(STATE.read_text().splitlines())
    assert n <= STATE_MAX_LINES, (
        f"STATE.md is {n:,} lines, over the {STATE_MAX_LINES:,} ceiling (operator ruling, "
        f"2026-08-31). It reached 19,241 once and the knowledge-ledger plan spent four PRs "
        f"getting it back to 1,892 — this is the tripwire that stops that happening twice.\n\n"
        f"THE FIX IS TO MOVE DETAIL, NEVER TO DELETE IT: write the full account to a new file "
        f"under docs/records/ and leave the one-line claim plus a pointer here. Raising the "
        f"ceiling is a decision to let the file grow — make it deliberately, in the PR body, or "
        f"not at all.")


def test_the_ceiling_leaves_room_to_work() -> None:
    """A ceiling with no headroom is a ceiling that gets raised on the next ordinary build, which
    is how a limit stops meaning anything. If this fails, the file has grown into its tripwire and
    the answer is a migration, not a bigger number."""
    n = len(STATE.read_text().splitlines())
    assert STATE_MAX_LINES - n >= 100, (
        f"only {STATE_MAX_LINES - n} lines of headroom under the {STATE_MAX_LINES:,} ceiling. "
        f"Move a section's detail into docs/records/ before the next build has to.")
