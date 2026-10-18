## Summary

A new, isolated package **`vinci/theme_intelligence/`** — a research discovery and prioritisation tool.
- It reads research from **seven publisher channels** (five automatic, two manual-first) and from documents the operator supplies.
- It extracts source-anchored evidence, named companies and risks.
- It keeps a persistent, versioned registry of theses and writes a weekly dashboard of nine-section **Living Thesis Cards**.

**"RESEARCH NOW" means allocate analyst attention — never buy.** The package stays off the fund's decision path:
- no fund module imports it;
- it imports only `vinci.config`, the existing LLM client and the HTTP cache (AST-pinned);
- it has its own SQLite registry;
- it has no buy, sell, target or weight field;
- its priority rules read no prices, returns or outcomes.

**This update fixes the three material defects the supervised pilot found**, plus one small metadata correction. It was approved as a narrow correction, and the demonstrations spent **$0** on new model calls.

- **Code:** inside `vinci/theme_intelligence/` only.
- **Untouched:** PDF optimisation, publisher configuration, state sync, thesis identity, and fund decision code.
- **Not merged; no schedule; no production state branch.** No article text, card or dashboard from the pilot is committed.

**Docs:**
- Record: `docs/records/2026-10-12-theme-intelligence-pilot-corrections.md`
- Pilot record: `docs/records/2026-10-12-theme-intelligence-supervised-pilot.md`
- Guide: `docs/theme_intelligence.md`, "After the pilot"

---

## Pilot corrections (this update)

### 1. A malformed first answer is salvaged, never asked again (P0)

- **What changed:**
  - A first answer that fails at the top level is recovered **field by field**, using the completeness pass's existing salvage.
  - A list the model wrote as broken JSON text is mended by **deletion only**: an unkeyed value, or a stray `}`. A mend is kept only if the whole text then decodes with no property given twice, and the items are then verified like any other.
  - A hypothesis that still can't be read becomes a **dropped proposition**. That raises a coverage alert, so the run reads **INCOMPLETE — REVIEW REQUIRED**.
  - Every step is logged as an `ANSWER_SALVAGED` warning, and the paid answer stays on disk exactly as it was returned.
  - The identical re-ask is gone. Answers an earlier run paid for and set aside are salvaged instead of being paid for again.
