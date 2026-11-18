---
id:
status: open
date: 2026-11-18
prs: []
supersedes:
superseded-by:
---

# W62 (+ W63): the R1 screening anchor withholds a value struck on a multiple that is not today's by its band's own cadence; `applicable`, the recipe and the tier untouched; never re-struck at the page's close, never the median; W61's split notice now states that verdict; GOOGL's $144,827M is no EBITDA; IN CODE, no committed page re-rendered; preview APPROVED by the operator 2026-11-18 ("Approve, add the row") ($0)

**WHAT.**
- **The problem.** W50 (#1114) made the page's R1 screening anchor price its band's CURRENT multiple, the band's latest close. That close can sit weeks before the page's price date (GOOGL's CIQ close 2026-09-30 against its page's 2026-11-11, 42 days; TJX's ex-lease close 2026-08-28, 75 days). W61 (#1118) printed a notice past 30 days; the anchor still priced on it.
- **The rule: by each band's cadence, read from the code that builds it** (`anchor.close_age`):
  - CIQ's history (`ciq_sheets._own_history_band` over the Multiples sheet's TEV/LTM EBITDA Close): calendar-quarter columns plus a partial column at the export date wherever CIQ writes one (6 of the 7 CIQ-history pages do; GOOGL's 2026-11-02 file does not, its 2026-09-22 file did). Stale past `STALE_CLOSE_DAYS`, 30 days before the page's price date. A re-export clears it.
  - The ex-lease history (`lease_basis.observations`): one observation per fiscal quarter, at Historical Capitalization's pricing date. Stale only once the page's price date is past the date its NEXT observation could be priced: the last balance-sheet date + the longest of its last four quarters + the slowest of their pricing lags (the window holds a 10-K's). Read over EVERY observation the export carries, priced or not. Before that date no export could hold a newer observation, so a refusal would be false by construction.
  - An undated close or page refuses. A page with no stored close is measured at its reference date, the date its inputs are cut at.
- **A value's refusal, not the recipe's** (coordinator, 2026-11-18): no screen value and no split. The dated multiple stays on show with the median beside it, never priced in its place. A `multiple_stale` data-quality flag, one detail line and the reason; `applicable`, the recipe tag and the tier untouched. The mid-cycle sentence says R1 WOULD price the median wherever the value is withheld (stale, or no usable current: W50's case too). The md ex-lease sentence says R1 prices no value on a stale history.
- **The "not priced" row** (the operator's addition at approval). On a page whose value is withheld as stale, the main table keeps a "Screen value / share" row. Its value cell reads "not priced", and its note names the cause and what clears it, in dates and days only, never the stock's quote or a difference from it. The note is written once in anchor.py (`Anchor.value_withheld`, absent where unset) and printed verbatim by both renderers. GOOGL's reads: "the multiple is the 2026-09-30 close, 42 days before the page's close; a fresh CIQ export clears it". An ex-lease note names its next observation's due date. The note is set only where R1 can price and staleness alone withholds the value.
- **THIS CHANGES W61'S APPROVED DISPLAY.** The split's "Stale multiple" notice and the last line of its arithmetic ran on a flat 30-day clock. They now state the ANCHOR's cadence verdict (coordinator, 2026-11-18: "the split's stale notice follows the anchor's cadence verdict"). A notice calling TJX's multiple stale while the anchor prices on it as the newest its history could carry contradicted itself. Since a stale anchor now has no split, a split derived since W62 never carries the notice. A page written before keeps its W61 notice until re-derived (#1119's TJX). `committed_gap_split` reads a committed page by the same verdict.
- **Not built: re-striking today's multiple at the page's close (option A).** It crosses the 2026-11-13 fence. The page already carries that multiple for every ex-lease page (`valuation.ev_ebitda_ex_lease_at_price`), on the anchor's own share count and net-debt builder, so re-striking with it makes W61's V0 the stock's quote EXACTLY (14 of 14 ex-lease pages with a screen value, |V0/P − 1| < 1e-6). The margin effect would then be the anchor minus the price.
- **W63, GOOGL.** $144,827M is no EBITDA. It is CIQ's comps TEV of 2026-10-30, $3,316,548M (Comparable Analysis → Financial Data, Latest), divided by the Multiples sheet's 22.9x close for the quarter ending 2026-09-30 (Financials_Quarterly, sha256 f494e7869b…). Those are two dates 30 days apart, across GOOGL's fall from $344.08 to about $283.72. `ev_ebitda_basis.headline_basis` never checks that the dates match. At its own close, from CIQ cells only: TEV(09-30) = 9.164139 (TEV/LTM Total Revenue Close, same column) × $445,867M (Income Statement Total Revenue, Q3'25–Q2'26, the four quarters known at that close) = $4,085,947M; ÷ 22.888839 = $178,514M. CIQ's Income Statement EBITDA over those quarters is $173,539M (2.9% below). The exact figure CIQ divides is on no sheet, so NO CELL IS NAMED, and the anchor uses neither number. GOOGL's value is withheld for its 42-day close.

**WHY.** "Today's multiple" (W50) is a claim about a date, and a close 42 days old is not today's on CIQ's history, which a re-export moves to the export date. The ex-lease history moves once a quarter whatever the export, so a flat clock refused it for most of every quarter, which is false by construction (coordinator). Staleness is not inapplicability: flipping `applicable` woke STATE row 10's coupling (`check_tier_agreement` refusing GOOGL's R3 record writes) and the R1 record gate on BRBR. Face validity only: 30 days is W61's limit (a month moves a share price about as much as the effects the screen separates), and the ex-lease due date is the series' own cadence. No forward return was read.

**APPROVAL.** The operator approved the preview on 2026-11-18, verbatim: "Approve, add the row". The row was added and pinned as asked, and it is the only change since the approved preview. THIS CHANGES W61'S APPROVED DISPLAY: the split's stale notice now follows the anchor's cadence rule.

**HOW VERIFIED.**
- Real runs on #1119's refreshed pages, head code against main's code (8ea51e99), with the committed companyfacts fixtures and the CIQ export read-only:
  - GOOGL: $292.90 → no screen value, `applicable` True, R3 tag kept, flag carried under the R4 machine read.
  - GOOGL's main table reads "Screen value / share | not priced | the multiple is the 2026-09-30 close, 42 days before the page's close; a fresh CIQ export clears it" on both renderers.
  - TJX ($136.20) and PARR ($13.14): value unchanged; W61's notice no longer prints.
  - SMPL and IT: the anchor diff is `computed_at` only.
  - Preview collapsed and force-open on both renderers.
- `tests/test_w62_anchor_stale_multiple.py`: 22 tests on the frozen cut (4889ddba). The "not priced" row is pinned end to end on GOOGL's page, md and web, as a positive; the negatives are a priced page, GOOGL held open, and GOOGL where R1 cannot price. GOOGL is priced through the real `CiqFacts` type carrying the vendor D&A its committed page records it read.
- 27 of 27 mutants red, among them a flat clock on the ex-lease history, `applicable` flipping, the cadence read over priced observations only, the gap wording not passed, the split's flat clock back, and the row removed from either renderer or set where R1 cannot price.
- 853 neighbouring tests green.
- Pins about other subjects that used a stale page derive with the check held open (`tests/stale_gate_support.py`): BRBR for W61's flags, GOOGL for the CIQ bridge, the dilution input watch. That is how W50's pins hold the multiple. `test_band_guards`' synthetic layer gains the two dates every committed page carries.

**BOUNDARY.**
- main `8ea51e99`, `data/dossiers/` (26 pages; roster 11 active + 15 watch), and #1119's head `b4e484f6`. Every date is identical on both, and on the frozen cut 4889ddba.
- 21 anchors reach the multiple leg; 2 are stale, BRBR (CIQ, 32 days) and GOOGL (CIQ, 42 days). Every ex-lease page passes: TJX due 2026-12-29, PARR 2026-11-25, TGT 2026-12-09, BURL 2026-12-17, ROST 2026-12-29, and the rest after them.
- 0 pages carry a close after the page's date or an undated close.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- (1) The $0 precheck (`prespend`) loses `anchor.anchor_base_value_per_share` on GOOGL and BRBR and stops those 2 builds for the operator. That is the intended stop, and a CIQ re-export clears both.
- (2) KNOWN LIMITATION: SMPL. Its ex-lease close is 15 days old, and its EV has moved about 24% since (its multiple at the page's close is 6.36x against 5.14x). Days cannot see that; only a test on the price move can, which reads the price, and that is the operator's fence. Not built. Falsifier: a page whose withheld or priced value is later shown to have moved more than its cadence allowed.
- (3) `audit_r1.check_leverage` prints "incomplete anchor (… base=None)" on a stale page and does not name the cause.
- (4) Recipe 3a's proposal still proposes a stale current.
- (5) A close dated after the page's own date is not checked (0 pages).
- (6) Follow-up on the board: `ev_ebitda_basis.headline_basis` should read a multiple only against a TEV of its own date. Of the 20 pages with the block, AMZN and GOOGL carry a 30-day gap.
