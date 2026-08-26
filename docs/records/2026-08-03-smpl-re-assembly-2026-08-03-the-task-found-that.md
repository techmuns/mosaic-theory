---
id: 
status: recorded
date: 2026-08-03
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**SMPL RE-ASSEMBLY — 2026-08-03. THE TASK FOUND THAT ITS OWN ACCEPTANCE GUARD HAD NEVER FIRED.**
**19c WAS ORDERED BEFORE ITS OWN INPUT.** `uncited_material_figures` ran at `assemble.py:433` while
`_mark_material` — which sets the `material=True` flags the guard FILTERS ON — ran at `:450`. So it
read a table with ZERO material rows, found nothing, and returned `[]` on every build since it
shipped (`315bfe7`, 2026-07-30). MEASURED, not inferred: at the old position SMPL's table has **0**
material rows and the guard returns `[]`; after `_mark_material` it has **1** and returns
`Asset Writedown ($M) LTM = -391.9`.
**ITS UNIT PINS PASSED THROUGHOUT BECAUSE THEY CONSTRUCT ROWS WITH `material=True`** — the fixture
supplied the exact state production never reached. That is the sharpest form of the ladder the
operator named: *defined-never-called → declared-never-read → called-never-fires →
imported-never-called → called-result-discarded* — and now **ordered-before-its-input**, which sits
under all of them because the call happens, the result is used, and the INPUT is empty.
**THIS CORRECTS #317, WHICH I RECORDED WRONGLY.** I reported that SMPL's committed page "violates a
shipped fail-loud guard" and that "current code cannot reproduce SMPL's committed page." Both false:
current code reproduces it EXACTLY, because the guard could not fire. The first re-assembly today
converged on attempt 1 and wrote a page still omitting −391.9 — the proof.
**FIXED** (guard moved after `_mark_material`) and pinned twice: an AST ordering check, plus a
behavioural pin driven off the COMMITTED artifact rather than a constructed row — because a
constructed row is precisely what hid it.

**AND WITH THE GUARD LIVE, SMPL CANNOT BE ASSEMBLED. 5 rerolls, 5 refusals, and the pattern is a
DIAGNOSIS rather than bad luck:**
· attempt 1 cited −391.9, missed −60.9 · 2 cited −60.9, missed −391.9 · 3 cited −60.9, missed −391.9
· 4 cited −391.9, missed −60.9 · 5 cited −60.9, missed −391.9. **NON-CONVERGENT.**
**EACH ROLL STATES EXACTLY ONE OF THE TWO.** Not a missing input: both values appear in the mech
dump the LLM receives. Not a matcher defect: `_figure_cited` accepts `$60.9M`, `60.9 million`,
`$61M` and rejects the false `$1,392M of revenue`.
**THE CAUSE IS THE GUARD'S KEYING, AND ITS OWN DOCSTRING NAMES THE SHAPE IT WAS DESIGNED FOR:**
*"a charge commonly repeats across columns — CNXC's −1,523.3 appears in both FY25 and LTM — and
citing it once satisfies the reader for both."* **CNXC's two material cells hold the SAME value**, so
one citation covers both. **SMPL's hold TWO DIFFERENT values for ONE event** —
`LTM 391.9 = YTD FY26 331.0 + FY25 Q4 60.9`, a period total and its own component — so value-keying
turns one event into two independent demands that natural prose does not satisfy.
**BLAST RADIUS MEASURED: 1 of 11.** Only SMPL and CNXC carry material rows; CNXC passes. The other
nine have no material row, so the guard demands nothing.
**AND THE COMMITTED PAGE FAILS THE SAME GUARD**, so SMPL is now blocked in both directions: it
cannot be re-assembled, and its current artifact would not pass. **THIS IS A GUARD-DESIGN DECISION
FOR THE OPERATOR, NOT A BUILD** — per-VALUE keying vs per-ROW (satisfied by citing any figure on a
material row). Recorded, not chosen.

**RESOLVED 2026-08-03 — OPERATOR RULING: KEY ON THE LARGEST VALUE IN THE ROW.** Not per-VALUE
(unsatisfiable, as five rolls showed); not per-ROW (satisfied by citing $60.9M beside a row showing
−392, which IS the original audit defect). **The asymmetry is the reason:** citing 60.9 without
391.9 understates the charge by 6.4×; citing 391.9 without 60.9 misleads nobody, because the
component is contained in the total. **The original defect is the acceptance pin** — a synthesis
citing only −60.9 must still refuse, on a FROZEN fixture (the committed artifact now passes, so it
cannot carry the pin). Six pins added; three alternative keyings (per-VALUE, per-ROW,
smallest-value) mutation-checked and **all CAUGHT**.

