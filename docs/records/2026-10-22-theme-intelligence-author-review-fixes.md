---
id: 2026-10-22-theme-intelligence-author-review-fixes
status: recorded
date: 2026-10-22
prs: []
supersedes:
superseded-by:
---

# Theme intelligence: the code review of #771 — an author statement is atomic, retractable, linked to its run, as-of in reports, and never splits a name

**WHAT.** The five findings of `/code-review high` on merged #771. Operator, 2026-10-22: "apply
fixes and then merge".

1. **One transaction.** The article, its document record(s) and the AUTHORS_STATED issue are
   written together (`attribution._write`). Before, the issue came after the article's
   transaction, so a failure between them left a name with no record of who stated it.
2. **Retraction.** `author --article A-… --retract NAME --by WHO --reason "…"` removes an author
   the OPERATOR stated, at upload or later.
   - It never removes one read from the page or its text. Those are refused.
   - It records an AUTHORS_RETRACTED issue and a document history line, and drops the name from
     the document's declared statements, so no replay restates it.
   - With no author left, the article reads UNKNOWN again.
   - Before: a re-read keeps operator-stated names, so a misspelt name was permanent.
3. **A structured run link.** `Author.stated_in` holds the run that stated the author.
   - QA's check reads it instead of searching the provenance text for " in run …: ". That search
     broke the repo rule "parsers consume structured values, never rendered strings".
   - The provenance now reads `operator-stated by WHO: WHY`.
   - The field is serialized only when set, so every other stored author is byte-identical.
   - The three runs that applied the operator's ruling on 2026-10-22 predate the field. They are
     named in `attribution.LINKLESS_RUNS`, and QA checks them by their marker. No new run can
     pass that way.
4. **As-of source lines.** The weekly report's source line no longer shows an author stated after
   the report's run (`report._sources_line(…, until=run.finished_at)`). Late dismissals, prices
   and company proposals were already bound this way.
5. **No `;` in a name.** The document record keeps names "; "-joined, so such a name came back as
   two. It is refused at `Declared`, by `author`, and at the CLI's `--author` / `--name` /
   `--retract`.

**Not changed** (the review's two design costs):
- each `author` run handles one article and renders the registry once — the three-article ruling
  took three runs;
- an unpushed author run makes the next `state pull` refuse (push first), unlike a review run,
  which a pull carries. Carrying an author run would mean re-applying its statement onto the
  rebuilt articles; the refusal is loud and nothing is lost.

**HOW VERIFIED.**
- **Real data — a scratch copy** of `theme-intelligence-state` 0cdebc0f, imported fresh with this
  branch.
  - The three runs that applied the ruling (R-20261022T035402Z/035403Z/035404Z-author) still pass
    QA 22/22, "every stated author is on its article: 1 article(s)" each.
  - Both merge ingest runs still pass the author check (3 and 5 articles).
  - **Import then export leaves `articles.jsonl` and `documents.jsonl` byte-identical**, so the
    new field adds no noise to the registry.
- **Pins:** 19 tests in `tests/test_theme_intelligence_author_statement.py` (9 new).
  - A failure writing the record leaves the article and the document untouched, with the run
    FAILED.
  - A typo is retracted: the article reads UNKNOWN, QA says so, the declared name is gone, and a
    restatement clears it.
  - A retraction is refused for a name not credited, or one the page credits.
  - An author stated at upload can be retracted.
  - QA reads the run link, and passes an unlinked statement only for the three named runs.
  - A report rendered again shows "author UNKNOWN" where the statement came later.
  - A `;` name is refused by `author`, `Declared` and the CLI (exit 2).
  - An author with no link serializes exactly as before.
- **Mutation:** 21 mutants, all killed.
- **Suite:** see the PR.

**BOUNDARY.** Registry `theme-intelligence-state` 0cdebc0f, imported on 2026-10-22 (UTC) with
this branch (base main f705660a). "Byte-identical" compares the branch's JSONL files with a fresh
export of their import.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0.
- **The three linkless runs are an exception by name**, recorded in code and here.
- **A retraction applies to every render**, earlier weeks included. Only a statement is bound
  as-of: a retracted name is gone from the article record, and its history lives in the
  AUTHORS_STATED / AUTHORS_RETRACTED issues and the document's history.
