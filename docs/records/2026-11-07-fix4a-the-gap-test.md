---
status: shipped
date: 2026-11-07
prs: [927]
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
| (d) pins + a lint for rule 8's old wording | **SHIPPED** | `tests/test_gap_test.py`: each type +/−, end to end on pages at the panel's freeze; a real type-3 page (SMPL); **no real type-4 page exists, and no path emits type 4** (§3, §7 F5); rule 8 pinned by sha256 |
| (e) a transform + the $0 cross-check | **SHIPPED** | `variants.gap_types` (`FIX_4A`); §4 |
| (f) the measurement | **PROPOSED, not run** | §6 |

## 2. How the type is decided

From statuses, lists, dates and table cells the layer already carries — **never a note, and never a
figure out of a display string**. It does match LABELS as keys: CIQ's metric names on its Guidance
sheet ("EPS Normalized", "EBITDA", "DPS"), the annual table's row labels ("FCF ($M)") and its "LTM"
column; a renamed label would change a type, which the pins on the 28 pages would show. One pin
blanks every fact's note on all 28 pages and the gaps do not move. Where
a rule cannot decide, the entry says "type not determined", which rule 8 reads as an unknown. **No
path emits type 4** (§7, F5). Every read is cut at the page's price date (`stock_info.as_of`, else
the drawdown window's end): a release filed, or a CIQ guide dated, after it is not read (F12).

**Two reads before a company type.** The release parser misses guides companies give: it reads
no guide from any release of MCK, ROST or V, while CIQ records one on their newest release's date.
So "no guide in any release we read" cannot by itself tell our gap from the company's practice.
CIQ's Guidance sheet (`catalyst_path.guidance_bridge_rows`: the latest guide CIQ records per
metric, with its date) is the second read. "Company's normal practice" needs the two reads to agree
over a span CIQ's export reaches (its freshest row's date).

| item | fields | our gap | does not apply | company's normal practice | change or deviation |
|---|---|---|---|---|---|
| segment profit | `concentration.segment_profit`, `segment_ebitda` | CIQ's roster names 2+ segments, its reconciling lines left out (F11), and the page lacks a 10-K segment profit (a multi-segment filer reports a profit measure per segment, ASC 280-10-50-22) | CIQ reads one segment and the page states no 10-K segment profit | — (segment EBITDA beside a 10-K segment measure is *not determined*: one read, F3) | not built (a recast needs two 10-Ks) |
| the outlook at a gap-down | `drawdown_cause[.anchor.*].revised_guidance` | the release parser read a guide from that 8-K's release, or CIQ records one on its date and the parser read none; or the window's read is UNKNOWN (`shape`: the index lookup failed, no CIK, or the window was not read — F1) | the window was READ and holds no gap-down 8-K | the ladder below | the ladder below |
| the company-adjusted figures | `valuation.ev_ebitda_adjusted_fwd`, `quality.net_debt_to_ebitda_adjusted` | they read only a gap-down 8-K's outlook, so a company adjusted-EBITDA guide in any release read, or on CIQ in that span, is our scope (F2) | — | ladder | ladder |
| the newest release's adjusted-EPS guide | `valuation.adjusted_eps` | CIQ records an EPS guide on the newest release's date, from which the parser read no guide | — | ladder | ladder |
| a current guide | `primary_source.current_guide` | CIQ records a guide on the date of a release the parser read none from | — | ladder | ladder |
| the FCF sign (the runway leg) | `quality.fcf_sign` | the page's annual table states LTM cash flow | — | — | — |
| net debt / EBITDA | `quality.net_debt_to_ebitda` (+ `leverage_survival`) | — | the annual table's LTM EBITDA is not positive | — | — |

**The ladder**, for each guide item:
- **Type 3:** two or more releases were read, none states the guide, and CIQ, reaching the newest,
  records none since the oldest. Where CIQ records an earlier guide, the basis states its date
  (F10). **The coordinator's default** (review of #927, 2026-11-08, within the ruling; the operator
  may overrule it): a last guide more than four quarters before the page's price date is the
  company's practice now; one inside four quarters would be a change, so it reads *not
  determined*.
