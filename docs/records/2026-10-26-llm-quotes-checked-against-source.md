---
id: 2026-10-26-llm-quotes-checked-against-source
status: shipped
date: 2026-10-26
prs: [804]
supersedes:
superseded-by:
---

# A quote an LLM returns is now checked against its source in code: covenant terms, the maturity event and graph edges keep a value only when its quote is a span of the document — the committed corpus fails 49 of 393, 1 of 2 and 13 of 339, and no failure looks recalled

**WHAT.** A verbatim-span check, and the three LLM phases that lacked one now use it.

- **The check** — `vinci/verbatim.py`. `SourceText(text).match(quote)` returns one of four answers:
  `verbatim` (one contiguous span), `elided`, `not_found` or `empty`. It is deterministic and calls
  no model. Both sides are reduced to one comparison key before matching:
  - NFKC normalisation;
  - every quote mark folded to one mark, and every dash folded to one dash;
  - case folded;
  - all whitespace and invisible format characters removed.

  A quote with ellipses is `elided` when every piece is a span AND the pieces occur in the
  document's order. Punctuation is trimmed only where it touches a cut: at an ellipsis, or at the
  quote's end. Nothing else is forgiven.
- **Covenant terms** (`covenant_extract._extract_from_exhibit`). A term whose quote is not a span
  of the exhibit text the model was sent becomes UNKNOWN. So does a present term with no quote.
  The note reads `(E5) refused: the model's quote is not in <exhibit>` (or `… gave no quote
  from …`), and a qa flag names the term. The row stays in the set, and the note keeps the
  accession that `governing_terms` dates rows by.
- **The maturity event** (`extract_maturity_event`). The model's full verbatim is checked against
  the 8-K body it was sent, before the 400-character cut. A miss is UNKNOWN plus a flag.
- **Graph edges** (`graph/extract.extract_graph_edges`). An edge whose evidence is not a span of
  the 10-K excerpts the model was sent is dropped before resolution. The drop is counted as
  `info["evidence_refused"]`, which `graph_coverage` carries on each name's row and in the report
  total, and `vinci graph-coverage` prints it. Test 0 (`graph/test0.score_test0`) carries it on
  each focal's row too, so a refused edge never reads as a silent CIQ miss.
- **The corpus run** — `scripts/audit_verbatim_corpus.py`. It runs the same `SourceText` over the
  committed artifacts and writes nothing back to them.
- **Pins** — `tests/test_verbatim.py`, on 16 real cases in `tests/fixtures/verbatim/real_cases.json`.
  Each case is a committed quote (or one piece of one) with a verbatim window of the EDGAR document
  it came from. EDGAR filings are public domain.
- **Three fixtures in `tests/test_dossier.py` were corrected.** Their fake documents did not contain
  what the fake model quoted. One of them, the P3 maturity pin, stored a paraphrase as PRESENT: the
  body said "was converted", the verbatim said "converted to common stock (Notice of Conversion)".
  That is the defect this build exists for. The pin now uses MVST's real committed 8-K sentence.

**WHY.** A 2026-10-22 research report (item P2-14) found the gap; the report is not in this repo
and reached this build through its brief. Covenant quotes and graph-edge evidence were stored as
the model returned them, while driver extraction checks its quotes. Only the document can show that
a value was READ rather than RECALLED. Recall is the live risk on filings older than the model's
training cutoff, and the covenant exhibits run back to 2009.

Absence was verified before building, not assumed:
- house words: `quote_norm`, `verbatim`, `span fidelity`;
- plain words: `appears in`, `substring`, `paraphras`, `fabricat`;
- `git log --all -i --grep` on six phrasings;
- `git log -S` on the quote and evidence lines, and on `driver_extract`'s containment line (which
  surfaced only #131);
- the definitions read: `_extract_from_exhibit`, `extract_maturity_event`, `extract_graph_edges`,
  `graph_coverage` and `judge_edges`.

The judge is an LLM, and it scores an edge against its own evidence, not against the filing.
`driver_extract`'s own docstring says covenant extraction "trusts the model to quote verbatim
(prompt-only)". Two related checks exist and were read: `theme_intelligence/verify.locate`
(span fidelity, with typographic normalisation) and `themes/exposure._fact_grounded` (fuzzy).

**HOW VERIFIED.**

*The corpus, through the production function* (`scripts/audit_verbatim_corpus.py`):

| corpus | quotes | verbatim | elided | refused | uncheckable |
|---|--:|--:|--:|--:|--:|
| covenant terms | 393 | 234 | 110 | 49 | 0 |
| maturity events | 2 | 1 | 0 | 1 | 0 |
| graph edges | 339 | 301 | 25 | 13 | 0 |

Of the 234 covenant verbatims, 186 pass under `driver_extract`'s existing rule (collapse
whitespace, lower-case). The other 48 need the new reductions. For graph edges the split is 248 and
53.

