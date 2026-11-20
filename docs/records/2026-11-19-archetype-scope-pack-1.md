---
status: open
date: 2026-11-19
prs: []
---

# Archetype scope pack 1 is committed for TeamNostra's audit: 2,931 companies counted into 24 archetypes, the operator's adopted coverage, 21 defects and 9 rulings (8 ruled), as 38 IDs in seven orders ($0; docs + scripts)

**WHAT.** Four additions; nothing under `vinci/` changes.
- **`docs/scope-pack-archetypes-1.md`, the pack.** In the shape of fix request 2's log:
  - IDs: 8 scope items `SP-S1..S8`, 21 defects `SP-D1..D21`, 9 rulings `SP-R1..R9`;
  - seven build orders, each with a done-when, frozen test pages per archetype, a rough PR count (VERIFY-AT-BUILD) and its dependencies;
  - a `fix-log-scope` block and a six-column log, every ID `open` for TeamNostra's reply. The log stays a plain table; a lint like `tests/test_fix_log.py` comes when the reply is taken in.
- **`docs/scope-pack-archetypes-1-findings.md`, the evidence**, scrubbed for this public repo:
  - no local paths, emails, credentials or machine names;
  - CIQ values only with their cell (workbook sha256[:10], sheet, row, column), knowable 2026-11-19; every other CIQ value is marked withheld;
  - no transcript words, and no other party's text beyond an ID.
- **`scripts/archetype_probe/`: 35 scripts and a README.** Every machine path is an environment variable (`ARCHETYPE_PROBE_WORK`, `_CIQ`, `_CIQ_PACKS`, `_SEC_CACHE`, `_DOTENV`). Each script imports `vinci` from the checkout it sits in and refuses any other. No output is committed.
- **STATE.md §5.0 row 4** gains one pointer to this record. §5.0 is at its 60-line cap, so no row was added (below).

**The operator's words, verbatim, in order (2026-11-19):**
1. The brief that started the probe: "US-first with large-cap Europe & international names in top 5 public markets countries as next stage", and "start the taxonomy and probe in a fresh session".
2. "adopt and start 5a": the step-5 coverage, adopted, quoted whole in the pack's §1 with its "[…]" elisions marked.
3. Two facts the pack records as findings, not as to-dos:
   - "MORN doesn't have earnings transcript and credit health on ciq, they do have typed transcript available on their website";
   - "there's no nyse listing as such" (AQN).
4. "Approve the defaults", answering "Approve the pack's ruling defaults (SP-R1 to R9, K-1 left open)?". So SP-R1–R3 and R5–R9 are ruled, and SP-R4 (K-1) stays open.
5. "Commit it", answering "Commit the scope pack to the repo for TeamNostra to audit?".

**WHY.** Scope decides what intake admits. Measured at main `9d036cbb`: **nothing at intake reads the archetype**. Once its roster line is written, a bank, a pre-revenue biotech, BRK or an MLP reaches the paid phases (findings §11c), and PCVX would be paid for in full on a page priced on nothing. So the pack declares, per archetype, what is in scope, refused, stage 2 or waiting, with each one's classifying signal and count. It names the defects each expansion meets, and orders the builds. TeamNostra audits commits, so the pack is one exact commit.

**HOW VERIFIED.**
- **Real runs, all at $0** (no model client; EDGAR and FINRA through the repo's clients; Polygon only through `vinci refresh`):
  - the census of both committed universes;
  - a per-layer probe of 64 tickers;
  - 16 full `prespend` builds at main `9d036cbb`, and 8 more on the 2026-11-19 exports at `6e03501f` (six names, the DVN variant, and DVN's re-export);
  - the D13 audit (5 pages and 109 candidate records, at `2ecf6da0`);
  - the defect-reach scan of the 26 committed pages.
- **The parameterised scripts were re-run at this branch's base, main `ac3c9479`, from the checkout root, and reproduce their earlier outputs:**
  - `pages5b.py`: the same 26 pages, archetypes, statuses and defect signatures as at `6e03501f` (its JSON compared whole);
  - `aqnclass5b.py`: 76 / 0 / 7 / 7 / 13;
  - `g17pick5b.py`: DAC's and TK's rows;
  - `xls_headers5b.py DVN`: both of DVN's Financials files read "Period Type: Annual";
  - `cites5b.py`: every cited cell;
  - `fresh5a.py MORN`: precheck PASS, 0 refusals, the same input record `inputs-0ce590dedda09330`.
- **Checks:**
  - `ruff check scripts/archetype_probe` is clean (the gate's ruff covers `vinci tests frontend` only);
  - the full gate (`bin/commit`) ran green;
  - a scan of the full diff found no local path, email or secret;
  - the pack's scope block and log agree on 38 IDs, each in one order.

**BOUNDARY.**
- **Census:** the screen band `universe_snapshot.jsonl` as of 2026-10-16 (2,065 CIKs) and the large-cap band `theme_universe_snapshot.jsonl` as of 2026-08-24 (928); union 2,931; unit a company (CIK). SIC and forms read from EDGAR submissions on 2026-11-19; SEC frames fetched 2026-11-19, not point-in-time.
- **Live pages:** the 26 committed pages at `6e03501f` and `ac3c9479`.
- **Builds:** a scratch data dir, page reference date 2026-10-16; prices are 16 symbols, 7,914 bars, 2024-11-20 to 2026-11-18.
- **CIQ:** packs dated 2026-10-28, and the operator's 2026-11-19 exports (63 files, each sha-checked; DVN's quarterly re-exported 17:19Z).
- **Every count in the pack and the findings states its own boundary beside it.**

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **§5.0 is at its 60-line cap** (`tests/test_state_open_now.py`, `MAX_LINES = 60`), so this build adds no row. Re-wrapping prose to make room would defeat the cap's purpose. The open items are this record's and the pack's. Row 4, whose FPI path the pack's Order 6 extends, carries the one pointer. A dedicated row waits on a row being closed: the coordinator's or the operator's call.
- **Open, and owed by the operator:**
  - DVN's quarterly Financials, exported with Period Type set to **Quarterly**. Both files on Drive are annual exports; the 17:19Z re-export is `b548221592`;
  - a CIQ pack for **DAC**, the substitute G17 test name, since AQN cannot be re-exported. The first check on its pack: the title reads "(NYSE:DAC)" and its Historical Capitalization 'Currency' row reads USD.

  Both are pending in the pack, and they follow as a small amendment.
- **SP-D20 is live:** the word "reported" is on 20 committed pages, and on 10 of the 17 comparable ones the figure is more than 2% from the filed EBITDA. B is taking it to the operator as a possible fix before review.
- **The scripts are working tools.** A re-run measures its own day's caches, Drive exports and committed data, so each output prints its boundary.
## Amendments

**2026-11-20** — **The PR that carried this record is #1145**, merged 2026-11-20 as `9a30cbac`. This record's `prs:` was left empty at merge, and the amendment contract freezes it. Since the merge (the W87 amendment, `docs/records/2026-11-20-w87-scope-pack-1-amendment.md`):
- DVN's quarterly re-export and DAC's pack landed and were built at $0, so neither export is owed;
- SP-D22 is added to the pack, which now has 39 IDs.

