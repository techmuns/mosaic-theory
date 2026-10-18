## Summary

A new, isolated package **`vinci/theme_intelligence/`**: a research discovery and prioritisation tool. It reads research from **seven publisher channels** — five automatic, two manual-first — and from documents the operator supplies. It extracts source-anchored evidence, named companies and risks; keeps a persistent, versioned registry of theses; and writes a decision-first weekly dashboard of nine-section **Living Thesis Cards**.

**"RESEARCH NOW" means allocate analyst attention — never buy.** The package stays off the fund's decision path (unchanged by this update): no fund module imports it; it imports only `vinci.config`, the existing LLM client and the HTTP cache (AST-pinned); it has its own SQLite registry; it has no buy / sell / target / weight field; its priority rules read no prices, returns or outcomes.

**This update carries out the "final consolidated corrections and seven-source configuration" brief** — next section. Earlier updates are condensed at the end; their full write-ups are in the records and in `docs/theme_intelligence/pr-body-history/`.

- **Code:** all inside `vinci/theme_intelligence/` (one new module, `llm.py`, subclassing the shared client — `vinci/graph/llm.py` itself is untouched).
- **Changed outside the package:** `STATE.md` (§2 line, §5.0 row 32 item 8), `docs/engineering.md` (glossary), `docs/theme_intelligence.md` (guide), `docs/records/2026-10-11-theme-intelligence-seven-sources.md`, tests, worked output; `origin/main` (#704–#706) merged in.
- **Untouched:** fund screen / ranker / dossier / verdict / scoring / valuation / ledger / portfolio / trading / historical-alpha-audit code.

Record: `docs/records/2026-10-11-theme-intelligence-seven-sources.md` · Guide: `docs/theme_intelligence.md` · Worked output: `docs/theme_intelligence/seven-sources-2026-10-11/`

**Not merged. The production weekly schedule is not enabled. The production state branch was not created.**

---

## Seven-source corrections (this update)

### Completed, limitations, cost — at a glance

| | |
|---|---|
| **Completed** | seven publishers (Bank of America retired, history kept, never requeued; MS / GS manual-first) · identity before ticker (Citi's "Delta" no longer Delta Air Lines) · a market regime only on market-structure evidence (5 Citi records corrected; J.P. Morgan's dispersion record kept) · three verification-check defects corrected (Gridlock open figures 17 → 6 of 851, ETF 5 → 1 of 232, from cached answers) · spending limits checked before every paid call · per-version publication dates · state sync exercised against this repository on a temporary branch · four defects the real runs exposed, fixed |
| **Limitations** | the article prompt cache (−45% on one run) ships OFF — equivalence not shown · a `state pull` keeps a replayed run's paid-call records only in its pre-pull backup · the figure ledger misreads "2,358.5GVA" and figure references (fixing re-bills every pass) · a block review cannot cite a market risk (4 Gridlock paragraphs open) · the spend guard is a size bound, not a provider billing cap · MS / GS automated access BLOCKED (upload only) |
| **Cost of this correction run** | **$7.33 measured** (provider-reported usage × list price; 7 paying runs, each counted once, pre-pull backups included). The spend guard's pre-call bounds summed $30.39 (an estimate); 44 paid calls, none over its bound |

### What changed

**P0 — Bank of America removed; seven publishers.**
- `[[retired]]` in `sources.toml`: no discovery, health check, upload request or new import. `ingest-file`, `ingest-inbox` and `article` refuse it — a page on its host or a subdomain included.
- History is untouched (articles, theses, runs, health records, candidates); a carried QUEUED BofA row becomes SOURCE_INACTIVE, never processed.
- Morgan Stanley / Goldman Sachs are **manual-first**: health-checked only, no discovery, research by upload. A week with nothing supplied reads MISSING, not absent.
- Every count derives from the seven configured channels.

**P0 — identity before ticker** (`securities.py`).
- A registrant is accepted only when the source's own description of the company (its quote and stated role) fits the issuer's SEC industry (SIC).
- A hint naming a non-SEC listing never resolves by a partial name.
- Point-in-time listing checks run after identity.
- Citi's "Delta" (a solid-oxide fuel-cell competitor) had resolved to Delta Air Lines. It is UNRESOLVED now: the company is Delta Electronics (TWSE 2308, a Ceres Power licensee), not SEC-registered.

**P0 — record kind** (`engine.record_kind`).
- A record is a market regime only when its evidence measures equity-market structure (correlation, dispersion, breadth, price volatility), on any node.
- Otherwise it is corrected to an investment thesis (`RECORD_KIND_CORRECTED`, with the reason) and its earnings transmission is tested.

**P1 — verification checks** (`verify.py`, `completeness.py`).
- A decline stated in words supplies the minus ("down ~27%").
- An ellipsis figure ("12 ... 30 or more") verifies piece by piece.
- A figure restated in a caption, table or summary is captured where the article states it. This needs all of:
  - the completeness pass names the claim;
  - the claim is verified;
  - the three words beside the figure share a content word, or the same precise number is written with the same unit.
- A shared number alone is never identity.

**P1 — spending limits** (`budget.py`).
- Limits: per run (scan $40 / batch $100), per document ($30 or `--max-cost`), and retries + completeness (85% of the document limit).
- Every call is bounded before it is sent and refused if it doesn't fit: checkpoint BUDGET_HELD, then resume without re-paying.
- Actual cost is recorded beside the bound (manifest `spend_guard`). The $30 preflight estimate is kept.

**P1 — publication dates.**
- Each article version keeps its own document's date and where it was read; cards show both when they differ.
- A report dated up to 30 days before its page is ordinary (`VERSION_DATES_DIFFER`). Anything else is `PUBLICATION_DATE_CONFLICT`, sent for review.
- A replayed upload keeps its original upload time.

**P1 — why completeness resends long documents.** Every part resends the whole article, because a gap's account may cite any block. `llm.py` + `PROMPT_CACHE_PARTS` can send it as a cached first block instead (the same text). It ships **OFF** — see below.

### Real runs (final code)

**Live seven-source health** on a copy of the weekly registry that carries BofA history:
- **2 healthy / 3 degraded / 2 blocked / 0 errors of 7**, measured twice.
- 0 requests to BofA's host; MS / GS not re-requested inside their back-off.
- A $0 scan: seven coverage rows; the 12 old BofA rows stay UNDATED (never requeued); no BofA on the dashboard.

**Citi PDFs, cached reruns** (extraction and completeness answers from cache):

| report | kinds | actions | open figures | open paragraphs | paid |
|---|---|---|---|---|---|
| Gridlock (60 pp), before | 14 thesis + 2 regime | 1 RESEARCH NOW · 5 WATCH · 10 SKIP | 17 of 851 | 4 of 292 | — |
| Gridlock, after | 16 thesis (same 16 ids) | 0 · 5 · 11 | **6 of 851** | 4 of 292 | $1.10 (reviews of changed cards) |
| LatAm (57 pp), after | 14 thesis (3 corrected) | 0 · 8 · 6 | 1 of 319 | 0 of 208 | $0.22 |
| ETF (34 pp + page), after | 1 thesis | SKIP | **1 of 232** (was 5) | 0 of 144 | $0 |

- **Reassessed under the corrected type:**
  - "Uneven US regional power-market regulation…" RESEARCH NOW → **SKIP**. The source shows no fundamental transmission step; the card says listed earnings are UNKNOWN — a hypothesis to test.
  - LatAm "Fiscal credibility and execution dispersion…" WATCH → SKIP.
  - J.P. Morgan's calm-index dispersion record: still a market regime, RESEARCH NOW.
- **Remaining open items, by materiality** (`e-verification/materiality-after.txt`):
  - none touches a RESEARCH NOW thesis;
  - Gridlock's open figures: five on one infographic page (the PDF's columns interleaved), all bearing on the transformer WATCH thesis; four of them ("80% over five years", "24–48 months", "12–30+ months", "~$400bn") are captured from the prose, and "top-10" is a label;
  - four paragraphs restating market risks the pass could not cite;
  - LatAm: a figure *reference*; ETF: a prior-year "$10 trillion".
