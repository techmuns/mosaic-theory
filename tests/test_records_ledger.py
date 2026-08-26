"""THE LEDGER'S OWN GUARDS — §5 stays frozen, records stay well-formed, citations keep resolving.

WHY (2026-08-25, P0 of the knowledge-ledger plan). STATE.md reached 19,209 lines / 1.7 MB, doubling
roughly every four weeks, because entries were APPENDED like a journal and TRUSTED like a snapshot.
Closing an item edited nothing upstream, so the file came to answer one question two ways: an entry
reading "STILL OPEN — the queue has not actually advanced" sat below a later entry recording that
same run green, and an agent that had verified the run itself that morning proposed re-triggering
it that afternoon.

The split is the one the fund already runs on its DATA — an append-only ledger beside regenerable
snapshots. STATE.md is the snapshot; `docs/records/` is the ledger. These pins are what stop the
old shape coming back, because a freeze nothing enforces is a note, not a rule.
"""
from __future__ import annotations

import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
STATE = ROOT / "STATE.md"
RECORDS = ROOT / "docs" / "records"

#: The ARCHIVE's line count at the freeze — §5 measured from the END of the §5.0 OPEN NOW block.
#: §5.0 is deliberately excluded: it is the LIVING block and legitimately grows and shrinks as
#: items open and close (it carries its own 60-line cap in test_state_open_now). Measuring the two
#: together made the freeze fire on ordinary open-item churn — a false alarm that would have
#: trained the next reader to raise the number, which is how a cap stops meaning anything.
ARCHIVE_FROZEN_AT = 9904
#: Slack for the strike-throughs and pointers that CLOSING an item legitimately adds in place.
FREEZE_SLACK = 40

STATUSES = {"open", "shipped", "falsified", "superseded", "accepted-risk"}


def _archive() -> list[str]:
    """§5 BELOW the §5.0 OPEN NOW block — the frozen archive, not the living open list."""
    lines = STATE.read_text().splitlines()
    start = next(i for i, x in enumerate(lines) if x.startswith("## 5. Next steps"))
    end = next((i for i, x in enumerate(lines[start + 1:], start + 1) if x.startswith("## ")),
               len(lines))
    section = lines[start:end]
    # the archive begins after §5.0's block: its heading, then the next "### " or "**" entry
    o = next((i for i, x in enumerate(section) if x.startswith("### 5.0")), None)
    if o is None:
        return section
    after = next((i for i, x in enumerate(section[o + 1:], o + 1)
                  if x.startswith("**") and "NOT open" not in x), len(section))
    return section[after:]


def test_section_5_is_frozen_and_can_only_shrink() -> None:
    """THE FREEZE, made checkable. New narrative belongs in `docs/records/`; §5 is now archive.

    A ceiling rather than an equality, because closing an item legitimately edits §5 in place —
    striking an entry, deleting a §5.0 row. Those shrink or barely move it. What this refuses is
    the old habit: appending another 40-line essay about something that shipped.
    """
    n = len(_archive())
    assert n <= ARCHIVE_FROZEN_AT + FREEZE_SLACK, (
        f"§5's archive is {n} lines, above the {ARCHIVE_FROZEN_AT} it was frozen at "
        f"(+{FREEZE_SLACK} slack). It is FROZEN: a build's narrative goes in a new "
        f"docs/records/ file, and STATE.md gets only the §5.0 row and a <=3-line claim. "
        f"See CLAUDE.md session ritual step 2.")


def test_the_ledger_has_its_contract_written_down() -> None:
    """A convention nobody can read is a convention that drifts. The README carries the naming
    rule, the header fields and the amendment contract, so a new session or a different tool can
    follow it without this test explaining it."""
    readme = (RECORDS / "README.md").read_text()
    for anchor in ("YYYY-MM-DD", "status:", "Amendments", "immutable"):
        assert anchor in readme, f"docs/records/README.md no longer explains {anchor!r}"
    assert (RECORDS / "TEMPLATE.md").is_file(), "the record template is gone"


def _records() -> list[pathlib.Path]:
    return [p for p in sorted(RECORDS.glob("*.md")) if p.name not in ("README.md", "TEMPLATE.md")]


def test_every_record_is_named_and_headed_correctly() -> None:
    """Filenames ARE the index — `ls` sorts chronologically and `grep D22 docs/records/` finds the
    entry. There is deliberately no curated index file: CLAUDE.md's existence-check rule warns that
    one rots and its gaps re-create the false 'not listed -> does not exist' inference."""
    for p in _records():
        assert re.match(r"^\d{4}-\d{2}-\d{2}-[a-zA-Z0-9][\w.-]*\.md$", p.name), (
            f"{p.name} does not match YYYY-MM-DD-<slug>.md — the filename is the index")
        text = p.read_text()
        assert text.startswith("---\n"), f"{p.name} has no front-matter header"
        header = text.split("---", 2)[1]
        status = re.search(r"^status:\s*(\S+)", header, re.M)
        assert status and status.group(1) in STATUSES, (
            f"{p.name} has status {status.group(1) if status else None!r}; "
            f"expected one of {sorted(STATUSES)}")
        assert re.search(r"^date:\s*\d{4}-\d{2}-\d{2}", header, re.M), (
            f"{p.name} has no valid `date:` — an undated record cannot be ordered or trusted")


def test_record_identifiers_do_not_collide_with_state_md() -> None:
    """CITATIONS MUST KEEP RESOLVING. ~100 S/D references live inside STATE.md and dozens more sit
    in code comments, docs and tests (D1 x20, D3 x11, D4 x9). A record carrying an `id:` that
    STATE.md still holds would make those citations ambiguous — the exact S10 collision that
    `test_state_identifiers` exists for, arriving through the new directory instead.
    """
    state_ids = set(re.findall(r"\*\*([SD]\d+)\.\s", STATE.read_text()))
    for p in _records():
        header = p.read_text().split("---", 2)[1]
        m = re.search(r"^id:\s*([SD]\d+)\s*$", header, re.M)
        if not m:
            continue
        assert m.group(1) not in state_ids, (
            f"{p.name} claims id {m.group(1)}, which STATE.md still holds as an entry heading. "
            f"A citation of it would resolve to two places. Migrate the STATE.md entry (P1) or "
            f"pick the next free identifier.")


def test_fossil_banners_point_somewhere_live() -> None:
    """A fossil marked without a forwarding address just strands the reader. Every banner names
    where current truth actually lives."""
    bannered = [p for p in ROOT.glob("docs/*.md")
                if p.read_text(errors="ignore").startswith("> **FOSSIL")]
    if not bannered:
        pytest.skip("no fossils marked yet")
    for p in bannered:
        head = "\n".join(p.read_text().splitlines()[:8])
        assert "STATE.md" in head and "RUNBOOKS" in head, (
            f"{p.name}'s fossil banner does not point at the live surfaces")
