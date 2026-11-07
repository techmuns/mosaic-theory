---
status: open
date: 2026-11-07
prs: []
supersedes:
superseded-by:
---

# Fix 4a: a missing item is sorted before it is read — our gap, does not apply, the company's normal practice, a change or deviation, or type not determined — and rule 8 lets only a change be raised as a risk; the "trailing-only" ask leaves the prompt. $0; the paid measurement is proposed, not run

**THE RULING.** Operator, 2026-11-07, verbatim: **"Yes, use the test"**. A missing item is sorted
into one of four types:

1. **OUR GAP** — our pipeline did not read it. Never a signal about the company.
2. **DOES NOT APPLY** — e.g. a single-segment filer has no segment profit. Neutral.
3. **THE COMPANY'S NORMAL PRACTICE** — e.g. a filer that has not given annual guidance in any
   release we read. Neutral: an unknown, not a risk.
4. **A CHANGE OR A DEVIATION** — disclosed before and absent now, or something peers disclose that
   this filer does not. Only this type may be raised as a risk, and only with its evidence: what
   was disclosed, where, and when it stopped. It lowers confidence; it is never a bear point by
   itself.

Everything not of type 4 goes to `key_unknowns` as an unknown, with what would resolve it and
when. It is never labelled bearish.

**WHY.** #926's measurement of fix 3a left 47 M-LABEL units in its 30 CAND draws (scorer at
`fc79a7be`); 46 trace to the prompt, nearly all in `key_unknowns`: 27 restate an adjusted forward
or guide as missing, 13 use "trailing-only", 5 say MCK discloses no segment profit, 1 says LLY's
runway is "not assessable". Rule 8 told the model that a missing "segment breakout, cash-runway
visibility, … forward guide, a survival_capacity leg UNKNOWN" is a BEARISH risk; rule 7b's example
and the `bear_points` schema text still asked for the "trailing-only" tag that #923 deleted from
every page with a CIQ forward multiple (STATE row 54, item 2).

## 1. What shipped, by brief item

| item | disposition | what |
|---|---|---|
| (a) the fact layer states each gap's type | **SHIPPED**, change-over-time half only | `vinci/dossier/gaps.py`; `MechanicalLayer.disclosure_gaps` (last key, absent until built) |
| (b) rule 8 rewritten to the test | **SHIPPED** | rule 8 is THE GAP TEST, symmetric ("a disclosure added is a dated fact, never a bull point by itself") |
| (c) the "trailing-only" ask removed | **SHIPPED** | rule 7b's example and the `bear_points` text; a trailing multiple "is read beside the forward (NTM) multiple wherever the page carries one" |
| (d) pins + a lint for rule 8's old wording | **SHIPPED** | `tests/test_gap_test.py`: each type +/−, end to end on pages at the panel's freeze; a real type-3 page (SMPL); **no real type-4 page exists** (§3) |
| (e) a transform + the $0 cross-check | **SHIPPED** | `variants.gap_types` (`FIX_4A`); §4 |
| (f) the measurement | **PROPOSED, not run** | §6 |

## 2. How the type is decided

From statuses, lists, dates and table cells the layer already carries — **never a note or a
display string**. One pin blanks every fact's note on all 28 pages and the gaps do not move. Where
a rule cannot decide, the entry says "type not determined", which rule 8 reads as an unknown. No
rule defaults to type 4.

**Two reads before a company type.** The release parser misses guides companies give: it reads
no guide from any release of MCK, ROST or V, while CIQ records one on their newest release's date.
So "no guide in any release we read" cannot by itself tell our gap from the company's practice.
CIQ's Guidance sheet (`catalyst_path.guidance_bridge_rows`: the latest guide CIQ records per
metric, with its date) is the second read. Types 3 and 4 both need the two reads to agree over a
span CIQ's export reaches (its freshest row's date).

