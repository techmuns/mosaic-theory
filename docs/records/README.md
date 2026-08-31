# `docs/records/` — the knowledge ledger

**One dated file per entry. The body is immutable once merged.**

STATE.md is the SNAPSHOT: what is true now, short enough to re-read every session. This directory
is the LEDGER: how it got that way, in full, forever. That is the same split the fund already runs
on its *data* — an append-only ledger beside regenerable snapshots — applied to its knowledge.

## Why it exists

STATE.md grew to 19,209 lines (1.7 MB), doubling every ~4 weeks, because entries were **appended
like a journal but trusted like a snapshot**. Closing an item edited nothing upstream, so the file
came to answer one question two ways. On 2026-08-25 an entry reading `STILL OPEN — the queue has
not actually advanced` sat below a later entry recording that same run green; an agent that had
verified the run itself that morning proposed re-triggering it that afternoon.

Immutable per-entry records make that contradiction **structurally impossible** rather than
procedurally discouraged: a reversal adds a record and flips one status line — it never rewrites
the claim it replaces.

## Naming

    YYYY-MM-DD-<id>-<slug>.md      e.g. 2026-08-25-D23-cohort-split.md
    YYYY-MM-DD-<slug>.md           when the entry carries no S/D identifier

`<id>` is the STATE.md identifier (`S12`, `D22`) when the entry has one, so **every existing
citation stays greppable** — `grep -rl D22 docs/records/` finds it. `ls` sorts chronologically;
there is no curated index, because CLAUDE.md's existence-check rule warns that a hand-maintained
index rots and its gaps re-create the false "not listed → doesn't exist" inference. Discovery is
`ls`, `grep`, and `git log`.

## The header

Every record opens with the same five fields. `status` is the only one that may change after merge.

    ---
    id: D23                      # S/D identifier, or omit
    status: open                 # open | shipped | recorded | falsified | superseded | accepted-risk
    date: 2026-08-25             # when the thing happened, not when the file was written
    prs: [501, 502]              # PRs that carried it
    supersedes:                  # record filename(s) this replaces, or omit
    superseded-by:               # filled in when something replaces THIS, or omit
    ---

## The amendment contract

**The body never changes after merge.** Two things may:

1. **`status:`** — flip it when the item closes, is falsified, or is superseded.
`recorded` is for a diagnosis, audit or experiment — something that happened and was written
down, as distinct from something that shipped.

2. **An appended `## Amendments` section** — dated entries at the end, the house style this repo
   already uses (49 entries in the old STATE.md carry in-place `AMENDED <date>` annotations).

3. **A repaired POINTER** — a citation whose target MOVED may be repointed. The path, never the
   claim. A pointer that no longer resolves has ALREADY destroyed what the record was for; repairing
   it preserves the meaning rather than changing it. Added 2026-08-31, when absorbing `docs/audits/`
   showed the rule as written made a directory rename impossible — the reason that absorption sat
   undone through P1, P2 and P3. The guard enforces the distinction mechanically: it strips
   `docs/…` paths from both versions and refuses the change if anything else moved.

Anything else — rewriting a sentence, deleting a paragraph, "tidying" — is refused by CI, which
diffs each record against the merge base. If a record is wrong, **append the correction**; the
wrong version staying visible is the point. That is Nygard's ADR rule, adapted to how this repo
already writes.

## Where things go

| you are writing… | it belongs in… |
|---|---|
| what is true NOW, in ≤3 lines, with a pointer | `STATE.md` |
| what is OPEN and who owns it | `STATE.md` §5.0 OPEN NOW |
| a build, incident, ruling, falsification, audit | a new record here |
| a rule about HOW to work | `CLAUDE.md` (behavior) |
| a convention, or a coined term's translation | `docs/engineering.md` |
| an operating loop someone follows step by step | `docs/RUNBOOKS.md` |
| a superseded plan, kept for its reasoning | leave it, banner it as a FOSSIL |

## Related conventions this generalizes

- **`docs/audits/`** — ABSORBED 2026-08-31. Its 14 files are records here under their own dates;
  the 5-file `2026-07-28-smpl/` audit flattened to `2026-07-28-smpl-*.md`, because `ls` is the only
  index and a subdirectory is invisible to it. The directory is gone: there is one place to look.
- **`planning/`** — the planning fossils CLAUDE.md already names. Superseded plans, not records.
