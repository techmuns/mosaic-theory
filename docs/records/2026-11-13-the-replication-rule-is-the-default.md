---
status: shipped
date: 2026-11-13
prs: [1048]
supersedes:
superseded-by:
---

# The panel harness's replication rule is the default for a new registration with a target, at ship alpha 0.01, the value fix 3a and fix 4a registered; `--single-run` opts out and is stated in the registration and printed; a registration written before it reads as it was written (STATE row 53 item (7), coordinator default 3 under the operator's delegation, not an operator ruling)

**WHAT.**
- **The authority.** This builds default 3 of
  `docs/records/2026-11-12-operator-delegation-and-defaults.md`: *the replication rule becomes
  the default (today `register --ship-alpha` is opt-in)*. It is a default the coordinator adopted
  under the operator's delegation, not an operator ruling, and the operator can reverse it. That
  record names S1 as its builder after order 8. Order 8 (#1030) merged on 2026-11-13 and S1 is
  paused, so A built it.
- **The default.** `compare.register` with a target now registers the replication rule at
  `compare.SHIP_ALPHA` = **0.01** against alpha 0.05, unless it is given another `ship_alpha`.
  A first run ships at p_lower ≤ 0.01 after Holm. In (0.01, 0.05] its score decides "replication
  required", and it counts only if a registered replication of the same design reaches
  p_lower ≤ 0.05. Above 0.05 it does not ship. The scoring code is unchanged: it already applied
  this rule whenever a registration carried `ship_alpha`. What changed is that a target
  registration now carries `ship_alpha` without being asked.
- **The opt-out.** `register --single-run` (library: `single_run=True`) registers a target decided
  by one run at alpha. It is stated in the registration as `"single_run": true`, so it is in the
  sha, and `register` prints it ("SINGLE RUN (--single-run, stated in the registration) …").
  `--single-run` and `--ship-alpha` are mutually exclusive in the parser. A single run with a ship
  alpha is refused by `register` and by `Registration` itself, and so is a single run with no
  target or a replication of one.
- **Printed.** `register` now prints the rule it registered: the replication rule with its two
  bounds, a single run, a replication of a named first run, or no-worsening only.
- **What does not move.**
  - A no-worsening-only registration has no target. The default never reaches it, and it is
    written with the same keys as before. Six of the eight paid panel runs since 2026-11-07 had
    that shape.
  - A registration written before the default has no `ship_alpha` key and reads as it was
    written. The default lives in `register`, never in the field: `Registration.ship_alpha` still
    defaults to None, so an old target registration is still the single run it was registered as.
  - `single_run` is written only when true (`_LATER_FIELDS`), and it is not a design field. A
    single run is decided exactly as a target registered before the default, so the two are one
    design and are drawn once. No design key written before this change moves.
  - `register-run` (`builds.py`, the independence measurement) and the judge have no target rule
    and are untouched.

**WHY.**
- **The value is VERIFIED AT BUILD from the records, never from an outcome.** Every target
  registration under the rule used 0.01:
  - fix 3a's `cceba9d9…` (`docs/records/2026-11-07-fix3a-measured-on-the-panel.md` §2: "alpha
    0.05 and ship alpha **0.01**");
  - fix 4a's `06ed949b…` (`docs/records/2026-11-09-fix4a-measured-on-the-panel.md` §2: "alpha
    0.05, ship alpha **0.01** (the replication rule)");
  - RUNBOOKS §n named `register --ship-alpha 0.01`;
  - #930's §5 proposed `--ship-alpha 0.01` for fix 3b. The coordinator struck it before any draw,
    because the run was no-worsening only
    (`docs/records/2026-11-09-fix3b-measured-on-the-panel.md` §2).

  No registration under the rule used any other value. The two registration files themselves
  are on the machine that drew them and were not read here. The value is the one their records
  state.
- **Where 0.01 came from.** PR 2's A/A reading proposed it before any run under the rule
  (`docs/records/2026-11-06-synthesis-eval-pr2-baseline-921-judge.md` §5). An A/A page set
  "improved" M-LABEL at p 0.024 with no change, and that was the smallest of eight one-sided p
  values. The record proposed "pre-register a replication (a second five-draw pair) for any
  decisive result with 0.01 < p ≤ 0.05, rather than a blanket α = 0.01". A blanket 0.01 would
  also blunt the no-worsening check. The coordinator ruled the rule on 2026-11-07, before fix 3a's
  draw. That is a null measurement and a face-validity argument about multiplicity. It reads no
  forward return and no result of the change under test.
- **The method.** The coordinator's source for default 3 is Evan Miller, *Adding Error Bars to
  Evals*, arXiv 2411.00640. The delegation record reads it as evals run as experiments with
  stated error and decided by a pre-registered rule. This change makes that rule the starting
  point of every target registration. It does not derive a number from the paper.
- **Why a default, and why a stated opt-out.** Opt-in meant a target registered without the flag
  was decided on one run at 0.05, the multiplicity PR 2's A/A run showed. Opting out is still
  possible: the rule's cost (below) may be unjustified for a cheap target. But the opt-out is
  written into the registration's sha before the draw, so a single run is a decision made in
  advance, not an omission.

**HOW VERIFIED.**
- **`tests/test_evals_replication_default.py` (18 tests).** 9 fail on main `98707f29`'s code (its
  `vinci/evals/compare.py` and `__main__.py` swapped in), for six reasons:
  - `SHIP_ALPHA` is absent;
  - `register` returns `ship_alpha` None;
  - the CLI writes no `ship_alpha` and prints no rule (two tests);
  - `--single-run` and `single_run` are unknown (three tests);
  - a default registration's band run decides "ships";
  - the end-to-end test's first registration reads `None == 0.01`.

  The other 9 pass on main as well as on this branch. They are the regression pins: four
  registrations as main wrote them read back byte for byte; the provenance check; an old target
  registration in the band still ships; a no-worsening registration keeps its keys; and the
  default's ship and fail bands.
