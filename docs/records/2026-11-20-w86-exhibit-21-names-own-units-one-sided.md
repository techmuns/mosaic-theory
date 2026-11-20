---
id: W86
status: recorded
date: 2026-11-20
prs: [1152]
---

# W86: a 10-K's Exhibit 21 can confirm that a name is the filer's own and can never show that a name is not. On B's 59 W85 `entity` rows, the CIQ company cell (`filed_under`) is on its filer's list on 19 rows (5 distinct names) and is the filer itself on 5 more (2 names); 23 rows confirm own by the reader's rule, LillyDirect's being on a list that names affiliates. Of B's 15 hand marks, Exhibit 21 alone confirms 7 own rows (2 names) and no not-own row (3 rows, 2 names); 33 of the 35 misses are on lists that say they omit insignificant subsidiaries ($0, a new reader, unwired)

**WHAT.**
- **A $0 reader, `vinci/edgar/exhibit21.py`.** It reads the Exhibit 21 of a filer's newest original 10-K filed by a date. The exhibit is found by the TYPE in EDGAR's SGML header (`EX-21`, `EX-21.1`, `EX-21.01`), never by its filename. Each listed name comes back with its jurisdiction, any ownership share its row states, and its `source_ref`: form, accession, exhibit type and URL. The read also carries:
  - the exhibit's own statement that it omits insignificant subsidiaries, verbatim (`states_omission`);
  - whether its own text says it lists affiliates as well (`names_affiliates`);
  - the registrant's name in force at the cut (`registrant`) and when the 10-K was filed (`filed_as`), read from EDGAR's submissions `formerNames`.
- **Statuses.** A read is `listed`, `no_ex21` (the header was read and types none), `no_names` (the exhibit was read and no name was found: a parse failure, never an empty list), `unread` (the header or the document could not be read; never reported as `no_ex21`), or `no_10k`.
- **`match_entity` reports one tier per entity.**
  - `registrant`: the entity is the filer itself.
  - `exact`: the name as listed, whitespace collapsed.
  - `normalised`: equal once case, punctuation and trailing corporate forms are set aside (Google = Google LLC).
  - `word_prefix`: the entity is the leading whole words of a listed name (Quest in "Quest Nutrition, LLC").
  - `not_listed`, or the read's status.
  - Each tier is its own value, so a consumer picks a tier knowingly.
- **`EntityMatch.confirms_own` names the tiers that may promote a row to "own"** (review round 2):
  - `exact` and `normalised` confirm, on a list that names no affiliates, for a row that states no share of 50% or less;
  - `registrant` confirms;
  - `word_prefix` never confirms. It is a lead: "NBC" leads 28 of TJX's names ("NBC Charlotte Merchants, LLC" first), and "Global" leads Concentrix's "The Global Email Trustee Limited";
  - no tier refutes.
  - A bare filer name lands on one subsidiary's row: "Uber" is `normalised` to "Uber B.V.", and "Amazon" is a `word_prefix` lead to "Amazon.com Services LLC". Both are the filer's own, and the row named is one of several.
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
- **The key that works is CIQ's company cell, `filed_under`.** It is a legal name ("Google LLC", "Quest Nutrition, LLC"), and every one of its 19 list matches is `exact`.
- **W85's `lead_party` is a read name, and 16 of the 59 are compound** by a separator rule: 15 contain " and " ("Oracle and Google"), and 1 has a comma before another name ("Whole Foods Market, The Government of USA"). A comma before a corporate form ("WFM Purchasing, LP") is not a separator. A 17th, "Balyasny Asset Management Google Cloud", names two parties with no separator. *Corrected in review round 2: the first count, 27, took every comma.*
  - `lead_party` matches 6 rows, all of them rows `filed_under` already matches.
  - Where `filed_under` is the filer itself (5 rows: GOOGL 6, 471, 576, 1239; SMPL 123), `lead_party` says whose row it is, and it matches on 3 of the 5 ("Google" ×2, "Quest Nutrition").
