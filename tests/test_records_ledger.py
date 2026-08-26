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

import contextlib
import importlib.util
import io
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
STATE = ROOT / "STATE.md"
RECORDS = ROOT / "docs" / "records"

#: P1 (2026-08-25) MIGRATED the archive out, so what remains below §5.0 is the pointer block, not
#: 9,904 lines of entries. The cap is re-set to the pointer's size: §5 can never re-accumulate
#: entries, because a new one is a file under docs/records/ and this refuses the alternative.
#:
#: The ARCHIVE's line count — §5 measured from the END of the §5.0 OPEN NOW block.
#: §5.0 is deliberately excluded: it is the LIVING block and legitimately grows and shrinks as
#: items open and close (it carries its own 60-line cap in test_state_open_now). Measuring the two
#: together made the freeze fire on ordinary open-item churn — a false alarm that would have
#: trained the next reader to raise the number, which is how a cap stops meaning anything.
#: That exclusion was ASSERTED and not true: `_archive` scanned for the next `**` line, and §5.0's
#: own body opens with one, so 31 of the 47 lines this measured were the living block. Harmless at
#: 9,904; at a 60-line cap it WAS the cap. Fixed in `_archive`, and the number re-measured against
#: what the archive actually is now — the two migration pointer blocks, 24 lines.
ARCHIVE_FROZEN_AT = 24
#: Slack for the strike-throughs and pointers that CLOSING an item legitimately adds in place.
FREEZE_SLACK = 40

#: `recorded` was added by P1: most migrated entries are DIAGNOSIS / EXPERIMENT / AUDIT records —
#: things that happened and were written down, not things that shipped. Calling those "shipped"
#: would be a small lie repeated 100+ times.
STATUSES = {"open", "shipped", "falsified", "superseded", "accepted-risk", "recorded"}


def _archive() -> list[str]:
    """§5 BELOW the §5.0 OPEN NOW block — the frozen archive, not the living open list."""
    lines = STATE.read_text().splitlines()
    start = next(i for i, x in enumerate(lines) if x.startswith("## 5. Next steps"))
    end = next((i for i, x in enumerate(lines[start + 1:], start + 1) if x.startswith("## ")),
               len(lines))
    section = lines[start:end]
    # THE ARCHIVE BEGINS AT THE NEXT '### ' HEADING, not at the next '**' line. §5.0's own body
    # opens with `**WHY THIS BLOCK EXISTS.**`, so a '**' scan stopped THERE and counted the whole
    # living block as archive. That was invisible while the cap was 9,904 — 31 lines of §5.0 inside
    # a five-figure budget is noise. At a 60-line cap it is most of the budget, and ordinary §5.0
    # churn would red this test with a message naming the wrong cause. Sub-headings are the real
    # boundary: §5.0 is a '### ' block and so is everything after it.
    o = next((i for i, x in enumerate(section) if x.startswith("### 5.0")), None)
    if o is None:
        return section
    after = next((i for i, x in enumerate(section[o + 1:], o + 1)
                  if x.startswith("### ")), len(section))
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


def test_the_freeze_measures_the_archive_and_not_the_living_open_block() -> None:
    """THE REGRESSION. `_archive` used to scan for the next `**` line, and §5.0's own body opens
    with `**WHY THIS BLOCK EXISTS.**` — so the "archive" it measured STARTED INSIDE §5.0 and
    carried 31 lines of the living block. Invisible against a 9,904-line cap; at a 60-line cap it
    was most of the budget, and adding open-item rows would have reddened the FREEZE test with a
    message naming the wrong cause. Pinned against the live file, not a fixture."""
    archive = _archive()
    assert archive, "the archive scan found nothing — the §5 heading shape changed"
    assert not any("WHY THIS BLOCK EXISTS" in x for x in archive), (
        "§5.0's body is inside the measured archive again — the freeze is now counting the "
        "LIVING open-item block, so ordinary churn will trip a test about the frozen archive")
    assert not any(x.lstrip().startswith("| ") for x in archive), (
        "the §5.0 OPEN NOW table is inside the measured archive — same defect, seen from the "
        "row side; open items must not consume the freeze budget")


