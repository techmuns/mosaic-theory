---
status: recorded
date: 2026-11-11
prs: [950]
supersedes:
superseded-by:
---

# The vote rule's independence measurement (paid, $96.70 of $110): independence is NOT falsified — Pearson's dispersion test reads X² 11.58 on 15 df, p 0.71, VIF 0.77 — so the design's binomial tables stand and its implementing PR may follow. Every build opened uncached, one draw of 240 carried no lean, and no rule flipped between builds on this panel. Found beside it, exploratory: LLY's request after #930 reads 39 of 40 bullish, against 7 of 10 before it

**THE APPROVAL.**
- **The operator, 2026-11-10, verbatim:** **"decide as per the expert team"**. The coordinator chose under that delegation: Option A + C(iii) + C(iv), with this measurement at four builds a page and a **$110 cap** (`docs/records/2026-11-10-the-proposal-vote-rule-design.md` §9).
- **The coordinator started step 3 after #958 merged.** The operator's merge approval, 2026-11-10, was "yes to all, merge them one at a time".
- **One budget ledger,** opened with the approval: `"decide as per the expert team (vote-rule independence measurement, $110 cap, coordinator 2026-11-10)"`, cap $110.00.
- **The run folder** (registration, ledger, draws, driver and score logs) is kept in the session family's notes folder, outside the repository. The requests carry licensed transcript text.

**THE RESULT IN FIVE LINES.**
- **Not falsified, by the registered rule.** X² 11.58 on 15 df (five pages with 0 < p̂ < 1, three df each), p 0.7106, VIF 0.77. The design's own decision rule: "Otherwise the design stands as written" (record §7).
- **Neither STOP fired:**
  - 1 dissent draw of 240, against the bar of more than 4;
  - the test had degrees of freedom: CNXC alone was unanimous.
- **The assumptions behind the binomial tables, checked:**
  - all 24 builds opened on an uncached draw (`first_draw_cache_read` 0 on every one);
  - each page's builds were 4,407 to 4,726 s apart, against the 300 s registered;
  - every draw was served by `claude-opus-4-8` and ended in `tool_use`.
- **Reported, decided on by nothing:**
  - the uncached first draws against the rest: exact stratified p 0.597;
  - the runs test within builds: z −0.11, p 0.911;
  - no option's proposal differed between two builds of one page, in 0 of 36 pairs under each of A, B and C(i).
- **Spend:** $96.7004 of $110 (240 calls); the design estimated $97.4.

## 1. What was registered, before any draw

- **The scorer** was written, reviewed and frozen before the draw:
  - the file `vinci/evals/independence.py`, sha256 `f38c983dd517d2bbbf41cc0c39a34abb5da81ebd2236e03d62c60cadcfc98338`, at commit `ccd63500`, with `python -m vinci.evals score-run`;
  - the registration's note carries the sha256, and the file scored the run unchanged.
- **The review that froze it:** `/code-review high --fix` found 7 issues before the freeze.
  - **3 fixed:** the scorer had not read draws as `synthesize` does. It now decodes escapes, treats a truncated draw as dissent, and treats a draw missing a structural field as dissent.
  - **3 decided before any draw:** the runs test's definition, the first-draw test reading the recorded cache state, and a run with no degree of freedom stopping as NOT TESTABLE.
  - **1 left:** a key helper shared with `verdict.py`, a decision-line file.
- **The registration** `f98809884b8cdd1da33058b384ef1962a812b59c9dff0d0a9db0593ebcb4a5bb` (`register-run`, $0):
  - the frozen panel v2's six pages (freeze `bcda7ce3`);
  - code `ccd63500`, with main's eight transforms in order: `asof_cut`, `relabel_drawdown_shape`, `trailing_only_note`, `survival_read`, `peer_gap_question`, `print_row_guide`, `gap_types`, `current_buybacks`;
  - 10 draws a build, 4 builds a page, at least 300 s between a page's builds;
  - inputs read from the primary checkout's `data/manual/ciq`, read only.
- **The six request pins equal #935's registered CAND requests, byte for byte:** BURL `47bbd4210ebc`, CNXC `eeadb7c6a74f`, LLY `9bb586e54132`, MCK `21800fb99664`, ROST `33261190dc69`, SMPL `4f3c3ca0d0f1`. So this run drew the requests #935 drew for #930, as main now builds them (`asof_cut` is the identity on the panel).
- **The note,** inside the sha, states:
  - the one falsifier and the two STOPs;
  - that nothing else decides;
  - that the run cannot move k, N, α, C(i)'s continuation set or C(ii)'s keep bar;
  - that it is never read for which page proposes.

