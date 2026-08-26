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

#: THE DATE STAMPED ON AN ENTRY WHOSE HEADER CARRIES NONE — an IMPUTATION, not a fact. It is
#: named rather than inlined, and every use is COUNTED AND LISTED at the end of the run, because
#: a silent imputation is the failure mode CLAUDE.md names first: the record then asserts a date
#: it does not have, and `ls` — which is deliberately the only index — orders it wrongly.
UNDATED_FALLBACK = "2026-07-27"

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
    source = STATE.read_text()

    # BY LINE, not by token: the file carries a comment header, and splitting on whitespace
    # turned its words into candidate integers.
    raw = (ROOT / "scripts" / "state_entry_boundaries.txt").read_text().splitlines()
    boundaries = [int(x.strip()) for x in raw if x.strip() and not x.lstrip().startswith("#")]

    # ---- THE OFFSETS ARE PINNED TO ONE FILE -------------------------------------------------
    # RECONSTRUCTION PROVES CONTIGUITY, NOT ALIGNMENT: any monotone offset list reproduces the
    # source, so a shifted list splits every entry in the wrong place and still reports OK.
    # And the offsets DO shift on ordinary work — they are counted from the §5 heading, and
    # §5.0 above the archive gains and loses a row every build. One inserted line silently
    # re-cuts all 168 records. So the source is pinned by content hash, and a mismatch is fatal.
    pin = next((x.split(":", 1)[1].strip() for x in raw
                if x.lstrip().startswith("# source-sha256:")), None)
    if pin is None:
        print("state_entry_boundaries.txt carries no `# source-sha256:` pin — refusing to split "
              "against an unidentified STATE.md.", file=sys.stderr)
        return 1
    actual = hashlib.sha256(source.encode()).hexdigest()
    if actual != pin:
        print(f"SOURCE MISMATCH — STATE.md is {actual[:12]}…, the boundaries were read against "
              f"{pin[:12]}…. These offsets do not describe this file (already migrated, or edited "
              f"since). Re-read the boundaries by hand and re-pin. Nothing written.",
              file=sys.stderr)
        return 1

    lines = source.splitlines(keepends=True)
    bounds = section_bounds([x.rstrip("\n") for x in lines])
    missing = [s for s in SECTIONS if s not in bounds]
    if missing:
        print(f"section(s) not found: {missing}", file=sys.stderr)
        return 1

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
    used: set[str] = set()
    stems: list[str] = []
    undated: list[str] = []
    for a, b, kind in sorted(plan):
        body = "".join(lines[a:b]).rstrip("\n")
        header = lines[a].rstrip("\n")
        found = re.search(r"(20\d\d-\d\d-\d\d)", header)
        date = found.group(1) if found else UNDATED_FALLBACK
        if not found:
            undated.append(header[:70])
        sd = re.match(r"^\*\*([SD]\d+)\.", header)
        ident = sd.group(1) if sd else ""
        base = f"{date}-{ident + '-' if ident else ''}{slugify(header)}"
        names[base] = names.get(base, 0) + 1
        stem = base if names[base] == 1 else f"{base}-{names[base]}"
        # THE FINAL stem is what hits the filesystem, so THAT is what must be unique. The
        # counter alone does not give it: slugs are truncated at 48 chars, so a header can
        # slug NATURALLY to `…-2` and overwrite the record that got `-2` from the counter —
        # silently, because reconstruction proved the PLAN and never looked at the disk.
        if stem in used:
            print(f"FILENAME COLLISION on {stem!r} — a record would be overwritten. "
                  f"Nothing further written.", file=sys.stderr)
            return 1
        used.add(stem)
        stems.append(stem)
        prs = ", ".join(re.findall(r"#(\d{2,4})", header))
        origin = "§5 archive" if kind == "s5" else "governance log"
        front = (f"---\nid: {ident}\nstatus: {status_for(header)}\ndate: {date}\n"
                 f"prs: [{prs}]\nsupersedes:\nsuperseded-by:\n"
                 f"migrated-from: STATE.md {origin}\n---\n\n")
        if write:
            (OUT / f"{stem}.md").write_text(front + body + "\n")
    print(f"  {'WROTE' if write else 'would write'} {len(stems)} records to {OUT}")
    if undated:
        # AN IMPUTED DATE IS NOT A FACT. These headers carry no date of their own, so the
        # record's `date:` and its filename are a STAMP, not evidence — surfaced by count and
        # by header so the imputation is reviewable rather than buried in 198 files.
        print(f"  !! {len(undated)} header(s) carry NO date — stamped {UNDATED_FALLBACK} "
              f"and NOT verified. `ls` no longer orders these:")
        for h in undated:
            print(f"       {h}")
    if write:
        # RECONSTRUCTION PROVED THE PLAN, NOT THE BYTES ON DISK. Count what actually landed.
        on_disk = {p.stem for p in OUT.glob("*.md")}
        lost = [s for s in stems if s not in on_disk]
        if lost:
            print(f"  {len(lost)} planned record(s) are not on disk: {lost[:5]}", file=sys.stderr)
            return 1
    else:
        print("  (dry run — pass --write to commit the split)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