- **No not-own row matched at any tier.** B's 3 not-own rows are 2 names, AtaiBeckley (×2) and Kelonia, both LLY, all `not_listed`. That is the only test of a false "own" these 59 give, and 2 names is a small one.

**THE MEASUREMENTS** (main `6c22b222`, EDGAR read 2026-11-20).
- **Survey: the 26 filers of every committed page** (`data/dossiers/*`), each on its newest original 10-K filed by any day:
  - **26 of 26** file an Exhibit 21, and every one parses to at least one name (`listed` 26).
  - **11 of 26 state an omission:** 7 in a sentence (GOOGL, LLY, NFLX, NKE, ROST, TGT, WLK) and 4 only by titling themselves "significant subsidiaries" (AMZN, FUBO, MCK, V).
  - **2 of 26 say they list affiliates:** LLY, ROST.
  - **1 of 26 states a share below 100% on any row:** PARR, on 3 rows (46%, 65%, 40%).
  - List sizes run from 1 (ORKA, VITL) to 352 (CNXC).
  - The newest 10-Ks of BRBR and FUBO were filed 2026-11-18, after their committed pages were built. A wired read passes the page's own date as `through`.
- **B's 59 rows** (#1004 comment 7032108050, B's post of 2026-11-20, main `51c84843`): every CIQ Key Developments row of the 26 committed pages that W85's unpushed classifier classes `entity`, out of 1,056 rows, with B's 15-row sample (`random.Random(20261120)`) marked by hand: 11 own, 3 not own, 1 can't tell. 8 filers: AMZN 11, BRBR 2, GOOGL 22, LLY 12, MCK 4, SMPL 3, TGT 3, UBER 2. Every filer files an Exhibit 21, so no row is `no_ex21`.

  **By key and tier** (rows, then distinct names in brackets):

  | key | on the list (Exhibit 21) | the filer itself | not listed | confirms own |
  |---|---|---|---|---|
  | `filed_under` | `exact` 19 (5) | `registrant` 5 (2) | 35 (14) | 23 rows (6 names) |
  | `lead_party` | `normalised` 5, `word_prefix` 1 | — | 53 | — |
  | either | 19 | 5 | 35 | 23 |

  - The 19 list matches are 5 names: Premier Nutrition Company, LLC; Dymatize Enterprises, LLC; Google LLC (14 rows); LillyDirect Pharmacy, LLC; Quest Nutrition, LLC (2 rows).
  - LillyDirect's row does not confirm own, because LLY's list names affiliates. That leaves 18 Exhibit 21 rows, plus the 5 registrant rows, confirming own.
  - Of the 35 misses, 33 are on lists that state an omission. 18 of those are on lists that say so in a sentence (GOOGL 4, LLY 11, TGT 3). 15 are on lists that only title themselves "significant subsidiaries" (AMZN 11, MCK 4). UBER's 2 Zipline rows are on a list that states none.

  **Against B's 15 hand marks** (`filed_under`):
  - **own, 11 rows (6 names):**
    - Exhibit 21 lists 8 rows, 3 names: Google LLC ×6, LillyDirect Pharmacy, LLC and Quest Nutrition, LLC.
    - Exhibit 21 alone confirms 7 rows, 2 names (Google LLC, Quest Nutrition). LillyDirect is listed on a list that names affiliates.
    - 1 row is the filer itself (row 471, filed under Alphabet).
    - 2 rows are not listed: AMZN's "Wfm Purchasing, LP" and TGT's "Shipt, Inc.", both on lists that state an omission.
  - **not own, 3 rows (2 names):** 0 on the list.
  - **can't tell, 1:** not listed (MCK's "Rocky Mountain Cancer Centers, LLP").
  - So on the sample a confirmation was right 8 times of 8 (7 from Exhibit 21, 1 the registrant). It found 8 of the 11 own rows.

  **At each page's own date** (`--through-page`: `date_semantics.analysis_as_of`), every tier count above is the same. Only BRBR reads a different 10-K: `0001772016-25-000153` at its 2026-10-23 page, where the newest is `0001772016-26-000027`, filed 2026-11-18.

  **Every row**, with B's source_ref. That is the KD workbook's sha256 prefix and the row's index into `[ln.strip() for ln in vinci.dossier.ciq.read_text(path).splitlines() if ln.strip()]`. Each row is a CIQ-derived fact (the Company cell, the KD date and type), and no headline or Situation text is reproduced. **Knowable date:** CIQ is not point-in-time, so each fact is knowable from its workbook's export, which the KD file does not stamp. It is no earlier than the row's KD date. 6 of the 8 workbooks are on this machine under B's hashes; BRBR's `4d36485e4132` and SMPL's `42488b41ad98` are not.

  | # | page | KD date | KD type | `filed_under` (CIQ Company cell) | workbook sha256 · row | `filed_under` tier | confirms own | `lead_party` tier | B's mark |
  |---|---|---|---|---|---|---|---|---|---|
  | 1 | AMZN | Oct-03-2026 | Product-Related Announcement | Wfm Purchasing, LP | `8966359496c0` · 111 | `not_listed` | — | `not_listed` | own |
  | 2 | AMZN | Aug-29-2026 | Product-Related Announcement | Wfm Purchasing, LP | `8966359496c0` · 351 | `not_listed` | — | `not_listed` | — |
  | 3 | AMZN | Aug-29-2026 | Product-Related Announcement | Wfm Purchasing, LP | `8966359496c0` · 354 | `not_listed` | — | `not_listed` | — |
  | 4 | AMZN | Aug-29-2026 | Product-Related Announcement | Wfm Purchasing, LP | `8966359496c0` · 357 | `not_listed` | — | `not_listed` | — |
  | 5 | AMZN | Aug-29-2026 | Product-Related Announcement | Wfm Purchasing, LP | `8966359496c0` · 360 | `not_listed` | — | `not_listed` | — |
  | 6 | AMZN | Aug-29-2026 | Product-Related Announcement | Wfm Purchasing, LP | `8966359496c0` · 366 | `not_listed` | — | `not_listed` | — |
  | 7 | AMZN | Aug-29-2026 | Product-Related Announcement | Wfm Purchasing, LP | `8966359496c0` · 369 | `not_listed` | — | `not_listed` | — |
  | 8 | AMZN | Aug-29-2026 | Product-Related Announcement | Wfm Purchasing, LP | `8966359496c0` · 375 | `not_listed` | — | `not_listed` | — |
  | 9 | AMZN | Aug-29-2026 | Product-Related Announcement | Wfm Purchasing, LP | `8966359496c0` · 378 | `not_listed` | — | `not_listed` | — |
  | 10 | AMZN | May-13-2026 | Business Expansion | Whole Foods Market, Inc. | `8966359496c0` · 1098 | `not_listed` | — | `not_listed` | — |
  | 11 | AMZN | Apr-30-2026 | Business Expansion | Audible, Inc | `8966359496c0` · 1245 | `not_listed` | — | `not_listed` | — |
  | 12 | BRBR | Jan-07-2026 | Product-Related Announcement | Premier Nutrition Company, LLC | `4d36485e4132` · 138 | `exact` | yes | `not_listed` | — |
  | 13 | BRBR | Oct-20-2025 | Product-Related Announcement | Dymatize Enterprises, LLC | `4d36485e4132` · 180 | `exact` | yes | `word_prefix` | — |
  | 14 | GOOGL | Nov-19-2026 | Product-Related Announcement | Alphabet Inc. (NasdaqGS:GOOGL) | `68170f53b65e` · 6 | `registrant` | yes | `normalised` | — |
  | 15 | GOOGL | Oct-27-2026 | Client Announcement | Google LLC | `68170f53b65e` · 276 | `exact` | yes | `not_listed` | own |
  | 16 | GOOGL | Oct-27-2026 | Client Announcement | Google LLC | `68170f53b65e` · 282 | `exact` | yes | `not_listed` | own |
  | 17 | GOOGL | Oct-22-2026 | Product-Related Announcement | Calico Life Sciences LLC | `68170f53b65e` · 315 | `not_listed` | — | `not_listed` | — |
  | 18 | GOOGL | Oct-22-2026 | Client Announcement | Google LLC | `68170f53b65e` · 321 | `exact` | yes | `not_listed` | — |
  | 19 | GOOGL | Oct-20-2026 | Product-Related Announcement | Google Public Sector LLC | `68170f53b65e` · 345 | `not_listed` | — | `not_listed` | — |
  | 20 | GOOGL | Oct-12-2026 | Client Announcement | Google LLC | `68170f53b65e` · 426 | `exact` | yes | `not_listed` | — |
  | 21 | GOOGL | Oct-08-2026 | Client Announcement | Google LLC | `68170f53b65e` · 459 | `exact` | yes | `not_listed` | own |
  | 22 | GOOGL | Oct-08-2026 | Client Announcement | Google LLC | `68170f53b65e` · 462 | `exact` | yes | `not_listed` | — |
  | 23 | GOOGL | Oct-07-2026 | Client Announcement | Alphabet Inc. (NasdaqGS:GOOGL) | `68170f53b65e` · 471 | `registrant` | yes | `not_listed` | own |
  | 24 | GOOGL | Oct-06-2026 | Client Announcement | Google LLC | `68170f53b65e` · 483 | `exact` | yes | `not_listed` | own |
  | 25 | GOOGL | Sep-30-2026 | Client Announcement | Google LLC | `68170f53b65e` · 519 | `exact` | yes | `not_listed` | own |
  | 26 | GOOGL | Sep-24-2026 | Client Announcement | Google LLC | `68170f53b65e` · 561 | `exact` | yes | `not_listed` | own |
  | 27 | GOOGL | Sep-23-2026 | Client Announcement | Alphabet Inc. (NasdaqGS:GOOGL) | `68170f53b65e` · 576 | `registrant` | yes | `not_listed` | — |
  | 28 | GOOGL | Sep-22-2026 | Client Announcement | Google LLC | `68170f53b65e` · 600 | `exact` | yes | `not_listed` | — |
  | 29 | GOOGL | Sep-15-2026 | Product-Related Announcement | GFiber | `68170f53b65e` · 645 | `not_listed` | — | `not_listed` | — |
  | 30 | GOOGL | Aug-25-2026 | Product-Related Announcement | Google LLC | `68170f53b65e` · 801 | `exact` | yes | `not_listed` | — |
  | 31 | GOOGL | Aug-25-2026 | Product-Related Announcement | Google LLC | `68170f53b65e` · 804 | `exact` | yes | `not_listed` | — |
  | 32 | GOOGL | Aug-24-2026 | Client Announcement | Google LLC | `68170f53b65e` · 825 | `exact` | yes | `not_listed` | — |
  | 33 | GOOGL | Jul-30-2026 | Product-Related Announcement | Alphabet Inc. (NasdaqGS:GOOGL) | `68170f53b65e` · 1239 | `registrant` | yes | `normalised` | — |
  | 34 | GOOGL | Jun-25-2026 | Client Announcement | Google LLC | `68170f53b65e` · 1455 | `exact` | yes | `not_listed` | — |
  | 35 | GOOGL | Jun-23-2026 | Product-Related Announcement | Calico Life Sciences LLC | `68170f53b65e` · 1494 | `not_listed` | — | `not_listed` | — |
  | 36 | LLY | Jul-06-2026 | Product-Related Announcement | AtaiBeckley Inc. | `4175d82ecd70` · 453 | `not_listed` | — | `not_listed` | not own |
  | 37 | LLY | Jun-23-2026 | Client Announcement | LillyDirect Pharmacy, LLC | `4175d82ecd70` · 573 | `exact` | — | `not_listed` | own |
  | 38 | LLY | May-31-2026 | Product-Related Announcement | Kelonia Therapeutics, Inc. | `4175d82ecd70` · 711 | `not_listed` | — | `not_listed` | not own |
  | 39 | LLY | May-26-2026 | Product-Related Announcement | Curevo, Inc. | `4175d82ecd70` · 738 | `not_listed` | — | `not_listed` | — |
  | 40 | LLY | May-21-2026 | Product-Related Announcement | Kelonia Therapeutics, Inc. | `4175d82ecd70` · 759 | `not_listed` | — | `not_listed` | — |
  | 41 | LLY | Apr-22-2026 | Product-Related Announcement | AtaiBeckley Inc. | `4175d82ecd70` · 978 | `not_listed` | — | `not_listed` | — |
  | 42 | LLY | Apr-08-2026 | Product-Related Announcement | AtaiBeckley Inc. | `4175d82ecd70` · 1038 | `not_listed` | — | `not_listed` | — |
  | 43 | LLY | Mar-17-2026 | Product-Related Announcement | AtaiBeckley Inc. | `4175d82ecd70` · 1134 | `not_listed` | — | `not_listed` | — |
  | 44 | LLY | Mar-03-2026 | Product-Related Announcement | AtaiBeckley Inc. | `4175d82ecd70` · 1278 | `not_listed` | — | `not_listed` | — |
  | 45 | LLY | Feb-26-2026 | Product-Related Announcement | AtaiBeckley Inc. | `4175d82ecd70` · 1299 | `not_listed` | — | `not_listed` | not own |
  | 46 | LLY | Jan-08-2026 | Product-Related Announcement | AtaiBeckley Inc. | `4175d82ecd70` · 1452 | `not_listed` | — | `not_listed` | — |
  | 47 | LLY | Jan-07-2026 | Product-Related Announcement | Kelonia Therapeutics, Inc. | `4175d82ecd70` · 1461 | `not_listed` | — | `not_listed` | — |
  | 48 | MCK | Mar-11-2026 | Business Expansion | Precision Medicine Group, LLC | `1d82ea5f732a` · 276 | `not_listed` | — | `not_listed` | — |
  | 49 | MCK | Mar-09-2026 | Product-Related Announcement | CoverMyMeds, LLC | `1d82ea5f732a` · 282 | `not_listed` | — | `not_listed` | — |
  | 50 | MCK | Feb-05-2026 | Business Expansion | Precision Medicine Group, LLC | `1d82ea5f732a` · 330 | `not_listed` | — | `not_listed` | — |
  | 51 | MCK | Nov-12-2025 | Client Announcement | Rocky Mountain Cancer Centers, LLP | `1d82ea5f732a` · 423 | `not_listed` | — | `not_listed` | can't tell |
  | 52 | SMPL | May-19-2026 | Product-Related Announcement | Quest Nutrition, LLC | `42488b41ad98` · 57 | `exact` | yes | `normalised` | own |
  | 53 | SMPL | Mar-04-2026 | Product-Related Announcement | Quest Nutrition, LLC | `42488b41ad98` · 81 | `exact` | yes | `normalised` | — |
  | 54 | SMPL | Jan-05-2026 | Product-Related Announcement | The Simply Good Foods Company (NasdaqCM:SMPL) | `42488b41ad98` · 123 | `registrant` | yes | `normalised` | — |
  | 55 | TGT | Sep-09-2026 | Product-Related Announcement | Shipt, Inc. | `c2f01e35537c` · 33 | `not_listed` | — | `not_listed` | — |
  | 56 | TGT | Jun-04-2026 | Product-Related Announcement | Shipt, Inc. | `c2f01e35537c` · 171 | `not_listed` | — | `not_listed` | own |
  | 57 | TGT | Nov-03-2025 | Product-Related Announcement | Shipt, Inc. | `c2f01e35537c` · 477 | `not_listed` | — | `not_listed` | — |
  | 58 | UBER | Jul-14-2026 | Business Expansion | Zipline International Inc. | `c01be9430440` · 231 | `not_listed` | — | `not_listed` | — |
  | 59 | UBER | Jun-30-2026 | Client Announcement | Zipline International Inc. | `c01be9430440` · 240 | `not_listed` | — | `not_listed` | — |

  - **The misses are unknowns, not investees.** Of the 14 distinct names not listed, B marked 4 (WFM Purchasing and Shipt own; AtaiBeckley and Kelonia not own) and 1 can't-tell. The other 9 are unmarked and are not judged here.
  - **Two diagnostics, not reader tiers:**
    - splitting each `lead_party` at the separators above raises its matches from 6 to 12;
    - also counting a name whose leading words are a listed name ("Google Cloud" begins with "Google", from "Google LLC") reaches 23 rows.
    - With `filed_under`, the union is 25 rows, 1 more than 24.
    - Both are W85's attribution logic, so they are left to B's wiring and not added to the reader.
