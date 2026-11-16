---
id:
status: shipped
date: 2026-11-16
prs: [1088]
supersedes:
superseded-by:
---

# E5 reads a title-cased debt-agreement heading as it reads a capitals one. Five real debt contracts it refused before any model call now reach the model at their pages' next paid build: VRRM's revolver amendment, CNXC's two receivables-facility amendments and NFLX's two notes purchase agreements. On NFLX they take two of the four call slots, which pushes its December 2025 revolver past the cost bound. A refusal with no title read now says so, not that the exhibit "declares itself no agreement at all" (STATE row 63)

**WHAT.**
- *The defect.* `covenant_extract.agreement_title` read only a heading set in capitals: `_TITLE`'s
  words (`_W`) and nouns (`_NOUN`) are capitals only, and so is `_AMEND_HEAD`. On a title-cased
  heading it returned None, `is_debt_agreement(None)` is False, and E5 refused the exhibit as "not
  a debt agreement" before any model call. The QA flag then said the exhibit "declares itself no
  agreement at all", a fact the reader could not know.
- *The audit, first, at $0.* The real E5 loop ran over every committed page's pointer rows, with
  each exhibit read from the EDGAR cache (cache-only) and the model stubbed from the committed page
  (#1084's probe). It refused 30 located exhibits as not a debt agreement. 7 had a title read,
  23 had none. Each was then read by hand:

  | # | page | exhibit | pointer family | head opens | title read | debt / amendment read | title read now | hand read |
  |---|---|---|---|---|---|---|---|---|
  | 1 | BRBR | `0001193125-19-270862` · `d812149dex101.htm` | Revolving Credit Facility | AMENDED AND RESTATED LIMITED LIABILITY COMPANY AGREEMENT … | AMENDED AND RESTATED LIMITED LIABILITY COMPANY AGREEMENT | False / False | same | not debt: an LLC operating agreement |
  | 2 | BURL | `0001193125-26-116001` · `burl-ex10_39.htm` | material contracts (10-K exhibit index) | BURLINGTON STORES, INC. EXECUTIVE SEVERANCE PLAN … | — | False / False | — | not debt: a severance plan |
  | 3 | CNXC | `0001803599-24-000117` · `exhibit101-thirdamendmentt.htm` | Other Loans | Third Amendment to Receivables Financing Agreement … | — | False / False | RECEIVABLES FINANCING AGREEMENT | **debt**: the Third Amendment to its receivables financing facility |
  | 4 | CNXC | `0001803599-26-000027` · `exhibit1022-2025form10k.htm` | material contracts (10-K exhibit index) | Performance Restricted Stock Unit CONCENTRIX CORPORATION … | — | False / False | — | not debt: a PRSU award notice |
  | 5 | CNXC | `0001803599-23-000091` · `a033123exhibit101.htm` | Credit Facility | Strictly confidential CONCENTRIX CORPORATION … | — | False / False | — | not debt: a put option letter for an acquisition |
  | 6 | CNXC | `0001803599-25-000014` · `exhibit101-fourthamendment.htm` | Other Loans | Fourth Amendment to Receivables Financing Agreement … | — | False / False | RECEIVABLES FINANCING AGREEMENT | **debt**: the Fourth Amendment to the same facility |
  | 7 | EPAM | `0001352010-26-000015` · `exhibit1017-epamnonxempl.htm` | material contracts (10-K exhibit index) | exhibit1017-epamnonxempl Adopted April 11, 2017 … | — | False / False | — | not debt: a directors deferral plan |
  | 8 | FUBO | `0001493152-25-020163` · `ex10-1.htm` | 2029 Convertible Notes | REGISTRATION RIGHTS AGREEMENT by and between … | REGISTRATION RIGHTS AGREEMENT | False / False | same | not debt: registration rights |
  | 9 | FUBO | `0001628280-25-009420` · `fubo-20241231exx1026.htm` | material contracts (10-K exhibit index) | FUBOTV INC. EXECUTIVE SEVERANCE PLAN … | — | False / False | — | not debt: a severance plan |
  | 10 | FUBO | `0001493152-24-000126` · `ex10-1.htm` | 2029 Convertible Notes | fuboTV Inc. Exchange Agreement … | — | False / False | — | not debt by its head: an exchange of convertible notes; it names no instrument, and the notes' terms are in their indenture |
  | 11 | IT | `0000930413-17-000070` · `c86994_ex10-1.htm` | State of Connecticut Economic Development Loan | JPMORGAN CHASE BANK, N.A. 383 Madison Avenue … | — | False / False | — | a bank commitment letter ("Project Cobra Commitment Letter"): kept refused, an open question |
  | 12 | LLY | `0000059478-26-000013` · `lly-12312025x10kexhibit103.htm` | material contracts (10-K exhibit index) | Form of Revenue Growth Award under … | — | False / False | — | not debt: an award agreement |
  | 13 | NCNO | `0001902733-26-000022` · `exhibit1035secondamendment.htm` | material contracts (10-K exhibit index) | SECOND AMENDMENT TO OFFICE LEASE … | OFFICE LEASE | False / True | same | not debt: an office-lease amendment |
  | 14 | NFLX | `0001193125-18-134734` · `d567970dex101.htm` | Senior Unsecured Bridge Term Loan Facility | NETFLIX, INC. $1,900,000,000 5.875% Senior Notes due … | — | False / False | SENIOR NOTES DUE 2028 PURCHASE AGREEMENT | **debt**: the purchase agreement for its 5.875% notes due 2028 |
  | 15 | NFLX | `0001193125-25-308651` · `d65144dex101.htm` | Unsecured Delayed Draw Term Loan Credit Facility | WELLS FARGO BANK, NATIONAL ASSOCIATION … | — | False / False | — | a bank commitment letter ("Project Noble Bridge Commitment Letter"): kept refused, an open question |
  | 16 | NFLX | `0001065280-26-000034` · `ex102_q425.htm` | material contracts (10-K exhibit index) | NETFLIX, INC. 2011 STOCK PLAN … | — | False / False | — | not debt: a stock plan |
  | 17 | NFLX | `0001193125-14-037000` · `d671121dex101.htm` | Senior Unsecured Bridge Term Loan Facility | $400,000,000 NETFLIX, INC. 5.750% Senior Notes due … | — | False / False | SENIOR NOTES DUE 2024 PURCHASE AGREEMENT | **debt**: the purchase agreement for its 5.750% notes due 2024 |
  | 18 | NKE | `0000320187-26-000088` · `nke-5312026exhibit1029.htm` | material contracts (10-K exhibit index) | June 16, 2026 Dear David, … | — | False / False | — | not debt: an offer letter |
  | 19 | ORKA | `0001213900-26-026929` · `ea027330001ex10-9_oruka.htm` | material contracts (10-K exhibit index) | FORM OF GRANT NOTICE FOR RESTRICTED STOCK … | — | False / False | — | not debt: an RSU grant notice |
  | 20 | PARR | `0000821483-26-000005` · `a20251231ex1010-formofawar.htm` | material contracts (10-K exhibit index) | Restricted Stock Agreement PAR PACIFIC HOLDINGS, INC. … | INC. RESTRICTED STOCK AWARD AGREEMENT | False / False | same | not debt: a restricted stock award |
  | 21 | TECX | `0001193125-26-076793` · `tecx-ex10_4.htm` | material contracts (10-K exhibit index) | Tectonic Therapeutic, Inc. Amended and Restated … | — | False / False | — | not debt: a director compensation policy |
  | 22 | TGT | `0000027419-26-000016` · `tgt20260131-exhibit1018.htm` | material contracts (10-K exhibit index) | January 2026 … Dear Brian: … | — | False / False | — | not debt: a transition letter |
  | 23 | TGT | `0000027419-16-000060` · `form8-k_creditagreement105.htm` | 364-Day Unsecured Revolving Credit Facility | 8-K 1 form8-k_creditagreement105.htm 8-K UNITED STATES … | — | False / False | — | not debt: the 8-K's own cover document |
  | 24 | TJX | `0000109198-26-000008` · `tjx-20260131xexhibit1024.htm` | material contracts (10-K exhibit index) | THE TJX COMPANIES, INC. STOCK INCENTIVE PLAN … | — | False / False | — | not debt: a stock-plan amendment |
  | 25 | UBER | `0001552781-23-000469` · `e23472_ex10-1.htm` | 2025 Convertible Notes | [Dealer’s name] [Dealer’s address] … | — | False / False | — | not debt: a capped-call confirmation |
  | 26 | V | `0001403161-16-000027` · `exh22aroptionagreement.htm` | Unsecured Revolving Credit Facility | AMENDED AND RESTATED PUT-CALL OPTION AGREEMENT … | AMENDED AND RESTATED PUT-CALL OPTION AGREEMENT | False / True | same | not debt: a put-call option agreement |
  | 27 | VITL | `0001193125-26-073423` · `vitl-ex10_10.htm` | material contracts (10-K exhibit index) | Vital Farms, Inc. Non-Employee Director Compensation Policy … | — | False / False | — | not debt: a director compensation policy |
  | 28 | VRRM | `0001104659-18-041476` · `a18-15692_1ex10d1.htm` | 2021 Term Loan Due 2028 | GORES II SUBSCRIPTION AGREEMENT … | GORES II SUBSCRIPTION AGREEMENT | False / False | same | not debt: a SPAC-era subscription |
  | 29 | VRRM | `0000950170-25-072679` · `vrrm-ex10_1.htm` | Revolving Credit Facility | Amendment No. 4 to REVOLVING CREDIT Agreement … | — | False / True | REVOLVING CREDIT AGREEMENT | **debt**: Amendment No. 4 to its Revolving Credit Agreement |
  | 30 | WERN | `0000793074-26-000090` · `wern-20260127ex101.htm` | 22 Unsecured Credit Agreement | wern-20260127ex101 … STOCK PURCHASE AGREEMENT … | STOCK PURCHASE AGREEMENT | False / False | same | not debt: a stock purchase agreement |

  "Debt / amendment read" is `is_debt_agreement` and `is_amendment` at base. No `is_agreement`
  symbol exists: I searched `is_agreement\b` over `vinci/`, `tests/` and `scripts/`, and ran
  `git log --all -S"def is_agreement"`, and found none.
- *The wrong refusals: 5 of 30, in two failure shapes with one root.* In each, `_TITLE` found no
  capitals noun in the head's first 1,500 characters. `_BARE_NOUN` did not apply, and the capitals
  `_AMEND_HEAD` did not match, so the reader returned None.
  - **Shape A, a title-cased amendment heading that names its contract** (VRRM 1, CNXC 2). VRRM's
    is mixed, "Amendment No. 4 to REVOLVING CREDIT Agreement", and it fails on the title-cased noun
    alone. CNXC's two also read `is_amendment` False, since `_IS_AMENDMENT` is capitals only.
  - **Shape B, a title-cased heading led by the issuer, the principal and the coupon** (NFLX 2):
    "NETFLIX, INC. $1,900,000,000 5.875% Senior Notes due 2028 Purchase Agreement". Its maturity
    word, "due", is lowercase as well.
- *The correct refusals: 25.* All 7 refusals whose title was read are right. Of the 18 untitled
  ones, two are bank commitment letters (IT 2017 and NFLX 2025), headed by an address block and a
  code name. They are debt commitments, but their heads name no agreement, so they stay refused.
  Whether such a letter should reach the extractor is a question for the gate's vocabulary, not
  for this reader (below). FUBO's exchange agreement names no instrument in its head.
- *The fix* (`vinci/dossier/covenant_extract.py`). It adds one last branch to `agreement_title`,
  tried only where every earlier branch read nothing, so no title that was read before can change.
  - It takes the **heading run** (`_HEADING_RUN`): the words at the head's start before its first
    prose word. That is capitalised words, numbers and amounts, and only the lowercase words a
    title carries: `_TITLE`'s own of, to, and, the, and "due".
  - It upper-cases the run and reads it with `_TITLE`'s grammar ending in a **contract noun**
    (`_HEADING_TITLE`: AGREEMENT, INDENTURE, GUARANTY, GUARANTEE). The title is then normalised as
    a capitals title is.
  - `is_amendment` reads the same run. `_IS_AMENDMENT`'s case-sensitivity and its rationale are
    untouched: body prose never starts a head.
- *The flag.* With a title read, the flag is unchanged: "(E5) not a debt agreement — refused …
  declares itself “TITLE”". With none, it now reads "(E5) refused rather than extracted under the
  pointer's guess (FAMILY): no agreement title was read from the head of SRC". These are the
  renderer's words (`render._NO_TITLE_READ`, #1084), and the flag claims neither that the
  document is no agreement nor that it is not debt. No render file is touched.
- *Vintage.* `2026-11-16.title-cased-covenant-headings-are-read`, with `covenant_extract.py`
  re-pinned to it.

**WHY.** The pointer's family is the pointer's guess, and the document's own head decides
(#652's identify-or-refuse). A heading's case is typography, not identity. "Third Amendment to
Receivables Financing Agreement" and its capitals twin are the same document. Refusing one and
admitting the other is the gate selecting on FORM, the error CLAUDE.md's grade rule names.

*DOES THIS SELECT ON FORM?* Before the fix it did: the capitals-only reader selected on how the
filer set the heading, and so refused five debt contracts. After it, case no longer decides.
What still decides is the same as before:
- the heading's position, the run at the head's start, which is how a document identifies itself
  and not a form of disclosure;
- the gate's unchanged vocabulary of debt and not-debt words, which is a KIND, never a magnitude.

Two choices in the fix are form-shaped, and each was set by face validity on real heads, never by
an outcome:
- The run ends at the first prose word. Read past it, prose is a heading, which is
  `_IS_AMENDMENT`'s case.
- A title-cased title must end in a contract noun. A press release headlines in title case and
  names the instrument it announces. CNXC's 2026 release "Concentrix Prices $600 Million Senior
  Notes Offering" read as "MILLION SENIOR NOTES" and passed the gate until this limit (measured on
  the cache corpus during the build).

Nothing ranks capture from the title. The title only decides whether the extractor sees the
exhibit.

**HOW VERIFIED.**
- *The loop at head, stubbed* (same probe, same cache). Of the 30 refused at base, 25 stay
  refused and 5 reach the model. Per page:

  | page | now sent | pushed past the cost bound (`_MAX_EXHIBITS` = 4) | calls at base → head |
  |---|---|---|---|
  | VRRM | `0000950170-25-072679` · `vrrm-ex10_1.htm`, Amendment No. 4 to the Revolving Credit Agreement (720,280 chars) | none | 2 → 3 |
  | CNXC | `0001803599-24-000117` and `0001803599-25-000014`, the third and fourth amendments to its Receivables Financing Agreement (445,616 and 453,029 chars) | `0001803599-21-000215` · `exhibit101122721.htm`, the 2021 First Amendment to its Credit Agreement and Joinder Agreement (586,261 chars), which its page extracted | 3 → 4 |
  | NFLX | `0001193125-18-134734` and `0001193125-14-037000`, the purchase agreements for its 5.875% notes due 2028 and its 5.750% notes due 2024 (100,502 and 111,691 chars) | `0001193125-25-327462` · `d82688dex101.htm`, its SENIOR UNSECURED REVOLVING CREDIT AGREEMENT of December 2025 (406,266 chars), and `0001193125-19-094705` · `d721020dex101.htm`, the 2019 FIRST AMENDMENT AGREEMENT to its revolver (346,410 chars). Its page extracted both | 4 → 4 |

  No other page's sent set moves.
- *The reader over the whole cache.* The cache holds 3,575 EDGAR archive documents (htm or txt,
  index pages excluded). Each was read through `html_to_text`, as `_fetch_exhibit` reads it, by
  base and head. 9 reads change, and no other.
  - 6 are debt contracts: the five above, and CNXC's Fifth Amendment to the same receivables
    facility, which no committed pointer targets.
  - 3 are not, and the gate refuses each: BURL's exchange agreement for convertible notes, an LLY
    award agreement, and a VRRM press release whose headline ends "Termination of Agreement".

  Titled heads go 137 → 146, gate passes 86 → 92, and amendments 46 → 49 (CNXC's three).
- *Pins* (`tests/test_covenant_title_reader.py`, 19 nodes, on
  `tests/fixtures/covenant_title_reader/heads.json`). The fixture holds 33 real heads cut from the
  cache through `_fetch_exhibit`: the audit's 30 and 3 corpus heads. Each cut is the shortest at
  which base and head read it exactly as they read the full head (its README).
  - Positive, per shape: A on VRRM and CNXC ×2, and B on NFLX ×2.
  - Code-review round 0 found that `is_amendment`'s new branch tested `_AMEND_PREFIX`, anchored
    at ^, before stripping a filing id, which `agreement_title` strips first. A derived pin holds
    it: CNXC's real head with WERN's real filing-id lead in front still reads as an amendment.
    The same review built `_HEADING_TITLE` and `_TITLE` from one shared word grammar
    (`_TITLE_WORDS`), and `_TITLE`'s pattern is byte-identical.
  - Negative, per class of correct refusal (7 classes): every head is refused. The 7 titled
    refusals keep their exact titles. The press release is not titled. A derived TECX head with a
    contract name after its first prose word is not titled.
  - The audit count: exactly 5 pass (VRRM 1, CNXC 2, NFLX 2), all hand-read as debt, and 25 are
    refused.
  - End to end on VRRM's frozen block (#1084): the amendment is sent to the model, named
    REVOLVING CREDIT AGREEMENT, and GORES II is still refused with its title. On TECX's frozen
    block, the untitled flag reads "no agreement title was read from the head of".
  - Two existing pins move with the premise. `test_a_title_cased_heading_is_not_renamed_by_its_recital`
    now pins the title VRRM's heading gives, and the NKE end-to-end pin now pins the new flag
    words.
- *Fail first.* Run with base code, 9 of the 19 new nodes fail: every positive, the filing-id
  derivation, the audit count, VRRM end to end and the flag. So do both edited pins. The 10 that pass at base pin behaviour that
  must not change. Five mutations of the new code each red at least one pin:
  - NOTES may end a title-cased title: the press-release pins red.
  - No "due": NFLX ×2 and the audit count red.
  - Any lowercase word continues the run: the TECX derivation reds.
  - No comma after a capitalised word: NFLX ×2 and the audit count red.
  - `is_amendment` ignores the run: CNXC ×2 and the filing-id derivation red.
- *No committed page moves.* `refresh.refresh_fleet` re-rendered all 26 pages: 26 unchanged,
  0 moved and 0 refused, and `git status` showed nothing under `data/` or `frontend/`. Each page
  gains the change only at its next paid re-assembly.

**BOUNDARY.**
- The audit and the loop runs are at main `032d2fde` (2026-11-16). They cover the 26 committed
  `data/dossiers/*/dossier.json`, of which 24 have pointer rows, with 91 located exhibits (one
  target per accession).
- 86 of the 91 were read. 5 were unreadable cache misses, never read: MCK's 4 and WERN's
  `0000793074-26-000159`.
- The base outcomes are 49 extracted, 30 refused as not a debt agreement, 7 cost bound and 5 fetch
  failed. Head's are 46 extracted, 5 no terms returned (the stub answers no rows for an exhibit no
  committed row cites), 25 refused, 10 cost bound and 5 fetch failed.
- The cache is the operator's EDGAR cache at `data/cache/sec` in the primary checkout, read
  2026-11-16, cache-only: a miss raised, and nothing was fetched.
- The corpus is every cached `/Archives/edgar/data/` document ending .htm, .html or .txt whose
  file name does not contain "index": 3,575 documents. Exhibit sizes are `html_to_text`
  characters.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- *NFLX's next paid build loses its current revolver.* Its page carries terms from its December
  2025 SENIOR UNSECURED REVOLVING CREDIT AGREEMENT and its 2019 first amendment. At head, two notes
  purchase agreements take those two slots, and the 2014 one is for notes that matured in 2024.
  The reader is right to read them, since each is the contract under which NFLX sold its notes,
  and the gate passes NOTES as it always has. What drops the revolver is the selector:
  `_core_agreement_exhibits` orders by the pointer's family and round-robins, and NFLX's pointer
  files both purchase agreements under a debt family ("Senior Unsecured Bridge Term Loan
  Facility"). **This is the operator's decision, and none of the options is built.** Each was
  simulated at $0 with the same stubbed loop over all 24 pages, the option patched in scratch
  only:
  - **(a) Admit the notes purchase agreements, as built.** NFLX sends the 2018 and 2014 purchase
    agreements, the 2009 credit agreement (`0001193125-09-194962`) and the 2021 second amendment
    (`0001193125-21-193187`). Its December 2025 revolver, its 2019 amendment and its January 2026
    incremental commitments (`0001193125-26-015951`) are past the bound.
  - **(b) Rank notes purchase agreements below every other target in the bound's order** (a
    selector change). NFLX sends the 2009 credit agreement, the 2021 second amendment, the
    December 2025 revolver and the 2019 amendment, the four it sends at base. Both purchase
    agreements and the January 2026 commitments are past the bound.
  - **(c) Keep notes purchase agreements refused** (a gate vocabulary change). NFLX sends the
    same four as under (b), and both purchase agreements are refused, under their titles.
  - Under (b) and (c), only NFLX differs from (a) among the 24 pages, because no other page
    targets a notes purchase agreement. VRRM and CNXC gain the same under all three.

  CNXC's 2021 first amendment drops the same way under every option. CNXC still sends its 2023 amendment and
  restatement and its 2025 amended and restated credit agreement.
- *Spend at the next paid builds.* VRRM makes 1 more call (720,280 chars) and CNXC 1 more, a net
  +312,384 chars. NFLX makes the same number of calls with 540,483 fewer chars.
- *VRRM's amendment may not merge with its base.* It is titled REVOLVING CREDIT AGREEMENT, and the
  A&R agreement VRRM's page extracts is titled AMENDED AND RESTATED REVOLVING CREDIT AGREEMENT.
  `governing_terms` groups by title, so the two may print as separate groups. This normalisation
  gap predates the fix (CNXC's "CREDIT AGREEMENT" and "AMENDED AND RESTATED CREDIT AGREEMENT"
  split the same way). It is found here and not fixed.
- *Bank commitment letters stay refused.* That is 2 refused (IT, NFLX) and 2 more cost-bound
  targets (NFLX January 2026, WLK 2016). Each is a debt commitment whose head is an address block
  and a code name. This is the gate's open question, not this reader's.
- *A capitals press-release headline naming notes would pass the gate.* This is not new: the
  capitals reader always took NOTES. It was measured at 0 cases on the cached ex-99 and press
  files.
- *Sibling wording outside this PR's files.* `schemas.py`'s comment on
  `CovenantExhibitOutcome.declared_title` still says "its head declares no agreement at all". It is
  a comment, changing no behaviour, and is left for a PR that may touch `schemas.py`.
- *Falsifier.* Either of two things on a re-assembled page:
  - E5 refuses a head that names a debt contract at its start, in any case;
  - E5 sends the model an exhibit under a title-cased title that a hand read finds is not the
    document's own name, as the press release's "MILLION SENIOR NOTES" was not.