- **Identity audit, 95 company mentions in 7 real registries:** 4 corrections — Delta, Siemens, Tencent, and CBRE's ticker. No previously correct match was lost.
- **Dates:**
  - LatAm: page 2026-09-14, report 2026-09-10 — both kept, `VERSION_DATES_DIFFER`;
  - ETF: page 2026-04-10, report 2026-04-08.

**Completeness resend — measured.** Gridlock's 22 parts sent 309,342–334,027 input tokens each: 7,130,969 in all, $35.65 of the pass's $39.44. Prompt-cache tokens: 0. The cache was tested on the ETF report, over the same cached extraction:

| run | completeness cost | open figures | open paragraphs | claims the pass added |
|---|---|---|---|---|
| original, uncached | $2.586 | 1 of 252 | 0 | 46 |
| control, uncached | $2.481 | 0 of 252 | 0 | 31 |
| article cached | **$1.418** | 2 of 252 | 0 | 26 |

The cached run is lowest on added claims, but inside the spread the two uncached runs already show. Neither equivalence nor harm is shown, so **it ships OFF; an operator decision**.

### GitHub state sync — the real private repository

Setup:
- temporary branch `theme-intelligence-state-test-20261011`;
- a SYNTHETIC registry (the labelled synthetic fixtures);
- the production branch checked absent before and after;
- credentials from gh's active login, through git's helper.

