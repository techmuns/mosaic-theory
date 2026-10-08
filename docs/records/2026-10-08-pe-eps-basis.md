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

The evidence travels with the answer. Per line it carries:
- the implied prices and their spread;
- the implied NTM EPS that line is tested at;
- the next-four-quarter sum and its gap.

The record also stores the rule as applied and a note saying why a row was not named.

One pure function, `ciq_sheets.pe_eps_basis`, does the test. **One reader per figure:**
- the P/E column is the ladder `current_multiples` already reads;
- the FY EPS is the Current point of the layer's own `paths`;
- only the four quarters, which no path carries, are read here.

A failure inside the annotation is WITHHELD and named in `withheld`; it never costs the layer its
paths, spreads, revisions or ladder. The field is ABSENT until a page is rebuilt
(`TOP_DROP_WHEN_NONE`), so **this PR changes no committed page.**

**WHY.** Step (2) of the build order the operator ruled for the EV/NTM EBIT recipe
(`2026-10-08-ev-ntm-ebit-eligibility-ratified.md`). CIQ picks the basis per company and the sheet
never says which: AMZN's P/E is struck on GAAP EPS and GOOGL's on normalized. An R3 underwrite
multiplying normalized EPS by a GAAP-struck multiple mixes two bases. AMZN's FY2028 consensus is
GAAP $14.11 against normalized $13.27, so the mixed figure understates by 6%.

**It lives beside `current_multiples`, not on each row.** A per-row key would have to be absent on
every non-P/E row, and the serializer drops a `None` key only at the layer level.

**THE TEST NEEDS NO PRICE.** P/E × EPS IS the price the multiple was struck at. So on the struck
line it is one number in every FY row, and on the other line it drifts with the gap between the two
lines.

The rule was set by face validity on the 26 exports, never by any outcome.

*Naming an FY basis.* SEPARATION IS TESTED FIRST. A line is named when:
- its implied prices agree within 1%; AND
- its rival's spread is at least 3× that and at least 0.5% — whether or not the rival also sits
  inside its own cap.

`indistinguishable` is the case where both fit and neither separates. The other two cases:
- A struck line is not exact: LLY's agrees to 0.05% and ROST's to 0.56%, because CIQ strikes on
  figures Trends prints rounded. Hence a cap, not equality.
- The 0.5% floor holds NFLX's FY rows at `indistinguishable`. Its two lines are under 0.5% apart.

*The NTM row.* Its implied EPS is a price ÷ the NTM P/E, set against each line's next four quarters
(the first four Trends lists, since it lists only unreported periods):
- **Which price.** A NAMED FY line gives one price, used for both lines. When the FY rows fit both
  lines, each line is tested at its OWN price.
- **Cap.** The cap widens to four quarters' cent-rounding (±$0.02) where that is larger. It is
  measured against the implied NTM EPS, the base the gap uses: AORT's quarters sum to $0.12, so
  rounding alone is ±16%.
- **Never flipped.** An NTM row that fits the OTHER line from a named FY basis is `undetermined`.
- **Never inherited.** A row the FY rows give no price for is `undetermined`, never copied from the
  FY rows.

**HOW VERIFIED.** Real run on all 26 committed names' Estimates exports, each the export its page
was built from (hash-matched on every one):

| scope | gaap | normalized | indistinguishable | undetermined |
|---|---|---|---|---|
| FY rows | 4 (AMZN, AORT, UBER, VRRM) | 18 | 1 (NFLX) | 3 (FUBO 1 row; ORKA, TECX 0) |
| NTM row | 4 (AMZN, AORT, UBER, VRRM) | 12 | 2 (GOOGL, NFLX) | 8 |

The eight NTM `undetermined`, each with its reason in `note`:

| reason | names |
|---|---|
| quarters missing on a line | CNXC, MVST |
| FY rows establish no price | FUBO, ORKA, TECX |
| no NTM P/E | VITL |
| neither line fits | LLY (normalized 1.63%, GAAP 8.16%) |
| one line fits, the rival neither fits nor separates | ROST (normalized fits at 0.91%; GAAP 1.02%) |

- **AMZN, to the cent.** P/E × GAAP EPS gives $256.24 / $256.37 / $256.23 across FY26–28 (spread
  0.053%). The same × normalized gives $165.20 / $254.90 / $240.98 (37%). The NTM row's implied EPS
  sits 0.12% from the GAAP sum of FQ3'26–FQ2'27 (9.39) and 3.2% from the normalized sum (9.10).
- **GOOGL's and NFLX's NTM rows are `indistinguishable`:** both lines fit, so the choice does not
  matter for their anchors. GOOGL's lines' next four quarters are 0.15% apart, so its R3 record's
  "normalized P/NTM" is right either way.
