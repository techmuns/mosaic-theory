## Summary

A new, isolated package **`vinci/theme_intelligence/`**: a research discovery and prioritisation tool. It reads research from **seven publisher channels** — five automatic, two manual-first — and from documents the operator supplies. It extracts source-anchored evidence, named companies and risks; keeps a persistent, versioned registry of theses; and writes a decision-first weekly dashboard of nine-section **Living Thesis Cards**.

**"RESEARCH NOW" means allocate analyst attention — never buy.** The package stays off the fund's decision path (unchanged by this update): no fund module imports it; it imports only `vinci.config`, the existing LLM client and the HTTP cache (AST-pinned); it has its own SQLite registry; it has no buy / sell / target / weight field; its priority rules read no prices, returns or outcomes.

**This update closes the last thesis-identity issues before a supervised pilot** — next section. Earlier updates are condensed at the end; their full write-ups are in the records and in `docs/theme_intelligence/pr-body-history/`.

- **Code:** inside `vinci/theme_intelligence/` only — `engine.py`, `store.py`, `coverage.py`, `schemas.py`, `report.py`, `config/taxonomy.toml`.
- **Untouched:**
  - the prompts, the model and the PDF reader;
  - the seven channels and source health;
  - cost limits, licensing holds and privacy;
  - fund decision code.

Record: `docs/records/2026-10-12-theme-intelligence-pilot-closeout.md` · Guide: `docs/theme_intelligence.md` (incl. the pilot checklist) · Worked output: `docs/theme_intelligence/pilot-closeout-2026-10-12/`

**New API spend: $0.00.** Not merged. The weekly schedule is not enabled. The production state branch was not created.

---

## Final identity closeout (this update)

### Corrections

- **The two fuel-cell readings are one thesis.**
  - Two readings of one article that share **at least two thirds of EACH side's evidence** are one causal chain, even when they name different kinds of mechanism (share gain vs demand volume).
  - The earlier ID `TH-DDEE0B7EF0` and its mechanism are kept. The other label is stated, with what each step means for earnings.
  - If either side has substantial evidence of its own, it may be a second, separately falsifiable mechanism. It then goes to review, with both consequences spelled out.
  - This reads the evidence each time. There is no blanket share/volume merge and no fuel-cell exception.
- **A thesis's segment is its economic subject.**
  - Order: what the thesis statement names → its product, or the sectors the source names as exposed → segments named in at least a fifth of its evidence. Otherwise it is left unassigned, never set from a passing mention.
  - New segment: *transformers / grid equipment*.
  - When a re-read reaches a thesis whose key was set wrongly by the old rule, the key is corrected. Same ID, versions and evidence; the old key is recorded (`KEY_CORRECTED`). It never takes a key another thesis holds, and the old key still finds the thesis.
- **A latent hazard is closed.** A thesis with no segment could absorb another story from the same article with the same node, mechanism and place. It now needs a shared sentence. The real re-read hit this once; the verification-hold invariant refused it loudly.
- **The review queue keeps evidence and assessment apart.**
  - Page alerts list the source's figures as written, marked **UNASSESSED** in that registry (page 37: `$2 to $4; $8; ~$20; $5 to $8`).
  - The low-cost gas card's established **SKIP-3** stays on its card.
- **Page 16 (600 GW vs 183 GW)** is ambiguous, so it stays a review item and is not linked. The source uses the figure for speculative, duplicated grid-queue requests ("projects that may never be built"). The power-scarcity thesis is about bargaining power moving to whoever holds capacity, which the figure doesn't show.
- **No-evidence propositions are no longer listed as opportunities.** SKIP-1 propositions move to their own section, "Not research opportunities", with the reason and the card. They stay in the counts, the archive and the print.

### Before / after (Citi Gridlock, cached answers, $0)

| | Before | After |
|---|---|---|
| Re-read into the first reading's registry — Gridlock theses | 18 | **17** |
| … held for review (fuel cells) | 1 | **0** — `TH-DDEE0B7EF0` updated v1 → v2, WATCH |
| … matched under an existing ID / duplicates / independent confirmations | 7 / 0 / 0 | **8 / 0 / 0** |
| Transformer thesis key | `seg:onsite_generation` | **`seg:grid_equipment`** (same ID `TH-1F366737A1`) |
| Other keys corrected | — | skilled labour, midstream capex → unassigned (were utilities / on-site) |
| Fresh registry: RN / WATCH / SKIP | 0 / 4 / 11 | 0 / 4 / 11 |
| Weekly page: NEW list / not research opportunities | 15 / — | **13 / 2** |

### Pilot-readiness check — 10 of 10 pass (`6-pilot-readiness.txt`)

1. **Fuel cells:** one fuel-cell thesis per registry, 0 siblings.
2. **Transformer:** keyed `seg:grid_equipment` in both registries.
3. **History:** all 20 baseline theses are present, every earlier version is byte-identical, and the first-ingested times and the article's 2026-06-28 date are unchanged.
4. **No double-counting:** 0 independent confirmations, 0 repeated rows.
5. **Limits stay visible:** verification reads INCOMPLETE, with 10 alerts.
6. **Cards:** all 36 rendered cards have all nine sections.
7. **Sources:** 7 channels; sources, health and fetch code unchanged; 4 pinning tests pass.
8. **One registry:** the automatic and manual paths share it (4 tests).
9. **Controls:** the $30 limit, licence holds, run budgets, no research document in git, and credentials never printed (9 tests).
10. **Fund code:** no file under `vinci/` outside the package changed, and 5 isolation tests pass. The only two files outside the package are reviewed earlier changes: the PDF-reader dependency and a stricter fund guard.