- **Type 4 — no path.** A release that states the guide, every release since for a full quarter
  stating none, and CIQ silent after it, is the shape a change would leave. It reads *not
  determined*, saying why (§7, F5). The schema still refuses a type-4 entry without what, where and
  when, and any other type that carries them.
- **Otherwise:** type not determined, with the reason.

**Not built, stated:**
- **The peer half of type 4.** The layer carries peers' multiples, never their disclosures.
- **A change in a filing** (a segment recast, a dropped KPI, a late filing). The layer reads one
  10-K's segment instance and holds no KPI history.
- **A release's 8-K item codes**, which `ReleaseExtract` does not store. The releases are the
  EX-99.1s of the 10 newest 8-Ks carrying item 2.02 or 8.01 (`mechanical._primary_source`), so an
  outlook furnished under 7.01 is never read; a non-results 8-K after a guided one is told apart
  only by time.
- **Coverage.** The registry covers the subjects rule 8 named. Rule 8 reads every other UNKNOWN as
  "type not determined" ("every other gap, listed or not").

## 3. Measured at $0 on the 28 pages committed at the panel's freeze (`bcda7ce3`)

115 entries on 28 pages (VRRM carries none), at this PR's round-2 code (the round-1 head
`72d5b3b7` read 96; §7 says what moved):

| item | our gap | does not apply | practice | change | not determined |
|---|--:|--:|--:|--:|--:|
| segment profit | 4 | 13 | 0 | 0 | 2 |
| segment EBITDA beside a 10-K segment measure | 0 | 0 | 0 | 0 | 6 |
| the outlook at a gap-down | 6 | 19 | 0 | 0 | 0 |
| the company-adjusted figures | 7 | 0 | 16 | 0 | 4 |
| adjusted-EPS guide, newest release | 6 | — | 8 | 0 | 9 |
| a current guide | 8 | — | 0 | 0 | 2 |
| the FCF sign | 2 | — | — | — | 0 |
| net debt / EBITDA | 0 | 2 | — | — | 1 |
| **total** | **33** | **34** | **24** | **0** | **24** |

- **MCK's segment gap reads type 1.** CIQ splits its revenue across 5 segments; the page's 10-K
  segment-profit read is UNKNOWN ("segment contexts exist but no profit measure … is tagged on two
  or more").
- **A single-segment filer reads type 2:** all 13 (BRBR, BURL, CNXC, FUBO, LLY, MVST, NCNO, NFLX,
  ROST, SMPL, TGT, V, VITL).
- **A real type-3 page: SMPL** (on the panel). None of its six releases read (2025-07-10 to
  2026-10-27) states an adjusted-EPS guide; CIQ, reaching 2026-10-27, records none since, and its
  last EPS guide is dated 2023-06-29, which the basis states. SMPL guides net sales and adjusted
  EBITDA. The same type for adjusted EPS on AMZN, AORT, BRBR, FUBO, GOOGL, WERN, WLK.
- **The company-adjusted figures (F2).** They read our gap where the company guides adjusted
  EBITDA: on SMPL (its 2026-10-27 release) and UBER (2026-08-05) on the panel, and on AORT, BRBR
  (CIQ, 2026-08-04), FUBO, IT (CIQ) and VITL. They read the company's practice on 16 pages where
  neither read shows such a guide (CNXC guides adjusted operating income).
- **No page reads type 4, and no path emits it** (§7, F5).
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

**The precheck build was not run.** RUNBOOKS §n step 2's check against a `vinci dossier precheck`
build was not run. A precheck builds from today's inputs, so its layer differs from the frozen one
in fields this change does not touch, and it cannot isolate the gap list. The builder and the
transform call the same function on the same layer. The one input they read differently is the
segment count, compared above on every page's own export.

**The $0 compare.** `python -m vinci.evals compare --base origin/main --cand 36f6b1ee` (round 1),
re-run for round 2 with the candidate captured in-process from this PR's round-2 tree (the same
`replay.capture`, the base through `capture_at`), on the frozen panel v2, with the CIQ root at the primary checkout's `data/manual/ciq`, read only. (The
default root's LLY comps export is not the page's own, and `FIX_3A`'s transforms refuse it, as
#926 found.)
- **Bare, no transforms:** every page differs by SYSTEM +285, tool schema +20, and facts +27. The
  +27 is `"disclosure_gaps": null`, because the committed layer carries no gaps.
