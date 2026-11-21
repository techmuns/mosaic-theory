---
id: 2026-11-20-w85-a-key-development-is-the-companys-own-only-when-its-row-says-so
status: open
date: 2026-11-20
prs: [1157]
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
- **Panel check (RUNBOOKS §n): DRAWN AND SCORED.**
  - **Why a second registration.** The first, `2f2314b07ebf7402`, was claimed and stopped with no key. Its claim is voided on main (#1167, #1172). #1167 then moved the harness's scorer fingerprint (`d9456b87` to `973d862a`), so RG-D12 refuses a draw of 2f2314b0 from any checkout.
  - **The registration drawn:** `75c0df5b6e2379bb`, on main through #1173.
    - It has the same design and the same 12 request pins; only the scorer differs.
    - The operator's approval, typed in the registering session: "Yes, measure W85 no-worsening on the panel again, cap $35" (approval `45ae4f7e`; ruling "New approval, this Mac").
    - Base `c8198583`, cand `fd10cfe5`, `--transform kd_attribution`, the six panel pages, 5 draws per arm, no-worsening only.
  - **The draw:** 60 draws, every one priced; spend **$28.7313 of $35** (the approval's ledger: 62 rows, 60 of them usage rows). Its `drawn` row is committed here.
  - **The score.** Run from the drawing checkout at main `483343fa`: **"ships: False; decision: ships once the moves listed are explained in writing"**. **No class metric worsens:** every p_upper is above 0.05. Held-out pages are 0 → 0 on every metric.

    | metric | BASE → CAND | p_lower | p_upper |
    |---|---|---|---|
    | M-ABSENT | 48 → 55 | 0.801 | 0.264 |
    | M-ECHO | 63 → 43 | 0.0365 (fewer) | 0.977 |
    | M-GAP | 9 → 11 | 0.772 | 0.402 |
    | M-LABEL | 48 → 56 | 0.911 | 0.148 |
    | M-PATH | 3 → 2 | 0.5 | 0.857 |
    | M-SIGN | 0 → 0 | 1 | 1 |

    | page | leans BASE | leans CAND | proposal |
    |---|---|---|---|
    | BURL | mixed 5 | mixed 5 | none → none |
    | CNXC | mixed 5 | mixed 5 | none → none |
    | ROST | mixed 4, strongly-bullish 1 | mixed 5 | none → none |
    | LLY | strongly-bullish 4, mixed 1 | strongly-bullish 5 | none → BUY |
    | MCK | mixed 4, strongly-bullish 1 | strongly-bullish 5 | none → BUY |
    | SMPL | strongly-bearish 4, mixed 1 | strongly-bearish 5 | none → AVOID_TERMINAL |

  - **BLOCKS (verbatim, from the run's `score_log.jsonl`):** LLY, MCK and SMPL, each "the lean moved (…) — explain it in writing before review".
- **The three moves, explained (§6.1; descriptive, deciding nothing).** Read off the run's 12 requests (BASE against CAND, the user text) and its 60 draws.
  - **What the score's proposal is.** It is production's (`verdict.derive_proposal`): the modal lean, WITHHELD unless the draws are unanimous. A page whose modal lean did not move can therefore gain a proposal from one draw.
  - **Which section changes.** On all three pages the requests differ only in the operating-drivers digest. SYSTEM is equal, and CNXC and ROST are identical.
  - **MCK, where the MODAL lean moved** (mixed → strongly-bullish; strongly-bullish 1/5 → 5/5). **Fisher's exact test, two-sided: p = 0.048.** It is the smallest of the six pages' tests, uncorrected for six.
    - **What W85 changed.** It removed NO row. It moved 11 Key Developments out of the company's own event list into the two labelled groups, and kept them in the request:
      - **another party's (7):** Epic Pharmacies' multi-party client row; Option Care Health's three guidance rows (Jan, Apr and Jul 2026); TempraMed; AOP Health; Iterum;
      - **naming no company (4):** CoverMyMeds; Precision for Medicine's Japan and Singapore offices; IDEOlogy Health with Rocky Mountain Cancer Centers.
      - McKesson's own rows stay where they were, the Option Care Health investment and the Precision Medicine Group acquisition among them.
    - **No draw in either arm names any of the 11 moved rows.** Each draw's whole output was searched for their distinctive names, and every "Option Care" or "Precision" in them cites the two M&A rows.
    - **The subsidiary question (W86/W88).** CIQ's company cell for the 4 entity rows is Precision Medicine Group, LLC (×2), CoverMyMeds, LLC and Rocky Mountain Cancer Centers, LLP. All 4 are `not_listed` on McKesson's Exhibit 21, which lists only "significant subsidiaries" (`docs/records/2026-11-20-w86-exhibit-21-names-own-units-one-sided.md`, rows 48–51). So:
      - **W88 as designed would NOT restore them:** it promotes only on a confirming listing;
      - **CoverMyMeds is a recall cost W88 cannot reach.** A name off a significant-subsidiaries list is evidence of nothing.
    - **What this shows and does not.** The lean moved with no draw citing a moved row. The record cannot say whether the move comes from the digest's new grouping (11 rows no longer read as McKesson's own), or is the noise of five draws per arm. One page in six at p = 0.048 is what chance alone gives about one panel in four.
  - **LLY** (strongly-bullish 4/5 → 5/5; **Fisher p = 1.0**). The modal lean did not move; the proposal appears only because CAND's draws are unanimous.
    - **What W85 changed.** It moved 42 rows into the groups: 28 another party's, mostly partners' and platforms' client announcements; and 14 naming no company: AtaiBeckley's, Kelonia's and Curevo's trial updates, the OURA–LillyDirect row, and Lilly's own two long-term-data rows (Lebrikizumab, Omvoh).
    - **Lilly's two own rows are a known error:** relabelled "stated by no party read". They are #47 and #112 among the post-cap findings that W88 takes.
    - **Draws in both arms name AtaiBeckley and Kelonia** only through Lilly's own M&A rows, which stay in the company's list in both arms, and the calls: the acquired-IPR&D charge.
  - **SMPL** (strongly-bearish 4/5 → 5/5; **Fisher p = 1.0**). The modal lean did not move; the proposal appears only because CAND's draws are unanimous.
    - **What W85 changed.** It moved three Quest Nutrition product rows (Jan, Mar and May 2026) under "do not name the company".
    - **Exhibit 21 confirms Quest Nutrition, LLC as the company's own** (W86 rows 52–54). W88 would restore all three.
    - **Draws:** one draw in each arm names the Dill Pickle launch, from the Q4 call, not from the moved row.

**BOUNDARY.**
- Defect measured at main `bc1c0e16`, 2026-11-20: 26 committed pages, 1,068 KD rows; 59 stated
  catalyst rows = 41 maturities (source C, every one the CIQ capital-structure panel) + 18 source
  D, of which 3 another party's.
- Fix measured at main `51c84843`, 2026-11-20: 26 pages, 1,056 KD rows (the other 1,256 driver
  rows are filings and calls); 19 source-D rows, 4 leave.
- Digest bytes: `synthesis._operating_drivers_digest` on the same rows, before and after.
- **Panel, the result.** One draw of registration `75c0df5b`, 2026-11-21 (drawn_at 06:09:56Z), in one run folder:
  - 12 requests and 60 draws, 6 pages × 2 arms × 5;
  - its approval's ledger, 62 rows (the approval, the claim, 60 usage rows);
  - the score: the run's one `score_log.jsonl` row.
- **Panel, the §6.1 reading.**
  - **Moved rows:** the `[event]` lines in CAND's user text under the two group headers, LLY 42, MCK 11 and SMPL 3. Each is in BASE's user text verbatim, except LLY's two "stated by no party read" rows, which gain that note.
  - **"No draw names them":** a case-blind search of each draw's whole tool output (all fields) for each moved row's distinctive names, 10 draws per page.
  - **Fisher's exact test:** two-sided, on the count of the CAND-modal lean in 5 BASE against 5 CAND draws.

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