- **End to end, through the CLI, at $0.** The paid client is spied: production's
  `AnthropicLlmClient`, built with no key, its SDK answering each draw with a queued synthesis
  from NFLX's committed one. The index lives in a temporary repository, and this repository's own
  index is checked unchanged.
  1. `register --from-impact … --target M-LABEL` (no rule flag) writes ship alpha 0.01 and prints
     the rule. Its row merges to the temporary main, and `run-compare --paid` draws it: two
     clients, 10 draws. `score` decides "replication required" at p_lower 6/252 = 0.024.
  2. The same design registered again under a second approval, with new words and no
     `--replicates`, is refused before any client is built ("design was already drawn").
  3. `register --replicates first.json` registers the replication on the first run's own request
     pins. `run-compare` draws it under the F3 exemption (operator 2026-11-12, "Refuse by request
     pins": "A replication under the replication rule stays allowed"), at p_lower 1/252, and
     `score` decides "replicated: ships". The index holds exactly two `drawn` rows, the first run's
     and the replication's.
- **The test helper's draw count.** Order 8's `_impact_export` captures each request at one draw.
  A real export carries one of its run's five identical calls, `cache_control` included (the
  session notes' `impact-captures-format.md`, and `vinci/impact/child.py`'s
  `draws=SYNTHESIS_DRAWS`). Drawn five times, the helper's request trips the guard ("the request
  differs from the one captured at $0"). The end-to-end test re-captures each arm at five draws,
  as the real export does. Order 8's tests never reached a draw, so they never met this. It is
  not a harness defect.
- **Mutants.** 17 mutants of this change, each run against the new module with every file
  restored by sha256 after it: **17 of 17 killed** (§BOUNDARY). They are:
  - the default set to None, its condition flipped, or never applied;
  - the default moved onto the field, so old files read 0.01;
  - the ship band tested at alpha;
  - Holm's comparison flipped;
  - the ship and replicate bands swapped;
  - `first_run_rule` flipped;
  - `single_run` never written, or always written;
  - `single_run` made a design field;
  - `register` or the CLI dropping it;
  - each refusal removed;
  - the rule not printed, or the single run printed as nothing.
- **Existing registrations do not move.**
  - `git show origin/main:docs/evals/registrations.jsonl` at `98707f29` holds one row, a
    `judge_test_read`, and no `registered` row, so no indexed registration can change sha or key.
  - The five real registration files on this machine are fix 3b (`4d6fe10e`), driver facts
    (`c04c4d3d`), RA-D2 (`b29121eb`), RA-D4 (`5bc72d2b`) and RA-D2+D4 (`dc9a6dad`), all
    no-worsening. Each reads to the same sha and the same design key at main and on this branch,
    and each round-trips byte for byte.
  - Their `inputs` carry a private path, so they stay out of git. The committed fixture
    `tests/fixtures/evals_registrations_before_the_default.json` was written by main's own
    `Registration.to_json` at `98707f29`. It holds fix 3b's real fields, with the root path and
    file names replaced, and three derived shapes: a target with no ship alpha, the rule at 0.01
    with a `scorer_ref`, and a replication.

**BOUNDARY.**
- **18 tests**: `tests/test_evals_replication_default.py`, run with main `98707f29`'s two harness
  files swapped in (9 failed, 9 passed) and on this branch (18 passed).
- **Five real registrations**: every `registration-*.json` under the `synthesis-eval-*` folders
  of the session notes folder on the operator's Mac, read 2026-11-13, at `98707f29` and on this
  branch.
- **17 mutants**: the list in HOW VERIFIED, each run against `tests/test_evals_replication_default.py`
  alone (`-x`).
- **"Six of the eight paid panel runs since 2026-11-07"**: the eight records named
  `docs/records/2026-11-*-measured-on-the-panel.md`, 2026-11-07 to 2026-11-11. Fix 3a and fix 4a
  registered a target under the rule. Fix 3b, driver facts, RA-D2, RA-D4, RA-D2+D4 (#967) and
  RE2-D16 were no-worsening. PR 2's runs (2026-11-06) predate the rule, and the guidance reader's
  check was refused at $0. RE2-D16's registration file is not on this machine, so the real-file
  check reads five of the six.
- **The ~$30 cost** is fix 3a's own estimate of a replication ("about $30", its §3), in US
  dollars.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A target run in (0.01, 0.05] now costs a second paid draw, or a STOP.** RUNBOOKS §n: "If the
  replication will not fit in what the approval has left, STOP and report — never raise the cap".
  About $30 on the six-page panel, per fix 3a's record. The two target runs so far landed far
  below 0.01 (7.5 × 10⁻⁵ and 2.6 × 10⁻¹¹), so neither would have needed one.
- **The opt-out is a choice.** A registration may still state `--single-run`, and the
  registration and its print say so. Whether a single run is right for a given target is the
  approver's call when they approve the cap.
- **Reversible.** If the operator reverses default 3, this PR is reverted or amended and a new
  record says so.
