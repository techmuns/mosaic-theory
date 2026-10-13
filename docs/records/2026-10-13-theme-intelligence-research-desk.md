---
id: 2026-10-13-theme-intelligence-research-desk
status: recorded
date: 2026-10-13
prs: [703]
supersedes:
superseded-by:
---

# Theme intelligence — the approved research desk is built: six screens and a thesis reading page, read from the registry; an engine issue-id collision found and fixed

**WHAT.**
- **The research desk** (`vinci/theme_intelligence/desk.py`, written by `write_run_outputs` beside
  the existing outputs). It reads stored records only: versions, priority factors, events,
  contributions, completeness ledgers, documents, candidates and health checks. It writes nothing
  to the registry and makes no model call. The pages:
  - **This Week** (`index.html`): a summary of the articles read, theses created or changed, and
    items needing attention; the week's thesis changes grouped by research area (new, upgraded,
    downgraded, challenged, new evidence); what each article produced, including zero-thesis,
    partial, held, failed and queued cases.
  - **Themes**: every thesis, active and archived, grouped by area, with search, filters and sort.
    Areas use short names (`AREA_NAME`); taxonomy keys and thesis identities are unchanged.
  - **Articles**: one page per week with a week selector. Read in full, partial, queued, failed,
    blocked, held and duplicate items are told apart, each with what it produced, its open
    completeness items and its follow-up.
  - **Review**: every unresolved finding on every ACTIVE thesis, whatever week raised it. Order:
    decision-affecting first, then Research Now, then the oldest. Each shows its age (from the
    version whose review first made it), the thesis, the review's words and a link to the exact
    card line. Resolved and historical findings are kept below. Read-only: no resolution state.
  - **Uploads**: every item to supply or clear, registry-wide and never dismissed by age —
    full-report requests, blocked articles, manual-first and blocked sources, held and
    match-uncertain documents, visual checks, rejected and completed imports. Each shows its
    publisher, source id, publication date, age, first-seen date and the EXISTING command.
  - **Sources**: health now, the stored health-check history only, freshness, articles analysed
    in the last four weeks, and the permitted intake mode. Automatic and manual-first coverage are
    in separate tables.
  - **Thesis reading page** (`theses/<id>.html`): answers the thesis, what changed, the strongest
    figures (with unit, period, observed or forecast, date), how the mechanism reaches
    fundamentals, why this action, what could prove it wrong, and what to investigate next.
    Exposures, related theses, open findings, the evidence, the history and the sources follow.
    The full nine-section card stays at `cards/<id>.html`, linked as Full record and section by
    section. No line is printed twice.
- **The Nomura horizon presentation.** The source's horizon LABEL and the near-term factor of
  record are now two statements, never two verdicts on one test.
  - The near-term condition is stated once, ✓/✗, from the factor of record.
  - The framing is printed as "a description of the thesis, not a test".
  - The factor's own cited claims are re-dated today with `timewindow.timing_of`, each with the
    basis of its date.
  - If the re-dated claims give another value, the page shows **Review required** and a timing
    finding joins Review. The research action of record stands until a reassessment.
  - Nomura `TH-2FFD9B58A8` has no such conflict: 5 measured claims dated by the article's
    publication date (no measurement date stated), all within the last quarter.
- **The engine fix (separate commit).** `Engine._issue` now hashes its DETAIL into the issue id,
  as `verify._issue` does. Two articles of one run that split one key into different products
  shared an issue id, and the append-only store refused the second article
  (`StoreIntegrityError`). Found by the synthetic stress registry.
- **`build_dashboard(…, runs=)`.** The desk passes its week explicitly. A registry with no weekly
  scan yet shows its manual runs as a week in progress. The default is unchanged.
- **Not built, documented as follow-up requirements:**
  - **A. A safe one-step weekly upload command.** A cache-only state pull; identity and licence
    checks; a cost preflight; an explicitly budgeted import; QA; ledger reconciliation; a
    fast-forward-only push. No implicit paid replay.
  - **B. Append-only review resolution.** Version-specific findings; reviewer, time, reason, and a
    verified correction or dismissal; full history kept. Accepting a warning never makes
    unsupported evidence valid.
- **OPEN — found, not fixed (a research-correctness gap that predates the desk).** A new thesis
  version written WITHOUT the card review (`--no-review`, review budget exhausted, or no client
  and no cache — the run records `REVIEW_NOT_RUN`) does not carry the previous version's open
  findings, even on an unchanged line. The card then reads "no unresolved review findings", and so
  does the desk, which reads the card's own findings (`report.line_findings`). Re-grades already
  carry findings (`Engine.reassess`); the article path does not.
