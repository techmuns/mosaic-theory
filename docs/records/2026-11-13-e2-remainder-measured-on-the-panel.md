---
status: recorded
date: 2026-11-13
prs: [1027]
supersedes:
superseded-by:
---

# The E2 remainder (#1027) measured on the panel, no-worsening only ($29.17 of $35.28): no class metric worsens, the nearest being M-ABSENT (77 → 99, p_upper 0.076); no page's modal lean or proposal moves; drawn once on `anthropic` 0.112.0, from the registration's scorer ref `96d0cfea` because a comment-only change moved the scorer's fingerprint after registration

**THE APPROVAL.**
- **The operator, 2026-11-13, verbatim:** **"Post, then register and draw (Recommended)"**.
- **The cap ruling, verbatim:** **"Estimate +20%, max $40 (Recommended)"**. The estimate was
  $29.40, so the cap is $35.28.
- **The announcement:** posted on #1004 (issuecomment-6849637841) before the registration.
- **The budget:** one ledger, opened at $35.28 with those words, for this check alone.

**THE DESIGN** (RUNBOOKS §n, a retrospective `register --from-impact`).
- **The export:** `pr1027-0d8a2a43-880435fc`, whose `manifest.json` has sha256
  `392b5e980a8b480ef1cb5a47e73b3f1869179f55e99012d8302052ea6b9041bd`.
  - It holds fresh $0 builds of the six panel pages, each made with its own arm's code.
  - All 12 arms are recapture-equal.
  - It is kept outside every repository, because requests carry licensed transcript text.
- **The registration:** sha256 `e3a37305c5d819e221a6b298f7f631f63e3fd8164428d0025feca1ce3f2c675f`.
  - Its fields:
    - base `0d8a2a43`, cand `880435fc` (#1027; its head `97231c6c` adds docs only);
    - pages BURL, CNXC, LLY, MCK, ROST and SMPL;
    - 5 draws per page per arm;
    - alpha 0.05, no-worsening only;
    - held out: CNXC and ROST;
    - `scorer_ref` `96d0cfea`, scorer fingerprint `b8ed9fec1e79…`.
  - Its `registered` row reached main in #1055 (`3d195fcd`) before any draw (RG-D14).
  - There is no target. The change corrects period labels and adds a checked-absent going-concern
    line, and no registered metric reads either as an improvement.
- **What moves in the requests**, in characters added, as `run-compare` printed them:

  | Page | facts | primary source | total |
  |---|---|---|---|
  | BURL | +4 | +77 | +81 |
  | CNXC | 0 | +73 | +73 |
  | LLY | 0 | +83 | +83 |
  | MCK | 0 | +73 | +73 |
  | ROST | 0 | +73 | +73 |
  | SMPL | +4 | +176 | +180 |

  The system prompt is byte-equal in the two arms on all six pages.

**WHY THE DRAW RAN FROM `96d0cfea`, NOT FROM MAIN.**
- **The refusal.** The first `run-compare --paid` ran from a clean checkout of main at `3d195fcd`.
  It refused before any draw: "the scorer here (e4c0827d24b9) is not the registered scorer
  (b8ed9fec1e79)". It spent nothing and wrote nothing:
  - the ledger has no row from it;
  - the run folder did not exist before the draw that followed.
- **The cause.** #1046 (`01ab6923`) merged between the registration's scorer ref and `3d195fcd`. It
  reworded a comment in `vinci/dossier/schemas.py`, which is one of the 16 scorer files.
  - **The change is byte-level only, with no behaviour change.** Six comment lines at line 2472
    became five comment lines, and no other line changed.
  - The module's AST, docstrings included, is identical at `96d0cfea` and `3d195fcd`.
  - The fingerprint hashes bytes, so it moved anyway.
- **The coordinator's call.** The coordinator chose to draw and score from a clean checkout at
  `96d0cfea`, the registration's recorded `scorer_ref`.
  - That checkout's fingerprint is `b8ed9fec…`, equal to the registered one, and was checked
    before the draw.
  - RUNBOOKS §n step 5 scores "from the registered scorer"; the draw and the score both ran there.

**A SLIP OF MINE, CAUGHT BY THE REFUSAL ABOVE.**
- **What I checked.** Before the first attempt, I checked whether any scorer file changed from
  `96d0cfea` to `3d195fcd`, with `git diff 96d0cfea 3d195fcd -- $FILES` in zsh.
- **What went wrong.** zsh does not word-split an unquoted scalar. The 16 paths reached `git diff`
  as ONE pathspec that matched nothing, so the diff printed nothing, and I read the empty output as
  "no scorer file changed". That was wrong.
- **The check redone.** With an array (`files=( … ); git diff … -- "${files[@]}"`) or with
  `${=FILES}`, the same check shows `vinci/dossier/schemas.py` (+5 −6) and one commit, `01ab6923`.
- **The lesson.** In zsh, pass a list as `${=var}` or as an array. And an empty filter result is a
  claim about the filter first: count what the pathspec matches before reading "nothing changed"
  from it.

**THE RUN** (`run-compare --paid`, from the `96d0cfea` checkout).
- **How it ran:**
  - one process, run once, on the shared venv;
  - `.env` was linked for this run only and unlinked after it, and is confirmed absent;
  - the draw calls only the Anthropic API: `vinci/evals/` names neither Polygon nor Tiingo, and
    no price was pulled.
- **The draws:** 60 (6 pages × 2 arms × 5).
  - Every one stopped on `tool_use`, and `claude-opus-4-8` served all 60.
  - None was unusable.
- **The SDK:** every one of the 60 draw rows states `sdk_version` **0.112.0**, so both arms ran on
  one SDK.
  - That is the shared venv's version (STATE row 62; the lock pins 2.6.0, and #1049 found request
    bodies byte-identical between the two).
  - `replay.one_sdk` admits the run.
