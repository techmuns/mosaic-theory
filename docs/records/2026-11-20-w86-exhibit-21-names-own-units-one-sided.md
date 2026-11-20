---
id: W86
status: recorded
date: 2026-11-20
prs: []
---

# W86: a 10-K's Exhibit 21 can confirm that a name is the filer's own and can never show that a name is not. 9 of B's 11 named own units are on their filer's list; Whole Foods and Shipt are not, and both lists say they omit insignificant subsidiaries. B's 59-row population was not located, so its coverage is NOT measured here ($0, a new reader, unwired)

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
  - `measure --rows`: any JSONL of `{ticker, entity, own?}` rows. This is what B's 59 rows need.
  - `fixtures`: rebuilds this PR's fixtures.
- **Not wired.** Nothing reads the reader. B wires it into W85's attribution after W85 merges.

**THE ANSWER TO W86's QUESTION: ONE-SIDED.**
- **A name ON the list is the filer's own statement.** It is evidence that the name is its own, with two exceptions the read carries:
  - a list that says it names affiliates too: LLY's "List of Subsidiaries & Affiliates", ROST's "SUBSIDIARIES & AFFILIATES";
  - a row whose stated share is a minority: PARR lists "Yellowstone Pipe Line Company (40.0% interest)" and "Laramie Energy, LLC (46.0% interest)". A 40% interest is an investee by any reading.
- **A name NOT on the list is evidence of nothing.** Reg S-K Item 601(b)(21)(ii) lets a filer omit every subsidiary that is not significant in aggregate. 11 of the 26 lists say they do. Amazon's lists 9 companies; Whole Foods is its own and is not one of them, and neither is Target's Shipt. A list that states no omission is not therefore complete: Uber's names 13 companies and says nothing.
- **DOES THIS SELECT ON FORM? Yes, on its absent side**, and that is why it is one-sided. Whether a subsidiary is on the list depends on the significance threshold, a disclosure-form fact, not on whether the unit is the filer's. So the reader may promote a Key Development row to "own" on a listed match. It may never demote a row to "investee" on a miss. B's wiring has to keep that asymmetry; `not_listed` must stay "unknown".
- **The exact tier alone finds none of the 11.** Every own match needs `normalised` (Google) or `word_prefix` (LillyDirect, Quest). `word_prefix` is the looser of the two. Whether it ever matches a non-own name is what B's 4 not-own sample rows would test, and those rows were not located (below).

**THE MEASUREMENTS** (main `6c22b222`, EDGAR read 2026-11-20).
- **Survey: the 26 filers of every committed page** (`data/dossiers/*`), each on its newest original 10-K filed by any day:
  - **26 of 26** file an Exhibit 21, and every one parses to at least one name (`listed` 26).
  - **11 of 26 state an omission:** AMZN, FUBO, GOOGL, LLY, MCK, NFLX, NKE, ROST, TGT, V, WLK.
  - **2 of 26 say they list affiliates:** LLY, ROST.
  - **1 of 26 states a share below 100% on any row:** PARR, on 3 rows (46%, 65%, 40%).
  - List sizes run from 1 (ORKA, VITL) to 352 (CNXC).
  - The newest 10-Ks of BRBR and FUBO were filed 2026-11-18, after their committed pages were built. A wired read passes the page's own date as `through`.
- **B's 11 named own units**, the entity strings as B's #1004 comment 7031763467 writes them (Google ×7, LillyDirect, Shipt, Quest, Whole Foods), not B's W85 strings. 5 filers: GOOGL, LLY, TGT, SMPL, AMZN.

  | tier | rows | entities → listed name |
  |---|---|---|
  | exact | 0 | — |
  | normalised | 7 | Google ×7 → Google LLC (GOOGL) |
  | word_prefix | 2 | LillyDirect → LillyDirect Pharmacy, LLC (LLY, a list naming affiliates); Quest → Quest Nutrition, LLC (SMPL) |
  | not_listed | 2 | Shipt (TGT), Whole Foods (AMZN); both lists state an omission |

- **B's 59 rows and its 15-row sample: NOT MEASURED.** B defines them as rows filed under an unlisted entity at main `51c84843`. They were not found in any of these places:
  - no W85 branch or PR on origin;
  - no record under `docs/records/`;
  - no hit for `git log --all -i --grep=W85` other than #1150's mention;
  - no #1004 comment other than B's request.
  - The committed pages carry no entity field, so the population exists only in B's unpushed W85 code.
  - The brief said to report this rather than re-derive a different population, so none was derived. The 4 not-own rows of B's sample are unknown here for the same reason.
  - Coordinator A was asked for the list on 2026-11-20. Once it lands: `PYTHONPATH=. python scripts/w86_exhibit21_coverage.py measure --rows <rows.jsonl> --through <page date>`.

**HOW VERIFIED.**
- **Real exhibits, end to end.** 26 of 26 committed filers were read through the repo's SEC client (the survey above). Every list's names were audited by hand for header and furniture rows.
- **The audit found and fixed four parser shapes:**
  - the "Entity" column title (EPAM, VRRM);
  - section titles (TJX's "Operating Subsidiaries");
  - numbered rows (WERN's "1.");
  - percent cells read as the jurisdiction (AMZN).
- **A heading set across two text blocks** (V's "List of Significant" / "Subsidiaries of Visa Inc.") is read as one statement.
- **`tests/test_exhibit21.py`, 28 test nodes on real committed documents** (`tests/fixtures/exhibit21/`: 11 exhibits, 3 of them cut, and 2 whole SGML headers).
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
- **Corpus before synthetic.** No fixture is hand-written. The no-list case is Alphabet's real exhibit with its table removed in the test: an SGML header page was tried first and read "COMPANY CONFORMED NAME: Alphabet Inc." as a name, which is why it is not used.

**BOUNDARY.**
- **The survey:** the 26 committed pages under `data/dossiers/` at main `6c22b222`. Each filer's newest original 10-K on its submissions document's recent page, filed by any day, read 2026-11-20. A 10-K/A is not read.
- **The 11:** rows built from B's comment text, each matched against its filer's same read.
- **Counts are of rows,** except "of 26", which counts filers.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$0.** SEC reads only, through the paced client and its cache, with the repo's default User-Agent, approved by the operator for this measurement (2026-11-20).
- **Text-mode parsing is loose.** An exhibit with no table gives one name per line ending in a corporate form, so a stray line such as an auditor's "LLP" signature would read as a name. Only TGT's exhibit among the 26 is text-mode. *Falsifier:* a text-mode list whose names include a line that is not a company.
- **`word_prefix` can over-match.** It is untested on non-own names until B's sample's 4 not-own rows are run. *Falsifier:* a not-own row matching at `word_prefix`.
- **The 59-row measurement is owed.** W86 is tracked on #1004's board, not in §5.0. When B's list lands, its result is appended here as an Amendment.
