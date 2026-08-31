---
id:
status: shipped
date: 2026-08-31
prs: [522]
supersedes:
superseded-by:
---

# Sweep clock + flag kind — two review fixes to the theme falsifier sweep

**WHAT.** Two CONFIRMED findings from the 2026-08-31 medium review of the first-thesis-card PRs,
both in the sweep shipped by the falsifier-sweep build — latent until a card existed, armed the
moment one did:

1. **The sweep ran on the wrong clock.** `_cmd_monitor` swept with `today=ref` (the calendar
   date) while the snapshot it writes is stamped `as_of=now_date` (last trading day) — the
   anchor every other as-of computation in that function uses. A weekend run could commit
   `deadline_passed: true` into a day file dated BEFORE the deadline: an immutable as-of
   artifact asserting a window closed after its own date. The exact run shape occurred (a
   Sunday run keyed to Friday's file) before any deadline was close enough to mislabel. Now
   `today=now_date`, source-pinned both ways (the ref form is asserted ABSENT).
2. **A passed FIRST-CONFIRMING was indistinguishable from a passed falsifier.** The
   passed-deadline render branch dropped `tf.kind`, printing every closed window as
   `⚑ <trigger> — deadline <d> PASSED → re-underwrite due`. The first declared card (confirming
   due 2026-12-15) would have printed its confirmation window closing under falsifier wording
   the day it passed. The kind now LEADS the flag (`⚑ first-confirming: …` / `⚑ falsifier: …`),
   and a render pin runs the sweep past the confirming deadline and asserts both kinds visible
   in one output. The flag wording itself is unchanged — flag-only, never adjudication.

**WHY.** Both are the recorded-criterion class the sweep exists to end, one level up: a flag
computed on a different clock than its artifact, and a flag that hides which criterion closed.
The existing pins covered a passed falsifier only — the wording pin was updated (kind-led) and
the confirming case pinned, per the INVARIANT rule.

**HOW VERIFIED.**
- `tests/test_theme_falsifier_sweep.py`: the updated wording pin, the new
  `test_a_passed_first_confirming_flags_with_its_kind_visible` (sweep run at 2026-12-16, both
  kinds asserted in one render), and the extended source pin on `_cmd_monitor`
  (`today=now_date` present, `today=ref` absent).
- ruff clean, `mypy --strict` clean on both touched modules; full offline suite green, exit 0.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- Committed monitor days keep whatever the run wrote — nothing rewrites history; the clock fix
  governs runs from here forward. No committed day carries a mislabeled flag (verified: every
  committed day's `theme_falsifiers` is empty).
- The pending-row render already carried the kind; only the passed branch changed. The
  scenario-side `passed_trigger_deadlines` flag lines are analyst-composed strings and carry
  their own context — untouched, deliberately.
