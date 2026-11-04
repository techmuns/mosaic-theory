---
id: 2026-11-04-an-amendment-heading-names-its-contract-in-its-recital
status: shipped
date: 2026-11-04
prs: []
supersedes:
superseded-by:
---

# An amendment whose heading names no contract is identified by the contract its recital names: SMPL's two credit amendments reach the covenant extractor again

**WHAT.** `covenant_extract.agreement_title` has a third reading, used only when the head carries
no capitals title ending in a debt noun (`_TITLE`) and is not a bare "INDENTURE". If the cleaned
head OPENS with an amendment heading in capitals (`_AMEND_HEAD`: up to three capitals words, none
of them OF, then AMENDMENT), the title is the FIRST contract the recital names, of any kind
(`_RECITAL_REF`: "the" or "that certain", then title-case words, then a contract noun). SMPL's "REPRICING AMENDMENT, DATED AS OF MARCH 16, 2018, BY AND
AMONG …" refers to "the Credit Agreement, dated as of July 7, 2017". Its "AMENDMENT NO 2.
(INCREMENTAL FACILITY AMENDMENT) …" defines "the Credit Agreement". Both now read `CREDIT
AGREEMENT`, which `is_debt_agreement` passes. Whether the named contract is debt stays that gate's
call: NCNO's "SECOND AMENDMENT TO OFFICE LEASE" is now named `OFFICE LEASE` and refused for it,
where it used to be refused as "no agreement at all". `is_amendment` recognises the same heading,
so these documents are marked as amendments on their own evidence. Until now SMPL's two were marked
only through a defect (see below). The end of `agreement_title` moved into `_as_title`, which
both readings use; its one addition, a strip of " .,-", is a no-op on the old path, whose title is
already stripped (item 2 below finds no other title changed). Extraction version
`2026-11-04.amendment-recital`.

**WHY — the decision, from the guard's own history.** #652 (`f55eff4a`,
`docs/records/2026-09-28-a-covenant-exhibit-is-identified-by-the-document.md`) put in the
IDENTIFY-OR-REFUSE guard to keep NON-debt documents away from a covenant extractor: NKE's CFO offer
letter, TGT's CEO transition letter, WERN's stock purchase agreement and UBER's capped-call
confirmation. Its corpus check counted 0 non-debt titles kept, and checked that every refusal
CARRYING A TITLE was a non-debt document. Refusals with no title were not audited one by one.
SMPL's two and NCNO's First Amendment were among them. That record accepted exactly this cost: *"The gate
can refuse a real agreement … Falsifier: a name whose covenant terms disappear at the next
artifact pass and whose exhibit is, on inspection, a real agreement."* SMPL is that falsifier,
caught at $0 by the pre-spend check (#893) before any pass.

An amendment to a credit agreement IS a debt contract. SMPL's committed covenant table (assembled
2026-08-18, before the guard) was extracted from exactly these two exhibits: 19 rows, 14 present,
stating the incremental term loan's principal, its rate, the maturity, the leverage covenant and
the amortization. Every titled amendment is already normalised to the contract it amends
("SIXTH AMENDMENT TO SECOND AMENDED AND RESTATED CREDIT AGREEMENT" → "SECOND AMENDED AND RESTATED
CREDIT AGREEMENT"). An amendment that names its contract only in the recital should get the same
identity, and it now does. So: yes, it passes.

**WHY THE RULE IS THIS NARROW.**
- *Anchored at the start of the head.* TGT's 8-K cover document (`form8-k_creditagreement105.htm`,
  which the selector fetches for its filename) cites "the Credit Agreement" just as an amendment's
  recital does. Only the heading says a document IS an amendment.
- *Capitals only*, for the reason `_IS_AMENDMENT` gives: an agreement's heading is set in capitals.
  A title-cased heading is a different shape: it names its contract itself. VRRM's "Amendment No. 4
  to REVOLVING CREDIT Agreement" defines its contract in the recital as the shorter "Credit
  Agreement". Read from there, it would be named for a contract its revolver is not, and split from
  the "AMENDED AND RESTATED REVOLVING CREDIT AGREEMENT" it amends. It stays refused, and is left for
  its own fix (below).
- *Not a charter.* "CERTIFICATE OF AMENDMENT" and "ARTICLES OF AMENDMENT" amend a charter, not a
  contract, so OF may not stand before AMENDMENT in the heading.
- *The first contract named, of any kind, not the first debt contract.* The first draft of this
  change read the recital with `_BASE_REF`, which a titled amendment already falls back on. Review
  round 0 showed why that is wrong here: `_BASE_REF`'s "the … Agreement" branch names ONLY a
  Credit/Loan/Indenture/Note agreement, and it is case-insensitive. So an amendment whose recital
  names "the Employment Agreement" was named for a later "the Credit Agreement" and passed. And a
  prose run ("the representations and warranties in the Credit Agreement") was taken as the name.
  An identity reader must not lean toward the answer the gate passes. `_RECITAL_REF` takes the
  first title-case name ending in a contract noun (Agreement, Indenture, Lease, Note(s),
  Guaranty/Guarantee, Plan, Letter), allowing "and"/"of" inside it ("Amended and Restated"). It
  changes no title on the corpus against the `_BASE_REF` draft (item 2).

**HOW VERIFIED** (real runs; CORPUS BEFORE SYNTHETIC).

1. **Every extraction target on every committed page**, simulated at $0 the way
   `extract_covenant_terms` loops: `_core_agreement_exhibits`, then fetch, the guard, the size cap
   and the 4-exhibit cost bound. There are 104 targets on the 25 committed pages with pointer rows.

   | | reach the LLM | cost-bound | refused |
   |---|--:|--:|--:|
   | main `4a820016` | 54 | 8 | 42 |
   | this change | 57 | 8 | 39 |

   The three that move are SMPL's two credit amendments (0001213900-18-003172,
   0001104659-19-060856) and NCNO's First Amendment to its 2022 Credit Agreement
   (0001902733-24-000041). All three are now titled `CREDIT AGREEMENT`. No target leaves the LLM,
   and no other page moves. One other refusal changes only its flag text: NCNO's office-lease
   amendment now declares itself "OFFICE LEASE" instead of "no agreement at all".
2. **Every located exhibit, not only the targets:** 184 exhibits on the same 25 pages' pointer
   rows, against main's module. 6 titles change: SMPL ×2 and NCNO's First Amendment (`CREDIT
   AGREEMENT`), BURL's 2014 "AMENDMENT No. 4 … to the Credit Agreement dated as of February 24,
   2011" (`CREDIT AGREEMENT`), and NCNO's second and fourth office-lease amendments (`OFFICE
   LEASE`, refused). 1 `is_amendment` changes, on BURL's 2014 amendment (False → True, which is
   correct). BURL's is a target past BURL's cost bound, so it is never fetched, before or after.
   The final code and the `_BASE_REF` draft give the same 6 titles, the same 1 amendment flag and
   the same fate for all 104 targets.
3. **The pre-spend check, A/B on identical inputs.** `vinci dossier precheck --ticker SMPL` on a
   copy of the store the paid run `4f30d3a2` used (sha256 `bad8ac0aad77…`) and the operator's
   2026-11-04 exports:
   - main's module: **13 regressions**, row 43's count reproduced exactly. The covenant one reads
     "`capital_structure.covenant_term_rows`: present → absent … declares itself no agreement at
     all" for both exhibits.
   - this change: **12**. `covenant_term_rows` is now "decided by the paid draw, not compared — the
     covenant phase sends at least one located exhibit to the model".
   - the diff between the two reports is that one field and the counts; the other 12 are the
     export's ('Fiscal Year Change' and the column-order refusal) and the data record's.
   - on a plain copy of the primary's store the same run gives 14: #893's 15 on such a store, less
     this one.
4. **Pins** (`tests/test_covenant_document_identity.py`, real heads in
   `tests/fixtures/covenant_heads/`: 10 exhibits, each the first 3,000 characters `_fetch_exhibit`
   returns, which is all of `agreement_title`'s input):
   - Positive: SMPL ×2 and NCNO's First Amendment read `CREDIT AGREEMENT`, pass the gate, and are
     amendments. This failed first on main (`None`).
   - End-to-end: SMPL's frozen 2026-08-18 page, whose pointer rows are the committed page's,
     through `extract_covenant_terms` with SEC serving the real exhibits. Both credit amendments
     reach the extractor, in order, and neither is refused. `forecast_llm_fields` leaves the table
     to the paid draw. This failed first on main.
   - Negative: NCNO's office-lease amendment is named `OFFICE LEASE` and refused; TGT's 8-K cover
     is not an amendment; NKE's offer letter, TGT's transition letter, UBER's confirmation and
     TJX's stock-plan amendment are refused; VRRM's title-cased amendment is not renamed `CREDIT
     AGREEMENT`.
   - Review round 0, each DERIVED from a real head and each failing on the first draft: NCNO's head
     with its object swapped to "the Employment Agreement" is named `EMPLOYMENT AGREEMENT` and
     refused (the draft read `None`, and `CREDIT AGREEMENT` once the review's first repair was in);
     NCNO's head cut so a prose run comes first still reads `CREDIT AGREEMENT`; SMPL's head with a
     CERTIFICATE / ARTICLES OF AMENDMENT heading reads `None`.
   - Mutations on the final code: 10 run, 10 caught. They were: drop the recital reading; require
     no heading; unanchor the heading (`^` removed AND `.search`); make it case-insensitive; let OF
     stand before AMENDMENT; fix `_ORD.upper()` and drop the new `is_amendment` line; refuse a
     non-debt base inside `agreement_title`; read the base with `_BASE_REF` again; make
     `_RECITAL_REF` case-insensitive; let it name only an Agreement. A control (fix `_ORD.upper()`,
     keep the new line) survives by design: the pins still hold once that defect is fixed.
     MUTATIONS THAT COULD NOT FAIL, found on the way, and all of them the pins' or the mutation's
     fault. Removing `^` alone, or swapping `.match` for `.search` alone, unanchors nothing,
     because each half anchors by itself; that happened twice. And the VRRM pin was first a
     hand-cut 600-character string that stopped before character 888, where the recital names "the
     Credit Agreement", so it could not fail. It now reads VRRM's real 3,000-character head.
5. Suite: ruff and `mypy --strict vinci` clean. `pytest -m "not network" -rs` was run with the CIQ
   folder linked and without it; the counts are in the PR body.

**BOUNDARY.**
- *104 targets / 25 pages:* `data/dossiers/*/dossier.json` at `4a820016`: 27 pages, of which
  GOOGL and ROST carry no present pointer rows. Targets are `_core_agreement_exhibits` over each
  page's committed `covenant_pointer_rows`. Fates are simulated with no LLM call. Exhibit text is
  the primary checkout's EDGAR cache, read 2026-11-04, and 0 fetches failed.
- *184 exhibits:* every distinct (accession, filename) on those pages' pointer rows that have an
  accession.
- *13 → 12:* SMPL only; exports Financials annual `cc99900b61`, quarterly `3a3e2873fa`, Estimates
  `fd3fbcf38f`, comps `647fa70755`; committed page assembled 2026-08-18; both runs at 2026-11-04
  10:16Z.
- *"No other page moves"* is the extraction-target set. Grouping and rendering are covered only by
  the NCNO reading below.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Two pages move, and only on their next re-assembly.** SMPL: 2 covenant calls, where main makes
  none. It gets back the targets its committed table was built from, so the table is restored
  rather than lost. NCNO: 1 more call (2 in all). Its committed page (2026-08-18, before the guard)
  already carries 7 rows from that First Amendment. The guard alone would have dropped them, and
  the field-presence check could not see it, because NCNO keeps rows from its 2024 agreement
  either way. The committed pages do not change until each name is re-assembled.
- **ACCEPTED — NCNO's First Amendment groups with a contract it does not amend.** It amends the
  2022-02-11 Credit Agreement. The other located NCNO agreement (0001902733-24-000171) is a new
  Credit Agreement dated 2024-10-28. Both read `CREDIT AGREEMENT`, and both are under one pointer
  family, so they were one group before titles existed too (`_ambiguous_titles` leaves same-family
  renewals merged, by design). On the committed page the 2024 agreement governs all 7 terms in that
  group. The 2024-02 amendment is only the base of two "amended by" chains (maturity, security),
  which read a replacement as an amendment. This is pre-existing, not introduced. *Falsifier:* a
  term the 2024 agreement leaves unstated and the 2024-02 amendment states would govern from the
  replaced facility.
- **NOT FIXED, reported — `_IS_AMENDMENT` is built from `_ORD.upper()`.** `.upper()` turns `\d`
  into `\D` and `\s` into `\S`, so the pattern matches ANY capitals "<words> AMENDMENT"
  ("OFFER LETTER AMENDMENT", "THE LEASE AMENDMENT"), present since #653 (`a88e95d5`). Of the 57
  targets reaching the LLM after this change, it decides `is_amendment` on only SMPL's two, and
  `_AMEND_HEAD` now holds those. Fixing it can change `agreement_is_amendment` wherever a capitals
  "<words> AMENDMENT" sits in a head's first 900 characters, so it needs its own measurement and
  PR.
- **NOT FIXED, reported — a title-cased amendment heading is still refused.** On the committed
  corpus there are three: VRRM's Amendment No. 4 to its Revolving Credit Agreement
  (0000950170-25-072679), and CNXC's Third and Fourth Amendments to its Receivables Financing
  Agreement (0001803599-24-000117, 0001803599-25-000014). None is on a committed page now (VRRM's
  10 rows all come from the GORES II subscription agreement the guard refuses; CNXC was assembled
  after the guard), so nothing is lost. But real covenant terms go unread. Reading the heading's own
  title-cased name, not the recital's defined term, is the likely fix. It should stay on amendment
  headings: a reader that took title-cased titles generally would also reach NFLX's title-cased
  notes purchase agreements and commitment letters. It is its own PR.
- **NOT FIXED, observed — SMPL's restored table may not describe the facility in force today.** The
  committed digest gives the 2019 incremental term loan's maturity as July 7, 2024, a date already
  past. The located pointers are 2018 and 2019 amendments. Whether they are SMPL's governing
  documents today is a question for the pointer layer, which this change does not touch.
- **The anchor half's only pin is derived.** No head in the corpus carries a capitals AMENDMENT
  anywhere but its start, so the anchor is pinned on TGT's real 8-K cover with an 8-K/A label
  inserted, and says so.
