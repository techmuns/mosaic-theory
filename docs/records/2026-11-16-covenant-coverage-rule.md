---
id:
status: shipped
date: 2026-11-16
prs: [1090]
supersedes:
superseded-by:
---

# The covenant phase reads every located exhibit before it sends any, and sends every debt contract a later located exhibit's own words do not show displaced, and whose notes have not matured. The four-exhibit cap becomes a runaway guard of 10 that flags loudly. VRRM's Amendment No. 4 now reads superseded by its amended and restated revolver; over the 24 pages with pointer rows a full paid rebuild makes 48 covenant calls, not 51. No committed page moves until its next paid re-assembly (STATE row 63)

**WHAT.**
- *The ruling.* Operator, 2026-11-16: "Order now, coverage next (Recommended)". #1088 built the
  order (purchase agreements last). This builds the coverage rule, the ruling's second half.
- *The defect.* `extract_covenant_terms` sent at most `_MAX_EXHIBITS = 4` exhibits per page: the
  first four debt contracts its round-robin over pointer families reached. The cap chose, so a page
  spent calls on documents that govern nothing and dropped live ones behind them:
  - VRRM sent Amendment No. 4 (`0000950170-25-072679 · vrrm-ex10_1.htm`, filed 2025-05-15) to a
    revolving credit agreement its own amended and restated revolver (filed 2025-10-17) replaced.
    Any term it returned would have printed as a separate, stale "REVOLVING CREDIT AGREEMENT"
    group (`governing_terms` groups by title);
  - AMZN sent its 2022 364-day agreement, which its 2023 five-year agreement terminated, and left
    its June 2026 term loan agreement past the bound;
  - NKE sent four 364-day agreements, each terminated by the next year's.