| item | fields | our gap | does not apply | company's normal practice | change or deviation |
|---|---|---|---|---|---|
| segment profit | `concentration.segment_profit`, `segment_ebitda` | CIQ's roster splits revenue 2+ ways and the 10-K XBRL read failed or found <2 segments (a multi-segment filer reports a profit measure per segment, ASC 280-10-50-22) | CIQ reads one segment and the XBRL tags <2 | (segment EBITDA only) the filer's segment measure is another one, stated at `segment_profit` | not built (a recast needs two 10-Ks) |
| the outlook at a gap-down | `drawdown_cause[.anchor.*].revised_guidance` | the release parser read a guide from that 8-K's release, or CIQ records one on its date and the parser read none | the window holds no gap-down 8-K | the ladder below | the ladder below |
| the company-adjusted EBITDA at the gap-down | `valuation.ev_ebitda_adjusted_fwd`, `quality.net_debt_to_ebitda_adjusted` | as above, for an adjusted-EBITDA level guide | (with the outlook) no gap-down 8-K | ladder | ladder |
| the newest release's adjusted-EPS guide | `valuation.adjusted_eps` | CIQ records an EPS guide on the newest release's date, from which the parser read no guide | — | ladder | ladder |
| a current guide | `primary_source.current_guide` | CIQ records a guide on the date of a release the parser read none from | — | ladder | ladder |
| the FCF sign (the runway leg) | `quality.fcf_sign` | the page's annual table states LTM cash flow | — | — | — |
| net debt / EBITDA | `quality.net_debt_to_ebitda` (+ `leverage_survival`) | — | the annual table's LTM EBITDA is not positive | — | — |

**The ladder**, for each guide item:
- **Type 3:** two or more releases were read, none states the guide, and CIQ, reaching the newest,
  records none since the oldest.
- **Type 4:** a release states the guide; every release read since states none; those releases
  span at least 75 days (`FULL_QUARTER`, so a non-results 8-K a month later is no stop); and CIQ,
  reaching the last of them, records none after it. The entry carries what (`disclosed`), where
  (`source_ref`) and when it stopped (`stopped`, `stopped_ref`). The schema refuses a type-4 entry
  without all of them, and any other type that carries them.
- **Otherwise:** type not determined, with the reason.

**Not built, stated:**
- **The peer half of type 4.** The layer carries peers' multiples, never their disclosures.
- **A change in a filing** (a segment recast, a dropped KPI, a late filing). The layer reads one
  10-K's segment instance and holds no KPI history.
- **A release's 8-K item codes**, which `ReleaseExtract` does not store. A non-results 8-K after a
  guided one is told apart only by time.
- **Coverage.** The registry covers the subjects rule 8 named. Rule 8 reads every other UNKNOWN as
  "type not determined" ("every other gap, listed or not").

## 3. Measured at $0 on the 28 pages committed at the panel's freeze (`bcda7ce3`)

96 entries on 28 pages (VRRM carries none):

