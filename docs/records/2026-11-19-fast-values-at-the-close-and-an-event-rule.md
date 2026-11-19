---
id:
status: shipped
date: 2026-11-19
prs: [1132]
supersedes:
superseded-by:
---

# The page's market cap, its TEV, the EV gap's market side and the name's cross-sectional multiples are struck at the page's own close, with CIQ's cap and TEV kept beside them as dated cross-checks. A CIQ export is refused when the company files a 10-Q, a 10-K or an 8-K item 2.02 after it, in place of the 45-day clock. In code, rendered on both twins; no committed page carries the values until a $0 refresh ($0, code only)

**THE RULINGS.** The operator, 2026-11-19, relayed verbatim by coordinator B:
- On B's question "Start with a $0 preview of market cap and TEV from the daily price, plus an
  event rule?": *"Yes, start there"*.
- On the preview, asked as "Approve W70's preview (schemas.py included), with the values landing
  by a $0 refresh?": *"Approve, $0 refresh"*.
  - Before asking, B told the operator what that covers: the protected `vinci/dossier/schemas.py`
    edit (new fields only, no Synthesis or verdict field); an unreadable EDGAR feed refusing the
    build; the panel's data date being used rather than CIQ's export stamp; and the Snapshot, TEV
    and EV-gap render lines going in now that #1129 had merged.
- **The row-53 panel check is not run, by the operator's acceptance of B's recommendation.** B
  recommended SKIPPING it, on the grounds that this changes the facts the synthesis reads, not its
  instructions, and said *"Say so if you want it run"*. The operator did not ask for it. Those are
  B's words, not the operator's.

**THE AUDIT** (coordinator B, read-only, main `e6a6c318`, the 26 committed pages):
- Every page's `stock_info.market_cap` was CIQ's comps "Market Capitalization Latest", from an
  export downloaded by hand weeks apart.
- A 45-day clock on that export (`freshness.MAX_PANEL_AGE_DAYS`, operator 2026-07-29) refused
  builds. On 26 of 26 pages the panel it measured was the CIQ comps snapshot.
- So a sourcing choice had become a recurring re-export chore and a source of refused builds. At
  2026-11-19 the clock refused FUBO (100 days), PARR (64), BRBR (59), BURL, ROST and TGT (55). Yet
  VRRM passed at 13 days while its Snapshot read "cap $333M (2026-11-06) ⚠ implies $2.19/sh vs
  CMP (+31.9%)" beside a $1.66 close.
- Expert practice is the reverse: fast values come from the daily feed, and a vendor export
  supplies slow data, is refreshed on EVENTS, and is dated wherever it is shown.

**WHAT.**
- **The construction** (`vinci/dossier/price_values.py`, pure functions of the page):
  - The page's market cap is its close (`stock_info.price` at `stock_info.as_of`) × its
    point-in-time share count (`stock_info.shares_out`, the count `valuation_basis` and the anchor
    read) → `stock_info.market_cap_at_close`.
  - The TEV at the close is that cap + CIQ's claims, i.e. CIQ's comps TEV less its comps cap, the
    name row's net debt → `implied_expectations.tev_at_close` and `tev_close_date`. It is
    `valuation_basis.value_at_page_price`'s construction.
  - No close, count or claims leaves the value UNKNOWN, naming what is absent. CIQ's figure is
    never put in its place and claims are never taken as zero.
- **CIQ's own figures stay as DATED cross-checks.**
  - `stock_info.market_cap` keeps its `market_cap_as_of`, and `implied_expectations.tev` keeps its
    `tev_as_of`.
  - `stock_info.cap_cross_check` holds the existing reconciliation (`freshness.reconcile_cap`),
    still read on CIQ's cap against close × count, so the page's cap is never set against itself.
  - A gap beyond 2% is a QA flag, `cap-cross-check:`, naming both dates.
  - A whole-number ratio is still refused, unchanged.
