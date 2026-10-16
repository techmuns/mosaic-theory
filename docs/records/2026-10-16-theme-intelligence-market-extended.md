---
id: 2026-10-16-theme-intelligence-market-extended
status: recorded
date: 2026-10-16
prs: []
supersedes:
superseded-by:
---

# Theme intelligence — "Is it priced?" for sector-only theses, consensus revisions as of the date, a split-sized-move check, and the weekly run

**WHAT.** The operator, on 2026-10-16, asked to "do these reliably" for the decisions left by #731.
Built, all display only (no research-action rule reads any of it):

1. **The companies the thesis implies are priced.**
   - These are the latest enrichment set's SEC-verified US listings, put in their OWN table labelled
     "EXTERNAL HYPOTHESIS, not named by the source; never counted".
   - An unverified listing or a foreign filer is not priced.
   - The P/E reads each company's CIK from the SEC's ticker map.
2. **Consensus revisions, point in time.** The source is the fund's committed dossiers
   (`data/dossiers/<TICKER>/dossier.json`, the derived layer of its CIQ Estimates export). For each
   company it shows:
   - how the next fiscal year's EPS consensus moved over 3 months (normalized EPS, else GAAP);
   - how many analysts revised it up and down.
   It is shown only when **both** hold; otherwise "not held", with which rule failed:
   - **the export certainly existed by the date** — on or after its floor, AND the dossier was
     assembled by then;
   - **the export is at most 31 days old.**
3. **A value check beside the count checks.** Any one-day move at least the size of a 3-for-2
   split (+50% or −33%) puts a visible warning on its row: real news, or a split the price source
   did not adjust.
4. **The weekly run prices.** A "Market context" step after QA runs in the Actions workflow (its
   `POLYGON_API_KEY` and `SEC_USER_AGENT` secrets already exist) and in
   `bin/theme-intelligence-weekly`. A failure is said and never blocks committing the scan. The
   contexts travel through the state-branch JSONL export; the round trip is pinned.

**WHY — and a correction.**
- I told the operator CIQ consensus "can't be read as of a past date". That was wrong in part.
  The Trends sheet keeps vintages 0, 1, 2, 3, 6, 9, 12 and 18 months back from the export.
- But every committed dossier dates its export only as a floor ("≥", 26 of 26, 2026-10-16). So
  mapping a vintage to an exact past day is approximate.
- The rule above therefore reads only the export's own present, and only when the thesis date
  certainly follows it.

**HOW VERIFIED.**
- **Real run: the pilot copy, as of 2026-10-14** (live Polygon and SEC, committed dossiers, $0).
  - All 13 active theses get a context; 50 implied-company rows are priced.
  - Revisions are held on 5 rows. Example: LLY FY 2027 normalized EPS 44.46 → 47.34 (+6.5%), 26
    analysts up, 0 down, of 29 (export on or after 2026-09-17; dossier assembled 2026-09-30).
  - 5 rows carry a split-sized warning.
- **Testing the anomaly before trusting it:** Moderna +177% on 2026-08-19 (62.96 → 174.38). The SEC
  cannot confirm a split yet: the last share count, 399,235,889, is dated 2026-07-24, before the
  move. The flag says so instead of guessing.
- **Tests:** 9 new ones (23 in `tests/test_theme_intelligence_market_context.py`).
  - Revisions on a FROZEN copy of AMZN's dossier consensus
    (`tests/fixtures/theme_intelligence/market/AMZN/`): the value and counts, look-ahead twice
    (before the floor; after the floor but before assembly), stale, no dossier, a negative base.
  - The split flag, including a jump after the date.
  - Implied companies end to end: own table on desk and Markdown, count and action unchanged,
    unverified and foreign filers skipped.
  - The export round trip; the rendered warning and counts.
  - 19 mutants, all killed; 2 first-pass survivors (display gaps) closed.
- **Full gate:** ruff clean, `mypy --strict vinci` clean, `pytest -m "not network"` 5734 passed, 515 skipped.

**BOUNDARY.**
- Pilot copy: md5 5fcc240d4b087d2feb1f81e6d6fabc3c, 13 ACTIVE theses, priced as of 2026-10-14 with
  this branch's code.
- Dossier dates: the 26 committed dossiers at this branch's base, 2026-10-16.
- Tiingo limits: read from tiingo.com/about/pricing, 2026-10-16.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$0, but more Polygon requests.** Each implied company is a request, about 4 a minute: on the
  pilot about 50 rows, so roughly 15 minutes when nothing is cached. The weekly job's limit is 120
  minutes.
- **Revisions cover only the fund's dossier names** (26 committed). Most implied companies read
  "no CIQ consensus held".
- **The split flag will fire on real news**, as on biotech trial readouts. It asks for a check; it
  removes nothing.
- **Tiingo deep history (P/E against five years) waits for `TIINGO_API_KEY`.** The free plan:
  50 requests an hour, 1,000 a day, 500 tickers a month, 30+ years of history. So deep history is
  to be fetched once per ticker and cached, with Polygon still serving the recent two years.
