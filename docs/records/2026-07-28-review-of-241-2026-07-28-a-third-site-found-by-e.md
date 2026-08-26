---
id: 
status: recorded
date: 2026-07-28
prs: [241]
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**REVIEW OF #241 — 2026-07-28. A THIRD SITE, found by enumerating consumers instead of trusting
the fix.** After the build already corrected itself once (one consumer → two), the review asked the
only question that pattern justifies: **how many consumers of `_multiples_close` are there?** NINE.
Classified rather than assumed:
· **`ev_ebitda_current`** — filters and takes `[-1]`, but `ev_ebitda_asof` filters IDENTICALLY, so
its value and its date MOVE TOGETHER and the pair stays honest even when the last cell is NM. SAFE
BY DESIGN, and the design is deliberate (asof's docstring exists "so the caller can judge whether
that 'current' multiple is stale").
· **`midcycle.py:464`** — sorts the series for min/median/upper-quartile. Filtering absences is
CORRECT for a band aggregate. NOT a defect.
· **`_latest_common_multiples`, `own_history_bands`** — date-anchored. Fine.
· **`ev_ebitda_percentile` — THE SAME DEFECT, LATENT.** `current, history = series[-1], series[:-1]`
on a FILTERED list, and this reading has **no as-of anywhere** (its source_ref names a quarter
COUNT, not a date), so a stale "current" would be ranked against its own history with nothing on
the page to reveal the substitution. FIXED: refuse with a stated reason when the latest cell is NM.
Latent today — no committed name has an NM latest TEV/LTM EBITDA, and all five spot-checked names
are unchanged — so it is PINNED SYNTHETICALLY rather than waiting for a real name to go NM, which
is how it would otherwise have been discovered. Mutation-tested (revert the fix ⇒ CAUGHT).
**THE LESSON, worth more than the fix:** item 20's spec was "no backward-fill on ANY time series",
and the first two cuts each fixed the consumer in front of them. Enumerating the CALL SITES of the
shared reader — not the readings — is what found all of them. Gate: ruff + `mypy --strict` clean ·
**1140 passed**.
