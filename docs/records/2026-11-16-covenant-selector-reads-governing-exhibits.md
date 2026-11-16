---
id:
status: shipped
date: 2026-11-16
prs: [1091]
supersedes:
superseded-by:
---

# The covenant phase targets every exhibit a located pointer row lists that governs debt by its own title, not one exhibit per pointer chosen by its file name: VRRM's 2025 term-loan restatement is now sent and supersedes the 2021 one main sent, and NKE's five-year agreement, NFLX's delayed-draw term loan agreement and TJX's 2030 revolving credit agreement are sent. Two exhibits of one filing never share a governing group, so WLK's IKE Zone figure no longer prints under its GO Zone loan's cite. Over the 24 pages with pointer rows a full paid rebuild makes 60 covenant calls, not 48. No committed page moves until its next paid re-assembly (STATE row 63)

**WHAT.**
- *The brief.* The coordinator, after #1090's audit found that the selector targets one exhibit per
  located accession: widen the target selector so the live governing documents a located pointer
  row lists are not dropped. Audit first at $0, set the rule by face validity, and read each new target
  through #1090's coverage rule. Due before VRRM's next paid build (re-rehearsal around
  2026-12-07).
- *The defect.* `_core_agreement_exhibits` targeted ONE exhibit per located pointer:
  `(core or r.exhibits)[:1]`, the first exhibit whose FILE NAME holds a word of `_CORE_AGREEMENT`,
  else the filing's first exhibit. No other exhibit of the filing was ever sent. VRRM's
  `vrrm-ex10_2.htm`, the 2025-10-17 Amendment and Restatement Agreement No. 2 of its first-lien
  term loan, sat second in its A&R revolver's filing. So VRRM's next paid build would have sent
  the 2021 restatement it restates (LIBO Rate + 3.25%) and never the terms in force.
- *The audit, first, at $0* (the table is at the end). Every untargeted exhibit on the 24 pages
  with pointer rows was read from the EDGAR cache through `_fetch_exhibit`, as the loop reads it,
  with E5's own readers, then read by hand. Of the 60:
  - **14 govern debt** (gate passes). Six are live by the CIQ panel: VRRM ex10_2, NKE's five-year
    agreement, NFLX's delayed-draw term loan agreement, TJX's 2030 revolving credit agreement,
    CNXC's fifth amendment to its receivables financing agreement (a plain amendment, not a
    restatement), and BURL's 2014 first amendment to its ABL agreement. The other eight are
    **not classifiable from located documents** (below);
  - **9 are credit support**: the gate passes 6 (two pledge agreements, an IP security agreement,
    a guarantee and collateral agreement, a limited-recourse guaranty, a performance guaranty)
    and refuses 3 (two intercreditor agreements, a borrower assumption agreement);
  - **1 governs debt but reads no title**: PARR's letter-form Fifth Amendment to Par Wyoming's
    Third Amended and Restated Loan Agreement (`0000821483-17-000034 ·
    exhibit101-5thamendmenttow.htm`). E5 reads no title from a letter head, so the gate refuses it,
    as at main. **Recorded, not fixed:** a title-reader item;
  - **3 are cache misses** (MCK), unreadable at $0;
  - **33 are other documents**: stock plans and awards, employment and transition papers, tax and
    investor agreements, a lease, a press release, an 8-K cover, a bank commitment letter, and
    EPAM's six page images (`.jpg`), which are now never read (N3).
