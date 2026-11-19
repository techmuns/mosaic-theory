---
id:
status: open
date: 2026-11-19
prs: [1094, 1125, 1130]
supersedes:
superseded-by:
---

# SMPL's bearish lean under fix 4b is a real effect, not noise. Fix 4b's SMPL falsifier fired, and by the operator's ruling (2026-11-19, "Yes, merge once green") fix 4b stays. Read at $0, all 12 bearish draws on fix 4b's bytes rest on figures SMPL's page holds, but 5 state the page's facts more strongly than it does, 4 of them in the line that states the lean

**WHAT.**
- **The falsifier.** Fix 4b's record (`docs/records/2026-11-17-fix4b-the-rebuttal-the-ask-the-path-and-the-example.md`) accepted LLY's and SMPL's lean moves as noise. Its falsifier: "the next panel run on main with fix 4b reads LLY below 4 bullish of 5 again, or SMPL at 4+ bearish of 5 again, on requests this change moved".
  - Y18's run (`docs/records/2026-11-19-y18-the-no-cause-ask-names-no-shape.md`, registration `99267760`) has a BASE that is main with fix 4b. SMPL read bearish 4, mixed 1 in each arm, so **the SMPL half fired**.
  - LLY read bullish 4, mixed 1, so the LLY half did not fire.
  - On fix 4b's bytes, SMPL has now read bearish in 12 of 15 draws over three runs of five: fix 4b's CAND arm, Y18's BASE and Y18's CAND.
  - On earlier requests it read bearish in 8 of 15: fix 4b's BASE (1), and #953's two arms (3 and 4), as fix 4b's record states.
- **The ruling.**
  - Coordinator B asked the operator: "Merge #1125 once green, logging SMPL's shift and opening the bleed-label follow-up?"
  - Operator, verbatim, 2026-11-19: **"Yes, merge once green"**.
  - B's recommendation, given before the question:
    - record the shift as a real effect, not noise, and do not revert fix 4b;
    - before SMPL's next paid build, read its fix-4b draws at $0 and check that each bearish read rests on facts the page holds. Judging the shift by later returns is barred (never tune on outcomes);
    - record the drawdown-anchor label as an open item (board W72). It is a fact-layer and prompt change with its own six-page panel check, and nothing starts without the operator's go and cap.
- **This record is that $0 read.** It records the shift and changes no code, prompt or page.

**THE READ ($0, no model call).** The saved draws were read with the registered scorer's own functions (`panel_inputs`, `arm_layer`, `draw_units`, `score_units`). Every claim the scorer could not test was then read against SMPL's frozen panel page.

| run | arm (bytes) | draws | lean | what the read finds in each bearish draw |
|---|---|---|---|---|
| fix 4b | BASE (before fix 4b) | 1–4 | mixed | not read (not bearish) |
| fix 4b | BASE | 5 | bearish | every figure on the page; one absence claim, "no recovery gap" |
| fix 4b | CAND (fix 4b) | 1, 2 | bearish | grounded |
| fix 4b | CAND | 3 | bearish | **overstates:** "broad double-digit takeaway erosion" (its lean line); "the two acquired brands at double-digit rates" |
| fix 4b | CAND | 4 | bearish | **overstates:** "first-ever revenue decline" (its lean line); "rose every year from FY15 … the first annual decline in the record"; also "no recovery gap" |
| fix 4b | CAND | 5 | mixed | not read |
| Y18 | BASE (fix 4b) | 1 | mixed | not read |
| Y18 | BASE | 2, 3, 4 | bearish | grounded |
| Y18 | BASE | 5 | bearish | **overstates:** "turned down absolutely for the first time in the series" |
| Y18 | CAND (identical to BASE) | 1 | mixed | not read |
| Y18 | CAND | 2, 5 | bearish | grounded |
| Y18 | CAND | 3 | bearish | **overstates:** "broad double-digit consumption decline" (its lean line); also "no recovery gap-up" |
| Y18 | CAND | 4 | bearish | **overstates:** "two consecutive years of double-digit revenue/EBITDA decline" (its lean line); "a SECOND consecutive year of double-digit top-line decline" |

- **What the page says against each overstatement.**
  - **Revenue fell once before FY26.** The page's revenue series runs FY15 379 → FY16 428 → FY17 396 → FY18 438 → … → FY25 1,451 → FY26 1,356 ($M, CIQ Financials; FY16, FY17 and FY21–FY24 are marked reclassified). So "rose every year", "first-ever" and "first time in the series" contradict the page. "The first annual decline after a multi-year climb" (Y18 BASE draw 3) holds, since FY18 to FY25 rose every year.
  - **Only Atkins is double-digit.** The page holds Q4 total consumption at −8.4% and Atkins at −22.6%. The draws' OWYN −7% and Quest −2.1% come from the call.
  - **FY26 is not a double-digit year.** FY26 revenue fell 7% (1,451 → 1,356), and FY25 EBITDA rose (242 → 262). The first double-digit revenue year would be the FY27 guide (−13% to −17%), not a reported one.
  - **The page measures no up-gap.** Its detector reads single days of −10% or worse, so "no recovery gap" claims an absence the page does not measure.
- **Grounded claims the read checked:**
  - EBITDA "turned down for the first time in the series" (Y18 CAND 2): EBITDA rose every year from FY15 22 to FY25 262.
  - "Cut to Hold (2.60)" (Y18 CAND 2): the page's rating event moves consensus 2.40 → 2.60, and its consensus line reads Hold (2.60).
  - The April guide's "−10% to −7%" sales and "−22% to −19%" adjusted EBITDA: on the page's `revised_guidance` and anchor outlook.
  - The 6th percentile: the page's EV/EBITDA own-history percentile is 0.056.
