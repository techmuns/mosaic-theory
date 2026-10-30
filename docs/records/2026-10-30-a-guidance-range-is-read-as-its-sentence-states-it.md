---
id: 2026-10-30-a-guidance-range-is-read-as-its-sentence-states-it
status: shipped
date: 2026-10-30
prs: [869]
supersedes:
superseded-by:
---

# A guidance range is read as its sentence states it — its scale, its line, its standing, its unit and its partner range; no committed value moves (audit E2-D1, D2, D7, D8, D13; Phase 2 batch B1)

**WHAT.** Five changes to `vinci/edgar/release_parse._guidance`. `parse_release`'s signature is
unchanged.
- **SCALE (E2-D1).** `_GUIDE_RANGE` now captures `thousand`/`K` and each side's `$`
  (`_RANGE_BODY`). `_admit_range` refuses two kinds of `$M` range, each with a
  `GUIDANCE_REFUSAL_PREFIX` note:
  - a range stated in thousands;
  - a range that states no scale at all ("$500,000 to $550,000", "$80 to $100").

  Both used to be stored as `$M`: a 1000x overstatement, or a guess.
- **LINE (E2-D2).** A revenue or net-sales guide is checked with the actuals' lead-word allowlist
  (`_sub_line`, from `_revenue_lead` and `_REVENUE_LEAD_OK`, plus "year-over-year", which
  qualifies a growth rate rather than the line). A sub-line ("subscription revenue", "North
  America revenue") is refused aloud instead of being stored as company revenue. The check runs
  in all four guidance loops (level, growth rate and change), after the one-range-per-scope gate.
- **STANDING (E2-D7).** `_superseded` finds a range whose own clause states the prior outlook
  ("Previously, the Company expected…", "compared to its prior outlook of…"), with no current
  statement after it ("now", a present-tense forward verb, "updating", "raises"…) and no
  "reaffirm". Such a range is skipped before it can take the metric's slot, so the range that
  replaces it is the one read. The skip leaves a machine-tier note, "Superseded guidance not read
  — …". It is not a refusal: a prior outlook is not guidance.
- **UNIT (E2-D8).** A gross margin stated in dollars (a `$`, or a scale word, and no `%`) is
  refused aloud. It is gross profit, not the rate the metric holds. Before, it was stored as
  1.2–1.3 %.
- **PARTNER (E2-D13).** `_CONTINUED` reads a second range that "and" joins to the first ("$250
  million to $260 million in the third quarter and $1.00 billion to $1.10 billion for the full
  year 2026"). `_paired_range` gives each range only the period stated right beside it
  (`_own_period`, a bare "Q3" included). So, in reverse order, the full-year range cannot take
  its partner's quarter. The second range's quote starts at the metric, so the 200-character cap
  never ends it before its own figures.
  A second range with no period of its own, or one paired by "respectively", is refused aloud.
  Before, it was dropped with no note.
- **`EXTRACTION_VERSIONS` row `2026-10-30.E2-guidance`**, in both twins. The drift pins are
  repinned.
- **One existing pin changed.** `tests/test_guidance_unit_suffix.py::
  test_a_following_word_is_not_eaten_as_a_unit` stored "$2.4 to $2.5 based on current rates" as
  $2.4–2.5M. That is G3's shape, which D1 refuses. The pin now asserts the refusal. Its real
  invariant (the "b" of "based" is never billions) still holds.

**WHY.** These are root-cause classes RC3, RC4, RC7 and RC8 of audit E2. In each case the stated
number was stored as something it is not:
- a scale nobody stated (RC8);
- a metric matched as a substring (RC4);
- a first match winning over a later supersession (RC3);
- a unit taken from the metric's name (RC8);
- a vocabulary that read one range per sentence, so the second was lost (RC7).

None of the five reaches a committed page today, and none is on the decision path. Each is
closed behind its audit probe.

**HOW VERIFIED.**
- **Failing first.** The 22 tests of `tests/test_guidance_ranges_as_stated.py` were copied into a
  detached worktree of main `9503c4fa`. There, 13 fail (one or more per defect: G1–G5, G11, G13,
  the D8 inline case, the reversed G13, and review round 0's four: the growth-rate and change
  loops, a bare "in Q3", a long lead-in's quote, "maintenance") and the 9 negative pins pass. On
  this branch all 22 pass. Seven negative pins quote filed sentences verbatim (Amazon, Verra Mobility, nCino, EPAM,
  Simply Good, Artivion, Vital Farms, BellRing). The "reaffirmed or now" pin is constructed, and
  the percent gross-margin pin pairs a constructed level with Simply Good's filed change.
- **The real run.** A read-only, offline replay from the primary checkout's SEC cache, run on
  main's code and on this branch's code, compared field by field (guidance, actuals, one-offs,
  qa_flags):
  - **The 13 pages in the rebuild's scope:** 54 cited releases, 53 replayed. No EX-99.1
    resolves from the cache for LLY's 2026-10-29 8-K. Main's actuals equal the committed actuals
    on all 53.
    **0 field differences.**
  - **26 of the 27 committed pages:** 113 exhibits. **0 field differences.**
- **Corpus before synthetic: each check on real text, ignoring the `seen` slot.** The population
  is 127 EX-99 documents: the 113 above plus 14 more cached EX-99 found by filename. They hold
  248 guidance-pattern matches.
  - **D2 fires 10 times,** on every one of nCino's "Subscription revenues between …" bullets
    (five releases, a quarter list and a year list each). Each sits after its "Total revenues"
    bullet, so the slot already holds the total and nothing stored moves. Before, the same range
    alone under its header was stored as nCino's revenue; a pin covers that case.
  - **D13 matches 1 sentence,** BellRing's "net sales and Adjusted EBITDA* … between
    $2.41-$2.49 billion and $425-$455 million, respectively". The existing two-metric refusal
    already covers it, and it adds no second note.
  - **D1, D7 and D8 match 0** of the 248.
  - **D7's prior-outlook vocabulary does find real prior statements.** Over the 127 documents it
    finds 20 markers with an amount after them in their clause. Each was read in context:
    - 18 sit at a prior range or an unrelated amount, for example Artivion's "previous range of
      $486 to $504 million", Target's "prior guidance of $7.50 to $8.50" and Verra Mobility's
      "up from a prior range of $925 million to $935 million";
    - 2 are current statements: Netflix's "consistent with our prior forecast: we are narrowing
      our revenue forecast…" and "…we currently expect".

    All 20 are classified correctly. None of the 18 prior ranges is preceded by a metric word, so
    none was ever a guidance match. That is why D7 changes nothing live.
- **Gates.** ruff, `mypy --strict vinci`, `node --check frontend/views/shared/dossier.js`, and the
  full offline suite (`pytest -m "not network"`). The PR body carries the counts.

**BOUNDARY.**
- **Commit.** Measured 2026-10-30, main `9503c4fa` against this branch.
- **Pages.** 27 committed pages under `data/dossiers/`. One is held out under a standing operator
  constraint and was not opened or replayed, and its issuer's filings were excluded from the
  cache scan by CIK.
  - The 13 pages in the rebuild's scope: AMZN, CNXC, GOOGL, LLY, NFLX, NKE, ORKA, PARR, ROST,
    SMPL, TJX, UBER and V.
  - The other 13: AORT, BRBR, EPAM, FUBO, IT, MVST, NCNO, TECX, TGT, VITL, VRRM, WERN and WLK.
- **Releases.** One EX-99.1 exhibit per cited 8-K.
  - The 13 pages: 54 cited, 53 cached.
  - All 26: 114 cited, 113 cached.
- **Guides.** On the 13 pages, the committed pages carry 56 numeric guides. Main's code parses 65
  from the 53 exhibits; the difference is STATE row 30's relabels, which wait for re-assembly.
  The 13 pages carry 49 actual rows.
- **Probe population.** 127 documents and 248 guidance-pattern matches: `_GUIDE_RANGE`,
  `_GUIDE_PCT` and the three change patterns, each match counted once per pattern.
- **Cache.** The primary checkout's `data/cache/sec`, read-only, with no network.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Thousands are refused, not scaled.** This is the brief's specification. Scaling would be
  defensible, because the scale is stated, but a thousands guide beside a page of $M guides is
  implausible enough to want a reader. Falsifier: a filer that really guides in thousands.
- **A $M range whose scale is stated outside the range is refused aloud.** For example, a table
  headed "(in millions)" over "$80 to $100". No such range exists in the 248 matches. Falsifier:
  a refusal note on a real outlook table.
- **A sub-line shadowed by its own total is still skipped without a note** (nCino ×10), as it was
  before. The check runs after the one-range-per-scope gate so that pages' flags do not churn. The
  total is what the page carries.
- **D7 is a vocabulary.** A prior range with no marker in its own clause (for example a
  "Prior | Updated" table column) is not seen as prior. In the corpus, such tables (Eli Lilly's)
  carry no introducer, so `_GUIDE_RANGE` never matches them. Falsifier: a stored guide whose
  verbatim is a prior range.
- **Not addressed.** The audit's probe G12, "adjusted EBITDA of 20% to 22% of revenue", is still
  stored as an adjusted-EBITDA percentage level. It is not in batch B1's list.
