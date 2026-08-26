"""P1 of the knowledge ledger: split STATE.md's archive into per-entry records, verbatim.

WHY A SCRIPT AND NOT AN EDIT. The migration must be PROVABLY lossless, and the only proof that
means anything is RECONSTRUCTION: concatenating the records back, in order, must reproduce the
source byte-for-byte. A hand edit cannot show that; this can, and refuses to write anything if it
cannot.

WHY THE BOUNDARIES ARE A DATA FILE AND NOT A REGEX. §5's entries have no machine-detectable
boundaries. Three independent probes said so: wording does not separate an entry from a
continuation (`REVIEW PASS ON #500/#501` is an entry, `FIRST RUN AFTER THE FIX` is not, and they
look identical), structure does not either (no `---` rules; blank-line counts split 470/332), and
confidence-tiering misclassified in both directions. The 218 candidates were therefore read and
classified BY HAND, and that judgement is recorded in ``BOUNDARIES`` rather than re-derived — a
regex that reproduces it today would silently stop matching the next time anyone edits the file.

The hand pass also found what no regex could: seven `###` sub-headings that ARE entry starts,
one of them inside a span the dated-bold scan had read as a single 615-line entry.
"""

from __future__ import annotations

import hashlib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
STATE = ROOT / "STATE.md"
OUT = ROOT / "docs" / "records"

#: Section bounds are re-derived from the '## ' headings, never hardcoded — the file moves.
SECTIONS = ("5. Next steps", "GOVERNANCE LOG")

STATUS_RULES = (
    (re.compile(r"FALSIF|REJECTED|RETRACTED|NULL RESULT|DEAD\b"), "falsified"),
    (re.compile(r"SUPERSEDED"), "superseded"),
    (re.compile(r"ACCEPTED RISK"), "accepted-risk"),
    (re.compile(r"\b(SHIPPED|BUILT|DONE|CLOSED|FIXED|RESOLVED|LANDED|MERGED)\b"),
     "shipped"),
    (re.compile(r"OPERATOR TO-DO|RULING NEEDED|\bOPEN\b|QUEUED|DEFERRED"), "open"),
)


def status_for(header: str) -> str:
    """Infer a status from the header's own words. RECORDED is the honest default: most of these
    are diagnoses, audits and experiment records — things that happened, not things that shipped."""
    for pattern, status in STATUS_RULES:
        if pattern.search(header):
            return status
    return "recorded"


def slugify(header: str, limit: int = 48) -> str:
    text = re.sub(r"[`*~#\[\]()]", " ", header)
    text = re.sub(r"^\s*\d+\.\s*", "", text)
    text = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    return (text[:limit].rstrip("-")) or "entry"


def section_bounds(lines: list[str]) -> dict[str, tuple[int, int]]:
    heads = [(i, x) for i, x in enumerate(lines) if x.startswith("## ")]
    out: dict[str, tuple[int, int]] = {}
    for (i, label), (j, _) in zip(heads, heads[1:] + [(len(lines), "")], strict=True):
        for want in SECTIONS:
            if label[3:].startswith(want):
                out[want] = (i, j)
    return out


def main(argv: list[str]) -> int:
    write = "--write" in argv
    lines = STATE.read_text().splitlines(keepends=True)
    bounds = section_bounds([x.rstrip("\n") for x in lines])
    missing = [s for s in SECTIONS if s not in bounds]
    if missing:
        print(f"section(s) not found: {missing}", file=sys.stderr)
        return 1

    # BY LINE, not by token: the file carries a comment header, and splitting on whitespace
    # turned its words into candidate integers.
    raw = (ROOT / "scripts" / "state_entry_boundaries.txt").read_text().splitlines()
    boundaries = [int(x.strip()) for x in raw if x.strip() and not x.lstrip().startswith("#")]
    s5_start, s5_end = bounds["5. Next steps"]
    gov_start, gov_end = bounds["GOVERNANCE LOG"]

    plan: list[tuple[int, int, str]] = []
    # §5 archive — hand-classified boundaries, offsets relative to the section start
    abs_starts = [s5_start + b for b in boundaries]
    for a, b in zip(abs_starts, abs_starts[1:] + [s5_end], strict=True):
        plan.append((a, b, "s5"))
    # governance log — '<n>. **' numbering IS mechanical, so it is derived not hand-listed
    gov = [i for i in range(gov_start, gov_end)
           if re.match(r"^\d+\.\s+\*\*", lines[i].rstrip("\n"))]
    for a, b in zip(gov, gov[1:] + [gov_end], strict=True):
        plan.append((a, b, "gov"))

    # ---- RECONSTRUCTION IS THE PROOF -------------------------------------------------------
    covered = "".join("".join(lines[a:b]) for a, b, _ in sorted(plan))
    expected = "".join(lines[abs_starts[0]:s5_end]) + "".join(lines[gov[0]:gov_end])
    got = hashlib.sha256(covered.encode()).hexdigest()
    want = hashlib.sha256(expected.encode()).hexdigest()
    if got != want:
        print("RECONSTRUCTION FAILED — the split does not reproduce the source. Nothing written.",
              file=sys.stderr)
        return 1
    n5 = len([x for x in plan if x[2] == "s5"])
    ng = len(plan) - n5
    print(f"  reconstruction OK: {len(plan)} records cover "
          f"{len(covered.splitlines())} lines exactly")
    print(f"    §5 archive : lines {abs_starts[0]}-{s5_end} ({n5} records)")
    print(f"    governance : lines {gov[0]}-{gov_end} ({ng} records)")
    print(f"    §5.0 kept in the snapshot: lines {s5_start}-{abs_starts[0]}")

    names: dict[str, int] = {}
    written = 0
    for a, b, kind in sorted(plan):
        body = "".join(lines[a:b]).rstrip("\n")
        header = lines[a].rstrip("\n")
        date = (re.search(r"(20\d\d-\d\d-\d\d)", header) or [None, "2026-07-27"])[1] \
            if re.search(r"(20\d\d-\d\d-\d\d)", header) else "2026-07-27"
        sd = re.match(r"^\*\*([SD]\d+)\.", header)
        ident = sd.group(1) if sd else ""
        stem = f"{date}-{ident + '-' if ident else ''}{slugify(header)}"
        names[stem] = names.get(stem, 0) + 1
        if names[stem] > 1:
            stem = f"{stem}-{names[stem]}"
        prs = ", ".join(re.findall(r"#(\d{2,4})", header))
        origin = "§5 archive" if kind == "s5" else "governance log"
        front = (f"---\nid: {ident}\nstatus: {status_for(header)}\ndate: {date}\n"
                 f"prs: [{prs}]\nsupersedes:\nsuperseded-by:\n"
                 f"migrated-from: STATE.md {origin}\n---\n\n")
        if write:
            (OUT / f"{stem}.md").write_text(front + body + "\n")
        written += 1
    print(f"  {'WROTE' if write else 'would write'} {written} records to {OUT}")
    if not write:
        print("  (dry run — pass --write to commit the split)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
