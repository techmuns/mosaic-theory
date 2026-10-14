---
id: 2026-10-12-theme-intelligence-pilot-corrections
status: open
date: 2026-10-12
prs: [703]
supersedes:
superseded-by:
---

# Theme intelligence — the pilot's three material defects corrected at $0: a salvaged first answer, a stricter RESEARCH NOW, review warnings on the line; a stored preview corrected

**WHAT.** The operator approved a narrow correction of three material defects the supervised
pilot showed (`docs/records/2026-10-12-theme-intelligence-supervised-pilot.md`), plus one metadata
correction. Nothing was paid: every demonstration used the pilot's saved paid answers, its HTTP
cache or offline fixtures.

1. **A malformed first answer is SALVAGED, never asked again** (`extract.read_answer`, `_ask`).
   - A top-level failure is recovered field by field (the completeness path's `salvage_fields`, now
     with `repair=True` for pass 1).
   - A list written as broken JSON text is mended by DELETION ONLY (`repair_list_text`): an
     unkeyed value inside an object, or a stray `}` that closes an item before its remaining
     properties. A repair stands only when the whole text then decodes with no property given
     twice; the items are then validated and verified like any other.
   - A hypothesis still unreadable is a DROPPED proposition with its name: a mechanism-coverage
     alert, so the run reads INCOMPLETE — REVIEW REQUIRED. Every salvage step is an
     `ANSWER_SALVAGED` warning; the paid answer stays on disk exactly as returned.
   - The identical re-ask is gone (it reproduced the identical slip in 4 of 4 answers). Answers
     an earlier run paid for and set aside (`<key>.invalid-N.json`) are salvaged, newest first,
     instead of paying again. Only an answer that is not an object of the schema at all still
     fails loud, with its one call costed.
2. **RESEARCH NOW eligibility.**
   - **A bare page label is no exposure** (`verify.bare_label`, `SECTOR_LABEL_ONLY`): a paragraph,
     list item or tag line that says nothing but the sector's name. Headings, chart titles and
     standfirsts are untouched, because report sections are named that way.
   - **Near-term means the next four quarters** (`NEAR_TERM_END_DAYS` 549 → 366).
   - **A straddling window** is new: one that runs past the horizon with most of it inside
     (`timewindow.straddles`). It is never near-term evidence and never longer-term only, so it
     gives WATCH, not SKIP-3. Without it, the corrected window would have sent the pilot's RN to
     SKIP-3 ("longer-term only") for a year beginning eleven weeks later.
   - `ENGINE_VERSION` ti-engine-5.
   - **Re-grade** (`Engine.reassess`, CLI `reassess`): stored evidence only, no model client. A
     changed action or a refused exposure is a NEW version whose reviewed sentences are kept word
     for word; the card review's findings are carried to the new run.
3. **Review warnings on the line** (`cards.RenderContext.flagged`, `report.REVIEW_WARNINGS`).
   - Every line the card review questioned and left printed (REVIEW_PARTIAL /
     REVIEW_INFERENCE_UNSUPPORTED) shows `⚠ UNRESOLVED REVIEW — <why>` in markdown, HTML and
     print, and is never labelled a verified fact.
   - A conditional line (could / may / might / would / if; the month "May" excepted) is at most
     SOURCE OPINION when the card is composed (`cards.capped_conditionals`).
   - QA expects the same capped label.
4. **Metadata: a stored preview recorded FULL.**
   - When its page is read again and the current parser (`ti-parse-7`) reads it as PARTIAL, a
     `RETRIEVAL_CORRECTED` record is appended. That record is a verification issue: append-only,
     already synced, and no schema change.
   - Every store read overlays it: the version reads PARTIAL. The original row, the first-seen
     date and the spend are unchanged.
   - The theses the article fed are re-graded at once.

**WHY.** The approval named exactly these defects. The pass-1 shape — `hypotheses` written as
text — is a recurring model slip (2026-10-10; 4 of 4 J.P. Morgan answers), and the identical
re-ask had been shown not to help, so the paid answers had to be used instead. The RN rule
change is face validity, not outcome-tuning: a category tag says nothing about exposure, and a
calendar year three quarters inside the horizon is neither a 2-4-quarter window nor
long-dated-only.

**HOW VERIFIED.**

