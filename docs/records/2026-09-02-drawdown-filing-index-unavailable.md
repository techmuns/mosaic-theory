---
id:
status: shipped
date: 2026-09-02
prs: [570]
supersedes:
superseded-by:
---

# An unreadable filing index is not the finding "the company filed nothing" — the drawdown block degrades to UNKNOWN instead of dropping the name

**WHAT.** `_drawdown_cause` (`vinci/dossier/mechanical.py`) now catches `HttpError` from
`_drawdown_filings` and carries the failure as its own state. When the lookup fails, `shape` is
`Sourced.unknown` with a note naming the outage, and `revised_guidance`'s note distinguishes "the
index was unavailable" from "no catalyst 8-K to follow". The gap-down DATES are unaffected — they
come from the data-record's own events, not from EDGAR, so an outage never put them in doubt.

**WHY.** This was the one submissions call site of 13 with no handler, and `_drawdown_cause` runs it
FIRST in `assemble_mechanical`. On a degraded feed a name carrying `earnings_gap_down` events — 9 of
17 committed dossiers (AORT, BRBR, CNXC, EPAM, FUBO, MVST, SMPL, VITL, VRRM) — raised out of the
whole assembly. `assemble_cohort`'s per-name `task` caught it and returned `(None, "<T>: HttpError:
…")`, so the run survived and the name **silently produced no dossier at all**.

**THE OBVIOUS FIX WOULD HAVE BEEN WORSE THAN THE BUG.** Wrapping the call and returning `[]` makes
the block fall through to `f"{gd.isoformat()} no company filing"` for every gap date. That string is
chosen deliberately — the comment beside it reads "state the WORLD, not our process: a hard fall on
a day the company filed nothing is itself a finding (it points away from company news), not a tooling
miss". Returning `[]` on an outage would therefore publish a **fabricated finding about the issuer**
on a rendered decision surface, in a run that is already degraded, with the suite green. That is the
fail-loud-never-fabricate rule exactly, and it is why this fix needed a distinct failure state rather
than a bare `except`.

**HOW VERIFIED.** `tests/test_drawdown_filing_index_unavailable.py`, 7 pins, each mutation-tested —
the pins were shown able to fail before being believed (baseline 7 passed):

    N1 revert the fix (raise again)     -> 4 failed
    N2 THE DANGEROUS FIX (swallow -> []) -> 2 failed
    N3 outage renders as a normal claim -> 1 failed
    N4 revised_guidance note collapsed  -> 1 failed

N2 is the one that matters: the pin set specifically refuses the plausible-looking fix, not merely
the original bug. Both healthy paths are pinned beside the degraded one — a readable feed that finds
a filing still attributes the gap, and a readable feed that genuinely finds nothing **still says "no
company filing"**, so the fix cannot suppress a real signal everywhere to satisfy the outage pins.

*Suite:* 3447 passed before, **3455 passed, 132 skipped, 37 deselected** after; `ruff check .` clean;
`mypy --strict vinci` clean (139 files).

**WHAT IT COSTS / WHAT IS ACCEPTED.**

*A behaviour change, deliberately.* Names that vanished from a degraded cohort now appear WITH a
dossier whose drawdown cause is UNKNOWN. That is the intended trade: a present record marked unknown
is auditable, an absent name is not. No healthy-feed output moves — the three healthy paths are
pinned.

*The `qa_flags` surface is untouched.* A degraded drawdown block is visible as an UNKNOWN with its
note, not as a flag. Whether an EDGAR outage should also raise a qa_flag is a separate judgment and
was not made here.

**WHAT THIS CLOSES.**

- **STATE.md §5.0 row 12 is STRUCK** — the accepted risk it recorded is resolved.
- `docs/records/2026-09-02-submissions-memo.md` gains an `## Amendments` entry: the submissions
  memo's measured 187.4 s → 15.5 s now applies to every name, not the no-gap subset.
- **The accepted-risk pin from #569 did not fire, and was replaced.** It asserted the absence of a
  `try` INSIDE `_drawdown_filings`; the correct fix wraps the call one frame up in `_drawdown_cause`,
  so it stayed green while the risk it guarded disappeared — row 12 would have rotted silently. It
  pinned a SHAPE rather than a PROPERTY. Its replacement asserts that an `HttpError` cannot escape
  the drawdown path, and was mutation-tested against a revert. *This is the TEST-LAYER RULE's own
  failure mode, caught one build later: a structural assertion about where code sits is not a pin on
  what the code does.*
