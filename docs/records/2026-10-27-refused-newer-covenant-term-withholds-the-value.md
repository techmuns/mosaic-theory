---
status: shipped
date: 2026-10-27
prs: [812]
supersedes:
superseded-by:
---

# A later exhibit's refused covenant term now withholds the value in force: it reads UNKNOWN, names the later filing, and keeps the older value as "Last verified" — and the web groups covenant terms by the agreement's own title, as the Markdown has since #652/#653

**WHAT.** STATE.md §5.0 row 32 item (18) closes.

- **The collapse** (`covenant_extract.governing_terms`). It still takes the latest PRESENT row of
  each (family, term). But when a STRICTLY LATER, DATED row in the same group is a refusal (#804's
  `(E5) refused:` note), the value in force becomes UNKNOWN, and two new fields carry the rest:
  - `refused_newer` holds the later refused rows;
  - `last_verified` holds the older PRESENT value.

  The (X-4) rule bounds what counts as later: a tied or empty date cannot establish that one
  exhibit came after another, so neither one withholds. A later row that does not state the term
  changes nothing, because an amendment that never mentions a term leaves it in force. The note's
  prefix is one constant, `REFUSED_NOTE_PREFIX`. The extractor writes it, the collapse reads it,
  and `dossier.js` mirrors it.
- **The page.** The flag LEADS and the older value FOLLOWS (the stamp-position rule). Python
  (`render._refused_newer_text`) and JS (`refusedNewerText`) write it identically.
  - Main body: `Interest / coupon: UNKNOWN — not verified since 2021-12-22: a later exhibit
    (filed 2025-07-29) states this term, but its quote could not be matched to the filing, so its
    value is withheld. Last verified: <the 2021 clause>`. On the web UNKNOWN is the
    `pill unresolved` badge, as on every other UNKNOWN fact.
  - The appendix table (on-demand on the web, printed in full): the same lead, then the refused
    row's own note (accession, exhibit file, why), then the last verified clause. Its Source §
    reads `last verified: …`.
- **The web's covenant grouping.** `dossier.js` gains `_ambiguousTitles` and groups by the
  agreement's own title, as `governing_terms` has since #652/#653 (2026-09-28). The operator
  approved this scope on the preview.
- **The synthesis digest.** `assemble.py` is unchanged in code and in scope by construction. The
  digest lists PRESENT governing values only, so a withheld term leaves it, as every other refused
  term already does, instead of reaching the LLM as the stale value in force. It takes effect at
  the next re-assembly.
- **The committed pages.** `data/dossiers/{NKE,BURL,NFLX}/dossier.md` and their
  `frontend/dossiers/` mirrors are re-rendered from their unchanged JSON (deterministic, no LLM
  call).

**WHY.**

*The defect.* #804 refuses a covenant term whose quote is not a span of its exhibit. Taking the
latest PRESENT row then handed the term to the OLDER exhibit whenever the newer one was refused.
The page showed that value as the term in force and never said a later exhibit had stated it. The
2026-10-26 artifact pass made it live:
- NKE's interest rate governed from 2023-03-13 over a refused 2024-03-11 statement;
- BURL's from 2021-12-22 over 2025-07-29, putting a LIBOR pricing grid on the page as the rate
  in force;
- NFLX's maintenance covenant from 2019-04-01 over 2021-06-17.

*Why UNKNOWN rather than the older value with a flag.* The later exhibit STATED the term. To call
the older value governing assumes the amendment did not change it, and that assumption is an
imputation. Fail loud, never fabricate.

*Why not a bare UNKNOWN, as Codex argued on #811.* The older clause is real, verified and dated,
and curating never deletes a fact. Shown after the flag and labelled, it gives the reader a bound
and names the exhibit to open. Dates go in the main body and accessions in the appendix, by K1b's
convention.