### Still open — your decisions

- **Low-cost US gas in a fresh registry.** It has no card there without a model proposal. A targeted page-37 re-ask needs your approval.
- **One evidence-less pair** (SKIP-1) can't be identity-checked. Both are now listed as not research opportunities.
- **Wording.** On a same-article re-read, the card's source row says "Direct confirmation — new evidence". That is round 3's label for same-identity new evidence, not the independent-confirmation class (which is 0). Reword it?
- **Untouched keys.** A key is corrected only when a re-read reaches the thesis. There is no bulk migration.

### Operator checklist — one supervised pilot (full version in the guide)

1. Keep the cron **off**. Keys stay in the environment and are never printed.
2. Run `sources --check-health`. Morgan Stanley and Goldman Sachs arrive only as uploads, into the same registry.
3. Confirm each licensed report's LLM terms before `--llm-permitted`.
4. Keep the **$30** per-document limit and set a scan `--budget`.
5. `state pull` → one scan by hand (small `--max-articles`, `--budget`) → `qa --run latest`.
6. Read in this order:
   - verification status;
   - coverage alerts (figures UNASSESSED; source-stated risks);
   - Research Now / Watch cards (06, 07, 08, 09);
   - identity flags (`SAME_ARTICLE_SIBLING`, `KEY_CORRECTED`, `PRODUCT_SPLIT`);
   - "Not research opportunities".
7. Record each verdict, plus the actual spend from `manifest.json` and the paid-call ledger.
8. **Stop and report** if any of these happens:
   - a call is paid beyond the budget;
   - one story yields two opportunities;
   - a re-read shows up as an independent confirmation;
   - a card is missing a section;
   - a document is analysed before its licence was confirmed.

### Screenshots (real runs)

![review queue](https://github.com/techmuns/mosaic-theory/blob/claude/theme-intelligence/docs/theme_intelligence/pilot-closeout-2026-10-12/screenshots/weekly-report-review-queue.png?raw=true)

![not opportunities](https://github.com/techmuns/mosaic-theory/blob/claude/theme-intelligence/docs/theme_intelligence/pilot-closeout-2026-10-12/screenshots/weekly-report-not-opportunities.png?raw=true)

### Tests, mutants, gate

- **Tests:**
  - `test_theme_intelligence_glyph_quarantine.py`: +6 — the same evidence is one chain ×2; partial evidence goes to review; key correction on all 3 routes; a blank segment is no shared subject; no absorption; a held key is never taken. 2 tests moved to the distinct-evidence variant.
  - `test_theme_intelligence_safeguards.py`: +2 — the segment rule, 7 cases (transformer, gas turbines, recips, fuel cells, cross-sector comparisons, evidence share, the source's exposure); the product sets the segment end to end. Also the alert figures.
  - `test_theme_intelligence_overlap.py`: no-evidence propositions are kept apart, counted and rendered.
- **Mutants:** **18 of the new guards, all killed.** Four survived the first round and were then pinned. The previous rounds' 29 + 22 were re-run: all killed.
- **Gate:**
  - ruff clean; `mypy --strict vinci` clean;
  - `pytest -m "not network"`: **4,958 passed, 511 skipped, 0 failed** (final tree; code `5db3b514`);
  - CI: read after push.

| brief item | disposition | note |
|---|---|---|
| P0 reconcile the fuel-cell theses | SHIPPED | one thesis on the same evidence; `TH-DDEE0B7EF0` kept; distinct evidence → review |
| P0 transformer subject / generic segmentation | SHIPPED | statement → product / exposure → evidence share; grid-equipment segment; safe key correction; regressions as asked |
| P1 low-cost gas kept visible | SHIPPED | figures UNASSESSED in the queue; SKIP-3 on its card; no re-ask |
| P1 page 16 | SHIPPED | ambiguous → review item, not linked |
| P1 no-evidence propositions not actionable | SHIPPED | own section; audit kept |
| P1 pilot-readiness 1–10 | SHIPPED | 10 / 10 |
| operator pilot checklist | SHIPPED | here and in the guide |
| tests, mutation, ruff, mypy, suite | SHIPPED | |
| GitHub CI | PENDING | read after push |
| not merged; schedule off; no production state branch; no fund code | SHIPPED | |

---

## Earlier updates (condensed; full text: `docs/theme_intelligence/pr-body-history/`)

- **Coverage and identity** (`docs/records/2026-10-12-theme-intelligence-coverage-identity.md`):
  - the part-4 re-ask ($0.5278);
  - one technology per thesis (fuel cells split from gas generation);
  - same-article identity matches;
  - risks the source states;
  - the low-cost gas card re-verified (WATCH → SKIP-3).
- **Analytical safeguards** (`docs/records/2026-10-12-theme-intelligence-analytical-safeguards.md`): field-by-field salvage, mechanism coverage, the timing rules, the preflight, unread back matter.
- **Targeted PDF cost reduction** (`docs/records/2026-10-12-theme-intelligence-pdf-glyph-quarantine.md`): Gridlock $11.70 vs $46.67; `--reread`.
- **State-pull ledger · seven-source corrections · hybrid ingestion · source health · review rounds 2–3 · the original build** — see the records named in `STATE.md` §2.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

