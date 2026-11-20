---
id: W86
status: recorded
date: 2026-11-20
prs: [1152]
---

# W86: a 10-K's Exhibit 21 can confirm that a name is the filer's own and can never show that a name is not. On B's 59 W85 `entity` rows, the CIQ company cell (`filed_under`) matches the filer's list on 24 (19 listed exactly, 5 the filer itself) and W85's `lead_party` adds none; 9 of B's 11 own-marked rows match, none of its 3 not-own rows does; 33 of the 35 misses are on lists that say they omit insignificant subsidiaries ($0, a new reader, unwired)

**WHAT.**
- **A $0 reader, `vinci/edgar/exhibit21.py`.** It reads the Exhibit 21 of a filer's newest original 10-K filed by a date. The exhibit is found by the TYPE in EDGAR's SGML header (`EX-21`, `EX-21.1`, `EX-21.01`), never by its filename. Each listed name comes back with its jurisdiction, any ownership share its row states, and its `source_ref`: form, accession, exhibit type and URL. The read also carries:
  - the exhibit's own statement that it omits insignificant subsidiaries, verbatim (`states_omission`);
  - whether its own text says it lists affiliates as well (`names_affiliates`);
  - the registrant's own name.
- **Statuses.** A read is `listed`, `no_ex21` (the header was read and types none), `no_names` (the exhibit was read and no name was found: a parse failure, never an empty list), `unread` (the header or the document could not be read; never reported as `no_ex21`), or `no_10k`.
- **`match_entity` reports one tier per entity.**
  - `registrant`: the entity is the filer itself.
  - `exact`: the name as listed, whitespace collapsed.
  - `normalised`: equal once case, punctuation and trailing corporate forms are set aside (Google = Google LLC).
  - `word_prefix`: the entity is the leading whole words of a listed name (Quest in "Quest Nutrition, LLC").
  - `not_listed`, or the read's status.
  - Each tier is its own value, so a consumer picks a tier knowingly.
- **A measurement script, `scripts/w86_exhibit21_coverage.py`.**
  - `survey`: every committed page's filer.
  - `measure --rows <jsonl> --entity-field <key>`: any JSONL of rows with a ticker, a name under `<key>` and an optional `own` mark. B's 59 were run on `filed_under` and on `lead_party`.
  - `fixtures`: rebuilds this PR's fixtures.
- **Not wired.** Nothing reads the reader. B wires it into W85's attribution after W85 merges.

**THE ANSWER TO W86's QUESTION: ONE-SIDED.**
- **A name ON the list is the filer's own statement.** It is evidence that the name is its own, with two exceptions the read carries:
  - a list that says it names affiliates too: LLY's "List of Subsidiaries & Affiliates", ROST's "SUBSIDIARIES & AFFILIATES";
  - a row whose stated share is a minority: PARR lists "Yellowstone Pipe Line Company (40.0% interest)" and "Laramie Energy, LLC (46.0% interest)". A 40% interest is an investee by any reading.
- **A name NOT on the list is evidence of nothing.** Reg S-K Item 601(b)(21)(ii) lets a filer omit every subsidiary that is not significant in aggregate. 11 of the 26 lists say they do. Amazon's lists 9 companies; Whole Foods is its own and is not one of them, and neither is Target's Shipt. A list that states no omission is not therefore complete: Uber's names 13 companies and says nothing.
- **DOES THIS SELECT ON FORM? Yes, on its absent side**, and that is why it is one-sided. Whether a subsidiary is on the list depends on the significance threshold, a disclosure-form fact, not on whether the unit is the filer's. So the reader may promote a Key Development row to "own" on a listed match. It may never demote a row to "investee" on a miss. B's wiring has to keep that asymmetry; `not_listed` must stay "unknown".
- **The key that works is CIQ's company cell, `filed_under`.** It is a legal name ("Google LLC", "Quest Nutrition, LLC"), and every one of its 19 list matches is `exact`. W85's `lead_party` is a read name, and 27 of the 59 are compound ("Oracle and Google", "BNP Paribas and Google Cloud"). It matches 6, all of them rows `filed_under` already matches. Where `filed_under` is the filer itself (5 rows: GOOGL 6, 471, 576, 1239; SMPL 123), `lead_party` says whose row it is, and it matches on 3 of the 5 ("Google" ×2, "Quest Nutrition").
- **No not-own row matched at any tier.** B's 3 not-own rows are AtaiBeckley ×2 and Kelonia, all LLY, all `not_listed`. That is the only test of a false "own" these 59 give, and three rows is a small one.

