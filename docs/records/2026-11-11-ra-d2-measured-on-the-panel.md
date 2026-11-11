---
status: recorded
date: 2026-11-11
prs: [981]
supersedes:
superseded-by:
---

# RA-D2 (#981, split from #967) measured on the panel, no-worsening only ($30.28 of $35): no class metric worsens, so it is not blocked; the modal lean moved on five of the six pages, LLY's taking its proposal from none to BUY, and no draw in either arm mentions the dividend

**THE APPROVAL.** The operator, relayed by the coordinator on 2026-11-11, verbatim: **"go ahead
with the correct steps as per experts"**. The steps: split #967 into RA-D2 and RA-D4, give each its
own panel check at a $35 cap, merge what passes and stop what fails.
- One budget ledger was opened with the words "go ahead with the correct steps as per experts
  (#967 split: RA-D2 panel check, $35 cap)": `synthesis-eval-ra-d2/ledger-ra-d2.jsonl`, in the
  session family's notes folder.
- The registration, the run folder (`run-ra-d2/`: draws, requests, score) and the logs are kept
  there too, outside the repository. The requests carry licensed transcript text and never enter
  git.
- #981 was frozen at `9ae02bac` for the measurement. The cap was not raised.

**THE RESULT.**
- **No class metric worsens beyond noise.** The rule is design record §6.1, no-worsening only: no
  class metric may reach p_upper ≤ 0.05, and every lean, proposal or committed-lean move must be
  explained. The lowest p_upper is M-ECHO's, 0.181. The score's decision reads "ships once the
  moves listed are explained in writing".
- **The class metrics,** 30 draws an arm (5 a page):

  | Metric | BASE → CAND | p_lower | p_upper |
  |---|---|---|---|
  | M-ABSENT | 53 → 38 | 0.0724 | 0.953 |
  | M-ECHO | 49 → 58 | 0.874 | 0.181 |
  | M-GAP | 6 → 6 | 0.613 | 0.613 |
  | M-LABEL | 55 → 59 | 0.815 | 0.296 |
  | M-PATH | 6 → 0 | 0.0123 | 1 |
  | M-SIGN | 0 → 0 | 1 | 1 |

  This run registered no target, so a fall (M-PATH 6 → 0, M-ABSENT 53 → 38) is reported, never
  claimed as an improvement.
- **By page,** each draw's count of units, as the scorer counts them:

  | Page | M-ABSENT BASE | M-ABSENT CAND | M-ECHO BASE → CAND | M-PATH BASE → CAND |
  |---|---|---|---|---|
  | BURL | 2, 1, 0, 4, 2 (9) | 6, 2, 2, 1, 3 (14) | 6 → 10 | 2 → 0 |
  | CNXC | 1, 1, 2, 3, 2 (9) | 2, 2, 0, 1, 4 (9) | 5 → 7 | 1 → 0 |
  | LLY | 0, 0, 0, 0, 1 (1) | 0, 0, 0, 0, 0 (0) | 13 → 11 | 0 → 0 |
  | MCK | 4, 6, 4, 6, 3 (23) | 2, 1, 1, 2, 3 (9) | 11 → 16 | 0 → 0 |
  | ROST | 0, 2, 1, 1, 0 (4) | 0, 2, 0, 0, 1 (3) | 5 → 3 | 1 → 0 |
  | SMPL | 2, 1, 0, 2, 2 (7) | 0, 0, 2, 1, 0 (3) | 9 → 11 | 2 → 0 |

  These are stated as measured. This record does not say why they moved.
- **Spend:** $30.2778 of $35, 60 calls, all with stop reason `tool_use`, none failed; served
  model `claude-opus-4-8` on every draw.

**THE MOVES, AND WHAT THE RUN SHOWS ABOUT EACH.** The rule asks for each move to be explained in
writing before review. Modal lean and the machine's proposal, BASE → CAND:
- **BURL:** mixed 3 / strongly-bullish 2 → strongly-bullish 3 / mixed 2; no proposal in either.
- **LLY:** strongly-bullish 4 / mixed 1 → strongly-bullish 5; **proposal none → BUY**. The proposal
  needs every draw to agree (`verdict.derive_proposal`, `draws_unanimous`), so BASE's one mixed
  draw withheld it and CAND's five agreeing draws make it.
- **MCK:** strongly-bullish 4 / mixed 1 → mixed 3 / strongly-bullish 2; no proposal in either.
- **ROST:** mixed 4 / strongly-bullish 1 → strongly-bullish 3 / mixed 2; no proposal in either.
- **SMPL:** mixed 3 / strongly-bearish 2 → strongly-bearish 3 / mixed 2; no proposal in either.
- CNXC held at mixed 5.

What the run can show about these moves:
- **What changed in the request.** Of each request's keys, only `messages` differs: SYSTEM and the
  tool schema are equal on every page. Within the message, `user.facts` differs by the dividend
  fields only:
  - the Dividend/sh row of the ratio table, whose base cells were the Ratios sheet's growth rates
    and are now the Income Statement's level (LLY's base 0.02 … 0.15 becomes 2.08, 2.25 …);
  - where CIQ writes 'NA', a cell that read "none" reads "—", with the table's note saying so;
  - on a non-payer (BURL, SMPL), key ratios' "dividend: none" becomes "dividend: not stated (the
    Income Statement reads 'NA')".

  In characters: BURL +305, CNXC +209, LLY +63, MCK +292, ROST +62, SMPL +309.
