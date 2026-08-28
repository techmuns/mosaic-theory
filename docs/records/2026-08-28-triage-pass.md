---
id:
status: shipped
date: 2026-08-28
prs: [515]
supersedes:
superseded-by:
---

# The de-rating events have a document now — 275 of 525, and the item code names the cause for 171

**THE COST GATE SAID YES, AND SAID SOMETHING MORE USEFUL THAN A PRICE.** Every queued name's
`cause_class` reads UNCLASSIFIED, and the reason was never budget: all 525 events come from the EOD
gap-down detector carrying `accession: null, detail: null`. `vinci/rank/cause.py` says so in its own
docstring — its LLM pass needs "the de-rating text wired onto events" before it can run at all. So
the gate did not time an LLM. It measured whether a document is reachable, and at what cost:

    268 names · 71 seconds · 0 LLM calls · $0

**WHAT A MECHANICAL PASS CAN SAY**, over all 525 events at ±1 day:

    named    171/525  (33%)  the item code names the cause — deterministic
    opaque   104/525  (20%)  a document exists, its code names no cause — THIS is the LLM tier
    dark     250/525  (48%)  no filing within a day — dark either way

The top of the queue is better documented than the tail: the first 25 names read 44/23/33. Worth
knowing before anyone extrapolates a sample.

**THE LLM TIER IS 20%, NOT 100%.** That is the finding. This repo's rule is structured-value
determinism where the facts are verbatim, with an LLM reserved for a COVERAGE-EVIDENCED escalation;
an 8-K item code is a filed value — 2.02 results, 4.02 non-reliance, 1.03 bankruptcy — so a third of
the queue's causes need no model at all, and the escalation now has a measured size instead of an
assumed one.

**IT SCORES NOTHING, DELIBERATELY.** An item code names the EVENT ("this was an earnings release"),
never its CHARACTER ("this is a mean-reversion candidate"). The first is filed; the second is an
inference, and mapping 2.02 to a `CauseClass` would reach the ranker's character axis — a
decision-path change made on a code that never claimed it. Pinned structurally: no module in the
decision path may import `vinci.triage`.

**THREE DEFECTS IN THE FIRST CUT, ALL FOUND BY RUNNING IT.**

1. **9.01 counted as a cause, and it inverted the result.** "Financial Statements and Exhibits" is
   an attachment marker riding along with most 8-Ks; it read as the single strongest signal (17 of
   22 events) — excellent apparent coverage, entirely an artefact.
2. **The first filing in the feed, not the nearest.** Submissions order is newest-first, so `[0]`
   returned whichever 8-K the company most recently filed inside the window. On HTZ's seven gap-downs
   that is a different filing for most of them — a real accession for the wrong event, worse than
   none.
3. **Blind to foreign issuers.** FVRR files zero 8-Ks and 57 6-Ks; so do QFIN, BAK and SLI — four of
   the first 25 queued names, reading as "no document exists" when the document was on the other
   form. Adding 6-K recovered 5 of 26 dark events. A 6-K carries no item codes, so it lands in the
   read-required tier: recovered, never promoted.

**VERIFIED.** 9 pins, 7 mutations caught. Two survived the first cut and both were test gaps rather
than code gaps: the 6-K case used empty items so it never exercised the form check, and the dark
case asserted the tier without asserting the fields were empty — a mutation leaking the
out-of-window accession and its cause into a row labelled `dark` passed. Both closed, both then
caught. Three generated SEC URLs fetched: HTTP 200, including a 6-K.
