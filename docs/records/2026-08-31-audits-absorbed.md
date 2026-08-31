---
id:
status: shipped
date: 2026-08-31
prs: [530]
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
`## Amendments`, and a repaired pointer.

**AMENDMENTS ARE APPEND-ONLY, which the first cut of the guard did not check.** Truncating both
versions at `## Amendments` and comparing only what preceded it left everything after that heading
unchecked — an existing amendment could be silently reworded, and an amendment IS a record of a
correction. It also made a mutation look survivable: a sentence appended past that heading reads as
a new amendment, which is what the channel is for. The mutation was invalid, not the guard; the gap
it exposed was real and is closed.

**THE 5-FILE SMPL AUDIT FLATTENED** to `2026-07-28-smpl-*.md`. `ls` is the only index by design, and
a subdirectory is invisible both to it and to `glob("*.md")` — moving the directory intact would
have parked five documents outside the contract inside the very directory that defines it.

**ALSO FIXED IN PASSING:** the SMPL ledger entry cited `docs/audits/2026-07-28-smpl-ic-audit.md`, a
file removed by #236 — a pointer that had been dangling for months. And §5.0 row 5 still opened
"a live $50k/5% GOOGL starter has NO ledger row", which #512 closed; GOOGL now heads the BOOK.

**VERIFIED.** 289 records, every `docs/records/…` pointer in the repo resolves, `docs/audits/` does
not exist. 4 mutations: a mid-body prose edit CAUGHT, an existing amendment reworded CAUGHT, a new
amendment appended ALLOWED, a path repointed ALLOWED — the last also proved live, since this change
repoints paths inside merged records and the guard passes.