- *The rule* (`vinci/dossier/covenant_extract.py`).
  1. **Every document a located pointer row lists is read** (`_located_exhibits`). A row lists the
     filing's exhibits the locator kept, not every document of the filing: an 8-K row keeps the
     agreement-named documents, a 10-K row the EX-10 files. Each pointer's primary, as
     `_core_agreement_exhibits` has always picked it, is followed at once by the other documents
     its row lists. The primary is targeted, read and refused exactly as before, and a primary of
     any pointer stays a primary whichever pointer lists its filing first. Only a document (.htm,
     .html, .txt) is read; a page image never is (N3, below).
  2. **Another exhibit is a TARGET when its own title names a contract that governs debt**
     (`_governs`). That is a debt agreement (`is_debt_agreement`) the gate admits for at least one
     word that is not credit support (SECURITY, PLEDGE, GUARANTY, GUARANTEE). So a credit, loan,
     financing or receivables agreement, an indenture, notes, a facility, or an amendment of any of
     them is a target, and so are "LOAN AND SECURITY AGREEMENT" and "CREDIT AND GUARANTY
     AGREEMENT". A title the gate admits ONLY for credit-support words is left to the agreement it
     secures, as `_CORE_AGREEMENT` always left it.
  3. **One that cannot be read is a target too.** It may govern debt, so it reads `fetch_failed`
     with the flag a primary's fetch failure has always had. As #1090 rules, the page then
     supersedes nothing.
  4. **The rest are read for who they are and never sent**, as #1090's round 2 reads them, and no
     outcome is written for them. A page lists only its targets.
  5. **Every target is read by the coverage rule**, so a newly targeted restatement supersedes
     what it restates. For VRRM's that needed two forms the reader did not know, each read on
     VRRM's real restatements:
     - a term defined in the parenthetical at the agreement's date, however long its history
       (`_BIND_RECITAL_AFTER`): "the Amended and Restated First Lien Term Loan Credit Agreement
       dated as of March 26, 2021 (as amended by that certain Amendment No. 1, … the “Existing
       Credit Agreement”)". The parenthetical runs 454 characters, past `_BIND_RECITAL`'s 240. An
       agreement named inside it binds nothing (`_second_agreement`, #1090's F5);
     - the operative clause in the passive: "The Existing Credit Agreement is, effective as of the
       Second Restatement Effective Date and immediately after giving effect to the incurrence of
       the Initial Term Loans, hereby amended and restated". Only the present "is … hereby" form
       counts; "was amended and restated" is history.
  6. Outcomes are in the located order: a target follows its row's primary. Sending is in another
     order (code review, round 0): every primary before any other exhibit a row lists, purchase
     agreements last. So the round-robin's purpose holds: a row listing many exhibits that govern
     debt never spends the guard on one facility while another facility's primary goes unsent.
- *The same-filing tie* (coordinator's ruling (a), 2026-11-16).
  - A filing's exhibits share its filing date. `governing_terms` groups rows by the agreement's
    title, or by the pointer family when the title is ambiguous, and lets the latest PRESENT row
    govern. So two exhibits of one filing in one group could not be ordered: the later in the list
    governed every term, and the earlier one's base was cited for it.
  - One exhibit per pointer was sent until now, so this never arose. Under the selector it would
    at 3 filings on 2 pages:
    - WLK's GO Zone and IKE Zone bond loan agreements (`0001193125-10-276447`, `dex101.htm` $89m
      and `dex102.htm` $65m, both "LOAN AGREEMENT" of November 1, 2010). IKE's figure would have
      printed under GO Zone's "Source §";
    - PARR's 2015 and 2017 pairs.
  - Now **two exhibits of one filing never share a group**. Where two files of one accession share
    a label, each file's rows form their own group, labelled with the file (`<label> · <file>`).
    This is in `governing_terms` and its mirror `governingTerms` in `dossier.js`, both reading the
    file from the row's machine-set `source_ref` through one helper each (`_exhibit_of`,
    `_exhibitFileOf`). A label that only one file per filing reaches is unchanged.
- *Two defects #1090's verification deferred here* (the coordinator: "your widening is what
  exposes them"), each fixed behind pins that fail first.
  - **N1 (medium): a recital's term could bind to an AMENDMENT's date.**
    - `_GAP_AGREEMENT` stopped at "No.", so "Amendment No. 1 to the Term Loan Agreement" read as
      "1 to the Term Loan Agreement": a second agreement with no AMENDMENT in it. The true bind was
      refused.
    - The overlapping restart then began at "the Term Loan Agreement, dated as of June 13, 2018"
      inside the amendment's name, and bound the term to the amendment's date. UBER's "Existing 2016
      Loan Agreement" read as of 2018-06-13.
    - A recital of NKE's shape, "(as amended by the First Amendment to the Credit Agreement, dated as
      of March 8, 2024, the “2022 Credit Agreement”)", displaced NKE's live 2024 364-day CREDIT
      AGREEMENT of that day.
    - The fix: the chain reads "No. N" as a word of a name, and a recital whose agreement is the
      object of "Amendment … to" (`_OBJECT_OF_AMENDMENT`, read before its start) binds nothing. The
      fix covers all three recital binders: the parenthetical, the overlapping restart and this PR's
      `_BIND_RECITAL_AFTER`.
  - **N3 (low): the sibling read fetched page images.** EPAM's 2026 10-K row lists six `.jpg`. Each
    was fetched, and one that failed switched the page to "supersedes nothing". Now ONLY A DOCUMENT
    (.htm, .html, .txt; `_DOCUMENT`, the locator's own rule for a 20-F's exhibits) is read, picked
    as a primary or targeted. Over the 26 committed pages' pointer rows, 145 exhibits are `.htm`
    and 6 `.jpg`; no primary is an image.
- *Approved (PREVIEW RULE).* The operator, relayed by the coordinator: **"Approve as shown
  (Recommended)"**. That covers the ` · <file>` label when two exhibits of one filing share a group,
  as `covenant-selector-preview/README.md` in the coordinator's notes folder shows it: WLK's page
  in Markdown and the production `renderDossier`, the main body, the provenance card collapsed and
  force-open, and the print PDF.
- *Vintage.* `2026-11-16.covenant-selector-reads-a-filings-governing-exhibits`, following
  `2026-11-16.covenant-coverage-rule`.

**WHY.** A credit analyst reads every agreement a filing carries that governs debt. A filing that
restates two facilities carries two agreements, and each governs its own debt. The one-per-pointer
rule read one and dropped the other, by file name and by position. And two different agreements
must never print as one, whatever their shared label and date.

*DOES THIS SELECT ON FORM?* The old selector did; this one reads substance, with two named
form-shaped residues.
- The old rule chose by FILE NAME and POSITION: the first exhibit whose name holds a word like
  "creditagree", else the first exhibit. `vrrm-ex10_2.htm` names no such word, and it came second.
- The new rule reads what each document declares itself in its own heading: a contract that
  creates or amends debt, or one that secures or guarantees debt another agreement creates. That
  is the document's legal function, its substance. No magnitude, size, currency or disclosure form
  enters it.
