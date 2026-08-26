---
id: 
status: recorded
date: 2026-07-27
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md governance log
---

3. **The CIQ figures demonstrably exclude the WRITEDOWN** — CIQ LTM EBITDA is +217 on 1,392 revenue
   while trailing GAAP operating income is negative, since the −$391.9M sits inside GAAP operating
   income. That is evidence about the writedown SPECIFICALLY. It is **not** evidence of "clean" in
   the ex-all-unusuals sense the page claims.

**A COINCIDENCE NAMED SO IT CANNOT BECOME PROVENANCE (the `13.837177` lesson, and this one is
sharper): FY2019's operating margin is 13.875% — 0.075pp from "about 13.8%", CLOSER than the
trailing candidate at 0.093pp.** A numeric-proximity argument would therefore pick FY2019 — a
fiscal year seven years back, which flatly contradicts *"trailing … through the third quarter"*.
**The number matched and the description did not.** Listed as a decoy, never as a candidate.

**RE-STRIKING THE MARGIN IS A DECISION-PATH CHANGE — flagged, not done.** `scenarios.py:752–754`:
`reward = base − spot` and `ratio = reward / risk` are computed from `per["base"].value_per_share`,
which the base margin sets. Moving it moves reward:risk and therefore the 2:1 bar. **That needs a
real shown run before merge, not a records fix.**

**CORRECTION TO MY OWN EARLIER FRAMING, per the operator:** the thirty-point GAAP-vs-CIQ spread is
evidence the two SOURCES differ in basis — **not** the range of plausible normalized margins, and
trailing GAAP-with-the-writedown is **context, not a candidate basis** for a normalized margin. On
the base target the candidates give ~$25.46 (13.89%) and ~$28.51 (15.51%) against the current
$25.67 — about 12%, with 14% near the conservative end. **So "takes the flattering side" does not
hold, and it is withdrawn. The defect is that the derivation is UNSTATED, not that it is aggressive.**

**THE RULING AS ORIGINALLY POSED (kept for the reasoning):**
- **§D — SOURCING FIRST.** *"Bind ~13.8% to a source or declare it unfindable. Only once it's bound
  is the basis mine to choose."* The `own_history[0].implied_ebit_margin = 0.138933` candidate is a
  0.06pp match that nothing binds, and **whether CIQ's EBIT definition excludes unusuals is asserted
  nowhere in this repo** — the page says clean, the code never does. The basis choice is DEFERRED
  behind the binding, not taken.
- **TWINS — the set is a CONCLUSION, not a proposal.** Analyst-committed list in the scenario
  record, verification persisted alongside it. **Interim:** mark the block LLM-proposed and unstable
  between builds. (The instability is measured, not asserted — `e.l.f. Beauty` re-entered and
  `Utz Brands` left on the 2026-08-03 re-assembly with nothing about SMPL changing.)
- **CIRCANA — label it management-cited.** *"A CEO citing a third party on a call is real and is not
  that party's data."* N1's finding rests on it, so provenance carries weight.

**AND THE SEARCH LESSON, recorded with them because it is now the SECOND instance.** Chasing §D I
grepped the literal `13.8` and concluded no field computed it — while the margin-valued field sat in
`own_history` under a different name (`implied_ebit_margin`). **Searched for the LABEL, not the
OBJECT.** First instance was #317, where `N1` collided with an unrelated concession-clause note and
`CHRO` returned twelve substring hits and zero real ones. The rule that falls out: **when a search
for a name comes back empty, search for the VALUE or the SHAPE before concluding absence** — repo
vocabulary is idiosyncratic and the object is often present under a name you did not guess.

**THE THREE RULINGS AS ORIGINALLY POSED (kept for the reasoning, superseded by the block above):**
- **§D — the base-margin anchor's basis. SOURCING IS THE FIRST PART OF THE RULING, NOT A RIDER.** The
  interpolation runs from **15.51%**, computed and cited (`[53]`, EDGAR `OperatingIncomeLoss`, GAAP
  inclusive of every unusual but the one named impairment) to **~13.8%**, which appears ONCE in METHOD
  prose with **no endnote and no field**. **The 13.8% end's basis is UNKNOWN** — the nearest match is
  `own_history[0].implied_ebit_margin = 0.138933` (`TEV/LTM Revenue ÷ TEV/LTM EBIT` off the CIQ
  Multiples sheet, as-of 2026-07-23), a **0.06pp** match that nothing binds, and whether CIQ's EBIT
  definition is ex-unusuals is asserted nowhere in this repo. The page says "clean"; the code never
  does. DECIDE IN ORDER: (1) establish what ~13.8% is and bind it to a `source_ref`, or retire it;
  (2) then which basis defines the anchor — this cannot be decided before (1); (3) then code enforces.
  **The size of the choice IS established:** on the same trailing period GAAP operating margin is
  NEGATIVE (the −$391.9M writedown sits inside it; LTM net income −$199M) against a CIQ-implied
  +13.89% — the basis moves the trailing anchor by ~30 points, and the derivation takes the flattering
  side without naming which side it is on.
  *(Corrected on review of #327: the first cut called 13.8% an "analyst-written CIQ-basis figure" —
  restating the AUDIT's claim as a measurement immediately after proving the artifact carries no such
  link, which pre-biases a ruling that asks the operator to choose between those very bases.)*
