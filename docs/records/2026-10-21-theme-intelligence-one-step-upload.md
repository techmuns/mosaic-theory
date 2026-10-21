---
id: 2026-10-21-theme-intelligence-one-step-upload
status: recorded
date: 2026-10-21
prs: []
supersedes:
superseded-by:
---

# Theme intelligence: one step for a weekly upload — nothing paid that the stated budget does not cover, nothing pushed that did not check out

**WHAT.** Follow-up A of `docs/records/2026-10-13-theme-intelligence-research-desk.md`, built at
the operator's direction ("yes, start B and A", 2026-10-21).

`python -m vinci.theme_intelligence upload --remote R --path F --source S --budget USD
[--llm-permitted] [--author …] [--same-as | --duplicate-of | --as-new] [--dry-run]`
(`upload.py`) runs six steps. Any refusal stops it, says why, and pushes nothing.

1. **Pull, cache-only** (`state.pull`).
   - A local document the branch lacks is replayed from this machine's cache only.
   - The upload STOPS if the pull leaves a document unreplayed, or if a replay skipped a
     completeness pass or a card review — the steps a paid replay would run and bill.
2. **Preflight — no model call, nothing written:**
   - the channel is active and the file is readable;
   - **author:** the document names its author(s), or `--author` states them. QA requires an
     author, so this is asked before paying (see WHY);
   - **identity:** the same file or the same text already held means nothing to import; an
     uncertain match means the operator decides with `--same-as` / `--duplicate-of` /
     `--as-new`;
   - **licence:** stated, or the channel permits it;
   - **cost:** the estimate's HIGH end must fit the required `--budget`.
3. **Import** through the shared pipeline. `--budget` is both the run's limit and the document's.
4. **QA:** every run the push carries (the import, any replay) is rendered and re-checked. An
   integrity failure stops the push.
5. **Ledger:** every paid call held before is unchanged, and every new one is the import's,
   priced, summing to the run's cost and within budget.
6. **Push,** fast-forward only, and only when the upload carries a run.
   - A pull alone re-mints the registry's migration stamps (`meta`). Pushing that would commit
     noise; found while building this.
   - `state.pull` now reports the runs it holds that the branch lacks (`SyncResult.local_only`),
     and `state.skipped` gives the counts behind the replay's "NOT run" line.

`--dry-run` stops after the preflight and needs no model client. `docs/theme_intelligence.md` is
updated.

**WHY.**
- An upload was four commands run by hand, and any of them could pay implicitly.
- On 2026-10-21 a `--cache-only` rehearsal printed "$0" while it skipped what the paid merge then
  spent $4.81 on (lead (m)).
