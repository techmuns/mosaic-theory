---
id:
status: shipped
date: 2026-09-02
prs: [571]
supersedes:
superseded-by:
---

# A degraded drawdown block raises a machine flag — hidden, because the block itself already tells the reader

**WHAT.** `_drawdown_cause` returns `(DrawdownCause, list[str])`. When the EDGAR filing index is
unreadable and the name has gap-down events, it emits one flag:

    drawdown-cause: EDGAR filing index unavailable — N gap-down date(s) carry no attributed cause;
    re-assemble when the feed recovers

`assemble_mechanical` appends it beside the other honest-miss flags, and `"drawdown-cause:"` is on
`flags._QA_MARKERS`, so it lands in the **machine tier** (dev/JSON only). It fires ONLY on a degraded
feed, so no committed artifact moves and no healthy-feed output changes.

**WHY A FLAG AT ALL.** #570 made the block degrade to UNKNOWN instead of dropping the name. The
dossier now says so on the human surface, but nothing said so to the *machine* — no counter, nothing
greppable across a batch. A degraded run should be measurable after the fact ("how many names lost
their drawdown cause on 2026-09-02?"), and that is what a machine-tier flag is for.

**THE AUDIENCE WAS THE REAL DECISION — and it went AGAINST the module's default, by operator
ruling.** `flags.partition` routes by PREFIX: anything matching `flags._QA_MARKERS` is hidden,
everything else is re-voiced to the human caveat channel. `flags.py`'s stated default is to SHOW a
new flag — *"Everything else defaults to a human CAVEAT — fail toward transparency, so a newly-added
flag is shown to the human, never silently hidden."* By that default this would have been a caveat:
an upstream outage blanking a decision block is data COMPLETENESS, not machine discipline, which is
the same line that keeps `UNTRACEABLE` visible while `TRANSCRIPT-FIGURE` is hidden.

**Operator ruling 2026-09-02: hide it.** The justification is that the reader is ALREADY TOLD at the
point of use — `shape` degrades to UNKNOWN and `_fact` renders
`- **Shape:** _UNKNOWN_ — EDGAR filing index unavailable…` inside the drawdown block itself (#570).
The human surface is therefore not silent, and promoting the flag would print the same sentence
twice on every affected name of a degraded run. The visible-absence rule is satisfied by the
rendered UNKNOWN, not by this flag.

**That makes the two halves load-bearing together, so they are pinned together.**
`test_the_outage_flag_is_hidden_because_the_block_itself_already_says_so` asserts BOTH that the flag
is hidden AND that the rendered line still names the outage. **FALSIFIER:** if that UNKNOWN note ever
stops rendering, the flag becomes the only signal and hiding it would make the outage silent — the
pin fails at that moment even though the routing is untouched, and the `_QA_MARKERS` entry must then
be removed. The exception is argued in a comment beside the hide-list entry, not left implicit.

**HOW VERIFIED.** `tests/test_drawdown_filing_index_unavailable.py` grows from 7 to 11 pins, each
mutation-tested (baseline 11 passed):

    G1 un-hide it (back to caveat channel)     -> 1 failed
    G2 block stops naming the outage (silent!) -> 2 failed   (the falsifier above)
    G3 flag never emitted                      -> 2 failed
    F2 fires on a HEALTHY feed too             -> 2 failed
    F3 wrong count in the flag                 -> 1 failed

**G2 is the one that earns the ruling.** It proves the hiding is not a bare preference but a
conditional: break the human-surface half and the test refuses the arrangement. F2 and the
healthy-feed pins matter as much — a flag firing on a working feed would appear on every dossier and
train the reader to ignore the channel, and one firing when the company GENUINELY filed nothing would
relabel a finding as a degradation.

*Suite:* 3476 passed before, **3481 passed, 132 skipped, 37 deselected** after; `ruff check .`
clean; `mypy --strict vinci` clean (139 files). The +5 is 4 new pins plus one case from
`tests/test_record_hygiene.py`, which parametrizes over `docs/records/` and so grew by this file.
No committed dossier changes — the condition cannot fire on a healthy assembly.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

*An exception to `flags.py`'s transparency default, taken knowingly.* The module's rule is that a new
flag defaults to visible; this one is hidden. Accepted because the human is told at the point of use,
and pinned so the exception cannot outlive its justification. The risk if that pin is ever weakened:
a degraded run becomes silent on the analyst's surface while the suite stays green.

*`_drawdown_cause` returns a tuple rather than carrying `qa_flags` on the model.* The model-field
shape (`CatalystCalendar`, `OperatingDriversExtract`) would add a key to every committed
`dossier.json` for a condition that fires only on a degraded feed. The tuple keeps the artifact
untouched; there is exactly one production caller.

*Not done:* no batch-level rollup of the flag. Counting degraded names across a run is the obvious
next use of a machine-tier flag, and it is not built here.

## Amendments

**2026-09-02 — review of the stack corrected two claims in the body above.**

1. **"promoting it would print the same sentence twice" was wrong.** `mechanical.py:2773` already
   emits `catalyst: submissions feed unavailable (…) — no print row` for the SAME outage, and
   `catalyst:` is NOT on `_QA_MARKERS` — so the analyst already receives one feed complaint about
   it, phrased differently. Hiding this twin means the human gets no COUNT of how many blocks the
   outage blanked. The hiding still stands (operator ruling), but on the narrower ground that the
   drawdown block itself names the outage at the point of use — not on non-duplication.
2. **The precondition for hiding was FALSE on the web.** `frontend/views/shared/dossier.js`'s
   `whatHappened()` gated the Shape fact on `status === "present"`, so a degraded drawdown rendered
   nothing on the web Brief and page 1 of the PDF — silent there, with its flag hidden, which is
   exactly what this record's FALSIFIER forbids. The helper-level pin could not see it. Fixed by
   removing the gate (the Python twin was always unconditional), and now bound by
   `tests/test_parity_pins.py::test_the_web_brief_renders_a_degraded_drawdown_shape_like_render_py`.

Also corrected: the flag counts DISTINCT dates (`gaps` is not de-duplicated upstream), and its
advice matches the cause — a missing CIK says "resolve the CIK", not "re-assemble when the feed
recovers".
