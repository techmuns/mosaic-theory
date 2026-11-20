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
- Operating types (guidance, product, client announcement, expansion, capacity, impairment) had
  no attribution: ONE reader (`kd_lead_party`) takes the Situation's sentence-case opening, cut at
  a capitalised announcement verb and at an appositive; one matcher (`kd_is`) asks, part by part,
  whether it is the company (its first identifying word one of the company's, then all of the
  company's words in it or all of its own among the company's: "Lilly" is Eli Lilly, "General
  Mills" is not General Motors). No lead party read → unread, never the Company cell's guess; the
  cell decides only a row filed under another LISTED company.
- Corporate types keep the #458 subject filter. A kept row whose Situation opens on a person (an
  executive change) is the company's; one that opens on another ORGANISATION (a legal form or a
  listing, not naming the company) is read as an operating row is: Diginex acquiring
  planA.earth on Visa's export, Merck acquiring Terns on Lilly's.
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
  equal to the page's, attribution aside): 1,056 rows → 481 company · 43 joint · 470 other ·
  58 entity · 4 unread (after review round 2; 492 · 41 · 464 · 59 · 0 before it).
- The calendar at each page's own reference date: the only rows that leave are GOOGL 2026-10 and
  2026-11 (Lyft), UBER 2027-01 (Wonder and Zipline), AMZN 2027-02 (Kartoon Studios), each named
  in its page's QA line; AMZN keeps 2027-01 (Amazon) and 2027-02 (Best Buy and Amazon).
- $0 classifier audit (coordinator B's condition): `random.Random(20261120)`, 15 rows per class
  (unread whole) = 61, hand-read: company 0/15, joint 1/15, entity 0/15, other 1/15, unread 1/1
  misclassified, none moving a calendar. Two were systematic — a name split at "and Company",
  an opening "A subsidiary of X" — and are fixed behind tests that failed first; the third (#46,
  Notarize's rename "Proof") is a one-off, left. Table: the PR body.
- The digest shape, measured before choosing (coordinator B's design question): a line per row
  +29,264 bytes, one header per group +5,114 (AMZN +0.93%, largest MCK +3.43%). After review
  round 2: +5,920 bytes over 19 pages (FUBO's +4.04% the most; 21 of 532 rows carry "(stated
  by …)"). Panel pages: BURL +245, LLY +554, MCK +396, SMPL +195; CNXC, ROST byte-identical.
- Review round 2 (coordinator B's independent review of #1157 at `4482be8d`): 14 rows move
  class, each read — the 4 no-lead rows → unread (TGT ×2, LLY ×2), 7 organisation-led M&A rows
  → other (FUBO's reverse merger, Merck/Terns ×2, Celltrion, Alohi, Diginex ×2), GOOGL's
  Balyasny row entity → other, NFLX's two iHeartMedia rows other → joint; 21 lead-party texts
  are corrected ("Eli Lilly and Company Raised" → "Eli Lilly and Company"). The calendar change
  is unchanged: the same 4 rows. Four regressions the first fix made on the corpus were found and
  pinned before the commit (V's "At Visa Payments Forum 2026, Visa", VITL's "The Board of
  Diectors of …", WLK's "M. Steven Bender, … of Westlake Corporation", BRBR's "Premier
  Protein®").
- Pins: `tests/test_kd_attribution.py` (45) on `tests/fixtures/ciq_kd_attribution.json` (cut by
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

**DOES THIS SELECT ON FORM?** (CLAUDE.md, before any new gate ships.) Yes, partly, and knowingly.
The calendar's own-party filter decides on how a row NAMES its party: the words of the Situation's
opening against the company's own name. It does not select on economic substance — a client's own
announcement that it chose the company is not the company's statement, and is left off however
material. And it misses the company where the company speaks under a NAME FORM other than its
own:
- a brand or a subsidiary name: AMZN `8966359496c0` row 168 (May-27-2026, "Prime Video
  announced…", filed under Amazon Digital Services LLC) → other, printed as "STATED BY ANOTHER
  PARTY"; AMZN row 100 (Jul-28-2026, Prime Video with Rogers) → other where it is joint;
- a lead naming the operating subsidiary over the company's own cell: GOOGL `68170f53b65e` rows 0
  (Nov-19-2026, a Gemini release) and 114 (Jul-30-2026), filed under Alphabet Inc.
  (NasdaqGS:GOOGL) itself, → entity, because a lead of "Google" is read before the cell;
- a banner whose name lacks the company's: TJX's "TJ Maxx" → other.
Each miss errs toward NOT calling a row management-stated, and the calendar names every row it
leaves off. W88 (wiring the 10-K's Exhibit 21, after this merges) can turn a row led by a
subsidiary's legal name into the company's where Exhibit 21 lists that subsidiary (Google LLC, if
listed, for the GOOGL rows); it cannot reach a brand that is no legal entity (Prime Video, TJ
Maxx), nor a subsidiary the exhibit leaves out as not significant.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- The 58 `entity` rows are never the company's: of 15 sampled (before round 2), 11 are its
  subsidiaries (Google LLC ×7, LillyDirect, Shipt, Quest Nutrition, WFM Purchasing), 3 are not,
  1 can't be told. The export does not say which. Falsifier: a subsidiary's dated action named in
  a QA line that the human reads as the company's own catalyst. W86/W88: the 10-K's Exhibit 21 as
  the subsidiary list (coordinator A).
- A one-word identity still takes a namesake: "Target Hospitality" would read as TGT's.
- The 4 `unread` rows (no lead party read) are never management-stated: 2 are the company's (LLY's
  long-term data), 2 are not (TGT's k2o, being haircare). Fail loud over guessing.
- The KD source_ref is "file · date", with no workbook sha256 or row, and `filed_under` and
  `lead_party` inherit it; the 2026-11-04 licence condition asks for both. Pre-existing; coordinator
  B opens its item.
- No committed page carries the attribution until it is rebuilt: the $0 refresh of the active
  pages is a separate PR after this merges.