- **Twins — the mechanism, not the two names.** DECIDE: does a verified outcome become a FIELD that
  travels with the twin (making the set partly sticky), or does the twin block stop carrying outcome
  claims at all? Current state is neither, and it launders an LLM claim and a human verification into
  the same rendered sentence.
- **Circana (narrow, and it governs N1 rather than itself).** May a management-sourced,
  un-independently-verified figure carry a thesis leg? The page now ATTRIBUTES rather than asserts
  ("Management frames the problem as execution-driven within a growing category — purposeful nutrition
  grew 10% …"), which was the audit's actual complaint; the +10% is load-bearing for N1's whole argument.

**R3 IS FIXED (2026-08-04) — and the module carried a SECOND instance, exactly as predicted.**
`_capital_summary` now derives both period labels from the columns' own headers instead of asserting
constants: the term-loan step reads `(FY 2024 (12 months) 131.3 → FY 2025 (12 months) 215.2)` and the
total is stamped with the column it was read from. **The second instance was `(latest quarter)` on
total debt — in the SAME function, fifteen lines from the `QoQ` constant, and PROPAGATED TWICE into
`render.py`** (the fact label at `:1177`, and a reconciliation note at `:951` that *instructed the
reader to "read the QoQ movement"*). All four are gone; no frequency is asserted that was not read
out of a header. Both reversions mutation-checked, **both CAUGHT**.
**THE SIBLING PIN DEMANDED THE DEFECT.** `test_dossier.py` asserted `"131.3→215.2 QoQ"` and
`"total debt 326.0 (latest quarter)"` against a fixture whose own headers read
**`"FY 2024 (12 months)"` / `"FY 2025 (12 months)"`** — two ANNUAL columns. The pin encoded the bug
as expected behaviour, so no re-run could ever have surfaced it. Inverted, plus a dedicated pin
carrying the observed failure shape and both polarities (annual AND quarterly).
**THE SHAPE, which is the reusable part:** the ordering guard in this function refuses to stamp
"(latest quarter)" on an unasserted column ORDER — and fifteen lines later the code asserted a
FREQUENCY it had never checked. **The guard checked the ORDER premise and never the PERIOD premise.**
**THE RENDER HALF LANDED ON ALL ELEVEN PAGES; THE VALUE HALF LAGS BY DESIGN.** A no-LLM
`refresh_fleet()` re-rendered every page, so the fact label and the reconciliation note are fixed in
the committed artifacts now. **SMPL's `(249.1→397.0 QoQ)` inside the VALUE string does not clear
until a re-assembly** — that string is produced from the CIQ bundle at assembly time. Not done here:
re-assembly re-rolls the synthesis, which had just converged and been reviewed, and nobody asked for
that. **Stated rather than quietly carried; it clears on the next scheduled assembly.**

**AND THE RENDER CHANGE EXPOSED A PERMANENT-RED SEAL — closed in the same PR because it had no path
to green.** The repo's own render-drift pin demands every committed `dossier.md` match the current
renderer. **FUBO is sealed by `known_wrong.json`, and `refresh_dossier` refused it outright — so the
one name that CANNOT re-assemble was unreachable by every writer**, and the R3 fix turned that pin
red on it with no remedy. Read the refusal's own words and the fix is obvious: the seal exists so a
page saying *"do not trust these figures"* cannot be made to **look freshly computed** — which a
pure re-render does not do. **Now: a sealed record RE-RENDERS its page and its `dossier.json` is
never written** (verified byte-identical, banner intact); a `transform` — an actual data refresh —
still RAISES. Pinned both polarities, and both mutations CAUGHT (seal broken / re-render inert).
**The shape: a guard whose only satisfying action was impossible for the name it guarded.**

**AND THE FIX RE-CREATED THE DEFECT IT SERVED — caught on review, one layer down.** The seal DECISION
is PATH-relative (`path.parent/known_wrong.json`); the banner RENDER was CONFIG-relative
(`_known_wrong_lines` defaulted to `get_config().data_dir/dossiers`) because `render_markdown` had
no root at all. **Two sources of truth for one fact.** Re-rendering a sealed dossier in another
checkout, a staging tree or a temp copy would decide *sealed* from the sidecar beside it and then
render the banner from somewhere else — **dropping it when the configured tree has no marker for
that ticker, or pasting an UNRELATED name's marker onto the page.** That is the FUBO defect exactly
(banner present in one artifact, absent from the one served), re-created by the fix meant to serve
it. `render_markdown` now takes `dossiers_root` and every writer passes the root it is writing into
(assemble, the midcycle CLI writer, both refresh paths). *(`cli.py`'s peek builds its path from
config itself, so it is unambiguous and unchanged.)*
**AND MY PIN MASKED IT, for the reason the operator named:** it copied FUBO to a temp dir and
asserted nothing about the banner — the render read the CONFIGURED tree, which holds FUBO's real
marker, so the page looked right for a reason unrelated to the isolated copy. Now the isolated
sidecar carries a SENTINEL string that exists nowhere else, so a config-tree read cannot satisfy it.
**Both mutations CAUGHT, including the reported bug itself** (render ignores the passed root).
**The lesson is the session's recurring one in a new place: a test whose subject and whose oracle
come from different trees proves nothing about either.**

**RIDER DECLINED AS NOT-A-LINE, with the blocker named (operator condition: "if it's a line").**
Marking SMPL's base margin as an unsourced derivation has the right home already — `AxisNote`
(`scenarios.py:230`), *"a dated analyst FINDING about one assumption axis"*, which exists BECAUSE of
the SMPL 2026-07-26 boundary-cells finding. But it needs three things, not one: **(1)** the scenario
record, which lives in the working SQLite DB — `*.db` is git-ignored (`.gitignore:16`) and no
database exists in this worktree, so the change cannot be written, committed, or proven by a real
run here; **(2)** an authoring path — `AxisNote` has **no CLI surface and no writer anywhere in
`vinci/`**, only the schema field and its render; **(3)** an analyst act, since by its own docstring
the note is a human finding. Proposed, not built, per *don't build speculatively*. **OPERATOR
ACTION:** author the note on SMPL's margin axis once (1) and (2) exist — text to the effect that the
derivation interpolates between a cited GAAP anchor (15.51%, `[53]`) and a trailing figure whose
basis and source are UNKNOWN, and that every per-share number descends from it.

**THE ORIGINAL QUEUED FIX (now shipped) — R3's surviving instruction.**
`md:400` still reads `term loans 397.0 (249.1→397.0 QoQ)`. `ciq_sheets.py:747` opens
`Capital Structure Summary` with **`freq="annual"`**, then `:778–779` compares two adjacent ANNUAL
columns and hard-codes the string `QoQ` — the printed move spans ~three quarters and a fiscal-year
boundary (term loans were 396.7 → 396.9 → 397.0, flat, across the real quarters). **The correct label
is already computed and discarded:** `_cs_col_date` parses each column's date at `:764`, uses it only
for the ascending-order refusal, and throws it away. *Called-result-discarded*, sitting directly below
a comment that refuses to stamp "(latest quarter)" on an unasserted convention — the function declines
a provenance it cannot prove, then asserts a frequency it cannot prove, fifteen lines later. FIX: name
the two periods instead of asserting a frequency.

**WATCH ITEM — 19c's amended rule is behaviour-pinned but NOT satisfiability-pinned (2026-08-03).**
The amended guard demands the largest material figure AND the latest actual one. **0 of 11 refuse today
only because those two coincide on every live row** (SMPL −391.9, CNXC −1,523.3), so the DIVERGENT case
— where they differ and the rule demands TWO citations — has never been exercised against a real LLM.
Mutation tests pin the BEHAVIOUR (4/4 caught); nothing pins SATISFIABILITY, and SMPL's five consecutive
refusals are the standing proof that a rule satisfiable in theory can be unsatisfiable in practice.
Falsifier: the first name whose material row has a stale largest value and a distinct current one. If it
cannot converge within the reroll bound, the demand — not the roll — is what to revisit.
