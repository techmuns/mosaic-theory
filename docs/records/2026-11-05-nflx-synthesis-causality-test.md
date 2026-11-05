---
status: recorded
date: 2026-11-05
prs: [920]
---

# NFLX synthesis causality test: three single-variable prompt edits, five paid draws each, against the 2026-11-05 build's five logged draws (PRE-REGISTERED; results below the line)

**WHAT.** A diagnostic, run under the operator's approval ("Also test on NFLX") with a HARD CAP of
$20. On 2026-11-05 audits found NFLX's synthesis misreading facts it was given. Three causes were
suspected in how the prompt PRESENTS those facts. Each is changed alone here (V1, V2, V3), and NFLX's
synthesis is drawn five times per change through the production path. The draws are compared with
the five draws of NFLX's real build (PR #918, run `56f6a840`), which are the CONTROL. A fourth
error class that no variant targets is scored as a NEGATIVE CONTROL. The test writes no page, sets
no parameter and changes no production file. Its result informs which prompt fixes to make, and
those fixes are separate PRs.

**PRE-REGISTRATION.** Everything from here to the RESULTS line was written, committed and pushed
before the first paid call. The commit that first carries this file is the timestamp.

## 1. The control and the harness

- **Control:** the five draws in NFLX's build log (`data/dossiers/NFLX/llm_call.log` in the
  worktree that built PR #918; git-ignored, holds licensed transcripts, never copied into the
  repo). sha256 `81b51293…6cd783`. Draw 1 wrote 188,482 cache tokens; draws 2–5 read them; 24
  uncached input tokens each; output 7,705 / 8,133 / 9,181 / 7,283 / 6,154 tokens. All five
  leaned `mixed`.
- **Harness** (local, never committed; §7 says where): it calls
  `vinci.dossier.synthesis.synthesize` with the production client
  `vinci.graph.llm.AnthropicLlmClient`. Its inputs:
  - NFLX's committed page at PR #918's head `0dbe8f97`;
  - NFLX's two CIQ transcripts in the assembler's CIQ copy, read by production's
    `ciq_sheets.transcript_for_synthesis`;
  - `sleeve=overshoot`, `draws=5`.
- **Capture:** in CAPTURE mode only the innermost SDK object (`client._client`) is swapped for a
  recorder. So every byte of the request is built by production code, and nothing is sent.
- **The mechanical layer as the synthesis read it.** The committed page's mechanical layer, with
  two post-synthesis attachments undone. Both are read off `vinci/dossier/assemble.py`, not
  guessed:
  - `capital_structure.covenant_term_rows` is attached AFTER synthesis. Set to null.
  - `ev_gap` is RECOMPUTED after synthesis by `ev_gap_transform`, so the synthesis read null.
    Set to null. The first rebuild left it in, and the diff was exactly that one block (§2).
- **Code:** `synthesis.py`, `graph/llm.py`, `mechanical.py`, `sleeves.py` and `config.py` have no
  diff between the build's main (`c4c9f432`) and the harness's (`3e97ee7d`).

## 2. The byte-identity proof (at $0, before any spend)

