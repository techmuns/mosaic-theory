---
id:
status: shipped
date: 2026-10-12
prs: [703]
supersedes:
superseded-by:
---

# Theme intelligence — undecodable PDF glyph text quarantined before anything reads it; a re-read is a new version, never a confirmation

**WHAT.** The targeted PDF cost correction on PR #703 (Fix 1 only — no Batch API, no model
change, prompt caching still OFF):

- **Quarantine** (`parse.py`, `documents.py`; reader `ti-parse-6`). A PDF font with no character
  map yields `(cid:N)` codes. Each LINE and table CELL is tested before anything reads the
  text: ≥ 3 codes covering ≥ 50% of its non-space characters, or a line ≥ 50% set in a font
  whose characters on that page are ≥ 50% codes (its scrambled near-letters go with it). Such
  text is left out; readable lines on the same page and a sentence that merely mentions a CID
  are kept. Per page the document record keeps lines, cells, characters and a sha256 of what
  was left out; the document is PARTIAL with "page N: undecodable font glyphs … NOT read — the
  page needs visual / OCR review"; the weekly report lists it as VISUAL / OCR REVIEW, never as a
  missing document, under "requiring a metadata, licence or visual check" (the paid run's own
  report showed it under "a metadata or licence check" — relabelled, pinned). No OCR. Generic —
  nothing names Citi, Gridlock or a page.
- **Downstream** (`completeness.py`): digits inside a `(cid:N)` code are never figures, and codes
  never count as argument words — so quarantine runs before figure counting, the completeness
  review, every prompt and the cost estimate. A side effect, measured: the body-size estimate
  had been skewed by the codes (9.0pt, 308,659 characters, vs 10.0pt), which merged three
  section bylines into headings; corrected, 7 readable blocks split differently (pages 7, 8, 9,
  26, 38), page references unchanged.
- **Re-read** (`ingest.py`, `--reread`): the same file again stays a DUPLICATE, and says when
  today's reader reads it differently; `--reread` analyses it as a NEW VERSION of the SAME
  article — document id, arrival time, file name and standing kept, a history line added;
  article id, title, date and first-seen kept; the earlier version, its verification ledger and
  thesis versions untouched. Unchanged text → DUPLICATE ("unchanged"), nothing sent.
- **No duplicate confirmations on a re-read** (`verify.same_sentence_reread`, `engine.py`,
  `cards.py`; engine `ti-engine-3`) — FOUND by this pass's copied-registry test on the real PDF,
  not anticipated: two extraction answers label one sentence's metric / period in different
  words, so the fingerprint differed and 18 key-evidence rows on five cards listed the same
  sentence and figure twice, the second classed "new". Now a sentence and figure read again
  from another version of the same article is REPEATED, and the card keeps one row. The same
  rule covers a preview's full text (UPGRADED).

**WHY.** The operator asked on 2026-10-11 how to cut the $46.67 Gridlock cost without losing
quality. Measured then: about 242,000 of Gridlock's 293,161 article tokens, resent in each of 22
completeness parts, were glyph codes from seven disclosure pages — the cost driver, not the
model or the format (converting the PDF to Markdown first would carry the same codes).

**HOW VERIFIED.**

*1. The defect, from the page images* (rendered locally, not committed — licensed): pages 54–60
are Appendix A-1 — analyst certification, the ratings distribution (as of 01 Apr 2026: Buy 61% /
Hold 32% / Sell 8%; Catalyst Watch 37 / 47 / 16; investment-banking-client shares), rating
definitions, the research-analyst affiliation table (23 analysts by Citi entity — all 23 names
also appear in the readable text, the entity mapping only there), general legal disclosures,
country distribution and data-provider notices, copyright. None of it is theme evidence.

*2. $0 demo on the three real Citi PDFs* (`1-demo-before-after-zero-cost.txt`): Gridlock tokens
**293,161 → 44,476 (−85%)**, ledger figures 851 → 403 (446 of the 851 were read from codes),
argument paragraphs 292 → 287, estimate 20 → 14 parts; quarantined 7 pages, 392 lines, 308,181
characters, 0 cells; title, date (2026-06-28 from the document text), author and file sha
unchanged; PARTIAL. LatAm and ETF: text, ledger and estimate byte-identical. Pages 1–53 of
Gridlock: text identical once blocks are joined (`8-compare-page-identity.txt`).

