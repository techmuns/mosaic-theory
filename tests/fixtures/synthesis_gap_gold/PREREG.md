# M-GAP gold — population, sample and split, fixed BEFORE any unit is looked at (2026-11-09)

Operator 2026-11-09, verbatim: "Yes, grade first". Coordinator's brief: build a calibrated gap-framing
metric, M-GAP, so fix 4a (#927) can be measured fairly. $0; no paid call.

## Population
- #926's 60 stored draws: registration `cceba9d939692bfcb5a2c78d27cad778d92e032e3d873b1d28e1fb668e5b975e`,
  `synthesis-eval-fix3a/run-fix3a-first/draws.jsonl` (sha256 recorded when read), both arms.
- Units: `vinci.evals.units.draw_units` at fc79a7be (units.py unchanged on main 138436c7).
- Fields: `key_unknowns` and `bear_points` units only.
- A unit's id: `<TICKER>:<ARM>:<draw n>:<unit id>` (arm stripped before coding).

## Sample
- SUBJECT units: every unit whose text matches the fix 4a session's SUBJECT regex
  (`fix4a-gap-test.md`), verbatim, re.I:
  `segment[- _](?:level )?(?:ebitda|profit|operating|margin|breakout|breakdown)|ev_ebitda_adjusted_fwd|net_debt_to_ebitda_adjusted|adjusted_eps|(?:adjusted|company)[- ](?:forward|EBITDA|EPS)[^.;]{0,30}(?:guid|UNKNOWN|unavailable|not)|\bno [^.;]{0,30}guid\w*|revised[- ]guid\w*|revised outlook|current[_ ]guide|runway|fcf[_ ]sign|survival_capacity|opaque|opacity|undisclosed|not disclosed`
- RANDOM units: 60 of the remaining units of those two fields, drawn by
  `random.Random(SEED).sample(sorted(remaining_ids), 60)` with
  **SEED = int("cceba9d939692bfc", 16)** (the registration sha's first 16 hex digits).
- The gold is the union; a unit's stratum (SUBJECT / RANDOM) is recorded, and recall is reported per
  stratum, with the RANDOM stratum weighted by its sampling fraction.

## DEV / TEST split, by page (three each)
- Rank the panel's six pages by `sha256("cceba9d939692bfc:" + TICKER)` ascending; the first three
  are DEV, the other three TEST. Computed once and recorded below, before coding.
- M-GAP is designed on DEV only; TEST is scored ONCE, after its bar is written.

## The split, computed
- order: ['MCK', 'CNXC', 'LLY', 'BURL', 'SMPL', 'ROST']
- **DEV: ['CNXC', 'LLY', 'MCK']**
- **TEST: ['BURL', 'ROST', 'SMPL']**

## The sample, drawn
- draws.jsonl sha256 `08b20173430e1e72da8e9bd62d10716325a67aacf9634b84042132343b67a61a`
- units in key_unknowns + bear_points: 799; SUBJECT 161; remaining 638; RANDOM 60; gold 221
- the coders' file is shuffled with Random(SEED + 1), ids g000…, arm and draw stripped

## Before coding
- TAXONOMY.md sha256 `961db53a34d160d963fc18427c6b8952707b9414e11ce8e1b8e6490f76c67392`
- synthesis_gap_types.json sha256 `74f807b33125c76f571ac13d2ffb6caa0782d1ef71d47df169b3209c3cfe9525`

## M-GAP frozen, and its bar — written BEFORE TEST is read (2026-11-09T12:32:32+0530)
- M-GAP = `vinci/evals/metrics.py::gap_framing`, fit on DEV only (CNXC, LLY, MCK: 121 units, 34 gold
  errors; DEV tp 34, fp 2, fn 0). metrics.py sha256 `80e5357f9a1acf81628be80a0261fcc81904befc3c5e7e84488c0286f8459351`.
- The gold's `error`: coder A's codes (coder B agreed on `error` for all 221 units); `item` from the
  adjudicator where the coders differed (11 units; no `error` changed).
- **THE BAR, on TEST (BURL, ROST, SMPL; scored ONCE):** precision >= 0.80, recall >= 0.80, and Cohen's
  kappa between M-GAP and the gold's `error` >= 0.70 — all three point estimates. Reported beside them:
  Wilson 95% intervals for precision and recall, a 95% bootstrap interval for kappa (10,000 resamples of
  units, Random(SEED)), and recall per stratum (SUBJECT; RANDOM). With few gold errors on TEST the
  intervals are wide; they are reported, not gated.
- MET only if all three point estimates meet it; otherwise NOT MET, and M-GAP gates nothing.
