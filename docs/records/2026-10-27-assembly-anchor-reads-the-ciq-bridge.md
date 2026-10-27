---
status: shipped
date: 2026-10-27
prs: [816]
supersedes:
superseded-by:
---

# A fresh assembly's anchor reads the CIQ bridge the backfill reads, so a pass no longer drops vendor-filled inputs; AMZN's and UBER's debt-side gaps to CIQ are itemized, and both are definitions

**WHAT.** STATE.md §5.0 row 27 item (7) closes in code. Item (2) is itemized and stays open only
as a recorded definition difference. Item (3) is re-checked and unchanged.

- **Item (7), the fix.**
  - `anchor.ciq_bridge(bundle, ticker)` is now the one CIQ read for both anchor write paths. It
    returns the workbook's cross-checked facts and a note, `None` for a refused extraction, and
    raises on two exports of one kind, as the backfill did.
  - `assemble._assembly_anchor` is the deterministic part of assembly that builds the anchor. It
    passes those facts to `compute_anchor`. `assemble_one` calls it where it called
    `compute_anchor` with no `ciq=`.
  - `cli._machine_anchor` (the `anchor-backfill` / `anchor-retag` computation) reads through the
    same helper. Its console lines are unchanged.
- **Item (2), the diagnosis.** No defect in `vinci/edgar/net_debt.py`. Both gaps are definitions,
  now stated in the module's docstring:
  - **AMZN −$8,544M** = −$9,315M of financing obligations CIQ counts as debt + $771M where the
    builder reads face value and CIQ reads carrying value;
  - **UBER +$222M** = its finance leases, which CIQ's Total Debt leaves out.
- **Item (3), re-checked.** Nothing has changed since its 2026-10-09 diagnosis.
- **No page is re-assembled or backfilled here.** Pages refresh in the one paid pass after the
  November CIQ re-exports.

**WHY.**
- **Item (7).** `compute_anchor` fills a hole EDGAR leaves from the CIQ workbook only when it is
  handed one. `anchor-backfill` handed it the workbook; assembly handed it nothing. So every input
  only CIQ supplies went UNKNOWN on each re-assembly, and each pass had to backfill it back.
  - On the 2026-10-26 pass this hit GOOGL's D&A (its anchor turned inapplicable) and ORKA's net
    debt (`docs/records/2026-10-26-artifact-pass-17-pages.md`).
  - The defect is wider than those two. FUBO's net debt, LLY's FCF, and MVST's D&A and net debt
    have been on the EDGAR-only assembly read since earlier passes. They were left there on
    purpose: `docs/records/2026-10-21-tjx-review-valuation-bases.md` re-derived them "on the
    assembly path (EDGAR only)" so the CIQ fill would not move them for an unrelated reason.
    Each had carried the CIQ value before:
    - LLY's FCF until 2026-09-30;
    - MVST's two inputs until 2026-09-18;
    - FUBO's net debt until 2026-10-21.
  - A rule of "backfill the pages that read `vendor_bridge`" could never find those three,
    because they had already lost the flag.
- **Item (2).** STATE row 27 carried AMZN −$9,640M and UBER −$1,775M as "not itemized". Those are
  the 2026-10-08 figures. #749's one builder moved them to −$8,544M and +$222M
  (`docs/records/2026-10-19-net-debt-one-builder.md`). Neither had been itemized line by line.

**HOW VERIFIED.**
- **Measured first, on the live corpus.** For each of the 27 committed pages: the anchor as main's
  assembly computes it (no `ciq=`) against the backfill's computation, on the page's mechanical
  layer, live EDGAR companyfacts and the real CIQ workbooks.
  - **CIQ extraction:** 0 of 27 refused, 0 folders absent.
  - **Pages main's assembly degrades** (a bridge input differs): 7.

    | Page | Input lost without `ciq=` | Value with it | On the committed page |
    |---|---|---|---|
    | GOOGL | `d_and_a` (anchor turns inapplicable; base $213.539 → none) | 25,536 | the CIQ value (backfilled 2026-10-26) |
    | ORKA | `net_debt` | −871.1 | the CIQ value (backfilled 2026-10-26) |
    | IT | `ltm_fcf` | 1,257.9 | the CIQ value |
    | TECX | `net_debt` | −222.7 | the CIQ value |
    | FUBO | `net_debt` | 172.4 | UNKNOWN |
    | LLY | `ltm_fcf` | 18,190 | UNKNOWN |
    | MVST | `d_and_a`, `net_debt` | 33.201, 65.2 | UNKNOWN, UNKNOWN |

  - **Pages whose anchor reads `vendor_bridge` today: 4 of 27** (GOOGL, IT, ORKA, TECX). The flag
    and a CIQ-sourced input agree on every page.
