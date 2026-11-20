# Archetype scope pack 1: what the fund covers, by archetype — for TeamNostra's audit

**Status: committed for TeamNostra's audit**, by the operator's decision of 2026-11-19, verbatim
"Commit it" (answering "Commit the scope pack to the repo for TeamNostra to audit?"). Its §5 rulings
are the operator's ("Approve the defaults", 2026-11-19; SP-R4 ruled 2026-11-20). Nothing here is built: it was prepared on
2026-11-19 at $0, with no model call, no paid run and no page written. The record is
`docs/records/2026-11-19-archetype-scope-pack-1.md`. **Amended 2026-11-20 (W87):** DVN's and DAC's
exports landed and were built, SP-D22 is added, and a list of what was found since is at the end
(`docs/records/2026-11-20-w87-scope-pack-1-amendment.md`).

**How to reply.** Every item has an ID and an Order, as in fix request 2's log:
- **SP-S*n*** is a scope item: a guard or a recipe to build.
- **SP-D*n*** is a defect. The numbers match the probe's own D1–D21.
- **SP-R*n*** is a ruling that some item waits on.

A reply gives each ID one of the five statuses fix request 2 uses (`open`, `in progress (#N)`,
`fixed`, `not fixing: <reason>`, `disagree: <evidence>`) and can be logged in that table's six
columns (§7). Every ID starts `open`.

**Where the evidence lives.** In this repo:
- the findings, `docs/scope-pack-archetypes-1-findings.md`, cited as "findings §N";
- the scripts, `scripts/archetype_probe/` (README there).

Script outputs are not committed; they regenerate under the run's own work folder.

---

## 0. Boundary of every count in this pack

