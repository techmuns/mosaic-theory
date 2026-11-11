---
status: recorded
date: 2026-11-11
prs: [983]
supersedes:
superseded-by:
---

# RA-D4 (#983, split from #967) measured on the panel, no-worsening only ($27.32 of $35): no class metric worsens; the modal lean moved on MCK, whose request is byte-identical in both arms, and on SMPL; no proposal moved

**THE APPROVAL.** The operator, relayed by the coordinator on 2026-11-11, verbatim: **"go ahead
with the correct steps as per experts"**. The steps: split #967 into RA-D2 and RA-D4, give each its
own panel check at a $35 cap, merge what passes and stop what fails.
- One budget ledger was opened with the words "go ahead with the correct steps as per experts
  (#967 split: RA-D4 panel check, $35 cap)": `synthesis-eval-ra-d4/ledger-ra-d4.jsonl`, in the
  session family's notes folder.
- The registration, the run folder (`run-ra-d4/`: draws, requests, score, per-page split) and the
  logs are kept there too, outside the repository. The requests carry licensed transcript text and
  never enter git.
- #983 was frozen at `a27072ec` for the measurement. The cap was not raised.
- Since then, #983 has been re-synced twice (`bff33bd0` onto `be6e2206`, then onto `62d682c6`).
  Each merge takes main's code and moves the version row; the PR's own diff in the code the run
  reads is unchanged.

**THE RESULT.**
- **No class metric worsens beyond noise.** The rule is design record §6.1, no-worsening only: no
  class metric may reach p_upper ≤ 0.05, and every lean, proposal or committed-lean move must be
  explained. The lowest p_upper is M-LABEL's, 0.112. The score's decision reads "ships once the
  moves listed are explained in writing".
- **The class metrics,** 30 draws an arm (5 a page):

  | Metric | BASE → CAND | p_lower | p_upper |
  |---|---|---|---|
  | M-ABSENT | 68 → 67 | 0.5 | 0.576 |
  | M-ECHO | 57 → 48 | 0.174 | 0.88 |
  | M-GAP | 6 → 11 | 0.904 | 0.199 |
  | M-LABEL | 50 → 60 | 0.932 | 0.112 |
  | M-PATH | 4 → 1 | 0.167 | 0.979 |
  | M-SIGN | 0 → 0 | 1 | 1 |

- **By page,** each arm's total units over its 5 draws, as the scorer counts them:

  | Page | Request | M-ABSENT | M-ECHO | M-GAP | M-LABEL | M-PATH |
  |---|---|---|---|---|---|---|
  | BURL | identical | 17 → 18 | 8 → 9 | 0 → 0 | 9 → 11 | 1 → 0 |
  | LLY | identical | 3 → 3 | 10 → 11 | 0 → 4 | 6 → 8 | 0 → 0 |
  | MCK | identical | 23 → 18 | 7 → 7 | 1 → 3 | 10 → 13 | 0 → 0 |
  | CNXC | differs | 10 → 14 | 14 → 7 | 3 → 1 | 6 → 6 | 0 → 0 |
  | ROST | differs | 6 → 8 | 7 → 7 | 1 → 0 | 9 → 5 | 1 → 0 |
  | SMPL | differs | 9 → 6 | 11 → 7 | 1 → 3 | 10 → 17 | 2 → 1 |

  The three pages whose requests are byte-identical in both arms are an in-run control. On them,
  M-LABEL goes 25 → 32 and M-GAP 1 → 7. On the three pages the change reaches, M-LABEL goes
  25 → 28 and M-GAP 5 → 4. The counts are stated as measured. This record does not say why they
  moved.
- **Spend:** $27.3239 of $35, 60 calls, all with stop reason `tool_use`, none failed; served
  model `claude-opus-4-8` on every draw.

**THE MOVES, AND WHAT THE RUN SHOWS ABOUT EACH.** Modal lean and the machine's proposal,
BASE → CAND:
- **MCK:** mixed 4 / strongly-bullish 1 → mixed 2 / strongly-bullish 3; no proposal in either.
  **MCK's request is byte-identical in both arms**: every key of the two requests is equal. So
  nothing this change does reaches MCK's synthesis, and its move is the draws' own variation.
- **SMPL:** mixed 3 / strongly-bearish 2 → strongly-bearish 3 / mixed 2; no proposal in either.
  - SMPL's request differs in `user.facts` only (+1,179 characters): four same-day guides join
    the bridge. They are Effective Tax Rate % 25.0 for FY 2026, Gross Margin % 35.10–35.60 for
    FY 2027, Revenue 1,125.89–1,180.15 for FY 2027, and EBITDA 194.25–205.54 for FY 2027, each
    dated as its row's latest guide.
  - **One CAND draw cites one of them.** Draw 3, strongly-bearish, names an unknown: "FY27 is
    only guided to 35.1–35.6%". That range is in CAND's request alone: BASE's carries 35.1 only as
    broker revision values.
  - The other two strongly-bearish CAND draws (1 and 2) cite none of the four added figures.
  - SMPL's FY 2027 revenue decline ("-13% to -17%") is cited in both arms, from facts both share
    (mentions per draw, BASE 2, 8, 4, 8, 4; CAND 7, 7, 0, 4, 0).
- **Held:** BURL (modal mixed in both; its one strongly-bullish draw became mixed), CNXC, LLY,
  ROST.

**WHERE THE CHANGE'S FIGURES ARE CITED,** on the three pages it reaches:
- **CNXC:** CAND draw 1 cites the added FY 2027 net-debt guide, "$3,300.0M", with the Guidance
  sheet as source. The same target is in both arms' transcript ("bring our net debt to below
  $3.3 billion"). The lean held at mixed 5.
- **ROST:** CAND draws 4 and 5 cite the Q4 same-store-sales guide "4%–5%" with the Guidance
  sheet as source. Both arms' transcripts also carry it, and BASE draws cite it from there. The
  lean held.
- **SMPL:** draw 3, as above. This is the only cited figure that appears in no form in BASE's
  request (searched as "35.10", "35.60", "35.1–35.6" and "35.1%").

So on the one page the change reaches where the lean moved (SMPL), one of the three bearish draws
cites a figure the change added. Five draws an arm measures a lean tally, not its cause. Whether
this is enough, against MCK's equal-sized move on a request the change does not touch, is the
reviewer's call under §6.1. This record does not make it.

**WHAT WAS MEASURED.**
- **The arms.** BASE is `origin/main` at the registration, `173b4818`; CAND is #983's head,
  `a27072ec`.
  - Both were captured with the transform `same_day_guides`, which re-reads the catalyst path's
    `guidance_bridge` and `guidance_bridge_rows` from each page's own CIQ folder (the primary
    checkout's `data/manual/ciq/`, read only) at the committed page's reference date.
  - The registration (`5bc72d2b9c16a660`) records every file's sha256.
- **Covered:** the guidance bridge and its rows on CNXC, ROST and SMPL, whose requests differ.
- **Not covered:** BURL's committed bridge, which predates A-D8's block discovery and is left as
  committed in both arms; the dividend fields (RA-D2, measured on its own,
  `docs/records/2026-11-11-ra-d2-measured-on-the-panel.md`); pages outside the panel; any other
  field a re-assembly would draw differently.
- **The $0 compare, before the draws:** CNXC +1,735, ROST +1,194 and SMPL +1,179 characters, in
  `user.facts` only. BURL, LLY and MCK are identical.

**HOW VERIFIED.**
- **The draw and the score.** The run was drawn once under registration `5bc72d2b9c16a660`. It was
  scored at $0 by `score_run` at `a27072ec`, against the approval's ledger, which records one run
  under the sha, with 60 draws.
- **The score's inputs.** The score CLI reads transcripts from a default CIQ root that is absent on
  this machine. So the score ran through `score_run`, with each page's inputs from
  `replay.panel_inputs` at the primary's CIQ folder. Those are the CLI's own checks: the page by
  its frozen blob, every transcript by its sha256.
- **The per-page split** repeats `score_run`'s own loop (`metrics.score_units` over each usable
  draw, with its echo index). Its totals equal the score's for every metric.
- **The citation search.** For each guide the CAND request adds, its figures are taken as
  written and searched in every CAND draw's raw output.
  - A hit's figure was then searched in BASE's whole request, transcripts included, in other forms
    too ("$3.3 billion").
  - ROST's "4%–5%" was matched by its phrasing, because a bare "4" matches any draw.

**BOUNDARY.**
- The six panel pages at the panel freeze (BURL, CNXC, LLY, MCK, ROST, SMPL), 5 draws an arm a
  page, on one served model, as the draws record.
- The counts are the scorer's units at scorer sha `b782bff0`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- #983 stays open and STOPPED until it is reviewed. This record does not merge it.
- A new run is a new approval: this one's ledger is spent to $27.32 of $35.
- Nothing here was tuned on the result. The registered rule and the frozen panel decided it.
