---
id: 
status: recorded
date: 2026-07-28
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**REVIEW FINDING — 2026-07-28 THE LIVE QUEUE HAS TWO COLLIDING NUMBER SERIES. This is the
concrete brief for the queued STATE-topology work; it is NOT a formatting nit.** Found reviewing
#240. Inside ONE continuous list, with **no separating heading**, item 24 (ANALYST-DECISION
BUCKET) is followed directly by a SECOND series restarting at 16 (CIQ ESCALATION — VITL). So
numbers **16–27 appear TWICE with entirely different meanings**: "item 22" resolves to either the
**VISIBLE-ABSENCE RULE** or **"Full STATE split"** depending on which occurrence a reader hits —
and the operator has been using the FIRST series' numbering in conversation all week, while the
SECOND series' item 22 is literally the task to fix this. HONESTY ABOUT AUTHORSHIP: the collision
PRE-DATED the audit work (both series already contained a 16), but the audit-derived additions
(17–27) **widened it from one colliding number to twelve**. **UPDATED 2026-07-28 — NOW FOURTEEN**:
#244 adds items **29** (bull-leg constraint) and **30** (type-check `tests/`), and §Next-steps
already holds a 29 (NCI TERM FOR THE R2 ENGINE) and a 30 (IR-DOCUMENT INGESTION TIER). The
colliding set is now `16–26, 28, 29, 30`. Recorded rather than avoided: renumbering to dodge the
clash would scatter the audit series, and the topology work is two slots away. Also within the first series, physical
order now reads `… 22, 23, 25, 27a, 27b, 26, 24` — 24/25/26 are out of sequence because successive
insertions anchored on convenient text rather than maintaining order. RECOMMENDATION for the
STATE-topology slot: prefix the audit-derived items (`A17`…`A27`) or relocate the older series
behind its own heading, then re-sequence; either removes the ambiguity permanently. **Recorded
rather than fixed here — re-sequencing a 4,000-line file inside a docs PR under review is the
scope creep this repo keeps refusing, and the work is already queued.**