**THE MEASUREMENTS** (main `6c22b222`, EDGAR read 2026-11-20).
- **Survey: the 26 filers of every committed page** (`data/dossiers/*`), each on its newest original 10-K filed by any day:
  - **26 of 26** file an Exhibit 21, and every one parses to at least one name (`listed` 26).
  - **11 of 26 state an omission:** AMZN, FUBO, GOOGL, LLY, MCK, NFLX, NKE, ROST, TGT, V, WLK.
  - **2 of 26 say they list affiliates:** LLY, ROST.
  - **1 of 26 states a share below 100% on any row:** PARR, on 3 rows (46%, 65%, 40%).
  - List sizes run from 1 (ORKA, VITL) to 352 (CNXC).
  - The newest 10-Ks of BRBR and FUBO were filed 2026-11-18, after their committed pages were built. A wired read passes the page's own date as `through`.
- **B's 59 rows** (#1004 comment 7032108050, B's post of 2026-11-20, main `51c84843`): every CIQ Key Developments row of the 26 committed pages that W85's unpushed classifier classes `entity`, out of 1,056 rows, with B's 15-row sample (`random.Random(20261120)`) marked by hand: 11 own, 3 not own, 1 can't tell. 8 filers: AMZN 11, BRBR 2, GOOGL 22, LLY 12, MCK 4, SMPL 3, TGT 3, UBER 2. Every filer files an Exhibit 21, so no row is `no_ex21`.

  | key | matched | of which | not listed |
  |---|---|---|---|
  | `filed_under` | **24** | `exact` 19, `registrant` 5 | 35, 33 on lists stating an omission (UBER's 2 Zipline rows are on a list that states none) |
  | `lead_party` | 6 | `normalised` 5, `word_prefix` 1 | 53 |
  | either | 24 | — | 35 |

  **Against B's 15 hand marks** (`filed_under`):
  - **own, 11:** 9 matched (8 `exact`: Google LLC ×6, LillyDirect Pharmacy, LLC, Quest Nutrition, LLC; 1 `registrant`: row 471, filed under Alphabet). 2 not listed: AMZN's "Wfm Purchasing, LP" and TGT's "Shipt, Inc.", both on lists that state an omission.
  - **not own, 3:** 0 matched.
  - **can't tell, 1:** not listed (MCK's "Rocky Mountain Cancer Centers, LLP").
  - So on the sample a match was right 9 times of 9, and it found 9 of the 11 own rows.

  **By entity** (names and tiers only, no CIQ headline or Situation text; each row's `source_ref` is B's workbook sha256 prefix and row index):

  | page | `filed_under` | rows (B's #) | `filed_under` tier → listed name | `lead_party` tiers | B's marks |
  |---|---|---|---|---|---|
  | AMZN | Wfm Purchasing, LP | 9 (1–9) | `not_listed` (omission stated) | `not_listed` 9 | own 1 |
  | AMZN | Whole Foods Market, Inc. | 1 (10) | `not_listed` (omission stated) | `not_listed` 1 | — |
  | AMZN | Audible, Inc | 1 (11) | `not_listed` (omission stated) | `not_listed` 1 | — |
  | BRBR | Premier Nutrition Company, LLC | 1 (12) | `exact` → Premier Nutrition Company, LLC | `not_listed` 1 | — |
  | BRBR | Dymatize Enterprises, LLC | 1 (13) | `exact` → Dymatize Enterprises, LLC | `word_prefix` 1 | — |
  | GOOGL | Alphabet Inc. (NasdaqGS:GOOGL) | 4 (14, 23, 27, 33) | `registrant` | `normalised` 2, `not_listed` 2 | own 1 |
  | GOOGL | Google LLC | 14 (15, 16, 18, 20, 21, 22, 24, 25, 26, 28, 30, 31, 32, 34) | `exact` → Google LLC | `not_listed` 14 | own 6 |
  | GOOGL | Calico Life Sciences LLC | 2 (17, 35) | `not_listed` (omission stated) | `not_listed` 2 | — |
  | GOOGL | Google Public Sector LLC | 1 (19) | `not_listed` (omission stated) | `not_listed` 1 | — |
  | GOOGL | GFiber | 1 (29) | `not_listed` (omission stated) | `not_listed` 1 | — |
  | LLY | AtaiBeckley Inc. | 7 (36, 41–46) | `not_listed` (omission stated) | `not_listed` 7 | not own 2 |
  | LLY | LillyDirect Pharmacy, LLC | 1 (37) | `exact` → LillyDirect Pharmacy, LLC | `not_listed` 1 | own 1 |
  | LLY | Kelonia Therapeutics, Inc. | 3 (38, 40, 47) | `not_listed` (omission stated) | `not_listed` 3 | not own 1 |
  | LLY | Curevo, Inc. | 1 (39) | `not_listed` (omission stated) | `not_listed` 1 | — |
  | MCK | Precision Medicine Group, LLC | 2 (48, 50) | `not_listed` (omission stated) | `not_listed` 2 | — |
  | MCK | CoverMyMeds, LLC | 1 (49) | `not_listed` (omission stated) | `not_listed` 1 | — |
  | MCK | Rocky Mountain Cancer Centers, LLP | 1 (51) | `not_listed` (omission stated) | `not_listed` 1 | can't tell 1 |
  | SMPL | Quest Nutrition, LLC | 2 (52, 53) | `exact` → Quest Nutrition, LLC | `normalised` 2 | own 1 |
  | SMPL | The Simply Good Foods Company (NasdaqCM:SMPL) | 1 (54) | `registrant` | `normalised` 1 | — |
  | TGT | Shipt, Inc. | 3 (55–57) | `not_listed` (omission stated) | `not_listed` 3 | own 1 |
  | UBER | Zipline International Inc. | 2 (58, 59) | `not_listed` (none stated) | `not_listed` 2 | — |

  - **The 35 misses are unknowns, not investees.** Of their 14 distinct names, B marked 4 (WFM Purchasing and Shipt own; AtaiBeckley and Kelonia not own) and 1 can't-tell. The other 9 are unmarked and are not judged here.
  - **Two diagnostics, not reader tiers.** Splitting each `lead_party` on " and " and ", " raises its matches from 6 to 12. Also counting a name whose leading words are a listed name ("Google Cloud" begins with "Google", from "Google LLC") reaches 23 rows on `lead_party`. Neither adds more than 1 row to the 24 that `filed_under` gives. Both are W85's attribution logic, so they are left to B's wiring and not added to the reader.
- **Before the list landed, B's 11 named own units** as B's earlier comment (7031763467) writes them ("Google" ×7, "LillyDirect", "Shipt", "Quest", "Whole Foods"): `normalised` 7, `word_prefix` 2, `not_listed` 2 (Shipt, Whole Foods), `exact` 0. Those were short names, not CIQ's company cells. On the real `filed_under` cells the same own units match `exact`.

**HOW VERIFIED.**
- **Real exhibits, end to end.** 26 of 26 committed filers were read through the repo's SEC client (the survey above). Every list's names were audited by hand for header and furniture rows.
- **The audit found and fixed four parser shapes:**
  - the "Entity" column title (EPAM, VRRM);
  - section titles (TJX's "Operating Subsidiaries");
  - numbered rows (WERN's "1.");
  - percent cells read as the jurisdiction (AMZN).
- **A heading set across two text blocks** (V's "List of Significant" / "Subsidiaries of Visa Inc.") is read as one statement.
- **`tests/test_exhibit21.py`, 29 test nodes on real committed documents** (`tests/fixtures/exhibit21/`: 11 exhibits, 3 of them cut, and 3 whole SGML headers).
  - Positive: Google under Alphabet (`normalised`, its `source_ref` naming 10-K `0001652044-26-000018` and EX-21.01); Quest and LillyDirect (`word_prefix`); Yellowstone Pipe Line at 40%; the filer itself (`registrant`).
  - Negative: Lyft under Alphabet (`not_listed`), and Whole Foods and Shipt `not_listed` on lists that state an omission. Uber's no statement is pinned as no statement, never as complete.
  - The header path: Alphabet's 10-K types EX-21.01; its 10-Q, read, types none (`[]`); an unread header is `None` → `unread`. `through` never asks for a later 10-K.
- **12 mutants, 12 killed:**
  - each of the four parser fixes reverted;
  - the corporate-form exception for a name with column vocabulary (LLY's "Eli Lilly (Philippines), Incorporated");
  - the registrant drop;
  - the cross-block heading;
  - `word_prefix` folded into `normalised`;
  - the share capture;
  - an unread header read as none;
  - `no_names` read as `listed`;
  - the affiliates flag;
  - `through` ignored.
- **Review round 0 (`/code-review high --fix`) found three defects in the first cut, all fixed:**
  - **Deduplicating rows by the normalised key merged distinct companies.** EPAM lists "EPAM Systems LLC" in four countries, and it lost 13 rows; CNXC lost 15 and LLY lost "Aparito LLC". A row is now dropped only when it repeats verbatim, name and jurisdiction both.
  - **The registrant was dropped by the normalised key**, which removed every subsidiary sharing its base name: "Gartner, LLC", "BellRing Brands, LLC", "Netflix Pte. Ltd.", "Eli Lilly and Company Limited". Only the registrant's own name, its corporate form kept, is dropped now ("TARGET CORP" = "Target Corporation"). An exact listed match comes before the `registrant` tier.
  - **A `through` before the submissions document's recent page read `no_10k`.** The read now looks back 550 days from `through`.
  - These changed the list sizes above and none of the survey's or the 11's tier counts. 3 more mutants, one per fix: 3 killed.
- **Codex round 1 (P1), fixed:** a read at a past `through` took the registrant's CURRENT name, a look-ahead. Oruka Therapeutics filed as "ARCA biopharma, Inc." until 2024-08-30 (its real submissions `formerNames`). At `through` 2024-06-30 the read is ARCA's 10-K `0000950170-24-009809`, which files no Exhibit 21, and it named the registrant "Oruka Therapeutics, Inc.". It now takes the name in force on `through`: the former-name span containing it, else the current name, the same rule `mechanical._former_name_flags` applies. The test failed on the PR head before the fix.
- **Corpus before synthetic.** No fixture is hand-written. The no-list case is Alphabet's real exhibit with its table removed in the test: an SGML header page was tried first and read "COMPANY CONFORMED NAME: Alphabet Inc." as a name, which is why it is not used.

**BOUNDARY.**
- **The 59:** B's population, at B's boundary: main `51c84843` and W85's unpushed `ciq_sheets.key_developments`, 59 of 1,056 KD rows of the 26 committed pages, with B's sample drawn by seed 20261120. Matched at this PR's head on 2026-11-20 against each of the 8 filers' newest original 10-K filed by any day. Counts are of rows; "14 distinct names" counts (page, `filed_under`) pairs.
- **The survey:** the 26 committed pages under `data/dossiers/` at main `6c22b222`. Each filer's newest original 10-K on its submissions document's recent page, filed by any day, read 2026-11-20. A 10-K/A is not read.
- **The 11:** rows built from B's comment text, each matched against its filer's same read.
- **Counts are of rows,** except "of 26", which counts filers.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$0.** SEC reads only, through the paced client and its cache, with the repo's default User-Agent, approved by the operator for this measurement (2026-11-20).
- **Text-mode parsing is loose.** An exhibit with no table gives one name per line ending in a corporate form, so a stray line such as an auditor's "LLP" signature would read as a name. Only TGT's exhibit among the 26 is text-mode. *Falsifier:* a text-mode list whose names include a line that is not a company.
- **`word_prefix` can over-match.** On the 59 it matched once (BRBR's "Dymatize", a `filed_under` exact match too), and no not-own row matched at any tier. Three not-own rows is a small test. *Falsifier:* a not-own row matching at any tier, `word_prefix` above all.
- **The 59 cannot be rebuilt from main.** W85's branch is not pushed. The population is B's post (#1004 comment 7032108050) at B's boundary, and the rows file this run read was built from that post's table, one row per table line: `own` is true for "own (subsidiary)", false for "not own", null for "can't tell" and for unmarked rows. When W85's PR opens, the population is reproducible from code at its head.
- **The newest 10-K, not the page's.** The 59 were matched against each filer's newest original 10-K filed by any day. A wired read passes each page's own date as `through`.