**AMENDED THE SAME DAY, ON REVIEW — AND THE OPERATOR'S OBJECTION IS THE INTERESTING PART.** I had
recorded a KNOWN LIMIT and shipped it as an accepted pass: a row whose LARGEST value is old and
whose RECENT value is small demands the stale event and stays silent on the current one, with a
test (`test_the_known_limit_is_a_limit_not_a_bug`) codifying exactly that. **The containment
argument that justified largest-only — "60.9 is a COMPONENT of 391.9" — is a fact about SMPL, not a
fact the ROW carries, while `max()` applies to every row.** Two UNRELATED impairments in different
periods (an old $500M, a current $25M) break it, and **a materiality guard is the one place a known
hole must not ship as accepted risk.** RULING: demand the LARGEST material value **and** the LATEST
ACTUAL one. **Satisfiability survives because the demand is keyed by VALUE, not by cell** — where
the largest figure IS the latest, the two collapse into one citation, which is the entire live
corpus (SMPL −391.9, CNXC −1,523.3). **Measured after the amendment: 0 of 11 refuse**, so it costs
nothing today and refuses precisely the shape that motivated it; no re-assembly needed.
**Largest-only is now itself a mutation the suite CATCHES** (4/4 caught: largest-only, latest-only,
per-VALUE, smallest-value). **The "latest actual = last non-forecast column" assumption is pinned
structurally rather than commented** — `test_actual_columns_precede_estimate_columns` asserts every
committed summary's `is_estimate` mask is non-decreasing across the corpus.
**THE GENERAL LESSON, and it is the session's shape again: a rule was justified by a relationship
that was TRUE OF THE EXAMPLE and ABSENT FROM THE DATA.** Face validity on one name is not face
validity on the corpus — the check is whether the DATA carries the relation the rule assumes, not
whether the relation happens to hold where you looked.
**RE-MEASURED AFTER THE FIX, on the eleven committed artifacts: still 1 of 11 — SMPL alone,
demanding −391.9.** Nothing new refuses; the change can only shrink the demand and did.
**SMPL THEN CONVERGED ON ATTEMPT 1** (bound was 5). The non-convergence above was a property of the
keying, not of the name — the same brief that failed five times in a row passed first try once the
guard stopped demanding a total AND its own component. **The new bear point states the figure the
old one omitted:** old *"impairments on acquired brand assets"* — no number at all; new *"GAAP
results turned deeply negative on a $391.9M asset writedown (Atkins/OWYN impairment), driving LTM
net income to −$199M"*. That single sentence is what the whole guard was for.
**THE GAP DID NOT MOVE:** `0.9839 / 0.9463 / 2.2589 / 2.1032`, shape `multiple-dominant` at both
FY2026 and FY2027 — identical across a fresh synthesis, as it must be, since no gap input is
LLM-written.
**AND THE BLIND SYNTHESIS MATCHES THE SHAPE WITHOUT BEING TOLD IT** — bear[2] reaches
`multiple-dominant` in prose (*the multiple collapsed alongside collapsing forward EBITDA*, trailing
5.3x at the 0th percentile of its own 8.5-year range) and bull[8] poses the same leg as the
question (NTM TEV/EBITDA 5.65 vs peer 8.72 — *residual overshoot rather than earned*). **The one
TENSION worth carrying:** the synthesis's decisive_question litigates the EARNINGS base (*does the
takeaway decline permanently reset it*), while the arithmetic says our revenue and margin
assumptions sit within 2% and 5% of the street's — the entire 2.10x rides on the exit multiple
being 2.26× the street's. Not a contradiction; the decisive question is aimed at the leg where we
and the market AGREE. That is exactly the cross-check A2 was built to expose, and it is the first
time it has been run against a synthesis that could not see the answer.