*3. ONE paid acceptance run* (registry `glyph-paid`, fresh; operator approved a one-time $32
document limit after two $0 holds at $30 and $31 — the estimate was $31.40):

| | the $46.67 run (hybrid-a) | cleaned (glyph-paid) |
|---|---|---|
| total | 51 calls, 8,117,094 in, 243,527 out, **$46.67** | 41 calls, 1,344,624 in, 199,137 out, **$11.70** |
| completeness | 22 calls, 7,130,969 / 151,527, $39.44 | 13 calls, 880,681 / 118,748, $7.37 |
| extraction | 2 calls, 607,565 / 40,886, $4.06 | 2 calls, 109,525 / 41,485, $1.58 |
| review | 27 calls, 378,560 / 51,114, $3.17 | 26 calls, 354,418 / 38,904, $2.74 |

*4. Evidence quality vs the baseline* (`4`–`8-compare-*.txt`; base = `final-a`, the $46.67 run's
own answers on the current rules):
- **Theses** 16 {WATCH 5, SKIP 11} → 14 {WATCH 6, SKIP 8}; RESEARCH NOW 0 → 0. 14 of the 16
  have a counterpart (4 same id, 8 by shared verified quotes, 2 by the same key shape).
  **Three SKIP → WATCH** (midstream capex, skilled labour, nuclear): each base card carried a
  long-dated window (SKIP-3 "longer-term only"); each new card carries no dated window at all,
  so SKIP-3 cannot fire and it falls to WATCH — not new near-term evidence. **Fuel cells**
  (WATCH) folded into the gas-generation thesis (WATCH: Bloom, Ceres, Weichai, Delta and six
  fuel-cell rows). **Low-cost US natural gas (WATCH; WMB, KMI) is absent from the cards**: 3 of
  its 4 evidence sentences are verified claims in the new run, on no thesis — model
  variability in hypothesis grouping (page 37 reads identically in both versions), and no
  ledger flags it (the ledger tracks figures and paragraphs, not hypotheses).
- **Numbers**: 255 base figure claims; 209 quoted verbatim in the new run; of the 46 others,
  21 captured under another quote, 9 judged immaterial with a stated reason (mostly "duplicate
  of a captured figure"), **15 OPEN in the ledger** (pages 14–19), **1 silently absent**: "the
  new capacity to be added gradually over four years from 2025 to 2028" (page 22 — a
  word-number, outside the ledger's digit-based count; its paragraph's other figures captured).
- **Why 15 are open: one malformed model answer.** Completeness part 4 of 13 returned
  `added_hypotheses` as a 4,420-character string that is not valid JSON; the whole part was
  dropped, as designed (`MALFORMED_ITEM_DROPPED`), its 50 gaps left open — 14 claims (data-centre
  capacity, cancellations, load swings, FERC's 90-day plan, EU grid costs, interconnection
  queues, transformer lead times 24–48 months / 3–4 years), 4 mentions, 1 risk and 50 reviews
  lost. Open items 6 + 4 → **27 + 27** (48 "no account", 25 of the 27 paragraphs from that
  part). Visible, not silent; not caused by the quarantine (pages 13–19 identical block for
  block). The base's 22 parts had no such drop.
- **Companies** 35 → 30; 29 identical (name, ticker, status). Not named in the new run: Renault,
  Volvo (EV-demand examples), Carwow, OLX (private), CBRE (data source) — their sentences are
  captured; Start Campus PRIVATE → UNRESOLVED.
- **Section 7**: genuine alternative explanations 13 → 11 (the 164 → 66 headline is registry
  cross-links, 151 → 55, from fewer overlapping theses); counter-evidence 0 → 4; disconfirming
  observables 34 → 36; unknowns 38 → 38; market risks 27 → 36 sentences, 9 → 10 distinct. Base
  risks not on the new cards as risks: on-site gas equipment overbuild, the skilled-labour
  shortage (its thesis is there, WATCH), European "bragawatts", raw-material inflation on storage
  returns.
- **Page references**: every new claim on pages 3–53; none on 54–60.

