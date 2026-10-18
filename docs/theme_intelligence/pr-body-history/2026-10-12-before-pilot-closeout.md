## Summary

A new, isolated package **`vinci/theme_intelligence/`**: a research discovery and prioritisation tool. It reads research from **seven publisher channels** — five automatic, two manual-first — and from documents the operator supplies. It extracts source-anchored evidence, named companies and risks; keeps a persistent, versioned registry of theses; and writes a decision-first weekly dashboard of nine-section **Living Thesis Cards**.

**"RESEARCH NOW" means allocate analyst attention — never buy.** The package stays off the fund's decision path (unchanged by this update): no fund module imports it; it imports only `vinci.config`, the existing LLM client and the HTTP cache (AST-pinned); it has its own SQLite registry; it has no buy / sell / target / weight field; its priority rules read no prices, returns or outcomes.

**This update resolves the outstanding thesis coverage and identity issues** — next section. Earlier updates are condensed at the end; their full write-ups are in the records and in `docs/theme_intelligence/pr-body-history/`.

- **Code:** all inside `vinci/theme_intelligence/` — `engine.py`, `coverage.py`, `pipeline.py`, `schemas.py`, `verify.py`, `completeness.py`, `extract.py`, `contradiction.py`, `report.py`, `config.py`, `config/taxonomy.toml`.
- **Changed outside the package:** `STATE.md` (§2 line, §5.0 row 32 item 8), `docs/engineering.md` (glossary), `docs/theme_intelligence.md` (guide), a new record, tests, worked output.
- **Untouched:** the prompts, the model, the PDF reader, prompt caching (OFF), the seven publishers, the cost limits, fund decision / valuation / portfolio / trading code.

Record: `docs/records/2026-10-12-theme-intelligence-coverage-identity.md` · Guide: `docs/theme_intelligence.md` · Worked output: `docs/theme_intelligence/coverage-identity-2026-10-12/`

**New API spend: $0.5278** — the one approved re-ask, nothing else (no full re-analysis, no card-review call). **Not merged. The weekly schedule is not enabled. The production state branch was not created.**

---

## Coverage and identity (this update)

### What changed

- **P0 · the part-4 re-ask** (the approved call, `reask-part --doc D-c6f361d4d57a6196 --part 4 --max-cost 1.20`):
  - ONE call, **$0.5278**. The chain reproduced from the cache first. All 41 cached answer files are byte-unchanged; the re-ask is kept beside the paid original.
  - It recovered 15 claims, 4 mentions, 3 additions to hypotheses, and 25 figure + 26 paragraph reviews.
  - It proposed **no new hypothesis**. The regulatory-reform proposition is listed as **dropped, with that reason**, so it has no thesis and no RN / WATCH / SKIP. Its evidence went to the transformer, gas-generation and skilled-labour theses.
  - The nearest held thesis ("Uneven U.S. regional power regulation…") is **SKIP-2** (no fundamental transmission step).
- **P0 · one technology per thesis:**
  - On-site generation is now three taxonomy products (gas turbines, reciprocating engines, fuel cells) under a generic one. Mechanisms carry a *family* (the kind of economics).
  - A thesis's product is the one its own statement names, else one at least a fifth of its cited claims name.
  - Two hypotheses on one key that share no supporting claim and name different products are **separate theses** (`|prod:`).
  - A risk naming only the split-off product goes with it, and the registry link names the product difference.
  - No fuel-cell rule: it is the taxonomy.
- **P0 · low-cost US natural gas:**
  - Where the first reading made the card, the re-read **re-verifies** it (4 of 4 sentences) and re-assesses it: **WATCH → SKIP-3** (the only dated element is the LNG glut "towards the end of this decade").
  - The nine-section card is in the worked output. It covers: industry economics (Henry Hub $2–4 vs Asian/European LNG); the companies the source names (WMB, KMI — unresolved to listed lines); earnings transmission (MODEL INFERENCE — not source-shown); market expectations (NOT ASSESSED); why it matters within 2–4 quarters (no dated window); falsifiers and next steps.
  - In a **fresh** registry the cleaned run's model proposed no thesis for page 37. The engine never writes one without a model proposal, so it stays an alert (reason in the record).
- **P1 · risks the source states:**
  - A sentence that states a downside in the source's own construction ("risks remaining", "might put downward pressure", "did not materialize", "execution risk remains") is checked against what already carries it. It is never matched on the bare word "risk", and never when the risk is said to be absent ("little risk of oversupply").
  - If nothing carries it, it goes **verbatim into 07 of only the cards whose evidence shares its paragraph**, labelled **SOURCE OPINION** and flagged. With no such card, or if a page break cut it, it is alerted and placed nowhere.
  - No generic disclaimer is added to every card.
