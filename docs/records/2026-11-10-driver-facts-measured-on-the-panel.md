---
status: recorded
date: 2026-11-10
prs: [941]
supersedes:
superseded-by:
---

# RG-D8/RG-D19 PR 1 (#941) measured on the panel, no-worsening only ($27.50 of $35): no class metric worsened (the lowest p_upper is M-GAP's 0.106); four modal leans moved and two proposals with them. LLY's BUY came on a request byte-identical to main's, so it is noise by construction. SMPL's AVOID_TERMINAL came on the one page whose changed row its draws cite: plausibly caused, within one page's noise (p 0.22), and in the direction the change intends. The score's decision: "ships once the moves listed are explained in writing"

**THE APPROVAL.** The operator, relayed by the coordinator on 2026-11-10, verbatim: **"yes to
all"**, with the cap of $35.
- **The ledger:** one budget ledger was opened with the approval text "yes to all (driver facts
  #941 panel run, $35 cap)": `synthesis-eval-driver-facts/ledger-driver-facts.jsonl` (sha256
  `147b1489…3dc65`), in the session family's notes folder.
- **Kept with it, outside the repository:**
  - the registration (`registration-driver-facts.json`, sha256 `c04c4d3d…13fc`);
  - the run folder (`run-driver-facts/`: draws, requests and the score log);
  - the logs.

  The requests carry licensed transcript text and never enter git.
- **The code:** #941 was frozen at `4eab7ec6` for the measurement. The cap was not raised.

**THE RESULT IN SIX LINES.**
- **By the registered rule, #941 passes the no-worsening checks.** No class metric reaches
  p_upper ≤ 0.05 over 30 draws per arm. The score's decision is "ships once the moves listed are
  explained in writing"; §3 is that writing.
- **The class metrics**, BASE → CAND, units summed over the panel:

  | metric | BASE | CAND | p_upper |
  |---|--:|--:|--:|
  | M-ABSENT | 60 | 46 | 0.981 |
  | M-LABEL | 50 | 56 | 0.308 |
  | M-GAP | 2 | 7 | 0.106 |
  | M-PATH | 5 | 2 | 0.949 |
  | M-SIGN | 0 | 0 | 1 |
  | M-ECHO (reported) | 48 | 56 | 0.250 |

  M-ABSENT's fall has p_lower 0.034. It is not a registered target, so it is no claim (§3).
- **Four modal leans moved, two proposals with them.**

  | page | BASE leans | CAND leans | proposal | request |
  |---|---|---|---|---|
  | LLY | bullish 4 / mixed 1 | bullish 5 | none → **BUY** | byte-identical in both arms |
  | SMPL | mixed 2 / bearish 3 | bearish 5 | none → **AVOID_TERMINAL** | 1 row changed |
  | BURL | bullish 3 / mixed 1 | bullish 2 / mixed 2 / mixed-leaning-bullish 1 | none in either arm | byte-identical |
  | ROST | mixed 3 / bullish 2 | bullish 3 / mixed 2 | none in either arm | 2 rows changed |

- **What #941 changes in the request:** six driver rows' values now read UNKNOWN, in the facts
  and the digest. CNXC has 3, ROST 2 and SMPL 1. BURL, LLY and MCK send byte-identical requests in
  both arms.
- **Spend:** $27.5048 of $35. 60 draws: 59 usable, and one BURL BASE draw (draw 4) gave no output
  and cost $0.

## 1. The $0 cross-check, before the ledger

- **The panel rule** yields the frozen six: BURL, CNXC, LLY, MCK, ROST and SMPL.
- **`compare --base origin/main --cand 4eab7ec6`, no transform:** all six requests are IDENTICAL.
  The command refuses ("reaches no page's request").
- **With `--transform driver_facts`:**

  | page | characters added |
  |---|--:|
  | CNXC | 411 |
  | ROST | 224 |
  | SMPL | 41 |
  | BURL, LLY, MCK | 0 |

  - Read line by line, each diff is only the changed rows' `value` and their digest lines.
  - SYSTEM, the tool schema, the model and `max_tokens` are equal on every page.
- **Inputs, by the panel freeze (`bcda7ce3`):**
  - the page blobs `627fe21a` (BURL), `604d559d` (CNXC), `ef07b22f` (LLY), `761787c0` (MCK),
    `a4bf3989` (ROST) and `0b4ff8eb` (SMPL);
  - every transcript, matched by name and sha256;
  - read from the primary checkout's `data/manual/ciq`, read only.
- **Registered before any draw:** `register --no-worsening --draws 5 --transform driver_facts`,
  with a note stating what the comparison covers and what it does not:
  - **Covered:** the one field the prompt reads.
  - **Not covered:** the figures and the locator, which are never sent; and rows a re-extraction
    would draw differently, because Tier B is not replayed.

## 2. How it was scored

- **The `score` CLI refused.** It has no `--ciq-root`, so it reads the assembler checkout's path,
  which does not exist on this Mac (STATE row 53, item 8).
- **So the score ran through `score_run`,** with each panel page and its transcripts read and
  checked by `replay.panel_inputs` (page blob plus every transcript sha256), at the CIQ root the
  capture used. This is the route fix 3b took. The score is appended to the run's `score_log.jsonl`
  with its decision.
