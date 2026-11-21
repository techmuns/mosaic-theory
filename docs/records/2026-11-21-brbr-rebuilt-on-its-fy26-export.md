---
status: open
date: 2026-11-21
prs: [1178]
---

# BRBR rebuilt on its FY2026 CIQ re-export, priced at the 2026-11-20 close ($14.57): one paid build, 8 calls, $4.15 of the operator's $4.85 cap, after a $0 precheck exit 0; lean mixed on 5 of 5 draws, no proposal. The rebuilt page carries no `ev_ebitda_basis` block, because the annual export has no LTM column right after a fiscal year-end (as on SMPL's and V's pages), and the $0 precheck does not compare that block

**WHAT.**
- **The build.** Run `ae3e0c41`, on main `b2e62ce6`: 8 calls (2 covenant, 1 driver extraction, 5 synthesis draws), $4.15, 0 failed, 0 refused by the cap, outcome `written`. It ran from the BRBR rebuild worktree's own `vinci/`, cache (an APFS clone of the primary's, kept apart from W85's draw running the same hour) and store copy. A wrapper reserved each call's worst case before sending, at 2.5 characters a token plus `max_tokens` of output, and refused any call past $4.85. Vendor pulls were refused, and the evidence spool was set to Drive's `manual/driver-evidence`. All 83 evidence files it wrote carry a Drive id.
- **The inputs.** The operator's 2026-11-21 re-export (Financials Annual and Quarterly, Key Developments, Profile, Estimates, Comparable Analysis) and the 2026-11-19 files (Credit Health, Customers, Suppliers, the Q3 and Q4 2026 calls). Prices to the 2026-11-20 close came from the operator-approved 2-request pull (`docs/records/2026-11-21-a-guide-check-across-two-fiscal-years-is-not-run.md`).
- **What moved on the page** (old = committed 2026-10-26 page, extraction `2026-10-09.3`; new = this build, extraction `2026-11-21.a-guide-check-across-two-fiscal-years-is-not-run`):

| field | old | new | new source_ref |
|---|---|---|---|
| price | 9.55 | **14.57** | EOD BRBR last close (2026-11-20) |
| market cap ($M) | 1,040.7 | 1,695.8 | CIQ Comparable Analysis→Financial Data, as-of 2026-11-20 |
| 52-week high / low | 34.88 / 7.33 | 33.56 / 7.33 | EOD BRBR 52-week high / low |
| EV/EBITDA | 6.4x | 9.0x | CIQ Financials→Multiples 'TEV/LTM EBITDA' Close (latest) |
| P/E | 5.7x | 11.7x | EDGAR XBRL eps_diluted × EOD latest stored close |
| net debt / EBITDA | 3.4x | 3.6x | CIQ Net Debt $1,065M [FQ4/CQ3 Sep-30-2026] ÷ CIQ EBITDA $298M [12 months Sep-30-2026] |
| levered FCF ($M) | 201.1 | 74.7 | CIQ Financials→Cash Flow 'Levered Free Cash Flow' [12 months Sep-30-2026] |
| interest coverage | 4.2x | 3.7x | CIQ Income Statement EBITDA ÷ Interest Expense [12 months Sep-30-2026] |
| total debt ($M) | 1,173.1 | 1,084.8 | CIQ Financials→Capital Structure Summary (FQ4/CQ3 Sep-30-2026) |
| geography | US 88%; Other Foreign 8%; Canada 4% | US 87%; Other Foreign 9%; Europe 4% | CIQ Financials→Segments, latest annual column Sep-30-2026 |
| R1 anchor base / share | 57.765 (firm) | **20.9035 (weak)** | anchor: multiple 8.965x at the 2026-11-20 close, margin median over 3 FY |
| guide check | CIQ 2335–2375 vs release 2335–2375 → VERIFIED | CIQ FY 2027 2320–2420 vs the release's 2026 2335–2375 → NOT CROSS-CHECKED, different fiscal years | CIQ revenue guide vs release (#1176) |
| synthesis lean | — | mixed, 5 of 5 draws, no proposal | `synthesis.draw_agreement` |

- **Test pins moved with the page**, as past rebuilds' did:
  - `tests/fixtures/companyfacts/BRBR.json` was regenerated (`scripts/build_companyfacts_fixture.py BRBR`, 26 tags).
  - Its old vintage, as committed at main `b2e62ce6`, was frozen to `tests/fixtures/companyfacts_frozen/BRBR.json`, as NFLX's, SMPL's, GOOGL's and AMZN's were. The net-debt pins compare EDGAR with CIQ figures frozen at 2026-06-30, and #531's grain pin in `tests/test_tag_freshness.py` describes a shape BRBR's FY2026 10-K ended: a fresh revenue alias with no annual series. That pin reads the frozen vintage for BRBR and now also checks, on the tracking fixture, that the served alias carries an annual series.
  - BRBR left `ANCHORS_AWAITING_BACKFILL`: its base is now the recompute's.
  - The W81 basis-block population floor is now 19, and the test states why.

**WHY.** BRBR waited from 2026-11-19 for CIQ to process its FY26 10-K. Coordinator A gave the go to build, relaying the operator's rulings: "Wait for CIQ", a cap of "$4.50 (Recommended)", then "Raise to $4.85 (Recommended)". The 11-19 precheck exited 1 on a press-release Financials export and 2 segment regressions. On this export every Financials statement's latest column is filed (FY and quarter to Sep-30-2026), and FY26 segments are read.

**HOW VERIFIED.**
- $0 precheck at `b2e62ce6` on this store: **exit 0**, 0 regressions, 0 post-spend refusals, 0 of 2 input checks flagged. 120 Sourced fields, the list members and the 6 blocks were compared.
- The paid page's figures match that precheck: price 14.57, anchor 20.9035, the guide line.
- The $0 estimate was $4.00–4.32, against $4.15 spent.
- The full offline suite, unlinked as CI runs it, is in the PR body; so are the CIQ-linked counts.

**BOUNDARY.** One page, BRBR; the costs are run `ae3e0c41`'s list-price figures. The "SMPL and V" claim is a scan of the 26 committed `data/dossiers/*/dossier.json` at this PR's head: 3 pages' annual summary has no `LTM` column (BRBR, SMPL, V), and none of the 3 carries `valuation.ev_ebitda_basis`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **OPEN (owner: agent), §5.0 row 43.** A page built just after a fiscal year-end carries no `ev_ebitda_basis`. CIQ's annual export then has no LTM column, the latest fiscal year being the LTM, and `ev_ebitda_basis._ltm_ebitda` reads only a column named `LTM`. The committed page had the block (ratio 1.018 to CIQ's LTM EBITDA, "indistinguishable"); the rebuild has none. The $0 precheck does not compare `mechanical.valuation.ev_ebitda_basis`, so it did not stop on the loss. A $0 code PR that reads the latest fiscal year where it ends on the LTM date, and adds the block to the precheck's comparison, would restore it on BRBR, SMPL and V by a refresh.
- **Unchecked.** The scenario mirror's `nextEvidence` now reads "effective November 19, 2026", dated `2026-11`, with source "catalyst calendar (stated)". That is a past month for a 2026-11-21 page, and its text is a fragment. It comes from the catalyst calendar and is not measured here.
- The anchor's confidence is `weak`: its margin reads 3 fiscal years, not 8, after BRBR's revenue tag changed.