- **Moved onto the values:**
  - the EV gap's market side (`refresh.ev_gap_transform`; `ev_gap.vintages.tev_close_date`
    beside `tev_as_of`);
  - the price-implied PEER rows. The name's own forward-multiple (†) rows and the G5 probe keep
    CIQ's TEV, the one that multiple was struck at;
  - the name's side of `ciq_sheets.cross_sectional_valuation`: EV/EBITDA scaled by TEV-at-close ÷
    CIQ's TEV, P/E by the close ÷ CIQ's printed close, with CIQ's figure and the peers' date
    beside it. The `source_ref` is byte-identical, since the synthesis copies it verbatim.
- **One builder for both write paths:** `mechanical.with_price_values` (assembly, after
  `stock_info`, before the synthesis) and `refresh.price_values_transform` (the $0 refresh seam).
  `recompute_derived` re-derives the values where a page carries them and adds nothing to a page
  built before them.
- **The new fields are ABSENT, never null, until built.** So a page built before them, and its
  synthesis request, are byte-identical: the `covenant_exhibit_outcomes` lesson of 2026-11-16,
  which `test_capture_at_a_ref_runs_that_refs_code_and_matches_in_process` would otherwise catch.
- **The event rule** (`freshness.event_verdict`, read through `mechanical.read_filing_events`):
  - An EXPORT panel is stale when the company filed a 10-Q, a 10-K or an 8-K item 2.02 strictly
    AFTER the panel's date and on or before the build: `_panel_freshness_flag`'s own `panel <
    print`, widened to the periodic forms.
  - `check_freshness` refuses it, naming the panel and the first such filing.
  - A filing list that cannot be read refuses.
  - The page's own close (`stock_info.as_of`) is exempt by name: it is not an export.
  - Unchanged: the missing-input refusal, the share-basis refusal, consensus never gating, the
    price-staleness rules.
  - `MAX_PANEL_AGE_DAYS` now feeds only the consensus caveat.
  - The $0 precheck reads the same filings through one seam (`prespend.filing_events`) and prints
    the event reading in place of a due date.
- **The render** (both twins, `render.py` and `dossier.js`):
  - the Snapshot prints the page's cap, and CIQ's figure, date and gap only beyond the tolerance
    (the share-basis wording on a whole-number ratio);
  - the price-implied levels name the TEV at the close and CIQ's own TEV the † rows divide, and
    the table cites the TEV at the close;
  - the EV gap states its TEV's two dates.
  - A page built before the fields renders exactly as before.
- **A new extraction vintage:** `2026-11-19.fast-values-at-the-close-and-an-event-rule`.

**THE FENCE (2026-11-13, "Keep it off") is not crossed.** The EV gap divides the scenario record's
base leg (`refresh._base_leg`), never the R1 anchor. It already differenced against CIQ's TEV; it
now differences against the TEV at the close. R1's anchor, `anchor_split` and `propose` are
untouched, and `test_screening_context_never_differences_the_anchor_against_spot` is green and
unedited.

**WHY.**
- The 45-day clock measured how long ago a file was downloaded. A panel is out of date when the
  company has reported since, and refusing on a date refused BURL and ROST, whose exports nothing
  had outdated.
- A cap struck on a weeks-old price is a value on the wrong date, which no staleness rule sees:
  VRRM's 31.9% passed both.
- **DOES THIS SELECT ON FORM?** No. Each value is arithmetic on the page's own close, count and
  CIQ's claims, and the rule reads filing events. No threshold was set on outcomes: the 2%
  tolerance and the 45-day consensus caveat are the existing constants.