- Residue 1, title vocabulary. A governing contract whose title names ONLY credit-support words
  would be left out. None of the 92 cached documents the gate passes is one: each of the 10 titles
  the carve-out leaves is a guaranty, pledge, or security or collateral agreement by hand read
  (PLEDGE AGREEMENT ×3, SECURITY AGREEMENT, INTELLECTUAL PROPERTY SECURITY AGREEMENT, GUARANTY
  AGREEMENT, LIMITED RECOURSE GUARANTY, PERFORMANCE GUARANTY, RESTATED GUARANTEE AND COLLATERAL
  AGREEMENT, AMENDED AND RESTATED GUARANTY AND SECURITY AGREEMENT). The direction of error is
  chosen: a credit-support document read as governing costs a call, and the rule leaves out only
  what holds no governing word.
- Residue 2, a heading the reader cannot read. A governing document with no title read is not
  targeted (PARR's letter amendment). That is the title reader's limit, recorded, not new here.
- The tie fix splits by filing identity (one accession, two files), not by any form of the
  documents.
- Set by face validity on the real documents, never by outcome. The hand verdicts were made before
  the rule was measured, and no forward return enters anything here.

**HOW VERIFIED.**
- *The audit* (table at the end): 60 exhibits, each read by hand. The reads (title, gate,
  amendment) are identical at main `51784e53` and at #1090's `995e3f21`.
- *The reader over the whole cache.* 3,575 cached EDGAR archive documents; the gate passes 92.
  - The two reader forms add **3 displacements**, all in VRRM's restatements:
    - the 2025 one displaces the 2021 first-lien term loan agreement;
    - the 2021 one displaces the 2018 agreement;
    - the 2025 one's security-agreement restatement binds through a recital #1090's binder already
      read, to a joinder's date. It matches no exhibit.
  - **N1 over every bind** (`_displacing_words` patched to accept any term, so every bound pair is
    listed): 151 binds before N1 and 151 after. Exactly 3 move: UBER's three term-loan amendments
    (`…21-000058`, `…23-000080`, `…23-000109`) lose the wrong bind to 2018-06-13 and gain the right
    one to 2016-07-13. No correct bind is lost and no wrong one gained; displacements and links do
    not move (UBER's clauses restate parts).
  - Within a CIK, links go from **14 to 16**. Both new links are real supersessions by hand read:
    0 false.
  - The passive form reads 49 times over the 92. The subject guard refuses the 46 that restate a
    PART ("Section 6.01(d) of the Credit Agreement is hereby amended and restated"); the 3 it admits
    are VRRM's whole-agreement restatements.
- *The real loop over all 26 pages* (24 with pointer rows; cache only; the model stubbed from each
  committed page's own term rows; base `995e3f21` against head).
  - Outcomes at base: 41 extracted, 7 no terms returned (48 sent), 27 refused, 10 superseded,
    1 terminated, 5 fetch failed.
  - At head: 39 extracted, 21 no terms returned (60 sent), 27 refused, 12 superseded,
    1 terminated, 8 fetch failed.
  - The two new supersessions: VRRM's 2021 restatement, by ex10_2 ("The Existing Credit Agreement
    is, …, hereby amended and restated"); TJX's 2021 agreement, by its 2025 2030 RCA ("amend and
    restate the 2026 Revolving Credit Agreement").
  - The 3 new fetch failures are MCK's cache misses, now targets. At a paid build they are
    fetched.
  - A stubbed model answers no rows for an exhibit no committed row cites, so "no terms returned"
    at head means "sent", not a model's answer.
- *The tie, measured:* one synthetic row per sent exhibit through the real `governing_terms`.
  - 9 filings send two or more exhibits.
  - At `995e3f21`'s code 3 of them lose an exhibit's value to a same-day sibling (WLK, and PARR
    twice). At head, 0 do.
  - The one value still not shown at head is BURL's 2014 ABL first amendment. Four later-dated
    amendments of the same agreement (2018–2025) govern ahead of it, which is the chain behaving
    as it should.
- *Pins* (`tests/test_covenant_selector.py`, 52 nodes, on `tests/fixtures/covenant_coverage_rule/`'s
  real cuts).
  - The brief's: VRRM's ex10_2 targeted right after the revolver and sent, and its 2021
    restatement superseded citing ex10_2's words, on both renderers end to end.
  - The six governing siblings targeted and sent (NKE five-year, NFLX DDTL, TJX 2030 RCA, CNXC
    RFA 5th amendment, AMZN 2023 364-day, BURL 2014 ABL amendment). TJX's 2021 agreement superseded.
  - Credit support (BURL's IP security agreement and pledge) and non-debt (VRRM's tax receivable
    agreement) read, never targeted.
  - An unread sibling is a target, fetch_failed with its flag, and the page supersedes nothing.
  - `_governs` on 12 real governing titles, 8 real credit-support titles and 4 non-debt ones.
  - The located order; a primary of any pointer stays a primary.
  - The reader's two forms on VRRM's real clauses; PARR's real restated PART displaces nothing;
    "was amended and restated" is history; an agreement inside the parenthetical binds nothing.
  - N1: UBER's real recital binds 2016-07-13 only, and the NKE shape, derived from NKE's real
    five-year agreement in both amendment forms, displaces only the 2022 agreement. N3: no image on
    EPAM's real rows is fetched, targeted or made a primary.
  - The tie: WLK's real pair (one derived row: the IKE principal, quoting `dex102.htm`'s own
    cached clause), as a unit pin and end to end on both renderers (web row equals Markdown row);
    and, over the living corpus, no committed page splits a group.
- *Fail first.* With main `71f9d9bb`'s `covenant_extract.py` and `dossier.js` (#1090 merged;
  its code is `995e3f21`'s), 49 of the 52 new nodes fail. The 3 that pass there are negatives,
  which hold trivially when nothing is widened; the capital-"The" one was red on this branch
  before the review's fix. Each negative was also shown live by a mutation of head's code that removes one piece,
  each reddening its pin:
  - `_governs` admitting credit support;
  - any titled sibling promoted;
  - an unreadable sibling skipped quietly;
  - no parenthetical binder;
  - the parenthetical binder ignoring a second agreement;
  - the passive form admitting the past without "hereby" (each of "is" and "hereby" alone holds
    the pin, so only the pair reddens it);
  - the subject guard off;
  - siblings never promoted;
  - the split applied to every group (reds the corpus pin);
  - the JS mirror never splitting (reds the end-to-end pin);
  - the gap chain without "No." (reds UBER's pin); no amendment-object guard (reds UBER's and both
    NKE pins); siblings that may be images, and a primary that may be one (each reds its N3 pin).
  The 5 N1 and N3 nodes also fail at this PR's own earlier commit `e563c013`.
- *Pins that move with the premise.* #1090's harnesses (`_run`, `_nflx_run`, the BURL plan's
  stub) now assert one outcome per TARGET in the located order. 14 of #1090's pins move: each
  expected send list grows by the governing sibling its row lists, and each says so in a
  "MOVED WITH THE SELECTOR" note. The sibling-pool pin (F1) is re-homed on BURL's real IP security
  agreement, because VRRM's ex10_2 is now a target. VRRM's two restatement cuts are re-cut (the
  fixture README). `test_dossier.py`'s MVST fake now serves the 8-K cover and the guaranty their
  real heads.
- *Committed pages do not move.*
  - All 26 went through `refresh.refresh_fleet`: 26 unchanged, 0 moved, 0 refused, 0 skipped,
    `data/` byte-identical.
  - Each committed `dossier.json` rendered through base and head `render_markdown` and
    `renderDossier` (node): 26 of 26 byte-identical on each.
- *Code review, round 0* (`/code-review high --fix`, on the branch after main `71f9d9bb` was
  merged in): 7 findings.
  - 4 fixed, each behind a pin that fails on the code before the fix where it changes behaviour:
    1. the subject guard read only a lowercase "the", while the passive form admits "The": "Section
       6.01(d) of The Credit Agreement is hereby amended and restated" displaced the agreement
       (`test_a_restated_part_displaces_nothing_whatever_the_case_of_its_the`, derived from PARR's
       real clause);
    2. past the guard, a row's siblings were sent before other families' primaries
       (`test_past_the_guard_every_primary_is_sent_before_any_sibling_amzn`, AMZN's real fixture
       with the guard at 2). The send order is now every primary first. No page reaches the guard,
       so no outcome moves;
    3. the `_MAX_EXHIBITS` comment's "WHY 10" stated the old busiest page and a target bound the
       selector removed;
    4. the located list was computed twice.
  - 1 dismissed: the primary is still gated by `is_debt_agreement`, not `_governs`, so a guaranty
    that is a row's primary is still sent. That path is deliberately unchanged. BURL's 2020 security
    agreement is a sent primary on its committed page, and the brief was to widen, not to narrow.
  - 2 deferred as one (grouping by identity, under WHAT IT COSTS).
- *Impact and suite:* (to fill).

**BOUNDARY.**
- Pages: the 26 committed `data/dossiers/*/dossier.json` at main `51784e53`. #1090 changes no page,
  so they are the same at `995e3f21`. 24 have pointer rows: 91 located pointers, 151 exhibit
  slots, 91 primary targets, 60 others. GOOGL and ROST have none.
- Cache: the operator's EDGAR cache `data/cache/sec` in the primary checkout, read 2026-11-16,
  cache only: a miss raised, and nothing was fetched.
- Corpus: every cached `/Archives/edgar/data/` document ending .htm, .html or .txt whose name does
  not contain "index": 3,575, of which the gate passes 92.
- Costs: the 55 committed run lines in `data/snapshots/assembly_runs/`, 107 successful
  `covenant_terms` calls, all claude-opus-4-8, at the list price in `vinci.config.LLM_PRICE_PER_MTOK`
  ($5 in, $25 out per million tokens): median $0.67, mean $0.69 a call, mean 1,926 output tokens.
  An added or dropped exhibit is priced at its chars / 2.87 (#1090's chars per token) input tokens
  plus 1,926 output tokens.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- *At each page's next paid build* (est., method above; base `995e3f21` → head):

  | page | calls | est. $ | what |
  |---|---|---|---|
  | AMZN | 4 → 5 | +0.56 | sends its 2023 364-day agreement (292,985 chars) |
  | BRBR | 1 → 2 | +1.17 | sends its 2019 credit agreement (644,426) |
  | BURL | 6 → 7 | +1.05 | sends its ABL agreement's 2014 first amendment (575,441) |
  | CNXC | 3 → 4 | +0.07 | sends its RFA fifth amendment (11,787) |
  | NFLX | 5 → 6 | +0.64 | sends its December 2025 delayed-draw term loan agreement (342,410) |
  | NKE | 1 → 2 | +0.56 | sends its five-year agreement (291,066) |
  | PARR | 4 → 8 | +0.27 | sends four 2015 and 2017 amendments (6,476–15,910 each) |
  | TJX | 2 → 3 | +0.09 | sends its 2030 RCA (+0.74) and its 2020 second amendment to the 2024 RCA (+0.12); skips its 2021 agreement (−0.77) |
  | VRRM | 2 → 2 | +0.10 | sends its 2025 term-loan restatement (+1.34); skips the 2021 one (−1.24) |
  | WLK | 5 → 6 | +0.28 | sends its IKE Zone loan agreement (135,264) |
  | MCK | 0 → 0 | — | 3 more targets, cache misses at $0; read at the paid build |
  | 13 others | unchanged | 0 | |
  | **all 24** | **48 → 60** | **+4.80** | |

- *Not classifiable from located documents: 8, each SENT under the rule* (about $2.41 of the
  +$4.80). A dead document the words cannot show dead is read, as #1090 rules ("an unclassifiable
  one is READ"):
  1. AMZN `0001104659-23-113444 · tm2329405d1_ex10-2.htm`, its 2023 364-day agreement. The
     panel's 364-day facility runs to 2027-10-01, likely a later renewal;
  2. BRBR `0001193125-19-270862 · d812149dex109.htm`, its 2019 credit agreement. The panel carries
     notes and a 2030 revolver, no term loan;
  3. PARR `0001193125-15-116573 · d902717dex104.htm`, Par Petroleum's delayed-draw term loan's
     fourth amendment;
  4. PARR `0001193125-15-116573 · d902717dex105.htm`, HIE's ABL second amendment and waiver;
  5. PARR `0001193125-15-116573 · d902717dex106.htm`, HIE Retail's first amendment;
  6. PARR `0000821483-17-000034 · ex103-2017x06x28amendmentn.htm`, the KeyBank credit agreement's
     Amendment No. 2;
  7. TJX `0001157523-20-000793 · a52222014ex10_2.htm`, the second amendment to its 2024 RCA. The
     panel carries only its 2029 and 2030 revolvers;
  8. WLK `0001193125-10-276447 · dex102.htm`, its IKE Zone bond loan agreement.
- *Credit support is not sent.* A guaranty, pledge or security agreement beside a credit
  agreement can state collateral or guarantors that the credit agreement states only by
  reference. Falsifier: a re-assembled page whose "Security / collateral / guarantors" term is
  UNKNOWN while a located credit-support document beside its credit agreement states it.
- *An unreadable sibling now prints a line* ("could not be fetched") at a build whose fetch fails.
  It may be a governing document, so the page says so rather than dropping it silently.
- *A later amendment under a split label stands in a group of its own* (code review, round 0,
  DEFERRED). If one filing carries two exhibits under one label and a LATER filing amends one of
  them under the same label, that amendment cannot join either split group: each original shows
  its own value as governing, and the amendment shows its own, with no "amended by" between them.
  - Measured exposure: 0 labels. On the 24 pages' head sends, the two split labels (WLK's "Term
    Loans Due 2026", PARR's "CREDIT AGREEMENT") are reached by no other filing.
  - The cheap fix is unavailable. A term row carries its exhibit's title and an amendment bit, not
    which agreement it is or amends, so `governing_terms` cannot tell which original a later
    amendment amends. The fix is to group by identity: store E5's `AgreementKey` (own and base) on
    each term row, and group by it in `governing_terms` and `dossier.js`. That is a schema change of
    its own.
  - Falsifier: a re-assembled page with a group labelled `<label> · <file>` and a bare `<label>`
    group from another filing.
- *Split groups repeat a label with a file.* On WLK and PARR at their next paid build, the reader
  sees one table per exhibit, named by file. Two amendments of one agreement in one filing (PARR's
  2017 pair) show as two groups, because the filing date cannot say which governs.
- *Falsifier.* A re-assembled page on which:
  - an exhibit beside a primary that governs debt by its own title is absent from the outcomes; or
  - a superseded line cites a later exhibit whose words name another agreement; or
  - a governing group holds two exhibits of one filing.

**THE AUDIT TABLE** (main `51784e53` pointer rows, cache only, E5's readers; "outcome at head" is
the stubbed loop at this PR's code; "no outcome" means read for who it is, never sent).

| # | page | filed | exhibit | title read | gate | hand class | outcome at head | hand note |
|---|---|---|---|---|---|---|---|---|
| 1 | AMZN | 2023-11-01 | `0001104659-23-113444` · `tm2329405d1_ex10-2.htm` | 364-DAY REVOLVING CREDIT AGREEMENT | passes | GOVERNS | no_terms_returned | 364-day agreement of 2023-11-01; nothing located shows it ended (the panel's 364-day facility runs to 2027-10-01, likely a later renewal); read |
| 2 | BRBR | 2021-02-26 | `0001772016-21-000029` · `ex991-termloanbrepricing02.htm` | — | refuses | OTHER | no outcome (read only) | a press release on the repricing the targeted Amendment No. 2 made |
| 3 | BRBR | 2019-10-21 | `0001193125-19-270862` · `d812149dex102.htm` | EMPLOYEE MATTERS AGREEMENT | refuses | OTHER | no outcome (read only) | not debt: “EMPLOYEE MATTERS AGREEMENT” |
| 4 | BRBR | 2019-10-21 | `0001193125-19-270862` · `d812149dex103.htm` | INVESTOR RIGHTS AGREEMENT | refuses | OTHER | no outcome (read only) | not debt: “INVESTOR RIGHTS AGREEMENT” |
| 5 | BRBR | 2019-10-21 | `0001193125-19-270862` · `d812149dex104.htm` | TAX MATTERS AGREEMENT | refuses | OTHER | no outcome (read only) | not debt: “TAX MATTERS AGREEMENT” |
| 6 | BRBR | 2019-10-21 | `0001193125-19-270862` · `d812149dex105.htm` | TAX RECEIVABLE AGREEMENT | refuses | OTHER | no outcome (read only) | not debt: “TAX RECEIVABLE AGREEMENT” |
| 7 | BRBR | 2019-10-21 | `0001193125-19-270862` · `d812149dex106.htm` | MASTER SERVICES AGREEMENT | refuses | OTHER | no outcome (read only) | not debt: “MASTER SERVICES AGREEMENT” |
| 8 | BRBR | 2019-10-21 | `0001193125-19-270862` · `d812149dex107.htm` | FORM OF INDEMNIFICATION AGREEMENT | refuses | OTHER | no outcome (read only) | not debt: “FORM OF INDEMNIFICATION AGREEMENT” |
| 9 | BRBR | 2019-10-21 | `0001193125-19-270862` · `d812149dex108.htm` | BORROWER ASSIGNMENT AND ASSUMPTION AGREEMENT | refuses | SUPPORT | no outcome (read only) | borrower assignment and assumption agreement: BellRing LLC assumes Post's term loan, whose terms are the credit agreement's (the gate refuses it) |
| 10 | BRBR | 2019-10-21 | `0001193125-19-270862` · `d812149dex109.htm` | CREDIT AGREEMENT | passes | GOVERNS | no_terms_returned | the 2019 credit agreement the targeted 2021 Amendment No. 2 amends; the panel carries notes and a revolver to 2030, no term loan, so probably replaced in 2022 by an agreement no pointer locates; read |
| 11 | BURL | 2020-04-16 | `0001193125-20-109457` · `d883886dex102.htm` | INTELLECTUAL PROPERTY SECURITY AGREEMENT | passes | SUPPORT | no outcome (read only) | intellectual property security agreement |
| 12 | BURL | 2020-04-16 | `0001193125-20-109457` · `d883886dex103.htm` | PLEDGE AGREEMENT | passes | SUPPORT | no outcome (read only) | pledge agreement |
| 13 | BURL | 2020-04-16 | `0001193125-20-109457` · `d883886dex104.htm` | AMENDED AND RESTATED INTERCREDITOR AGREEMENT | refuses | SUPPORT | no outcome (read only) | A&R intercreditor agreement (lien priority; the gate refuses it) |
| 14 | BURL | 2020-04-16 | `0001193125-20-109457` · `d883886dex105.htm` | PARI PASSU INTERCREDITOR AGREEMENT | refuses | SUPPORT | no outcome (read only) | pari passu intercreditor agreement (the gate refuses it) |
| 15 | BURL | 2014-08-18 | `0001193125-14-313404` · `d772516dex102.htm` | SECOND AMENDED AND RESTATED CREDIT AGREEMENT | passes | GOVERNS | no_terms_returned | FIRST AMENDMENT TO the ABL's Second A&R Credit Agreement of 2011-09-02, a live chain (ABL on the panel to 2030-07-25) |
| 16 | CNXC | 2026-01-28 | `0001803599-26-000027` · `exhibit1023-202510xk.htm` | — | refuses | OTHER | no outcome (read only) | an RSU award notice |
| 17 | CNXC | 2026-01-28 | `0001803599-26-000027` · `exhibit1024-2025form10xk.htm` | — | refuses | OTHER | no outcome (read only) | an employee stock purchase plan |
| 18 | CNXC | 2025-04-11 | `0001803599-25-000111` · `exhibit102041125.htm` | RECEIVABLES FINANCING AGREEMENT | passes | GOVERNS | no_terms_returned | Fifth Amendment to the Receivables Financing Agreement of 2020-10-30, a live chain (securitization facility on the panel); a plain amendment, not a restatement |
| 19 | CNXC | 2023-03-31 | `0001803599-23-000091` · `a033123exhibit102.htm` | INVESTOR RIGHTS AGREEMENT | refuses | OTHER | no outcome (read only) | not debt: “INVESTOR RIGHTS AGREEMENT” |
| 20 | CNXC | 2023-03-31 | `0001803599-23-000091` · `a033123exhibit103.htm` | — | refuses | OTHER | no outcome (read only) | a bank commitment letter (bridge facility), refused as the other commitment letters are |
| 21 | EPAM | 2026-02-26 | `0001352010-26-000015` · `exhibit1017-epamnonxempl001.jpg` | — | refuses | OTHER | never read (an image, N3) | an image page of the filing (JPEG bytes, no text) |
| 22 | EPAM | 2026-02-26 | `0001352010-26-000015` · `exhibit1017-epamnonxempl002.jpg` | — | refuses | OTHER | never read (an image, N3) | an image page of the filing (JPEG bytes, no text) |
| 23 | EPAM | 2026-02-26 | `0001352010-26-000015` · `exhibit1017-epamnonxempl003.jpg` | — | refuses | OTHER | never read (an image, N3) | an image page of the filing (JPEG bytes, no text) |
| 24 | EPAM | 2026-02-26 | `0001352010-26-000015` · `exhibit1017-epamnonxempl004.jpg` | — | refuses | OTHER | never read (an image, N3) | an image page of the filing (JPEG bytes, no text) |
| 25 | EPAM | 2026-02-26 | `0001352010-26-000015` · `exhibit1017-epamnonxempl005.jpg` | — | refuses | OTHER | never read (an image, N3) | an image page of the filing (JPEG bytes, no text) |
| 26 | EPAM | 2026-02-26 | `0001352010-26-000015` · `exhibit1017-epamnonxempl006.jpg` | — | refuses | OTHER | never read (an image, N3) | an image page of the filing (JPEG bytes, no text) |
| 27 | FUBO | 2025-10-30 | `0001493152-25-020163` · `ex10-2.htm` | TAX RECEIVABLES AGREEMENT | refuses | OTHER | no outcome (read only) | not debt: “TAX RECEIVABLES AGREEMENT” |
| 28 | FUBO | 2025-10-30 | `0001493152-25-020163` · `ex10-3.htm` | AMENDED AND RESTATED LIMITED LIABILITY COMPANY AGREEMENT | refuses | OTHER | no outcome (read only) | not debt: “AMENDED AND RESTATED LIMITED LIABILITY COMPANY AGREEMENT” |
| 29 | FUBO | 2025-10-30 | `0001493152-25-020163` · `ex10-4.htm` | STOCKHOLDERS AGREEMENT | refuses | OTHER | no outcome (read only) | not debt: “STOCKHOLDERS AGREEMENT” |
| 30 | IT | 2020-09-28 | `0001193125-20-256749` · `d75343dex102.htm` | RESTATED GUARANTEE AND COLLATERAL AGREEMENT | passes | SUPPORT | no outcome (read only) | guarantee and collateral agreement |
| 31 | LLY | 2026-02-12 | `0000059478-26-000013` · `lly-12312025x10kexhibit104.htm` | AWARD UNDER THE 2002 LILLY STOCK PLAN ELI LILLY AND COMPANY RELATIVE VALUE AWARD AGREEMENT | refuses | OTHER | no outcome (read only) | not debt: “AWARD UNDER THE 2002 LILLY STOCK PLAN ELI LILLY AND COMPANY RELATIVE VALUE AWARD AGREEMENT” |
| 32 | LLY | 2026-02-12 | `0000059478-26-000013` · `lly-12312025x10kexhibit105.htm` | — | refuses | OTHER | no outcome (read only) | an RSU award form |
| 33 | MCK | 2021-04-02 | `0000927653-21-000019` · `ex102-creditagreementamend.htm` | — (cache miss) | — | UNREAD | fetch_failed | cache miss; by its name a credit agreement amendment; a target, read at the paid build |
| 34 | MCK | 2013-11-21 | `0001193125-13-450016` · `d629383dex102.htm` | — (cache miss) | — | UNREAD | fetch_failed | cache miss; a target, read at the paid build |
| 35 | MCK | 2013-11-21 | `0001193125-13-450016` · `d629383dex103.htm` | — (cache miss) | — | UNREAD | fetch_failed | cache miss; a target, read at the paid build |
| 36 | NCNO | 2026-03-31 | `0001902733-26-000022` · `exhibit1036fourthamendment.htm` | OFFICE LEASE | refuses | OTHER | no outcome (read only) | not debt: “OFFICE LEASE” |
| 37 | NFLX | 2026-01-23 | `0001065280-26-000034` · `ex103_q425.htm` | — | refuses | OTHER | no outcome (read only) | a stock plan |
| 38 | NFLX | 2025-12-22 | `0001193125-25-327462` · `d82688dex102.htm` | SENIOR UNSECURED DELAYED DRAW TERM LOAN CREDIT AGREEMENT | passes | GOVERNS | no_terms_returned | the December 2025 delayed-draw term loan agreement: LIVE (2Y/3Y DDTL on the panel) |
| 39 | NKE | 2025-03-10 | `0000320187-25-000008` · `nikefiveyearcreditagreemen.htm` | FIVE YEAR CREDIT AGREEMENT | passes | GOVERNS | no_terms_returned | the FIVE YEAR CREDIT AGREEMENT of 2025-03-07: LIVE (panel's facility to 2030-03-07) |
| 40 | PARR | 2026-02-25 | `0000821483-26-000005` · `a20251231ex1012-performanc.htm` | INC. PERFORMANCE RESTRICTED STOCK UNIT AWARD AGREEMENT | refuses | OTHER | no outcome (read only) | not debt: “INC. PERFORMANCE RESTRICTED STOCK UNIT AWARD AGREEMENT” |
| 41 | PARR | 2026-02-25 | `0000821483-26-000005` · `a20251231ex1013-formofrest.htm` | INC. RESTRICTED STOCK UNIT AWARD AGREEMENT | refuses | OTHER | no outcome (read only) | not debt: “INC. RESTRICTED STOCK UNIT AWARD AGREEMENT” |
| 42 | PARR | 2026-02-25 | `0000821483-26-000005` · `a20251231ex1015-nonxqualif.htm` | INC. NONSTATUTORY STOCK OPTION AGREEMENT | refuses | OTHER | no outcome (read only) | not debt: “INC. NONSTATUTORY STOCK OPTION AGREEMENT” |
| 43 | PARR | 2026-02-25 | `0000821483-26-000005` · `a20251231ex108-incentiveco.htm` | — | refuses | OTHER | no outcome (read only) | an incentive compensation plan |
| 44 | PARR | 2015-04-02 | `0001193125-15-116573` · `d902717dex102.htm` | PLEDGE AGREEMENT | passes | SUPPORT | no outcome (read only) | pledge agreement |
| 45 | PARR | 2015-04-02 | `0001193125-15-116573` · `d902717dex103.htm` | LIMITED RECOURSE GUARANTY | passes | SUPPORT | no outcome (read only) | limited recourse guaranty |
| 46 | PARR | 2015-04-02 | `0001193125-15-116573` · `d902717dex104.htm` | DELAYED DRAW TERM LOAN AND BRIDGE LOAN CREDIT AGREEMENT | passes | GOVERNS | no_terms_returned | fourth amendment to Par Petroleum's 2014 delayed-draw and bridge loan agreement; the panel carries no such loan; read |
| 47 | PARR | 2015-04-02 | `0001193125-15-116573` · `d902717dex105.htm` | SECOND AMENDMENT AND WAIVER TO ABL CREDIT AGREEMENT | passes | GOVERNS | no_terms_returned | second amendment and waiver to HIE's 2013 ABL credit agreement; the panel's ABL is the 2023 one; read |
| 48 | PARR | 2015-04-02 | `0001193125-15-116573` · `d902717dex106.htm` | CREDIT AGREEMENT | passes | GOVERNS | no_terms_returned | first amendment to HIE Retail's Bank of Hawaii credit agreement; read |
| 49 | PARR | 2017-07-05 | `0000821483-17-000034` · `ex103-2017x06x28amendmentn.htm` | CREDIT AGREEMENT | passes | GOVERNS | no_terms_returned | Amendment No. 2 to the KeyBank credit agreement of 2015-12-17 (the 8-K's Item 8.01), the same agreement its targeted ex102 amends; read |
| 50 | PARR | 2017-07-05 | `0000821483-17-000034` · `exhibit101-5thamendmenttow.htm` | — | refuses | GOVERNS* | no outcome (read only) | a letter-form Fifth Amendment to Par Wyoming's Third A&R Loan Agreement (2015-04-30): debt, but E5 reads no title from a letter head, so it is refused, as at main; a title-reader question, not this selector's |
| 51 | PARR | 2017-07-05 | `0000821483-17-000034` · `form8-kxtermloanrepaymenta.htm` | — | refuses | OTHER | no outcome (read only) | the 8-K's own cover document (Item 8.01) |
| 52 | SMPL | 2019-11-07 | `0001104659-19-060856` · `a19-22146_1ex10d2.htm` | EMPLOYMENT AGREEMENT | refuses | OTHER | no outcome (read only) | not debt: “EMPLOYMENT AGREEMENT” |
| 53 | TGT | 2026-03-11 | `0000027419-26-000016` · `tgt20260131-exhibit1019.htm` | RESTRICTED STOCK UNIT AGREEMENT | refuses | OTHER | no outcome (read only) | not debt: “RESTRICTED STOCK UNIT AGREEMENT” |
| 54 | TGT | 2026-03-11 | `0000027419-26-000016` · `tgt20260131-exhibit1022.htm` | TRANSITION AGREEMENT | refuses | OTHER | no outcome (read only) | not debt: “TRANSITION AGREEMENT” |
| 55 | TJX | 2020-05-21 | `0001157523-20-000793` · `a52222014ex10_2.htm` | 2024 REVOLVING CREDIT AGREEMENT | passes | GOVERNS | no_terms_returned | second amendment to the 2024 Revolving Credit Agreement of 2016-03-11; the panel carries only the 2029 and 2030 revolvers, so probably replaced, but no located exhibit says so; read |
| 56 | TJX | 2025-05-09 | `0000109198-25-000033` · `exhibit102-secondamendment.htm` | 2030 REVOLVING CREDIT AGREEMENT | passes | GOVERNS | no_terms_returned | the 2030 REVOLVING CREDIT AGREEMENT: amends and restates the 2021 agreement; LIVE (panel revolver to 2030-05-09) |
| 57 | VRRM | 2025-10-17 | `0001193125-25-242530` · `vrrm-ex10_2.htm` | CREDIT AGREEMENT | passes | GOVERNS | no_terms_returned | Amendment and Restatement Agreement No. 2 of the first-lien term loan, 2025-10-17: LIVE (2021 Term Loan on the panel, governed to 2032-10-15) |
| 58 | VRRM | 2018-06-21 | `0001104659-18-041476` · `a18-15692_1ex10d2.htm` | TAX RECEIVABLE AGREEMENT | refuses | OTHER | no outcome (read only) | not debt: “TAX RECEIVABLE AGREEMENT” |
| 59 | WERN | 2026-06-10 | `0000793074-26-000120` · `wern-20260605ex102.htm` | PERFORMANCE GUARANTY | passes | SUPPORT | no outcome (read only) | performance guaranty of the receivables facility |
| 60 | WLK | 2010-12-08 | `0001193125-10-276447` · `dex102.htm` | LOAN AGREEMENT | passes | GOVERNS | no_terms_returned | the IKE Zone bonds' loan agreement (Series 2010A-2, $65m), beside the GO Zone one (dex101); read |
