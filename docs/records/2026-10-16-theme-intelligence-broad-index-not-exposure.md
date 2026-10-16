---
id: 2026-10-16-theme-intelligence-broad-index-not-exposure
status: recorded
date: 2026-10-16
prs: []
supersedes:
superseded-by:
---

# Theme intelligence — a whole-market index the source attaches is named on every surface and never counted as the thesis's exposure

**WHAT.** Operator ruling, 2026-10-16: "exclude broad indexes". The code review of #730 found that
an attached S&P 500 counted as a thesis's exposure. A whole market is not an exposure.

- **The test.** `cards.is_broad_market` asks whether an instrument is a whole-market index or a
  fund that tracks one.
  - A whole-market index is one whose membership is set by geography and size alone, never by
    sector or theme.
  - The index is recognised by its WHOLE normalised name in `BROAD_MARKET_INDICES`.
    - "The S&P 500 Index" and "S&P 500" match.
    - "S&P 500 Software Index" and "S&P 500 Utilities" do not.
  - A fund is recognised by a listed ticker in `BROAD_MARKET_FUNDS` (SPY, VOO, QQQ, IWM, EWZ …).
- **One definition, every path.** `exposure_instruments` leaves them out. The count (F6, the
  exposure condition), the desk, the card, the dashboard and the market panel all read it.
  `broad_market_instruments` returns them, and `CountedExposures.broad` carries them.
- **Named, never dropped.**
  - Card section 05, HTML and Markdown: a new heading, "Broad market indices the source attaches —
    the whole market, not counted as this thesis's exposure".
  - The desk's Who is exposed: "S&P 500 (broad market index — not counted)".
  - The dashboard row: "[broad market index — not counted]".
  - When the whole market is the only instrument, the desk's exposure gate and the card's why-line
    say so: "only a broad market index (S&P 500) — the whole market is not counted as an
    exposure".
- The market panel no longer prices a whole-market index as an exposure row. Its benchmark is
  already SPY.

**DOES THIS SELECT ON FORM?** No.
- It keys on what the instrument holds: a whole market, of one country, a region or the world.
- An index and the fund that wraps it are treated alike (S&P 500 and SPY).
- It is a LIST, so a whole-market index written another way still counts. That is a recall limit,
  not a selection on form. A new spelling is added to the list, never inferred.
- Two classifications are judgement calls the operator may overrule:
  - Nasdaq-100 / QQQ count as broad: membership is set by exchange and size, not by sector.
  - Single-country indices (Ibovespa, IPC, Colcap, BVL, FTSE 100 …) count as broad: each is the
    whole market of one country.

**WHY — and a correction to the review's example.** The finding said TH-A56902FFB6 (J.P. Morgan,
committed fixture) had the S&P 500 as its only counted exposure. It does not. It also counts a
sector, "AI adopters in the S&P 500" (F6 "0 listed · 1 sector · 1 instrument" on main). The real
S&P-only case is TH-5C3B51DF57 in a local registry copy, described below.

**HOW VERIFIED.**
- **Corpus first.** Every attached instrument on the current version of every thesis in every
  local registry copy: 152 registries, 1,083 current versions, 196 attachments, 11 distinct names.
  - Classified broad, 48 attachments: S&P 500 ×32; Ibovespa, IPC, Colcap and BVL ×4 each.
  - Still counted: S&P 500 Utilities ×47, Cboe 3-month implied correlation index ×33, IGV ×27,
    S&P 500 Software Index ×25, Magnificent 7 ×9, S&P 500 AI Usage ×7.
- **Re-grade, main vs this branch.** Copies were re-graded by `run_reassess` ($0: no fetch, no
  model call; listing re-checks off on both sides, so the run is offline and the difference is
  this change alone). The population was the 90 registries whose versions name any of the five,
  plus the J.P. Morgan fixture built fresh: 640 current theses.
  - **18 exposure factors drop one instrument. 0 research actions change.**
  - TH-5C3B51DF57 ("Extreme S&P 500 top-10 correlation …", a market-regime record) goes from
    "0 listed · 0 sector · 1 instrument" to none. It is WATCH · on hold before and after.
  - The Latin America theses: TH-3A53B04C0B (Ibovespa) and TH-F4A90F739D (IPC) are active. Both
    keep version 1 under both codes; their stored F6 predates instrument counting. They count 1
    and 2 sectors, so they stay exposed. The other two (Colcap, BVL) are archived.
- **The live pilot.** No current version attaches a whole-market index; the S&P 500 appears only as
  a comparator on TH-FBDC863613. Nothing changes there.
- **Pins.**
  - `test_a_whole_market_index_is_told_from_a_sector_one`: the 10 observed names (5 broad,
    5 sector) plus two constructed spellings.
  - `test_the_whole_market_is_named_and_never_counted`.
  - `test_a_thesis_whose_only_instrument_is_the_whole_market_counts_no_exposure`: end to end on the
    fixture; the gate and the why-line.
  - `test_every_surface_lists_the_instruments_the_count_takes`, extended: the S&P 500 on the desk,
    the card (HTML and Markdown) and the dashboard row, never among the exposures.
- **Mutation.** 12 mutants, all killed: never broad, prefix match, funds ignored, no
  normalisation, the count keeping broad, `broad` not carried, the card heading, the Markdown
  heading, the desk gate, the desk label, the dashboard, the why-line.
- **Suite.** ruff and `mypy --strict` clean; `pytest -m "not network"`: 5787 passed.
- **Preview.** `docs/theme_intelligence/broad-index-2026-10-16/screenshots/` holds:
  - each page collapsed and with every `<details>` opened;
  - section 05 of the card, expanded.

**ALSO DONE (operator, 2026-10-16: "move the pilot to main").** The pilot checkout moved from
8afbe671 to main 11e77e49.
- The live registry is untouched: schema v5, md5 5fcc240d4b087d2feb1f81e6d6fabc3c.
- It migrates to v7 on its next run or render.
- Proven on a backup copy with main's code: v5 → v7, all 22 tables with every row unchanged, plus
  the new `market_contexts` table.

**ALSO OPEN (found here, not changed).** The Cboe 3-month implied correlation index counts as an
attached instrument exposure: 33 current versions across the copies. It is a volatility statistic,
not an equity holding. Whether it counts is the operator's ruling.

**BOUNDARY.**
- Measured 2026-10-16 on this branch over main 11e77e49.
- Population: the 152 `registry.db` files under the theme-intelligence data folder of the pilot
  worktree, read from backup copies; current versions only.
- "Attachments" = funds, indices and cited baskets in an attaching role (`INSTRUMENT_ROLES`, or a
  cited basket), counted per current version.
- The 90 re-graded registries are those whose stored versions name any of the five as
  `name_as_written`, in any version and any role. That is a superset of the 35 with a current
  attachment; the rest are the check that nothing else moves.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- A whole-market index spelled another way still counts. Falsifier: a corpus survey finding a
  whole-market instrument among the counted ones.
- A market-regime record whose only attachment is the index it measures now reads "no exposure".
  That is the ruling's consequence, and it is said on the gate.
- A country view can no longer pass the exposure gate on its country index alone.
