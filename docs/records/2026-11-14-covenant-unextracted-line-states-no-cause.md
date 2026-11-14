---
id:
status: shipped
date: 2026-11-14
prs: []
supersedes:
superseded-by:
---

# The covenant block's not-extracted line stops stating a cause the record does not hold: both renderers now say the page does not state why, and name the QA flags in dossier.json where the extraction's notes are kept. It was "(cost bound / fetch fail)" for every exhibit, and E5 had refused 22 of the 29 it names. The 16 committed pages keep the old line until a $0 re-render (STATE row 63)

**WHAT.** `vinci/dossier/render.py` (`_covenant_term_lines`) and `frontend/views/shared/dossier.js`
(the covenant-terms block) print one line for the located agreement exhibits the term rows do not
cite. Each printed "(cost bound / fetch fail)" for every such exhibit. Both now print:

> N located agreement exhibit(s) not extracted this run; this page does not state why (the
> extraction's notes are QA flags in dossier.json) — see the pointer table: <accessions>

The set of accessions is unchanged: located pointer accessions minus those the term rows cite.
No committed page is re-rendered here.

**WHY.** The line gave two causes for every exhibit, whatever happened to it. On the committed
corpus most of them were refused, a cause it did not offer. E5 reads the exhibit's own heading and
refuses one that is not a debt agreement (`covenant_extract.extract_covenant_terms`, the IDENTIFY
OR REFUSE branch). EPAM's `0001352010-26-000015` declares itself no agreement at all, and NCNO's
`0001902733-26-000022` is an office lease. Both pages told the reader the cause was the cost bound
or a fetch failure.

*Why neutral, and not each exhibit's own reason.* The brief asked for each exhibit's reason where
a STRUCTURED field records it. None does. `CovenantPointer` carries `family`, `filing`,
`filing_date`, `accession`, `exhibits` and `note`. `CovenantTerm` carries a term's value and
citation. The reason exists only as an `(E5)` QA-flag string, which `flags._QA_MARKERS` hides from
the page. The cost-bound string names the exhibit's filename, not its accession, so a reader of the
flags would have to re-derive which pointer it belongs to. Two paths leave no flag at all: an
exhibit the extraction ran on and the model returned no terms for, and a located pointer with no
exhibit for `_core_agreement_exhibits` to target (none on the committed corpus at `6652a242`).
Parsers consume structured values, never rendered strings (CLAUDE.md), so the line claims no
cause. It says where the notes are kept, and does not promise one for each exhibit.

*The field the extractor would need* (not built; populating it needs a paid re-assembly): one
outcome per targeted exhibit, written by `extract_covenant_terms` at the point each branch of its
loop appends its flag or extracts. It would be attached with `covenant_term_rows`
(`assemble.py`, after synthesis). A shape that fits the loop: `CapitalStructure.covenant_exhibit_
outcomes: Sourced[list[CovenantExhibitOutcome]] | None`, each holding `accession`, `filename`,
`family`, and `outcome`, one of `extracted`, `cost_bound`, `fetch_failed`, `not_debt_agreement`,
`too_large`, `llm_error` or `no_terms_returned`. It would also hold `declared_title`, the heading
E5 read, or None. Both renderers would then print each exhibit's outcome from it. A page without
the field, which is every committed page until it is re-assembled, keeps the neutral line.

**HOW VERIFIED.**
- *Pins, end to end, on frozen committed JSON* (`tests/test_covenant_unextracted_reason.py`). The
  fixtures `tests/fixtures/covenant_unextracted/{EPAM,NCNO,AMZN,BURL}.json` hold each page's
  committed `capital_structure` block, unmodified, and its `(E5)` QA flags. Each test hosts the
  block in the real committed dossier and renders it through `render_markdown` and through the
  production `renderDossier` in node:
  - (precondition) located minus cited is exactly the case's refused and cost-bound accessions,
    and the frozen flags record each one's reason;
  - (−) EPAM, NCNO, AMZN, BURL: neither renderer's line names a cause, and "cost bound / fetch
    fail" appears nowhere on either page. The web line equals the Markdown line;
  - (+) AMZN, BURL: each genuinely cost-bound exhibit is still listed on both renderers. The line
    names the record that holds its cost-bound note;
  - (− living corpus) no committed page's line names a cause.
- *Red at base* (`188e0476`, before the fix): 11 of the 15 nodes fail and the 4 preconditions
  pass. Each (−) node fails on the cause words (`assert not ['cost bound', 'fetch fail']`). The (+)
  nodes fail on the pointer half; their listing half held at base, because the old line already
  listed every accession. The corpus node fails on AMZN, the first page in sort order.
- *Re-render over a copy, not committed.* Every committed `dossier.json` at `6652a242` was
  rendered with head code (`render_markdown`, the scenario card, `dossiers_root=data/dossiers`, as
  `refresh.py` writes `dossier.md`) and diffed against its committed `dossier.md`. **16 of 26
  pages move, each by exactly that one line (one out, one in), and nothing else moves:** AMZN,
  BRBR, BURL, CNXC, EPAM, IT, NCNO, NFLX, NKE, PARR, TGT, TJX, UBER, V, VRRM, WLK. The other 10
  are byte-identical: FUBO, GOOGL, LLY, MCK, ORKA, ROST, SMPL, TECX, VITL, WERN. Each
  `frontend/dossiers/<T>.md` equals its `data/dossiers/<T>/dossier.md` at `6652a242`, so the
  mirror moves on the same 16. The web view renders from the JSON, so it changes on deploy with
  no artifact.

**BOUNDARY.** Every count is over the committed corpus at main `6652a242` (2026-11-14): 26
`data/dossiers/*/dossier.json`, of which 16 print the line. The line names 29 accessions: 22
carry an `(E5) not a debt agreement` flag naming the accession, and 7 carry an `(E5) exhibit not
extracted (cost bound)` flag naming the exhibit `_core_agreement_exhibits` targets for that
pointer. None carries a fetch-failure flag, and none is unaccounted for. Of the 16 pages, 12 name
only refused exhibits; AMZN and WLK only cost-bound ones; BURL and NFLX both. At the earlier base
`188e0476` the figures were 15 pages and 28 accessions (21 refused, 7 cost bound). IT's
`0000930413-17-000070` arrived with #1070. The pins' red-at-base count is over the 15 nodes of
`tests/test_covenant_unextracted_reason.py`, run at `188e0476` with the fix absent: 11 failed and
4 passed.

**WHAT IT COSTS / WHAT IS ACCEPTED.** The pages with a genuinely cost-bound exhibit (AMZN, WLK,
and BURL's and NFLX's cost-bound ones) no longer state that cause on the page. Its reason stays in
dossier.json's QA flags, which the line names. This is accepted until the outcome field above
exists, because a line that names the right cause on some exhibits and the wrong one on others
cannot tell the reader which is which. The 16 committed pages carry the old line until the $0
re-render, which the coordinator signals. Falsifier: a committed page whose line names a cause, or
whose unextracted exhibit has no `(E5)` note in its QA flags. `test_no_committed_page_names_a_cause_on_the_line`
reads the first through HEAD's renderer over every committed `dossier.json`; it does not read the
committed `dossier.md`, so the 16 pages that still carry the old line until the re-render do not
trip it. The second is checked here, by hand, once.
