---
id:
status: shipped
date: 2026-10-27
prs: [828]
supersedes:
superseded-by:
---

# Foreign private issuers leave the primary population until FPI readiness lands, by operator ruling, and one switch re-admits them

**WHAT.** Operator ruling of 2026-10-27, relayed by the lane owner, closing STATE §5.0 row 33:
**EXCLUDE ADRs and other foreign private issuers from the primary population until row 4's FPI
readiness lands.** This record ships that ruling.

- **The definition is deterministic.** A line is a foreign private issuer's when either holds:
  - the feed types it a depositary receipt or a foreign ordinary share (`ADRC` / `GDR` / `OS`,
    `universe.FOREIGN_LINE_TYPES`);
  - its issuer's latest periodic report filed by the reference date is a 20-F or 40-F
    (`instrument.latest_report`). An amendment never counts: it restates an earlier period.
  - Never by country of incorporation alone. Transocean (incorporated in Switzerland) files
    10-K/10-Q and stays.
- **It is measured, not hidden.** Each line leaves at a NAMED stage, `foreign_private_issuer`
  (`DROP_STAGES` 10 → 11), with its evidence: the feed's type, or the 20-F/40-F's form, date and
  accession.
- **One switch.** `UniverseConfig.exclude_foreign_private_issuers`: True for the primary band,
  False for the theme band, which keeps its foreign megacaps. Setting it False re-admits every one
  of them; it is the switch to flip when row 4 lands.
- **No gate threshold changed.** Cap band, ADV floor, SIC denylist and type allowlist are as they
  were.
- **The cohort pool now pools the new stage** (`scripts/build_cohort_pool.py` `POOLABLE`). The
  2026-08-26 ruling — an industry's move is the industry's wherever the issuer is domiciled; "this
  changes the yardstick, not the shopping list" — still holds. Without this, the excluded names
  would have left the industry medians as well as the queue.

**THE SIGNED-OFF POPULATION MOVES, BY OPERATOR RULING.** `docs/records/2026-09-01-population-
signoff-2113.md` sealed 2,113 as the baseline and said a build moving it owes its own sign-off. This
move IS one: the operator's ruling of 2026-10-27, not an engineering choice.

**REAL RUN — the 2026-10-16 build, replayed.**
- **Inputs:** the 2026-10-16 weekly's own cache, TTL ignored, network refused. Main's code
  reproduces the committed 2,065 exactly (`docs/records/2026-10-27-screened-population-typing-and-
  incumbent-line.md`).
- **Result:** **2,065 → 1,803.**
  - **262 leave** at `foreign_private_issuer`: 85 typed `ADRC`, 114 on a 20-F, 63 on a 40-F.
  - **None enter, and 0 caps move** on the names that stay.
  - Every other stage count is identical, except one fewer admission sized on a period-average
    share count (167 → 166), because one leaver was sized that way.
- **The 262 against the measurement before the ruling:** 255 filed a 20-F/40-F (78 typed `ADRC`,
  177 typed `CS`). The 7 others are `ADRC` lines whose issuers file 10-Q, so the feed's type
  decides them.
- **Downstream:**
  - Decision ledger (IT, SMPL, GOOGL, VRRM): **none**.
  - Committed dossiers (27): **none**.
  - **Ranked queue: 56 of the 343** served names leave at the next weekly run. By rank: QFIN 1,
    GPCR 16, SLI 20, JKS 24, SGML 25, IPX 29, DQ 30, NAK 35, FVRR 39, BLDP 49, LAR 51, ALM 57,
    USAS 60, NBTX 61, BTDR 66, PONY 75, LPL 95, BGSI 96, CYD 106, ATS 108, CSIQ 113, WB 119,
    DNN 127, IMTX 131, BLSH 135, JMIA 138, ASM 139, AAUC 144, GIL 154, EXK 159, TATT 165,
    GLOB 170, HSAI 175, SVM 185, SII 190, SA 199, ABVX 201, SSYS 205, MLCO 219, ITRG 224, EQX 226,
    GROY 234, NXE 236, STN 238, BRSL 240, BBUC 253, SID 256, TTAM 264, AGRO 270, LAES 284,
    POET 292, CRML 294, RZLV 304, DBVT 314, IVA 318, AG 339.
- **The full list of 262 leavers**, each with its evidence, is the run's retention rows
  (`stage == "foreign_private_issuer"`). The next weekly run commits them under
  `data/snapshots/screen_runs/`.

**EDGE CASES THE RULING'S WORDS DO NOT REACH — measured, and left in.** Four members have filed no
periodic report yet, so "latest periodic report is a 20-F or 40-F" is false for them. They stay:
- **AYA, OGC** registered on Form 40-F (`40FR12B`, 2026-04-13 and 2026-03-27);
- **GORO, MDA** have filed only 6-Ks, which only a foreign private issuer files.

Widening the definition to registrations or 6-K filers would take a further ruling. FALSIFIER:
the first periodic report each files decides it at the next build.

**HOW VERIFIED.**
- **Pins: `tests/test_foreign_private_issuers.py`, 7.** Real records frozen in
  `tests/fixtures/foreign_private_issuers.json` (Polygon record, 2026-10-16 close / 90-day ADV /
  share count, EDGAR filing index):
  - positive: **HIMX**, typed `ADRC`, leaves on its type, and no SEC call is spent;
  - positive: **ZIM**, typed `CS`, leaves on its 20-F of 2026-03-09, 75 rows down an index of
    6-Ks;
  - negative: **RIG**, incorporated in Switzerland, 10-Q filer, stays;
  - the one switch re-admits all three;
  - the default excludes and the theme band keeps them;
  - an amendment never decides, and a later report is not yet the issuer's word;
  - every admitted type other than `CS` is classed foreign (no OS / GDR line exists to pin by
    record).
- **Mutations: 7 of 7 red.** Switch ignored; type branch removed; filing branch removed;
  amendments deciding; `OS` dropped; theme band excluding; default re-admitting.
- **Existing tests adjusted:**
  - The ADS-sizing pins (`test_ads_denominated_cap.py`) and one dual-class pin run with the switch
    OFF, because ADS sizing still decides the theme band and a re-admitted primary band.
  - The resolver fakes gained a `latest_report` stub.
  - The stage-count guard went 10 → 11 with its reason.
- **No paid model call.**

**BOUNDARY.**
- **Population:** the primary band as of 2026-10-16 (committed `universe_snapshot.jsonl`, 2,065).
- **Polygon types:** the 2026-10-17 reference pull.
- **Filing forms:** each issuer's EDGAR submissions RECENT block as held in that run's cache
  (fetched 2026-10-17), reports filed on or before 2026-10-16.
- **Queue:** the committed `ranked_queue.jsonl` (343 names, run 2026-10-16-01).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
1. **The population shrinks 12.7% and the served queue loses 56 names**, its rank-1 name among
   them. That is the ruling's intent.
2. **The 4 unreached FPIs stay** until they file a periodic report (above).
3. **Cohort medians change composition** only in that the excluded names move from "screened" to
   "pooled". The next pool build must be run for the median to keep them.
