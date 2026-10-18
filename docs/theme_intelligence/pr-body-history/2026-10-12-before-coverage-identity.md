## Summary

A new, isolated package **`vinci/theme_intelligence/`**: a research discovery and prioritisation tool. It reads research from **seven publisher channels** — five automatic, two manual-first — and from documents the operator supplies. It extracts source-anchored evidence, named companies and risks; keeps a persistent, versioned registry of theses; and writes a decision-first weekly dashboard of nine-section **Living Thesis Cards**.

**"RESEARCH NOW" means allocate analyst attention — never buy.** The package stays off the fund's decision path (unchanged by this update): no fund module imports it; it imports only `vinci.config`, the existing LLM client and the HTTP cache (AST-pinned); it has its own SQLite registry; it has no buy / sell / target / weight field; its priority rules read no prices, returns or outcomes.

**This update adds the analytical safeguards the cleaned paid run called for** — next section. Earlier updates are condensed at the end; their full write-ups are in the records and in `docs/theme_intelligence/pr-body-history/`.

- **Code:** all inside `vinci/theme_intelligence/`. One new module, `coverage.py`. Changed: `extract.py`, `completeness.py`, `ingest.py`, `__main__.py` (`reask-part`), `engine.py`, `priority.py`, `timewindow.py`, `documents.py`, `parse.py`, `pipeline.py`, `report.py`, `schemas.py`, `store.py`, `config.py`.
- **Changed outside the package:** `STATE.md` (§2 line, §5.0 row 32 item 8), `docs/engineering.md` (glossary), `docs/theme_intelligence.md` (guide), a new record and an amendment to the previous one, tests, worked output.
- **Untouched:**
  - the PDF parser's reading of text (the cleaned Gridlock text is byte-identical — the token saving stands), the model, the prompts;
  - prompt caching (OFF), Batch API (not used), the seven publishers;
  - fund decision / valuation / portfolio / trading / historical-alpha-audit code.

Record: `docs/records/2026-10-12-theme-intelligence-analytical-safeguards.md` · Guide: `docs/theme_intelligence.md` · Worked output: `docs/theme_intelligence/analytical-safeguards-2026-10-12/`

**New API spend: $0.00. Not merged. The production weekly schedule is not enabled. The production state branch was not created.**

---

## Analytical safeguards (this update)

Everything below was measured at **$0**, on the paid cleaned Gridlock run's own saved answers (replayed into fresh and copied registries) and on offline fixtures. **No model call was made.**

### P0 — a malformed field costs that field, never the answer

- `extract.salvage_fields`: an answer whose top level fails is read **field by field, then item by item**.
  - A list sent as valid JSON text is decoded.
  - A field that is neither is discarded whole, with the exact error and the item ids its text names. Those ids are reported, never used.
  - The paid answer file is never rewritten.
- A recovered part joins the result and is verified like any answer, but is **not shown to later parts**. Later requests therefore stay exactly as paid, and a replay costs $0.
- References to rejected claims cannot vouch for anything, pinned end to end: the figure stays `capture_not_verified`, the paragraph `account_names_no_record`.
- **`reask-part --doc D-… --part N --max-cost X`** pays for that one part only:
  - the whole chain must first reproduce from the cache, otherwise nothing is sent;
  - the call is bounded against `--max-cost`, which is required (no default);
  - the new answer is kept beside the paid original.
- **Real, Gridlock part 4 of 13:** recovered **14 claims, 4 mentions, 1 risk, 2 hypothesis additions, 25 figure + 25 paragraph reviews**. Only `added_hypotheses` was lost: 4,420 characters that are not valid JSON ("Expecting property name enclosed in double quotes: line 1 column 938"), which named one proposition.

### P0 — no distinct mechanism disappears without an alert

`coverage.py` (new) runs after every analysis. Its results are stored on the completeness report, raised as `MECHANISM_COVERAGE` issues, and shown in research verification, which then reads INCOMPLETE.
- **Propositions:** every hypothesis a model pass proposed is on a card, merged under one identity key, or dropped with the reason.
  - A merge names both propositions and their shared vs own evidence; distinct evidence raises an alert.
  - A proposition named only in a malformed field counts as dropped.
