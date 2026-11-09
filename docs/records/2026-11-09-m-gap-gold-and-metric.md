---
status: recorded
date: 2026-11-09
prs: [929]
supersedes:
superseded-by:
---

# M-GAP, a calibrated gap-framing metric ($0): a 221-unit gold drawn from #926's draws by a pre-registered rule and double-coded blind (kappa 1.000 on the error); the metric, fit on DEV, meets its pre-registered bar on TEST, scored once (precision 0.833, recall 0.882, kappa 0.827); M-LABEL cannot be #927's no-worsening check as it stands, and a handling plus #927's registration are proposed, not run

**THE APPROVAL.** Operator, 2026-11-09, verbatim: **"Yes, grade first"**, answering whether to build
a calibrated gap-framing metric before measuring fix 4a (#927). It costs $0: no paid call was made.
The coder and adjudicator agents ran inside the session.

**WHY.** #927 replaces the prompt's rule 8 ("a missing disclosure is a BEARISH risk") with the
operator's gap test. Each missing item a page carries is sorted (`vinci/dossier/gaps.py` on #927)
into one of four types:
1. our gap;
2. does not apply;
3. company's normal practice;
4. change or deviation.

A fifth outcome, "type not determined", is read as an unknown. Only type 4 may be raised as a risk.

The harness's one calibrated target, M-LABEL, cannot read that change:
- It counts some compliant output as errors: on MCK, two of three compliant typed lines are hits
  (#927's record §6).
- RUNBOOKS §n step 7: the 644-claim gold's TEST half was read once, so a new metric needs fresh
  gold.

**THE RESULT IN SIX LINES.**
- **Gold:** 221 units of #926's 60 stored draws, both arms: 161 picked by a subject selector plus
  60 at random, under a seed fixed before any unit was read.
  - Split DEV/TEST by page, by a recorded rule: CNXC, LLY, MCK / BURL, ROST, SMPL.
  - Coded by two blind coders; the adjudicator settled 11 `item` splits and changed no error.
- **Agreement:** kappa 1.000 on `gap` and on `error` (221 of 221). The two coders are two
  instances of one model under one rubric, so this measures that model's consistency, not two
  independent readers (§3).
- **M-GAP**, deterministic, fit on DEV: tp 34, fp 2, fn 0.
- **On TEST, scored once after its bar was written:** precision 0.833 (Wilson 95% 0.61–0.94),
  recall 0.882 (0.66–0.97), kappa 0.827 (bootstrap 95% 0.66–0.96). **The bar is MET**
  (0.80 / 0.80 / 0.70).
- **M-LABEL** fires on 53% of the gold's NEUTRAL gap statements and on 29% of its gap-framing
  errors, and on 2 of #927's 3 compliant typed lines (M-GAP on none). So it cannot be #927's
  no-worsening check as it stands (§6).
- **#927's registration is proposed, not run** (§7): M-GAP as target, ≈$31, cap $35, or $70 with
  room for a replication.

## 1. The population, the sample and the split — fixed before any unit was read

The pre-registration is `tests/fixtures/synthesis_gap_gold/PREREG.md`, with the shas it recorded at
each step.
- **Population:**
  - #926's stored draws (registration `cceba9d9…`, `draws.jsonl` sha256 `08b20173…`, the same
    file the coordinator re-scored);
  - units by `units.draw_units` (unchanged since `fc79a7be`);
  - the `key_unknowns` and `bear_points` fields only: 799 units.
- **Sample:**
  - SUBJECT: every unit matching the fix 4a session's subject selector, verbatim: 161 units.
  - RANDOM: 60 of the remaining 638, drawn by `random.Random(int("cceba9d939692bfc", 16))`, a seed
    fixed in writing first.
- **Split:**
  - The rule: rank the six panel pages by `sha256("cceba9d939692bfc:" + TICKER)`; the first three
    are DEV.
  - DEV = CNXC, LLY, MCK (121 units); TEST = BURL, ROST, SMPL (100).

## 2. The ground truth: each page's gap types, frozen

`vinci/evals/synthesis_gap_types.json` holds the panel pages' gap entries, typed by #927's own code
at `601d2f7e` (`gaps.disclosure_gaps` via `variants.gap_types`).
- Each page is the one frozen at the panel's freeze, blob checked. The five `FIX_3A` transforms were
  applied first; the types are identical without them. Each page's own comps export was used.
- **The PAGE's truth,** the same for both arms. M-GAP reads it and imports nothing from #927, so this
  PR does not depend on #927 merging.
- 25 entries over six pages: 10 does not apply, 6 company's normal practice, 9 our gap.
  **No page has a "change or deviation" entry.** So on this panel, any gap held against the company
  is the misread.

## 3. The taxonomy and the coding

- **The taxonomy** (`TAXONOMY.md`) was written before any coding. For each unit the coder decides:
  - does it state a gap;
  - which of the page's entries ("other" if none);
  - its framing: risk, bearish, bear-rest or neutral;
  - is that entry type 4;
  - `error` = a gap framed as risk, bearish or bear-rest that is not type 4.
- **Two coders,** each in its own folder holding only the taxonomy, the page entries and the
  shuffled units (opaque ids, arm and draw stripped).
  - Neither transcript touches the other's folder or the population file.
  - Neither decided codes by script.
- **Agreement:** `gap` 161 vs 161 and `error` 51 vs 51, the same units: kappa 1.000 on both, in
  each half. The coders differ only on `item`, for 11 units (whether a covenant-basis line names the
  company adjusted-EBITDA entry). The adjudicator decided all 11 for coder B, and no `error`
  changed.
- **What kappa 1.000 is, plainly.** The coders are two instances of one model under one rubric, so
  it is that model's consistency, not two independent readers. The 644-claim gold's coders agreed
  at 0.76 on a harder, eleven-class taxonomy. This taxonomy asks one narrower question, and
  agreement on it is expected to be higher. A human-coded sample would be the independent check;
  it is not done here.
- **The gold, by half:**
  - 51 errors, every one a `key_unknowns` line (31 bearish, 20 risk), in both arms (BASE 27,
    CAND 24);
  - 110 neutral gap statements;
  - 60 units state no gap.
  - **No bear point states a gap, so M-GAP's bear-point branch is untested on this gold.**
  - The RANDOM stratum holds no error (0 of 60). Every error falls inside the subject selector, so
    recall outside it is estimated at 0 misses in 60 sampled units.

## 4. M-GAP — the metric (`metrics.gap_framing`)

A `key_unknowns` line or a bear point is a hit when all three hold:
- it STATES a gap (UNKNOWN, missing, not disclosed, unreadable, not derivable, no segment breakout,
  no forward or adjusted figure, opacity);
- it holds the gap against the company: bearish; or a risk, concern or opacity, unless it calls the
  gap neutral or an open question ("a risk, NOT a neutral gap" stays a risk); or, in a bear point,
  the gap is what the point rests on;
- the page's gap test types none of the entries the unit names a change. An unnamed gap is "type
  not determined" and counts.

A label the unit QUOTES (`'not assessable (a risk)'`) is the page's word, not the unit's framing;
a possessive never opens a quote.

- **Defined only on the frozen pages.** Off them it is left out of a score (undefined, never zero),
  and a registration refuses it as a target. It is not a no-worsening check for other changes (not
  in `GOLD_CLASS`).
- **Fit on DEV only:** 121 units, 34 errors → tp 34, fp 2, fn 0. Both false hits use "opaque" or
  "risk" descriptively ("limits risk decomposition").
- **Frozen** (`metrics.py` sha256 `80e5357f…`) with its bar written before TEST was read: precision
  ≥ 0.80, recall ≥ 0.80, kappa ≥ 0.70 as point estimates. Intervals are reported, not gated.

**TEST, scored once:** 100 units, 17 errors, 18 hits.

| | value | 95% interval |
|---|---:|---|
| precision (15 of 18) | **0.833** | Wilson 0.608–0.942 |
| recall (15 of 17) | **0.882** | Wilson 0.657–0.967 |
| kappa vs the gold's `error` | **0.827** | bootstrap 0.656–0.960 (10,000 resamples) |

**The bar: MET.**
- Per stratum: SUBJECT 17 errors, 15 caught, 3 false hits; RANDOM 0 errors, 0 false hits.
- **The five TEST disagreements, read after the score (the metric unchanged):**
  - three false hits use "opaque" as a description, which the coders read as neutral (a chain's
    margins "opaque", a brand split "opaque", a debt panel "opaque");
  - one miss says "a material gap given a windfall-flattered headline", with no risk word;
  - one miss says "an opacity to resolve, not a neutral gap", where the neutral marker "to resolve"
    suppressed it.
  - Two of the five are units both coders had flagged as ambiguous before any adjudication.

## 5. What this gold can and cannot show

- **It is old-prompt output.** Both arms of #926 wrote under rule 8 as it was. M-GAP's precision on
  output written UNDER the gap test (typed lines) is untested beyond the three probe lines in §6,
  where it fires on none. A post-run audit is proposed in §7.
- **No type-4 page.** The type-4 exemption is pinned on a constructed page, never seen in real
  output.
- **No bear point states a gap,** so the bear-rest branch rests on the taxonomy's definition alone.
- **The intervals are wide,** with 17 TEST errors: the precision interval reaches 0.61.
- **The gap types are looked up by ticker** (`gap_entries`). Every harness path reads the frozen
  panel pages, whose blobs the fixture records and a pin checks. A score on a re-assembled page of
  the same ticker would read freeze-time types, so new pages need new frozen types (a code review
  finding, not fixed: the metric was frozen when TEST was read).
- **Known misreads, kept:** a descriptive "opaque" counts as framing (3 TEST false hits), and
  "to resolve" suppresses an explicit "not a neutral gap" (1 TEST miss). Changing either after
  TEST would read TEST in-sample; a revised M-GAP needs fresh gold.

## 6. M-LABEL on the same gold — can it be #927's no-worsening check?

M-LABEL is the fixed scorer, never fit here, run over all 221 units:

| gold | units | M-LABEL hits | families |
|---|---:|---:|---|
| a gap framed against the company (error) | 51 | 15 (29%) | segment-undisclosed 10, no-adjusted-forward 4, runway 1 |
| a NEUTRAL gap statement | 110 | **58 (53%)** | no-adjusted-forward 54, trailing-only 20, bleed 2, runway 1 |
| no gap | 60 | 1 (2%) | trailing-only 1 |

On #927's three compliant typed lines (MCK), M-LABEL counts two (segment-undisclosed,
no-adjusted-forward) and M-GAP none.

