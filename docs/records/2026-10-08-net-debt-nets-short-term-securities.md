---
id:
status: shipped
date: 2026-10-08
prs: [684]
supersedes:
superseded-by:
---

# The anchor's net debt nets the short-term securities a CIQ TEV nets — GOOGL's reads −$121,683M, CIQ's own figure; five committed anchors await the backfill

**WHAT.** `anchor._lease_inclusive_net_debt` now subtracts ONE current-securities tag reported AT
the cash instant (`anchor._short_term_securities`), in priority order:
`MarketableSecuritiesCurrent` → `ShortTermInvestments` →
`AvailableForSaleSecuritiesDebtSecuritiesCurrent`. The bridge text names the tag and date where a
leg is netted, and is byte-unchanged where none is. The EDGAR `cash` concept is NOT changed: the
screen's snapshot also reads it, and the row 27 record warned against that repair.

**WHY.** §5.0 row 27 (`2026-09-10-anchor-net-debt-basis-split.md`): GOOGL's page carried net DEBT
+$64,880M beside CIQ's net CASH −$121,683M for the same quarter. Every multiple this figure bridges
is a CIQ TEV multiple, and CIQ's TEV nets cash AND short-term investments; the anchor netted cash
alone. The 2026-07-22 lease convention made the DEBT leg one ruler with CIQ; this does the same for
the cash leg. It is the prerequisite the operator ruled first for the EV/NTM EBIT recipe
(`2026-10-08-ev-ntm-ebit-eligibility-ratified.md`): AMZN on an EV bridge would be row 27's own
falsifier — "a name underwritten through EV−net-debt that carries material short-term investments".

The tag rules come from the corpus, not from the taxonomy:
- **One tag, never a sum** — a balance tagged twice would be netted twice.
- **Never the parent `MarketableSecurities`**, which carries the noncurrent part. ORKA's parent is
  $857.1M = $605.1M current + $252.0M noncurrent, and CIQ nets $605.1M.
- **Never `AvailableForSaleSecuritiesDebtSecurities`**, which includes securities already inside
  cash equivalents. NFLX's is $9,131.5M against $28.7M of short-term investments.
- **Only at the cash instant.** Six names carry a read tag that STOPPED before their cash date:
  EPAM 2024-12-31, LLY 2025-09-30, TGT 2026-01-31, plus MVST, NKE and ROST. CIQ nets none of them.
- **A stale tag falls through** to the next one. WLK's `MarketableSecuritiesCurrent` ends in 2016;
  its $209M current figure is under the third tag.

**HOW VERIFIED.**

*Against CIQ, on every name where EDGAR and CIQ share a balance-sheet date.* EDGAR cash + the leg
equals CIQ's "Total Cash & ST Investments" exactly:

| name | EDGAR cash | leg (tag) | sum | CIQ |
|---|---:|---|---:|---:|
| AMZN | 78,213 | 44,775 (MarketableSecuritiesCurrent) | 122,988 | 122,988 |
| GOOGL | 55,911 | 186,563 (MarketableSecuritiesCurrent) | 242,474 | 242,474 |
| ORKA | 268.5 | 605.1 (MarketableSecuritiesCurrent) | 873.6 | 873.6 |
| UBER | 4,870 | 521 (MarketableSecuritiesCurrent) | 5,391 | 5,391 |
| NFLX | 9,099.2 | 28.7 (ShortTermInvestments) | 9,127.9 | 9,127.9 |
| WLK | 1,643 | 209 (AvailableForSaleSecuritiesDebtSecuritiesCurrent) | 1,852 | 1,852 |

*Before/after, old and new code on IDENTICAL facts.* The 2026-10-08 EDGAR pull was frozen once and
`compute_anchor` was run on it from a clean main worktree and from this branch, with each name's
CIQ bundle and operator tag as the backfill applies them. **5 of 26 anchors move:**

