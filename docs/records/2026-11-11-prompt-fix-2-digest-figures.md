---
id: 2026-11-11-prompt-fix-2-digest-figures
status: shipped
date: 2026-11-11
prs: [1019]
supersedes:
superseded-by:
---

# Prompt-fix 2: every figure the synthesis is handed carries its sign, unit and period from the structured value — no change prints as "+0%", CIQ's 0.0 beside a differing actual and estimate reads "n/a", the digests print their units, stated changes, periods and signed structured values; in code, no committed page moves until it is re-read or re-assembled

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
   row reads 0.0 too, so the 0% comes from a difference rounded to the cent) and PARR's FY2014,
   FY2015, FY2016, FY2020, FY2021, FY2024 (FY2014: actual −1.44 against estimate −1.87; FY2015:
   −1.06 against 0.65). Each printed "+0%", a met estimate the rows contradict. Now "n/a",
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
   states it (or "period not stated") and an anchored row its signed `value_num` in its unit
   ("[structured: -1.9%]"). Transcript rows are unchanged: their checked figures reach the prompt
   through `prompt_driver_value` (#1006).

**WHY.** A synthesis that is handed "+0%" for a surprise CIQ never computed, or "1.9%" for a fall,
can only misread it; fix 2 is the input half of the 644-claim diagnosis's SIGN, UNIT and PERIOD
classes. The output half (the claim trace) is A's driver-facts stream.

**HOW VERIFIED.** All at $0.
- **Fail first:** the 19 nodes of `tests/test_fix2_digest_figures.py` fail with main's
  `ciq_sheets.py` and `synthesis.py` in this tree, and pass here.
- **The CIQ rows themselves:** the surprise fixture (`tests/fixtures/ciq_surprise_listings.json`)
  now keeps each surprise row's Actual and Estimate rows, regenerated from the same exports (sha256
  checked against the fixture's `_about` before the run; every previously kept row unchanged). The
  pins read PARR's, NFLX's and GOOGL's real rows through the real `CiqBundle`.
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
  lines the `primary_source` and `operating_drivers` sections, not `facts`.
- **The committed pages wait.** The three committed-page equality pins (PARR, GOOGL, NFLX in
  `tests/test_surprise_listing_block.py`) are strict expected failures until each page's $0 re-read
  (`vinci dossier ciq-reread --field surprise_history`) in A's combined pass; the growth cells and
  digests move on re-assembly.

**NOT DONE.**
- **A reconciliation's unit**: `ReconciliationValue` has no unit field (its comment: "$M (or
  $/share for EPS)"; a gross-margin reconciliation prints "34.0"). Adding one edits `schemas.py` and
  `release_parse.py`, both on A's unmerged `claude/fixreq2-e2-remainder`.
- **Found, not fixed (hold scope):** the peer-gap line (`ciq_sheets`, "… vs peer median … ({gap:+.0%})")
  and the GAAP-EPS momentum flag text (`synthesis`, `{g:+.0%}`) still print a small change as
  "+0%"; neither was in the five.
