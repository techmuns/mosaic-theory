---
id:
status: shipped
date: 2026-10-10
prs: [703]
supersedes:
superseded-by:
---

# Theme intelligence — a research-only scanner of eight publisher channels that keeps a versioned registry of theses and writes nine-section Living Thesis Cards and a weekly decision page

**WHAT.** A new, isolated package `vinci/theme_intelligence/` (its own SQLite registry under
`data/theme_intelligence/`; no fund module imports it, AST-pinned; it imports only `vinci.config`,
the existing LLM client and the HTTP cache). Pipeline: discover (eight adapters, editable
`config/sources.toml`) → fetch (honest User-Agent, robots per RFC 9309, fail closed) → parse
(JSON-LD / meta / byline; FULL / PARTIAL / BLOCKED) → extract (LLM pass 1, prompt `ti-extract-5`,
cached by content) → verify (deterministic: verbatim span, figure-in-quote incl. scale and number
words, unit, chart hedges forced approximate, forecasts never actual, as-of in the source note,
look-ahead blocked, stale series labelled, unnamed entities and unsupported recommendations
dropped) → resolve (SEC company / fund maps, foreign private issuers never ADR-substituted) →
engine (identity key = value-chain node × mechanism × direction × geography; same economics →
version, same origin → attribution, opposite direction on one node → COMPETING, different
mechanism or child economics → SIBLING, parent / child never merged, `other` → REVIEW_NEEDED;
append-only versions with field diffs and change classes) → deterministic priority (RESEARCH NOW /
WATCH / SKIP + evidence direction; readiness and valuation NOT_ASSESSED) → LLM pass-2 review
(`ti-review-3`; a withheld DECISION-BEARING sentence holds promotion, a withheld narrative one is
withheld and logged) → cards (web / print / Markdown / JSON) and the weekly dashboard (six
always-printed categories, "showing X of Y", searchable archive). CLI: `scan`, `article`,
`report`, `qa`, `backup`, `export-state`, `import-state`. Scheduling: an opt-in Actions workflow
(Monday 03:00 UTC = 08:30 Asia/Kolkata, runs only when `THEME_INTELLIGENCE_SCHEDULE_ENABLED` is
`true`; `workflow_dispatch` always) whose durable state is a JSONL export on the
`theme-intelligence-state` branch, and a local wrapper `bin/theme-intelligence-weekly`.

**WHY.** The brief (`CLAUDE_CODE_THEME_INTELLIGENCE_BUILD_BRIEF.md`, 2026-10-09) asks for a reusable
discovery-and-prioritisation tool whose "RESEARCH NOW" means analyst attention, never a buy, kept off
the fund's screen / ranker / dossier / verdict / scoring / freeze / ledger / portfolio and not
dependent on the unmerged #695. Its acceptance test is the J.P. Morgan "Software Shock: AI's Broken
Logic" article as of 2026-02-09: exactly three theses.

**HOW VERIFIED.**
- *Acceptance, real URL.* The page was retrieved FULL (42 blocks, 1,146 body words, JSON-LD author
  Kriti Gupta, published 2026-02-09 10:30 +05:30). Prompt `ti-extract-4` produced TWO theses — the
  model folded the software recovery into the AI-infrastructure dislocation. A general decomposition
  rule (one hypothesis per value-chain node × mechanism × direction the article draws an
  implication for; a conditional "if …, … may be an entry point" view counts) took `ti-extract-5` to
  three. Its first run then showed AI infrastructure at WATCH, held because the review withheld
  three NARRATIVE sentences citing the wrong claim; the brief says to hold promotion when MATERIAL
  claims lack evidence, so the hold was narrowed to decision-bearing sentences (bottom line,
  what-changed, decision, dislocation lines). Definitive run `R-20261010T121233Z-article`: AI
  infrastructure RESEARCH NOW (META, AMZN, GOOGL, MSFT named as capex spenders, no chipmaker added,
  readiness NOT_ASSESSED), software WATCH (RSI 18, IGV over 20% below its 200-day, ~8x EV/sales near
  November 2022; conditional premise; IGV a FUND, Anthropic PRIVATE, no company named), AI adoption
  WATCH (145-member basket; NTM margins 16.4 / 14.5 / 13.0% forecast, approximate, chart-read,
  data as of 2026-02-02 per 22V / FactSet; "association, not causation" in its unknowns); the
  99th-percentile correlation stays a market RISK. QA 12/12.