- **Observed, not changed:** a card's source row links an uploaded document's `urn:document:…`
  identifier as if it were a web page (`cards.render_html`, section 09). The desk prints it as
  text.

**WHY.** The approved information architecture is the analyst's weekly loop: what came in, what
changed, what needs a decision, what to supply. The old single weekly page covered one week, and
its review queue showed only that week's theses, so a finding raised earlier went out of view.
The Nomura card printed "Horizon: Longer term" beside a met near-term condition with no account
of why, which read as a contradiction.

**HOW VERIFIED.**
- **The real pilot** — a scratch COPY of `pilot-2026-10-12/registry.db`; the original was never
  opened by the build. Its latest run renders 10 desk pages: 5 articles read (3 in full, 2 preview
  only), 4 theses created, 8 open findings on 3 active theses (5 decision-affecting), 7 upload
  items.
  - 0 broken links of 635 local links; 0 engine ids or codes in the default view.
  - Every reading page reaches all nine card sections.
  - No horizontal overflow at 1440 or 390 px on all 10 pages (headless Brave).
- **The synthetic stress registries** (`tests/theme_intelligence_stress.py`; through the REAL
  engine; every article on the reserved `.test` domain and titled "[SYNTHETIC STRESS TEST]"; never
  the real registry):
  - **6 weeks:** 110 articles, 62 theses, 73 desk pages. 0 broken of 6,247 links, 0 default-view
    ids or codes.
  - **12 weeks:** 229 articles, 111 theses (96 active, 12 Research Now), 128 desk pages, rendered
    in ~1.2 s. Review: 38 open findings, 27 of them open four weeks or more. Uploads: 58 items.
    0 broken of 14,622 links, 0 default-view ids or codes. No page overflow at 1440 or 390 px on
    the 8 pages measured.
- **Tests** in `tests/test_theme_intelligence_desk.py` (end to end on the stress registries and on
  hypothetical articles built from the real extraction types):
  - scale; every capped list says "showing N of M" and keeps every row;
  - every open finding of every active thesis on Review, including earlier weeks, in order;
  - review links open the exact flagged line;
  - a preview never reads as full;
  - all links and anchors resolve;
  - the default view has no ids or codes while the audit view keeps them;
  - nine sections reachable; older uploads stay listed; no line printed twice;
  - the registry unchanged and no model call;
  - the near-term reading told apart from the framing (positive pin), and Review required when
    its claims no longer support it (negative pin);
  - the engine collision (fails on the unfixed engine with `StoreIntegrityError`).
- **Mutants:** 7 of 7 killed — a capped table dropping rows, the timing conflict never raised,
  review reading only this week's theses, a document identifier linked, a preview read as full,
  the near-term condition listed twice, an audit id leaking into the default view.
- **The not-carried finding, probed:** with review on, version 1's line s01.0 was flagged. With
  review off (`REVIEW_NOT_RUN`), version 2 has the same line text and no finding.
- **Gate:** ruff (`vinci tests frontend`), `mypy --strict vinci` and the offline suite — results in
  the PR.

**BOUNDARY.**
- "Real pilot": `data/theme_intelligence/v2/pilot-2026-10-12/registry.db` (unchanged since
  `R-20261012T133456Z-reassess`). Rendered from a copy at that run, 2026-10-13. Its desk week is
  the 12 manual runs of 2026-10-12, with no weekly scan yet: 10 succeeded or partial, 2 failed.
- "Articles read": analysed article versions of the week, by article.
- "Open findings": withheld plus review-flagged lines of each ACTIVE thesis's version as of the
  rendered run (`report.line_findings`), plus timing conflicts (0 in every registry here).
- "Upload items": every non-completed item on the Uploads page, registry-wide.
- Stress counts: the last scan of each synthetic registry (seed 7, ending 2026-10-12), built
  2026-10-13 at this commit's parent plus this change.
- "Links": every relative `href` on the desk pages and the cards they link, resolved to a file
  and an anchor.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0: no model call, no re-run, no record edited. Budget unchanged at $4.3345 of $18.
- **"Decision-affecting" is a display rule, not a priority rule:** a withheld line, a timing
  conflict, or a finding on a line citing a claim the research action counts (F2/F5/F7/F12). It
  orders the queue; it never changes an action.
- **Many sibling links at scale.** The stress registry gives every AI-infrastructure thesis 82
  SIBLING links (same parent node). The reading page folds them under one line; Themes counts only
  direct links.
- **Accepted: the desk mirrors the card's findings.** The OPEN item above therefore applies to
  both until the carry is fixed. Falsifier: a version recording `REVIEW_NOT_RUN` whose unchanged
  line had an open finding on the previous version.