- **P1 · one thesis per story across versions:**
  - A re-read hypothesis holding ≥ half its sentences on a thesis from the same article **updates that thesis**. Direction, geography, mechanism family, segment, product and horizon must agree; a node *label* difference is stated, never blocking.
  - Any other difference → created, **held for review** (never RN), flagged.
  - Overlapping sentences alone never merge.
- **Two re-read defects found and fixed on the real run:**
  - a sentence read twice counted twice as material evidence (gas thesis 4 → 8);
  - "~75K units" scaled two ways made a duplicate row.

### Research priorities — before vs after (cleaned Gridlock, $0 replays)

| | Before (previous code) | After |
|---|---|---|
| Theses | 14 | **15** |
| RESEARCH NOW | 0 | **0** |
| WATCH | 3 — transformer, gas generation (fuel cells merged in), powered land | **4** — transformer, gas generation, **fuel cells (separate)**, powered land |
| SKIP | 11 | 11 |
| Coverage alerts | 4 (incl. "fuel cells merged") | 10 (no merge alert; 6 risk sentences no model pass listed; pages 7, 16, 37) |

The fuel-cell thesis is WATCH because there is no verified dislocation or catalyst; being separate earns it nothing.

### Theses — created / updated / separated / held (re-read into the first reading's registry)

| Outcome | Theses |
|---|---|
| **Separated** | fuel cells from gas generation (by product, 0 of 17 supporting claims shared) |
| **Matched — same id updated** | transformer (61 of 68 sentences), powered land, China buildout, power scarcity, midstream capex, skilled labour, energy security — five of them only a node label apart |
| **Updated by unchanged key** | gas generation, regional regulation, nuclear, energy infrastructure, Australia, European grid (attribution only) |
| **Re-verified, re-assessed** | low-cost US gas (WATCH → SKIP-3); the first fuel-cell thesis (WATCH kept) |
| **Held for review** | the cleaned fuel-cell hypothesis vs the first fuel-cell thesis — 14 of 17 sentences shared, mechanism family differs (share shift vs demand volume) |
| **Created** | one evidence-less proposition ("Citi Wealth recommends selective AI capex…", SKIP-1) — nothing to identity-check |

**0 duplicate evidence rows. 0 independent confirmations. 0 paid calls.** Before this update the same re-read gave 7 siblings and 0 matches.

### Remaining coverage alerts — triaged (facts in `6-coverage-alert-triage.txt`)

| Alert | Class |
|---|---|
| page 7 — 6 facts | **background** — the shared data-centre demand backdrop; its two headline figures are on the gas-generation card from page 14; 2 of 6 are chart labels |
| page 14 | **represented** — no longer an alert; the re-ask put its 3 facts on gas generation |
| page 16 — 600 GW vs 183 GW | **unresolved** — relevant to the power-scarcity thesis (SKIP-1, no verified material evidence); not attached automatically |
| page 16 — 1 GW dropped off | **risk / counter-evidence** — carried by the NERC load-volatility risk |
| page 37 — 4 facts | **distinct thesis** — low-cost US gas (above) |
| 6 risk sentences | 4 placed on their paragraph's cards; 2 cut by a page break (alerted only) |

### Screenshots (real runs)