| item | our gap | does not apply | practice | change | not determined |
|---|--:|--:|--:|--:|--:|
| segment profit (incl. segment EBITDA) | 4 | 13 | 6 | 0 | 2 |
| the outlook at a gap-down | 6 | 19 | 0 | 0 | 0 |
| company-adjusted EBITDA at the gap-down | 3 | (in the outlook's entry) | 2 | 0 | 3 |
| adjusted-EPS guide, newest release | 6 | — | 8 | 0 | 9 |
| a current guide | 8 | — | 0 | 0 | 2 |
| the FCF sign | 2 | — | — | — | 0 |
| net debt / EBITDA | 0 | 2 | — | — | 1 |
| **total** | **29** | **34** | **16** | **0** | **17** |

- **MCK's segment gap reads type 1.** CIQ splits its revenue into 5 lines; the 10-K XBRL read
  failed ("segment contexts exist but no profit measure … is tagged on two or more").
- **A single-segment filer reads type 2:** all 13 (BRBR, BURL, CNXC, FUBO, LLY, MVST, NCNO, NFLX,
  ROST, SMPL, TGT, V, VITL).
- **A real type-3 page: SMPL** (on the panel). None of its six releases read (2025-07-10 to
  2026-10-27) states an adjusted-EPS guide, and CIQ, reaching 2026-10-27, records none since. It
  guides net sales and adjusted EBITDA. The same type on AMZN, AORT, BRBR, FUBO, GOOGL, WERN, WLK.
- **No real type-4 page exists** on the 28.
  - The nearest is FUBO. Its 2026-04-06 release states a Fiscal 2026 adjusted-EBITDA guide, and
    the two releases since (05-06, 08-05) state none. But CIQ records an EBITDA guide dated
    2026-08-05, so FUBO's gap reads ours (the parser missed it), not a withdrawal.
  - MVST's revenue guide is absent after 2026-05-11, but CIQ's export reaches only 2026-03-16, so
    it cannot agree: type not determined.
  - The positive pin moves FUBO's one CIQ EBITDA row to the April release's date, the shape a
    withdrawn guide would leave, on FUBO's otherwise real page.
- **LLY's runway leg reads type 1.** Its FCF-sign read is UNKNOWN ("no OCF/capex"), while its own
  annual table states LTM CFO, capex and FCF. IT is the same.

## 4. The transform and the $0 cross-check

`variants.gap_types` writes `disclosure_gaps` with the ref's own `mechanical.disclosure_gaps`:
- the identity at main (no rule);
- it moves only its own field, and is idempotent;
- its one string read is the committed segments line's count, through one tested helper
  (`segment_count_from_line`, harness only), which refuses anything that is not the lean roster.

The builder reads the roster from the export (`ciq_sheets.segment_count`).

**Builder = transform**, measured at $0 on the frozen pages whose `Financials_Annual` export is on
disk (the primary checkout's `data/manual/ciq`, read only):
- the export rebuilds the page's committed `concentration.segments` and `segment_ebitda` byte for
  byte on 26 of 27 (UBER's is not its page's own; AORT has none on disk);
- on all 27, the builder's count equals the transform's and the gap lists are equal;
- all six panel pages pass.

In CI the same check runs on the six panel pages' own Segments sheets, cut to the cells read
(`tests/fixtures/ciq_segments_eval_panel.json`: 19–36 cells of 403–778 per page). Each cut is proved
by rebuilding its page's committed lines.

<!-- COMPARE -->

## 5. Pins and mutation

`tests/test_gap_test.py`:
- each type +/− end to end on pages at the freeze;
- the evidence legs;
- the no-note pin on all 28 pages;
- the builder's roster against the rendered line;
- the assembly writing the field (LLY's real inputs, `tests/test_asof_cut.py`'s harness);
- the transform's own-field, idempotence and identity;
- **the lint**: rule 8's old wording ("OPACITY-AS-SIGNAL", "is NOT neutral", "BEARISH risk") and
  the ask ("trailing-only", "blind-flag") absent from every book's system prompt and tool schema,
  each entry pinned live;
- the request itself: MCK's typed gaps are the facts' last key, and removing that one value leaves
  the request the untransformed layer sends.

13 of 13 mutants are caught: the wiring removed; each type-4 guard (CIQ's reach, the full
quarter); each type-3 guard (one release, no CIQ); the 1b skip; single-segment → ours;
multi-segment → nothing; the FCF rule; rule 8's old wording; the blind-flag ask; a loose roster
helper; and a rule that reads the segment note.

`tests/test_dossier.py`'s old pin, which asserted "OPACITY-AS-SIGNAL" and "BEARISH risk", now
asserts their absence. That is the ruling's intended reversal.

## 6. The measurement — PROPOSED, not run (the operator approves any paid run and its cap)

<!-- PROPOSAL -->

**BOUNDARY.**
- **Pages:** the 28 committed at `bcda7ce3` (the panel's `freeze_ref`); the panel is v2 (BURL,
  CNXC, LLY, MCK, ROST, SMPL).
- **Code:** this branch.
- **Counts:** entries of `disclosure_gaps` per item and type. The transform path reads the segment
  count from the committed line. The builder path was checked equal on 27 of 28 pages' exports.
- **CIQ root:** the primary checkout's `data/manual/ciq`, read only, 2026-11-07.
- **#926 figures:** its 60 draws (registration `cceba9d9`), units of `units.draw_units`, the scorer
  at `fc79a7be`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The rule's literal reach.** "Everything not of type 4 goes to `key_unknowns`" is implemented as
  written, so a "does not apply" gap is also an unknown. A single-segment filer's segment line can
  then appear in `key_unknowns` with nothing to resolve. Accepted as the ruling's words. It is
  falsified as harmless if the measured draws spend `key_unknowns` lines on type-2 gaps at the
  expense of real unknowns.
- **Refresh paths do not rewrite the field.** Only an assembly writes `disclosure_gaps`. A
  `vinci dossier refresh` transform that rewrites `primary_source` or `drawdown_cause` leaves the
  gaps as built. No page carries the field until it is rebuilt.
- **A type-1 that is really type 3 is possible** where CIQ dates a GAAP-only guide at a release
  (ROST's adjusted-EPS entry). Both types are neutral, so rule 8's behaviour is the same.