*Why the web grouping came with it.* Found while building: the JS collapse never received
#652/#653's title grouping. At 18d19bfb the web grouped covenant rows by the pointer's guessed
family, and the two collapses disagreed on 13 of 22 pages. On the web, BURL's ABL credit
agreement was still split across two convertible notes and a term loan — the defect #652 fixed in
the Markdown.

On that grouping the JS flag would fire on AMZN, CNXC, NKE, PARR ×2 and TJX, not on NKE, BURL and
NFLX. Each of the four extra pages pairs exhibits whose documents carry DIFFERENT titles, which is
exactly where the Python collapse keeps them apart:
- AMZN: a 2014 "CREDIT AGREEMENT" with the 2023 "FIVE-YEAR REVOLVING CREDIT AGREEMENT";
- CNXC: a 2021 "CREDIT AGREEMENT AND JOINDER AGREEMENT" with a 2023 "CREDIT AGREEMENT";
- PARR: a 2014 "UNCOMMITTED CREDIT AGREEMENT" with a 2015 "CREDIT AGREEMENT";
- TJX: a 2020 "364 DAY REVOLVING CREDIT AGREEMENT" with the 2025 "2029 AMENDED AND RESTATED
  REVOLVING CREDIT AGREEMENT".

AMZN's and TJX's are plainly different contracts. The page would have announced a supersession
the documents do not show. The JS could not stay in lockstep without the title grouping.

**HOW VERIFIED.**

*The count, re-taken before building* (`governing_terms` on each page's own term and pointer
rows): 39 refused rows.
- **3** are later than their group's latest PRESENT row: NKE, BURL and NFLX, as the pass recorded.
- **6** are earlier: AORT, BURL, NKE, PARR, and UBER ×2.
- **30** sit in groups with no PRESENT row, so they already read UNKNOWN.
- **0** are tied or undated.

*Real runs, all on the committed JSON, nothing re-extracted:*
- **Markdown.** Every committed page was re-rendered: **3** files change (NKE, BURL, NFLX),
  **2** lines each (the main-body line and the appendix row). The six earlier-refusal cases and
  every family footer render as before.
- **The digest.** It changes on the same 3 pages, losing one line each:
  - NKE's 2023 SOFR grid;
  - BURL's 2021 LIBOR grid;
  - NFLX's 2019 "no traditional financial-maintenance covenant".
- **Python ↔ JS collapse.** The two agree on **22 of 22** pages with term rows, field by field:
  family, term, status, note, accession, the refused rows, the last verified ref, and the lead
  text. Before the port they disagreed on 13. Both flag exactly the same three terms.
- **The web.** It changes on **13 of 22** pages:
  - BRBR, TGT and V: labels only;
  - AMZN, AORT, BURL, CNXC, NFLX, NKE, PARR, TJX, UBER and WLK: regrouped.

  Rendered by headless Brave on main and on this branch:
  - On all 13, the web's main-body covenant block equals the Markdown's, line for line in order.
    The one difference is K1b's dated suffix, which the web never prints (FOUND, NOT FIXED below).
  - The flag text on the web equals the Markdown's on all three pages.
  - Every other `<details>` is text-identical before and after.
  - No `undefined`, `NaN` or `[object Object]` appears in any `<details>`, collapsed or under
    print media with the full-dossier scope.
