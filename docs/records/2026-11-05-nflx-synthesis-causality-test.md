---
status: open
date: 2026-11-05
prs: []
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

*(filled after the run — nothing below this line existed when the pre-registration was pushed)*

**BOUNDARY.** Population: NFLX only, the 2026-11-05 inputs of PR #918 (page `0dbe8f97`, CIQ
transcripts Q2 and Q3 2026). Unit: one draw of `claude-opus-4-8` through `synthesize`. Control: the
build log's 5 draws (2026-11-05). Variants: 5 draws each, measured 2026-11-05 at code `3e97ee7d`.
Points are counted over bear_points claims only for M3; over every prose unit otherwise.
