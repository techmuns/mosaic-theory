---
id: S2
status: recorded
date: 2026-07-27
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**S2. G3's INPUT IS A SELECTION DISTORTION, not a labelling defect** (operator re-scope). In
`screens/assemble.py`, `cur_price = _close_on_or_before(bars, reference_date)` (days old) and
`cur_eps = annual_eps_as_of(...)` (a filing, up to a YEAR old) are combined into `cur_pe` and
stamped `as_of=reference_date`, which is true of neither; `pe_pctile` inherits it. **DIRECTION:**
stale annual EPS against a current price makes GROWERS look expensive and DECLINERS look cheap,
systematically, in the gate that sets the multiple floor — on an overshoot screen that biases
toward VALUE TRAPS. **TWO HALVES, split deliberately:** the STAMP half (honest labelling, no
outcome change) ships with the screen PR; the BASIS half (a fresher EPS moves G3 outcomes and can
flip names) is its own item with its own fleet before/after. **READ FIRST:** is a fresher EPS
basis even available? And **is this the same surface as the dossier's P/E staleness fix** — if so
that fix was scoped to one consumer rather than the source, making this a recurrence.
