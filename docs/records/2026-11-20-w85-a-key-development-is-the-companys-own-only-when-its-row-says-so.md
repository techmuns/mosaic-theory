---
id: 2026-11-20-w85-a-key-development-is-the-companys-own-only-when-its-row-says-so
status: open
date: 2026-11-20
prs: []
supersedes:
superseded-by:
---

# W85: a CIQ Key Development is "management-stated" only when its row names the company; another party's is grouped under a header with who states it, left off the calendar and named in its QA line ($0, code)

**WHAT.**
- `ciq_sheets.key_developments` gives every CIQ Key Developments row an `attribution`
  (`schemas.KdAttribution`):
  - `party`: company / joint / entity / other / unread (`schemas.KdParty` defines each);
  - `filed_under`: CIQ's Company cell, kept on the page as a fact with its source_ref (operator,
    2026-11-20, relayed by coordinator B: "Yes, as recommended");
  - `lead_party`: the party the row's Situation opens on.
- Corporate types keep the #458 subject filter and read as the company's. Operating types
  (guidance, product, client announcement, expansion, capacity, impairment) had no attribution:
  ONE reader (`kd_lead_party`) takes the Situation's sentence-case opening, one matcher
  (`kd_names`) asks whether it names the company. No lead read → the Company cell decides.
- `mechanical._operating_events` writes "a management-stated dated operating action" only for a
  row with no attribution (a filing's, a call's) or a company / joint one. Every other dated
  event is left off and named, every one, in the calendar's QA line (both renderers print it).
- The synthesis digest and the scenario template print the company's own rows first, unchanged,
  then the rest under one header per group ("STATED BY ANOTHER PARTY", "DO NOT NAME THE
  COMPANY"), with "(stated by X)" only where the row's headline does not already name X.
- `attribution` is not sent in the synthesis facts (`synthesis.NOT_SENT`) and is absent, never
  null, when None — in every dump (`OperatingDriver`'s serializer) and on the page
  (`DRIVER_ROW_DROP_WHEN_NONE`): every committed page round-trips byte for byte, and a layer
  replayed at an older ref (`evals.replay.layer_at`) compares equal.

**WHY.** Coordinator B, reviewing #1150 (2026-11-19): GOOGL's Brief named Lyft's European launch
as its next catalyst; UBER's, a Wonder–Zipline drone service that does not name Uber; AMZN's
calendar carried a Kartoon Studios series with Amazon the counterparty. The export's columns are
Date, Company, Type, Headline, Other Parties — no role, no announcer. The Company cell is whom CIQ
files the row under: decisive for another LISTED company (Lyft), but 320 rows CIQ files under the
company (or an entity bearing its name) open on another party, and Other Parties is '-' on the
Kartoon row. So the announcing party is read, through one reader, from the one place CIQ writes it.

**HOW VERIFIED.**
- Production `key_developments` on each committed page's own export (26/26; every re-read row
  equal to the page's, attribution aside): 1,056 rows → 492 company · 41 joint · 464 other ·
  59 entity · 0 unread.
- The calendar at each page's own reference date: the only rows that leave are GOOGL 2026-10 and
  2026-11 (Lyft), UBER 2027-01 (Wonder and Zipline), AMZN 2027-02 (Kartoon Studios), each named
  in its page's QA line; AMZN keeps 2027-01 (Amazon) and 2027-02 (Best Buy and Amazon).
- $0 classifier audit (coordinator B's condition): `random.Random(20261120)`, 15 rows per class
  (unread whole) = 61, hand-read: company 0/15, joint 1/15, entity 0/15, other 1/15, unread 1/1
  misclassified, none moving a calendar. Two were systematic — a name split at "and Company",
  an opening "A subsidiary of X" — and are fixed behind tests that failed first; the third (#46,
  Notarize's rename "Proof") is a one-off, left. Table: the PR body.
- The digest shape, measured before choosing (coordinator B's design question): a line per row
  +29,264 bytes, one header per group +5,114 (AMZN +0.93%, largest MCK +3.43%). Panel pages:
  BURL +245, LLY +396, MCK +396, SMPL +195; CNXC, ROST byte-identical.
- Pins: `tests/test_kd_attribution.py` (29) on `tests/fixtures/ciq_kd_attribution.json` (cut by
  `scripts/build_kd_attribution_fixture.py` from the pages' own exports, each Situation equal to
  the frozen page's verbatim) and the cut-4889ddba frozen pages, end to end through
  `render_markdown`.
- Panel check (RUNBOOKS §n; operator 2026-11-20 "Yes, as recommended": no-worsening, the six
  panel pages, 5 draws per arm, cap $35): NOT YET DRAWN. It is registered from the reviewed code
  PR's head (coordinator B's order: a review fix after registering would change the request
  bytes and void the draw), and its registration sha, spend and result are added here then.

**BOUNDARY.**
- Defect measured at main `bc1c0e16`, 2026-11-20: 26 committed pages, 1,068 KD rows; 59 stated
  catalyst rows = 41 maturities (source C, every one the CIQ capital-structure panel) + 18 source
  D, of which 3 another party's.
- Fix measured at main `51c84843`, 2026-11-20: 26 pages, 1,056 KD rows (the other 1,256 driver
  rows are filings and calls); 19 source-D rows, 4 leave.
- Digest bytes: `synthesis._operating_drivers_digest` on the same rows, before and after.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- The 59 `entity` rows are never the company's: of 15 sampled, 11 are its subsidiaries (Google
  LLC ×7, LillyDirect, Shipt, Quest Nutrition, WFM Purchasing), 3 are not, 1 can't be told. The
  export does not say which. Falsifier: a subsidiary's dated action named in a QA line that the
  human reads as the company's own catalyst. Proposed: W86, the 10-K's Exhibit 21 as the
  subsidiary list (coordinator B).
- A banner whose name lacks the company's (TJX's "TJ Maxx") reads as `other`.
- No committed page carries the attribution until it is rebuilt: the $0 refresh of the active
  pages is a separate PR after this merges.