- *A → B on preserved state.* The registry was exported to JSONL, re-imported into a fresh database
  (the scheduler's durable path) and a labelled HYPOTHETICAL article B applied: same thesis id,
  version 2, contribution NEW (independent origin), evidence STRONGER, RESEARCH NOW kept, v1's
  content hash unchanged. The FIRST two attempts demoted it to WATCH — the card's own
  "Update (2026-02-20, <publisher>):" prefix was number-checked as if the sentence asserted 2026 /
  02 / 20 (then mis-stripped when the publisher name held parentheses). Update metadata now sits in
  the ⟨…⟩ system-label brackets the number check ignores; pinned with a publisher name carrying
  parentheses and digits.
- *Live scans, all eight channels.* `scan --days 10 --max-articles 3` (`R-20261010T114919Z-scan`)
  and then the real weekly wrapper (`R-20261010T120521Z-scan`), which drained the three QUEUED
  articles first, recognised the two TrendForce pieces as already known, recorded the SemiAnalysis
  paid post PARTIAL, and passed QA 13/13. Real data exposed and fixed: a TrendForce `TechArticle` /
  Organization author the parser ignored; "650 million units" vs 650e6 and "2027-2028" read as
  -2028; "Two more hikes", "seven" and "around –10%" (typographic minus) failing the figure check —
  replayed cache-only, the weekly run's two false failures and its spurious hold are gone; QUEUED
  candidates re-marked IN_WINDOW by the next discovery; the same company named by two articles
  listed twice; `report --run` on an old run rendering later versions; two runs in one second
  sharing a run id.
- *Tests.* 78 offline test items in seven `tests/test_theme_intelligence_*.py` files (13 of them
  the append-only check parametrised over each history table): acceptance (authentic excerpt +
  frozen extraction + authentic SEC rows — no hand-written card), every §8 overlap case on clearly
  labelled hypothetical fixtures, store durability, parse / verify, discovery / scan / resume /
  dashboard, isolation, workflow; plus `extract.py` and `verify.py` added to
  `test_theme_thesis.py`'s LLM-schema pin. 25 mutants of the guards, every one killed.

**BOUNDARY.** Acceptance: one article (`A-332d3da6f3ac`), as-of 2026-02-09, 22 claims extracted /
22 span-verified, 15 named entities, model `claude-opus-4-8`, prompts `ti-extract-5` /
`ti-review-3`, measured 2026-10-10. Scans: window 2026-10-01 → 2026-10-10, as-of 2026-10-10, the
eight configured channels as reachable on 2026-10-10 with the honest User-Agent; "discovered" =
unique canonical URLs a channel's listing / feed / page data exposed that day; "in window" = those
whose source-stated date falls inside it. Costs at list price ($5 / $25 per M input / output
tokens): first live JPM run $0.53 (extraction + three reviews), first scan $0.84 (3 articles),
weekly run $0.81 (3 articles), A → B $0.05; cache hits cost 0 and are reported separately.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- Morgan Stanley (connection dropped, robots unreachable → fail closed) and Goldman Sachs (HTTP 403)
  refuse the honest User-Agent: reported BLOCKED every run, never bypassed. Falsifier: either
  answers — the coverage row says "expected BLOCKED but reachable — update the config".
- BofA insight pages state no publication date: counted UNDATED, never placed in a window; use
  `article --url`. Falsifier: BofA adds dates and its candidates start landing IN_WINDOW.
- The pass-2 review is an LLM; its BLOCKs on narrative lines are frequent (6 on the acceptance
  cards) and withheld, not hidden. A decision-bearing BLOCK holds promotion, so a review mistake can
  only DEMOTE (never promote). Falsifier: a thesis held by a review the source plainly supports.
- The SEC ticker map is current, not point-in-time, and does not state a ticker's security type
  (Alphabet lists GOOGM / GOOGN beside GOOG / GOOGL); every resolution says so.
- Scheduling is NOT claimed operational on Actions: a `workflow_dispatch` workflow can only be run
  once it is on the default branch, so the first Actions run, and the state branch it creates,
  happen after merge. The local wrapper's run is the verified scheduled-equivalent run.

## Amendments

- **2026-10-10 — review of PR #703, corrected on the same PR:**
  `docs/records/2026-10-10-theme-intelligence-review-corrections.md`. Claims above that no longer
  hold: (1) AI infrastructure's RESEARCH NOW — under the corrected evidence typing its only
  offered dislocation is the article's rhetorical question (a SOURCE OPINION), so it is WATCH;
  the three theses and their other actions stand. (2) "The SEC ticker map is current, not
  point-in-time" — listings are now read from the as-of cover page; GOOGM / GOOGN were not
  registered on 2026-02-09 and never enter the record as stock. (3) The decision trace quoted in
  the PR ("Alphabet (GOOG/GOOGL/GOOGM/GOOGN)") was the defect the review named. (4) The weekly
  run's records above were produced by `ti-extract-5`; the sample was reprocessed from scratch.