*5. Identity, on copies of `final-a`* (`9-reread-identity-copied-registry.txt`, $0): DUPLICATE
with the `--reread` hint; `--reread --cache-only` REFUSED (the prompt differs — registry
candidates and the article's 8 authors — so no cached answer was reused against changed text);
then a labelled $0 harness (alignment hints and text-found authors suppressed so the paid run's
prompts recur, proven first in a fresh registry) ran the production path: one article, one
document (standing, arrival, filename kept, history +1), two versions, v1's ledger untouched,
the 16 theses kept (5 gain a version 2, 11 untouched), **18 duplicated rows → 0 after the fix**,
0 independent confirmations, $0. Article authors 8 → 12 (four section bylines the corrected
split exposes, each with its block quote).

*Tests*: `tests/test_theme_intelligence_glyph_quarantine.py` — 31: a byte-written synthetic PDF
(clean / mixed / unreadable pages, a CID mention, an undecodable cell); the safeguard off
reproduces the defect; clean PDFs read exactly as before; re-read identity; **an end-to-end
re-read whose second answer relabels the same sentence (REPEATED, one row) and takes the
sentence's other figure (NEW)**; unit pins on the real `Claim` type (positive: relabelled,
shorter quote, typography; negative: same version, another article, another figure, a
fragment, another sentence). **26 mutants, all killed** (17 quarantine / re-read, 9 same-
sentence rule; 3 + 1 survived first and were pinned). Full offline suite on the final tree: exit 0,
4,864 passed, 511 skipped, 0 failed; ruff and `mypy --strict vinci` clean.

**BOUNDARY.** Article `A-82a8a9210bae` (Citi, "Overcoming Gridlock 2.0", 60 pages, file sha256
`c6f361d4…`), as of 2026-10-11. Base: registry `final-a`, run `R-20261011T141624Z-ingest`
(answers of `R-20261011T100624Z-ingest`, code of 2026-10-11). New: registry `glyph-paid`, run
`R-20261012T050655Z-ingest`, code `ec780bc2`, 2026-10-12 05:06–05:36 UTC. Tokens: provider usage
of calls not served from the cache. Figure claims: span-verified claims with a stated value.
Cost of this pass: **$11.7015 measured** (the one paid run; the two holds, the demo, the
comparisons and the identity runs made no model call).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- *Not paired with a control draw.* Attribution of the thesis differences to model variability
  rests on elimination (pages 1–53 read identically), not on a measured noise floor. A second
  cleaned draw (~$12) would measure it — not run without approval.
- *One malformed part drops 50 reviews.* Pre-existing, not glyph-related; listed and offered as
  a separate task (salvage the valid fields of a part answer).
- *A WATCH thesis can vanish between draws* (low-cost US gas) with nothing flagging it; the
  ledger does not track hypotheses.
- *A word-number qualification can be lost silently* (the ledger counts digits).
- *A re-read may add sibling theses* when the new answer keys a story differently; measured only
  with alignment hints OFF (8 such theses); unmeasured in production.
- *SKIP-3 vs no window*: a thesis with only long-dated evidence is SKIP, one with no dated
  evidence WATCH — reported, not changed (prioritisation not reopened).
- *Quarantined pages are not read.* Falsifier: a document whose undecodable pages carry theme
  evidence — the VISUAL / OCR REVIEW line is the control.

## Amendments

- **2026-10-12 — a claim above is WRONG.** "1 silently absent: … over four years from 2025 to 2028
  (page 22 — a word-number, outside the ledger's digit-based count)" — the ledger DOES read counted
  periods written in words (`completeness._WORD_FIG`); "four years" was in the cleaned run's ledger
  and judged IMMATERIAL by pass 1b with a stated reason ("capacity addition timing assumption,
  modeling context"). A recorded materiality judgment that differed from the baseline's, not a
  silent loss. Found while acting on the review that followed;
  `docs/records/2026-10-12-theme-intelligence-analytical-safeguards.md` and
  `docs/theme_intelligence/analytical-safeguards-2026-10-12/9-risks-companies-numbers-investigated.txt`.
  The same follow-up fixed the part-salvage, mechanism-coverage, SKIP-3 timing, sibling, preflight
  and unread-page limitations listed above.