| step | result |
|---|---|
| 1 operator machine pushes | `4df9c5c`, fast-forward from nothing |
| 2 a fresh directory restores | 1 run · 1 article · 1 thesis |
| 3 it imports a manual document | UPGRADED, $0.51 |
| 4 it pushes | `3f98095`, fast-forward |
| 5 the stale operator imports its own, pushes | **REFUSED** ("the branch moved … run `state pull` first") → pull (backup, rebuild, replay from cache) → `11ba544` |
| 6 Actions-style runner: clone → `import-state` → $0 scan | ONE weekly report over 4 runs, both uploads in it ("original NOT on this machine"); health 2 / 3 / 2 of 7; QA 22/22 |
| 7 a raw rewind push | rejected by GitHub ("fetch first") |
| 8 second stale round (after the replay fix) | push refused → pull → the HTML edition of a report the branch holds as PDF goes to REVIEW (never counted twice), keeping its name and upload time → `2cf1f7e`; a second runner restores it, QA 22/22 |
| 9 privacy | 22 files, all JSONL; no PDF, HTML, article text, token, key or auth header; 0 text-carrying blocks |
| 10 history | thesis versions (v1 → v2, hashes and links), version dates, document records identical on both sides |
| 11 re-checked vs carried | same upload run: on the importing machine 11 of 12 claims re-checked against stored text; on the runner 0 of 12 — "NOT re-checkable here … never counted as re-verified" |

The test branch is left for review: `git push origin --delete theme-intelligence-state-test-20261011`.

### Screenshots

The seven-publisher dashboard — KPI strip and source health:

![dashboard](https://github.com/techmuns/mosaic-theory/blob/claude/theme-intelligence/docs/theme_intelligence/seven-sources-2026-10-11/screenshots/seven-source-dashboard.png?raw=true)

The Gridlock regulation card, now an investment thesis (SKIP):

![regulation](https://github.com/techmuns/mosaic-theory/blob/claude/theme-intelligence/docs/theme_intelligence/seven-sources-2026-10-11/screenshots/gridlock-regulation-card-investment-thesis.png?raw=true)

The fuel-cell card — "Delta" UNRESOLVED (was Delta Air Lines):

![delta](https://github.com/techmuns/mosaic-theory/blob/claude/theme-intelligence/docs/theme_intelligence/seven-sources-2026-10-11/screenshots/gridlock-fuel-cell-card-delta-unresolved.png?raw=true)

A LatAm card's sources table with both version dates:

![dates](https://github.com/techmuns/mosaic-theory/blob/claude/theme-intelligence/docs/theme_intelligence/seven-sources-2026-10-11/screenshots/latam-capex-card-version-dates.png?raw=true)

### Found by the real runs — fixed, pinned, mutation-checked

- **Wrong page named for upload.** A health action named Citi's LatAm page (whose report the scan reads itself) instead of the page that was partial (a 96-word teaser). It now names the partial page.
- **Empty persistent-failure line.** "[PERSISTENT_FAILURE] Citi: " printed with nothing after it; it now says what persists. Cut lists now say they are cut.
- **Contradictory KPI.** The KPI strip said "Blocked sources: none" beside a health block counting 2. It now reads "Blocked automatic channels", and each manual-first channel carries its access status.
- **Replay lost provenance.** A `state pull` replay recorded the private copy's hash as the upload's name and the replay time as its upload time; both now carry through.
- **Market-regime exemption too broad.** My first record-kind rule exempted the market-wide node; reviewing the LatAm cards showed that was wrong, and the exemption was removed.

### Tests, mutants, gate

- **New tests:**
  - `test_theme_intelligence_dates.py` (6);
  - `test_theme_intelligence_verification_quality.py` (28);
  - `test_theme_intelligence_prompt_cache.py` (8);
  - additions to the record-kind, source-health, state-sync, scan, seven-source and budget tests.
- **Mutants:** 66, all killed.
  - 19 over the round's earlier commits (16 at first; the 3 survivors were test gaps, then pinned);
  - dates 9; verification checks 18; record kind 3; health output 5; article cache 8; replay provenance 3; KPI 1.
- **Gate:**
  - ruff (vinci, tests, frontend) clean;
  - `mypy --strict vinci` clean, 183 files;
  - `pytest -m "not network"` at the merge commit `4770d248`: **4,820 passed, 511 skipped, 0 failed**.

### Completion — the brief, item by item

| brief item | disposition | note |
|---|---|---|
| P0 BofA 1–8 (config, discovery, health, queues, imports, dashboard, dependencies, tests / docs) | SHIPPED | live: 7 channels, 0 BofA requests; fresh install + migrated registry tested |
| P0 BofA historical preservation | SHIPPED | history untouched, never requeued (real migrated registry + test) |
| P0 identity 1–3, 5, 7, 8 | SHIPPED | SIC compatibility, UNRESOLVED otherwise, PIT after identity; 10 identity tests |
| P0 identity 4 (Delta Electronics) | SHIPPED | identified from the source context; not SEC-registered → UNRESOLVED |
| P0 identity 6 (audit Gridlock / LatAm) | SHIPPED | 95 mentions, 4 corrections; conservative misses listed |
| P0 classification 1–2, 7 | SHIPPED | 5 Citi records corrected; J.P. Morgan dispersion kept |
| P0 classification 3–5 (earnings transmission, explanation, opinion vs measured) | SHIPPED | the existing transmission analysis now applies; the cards label every line |
| P0 classification 6 (reassess Gridlock RN / Watch) | SHIPPED | RESEARCH NOW → SKIP (no fundamental step stated) |
| P0 other Citi cards, fragmentation | SHIPPED | LatAm 3 corrected; no merge needed, one overlap for a human |
| P1 verification 1–3, 6, 7 | SHIPPED | materiality report; Research Now first; targeted, cached |
| P1 verification 4 (deterministic fixes) | PARTIAL | three check defects fixed; ledger misreads not fixed — the fix re-bills every pass |
| P1 verification 5 (unsupported out of evidence) | SHIPPED | unchanged rule: unverified material is never linked |
| P1 cost 1–6, limits per document / batch / scan / retries | SHIPPED | bounded before every call; 44 real calls within bound |
| P1 cost — no absolute cap claimed; $30 preflight kept | SHIPPED | |
| P1 cost — completeness resend investigation | SHIPPED | measured per part |
| P1 cost — excerpt / caching optimisation | PARTIAL | built and measured (−45%); equivalence not shown → OFF |
| P1 cost — estimated vs measured reported apart | SHIPPED | |
| P1 GitHub state sync 1–9 | SHIPPED | real repository, temporary branch, synthetic registry |
| P1 publication dates | SHIPPED | both kept with provenance; conflict flagged |
| P2 operating model | SHIPPED | Citi fetch + budgets; J.P. Morgan / TrendForce automatic; Nomura request; SemiAnalysis PARTIAL + upgrade; MS / GS manual-first; BofA removed |
| P2 acceptance 1–15 | SHIPPED | see the next table |
| GitHub CI | PENDING | read after push |

| acceptance | evidence |
|---|---|
| 1 seven configs | `test_exactly_seven_active_channels_…`; `sources` on a fresh install |
| 2 no BofA requests / checks / queues / imports | live: 0 requests; refusal through every route (test) |
| 3 historical BofA auditable, not reactivated | migrated real registry; test |
| 4 Citi Delta | UNRESOLVED on the real card (screenshot) |
| 5 no false common-name matches | identity tests (10) + the 95-mention audit |
| 6 sector vs regime | 5 real corrections; J.P. Morgan kept; record-kind tests |
| 7 nine sections unchanged | the section-order QA check, 22/22 |
| 8 PDF verification resolved or reported | 17 → 6, 5 → 1, materiality listed |
| 9 spending caps | budget tests; real refusals simulated; 44 real calls within bound |
| 10 GitHub sync | the table above |
| 11 one ranked report, both routes | the runner's single weekly report |
| 12 SemiAnalysis / TrendForce and SemiAnalysis / J.P. Morgan relationships | `test_theme_intelligence_evidence_roles.py` (real frozen fixtures) |
| 13 Software Shock → three cards | `test_exactly_three_theses_with_the_expected_actions` (real frozen fixture) |
| 14 health with seven | live 2 / 3 / 2 of 7 |
| 15 fund logic untouched | this update touched only `vinci/theme_intelligence/`, tests, docs and `STATE.md`; the PR's other changes outside the package are the weekly workflow, its `bin/` script and the `pdfplumber` dependency — no fund module |

---

## Earlier updates (condensed; full text: `docs/theme_intelligence/pr-body-history/`)

- **Hybrid research ingestion** (`docs/records/2026-10-11-theme-intelligence-hybrid-ingestion.md`).
  - Claim-level contradiction.
  - Supplied PDF / HTML / Markdown / text through the same pipeline, identified before any model call.
  - A $30 cost hold, one registry, one weekly report.
- **Source health** (`docs/records/2026-10-11-theme-intelligence-source-health.md`). Every channel is checked cheaply and LLM-free, with history and alerts.
- **Review round 3** (`docs/records/2026-10-11-theme-intelligence-review-round-3.md`).
  - A challenge needs the same claim; the segment is part of identity.
  - Research verification is shown apart from execution.
- **Review round 2** (`docs/records/2026-10-10-theme-intelligence-review-corrections.md`). J.P. Morgan's Software Shock yields exactly three WATCH theses.
- **The original build** (`docs/records/2026-10-10-theme-intelligence.md`): the package, its registry, the nine-section cards, the weekly workflow (opt-in cron, state branch).

🤖 Generated with [Claude Code](https://claude.com/claude-code)

