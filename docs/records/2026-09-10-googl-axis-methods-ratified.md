---
id:
status: recorded
date: 2026-09-10
prs: []
supersedes:
superseded-by:
---

# GOOGL's two axis methods are ratified — scoped to the fundamental horizon, with one gap left open

**WHAT.** `scenarios/GOOGL.json` now carries `ratified: 2026-09-10` / `ratified_by: analyst` on both
`assumptions.earnings` and `assumptions.multiple`, and both method sentences are restated. **§5.0 row
20 is closed.** The verdict was not touched: **ratio 2.4299, gate PASS, `verdict.status: confirmed`,
spot $339.35 as of 2026-08-31 — byte-identical before and after.**

## The diagnosis changed what got written — three times

**1. Methods A and B are NOT this record's earnings axis.** They are the **March-2027 TRADE-horizon**
denominator constructions (annual day-weight `306/366 = 83.6066%` FY27 + `16.3934%` FY28, versus
annual-constrained FY27-seasonality). **This record is the FUNDAMENTAL horizon** — bear
`$315.454 = 15.388 × 20.5x`, base `$397.4145 = 16.221 × 24.5x` — whose denominator is §4's **Street
target-period construction**: controls `$16.02–16.07`, point lock **`$16.0445`**, legs struck around
it on a common diluted-share basis. **No day-weighting anywhere in it.** Writing "day-weighted annual
accrual" into this axis would have attached one horizon's method to another's numbers.

*The record already knew: `2026-09-01-r3-reaches-the-create-path.md` states "this 1.69x is the
FUNDAMENTAL asymmetry on the ~Aug-2027 horizon; the ledger row's ~1.21–1.25x is the TRADE asymmetry
on its own clock."*

**2. The mislocated phrase is struck.** The memo attaches *"single binding valuation assumption"* to
the **TRADE** bear's ~26x → 22x compression (Decision Card, and again at the end of §7B). The
scenario record's multiple prose and STATE row 20 both attached it to **20.5x**. Fixed in the record
before ratification, because ratification would have sealed it.

**3. The 20.5x reason is recorded as MISSING, not supplied.** Base 24.5x and bull 26.0x are
**identical across both horizons**; only the bear differs — 20.5x fundamental against 22.0x trade —
and **the memo gives no reason.** §7A presents 20.5x in a table with no accompanying justification.
It is ratified as judgment with the gap named. **Authoring a justification would manufacture support
for the leg that sets the risk denominator on a record already at gate PASS** — the shape
`IRR_FLOOR`'s own docstring forbids: *"the easiest possible place to manufacture a pass. NOT tuned
on outcomes."*

## The multiple axis is ANCHOR-AND-DISPLACE, and the bull leg proves it is not derived

Every leg is a displacement from the **verified current normalized P/NTM ~26.03x**: bull 26.0x holds
it, base 24.5x compresses one notch on duration, bear 20.5x de-rates substantially. Consistent with
the memo's mechanism — bear EPS `$15.388` **exceeds** today's NTM `$13.28698`, so the entire bear
outcome is a de-rating rather than an earnings fall.

