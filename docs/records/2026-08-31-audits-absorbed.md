---
id:
status: shipped
date: 2026-08-31
prs: [540]
supersedes:
superseded-by:
---

# The ledger has one directory, and the rule it claimed to enforce is now enforced

**WHAT.** `docs/audits/` is absorbed: its 14 files are records, and the directory is gone. P0 said
it would happen in P1. It did not happen in P1, P2 or P3 — and the reason turns out to be
structural, not neglect.

**WHY IT KEPT NOT HAPPENING.** Absorbing the files means repairing the citations that point at them,
and 14 of those citations live inside MERGED record bodies. `docs/records/README.md` froze those:
*"rewriting a sentence, deleting a paragraph, 'tidying' — is refused."* So the migration was
blocked by the ledger's own contract, and each phase deferred it rather than break the rule.

**THE CONTRACT NOW HAS A THIRD EXCEPTION, DELIBERATELY NARROW.** A citation whose target MOVED may
be repointed — **the path, never the claim.** A pointer that no longer resolves has already
destroyed what the record was for; repairing it preserves the meaning rather than changing it.

The distinction is enforced by comparison, not by trust: the guard blanks every `docs/…` path in
both versions and refuses the change if anything else moved. So P0's sentence — "`docs/audits/`
remains a second dated-record convention until P1 absorbs it" — **stands exactly as written**,
now false and visibly so, with an appended amendment saying what actually happened. That is the
ledger working: the wrong version stays visible.

**THE GUARD THE README HAS PROMISED SINCE P0 DID NOT EXIST.** The claim that CI "diffs each record
against the merge base" was never true — a record body could be edited and the suite stayed green.
It is real now, and it enforces three permitted changes: a `status:` flip, an appended
`## Amendments`, and a repaired pointer. The front matter is compared too — `status:` is the only
field the README lets change, and a body-only check would have left `date:`/`prs:` editable in
place, which is the exact defect the P0 record had to correct by APPENDING an amendment.

**AMENDMENTS ARE APPEND-ONLY, which the first cut of the guard did not check.** Truncating both
versions at `## Amendments` and comparing only what preceded it left everything after that heading
unchecked — an existing amendment could be silently reworded, and an amendment IS a record of a
correction. It also made a mutation look survivable: a sentence appended past that heading reads as
a new amendment, which is what the channel is for. The mutation was invalid, not the guard; the gap
it exposed was real and is closed.

**AND THE SPLIT HAD TO BE HEADING-ANCHORED, TAKEN ONCE.** `str.split("## Amendments")` reads the
wrong region two ways, both of them live in this repo rather than hypothetical. A record with TWO
such headings — which THIS change created on `2026-08-25-knowledge-ledger-p0.md`, by appending a
new section rather than an entry under the existing one — puts everything after the second heading
outside both comparisons, so the amendment recording this absorption could have been reworded
post-merge with the suite green. And a substring match also fires on the string in PROSE: this
record names `## Amendments` inline while describing the guard, which would have cut its own body
check off at that sentence and left the rest editable forever. The split is now
`^## Amendments$`, `maxsplit=1`, with both cases pinned as mutations.

**THE 5-FILE SMPL AUDIT FLATTENED** to `2026-07-28-smpl-*.md`. `ls` is the only index by design, and
a subdirectory is invisible both to it and to `glob("*.md")` — moving the directory intact would
have parked five documents outside the contract inside the very directory that defines it.

**FLATTENING BROKE THE MANIFEST'S OWN LINKS, AND A `docs/`-PREFIXED SCAN CANNOT SEE IT.** The
audit-of-record indexes its four siblings with RELATIVE links — `[`ic-memo.md`](ic-memo.md)` — which
resolved inside `2026-07-28-smpl/` and resolve nowhere once the files are siblings under new names.
Six links plus eleven backticked filenames, repaired here. The lesson generalises: the repointing
exception blanks `docs/…` paths only, so a bare or relative pointer is NOT repairable after merge —
it has to be fixed in the same change that moves the file, or never.

**ONE POINTER IS LEFT DANGLING, DELIBERATELY.** `2026-07-28-audit-record-…` cites
`docs/audits/2026-07-28-smpl-ic-audit.md` — removed by #236 — across a LINE BREAK, so neither the
repair pass nor the exemption regex sees one path. Repairing it means changing non-path text in a
merged record, which the contract refuses. It is recorded here rather than smuggled through; the
same paragraph in the manifest, which the migration had repointed at the manifest ITSELF (making
"added by #236, removed by this commit" describe the file you are reading), is restored to name the
removed file. A path repair that changes what the sentence CLAIMS is not a path repair.

**ALSO FIXED IN PASSING:** §5.0 row 5 still opened "a live $50k/5% GOOGL starter has NO ledger row",
which #512 closed; GOOGL now heads the BOOK.

**VERIFIED.** 290 records; `docs/audits/` does not exist; every pointer into the migrated files
resolves — `docs/…` paths AND the relative links a `docs/`-prefixed scan cannot see — apart from the
one line-wrapped citation recorded above. 7 mutations: a mid-body prose edit CAUGHT, an existing
amendment reworded CAUGHT, an amendment past a SECOND heading reworded CAUGHT, a body edit hiding
behind the heading named in prose CAUGHT, a `date:` rewritten in place CAUGHT; a new amendment
appended ALLOWED, a path repointed ALLOWED — the last also proved live, since this change repoints
paths inside merged records and the guard passes.