def test_the_migration_script_refuses_a_state_md_its_offsets_do_not_describe() -> None:
    """THE ONE THING RECONSTRUCTION CANNOT PROVE. `state_entry_boundaries.txt` is a list of raw
    LINE OFFSETS, and the reconstruction check only proves the split is CONTIGUOUS — which any
    monotone offset list satisfies. So a shifted list re-cuts all 198 records in the wrong places
    and still prints `reconstruction OK`. And the offsets shift on ordinary work: they count from
    the §5 heading, and §5.0 above the archive gains a row every build. Demonstrated: inserting one
    line into §5.0 produced 198 wrong-boundary records, written without complaint.

    The source is therefore pinned by content hash. THIS repo's STATE.md is the MIGRATED one, so
    the live corpus IS the negative case — the script must refuse it, and refuse it legibly (it
    used to die on `ValueError: zip() argument 2 is longer than argument 1`).
    """
    spec = importlib.util.spec_from_file_location(
        "migrate_state_to_records", ROOT / "scripts" / "migrate_state_to_records.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    err = io.StringIO()
    with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
        rc = mod.main([])           # dry run: no --write, so nothing can be touched either way
    assert rc == 1, "the script accepted a STATE.md its offsets do not describe"
    assert "SOURCE MISMATCH" in err.getvalue(), (
        f"refused, but not legibly: {err.getvalue()!r} — a bare traceback trains the next reader "
        f"to 'fix' the script rather than re-read the boundaries")


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


def test_no_record_carries_an_invented_date() -> None:
    """FAIL LOUD, NEVER FABRICATE — applied to the ledger's own metadata (review, #504).

    The migration stamped a hardcoded `2026-07-27` on every entry whose header carried no date: 33
    records, including every S1–S18 / D1–D22 entry. `ls` is the only index by design, so those
    sorted wrongly, and the "an undated record cannot be ordered or trusted" pin passed *because
    the date had been invented*. A guessed value that satisfies its own guard is the worst shape
    this repo has a rule against.

    15 were recovered from git history (the first commit containing the entry's text — real data);
    the remaining 21 say UNKNOWN out loud. Either is acceptable; a silent guess is not."""
    for p in _records():
        front = p.read_text().split("---", 2)[1]
        if "date-source: UNKNOWN" in front:
            continue                      # declared unknown — honest
        m = re.search(r"^date:\s*(\S+)", front, re.M)
        assert m, f"{p.name} has no date and does not declare it unknown"
        body = p.read_text().split("---", 2)[2]
        first = next((x for x in body.splitlines() if x.strip()), "")
        if m.group(1) == "2026-07-27" and "2026-07-27" not in first:
            assert "date-source:" in front, (
                f"{p.name} carries the migration's fallback date with nothing saying where it came "
                f"from — that is an invented value presented as a fact")


def test_no_archive_record_claims_to_be_open() -> None:
    """ONE AUTHORITY ON WHAT IS OPEN (review, #504). Five migrated records were stamped `open` from
    their header wording — none of them in §5.0's list, one containing struck-through closed items.
    That is exactly the two-answers failure the ledger exists to end, re-created inside the ledger.

    §5.0 OPEN NOW is the authority. An archive record RECORDS that something was once open; it does
    not assert that it still is."""
    for p in _records():
        front = p.read_text().split("---", 2)[1]
        if "migrated-from" not in front:
            continue                      # a current record may legitimately be open
        assert not re.search(r"^status:\s*open\s*$", front, re.M), (
            f"{p.name} is an ARCHIVE record claiming status open, while §5.0 OPEN NOW is the only "
            f"authority on that — use `recorded`")


def test_every_sd_identifier_has_its_own_record() -> None:
    """AN ENTRY THAT STARTS AFTER AN INLINE ASIDE IS STILL AN ENTRY (review, #504).

    The migration matched `^\\*\\*([SD]\\d+)\\.` — LINE-ANCHORED — and so missed D10, D13 and D14,
    each of which opens `*(scheduling superseded by D19.)* **D14. …`. All three were swallowed by a
    neighbouring record: outside the collision guard, absent from `ls`, and unfindable by filename.

    `tests/test_state_identifiers.py` warns about this exact anchoring in prose, and the migration
    did it anyway — so the property is pinned here rather than left to a comment."""
    ids_in_front, ids_in_text = set(), set()
    for p in _records():
        txt = p.read_text()
        m = re.search(r"^id:\s*([SD]\d+)", txt.split("---", 2)[1], re.M)
        if m:
            ids_in_front.add(m.group(1))
        ids_in_text |= {f"{k}{n}" for k, n in re.findall(r"\*\*([SD])(\d+)\.\s", txt)}
    missing = sorted(ids_in_text - ids_in_front)
    assert not missing, (
        f"{missing} appear as entry HEADINGS but no record claims them in front-matter — they are "
        f"buried inside another record, so `ls` and the collision guard cannot see them")