The J.P. Morgan answers ($0):
- **All four saved malformed answers**, read by the new reader: each recovers its one hypothesis,
  the article's thesis (earnings broadening beyond the mega-caps). Three by deleting an extra
  unkeyed bottom-line object (245–305 characters), one by deleting one stray `}`. All 25–30
  claims, 11–12 mentions and 2–3 risks are kept, and none is lost.
- **End to end, `--cache-only`, on copies** (the article was kept OUT of the real pilot registry,
  so a paid acceptance test can still apply it there):
  - In a fresh registry, the answer set aside under the empty-context key was salvaged.
  - In a rehearsal copy, so was the answer under the populated-context key.
  - Both give one WATCH, `TH-FBDC863613`, with verification INCOMPLETE stated: the completeness
    pass has no saved answer (27–28 of 62 figures open).

The real pilot registry ($0, after a rehearsal on a copy):
- **Re-grade** (`R-20261012T114353Z-reassess`):
  - `TH-7C895A0A4E` RESEARCH NOW → WATCH (v2, DOWNGRADED). Its factors moved: F5 `yes` →
    `runs_past`; F6 1 sector → 0; F12 `qualifies` → `absent`; the Semiconductors tag refused.
  - `TH-1516B6186B` stays WATCH; its v2 drops the tag exposure.
  - `TH-2FFD9B58A8` is unchanged, so no version was written.
  - QA 20/20.
- **SemiAnalysis** (`R-20261012T114354Z-article`, `--cache-only`): `RETRIEVAL_CORRECTED` on
  `AV-2395b03fac4480e2`, parser ti-parse-6 → ti-parse-7. A re-render of its original run reads
  "0 full · 1 partial" and "read only in part", and lists the article as awaiting an authorised
  complete copy. It has no theses to re-grade.
- **Review warnings:** all 7 flagged lines show the warning after the re-grade (2 on
  `TH-1516B6186B`, 5 on `TH-2FFD9B58A8`). The two conditional risk lines print SOURCE OPINION.
- **Spend:** still $3.9494 of $18.

**Corpus checks before the label rule** ($0):
- 137 distinct sector exposures across 138 local registries: 21 sit in non-argument blocks, mostly
  section headings, a chart title and a standfirst.
- The bare-label test matches only TrendForce's category lines. A broad "argument blocks only"
  rule would have refused report section headings, including those of the Gridlock transformer
  thesis, and reopened thesis identity.

Tests and gate:
- **Tests:** `tests/test_theme_intelligence_pilot_corrections.py`, 25 new tests on the pilot's
  shapes with hypothetical text; the salvage tests in `test_theme_intelligence_long_articles.py`
  rewritten from the re-ask contract; one near-term pin flipped (`"2027"` as of 2026-10-10 is no
  longer near-term) and three added.
- **Mutants:** 31 of 31 killed, one per new guard.
- **Gate:** ruff, `mypy --strict vinci` (184 files), `pytest -m "not network"` (see the PR).

**BOUNDARY.**

| Count | Population and unit |
|---|---|
| "4 of 4" | the pilot registry's saved `.invalid-N.json` pass-1 answers for the J.P. Morgan article (two cache keys, two each) |
| "137 / 138 / 21" | distinct (version, block, quote, name) sector exposures in every local registry's stored extractions (pass 1 + completeness) under `data/theme_intelligence/`, 2026-10-12; blocks read from the stored versions (synced registries store no block text) |
| "7 lines" | the pilot registry's REVIEW_PARTIAL issues, all runs, as of 2026-10-12 |
| "$3.9494" | `runs.payload.spend` of the pilot registry, 10 runs, 19 paid calls |

All measured at `6ebe229e` plus this change.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0.
- A straddling window gives WATCH where the old 549-day test gave near-term. Theses whose RN
  rested on next year's full-year figure fall to WATCH on their next re-grade. That is the intent.
- A salvaged hypothesis loses only what was deleted (an extra unkeyed bottom line, named in the
  warning).
- **Open:** whether to pay ONE targeted J.P. Morgan acceptance test in the pilot registry.
  - Its pass 1 is salvaged from the saved answer at $0. Only the completeness pass and the card
    review would be paid.
  - Estimate $0.20–$0.60 actual (pilot analogues: completeness $0.09–$0.37 per part, review
    $0.05–$0.10 per call), under a $2.00 run limit.
  - Not needed to prove the fix; needed to finish the article's analysis.