- **Per-page units, re-computed with the scorer's own functions** (`draw_units` →
  `score_units`) over the same draws, reproduce the panel totals exactly. They are descriptive:
  the decision reads the panel totals.

| metric | BURL | CNXC | LLY | MCK | ROST | SMPL |
|---|---|---|---|---|---|---|
| M-GAP | 0 → 0 | 0 → 3 | 1 → 1 | 0 → 1 | 1 → 0 | 0 → 2 |
| M-ABSENT | 12 → 9 | 14 → 8 | 0 → 1 | 19 → 18 | 10 → 6 | 5 → 4 |
| M-LABEL | 8 → 12 | 6 → 7 | 7 → 6 | 13 → 13 | 7 → 6 | 9 → 12 |

## 3. The moves, explained

**THE CONTROL INSIDE THE RUN.** BURL, LLY and MCK send byte-identical requests in both arms, so
every difference between their arms is sampling alone. On them:
- BURL's M-LABEL moved 8 → 12 and its M-ABSENT 12 → 9;
- LLY's proposal flipped from none to BUY on one dissent fewer;
- BURL's modal lean moved.

That is the noise floor this measurement is read against: a single page moves by about four
units, and a five-draw proposal flips on one dissent. (STATE row 53, item 5, states the same
property of production's unanimity gate.)

- **LLY: none → BUY.** Its request is byte-identical to main's. The move is noise by
  construction, and #941 cannot have caused it.
- **BURL: lean moved, no proposal in either arm.** Byte-identical requests: noise by construction.
- **ROST: lean moved, no proposal in either arm.**
  - The two changed rows are both "average unit retail (AUR)" values: figure-less phrases
    stitched with "...", now UNKNOWN.
  - No draw in either arm mentions AUR or average unit retail (0 of 5 BASE, 0 of 5 CAND), so the
    move does not trace to the change.
  - It is the size of BURL's move.
- **SMPL: mixed 2 / bearish 3 → bearish 5, so the proposal goes none → AVOID_TERMINAL.**
  - **NOT shown to be noise.** It is explained as plausibly caused.
  - **The changed row.** "Quest salty brand size: over $0.5 billion in retail sales… growing
    double digit" is a bull fact whose quote ("It's over $0.5 billion in retail sales…") does not
    name the brand. The check marks it UNKNOWN, and the synthesis now reads its value as
    unverified. The quote itself is still in the facts.
  - **What the draws do with it.** They still cite it, but less. Mentions of the salty fact in
    bull points went 8 → 6 across the five draws. Both **mixed** draws (BASE 1 and 2) cite it
    twice, and so do two bearish ones (BASE 3, CAND 5). Every draw citing it once is bearish, in
    both arms. This is an association across ten draws, not a demonstration.
  - **How strong.** Bearish 3 of 5 → 5 of 5 has p ≈ 0.22, one-sided (C(8,5)/C(10,5) = 56/252).
    That is within one page's noise, the same as the LLY flip fix 3b explained, and the same flip
    LLY made here with no change at all.
  - **The direction is the one #941 intends.** A bull value the code could not verify against
    its quote is no longer presented as a validated fact.
  - **SMPL's committed page is held** for its Q1 FY27 10-Q (STATE row 36). This is a measured
    panel blob, not a page or a proposal anyone acts on.
- **M-GAP, 2 → 7 (p_upper 0.106; no worsening by the rule).** The rise sits on CNXC (0 → 3),
  SMPL (0 → 2) and MCK (0 → 1); MCK is byte-identical.
  - None of the six CAND hits cites a changed row or an UNKNOWN value.
  - Five frame a valuation-history or acquisition gap: "the multiple sits at the floor of its own
    history", a size not disclosed for CastleHill. The sixth is SMPL's price-elasticity unknown.
  - **Not traced to the change.**
- **M-ABSENT, 60 → 46 (p_lower 0.034).** It is not a registered target, so it is not claimed.
  BURL, on byte-identical requests, moved 12 → 9 of it.

**BOUNDARY.**
- **Population:** the six frozen panel pages at freeze `bcda7ce3`, BASE `origin/main` (`1d0c374c`
  at registration) against CAND `4eab7ec6`, with transform `driver_facts`.
- **Draws:** 5 per arm per page, 60 in all, on 2026-11-10, served model `claude-opus-4-8`.
- **Units:** distinct units per draw, summed over the panel.
- **Mention counts** are a case-insensitive regex over each draw's JSON: "salty", "0.5 billion",
  "$500 million" or "half a billion" for SMPL; "AUR" or "average unit retail" for ROST.
- **p ≈ 0.22** is a one-sided Fisher exact test on one page's 5 + 5 draws, not the registered
  rule's statistic.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **SMPL's proposal move is accepted as explained, not as disproved.**
  - Falsifier: on a fresh registered measurement, SMPL's bearish share rising with UNKNOWN
    driver values beyond one page's noise. The operator weighs it at #941's merge.
- **The measurement covers #941's request change only.** The page pass (PR 3) changes no request
  byte: the synthesis reads the in-memory row at assembly. Its own replay gap is stated in the
  design record, §9.
- **$27.5048 of the $35 approval.** The approval is spent for this design. A second draw needs a
  new registration and a new approval.
