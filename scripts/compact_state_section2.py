"""Move §2's OVERSIZED capability entries into records, leaving the summary and a pointer.

WHY. §2 carries a documented convention — a one-line summary in the snapshot, the detail in a
record with a `*(detail: …)*` pointer — and NOTHING ENFORCES IT. Measured 2026-09-01: 14 of 91
bullets run >= 21 lines and hold 459 lines, 45% of §2 in 15% of its entries. The largest is 70.
Three of the 14 already carry a pointer, so their detail is duplicated, not relocated.

The only guard was the whole-file cap (2,100, `test_records_ledger.py`), which fires hundreds of
lines downstream and lands on whichever build happens to be last — STATE.md sat at 2,095 with five
lines of headroom. A cap on the total cannot tell a 3-line capability summary from a 70-line build
narrative; that is what the per-entry pin shipped alongside this is for.

RECONSTRUCTION IS THE PROOF, as in P3: every migrated block, concatenated back in order, must
reproduce the source span byte-for-byte. This refuses to write anything if it does not.

    python scripts/compact_state_section2.py --dry-run
    python scripts/compact_state_section2.py
"""

from __future__ import annotations

import datetime as dt
import hashlib
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

STATE = ROOT / "STATE.md"
RECORDS = ROOT / "docs" / "records"

#: A bullet at or above this many lines is a NARRATIVE, not a summary, and its detail belongs in a
#: record. Chosen from the live distribution rather than an ideal: median 6, mean 11, p90 23. At 21
#: the cut takes the 14 entries that hold 45% of the section and leaves every genuine summary alone.
THRESHOLD = 21

#: The pointer line §2 already uses. Matched, never re-invented — `test_records_ledger.py`
#: (`_pointer_pairs`) parses this exact shape to prove every pointer resolves.
POINTER = "  *(detail: `docs/records/{name}`)*"


def bullets(body: list[str]) -> list[tuple[int, int]]:
    """(start, end) for every top-level `- **…` bullet in the section body."""
    idx = [i for i, line in enumerate(body) if re.match(r"^- \*\*", line)]
    return [(i, idx[j + 1] if j + 1 < len(idx) else len(body)) for j, i in enumerate(idx)]


def title_of(block: list[str]) -> str:
    """The bolded title, which may WRAP across several lines — `- **A\\n  B**` is one title."""
    text = "\n".join(block)
    m = re.match(r"^- \*\*(.+?)\*\*", text, re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else block[0][2:].strip()


def slugify(text: str, limit: int = 52) -> str:
    text = re.sub(r"[`*~#\[\]()]", " ", text)
    text = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    return text[:limit].rstrip("-") or "entry"


def summary_lines(block: list[str]) -> list[str]:
    """The lines the SNAPSHOT keeps: the bolded title, rewrapped, and nothing else.

    Deliberately not "the first N lines" — a title that wraps would be cut mid-sentence, and the
    prose after it is exactly the detail being moved.
    """
    title = title_of(block)
    out, line = [], "- **"
    for word in title.split():
        if len(line) + len(word) + 1 > 98:
            out.append(line)
            line = "  " + word
        else:
            line = f"{line}{word} " if line.endswith(("**", " ")) else f"{line} {word}"
    out.append(line.rstrip())
    out[-1] += "**"
    return out


def main(argv: list[str]) -> int:
    dry = "--dry-run" in argv
    lines = STATE.read_text().splitlines()
    s = next(i for i, x in enumerate(lines) if x.startswith("## 2."))
    e = next(i for i, x in enumerate(lines) if x.startswith("## 3."))
    body = lines[s:e]
    source_sha = hashlib.sha256("\n".join(body).encode()).hexdigest()

    big = [(a, b) for a, b in bullets(body) if b - a >= THRESHOLD]
    if not big:
        print("  nothing over the threshold")
        return 0

    # ---- RECONSTRUCTION: the blocks plus the gaps must rebuild the section exactly -------------
    rebuilt, cursor = [], 0
    for a, b in big:
        rebuilt.extend(body[cursor:a])
        rebuilt.extend(body[a:b])
        cursor = b
    rebuilt.extend(body[cursor:])
    if hashlib.sha256("\n".join(rebuilt).encode()).hexdigest() != source_sha:
        print("RECONSTRUCTION FAILED — the split does not reproduce §2. Nothing written.",
              file=sys.stderr)
        return 1

    today = dt.date.today().isoformat()
    written, saved, out_body, cursor = [], 0, [], 0
    for a, b in big:
        block = body[a:b]
        title = title_of(block)
        name = f"{today}-s2-{slugify(title)}.md"
        existing = re.search(r"\*\(detail: `docs/records/([\w.\-]+\.md)`\)\*", "\n".join(block))
        record = RECORDS / name
        text = (
            "---\nid:\nstatus: recorded\n"
            f"date: {today}\nprs: []\nsupersedes:\nsuperseded-by:\n"
            "migrated-from: STATE.md §2 (capability entry, compacted)\n"
            "date-source: the migration date — the capability is older and is dated in the body\n"
            "---\n\n"
            f"# {title}\n\n"
            "*The one-line summary stays in STATE.md §2 with a pointer here. This is the detail "
            "that stood beneath it, verbatim.*\n\n"
            + "\n".join(block) + "\n"
        )
        out_body.extend(body[cursor:a])
        keep = summary_lines(block)
        keep.append(POINTER.format(name=existing.group(1) if existing else name))
        out_body.extend(keep)
        cursor = b
        saved += len(block) - len(keep)
        if existing:
            # Detail already lives in a record — this block was a DUPLICATE. Do not write a second
            # copy; just collapse it back to summary + the pointer it already had.
            written.append((None, existing.group(1), len(block) - len(keep)))
            continue
        if not dry:
            record.write_text(text)
        written.append((name, None, len(block) - len(keep)))
    out_body.extend(body[cursor:])

    new_state = lines[:s] + out_body + lines[e:]
    print(f"  §2: {len(body)} -> {len(out_body)} lines   (-{saved})")
    print(f"  STATE.md: {len(lines)} -> {len(new_state)} lines")
    for name, dup, n in written:
        print(f"    -{n:>4}  {'DUPLICATE of ' + dup if dup else name}")
    if dry:
        print("\n  --dry-run: nothing written")
        return 0
    STATE.write_text("\n".join(new_state) + "\n")
    print(f"\n  wrote {sum(1 for n, d, _ in written if n)} records; "
          f"{sum(1 for n, d, _ in written if d)} were duplicates and were collapsed only")
    return 0


if __name__ == "__main__":
    os.chdir(ROOT)
    raise SystemExit(main(sys.argv))
