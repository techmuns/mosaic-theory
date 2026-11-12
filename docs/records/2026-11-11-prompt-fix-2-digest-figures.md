---
id: 2026-11-11-prompt-fix-2-digest-figures
status: shipped
date: 2026-11-11
prs: [1019]
supersedes:
superseded-by:
---

# Prompt-fix 2: every figure the synthesis is handed carries its sign, unit and period from the structured value — no change prints as "+0%", CIQ's 0.0 beside a differing actual and estimate reads "n/a", the digests print their units, stated changes, periods and structured values (signed where a change); in code, no committed page moves until it is re-read or re-assembled

**WHAT.** The prompt-fix program's fix 2, handed to fix request 2's streams on #1004 and kept by
S2 when A's driver-facts stream took RG-D1 to RG-D7 and fix 5 (A's 13:14Z comment, operator-
approved). Four places dropped a figure's sign, unit or period:

1. **`{:+.0f}%`** — the five formats A's stream found in `vinci/dossier/ciq_sheets.py` (the annual
   summary's growth cells twice, the quarterly QoQ and YoY rows, the consensus path's net move) and
   the surprise line's `{:+.0%}` printed any change under half a percent as "+0%" or "-0%", a
   change read as none. All go through one formatter, `ciq_sheets.signed_pct`: whole percents,
   the first significant decimal under half a percent, "0%" only for an exact zero; judged on the
   printed whole, so −0.5 (Python rounds .5 to even) is "-0.5%", not "-0%".
2. **CIQ's 0.0 surprise beside an Actual and an Estimate of its own that differ** (the "+0%"
   placeholders): NFLX's GAAP EPS FY2004–FY2013 (sub-cent split-adjusted EPS; CIQ's "Difference"
   row reads 0.0 too, so the 0% comes from a difference rounded to the cent), FY2016 (0.043
   against 0.04042) and FY2024 (1.983 against 1.97564); GOOGL's FY2005 (0.1255 against 0.13215, a
   miss); and PARR's FY2014, FY2015, FY2016, FY2020, FY2021, FY2024 (FY2014: actual −1.44 against
   estimate −1.87; FY2015: −1.06 against 0.65). *(Review round 1 corrected this list: the first
   draft named NFLX FY2004–FY2013 only and omitted GOOGL; the pins now hold each set exactly.)* Each printed "+0%", a met estimate the rows contradict. Now "n/a",
   explained once inside the line's trailing note, the only place the web's `parseSeries` reads
   as a note; nothing is computed in CIQ's place. A 0.0 whose actual equals its estimate stays
   "0%".
