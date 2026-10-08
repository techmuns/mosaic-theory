---
id:
status: shipped
date: 2026-10-08
prs: [686]
supersedes:
superseded-by:
---

# The forward P/E states which EPS line it is struck on — measured per export, the NTM row on its own, never assumed

**WHAT.** A new field, `forward_consensus.pe_eps_basis`, beside `current_multiples`. It states
which consensus EPS line — `EPS (GAAP)` or `EPS Normalized` — CIQ struck the Estimates→Multiples
Price/Earnings column on, for two scopes:
- **`fiscal_years`** — the FY rows the page carries (FY+0..FY+2);
- **`ntm`** — the NTM row, tested on its own, because it is the row an R3 anchor reads.

Each scope reads one of four values:

| value | meaning |
|---|---|
| `gaap` / `normalized` | that line is shown to be the struck one |
| `indistinguishable` | both lines fit; the data cannot tell them apart |
| `undetermined` | neither line is shown to be the struck one |

The evidence travels with the answer: per line, the implied prices, their spread, the
next-four-quarter sum and its gap, plus the rule as applied and a note saying why a row was not
named. One pure function, `ciq_sheets.pe_eps_basis`, does the test, and `forward_consensus` calls
it. The field is ABSENT until a page is rebuilt (`TOP_DROP_WHEN_NONE`), so **this PR changes no
committed page.**

**WHY.** Step (2) of the build order the operator ruled for the EV/NTM EBIT recipe
(`2026-10-08-ev-ntm-ebit-eligibility-ratified.md`). CIQ picks the basis per company and the sheet
never says which: AMZN's P/E is struck on GAAP EPS and GOOGL's on normalized. An R3 underwrite
multiplying normalized EPS by a GAAP-struck multiple mixes two bases. AMZN's FY2028 consensus is
GAAP $14.11 against normalized $13.27, so the mixed figure understates by 6%.

**It lives beside `current_multiples`, not on each row.** A per-row key would have to be absent
on every non-P/E row, and the serializer drops a `None` key only at the layer level. Per-row
`null`s would also churn every page. The four outcomes, the tested periods and the evidence belong
together anyway.

**THE TEST NEEDS NO PRICE.** P/E × EPS IS the price the multiple was struck at. So on the struck
line it is one number in every FY row, and on the other line it drifts with the gap between the two
lines.

The rule was set by face validity on the 26 exports, never by any outcome:
- **Named FY basis:** the line's implied prices agree within 1%, AND the rival's spread is at
  least 3× that and at least 0.5%.
  - A struck line is not exact: LLY's agrees to 0.05% and ROST's to 0.56%, because CIQ strikes on
    figures Trends prints rounded. Hence a cap, not equality.
  - The 0.5% floor is what holds NFLX at `indistinguishable`. Its two lines are under 0.5% apart,
    so a 0.24% GAAP spread beside 0.06% normalized is not evidence.
- **NTM:** tested only when the FY rows name a basis, because only then is there a price. The
  price ÷ the NTM P/E gives the implied NTM EPS, which is set against each line's next four quarters
  (the first four Trends lists, since it lists only unreported periods).
  - Its cap widens to the cent-rounding of four summed quarters where that is larger. AORT's sum to
    $0.12, so rounding alone is ±17%.
  - An NTM row that fits the OTHER line is `undetermined`, never a silent flip.
  - An untested NTM row is `undetermined`, never inherited from the FY rows.

**HOW VERIFIED.** Real run on all 26 committed names' Estimates exports, each the export its page
was built from (hash-matched on every one):

| scope | gaap | normalized | indistinguishable | undetermined |
|---|---|---|---|---|
| FY rows | 4 (AMZN, AORT, UBER, VRRM) | 18 | 1 (NFLX) | 3 (FUBO 1 row; ORKA, TECX 0) |
| NTM row | 4 (AMZN, AORT, UBER, VRRM) | 12 | 1 (GOOGL) | 9 |

The nine NTM `undetermined`, each with its reason in `note`:

| reason | names |
|---|---|
| quarters missing on a line | CNXC, MVST |
| FY rows name no basis | FUBO, ORKA, TECX, NFLX |
| no NTM P/E | VITL |
| off both lines | LLY (normalized 1.6%, GAAP 8.2%), ROST (~1%) |

