---
id:
status: shipped
date: 2026-10-11
prs: [707]
supersedes:
superseded-by:
---

# A monitor day reads nothing dated after itself — a re-cut of a past day no longer writes later filings, evidence or decisions into it

**WHAT.** Every DATED input `vinci monitor` reads is now bounded by the session the day is filed
under (`now_date`, the snapshot's `as_of`):
- **Filings.** `monitor.freshness_row` drops every filing dated after its `today`, so newer
  filings, `unread_print` and the next-print estimate read only what was filed by the day. The bound
  sits in the pure function, so it holds for every caller rather than at one fetch site.
- **Evidence dates.** `last_evidence_date(record, as_of=)` ignores an underwrite date or
  `[amended …]` tag after the day; with every date after it, the record states no evidence for that
  day. `evidence_after` names what was dropped, and the CLI writes one note per such record, so a
  missing date never reads as a record that states none.
- **The freshness set and its verdicts** come from `asof_rows`, the ledger as of the day — the same
  point-in-time read the book three blocks up already used. They were drawn from the whole ledger.
- **The anchor is the session, not the calendar `ref`.** The freshness rows (`today=now_date`, was
  `ref`) and the prior-day read (strictly before `now_date`, was `ref`) now take the anchor the
  theme sweep took on review 2026-08-31. A weekend `--ref` flagged Saturday's deadline as passed in
  Friday's file, and read Friday's own file as a prior day of itself.

**WHY.** Re-running `--ref 2026-09-22` on 2026-10-11 wrote IT's 10-08 8-K and WERN's 10-06 and
10-08 8-Ks into the 09-22 day as unread prints: EDGAR answers with everything filed up to the call.
The panel-emit pin forces a re-cut of the latest day whenever a page moves, so this was a standing
route for later information into a dated record (#705 avoided it by writing a new day). Reading the
freshness code for the rest of the list, not assuming it, found the other three: evidence dates,
the freshness set, and the weekend anchor.

**A CORRECTION TO #705's RECORD.** It said #657's 2026-09-29 re-cut "may have" written later
filings into 09-22. It did not: the committed 09-22 day carries no date after itself. The day that
DOES is 2026-07-20 — EPAM's and SMPL's 2026-07-21 underwrites and WERN's 2026-07-21 amendment as its
evidence dates, written by its own re-run on 07-21 (`92feab02`). It is a superseded day,
`write_snapshot` refuses to rewrite it, and it is left as history.

**HOW VERIFIED.** On real data, at `f81eee50` plus this change, each re-cut written to a scratch
directory (never `data/monitor/`) and compared with the committed day:
- **`--ref 2026-09-22`, the observed case.**

  | | before (`main`) | after |
  |---|---|---|
  | filings after the day | 3, in 2 of 9 freshness rows (IT 1, WERN 2) | 0 |
  | freshness block vs the committed day | differs on IT and WERN | identical, 9 of 9 rows |
  | panel rows differing from the committed day | 4 of 124 | 2 of 124 (UBER's, below) |

- **`--ref 2026-10-09`, the latest day:** identical to the committed day in all seven blocks (rows,
  spread, freshness, realized, theme falsifiers, panels, notes). The routine run is unchanged.
- **`--ref 2026-07-20`:** GOOGL (ledgered 2026-08-14) no longer gets a BUY row — 8 freshness rows,
  was 9. No evidence date after the day is written, and all 8 records whose evidence postdates it
  are named in the notes (AORT, BRBR, EPAM, IT, MVST, NCNO, SMPL, WERN).
- **Tests** (`tests/test_monitor_ref_date_bound.py`, 7) on frozen copies of the real IT / WERN /
  GOOGL / EPAM records and the real filing accessions:
  - the pure function: the post-day filings refused, on-day ones kept, the next-print estimate,
    evidence bounded and named;
  - **through the real command** over the real committed ledger: the 09-22 re-cut reproduces the
    committed day's IT and WERN rows exactly; the 07-20 day drops GOOGL and names every postdating
    record; a Sunday `--ref` files Friday without Saturday's deadline or Friday's own file; IT reads
    `watch`, not BUY, on 07-17, before its ledger entry.
- **Mutation:** 8 mutants (each bound removed, `today=ref`, prior days by `ref`, the whole-ledger
  set, the whole-ledger verdict, the note removed), all 8 killed.

**THE PANELS — ASSESSED, NOT REDESIGNED.** What this bound cannot reach is every input read as a
WHOLE DOCUMENT as it stands at the run:
- dossier pages: the panel grid, and the freshness `measured` and `stale_tags`;
- scenario records: legs, triggers, dated triggers, the watch set;
- theme cards, and `followed.json`'s panel declarations.

On the 09-22 re-cut that is UBER's two panels: `multiple_and_price` as of 2026-10-09 (19.48x over
13 closes; the committed day has 19.20x over 12), and `dilution` windowed to 09-22 with 6 prospectus
supplements (committed: to 08-24, 4). Both come from UBER's page re-assembled 2026-10-11 (#705).
None of these documents has a per-item date to filter on. Filtering by the document's own date
drops rather than reconstructs: SMPL was held on 07-20 under a record since re-underwritten
(2026-08-05), and a card re-declared after a day replaces one that was in force on it.

| option | what it does | cost |
|---|---|---|
| **1. rule — a moved page gets a NEW day; a past day is never re-cut** | what #705 did | none in code; rests on the operator, and needs a session after the latest day |
| 2. version — read each document as committed on the day | faithful | the monitor reads git history in every checkout that runs it; "committed on the day" needs a definition; the panel-emit pin would compare against own-date pages, and stop forcing re-cuts at all |
| 3. stamp — each panel names its page's date, the day flags any after itself | honest | still lookahead, now labelled |

**Recommendation: 1 now; 2 only if past days are ever re-cut for analysis.** An operator call,
recorded on STATE §5.0 row 5.

**BOUNDARY.**
- **Re-cuts:** run 2026-10-11 at `f81eee50` (before) and `f81eee50` plus this change (after).
  EDGAR and Polygon were read through the repo's own clients. Compared against the committed
  `data/monitor/<day>.json`.
- **Rows and panels:** "freshness rows" are the day's `freshness` list (9 on 09-22 and 10-09);
  "panel rows" are its `panels` list (124 on 09-22 and 10-09), matched on (ticker, key).
- **Sweep:** "dates after the day" covers `last_evidence_date`, every `newer_filings` date, every
  `passed_trigger_deadlines` deadline and every passed theme deadline. It ran over the 5 committed
  days (`data/monitor/2026-*.json` at `f81eee50`).
- **Excluded from the scan, by design:** future-dated fields — next-print estimates, horizon dates,
  theme deadlines not yet passed.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A record written after a day still puts today's legs and triggers into that day's row.** Only
  its dates are bounded; the note says so on the day. Falsifier: a re-cut day whose row carries a
  trigger with no matching note.
- **Whole-document inputs are unbounded** (above). They wait on the row 5 ruling.
- **The committed 2026-07-20 day keeps its three 07-21 evidence dates.** Rewriting a superseded day
  is an explicit operator act (`rewrite_history`), not a side effect of this fix.
- **Behaviour change on a weekend run:** a deadline or record dated after Friday's session no longer
  reaches Friday's file; it reaches Monday's.
