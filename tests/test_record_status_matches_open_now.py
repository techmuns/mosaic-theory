"""A RECORD THAT READS `status: open` IS CITED BY AN OPEN §5.0 ROW — the ledger and the snapshot
give one answer to "is this still open?".

WHY (2026-11-11, the record-status sweep). §5.0 OPEN NOW is the one authority on what is open
(`tests/test_state_open_now.py`). A record's `status:` answers the same question in the ledger, and
the records README says it flips "when the item closes, is falsified, or is superseded". Nothing
checked that it did. On main `4c8349bc`, 77 records read `status: open` and 25 of them were cited
by no numbered §5.0 row (79 and 27 on `2637e91b`; the boundary is every `docs/records/*.md` but
README and TEMPLATE, and a citation is the record's filename inside a numbered row). Records from
both coordinators did this, from 2026-08-26 on. One example: `2026-11-05-fact-layer-r2-upload.md`
says in its own title that it closes STATE row 32's item (30), yet it still read `open`. That is
the two-answers failure §5.0 exists to end, rebuilt one level down, in the ledger.

THE RULE. A record reading `status: open` says its item is open, so a NUMBERED row of §5.0 must
cite it by filename, outside any struck (`~~closed~~`) span. Put the other way round: a record no
open row cites is not `open`. It is `shipped`, `recorded`, `superseded`, `falsified` or
`accepted-risk`. §5.0's prose lines do not count: the block's own rule is that a closed item's row
is deleted, so only a row says an item is open.

WHAT THIS DOES NOT CHECK — the converse. An open row may cite a shipped record as background. For
example, row 41 cites the code fixes whose pages it rebuilds, so "cited ⇒ open" is false and is not
pinned. Whether a cited record's item is still open is a judgment made at the row, and this test
does not read it.
"""
from __future__ import annotations

import functools
import pathlib
import re
from collections.abc import Iterable, Mapping

ROOT = pathlib.Path(__file__).resolve().parents[1]
STATE = ROOT / "STATE.md"
RECORDS = ROOT / "docs" / "records"

#: A numbered §5.0 row, as `test_state_open_now._rows` reads one.
_ROW = re.compile(r"^\|\s*\d+[a-z]?\s*\|")
#: A struck span: a closed item kept in its row for history. Non-greedy, so two spans on one row
#: stay two spans and the open text between them is kept.
_STRUCK = re.compile(r"~~.*?~~")
_STATUS = re.compile(r"^status:[ \t]*(\S+)[ \t]*$", re.M)


def open_rows(state_text: str) -> list[str]:
    """Every numbered row of §5.0 OPEN NOW, with its struck spans removed."""
    lines = state_text.splitlines()
    start = next((i for i, x in enumerate(lines)
                  if x.startswith("### 5.0") and "OPEN NOW" in x), None)
    assert start is not None, "STATE.md has no §5.0 OPEN NOW heading to read open rows from"
    end = next((i for i, x in enumerate(lines[start + 1:], start + 1)
                if x.startswith(("### ", "## "))), len(lines))
    return [_STRUCK.sub("", x) for x in lines[start:end] if _ROW.match(x)]


def front_status(text: str) -> str | None:
    """The `status:` of a record's FRONT MATTER. A body that quotes `status: open` (a template, a
    record describing this guard) is not the record's status."""
    if not text.startswith("---\n"):
        return None
    m = _STATUS.search(text.split("---", 2)[1])
    return m.group(1) if m else None


def is_cited(name: str, rows: Iterable[str]) -> bool:
    """`name` (a record filename) appears in a row as a whole name. `…-fix-request` is not cited
    by a row naming `…-fix-request-2.md`."""
    stem = re.escape(name.removesuffix(".md"))
    whole = re.compile(rf"(?<![\w-]){stem}(?![\w-])")
    return any(whole.search(r) for r in rows)


def uncited_open_records(state_text: str, records: Mapping[str, str]) -> list[str]:
    """Each record reading `status: open` that no open §5.0 row cites. Empty means coherent."""
    rows = open_rows(state_text)
    return sorted(n for n, t in records.items()
                  if front_status(t) == "open" and not is_cited(n, rows))


@functools.lru_cache(maxsize=1)
def _records() -> dict[str, str]:
    """Read once per run; callers copy what they change, never the cached dict."""
    return {p.name: p.read_text() for p in sorted(RECORDS.glob("*.md"))
            if p.name not in ("README.md", "TEMPLATE.md")}