- *The audit, first, at $0* (below; the table is at the end). The real loop ran over every
  committed page's pointer rows, each exhibit read from the EDGAR cache (cache only) and the model
  stubbed from the committed page (#1084's probe). Every located exhibit was then read: its title
  and amendment reads, the agreement it is or amends, what any later exhibit says of it, and the
  page's CIQ panel.
- *The rule* (`vinci/dossier/covenant_extract.py`).
  1. **Read every target first.** Each exhibit is fetched and identified before any is sent,
     because which documents govern is decided across all of them. Refusals (`not_debt_agreement`)
     and fetch failures are as before.
  2. **Identity, from the document's own words** (`exhibit_identity`): the agreement it is (the
     title E5 read and its own "dated as of" date) and, for an amendment, the agreement it amends.
     That is named in its heading ("to Revolving Credit Agreement, dated as of March 1, 2018") or,
     failing that, as the first agreement its recital names ("pursuant to the Credit Agreement (…)
     dated as of February 11, 2022"). A heading date equal to the exhibit's own date is the
     amendment's, not its base's (CNXC's "FIRST AMENDMENT TO CREDIT AGREEMENT AND JOINDER
     AGREEMENT dated as of December 27, 2021").
  3. **What a document displaces** (`displaced_agreements`). An agreement it binds to a defined
     term, by name and date, in a recital ("that certain Revolving Credit Agreement, dated as of the
     Original Closing Date (… the “Original ABL Credit Agreement”)") or a definition ("“2025 Credit
     Agreement” means that certain 364-Day Credit Agreement, dated as of March 7, 2025"). A defined
     date resolves by its own definition ("“Original Closing Date” shall mean March 1, 2018"); a
     paired definition binds both parts ("“Existing Credit Agreements” means the Existing 3-Year
     Credit Agreement and the Existing 364-Day Credit Agreement"). It must then DISPLACE that term
     whole, in one of nine verb forms, each read on a committed page's exhibit: amend and restate
     (VRRM, AMZN, EPAM, WLK, TJX), "an amendment and restatement of" (AMZN), "substituted for"
     (AMZN), "provisions of … shall be superseded" (CNXC), "has been, or … will be, terminated"
     (NKE), "shall be terminated" (V), "commitments thereunder shall have been terminated" (AMZN),
     "commitments under … terminated", and "evidence of termination of" (TJX). Two guards:
     - a PART of the agreement is not the agreement ("Section 2.5.12 of the 2025 Credit
       Agreement has been … terminated");
     - neither is a possessive ("the Original ABL Credit Agreement’s Schedule 1.1");
     - nor something under it (code-review round 0): "the Revolving Commitments under the
       Existing Credit Agreement shall have been terminated" ends a tranche's commitments, and
       its other loans may stay outstanding.
     A bare "termination of" is not admitted: "upon termination of the Credit Agreement" is a
     condition, not a statement that it ended.
  4. **SUPERSEDED** (`_coverage`). A target is superseded when a target filed STRICTLY LATER
     displaces the agreement it is or amends: the SAME NAME and the same date (independent review,
     round 2, F1; a name that is only the other's tail is a doubt, and the exhibit is read). What
     an exhibit "is": a base agreement, or an amendment AND RESTATEMENT, is the agreement dated as
     of its own date; a plain amendment is only what it amends. On any doubt about identity it is
     READ, never skipped:
     - a displaced agreement CONFUSABLE with two agreements on the page (the same date, and one name
       the other's tail) decides none of them. The page is every located exhibit AND every debt
       agreement in a located filing beside one, which the loop reads for who it is but never sends
       (F1: VRRM's term-loan restatement `vrrm-ex10_2.htm` sits beside its A&R revolver, both
       dated October 17, 2025). VRRM's revolver and its first-lien term loan are both dated March 1,
       2018, and their names are not confusable;
     - a tied or empty filing date cannot order two documents (`governing_terms`' (X-4) rule);
     - a page with a target or a same-filing exhibit that could not be fetched supersedes
       NOTHING, and a flag says so (code-review round 0): the unread exhibit may be another
       agreement the displaced name fits, so no name on the page can be shown unambiguous;
     - a displaced agreement dated as any date an UNTITLED refused exhibit's head states decides
       nothing (Codex, round 1).
     The earliest such later exhibit is cited, with its own words.
  5. **TERMINATED** (`_matured_notes`). Every maturity year the title states, from its first
     "NOTES DUE", is before the page's reference date (`maturity_check.bound`), and the CIQ panel
     carries no instrument maturing in any of them, by its own date or a governed one. A row of
     UNSTATED principal counts as carried, since unknown is not absent. A panel that still carries
     one disagrees, and the exhibit is read. (The years and the unstated principal are code-review
     round 0.)
  6. **Everything else is READ**, however old it looks. A purchase agreement is still sent after
     every other debt contract (#1088). `_MAX_EXHIBITS` becomes **10**, a runaway guard: a page
     with more live debt contracts sends the first 10 in that order. Each one past it reads
     `cost_bound` and gets a flag beginning "(E5) RUNAWAY GUARD" that names the count and the
     guard. **Why 10:** the busiest committed page sends 6 under the rule (BURL). The locator can
     return at most 13 targets: one 10-K row and two 8-Ks for each of the six families it
     searches. At the $0.69 mean list price of a covenant call, 10 calls are about $7.
- *The field.* `CovenantExhibitOutcome` gains two kinds, `superseded` and `terminated`, and two
  optional fields, dropped from the JSON when unset:
  - `superseded_by` and `superseded_by_filename`, the later exhibit's accession and file: two
    structured values, never one display string (code-review round 0);
  - `evidence`, its words in quotes and the agreement they name, or the maturity against the
    reference date. Display only: no parser reads it.

  A cost-bound exhibit now carries the heading E5 read, because every target is read first.
- *The render.* Both renderers print the new causes. The approved wording table gains two rows,
  **approved 2026-11-16** by the operator, relayed by the coordinator: "Approve as shown
  (Recommended)" (PREVIEW RULE):

  | outcome | printed |
  |---|---|
  | `superseded` | not sent: superseded by `<accession> · <file>` — “`<its words>`”, which names the `<AGREEMENT>` dated `<date>` that this exhibit is / amends |
  | `terminated` | not sent: terminated — its title states notes due `<year>`, before the page's reference date (`<date>`), and the CIQ panel carries no instrument maturing in `<year>` |

  `cost_bound` keeps its approved words ("not sent: past the cost bound on exhibits per page");
  under the rule it is reached only past the guard.
- *Vintage.* `2026-11-16.covenant-coverage-rule`.

**WHY.** A credit analyst reads every document that governs debt still outstanding: each live
instrument's governing agreement and its amendment chain. They skip a document a later one
displaced and one whose debt has ended. A count cap does neither. It reads the first four,
whatever they are.

*DOES THIS SELECT ON FORM?* No, with two form-shaped choices named and bounded.
- What decides is the documents' own statements of legal effect: this agreement amends and
  restates that one; that one's commitments are terminated; these notes were due in 2024.
  Each is SUBSTANCE: what the later document did to the earlier one, read from its words, and the
  maturity the instrument states. No magnitude, size, currency or disclosure form enters it.
- The choices that are form:
  - The reader knows nine verb forms and two binding forms. A document that displaces another in
    other words goes unrecognised, and both are READ. The rule's form-dependence can only cost
    calls, never skip a live document.
  - Name matching uses equality or a word tail, after removing "AMENDED AND RESTATED". Two names
    for one agreement that share no tail fail to match, and both are read. Two different
    agreements under tail-sharing names on the same date are refused as ambiguous.
- Set by face validity on real documents, never by outcome. The audit's hand verdicts were made
  before the rule was measured against them, and no forward return enters anything here.

**HOW VERIFIED.**
- *The audit* (main `51784e53`, 26 committed pages, 24 with pointer rows, 91 located exhibits).
  - 5 are unreadable cache misses (MCK 4, WERN 1).
  - At main the loop's outcomes are 48 extracted, 3 no terms returned (51 sent), 25 refused,
    10 cost bound and 5 fetch failed.
  - At head they are 41 extracted, 7 no terms returned (48 sent), 27 refused, 10 superseded,
    1 terminated and 5 fetch failed, with 0 cost bound. Two refusals are new, NFLX's
    January 2026 incremental-commitments letter and WLK's 2016 bridge commitment letter: both were
    cost bound and never read, and are now read and refused like the other bank commitment
    letters.
  - A stubbed model answers no rows for an exhibit no committed row cites, so "no terms returned"
    at head means "sent, with no committed answer to replay", not a model's answer.
- *Hand verdicts on all 91* (the table below).
  - **The 11 the rule skips: 11 agreed.** Each is superseded or matured by the later exhibit's
    words, read by hand in the cached text. **0 false skips.** (Before round 2 it skipped 12; EPAM's
    2017 agreement, which its 2021 restatement does restate, is now read on a doubt about identity:
    the restatement names a "Credit Agreement" and E5 titles the exhibit by its cover, "REVOLVING
    CREDIT FACILITY CREDIT AGREEMENT".)
  - **The 48 it sends:** 29 live by the hand read; 19 read though the hand read suspects some are
    dead, because nothing located shows it without doubt:
    - AMZN's 2014 and 2020 agreements;
    - EPAM's 2017 agreement (above);
    - BURL's 2020 security agreement;
    - NCNO's 2024 first amendment;
    - NFLX's 2009 agreement;
    - PARR's 2014, 2015 and 2017 Mid Pac / Texadian papers;
    - TJX's 2021 agreement, which a 2025 document in another of its located accessions restates,
      a document the loop does not target (see WHAT IT COSTS);
    - UBER's three term loan amendments (its panel carries no term loan);
    - V's 2013 364-day agreement;
    - WLK's four bond and credit agreements (an Item 1.02 after its panel may have ended its 2016
      revolver) and its 2009 amendment.
  - The 27 refusals are as #1088's audit read them, plus the 2 commitment letters above.
- *The reader over the whole cache.* 3,575 EDGAR archive documents were read through
  `html_to_text`, as `_fetch_exhibit` reads them; the gate passes 92.
  - 24 of those 92 displace an agreement, 29 displacements in all. Each is a whole-agreement
    restatement or termination by hand read.
  - Within a CIK, those displacements link 14 cached documents to an earlier one under the
    same-name rule (round 2, F1). Every link is a real supersession: 0 false links. A 15th,
    EPAM's, matches only by a name's tail and is read on that doubt.
  - On the final round-2 reader the scan reads the same 29 displacements in the same 24
    documents. F5's first draft, which stopped a recital's gap at any agreement noun, lost two of
    them (EPAM's and TJX's 2030 agreement's), whose recitals name the agreement's own amendment
    history before its term. The kept rule allows an AMENDMENT in the gap and stops only at
    another agreement.
  - The part and possessive guards refused nothing in the corpus. So each was pinned on a clause
    DERIVED from a real one. Writing the part pin found that the part guard read `[^.;]`, so a
    dotted section number defeated it. That was fixed, and the independent review (round 2, F6)
    then showed the part guard REDUNDANT: every part reaches the term through "of", "to", "in" or
    "under", which the round-0 subject guard (`_UNDER_THE`) already refuses, and turning the part
    guard off moved no pin. It is removed; the part pin now holds the subject guard.
- *Pins* (`tests/test_covenant_coverage_rule.py`, 44 nodes, on
  `tests/fixtures/covenant_coverage_rule/`).
  - The fixtures are real: seven committed pages' layers, unmodified, and 61 cuts of the cached
    exhibits: every target, and since round 2 every other exhibit of a located filing. Each cut
    reads exactly as its full exhibit reads (its README). `round2_heads.json` holds three more real
    heads (UBER, VRRM `vrrm-ex10_2.htm`, NKE's five-year agreement).
  - **The brief's five:**
    1. VRRM's Amendment No. 4 reads superseded, citing `0001193125-25-242530 · vrrm-ex10_1.htm`
       and its words.
    2. CNXC's receivables financing agreement's third and fourth amendments stay sent, while its
       2023 restatement and 2021 amendment read superseded.
    3. BURL sends all 6 live contracts, with no cost bound.
    4. A synthetic overflow, BURL's real exhibits twice over (12 live), sends 10 and flags 2 as
       RUNAWAY GUARD.
    5. AMZN's 2014 agreement, which nothing names, is read, and its June 2026 term loan is sent.
  - **Beyond the brief:**
    - NFLX's 2014 purchase agreement reads terminated, and its 2018 one goes last;
    - a panel still carrying the year disagrees, and the exhibit is read;
    - NKE's three successive 364-day agreements read superseded;
    - TJX's collective definition supersedes both of its agreements.
  - **Negatives, each derived from a real clause:** a conditional termination; a part of the
    agreement; a possessive; an agreement named two ways on the page; a tied or empty filing date
    (2 nodes). Code-review round 0 added five more:
    - a panel row of unstated principal in the year;
    - a title with a live tranche;
    - "the Revolving Commitments under the …" terminated;
    - a page with an unread exhibit (VRRM with its term-loan restatement unreadable);
    - a one-word name.
  - **End to end,** VRRM's and NFLX's committed pages with the real loop's outcomes, through
    `render_markdown` and the production `renderDossier` in node: each line names its cause, and
    the web line equals the Markdown.
  - Seven preconditions hold each fixture to its committed page.
- *Fail first.* With base's `covenant_extract.py` (main `51784e53`) and head's schema and
  renderers (so the file imports), 11 of the first 24 new nodes fail: every positive and both renders.
  The 13 that pass at base are the 7 preconditions and the 6 negatives, which hold trivially when
  nothing is ever superseded. So each negative was also shown live by a mutation of head's code,
  each removing one piece and each reddening at least one pin:
  - no part guard (since removed as redundant, round 2 F6: with the subject guard in place this
    mutation reds nothing);
  - no possessive guard;
  - no ambiguity check;
  - any other exhibit counted as later;
  - a bare "termination of" admitted;
  - no panel check;
  - names ignored, so dates alone match. That last one reds VRRM's own pin, because the term
    loan's restatement would also be skipped.
- *Code-review round 0* (`/code-review high --fix`) found ten things; six are fixed.
  - Fixed, each behind a pin that fails on the pre-review code (5 of 5 red there):
    1. the matured-notes test read only the first year;
    2. it read an unstated principal as absent;
    3. a clause about something "under the" agreement read as ending it;
    4. `superseded_by` was a display string;
    5. a page with an unread exhibit could pass the ambiguity check on a guess;
    6. a one-word name matched any name ending in it.
  - Not fixed (one DEFER, three DISMISS), each with its reason in the PR's dispositions:
    - a conditional "shall be terminated if …", unobserved in the 29 corpus displacements;
    - an exhibit skipped as superseded when its superseder is itself not sent (too large, an LLM
      error, past the guard). Its terms are still not in force, and the superseder's line says
      why it was not read;
    - case-blind "DATED AS OF" in an all-caps heading, which fails closed (the exhibit is read);
    - repeated whole-text scans, a cost of seconds.
  - The audit at the post-review code: 0 of 91 outcomes move, and 51 → 47 held then (48 since
    round 2).
- *Codex, round 1* (two P1 findings, both fixed behind pins that fail on the PR head):
  - an UNKNOWN CIQ panel was read as an empty one, so notes could read terminated on a missing
    panel. With no panel, no notes read terminated (`test_an_unknown_instrument_panel_is_not_an_empty_one`);
  - a refused exhibit whose title was NOT read did not count in the ambiguity check. It may be the
    displaced agreement under an unread name. Codex asked to count every such refusal as unread,
    which would switch the rule off on CNXC, NKE, TJX and EPAM (each has an untitled offer letter
    or plan). So the fix is narrower: a displaced agreement dated as any date an untitled
    refusal's head states decides nothing (`test_an_untitled_exhibit_dated_as_the_displaced_agreement_blocks_the_supersession`,
    derived from VRRM's term-loan restatement with its heading removed).
  - The audit after the round: 0 of 91 outcomes move.
- *Independent review, round 2* (the coordinator's, at head `e532bb0c`; "on any doubt about
  identity, READ, never skip"), and *Codex, round 2*, in one commit. Each fix is behind a pin that
  fails on the pushed head (`ea9c5c46`): 13 new nodes, 13 red there.
  - **F1** (medium) same-date sibling agreements read as one. A name now matches only the same
    name; the tail only makes two namings confusable, and two confusable agreements on a page make
    the displaced name ambiguous. The page includes every debt agreement in a located filing that
    the selector does not target, read for who it is. A plain amendment's own date is no identity.
    Pins: VRRM's real `vrrm-ex10_2.htm` targeted and untargeted beside its A&R revolver against a
    derived later restatement (both read); the NKE shape, derived from NKE's real heads (a 364-day
    and a five-year agreement both of March 11, 2022, neither superseded; a five-year First
    Amendment of March 8, 2024 never superseded, while the 2024 364-day agreement still is); the
    name rule itself. EPAM's 2017 agreement moves from superseded to read.
  - **F2** (low) UBER's three term loan amendments read their base as dated 2018-06-13, Amendment
    No. 1's date in the recital. The heading read now stays in the heading (it ends at the parties
    or the recitals), and they read 2016-07-13. The table below is corrected.
  - **F3** (low) a "(y) that certain …" now binds only inside a definition with its "(x)", and
    before the next definition begins. One derived pin per half.
  - Found writing F3's pin: a recital's gap could reach across a sentence end to a definition's
    own term ("… that certain Five Year Credit Agreement, dated as of March 11, 2022. “2025 Credit
    Agreement” means …"). A recital never binds a term that heads a definition; pinned.
  - **F4** (low) "… outstanding under the … shall have been paid in full" must say all of it, in
    lower-case words, and "commitments under the … terminated" must say all or the commitments,
    never a tranche's. Pinned on AMZN's real condition edited to each tranche form.
  - **F5** (low) a recital's gap stops at a second agreement that is not an amendment of the first,
    so the term binds to the agreement beside it; an amendment named there is the agreement's own
    history (EPAM's "as amended by the First Amendment to Credit Agreement …", TJX's "(as amended by
    that certain First Amendment to 2026 Revolving Credit Agreement …"). The recital search
    overlaps, so the second agreement's own recital is still read. Derived pin on VRRM's real
    recital.
  - **F6** (test quality) the part guard was redundant (above); removed.
  - **Codex round 2** (P1) an undated row of the panel could hide the notes. A notes-kind row
    (its type or description names notes, bonds or debentures) with principal and no maturity
    date now blocks `terminated`; NFLX's own undated rows (commercial paper, a lease, a term loan)
    do not. Derived pin on NFLX's real panel.
  - Each new guard, removed in turn, reds at least one pin; F3's two halves each red their own.
  - After the round: the stubbed loop over all 26 pages moves EPAM's 2017 agreement only (to
    read), so 11 skips remain; 51 → 48 calls; the corpus scan's numbers are under *The reader
    over the whole cache*.
- *Three existing pins move with the premise.*
  - The plan pin's kinds exclude the two new ones, which this file drives.
  - A cost-bound exhibit now carries its heading.
  - NFLX's purchase agreements are now sent after its four credit agreements, rather than past a
    cap of four.
- *Committed pages do not move.* All 26 went through `refresh.refresh_fleet`: 26 unchanged,
  0 moved, 0 refused, 0 skipped, and `git status` showed nothing. Each committed `dossier.json`
  rendered through base and head `dossier.js` in node gave byte-identical HTML on 26 of 26.
- *Preview (PREVIEW rule).* Nine pages, BEFORE (main's loop) and AFTER (this PR's), each
  committed `dossier.json` with that loop's outcomes, in three forms:
  - through `render_markdown`;
  - through the production `renderDossier`, collapsed and force-open;
  - VRRM and NFLX printed in the "Full dossier" scope.

  The images are in the coordinator's notes folder, not in the repo. **Approved 2026-11-16** by
  the operator, relayed by the coordinator: "Approve as shown (Recommended)", covering the
  `superseded` and `terminated` rows as `coverage-rule-preview/README.md` shows them.

**BOUNDARY.**
- Every page count is at main `51784e53` (2026-11-16), over the 26 committed
  `data/dossiers/*/dossier.json`; 24 have pointer rows, with 91 located exhibits, one per pointer
  accession.
- The cache is the operator's EDGAR cache, `data/cache/sec` in the primary checkout, read
  2026-11-16, cache only: a miss raised, and nothing was fetched.
- The corpus is every cached `/Archives/edgar/data/` document ending .htm, .html or .txt whose name
  does not contain "index": 3,575, of which the gate passes 92.
- Costs use the 55 committed run lines in `data/snapshots/assembly_runs/` (main `51784e53`):
  - 107 successful `covenant_terms` calls on 21 names, all claude-opus-4-8, at the list price in
    `vinci.config.LLM_PRICE_PER_MTOK` ($5 input, $25 output per million tokens). Median $0.67,
    mean $0.69 per call.
  - Chars per token: 2.87, the median over the 47 calls that match one to one, by order, the
    exhibits their page's committed term rows cite.
  - An added or dropped exhibit is priced at its chars / 2.87 input tokens plus 1,926 output
    tokens (the mean).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- *At each page's next paid build* (est., method above; main → head):

  | page | calls | est. $ | why |
  |---|---|---|---|
  | AMZN | 4 → 4 | +0.00 | sends its June 2026 term loan agreement; skips its 2022 364-day agreement (terminated by the 2023 five-year) and its 2018 restatement (restated in 2020) |
  | BURL | 4 → 6 | +2.08 | sends its ABL agreement's fourth amendment (661,985 chars) and its term loan's 2014 Amendment No. 4 (478,924), live chains |
  | CNXC | 4 → 3 | −1.19 | skips its 2023 restatement (superseded by the 2025 one) and its 2021 amendment (of the agreement 2023 restated) |
  | NFLX | 4 → 5 | +0.22 | sends its 2018 notes purchase agreement, last; its 2014 one reads terminated |
  | NKE | 4 → 1 | −1.58 | skips its 2023, 2024 and 2025 agreements, each terminated by the next |
  | TJX | 4 → 2 | −0.72 | skips its 2020 amendment and its 2020 364-day agreement (the 2021 agreement requires their termination) |
  | VRRM | 3 → 2 | −1.30 | skips Amendment No. 4 (superseded by its A&R revolver) |
  | WLK | 4 → 5 | +0.12 | sends its 2009 amendment (38,623 chars), unclassifiable |
  | 16 others | unchanged | 0 | |
  | **all 24** | **51 → 48** | **−2.37** (about $33.14 → $30.77) | |

  The coordinator's estimate of about $0.33 per exhibit was re-derived as above: a call is
  $0.67 at the median, and its price follows its exhibit's size.
- *A dead document the words cannot show dead is READ.* That is 19 of the 48 sends, est. $9.12 a
  fleet rebuild at the per-exhibit prices. The alternative, skipping on dates or tenor ("a
  364-day agreement from 2013 is dead"), would skip a live document wherever an extension was
  never filed. Precision first is the operator's rule ("an unclassifiable one is READ").
- *Item 1.02 is not read.* The page carries an Item 1.02 only inside prose (`panel_vintage`,
  `maturity_filings`), which no parser may read. Where its 8-K is itself located, the replacing
  agreement's own words are what the rule reads. WERN's 1.02 8-K (`0000793074-26-000159`) is a
  cache miss at $0, and the agreement it terminated, its 22 Unsecured Credit Agreement, is not a
  located exhibit, so WERN skips nothing.
- *An instrument the panel no longer carries* is used only beside a title's stated maturity. A
  pointer's family cannot match a document to an instrument: BURL's ABL amendments sit under a
  matured convertible's family. UBER's term loan amendments, whose panel carries no term loan,
  are therefore read.
- **Found, not fixed: the loop targets ONE exhibit per located accession.**
  `_core_agreement_exhibits` takes the first core exhibit of each pointer (`[:1]`). Over the 24
  pages, 60 other exhibits sit on located pointers; 3 are cache misses, and the gate passes 20 of
  the rest. Among them are live governing documents:
  - **VRRM's `vrrm-ex10_2.htm`** in `0001193125-25-242530`: its "AMENDMENT AND RESTATEMENT
    AGREEMENT NO. 2" of October 17, 2025, which restates the first-lien term loan agreement whose
    2021 restatement (`0001564590-21-015880`) the page sends. So VRRM's next paid build still
    extracts the 2021 term loan terms (LIBO Rate + 3.25%), not the ones in force;
  - NKE's five-year agreement (the panel's facility to 2030-03-07);
  - NFLX's December 2025 delayed-draw term loan agreement;
  - TJX's "2030" revolving credit agreement;
  - CNXC's restated receivables financing agreement.

  The rest include guaranties, pledges and security agreements, which the selector's design
  deliberately leaves to the core agreement. Widening the targets is a selector change with its
  own cost and its own audit, and is not built here. It matters before VRRM's next paid build
  (re-rehearsal around 2026-12-07).
- *Falsifier.* A re-assembled page on which:
  - an exhibit reads superseded while the agreement it is or amends is still in force (its later
    exhibit's words named another agreement); or
  - an exhibit reads terminated while its notes are outstanding; or
  - the RUNAWAY GUARD fires on a page whose live contracts a hand read finds fewer than 10.

**THE AUDIT TABLE** (main `51784e53` pointer rows, head code). "Identity" is the agreement the
exhibit is / the one it amends, as the reader read it (name · date as of).

| # | page | filed | exhibit | family | title read | amend | identity (is / amends) | outcome at head | hand verdict |
|---|---|---|---|---|---|---|---|---|---|
| 1 | AMZN | 2023-11-01 | `0001104659-23-113444` · `tm2329405d1_ex10-1.htm` | Revolving Credit Facility | FIVE-YEAR REVOLVING CREDIT AGREEMENT | no | FIVE-YEAR REVOLVING CREDIT AGREEMENT · 2023-11-01 / — | extracted | LIVE: AMZN's five-year revolver; the panel carries a revolver |
| 2 | AMZN | 2022-11-18 | `0001193125-22-289041` · `d413765dex101.htm` | Short-Term Credit Facilities | 364-DAY REVOLVING CREDIT AGREEMENT | no | 364-DAY REVOLVING CREDIT AGREEMENT · 2022-11-18 / — | superseded by `0001104659-23-113444` | SUPERSEDED, agreed: the 2023 five-year agreement terminates its commitments |
| 3 | AMZN | 2020-06-23 | `0001193125-20-176528` · `d948849dex101.htm` | Unsecured 364-Day Revolving Credit Facil | AMENDED AND RESTATED CREDIT AGREEMENT | no | CREDIT AGREEMENT · 2020-06-23 / — | extracted | READ, unclassified: JPM 364-day A&R; probably restated by a March 2022 A&R no pointer locates |
| 4 | AMZN | 2014-09-05 | `0001018724-14-000042` · `amzn2014september5-ex101.htm` | Revolving Credit Facility | CREDIT AGREEMENT | no | CREDIT AGREEMENT · 2014-09-05 / — | extracted | READ, unclassified: probably replaced by the May 2016 agreement the 2018 A&R restates, which no pointer locates |
| 5 | AMZN | 2018-04-27 | `0001193125-18-139368` · `d574720dex101.htm` | Short-Term Credit Facilities | AMENDED AND RESTATED CREDIT AGREEMENT | no | CREDIT AGREEMENT · 2018-04-27 / — | superseded by `0001193125-20-176528` | SUPERSEDED, agreed: the 2020 A&R is "an amendment and restatement of" it |
| 6 | AMZN | 2026-06-10 | `0001104659-26-072140` · `tm2613616d4_ex10-1.htm` | Unsecured 364-Day Revolving Credit Facil | TERM LOAN AGREEMENT | no | TERM LOAN AGREEMENT · 2026-06-08 / — | no_terms_returned | LIVE: a new term loan filed after the panel |
| 7 | BRBR | 2021-02-26 | `0001772016-21-000029` · `ex10-1_amend2creditagmt.htm` | Revolving Credit Facility | CREDIT AGREEMENT | yes | — / CREDIT AGREEMENT · 2019-10-21 | extracted | LIVE chain: amends the 2019 agreement no later exhibit names |
| 8 | BRBR | 2019-10-21 | `0001193125-19-270862` · `d812149dex101.htm` | Revolving Credit Facility | AMENDED AND RESTATED LIMITED LIABILITY COMPANY AGREEMENT | no | — | not_debt_agreement | REFUSED as before (not debt, or no title read) |
| 9 | BURL | 2020-04-16 | `0001193125-20-109457` · `d883886dex101.htm` | Convertible Senior Notes 1.25% Mature on | SECURITY AGREEMENT | no | SECURITY AGREEMENT · 2020-04-16 / — | extracted | READ, unclassified: secures 2020 secured notes; whether they remain is not in any located exhibit |
| 10 | BURL | 2025-07-29 | `0001193125-25-168007` · `d946952dex101.htm` | Convertible Senior Notes 2.25% Mature on | SECOND AMENDED AND RESTATED CREDIT AGREEMENT | yes | — | extracted | LIVE chain: ABL second A&R, sixth amendment |
| 11 | BURL | 2018-07-02 | `0001564590-18-016500` · `burl-ex101_6.htm` | Senior Secured Term Loan Facility Term B | SECOND AMENDED AND RESTATED CREDIT AGREEMENT | yes | — | extracted | LIVE chain: ABL second A&R, second amendment |
| 12 | BURL | 2026-03-19 | `0001193125-26-116001` · `burl-ex10_39.htm` | material contracts (10-K exhibit index) | — | no | — | not_debt_agreement | REFUSED as before (not debt, or no title read) |
| 13 | BURL | 2021-12-22 | `0001193125-21-364998` · `d275638dex101.htm` | Convertible Senior Notes 1.25% Mature on | SECOND AMENDED AND RESTATED CREDIT AGREEMENT | yes | — | extracted | LIVE chain: ABL second A&R, third amendment |
| 14 | BURL | 2022-07-22 | `0001193125-22-200058` · `d393601dex101.htm` | Convertible Senior Notes 2.25% Mature on | SECOND AMENDED AND RESTATED CREDIT AGREEMENT | yes | — | no_terms_returned | LIVE chain: ABL second A&R, fourth amendment |
| 15 | BURL | 2014-08-18 | `0001193125-14-313404` · `d772516dex101.htm` | Senior Secured Term Loan Facility Term B | CREDIT AGREEMENT | yes | — / CREDIT AGREEMENT · 2011-02-24 | no_terms_returned | LIVE chain: term loan agreement of 2011-02-24 (Term B-7 on the panel) |
| 16 | CNXC | 2025-04-11 | `0001803599-25-000111` · `exhibit101041125.htm` | Credit Facility | AMENDED AND RESTATED CREDIT AGREEMENT | yes | CREDIT AGREEMENT · 2025-04-11 / CREDIT AGREEMENT · 2023-04-21 | extracted | LIVE: the 2025 amendment and restatement |
| 17 | CNXC | 2024-04-26 | `0001803599-24-000117` · `exhibit101-thirdamendmentt.htm` | Other Loans | RECEIVABLES FINANCING AGREEMENT | yes | — / RECEIVABLES FINANCING AGREEMENT · 2020-10-30 | no_terms_returned | LIVE chain: receivables financing agreement, third amendment |
| 18 | CNXC | 2023-04-26 | `0001803599-23-000107` · `form8-k04x26x23exhibit101.htm` | Senior Unsecured Revolving Credit Facili | CREDIT AGREEMENT | yes | CREDIT AGREEMENT · 2023-04-21 / CREDIT AGREEMENT · 2020-10-16 | superseded by `0001803599-25-000111` | SUPERSEDED, agreed: the 2025 restatement supersedes it |
| 19 | CNXC | 2026-01-28 | `0001803599-26-000027` · `exhibit1022-2025form10k.htm` | material contracts (10-K exhibit index) | — | no | — | not_debt_agreement | REFUSED as before (not debt, or no title read) |
| 20 | CNXC | 2023-03-31 | `0001803599-23-000091` · `a033123exhibit101.htm` | Credit Facility | — | no | — | not_debt_agreement | REFUSED as before (not debt, or no title read) |
| 21 | CNXC | 2025-01-21 | `0001803599-25-000014` · `exhibit101-fourthamendment.htm` | Other Loans | RECEIVABLES FINANCING AGREEMENT | yes | — / RECEIVABLES FINANCING AGREEMENT · 2020-10-30 | no_terms_returned | LIVE chain: receivables financing agreement, fourth amendment |
| 22 | CNXC | 2021-12-30 | `0001803599-21-000215` · `exhibit101122721.htm` | Senior Unsecured Revolving Credit Facili | CREDIT AGREEMENT AND JOINDER AGREEMENT | yes | — / CREDIT AGREEMENT · 2020-10-16 | superseded by `0001803599-23-000107` | SUPERSEDED, agreed: amends the 2020 agreement the 2023 restatement supersedes |
| 23 | EPAM | 2017-05-26 | `0001352010-17-000022` · `exhibit10-1epamcreditagree.htm` | Revolving Credit Facility | REVOLVING CREDIT FACILITY CREDIT AGREEMENT | no | REVOLVING CREDIT FACILITY CREDIT AGREEMENT · 2017-05-24 / — | extracted | READ, on a doubt about identity (review round 2, F1): its 2021 A&R restates a "Credit Agreement" of the same date, and E5 titles this exhibit by its cover, "REVOLVING CREDIT FACILITY CREDIT AGREEMENT"; the names differ |
| 24 | EPAM | 2026-02-26 | `0001352010-26-000015` · `exhibit1017-epamnonxempl.htm` | material contracts (10-K exhibit index) | — | no | — | not_debt_agreement | REFUSED as before (not debt, or no title read) |
| 25 | EPAM | 2021-10-25 | `0001352010-21-000039` · `exhibit101-arcreditagreeme.htm` | Revolving Credit Facility | REVOLVING CREDIT FACILITY AMENDED AND RESTATED CREDIT AGREEMENT | no | REVOLVING CREDIT FACILITY CREDIT AGREEMENT · 2021-10-21 / — | extracted | LIVE (or later restated by a document no pointer locates) |
| 26 | FUBO | 2025-10-30 | `0001493152-25-020163` · `ex10-1.htm` | 2029 Convertible Notes | REGISTRATION RIGHTS AGREEMENT | no | — | not_debt_agreement | REFUSED as before (not debt, or no title read) |
| 27 | FUBO | 2025-03-03 | `0001628280-25-009420` · `fubo-20241231exx1026.htm` | material contracts (10-K exhibit index) | — | no | — | not_debt_agreement | REFUSED as before (not debt, or no title read) |
| 28 | FUBO | 2024-01-02 | `0001493152-24-000126` · `ex10-1.htm` | 2029 Convertible Notes | — | no | — | not_debt_agreement | REFUSED as before (not debt, or no title read) |
| 29 | IT | 2017-01-05 | `0000930413-17-000070` · `c86994_ex10-1.htm` | State of Connecticut Economic Developmen | — | no | — | not_debt_agreement | REFUSED as before (not debt, or no title read); a bank commitment letter |
| 30 | IT | 2020-09-28 | `0001193125-20-256749` · `d75343dex101.htm` | State of Connecticut Economic Developmen | AMENDED AND RESTATED CREDIT AGREEMENT | no | CREDIT AGREEMENT · 2020-09-28 / — | extracted | LIVE (or later restated by a document no pointer locates) |
| 31 | LLY | 2026-02-12 | `0000059478-26-000013` · `lly-12312025x10kexhibit103.htm` | material contracts (10-K exhibit index) | — | no | — | not_debt_agreement | REFUSED as before (not debt, or no title read) |
| 32 | MCK | 2021-04-02 | `0000927653-21-000019` · `ex101-creditagreementamend.htm` | Senior Unsecured 364-Day Revolving Credi | — | — | — | fetch_failed | UNREADABLE at $0 (cache miss): read and classified at the paid build |
| 33 | MCK | 2026-06-12 | `0000927653-26-000167` · `mck_ex101termloanagreement.htm` | Syndicated Senior Unsecured Revolving Cr | — | — | — | fetch_failed | UNREADABLE at $0 (cache miss): read and classified at the paid build |
| 34 | MCK | 2026-04-06 | `0000927653-26-000045` · `mck_ex101executedcreditagr.htm` | Senior Unsecured 364-Day Revolving Credi | — | — | — | fetch_failed | UNREADABLE at $0 (cache miss): read and classified at the paid build |
| 35 | MCK | 2013-11-21 | `0001193125-13-450016` · `d629383dex101.htm` | Syndicated Senior Unsecured Revolving Cr | — | — | — | fetch_failed | UNREADABLE at $0 (cache miss): read and classified at the paid build |
| 36 | NCNO | 2024-02-13 | `0001902733-24-000041` · `firstamendmenttocreditagre.htm` | Senior Secured Revolving Credit Facility | CREDIT AGREEMENT | yes | — / CREDIT AGREEMENT · 2022-02-11 | extracted | READ, unclassified: amends a 2022 agreement the 2024 agreement probably replaced; the 2024 one does not say so |
| 37 | NCNO | 2026-03-31 | `0001902733-26-000022` · `exhibit1035secondamendment.htm` | material contracts (10-K exhibit index) | OFFICE LEASE | yes | — | not_debt_agreement | REFUSED as before (not debt, or no title read) |
| 38 | NCNO | 2024-10-30 | `0001902733-24-000171` · `exhibit101creditagreementb.htm` | Senior Secured Revolving Credit Facility | CREDIT AGREEMENT | no | CREDIT AGREEMENT · 2024-10-28 / — | extracted | LIVE: the panel's revolver maturity (2029-10-28) is this agreement's |
| 39 | NFLX | 2018-04-26 | `0001193125-18-134734` · `d567970dex101.htm` | Senior Unsecured Bridge Term Loan Facili | SENIOR NOTES DUE 2028 PURCHASE AGREEMENT | no | SENIOR NOTES DUE 2028 PURCHASE AGREEMENT · 2018-04-26 / — | no_terms_returned | LIVE notes (5.875% due 2028 on the panel); a purchase agreement, sent last |
| 40 | NFLX | 2009-09-21 | `0001193125-09-194962` · `dex101.htm` | Senior Unsecured Revolving Credit Facili | CREDIT AGREEMENT | no | CREDIT AGREEMENT · 2009-09-16 / — | extracted | READ, unclassified: a 2009 agreement; nothing located names it |
| 41 | NFLX | 2025-12-05 | `0001193125-25-308651` · `d65144dex101.htm` | Unsecured Delayed Draw Term Loan Credit  | — | no | — | not_debt_agreement | REFUSED as before (not debt, or no title read); a bank commitment letter |
| 42 | NFLX | 2021-06-17 | `0001193125-21-193187` · `d552068dex101.htm` | Unsecured Revolving Credit Facility | REVOLVING CREDIT AGREEMENT | yes | — / REVOLVING CREDIT AGREEMENT · 2017-07-27 | extracted | LIVE chain: amends the 2017 revolving credit agreement |
| 43 | NFLX | 2026-01-23 | `0001065280-26-000034` · `ex102_q425.htm` | material contracts (10-K exhibit index) | — | no | — | not_debt_agreement | REFUSED as before (not debt, or no title read) |
| 44 | NFLX | 2014-02-05 | `0001193125-14-037000` · `d671121dex101.htm` | Senior Unsecured Bridge Term Loan Facili | SENIOR NOTES DUE 2024 PURCHASE AGREEMENT | no | SENIOR NOTES DUE 2024 PURCHASE AGREEMENT · 2014-02-19 / — | terminated | TERMINATED, agreed: notes due 2024; the panel carries none |
| 45 | NFLX | 2025-12-22 | `0001193125-25-327462` · `d82688dex101.htm` | Senior Unsecured Revolving Credit Facili | SENIOR UNSECURED REVOLVING CREDIT AGREEMENT | no | SENIOR UNSECURED REVOLVING CREDIT AGREEMENT · 2025-12-19 / — | extracted | LIVE: the December 2025 revolver |
| 46 | NFLX | 2019-04-01 | `0001193125-19-094705` · `d721020dex101.htm` | Unsecured Delayed Draw Term Loan Credit  | REVOLVING CREDIT AGREEMENT | yes | — / REVOLVING CREDIT AGREEMENT · 2017-07-27 | extracted | LIVE chain: amends the 2017 revolving credit agreement |
| 47 | NFLX | 2026-01-20 | `0001193125-26-015951` · `d37713dex101.htm` | Unsecured Revolving Credit Facility | — | no | — | not_debt_agreement | REFUSED as before (not debt, or no title read); a bank commitment letter |
| 48 | NKE | 2025-03-10 | `0000320187-25-000008` · `nike-364xdaycreditagreemen.htm` | 364-day Committed Credit Facility | 364-DAY CREDIT AGREEMENT | no | 364-DAY CREDIT AGREEMENT · 2025-03-07 / — | superseded by `0000320187-26-000020` | SUPERSEDED, agreed: the 2026 364-day agreement terminates it |
| 49 | NKE | 2024-03-11 | `0000320187-24-000009` · `nike-364xdaycreditagreemen.htm` | Committed Credit Facilities | CREDIT AGREEMENT | no | CREDIT AGREEMENT · 2024-03-08 / — | superseded by `0000320187-25-000008` | SUPERSEDED, agreed: the 2025 364-day agreement terminates it |
| 50 | NKE | 2026-07-15 | `0000320187-26-000088` · `nke-5312026exhibit1029.htm` | material contracts (10-K exhibit index) | — | no | — | not_debt_agreement | REFUSED as before (not debt, or no title read) |
| 51 | NKE | 2026-03-09 | `0000320187-26-000020` · `a364-daycreditagreementxni.htm` | 364-day Committed Credit Facility | 364-DAY CREDIT AGREEMENT | no | 364-DAY CREDIT AGREEMENT · 2026-03-06 / — | extracted | LIVE: the panel's 364-day facility (2027-03-05) |
| 52 | NKE | 2023-03-13 | `0000320187-23-000006` · `nike-364xdaycreditagreemen.htm` | Committed Credit Facilities | CREDIT AGREEMENT | no | CREDIT AGREEMENT · 2023-03-10 / — | superseded by `0000320187-24-000009` | SUPERSEDED, agreed: the 2024 agreement terminates it |
| 53 | ORKA | 2026-03-12 | `0001213900-26-026929` · `ea027330001ex10-9_oruka.htm` | material contracts (10-K exhibit index) | — | no | — | not_debt_agreement | REFUSED as before (not debt, or no title read) |
| 54 | PARR | 2015-04-02 | `0001193125-15-116573` · `d902717dex101.htm` | ABL Credit Facility Due 2028 | CREDIT AGREEMENT | no | CREDIT AGREEMENT · 2015-04-01 / — | extracted | READ, unclassified: a 2015 Mid Pac agreement; nothing located names it |
| 55 | PARR | 2017-07-05 | `0000821483-17-000034` · `ex102-midpacxhiekeybankxam.htm` | Term Loan Credit Agreement | CREDIT AGREEMENT | yes | — / CREDIT AGREEMENT · 2015-12-17 | extracted | READ, unclassified: amends a 2015 agreement nothing located names |
| 56 | PARR | 2026-02-25 | `0000821483-26-000005` · `a20251231ex1010-formofawar.htm` | material contracts (10-K exhibit index) | INC. RESTRICTED STOCK AWARD AGREEMENT | no | — | not_debt_agreement | REFUSED as before (not debt, or no title read) |
| 57 | PARR | 2014-10-31 | `0001193125-14-392228` · `d814202dex101.htm` | ABL Credit Facility Due 2028 | UNCOMMITTED CREDIT AGREEMENT | yes | — / UNCOMMITTED CREDIT AGREEMENT · 2013-06-12 | extracted | READ, unclassified: amends a 2013 uncommitted agreement nothing located names |
| 58 | PARR | 2023-06-01 | `0001193125-23-158690` · `d292719dex102.htm` | Term Loan Credit Agreement | ASSET-BASED REVOLVING CREDIT AGREEMENT | yes | — / ASSET-BASED REVOLVING CREDIT AGREEMENT · 2023-04-26 | extracted | LIVE chain: amends the 2023 ABL agreement |
| 59 | SMPL | 2018-03-20 | `0001213900-18-003172` · `f8k032018ex10-1_simplygood.htm` | Credit Agreement | CREDIT AGREEMENT | yes | — / CREDIT AGREEMENT · 2017-07-07 | extracted | LIVE chain: amends the 2017 credit agreement (the panel's Barclays facility) |
| 60 | SMPL | 2019-11-07 | `0001104659-19-060856` · `a19-22146_1ex10d1.htm` | Credit Agreement | CREDIT AGREEMENT | yes | — / CREDIT AGREEMENT · 2017-07-07 | extracted | LIVE chain: amends the 2017 credit agreement |
| 61 | TECX | 2026-02-26 | `0001193125-26-076793` · `tecx-ex10_4.htm` | material contracts (10-K exhibit index) | — | no | — | not_debt_agreement | REFUSED as before (not debt, or no title read) |
| 62 | TGT | 2026-08-14 | `0000027419-26-000032` · `five-yearcreditagreementex.htm` | 364-Day Unsecured Revolving Credit Facil | FIVE-YEAR CREDIT AGREEMENT | no | FIVE-YEAR CREDIT AGREEMENT · 2026-08-14 / — | extracted | LIVE: the 2026 five-year agreement |
| 63 | TGT | 2026-03-11 | `0000027419-26-000016` · `tgt20260131-exhibit1018.htm` | material contracts (10-K exhibit index) | — | no | — | not_debt_agreement | REFUSED as before (not debt, or no title read) |
| 64 | TGT | 2016-10-05 | `0000027419-16-000060` · `form8-k_creditagreement105.htm` | 364-Day Unsecured Revolving Credit Facil | — | no | — | not_debt_agreement | REFUSED as before (not debt, or no title read) |
| 65 | TJX | 2020-05-21 | `0001157523-20-000793` · `a52222014ex10_1.htm` | Senior Unsecured Revolving Credit Facili | 2022 REVOLVING CREDIT AGREEMENT | yes | — / 2022 REVOLVING CREDIT AGREEMENT · 2016-03-11 | superseded by `0001193125-21-202939` | SUPERSEDED, agreed: the 2021 agreement requires evidence of termination of its base |
| 66 | TJX | 2020-08-11 | `0000109198-20-000015` · `exhibit101364dayrevolv.htm` | Senior Unsecured Revolving Credit Facili | 364 DAY REVOLVING CREDIT AGREEMENT | no | 364 DAY REVOLVING CREDIT AGREEMENT · 2020-08-10 / — | superseded by `0001193125-21-202939` | SUPERSEDED, agreed: the same condition names it |
| 67 | TJX | 2026-03-31 | `0000109198-26-000008` · `tjx-20260131xexhibit1024.htm` | material contracts (10-K exhibit index) | — | no | — | not_debt_agreement | REFUSED as before (not debt, or no title read) |
| 68 | TJX | 2021-06-29 | `0001193125-21-202939` · `d169110dex101.htm` | Senior Unsecured Revolving Credit Facili | 2026 REVOLVING CREDIT AGREEMENT | no | 2026 REVOLVING CREDIT AGREEMENT · 2021-06-25 / — | extracted | READ: a 2025 document in the same accession as TJX's 2025 amendment restates it, but no pointer targets that document |
| 69 | TJX | 2025-05-09 | `0000109198-25-000033` · `exhibit101-firstamendmentt.htm` | Senior Unsecured Revolving Credit Facili | 2029 AMENDED AND RESTATED REVOLVING CREDIT AGREEMENT | yes | — / 2028 REVOLVING CREDIT AGREEMENT · 2023-05-08 | extracted | LIVE: amends and restates the 2028 agreement |
| 70 | UBER | 2023-11-24 | `0001552781-23-000469` · `e23472_ex10-1.htm` | 2025 Convertible Notes | — | no | — | not_debt_agreement | REFUSED as before (not debt, or no title read) |
| 71 | UBER | 2021-03-01 | `0001552781-21-000058` · `e21071_ex10-1.htm` | 2028 Convertible Notes | TERM LOAN AGREEMENT | yes | — / TERM LOAN AGREEMENT · 2016-07-13 | extracted | READ, unclassified: the panel carries no term loan, but no located exhibit says the term loan ended |
| 72 | UBER | 2022-04-05 | `0001552781-22-000307` · `e22228_ex10-1.htm` | Senior Unsecured Revolving Loans | REVOLVING CREDIT AGREEMENT | yes | — / REVOLVING CREDIT AGREEMENT · 2015-06-26 | extracted | LIVE chain: amends the 2015 revolving credit agreement |
| 73 | UBER | 2023-03-03 | `0001552781-23-000080` · `e23085_ex10-1.htm` | 2025 Convertible Notes | TERM LOAN AGREEMENT | yes | — / TERM LOAN AGREEMENT · 2016-07-13 | extracted | READ, unclassified: as the 2021 term loan amendment |
| 74 | UBER | 2023-03-14 | `0001552781-23-000109` · `e23109_ex10-1.htm` | 2028 Convertible Notes | TERM LOAN AGREEMENT | yes | — / TERM LOAN AGREEMENT · 2016-07-13 | extracted | READ, unclassified: as the 2021 term loan amendment |
| 75 | V | 2013-01-31 | `0001193125-13-032823` · `d476341dex101.htm` | Unsecured Revolving Credit Facility | 364-DAY REVOLVING CREDIT AGREEMENT | no | 364-DAY REVOLVING CREDIT AGREEMENT · 2013-01-31 / — | extracted | READ, unclassified: a 2013 364-day agreement; nothing located names it |
| 76 | V | 2016-05-10 | `0001403161-16-000027` · `exh22aroptionagreement.htm` | Unsecured Revolving Credit Facility | AMENDED AND RESTATED PUT-CALL OPTION AGREEMENT | yes | — | not_debt_agreement | REFUSED as before (not debt, or no title read) |
| 77 | VITL | 2026-02-26 | `0001193125-26-073423` · `vitl-ex10_10.htm` | material contracts (10-K exhibit index) | — | no | — | not_debt_agreement | REFUSED as before (not debt, or no title read) |
| 78 | VRRM | 2025-10-17 | `0001193125-25-242530` · `vrrm-ex10_1.htm` | 2021 Term Loan Due 2028 | AMENDED AND RESTATED REVOLVING CREDIT AGREEMENT | no | REVOLVING CREDIT AGREEMENT · 2025-10-17 / — | extracted | LIVE: the A&R revolver |
| 79 | VRRM | 2021-03-29 | `0001564590-21-015880` · `vrrm-ex101_62.htm` | Revolving Credit Facility | FIRST LIEN TERM LOAN CREDIT AGREEMENT | yes | FIRST LIEN TERM LOAN CREDIT AGREEMENT · 2021-03-26 / FIRST LIEN TERM LOAN CREDIT AGREEMENT · 2018-03-01 | extracted | LIVE chain: restates the 2018 first-lien term loan (2021 Term Loan on the panel) |
| 80 | VRRM | 2018-06-21 | `0001104659-18-041476` · `a18-15692_1ex10d1.htm` | 2021 Term Loan Due 2028 | GORES II SUBSCRIPTION AGREEMENT | no | — | not_debt_agreement | REFUSED as before (not debt, or no title read) |
| 81 | VRRM | 2025-05-15 | `0000950170-25-072679` · `vrrm-ex10_1.htm` | Revolving Credit Facility | REVOLVING CREDIT AGREEMENT | yes | — / REVOLVING CREDIT AGREEMENT · 2018-03-01 | superseded by `0001193125-25-242530` | SUPERSEDED, agreed: amends the revolver the A&R restates |
| 82 | WERN | 2026-10-08 | `0000793074-26-000159` · `wern-20261005ex101.htm` | 22 Unsecured Credit Agreement | — | — | — | fetch_failed | UNREADABLE at $0 (cache miss): read and classified at the paid build |
| 83 | WERN | 2026-06-10 | `0000793074-26-000120` · `wern-20260605ex101.htm` | Loan Security Agreement Facility | LOAN AND SECURITY AGREEMENT | yes | — / LOAN AND SECURITY AGREEMENT · 2025-03-27 | extracted | LIVE chain: amends the 2025 loan and security agreement |
| 84 | WERN | 2026-04-14 | `0000793074-26-000090` · `wern-20260127ex101.htm` | 22 Unsecured Credit Agreement | STOCK PURCHASE AGREEMENT | no | — | not_debt_agreement | REFUSED as before (not debt, or no title read) |
| 85 | WERN | 2025-04-02 | `0000793074-25-000019` · `wern-2025327ex101.htm` | Loan Security Agreement Facility | LOAN AND SECURITY AGREEMENT | no | LOAN AND SECURITY AGREEMENT · 2025-03-27 / — | extracted | LIVE: the receivables facility (on the panel) |
| 86 | WLK | 2010-07-08 | `0001193125-10-155766` · `dex101.htm` | Loan Related to Tax-Exempt Waste Disposa | AMENDED AND RESTATED LOAN AGREEMENT | no | LOAN AGREEMENT · 2010-07-02 / — | extracted | READ, unclassified: tax-exempt bond loan agreement |
| 87 | WLK | 2016-08-24 | `0001193125-16-689964` · `d247458dex101.htm` | Revolving Credit Facility | CREDIT AGREEMENT | no | CREDIT AGREEMENT · 2016-08-23 / — | extracted | READ, unclassified: the 2016 revolver; an Item 1.02 after the panel may have ended it, but no located exhibit says so |
| 88 | WLK | 2010-12-08 | `0001193125-10-276447` · `dex101.htm` | Term Loans Due 2026 | LOAN AGREEMENT | no | LOAN AGREEMENT · 2010-11-01 / — | extracted | READ, unclassified: GO Zone bond loan agreement |
| 89 | WLK | 2007-12-18 | `0001193125-07-267027` · `dex101.htm` | Loan Related to Tax-Exempt Waste Disposa | LOAN AGREEMENT | no | LOAN AGREEMENT · 2007-11-01 / — | extracted | READ, unclassified: tax-exempt bond loan agreement |
| 90 | WLK | 2009-02-09 | `0001193125-09-021484` · `dex101.htm` | Revolving Credit Facility | CREDIT AGREEMENT | yes | — / CREDIT AGREEMENT · 2008-09-08 | no_terms_returned | READ, unclassified: amends a 2008 agreement nothing located names |
| 91 | WLK | 2016-06-14 | `0001193125-16-620795` · `d211826dex101.htm` | Term Loans Due 2026 | — | no | — | not_debt_agreement | REFUSED as before (not debt, or no title read); a bank commitment letter |