- **With `FIX_3A` + `FIX_4A` at both refs:**
  - USER moves only in its facts section;
  - with the `disclosure_gaps` value removed, the branch's request equals its `FIX_3A`-only
    request byte for byte, on all six pages (rounds 1 and 2);
  - `FIX_3A` alone at main reproduces #926's per-page deltas exactly (−92, −117, −110, −163, −92,
    −92).
- **SYSTEM and the tool schema:** in every one of the five books, SYSTEM moves only in rule 7b
  (−23 characters) and rule 8 (256 → 564, +308), and the tool schema only in the `bear_points`
  clause (+20). Shown by substituting the old spans with the new and getting the branch's text byte
  for byte.
- **Rule 8 is longer by 308 characters.** The ruling's four types and its evidence demand do not
  fit in fewer words; the trailing-only ask was deleted from both places it lived.

| page | the typed gaps the request carries (round 2) | facts Δ | request total, base → cand |
|---|---|--:|---|
| BURL | segment: does not apply · outlook: does not apply · adjusted figures: practice | +1,177 | 452,904 → 454,386 (+0.33%) |
| CNXC | segment: does not apply · outlook: our gap · adjusted figures: practice | +1,073 | 365,461 → 366,839 (+0.38%) |
| LLY | segment: does not apply · outlook: does not apply · adjusted figures: practice · adjusted EPS: our gap · FCF sign: our gap | +1,702 | 647,727 → 649,734 (+0.31%) |
| MCK | segment: **our gap** · outlook (3 windows): does not apply · adjusted figures: practice · adjusted EPS: our gap · current guide: our gap | +2,045 | 484,106 → 486,456 (+0.49%) |
| ROST | segment: does not apply · outlook: does not apply · adjusted figures: practice · adjusted EPS: our gap · current guide: our gap | +1,747 | 459,324 → 461,376 (+0.45%) |
| SMPL | segment: does not apply · outlook (2 windows): does not apply · adjusted figures: **our gap** · adjusted EPS: **practice** | +1,642 | 477,864 → 479,811 (+0.41%) |

Over the panel: SYSTEM +1,710, tool schema +120, facts +9,386 characters (round 1: +7,376). A
request total is SYSTEM + the tool schema's JSON + USER, at draws=1, with the frozen transcripts;
base is main `a9c59287`, cand this PR's round-2 tree, both with `FIX_3A` + `FIX_4A`.

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
helper; and a rule that reads the segment note. Boundary: one mutant at a time on the code at
`aed508e5` (the PR head after review round 0), `tests/test_gap_test.py` with `-x`. The same 13
were caught before round 0, on the tree committed as `36f6b1ee`. Round 0's two code fixes carry
their own pins, each shown failing on `36f6b1ee`.