- **No draw cites what changed.** Searched every draw's output, all 60 in both arms, for
  "dividend", "payout", "DPS" and "Dividend/sh": 0 mentions in either arm. No point, twin,
  decisive question, unknown or lean sentence in either arm uses the dividend fields.
- **The moves do not share a direction.** BURL, LLY and ROST move toward strongly-bullish; MCK
  toward mixed; SMPL toward strongly-bearish. Each is one or two draws of five.

So the run shows no point that carries the changed fields into a lean. It cannot show what moved
the leans: five draws an arm measures a lean tally, not a cause. Whether this explanation is
enough, LLY's proposal above all, is the reviewer's call under §6.1. This record does not make it.

**WHAT WAS MEASURED.**
- **The arms.** BASE is `origin/main` at the registration, `2b9b766c`; CAND is #981's head,
  `9ae02bac`.
  - Both were captured with the transform `dividend_level`, which re-reads `return_ratios` and
    `key_ratios` from each page's own CIQ folder (the primary checkout's `data/manual/ciq/`, read
    only).
  - The registration (`b29121ebdc675bd3`) records every file's sha256.
- **Covered:** `return_ratios` (the Dividend/sh row from the Income Statement, its citation, its
  'NA' and LTM notes) and `key_ratios` (the dividend status and its citation) on all six pages.
- **Not covered:** pages outside the panel; any other field a re-assembly would draw differently.
- **The $0 compare, before the draws:** every panel page's request differs in `user.facts` only,
  as above.

**HOW VERIFIED.**
- **The draw and the score.** The run was drawn once under registration `b29121ebdc675bd3`. It was
  scored at $0 by `score_run` at `9ae02bac`, against the approval's ledger, which records one run
  under the sha, with 60 draws.
- **The score's inputs.** The score CLI reads transcripts from a default CIQ root that is absent on
  this machine. So the score was run through `score_run`, with each page's inputs from
  `replay.panel_inputs` at the primary's CIQ folder. Those are the CLI's own checks: the page by
  its frozen blob, and every transcript by its sha256.
- **The per-page split** repeats `score_run`'s own loop (`metrics.score_units` over each usable
  draw, with its echo index). Its totals equal the score's: 53 and 38, 49 and 58, 6 and 0.
- **The dividend search** reads each draw's raw output as JSON text, case-insensitively.

**BOUNDARY.**
- The six panel pages at the panel freeze (BURL, CNXC, LLY, MCK, ROST, SMPL), 5 draws an arm a
  page, on one served model, as the draws record.
- The counts are the scorer's units at scorer sha `0e8871ab`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- #981 stays open and STOPPED until it is reviewed. This record does not merge it.
- A new run is a new approval: this one's ledger is spent to $30.28 of $35.
- Nothing here was tuned on the result. The registered rule and the frozen panel decided it.
