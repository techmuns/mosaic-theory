---
status: recorded
date: 2026-11-11
prs: [961]
supersedes:
superseded-by:
---

# RE2-D16's covenant fence (#961) measured on the panel, no-worsening only ($25.79 of $35): no class metric worsened (the lowest p_upper is M-ECHO's 0.10), no proposal moved; three modal leans moved and are explained here

**THE APPROVAL.** The operator, 2026-11-11, verbatim: **"go ahead with the correct steps as per
experts"**. The coordinator relayed it and named the step as the six-page panel check, with the
approval text **"go ahead with the correct steps as per experts (#961 panel check, $35 cap)"**.
- One budget ledger was opened with those words and a $35 cap. It belongs to this check alone.
- One registration was drawn once: no-worsening, since the change removes facts and adds no label,
  so no target can fire.

**THE DESIGN** (RUNBOOKS §n).
- **The transform:** `covenant_value_figures` (`vinci/evals/variants.py`, #961). It re-runs each
  ref's own fence on the page's stored covenant rows and rebuilds the `covenant_terms` digest the
  synthesis reads. `tests/test_evals_covenant_transform.py` pins it equal to what
  `_extract_from_exhibit` writes for the same stored answer.
- **The $0 compare first:**
  - CNXC differs: `user.facts` −117 characters, 5 lines. Its governing interest line leaves the
    digest.
  - SMPL differs: `user.facts` −147 characters, 5 lines. Its interest line and an "amended by"
    note leave the digest.
  - BURL, LLY, MCK and ROST are identical, and the system prompt is equal on all six.
  - Re-run at `946943ec` vs `4c2e02f2` after the PR's re-sync: the same result.
- **The registration:** sha256 `57125a4667c30ab805b156a5dea3f8fd7cc013b4612cc8a00fa3e1b83baeea43`.
  - base `origin/main`, resolved at registration to `1d6c7d9f`; cand `18c8549f`;
  - the frozen panel BURL, CNXC, LLY, MCK, ROST, SMPL;
  - 5 draws per condition, alpha 0.05;
  - every request's bytes pinned.
- **The run:** `run-compare --paid`, 60 draws (6 pages × 2 arms × 5), every one `tool_use`, served
  by `claude-opus-4-8`. Cost **$25.7946**. The ledger reads $25.79 of $35.

**THE SCORE, at $0** (`compare.score_run`, one score-log line at 2026-11-11 09:52 +05:30).

| Metric | BASE | CAND | p_lower | p_upper |
|---|---|---|---|---|
| M-ABSENT | 55 | 63 | 0.753 | 0.298 |
| M-ECHO | 52 | 65 | 0.933 | 0.100 |
| M-GAP | 8 | 10 | 0.738 | 0.416 |
| M-LABEL | 56 | 54 | 0.436 | 0.685 |
| M-PATH | 2 | 3 | 0.833 | 0.500 |
| M-SIGN | 0 | 0 | 1 | 1 |

- **No class metric worsens at p_upper ≤ 0.05.** The lowest is M-ECHO's 0.10.
- **No page's proposal moves.** LLY is BUY → BUY; the other five are none → none.
- **The decision:** "ships once the moves listed are explained in writing". Three modal leans moved.

**THE THREE LEAN MOVES, EXPLAINED.**
- **MCK** went mixed 4 / strongly-bullish 1 → mixed 1 / strongly-bullish 4. **ROST** went mixed 4 /
  strongly-bullish 1 → strongly-bullish 3 / mixed 2.
  - Both requests are BYTE-IDENTICAL in the two arms (the $0 compare above), so neither move can
    come from this change. They are the noise floor of a 5-draw modal lean: it moves by 2 to 3
    draws with nothing changed.
- **SMPL** went strongly-bearish 4 / mixed 1 → mixed 3 / strongly-bearish 2. Its request does differ:
  the fence withholds its interest line and an "amended by" note from the covenant digest.
  - The move is 2 draws of 5. That is the size of ROST's identical-request move, and smaller than
    MCK's.
  - The three CAND draws that lean mixed give their reasons as a strong balance sheet, a near-floor
    multiple and intact solvency. Both arms' requests carry all three, and BASE draw 2 leaned mixed
    on the same ground.
  - Three CAND draws mention covenants. Each says the covenant terms cannot be verified from the
    facts, which is the withheld line read as an absence. That points toward caution, not toward a
    lighter read.
  - So the move is not distinguishable from the variance the two unchanged pages show.
- **The panel's committed-lean count** is not flagged by the score.

**WHAT THIS DOES NOT COVER.**
- **No target.** The run shows only that nothing worsened. Whether withholding an unverifiable term
  improves a read is unmeasured.
- **Only the two panel pages whose digest moves.** On the panel the fence also withholds BURL's 2
  terms and MCK's 1, but neither is a governing term, so neither request moves. Off the panel it
  withholds terms on 9 pages: EPAM, FUBO, IT, NCNO, NKE, PARR, UBER, VRRM and WERN. Their requests
  change at their next re-assembly, unmeasured here.
- **CAND is scored against BASE's layer,** as in fix 3b (STATE row 53, item 6, deferred).
- **`score` takes no `--ciq-root`.** As in fix 3b's record §6, the first `score` invocation was
  refused before scoring ("BURL: transcripts on disk [] differ from the panel"). It was then run once
  through the same `compare.score_run`, with `replay.panel_inputs` reading the CIQ root
  `run-compare` read. Every page blob and transcript sha256 was checked against the freeze.

**BOUNDARY.**
- **Pages:** the frozen panel of six (freeze `bcda7ce3`).
- **Draws:** 5 per page per arm, 60 in all, drawn once under one registration.
- **Code:** base `1d6c7d9f`, cand `18c8549f` (#961 after its first re-sync onto main). #961 merged
  to main as `d9dd48f5` after this check.
- **Cost:** $25.7946 of the $35 approval, from the run's own ledger.
- **Date:** 2026-11-11.

**WHAT IT COSTS / WHAT IS ACCEPTED.** A 5-draw modal lean moves by 2 to 3 draws on an unchanged
request, so this design cannot show a lean move of that size caused by a change. *Falsifier:* a
re-assembled SMPL page whose lean moves, with its synthesis citing the withheld covenant line as the
reason.