| | rebuilt | logged | equal |
|---|---|---|---|
| SYSTEM | 7,364 chars, sha256 `8fcfd615fd0dff95…` | 7,364 chars, sha256 `8fcfd615fd0dff95…` | **yes** |
| USER | 474,921 chars, sha256 `618e478112ec0f1d…` | 474,921 chars, sha256 `618e478112ec0f1d…` | **yes** |
| model | `claude-opus-4-8` | `claude-opus-4-8` | yes |
| max_tokens | 16384 | 16384 (each draw's usage) | yes |

- **Diffs:** the unified diff is 0 lines for SYSTEM and 0 lines for USER. The full sha256 of both
  match.
- **The rest of the request, as production builds it:**
  - top-level `cache_control: {"type": "ephemeral"}`;
  - `tool_choice` forced to `assemble_dossier_framing`;
  - one user message whose content is a plain string;
  - no `temperature`, `top_p` or `top_k`.
- **What the log cannot prove:** it holds no tool schema. The tool comes from `tool_for("overshoot")`
  in the unchanged `synthesis.py`.
- **All five draws** of a captured build send one identical request.

## 3. The variants: each changes exactly ONE span

Each variant is applied inside the harness only, as a module patch or a copied mechanical layer.
Its request was captured at $0 and compared with the baseline character by character. Each differs
in ONE contiguous span; model, max_tokens, tools, tool_choice and cache_control are equal.

- **V1 SIGNED.** The MATERIAL FIGURES line, USER only, at char 471,794 (20 chars replaced by 95).
  - was: `LTM: 2,800.0 in the table; write "$2,800.0M"; …`
  - now: `LTM: +2,800.0 in the table: ADDS $2,800.0M to pre-tax income (a gain), whatever the row's label says; write "$2,800.0M"; …`
  - The page's own table holds +2,800.0 on this row. Its source_ref reconciles to
    `us-gaap:NonoperatingIncomeExpense`.
- **V2 NEUTRAL DRAWDOWN LABEL.** `drawdown_cause.shape.value`, USER only, at char 59,402 (50 chars
  replaced by 75). It is the only site of the wording in the facts; the two transcript uses of
  "gradual" are management's and stay.
  - was: `gradual bleed — no discrete gap-down detected`
  - now: `no single-day drop of -10% or worse in the window (detector threshold -10%)`
  - No new fact: the threshold is already on the page (`gap_threshold: -0.1`), and the window is
    in the value's source_ref. The ASCII "-10%" follows the dated parts' own wording.
- **V3 NEUTRAL EXAMPLE.** Rule 13's literal example, SYSTEM only, at char 6,324 (1,007 chars
  replaced by 892). The old example is LLY's committed bear point, verbatim. Its figures are
  replaced by fictional ones that belong to no filer, in the same JSON shape: seven entries, six
  cited and one `derived: difference`, in claim order. The rebuttal clause is gone.
  - was (claim): `… reflecting heavy capex/IPR&D draw — genuine, but outweighed by 121.4x coverage and 0.9x net leverage leaving reinvestment capacity intact.`
  - now (claim): `Reported FCF conversion is weak relative to earnings: LTM Levered FCF was $412.6M against $1,870M EBITDA (CFO $1,205M less capex $388M = $817M); interest coverage is 6.2x and net leverage is 2.4x.`
  - The fictional figures are internally consistent: 1,205 − 388 = 817, and 4,488 ÷ 1,870 = 2.4.
  - **A confound to read V3 by:** rule 7 still tells the model to frame a minority counter-point as
    "a genuine counter-point, OUTWEIGHED by …" when the lean is committed. V3 removes only the
    example's reinforcement of that pattern, not the rule.

## 4. The metrics

Every draw's raw tool output is decoded with production's `synthesis._decode_escapes`, then split
into PROSE UNITS: each bull/bear claim, each key unknown, the decisive question and each piece of
its evidence, each twin's `distinguishing_fact`, and `evidence_balance`. A `source_ref` or
`figures` entry is never scored, because a source_ref quotes the row label "…Charges".

The REGEX picks CANDIDATES. READING adjudicates each candidate by the written rule, and every
adjudication is listed in RESULTS. The regexes (Python, case-insensitive) are frozen in the local
scorer, sha256 `06233905…a733e6`.