- **Before the list landed, B's 11 named own units** as B's earlier comment (7031763467) writes them ("Google" ×7, "LillyDirect", "Shipt", "Quest", "Whole Foods"): `normalised` 7, `word_prefix` 2, `not_listed` 2 (Shipt, Whole Foods), `exact` 0. Those were short names, not CIQ's company cells. On the real `filed_under` cells the same own units match `exact`.

**HOW VERIFIED.**
- **Real exhibits, end to end.** 26 of 26 committed filers were read through the repo's SEC client (the survey above). Every list's names were audited by hand for header and furniture rows.
- **The audit found and fixed three parser shapes:**
  - the "Entity" column title (EPAM, VRRM);
  - section titles (TJX's "Operating Subsidiaries");
  - numbered rows (WERN's "1.").
  - *Corrected in review round 2:* this line first listed a fourth, "percent cells read as the jurisdiction (AMZN)". AMZN's share cells follow its jurisdiction, so they were never read as one. The guard that skips a share cell stays, and no committed exhibit exercises it.
- **A heading set across two text blocks** (V's "List of Significant" / "Subsidiaries of Visa Inc.") is read as one statement.
- **`tests/test_exhibit21.py`, 62 test nodes on real committed documents** (`tests/fixtures/exhibit21/`: 11 exhibits, 3 of them cut, 3 whole SGML headers and 1 whole `index.json`).
  - Positive: Google under Alphabet (`normalised`, its `source_ref` naming 10-K `0001652044-26-000018` and EX-21.01); Quest and LillyDirect (`word_prefix`); Yellowstone Pipe Line at 40%; the filer itself (`registrant`).
  - Negative: Lyft under Alphabet (`not_listed`), and Whole Foods and Shipt `not_listed` on lists that state an omission. Uber's no statement is pinned as no statement, never as complete.
  - The header path: Alphabet's 10-K types EX-21.01; its 10-Q, read, types none (`[]`); an unread header is `None` → `unread`. `through` never asks for a later 10-K.
- **The first 12 mutants, 12 killed:**
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
- **Review round 2 (coordinator A's independent review at `5b8732e1`).** Each FIX test failed on that head:
  - **Text mode read the exhibit's heading as a subsidiary.** Visa's and Simply Good Foods' exhibits with their tables removed read `listed` with one name, "Subsidiaries of …", which ends in a form. A heading is now never a name, in either mode.
  - **Text mode dropped real names.** 182 of the 26 lists' 1,105 names ended in a form the table lacked (s.r.o., d.o.o., K.K., S.A.C., EOOD, C.V., SHPK, WLL …), carried a note after the form (", dba …", "… Branch", "i.L."), or led with it ("PT …", "UAB …"). "Name - Delaware" lines lost their jurisdiction, and a "(40.0% interest)" was read as one. 62 remain, names text mode cannot see any form in, 49 of them Concentrix's ("Concentrix Maroc"). Only TGT's exhibit has no table, and no count moves. "Trust" marks a company but is not set aside when names are compared, so "NBC" does not equal "NBC Trust".
  - **EDGAR's state tag hid the registrant.** "TJX COMPANIES INC /DE/" normalised to "tjx companies inc de". `/XX/` tags are now set aside.
  - **`word_prefix` gave a false "own".** The record said B's wiring may promote on "a match". `confirms_own` now names the tiers (above).
  - **`name_in_force` read today's name in a gap.** On ORKA's real `formerNames`, 2003-02-01 falls between HYSEQ's and NUVELO's spans and read "Oruka Therapeutics"; it now reads NUVELO, and a day before the first span reads HYSEQ. The list also drops the name the 10-K was filed under, and the registrant tier matches it (`filed_as`). `mechanical._former_name_flags` keeps the containing-span rule and so the same gap. That file is held by B, so the gap is named here for B and not fixed there.
  - **A submissions document that cannot be read** now returns `unread` for that filer; it had raised and stopped a whole `measure` run.
  - **Pins added for behaviour already right**, each killing a mutant that survived before:
    - a header URL that answers with a non-SGML page (Alphabet's real `index.json`) is `unread`, never `no_ex21`;
    - an exhibit that cannot be fetched is `unread`, never `no_names`;
    - `through` is inclusive;
    - the exhibit type is matched whole (through `_is_ex21_type`);
    - the `&` rule, stacked forms, and exact matching kept case-sensitive.
  - **Prose corrected:** the compound count (27 → 16), the evidence split by tier with distinct names, and the per-row table with its source_ref and knowable date.
  - **Mutants:** A's 34, ported to this code, plus 13 for this round's fixes: 47 in all. **43 are killed.** Four survive, each with its reason:
    - **the first-pass heading fallback alone:** an equivalent mutant, since the cross-block pass returns the same statement. Both passes together are killed.
    - **the "not significant" arm of the omission pattern:** equivalent on the corpus. The one list that says it (LLY's) also says "omitted".
    - **accepting a non-text EX-21 (a PDF):** no header in the corpus types one.
    - **the share-cell guard:** no exhibit exercises it. DISMISSED, since no real exhibit puts a share cell before its jurisdiction and a pin would need a synthetic row.
- **Corpus before synthetic.** No fixture is hand-written. The no-list case is Alphabet's real exhibit with its table removed in the test: an SGML header page was tried first and read "COMPANY CONFORMED NAME: Alphabet Inc." as a name, which is why it is not used.

**BOUNDARY.**
- **The 59:** B's population, at B's boundary: main `51c84843` and W85's unpushed `ciq_sheets.key_developments`, 59 of 1,056 KD rows of the 26 committed pages, with B's sample drawn by seed 20261120. Matched at this PR's head on 2026-11-20 against each of the 8 filers' newest original 10-K filed by any day. Counts are of rows; "14 distinct names" counts (page, `filed_under`) pairs.
- **The survey:** the 26 committed pages under `data/dossiers/` at main `6c22b222`. Each filer's newest original 10-K on its submissions document's recent page, filed by any day, read 2026-11-20. A 10-K/A is not read.
- **The 11:** rows built from B's comment text, each matched against its filer's same read.
- **Counts are of rows,** except "of 26", which counts filers.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$0.** SEC reads only, through the paced client and its cache, with the repo's default User-Agent, approved by the operator for this measurement (2026-11-20).
- **Text-mode parsing is loose in both directions.** Only TGT's exhibit among the 26 is text-mode.
  - It reads a line that ends in a form, so a stray line such as an auditor's "LLP" signature would read as a name.
  - It cannot read a name with no form in it: 62 of the 1,105 names the 26 tables list.
  - *Falsifier:* a text-mode list whose names include a line that is not a company, or that loses a listed company.
- **`word_prefix` over-matches, so it confirms nothing.** "NBC" leads 28 of TJX's names and "Global" a Concentrix trustee. On the 59 it matched once on `lead_party` (BRBR's "Dymatize", a `filed_under` exact match too). No not-own row matched at any tier, and 2 not-own names is a small test. *Falsifier:* a not-own row that `confirms_own`.
- **The 59 cannot be rebuilt from main.** W85's branch is not pushed. The population is B's post (#1004 comment 7032108050) at B's boundary, and the rows file this run read was built from that post's table, one row per table line: `own` is true for "own (subsidiary)", false for "not own", null for "can't tell" and for unmarked rows. When W85's PR opens, the population is reproducible from code at its head.
- **The newest 10-K and the page's own both measured.** At each page's `analysis_as_of` the counts are the same; only BRBR reads an older 10-K. A wired read passes the page's date as `through`.