- **The cost: $29.1654**, from the run's own ledger: 0.8% under the $29.40 estimate, with $6.11 of
  the $35.28 cap left.
  - Cache writes: 2,088,834 tokens. Cache reads: 8,355,336. Uncached input: 1,440. Output: 477,011.

  | Page | BASE | CAND |
  |---|---|---|
  | BURL | $2.3046 | $2.3461 |
  | CNXC | $2.1065 | $2.1638 |
  | LLY | $2.9197 | $3.0047 |
  | MCK | $2.3944 | $2.3199 |
  | ROST | $2.4000 | $2.4225 |
  | SMPL | $2.4550 | $2.3282 |

**THE SCORE, at $0** (`vinci.evals score`, from the same `96d0cfea` checkout, one score-log line
at 2026-11-13T17:44:54+0530).

| Metric | BASE | CAND | p_lower | p_upper | held out (CNXC, ROST) |
|---|---|---|---|---|---|
| M-ABSENT | 77 | 99 | 0.942 | 0.0762 | 26 → 32 |
| M-ECHO | 55 | 63 | 0.850 | 0.211 | 17 → 22 |
| M-LABEL | 24 | 24 | 0.617 | 0.617 | 7 → 6 |
| M-PATH | 1 | 2 | 0.889 | 0.500 | 0 → 2 |
| M-SIGN | 0 | 0 | 1 | 1 | 0 → 0 |

- **No class metric worsens at p_upper ≤ 0.05.** The decision is **"ships"**, with no reasons
  listed.
- **M-GAP is not scored.** It runs only on the pages whose gap types were frozen on the committed
  page blob, and an impact arm is a fresh build with no blob. It is barred as a target in any case
  (RG-D13).

**M-ABSENT IS THE NEAREST TO THE LINE, so here it is in full.**
- **What it counts:** a figure or a quoted phrase in the prose that the page's facts do not state.
  It is either in the transcripts only, or nowhere.
- **The rise:** 77 → 99 (+22), at p_upper 0.076, which the registered rule does not read as a
  worsening.

Per page (units with a hit, summed over the 5 draws):

| Page | BASE | CAND | change |
|---|---|---|---|
| BURL | 19 | 29 | +10 |
| CNXC (held out) | 17 | 20 | +3 |
| LLY | 0 | 2 | +2 |
| MCK | 23 | 27 | +4 |
| ROST (held out) | 9 | 12 | +3 |
| SMPL | 9 | 9 | 0 |

By kind of hit (unit counts per family; one unit can fall under two families):

| Family | BASE | CAND |
|---|---|---|
| quoted phrase, in no source | 9 | 20 |
| quoted phrase, in the transcripts only | 9 | 20 |
| figure, in the transcripts only | 41 | 49 |
| figure, in no source | 21 | 15 |

- **This run cannot say whether the change causes the rise.** The change adds 73 to 180 characters
  of period labels and a going-concern line to each request, and none of those words are
  management's.
- **The counts above are the measurement, at 5 draws per arm.** If a later check on these pages
  reads M-ABSENT again, this is the number to compare it with.