**Round 2 (the coordinator's review): 37 of 37 mutants are caught**, one at a time on the round-2
tree, with `tests/test_gap_test.py`, every `tests/test_evals_*.py` and the `test_dossier.py`
contract pin (the reviewer's runner; the HEAD-vs-tree capture test deselected). The reviewer's 23
carry their ids, a `*` marking one re-pointed to code that moved.

| id | what it breaks | first run | after round 2's last pins |
|---|---|---|---|
| G1* | an unreadable CIQ date skipped, not refused | survived | killed |
| G2 | an undated release not refused | survived | killed |
| G3 | CIQ's EPS family narrowed to "EPS Normalized" | killed | killed |
| G4 | a declared dividend counted as a guide | survived | killed |
| G5 | the 1c skip of a release the parser read | killed | killed |
| G6 | the full quarter of a stop | killed | killed |
| G7 | CIQ's reach on a stop | killed | killed |
| G8 | practice from one release | killed | killed |
| G9 | CIQ's reach on practice | killed | killed |
| G10 | the span from the oldest release | killed | killed |
| G11 | two segments read as one | survived | killed |
| G12* | a failed 10-K read on a one-segment filer | killed | killed |
| G13 | leverage on non-positive EBITDA | killed | killed |
| G14 | the FCF sign with no LTM cash flow | killed | killed |
| G15* | an unread window as "does not apply" (F1) | killed | killed |
| S1, S2 | the schema's evidence legs | killed | killed |
| R1, R2 | rule 8's meaning (F6) | killed | killed |
| T1, T2* | the transform's identity; the line's lone segment | killed | killed |
| W1 | the builder handed no segment count (F7) | killed | killed |
| C1* | a lone segment short of 99.5% read as one | killed | killed |
| mine, round 0 (6 not above) | practice without CIQ; single → ours; multi → nothing; the blind-flag ask; a loose line helper; a note read | killed | killed |
| round 2 (8) | no scope rung (F2); segment EBITDA as practice (F3); the stop shape as practice (F5); a tiebreak row read (F8); no four-quarter window (F10); no reconciling lines (F11); releases uncut; CIQ uncut (F12) | killed | killed |

`tests/test_dossier.py`'s old pin, which asserted "OPACITY-AS-SIGNAL" and "BEARISH risk", now
asserts their absence. That is the ruling's intended reversal.

## 6. The measurement — PROPOSED, not run (the operator approves any paid run and its cap)

**The target, and why M-LABEL alone cannot read this change.**
- Today's only calibrated target is M-LABEL. On #926's 30 CAND draws it counts 47 units: "no
  adjusted forward" 29, trailing-only 13, segment-undisclosed 5, runway-not-derivable 1, bleed 1.
- **Item (c)** removes the prompt's ask behind the 13 trailing-only units. That family is precise:
  the old label's words, on a page that carries a CIQ forward multiple. So M-LABEL can read (c).
- **Items (a)–(b)** act on the other three families, but M-LABEL counts some of the very output
  the ruling asks for. Shown at $0 on MCK's frozen page (the scorer's `label_echo`), on three
  compliant, typed `key_unknowns` lines:
  - "Segment profit by segment (concentration.segment_profit) is our gap: …" is a hit
    (segment-undisclosed, `segment_profit`);
  - "ev_ebitda_adjusted_fwd does not apply: no gap-down 8-K is in the window …" is a hit
    (no-adjusted-forward);
  - "valuation.adjusted_eps is our gap … CIQ records an EPS guide dated 2026-11-04 …" is not.
  - The families' conditions hold on every panel page.
  - So M-LABEL can fall from (c), and from the model dropping inapplicable gaps. It cannot see the
    ruling's own effect, a gap that is no longer called a risk, and it can count compliance as a
    misread.
- **Precision.** On gold, M-LABEL is right 22 of 32 TEST hits. On output written under the gap
  test its precision is untested, and it is biased AGAINST this change.

**So the ruling's effect needs a new metric, and a new metric needs fresh gold first.** RUNBOOKS §n
step 7: TEST was read once at `a677d1a1`, so a metric designed now would read it in-sample.
- **Proposed metric: M-GAP.** A unit frames a gap that is not a stated change as a risk, or rests a
  bear point on one.
- **The gold, at $0 to draw:** the units of #926's 60 existing draws (registration `cceba9d9`):
  - every `key_unknowns` and `bear_points` unit that speaks about a rule-8 subject. A crude selector
    finds 147 + 14 = 161 (52 of the `key_unknowns` carry a risk word: 30 BASE, 22 CAND);
  - plus a random 60 of the remaining units of those two fields, to measure recall;
  - **about 220 claims**, double-coded, split DEV/TEST by page before coding (three pages each). The
    metric is fit on DEV and TEST is scored once.
  - Boundary: those 60 draws, units by `units.draw_units` at `fc79a7be`, the selector kept in the
    session family's notes folder (`fix4a-gap-test.md`).

**The registration, once the target is chosen** (with M-LABEL alone it can be registered today,
the bias stated in its `--note`):

```
python -m vinci.evals budget-open --budget-ledger <notes>/ledger-fix4a.jsonl --cap 35 \
  --approval "<the operator's words>"
python -m vinci.evals register --base origin/main --cand <this PR's head> \
  --transform relabel_drawdown_shape --transform trailing_only_note --transform survival_read \
  --transform peer_gap_question --transform print_row_guide --transform gap_types \
  --target M-LABEL [--target M-GAP] --ship-alpha 0.01 \
  --ciq-root /Users/work/Documents/GitHub/mosaic-theory/data/manual/ciq \
  --note "<what the target covers and does not>" --budget-ledger <notes>/ledger-fix4a.jsonl \
  --out <notes>/registration-fix4a.json
python -m vinci.evals run-compare --registration <…> --budget-ledger <…> --out-dir <fresh> --paid
python -m vinci.evals score --out-dir <…> --registration <…> --budget-ledger <…>
```

- **Both arms carry `FIX_3A`.** The frozen pages predate #923, and a rebuilt page carries its
  labels, so the comparison isolates fix 4a.
- **Design:** panel v2, 5 draws per page per arm, 60 calls.
- **Cost:** #926 drew the same design for **$30.72** (60 calls, $4.55–$6.23 a page). This change
  moves each request by 0.31–0.49% (§4, round 2), so **≈$31**.
- **Cap proposed: $35** for the first run. A replication (p_lower in (0.01, 0.05]) would cost ≈$31
  more and does not fit $35; RUNBOOKS §n stops rather than raise a cap. So **$70** if the operator
  wants it to fit one approval.

## 7. The coordinator's review (round 2, the last): F1–F13

On the round-1 head `72d5b3b7`. One commit, $0. Each FIX has a pin that fails on `72d5b3b7`.

- **F1, FIX. "Does not apply" when our own lookup failed.** `filings == []` is also what
  `mechanical._read_gaps` writes when the 8-K index lookup failed or there is no CIK, and what
  `_gap_window` writes for a window it never read. In both, `shape` is UNKNOWN. A window now reads
  "does not apply" only when it was READ (`shape` PRESENT); otherwise it is our gap. Pinned on
  BRBR's real page with the lookup marked failed, and on MCK's with the at-anchor window unread.
- **F2, FIX. The company-adjusted figures.** `_adjusted_facts` reads only a gap-down 8-K's outlook,
  so they are their own item. Where the company guides adjusted EBITDA in a release read, or on
  CIQ in that span, they are our gap, and the basis names the guide and its release. SMPL and UBER
  are pinned as our gap; BRBR on CIQ alone.
- **F3, FIX. Segment EBITDA from one read.** Beside a 10-K segment measure it read "practice", but
  the instance read tries `OperatingIncomeLoss` first, so one read cannot show the filer discloses
  no segment EBITDA. It is now not determined, pinned on AMZN, AORT, GOOGL, NKE, TJX and WLK.
- **F4, FIX. Guards pinned with the real entries they decide.**
  - G9 (CIQ's reach): IT, MVST ×2, PARR ×2, VITL;
  - G10 (the span from the oldest release): NCNO's adjusted EPS;
  - G13 (non-positive EBITDA): ORKA and TECX.
  - Four more guards decide no real entry and are pinned on one-field edits: G6 (the full
    quarter), G7 (CIQ's reach on a stop), G12 (a failed 10-K read on a one-segment filer), G14 (an
    FCF sign with no LTM cash flow).
- **F5, FIX. Type 4's evidence rests on parser blanks.**
  - **Measured at $0 on the 28 pages: does CIQ re-date a guide reaffirmed unchanged?** Two pairs
    where the parser read the same low and high in two releases have CIQ data to compare:
    - AORT's 2026 revenue (480–496, 2026-05-07 and 08-06): CIQ dates it 2026-08-06, so it
      re-dated;
    - VITL's 2026 revenue (775–800, 05-07 and 08-06): CIQ dates it 05-07, but its export reaches
      only 05-07, so this shows nothing.
    - Five other repeated guides were superseded by a later changed guide.
    - So re-dating is shown once, and never shown otherwise.
  - The coordinator found the parser's blanks mostly misses (20 of 20 where CIQ can see the
    release).
  - **So no path emits type 4.** The stop shape reads not determined, saying why. Pinned on TGT's
    real page with its two refuting CIQ EPS rows moved to March.
  - The false comment ("the release list holds every EX-99.1") now states that the releases are the
    10 newest 2.02/8.01 8-Ks, so 7.01 outlooks are never read.
- **F6, FIX.** Rule 8 is pinned by sha256 (`RULE_8_SHA256`, every book). R1 ("practice may be
  raised as a risk") and R2 ("read as bearish") now fail it.
- **F7, FIX.** The assembly is pinned with LLY's real cut Segments sheet: the count reaches the
  builder, and W1 (`segment_count=None`) fails it.
- **F8, NO CHANGE NEEDED, pinned.** `filed_tiebreak.apply` rewrites only its `MAPPING` and
  `CONTAINING` rows: "Other Unusual Items", "Restructuring Charges" and "Merger & Related Restruct.
  Charges". The survival items read none of those (`gaps.ANNUAL_ROWS_READ`). A pin keeps the two
  sets disjoint, so a stale entry cannot occur.
- **F9, FIX.** The segment bases claim no read that may not have happened. An absent
  `segment_profit` says "the page states no segment profit from the 10-K"; an UNKNOWN one says
  "the 10-K segment-profit read is UNKNOWN".
- **F10, FIX.** The practice basis states CIQ's last guide date: SMPL's EPS, 2023-06-29. The
  coordinator's default (four quarters) is in §2 and in `gaps.FOUR_QUARTERS`, pinned on a GOOGL
  edit inside the window.
- **F11, FIX.** The segment count leaves out reconciling lines (eliminations, intersegment,
  corporate, unallocated: `ciq_sheets.is_segment_line`). One test serves the builder and the
  harness; WLK now reads 2. No type moved.
- **F12, FIX.** Releases and CIQ guide rows dated after the page's price date are not read here.
  ORKA's 2026-10-26 release on its 2026-10-23 page is pinned, with an SMPL edit. **Found, not
  fixed:** the layer itself does not cut `primary_source.releases` or CIQ's guide rows at the price
  date (STATE row 57).
- **F13, FIX.**
  - S1 (a type-4 entry without `source_ref`) and S2 (another type carrying `stopped_ref` or
    `disclosed`) are pinned.
  - `tests/fixtures/ciq_segments_eval_panel.json` is re-cut by nulling. Every non-empty cell whose
    loss leaves four readings unchanged is null: `segments` and `segment_ebitda` against the
    committed lines, `segment_count` and `stated_currency` against the full sheet. 17–26 cells are
    kept per page, of 403–778.

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

## Amendments

- **2026-11-09 — measured; ships by the registered rule.** $30.31 of $70, panel v2, #927 frozen at
  `564baad8`: M-GAP 37 → 4 units, p_lower 2.6 × 10⁻¹¹ against the 0.01 ship bar, so no
  replication; M-LABEL's gated families 10 → 1; no class worsened. See
  `docs/records/2026-11-09-fix4a-measured-on-the-panel.md`.