**So, as it stands, M-LABEL cannot be #927's no-worsening check.** Three of its families
(no-adjusted-forward, segment-undisclosed, runway-not-derivable) count a gap STATED. They count a
neutral statement more often than a framed one. #927 asks the model to state each gap, typed and
neutral. So a compliant CAND arm can raise those families and read as a worsening, biased against
the change. The other families (bleed, trailing-only, pe-percentile-blocked) count labels #927 does
not ask for, and its item (c) should lower trailing-only.

**PROPOSED, for the coordinator's review (not decided here, and pre-registered before any draw):**
- **(A, recommended)** M-GAP is the target. M-LABEL's no-worsening check counts only the families
  #927 does not ask the model to write: bleed, trailing-only and pe-percentile-blocked. The three
  gap-statement families are reported, not gated.
  - This needs a small scorer field (a registration's no-worsening families), its own pinned code
    and tests, landed before #927 is registered.
  - Its falsifier: the CAND arm's gap-statement families rise while M-GAP falls. That is the
    expected signature of compliance; read the other way, it would mean M-GAP misses a framing
    those families catch.
- **(B)** M-GAP is the target and M-LABEL is reported, not gated, for #927, with its families stated
  in the registration's note. No code is needed, but nothing guards the bleed and trailing-only
  labels.
- **(C)** M-LABEL gates whole, as the scorer does today. That is biased against #927, and is not
  recommended.

## 7. #927's registration — PROPOSED, not run (it needs the operator's approval and a cap)

- **Design:** main → #927's head, on the frozen panel v2. Both arms carry the five `FIX_3A`
  transforms and `gap_types` (`FIX_4A`). Five draws per page per arm, 60 calls. Ship alpha 0.01
  (the replication rule).
- **Target: M-GAP.** M-LABEL is handled as §6 is ruled. The `--note` states that the target covers
  the gap framing and that M-GAP is defined on these six pages.

```
python -m vinci.evals budget-open --budget-ledger <notes>/ledger-fix4a.jsonl --cap 35 \
  --approval "<the operator's words>"
python -m vinci.evals register --base origin/main --cand <#927's head> \
  --transform relabel_drawdown_shape --transform trailing_only_note --transform survival_read \
  --transform peer_gap_question --transform print_row_guide --transform gap_types \
  --target M-GAP --ship-alpha 0.01 \
  --ciq-root /Users/work/Documents/GitHub/mosaic-theory/data/manual/ciq \
  --note "<what the target covers and does not>" --out <notes>/registration-fix4a.json
python -m vinci.evals run-compare --registration <…> --budget-ledger <…> --out-dir <fresh> \
  --ciq-root <the same root> --paid
python -m vinci.evals score --out-dir <…> --registration <…> --budget-ledger <…>
```

- **The CIQ root** must be the primary checkout's `data/manual/ciq`. The assembler's copy holds
  stale LLY and SMPL comps exports, which the transforms refuse.
- **Cost:** #926 drew the same design for $30.72, and #927 moves each request by 0.31–0.49%. So
  **≈$31**.
  - **Cap $35** covers the first run only. A result in (0.01, 0.05] then STOPS: a replication
    (≈$31) would not fit.
  - **$70** fits a replication in the same approval.
- **The post-run audit, pre-registered with it:** M-GAP's precision on gap-test output.
  - Code blind, mixed across arms, every CAND unit M-GAP flags plus an equal random sample of
    unflagged CAND gap-subject units, by the same taxonomy, before the score is read.
  - If its precision there falls below 0.80, the result is reported as unproven rather than read as
    a pass or a block.

**BOUNDARY.**
- **Gold:** the 221 units above, #926's 60 draws, `units.draw_units` at `fc79a7be`, both arms; the
  `key_unknowns` and `bear_points` fields; SUBJECT by the fix 4a selector plus RANDOM 60 of 638.
- **Halves:** DEV = CNXC, LLY, MCK (121 units, 34 errors); TEST = BURL, ROST, SMPL (100 units,
  17 errors).
- **Gap types:** #927 at `601d2f7e`, the panel's freeze pages (`bcda7ce3`), with FIX_3A, each page's
  own comps export, the primary checkout's CIQ root read only.
- **M-GAP:** `metrics.py` sha256 `80e5357f…`.
- **Intervals:** Wilson 95% for precision and recall; a bootstrap of units for kappa (seed as
  above).
- **M-LABEL:** the scorer on main `138436c7`, the same 221 units, the pages at the freeze.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0.
- **Accepted, with its falsifier: the gold is one model's coding,** kappa 1.000 between two
  instances. Falsified if a human-coded sample of the same units disagrees with the gold's `error`
  on more than 10% of them.
- **Accepted:** M-GAP is untested on gap-test output and on bear points, and has never met a
  type-4 page (§5). The audit in §7 is the check.