- **Real run, fixed path.** `assemble._assembly_anchor` was run for GOOGL and ORKA against their
  real CIQ workbooks, then for the other five:
  - **Before:** GOOGL's D&A reads `UNKNOWN — no D&A tag (combined or split)` and ORKA's net debt
    `UNKNOWN — no debt/cash tag`.
  - **After:** each reads the committed vendor-bridged value and its source string, with
    `data_quality = vendor_bridge`. IT and TECX also match their pages.
  - FUBO, LLY and MVST read the CIQ values in the table above. Their pages move on their next
    re-assembly.
- **Pins on a frozen cut of the real inputs** (`tests/test_anchor_assembly_ciq_bridge.py`, 10).
  The cut is `tests/fixtures/anchor_ciq_bridge.json`, taken at main `47d8ca27` and holding, for
  GOOGL and ORKA:
  - the page subset the chain reads;
  - the anchor block `anchor-backfill` wrote on 2026-10-26;
  - the four facts the bridge reads (derived scalars only);
  - the tracking companyfacts fixture, trimmed to the tags the chain's output depends on (14 of
    34 for GOOGL, 6 of 27 for ORKA).

  The cut was checked to reproduce the committed block and the full page's read. Positive pins:
  - the assembly chain (`_assembly_anchor`, the R4 proposal, `preserve_operator_tag`) writes the
    backfilled block, every field except `computed_at`, GOOGL's operator decision included;
  - `_machine_anchor` on the same inputs gives the same block;
  - `assemble_one` builds its anchor through `_assembly_anchor`, read off the source, because
    `assemble_one` cannot be driven offline. This is the `test_spot_audit` / `test_freshness`
    precedent.

  Negative pins:
  - a name with no CIQ pull still reads UNKNOWN, and its block differs from the backfilled one;
  - a workbook without the row reads UNKNOWN, never a guess;
  - a refused extraction hands on nothing.
- **Mutations.** Each was applied with `PYTHONDONTWRITEBYTECODE=1` and restored after:

  | Mutant | Pins red |
  |---|---|
  | `_assembly_anchor` drops `ciq=` | 3 (both positives, the backfill parity) |
  | `assemble_one` calls `compute_anchor` directly | 1 |
  | the backfill reads no CIQ | 1 |
  | the helper hands on a refused extraction | 0 |
  | the helper's and `_bridge_inputs`' refusal checks both removed | 2 |

  The helper-only mutant survives because `_bridge_inputs` checks `ciq.ok` too: the refusal is
  guarded twice.
