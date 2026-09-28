---
id: 2026-09-28-a-covenant-exhibit-is-identified-by-the-document
status: shipped
date: 2026-09-28
prs: [652]
supersedes:
superseded-by:
---

# A covenant exhibit is identified by the document, not by the search that found it

**WHAT.** `_covenant_pointers` locates an instrument's governing agreement by full-text-searching
EDGAR for a CLASS-GENERIC phrase — "Indenture", "Credit Agreement" — and then labels whatever it
finds with that instrument's name. Nothing verifies the filing has anything to do with the
instrument. Two families sharing a phrase partition ONE hit list under a global `seen` set, so the
second family is handed whatever the first did not take: **the label is decided by arrival order.**

The consequence reached the pages. BURL's ABL amendment sits at position 14 of its `"Indenture"`
hit list and was published as a 2.25% convertible note **that matured in April 2025** — a 2030
maturity, Term SOFR pricing and a springing fixed-charge covenant, all attributed to a dead
convertible, on a name at 3.8x net debt/EBITDA. It is not a BURL quirk:

| name | the document actually is | it was labelled |
|---|---|---|
| VRRM | Amended & Restated Revolving Credit Agreement | 2021 Term Loan Due 2028 |
| WERN | **STOCK PURCHASE AGREEMENT** | 22 Unsecured Credit Agreement |
| UBER | a capped-call dealer confirmation | 2025 Convertible Notes |
| NKE | a **CFO offer letter** | material contracts |
| TGT | a **CEO transition letter** | material contracts |

A covenant-term extractor was being handed executive compensation letters, and whatever it
returned was published as that instrument's terms.

A second, independent defect fed the same surface: `_COVENANT_CLASS_RE` was
`\b(loan|credit|facilit|…)\b`, and the shared TRAILING `\b` makes every entry an exact word.
"facilit" is not a word, so it never matched "Facility" at all; the plurals fell out too
(`\bloan\b` misses "Loans"). Three real revolvers were therefore routed to the generic bucket and
published with the note *"no contract-level filing expected (aggregate line item)"* — a flatly
false statement about a facility that files its credit agreement.

**WHY.** The pointer's `family` is a guess and was rendered as a fact. The only thing that knows
what a document is, is the document: an agreement states its own name in its first lines. So the
fix asks it. `agreement_title` reads that name deterministically (no LLM) and normalises it to the
BASE contract — "Sixth Amendment to Second Amended and Restated Credit Agreement" becomes "SECOND
AMENDED AND RESTATED CREDIT AGREEMENT" — so an amendment groups with the contract it amends and
still supersedes it. `is_debt_agreement` then decides whether a covenant extractor should see the
document at all, and one that cannot be identified is REFUSED and flagged rather than extracted
under a guessed label. Identify or refuse.

The normalisation is not cosmetic: the governing collapse keys on the family, so had the title
stayed at the amendment INSTANCE, BURL's Fourth and Sixth Amendments would have become two groups
and both would have read as governing.

**HOW VERIFIED.**

*The corpus, before the code.* 144 located exhibit heads were fetched from EDGAR across 24 names
and the reader iterated against all of them — not against the case that prompted it. The shipped
module keeps 68 and refuses 76, with **0 non-debt titles wrongly kept**: every refusal carrying a
title is a genuine non-debt document (equity awards, employment and transition letters, escrow,
investor-rights, tax-receivable, stock-purchase, put-call).

*The real run.* BURL re-assembled on this branch, exit 0. Its covenant headings, before → after:

    Covenants — Convertible Senior Notes 1.25% Mature on December 15 2027
    Covenants — Convertible Senior Notes 2.25% Mature on April 15 2025      -> Covenants — SECOND AMENDED AND RESTATED CREDIT AGREEMENT
    Covenants — Senior Secured Term Loan Facility Term B-7 Loans            -> Covenants — SECURITY AGREEMENT

Three headings naming instruments the documents are not became two naming the contracts they are.
The five credit-agreement exhibits collapsed into ONE group and the chain works — the maturity
line now reads "July 25, 2030 — per an 8-K filed 2018-07-02, amended 2025-07-29", base then
amendment. Every extracted fact survived (1.00:1.00 x8, SOFR x13, springing x4, July 25 2030 x2),
and the 10-K material-contracts pointer was refused with a flag naming what it found.