## 2. The run

- **How it was drawn:** 24 builds, round-robin by page, each through `run --registration --build --paid`, from 2026-11-10 22:45:54 to 2026-11-11 04:53:27 (+05:30).
- **Every build:**
  - drew 10 of 10 usable draws;
  - started 4,407 to 4,726 s after its page's previous build ended (the first round had none);
  - opened with 0 cache-read tokens.
- **Cost:**
  - first draws: 24, mean $1.354;
  - cached draws: 216, mean $0.297;
  - 91.3 s mean a call.

## 3. The score, by the registered rule

| page | pooled modal lean | its count, builds 1–4 (of 10) | p̂ | X² (3 df) |
|---|---|---|--:|--:|
| BURL | mixed | 6, 5, 7, 8 | 0.650 | 2.20 |
| CNXC | mixed | 10, 10, 10, 10 | 1.000 | — (no df) |
| LLY | strongly-bullish | 10, 9, 10, 10 | 0.975 | 3.08 |
| MCK | strongly-bullish | 6, 6, 4, 5 | 0.525 | 1.10 |
| ROST | mixed | 8, 8, 4, 7 | 0.675 | 4.90 |
| SMPL | mixed | 5, 5, 5, 6 | 0.525 | 0.30 |
| **pooled** | | | | **11.58 on 15 df, p 0.711** |

- **VIF 0.77:** the per-build counts spread slightly LESS than a binomial would. At 15 df that is within noise; the test is one-sided against overdispersion, and it does not fire.
- **The per-build tallies,** each of 10:
  - **BURL:** bullish 4 / mixed 6; bullish 4 / mixed 5 / dissent 1; bullish 3 / mixed 7; bullish 2 / mixed 8.
  - **CNXC:** mixed 10 in all four.
  - **LLY:** bullish 10; bullish 9 / mixed 1; bullish 10; bullish 10.
  - **MCK:** bullish 6 / mixed 4; bullish 6 / mixed 4; bullish 4 / mixed 6; bullish 5 / mixed 5.
  - **ROST:** mixed 8 / bullish 2; mixed 8 / bullish 2; bullish 6 / mixed 4; mixed 7 / bullish 3.
  - **SMPL:** bearish 5 / mixed 5 in builds 1–3; mixed 6 / bearish 4 in build 4.
- **The one dissent draw:** BURL build 2, draw 1, lean `mixed-to-bullish`, which is not one of the three. Production proposes nothing on an unrecognized lean (`verdict.derive_proposal`), and R3 counts it as dissent.

## 4. Reported, decided on by nothing

- **First draws:**
  - all 24 builds opened uncached;
  - 16 of their 24 first draws carry the page's pooled modal lean;
  - the exact test, stratified by page, gives p 0.597.