- **Margins.** Named FY rows:
  - largest own spread: VITL 0.970%, against the 1% cap;
  - smallest rival: IT 0.987%, against the 0.5% floor;
  - smallest separation: VITL 5.8×.

  Named NTM rows:
  - largest own gap: AORT 3.37%, inside its 16% rounding cap;
  - smallest rival: TGT 0.535%, against the 0.5% floor (thin);
  - smallest separation: TGT 5.1×.

  Every thin margin fails toward `undetermined` or `indistinguishable`, never toward a wrong name.
- **Dry run through `refresh_dossier`** (`forward_consensus_transform`) on copies of all 26 pages:
  - landed on 26 and refused none;
  - no other top-level key and no other `forward_consensus` key moved, `withheld` included;
  - every `dossier.md` is byte-identical, and `anchor` stays last.

*Tests* (`tests/test_pe_eps_basis.py`, 48). The pure pins run in CI on a frozen DERIVED table
(`tests/fixtures/pe_eps_basis_cases.json`): 11 cases covering every outcome, with each P/E row and
Current consensus per line as the pages already commit them, exports named and hashed. They pin:
- each outcome, and that a named basis obeys its stated rule;
- AMZN to the cent;
- NFLX on both rows;
- LLY's NTM row, which no line fits;
- ROST's note, which says WHICH line fits;
- FUBO's single row;
- no-P/E writes no field;
- a $0.00 quarter sum as a figure;
- a negative P/E left untested;
- a missing line as an outcome;
- the NTM cap on the implied base;
- a path without its Current point leaving its row untested (built from AMZN's committed page —
  13 of 676 committed paths end before Current, none of them EPS yet).

Local-only (they need the workbook):
- the live read equals the frozen case on the same export, and every implied price is P/E × the
  layer's own path;
- a Trends sheet without the GAAP block still answers (AMZN's real sheet);
- a failure in the annotation leaves the layer standing and names itself in `withheld`.

The contradiction guard has no corpus instance. Its pin is CONSTRUCTED from AMZN's real values and
says so.

*Mutation.* 17 mutants, all killed:

| mutant | tests failing |
|---|---|
| names the rival | 24 |
| last four quarters | 11 |
| wiring dropped | 11 |
| NTM inherited from the FY rows | 10 |
| no separation | 4 |
| no rival floor | 2 |
| NTM cap ignores rounding | 2 |
| fitting FY rows leave NTM untested | 2 |
| contradiction flips silently | 1 |
| `null` instead of absent | 1 |
| zero sum read as missing | 1 |
| note always 'neither fits' | 1 |
| missing block drops the field | 1 |
| negative P/E tested | 1 |
| NTM cap on the line's own sum | 1 |
| no isolation | 1 |
| FY EPS taken from a non-Current point | 1 |

The last one first SURVIVED; the stale-path pin above was added for it. A cent-rounding allowance
on the FY cap also survived in the first cut — no FY row needs it — and was removed.

**REVIEW OF #686 (`/code-review`, 2026-10-08) — ten findings.**

Eight were applied:

| # | finding | fix |
|---|---|---|
| 1 | zero sum | `is not None` |
| 3, 4 | ROST's note and this record's reason | the note now says which line fits |
| 5 | missing block | an outcome, never an absent field |
| 6 | FY rows that fit both lines | they establish two prices; NFLX's NTM moves `undetermined` → `indistinguishable` |
| 7 | negative P/E | only a positive P/E is tested |
| 8 | the NTM cap | now on the implied base |
| 10 | annotation failure | withheld, never raised |

Finding 9 (one reader per figure) was applied too: the FY EPS now comes from `paths`.

**Finding 2 is held for the operator.** It asks that a line be named only if its rival is OUTSIDE
the rival's own cap. That is a rule change. Measured on the 26:
- **IT** would move normalized → `indistinguishable` on both rows (its GAAP rival spread is 0.99%,
  inside 1%, against normalized 0.06%);
- **TGT's** NTM row would move normalized → `indistinguishable`.

No GAAP-struck name moves, and eligibility is untouched. The rule text now states the precedence the
code applies.

**BOUNDARY.**
- **Population:** the 26 committed dossiers at main @4e2af811, and each one's on-disk Estimates
  export (the hash its page carries).
- **"13 of 676 paths":** every path on those pages.
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
## Amendments
**2026-10-08 — finding 2 RULED: keep the current rule.** Operator, after the review: "keep the
current rule". Separation stays tested first: a line is named when it fits within its cap and its
rival is at least 3× as dispersed and at least 0.5%, whether or not the rival also sits inside its
own cap. IT stays normalized on both rows and TGT's NTM row stays normalized. The field reached the
26 pages in #687 (`docs/records/2026-10-08-artifact-pass-pe-eps-basis.md`).
