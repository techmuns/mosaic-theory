---
id:
status: shipped
date: 2026-10-11
prs: [707]
supersedes:
superseded-by:
---

# A monitor day reads nothing dated after itself — a re-cut of a past day no longer writes later filings, evidence or decisions into it

**WHAT.** Every DATED input `vinci monitor` reads is bounded, against TWO named anchors:
- **Filed under the SESSION (`now_date`, the snapshot's `as_of`).** A dated trigger is PASSED
  against it, the next print is estimated from it, and prior monitor days are read strictly before
  it — the anchor the theme sweep took on review 2026-08-31.
- **Reads through the DATE ASKED FOR (`ref`; today on a routine run).** `freshness_row(…,
  known_through=)` drops every filing and every record evidence date after it.
  - A routine run before today's close is filed under the last session, and still flags this
    morning's 8-K.
  - A re-cut of a past day passes that day, and reads only what was filed by then.
  - The EDGAR fetch window is anchored on the same `known_through`, so the fetch and the filter
    cannot drift apart.

**Within that:**
- **Evidence dates are bounded and typed.** `last_evidence_date(record, as_of=)` ignores an
  underwrite date or `[amended …]` tag after the bound. What it drops lands on the row as
  `FreshnessRow.evidence_after_day` (`EvidenceDate(on, source)`), and the day's note is rendered from
  that field, never the other way round.
- **A record stating NO evidence by the bound gets no row**, and the day's notes name it. Its legs,
  triggers and deadlines would all be later ones. A record AMENDED after the day keeps its row, its
  bounded date, and a note that its legs and triggers are today's.
- **The freshness set and its verdicts come from `live_verdicts`:** decisions entered by the
  session and NOT CLOSED by it, the newest winning — the book's own read, closures applied. A name
  with no live decision appears only if its record is a watch, labelled with the record's status.
- **One unreadable date drops ITS row, not the day.** An underwrite date or amendment tag that is
  no ISO date (`2026-02-30` matches the tag) raises `UnreadableEvidenceDateError` naming the record
  and the field. The CLI writes the day without that row, and a note names it — the theme-card
  doctrine.

**WHY.** Re-running `--ref 2026-09-22` on 2026-10-11 wrote IT's 10-08 8-K and WERN's 10-06 and
10-08 8-Ks into the 09-22 day as unread prints: EDGAR answers with everything filed up to the call.
The panel-emit pin forces a re-cut of the latest day whenever a page moves, so this was a standing
route for later information into a dated record (#705 avoided it by writing a new day). Reading the
freshness code for the rest of the list, rather than assuming it, found the others: evidence dates,
the freshness set, and the weekend anchor.

**REVIEW FIXES (same PR, before merge).** A code review of the first cut found seven issues; all
seven are fixed here.
1. **The first cut anchored everything on the session, and so hid a routine run's newest prints.**
   A Monday-morning run is filed under Friday, and it dropped Monday's 07:00 8-K. It now reads
   through `ref`, so the two anchors above are separate.
2. **IT read BUY on every committed day from 08-11**, although its only decision closed on 07-21
   and its record is a watch. The set ignored closures; `live_verdicts` applies them.
3. **A closed-and-re-entered name took its OLDEST verdict** (`next(…)` in ledger order). It now
   takes the newest open one. Nothing showed, because SMPL is BUY on both.
4. **A record written after the day still got a row**, with today's triggers and deadlines. It now
   gets no row, and the day's note names it.
5. **The EDGAR window sat on `ref` while the bound moved to the session.** Both now share
   `known_through`.
6. **The dropped evidence dates existed only as prose in `notes`, and the tests string-matched
   them.** They are now a typed row field, and the note is rendered from it.
7. **A malformed date aborted the whole run, unnamed.** It now drops that record's row, and the day
   names it.

**A CORRECTION TO #705's RECORD.** It said #657's 2026-09-29 re-cut "may have" written later
filings into 09-22. It did not: the committed 09-22 day carries no date after itself. The day that
DOES is 2026-07-20 — EPAM's and SMPL's 2026-07-21 underwrites and WERN's 2026-07-21 amendment as its
evidence dates, written by its own re-run on 07-21 (`92feab02`). It is a superseded day,
`write_snapshot` refuses to rewrite it, and it is left as history.

**HOW VERIFIED.** On real data, each re-cut written to a scratch directory (never `data/monitor/`)
and compared with the committed day:
- **`--ref 2026-09-22`, the observed case.**

  | | before (`main`) | after |
  |---|---|---|
  | filings after the day | 3, in 2 of 9 freshness rows (IT 1, WERN 2) | 0 |
  | freshness block vs the committed day | differs on IT's and WERN's filings | identical except IT's verdict, BUY → watch (fix 2) |
  | panel rows differing from the committed day | 4 of 124 | 2 of 124 (UBER's, below) |

- **`--ref 2026-10-09`, the latest day:** identical to the committed day in every block but one
  field — IT's freshness verdict, BUY → watch. The next routine run will show IT as a watch.
- **`--ref 2026-07-20`:**
  - **2 freshness rows** (IT BUY, open that day; WERN watch). The pre-PR code wrote 9, and the
    committed day holds 4.
  - **The 6 records with no evidence by 07-20 get no row and are named:** AORT, BRBR, EPAM, MVST,
    NCNO, SMPL.
  - **IT and WERN carry their later amendments** in `evidence_after_day`, with a note each.
  - No evidence date after the day is written.
- **Tests** (`tests/test_monitor_ref_date_bound.py`, 11) on frozen copies of the real IT / WERN /
  GOOGL / EPAM records, the real filing accessions, and the real ledger:
  - **pure functions:**
    - the filing bound;
    - the two anchors;
    - the next-print estimate;
    - evidence bounded and typed;
    - the unreadable date refused by name;
    - `live_verdicts` over the real ledger: IT gone after its close, and the newest open decision
      winning on a derived two-open SMPL;
  - **through the real command:**
    - the 09-22 re-cut reproduces the committed day's IT and WERN filings and evidence dates, and
      IT reads watch;
    - 07-20 holds no record written after it;
    - a Monday run before the close still flags Monday's 8-K, keeps a Monday record, and does not
      pass a Monday deadline;
    - a Sunday `--ref` files Friday without Saturday's deadline or Friday's own file;
    - one unreadable record drops its row, not the day.
- **Mutation:** 12 mutants on the final code, all 12 killed:
  - each bound removed;
  - `known_through` ignored;
  - the first cut's session-only read;
  - filed under `ref`;
  - prior days by `ref`;
  - closures ignored;
  - the oldest decision winning;
  - the postdating record kept;
  - the note removed;
  - the unreadable record aborting the run.

**THE PANELS — ASSESSED, NOT REDESIGNED.** What this bound cannot reach is every input read as a
WHOLE DOCUMENT as it stands at the run:
- dossier pages: the panel grid, and the freshness `measured` and `stale_tags`;
- scenario records: legs, triggers and dated triggers, for a record amended after the day;
- theme cards, and `followed.json`'s panel declarations.

On the 09-22 re-cut that is UBER's two panels:
- `multiple_and_price` as of 2026-10-09: 19.48x over 13 closes, where the committed day has 19.20x
  over 12;
- `dilution` windowed to 09-22 with 6 prospectus supplements, where the committed day runs to 08-24
  with 4.

Both come from UBER's page re-assembled 2026-10-11 (#705). None of these documents has a per-item
date to filter on, and filtering by the document's own date drops rather than reconstructs: a theme
card re-declared after a day replaces one that was in force on it.

| option | what it does | cost |
|---|---|---|
| **1. rule — a moved page gets a NEW day; a past day is never re-cut** | what #705 did | none in code; rests on the operator, and needs a session after the latest day |
| 2. version — read each document as committed on the day | faithful | the monitor reads git history in every checkout that runs it; "committed on the day" needs a definition; the panel-emit pin would compare against own-date pages, and stop forcing re-cuts at all |
| 3. stamp — each panel names its page's date, the day flags any after itself | honest | still lookahead, now labelled |

**Recommendation: 1 now; 2 only if past days are ever re-cut for analysis.** An operator call,
recorded on STATE §5.0 row 5.

**BOUNDARY.**
- **Re-cuts:** run 2026-10-11 at `f81eee50` (before) and at this branch's head (after). EDGAR and
  Polygon were read through the repo's own clients. Compared against the committed
  `data/monitor/<day>.json`.
- **Rows and panels:** "freshness rows" are the day's `freshness` list (9 on 09-22 and 10-09);
  "panel rows" are its `panels` list (124 on 09-22 and 10-09), matched on (ticker, key). The new
  `evidence_after_day` key, empty on every 09-22 and 10-09 row, is not counted as a difference.
- **Sweep:** "dates after the day" covers `last_evidence_date`, every `newer_filings` date, every
  `passed_trigger_deadlines` deadline and every passed theme deadline. It ran over the 5 committed
  days (`data/monitor/2026-*.json` at `f81eee50`).
- **Excluded from the scan, by design:** future-dated fields — next-print estimates, horizon dates,
  theme deadlines not yet passed.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A record amended after a day still puts today's legs and triggers into that day's row,**
  including any dated trigger the amendment added. Only its dates are bounded; the typed field and
  the note say so on the day. Falsifier: a re-cut day whose row carries a later trigger while its
  `evidence_after_day` is empty.
- **A past day can now lack a held position's freshness row.** SMPL on 07-20: its record states
  nothing before 08-05. The book row stays; the note names the gap.
- **Whole-document inputs are unbounded** (above). They wait on the row 5 ruling.
- **The committed days keep what they hold.** 2026-07-20 keeps its three 07-21 evidence dates, and
  every day from 08-11 keeps IT as BUY. Rewriting a superseded day is an explicit operator act
  (`rewrite_history`), not a side effect of this fix.
- **Behaviour change on a weekend or before-close run:** a DEADLINE after the session no longer
  passes in that session's file. Filings and records up to the run's date are still read.