**The trap, and the test that clears it.** Base 24.5x sits beside own-median 24.24x and bull 26.0x
beside p75 26.75x — proximity that invites a reader to infer the derivation the memo forbids. **The
memo forbids it three times** (§5 *"valuation context, not load-bearing evidence supporting 22x /
24.5x / 26x"*; §9 *"the historical P/E percentile therefore cannot be load-bearing"*; §C *"context
only"*) and derives no multiple from any percentile anywhere.

**Bull settles it: 0.03 from current, 0.75 from p75.** A distribution-derived bull would sit at p75.
The base/median proximity is coincidental corroboration.

## Ratification scope, stated so it cannot creep

| ratified | NOT ratified by this |
|---|---|
| fundamental horizon (~Aug-2027) earnings: Street target-period construction | Method A / Method B (trade-horizon denominators) |
| fundamental multiples **20.5x / 24.5x / 26.0x** | the **22.0x** trade bear |
| the anchor-and-displace mechanism | the verdict — untouched, PASS/confirmed stands |

## Prior ratification — checked on five surfaces before writing

`scenarios/GOOGL.json` (null ×2) · `scenarios/archive/GOOGL-2026-08-17.json` (null ×2) ·
`frontend/scenarios/GOOGL.json` and `…-2026-08-17.json` (`unratified: true` ×2 each) ·
`frontend/dossiers/GOOGL.md` (*"DRAFT — not ratified by the analyst"* ×2) ·
`git log --all -S'"ratified": true' -- scenarios/GOOGL.json` (no commit ever set it). **Positive
control: BRBR / IT / SMPL / WERN carry the field**, so absence was outstanding work, not a schema
artifact.

## What this makes standing for R3 — which is what WST inherits

`docs/RUNBOOKS.md` step 10 now names **anchor-and-displace as the standing R3 multiple method**, with
the corroboration rule, the bull-vs-p75 tell, and the rule that a missing displacement reason is
recorded rather than supplied. **WST's displacement will have better support than GOOGL's**: its
compression is **observed over 24 months** (−21.1% to −6.8% across the anchor sweep) rather than
assumed.

## HOW VERIFIED

**Surgical edit with a full untouched-key guard.** Fifteen top-level keys — `result`, `verdict`,
`scenarios`, `facts`, `spot`, `spot_as_of`, `tier`, `gate_adjudication`, `survival_input`,
`underwrite_date`, `supersedes`, `superseded_by`, `refresh_log`, `recipe_id`, `multiple_basis` —
were hashed before and re-asserted after; the write is refused if any moves. `git diff --stat` on the
record: **6 insertions, 6 deletions** — exactly the six fields. Re-validated through
`ScenarioRecord.model_validate`.

**THE SUITE REFUSED THE FIRST TWO DRAFTS, AND WAS RIGHT BOTH TIMES.** Recorded because the
corrections improved the prose, and because an agent's accepted risk was simply wrong:

- **Two e2e guards caught a stale artifact I had proposed to accept.** `test_analysis_tier_reads_in_
  decision_order_e2e` and `test_screening_context_reaches_every_committed_dossier_e2e` render
  `dossier.md` LIVE from the committed JSON and compare it back to disk — so *"leave it for the
  standing artifact pass"* was not available. It was also unnecessary: that render path is
  `render_markdown(dossier, card=_read_scenario_card(ticker))`, **fully deterministic and with no
  LLM phase**, so the `.md` regenerates exactly without re-running synthesis. **12 lines changed,
  all four of them the two stamps and the two method sentences.**
- **`test_every_committed_scenario_record_is_register_clean` rejected `ratified` IN THE PROSE** —
  *"ratification is a structured field, not prose"* — and **rejected the house label `ANCHOR`** —
  *"state the claim, not the house label."* Both correct: the date belongs to `ratified`, and the
  method sentence now says *"every leg is a DISPLACEMENT FROM THE VERIFIED CURRENT normalized
  P/NTM"* instead of naming the pattern. **The house term is coined in `docs/RUNBOOKS.md` and this
  record, where a house term belongs; the record's own prose states the mechanism.**
- **`test_committed_r3_record_is_shaped_by_its_recipe` required each leg's own words** —
  `bear:` / `base:` / `bull:` must each appear in every method sentence. The first multiple draft
  had dropped the prefixes into continuous prose.

**Final state: `ruff` + `mypy --strict` (151 files) clean, 3,636 passed / 145 skipped offline, and
the figures re-checked after every write** — ratio **2.4298836625376596**, gate **PASS**, verdict
**confirmed**, spot **$339.35 @ 2026-08-31**, legs **$315.454 / $397.4145 / $432.874**. Unmoved.

**BOUNDARY.** Source: `/Users/work/Downloads/GOOGL_IC_Memo_2026-08-17.md`, 1,246 lines, read in full
at 2026-09-10 — every quotation above is verbatim from it, not from a summary. Record state is
`scenarios/GOOGL.json` at this commit. Multiples, EPS and percentiles are the memo's own sections 4,
5, 7A and 7B, USD. Ratification surfaces: the five named above. Artifacts re-rendered:
`data/dossiers/GOOGL/dossier.md`, `frontend/dossiers/GOOGL.md`, `frontend/scenarios/GOOGL.json`.

**WHAT IT COSTS / WHAT IS ACCEPTED. The 20.5x-versus-22.0x gap is an ACCEPTED, VISIBLE hole**, not a
resolved question — the only thing in this build left open on purpose. **Falsifier: any later
document giving a reason for the horizon-dependent bear displacement**, at which point the method
sentence gains it by amendment rather than by invention. **And the ratification is only as good as
the diagnosis behind it**: it rests on reading the memo in full rather than on the summary that had
been circulating, which is what surfaced all three corrections — the wrong horizon on the earnings
axis, the mislocated binding-assumption phrase, and the missing bear reason.
