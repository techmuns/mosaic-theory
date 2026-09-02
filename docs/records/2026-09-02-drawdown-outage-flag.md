---
id:
status: open
date: 2026-09-02
prs: []
supersedes:
superseded-by:
---

# A degraded drawdown block now says so at the top of the dossier, in the human channel

**WHAT.** `_drawdown_cause` returns `(DrawdownCause, list[str])`. When the EDGAR filing index is
unreadable and the name has gap-down events, it emits one flag:

    drawdown-cause: EDGAR filing index unavailable — N gap-down date(s) carry no attributed cause;
    re-assemble when the feed recovers

`assemble_mechanical` appends it beside the other honest-miss flags. It fires ONLY on a degraded
feed, so no committed artifact moves and no healthy-feed output changes.

**WHY.** #570 made the block degrade to UNKNOWN instead of dropping the name, and that note renders
at the point of use (`_fact` prints `_UNKNOWN_ — <note>`). But a blank cause sitting under a real
price gap is a decision fact, not just a rendering: the reader must be able to tell **"EDGAR was
down, re-assemble"** from **"the company filed nothing"**, which is a FINDING this module states
deliberately. Same role as the `stock-info:` twin of the CMP-row note.

**THE AUDIENCE WAS THE REAL DECISION, and it is pinned rather than commented.** `flags.partition`
routes by PREFIX: anything matching `flags._QA_MARKERS` is hidden (dev/JSON only), everything else
is re-voiced to the human caveat channel. `drawdown-cause:` is deliberately NOT added to that
hide-list, so the flag reaches the analyst. Three things settle it:

- `flags.py`'s own stated default — *"Everything else defaults to a human CAVEAT — fail toward
  transparency, so a newly-added flag is shown to the human, never silently hidden."*
- The QA hide-list is machine-INTEGRITY self-checks (TWIN, DIRECTIONAL, UNCITED, LLM overstep). An
  upstream outage that blanks a decision block is not the machine's discipline, it is the data's
  completeness — the same reason `UNTRACEABLE` is a caveat while `TRANSCRIPT-FIGURE` is QA.
- The contrast case: `operating-drivers:` IS hidden, because a no-driver name is ordinary across the
  fleet and promoting it "would drown the channel". A degraded feed is not ordinary.

`test_the_flag_reaches_the_human_caveat_channel_not_the_hidden_qa_tier` asserts the AUDIENCE, not
the text. Adding `drawdown-cause:` to `_QA_MARKERS` reddens it — hiding this flag must be a
deliberate, visible edit rather than a silent one.

**HOW VERIFIED.** `tests/test_drawdown_filing_index_unavailable.py` grows from 7 to 11 pins, each
mutation-tested (baseline 11 passed):

    F1 flag never emitted           -> 2 failed
    F2 fires on a HEALTHY feed too  -> 2 failed
    F3 wrong count in the flag      -> 1 failed
    F4 flag HIDDEN in the qa tier   -> 1 failed   (the audience pin)

F2 and the two healthy-feed pins matter as much as F1: a flag that fired on a working feed would
appear on every dossier and train the reader to ignore the channel, and a flag that fired when the
company GENUINELY filed nothing would relabel a finding as a degradation.

*Suite:* 3476 passed before, **3480 passed, 132 skipped, 37 deselected** after; `ruff check .`
clean; `mypy --strict vinci` clean (139 files). No committed dossier changes — the condition cannot
fire on a healthy assembly.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

*The flag is on the human decision surface, not the dev tier.* That is a deliberate widening of the
caveat channel: on a degraded run every affected name gains a caveat line. Accepted because the
alternative — a blank cause with no top-level signal — is the absent-and-silent shape the
visible-absence rule prohibits, and because the condition is rare by construction.

*`_drawdown_cause` returns a tuple rather than carrying `qa_flags` on the model.* The model-field
shape (`CatalystCalendar`, `OperatingDriversExtract`) would add a key to every committed
`dossier.json` for a condition that fires only on a degraded feed. The tuple keeps the artifact
untouched; there is exactly one production caller.

*Not done:* the flag is not deduplicated against the rendered UNKNOWN note — the reader sees both,
which is the intent of a "loud twin", and matches how `stock-info:` already behaves.