| what | boundary |
|---|---|
| census (§1 counts) | the two committed universes: the screen band `data/snapshots/universe_snapshot.jsonl`, as of **2026-10-16**, 2,065 CIKs; the large-cap band `data/snapshots/theme_universe_snapshot.jsonl`, as of **2026-08-24**, 928 CIKs; union 2,931 distinct CIKs. Unit: a company (CIK). SIC and filing forms read from EDGAR submissions on 2026-11-19; tag signals from SEC XBRL frames (CY2024/CY2025 durations, CY2025Q4I instants), fetched 2026-11-19. Frames are SEC's calendar-aligned views, **not point-in-time**: good enough for a census, never for a value. Cap weights use each band's own snapshot cap |
| live pages (§1, §3) | the **26 committed pages** `data/dossiers/*/dossier.json` at main **`6e03501f`**, re-run at **`ac3c9479`** with an identical result (every page's archetype and status, every defect signature); each one's status from `data/coverage_roster.jsonl` there (11 active, 15 watch); each one's archetype from the census by CIK (`scripts/archetype_probe/pages5b.py`) |
| builds (§2) | the 5a full $0 builds: main `9d036cbb`, 16 builds of 13 names. The fresh-export rerun: main `6e03501f`, 6 names plus 1 variant, and DVN again on its 17:19Z re-export. **Amendment (W87), main `6c22b222`, built 2026-11-20T06:43–06:47Z:** DVN on its quarterly re-export (`a532e1a269`), DAC's 11-file pack, and AWK and MORN re-checked; logs `fresh5a_DVN3.log`, `fresh5a_DAC.log`, `fresh5a_AWKMORN_main.log` (regenerated, not committed). DAC's prices were added to the store: 500 bars, 2024-11-20 to 2026-11-18, one Polygon aggs call. All use a scratch data dir whose page reference date is **2026-10-16** (the fleet's newest screen run, on the maintenance route) and a scratch price store of 16 symbols, 7,914 bars, 2024-11-20 to 2026-11-18 (Polygon, the plan's 2-year window) |
| CIQ figures | each quoted with its source_ref: the workbook's sha256[:10], its sheet, its 0-based row and column as the repo's loader reads them, and the column header. CIQ is not point-in-time, so each figure is **knowable from its export date**: 2026-11-19 for the operator's fresh packs; 2026-11-20 for DVN's quarterly re-export and DAC's pack. No workbook is committed or quoted beyond the cells named |
| EDGAR figures | companyfacts or filed documents, each with its accession |

---

## 1. Declared scope

**The operator's ruling, verbatim:** "adopt and start 5a" (2026-11-19). The operator wrote it with
B's step-5 message attached, and adopted that message. That message is quoted below, verbatim except where
marked: **each "[…]" is an elision made for this pack, not part of the adopted text** (the operator
adopted the full message).

> In scope for stage 1 (1,436 of 2,065, or 69.5% of the screen band; 669 of 928, or 72.1% of large caps)
> - Profitable operating companies, including those that don't report operating income as one line. Asset managers, exchanges, insurance brokers and royalty companies use the same method. Most already work; the build adds the missing debt line items, derives operating income where it isn't reported, and reads share counts per share class.
> - Loss-making growth companies (CRWV, RIVN): in scope once R2 is finished. They are 13.1% of the screen band, too many to leave out.
> - Utilities and managed care: valued on earnings (R1/R3), as today. A rate-base method stays your judgement. Managed care keeps its net-debt refusal, because much of its cash sits in regulated subsidiaries.
> - REITs: in scope, but only after a REIT method (price to FFO) is built. Until then they refuse, so INVH's 192% margin stops.
> - Oil, gas and mining: in scope; a reserve-value leg (PV-10) is added later.
> - Foreign filers reporting US GAAP in dollars (NBIS, AQN): in scope, with two conditions: a company whose business changed is refused rather than valued on its old business's history; a 6-K counts as a results event only when it carries an earnings release or interim statements. That ends the one-week life of an export.
>
> Out of scope, refused when a page is requested (394 of the screen band, 19.1%)
> - Banks, lenders, insurers and broker-dealers with a bank book. […] SCHW's wrong net debt ends here too. The screen stays as it is for now.
> - Pre-revenue biotech. The value depends on binary trial outcomes, which is not this fund's edge.
> - BRK and other conglomerates.
> - MLPs, until you rule on K-1 tax forms.
>
> Stage 2: foreign filers reporting under IFRS or in another currency (190 companies), plus non-SEC names such as EssilorLuxottica and Saint-Gobain. […]
> Wait: companies with no 10-K yet (45). […]
> Two rulings come with this: Debt-free companies such as ISRG: count debt as zero only when the 10-K's balance sheet has no debt line and its notes show no borrowing. The page then says "no debt reported in the 10-K". Otherwise it refuses. K-1 names: your call on whether the fund holds MLPs.

**The two counts, reconciled.** The adopted text's in-scope figure includes the two groups this pack
holds apart: G13/G13b (refused until P/FFO) and G05b/G16b (not decided by the text; SP-R9).
- **Screen band:** 1,306 + 114 (G13/G13b) + 16 (G05b/G16b) = **1,436** (69.5% of 2,065).
- **Large-cap band:** 626 + 40 + 3 = **669** (72.1% of 928).

Both are on §0's census boundary: the screen band as of 2026-10-16, the large-cap band as of
2026-08-24, census read 2026-11-19, unit a company (CIK), measured by `grid.py`'s archetypes. The
other figures in the adopted text match the census: 394 (19.1%) out of scope; 190 in stage 2; 45
waiting; and 13.1% for G03.

**The adopted text mapped to this pack's archetype codes.** This is the probe's mapping, not part
of the adopted text:

| adopted text | archetype codes |
|---|---|
| profitable operating companies, incl. operating income not reported as one line; asset managers, exchanges, insurance brokers, royalty companies | G01, G02, G11, G12, G16 |
| loss-making growth companies, once R2 is finished | G03 |
| utilities and managed care, R1/R3; managed care keeps its net-debt refusal | G14, G09 |
| REITs, after a P/FFO method | G13, G13b |
| oil, gas and mining; PV-10 later | G05 |
| foreign filers reporting US GAAP in dollars, with the two conditions | G17, G17b |
| banks, lenders, insurers, broker-dealers with a bank book | G06, G07, G08, G10 |
| pre-revenue biotech | G04 |
| BRK and other conglomerates | BRK in G08 by SIC; other conglomerates have no census signal (SP-R7) |
| MLPs: out of scope for stage 1 (SP-R4, ruled 2026-11-20) | G15 |
| stage 2: IFRS or another currency; non-SEC names | G18, G19; no CIK |
| wait: no 10-K yet | G20 |
| not decided by the adopted text | G05b, G16b (SP-R9) |

**Precedence, first match wins:**
1. no annual report on file;
2. FPI with IFRS;
3. FPI with US GAAP, non-USD;
4. FPI with US GAAP, USD;
5. statement form, by SIC;
6. economic model, for operating companies only, by frames.

Within statement form the order is bank → lender → managed care → insurer → insurance broker →
broker-dealer → asset manager → REIT → real-estate operator → partnership → utility → royalty →
other 67xx → operating company. Within economic model it is no USD frame data → pre-revenue →
reserve-based → pre-profit → operating income untagged → positive operating income. The rules are
in `scripts/archetype_probe/classify.py` and `grid.py`.

| archetype | decision | classifying signal | screen band n (%) | large-cap band n (%) | union | live pages at `6e03501f` |
|---|---|---|---|---|---|---|
| G01 proven path | **in scope** | 10-K; operating company; `OperatingIncomeLoss` positive in the CY2024 or CY2025 frame | 793 (38.4%) | 435 (46.9%) | 1,202 | 18: AMZN, BRBR, CNXC, EPAM, GOOGL, IT, MCK, NCNO, NFLX, ROST, SMPL, TGT, UBER, V, VITL, VRRM, WERN, WLK |
| G02 operating income untagged | **in scope** | 10-K operating company; revenue present; no `OperatingIncomeLoss` in either frame | 60 (2.9%) | 60 (6.5%) | 115 | 4: BURL, LLY, NKE, TJX |
| G03 pre-profit | **in scope once R2 is built** (SP-S4) | `OperatingIncomeLoss` ≤ 0 in both CY2024 and CY2025. A proxy: the anchor routes on its own whole-history median (TTWO and CRWV disagree with the proxy; findings §3a) | 271 (13.1%) | 37 (4.0%) | 302 | 1: FUBO (watch) |
| G04 pre-revenue | **out of scope, refused at intake** (SP-S1) | revenue < $10M in both CY2024 and CY2025 | 112 (5.4%) | 6 (0.6%) | 116 | **2: ORKA, TECX (both watch) — see SP-R6** |
| G05 reserve-based | **in scope; PV-10 leg later** (SP-S6) | SIC 1000/1040/1090/1220/1221/1311/1400 | 46 (2.2%) | 17 (1.8%) | 62 | 1: PARR (watch). SIC 1311 puts a refiner here; see the note below the table |
| G05b no USD frame data | **not decided by the adopted text** (SP-R9) | 10-K operating company with no CY2024/25 us-gaap USD frame data | 15 (0.7%) | 3 (0.3%) | 18 | 0 |
| G06 bank | **out of scope** (SP-S1) | SIC 6021/6022/6029/6035/6036 | 161 (7.8%) | 27 (2.9%) | 184 | 0 |
| G07 lender / specialty finance | **out of scope** (SP-S1) | SIC 6099, 6111, 6141, 6153, 6159, 6162, 6163, 6172, 6189, 6199 | 52 (2.5%) | 10 (1.1%) | 61 | 0 |
| G08 insurer | **out of scope** (SP-S1); BRK is here by SIC 6331 | SIC 6311/6321/6331/6351/6361/6399 | 45 (2.2%) | 27 (2.9%) | 71 | 0 |
| G09 managed care | **in scope**, net-debt refusal kept | SIC 6324 | 4 (0.2%) | 6 (0.6%) | 10 | 0 |
| G10 broker-dealer / IB | **out of scope** (SP-S1), SCHW's D3 included | SIC 6211 | 9 (0.4%) | 10 (1.1%) | 18 | 0 |
| G11 asset manager / exchange | **in scope** | SIC 6200/6282/6221 | 23 (1.1%) | 16 (1.7%) | 38 | 0 |
| G12 insurance broker | **in scope** | SIC 6411 | 9 (0.4%) | 7 (0.8%) | 16 | 0 |
| G13 REIT | **refused until P/FFO** (SP-S2, lifted by SP-S5) | SIC 6798 | 94 (4.6%) | 37 (4.0%) | 128 | 0 |
| G13b real-estate operator | **refused until P/FFO** (SP-S2) | SIC 6500/6510/6512/6513/6519/6531/6532/6552. **13 REITs sit outside SIC 6798** (they carry `RealEstateInvestmentPropertyNet` ≥ 50% of assets; INVH among them), so a guard on SIC 6798 alone misses them (findings §3b) | 20 (1.0%) | 3 (0.3%) | 23 | 0 |
| G14 regulated utility | **in scope**, R1/R3 | SIC 4911/4924/4931/4932/4941/4961/4991 | 29 (1.4%) | 35 (3.8%) | 64 | 0 |
| G15 partnership / MLP | **out of scope for stage 1** (SP-R4, ruled 2026-11-20) | a partnership name (" L.P.", ends " LP" or ", LP"), or both `PartnersCapital` and `LimitedPartnersCapitalAccount` at CY2025Q4I. Checked before utility | 15 (0.7%) | 7 (0.8%) | 22 | 0 |
| G16 royalty / patent owner | **in scope** | SIC 6792/6794/6795 | 6 (0.3%) | 2 (0.2%) | 8 | 0 |
| G16b holding / investment office | **not decided by the adopted text** (SP-R9) | other SIC 67xx | 1 (0.0%) | 0 | 1 | 0 |
| G17 FPI · US GAAP USD · operating | **in scope**, with the D2 refusal and the D8 6-K rule (SP-S7) | latest annual a 20-F or 40-F; newest fiscal year in us-gaap; reporting currency USD; operating form | 57 (2.8%) | 11 (1.2%) | 68 | 0 |
| G17b FPI · US GAAP USD · other form | **in scope** (as G17) | as G17, with a non-operating form | 8 (0.4%) | 0 | 8 | 0 |
| G18 FPI · US GAAP non-USD (or unread) | **stage 2** | as G17, with a currency other than USD | 25 (1.2%) | 24 (2.6%) | 47 | 0 |
| G19 FPI · IFRS | **stage 2** | newest fiscal year is an `ifrs-full` year | 165 (8.0%) | 141 (15.2%) | 297 | 0 |
| G20 no annual report on file | **wait** | no 10-K, 20-F or 40-F on the CIK | 45 (2.2%) | 7 (0.8%) | 52 | 0 |
| non-SEC names | **stage 2** | no CIK | — (not in either universe) | — | — | 0 |
| **total** | | | **2,065** | **928** | **2,931** | **26** |

**What the counts say.**
- In scope (G01, G02, G03, G05, G09, G11, G12, G14, G16, G17, G17b) is **1,306 of 2,065 (63.2%)** of the screen band. G03 and G05 wait on their methods.
- Refused at intake (G04, G06, G07, G08, G10, G15) is **394 (19.1%)**.
- G13/G13b, held until P/FFO, is **114 (5.5%)**.
- Stage 2 (G18, G19) is **190 (9.2%)**; wait (G20) is **45 (2.2%)**.
- Not decided (G05b, G16b) is **16 (0.8%)**.
- Unit: companies in the screen band, the boundary in §0. The six groups sum to 2,065.

**Notes the table can't hold:**
- **Two live pages are in an out-of-scope archetype:** ORKA and TECX (G04, both on watch). The intake guard (SP-S1) has to say what happens to them. That is ruling SP-R6.
- **SIC 1311 misfiles a refiner.** PARR is G05 by SIC, but a PV-10 leg has nothing to value at a refiner. SP-S6's signal should key on a reserves disclosure, not on SIC alone.
- **"Conglomerates" has no census signal.** BRK is G08 by SIC 6331, so the guard needs a named list or a rule (SP-R7).
- **G09 keeps the net-debt refusal,** but the anchor block still computes an EDGAR net debt beside it (SP-D14). For G09 that inconsistency survives the out-of-scope guard.
- **Candidate transcript sources (SP-S8, not built).** Two sources are recorded but not read by the pipeline today:
  - company-published transcripts (e.g. MORN's site);
  - EDGAR 8-K item 7.01 written Q&A (MORN's monthly "Investor Questions and Answers" exhibits, an EDGAR read).

  Today the builder reads a transcript only from the name's CIQ manual folder, chosen by file name, and labels every one "CIQ transcript(s)" (findings §11f). Any future use falls under the transcript rule: no public field quotes more than 12 consecutive transcript words, and a driver row quotes none.
- **DVN's and DAC's exports are in; AQN cannot be re-exported.**
  - **DVN's mislabel refusal is cleared.** Its 2026-11-20 quarterly re-export (`a532e1a269`, "Period Type: Quarterly") builds, and the precheck passes with 0 refusals. **Its R1 value is withheld** by the event rule on the multiple's close (W73): the export's newest close is the 2026-09-30 quarter-end, and DVN filed its results 8-K item 2.02 on 2026-11-05. An export carrying a close after that filing would clear it. That export is **optional, not owed**.
  - CIQ has no NYSE:AQN listing (the operator, verbatim: "there's no nyse listing as such"). AQN is therefore **refused: home-market primary listing (CAD capitalisation panel); no US listing in CIQ, per the operator** (SP-D21).
  - **DAC's pack landed (2026-11-20) and passes.** Every sheet is titled "(NYSE:DAC)", every money panel states USD, and the precheck passes with 0 refusals, so TK is not needed. Its R1 declines on SP-D22 (Order 6 below).

---

## 2. Evidence

Each command runs from the checkout root as `python scripts/archetype_probe/<script>.py`, with
`ARCHETYPE_PROBE_WORK` set to a folder outside the checkout (and `ARCHETYPE_PROBE_CIQ` for a script
that reads a CIQ pack). The README there gives every variable. Each script imports `vinci` from the
checkout it runs in and prints `vinci.__file__` first. Every write goes to the work folder, and
every CIQ workbook is copied there, hash-checked and deleted.

| evidence | where | repro | boundary |
|---|---|---|---|
| census and archetype counts | findings §3 | `scripts/archetype_probe/census_fetch.py`, then `classify.py`, `grid.py`, `crosstab.py` | §0 census |
| readiness grid: 20 archetype rows × 14 columns, W/R/X/N per layer, updated in place by 5a and the fresh rerun | findings §6 | `scripts/archetype_probe/probe.py <T …>`, `score.py`, `grid.py`; per-name output under `<WORK>/out/probe/` | 64 probed tickers (61 reached a CIK), cut 2026-11-19 |
| 5a full $0 builds: the precheck plus the page it would write | findings §11a, §11b | `setup5a.py`, then `build5a.py <T>` or `build5a.py <T>:nociq`; output under `<WORK>/out/` | main `9d036cbb`; 16 builds, 13 names |
| fresh-export rerun | findings §11f | `fresh5a.py [T …]`, `variant5a.py`, `bs5a.py`, `aqnhc5a.py`, `morn5a.py`, `morn5a_ctx.py`, `rivn5a.py`, `mornebitda5b.py`; output under `<WORK>/out/` | main `6e03501f`; PLD, AWK, RIVN, MORN, DVN, AQN, plus the DVN variant |
| intake for each out-of-scope kind | findings §11c | `intake5a.py` | main `9d036cbb`; MTB, PCVX, BRK-B, EPD; two states (main as it is; after the two intake steps) |
| D13 on the live corpus | findings §11e | `d13audit.py` | main `2ecf6da0`; 5 pages, 109 candidate records, EPD control |
| defect reach on live pages | §3 below | `pages5b.py` (writes `<WORK>/out/pages5b.json`) | §0 live pages |
| source_refs for the CIQ figures quoted here | §3 below | `cites5b.py` | fresh packs, exported 2026-11-19 |

**What the builds show, in one table.** These are precheck outcomes. A precheck outcome is not a
verdict.

| name | archetype | pack | precheck | the page |
|---|---|---|---|---|
| SPGI (control) | G01 | none | STOP: 2 post-spend refusals, caused by the missing export | — |
| PLD | G13 | 2026-11-19 | **PASS**, 0 refusals | nothing priceable: R1 declines (lease basis unresolved), R3 is refused on STATE row 10, R4 has no bridge (SP-D17) |
| AWK | G14 | 2026-11-19 | **PASS**, 0 refusals | R1 priced (firm); R3 template emits; R4 refused (SP-D17) |
| MORN | G11 | 2026-11-19 | **PASS**, 0 refusals | R1 priced (firm); R3 and R4 templates emit. No transcripts and no Credit Health Panel: **absent at the source** (CIQ carries neither for MORN, per the operator) |
| RIVN | G03 | 2026-11-19 (and 2026-10-28) | REFUSED before any model call (SP-D18) | — |
| DVN | G05 | 2026-11-19 (twice); 2026-11-20 | 2026-11-19: REFUSED before any model call, both times (the quarterly file was the annual one; then an annual export again). **2026-11-20: PASS**, 0 refusals, on a true quarterly re-export | R1 applies, but its value is withheld (W73: its newest close predates its 2026-11-05 results); R1, R3 and R4 templates emit. The 2026-11-19 variant without the bad file passed with nothing priceable (SP-D19) |
| DAC | G17 | 2026-11-20 | **PASS**, 0 refusals; NYSE listing; every money panel USD | R1 declines (SP-D22); R3 refused (STATE row 10); R4 template emits; the diluted count is read |
| AQN | G17b | 2026-11-19 (TSX listing) | REFUSED before any model call: **refused: home-market primary listing (CAD capitalisation panel); no US listing in CIQ, per the operator** (SP-D21) | — |
| PCVX | G04 (out of scope) | 2026-10-28 | 1 refusal (timing) | after a re-export, a fully paid build of a page priced on nothing (SP-S1, SP-S3) |
| MTB, BRK-B, EPD | G06, G08, G15 (out of scope) | none | STOP, export-driven | intake admits each once its roster line is written (findings §11c) |

---

## 3. Defects SP-D1 to SP-D22

**Classes:**
- **wrong**: produces something false;
- **refuses**: fails loud;
- **latent**: wrong in mechanism, but on no live page;
- **label**: true value, false or missing words;
- **doc**: documentation;
- **spend**: lets a paid build run on a page that can't be priced.

**"Live"** = the 26 pages at main `6e03501f`, by the signature named (`pages5b.py`), with every
page listed.

| ID | defect, in plain words | class | live pages | repro | smallest fix | order |
|---|---|---|---|---|---|---|
| SP-D1 | REIT revenue: the ASC 606 tag is only a component, and lease revenue is not read, so a one-year component is taken as total revenue (INVH printed a 192% margin) | wrong; latent | 0 (no G13/G13b page) | `probe.py INVH O VMRK` | refuse R1 for a lease-revenue filer until a REIT basis exists (covered by SP-S2's refusal) | 1 |
| SP-D2 | a transformed business passes the margin gate on its predecessor's years (NBIS: Yandex → Nebius, 2024) | wrong; latent | 0 FPI pages | `probe.py NBIS` | refuse when a revenue-tag conflict covers the recent years | 1 |
| SP-D3 | SIC 6211 holding companies with a bank book get a net debt (SCHW −$12.85bn) | wrong; latent | 0 SIC-6211 pages | `probe.py SCHW` | refuse at intake (SP-S1); in the module, test SIC 6211 together with a `Deposits` line | 1 |
| SP-D4 | debt carried in tags the builder doesn't read, so net debt is refused (CME `UnsecuredLongTermDebt`, ORCL `LongTermNotesAndLoans`, O/VMRK `NotesPayable`) | refuses | 0 found by this signature | `probe.py CME ORCL O VMRK` | widen the core debt tags, each measured on the corpus | 2 |
| SP-D5 | a debt-free company's net debt is refused, not taken as −cash | refuses | **2: ORKA, TECX** (both watch, G04): EDGAR's net debt refused, CIQ's balance sheet used | `probe.py ISRG TPL PCVX VKTX`; `pages5b.py` | after ruling SP-R1, apply B's proposed rule | 2 |
| SP-D6 | no current cover share count for multi-class or co-registrant filers | refuses | **3: FUBO, NKE, V** use CIQ's comps count instead of EDGAR's cover count | `probe.py EL HSY BRK-B NEE`; `build5a.py PLD:nociq` | read per-class and per-registrant counts from the filing's instance | 2 |
| SP-D7 | `OperatingIncomeLoss` untagged, so R1's margin falls back to CIQ's financial summary (weak) | refuses (weak) | **3: BURL, LLY, NKE** (anchor margin "financial_summary (short history)") | `probe.py LLY PFE AJG`; `pages5b.py` | a stated derivation with a basis label, or accept the CIQ fallback as designed | 2 |
| SP-D8 | every 6-K outdates a CIQ export, so an FPI's export lives about a week (NVO 6d, TSM 7d, BABA 7d, NBIS 8.5d, FNV 12d) | refuses (over-refusal) | 0 FPI pages | `probe.py NVO TSM BABA NBIS FNV` | refuse only on a 6-K carrying an earnings release or interim statements (the adopted rule; detection in SP-R2) | 6 |
| SP-D9 | a successor registrant starts with no history (XOM's new CIK) | refuses | 0 | `probe.py XOM` | stitch predecessor companyfacts across an 8-K12B succession | — (G20 waits) |
| SP-D10 | the IFRS fiscal year can be a year stale in companyfacts (TSM) | refuses | 0 | `probe.py TSM`; `fpi_facts.py` | read the instance (STATE row 4's FPI1c) | — (stage 2) |
| SP-D11 | `vinci dossier precheck` ends in a traceback, not its own refusal line, when a CIQ loader refuses: `CiqPreliminaryError` (PLD's and MTB's 2026-10-28 packs), `CiqMislabelledError` (DVN), `CiqCurrencyError` (AQN). Nothing is spent | refuses (in the wrong form) | n/a (a tool's output, not a page field) | `build5a.py PLD MTB`; `fresh5a.py DVN AQN` | catch the CIQ loader's refusal classes beside the three `prespend.run` already catches | 1 |
| SP-D12 | a loss-maker with no EV/EBITDA band reads `unknown`, never `R2_NEEDED`: the band gate runs before the margin gate that routes to R2 | refuses (routing) | **3: FUBO, ORKA, TECX** (anchor `unknown`, "own-history multiple missing") | `build5a.py RIVN:nociq CRWV`; `pages5b.py` | route on the margin when the band is absent for NM reasons | 3 |
| SP-D13 | the P/E note "a more recent annual figure exists and is negative" fires without checking that the figure exists (EPD's tag stops at FY2011) | wrong; **latent** | 5 pages print it (CNXC, FUBO, TECX, WERN, WLK), and it is **TRUE on all 5** (audit at `2ecf6da0`; of 109 candidate records, 107 TRUE, 2 OTHER, 0 FALSE) | `d13audit.py` | split the branch: "a later year exists and is negative" vs "the tag stops at <year>" | 1 |
| SP-D14 | the anchor computes an EDGAR net debt for a bank, lender or insurer that `leverage_survival` refuses on the same page (MTB $3,883M; JSON only) | wrong (contained) | 0 bank pages. **Survives for G09**, which is in scope with the refusal kept | `build5a.py MTB:nociq` | apply the SIC rule in the anchor's bridge | 1 |
| SP-D15 | RUNBOOKS §i step 1's follow-entry example lacks `followed_since`, which `vinci.followed` requires | doc | n/a | read `docs/RUNBOOKS.md` §i against `vinci/followed.py` | add the field to the example | 7 |
| SP-D16 | the anchor's diluted share count reads a 10-Q quarter only, so a 20-F filer never has one (NBIS) | refuses | 0 | `build5a.py NBIS` | an FPI branch: the 20-F's annual diluted weighted average, labelled annual | 6 |
| SP-D17 | the EV bridge reads only CIQ's subtotal 'Total Cash & ST Investments', which CIQ's **Real Estate** and **Utility** balance-sheet templates do not carry, so R4 is unpriceable because of the sheet's form (detail below) | refuses (selects on form) | 0 (no live page uses those templates; MORN and RIVN carry the row) | `fresh5a.py PLD AWK`; `bs5a.py PLD AWK MORN RIVN`; `cites5b.py` | build the cash leg from its parts when the subtotal is absent (`ciq_balance._CASH_PARTS` already lists them), pinned on both real sheets | 2 |
| SP-D18 | RIVN's LTM refusal is caused by CIQ's own data, so no re-export clears it (detail below) | refuses (correctly; durable) | 0 (RIVN has no page) | `fresh5a.py RIVN`; `rivn5a.py`; `cites5b.py` | a reviewed tie-break mapping, or a ruling (SP-R3). Not a re-export | 3 |
| SP-D19 | a missing **required** CIQ export raises a caveat, never a refusal: a DVN variant without its quarterly Financials passes the precheck, and its anchor stops at "own-history multiple missing" | spend | 0 pages carry a "pull CIQ" required-export caveat | `variant5a.py` | a precheck refusal, or a verdict line, when a module required for the sleeve is absent | 1 |
| SP-D20 | two CIQ EBITDA definitions on one page, each consumed consistently, but the page calls CIQ's annual figure "reported LTM EBITDA" and the LTM check reports a DIFFER with no cause (detail below) | label (no value wrong) | the label is on **20 pages** (every page with `ev_ebitda_basis`). Of the 17 that also carry a filing-rebuilt EBITDA, the "reported" figure is within 2% of it on 7 and beyond 2% on 10 | `mornebitda5b.py`; `pages5b.py` | name the cause when annual EBITDA plus annual 'Other Amortization' equals the four quarters; relabel "reported" as "CIQ annual, pre-rent". **Live label; may be fixed before review, per the operator** | 1 |
| SP-D21 | a foreign filer whose CIQ primary listing is a home-market listing gets that market's currency in its quarterly Historical Capitalization panel, so `CiqCurrencyError` refuses its whole pack, though it reports US GAAP in USD (detail below). No re-export cures it: AQN is **refused: home-market primary listing (CAD capitalisation panel); no US listing in CIQ, per the operator** | refuses (over-refusal), and a label: the refusal calls a USD workbook "a foreign-currency workbook" | 0 FPI pages. The population at risk **can't be counted from the data held**: 0 of 76 G17/G17b names show a non-US venue in EDGAR's `exchanges`. Proxies: 7 file 40-F, 7 are incorporated in Canada, 13 carry an ADS line | `fresh5a.py AQN`; `aqnhc5a.py`; `cites5b.py` | **Conversion** at a dated rate waits on SP-R5's FX ruling. **Smaller still, needing no ruling:** refuse the panel, not the pack (its only page-path reader is the ex-lease band) | 6 |
| SP-D22 | **a lessor with no CIQ rent row is treated as having material rent, so R1 declines on the form of its statements.** With no 'Net Rental Exp.' row in CIQ's annual income statement, the lease check reads rent as material (`lease_basis._materiality`); the ex-lease band then needs CIQ's lease rows to reconcile to EDGAR's, and on a lessor there is nothing to reconcile, so R1 declines (detail below) | refuses (selects on form) | **0 of the 26 committed pages** at main `6c22b222` carry the "rent could not be measured" text | `fresh5a.py DAC`; `fresh5a.py PLD` | when CIQ states no rent row, measure rent from EDGAR (`OperatingLeaseCost` / `LeaseCost`), read a filer with no lessee-lease tag as immaterial and say so, and refuse only when EDGAR cannot decide either | 2 |

**SP-D17 in detail.** Fresh packs, knowable 2026-11-19.
- **PLD** (Financials_Quarterly `d360d90d26`, Balance Sheet, header "Template: Real Estate"). 'Total Cash & ST Investments' is **absent** from the sheet. At column 39 [Q3 Sep-30-2026]: 'Cash And Equivalents' row 23 = 2,273.497; 'Total Debt' row 74 = 37,490.782; 'Net Debt' row 75 = 35,200.599.
- **AWK** (Financials_Quarterly `c5844ae7d9`, Balance Sheet, header "Template: Utility"). The row is **absent**. At column 39 [Q3 Sep-30-2026]: 'Cash And Equivalents' row 17 = 121.0; 'Short Term Investments' row 18 = 29.0; 'Total Debt' row 80 = 16,427.0; 'Net Debt' row 81 = 16,277.0.
- AWK's parts reconcile to CIQ's Net Debt exactly (16,427.0 − 121.0 − 29.0). PLD's are 16.7 apart, a gap the rows shown don't explain.

**SP-D18 in detail.**
- **CIQ, annual** (Financials_Annual `a710dc0303`, Income Statement, row 41 'Gain (Loss) On Sale Of Invest.'): column 7 [12 months Dec-31-2025] = '-'; column 8 [LTM 12 months Sep-30-2026] = 405.0.
- **CIQ, quarterly** (Financials_Quarterly `4835b5b653`, Income Statement, row 42): column 24 [Q4 Dec-31-2025] '-'; column 25 [Q1 Mar-31-2026] 506.0; columns 26–27 [Q2, Q3 2026] '-'.
- Both knowable 2026-11-19. The 2026-10-28 pack refused on the same row; its cells are not quoted here, because its hashes were not recorded.
- **The filings side with the quarterly export.** RIVN's 10-Qs tag `IncomeLossFromEquityMethodInvestments` 101.0 for Q1, 6M and 9M 2025 and 506.0 for Q1, 6M and 9M 2026 (0001874178-26-000035, -000054, -000066). The FY2025 10-K tags no FY figure under that concept, so Q4 2025 is not decided.
- The guard is right to refuse. The tie-break can't decide it, because no reviewed mapping exists for this CIQ row.

**SP-D20 in detail.** MORN, knowable 2026-11-19.
- **CIQ annual LTM** (Financials_Annual `fef17b2405`, Income Statement row 80 'EBITDA', column 10 [LTM 12 months Sep-30-2026]) = 719.4. That is EBIT (row 82, column 10: 616.7) plus annual Cash Flow row 20 'Depreciation & Amort., Total' (column 10: 102.7). It **excludes** Cash Flow row 22 'Other Amortization' (column 10: 102.7).
- **CIQ quarterly** (Financials_Quarterly `b23ba84d1d`, Income Statement row 82 'EBITDA', columns 36–39 [Q4 2025 to Q3 2026]) = 187.6 + 206.7 + 207.3 + 220.5 = 822.1. Each quarter adds back all of D&A.
- 719.4 + 102.7 = 822.1 exactly.
- **Filed:** `OperatingIncomeLoss` LTM 643.5 plus `DepreciationDepletionAndAmortization` LTM 205.4 = 848.9 (10-K 0001289419-26-000013; 10-Qs 0001289419-26-000025, -000041, -000054).
- **Every consumer divides on its own basis, so no value is wrong:** R1's ex-lease band and exit EBITDA both use all D&A; the headline basis check reads the annual figure, as CIQ's own multiple does.

**SP-D21 in detail.** AQN, knowable 2026-11-19.
- **The CAD panel** (Financials_Quarterly `76c40e0928`, Historical Capitalization): the header reads "In Millions of the trading currency" and "Currency: Trading Currency"; the 'Currency' row (row 15, column 35 [Q3 Sep-30-2026]) = CAD.
- **The same workbook's Income Statement** reads "In Millions of the reported currency", and its 'Currency' row (row 15, column 35) = USD. 17 of the pack's 18 money panels state USD.
- **Who reads the panel.** Its only page-path reader is `lease_basis.observations` (`lease_basis.py:301`, TEV for the ex-lease band). The CIQ quality scorecard cross-checks it; nothing else on the page path reads it. Searched: `Historical Capitalization`, `Historical Capitalisation`, `hist_cap`, `historical_cap`, and `git log -S"Historical Capitalization" -- vinci`.
- **The two fixes.**
  - **Refuse the panel, not the pack.** `lease_basis` refuses its band with the stated currency, and every other panel is read. Where rent is immaterial, R1 never needed the panel; where it is material, R1 declines. Whether AQN's rent is material was not measured, because its pack was refused before its page.
  - **Convert each column at a dated rate**, using its 'Pricing as of' date. This needs SP-R5.

**SP-D22 in detail.**
- **DAC** (2026-11-20 pack): EDGAR tags no lessee lease cost and no operating-lease liability for DAC at all. It tags $945.8M of lease payments it will *receive* in 12 months (it leases out ships), against FY2025 operating income of $498.8M and D&A of $163.4M (20-F 0001104659-26-021574). Its rent is very likely immaterial, yet R1 is refused: 0 quarters reconcile CIQ's lease rows to EDGAR (≥4 needed).
- **PLD** (2026-11-19 pack): the same path ("rent could not be measured … treated as material", then no usable ex-lease current).
- **Live pages:** none of the 26 committed pages at main `6c22b222`.
- Same family as SP-D17: the refusal follows a row the template does not carry.

---

## 4. Orders (build batches)

A suggested shape. Rough PR counts are **VERIFY-AT-BUILD**.

**On test pages.** Each order names its **frozen** test pages per archetype: fixtures cut from real
data and frozen, where value-level pins live (CLAUDE.md test-layer rule). B's brief said none of
today's 26 pages serves a new archetype. Measured, 4 of the 26 are outside G01/G02: FUBO (G03),
ORKA and TECX (G04), PARR (G05 by SIC). None is G09, G11–G14, G16 or G17, so every in-scope
archetype other than G01–G03 needs a new fixture.

### Order 1: stop the wrong outputs; refuse out-of-scope names before any model client

| ID | item |
|---|---|
| **SP-S1** | **The out-of-scope intake guard**, at `coverage_roster.require_buildable` / `assemble.load_finalists`, before `AnthropicLlmClient` is constructed. It refuses G04, G06, G07, G08, G10 (SIC 6211 with a bank book included), BRK and the conglomerates list (SP-R7), G15 (SP-R4), G16b and G05b as SP-R9 rules, and stage-2 and wait names (G18, G19, non-SEC, G20). Each refusal names the archetype and the ruling. Measured today: nothing at intake reads the archetype, and once a roster line exists a bank, a biotech, BRK or an MLP reaches the paid phases (findings §11c) |
| **SP-S2** | **G13/G13b refused until P/FFO**, keyed on SIC 6798 and 65xx **and** on `RealEstateInvestmentPropertyNet` ≥ 50% of assets, so INVH-type REITs are caught. Lifted by SP-S5 |
| **SP-S3** | **The precheck states "nothing priceable"** when no recipe template can be emitted on the $0 page: PLD (fresh pack), PCVX (re-exported), the DVN variant. Whether that is a verdict line or a refusal is open (SP-R8) |
| SP-D1, SP-D2, SP-D3, SP-D11, SP-D13, SP-D14, SP-D19, SP-D20 | as in §3 |

- **Done when:**
  - every out-of-scope frozen test name is refused before a model client exists;
  - the in-scope controls still pass the precheck;
  - each wrong-output pin fails on main before its fix and passes after;
  - the 26 live pages move only as SP-R6 rules.
- **Frozen test pages:**
  - refused: MTB (G06), SYF (G07), BRK-B (G08), SCHW (G10, SP-D3), PCVX (G04), EPD (G15, SP-D13), PLD (G13), INVH (G13b, SP-D1), NBIS (SP-D2), MTB (SP-D14);
  - must still pass: SPGI (G01), AWK (G14), MORN (G11, SP-D20);
  - the DVN variant (SP-D19).
- **Cost:** 4–6 PRs.
- **Depends on:** SP-R6, SP-R7, SP-R8, SP-R9 (all ruled). Not on any other order.

### Order 2: widen the proven path

| ID | item |
|---|---|
| SP-D4, SP-D5 (after SP-R1), SP-D6, SP-D7, SP-D17, SP-D22 | as in §3 |

- **Done when:** each name below reaches the layer its defect blocks on a frozen fixture, and the live pages SP-D5, SP-D6 and SP-D7 touch (ORKA, TECX; FUBO, NKE, V; BURL, LLY, NKE) are re-measured, with each move stated.
- **Frozen test pages:** CME, ORCL (SP-D4); ISRG, TPL (SP-D5); EL, HSY, NEE (SP-D6); LLY, PFE, AJG (SP-D7); AWK's and PLD's quarterly balance sheets (SP-D17); DAC and PLD (SP-D22).
- **Cost:** 5–7 PRs.
- **Depends on:** SP-R1, for SP-D5 only.

### Order 3: R2 for loss-makers

| ID | item |
|---|---|
| **SP-S4** | **The R2 recipe** (STATE row 10), with the anchor's routing fixed so a loss-maker can reach it |
| SP-D12, SP-D18 (after SP-R3) | as in §3 |

- **Done when:** RIVN, CRWV and FUBO route to R2 and emit an R2 template on frozen fixtures, and RIVN's refusal is settled as SP-R3 rules.
- **Frozen test pages:** RIVN (G03, SP-D18), CRWV (G03), FUBO (G03, live, watch), NCNO (reaches `R2_NEEDED` through its band today).
- **Cost:** 3–5 PRs, plus R2's method design.
- **Depends on:** SP-R3; STATE row 10, where R3's template still reads R1's `applicable` bit.

### Order 4: the REIT recipe

| ID | item |
|---|---|
| **SP-S5** | **A P/FFO recipe** for G13/G13b. FFO appears nowhere in `vinci/**/*.py` (findings §2, B8). Lifting SP-S2 waits on it |

- **Done when:** PLD, O, VMRK and INVH each emit a P/FFO template on frozen fixtures, and SP-S2 is lifted for them.
- **Frozen test pages:** PLD, O, VMRK, INVH, PEB.
- **Cost:** 3–5 PRs, plus a method choice for the operator (which FFO, and where it is read).
- **Depends on:** Order 1 (SP-S2), SP-D1, SP-D17.

### Order 5: the PV-10 leg

| ID | item |
|---|---|
| **SP-S6** | **A PV-10 leg** for G05, keyed on a reserves disclosure rather than SIC alone (PARR) |

- **Done when:** DVN and FCX carry the leg on frozen fixtures, and PARR's classification is decided.
- **Frozen test pages:** DVN (its 2026-11-20 quarterly re-export builds; no longer pending), FCX, CRK.
- **Cost:** 2–4 PRs, plus the method.
- **Depends on:** SP-D7 (DVN's operating income has been untagged since FY2016). DVN's re-export is in hand (2026-11-20).

### Order 6: FPI, US GAAP, USD

| ID | item |
|---|---|
| **SP-S7** | **The G17/G17b path**: the D2 refusal (Order 1), the D8 6-K rule and the D16 count |
| SP-D8 (after SP-R2), SP-D16, SP-D21 | as in §3 |

- **Done when:**
  - DAC and NBIS build at $0 on frozen fixtures;
  - AQN's pack is no longer refused whole for one panel (SP-D21's FX-free fix), or is converted after SP-R5;
  - a 6-K without an earnings release no longer outdates an export;
  - the 20-F's diluted count is read and labelled annual.
- **Frozen test pages:**
  - **DAC**, the substitute G17 name. **Its export is in hand (2026-11-20) and builds at $0.**
    - **What it tests:** the 6-K event rule (SP-D8: DAC's two 6-Ks since August predate the export, so the pass is correct); the US listing and USD panels.
    - **What it does not:** SP-D21 (its panels are USD); SP-D16 (DAC furnishes quarterly XBRL on 6-K, so its diluted count is read; NBIS stays the SP-D16 case).
    - **R1** prices only after SP-D22.

    Evidence that picked it: a 20-F filed 2026-02-27; us-gaap-only USD companyfacts; operating income $540.9M (CY2024) and $498.8M (CY2025) in SEC frames; NYSE the only venue EDGAR lists; no ADS line; incorporated in the Marshall Islands; no census overlap flags; 3 6-Ks in 180 days. Not in the data: that CIQ's primary listing is NYSE. The first check on its pack, the export's title "(NYSE:DAC)" and the Historical Capitalization 'Currency' row (USD), passed on 2026-11-20, so TK is not needed.
  - AQN, frozen as SP-D21's refusal case.
  - NBIS.
- **Cost:** 3–5 PRs.
- **Depends on:** SP-R2; SP-D22 for DAC's R1; SP-R5 for SP-D21's conversion route only. DAC's export is in hand.

### Order 7: documentation

| ID | item |
|---|---|
| SP-D15 | as in §3 |

- **Done when:** the RUNBOOKS example passes `vinci.followed`'s own check.
- **Cost:** 1 PR.

### Not in an order

| ID | why not |
|---|---|
| SP-D9 | G20 waits |
| SP-D10 | stage 2 |
| **SP-S8** | candidate transcript sources (§1). Recorded, not built |

---

## 5. Rulings

The operator ruled on 2026-11-19, verbatim: "Approve the defaults", in answer to "Approve the
pack's ruling defaults (SP-R1 to R9, K-1 left open)?". Those eight defaults are the operator's
rulings. **SP-R4 was ruled on 2026-11-20**: asked "Rule SP-R4: keep MLPs (K-1 issuers) out of scope for stage 1?", the operator answered, verbatim,
"Yes, keep them out". All nine are now ruled. **Who drafted them:** SP-R1 and SP-R4 quote the adopted
step-5 text (§1); B drafted SP-R9's defaults; the probe drafted the rest.

| ID | question | default | operator ruling | unblocks |
|---|---|---|---|---|
| SP-R1 | D5: when is a company debt-free? | the adopted text: "count debt as zero only when the 10-K's balance sheet has no debt line and its notes show no borrowing. The page then says "no debt reported in the 10-K". Otherwise it refuses." | adopted as the recommended default, 2026-11-19 ("Approve the defaults") | SP-D5 |
| SP-R2 | D8: how is a "results" 6-K detected? The rule itself is adopted | a 6-K is a results event when its exhibit index lists an EX-99 whose description or first heading names results, an earnings release or interim financial statements. A 6-K whose index can't be read counts as a results event (fail closed) | adopted as the recommended default, 2026-11-19 ("Approve the defaults") | SP-D8 |
| SP-R3 | D18: may the filing decide RIVN's row? | add a reviewed mapping of CIQ 'Gain (Loss) On Sale Of Invest.' to `IncomeLossFromEquityMethodInvestments`, measured on RIVN, so the filing decides for the quarterly side. The refusal stays wherever the filing can't decide | adopted as the recommended default, 2026-11-19 ("Approve the defaults") | SP-D18 |
| SP-R4 | K-1 names (G15) | the adopted text: "K-1 names: your call on whether the fund holds MLPs." Until it is ruled, G15 stays refused at intake | **ruled 2026-11-20: G15 out of scope for stage 1, refused at intake** (asked "Rule SP-R4: keep MLPs (K-1 issuers) out of scope for stage 1?"; answered "Yes, keep them out") | SP-S1 (G15) |
| SP-R5 | stage 2's FX | no FX conversion in stage 1. Before any non-USD figure is read, stage 2 rules on the rate source and the date convention (period-end for balances, period average for flows; a market-data panel at its own 'Pricing as of' date) | adopted as the recommended default, 2026-11-19 ("Approve the defaults") | stage 2; SP-D21's conversion route |
| SP-R6 | the two live pages in an out-of-scope archetype (ORKA, TECX; G04, both on watch) | they stay frozen on watch, as committed. The guard refuses any move back to active and any paid rebuild | adopted as the recommended default, 2026-11-19 ("Approve the defaults") | SP-S1 |
| SP-R7 | which names are "conglomerates"? | a named list, BRK-A and BRK-B, until a rule is proposed and measured | adopted as the recommended default, 2026-11-19 ("Approve the defaults") | SP-S1 |
| SP-R8 | is "nothing priceable" a verdict line or a refusal? | a verdict line with its own exit code. The operator still chooses to spend | adopted as the recommended default, 2026-11-19 ("Approve the defaults") | SP-S3 |
| SP-R9 | G05b and G16b, which the adopted text does not decide | G05b (no USD frame data; 15 screen band, 3 large-cap): classify each by its own filing at intake and follow its real archetype, refusing loudly where facts are missing. G16b (HASI; 1 screen band): out of scope as a financial investment company, refused at intake | adopted as the recommended default, 2026-11-19 ("Approve the defaults") | SP-S1 |

---

## 6. What this pack does not claim

- **That any archetype will earn its coverage.** Nothing here reads a forward return or an outcome. Scope is set by whether the pipeline can build and price a page, not by what would have paid.
- **That the census predicts a page's recipe.** G03 is a proxy; TTWO and CRWV disagree with the anchor's own routing. Frames are not point-in-time.
- **That readiness holds for every name in an archetype.** Each row of the grid rests on 1 to 12 probed names (findings §5).
- **That a passing precheck means a priceable page.** PLD passes and prices on nothing.
- **How many FPIs SP-D21 reaches.** CIQ's primary listing is in none of the data held, so only proxies are given (7 40-F filers, 7 incorporated in Canada, 13 with an ADS line, of 76 G17/G17b).
- **That D20's cause on other live pages is known.** The annual-vs-quarters EBITDA gap shows on BRBR, WLK, CNXC and IT, and its cause there was not read.
- **Anything from MORN's website.** It was not fetched. The EDGAR written Q&A was found, not read as commentary.
- **That the scripts' outputs are part of this pack.** The scripts take every machine path from the environment and import `vinci` from the checkout they run in (`scripts/archetype_probe/README.md`). They were run at $0. Their outputs are not committed: they regenerate, and a re-run at a newer main or on a re-exported pack measures a different boundary.
- **Any cost or count outside its stated boundary.** PR counts are guesses, VERIFY-AT-BUILD.

---

## 7. Scope block and starting log, for logging a reply

```fix-log-scope
1: SP-S1 SP-S2 SP-S3 SP-D1 SP-D2 SP-D3 SP-D11 SP-D13 SP-D14 SP-D19 SP-D20
2: SP-D4 SP-D5 SP-D6 SP-D7 SP-D17 SP-D22
3: SP-S4 SP-D12 SP-D18
4: SP-S5
5: SP-S6
6: SP-S7 SP-D8 SP-D16 SP-D21
7: SP-D15
—: SP-D9 SP-D10 SP-S8 SP-R1 SP-R2 SP-R3 SP-R4 SP-R5 SP-R6 SP-R7 SP-R8 SP-R9
```

That is 8 scope items, 22 defects and 9 rulings: 39 IDs, every one `open`.

**§5 carries the operator's rulings; this log carries TeamNostra's review.** So the ruling IDs
stay `open` here, because the log's five statuses record the reply to the pack, not the operator's
ruling.

| ID | Order | Status | Commit or PR | Test | Pages rebuilt |
|---|---|---|---|---|---|
| SP-S1 | 1 | open | | | |
| SP-S2 | 1 | open | | | |
| SP-S3 | 1 | open | | | |
| SP-D1 | 1 | open | | | |
| SP-D2 | 1 | open | | | |
| SP-D3 | 1 | open | | | |
| SP-D11 | 1 | open | | | |
| SP-D13 | 1 | open | | | |
| SP-D14 | 1 | open | | | |
| SP-D19 | 1 | open | | | |
| SP-D20 | 1 | open | | | |
| SP-D4 | 2 | open | | | |
| SP-D5 | 2 | open | | | |
| SP-D6 | 2 | open | | | |
| SP-D7 | 2 | open | | | |
| SP-D17 | 2 | open | | | |
| SP-D22 | 2 | open | | | |
| SP-S4 | 3 | open | | | |
| SP-D12 | 3 | open | | | |
| SP-D18 | 3 | open | | | |
| SP-S5 | 4 | open | | | |
| SP-S6 | 5 | open | | | |
| SP-S7 | 6 | open | | | |
| SP-D8 | 6 | open | | | |
| SP-D16 | 6 | open | | | |
| SP-D21 | 6 | open | | | |
| SP-D15 | 7 | open | | | |
| SP-D9 | — | open | | | |
| SP-D10 | — | open | | | |
| SP-S8 | — | open | | | |
| SP-R1 | — | open | | | |
| SP-R2 | — | open | | | |
| SP-R3 | — | open | | | |
| SP-R4 | — | open | | | |
| SP-R5 | — | open | | | |
| SP-R6 | — | open | | | |
| SP-R7 | — | open | | | |
| SP-R8 | — | open | | | |
| SP-R9 | — | open | | | |

---

## 8. Found since the pack, not in its orders

Each item has one plain line, with its owner and status as of this amendment (2026-11-20). They are
listed so a reviewer sees them beside the pack; none is an SP ID. **Their statuses at send time go
in the cover note.**

| item | owner | status as of 2026-11-20 |
|---|---|---|
| **W84**: an ex-lease quarter whose report was released the same day is priced at the first close after its filing | A | open (STATE §5.0 row 10; no PR) |
| **W85**: a counterparty's Key Developments news is not the company's catalyst (the Lyft rows on GOOGL, UBER and AMZN) | B | open (STATE §5.0 row 10: "not fixed here") |
| **W86**: a 10-K's Exhibit 21 as a one-sided test of a filer's own units | A | PR #1152, open |