**HOW VERIFIED.**
- **Measured** at a 2026-11-19 build on the 26 committed pages at main `e6a6c318`: the head code
  (`price_values_transform` → `ev_gap_transform`, its consensus vintage carried as stored →
  `recompute_derived`) applied to the committed JSON.
  - **Control:** the branch's code reproduces 26 of 26 `dossier.md` and `dossier.json` byte for
    byte. Re-run on `ff8ecfc8` (#1129 moved no `dossier.json`), it holds on 26 of 26.
  - **Every page gains the new fields:** 26 of 26.
  - **The cross-sectional read is restated on 24 of 26**, and its numbers move on 15. GOOGL's
    export on disk fails the control (main's `cross_sectional_valuation` does not rebuild its
    committed string), and PARR's quarterly export is mislabelled (row 28): both are left as
    stored.
  - **The peer implied levels move by more than 0.5% on 19**: PARR −7.5%, TJX −7.0%, LLY +6.9%,
    VRRM −6.4%, NFLX +6.0%.
  - **The EV gap moves at 3 dp on 4 of the 6 computed:** BRBR 1.182→1.145, EPAM 0.821→0.802,
    NCNO 0.694→0.709, SMPL 1.536→1.520.
  - **The cap cross-check flags 15**; a corporate action fires on 0.
  - **Named cases:**
    - VRRM: $252.3M at the 2026-11-17 close vs CIQ's $332.9M (+31.9%).
    - MCK: +1.0% on one date, not flagged — the noise floor of the two share counts.
    - PARR: +10.0%.
    - FUBO given EDGAR's pre-split 342.4M: ratio 12.0, refused as a share basis.
  - **Freshness at 2026-11-19:**
    - The clock refuses BRBR, BURL, FUBO, PARR, ROST and TGT; the event rule refuses BRBR, FUBO,
      ORKA, PARR, TGT and TJX, each naming its filing.
    - ORKA (10-Q 2026-11-09) and TJX (8-K 2.02 2026-11-18) are newly refused. BURL and ROST are
      newly passed: nothing has been filed since their 2026-09-25 panels.
    - All 26 pass at their own build date.
    - On the 13 pages whose comps export date is recorded, 0 filings fall between the panel's
      data date and its export stamp.
  - **A $0 refresh would be refused on 0 pages** by the cited-figure guards.
- **Tests:**
  - `tests/test_price_values.py` (8), `tests/test_event_rule.py` (16) and
    `tests/test_price_values_render.py` (7). Each guard is pinned positive and negative on real
    pages (the frozen cut `cut-4889ddba`, and VRRM's 2026-11-18 copy, the rebuilt page) and on the
    real filings frozen in `tests/fixtures/event_rule_filings.json`.
    - Those filings are public EDGAR metadata, read 2026-11-19 through `read_filing_events`.
    - No test sends a request: the precheck's one seam is stubbed, and no cache appears.
  - **Rewritten pins** of the behaviour replaced: `test_freshness`, `test_staleness_split`,
    `test_prespend`, `test_consensus_parity`, `test_ev_gap_transform_idempotent` (as its docstring
    asks of a deliberate basis change) and `test_capital_structure_vintage`'s docstring.
- **Fail-first:**
  - On main's `vinci/`, the two new data test files cannot import, and 3 parity, 3 staleness-split
    and 7 freshness tests fail.
  - On the committed renderers, 5 of the 7 render pins fail; the 2 negative pins pass on both.
- **The web**, served from a scratch frontend: the moved lines are main body, collapsed and
  force-open, with 0 console errors on the final load.

**BOUNDARY.** Every count is over the 26 committed pages (`data/dossiers/*/dossier.json`, every
page on `data/coverage_roster.jsonl`) at main `e6a6c318`, measured 2026-11-19, unless it names
`ff8ecfc8`. "Moves" compares the committed JSON with the head transform's output on it. The
filings are every 10-Q, 10-K and 8-K item 2.02 each filer made 2026-08-01..2026-11-19 (EDGAR
submissions, read 2026-11-19). An export date is "recorded" where `inputs.ciq[comps].export_date`
is present.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The synthesis request changes** on every page that carries the values: their facts, never the
  instructions. The row-53 check is not run (above).
- **VRRM's committed prose quotes CIQ's snapshot figures** (3.6x, 9.1x, $333M). They stay on the
  page as dated CIQ figures beside the at-close ones until the page is re-assembled.
- **An unreadable EDGAR feed now refuses a build** where the clock needed no network.
- **The rule compares the panel's data date**, conservative by at most the routine 1–4 day gap to
  the export stamp.
- **No committed page carries the values yet.** They land by a separate $0 refresh (active pages,
  BRBR excluded), STATE row 10.
