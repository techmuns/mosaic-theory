# mosaic — Loop 1 (paper-mode validation engine)

The **first production slice of a real, AI-native, long-only US equity research system** — the fund's
actual engine, thin in *scope* (one screen, thin ingestion) but production-grade in *quality*. It runs
in **paper mode**: it records and scores its own decisions against live market data and **deploys no
capital**. Going live with real money is **gated** on this phase validating that the depth
discriminator's verdicts carry information.

The design specs live in [`docs/`](docs/) (`LOOP1_BUILD_PLAN`, `MINIMAL_LOOP`, `INGESTION_LAYER`,
`FUNNEL_SCREENS`, `EDGE_THESIS`, `OBJECTIVE_FUNCTION`, `GRAPH_LOOP`, `data_sources`).

## What this is (and is not)

It is a **falsification experiment**, not an MVP. Its one job is to produce honest evidence on a single
question — **does the manual depth discriminator's BUY/AVOID verdict carry information?** — measured as
the **BUY−AVOID forward-return spread**. The screen finds the *setup*; the human runs the *discriminator*
(the A/B/C source-binding + CIQ process); this code is the **plumbing and the decision ledger around
that judgment** — never the judgment itself.

## ⛔ Pre-registered kill criteria (fixed BEFORE any live verdict is logged)

Set firmly in advance so results can't be rationalised post-hoc (the Goodhart fence applied to the
experiment itself). With a tiny sample these are **directional gates, not significance tests** — we seek
*the absence of a clear negative + a plausible positive + sound sourced reasoning, sustained.*

- **Continue if:** the BUY−AVOID spread is **clearly positive over ≥2 quarters of *resolved* verdicts**,
  **and** the reasoning audit shows genuine twin-engagement (the discriminator actually ruled out
  "terminal decline" with sourced evidence, not rationalised), **and** the loop is operable.
- **Kill / rethink if:** the spread is **≈0 or negative** (the discriminator adds no information),
  **or** all return is explained by **beta** (no selection skill), **or** the loop can't be operated
  reliably.

These will not be edited in response to results. Tuning the screen or the metrics on forward returns is
**forbidden** — it contaminates the validation. The screen is tuned by **face-validity only**.

## Go-live gates (before any real capital — out of this code's scope, recorded here)

- **Polygon data licence.** The free tier is personal/eval use; a **commercial data licence is required
  before LP capital runs on this feed.**
- Regulatory/counsel track (HK SFC Type 9, etc.) per the planning docs — not a code concern.

## Build status

| Step | Component | State |
|---|---|---|
| 0 | Scaffold + schemas-as-code (envelope, data-record, candidate-record, ledger) | ✅ done |
| 1 | US entity resolver (CIK↔ticker↔name, fail-loud) | ✅ done |
| 2 | SQLite store + durable JSONL snapshots | ✅ done |
| 3 | EOD client (Polygon Grouped Daily) + Screen-2 price features | ✅ done |
| 4 | EDGAR client (XBRL fundamentals + 8-K full-text + filings) | ✅ done |
| 5 | Screen 2 (overshot de-rating) as PASS/FAIL/UNKNOWN gates | ✅ done |
| 6 | Decision ledger + entry workflow (BUY **and** AVOID) | ✅ done |
| 7 | Scoring harness (BUY−AVOID spread, hit-rate, α/β, twin-realisation) | ✅ done |
| 8 | Scheduled automation (GitHub Actions cron) | ✅ done |
| — | Graph track Test 0 (1-hop graph quality) | ⏳ next (parallel; needs `ANTHROPIC_API_KEY`) |

**Loop 1 build order complete.** The pipeline runs end-to-end on real data: a weekly screen surfaces
candidates → the manual discriminator logs BUY/AVOID verdicts (entry price frozen) → monthly scoring
computes the BUY−AVOID spread. It now needs **time**: the PM logs forward verdicts; verdicts resolve at
their horizons; the spread accumulates. Remaining build work is the **graph track (Test 0)** — offline,
parallel, validating the moat — plus the cap-band universe builder (the current universe is a thin seed).

## Data sources (US-only, free/cheap)

- **SEC EDGAR** — XBRL `companyfacts` fundamentals, 8-K full-text search (de-rating trigger), submissions
  (SIC sector, recent filings). Free, authoritative, no credential.
- **Polygon.io Grouped Daily** — whole-US-market EOD OHLCV in one call/day (the primary price feed;
  *Stooq, the docs' original free feed, is now JS bot-walled and unusable from a headless job*).
- **Claude Sonnet 4.6** — graph-track relationship extraction (Test 0) only; the core loop uses no LLM.

Every datum carries a `(value, as_of, source, coverage_status)` envelope, so missing data is an
explicit **UNKNOWN → defer**, never a silent zero. Source-reliability tiers: EDGAR > IBKR > EOD > news.

## Setup

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

Credentials (environment variables; also set as GitHub Actions secrets for automation):

```bash
export POLYGON_API_KEY=...      # step 3 (EOD)
export ANTHROPIC_API_KEY=...    # graph track (LLM extraction)
export SEC_USER_AGENT="you you@example.com"   # optional; SEC fair-access contact
```

## Run

```bash
# Run from the repo root (python -m is the robust entrypoint).
.venv/bin/python -m mosaic resolve AAPL GOOGL BRK.B --enrich   # entity resolver demo

.venv/bin/pytest -q                   # full suite
.venv/bin/pytest -q -m "not network"  # offline only (skip live SEC/Polygon tests)
.venv/bin/ruff check mosaic tests && .venv/bin/mypy mosaic     # lint + types
```

## Layout

```
mosaic/
  config.py     universe definition (exchange filter, cap band), paths, API pacing
  schemas/      the data contracts (envelope, data-record A, candidate-record B, ledger)
  resolver/     US entity resolver — the join key (built first, hardened hardest)
  store/        SQLite working store + durable JSONL snapshots
  edgar/        XBRL fundamentals, 8-K full-text search, recent filings
  eod/          (step 3) Polygon EOD client + Screen-2 price features
  screens/      (step 5) Screen 2 gates -> candidate-records
  ledger/       (step 6) decision ledger + entry CLI
  scoring/      (step 7) BUY-AVOID spread, hit-rate, alpha/beta, twin-realisation
  graph/        graph track — 1-hop dependency graph + Test 0 quality harness
data/snapshots/ durable, committed JSONL provenance (the working .db is rebuildable, not committed)
```

## Disciplines (non-negotiable)

- **Validate, never optimise on forward returns.** Gates and metrics are set by face-validity and known
  historical cases. No P&L tuning, ever.
- **Forward, not backtested.** The LLM-aided discriminator has hindsight on known names, so only forward
  paper verdicts are clean evidence.
- **Log AVOIDs as well as BUYs** — they are half the validation set (the BUY−AVOID spread needs both).
- **Fail loud over guess** — ambiguous entity resolution, partial data refreshes, and throttled searches
  raise; they never silently degrade.
