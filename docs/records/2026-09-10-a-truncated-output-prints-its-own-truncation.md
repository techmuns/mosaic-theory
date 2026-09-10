---
id:
status: recorded
date: 2026-09-10
prs: []
supersedes:
superseded-by:
---

# A truncated output prints its own truncation — the rule, and two live instances in the renderer

**WHAT.** The 2026-09-10 sampling error is now a rule in CLAUDE.md and a machine check on the two
places in `vinci/` that had the same shape. **The mechanism is worse than sampling: a sample knows
it is a sample.** A print of the first 3 of 5 carries no signal that it is partial — and the count
being right beside it is what made the partial body convincing.

*"GLP-1 mentions: 5"* was correct. Three were printed. The conclusion — *"no profit statement"*,
*"not determinable from these filings"* — was contradicted by the 4th and 5th, and reached a merged
record before it was caught. **Same family as EVERY COUNT STATES ITS BOUNDARY: the population was
there, it just was not stated.**

## Two instances in `vinci/panels_render.py` — one with a corpus witness, NEITHER yet rendered

**Scope stated before the numbers, because "live" would overclaim.** STATE row 5 records that
**nothing consumes `panels_render` yet** — no emitter, no frontend grid. So the DATA condition is
present on the committed corpus today, and no human has been shown a wrong panel. This is the good
case: the defect was found in the window between writing the renderer and wiring it.

**1. The form-mix bars — the corpus witness.** `payloads_for` counted every filing's form, drew the top **5**, and
said nothing about the rest. **TECX carries 8 form types over 26 filings**: the panel drew 5 bars
covering 22 filings, and the chart read as the whole mix. Real run, real committed dossier, through
the real renderer:

```
…<span class="bval">2</span></div></div>
<p class="sub">showing 5 of 8 form types (22 of 26 filings)</p>
```

**2. The filing-watch timeline.** `_timeline` drew at most **4** *"filed since"* dots. **The panel's
entire purpose is how far behind the evidence is**, so a nine-filing gap rendered identically to a
four-filing one — the one place where understating the count defeats the panel rather than merely
abbreviating it. It now carries `+5 more / of 9 filed since`.

Both constants are named (`_FORM_BARS`, `_TIMELINE_DOTS`) so the drawn count and the stated count
cannot drift: a hardcoded *"showing 5 of"* would **lie** rather than break when the limit changes,
and one pin reads both numbers back out of the rendered body to stop exactly that.

## HOW VERIFIED

**Mutation-tested against a revert of both fixes**, not merely run green: restoring the two original
truncations turns **3 pins red** — the timeline pin, the corpus pin, and the off-by-one at 6 types.
The two NEGATIVE pins stay green under the revert by design, since they assert silence.

**The corpus pin cannot pass vacuously.** It asserts that some committed dossier actually overflows
the bars, and fails with a message naming TECX's 8-over-26 if none does — a pin that would go quiet
the day the corpus stopped containing its own test case is a pin on nothing.

**A near-miss worth recording, because it is the same error again.** A first pass at "is this live?"
scanned committed dossiers for `freshness.newer_filings` and reported **max 0**, which reads as
*"the timeline truncation is latent."* It was a **KEY-MISS, not an empty list** — `freshness` is a
runtime structure from `vinci/monitor.py`, absent from `dossier.json` entirely. Checking the key
path before believing the count is what caught it, and the timeline case is therefore **unproven
from disk**, not proven absent.

## The asymmetry this leaves, recorded because it governs future dispositions

**A NAME CAN BE GATED ON FILINGS ALONE, BUT NOT CLEARED ON THEM.** Agilent's zero across six
vocabularies in 119,719 words disposes of it *on the filing record* — and its comparator WAT
disclosed GLP-1 only on calls, with its 10-Q reporting blended. Absence of disclosure is evidence
about disclosure. A figure found in a filing is dispositive; a figure not found there is dispositive
only against the prong that requires one, and never against the exposure itself.

## The read-out headline, so the memo does not undersell a working screen

**The picks-and-shovels leg closing at WST alone is NOT a null result.** The validator ran, the
basket froze, and **four names were disqualified on their own disclosures, each failing
differently** — BDX on counts, WAT on a rate with no base, MCK neutral, CAH *"not meaningful"*, COR
**dilutive**. Three distributors, three distinct mechanisms; **no analogy would have reached any of
them**, which is the screen doing its job rather than a screen finding nothing.

**The honest headline: the driver is probably real and the fund can express it through one name —
a finding about TRADABILITY, not about the thesis.**

**BOUNDARY.** Population: all committed `data/dossiers/*/dossier.json` (18 at this commit) rendered
through `payloads_for`; the corpus instance is TECX, 8 form types over 26 filings. `_FORM_BARS = 5`,
`_TIMELINE_DOTS = 4`. Mutation: both truncations reverted, 3 of 6 pins red. Vocabulary counts for
Agilent (6 vocabularies / 119,719 words) are restated from
`docs/records/2026-09-10-cor-gated-agilent-unsized-from-edgar.md`, not re-measured. Measured
2026-09-10.

**WHAT IT COSTS / WHAT IS ACCEPTED.** **The timeline fix is unproven on real data** — no committed
artifact carries `freshness`, so its pin runs on constructed input while the form-mix pin runs on the
corpus. Stated rather than papered over: one of the two fixes has a corpus witness and one does not.
**And the rule is a RULE, not a guard** — nothing scans for a new unstated `[:N]`, because the sites
that matter are the ones a human or an LLM reads as a whole, and that is a judgement no lint makes.
**Falsifier: a third instance shipping after this date** — at which point the judgement has failed
twice and the sweep becomes worth its false positives.