- **Shown at $0:**
  - **All four saved J.P. Morgan answers** recover the article's one thesis, "earnings broadening beyond the mega-caps". Three needed an extra unkeyed bottom-line sentence deleted, one needed a stray brace deleted. Each answer keeps all its 25–30 claims.
  - End to end on copies of the registry (fresh, and the pilot's state), the article produces one WATCH. Verification says INCOMPLETE because the completeness pass has no saved answer.

### 2. RESEARCH NOW needs real exposure and a real near-term window (P0)

- **What changed:**
  - **A bare page label is not an exposure** (`SECTOR_LABEL_ONLY`): a page line that says nothing but the sector's name, such as TrendForce's "Semiconductors" category tag.
    - Headings, chart titles and standfirsts are untouched.
    - A check of 137 stored exposures across 138 registries found that only TrendForce's category lines match.
    - A broader rule would have caught report section headings and reopened thesis identity.
  - **Near-term means the next four quarters** (previously 549 days).
  - **A window that runs past the next four quarters but mostly falls inside them** is new. It never counts as near-term evidence and never counts as longer-term only, so it gives **WATCH**, not RESEARCH NOW or SKIP-3.
  - **`reassess`** re-grades stored theses from their stored evidence, with no model client. A change is written as a new version; the reviewed sentences are kept word for word and the review findings are carried over.
- **Real pilot registry, $0:**
  - `TH-7C895A0A4E`: **RESEARCH NOW → WATCH** (v2, DOWNGRADED) — near-term relevance `yes` → `runs_past`; source-named exposures 1 → 0; inflection route `qualifies` → `absent`.
  - `TH-1516B6186B`: stays WATCH; the tag is dropped as an exposure.
  - The Nomura WATCH is unchanged.

### 3. Review warnings are shown on the line (P0)

- **What changed:**
  - A line the card review questioned but left printed now shows `⚠ UNRESOLVED REVIEW — <why>` in markdown, HTML, print and JSON, and is never labelled as a verified fact.
  - A conditional line (could / may / might / would / if) is at most SOURCE OPINION when the card is composed. QA expects the same.
- **Shown at $0:** all **7** flagged lines carry their warning (2 TrendForce, 5 Nomura). The two conditional risk lines now print as SOURCE OPINION.

### 4. A stored preview recorded as FULL is corrected (metadata)

- **What changed:**
  - When the current parser reads an already-stored "FULL" version as a preview, a `RETRIEVAL_CORRECTED` record is appended. The record is append-only, already syncs, and needs no schema change.
  - Every reader then sees PARTIAL, and the theses that article fed are re-graded.
  - The original row, first-seen date and spend are never edited.
- **Shown at $0:** the SemiAnalysis preview now reads "0 full · 1 partial", is marked "read only in part", and is listed as awaiting an authorised complete copy.

### Paid J.P. Morgan acceptance test — is it needed?

It is **not needed to prove the fix**: all four saved answers are salvaged at $0. It **is needed to finish the article's analysis**, because its completeness pass and card review never ran.

- **What it would do:** run **one** targeted `article` call in the pilot registry. Pass 1 is salvaged from the saved answer at $0, so only the completeness pass and the card review would be paid.
- **Cost:** estimated **$0.20–$0.60** actual, under a **$2.00** run limit. That is within the $14.05 still unspent of the $18.
- **Waiting for your approval.** No model calls until then.

### Remaining material blockers to supervised weekly use

1. **Source rights.**
   - Publisher licensing is **not confirmed** for J.P. Morgan, TrendForce, Nomura or SemiAnalysis.
   - The Option 2 risk acceptance covered one internal pilot only.
   - The weekly schedule stays off until each publisher grants permission or a licensed feed replaces it.
2. **Coverage depends on those same rights.**
   - 2 of 7 channels are healthy.
   - Morgan Stanley and Goldman Sachs are blocked; Citi, Nomura and SemiAnalysis serve partial pages or previews.
   - Each gap needs an *authorised* upload.

### Tests, mutants, gate

- **Tests:**
  - `tests/test_theme_intelligence_pilot_corrections.py`: 25 tests on the pilot's shapes, using hypothetical text.
  - The salvage tests were rewritten for the new no-re-ask behaviour.
  - One near-term pin was flipped ("2027" as of 2026-10-10) and three were added.
- **Mutants:** **31 of 31 killed** — one per new guard.
- **Gate:**
  - ruff clean; `mypy --strict vinci` clean (184 files).
  - `pytest -m "not network"`: **4,996 passed, 511 skipped, 0 failed** (code `9840e660`).
  - CI: read after push.

| brief item | disposition | note |
|---|---|---|
| P0 initial extraction failure — field-by-field salvage | SHIPPED | the completeness salvage, applied to pass 1 |
| — deterministic recovery, no invented content | SHIPPED | deletion only; refused when a property would be given twice |
| — keep paid answers; name lost hypotheses; INCOMPLETE / REVIEW REQUIRED | SHIPPED | the raw answer kept on disk; dropped proposition → coverage alert |
| — test all four saved J.P. Morgan answers at $0; no repeat of a paid request | SHIPPED | 4/4 recover the thesis; set-aside answers salvaged, never re-paid |
| P0 RESEARCH NOW eligibility — a tag is not an exposure | SHIPPED | `bare_label`; corpus-checked |
| — a genuine near-term window; full-year 2027 not a 2–4-quarter catalyst | SHIPPED | next four quarters; straddling window → WATCH |
| — reassess the RN from stored evidence | SHIPPED | `TH-7C895A0A4E` RESEARCH NOW → WATCH (v2) in the pilot registry |
| P0 review warnings visible | SHIPPED | 7 / 7 on their lines; conditional lines never MEASURED OBSERVATION |
| Metadata — stored previews no longer FULL | SHIPPED | `RETRIEVAL_CORRECTED`; row, first-seen date, spend kept |
| $0 demonstration first | SHIPPED | saved paid answers, HTTP cache, offline fixtures |
| regression tests, mutation, ruff, mypy, full suite | SHIPPED | |
| GitHub CI | PENDING | read after push |
| report whether ONE paid J.P. Morgan test is needed + cost | SHIPPED | not needed for the fix; ~$0.20–$0.60 to finish the article — awaiting approval |
| no rerun of all five; no merge; no schedule; no fund code | SHIPPED | |

---

## Earlier updates (condensed; full text: `docs/theme_intelligence/pr-body-history/`)

- **Supervised pilot** (`docs/records/2026-10-12-theme-intelligence-supervised-pilot.md`):
  - five web articles from four publishers, $3.9494 of $18;
  - verdicts: engineering REVIEW, research REVIEW, readiness FAIL (source rights);
  - the paywall-window fix.
- **Pilot closeout** (`docs/records/2026-10-12-theme-intelligence-pilot-closeout.md`):
  - one fuel-cell thesis;
  - the subject segment;
  - the review queue;
  - the readiness check (10 of 10).
- **Coverage and identity · analytical safeguards · targeted PDF cost reduction · state-pull ledger · seven-source corrections · hybrid ingestion · source health · review rounds 2–3 · the original build:** see the records named in `STATE.md` §2.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

