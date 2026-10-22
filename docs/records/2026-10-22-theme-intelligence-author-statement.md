---
id: 2026-10-22-theme-intelligence-author-statement
status: recorded
date: 2026-10-22
prs: [771]
supersedes:
superseded-by:
---

# Theme intelligence: the operator can state an analysed article's author — $0, with who and why

**WHAT.** Item 2 of the open list (operator: "yes, start item 2 and the triage sheet",
2026-10-22).

- **The command** (`attribution.py`, $0, no model call, a run of mode `author`):
  `author --article A-… --name NAME [--name …] [--title T] --by WHO --reason "…"`.
- **What it writes:**
  - **the article record:** each name, its source `operator-stated by WHO in run R-…: WHY` (the
    marker an author stated at upload already carries, now `schemas.OPERATOR_STATED`), and its
    author status KNOWN;
  - **the article's document record(s):** the names among the declared statements, so a replay
    states them again, and a dated history line;
  - **an AUTHORS_STATED issue** on the article.
- **Refused, with nothing written:** a blank name, a blank "by" or reason, an unknown article,
  or a name the article already credits (compared as names, so "MORGAN  stanley" counts).
- **It never touches a thesis version.** A card's sealed source row keeps what its version
  recorded ("author UNKNOWN") until a later version. Live surfaces read the article record: QA
  and the weekly report's source line.
- **Also:**
  - **Re-reads.** A re-read keeps an operator-stated author, as it keeps a text-credited one
    (`pipeline._article_record`). Until now a later version of the page would have un-stated it.
  - **Weeks.** `author` joins `report.REFRESH_MODES`, so it never opens a desk week.
  - **`qa`.** It checks that every article an author run names carries an author stated in that
    run.
  - **Pulls.** An unpushed author run makes a `state pull` refuse (push first). It is never
    dropped silently.

**WHY.**
- 3 of the registry's 9 uploads name no author, so QA's integrity check "every analysed article
  names its author(s)" fails on both ingest runs of the 2026-10-21 merge.
  - The articles are Morgan Stanley's caffeine, ms-industry-5 and hc-industry:
    A-bcae0b1f5d86, A-9faa09cf8082, A-cfc65506a485.
  - The runs are R-20261021T101854Z-ingest and R-20261021T102637Z-ingest.
- The only route to an author was to analyse the documents again, paid
  (`docs/records/2026-10-21-theme-intelligence-one-step-upload.md`).
- **What the pages say.** I read the three originals (the retired pilot's archive, read only):
  - No page has a byline. The PDF metadata names no author, and no page carries an "Author …"
    line.
  - Each is an unsigned Morgan Stanley web article (morganstanley.com Insights) quoting Research
    analysts: for example Dara Mohsenian (caffeine), and Sheng Zhong and Chetan Ahya (Industry
    5.0).
  - The 6 sibling uploads that have authors got them from an explicit "Author …" line in the
    text, e.g. "Author Erin Wright, Healthcare Services Analyst".
  - Naming a quoted analyst as author would invent it. **The proposal is the institution,
    "Morgan Stanley"**, titled "institution — the page names no individual author". Stating it
    on the registry of record is the operator's call.

**HOW VERIFIED.**
- **Real data — a SCRATCH copy** of `theme-intelligence-state` 9939047e, imported fresh with this
  branch. The statement was a labelled probe (by `verification-probe`); nothing was pushed.
  - QA's author check on R-20261021T101854Z-ingest went from **FAIL** ("A-9faa09cf8082 (Morgan
    Stanley)") to **PASS** ("3 article(s)").
  - On R-20261021T102637Z-ingest it went from **FAIL** (A-bcae0b1f5d86, A-cfc65506a485) to
    **PASS** ("5 article(s)").
  - Three author runs, $0 each. The latest passed QA 22/22, including "every stated author is
    on its article".
  - Each document's declared authors read "Morgan Stanley", and its history carries the
    statement.
  - A repeat as "morgan stanley" was refused: "already credits".
- **Pins:** 10 tests in `tests/test_theme_intelligence_author_statement.py`.
  - The statement clears QA on the upload's run and records who and why on the article, the
    document (read back through `Declared.recorded`) and the issue. No thesis version or event
    moves.
  - Each refusal writes nothing.
  - A re-read (a second version of an unsigned page) keeps the stated author.
  - The run adds no desk week and joins the scan's.
  - QA fails a statement whose article is missing, or does not carry it.
  - An unpushed author run makes a pull refuse; once pushed, it crosses.
- **Mutation:** 11 mutants, all killed. One first survived — QA passing any statement on an
  existing article — and got its pin.
- **Suite:** see the PR.

**BOUNDARY.**
- Registry `theme-intelligence-state` 9939047e, imported on 2026-10-22 (UTC) with this branch
  (base main 6535e727).
- "3 of 9" counts the registry's document records (the uploads) whose article's author status
  is UNKNOWN.
- The QA results are the author check on the two named runs.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0. An author stated in error stays in the record (the article's authors are upserted, and
  the document history and the issue keep the statement). Correcting one is a later statement,
  not a deletion.
- **A card's sealed source row is not rewritten.** "author UNKNOWN" stays on the versions that
  recorded it, which is what was true when they were written.
- **OPEN, the operator's:** stating the three articles' author on the registry of record (the
  name, and who states it).
