---
id: 2026-11-04-890-cross-review-rank-and-duration-narrowed
status: shipped
date: 2026-11-04
prs: [899]
supersedes:
superseded-by:
---

# #890's two trace rules are narrowed to what they meant: a percentile's rank traces only for a figure written as a rank, and only a whole-number duration is a label — the cross-review's figures the cited fact does not support are flagged again

**WHAT.** #890 (merged a439eabe) let the per-fact trace accept two kinds of figure the cited fact
did not state. The cross-review posted on #890 after it merged found both, and this follow-up fixes
exactly what it asked:

1. **The rank, only when written as one.** #890 admitted a percentile's whole-number rank for any
   figure of that value, so "2.0x", "2 turns" and "fell 2%" cited to SMPL's 0.0183 P/E percentile
   all traced, and so did AMZN's "compressed to 3.0x" and TJX's "de-rated to 6.0x".
   - Now the rank traces only for a figure, ordinal or not ("3rd", "3"), followed by
     "percentile" / "pctile" / "%ile" (`synthesis._RANK_AFTER`, read through
     `_claim_figure_ends`). An ordinal alone ("the 2nd straight quarter", "its 2nd-largest
     customer") and a percentile-point move ("rose 2 percentile points") are figures: both traced
     on this branch's first cut and were caught in its own `/code-review` round.
2. **Durations, only whole numbers.** #890 skipped every hyphenated or "y" duration, decimals
   included. NCNO's "its own 2.3y range" is its band's span (`own_history.value[0].window_span_years`),
   a fact the point must cite, and #890 let a "7.3y" or "7.3-year" rewrite of it pass, as well as a
   "7.4-year payback".
   - Now only a whole number before `-<unit>` or "y" is a label ("5-year", "52-week", "~9y"). A
     decimal one is a figure.
3. **The 0..1 guard is pinned.** Before, dropping `0 <= o <= 1` in `_stated_numbers` failed no
   test. Through the trace the guard cannot be seen: a percentile field above 1 already traces its
   ×100 value, and a negative rank is never a figure's magnitude. So it is pinned on the numbers the
   fact states.
4. **The two nits.** The two mypy errors at the test's line 266 are annotated. The corpus invariant
   now validates each page as itself (it had hard-coded `ticker="SMPL"`).

Extraction `2026-11-04.rank-written-as-rank` (+ web twin), re-pinned.

**WHY.** The trace is a guard. A rule that admits a figure because some other number equals it is
the coincidence G-D6 exists to refuse. The reviewer showed the rule admitting fabrications, and
they are flagged again.

**HOW VERIFIED.**
- **Every reviewer case, reproduced before the fix** through the real `_validate` against the
  committed pages and the frozen SMPL page.
  - On a439eabe each traced: "2.0x", "2 turns", "fell 2%"; AMZN "3.0x", "3 straight periods", the
    "3" of "3-4%"; TJX "6.0x"; "a 7.4-year payback"; NCNO "7.3y" / "7.3-year"; MVST "~4.1y".
  - On cfedcb39 (before #890) every one was flagged.
  - On this branch every one is flagged again.
- **New pins.** 18 new test cases in `tests/test_untraceable_rank_and_duration.py`: 12 negatives
  (4 of them added in the review round), 5 positives and the guard pin. The "2.3y" positive also
  moves to the negatives ("~9y" replaces it), and the corpus invariant changes twice. The 8
  first-cut negatives fail on a439eabe, run in a scratch copy of it. The 4 review-round negatives
  (an ordinal alone, a percentile-point move) traced on the first cut too.
  - The guard pin passes on a439eabe, where the guard exists. With the guard deleted from this
    branch it fails (mutation run).
  - "2nd percentile", "2 percentile", "2 pctile", "2%ile", "5-year", "52-week", "~2y", "~9y" and
    "180-day" still trace or skip.
- **The corpus**, `_validate` over the 27 committed pages at a439eabe:
  - UNTRACEABLE: cfedcb39's code 338 → a439eabe's 326 → this branch's **328**.
  - Against cfedcb39 there are exactly **10 flips** and every other flag is identical: the five
    ranks (AMZN, IT, NFLX, NKE "3rd"; TJX "6th") and five whole-number durations (EPAM "~9y"; LLY
    "5-year" and "~2y"; NFLX and WLK "52-week").
  - Against a439eabe, NCNO "2.3y" and MVST "~1.7y" are flagged again. UBER's "~1.8y", a QA-only
    TRANSCRIPT-FIGURE note, also returns.
  - #890's own figures move accordingly: on its 30 page versions 373 → 363 (318 → 311 on the
    9e996d7f pages, 55 → 52 on #886's three, unchanged).
- **The holes, as mutations on the same 27 pages:**

  | mutation | cfedcb39 | a439eabe | this branch |
  |---|--:|--:|--:|
  | each page's own percentile rank written as "N.0x", "N turns" or "fell N%" (114) | 42 caught | 0 | 42 |
  | a made-up decimal duration, "a X.Xy span" or "a X.X-year payback", cited to every committed point (564) | 486 caught | 0 | 486 |

- **Made-up-figure mutations, unchanged set for set against a439eabe:**
  - G-D6 shape: 1,236 of 1,408 caught.
  - Small whole numbers: 1,129 of 1,408.
  - Ordinal ranks 0–100 on each percentile fact: 3,653 of 3,838.
  - Whole-number "N-year" durations followed by a made-up figure: 1,240 of 1,408.
  - The frozen SMPL draw: 195 of 199.

**BOUNDARY.**
- Corpus: the 27 `data/dossiers/*/dossier.json` at a439eabe; #890's populations re-measured on its
  own pages (9e996d7f's 27 and #886's 3 at 2746d0ef). Measured 2026-11-04. Unit: an UNTRACEABLE
  figure.
- Mutations: one-point syntheses through the real `_validate`, seeded. "Structured point" means a
  committed point whose ref is in the layer and is not a transcript. The 114 are 3 phrasings × 38
  percentile facts with a ref and a 0..1 value.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Not fixed here, recorded as STATE §5.0 row 45 (hold scope):**
  - The spaced form "7.3 years" passes on a439eabe and on cfedcb39 alike. `_CAL_AFTER` has always
    skipped "<n> years/days/…", decimals included.
  - A whole-number duration that is really a quantity ("an 83-day DSO") is still skipped. The
    reviewer's requested rule keeps every whole number.
  - Both want a rule that reads a duration's number as a figure where a fact could state it, and
    the corpus should be measured first.
- A rank written in a form outside the four ("2-pctile", "rank 2") is a figure, and stays flagged
  unless the cited fact states it. Falsifier: a committed point writing its percentile that way.
- No committed page moves in this PR. Each page's caveats change at its next assembly.
