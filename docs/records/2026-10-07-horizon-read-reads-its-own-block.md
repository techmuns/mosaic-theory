---
id: 2026-10-07-horizon-read-reads-its-own-block
status: shipped
date: 2026-10-07
prs: [674]
supersedes:
superseded-by:
---

# `horizon_read` reads each metric's revision counts from its own block — fixed in code; every page stays wrong until the artifact pass

**WHAT.**
- `ciq_sheets.horizon_read` now ends each Estimates→Revisions block at the next block of ANY kind
  (`_block_starts`, from #673). Before, it ended at the next metric on its own `_METRICS` list.
- `horizon_read_as_assembled` rebuilds the string the old bounding wrote. It has one use: proving
  that a stored page came from this export. It is never a source of figures.
- `refresh.horizon_read_transform(ticker)` corrects `catalyst_path.horizon_read` in place, but only
  when that rebuild is byte-identical to the stored string. Any other page is left alone for a
  re-assembly, because correcting it would mix vintages.
- `refresh.moved_cited_counts` refuses a refresh when the prose cites a count ('41↑/4↓') that the
  refreshed layer no longer carries anywhere. It is the count-sized companion to
  `moved_cited_claims`, whose floor is money and which let every count through. It reads both
  spellings the stored prose can hold, since a dict claim is serialised with JSON's ASCII escaping.
- **No committed page changes in this PR.** The 26 pages still print the wrong counts until the
  artifact pass runs `horizon_read_transform` (§5.0 row 30).

**WHY.** `_revisions_windows` keeps the LAST 'Last Month' / 'Last 2 Months' / 'Last 3 Months' rows
it sees before the block's end. With the end set at the next listed metric, the scan ran on through
every unlisted block in between and printed that block's counts under the listed metric's name.
AMZN's 'Net Income (GAAP) FQ3 2026: 1m 4↑/0↓, 2m 10↑/0↓, 3m 41↑/4↓' were TEV's; its own block reads
'1m 3↑/0↓, 2m 5↑/1↓, 3m 24↑/8↓'. The field is a synthesis input.

**WHAT THE FIX MOVES** (measured on the 26 pages, boundary below):

| | count |
|---|---|
| printed lines before → after | 431 → 453 |
| lines corrected (same metric and period, other counts) | 114 |
| lines added (the metric's own block has counts; the wrong block had none) | 24 |
| lines removed (the wrong block had counts; the metric's own block has none) | 2 — ROST Interest Expense FQ3/FQ4 2027 |
| corrected lines whose net direction flips on the widest window printed, incl. to or from zero | 51 of 114 |
| pages rebuilt byte-identically under the old bounding, so correctable in place | 26 of 26 |

Names moved per metric: Net Income (GAAP) 26, Interest Expense 22, EPS (GAAP) 19, EPS Normalized 3,
EBIT 1. Revenue, EBITDA, EBT (GAAP) and Net Income (Excl. Excep) never move. Flips include:
- NFLX EPS (GAAP) FQ3 2026: 3m 1↑/0↓ → 10↑/21↓
- V Net Income (GAAP) FQ4 2026: 3m 25↑/0↓ → 4↑/9↓
- GOOGL EPS (GAAP) FQ3 2026: 3m 0↑/1↓ → 21↑/14↓

**The page shows less of it than the synthesis read.** The rendered page prints only the
Revenue/EBITDA/EBIT/EPS lines (`render._HORIZON_KEEP`). Net Income (GAAP) and Interest Expense — two
of the three most-moved metrics — are only counted ('+7 non-headline metric rows in JSON'). The
synthesis prompt carries the whole string.

**DOES THE STORED PROSE LEAN ON A WRONG COUNT?** Every claim in the 26 stored syntheses was scanned
for a cited count in either spelling — 'N↑/M↓' and 'N up / M down'. The scan read 553 claims and
found 15 citing a count, 21 cited pairs in all.
- At token level, none vanishes from the page after the fix, so the dry run refused nothing.
- At line level, none names a metric and period whose line moved. Each cites:
  - a Revenue or EBITDA line (those never move);
  - a line that did not move on that name (CNXC EBIT; BURL and NFLX EPS Normalized);
  - or the FY 'last mo' breadth fields (`consensus_context.eps_trend` / `revenue_trend`), read
    by a different reader. Each such count was found there, under the metric the claim names.
- That other reader, `_revision_breadth`, takes the first 'Upward'/'Downward' within ten rows of its
  title. It was checked on all 52 reads (26 names × EPS (GAAP), Revenue). Every pair sits inside the
  metric's own block, under 'Last Month'.

What this cannot show: whether a lean was drawn partly from a wrong count the prose never quotes.
The text cannot answer that. Re-drawing a synthesis is a re-assembly, which is the operator's call.

**HOW VERIFIED.**
- **Corpus pin.** `tests/test_horizon_read_block_bounds.py` covers all 26 names. Every printed line
  must equal what the metric's own block yields, read INDEPENDENTLY of `_block_starts` — that read
  bounds a block at the next period header ('FQ…'/'FY…' row).
- **Licence pin.** A second corpus pin requires every line that moves to belong to a metric whose
  two boundings end at different rows. That is what licenses correcting a page in place.
- **Transform.** End to end on AMZN: the transform replaces the field and moves nothing else. A
  stored string this export cannot rebuild is left alone (negative pin).
- **Refusal.** A count the prose cites that vanishes is refused, in both spellings. End to end, a
  transform that erases the 3↑/0↓ AMZN's prose cites raises and writes nothing.
- **Dry run on copies of all 26 committed dossier folders, through `refresh_dossier`.**
  - It refused none.
  - Across all 26, exactly one JSON path moved: `mechanical.catalyst_path.horizon_read.value`.
  - On the rendered pages, only the horizon block's revision lines moved, plus its
    '+N non-headline rows' tally on the 15 names whose non-headline line count changed.
  - No `known_wrong.json` seal exists today, so no page is barred from the refresh.
- **Mutation.** Five mutants, all killed:

| mutant | tests failing |
|---|---|
| old bounding restored | 26 |
| renderer scans to the end of the sheet | 26 |
| transform skips the identity check | 1 |
| count guard not wired into `refresh_dossier` | 1 |
| count guard reads only the unescaped spelling | 2 |

The CIQ-backed tests skip in CI (the licensed workbooks are never committed). The guard tests
run without them.

**BOUNDARY.**
- **Population:** the 26 committed dossiers (`data/dossiers/*/dossier.json`) and their on-disk CIQ
  Estimates exports.
- **Code:** branch `fix/horizon-read-block-bounds` on main @0ee72077; measured 2026-10-07.
- **Unit:** one printed line = one metric × one FQ period.
- **Direction:** the sign of up − down on the widest window the line prints.
- **Prose scan:** the claim blocks `_prose` reads (`SYNTHESIS_CLAIM_LISTS` + `SYNTHESIS_CLAIM_SCALARS`).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The guard has a limit.** A count the prose paraphrases in words ('41 upward revisions') is not a
  token and is not caught; the docstring says so. Today's prose was checked for that by hand. 132
  claims carry revision vocabulary, and 58 numbers sit near a revision word outside the two
  spellings. They are dates, percentages, dollar amounts and rating tallies — no horizon count,
  except NCNO's mistyped 'Revenue FQ2 3m 2↑/8↑', and Revenue never moves.
- **Every page is wrong until the artifact pass.** Until then, all 26 print the old counts, and
  every synthesis drawn before this merge read them.
