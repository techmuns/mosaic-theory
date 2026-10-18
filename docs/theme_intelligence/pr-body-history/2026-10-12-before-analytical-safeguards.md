## Summary

A new, isolated package **`vinci/theme_intelligence/`**: a research discovery and prioritisation tool. It reads research from **seven publisher channels** — five automatic, two manual-first — and from documents the operator supplies. It extracts source-anchored evidence, named companies and risks; keeps a persistent, versioned registry of theses; and writes a decision-first weekly dashboard of nine-section **Living Thesis Cards**.

**"RESEARCH NOW" means allocate analyst attention — never buy.** The package stays off the fund's decision path (unchanged by this update): no fund module imports it; it imports only `vinci.config`, the existing LLM client and the HTTP cache (AST-pinned); it has its own SQLite registry; it has no buy / sell / target / weight field; its priority rules read no prices, returns or outcomes.

**This update is the targeted PDF cost reduction** — next section. Earlier updates are condensed at the end; their full write-ups are in the records and in `docs/theme_intelligence/pr-body-history/`.

- **Code:** all inside `vinci/theme_intelligence/` — `parse.py`, `documents.py`, `completeness.py`, `ingest.py`, `__main__.py`, `report.py`, `schemas.py`, `config.py`, `verify.py`, `engine.py`, `cards.py`.
- **Changed outside the package:** `STATE.md` (§2 line, §5.0 row 32 item 8), `docs/engineering.md` (glossary), `docs/theme_intelligence.md` (guide), a new record, tests, one labelled synthetic PDF fixture, worked output; `origin/main` (#707) merged in.
- **Untouched:** fund screen / ranker / dossier / verdict / scoring / valuation / ledger / portfolio / trading / historical-alpha-audit code. No Batch API, no model change; **prompt caching stays OFF**; seven publishers unchanged.

Record: `docs/records/2026-10-12-theme-intelligence-pdf-glyph-quarantine.md` · Guide: `docs/theme_intelligence.md` (Manual documents) · Worked output: `docs/theme_intelligence/pdf-glyph-quarantine-2026-10-12/`

**Not merged. The production weekly schedule is not enabled. The production state branch was not created.**

---

## Targeted PDF cost reduction (this update)

**The defect, confirmed from the page images.** Citi's 60-page Gridlock report sets pages 54–60 (Appendix A-1, the disclosures) in a font with no character map. The text layer reads them as `(cid:N)` codes: 308,181 characters, about 85% of the tokens sent in every model call, and 446 false "figures" in the completeness review. The page images show the analyst certification, Citi's ratings distribution, the analyst-affiliation table, legal and country notices, and the copyright notice — no theme evidence. The images are not committed (licensed).

### What changed

- **Quarantine** (`parse.py`, `documents.py`; reader `ti-parse-6`). Each line and table cell is tested before anything reads the text. It is left out when it has ≥ 3 codes covering ≥ 50% of its non-space characters, or when it is mostly set in a font whose characters on that page are ≥ 50% codes.
  - Kept: a readable line on the same page, and a sentence that only mentions a CID.
  - Recorded per page on the document record: lines, cells, characters, and a sha256 of what was left out.
  - The document is PARTIAL with "… NOT read — the page needs visual / OCR review". The weekly report lists it under **"requiring a metadata, licence or visual check"**, never as a missing document.
  - No OCR. Nothing names Citi, Gridlock or a page number.
- **Downstream** (`completeness.py`). Digits inside a code are never figures, and codes never count as argument words. So the quarantine applies before figure counting, the completeness review, every prompt and the cost estimate.
  - A side effect, measured: the codes had skewed the body-size estimate (9.0pt instead of 10.0pt), which merged three section bylines into headings. Corrected, 7 readable blocks split differently (pages 7, 8, 9, 26, 38). Page references are unchanged.
- **Re-read** (`ingest-file --reread`). The same file stays a DUPLICATE; the DUPLICATE note says when today's reader would read it differently.
  - `--reread` makes a **new version of the same article**. The document keeps its id, arrival time, file name and standing, plus a history line.
  - The article keeps its id, title, date and first-seen time. The earlier version, its verification ledger and its thesis versions are untouched.
  - Unchanged text → DUPLICATE ("unchanged"), and nothing is sent to the model.
- **No duplicate confirmations on a re-read** (`verify.same_sentence_reread`, `engine.py`, `cards.py`; engine `ti-engine-3`). The copied-registry test on the real PDF **found this defect**:
  - two extraction answers labelled one sentence's metric and period in different words, so the evidence fingerprint differed;
  - result: 18 key-evidence rows on five cards showed the same sentence and figure twice, and the second reading was classed "new".
  - Now the same sentence and figure from another version of the same article is REPEATED, and the card keeps one row.

### Measured — one paid acceptance run

Registry `glyph-paid`, fresh. You approved a one-time $32 document limit after two $0 holds at $30 and $31 (the estimate was $31.40).

| | the $46.67 run | cleaned |
|---|---|---|
| **total** | 51 calls · 8,117,094 in · 243,527 out · **$46.67** | 41 calls · 1,344,624 in · 199,137 out · **$11.70** |
| completeness | **22 calls** · 7,130,969 / 151,527 · $39.44 | **13 calls** · 880,681 / 118,748 · $7.37 |
| extraction | 2 · 607,565 / 40,886 · $4.06 | 2 · 109,525 / 41,485 · $1.58 |
| card review | 27 · 378,560 / 51,114 · $3.17 | 26 · 354,418 / 38,904 · $2.74 |

**$0 demo, the three real Citi PDFs, old reader → new:**

| report | article tokens | ledger figures | parts | estimate |
|---|---|---|---|---|
| Gridlock (60 pp) | 293,161 → **44,476** | 851 → 403 | 20 → 14 | $7–$38 → $6–$31 |
| LatAm (57 pp) | identical | 319 → 319 | 11 → 11 | identical |
| ETF (34 pp) | identical | 232 → 232 | 8 → 8 | identical |

Gridlock's title, date (2026-06-28, from page 1–2), PDF-metadata author and file sha256 are unchanged. Pages 1–53 read identically once blocks are joined.

### Evidence quality vs the baseline

Baseline: the $46.67 run's own answers on the current rules. Every item is listed in the worked output.

- **Theses: 16 → 14** (WATCH 5 → 6, SKIP 11 → 8, RESEARCH NOW 0 → 0). 14 of the 16 have a counterpart: 4 with the same id, 8 matched by shared verified quotes, 2 with the same key.
  - **Three SKIP → WATCH** (midstream capex, skilled labour, nuclear). Each base card cited a long-dated window, so rule SKIP-3 ("longer-term only") fired. Each new card cites no dated window, so SKIP-3 cannot fire and the thesis falls to WATCH. No new near-term evidence is behind these changes.
  - **Fuel cells** (WATCH) is folded into the gas-generation thesis (WATCH), which now lists Bloom, Ceres, Weichai and Delta and six fuel-cell rows.
  - **Low-cost US natural gas (WATCH; WMB, KMI) is missing from the cards.** 3 of its 4 evidence sentences are verified claims in the new run, but no thesis carries them. Page 37 reads identically in both versions, so this is model variability in how claims are grouped. Nothing flags it: the ledger tracks figures and paragraphs, not hypotheses.
- **Numbers.** Of 255 base figure claims, 209 are quoted verbatim in the new run. The other 46:
  - 21 captured under another quote;
  - 9 judged immaterial, with a stated reason;
  - **15 OPEN** in the ledger (pages 14–19);
  - **1 silently absent**: "added gradually over four years from 2025 to 2028" (page 22). It is a number written as words, which the digit-based ledger does not count.
- **Why 15 are open: one malformed model answer.** Completeness part 4 of 13 returned a field as a string that is not valid JSON. The whole part was dropped, as designed (`MALFORMED_ITEM_DROPPED`), and its 50 gaps stayed open.
  - Lost from that part: data-centre capacity, cancellations, load swings, FERC's 90-day plan, transformer lead times of 24–48 months, and 9 more claims.
  - Open items went from 6 + 4 to **27 + 27**. They are visible in the report. This is not caused by the quarantine: pages 13–19 are identical block for block.
- **Companies: 35 → 30**, of which 29 are identical (name, ticker, status).
  - Not named in the new run: Renault, Volvo, Carwow and OLX (examples of EV demand), and CBRE (a data source). Their sentences are captured.
  - Start Campus changed from PRIVATE to UNRESOLVED.
- **Section 7 (what could go wrong).** Genuine alternative explanations went from 13 to 11. The headline 164 → 66 is mostly registry cross-links (151 → 55), because fewer theses overlap. Other counts: counter-evidence 0 → 4; market risks 9 → 10 distinct.
  - Base risks no longer on the cards as risks: overbuild of on-site gas equipment, the skilled-labour shortage, European "bragawatts", and raw-material inflation.
- **Page references:** every new claim cites pages 3–53; none cites pages 54–60.

### Information not read (pages 54–60)

- the analyst certification;
- the ratings distribution as of 01 Apr 2026 (Buy 61% / Hold 32% / Sell 8%; Catalyst Watch 37 / 47 / 16; shares of investment-banking clients) and the rating definitions;
- the analyst-affiliation table — 23 analysts listed by Citi entity. All 23 names also appear in readable text; the entity mapping does not;
- general legal, country-distribution and data-provider notices, and the copyright notice.

None of it is evidence for the theme, and the report flags it for a visual check.

### Identity — `--reread` on the real PDF, copied registries, $0

Worked output: `9-reread-identity-copied-registry.txt`.

- **The same file again → DUPLICATE**, with the `--reread` hint.
- **`--reread --cache-only` → REFUSED.** The prompt differs from the paid run's: it lists the registry's theses and the article's 8 known authors. So no cached answer was reused against changed text. A real re-read pays again (~$12), which was not approved.
- **A labelled $0 harness** then reproduced the paid run's prompts so every answer came from the cache. It suppresses the registry alignment hints and the authors found in the text, and was proven first in a fresh registry. The production path ran downstream of it. Results:
  - one article and one document: standing, arrival time and file name kept; one history line added;
  - two versions; the first version's ledger untouched;
  - the 16 theses kept: 5 gain a version 2, 11 untouched;
  - **duplicated rows 18 → 0**; independent confirmations 0; $0 spent;
  - article authors 8 → 12: four section bylines the corrected split now exposes, each with its quote.
- **The same file once more → DUPLICATE ("unchanged").**

### Safe to enable by default?

**The quarantine itself: yes — it is on in this branch.**
- Clean PDFs read byte-identically: LatAm, ETF, and three synthetic fixtures (test).
- On Gridlock it removed only pages 54–60, which hold no theme evidence, and kept every page reference.
- The weaker evidence in the paid run does not trace to it. It traces to one malformed model answer (a pre-existing weakness, visible as open items) and to run-to-run model variability.

What to know before relying on single runs: see the limitations.

### Limitations

- **No control draw.** The thesis differences are put down to model variability by elimination (pages 1–53 read identically), not against a measured noise floor. A second cleaned draw (~$12) would measure it; it was not run without your approval.
- **One malformed field drops a whole completeness part** (50 reviews). This is pre-existing and not about glyphs. A separate task is offered: keep the valid fields and drop only the bad one.
- **A WATCH thesis can disappear between draws** (low-cost US gas), and nothing flags it.
- **A number written in words can be lost silently**, because the ledger counts digits only.
- **A re-read can add sibling theses** when the new answer keys a story differently. The harness measured 8 such theses with alignment hints off; the number in production is unmeasured.
- **SKIP-3 versus no window:** a thesis with only long-dated evidence is SKIP, while one with no dated evidence is WATCH. Reported, not changed — prioritisation was not reopened.
- **Quarantined pages are not read**, and there is no OCR. Falsifier: a document whose undecodable pages carry theme evidence. The visual-check line is the control.

### Screenshot

The paid run's real weekly report, re-rendered at $0 with the final code (other sections removed for the picture):

![visual check](https://github.com/techmuns/mosaic-theory/blob/claude/theme-intelligence/docs/theme_intelligence/pdf-glyph-quarantine-2026-10-12/screenshots/weekly-report-visual-ocr-review.png?raw=true)

### Tests, mutants, gate

- `tests/test_theme_intelligence_glyph_quarantine.py` (31) uses a byte-written synthetic PDF (`glyph_mixed_synthetic.pdf`) with a clean page, a **mixed** page (readable lines, a sentence mentioning `(cid:12)`, undecodable lines, an undecodable table cell) and an unreadable page. It covers:
  - the safeguard switched off reproduces the defect;
  - **clean PDFs read exactly as before**;
  - glyph codes never become figures, arguments or cost;
  - re-read identity and a re-read that keeps an UPGRADED document's standing;
  - **an end-to-end re-read whose second answer relabels the same sentence (REPEATED, one row) and takes its other figure (NEW)**;
  - unit pins on the real `Claim` type, positive and negative;
  - the report's visual-check label.
- **26 mutants, all killed** (17 quarantine / re-read; 9 same-sentence rule). 3 + 1 survived at first and were pinned.
- **Gate:** ruff (vinci, tests, frontend) clean; `mypy --strict vinci` clean, 183 files; `pytest -m "not network"`: at the merge commit `9984f6e9` (main #707 merged in): **4,876 passed, 511 skipped, 0 failed**.

**Cost of this pass: $11.7015 measured** — the one paid run. The two holds, the demo, the comparisons and the identity runs made no model call.

| brief item | disposition | note |
|---|---|---|
| 1 confirm the defect (page images; affected pages; material content) | SHIPPED | pages 54–60 = disclosure appendix; contents listed; no theme evidence |
| 2 generic safeguard (line / block / cell; mixed pages; CID mentions kept) | SHIPPED | text + font rules; synthetic mixed page; nothing hard-coded |
| 2 before figures, completeness, prompts, cost estimate | SHIPPED | demo: 293,161 → 44,476 tokens; 851 → 403 figures; estimate 20 → 14 parts |
| 2 structure, page refs, file identity preserved | SHIPPED | pages 1–53 identical once joined; 7 blocks re-split (bylines), page refs unchanged; file sha unchanged |
| 2 record what was excluded; PARTIAL; no false figures / arguments | SHIPPED | per page lines / cells / chars / sha256 |
| 2 no OCR; flag for visual / OCR review; no full-verification claim | SHIPPED | report line (screenshot) |
| 3 identity (same article, history, cleaned version auditable, no rewrite, no reused answers, no duplicate confirmations) | SHIPPED | `--reread`; duplicate defect found on the real PDF and fixed (18 → 0) |
| 3 test on a copied registry | SHIPPED | copies of `final-a`; production branch untouched |
| 4 $0 demo incl. a clean Citi PDF | SHIPPED | LatAm and ETF identical |
| 5 one controlled paid run, approved limit | SHIPPED | $11.70 (one run; $32 one-time limit approved) |
| 5 evidence comparison, nothing silently lost | PARTIAL | everything is listed. Silent losses: one WATCH thesis (model variability), one number in words. 15 figures open from one malformed answer (visible) |
| 6 targeted + mutation tests, ruff, mypy, offline suite | SHIPPED | 31 tests; 26 mutants killed |
| 6 GitHub CI | PENDING | read after push |
| caching OFF, seven publishers, fund code untouched, not merged, schedule off, no production state branch | SHIPPED | |

---

## Earlier updates (condensed; full text: `docs/theme_intelligence/pr-body-history/`)

- **State-pull ledger — the pilot condition** (`docs/records/2026-10-11-theme-intelligence-state-pull-ledger.md`). A `state pull` carries every run the branch lacks (run id, times, cost, paid-call rows), replays once from the cache, and checks the paid-call ledger. Real, on a temporary branch: a fresh restore holds 19 paid calls, $1.7882, identical call by call.
- **Seven-source corrections** (`docs/records/2026-10-11-theme-intelligence-seven-sources.md`):
  - Bank of America retired; Morgan Stanley / Goldman Sachs manual-first;
  - identity before ticker (Citi's "Delta" is UNRESOLVED);
  - a market regime only on market-structure evidence;
  - verification-check fixes;
  - spending limits checked before every paid call;
  - per-version dates;
  - state sync exercised on the real repository.
- **Hybrid research ingestion** (`docs/records/2026-10-11-theme-intelligence-hybrid-ingestion.md`):
  - claim-level contradiction;
  - supplied PDF / HTML / Markdown / text through the same pipeline, identified before any model call;
  - a $30 cost hold;
  - one registry, one weekly report.
- **Source health** (`docs/records/2026-10-11-theme-intelligence-source-health.md`). Every channel is checked cheaply and without the LLM, with history and alerts.
- **Review round 3** (`docs/records/2026-10-11-theme-intelligence-review-round-3.md`). A challenge needs the same claim; the segment is part of identity; research verification is shown apart from execution.
- **Review round 2** (`docs/records/2026-10-10-theme-intelligence-review-corrections.md`). J.P. Morgan's Software Shock yields exactly three WATCH theses.
- **The original build** (`docs/records/2026-10-10-theme-intelligence.md`): the package, its registry, the nine-section cards, and the weekly workflow (opt-in cron, state branch).

🤖 Generated with [Claude Code](https://claude.com/claude-code)