Weekly report — coverage alerts, each sentence whole:
![alerts](https://github.com/techmuns/mosaic-theory/blob/claude/theme-intelligence/docs/theme_intelligence/coverage-identity-2026-10-12/screenshots/weekly-report-coverage-alerts.png?raw=true)

Regional-regulation card — three risks the source states, as SOURCE OPINION, none withheld:
![regional](https://github.com/techmuns/mosaic-theory/blob/claude/theme-intelligence/docs/theme_intelligence/coverage-identity-2026-10-12/screenshots/regional-regulation-card-07-source-risks.png?raw=true)

Fuel-cell card — a separate thesis; the link to gas generation names the product; the scandium risk is here:
![fuel](https://github.com/techmuns/mosaic-theory/blob/claude/theme-intelligence/docs/theme_intelligence/coverage-identity-2026-10-12/screenshots/fuel-cell-card-07.png?raw=true)

### Final acceptance

| # | Criterion | Result |
|---|---|---|
| 1 | re-ask completes or fails explicitly, no other paid call | completed, $0.5278, one call |
| 2 | fuel cells and gas generation not combined | separate theses (`|prod:fuel_cells`) |
| 3 | low-cost gas treated defensibly | re-verified card SKIP-3; fresh registry: alert with its reason |
| 4 | the two risks accounted for | this reading's model wrote both as alternative mechanisms on the right cards (carried); the flag path placed each on that card when they were not carried (shown on the same answers) |
| 5 | same-article reruns update identities when justified | 7 matched (transformer 61/68) |
| 6 | distinct themes stay separate | different mechanism family / direction → held for review (pinned) |
| 7 | remaining alerts explained | table above |
| 8 | no duplicate evidence or confirmation through replay | 0 / 0; a twice-counted sentence and a twice-scaled figure fixed |
| 9 | nine-section cards, seven publishers, cost limits, PDF cleanup unchanged | unchanged |

### Remaining gaps

- **Low-cost gas in a fresh registry:** no card without a model proposal. A targeted re-ask of that paragraph needs your approval.
- **The fuel-cell pair** (cleaned hypothesis vs first-reading thesis) is held for your decision.
- **One evidence-less pair** (SKIP-1) can't be identity-checked.
- **The transformer thesis is keyed segment `onsite_generation`** (it was in the paid run too). Not changed here.
- **The first reading cannot be replayed at $0.** Its prompt no longer reproduces; the cache miss failed loudly with nothing sent.
- **A placed source risk is a new card line**, so production re-reviews that card (normal cost). Here the replays ran without the paid review pass.

### Tests, mutants, gate

- **Tests:**
  - `tests/test_theme_intelligence_safeguards.py`: +7 (8 new, 1 replaced).
  - `test_theme_intelligence_glyph_quarantine.py`: +4 (6 cases), plus 1 extended.
  - `test_theme_intelligence_long_articles.py`: +1, plus 1 updated for the new accounting.
- **Mutants:** **32 of this pass's guards, all killed.** Three survived the first round and were pinned. The previous pass's 22 applicable mutants were re-run, all killed.
- **Gate:**
  - ruff clean; `mypy --strict vinci` clean;
  - `pytest -m "not network"`: **4,935 passed, 511 skipped, 0 failed** (final code `511b352b`);
  - every docs-reading test re-run green after the docs commit.

| brief item | disposition | note |
|---|---|---|
| P0 re-ask part 4 (one call, $1.20 limit, originals kept, reuse others, verify refs, $0 replay, classification, spend) | SHIPPED | $0.5278; no new hypothesis → dropped with reason; nearest thesis SKIP-2 |
| P0 separate economic mechanisms | SHIPPED | product-qualified identity, real Gridlock evidence; no fuel-cell exception |
| P0 low-cost US gas | SHIPPED (registry with the first reading) / PARTIAL (fresh registry) | fresh: no model proposal — alert + reason; re-ask needs approval |
| P1 omitted risks | SHIPPED | scan + placement; both named risks accounted for |
| P1 same-article siblings | SHIPPED | 7 matched, 1 held for review, 0 duplicates / confirmations |
| P1 alert triage | SHIPPED | table above |
| tests, mutation, ruff, mypy, suite | SHIPPED | |
| GitHub CI | PENDING | read after push |
| not merged; schedule off; no production state branch; no fund code | SHIPPED | |

---

## Earlier updates (condensed; full text: `docs/theme_intelligence/pr-body-history/`)

- **Analytical safeguards** (`docs/records/2026-10-12-theme-intelligence-analytical-safeguards.md`):
  - a malformed answer field costs that field, and `reask-part` re-asks one part;
  - mechanism-coverage alerts;
  - SKIP-3 reads the source's long-dated sentences;
  - re-read siblings flagged;
  - the preflight estimates from the text sent;
  - unread back matter classified.
- **Targeted PDF cost reduction** (`docs/records/2026-10-12-theme-intelligence-pdf-glyph-quarantine.md`):
  - undecodable glyph text is quarantined;
  - Gridlock $11.70 vs $46.67;
  - `--reread`; a sentence read again is REPEATED, never new.
- **State-pull ledger — the pilot condition** (`docs/records/2026-10-11-theme-intelligence-state-pull-ledger.md`).
- **Seven-source corrections** (`docs/records/2026-10-11-theme-intelligence-seven-sources.md`).
- **Hybrid research ingestion · source health · review rounds 2–3 · the original build** — see the records named in `STATE.md` §2.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