- **Item (2), line by line, at the shared 2026-06-30 balance sheet** (EDGAR from companyfacts,
  CIQ from each Financials workbook's quarterly Balance Sheet, $M).

  AMZN (EDGAR's EV net debt 120,103 against CIQ's 128,647):

  | Leg | EDGAR (the builder) | CIQ | Gap |
  |---|---|---|---|
  | Cash + short-term investments | 78,213 + 44,775 | 122,988 | 0 |
  | Short-term borrowings | 325 | 325 | 0 |
  | Finance + operating leases | 13,451 + 96,320 | 15,433 + 94,338 | 0 |
  | Current long-term debt | inside 132,995 | 3,745 = 3,330 + **415** financing obligations | |
  | Long-term debt | 132,995: `LongTermDebt`, at face | 137,794 = 128,894 + **8,900** financing obligations | |
  | Debt, together | 132,995 | 141,539 | **−8,544** = −9,315 + 771 |

  - The financing obligations are in Amazon's 10-Q (0001018724-26-000026), in the commitments
    note's footnote: $415M "within 'Accrued expenses and other'" and $8.9bn "within 'Other
    long-term liabilities'".
  - companyfacts carries no instant for them at 2026-06-30 or at 2025-12-31 (a raw scan of every
    instant at both dates), so the builder has nothing to read.
  - The $771M is the 10-Q debt note's "unamortized discount and issuance costs, net". Amazon tags
    face value ($132,995M) as `LongTermDebt`. The builder's larger-of rule takes that over
    noncurrent + current carrying value ($128,894M + $3,330M). OC's tagged $899M
    `SeniorNotesCurrent` is found only through that rule, so it stays.
  - The same decomposition holds at 2025-12-31: −(358 + 7,800) + 440 = −7,718. Over the eight
    CIQ quarterly columns back to 2024-09-30 the gap sits between −7,013 and −8,544.
  - On AMZN's ex-lease anchor bridge the difference is about $0.78 per diluted share (8,544 /
    10,903M shares).

  UBER (EDGAR's EV net debt 9,562 against CIQ's balance-sheet 14,731 − 5,391 = 9,340):

  | Leg | EDGAR | CIQ | Gap |
  |---|---|---|---|
  | Cash + short-term investments | 4,870 + 521 | 5,391 | 0 |
  | Debt (`LongTermDebt`, current maturities inside) | 12,723 | 1,997 + 10,726 | 0 |
  | Operating leases | 2,008 | 178 + 1,830 | 0 |
  | Finance leases | 222 (138 + 84, the 10-K note at 2025-12-31) | not carried | **+222** |

  CIQ's own "Net Debt" field (4,744) also nets $4,596M of long-term marketable securities. That is
  CIQ's definition, read since the 2026-10-11 export, and the page already prints it as its own
  `ev_bridge` line (`docs/records/2026-10-11-uber-reassembled-on-new-ciq.md`).
- **Item (3), re-checked.** FUBO's export (files dated 2026-09-01) and BRBR's (2026-09-22) predate
  the 2026-10-09 diagnosis. The 2026-10-26 Drive comparison replaced only AORT, CNXC and ORKA.
  - At main `e84beb67` (10-09) and `47d8ca27` both pages withhold the same ratios: FUBO "RoE, RoCE,
    RoA", BRBR "RoE, total debt/equity", `[LTM 12 months Jun-30-2026]`.
  - FUBO's Levered FCF still reads −$107.8M `[12 months Sep-27-2025]`. Its annual sheet has an
    `LTM 12 months Jun-30-2026` column with that row empty, and its synthesis still calls the
    figure "LTM". FUBO has not been re-assembled since 2026-08-18.
  - On the other 25 pages the Levered FCF reads its sheet's latest column. NKE's
    `12 months May-31-2026` is its fiscal year-end and its latest column.
- **Suite:** ruff and `mypy --strict` clean, and the full offline suite. The result is in the PR.

**BOUNDARY.**
- **Pages:** the 27 committed `data/dossiers/*/dossier.json` at main `47d8ca27`.
- **EDGAR:** companyfacts through `EdgarClient` on 2026-10-27, from the shared cache. The frozen cut
  uses `tests/fixtures/companyfacts/` at the same commit.
- **CIQ:** the assembler's copy (`mosaic-theory-ta/data/manual/ciq`, read-only), mirrored from Drive
  on 2026-10-26.
  - GOOGL `…Financials_Quarterly.xls` sha `36160a403e`;
  - ORKA's file and sha are in the fixture;
  - AMZN sha `e5abf9d69d`;
  - UBER sha `a55c4821ce`.
- **"Degrades":** any of `_BRIDGE_FIELDS` differs between the two computations on the same inputs.
- **Units:** $M, except shares and $ per diluted share.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The next pass moves three pages for this reason alone.** FUBO's net debt, LLY's FCF and MVST's
  D&A and net debt take their CIQ values the next time each is re-assembled or backfilled. The
  pass that does it should report those moves apart from its fresh-data drift.
- **Neither write path records a refused extraction on the page.** The backfill prints it, and
  assembly drops it. 0 of 27 refuse today, so this hides nothing on the corpus.
- **AMZN's and UBER's differences stay.** They are recorded in `net_debt.py`, and none is a
  misread. Telling face value from carrying value would mean matching the excess to an unread
  current-debt tag, which is not built.
