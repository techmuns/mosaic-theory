---
status: recorded
date: 2026-11-11
prs: [967]
supersedes:
superseded-by:
---

# #967 (RA-D2, RA-D4) measured on the panel, no-worsening only ($30.54 of $35): it DOES NOT SHIP. M-ABSENT worsens beyond noise, 45 → 70 (p_upper 0.018), and the modal lean moved on four of the six pages, MCK's taking its proposal from BUY to none

**THE APPROVAL.** The operator, relayed by the coordinator on 2026-11-10, verbatim: **"yes to all,
merge them one at a time"**, covering #967's panel check at a $35 cap.
- One budget ledger was opened with the words "yes to all (#967 panel check, $35 cap)":
  `synthesis-eval-ra-d2-d4/ledger-ra-d2-d4.jsonl`, in the session family's notes folder.
- The registration, the run folder (`run-ra-d2-d4/`: draws, requests, score log) and the logs are
  kept there too, outside the repository. The requests carry licensed transcript text and never
  enter git.
- #967 was frozen at `4b38b7a2` for the measurement. The cap was not raised.

**THE RESULT.**
- **By the registered rule, #967 does not ship.** The rule is design record §6.1, no-worsening
  only: no class metric may reach p_upper ≤ 0.05, and every lean, proposal or committed-lean move
  must be explained. The score's decision reads "does not ship".
- **The class metrics,** 30 draws an arm (5 a page):

  | Metric | BASE → CAND | p_upper | |
  |---|---|---|---|
  | M-ABSENT | 45 → 70 | 0.0178 | **blocks** |
  | M-GAP | 7 → 10 | 0.295 | |
  | M-PATH | 3 → 6 | 0.278 | |
  | M-LABEL | 55 → 52 | 0.744 | |
  | M-ECHO | 51 → 51 | 0.547 | reported |
  | M-SIGN | 0 → 0 | 1 | |

- **M-ABSENT by page,** each draw's count of absent-figure units, as the scorer counts them:

  | Page | BASE (5 draws) | CAND (5 draws) | Sum |
  |---|---|---|---|
  | BURL | 2, 4, 1, 1, 3 | 4, 9, 2, 3, 3 | 11 → 21 |
  | CNXC | 2, 1, 3, 1, 4 | 4, 2, 2, 1, 4 | 11 → 13 |
  | LLY | 0, 0, 0, 0, 0 | 0, 0, 0, 0, 1 | 0 → 1 |
  | MCK | 2, 2, 2, 1, 4 | 4, 2, 6, 8, 5 | 11 → 25 |
  | ROST | 1, 0, 1, 2, 0 | 1, 1, 2, 2, 0 | 4 → 6 |
  | SMPL | 2, 0, 3, 2, 1 | 0, 2, 1, 1, 0 | 8 → 4 |

  The rise is MCK's (+14) and BURL's (+10). By the scorer's family, it is mostly figures found
  only in the transcript: MCK's "transcript-only" hits go 8 → 19, and BURL's 3 → 11 with its quoted
  ones 7 → 13. These counts are stated as measured. This record does not say why they rose.
- **Leans moved on four pages** (BASE → CAND, modal lean and the machine's proposal):
  - **MCK:** strongly-bullish 5 → strongly-bullish 3 / mixed 2; **proposal BUY → none**;
  - **BURL:** mixed 4 / strongly-bullish 1 → mixed 2 / strongly-bullish 3; no proposal in either;
  - **ROST:** strongly-bullish 3 / mixed 2 → mixed 3 / strongly-bullish 2; no proposal in either;
  - **SMPL:** strongly-bearish 3 / mixed 2 → mixed 3 / strongly-bearish 2; no proposal in either.

  CNXC and LLY held their leans. The rule asks for each move to be explained in writing before
  review. With M-ABSENT blocking, no explanation is offered here: the change does not ship either
  way.
- **Spend:** $30.5374 of $35, 60 calls, none failed.

**WHAT WAS MEASURED.**
- **The arms.** BASE is #957's head at the registration, `873fbe45`; CAND is #967's, `4b38b7a2`.
  Both were captured with the transform `dividend_and_same_day_guides`, which re-reads the fields
  from each page's own CIQ folder (the primary checkout's `data/manual/ciq/`, read only). The
  registration records every file's sha256.
- **Covered:** `return_ratios` (the Dividend/sh row from the Income Statement, its citation, MCK's
  LTM note) and `key_ratios` (the dividend status and its citation) on all six pages; the guidance
  bridge and its rows (every period guided on the latest date) on CNXC, LLY, MCK, ROST and SMPL.
- **Not covered:** BURL's guidance, whose committed bridge predates A-D8's block discovery, so no
  code at the base rebuilds it (left as committed in both arms); pages outside the panel; any
  other field a re-assembly would draw differently.
- **The $0 compare, before the draws.** Every panel page's request differs in `user.facts` only;
  SYSTEM and the tool schema are equal. In characters: BURL +104, CNXC +1,798, LLY +63, MCK +290,
  ROST +1,256, SMPL +1,283.

**HOW VERIFIED.**
- The run was drawn once under registration `dc9a6dad36abd0eb` and scored at $0 by `score_run` at
  `4b38b7a2`, against the approval's ledger. The ledger records one run under the sha, with 60
  draws.
- The score CLI reads transcripts from a default CIQ root that is absent on this machine, so the
  score was run through `score_run` with each page's inputs from `replay.panel_inputs` at the
  primary's CIQ folder. Those are the CLI's own checks: the page by its frozen blob, every
  transcript by its sha256.
- The per-page M-ABSENT split repeats `score_run`'s own loop (`metrics.score_units` over each
  usable draw, with its echo index); its totals equal the score's, 45 and 70.

**BOUNDARY.**
- The six panel pages at the panel freeze (BURL, CNXC, LLY, MCK, ROST, SMPL); 5 draws an arm a
  page; one served model, as the draws record.
- The counts are the scorer's units at scorer sha `c6035804`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- #967 stays open and STOPPED. It is not merged on this result.
- Whether to change #967 and measure again, keep only part of it, or close it is the operator's
  call. A new run is a new approval: this one's ledger is spent to $30.54 of $35.
- Nothing here was tuned on the result. The registered rule and the frozen panel decided it.