- **AMZN, to the cent.** P/E × GAAP EPS gives $256.24 / $256.37 / $256.23 across FY26–28 (spread
  0.053%). The same × normalized gives $165.20 / $254.90 / $240.98 (37%). The NTM row's implied EPS
  sits 0.12% from the GAAP sum of FQ3'26–FQ2'27 (9.39) and 3.2% from the normalized sum (9.10).
- **GOOGL's NTM row is `indistinguishable`.** Its two lines' next four quarters are 0.15% apart, so
  its R3 record's "normalized P/NTM" is right, and would be right on either line.
- **Margins.** Named FY rows:
  - largest own spread: VITL 0.970%, against the 1% cap;
  - smallest rival: IT 0.987%, against the 0.5% floor;
  - smallest separation: VITL 5.8×.

  Named NTM rows:
  - largest own gap: AORT 3.37%, inside its 16.7% rounding cap;
  - smallest rival: TGT 0.535%, against the 0.5% floor (thin);
  - smallest separation: TGT 5.1×.

  Every thin margin fails toward `undetermined` or `indistinguishable`, never toward a wrong name.
- **Dry run through `refresh_dossier`** (`forward_consensus_transform`) on copies of all 26 pages:
  - landed on 26 and refused none;
  - no other top-level key and no other `forward_consensus` key moved;
  - every `dossier.md` is byte-identical, and `anchor` stays last.
- **Tests** (`tests/test_pe_eps_basis.py`) run on a frozen DERIVED table
  (`tests/fixtures/pe_eps_basis_cases.json`): 11 cases covering every outcome, with each P/E row and
  Current consensus per line as the pages already commit them, exports named and hashed. They pin:
  - each case's outcome;
  - that a named basis obeys its stated rule;
  - AMZN to the cent;
  - NFLX's `indistinguishable`;
  - LLY's NTM not named;
  - FUBO's single row;
  - no-P/E writes no field;
  - the live read equals the frozen case on the same export (11 of 11 here; skips where the
    workbook is absent);
  - the field absent, not `null`, on a page without it, built in the test so it cannot lapse.

  The contradiction guard has no corpus instance. Its pin is CONSTRUCTED from AMZN's real values and
  says so.
- **Mutation:** eleven mutants. Ten killed:

  | mutant | tests failing |
  |---|---|
  | names the rival | 21 |
  | last four quarters | 11 |
  | wiring dropped | 11 |
  | every FY row, not FY+0..+2 | 10 |
  | NTM inherited from the FY rows | 6 |
  | no rival floor | 2 |
  | no separation | 1 |
  | NTM cap ignores rounding | 1 |
  | contradiction flips silently | 1 |
  | `null` instead of absent | 1 |

  The eleventh, a cent-rounding allowance on the FY cap, SURVIVED: no FY row in the corpus needs
  it. It was removed rather than kept unpinned. All 26 outcomes are unchanged without it.

**BOUNDARY.**
- **Population:** the 26 committed dossiers at main @4e2af811, and each one's on-disk Estimates
  export (the hash its page carries).
- **Date:** measured 2026-10-08.
- **Units:** spreads and gaps are fractions; prices in $ per share as CIQ strikes them; EPS in $.

**THIS RULE IS NOT THE ONE THE RATIFICATION RECORD USED.** That scan named a basis when P/E × EPS
varied by under 0.3% and 3× less than the other line. It reported AORT and VITL as "the test cannot
tell"; this rule names AORT GAAP and VITL normalized. Eligibility is unchanged:
- AORT carries no material non-operating income, so it fails condition 3;
- VITL is normalized.

AMZN and UBER remain the only names meeting all three conditions.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Pages carry it after an artifact pass.** `forward_consensus_transform` on the 26 pages, in its
  own PR.
- **Not rendered.** The JSON carries it; the page does not show it yet. A render is a layout change
  under the preview rule.
- **`P/LTM EPS` is still unlabelled** (§5.0 row 32 (1)), and the forward-multiple HISTORY's
  P/NTM EPS rows keep their `BASIS MATCH: LIMITED` ruling. Both are out of scope here.
- **Version row `2026-10-08.3`** names this change, and also #684's anchor change, which appended
  no row. That is the same omission the 2026-10-08.1 note records, caught here rather than left.