*Mutation — seven, all caught, and TWO SURVIVED THE FIRST ROUND.* That round is the finding worth
keeping. N1 deleted the refusal branch entirely and every pin stayed green, because all of them
exercised the two predicates and none exercised the branch. N2 dropped the `_NOT_DEBT` half of the
gate and also survived, because the pin that was supposed to cover it asserted on a STOCK PURCHASE
AGREEMENT — which contains no debt word, so it is refused either way; the pin could not tell the
two halves apart. Both now have pins that can fail: an end-to-end one asserting NKE's offer letter
never reaches the extractor, and the overlap case TAX RECEIVABLES AGREEMENT, where "RECEIVABLES"
IS a debt word. N3–N7 (amendment instance kept, digit guard dropped, base recovery removed,
pointer restored over the document, stem fix reverted) were caught first time. Sources restored
byte-identical; `__pycache__` cleared between mutants.

*A wrong turn, recorded.* The first title anchor keyed on the `(this "Agreement")` clause, which
looked perfectly regular across BURL's three exhibits. Measured on the corpus it matched **15 of
94** — an 85% fallback to the very labels being replaced. It was a rule generalised from one name,
and only the corpus run caught it; the reader took five measured iterations after that.

**BOUNDARY.** Measured 2026-09-28 on branch `fix/covenant-family-from-the-document` off
`60f9c147`.
- *11 of 26 names with >=2 agreement-class families on one efts phrase*: population = the committed
  `data/dossiers/*/dossier.json` carrying capital-structure instruments; unit = names; the phrase
  is `_covenant_query(description)` per instrument.
- *144 heads / 68 kept / 76 refused / 0 wrongly kept*: population = up to 3 exhibits per pointer row
  carrying an accession, across 24 names (2 of the 26 have no such row); unit = exhibit documents;
  each head = the first 3,000 characters, fetched live from EDGAR that day.
- *15 of 94*: the FIRST anchor, on the earlier sweep that took only the first exhibit per pointer
  row — a different population from the 144, and not comparable to the 68/76 above.
- *position 14 / position 10*: BURL's ABL accession's rank among DISTINCT accessions returned by
  efts for `"Indenture"` (34 hits, 24 distinct) and `"Credit Agreement"` (52 hits, 34 distinct),
  8-K forms, `ciks=0001579298`.
- *3 revolvers misrouted by the dead stem*: BURL, CNXC, UBER, over the same 26 dossiers.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **THE HEADINGS CHANGE FLEET-WIDE ON RE-ASSEMBLY, AND THE CODE LANDING DOES NOT MOVE THEM.** A
  committed dossier keeps its old grouping until that name is re-assembled, so code-closed and
  reader-closed are different dates here. Until the artifact pass runs, pages still carry the
  guessed instrument labels described above.
- **The gate can refuse a real agreement.** Precision on this corpus is total, but recall is not
  provable — a debt contract whose head my reader cannot parse is refused and its terms go
  UNKNOWN. That is the intended direction (a false UNKNOWN is recoverable; a covenant published
  against the wrong instrument is not), but it IS a loss. *Falsifier:* a name whose covenant terms
  disappear at the next artifact pass and whose exhibit is, on inspection, a real agreement.
- **The refusal list is a keyword list, and keyword lists rot.** A new non-debt contract type with
  a debt word in its name would pass. *Falsifier:* the corpus sweep re-run at the next pass showing
  a kept title that is not a debt contract.
- **Grouping by title merges two genuinely distinct contracts that share a name.** Two unrelated
  "CREDIT AGREEMENT" documents for one issuer would collapse into one group. Not observed on this
  corpus; accepted because the alternative in force today is worse and arbitrary.
- **NOT FIXED, reported not silently repaired:** `render.py:1245` composes `f"{lead} · {raw}"`, so a
  term whose extracted lead equals its raw clause prints twice — BURL's maturity still renders
  "July 25, 2030 · July 25, 2030". Cosmetic, on a decision value, and outside this brief.
- **NOT FIXED:** the pointer's `family` itself is still an unverified guess; this change stops it
  being *published* as the document's identity, but `_covenant_pointers` still searches with a
  class-generic phrase and still apportions hits by arrival order. A pointer layer that queries
  per-instrument is the real repair and is not attempted here.
