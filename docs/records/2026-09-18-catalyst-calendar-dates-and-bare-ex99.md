---
id:
status: shipped
date: 2026-09-18
prs: [633]
supersedes:
superseded-by:
---

# The catalyst calendar dated 33 of 41 rows into a year the text never stated, and a release typed EX-99 was invisible

**WHAT.** Four defects, two files.

1. `_CAL_FWD_EVENT` accepted a year only IMMEDIATELY after the month, so a month-day-year date
   ("effective April 2, 2026") read as year-less and fell through to the next-occurrence rule.
   The year is now read wherever the date states it — after the month or after the day.
2. An UNSTATED year resolved against the page's REFERENCE date rather than the row's own. A Key
   Development dated `Mar-31-2026` saying "starting on April 15" means that April; it was
   published as 2027-04. Resolution order is now: the stated year → the row's own date → the
   reference date.
3. `since` joined `_CAL_BACKWARD`. "Since launching at I/O in May, there's been a 40% increase" is
   a retrospective, and it was being published as a 2027-05 catalyst.
4. `_ex991_names_from_headers` matched only the dotted `EX-99.1`. PARR and LLY type their
   quarterly release `EX-99`, so those releases were never read — PARR's page said "carries 2.02
   but no EX-99.1 exhibit was found" against a filing that plainly furnishes one, and its Q3-2025
   quarter was simply absent from the release set.

**WHY.** A calendar's whole job is what is AHEAD, and this one was publishing the past as the
future. Every mis-dated row landed a year late, which put it in front of the human as a catalyst
precisely because the event had already happened. The two new ultra-short-term-trade pages carried
four of them between them (WLK 2027-04 and 2027-06, AMZN 2027-04 and 2027-05) — a sleeve whose
verdicts are scored at 180 days, reading a calendar that invented rows past its own horizon.

The missed release is the same failure in the other direction: a real filing read as furnishing
nothing, so a quarter went missing from the set the reconciliation and the synthesis prompt read.

**HOW VERIFIED.** Re-derived `_dated_operating_events` over EVERY committed page's own stored
driver rows, old code vs new, no network: **41 stated-date rows across 17 pages → 8.** 31 dropped
because the corrected date is in that page's own past; 2 dropped as retrospectives. Of the 41
originals, **25 stated a year in their own clause that the published stamp contradicted** — all 25
dated a year late. 16 of the 17 pages carried at least one bad row.

The exhibit fix, run against live EDGAR: PARR `0001628280-25-048903` → 1 exhibit,
`a20250930991earningsreleas.htm` → 2 reconciliation rows (`Q3 2025` 302.6, 372.5); LLY
`0000059478-26-000043` → 1 exhibit, `q126lillysalesandearningsp.htm`. Both were `[]` before.

The corpus caught a regression I introduced: widening the pattern let the optional DAY group eat
the first two digits of a bare year, so "October 2025" read as day-20 with the year lost and a new
2026-10 row appeared on AMZN. That is what `(?!\d)` is for, and it is pinned.

Three pins, each red on the old code before it was green on the new: the unit pins on the real WLK
/ AMZN / GOOGL verbatims, a corpus guard that re-derives every committed page and refuses a stamp
contradicting a year the clause states (it reddened on AORT first), and the exhibit pin built from
the two filings' REAL SGML headers. Mutation battery: 8 mutations, 8 caught — reverting each fix,
blinding `_cal_row_month`, deleting the past-drop, and widening `EX-99` far enough to swallow the
`EX-99.2` sibling.

**BOUNDARY.** The 41 → 8 count: all 20 `data/dossiers/*/dossier.json` committed at `origin/main`
a1fd3a3, each page's own `mechanical.operating_drivers.rows` as input and its own `reference_date`
as the reference; unit = stated-date (`date_basis == "stated"`) catalyst rows, source D only —
print, guidance and maturity rows are untouched. The exhibit measurement: 22 names × their 10 most
recent 8-Ks, EDGAR as of 2026-09-18, filtered to items 2.02/8.01 with no release found = 29
filings, of which exactly 2 furnish one under a bare `EX-99`; the other 27 are genuinely
release-free (debt take-downs with EX-1.1/EX-4.x, XBRL-only 8-Ks).

**THE ADDED-ON-TOP CASE, MEASURED (2026-09-18, review).** The widening was first measured only
where NO release was found — the recovery case — which left one question open: how often does a
filing carry BOTH a dotted `EX-99.1` and a bare `EX-99`, so that the bare form ADDS a document to a
release already located? Answered by census rather than by sample: **every 8-K in EDGAR's 2026 Q2
full index — 18,300 filings, zero fetch errors**, each classified by the EX-99 types its own SGML
header declares.

| | filings | share |
|---|--:|--:|
| no EX-99 text document | 8,911 | 48.7% |
| dotted `EX-99.1` only — unchanged by the widening | 9,164 | 50.1% |
| **bare `EX-99` only — the recovery case** | **221** | **1.21%** |
| **both dotted and bare — the added-on-top case** | **4** | **0.022%** |

So the widening recovers a release in about **one 8-K in 83**, not merely PARR's and LLY's, and the
case it was not measured on occurs in about one in 4,575.

All four were parsed, both documents each. **The bare document adds ZERO rows and produces ZERO
value conflicts in all four** — the anchored vocabulary finds nothing in any of them:

- CIK 1718405 `0001493152-26-026891` — the bare `EX-99` is `ex96-1.htm`, an 883,297-character S-K
  1300 mining technical report (Exhibit 96.1) the filer mis-typed. Parses to nothing.
- CIK 788784 and 81033 `0001193125-26-205254` (one filing, two co-filers) — a genuine Exhibit 99
  beside a genuine Exhibit 99.1. Both parse to nothing.
- CIK 885978 `0000885978-26-000017` — **the types are SWAPPED**: `EX-99.1` is `ex10-1.htm`, a
  529KB credit agreement (Exhibit 10.1), and the bare `EX-99` is `ex99-1.htm`, the actual 2.9KB
  press release whose own text reads "Exhibit 99.1".

That last filing settles the remedy the review proposed. **Restricting the bare form to filings
with no dotted `EX-99.1` would have lost the real press release there** and kept the credit
agreement — so preferring the dotted type is measurably the wrong rule, and the widening stays as
written. The residual cost is compute, not correctness: a mis-typed exhibit is fetched and scanned
(883KB in the worst of the four), and the 529KB credit agreement is fetched under the DOTTED type
regardless of this change.

**WHAT IT COSTS / WHAT IS ACCEPTED.** The committed pages keep their bad rows until they are
re-assembled — this PR changes code only, and the artifact pass is a separate commit by rule.
Stamps stay MONTH-granular, so an event stated for the 1st of the current month is still published
in the month it already happened in; on this corpus that is 2 rows (AMZN, BRBR) and a day-granular
drop would have changed nothing, so none was built. Falsifier: if a page shows a stated-date row
whose month is the reference month and whose stated day has passed, the month granularity is
costing more than it saves and the drop should read the day.

**REPORTED, NOT FIXED.** The event TEXT of a calendar row starts at the last comma before the
match, and a thousands separator is a comma: AMZN's "…into the 330,000-customer AWS Marketplace
starting in September" renders as "000-customer Amazon Web Services (AWS) Marketplace starting in
September". The DATE and the source_ref are right; the label is garbled. One condition on
`vinci/dossier/mechanical.py` `_dated_operating_events`' clause split, held out of this PR as a
separate defect from date parsing.