**AND A METHOD DEFECT IN MY OWN MEASUREMENT HARNESS, worth the same rung as the rest.** The
mutation harness rewrote `synthesis.py`, ran pytest, then restored the source and asserted
`reverted: True` — **comparing SOURCE while Python executed BYTECODE.** The final revert left a
`__pycache__` entry from the smallest-value mutation, and the next six test runs loaded it: the
suite reported 6 failures against code that was not in the tree, and the debug output
(`FY25 = -60.9`) was precisely `min(seen, key=abs)`. **The first across-eleven measurement was taken
under that stale bytecode and has been re-run clean** (same answer, 1 of 11 — but that was luck, not
method). `bin/commit` already clears `__pycache__`, so the shipped gate was never exposed; the
exposure is ad-hoc harnesses only. **Standing rule: a harness that mutates source clears
`__pycache__` on revert — otherwise "reverted" is source-true and execution-false.** Same class as
the tree-vs-index defect: verified one artifact, executed another.

**TWO SMALLER FINDINGS FROM THE SAME RUN.**
(1) **`vinci dossier` EXITS 0 ON A PER-NAME FAILURE** — correct for a batch (one bad name should not
fail ten), and my first reroll harness read exit 0 as convergence and stopped after a single refused
build. The signal is the `N done · M error(s)` report, not the exit status. D16's shape in a harness.
(2) **ASSEMBLY DID NOT MIRROR, DEMONSTRATED LIVE.** The 15:44 re-assembly wrote
`data/dossiers/SMPL/` while `frontend/dossiers/SMPL.md` stayed the older page — FUBO's
missing-banner shape, reproduced by accident. `mirror_to_frontend()` is now called from the dossier
CLI too, **gated on `if dossiers:`** so a refused run cannot republish the old page as fresh.

**THE SYNTHESIS IS BLIND TO `ev_gap`, AND ONLY STATEMENT ORDER PROTECTED IT.** `synthesize` dumps
the WHOLE mechanical layer to the LLM (`model_dump(exclude={"primary_source"})`), so a transform
moved above it would feed `shape: multiple-dominant` straight into the prose — and the A2 comparison
would silently become a test of whether the model can copy. Pinned: the gap is computed AFTER the
synthesis, the premise (whole-mech dump) is asserted so the ordering pin cannot read as arbitrary,
and no committed synthesis may use the shape vocabulary.

**THE GAP DID NOT MOVE, as predicted:** `0.9839 / 0.9463 / 2.2589 / 2.1032` identical across the
re-assembly — TEV is struck from the comps cap, not `price × shares`. **`tev_as_of` moved
2026-07-24 → 2026-07-23 and that is a CORRECTION, not an input change:** the old artifact's
`source_ref` carries the pre-correction format (`as-of 2026-07-24`), i.e. the EXPORT stamp used as
the data date; the new one resolves to the last actual data bar. `comps_as_of` still reads
2026-07-24 and no workbook was re-exported.

**THE 15:44 ROLL IS THE DEFECT VERBATIM, WHICH VALIDATES THE GUARD EVEN THOUGH IT CANNOT BE MET.**
Its bear point [4]: *"a $60.9M Atkins impairment (FY25) followed by further OWYN/Atkins brand-asset
writedowns driving a -$199M LTM net loss"* — the LTM figure described QUALITATIVELY and never
stated. That is the 2026-07-30 shape the guard's own docstring cites, reproduced on a fresh roll.
The guard is RIGHT to refuse it; it simply demands a second figure the prose will not carry.
**ARTIFACT DECISION: SMPL RESTORED TO `origin/main`.** The 15:44 build was produced while the guard
was blind and the live guard refuses it; committing it would ship a page the code rejects. This
branch carries the CODE FIX AND PINS ONLY — no artifact moved.

**AND THE ANSWER TO THE QUESTION THE RE-ASSEMBLY WAS RUN FOR: THE BLIND SYNTHESIS *MATCHES*
`multiple-dominant`.** Written with no sight of `ev_gap` (pinned), the fresh roll argues:
· bull [0] — *"the de-rate is idiosyncratic and violent — SMPL fell -59% over 12 months while its
  small-cap benchmark rose +36% … not a slow-bleed secular fade"*
· bull [1] — *"absolute EBITDA … rose from $67M (FY17) to a $262M FY25 peak and sits at $217M LTM,
  so the headline 'margin compression' is a level that remains near record scale, not a collapse"*
**Together those are the multiple-dominant case in prose: the price fell while the earnings did
not.** The arithmetic says the same thing — `revenue 0.98 × margin 0.95 × multiple 2.26` — with the
gap concentrated entirely in the multiple. **The audit's original conclusion, reproduced
independently by a synthesis that could not see it.** That is the strongest evidence to date that
the decomposition is measuring something real rather than restating its own inputs.
