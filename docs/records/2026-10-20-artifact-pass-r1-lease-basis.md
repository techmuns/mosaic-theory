---
id:
status: shipped
date: 2026-10-20
prs: [752]
supersedes:
superseded-by:
---

# Artifact pass: #749's one net-debt builder and #750's one lease basis land on the committed pages together — 17 anchors re-derived, 14 R1 values move

**WHAT.** The ONE artifact pass that #749 (`docs/records/2026-10-19-net-debt-one-builder.md`) and
#750 (`docs/records/2026-10-19-r1-prices-on-one-lease-basis.md`) both left for after their merge,
run on main `53cbe9fe` (#749 on top of #750 and #751's freshness fix). Artifacts only: pages
(`data/dossiers/*` and the `frontend/dossiers/*` mirror), two EDGAR fixtures, this record, STATE,
and the `ANCHORS_AWAITING_BACKFILL` tracking set, which #749 defined to be emptied in this pass
(the #685 precedent).
- **Step 1, `refresh.lease_basis_transform`** through `refresh_dossier` (kept synthesis) on every
  page but VITL (held, below). 23 pages now carry `valuation.lease_basis`:
  - 15 material with an ex-lease history: AMZN, AORT, BURL, CNXC, EPAM, NCNO, NFLX, NKE, PARR,
    ROST, SMPL, TGT, TJX, WERN, WLK (NCNO is an R2 page with no R1 multiple);
  - 2 material and refused: MVST (6 quarters of history, ≥8 needed) and UBER (4 of 30 checkable
    quarters unreconciled);
  - 6 immaterial: BRBR, GOOGL, IT, LLY, V, VRRM.
  - FUBO, ORKA and TECX were left alone by the transform's own rule: no CIQ EV/EBITDA history.
- **Step 2, `anchor-backfill`** on 17 names: the 15 lease-material ones plus UBER (its lease basis
  refuses, but #749 moves its net debt) and TECX (#749 refuses its stale 2023 debt; CIQ fills it).
  **17 anchors re-derived; 14 R1 base values move** (13 change, NFLX's is new); NCNO, TECX and
  UBER move net debt only.
- **Step 3, `refresh.ev_bridge_transform`** on every page: the EDGAR figure beside CIQ's TEV
  claims, lease-inclusive by construction (#750 review), now read by #749's builder. It moved on
  AMZN, BURL, CNXC, NFLX, NKE, SMPL, TGT, UBER and WERN; checked afterwards, no page's figure
  differs from the builder.
- **Hand corrections and holds:**
  - **AMZN's anchor reason** is restored verbatim. The backfill replaced the operator's R4 re-tag
    text with the machine's under `preserve_operator_tag`, the one rule for BOTH anchor write paths
    (backfill and re-assembly); #701 restored this field after #700's re-assembly did the same.
    STATE row 27 (6).
  - **VITL is HELD at main's page** — no lease basis, no backfill. On the ex-lease history its R1
    screen flips to applicable/firm at $29.84, beside the operator's re-tag reason that no trailing
    median describes the business and that the rent gap is a vendor defect. The $288M is VITL's own
    reported total lease cost (EDGAR `LeaseCost` $293.0M, FY2025), so the reason's premise has moved
    under it; publishing a firm machine value against a standing human judgment is the operator's
    call to make, not this pass's. #749 does not move VITL. STATE row 32 (11).
  - **MVST, LLY and FUBO are not backfilled:** their only change on the backfill path is a CIQ
    vendor fill (`vendor_bridge`) that assembly does not make — MVST's net debt none → $65.2M, LLY
    and FUBO a flag — unrelated to either PR.
- **Fixtures:** `CNXC.json` and `NKE.json` regenerated with main's
  `scripts/build_companyfacts_fixture.py` (which carries #749's builder tags) from the cache the
  backfill read. They are the two names whose anchors also moved on EDGAR filings newer than their
  fixtures; CNXC's now holds `OperatingLeaseLiability` at 2026-08-31 (accn 0001803599-26-000155,
  $905.6M), which a three-way merge of the older regeneration had dropped.
- **`ANCHORS_AWAITING_BACKFILL` is empty again.**

**WHY.** Both PRs changed how the anchor reads net debt and which multiple R1 prices, and both left
the pages for one pass, because they move the same retail anchors. A first build of this pass on
`618f07e5` predated #749 and delivered only the lease half; review of #752 caught it (BURL's page
would have shown $319.93 where main's code gives $322.06), and the pass was rebuilt from main's
pages on `53cbe9fe`.

**HOW VERIFIED.**
- **Before writing anything, the prose was checked** for quotes of the figures this pass moves
  (anchor base value, multiple, net debt) on all 27 pages. Twelve pages quote a matching number;
  on the eight of them whose anchors move (CNXC, EPAM, NFLX, PARR, ROST, TJX, WERN, WLK), every
  quote is CIQ's displayed own-history figure (current, percentile, median) or CIQ's own Net Debt
  line — e.g. TJX "median 12.0x", ROST "median 12.7x", CNXC "CIQ Net Debt $5,249M"; WERN's "31"
  is a date. None quotes the anchor's R1 value.
- **The anchors, committed (main `53cbe9fe`) → new**, `anchor_base_value_per_share`, multiple,
  net debt $M:

  | name | multiple | net debt | R1 $/share |
  |---|---|---|---|
  | TJX | 12.04 → 15.85 | 8,313 → −3,133 | 88.52 → 129.10 |
  | BURL | 12.82 → 16.37 | 5,338 → 1,210 | 183.42 → 322.06 |
  | ROST | 12.72 → 14.84 | 451 → −3,270 | 132.16 → 166.18 |
  | CNXC | 6.89 → 7.46 | 5,249 → 4,131 | 62.55 → 93.27 |
  | PARR | 6.91 → 7.71 | 949 → 567 | 34.01 → 47.86 |
  | NKE | 21.14 → 23.54 | 3,470 → 990 | 89.16 → 101.02 |
  | TGT | 8.44 → 8.95 | 14,804 → 9,946 | 137.57 → 158.47 |
  | EPAM | 22.41 → 25.30 | −637 → −764 | 352.35 → 398.58 |
  | WLK | 7.73 → 7.91 | 4,024 → 3,215 | 105.98 → 115.51 |
  | WERN | 6.68 → 6.65 | 897 → 784 | 30.82 → 32.53 |
  | SMPL | 17.85 → 17.92 | 325 → 273 | 43.33 → 44.10 |
  | AMZN (R4) | 24.39 → 26.12 | 119,007 → 23,783 | 249.57 → 276.71 |
  | AORT (R2) | 32.11 → 37.98 | 331 → 290 | 19.79 → 25.50 |
  | NFLX | 43.35 → 38.49 | none → 5,181 | none → **52.00** (inapplicable → applicable, firm) |
  | NCNO (R2) | no multiple | 255.3 → 242.6 | inapplicable either way |
  | UBER (R4) | no multiple | 7,565 → 9,562 | inapplicable either way |
  | TECX | no multiple | −207.7 → −222.7 (CIQ fill) | inapplicable either way |

- **Each move split into its two causes** (same path, without then with the lease basis):

  | name | committed | #749 builder + today's facts | + lease basis (this pass) |
  |---|---:|---:|---:|
  | BURL | 183.42 | 185.55 (net debt 5,202 = CIQ) | 322.06 |
  | TGT | 137.57 | 140.10 (13,650) | 158.47 |
  | WERN | 30.82 | 30.96 (888) | 32.53 |
  | CNXC | 62.55 | 65.98 (5,036; newer filing) | 93.27 |
  | NKE | 89.16 | 88.50 (4,169; newer filing) | 101.02 |
  | AMZN | 249.57 | 249.47 (120,103) | 276.71 |
  | TJX | 88.52 | 88.52 | 129.10 |
  | ROST | 132.16 | 132.16 | 166.18 |

  BURL/TGT/WERN/AMZN's middle column is #749's own figure; NFLX's value exists only because #749
  reads its net debt (#750's ex-lease path offers no CIQ fill).
- **Consistency on all 27 pages:** `anchor.lease_basis_mismatch` finds none and the valuation-basis
  block lists no lease conflict. Every material page with an ex-lease anchor prints the ex-lease
  basis line; MVST and UBER print the refusal; NCNO describes the history without claiming R1
  prices it; immaterial pages, and held VITL, print what main's do. AMZN's freshness line reads
  "3d old — 2026-10-06".
- **The backfill pin** (`test_the_period_fix_moves_the_committed_anchor_and_exactly_these_names`)
  passes with the set empty and the two fixtures regenerated; before the regeneration it named
  exactly CNXC and NKE.
- **Suite:** see the PR.

**BOUNDARY.**
- **Pages:** the 27 committed dossiers at main `53cbe9fe`, re-derived 2026-10-20; the CIQ exports
  are the shared copy (`mosaic-theory-ta/data/manual/ciq`), each matched to its page by the export
  hash its own-history bands carry; EDGAR is the cache as of 2026-10-20.
- **"Re-derived"** = an anchor written by this pass (17). **"Value moves"** = its
  `anchor_base_value_per_share` differs from main's (14, NFLX's from none).
- **The prose check** searched each page's synthesis prose (`refresh._prose`) for the anchor's base
  value at 0–2 decimals, its multiple at 1–2 decimals with "x", and its net debt at 0–1 decimals.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **VRRM's route-A "net debt / FY26 adj-EBITDA" is not refreshed** (985 → 980 under the builder):
  it is written only at assembly and no refresh path exists, so it lands on VRRM's next
  re-assembly. STATE row 27 (1).
- **VITL is held** until the operator rules on its re-tag reason; then this pass lands it.
- **AMZN's reason was restored by hand again**; until row 27 (6) is fixed, any backfill or
  re-assembly of AMZN overwrites it.
- **MVST's anchor still lacks the CIQ-filled net debt** a backfill would give it — the existing
  assembly/backfill difference.
- **The operator items from #750 stand:** EPAM, WERN and SMPL's R1 records were struck on the old
  basis (row 32 (10)); no cap on thin-EBITDA quarters.