*Each reduction earns its place.* Undo one step and real passes are lost. Over the 732 term and
edge quotes:

| step undone | passes lost | what the source had |
|---|--:|---|
| whitespace removal | 83 | spaces `html_to_text` inserts at tag edges: `“ Maturity Date ”`, `WHEREAS ,` |
| quote-mark folding | 97 | `“”` where the model typed `'` or `"` |
| NFKC | 1 | an omission marked with the single character `…` |
| dash folding | 1 | `Cross‑Default`, written with U+2011, a non-breaking hyphen |
| case folding | 1 | a sentence-initial `Each` quoted as `each` |

The cut-punctuation trim adds 2 passes (AORT `...; (b)`, UBER's closing `).`), both covenant
quotes. Both are pinned as pieces of their real quotes, because the whole UBER quote spans 137,000
characters of its exhibit.

*Why the 49 covenant refusals fail.* A scratch classifier assigned each a class, and every one was
then read by hand:

- **pieces out of order — 16.** Every piece is in the exhibit, in a different order. AMZN interest
  ×2, AORT interest and security, IT maturity and security, MVST security, NKE interest ×2, PARR
  security, TGT interest, UBER interest, principal and security, WERN covenants and maturity.
- **the quote reads across source text — 16.**
  - Page furniture, 11: page numbers, a running header, bullets. AORT covenants and interest, BURL
    security, EPAM prepayment/EoD, NCNO covenants, NFLX security, PARR principal, TJX interest and
    security, V interest, WLK prepayment/EoD.
  - A table's column header, 1: NFLX covenants, `Period EBITDA`.
  - Words dropped with no ellipsis, 3: IT principal, UBER prepayment/EoD (`(as defined below)`),
    WERN prepayment/EoD.
  - A struck-out figure, 1: UBER upfront fee. The exhibit is a redline, and `html_to_text` keeps
    `<STRIKE>2.00</STRIKE>` inline beside the inserted `0.125`, so the text reads `2.00 0.125 %`.
    The model quoted the in-force figure.
- **a label or locator the model added — 11.** For example `2.03(b)`, `Section 2.08(c):`,
  `[Term Loan payment schedule]`. AMZN prepayment/EoD, AMZN security ×3, AORT maturity, CNXC
  termination fee, IT covenants, NFLX prepayment/EoD, NKE prepayment/EoD, UBER amortization and
  prepayment/EoD.
- **the quote diverges from the source — 6.** Stitched or bracketed text with no clean span: IT
  security, PARR interest (a fee grid), TGT prepayment/EoD (`(f)/(g) [bankruptcy]`), TJX and WERN
  prepayment/EoD, WLK covenants.

By name: AMZN 6 of 26 quoted terms, AORT 5/33, BURL 1/23, CNXC 1/15, EPAM 1/13, IT 5/18, MVST 1/23,
NCNO 1/16, NFLX 3/22, NKE 3/20, PARR 3/20, TGT 2/9, TJX 3/25, UBER 7/31, V 1/14, WERN 4/26,
WLK 2/30. BRBR, FUBO, SMPL and VRRM are 0.

*Maturity events.* TGT's verbatim opens `Section 3.01(e):`, and the body reads `(e) receipt by the
Agent`, so it is refused. MVST's is verbatim.

*Graph edges, 13 refused:*
- EXTR, 6. The evidence sits in the excerpts of the PRIOR 10-K (0000950170-24-098129), not the
  reconstructed one (0000950170-25-109742). One of the six names, Alpha Networks, is absent from
  the reconstructed 10-K altogether. So EXTR's edges were read from the earlier filing, and the
  file cannot say so because it carries no accession.
- MRCY, 4: two sentences stitched with ` / `.
- BKTI, 1: the filing's `LLC,,` quoted as `LLC,`.
- ITRI, 1: read across `1 Table of Contents`.
- ATOM, 1: the end of a sentence placed before the sentence itself.

The judge called 12 of the 13 `real_supply_chain`.

*No refusal carries the signature of recall* — a figure or a name the source does not contain.
- Covenant terms: `synthesis._claim_figures` finds every figure of 47 of the 49 refused VALUES in
  the exhibit. The other two were read by hand. AORT's is a `2.75%-3.75%` range whose dash parses
  as a minus. NFLX's are dates written `9/30/2009` for the exhibit's "September 30, 2009". NFLX's
  `$200,0000,000` is the filing's own typo, copied faithfully.
- Graph edges: every refused edge's counterparty name is in its reconstructed excerpts, except
  EXTR's Alpha Networks (above).
- So the check refuses on the form of the quote. In this corpus it caught no case of a value that
  was invented.

*Pins and mutation.*
- `tests/test_verbatim.py` has 27 tests, one of them network-marked. Of the 16 real cases, 9 are kept (verbatim or elided) and
  7 are refused, drawn from all three corpora.
- End-to-end pins drive real text through `extract_covenant_terms`, `extract_maturity_event`,
  `extract_graph_edges` and `graph_coverage`.
- 19 mutants were run; all 19 were killed. The check's mutants: each reduction undone; empty
  counted as found; `found` widened to `not_found`; order ignored; elision off; each trim removed.
  The call-site mutants: each of the three gates switched off; the covenant flag dropped; the
  refusal note's accession dropped; the graph checked against the wrong text; the coverage count
  zeroed.
- The network-marked `test_fixture_windows_are_the_cited_documents_text` re-fetched all 16
  documents from EDGAR. Every window is the document's own text, and the whole document gives
  each case's answer.
- Full suite: `pytest -m "not network"`, plus ruff and `mypy --strict vinci`. The counts are in
  the PR.

**BOUNDARY.**
- *Covenant terms.* 27 committed dossiers at 545403de. 22 carry `covenant_term_rows` PRESENT and 21
  carry at least one quoted PRESENT term. The population is the 393 PRESENT term rows, each with a
  `verbatim: “…”` note; the 165 UNKNOWN rows carry no quote and were not counted. The source is
  `html_to_text` of each row's cited exhibit, 62 distinct exhibits.
- *Maturity events.* 8 dossiers carry one, 2 of them PRESENT (MVST, TGT). The source is the 8-K's
  primary body, cut at 1,200,000 characters as sent.
- *Graph edges.* `data/graph_coverage.json` as committed at be4268e6 (2026-06-26) and unchanged
  since: 339 edges from 75 of 109 focals. The source is RECONSTRUCTED, as the focal's latest 10-K
  filed on or before 2026-06-26, through `relevant_excerpts`.
- *Ablation.* The 732 = 393 + 339 term and edge quotes; the 2 maturity verbatims are excluded.
- *Fetching.* Exhibits and 10-Ks were read from the local SEC caches of the sibling checkouts,
  read-only. Submissions were re-fetched under a 1-day TTL, measured 2026-10-26. There were no
  fetch failures and nothing was uncheckable.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **The next re-assembly withholds values that were most likely read correctly.** That is the 49
  covenant terms above, now UNKNOWN with a flag each, and TGT's maturity event. A graph re-run
  drops the 13 edges. The committed artifacts are NOT rewritten by this build. The check proves
  reading; a quote that cannot prove it is refused, not vouched for.
- **Two governing values fall back to an older exhibit.** `governing_terms`, and its JS mirror in
  `frontend/views/shared/dossier.js`, let the latest PRESENT row govern. When a NEWER exhibit's term
  is refused, the older base value governs, with nothing saying the newer exhibit stated the term.
  Simulated on the committed corpus with the 49 refusals applied: EPAM prepayment/EoD reverts from
  8-K 0001352010-21-000039 to 0001352010-17-000022, and NKE prepayment/EoD from 0000320187-26-000020
  to 0000320187-25-000008. Found by this build's own review and not fixed here: the fix changes the
  Python collapse and its JS mirror together, which is a render change under the preview rule.
- *The softer alternative, not taken:* keep the value PRESENT with a flag. The brief allowed it.
  It was not taken because `driver_extract` drops the row, and a PRESENT value on an unverified
  quote is exactly what this build exists to stop. Reversing it is one branch in
  `_extract_from_exhibit`.
- **Page furniture is refused on purpose.** 11 of the 49 read across page furniture that our own
  parser leaves inside a clause: page numbers, a running header, bullets. A gap of digits is the one
  gap a span check must never forgive, because it is where a figure would hide. The fix belongs in
  `html_to_text`, not in the check: a follow-up.
- **Presence, not support.** A short quote is a span of many documents, and an ellipsis can omit a
  qualifier. A pass says the words were read from this document. It does not say they carry the
  value attached to them. The VALUE is not traced to its quote (`driver_extract` does trace it):
  a follow-up.
- **Not done here, reported:**
  - `graph_coverage.json` carries no accession. That was flagged when it was committed
    (be4268e6), and it is why EXTR's vintage is a question at all. `GraphEdge` has the accession;
    `coverage.py` drops it on output.
  - `driver_extract` keeps its own whitespace-and-case rule, so it lacks the quote-mark folding
    that accounts for 97 passes here. Two normalisers for one question is the divergence class
    CLAUDE.md warns about.
  - `html_to_text` keeps a redline's struck-out text inline (UBER's `2.00 0.125 %` above), so every
    extractor that reads an amended exhibit is sent deleted terms beside the ones in force. Not
    measured beyond the one case found here.

**Incident → invariant.** P2-14 → `vinci.verbatim` at all three call sites, pinned end to end on
real text. Shipped: Y.
