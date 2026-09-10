---
id:
status: recorded
date: 2026-09-10
prs: []
supersedes:
superseded-by:
---

# The anchor needs its own check — and an unverified accepted risk is an assumption in a formal coat

**WHAT.** Two rules, from the same session that produced the method they guard.

1. **`docs/RUNBOOKS.md` step 10** — anchor-and-displace makes TODAY'S multiple the reference for
   every R3 leg, so it silently imports whatever the market did that day. **The anchor now needs a
   stated sanity check, not just the displacement a reason.**
2. **`CLAUDE.md`, INVARIANT RULE** — **an accepted risk is a CLAIM.** An unverified one is an
   assumption wearing a formal label, and this build shipped one.

## 1. The anchor

The corroborators do the checking. **A reference that may not GENERATE a target can still DETECT a
distorted anchor** — that distinction is the useful half of the `BASIS MATCH: LIMITED` ruling, and
the reason GOOGL's memo carried three references it explicitly refused to derive from.

**Three classes disqualify a bare current anchor**, each with a live instance from this week's work:

| class | live instance | what current reads |
|---|---|---|
| **post-deal entity** — the denominator changed under the history | **WAT** | 26.4x = 63rd percentile, but the n=38 series is **pre-BD-Biosciences**; the percentile is itself a LIMITED mismatch and the anchor is **unverifiable** |
| **one-off in the denominator** — current EPS is not a run-rate | *(none in the four)* | — |
| **percentile extreme** — anchoring assumes the extreme persists | **MCK** | 19.9x against a 13.1x own median — **95th percentile** |

And where current IS defensible, the check is cheap and should be stated:

| | current | own history | verdict on the anchor |
|---|---|---|---|
| **GOOGL** | 26.03x | median 24.24x, p75 26.75x | between median and p75 — **defensible** |
| **WST** | 36.9x | **37th percentile**, below median | **defensible**, and the conservative direction |

**A distorted anchor is a reason to price off something else, or to state the distortion AS the
binding assumption — never to anchor anyway and displace from it.**

*Two of the four names carried to step 10 would have failed this check.* The method was ratified on
the two that pass it.

## 2. The accepted risk

The ratification build wrote, into a record, that `frontend/dossiers/GOOGL.md` was **knowingly
stale** because refreshing it *"needs a full `vinci dossier assemble`, which re-runs the LLM
synthesis phases"* — and left it for the standing artifact pass.

**Two e2e guards refused that.** `test_analysis_tier_reads_in_decision_order_e2e` and
`test_screening_context_reaches_every_committed_dossier_e2e` render `dossier.md` LIVE from the
committed JSON and compare it back to disk. And the render path they use —
`render_markdown(dossier, card=_read_scenario_card(ticker))` — is **fully deterministic with no LLM
phase**, so the artifact regenerated exactly in one call. **12 lines changed, all four of them the
two stamps and the two method sentences.**

**The risk did not exist.** What existed was an unchecked belief about how the renderer worked,
written in the vocabulary of a deliberate trade-off. **The formal words made it look like a
decision.** An accepted risk must show that the risk EXISTS and that the cheap fix is genuinely
unavailable; "accepted" is a conclusion, not a way to stop checking.

*The same session's two other CI catches point the same way — the register lint rejecting `ratified`
in prose (**"a structured field, not prose"**) and the house label `ANCHOR` (**"state the claim, not
the house label"**), both of which improved the sentence. **Machine checks caught what review did
not**, three times in one build.*

## What this does NOT change

**Anchor-and-displace stands as the standing R3 method.** The addition is a precondition on its
input, not a doubt about its mechanism, and the bull-leg test that established it is untouched:
GOOGL's 26.0x sits **0.03** from current against **0.75** from p75, where a distribution-derived
bull would sit.

**BOUNDARY.** No new measurement. Multiples and percentiles are restated from
`docs/records/2026-09-03-glp1-step10-references-and-bdx-gate.md` (WST/WAT/MCK, n=38 settled
quarter-ends, quarterly basis) and `docs/records/2026-09-10-googl-axis-methods-ratified.md`
(GOOGL, IC memo 2026-08-17 §5). WAT's pre-deal limitation is from
`docs/records/2026-09-10-wat-glp1-base-sized.md`. The CI behaviour is from the 2026-09-10 run of
`pytest -m "not network"` at the ratification commit. Dated 2026-09-10.

**WHAT IT COSTS / WHAT IS ACCEPTED — and this one is checked before it is claimed.** **The anchor
check is a RULE, not a guard**: nothing computes a percentile and refuses an underwrite, because the
three disqualifying classes are not all machine-detectable (a one-off in the denominator is a
judgement about the accounts, not a field). **The cheap fix was looked for and does not exist** —
the percentile half alone would be computable, but a check that catches one of three classes and
stays silent on the other two is worse than a rule, because it would read as coverage.
**Falsifier: an R3 record anchored on a distorted current multiple without stating the
distortion** — at which point the computable half ships and the other two stay in prose.
