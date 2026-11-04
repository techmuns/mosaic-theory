---
id: 2026-11-04-untraceable-figure-caveats-measured
status: open
date: 2026-11-04
prs: []
supersedes:
superseded-by:
---

# The "Untraceable figure" caveats are measured: nearly all are a real figure the point took from a fact it did not cite, which only the citation schema or the prompt can fix; two false classes (a percentile written as its rank, a hyphenated duration) are closed in the trace, and every made-up figure the trace caught it still catches

**WHAT.** A deterministic replay of `synthesis._validate` (no model call) over every committed
synthesis, each UNTRACEABLE flag classified by where its figure lives, then two check-side fixes:

- **A percentile traces as its rank.** `ev_ebitda_percentile_5y` stores 0.026 and the point writes
  "the 3rd percentile"; 2.6 against 3 is outside the trace's max(0.05, 2%) tolerance. A 0..1 value
  in a field named for a percentile (`synthesis._PERCENTILE_FIELDS`: `pe_percentile_5y`,
  `ev_ebitda_percentile_5y`, the history bands' `percentile`) now also states its whole-number
  rank (half up), traced only as that rank, the way a date already states its year.
- **A duration is a label however it is written.** `_CAL_AFTER` skipped "5 years"; the claim trace
  now also skips "a 5-year window", "the 52-week low", "over ~2y", "its 2.3y range"
  (`synthesis._DURATION_AFTER`). Time units only: "$5-billion" and "5-10%" stay figures. The
  transcript-row check (`driver_extract._figures`) is deliberately left as it was, so a row's value
  still needs its quote to state a hyphenated duration.

Extraction version `2026-11-04.trace-rank-and-duration` (Python table and its web twin).

**THE MEASUREMENT (step 1).** 373 UNTRACEABLE figures on 176 points over 30 page versions: 318 on
154 points across the 27 committed pages (only CNXC, LLY, NFLX, NKE, ROST and TJX print them today;
the other 21 were assembled before #859 and would print them at their next assembly), and 55 on 22
points across PR #886's GOOGL (21), LLY (24) and AMZN (10). Each flag was located by the
precision its figure is written at ("15.1" is any stored value that, at a trace scale, rounds to
15.1), with a decoy test: ten same-precision figures around it, and a match counts as evidence
only if fewer than half of the decoys also match.

| class | main 27 pages | #886 3 pages |
|---|--:|--:|
| (b) the cited fact's own percentile, written as its rank — FIXED | 4 | 1 |
| (b') another value of the cited fact rounds to it — NOT fixed (below) | 7 | 0 |
| (d) a hyphenated / abbreviated duration — FIXED | 5 | 2 |
| (a) stated by another fact in the cited fact's section, specifically | 139 | 18 |
| (a) stated by another fact elsewhere on the page, specifically | 46 | 9 |
| (e) stated only in a block that carries NO source_ref | 6 | 2 |
| (u) some fact states it, but so do most decoys — (a) or (c), not decidable | 111 | 23 |
| (c) no value on the page states it | 0 | 0 |

No figure falls in (c) deterministically: a page carries 5,000–12,000 numbers, so almost any figure
of four or fewer significant digits is stated somewhere. (c) was settled by hand:

- **#886, all 55 by hand:** 49 (a), 1 (b), 2 (d), 2 (e), **1 (c)**. GOOGL's "-0.3% over 180 days"
  is NOT found nowhere: it is the name's own 180-day return, -0.319% (`idiosyncratic_vs_shared.
  name_180d_return`, ref `EOD GOOGL 180d to 2026-10-16`), in a point citing the relative return —
  (a), the same shape as the frozen SMPL point `test_model_input_checks` pins. LLY's "$6.5B
  Houston" IS the (c): the page's only Houston fact, `operating_drivers.rows[24]` (Key
  Developments, Sep-21-2026), names the groundbreaking and its verbatim ends before the sum; the
  CIQ Key Developments export on file states "$6.5 billion" further on, the two calls on file do
  not, and the point cites an unrelated 2019 acquisitions fact. A true figure the validated layer
  does not hold — flagged, correctly. LLY's "$5B Richmond" is (a) (`operating_drivers.rows[6]`
  states "$5 billion"), and its "5-year window" is (d).
- **main, a seeded sample of 20 of the 111 (u)** (seed 20261104): 17 (a), 1 a duration "8q" (not
  in the fixed forms; left), 2 not stated on the page — TECX's "~-40% intraday" gap and FUBO's
  "~2%" consensus EBITDA margin, each a figure the model worked out rather than read.

So the coordinator's loose scan (51 of 55 found elsewhere on the page) was right in substance: 49
(a) + 2 (e) on the page, 1 (b) in the cited fact itself, 2 labels, 1 genuinely absent.

**THE FIX ON THE CORPUS (step 2), before = 9e996d7f, after = this branch, same pages.**
- main's 27 pages: 318 → **309** UNTRACEABLE (IT, NFLX, NKE, TJX a rank; EPAM, MVST, NCNO, NFLX, WLK
  a duration), and one QA-only TRANSCRIPT-FIGURE note (UBER's "~1.8y") clears too.
- #886's 3 pages: 55 → **52** (AMZN 10 → 9: "3rd percentile"; LLY 24 → 22: "5-year window",
  "~2y"; GOOGL 21 → 21). The (c) "$6.5B Houston" is still flagged.
- No flag of any kind was added; every other flag is identical as a multiset (BURL, FUBO, NCNO
  and TECX list their DIRECTIONAL flags in a different order from run to run — the validator
  iterates a set — on both trees).

**WHY NOT MORE, check-side.** Two wider rules were built in the replay and rejected:
- *Round to the figure's written precision against the cited fact* (any value, not just a
  percentile) would clear 12 figures, and 7 of them are not the cited fact's: CNXC's "margin 12%
  vs 18%, rev growth 3% vs 8%, LT EPS growth 5% vs 10%" (operating statistics) cited to its trading
  multiples, where 17.6, 2.87, 8.45 and 4.8 round to 18, 3, 8 and 5; BURL's "the name fell 24%"
  (its own -24.4%) cited to the relative return (-23.5%); WERN's "caps (14x)" (43.1 ÷ 3.1, worked
  out); TECX's "Phase 2" (a label).
- *Trace a figure to any fact in the cited fact's section* would clear most of (a), and it is the
  pinned G-D6 case: on the made-up-figure mutation below it catches 675 of 1,564 where the per-fact
  trace catches 1,362.

**HOW VERIFIED.**
- The replay reproduces the stored caveats exactly on every page that carries them (CNXC 17, LLY 7,
  NFLX 33, NKE 12, ROST 13, TJX 15 on main; GOOGL 21, LLY 24, AMZN 10 on #886).
- **No made-up figure gets through that was caught before** — each mutation is a fresh one-point
  synthesis through the real `_validate`, cited to a real ref of a committed page, seeded, so
  before and after see identical figures:
  - G-D6 shape: 1,564 made-up 1-dp figures in [100, 1000), four per committed structured point —
    1,362 flagged before and **the identical 1,362 after**.
  - Small whole numbers 1–24 (the only band a precision rule can widen): 1,564 — 1,257 flagged
    before and the identical 1,257 after.
  - Every rank 0–100 written as "the Nth percentile", cited to each page's two percentile facts:
    4,242 — 4,053 flagged before, 4,038 after; **each of the 15 no longer flagged is that fact's
    own rank** (3 for 0.026 on AMZN's two versions, EPAM, IT, NFLX and NKE; BRBR 4; BURL 2; EPAM
    8; SMPL 2; TJX 6; UBER 8; VITL 8 and 3; VRRM 4). The rule admits one number per percentile,
    and only to its own fact.
  - A made-up 1-dp figure after "a N-year window": 1,564 — the figure flagged 1,371 before and the
    identical 1,371 after; the duration itself was flagged 1,243 times before and 0 after.
  - The committed G-D6 draw (frozen SMPL, seed 20261029): 195 of 199 before and after, now pinned
    as an exact count.
- **The 1,176.** The brief asked that "the G-D6 mutation that made up 1,176 figures" still be caught
  1,176 of 1,176. That figure is the audit's measurement of the OLD whole-layer trace on c51c286a,
  which let 1,176 of 1,176 made-up figures through; its draw is not committed (searched `1,176`,
  `1176`, `G-D6` across the repo: the code comment and a test docstring only). The committed
  reproduction is the frozen 199-figure draw; the corpus mutation above is the larger stand-in.
- Pins (`tests/test_untraceable_rank_and_duration.py`, 41): 18 fail on 9e996d7f (run in a scratch
  copy of it) — the frozen page's "2nd percentile" for its 0.0183, ranks 0–100 against it, a
  history band's rank, the five duration forms, a figure after a duration flagged alone, the
  closed field set against the page schema, and the corpus invariant on EPAM, IT, MVST, NCNO,
  NFLX, NKE, TJX and WLK. The negative assertions hold on both trees: of ranks 0–100 cited to the
  frozen percentile only its own (2) is new ({0, 5, 18} traced before through its other numbers);
  the same 0.0183 in a field that is not a percentile, or the rank cited to another fact, stays
  flagged; "$5-billion", "5-10%" and "7-yard" stay figures; the transcript-row check still reads
  every duration as a figure.
- ruff and `mypy --strict vinci` clean; `pytest -m "not network"` — see the PR body.

**A LIMIT OF G-D6 MEASURED ON THE WAY, reported not fixed.** 202 of the 1,564 made-up figures trace
on both trees, because the fact a point cites can itself hold hundreds of numbers: 48 of 112 cited
to `CIQ Estimates→Trends` (median 134 numbers in the fact), 33 of 136 to the income-statement
margin reconciler (40), 19 of 28 to the annual statement (312). The per-fact trace is as strong as
the cited fact is small.

**WHAT IS LEFT, AND WHOSE (step 2's STOP).** 49 of the 52 caveats on #886's pages are class (a), a
real figure the point took from a fact it did not cite; on main's 309, 185 are (a) located
specifically, and 17 of a 20-flag sample of the 111 undecided are (a) too. The caveat
is TRUE — the cited fact does not contain the figure — so the guard is right and nothing on the
check side can clear them without clearing a made-up figure cited the same way. The point schema
has one `source_ref`, and the prompt never asks that a point's figures come from it. Each remedy
below is the operator's call; none is built.

1. **Citation schema** (the "later build" of the 2026-10-29 ruling): a point cites every fact its
   figures come from, and each figure must trace to one of them. Ceiling on these pages: the 49
   (a) of #886 and most of main's. It changes `schemas.py` (a protected file), the tool schema,
   the prompt, the renderer's citation and `_validate`, and needs a paid re-draw to measure. Each
   added ref widens the universe a figure may trace to, so the catch rate falls with it — the
   section simulation above is the far end of that curve; a cap on refs per point would be a
   face-validity number to set before any re-draw.
2. **Prompt only**: tell the model that every figure in a point must be stated by the fact it
   cites, and to split a point that combines facts. No schema change; the effect is measurable
   only by a re-draw (one page ≈ $3–6 at the #886 costs).
3. **One caveat per point**: name every untraced figure of a point in one line. On #886, 52
   caveats would print as 22 lines; on main, 309 as 154. Hides nothing and moves no guard, but
   changes what the page prints, so it is a preview-and-approve render change.
4. **Give the ref-less blocks a ref** (class (e)): `peer_capital_intensity.rows` (2,326 numbers on
   27 pages), `consensus_context.consensus_levels` (1,890 on 25), `capital_structure.
   maturity_check` (755) and others carry no `source_ref`, so no point can cite a figure in them
   (LLY's "$27,958M" acquired and "FY33 $103,325.5M median"). An assembler/schema change.

**BOUNDARY.**
- Corpus: `data/dossiers/*/dossier.json` at 9e996d7f (27 pages; synthesis as committed, assembled
  2026-08-18 → 2026-10-29) and PR #886's three pages at 2746d0ef (assembled 2026-11-03), measured
  2026-11-04. Unit: an UNTRACEABLE figure (one flag; a point can carry several), or a point.
- Classes: first that applies, in the table's order; "specific" = fewer than 5 of 10 decoys at
  ±4% steps (or ±1 unit of the last digit) also stated; "section" = the cited fact's top-level
  key of the mechanical layer. The hand classification covers #886's 55 and a 20-flag sample of
  main's 111 (u); the rest of (u) is not classified.
- Mutations: one-point syntheses on the same 30 page versions; "structured point" = a committed
  bull/bear/decisive point whose ref is in the layer and is not a transcript (391 points × 4 =
  1,564); percentile facts = `pe_percentile_5y` / `ev_ebitda_percentile_5y` with a ref (42).
- Scripts (scratch, not committed): `classify.py`, `replay.py`, `dur_check.py`,
  `sibling_sim.py`, `gd6_where.py`, run against a copy of 9e996d7f's `vinci/` and this branch's.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- A made-up whole number that happens to equal the cited percentile's rank now traces — the same
  latitude a fact's year already has. Falsifier: a committed point whose "Nth percentile" is not
  the percentile its cited fact states, yet traces.
- A made-up duration in hyphenated or abbreviated form is not checked, as its spaced form never
  was. Falsifier: a committed point whose "N-year"/"Ny" is false against the fact it cites.
- Nothing on a committed page moves in this PR: the caveats are written at assembly, so each page
  drops its rank and duration caveats at its next assembly. #886's pages keep 10 / 21 / 24 until
  then.