def test_every_open_record_is_cited_by_an_open_row() -> None:
    bad = uncited_open_records(STATE.read_text(), _records())
    assert not bad, (
        f"{len(bad)} record(s) read `status: open`, but no open STATE.md §5.0 row cites them, so "
        f"the ledger says open where the snapshot says nothing is:\n  " + "\n  ".join(bad) +
        "\nEither the item has closed — flip `status:` to shipped, recorded, superseded, "
        "falsified or accepted-risk, the one change docs/records/README.md allows after merge — "
        "or it is open, and the §5.0 row that tracks it must cite the record by filename.")


# ── pins: the same function, on the real STATE.md and a real open record ────────────────────────


def _real_open_record() -> tuple[str, dict[str, str]]:
    """A REAL record that reads `open` and is cited today, alone in its mapping. A pin on a
    hand-rolled record would test the fixture (CLAUDE.md, corpus before synthetic). Keeping it
    alone keeps each pin about this one record, whatever the rest of the corpus reads."""
    records = _records()
    rows = open_rows(STATE.read_text())
    name = next(n for n, t in records.items() if front_status(t) == "open" and is_cited(n, rows))
    return name, {name: records[name]}


def _drop_row_citations(state_text: str, name: str, keep: str = "") -> str:
    """STATE.md with `name` blanked inside §5.0's numbered rows only; elsewhere it stays."""
    stem = name.removesuffix(".md")
    return "\n".join(x.replace(stem, keep or "a-record-no-longer-cited") if _ROW.match(x) else x
                     for x in state_text.splitlines())


def test_a_cited_open_record_passes() -> None:
    """THE POSITIVE PIN. A real open record its row cites passes."""
    name, records = _real_open_record()
    assert name not in uncited_open_records(STATE.read_text(), records)


def test_an_open_record_whose_row_drops_it_is_flagged() -> None:
    """THE NEGATIVE PIN, in the shape that was observed. A record reads open after its row has
    stopped carrying it (closed, deleted or rewritten). The fact-layer R2 upload record read open
    after row 32 closed its item (30)."""
    name, records = _real_open_record()
    assert uncited_open_records(_drop_row_citations(STATE.read_text(), name), records) == [name]


def test_a_citation_outside_the_rows_does_not_count() -> None:
    """§2, the archive, and §5.0's own prose are history or narrative, never the open list. If
    such a mention kept a record open, a bullet in §2 could hold it open forever."""
    name, records = _real_open_record()
    state = _drop_row_citations(STATE.read_text(), name)
    heading = next(x for x in state.splitlines() if x.startswith("### 5.0"))
    state = state.replace(heading, f"{heading}\n\nProse naming docs/records/{name}.", 1)
    state += f"\n- A §2-style claim pointing at `docs/records/{name}`.\n"
    assert name in state
    assert uncited_open_records(state, records) == [name]


def test_a_citation_inside_a_struck_span_does_not_count() -> None:
    """A struck item inside a row is closed, and the row keeps it only for history."""
    name, records = _real_open_record()
    stem = name.removesuffix(".md")
    state = _drop_row_citations(STATE.read_text(), name, keep=f"~~{stem}~~")
    assert uncited_open_records(state, records) == [name]


def test_a_flipped_record_is_not_flagged_once_its_row_drops_it() -> None:
    """THE POSITIVE PIN for the remedy. Once its row drops it, the record flips to a closed status
    and passes. Every status the ledger allows other than `open` passes."""
    name, records = _real_open_record()
    state = _drop_row_citations(STATE.read_text(), name)
    for closed in ("shipped", "recorded", "superseded", "falsified", "accepted-risk"):
        flipped = re.sub(r"(?m)^status:\s*open\s*$", f"status: {closed}", records[name], count=1)
        assert front_status(flipped) == closed
        assert uncited_open_records(state, {name: flipped}) == []


def test_a_name_that_is_a_prefix_of_a_cited_one_is_not_cited() -> None:
    """A whole-name match. `…-fix-request` is a different record from `…-fix-request-2.md`, so a
    row citing the second does not hold the first open."""
    name, records = _real_open_record()
    prefix = name.removesuffix(".md").rsplit("-", 1)[0] + ".md"
    assert prefix != name and prefix not in records
    assert uncited_open_records(STATE.read_text(), {prefix: records[name]}) == [prefix]


def test_status_open_in_a_body_is_not_the_records_status() -> None:
    """The front matter is the record's status. A body that quotes the template's
    `status: open`, as a record about this guard would, is not."""
    records = _records()
    name = next(n for n, t in records.items() if front_status(t) == "shipped")
    quoting = records[name] + "\n```\nstatus: open\n```\n"
    assert front_status(quoting) == "shipped"
    assert name not in uncited_open_records(STATE.read_text(), {name: quoting})