- **The preview.** The operator saw the main body, the collapsed provenance `<details>` and its
  print/force-open state for NKE, BURL and NFLX, plus the Markdown diff and the main body of the
  other ten regrouped pages, and approved it (2026-10-27, "Approved, including the JS
  title-grouping port").

*Pins* (`tests/test_covenant_refused_newer.py`, 21 tests):
- **Frozen fixtures.** `tests/fixtures/refused_newer/` holds the committed capital-structure
  blocks of NKE, BURL and NFLX at 18d19bfb, unmodified. Each end-to-end test renders the REAL
  committed dossier with its block swapped in, through `render_markdown` and through the
  production `renderDossier` under node.
- **Positive:** the three flags, their lead, the refused accession in the appendix row, and the
  older value after the flag.
- **Negative:**
  - on the same NKE page, the 364-day agreement's refused 2025 interest row under its verified
    2026 renewal;
  - built from the real types: a later row that does not state the term, a tied date, an undated
    refusal, and an undated governing row.
- **Writer → reader:** a refusal written by `_extract_from_exhibit` withholds the value when it
  is the later row.
- **The living corpus:**
  - every committed refused row is classified independently of the flag — later ones are flagged,
    earlier ones are not;
  - the whole Python ↔ JS collapse agrees on every committed page.
- **Node-free:** the JS carries the shared prefix and the title grouping.

*Mutation: 17 of 17 mutants killed.* Each mutant was applied, run against the new pins, then
restored, with bytecode writing off.
- **Python collapse (7):**
  - no later refusal withholds;
  - an earlier refusal withholds too;
  - a tied refusal withholds;
  - the undated-governing guard is dropped;
  - the value is kept instead of withheld;
  - any later UNKNOWN withholds;
  - the extractor writes a different note.
- **Python render (3):** the main-body branch dropped; the appendix branch dropped; the flag
  trailing the clause instead of leading it.
- **JS (7):**
  - no later refusal withholds;
  - an earlier one withholds;
  - no title grouping (the pre-build web);
  - no title ever ambiguous;
  - the main-body branch dropped;
  - the appendix branch dropped;
  - the prefix constant drifting.

**BOUNDARY.**
- **Pages:** the 27 committed `data/dossiers/*/dossier.json` at main 18d19bfb, measured
  2026-10-27; 22 of them carry `covenant_term_rows` PRESENT.
- **Refused rows:** every term row whose note starts `(E5) refused:`, dated by its own pointer
  row, set against the latest PRESENT row of its own (family-or-title, term) group as
  `governing_terms` groups it. Unit: rows.
- **Python ↔ JS:** the whole collapse output per page, through node 26 on the same JSON.
- **The web:** headless Brave at 1280 px, the Analysis and Appendix tiers, served from an export
  of 18d19bfb's `frontend/` (main) and from this branch.
- **Markdown and digest:** each page's committed JSON rendered in memory and compared with the
  committed file (Markdown), or with `covenant_digest` on 18d19bfb's `covenant_extract` (digest).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Three values a reader saw as governing now read UNKNOWN.** Each was very likely in force
  unchanged, or close to it: #804 found no refused value that carries a figure its exhibit lacks.
  That is the trade #804 made, applied one level up. A refused statement is withheld, and so is
  the inference that it changed nothing.
- **The digest no longer gives the LLM those three terms** — not the older value, and not a
  warning. That matches every other refused term. If a synthesis is later shown reasoning as
  though a withheld term were absent, rather than unverified, the digest needs an UNKNOWN line
  for it.
- **A refusal is recognised by its note's prefix, not by a structured field.** The committed rows
  predate any such field, and adding one needs a re-assembly. Writer and reader share one
  constant, and two pins tie them: the writer → reader test and the node-free JS literal.
- **The web's covenant blocks change on 13 pages beyond the three.** Each now reads as its own
  Markdown has since 2026-09-28. Approved on the preview.

**FOUND, NOT FIXED.**
- **The web has never printed K1b's "— per an 8-K filed …" on a covenant line.**
  `covenantSourceSuffix` reads `g.base_ref` and `g.amended_by`, but `governingTerms` has returned
  `baseRef` and `amendedBy` since RC-1.5d (2026-07-07). So the suffix has been "" on every web
  and PDF covenant line since #482 (2026-08-20) shipped it, while the Markdown carries the dates.
  A render change, so a preview first. Recorded as STATE.md §5.0 row 32 item (19). The new flag
  computes its own dates and does not depend on it.

**Incident → invariant.** A refused newer term let an older exhibit govern unsaid →
`governing_terms` and `governingTerms` withhold the value behind a later dated refusal, pinned end
to end on frozen committed blocks in both languages, with a living-corpus classification and a
whole-collapse parity pin. Shipped: Y.