- **Runs within builds,** pooled over the builds holding both symbols: z −0.11, two-sided p 0.911. No clumping or alternation inside a build.
- **Each option on each build** (C(iii)'s states in brackets):
  - **A** (R1 on each build's first five):
    - LLY proposes BUY in all four builds;
    - BURL is borderline in three and none in one; MCK borderline in three and none in one; SMPL borderline in one;
    - CNXC and ROST are none.
  - **B** (R1 at ten): LLY BUY in all four; MCK borderline in two; ROST borderline in one; the rest none.
  - **C(i):** LLY BUY in all four; MCK borderline in two; the rest none. It drew 6.46 draws a build on average.
  - **No option's proposal differed between two builds of one page:** 0 of 36 pairs under each of A, B and C(i).
    - This panel's pages sit far from every rule's threshold: LLY near 1, the rest near or under one half, or mixed.
    - So it cannot show the flip rates §4 of the design tabulates for names near a threshold, and was never meant to (§7: "six pages cannot measure a flip-rate difference").

## 5. Found beside it, exploratory: LLY's lean rate after #930

- **The comparison:**

  | LLY request | runs | bullish draws |
  |---|---|---|
  | `6515cd17c893`, before #930 | #931's CAND, #935's BASE | 7 of 10 |
  | `9bb586e54132`, after #930 | #935's CAND, this run | 44 of 45 (5 of 5, and 39 of 40) |

  - Fisher's exact test, two-sided: p 0.016 (this run alone against the 10: p 0.022).
  - The two requests differ only in fix 3b's spans (`docs/records/2026-11-09-fix3b-measured-on-the-panel.md` §1).
- **Why it is not a conclusion:**
  - LLY was singled out because its count moved, after the data were seen;
  - the earlier draws were made on 2026-11-09 (#931 from 15:01, #935 from 18:39, +05:30), these on 2026-11-10 to 11, under the same model id;
  - it was not registered.
- **What it bears on.** #935 §4 explained LLY's move to BUY as "within one page's noise", and noted that "it cannot be excluded either", because fix 3b removes a caution-worded clause from LLY's survival line ("FCF sign UNKNOWN — runway not assessable").
  - These 40 draws make the noise reading less likely.
  - #930 was merged on its merits as a data fix, whatever verdict it produces (the operator's ruling).
  - Whether a removed caution clause moves a lean is a question for a registered test, not for this record.
- **It feeds nothing in the vote rule.** The rule was fixed before the draw; this run is never read for which page proposes.

## 6. What follows

- **The design stands as written** (record §7), so step 4, the implementing PR, may follow:
  - R1;
  - R3 (failed, unparsed or unrecognized draws as dissent);
  - the single spelling key;
  - R4 (the split sealed in the ledger);
  - R5;
  - C(iii) (the borderline outcome);
  - C(iv) (the ten-draw confirmation at `log-verdict`).
- **It is a decision-path change:** the edit hook asks the operator, and it shows a real run before merge. It STOPS for the operator's merge.

**BOUNDARY.**
- **Draws:** 240.
  - Six pages, four builds, ten draws.
  - `claude-opus-4-8` on every call, every call ending in `tool_use`.
  - Drawn 2026-11-10 22:45 → 2026-11-11 04:53 (+05:30).
- **Hashes:**
  - `draws.jsonl` sha256 `975fc1090efb7b241be2ee9a43f7b93f405e7d8c736fea060b795837812a4e1e`;
  - the ledger `c8969b16cb3863c11fee70011c6e51931054898455d5268c0f5c7a95324d20dd`;
  - the registration `f98809884b8cdd1da33058b384ef1962a812b59c9dff0d0a9db0593ebcb4a5bb` (its file's sha256 equals its sha).
- **The scorer:** `vinci/evals/independence.py` at `ccd63500` (sha256 `f38c983d…`). A lean is read as `synthesize` reads it, and a draw with no recognized lean is dissent.
- **The dispersion test:** per page, the pooled modal lean over its 40 draws, ties to first appearance. Pages with p̂ of 0 or 1 carry no degree of freedom. χ² by the regularized upper gamma.
- **The first-draw test:** the 24 builds whose first draw read 0 cache tokens, against the page's other draws; hypergeometric, convolved over pages, two-sided.
- **The runs test:** Wald–Wolfowitz within each build, on modal or not, pooled into one z.
- **§5's counts:** the committed-lean labels of LLY's draws in #931's and #935's records, five per arm, and this run's 40. The request identity was checked by `replay.capture_at` (`docs/records/2026-11-10-the-proposal-vote-rule-design.md` §2) and by this run's pin. Fisher's exact test is two-sided.
- **Spend:** production's `cost_usd`, summed from the ledger: $96.7004.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$96.7004 of the $110 approval;** $13.30 unspent.
- **Accepted, with its falsifier: independence held on six pages, two of them near p̂ 0.5.**
  - **Where the power is:** MCK and SMPL hold most of it. LLY and CNXC sit at or near a boundary, where a count cannot overdisperse.
  - **What it cannot catch:** a weak correlation. The design's simulated power at ρ 0.05 was 37%.
  - **Falsifier:** a later registered run on pages near p̂ 0.5 reads X² over the 5% point.
- **Not shown by this run:** the flip rates near a threshold. No page here sits there (§4).
- **Deferred from Codex's round 2 on #978, both in the FROZEN scorer, so both wait for its next
  version.** The scorer is the file whose sha256 the drawn registration carries, and editing it
  after the run would make the committed scorer differ from the one that scored. Neither case
  occurs in this run.
  - **An unknown first-draw cache state** (`first_draw_cache_read` None, when the first API
    attempt fails) is read as "not uncached" and leaves the exact test silently. It should be
    reported as UNKNOWN. Here all 24 builds recorded 0.
  - **A runs test with no variance** (every build unanimous) prints z 0, p 1, a fabricated null.
    It should be reported as UNKNOWN or suppressed. Here the pooled statistic had variance: z
    −0.11.