| name | net debt ($M) | CIQ net debt ($M) | R1 base $/sh |
|---|---:|---:|---|
| GOOGL | +64,880 → **−121,683** | −121,683 | 197.01 → 212.17 |
| AMZN | 163,782 → 119,007 | 128,647 | 245.46 → 249.57 |
| WLK | 4,233 → **4,024** | 4,024 | 104.35 → 105.98 |
| UBER | 8,086 → 7,565 | 9,340 | — (R1 inapplicable) |
| VRRM | 1,038.1 → 1,032.9 | (CIQ is at Q1) | 21.75 → 21.79 |

- **No applicability flag, band-guard flag or recipe changed.** The market-reconciliation guard
  reads this net debt, and none tripped.
- **ORKA and NFLX do not move.** Their EDGAR debt tags are absent, so their anchors already take
  CIQ's net debt, which nets securities.
- **The stale-tag names do not move:** EPAM, LLY and TGT among them.

*Tests.* `tests/test_net_debt_securities_leg.py` runs on real data only:
- the six-name agreement with CIQ, from a frozen derived table
  (`tests/fixtures/ciq_cash_and_st_investments.json`; workbooks named and hashed, never
  committed);
- GOOGL's sign flip to CIQ's figure;
- the ORKA and NFLX traps — present in the data, not read;
- the six stale names — present, ended before the cash date, not netted;
- WLK's fall-through;
- BRBR's unchanged bridge text;
- a pin on `compute_anchor`'s output: AMZN's `anchor.net_debt` carries the leg, and the R1 base
  rises by exactly $44,775M ÷ diluted shares.

*Fixtures.* The six securities tags were added to `FIXTURE_TAGS`, and injected from the same pull
into the 29 committed companyfacts fixtures. 16 of the 29 carry at least one tag; the other 13
filers report none. Each fixture equals its old content plus those tags: 12,696 lines added, 0
removed (`git diff --histogram`).

*The corpus pin.* `test_dilution_denominator`'s pin now names exactly AMZN, VRRM and WLK as
diverging, recorded in `ANCHORS_AWAITING_BACKFILL`. GOOGL is bridge-only to that pin, and UBER has
no base.

*Mutation.* Eight mutants, seven killed:

| mutant | tests failing |
|---|---|
| no shared-period gate | 9 |
| text printed when nothing is netted | 7 |
| search ends at the first tag | 5 |
| leg printed but not netted | 3 |
| parent read first | 2 |
| AFS total instead of AFS current | 2 |
| leg added, not subtracted | 2 |
| **priority order swapped** | **0 — survived** |

The order swap survives because no committed name reports two read tags at its cash instant. The
corpus cannot tell the order apart, so it is not pinned.

**BOUNDARY.**
- **Population:** the 26 committed dossiers at main @14c0b4d0; the tag census also covers the three
  non-dossier fixtures (HLF, HWM, WOR).
- **EDGAR:** companyfacts pulled 2026-10-08 through `EdgarClient`.
- **CIQ:** the Financials workbooks on disk 2026-10-08 (file and sha in the fixture), all six at
  2026-06-30.
- **Units:** $M except per-share values, which are $ per diluted share.
- **"Exactly":** within $0.05M, CIQ's rounding.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The committed pages still carry the old numbers** until the anchor backfill runs in its own
  artifact PR. That PR will also bring in fresh-facts drift, which must be reported separately from
  this leg. `ANCHORS_AWAITING_BACKFILL` and §5.0 row 27 track it.
- **Remaining gaps to CIQ are on the DEBT side and not itemized:** AMZN −$9,640M and UBER −$1,775M.
  After this fix the cash leg contributes nothing to either.
- **The screen's EDGAR snapshot still nets cash only.** `client.compute_fundamental_snapshot` feeds
  `mechanical`'s forward-adjusted net debt. Not changed here, because it is the screen's input.
- **The priority order is unpinned** (the surviving mutant). A filer tagging two read tags at one
  instant would take the first; none does today.
- **Row 27's record stays `open`** until the backfill lands the corrected figures on the pages.