- **Evidence:** verified material facts that no thesis carries are listed by page. Facts carried by a market risk or by an earlier version's card don't count.
  - Each group is marked excluded (with the completeness verdict's reason), related, or unexplained.
  - Two or more unexplained facts on one page raise an alert; a lone fact is listed only.
- **Risks:** every proposed risk shows which card(s) it is on, or why it was dropped.
- **Names:** organisations a cited paragraph names as examples or as a dated source, but that were never recorded, are listed for review — never added automatically.
- **No card is forced, and nothing merges by similarity.**

### P0 — missing timing never upgrades a thesis

- **Windows written in words are now read:** "next five years", "next decade", "before 2030", "into the 2030s", "the end of the decade".
- **An opinion with a far horizon counts as long-dated,** never as near-term.
- **SKIP-3 also reads beyond the card's citations:** the thesis's other links and the verified claims in its source paragraphs. These count for long-dated timing only.
- **With no dated window anywhere, the thesis stays WATCH** and now says "timing UNKNOWN in the source evidence; a review should establish it".

### P1

- **Re-read.**
  - A new thesis that repeats at least half the sentences of a thesis from an earlier version of the same article is flagged `SAME_ARTICLE_SIBLING`. It is never merged.
  - A fact an earlier version's card already carries raises no alert.
  - Offline fixtures cover the production path with alignment hints on.
- **Preflight.** Estimated from the text actually sent and the number of parts. The high end prices every call at its full output cap. The $30 default and every per-call bound are unchanged.
- **Unread pages.** Each one is classified from readable evidence only: back matter, possibly material, or unclassified.
  - Only when every unread page is back matter, confirmed by the document's own contents list, does the research-action gate treat the analysis text as whole. F11 says why.
  - The document itself stays PARTIAL.
- **Risks, companies, written numbers.** Investigated case by case — see the correction below.

### Measured — the Gridlock analysis, before and after (all $0 except the paid run)

| | baseline (the $46.67 answers) | paid cleaned run ($11.70) | cleaned answers + safeguards |
|---|---|---|---|
| open figures + paragraphs | 6 + 4 | **27 + 27** | **6 + 5** |
| actions | WATCH 5 · SKIP 11 | WATCH 6 · SKIP 8 | WATCH 3 · SKIP 11 |
| RESEARCH NOW | 0 | 0 | 0 |
| held at the $30 default? | — | yes ($31.40 est.) | **no** ($6.56–$20.77 est.) |
| mechanism-coverage alerts | — | — | **6** |

**The three SKIP→WATCH theses are SKIP-3 again, each on the source's own sentence:**

| thesis | sentence that now decides it | how it is read |
|---|---|---|
| midstream capex | "We forecast annual capex over the next five years to be >2x …" | long-dated forecast |
| skilled labour | "The shortage is unlikely to clear before 2030 …" | an opinion with a horizon, recovered from part 4 |
| nuclear | "… over the next decade" | long-dated forecast |

**The 6 coverage alerts (all of them):**
1. **Dropped:** "Regulatory reform to accelerate large-load grid connection …" (the malformed field). Its evidence was kept, and the re-ask command is given.
2. **Merged:** "Fuel cells gain data center share …" was folded into the gas-generation thesis under one identity key, with **0 supporting claims shared and 17 of its own**.
3. **Pages 7, 14, 16:** 6, 4 and 2 verified facts that no thesis carries.
4. **Page 37:** 4 verified facts that no thesis carries — **the low-cost US natural gas argument** (Henry Hub $2–4/MMBtu; Asian LNG ~$8, surging to ~$20; $5–8 by decade-end).

Coverage overall: 16 propositions accounted for (14 on cards, 1 merged, 1 dropped); 24 uncarried facts in 12 page groups; 11 risks, each with its card(s); 9 unrecorded names, including Renault, Volvo, Carwow, OLX and CBRE.

**Re-read of the real PDF** (a copy of the baseline registry; a labelled harness with alignment hints off):
- 1 article, 1 document, 2 versions;
- **0 duplicate rows, 0 independent confirmations**;
- 7 sibling theses flagged — e.g. the transformer story re-keyed, with 60 of its 67 sentences already on the earlier thesis;
- page 37 is not alerted there, because the earlier version's gas card still carries it.

**Preflight vs measured (list price):**

| report | old estimate | new estimate | measured |
|---|---|---|---|
| Gridlock as first read | $9.20–$50.30 | $28.54–$58.92 (held) | $46.67 |
| Gridlock cleaned | $5.60–$31.40 (held) | **$6.56–$20.77** | **$11.70** |
| LatAm | $4.40–$25.10 | $6.60–$19.82 | $9.47 |
| ETF | $3.20–$18.80 | $3.75–$14.10 | $3.80 |

**Unread pages.** Gridlock pages 54–60 are all classed as back matter:
- **Fine print:** 13,229–56,781 characters per page at 9pt, against a median readable page of 2,430 characters at 10pt.
- **Position:** after page 51, the last section the document's contents list names, with no readable analysis after them.
- **Effect:** the research gate treats the analysis text as whole, while verification still reads "1 article read only in part". The synthetic mixed fixture's pages stay unclassified.

### Final acceptance

| # | criterion | result |
|---|---|---|
| 1 | valid content of the malformed response recovered, nothing fabricated | 14 claims, 4 mentions, 1 risk, 50 reviews; the broken field is discarded with its error, and its named id is reported but never used |
| 2 | unaccounted items reduced or explicitly held | open 27 + 27 → 6 + 5; the 1 lost proposition is an alert with a re-ask command |
| 3 | the low-cost gas mechanism cannot vanish without an alert | page 37 alerts (and is pinned on a synthetic fixture of the same shape) |
| 4 | defensible source-based timing for the three theses | all SKIP-3, each with the source sentence named |
| 5 | risks, company roles, written-number qualifications accounted for | see "Correction" and "Still open" |
| 6 | a normal re-read: no false confirmation, no unexplained duplicates | offline, alignment hints ON: the aligned story updates the same thesis (REPEATED); the story keyed anew is flagged; one shared sentence in three is not flagged |
| 7 | seven-source scanner and card structure unchanged | `sources.toml` and the card sections are untouched; their tests pass |
| 8 | glyph quarantine still saves the tokens | the cleaned text's content sha `6ea8321738bb3305` is unchanged |
| 9 | spending limits and privacy intact | $30 default pinned; per-call guard unchanged; `reask-part` needs `--max-cost`; the new coverage record holds claim ids, proposition titles, risk lines and organisation names — no article text |

### Correction

The previous update said "added gradually over four years from 2025 to 2028" was silently missed because the ledger "counts digits". **That was wrong.**
- The ledger does read counted periods written in words.
- Pass 1b judged that figure immaterial and gave a reason ("capacity addition timing assumption, modeling context").
- The previous record carries an amendment.

### Still open (not done in this pass)

- **Re-ask Gridlock part 4** to recover its one lost proposition: `reask-part --doc D-c6f361d4d57a6196 --part 4 --max-cost 1.20`. The call is bounded at $0.98. Not run without your approval.
- **A re-asked answer only applies at the next analysis of that version** (a replay or a re-read), not in place — the registry is append-only.
- **The six coverage alerts need a reviewer:**
  - Whether the gas mechanism deserves a card is your call.
  - Fuel cells stay merged by the identity rule. Splitting hypotheses that share a key but have distinct evidence would be an identity-rule change.
- **Two baseline risks are on no card and flagged by no check:** European "bragawatts" (page 47) and raw-material inflation on storage returns (page 33). A risk stated inside an already-accounted paragraph is not tracked.
- **Coverage and sibling thresholds are face-validity choices** (2 facts per page; ≥ half the sentences). Each has a stated falsifier.
- **No control draw yet:** run-to-run variability is still unmeasured (~$12 for one).

### Screenshot

The replay's real weekly report (other sections removed for the picture):

![coverage](https://github.com/techmuns/mosaic-theory/blob/claude/theme-intelligence/docs/theme_intelligence/analytical-safeguards-2026-10-12/screenshots/weekly-report-mechanism-coverage.png?raw=true)

### Tests, mutants, gate

- **New tests:**
  - `tests/test_theme_intelligence_safeguards.py` (33): the real malformed shape, JSON-text decoding, rejected claims never vouching (end to end), coverage alerts by page, distinct-evidence merges, named-but-unrecorded companies, timing words, opinion horizons, SKIP-3 from the source paragraph (end to end), near-term context never upgrading a thesis, unread-page classes, the back-matter gate (end to end), the four measured costs, and written numbers.
  - +4 in `test_theme_intelligence_long_articles.py`: a recovered part is never fed forward and replays free; re-ask sends one part; a whole answer is never re-asked; nothing is sent when the chain can't be reproduced.
  - +3 in `test_theme_intelligence_glyph_quarantine.py`: the re-read with alignment hints on; cross-citation is not a sibling; an earlier card's fact raises no alert.
- **Changed tests:** 2 rewritten — a malformed field no longer leaves the pass "not run". The preflight calibration test moved to the new model.
- **Mutants:** 24, all killed. One survived at first (the place-name filter) and was then pinned.
- **Gate:** ruff (vinci, tests, frontend) clean; `mypy --strict vinci` clean, 184 files; `pytest -m "not network"`: **4,919 passed, 511 skipped, 0 failed** (final tree, `95dc64a9`).

| brief item | disposition | note |
|---|---|---|
| P0 salvage 1–3 (field by field, keep valid, exact errors) | SHIPPED | real part 4 recovered |
| P0 salvage 4 (rejected refs cannot verify) | SHIPPED | pinned end to end |
| P0 salvage 5 (paid response kept) | SHIPPED | the file is byte-unchanged; a re-ask is written beside it |
| P0 salvage 6 ($0 recovery of the saved response) | SHIPPED | |
| P0 salvage 7 (re-run only the affected segment) | SHIPPED | `reask-part`; applies at the next analysis of the version |
| P0 salvage 8 (no automatic paid calls) | SHIPPED | `--max-cost` required; none run |
| P0 coverage 1–3, 6, 7 | SHIPPED | `coverage.py` |
| P0 coverage 4 (the low-cost gas mechanism) | SHIPPED | real page 37 alert; synthetic pin |
| P0 coverage 5 (fuel cells merged?) | SHIPPED | yes — merged on one key, now alerted; splitting is a decision for you |
| P0 timing 1–5 | SHIPPED | the three theses are SKIP-3 on source sentences |
| P1 companies and risks | PARTIAL | companies listed for review; 2 baseline risks unflagged |
| P1 written-number qualification | SHIPPED | it was not missed (correction); a figure without a verdict stays open (pinned) |
| P1 re-read workflow (offline, alignment on) | SHIPPED | |
| P1 preflight calibration | SHIPPED | all four measured costs in range; $30 kept |
| P1 unread pages | SHIPPED | back matter / possibly material / unclassified |
| tests, mutation, ruff, mypy, suite | SHIPPED | |
| GitHub CI | PENDING | read after push |
| not merged; schedule off; no production state branch; no fund code | SHIPPED | |

---

## Earlier updates (condensed; full text: `docs/theme_intelligence/pr-body-history/`)

- **Targeted PDF cost reduction** (`docs/records/2026-10-12-theme-intelligence-pdf-glyph-quarantine.md`):
  - undecodable PDF glyph text is quarantined before anything reads it;
  - Citi Gridlock's one paid acceptance run cost $11.70 vs $46.67 (input tokens 8.1M → 1.3M; completeness calls 22 → 13);
  - `--reread`; a sentence read again is REPEATED, never new.
- **State-pull ledger — the pilot condition** (`docs/records/2026-10-11-theme-intelligence-state-pull-ledger.md`). A pull carries every paid-call record, run id and cost, counted once; a real fresh restore matches every record call by call (19 calls, $1.7882).
- **Seven-source corrections** (`docs/records/2026-10-11-theme-intelligence-seven-sources.md`):
  - Bank of America retired;
  - identity before ticker;
  - a market regime only on market-structure evidence;
  - spending limits before every call;
  - per-version dates;
  - state sync on the real repository.
- **Hybrid research ingestion · source health · review rounds 2–3 · the original build** — see the records named in `STATE.md` §2.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