- **Every figure in the 12 draws' lean lines and bear points has its value somewhere in the facts the request carries,** by the registered scorer's M-ABSENT, which matches a value, not its meaning. Two exceptions:
  - four "$288.9M" (fix 4b CAND 2, Y18 BASE 3 and 4, Y18 CAND 5): the page holds 288.9 in its CIQ consensus path with no unit, and the draw added "$…M";
  - two quoted phrases that are not facts.

  The core facts in the table below were checked one by one, by meaning, in the page's mechanical layer. So were the call's −8.4% and −22.6%. No bearish draw rests on a figure that neither the page nor the call holds.
- **The facts every bearish read rests on** (of the 12 bearish draws on fix 4b's bytes, how many cite each):

  | fact on the page | draws |
  |---|---|
  | FY26 revenue 1,451 → 1,356 and EBITDA 262 → 206 | 12 |
  | the FY27 guide: sales −13% to −17%, adjusted EBITDA −9% to −14% (8-K `0001702744-26-000028` Ex-99.1) | 12 |
  | the $331.0M FY26 writedown ($391.9M over five years) | 12 |
  | FY27 EBITDA consensus 288.9 → 196.8 (−32%) | 12 |
  | Q4 consumption −8.4%, Atkins −22.6% (the call) | 12 |
  | price elasticities expected well above 1 (the call) | 12 |
  | ROIC 7.0% → 5.7% | 8 |
  | SMPL −38.3% against IWM +16.0% over the year | 6 |
  | FY26 buyback near $213M at $18.29, against a $12.47 close | 5 |
  | CIQ's LTM EBITDA $206M against −$155M rebuilt from the filings | 5 |

- **The overstatements sit only in the bearish draws on fix 4b's bytes:** 5 of those 12, against none of the other 8 readable draws (7 mixed and the one bearish draw before fix 4b), by the pattern scan in BOUNDARY. The "no recovery gap" absence claim is not confined to them: it appears in 5 draws across both leans (fix 4b BASE 5 and CAND 4 and 5, Y18 CAND 1 and 3).
  - Removing them leaves each of the 5 resting on the same facts the 7 grounded bearish draws cite.
  - SMPL's facts are byte-identical across fix 4b's two arms (its request moved only in SYSTEM and the tool schema, as fix 4b's record states). So the shift is the same facts weighed under fix 4b's rules, not a response to new facts.
  - Whether those facts warrant strongly-bearish rather than mixed is the reader's judgment. This read does not make it, and later returns may not.
- **The registered scorer flags 2 of the 5:** M-PATH catches fix 4b CAND 4's "every year" and Y18 CAND 4's "consecutive" in its lean line. "First-ever", "first time in the series", "broad double-digit" and "no recovery gap" pass every metric.

**WHAT STAYS OPEN** (STATE row 55; §5.0 is at its 60-line cap, so both items are folded into that row).
- **SMPL's overstated wording, owner the operator.** Whether a lean line that states the page's facts more strongly than the page does needs a check (a metric or a prompt rule) is the operator's call. Nothing here changes either.
- **The drawdown-anchor label (board W72), owner coordinator B; waits on the operator's go and cap.**
  - `_dated_words.none_shape` (`vinci/dossier/mechanical.py:821`) writes "no discrete gap-down — …" into 22 dated parts across 13 of the 14 committed anchored pages, and the digest's literal example repeats it.
  - Y18 showed the phrase stays in MCK's request 6 times after its reword.
  - Changing it is a fact-layer and prompt change with its own six-page panel check, estimated near $25 (Y18's cost $25.54).

**HOW VERIFIED.**
- **Saved draws only:** each draw's raw output from its run's `draws.jsonl`, scored at $0 by the registered metrics. No model was called.
- **The claims the scorer passes,** read against the frozen page's own series:
  - `drawdown_cause`, the revenue, EBITDA and margin trajectory, and `roic_trend`;
  - `revised_guidance`, the consensus path and `revision_events`.

  Every value quoted above was printed from the page.
- **The call transcript** sits beside the page in the request. It is private, and nothing here quotes it: the figures above are the page's.

**BOUNDARY.**
- **Draws:** the 20 SMPL draws saved on this disk, all on the frozen panel v2 page (freeze `bcda7ce3`, SMPL blob `0b4ff8eb`).
  - Fix 4b's run: registration `e309bd25`, drawn 2026-11-17, 5 BASE and 5 CAND.
  - Y18's run: `99267760`, drawn 2026-11-19, 5 and 5.
  - #953's ten (registration `978a6a52`, drawn 2026-11-13) were not found. The search covered every side-session notes folder, the session temp folders and the GitHub checkouts: a search for `draws.jsonl`, matched by each run's score-log registration. So 5 of "the 15 before" were read, and the 8-of-15 count is fix 4b's record's.
- **Lean:** the first word of each draw's `evidence_balance`, as the registered scorer reads it. "Bearish" means strongly-bearish.
- **Scorer:** the registered metrics, run from main `abadb913`. Its 16 scorer files differ from the registered ref `55b92b52` only by Y18's own `synthesis.py` change (the ASK's wording), which no metric reads.
- **Fact counts:** case-insensitive regexes over each bearish draw's bear points and lean line, one per fact (the table's rows).
- **The pattern scan:** case-insensitive regexes for "recovery gap", "first-time / first annual / first-ever / first decline", "every year", "double-digit" and "consecutive". They ran over the lean line, bear points and bull points of all 20 draws, and every match was printed and read. "Double-digit" said of the price increase, or of the FY27 guide, is grounded and is not counted.

**WHAT IT COSTS / WHAT IS ACCEPTED.** $0. Nothing is accepted here. SMPL's shift is recorded as real by the operator's ruling, and the two open items above are the operator's and B's.