3. **The primary-source digest**: a level guide printed no unit ("guidance (adjusted eps 2026):
   10.97–11.09" in $/share, "(adjusted operating income 2026): 1206.0–1216.0" in $M), an event
   impact no $M, and a reconciliation not the change its release states. Now `GuidanceItem.unit`,
   "$M" (the `EventImpact` schema's unit) and `ReconciliationValue.change`.
4. **The operating-drivers digest** printed an anchored row's verbatim value and never its
   structured one, and no row its period: SMPL's "general and administrative expenses: $0.8
   million, or 1.9%" is a FALL (`value_num` −1.9). Each row now prints its period as its source
   states it (or "period not stated") and an anchored row its `value_num` in its unit
   ("[structured: -1.9%]"). Only a percent row is a signed change and prints its sign; a
   release KPI row stores a level and prints none ("[structured: 5500 vehicles]", Lucid's 8-K
   0001104659-26-042847 — review round 1: the first head printed "+5500", a count read as a
   rise). Transcript rows are unchanged: their checked figures reach the prompt through
   `prompt_driver_value` (#1006).

**WHY.** A synthesis that is handed "+0%" for a surprise CIQ never computed, or "1.9%" for a fall,
can only misread it; fix 2 is the input half of the 644-claim diagnosis's SIGN, UNIT and PERIOD
classes. The output half (the claim trace) is A's driver-facts stream.

**HOW VERIFIED.** All at $0.
- **Fail first:** the tests of `tests/test_fix2_digest_figures.py` fail with main's
  `ciq_sheets.py` and `synthesis.py`, and pass here (each review round re-ran it, in a throwaway
  worktree).
- **The growth cells, end to end** (review round 2): `financial_summary_annual` and
  `financial_summary_quarterly` print a sub-half-percent change to its digit — CNXC's real Q3-26
  QoQ ("-0.4%", frozen in `tests/fixtures/ciq_ltm_quarters.json`) and the committed synthetic
  bundle with one revenue cell set 0.3% (annual) or −0.05% (YoY) off its base. Each pin fails with
  main's code, and each kills the mutant that rewrites its cell as `f"{round(x):+d}%"`, which the
  format lint alone let through.
- **The CIQ rows themselves:** the surprise fixture (`tests/fixtures/ciq_surprise_listings.json`)
  keeps the Actual and Estimate rows `surprise_history` itself reads, regenerated from the same
  exports (sha256 checked against the fixture's `_about` before each run; every other row equal to
  the fixture before this PR). The builder runs the reader and cuts by its own walk
  (`ciq_sheets._surprise_basis_rows`), so the selected listing's fiscal-year block is all it keeps:
  4 rows per name, and in each only the columns where the surprise row states a number. Review
  round 2 cut the first version, which kept 46 such rows (PARR 18, GOOGL 20, NFLX 8) of which 12
  are read; non-empty cells now 571 (PARR), 783 (GOOGL) and 395 (NFLX), against 509, 691 and 299
  before this PR and 1,265, 1,841 and 795 at the first cut.
  `::test_the_fixture_holds_only_the_actual_and_estimate_cells_the_reader_reads` holds the rule.
  The pins read PARR's, NFLX's and GOOGL's real rows through the real `CiqBundle`.
- **The $0 panel compare** (`python -m vinci.evals compare --base origin/main --cand <branch>`,
  after merging main at `91817458`): all six panel requests move, in the USER message only — the
  primary-source digest (BURL +35, CNXC +66, LLY +3, SMPL +60 characters) and the drivers digest
  (+777 to +2,875); per request +0.19% (BURL) to +0.45% (LLY). From the captures, `system`,
  `tools`, `tool_choice`, `model`, `max_tokens` and `cache_control` are byte-identical on all six;
  every USER line other than the digest lines this record names is identical, and each page has
  as many driver rows at both refs.
- **The facts half** (the surprise line and the growth cells) does not reach the frozen panel
  replay, which reads each page's committed layer; it reaches a page when that page is re-read or
  re-assembled.

**BOUNDARY.** Panel v2 (BURL, CNXC, LLY, MCK, ROST, SMPL) at its freeze `bcda7ce3`; base main
`91817458`, head this branch; sizes are characters of the USER message as captured by
`vinci.evals.replay.capture_at`; the CIQ exports are the three named in the fixture's `_about`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The paid panel check: none proposed.** SYSTEM and the tool schema are byte-identical; the move
  prints values the layer already holds, with no instruction text. The operator's ruling recorded
  in `docs/records/2026-11-11-fix2-bookkeeping-batch-3.md` (item 2): FACTS-only request moves need
  no paid panel by default ("Not needed; #953 is the test (Recommended)"), with #953's
  retrospective run as its falsifier. Stated for the operator to overrule: the harness names these
  lines the `primary_source` and `operating_drivers` sections, not `facts`. Two more facts for that
  call (review round 2): `vinci/dossier/synthesis.py` is in `compare.SCORER_FILES`, so the scorer
  fingerprint changes and `score_run` refuses to score a registration made before this merges at
  any other code; and M-ECHO's instruction set (`metrics.EchoIndex.of`, every USER section but the
  facts and transcripts) moves on identical draws — on SMPL's frozen request from 3,223 to 3,337
  shingles (+292 / −178), so a no-worsening check would see M-ECHO move without any draw
  changing.
- **The committed pages wait.** The three committed-page equality pins (PARR, GOOGL, NFLX in
  `tests/test_surprise_listing_block.py`) are strict expected failures until each page's $0 re-read
  (`vinci dossier ciq-reread --field surprise_history`) in A's combined pass; the growth cells and
  digests move on re-assembly.

**ACCEPTED IN REVIEW ROUND 1 (stated, not fixed).**
- **A near-tie reads "n/a" too.** NFLX FY2024's actual 1.983 against its estimate 1.97564 is a
  true surprise of about +0.37%, and the page printed "+0%", nearly right; it now prints "n/a".
  The rule states what CIQ's rows show and computes nothing in CIQ's place; a tolerance that would
  keep "+0%" for a near-tie is a threshold, and none is set here.
- **A release KPI's period is the year `_period_near` reads.** Lucid's "during the quarter ended
  March 31, 2025, the Company produced 2,212 vehicles" carries period "2025", and the digest now
  prints it: a quarter's count labelled with its year. It is the extractor's field
  (`vinci/edgar/release_parse.py`), outside this fix; no committed page carries a KPI row.

**ACCEPTED IN REVIEW ROUND 2 (stated, not fixed).**
- **The annual summary's ESTIMATE-column growth cell is held by the format lint only.** Neither
  committed fixture states a forward estimate (the synthetic bundle and the frozen LTM rows have
  no FY-estimate column), so no end-to-end pin reaches it; its mutant survives the suite.
- **A 0.0 with its Actual or its Estimate missing stays "0%".** Nothing contradicts CIQ there, so
  the page prints what CIQ states; "n/a" would withhold a stated value on no evidence. Pinned both
  ways (`::test_a_zero_with_one_side_missing_stays_ciqs_zero`); no live cell has this shape.
- **`_range(None, x)` prints "None–x"** — unreachable: every guide constructor sets a number where
  `qualitative` is False (the level path compares `low > high`), and of the 124 committed guides
  `low` is None only on the 3 qualitative ones, which the digest prints before `_range`.
- **`ciq_sheets` line 1205's `{:+.1%}`** (a quarter's YoY in the LTM note) can print "+0.0%"; not
  among the five, found not fixed.
- **"(period not stated)" beside a metric that names its quarter** ("Quest household penetration
  Q4"): the digest prints the row's `period` field as stored, and reading a period out of the
  metric's label would be a parse of a rendered string.

**NOT DONE.**
- **A reconciliation's unit**: `ReconciliationValue` has no unit field (its comment: "$M (or
  $/share for EPS)"; a gross-margin reconciliation prints "34.0"). Adding one edits `schemas.py` and
  `release_parse.py`, both on A's unmerged `claude/fixreq2-e2-remainder`.
- **Found, not fixed (hold scope):** the peer-gap line (`ciq_sheets`, "… vs peer median … ({gap:+.0%})")
  and the GAAP-EPS momentum flag text (`synthesis`, `{g:+.0%}`) still print a small change as
  "+0%"; neither was in the five.