| metric | candidate regex | adjudication rule (counts per DRAW: does any unit do it?) |
|---|---|---|
| **M1** merger row as a COST (V1 target) | a unit matching `2,800(?:\.0)?\|\$2\.8\s?(?:bn\|billion\|B\b)\|\bmerger\w*`, read with the verbatim PLURAL label `Merger & Related Restruct. Charges( ($M))` removed, containing `\b(?:charges?\|costs?\|drags?\|dragg\w*\|expenses?\|headwinds?\|losses?\|write-?(?:downs?\|offs?))\b` | the unit calls the +2,800.0 row ITSELF a charge, cost, drag, expense, headwind or loss. A singular rewrite of the label as a noun ("a $2,800.0M … Restruct. Charge") counts; the verbatim plural label alone does not. A cost word about something else in the unit (head-count cost) does not count. |
| **M1b** the row's direction stated correctly (V1 secondary) | the same unit set, containing `gains?\|income\|benefits?\|flatter\w*\|boost\w*\|inflat\w*\|credit\|…` | the unit states the row ITSELF adds to earnings: a gain, non-operating income, or something that inflates, flatters or overstates earnings. "Pre-tax income" in a clause about another figure does not count. |
| **M2a** "bleed"/"gradual" (V2 target) | `\bbleed\w*\|\bgradual\w*` in any unit | used to describe NFLX's price decline (a quote of management's transcript "gradual" about something else does not count) |
| **M2b** the follow's cause asserted unreversed (V2 target) | `has/have not (yet) reversed/recovered/abated/eased/ended/stopped/played out/run its course`, `not (yet) reversed/recovered`, `kept/keeps/still playing out`, `continue to play out`, `unreversed`, `never revers\w*` | the unit asserts the decline, or a cause tied to the follow, persists or has not reversed. "has not played out AS an earnings break" (a bull reading) does not count. Margin wording ("margin optics never reverse") is PATH, not M2b. |
| **M3** bear points closed by a bullish rebuttal (V3 target) | in a BEAR claim, `\boutweigh\w*\|\bgenuine\b[^.;]{0,60}?\bbut\b` | the bear point ends by setting a BULLISH counter against itself ("genuine, but outweighed by …"). A bear point where the BEAR fact outweighs ("outweighing the intact headline consensus") does not count. Reported per draw and as points / bear points. |
| **M3-broad** (V3 secondary) | in a BEAR claim, the M3 regex or `though\|although\|even as`, `but … qualified/offset/outweigh/tempered/mitigated/frames`, `qualified/offset/mitigated/cushioned/tempered/countered by`, `offsetting`, `weighed against`, `does not overturn` | any concessive clause that sets a bullish counter against the bear point. A neutral caveat ("cannot by itself distinguish overshoot from impairment") does not count. |
| **PATH** NEGATIVE CONTROL (no variant targets it) | in a unit naming EBITDA/margin/earnings/EBIT/operating or net income/FCF: `every step/year/period/single year`, `without interruption/a break/a dip/a down-year/a reversal/a pause`, `never reverse*/dip*/decline*/fell/fall*/contract*`, `uninterrupted`, `unbroken`, `monoton*`, `year after year`, `straight-line`, `in every year/period`, `consecutive` | the unit claims a MONOTONE path for the multi-year EBITDA or margin series. That series dips in FY2022: EBITDA 6,402.9 → 5,969.5 ($M), on the page's own annual table. |
| **LEAN** | `split_lean(evidence_balance)[0]` (production's `verdict.split_lean`) | as computed |

## 5. The decision rule, and what five draws can show

- **The unit is the DRAW.** Points within one draw are not independent, so a point count is
  descriptive only.
- **The test:** Fisher's exact, two-sided, on 5 draws against 5:

  | counts compared | p |
  |---|---|
  | 5/5 vs 0/5 | 0.008 |
  | 5/5 vs 1/5, or 4/5 vs 0/5 | 0.048 |
  | 5/5 vs 2/5, or 3/5 vs 0/5 | 0.167 |
  | 4/5 vs 1/5 | 0.206 |
  | 2/5 vs 0/5 | 0.444 |
  | 1/5 vs 0/5 | 1.000 |

- **The labels:**
  - **evidence** — only a swing of at least four draws (p ≤ 0.048).
  - **suggestive, not evidence** — a swing of three.
  - **no evidence** — two or fewer. A one-of-five difference is noise.
- **What each target can show at n=5,** given the control's scores (§6):
  - **M1** (control 1/5) cannot show a REDUCTION as evidence. Only a rise to 5/5 would be evidence.
  - **M1b** (control 2/5) cannot reach evidence either way: 2/5 → 5/5 is p = 0.167.
  - **M2a** (control 5/5) can: ≤ 1/5 is evidence.
  - **M2b** (control 2/5) cannot show a reduction as evidence.
  - **M3** (control 3/5) cannot show a reduction as evidence.
  - **M3-broad** (control 4/5) can: 0/5 is evidence.
  - **PATH** (control 3/5) is the noise floor. Whatever it moves by is the run-to-run swing the
    other metrics must beat.
- **Two assumptions the design cannot test:**
  - The control was drawn earlier on 2026-11-05 than the variants; the model id is the same, and
    stationarity across those hours is assumed. A fresh 5-draw control would cost about $2.6 and
    is not in this test.
  - The scorer is the experimenter. The regexes and rules are frozen here, and every
    adjudication is listed in RESULTS so it can be checked.

## 6. The control's scores (adjudicated before any variant draw)

| draw | M1 cost | M1b direction | M2a bleed/gradual | M2b unreversed | M3 narrow | M3-broad | PATH | lean |
|---|---|---|---|---|---|---|---|---|
| C1 (kept) | **yes**: bear[3] "a $2,800.0M … Restruct. Charge", "one-time rather than recurring drag"; ku[5] "restructuring/aborted-deal costs" | no | yes (1 unit) | **yes**: bear[0] "has NOT reversed" | 1/5 (bear[4]) | 2/5 | **yes**: bull[0] "compounded without interruption", bull[1] "RISEN every step" | mixed |
| C2 | no | **yes**: "overstates the operating earnings" | yes (1) | no | 1/5 (bear[1]) | 4/5 | **yes**: bull[0] "rose every year" | mixed |
| C3 | no | **yes**: "one-time $2,800.0M non-operating gain" | yes (4) | **yes**: bear[0] "has NOT recovered — it kept playing out"; "never reversed" | 0/7 | 0/7 | no | mixed |
| C4 | no | no (sign disagreement only) | yes (3) | no | 0/5 | 2/5 | no | mixed |
| C5 | no | no ("flattered" is about the $2,590M quarter) | yes (1; "gradual multiple de-rate") | no | 1/5 (bear[4]) | 3/5 | **yes**: bull[0] "climbed every year" | mixed |
| **control** | **1/5** | **2/5** | **5/5** (10 units) | **2/5** | **3/5** draws; 3 of 27 bear points | **4/5** draws; 11 of 27 | **3/5** | mixed 5/5 |

- **Regex candidates adjudicated OUT in the control:**
  - C3 bear[1] "outweighing the intact headline consensus level": the bear fact dominates.
  - C1 bull[0] "margin optics never reverse": this is PATH, not M2b.
  - C5 bull[6] "has not played out as an earnings break": a bull reading.
  - C5 bear[0]'s "though the near-floor multiple … cannot by itself distinguish": a neutral caveat.

## 7. The budget rule, and where the raw draws live

- **The order:** V1, V2, V3, five sequential draws each — 15 paid draws, one cache write per
  variant.
- **The guard** wraps the SDK object only. Before forwarding each request, it:
  1. asserts the request EQUALS that variant's request captured and diffed at $0 (§3);
  2. refuses it if spend so far plus the worst case of one more draw would cross $20. The worst
     case is $1.6096: 192,000 prompt tokens all written to cache at 1.25 × $5/Mtok, plus 16,384
     output tokens at $25/Mtok.
- **The pins:** both stops were shown at $0 before the run. A V2 request checked against V1's
  stopped with 0 calls forwarded. A ledger at $18.50 stopped draw 1 with 0 forwarded.
- **The cost of each draw** is production's `vinci.graph.llm.cost_usd` (the function behind
  `run_metrics`' `usd`), applied to the response's usage.
- **Expected spend:** about $2.6 per variant, about $7.7 in all.
- **The raw draws, the per-draw usage, the spend ledger and the harness scripts** are kept outside
  the repo, never committed, in this session family's side-session notes folder under
  `nflx-causality-2026-11-05/`. The full prompts and synthesis logs carry licensed transcripts, so
  they stay in the session's scratch directory only.

---

## RESULTS

*Nothing below this line existed when the pre-registration was pushed (`302a7be7`,
2026-11-05T20:16:57+05:30). The first paid call followed it.*

**THE RESULT IN SIX LINES.**
- **V2 is the only effect that clears the pre-registered bar.** The borrowed "bleed"/"gradual"
  wording fell from 5 of 5 draws to 1 of 5 (p = 0.048), and from 10 prose units to 1.
- **V2 does NOT move the claim that the follow's cause "has NOT reversed":** 2 of 5 → 2 of 5. And
  the slow-decline reading survived in other words ("a slow, continuous grind").
- **V1 moves its metrics the way it was meant to, but not past noise.** Cost framing went 1 of 5 →
  0 of 5. The row was called a gain or income in 2 of 5 → 5 of 5 (p = 0.167, suggestive). V1's own
  instruction words came back in the prose.
- **V3 shows no effect on bear points closed by a rebuttal:** 3 of 5 draws → 2 of 5; 3 of 27 bear
  points → 3 of 27. The rebuttals that remain use rule 7's own wording.
- **The negative control moved by three draws with nothing aimed at it** (PATH 3/5 in the control,
  0/5 under V3). A three-of-five swing is inside this design's noise.
- **Spend:** $7.6768 for 15 draws, of the $20 cap. No draw failed, no cache missed, no lean flipped
  its mode.

### 8. Cost — production's `cost_usd`, per draw

Every variant response came from `claude-opus-4-8` and stopped on `tool_use`; each draw had 24
uncached input tokens. The control is priced by the same function from its logged usage; its
$2.5170 was spent by PR #918's build, not by this test.

| draw | cache write | cache read | output | USD | | draw | cache write | cache read | output | USD |
|---|---:|---:|---:|---:|---|---|---:|---:|---:|---:|
| C1 | 188,482 | 0 | 7,705 | 1.3708 | | V2-1 | 188,487 | 0 | 6,882 | 1.3502 |
| C2 | 0 | 188,482 | 8,133 | 0.2977 | | V2-2 | 0 | 188,487 | 8,652 | 0.3107 |
| C3 | 0 | 188,482 | 9,181 | 0.3239 | | V2-3 | 0 | 188,487 | 8,733 | 0.3127 |
| C4 | 0 | 188,482 | 7,283 | 0.2764 | | V2-4 | 0 | 188,487 | 7,951 | 0.2931 |
| C5 | 0 | 188,482 | 6,154 | 0.2482 | | V2-5 | 0 | 188,487 | 7,752 | 0.2882 |
| V1-1 | 188,514 | 0 | 7,963 | 1.3774 | | V3-1 | 188,431 | 0 | 7,797 | 1.3727 |
| V1-2 | 0 | 188,514 | 8,069 | 0.2961 | | V3-2 | 0 | 188,431 | 6,650 | 0.2606 |
| V1-3 | 0 | 188,514 | 8,700 | 0.3119 | | V3-3 | 0 | 188,431 | 8,124 | 0.2974 |
| V1-4 | 0 | 188,514 | 9,221 | 0.3249 | | V3-4 | 0 | 188,431 | 7,421 | 0.2799 |
| V1-5 | 0 | 188,514 | 6,769 | 0.2636 | | V3-5 | 0 | 188,431 | 9,723 | 0.3374 |

- **Totals:** V1 $2.5739, V2 $2.5549, V3 $2.5480. **Paid total $7.6768**, the same as the spend
  ledger; $12.32 of the cap unused.
- **Cache:** the guard's check ran before every draw. One cache write per variant, then four
  reads; no draw read 0 from cache.

### 9. Per draw

M1 to PATH say whether the draw did it; M2a gives the units in brackets; M3 and M3-broad are bear
points counted over the draw's bear points.

| draw | M1 cost | M1b direction | M2a | M2b | M3 | M3-broad | PATH | lean |
|---|---|---|---|---|---|---|---|---|
| C1 | **yes** | no | yes [1] | **yes** | 1/5 | 2/5 | **yes** | mixed |
| C2 | no | **yes** | yes [1] | no | 1/5 | 4/5 | **yes** | mixed |
| C3 | no | **yes** | yes [4] | **yes** | 0/7 | 0/7 | no | mixed |
| C4 | no | no | yes [3] | no | 0/5 | 2/5 | no | mixed |
| C5 | no | no | yes [1] | no | 1/5 | 3/5 | **yes** | mixed |
| V1-1 | no | **yes** | yes [1] | no | 0/5 | 0/5 | no | mixed |
| V1-2 | no | **yes** | yes [1] | no | 2/4 | 3/4 | no | **strongly-bullish** |
| V1-3 | no | **yes** | yes [2] | **yes** | 0/6 | 0/6 | no | mixed |
| V1-4 | no | **yes** | yes [2] | no | 0/5 | 1/5 | no | mixed |
| V1-5 | no | **yes** | yes [1] | **yes** | 2/5 | 2/5 | **yes** | mixed |
| V2-1 | no | **yes** | no | no | 0/6 | 0/6 | no | mixed |
| V2-2 | **yes** | no | yes [1] | **yes** | 1/5 | 1/5 | **yes** | mixed |
| V2-3 | no | **yes** | no | no | 1/5 | 1/5 | **yes** | mixed |
| V2-4 | **yes** | no | no | no | 0/6 | 0/6 | no | mixed |
| V2-5 | no | **yes** | no | **yes** | 0/4 | 1/4 | no | mixed |
| V3-1 | **yes** | **yes** | yes [2] | no | 2/4 | 2/4 | no | mixed |
| V3-2 | **yes** | no | yes [3] | no | 0/7 | 0/7 | no | mixed |
| V3-3 | no | **yes** | yes [1] | no | 0/5 | 0/5 | no | mixed |
| V3-4 | no | no | yes [5] | no | 0/5 | 0/5 | no | mixed |
| V3-5 | no | **yes** | yes [2] | no | 1/6 | 1/6 | no | mixed |

### 10. Per variant against the control: the pre-registered verdicts

Draw counts, then Fisher's exact (two-sided) against the control. **Bold** is a variant's own
target.

| metric | control | V1 | V2 | V3 |
|---|---|---|---|---|
| M1 cost | 1/5 | **0/5** (p 1.0) | 2/5 | 2/5 |
| M1b direction | 2/5 | **5/5** (p 0.167) | 3/5 | 3/5 |
| M2a bleed/gradual, draws [units] | 5/5 [10] | 5/5 [7] | **1/5 [1]** (p 0.048) | 5/5 [13] |
| M2b unreversed | 2/5 | 2/5 | **2/5** (p 1.0) | 0/5 |
| M3, draws (bear points) | 3/5 (3/27) | 2/5 (4/25) | 2/5 (2/26) | **2/5 (3/27)** (p 1.0) |
| M3-broad, draws (bear points) | 4/5 (11/27) | 3/5 (6/25) | 3/5 (3/26) | **2/5 (3/27)** (p 0.524) |
| **PATH (negative control)** | 3/5 | 1/5 | 2/5 | 0/5 |
| lean | mixed 5/5 | mixed 4, strongly-bullish 1 | mixed 5/5 | mixed 5/5 |

**V1 (signed line).**
- **Target, cost framing:** 1/5 → 0/5. **No evidence**, as pre-registered: a reduction from 1 of
  5 cannot be shown at this n.
- **Secondary, direction:** 2/5 → 5/5, **suggestive, not evidence** (p = 0.167). It is a
  three-draw swing, the size the negative control moved by on its own.
- **What the draws did:** every V1 draw stated the row as a gain that adds to pre-tax income, and
  none called it a charge, cost or drag. In the 15 draws V1 did not touch (control, V2, V3), cost
  framing appeared in 5: C1, V2-2, V2-4, V3-1, V3-2.
- **Side effect — the instruction's words reached the prose.** Every V1 draw wrote "ADDS"/"ADD to
  pre-tax income", and V1-1 wrote "whatever the 'Merger & Related Restruct. Charges' label says".
  This is prompt machinery echoed to the reader. A fix built on V1 has to be worded so that the
  echo reads as analysis.

**V2 (neutral drawdown label).**
- **Target, the borrowed word:** 5/5 → 1/5, and 10 units → 1. **Evidence**, the one result that
  clears the pre-registered bar (p = 0.048). The one survivor is V2-2's "slow bleed".
- **Target, "has NOT reversed":** 2/5 → 2/5, **no effect.** V2-2 wrote "has not reversed, it has
  extended"; V2-5 wrote "has not yet reversed". So that error is not driven by the label.
- **What V2 did and did not change:** it removed the label, not the slow-decline reading. V2-4
  wrote "a slow, continuous grind" and V2-5 "a grinding, continuous de-rate".
- **A limit on what V2 can show here:** for NFLX that reading is not false. The stock fell −39.6%
  over the trailing year with no single day of −10% or worse. STATE row 47's case is a name whose
  price ROSE (LLY, +35.6%) yet is described as bleeding. NFLX cannot test it; this test measured
  label echo, not mislabelling.

**V3 (neutral example).**
- **Target, narrow:** 3/5 → 2/5, and 3 of 27 bear points → 3 of 27. **No effect.**
- **Target, broad:** 4/5 → 2/5, and 11 of 27 bear points → 3 of 27, **no evidence** (p = 0.524).
  The point-level fall is shared by V2 (3 of 26), which leaves the example alone, so it cannot be
  laid on V3.
- **The rebuttals that remain under V3 use rule 7's template,** not the old example's trailing
  clause: V3-1's "A genuine counter-signal — outweighed by …" and V3-5's "A genuine counter-point
  …, OUTWEIGHED by …". All three sit in bear points of `mixed`-lean draws, although rule 7
  prescribes that framing only for a committed lean.
- **So rule 7 is the likelier source.** This is suggestive (two draws, three points), not tested.

**Negative control (PATH).**
- **The counts:** 3/5, 1/5, 2/5, 0/5 across control, V1, V2 and V3.
- **What that means:** nothing targeted it, yet it moved by up to three draws. That is the noise
  floor this test reads by. Only V2's M2a moved by more (four draws, and ten units to one).
- **The error is still there in the 15 variant draws:** monotone wording over the FY17→LTM series
  that dips in FY2022 appears in V1-5, V2-2 and V2-3 ("rose every year from $911M (FY17)").

**Leans and decision impact.**
- **The modal lean is `mixed` in every condition.** V1-2 alone leaned `strongly-bullish`.
- **No proposal change.** Under production that build's draws would DISAGREE and withhold the
  proposal; a `mixed` build proposes nothing, so the outcome is the same — none, as on PR #918.
- **One `strongly-bullish` draw in five** is the size of the draw variance already measured on
  AMZN (4/1), so it is not laid on V1.

### 11. Adjudications that are not obvious from the regex

- **Out (candidates the regex picked, removed by rule):**
  - V1-2 bull[3]: "ROIC 21.7% up every year from 16.2% (FY24)". It is not the EBITDA/margin series,
    and its span (FY24→LTM) is true.
  - V3-3 bull[1]: "rose every step through the drawdown". Its span is FY24→LTM, which is true.
  - V3-3 bull[2], "has so far held, not reversed", and V3-5 bull[2], "has NOT played out as a
    fundamental break": bull readings, as C5 bull[6] was.
  - V2-1 bear[3]'s "even as price rises", and V3-1 bear[1], V3-2 bear[0], V3-3 bear[1] and V3-5
    bear[4]'s "even as …": each clause sharpens the bear contrast; none weighs the point down.
- **Borderline, counted NO:**
  - V1-4 bull[0] "climbed every year — from $13,660M (FY25)" and V2-4 bull[0] "compounded without
    interruption — $13,660M FY25 to $15,957M LTM": monotone wording over a one-step span that
    excludes FY2022.
  - V3-4 bear[1]: "flattered by a one-off" attaches to the $2,590M quarter; the 2,800 is "the
    matching LTM … line". Ruled as C5 was.
- **Borderline, counted YES:**
  - V2-1 bear[2], "spanning these … flatter the true run-rate": the 2,800 is one of "these".
  - V2-3 bear[3], "partly a non-operating artifact", with the 2,800 named in the same clause.
  - V2-5 bear[2]'s "even as it lands above peer revenue growth": a bullish fact closing the point,
    so M3-broad.
- **Yes on both M1 and M1b, in one unit:** V3-1's decisive evidence calls the row "a $2,800.0M
  restructuring charge" yet says it makes the P/E overstate how cheap earnings are. The point
  contradicts itself.

### 12. Sensitivity and exploratory reads (NOT pre-registered — read as such)

- **M2b recall.** The regex misses persistence written as continuation: V3-4's "the bleed
  continued", V2-2's "it has extended", C1's "shows continued decline".
  - The sweep: claims that the decline continued or persists, in units about the price path,
    joined with M2b.
  - The result: control 3/5 (C1, C3, C4), V1 3/5, V2 3/5 (V2-2, V2-4, V2-5), V3 2/5. V2 does not
    move it under this wider reading either.
- **PATH recall.** Units stating EBITDA or margin endpoints from FY17 without monotone words
  ("EBITDA margin climbed 8%→32%") are TRUE net changes, not path claims. They are not counted, as
  pre-registered.
- **Pooling the untargeted conditions.** For each metric, the 15 draws whose variant did not
  target it are taken as a larger control (5 vs 15, Fisher two-sided):

  | metric | variant | untargeted draws | p |
  |---|---|---|---|
  | M1 cost | V1 0/5 | 5/15 | 0.27 |
  | M1b direction | V1 5/5 | 8/15 | 0.11 |
  | M2a | V2 1/5 | 15/15 | 0.001 |
  | M2b | V2 2/5 | 4/15 | 0.61 |
  | M3 | V3 2/5 | 7/15 | 1.0 |
  | M3-broad | V3 2/5 | 10/15 | 0.35 |

  The same picture: V2's label effect is large, everything else is inside noise.

### 13. What five draws can and cannot show

- **What it can show:** an effect as large as V2's on its own word, near-total in one direction.
- **What it cannot:**
  - It cannot show a reduction from a base rate of 1 or 2 of 5 (M1, M2b) as anything.
  - It cannot tell a three-of-five swing from the swing the negative control made by itself.
  - It cannot separate a variant's effect from the hours between the control's build and these
    draws. The model id is the same; stationarity is assumed, not tested.
  - It is one name. NFLX's price fell, so the V2 result says nothing about STATE row 47's
    rising-price case.
- **The rule:** a one-of-five difference is not evidence. Here, neither is a three-of-five one.

### 14. What this informs (the fixes are separate PRs, and the coordinator's to brief)

- **V2's edit removes the echoed label reliably, at no cost to the lean.** But it does not reach
  the "has NOT reversed" claims, so those need a different lever.
- **One untested suspect for those claims:** the anchor section's ASK, "has the cause named at the
  follow played out?". It is asked even when the at-anchor part shows no gap-down, so no cause was
  ever named. That is a hypothesis for a next test, not a finding.
- **V1's direction is right but unproven at n=5,** and the fix that follows it must handle the echo.
- **V3 does not move the rebuttal pattern.** Rule 7's own "OUTWEIGHED by" template, applied here to
  `mixed` leans, is the likelier source. Also untested.

- **Population:** NFLX only, on the 2026-11-05 inputs of PR #918: page `0dbe8f97`, and the CIQ
  transcripts of the Q2 and Q3 2026 calls.
- **Unit:** one draw of `claude-opus-4-8` through `synthesize`, `draws=5` per condition.
- **Control:** the build log's 5 draws (run `56f6a840`, 2026-11-05).
- **Variants:** 5 draws each, drawn 2026-11-05 between 20:17 and 20:40 +05:30, at code `3e97ee7d`.
- **What each count runs over:**
  - M3 and M3-broad count `bear_points` claims only: 27 / 25 / 26 / 27 across control / V1 / V2 / V3.
  - Every other metric counts over all prose units, excluding `source_ref` and `figures`.
  - A count without "units" or "points" is a count of DRAWS.
- **Cost:** list price from `vinci.config.LLM_PRICE_PER_MTOK` ($5 / $25 per Mtok; cache write
  1.25×, cache read 0.1×).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$7.6768 of the $20 cap.** No page, parameter or production file was written; nothing is
  accepted as risk.
- **The scorer is the experimenter.** That is mitigated, not removed: every rule was frozen and
  pushed before the first draw, and every non-obvious adjudication is listed in §11.
- **The raw draws are local and never committed:** each draw's tool output, usage and USD; the
  spend ledger; the harness and scorer scripts; and the two proofs (§2, §3). §7 says where.