**THE REST, PER PAGE** (units with a hit, BASE → CAND, over the 5 draws).

| Page | M-LABEL | M-PATH | M-ECHO | M-SIGN |
|---|---|---|---|---|
| BURL | 3 → 6 | 0 → 0 | 7 → 9 | 0 → 0 |
| CNXC (held out) | 1 → 2 | 0 → 0 | 9 → 9 | 0 → 0 |
| LLY | 4 → 5 | 0 → 0 | 14 → 15 | 0 → 0 |
| MCK | 5 → 2 | 0 → 0 | 5 → 7 | 0 → 0 |
| ROST (held out) | 6 → 4 | 0 → 2 | 8 → 13 | 0 → 0 |
| SMPL | 5 → 5 | 1 → 0 | 12 → 10 | 0 → 0 |

These per-page counts come from a $0 script that repeats `score_run`'s loop through the same
library calls. It reproduces the scorer's five totals exactly.

**LEANS AND PROPOSALS.** No page's modal lean moves, and no proposal moves.

| Page | BASE leans | CAND leans | Proposal |
|---|---|---|---|
| BURL | mixed 5 | mixed 5 | none → none |
| CNXC | mixed 5 | mixed 5 | none → none |
| LLY | strongly-bullish 5 | strongly-bullish 5 | BUY → BUY |
| MCK | mixed 4, strongly-bullish 1 | mixed 3, strongly-bullish 2 | none → none |
| ROST | mixed 3, strongly-bullish 2 | mixed 4, strongly-bullish 1 | none → none |
| SMPL | strongly-bearish 3, mixed 2 | strongly-bearish 3, mixed 2 | none → none |

The panel's committed-lean draws are 11 in each arm: LLY 5, MCK 1 → 2, ROST 2 → 1, SMPL 3.

**EVERY M-ECHO PHRASE IN CAND ONLY, as `score` printed them.**
- **What these are:** 5-word runs found in the request's instructions and in none of its facts or
  transcripts. By construction, no echo phrase is transcript text.
- The phrases, with their pages:
  - "justified vs residual question for" (BURL)
  - "from pre tax income a" (CNXC, SMPL)
  - "can fall while ebitda rises" (CNXC)
  - "expectations embedded in the price" (LLY, ROST)
  - "a bull nor a bear" (LLY)
  - "leverage leaving reinvestment capacity intact" (LLY)
  - "and x net leverage leaving" (LLY, MCK)
  - "yes latest q ocf and" (LLY)
  - "the names own resolved past" (MCK)
  - "multiple at its own history" (MCK)
  - "it is the real signal" (ROST)
  - "the quality is real and" (ROST)
  - "read beside the forward ntm" (ROST)
  - "the cause named at the" (SMPL)

**WHAT THIS DOES NOT COVER.**
- **No target.** The run shows only that no class metric worsened beyond the registered line. It
  does not measure whether the corrected period labels or the going-concern line improve a read.
- **Only the six panel pages.** #1027's cross-setup section D lists 103 moves on 25 built pages.
  The other pages' requests change at their next re-assembly, unmeasured here.
- **5 draws per arm** resolve a modal lean only coarsely. A move of 1 or 2 draws, like MCK's and
  ROST's here, is within what an unchanged request shows (the RE2-D16 record,
  `docs/records/2026-11-11-re2-d16-measured-on-the-panel.md`).

**THE `drawn` ROW.**
- **What this record commits** is the one `drawn` row the draw's claim appended at `96d0cfea`, byte
  for byte. It is appended to main's `docs/evals/registrations.jsonl` after the `registered` row.
- **Its approval field** is `dfd1dae1…`. That equals the `registered` row's approval and the sha256
  of the ledger's first line.

**BOUNDARY.**
- **Pages:** the six panel pages, as fresh builds from the impact export above.
- **Draws:** 5 per page per arm, 60 in all, drawn once under registration `e3a37305…` and claimed
  at 2026-11-13T10:43:49Z.
- **Code:** base `0d8a2a43`, cand `880435fc`, scorer `96d0cfea` (fingerprint `b8ed9fec…`).
- **Counts:** every count is the number of units with a hit, summed over a page-arm's 5 draws.
- **Cost:** $29.1654 of the $35.28 approval, from the run's own ledger.
- **SDK:** `anthropic` 0.112.0, as stated by all 60 draw rows.
- **Kept outside the repo:** the requests, draws, score log and ledger, under
  `/Users/mac/dev/panel-exports/pr1027-run/`.