- Nothing reconciled the spend before a push.
- **The author gate is a real-data finding.** Of the registry's 9 uploads (9939047e):
  - none names an author in its metadata, and none was stated;
  - 6 got one only because the model credited it from the text;
  - **3 stayed without one** (Morgan Stanley's caffeine, ms-industry-5 and hc-industry).
  - QA's integrity check "every analysed article names its author(s)" therefore **FAILS on both
    ingest runs of the 2026-10-21 merge** (R-20261021T101854Z-ingest and
    R-20261021T102637Z-ingest). The weekly job QA's only its own scan, so nobody saw it.
  - Without the gate, an upload like those 3 would pay, then refuse to push for good.

**HOW VERIFIED.**
- **Real data, $0 by construction:**
  - A PRIVATE bare mirror of `theme-intelligence-state` 9939047e (never origin) and a fresh data
    directory.
  - `ANTHROPIC_API_KEY` blanked, so no path could reach a paid model.
  - The original of a held document was copied from the retired pilot's archive.
  - Five paths were run against this branch. The mirror stayed at 9939047e throughout, and the
    local paid ledger stayed at 213 calls / $26.5690:
    1. **The held document (`canada.pdf`, D-46320a8686ac13aa), dry run:** "the same file is on
       the registry … nothing to import".
    2. **The same, for real:** "nothing to import", QA "no run to check", ledger "213 earlier
       paid call(s) unchanged; 0 new", push "nothing to push". Exit 0.
    3. **A new (synthetic) document at `--budget 0.01`:** refused at the preflight — "estimated
       $1–$7 … Run again with --budget 7". Exit 1.
    4. **The same with no licence stated:** refused — "not stated for this file, and the
       channel's policy is 'unknown' — nothing written". Exit 1.
    - Paths 3–5 state `--author`; the synthetic report names none.
    5. **Its dry run:** identity NEW, licence stated, cost $1–$7 against $50, "nothing imported,
       nothing pushed".
  - The paid path was NOT run on real data: paying for a document is the operator's call.
- **The paid path, offline** — 21 tests in `tests/test_theme_intelligence_upload.py`.
  - **The setup:** a local bare repository stands in for GitHub. A fake model answers through
    the REAL spend guard and the REAL content-addressed cache, so its paid calls land in the real
    ledger (fake money) and a later cache-only replay is genuine.
  - **What the tests cover:**
    - the six steps end to end, the scheduled side then holding the upload and only its paid
      calls;
    - the same file, and the same text in another file: nothing to import, nothing pushed;
    - each preflight refusal (budget, licence unstated or refused, unknown channel, unknown
      `--same-as`, a non-positive budget, no author) — nothing written, paid or pushed;
    - an uncertain identity is refused;
    - a dry run, with and without a client;
    - an unreplayable local document stops the pull;
    - a replay that skipped a card review stops the pull;
    - a branch that moved during the upload refuses the push, and the re-run carries the import
      at $0, its paid calls crossing once, unchanged;
    - an integrity failure from QA stops the push, keeps the paid import locally, and never
      counts open research as a failure;
    - a paid call outside the import stops the push;
    - every ledger refusal.
  - **Two real findings while building:**
    - **No author.** The synthetic report names none, and "every analysed article names its
      author(s)" is an integrity check. The first build paid and then refused to push it.
      The real registry showed the same shape on 3 of its 9 uploads, so the check now runs at
      the preflight, before paying.
    - **The test's replay pipeline ran with reviews OFF**, which made a cached review look
      skipped. Fixed in the test, so the pipelines are built as the CLI builds them.
- **Mutation:** 18 mutants, all killed. They cover each preflight gate (the author gate
  included), both pull stops, the dry run, the QA stop, each ledger rule, the no-op push, the
  pull's `local_only`, and a refused push reported as pushed.
- **Suite:** see the PR.

**BOUNDARY.** Registry `theme-intelligence-state` 9939047e on 2026-10-21, mirrored privately and
pulled into a fresh data directory with this branch (base main c5b3f3c2). The paid ledger counts
every paid model call the registry holds: 213 calls, $26.5690. The estimate is
`ingest.estimate_cost` at list price, for the synthetic Morgan Stanley fixture.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0 to build and verify. The command never pays more than `--budget`.
- **A re-run after a refused push is $0 only when every answer its replay needs is cached.** If
  the branch's new runs changed a card it reviews, step 1 stops it before anything is paid, and a
  paid replay (`state pull`) is the operator's call.
- **An uncertain identity is always refused**, never guessed. The operator decides with
  `--same-as` / `--duplicate-of` / `--as-new`.
- **The author gate asks for `--author` on every upload whose metadata names none.** On the
  registry that was all 9, including the 6 the model would have credited from the text. That is
  the price of never paying for an import QA will refuse.
- **OPEN, the operator's call:** the 3 analysed uploads with no author keep QA's integrity check
  failing on both merge runs.
  - A $0 path to state an analysed article's author was not found. Searched: `ingest-file
    --release` (HELD / REVIEW only), `--reread` (re-analyses only a changed reading), the
    pipeline's text credit (`_with_text_authors`), and `git log -S authors_status`.
