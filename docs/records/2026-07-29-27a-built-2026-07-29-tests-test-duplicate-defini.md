---
id: 
status: shipped
date: 2026-07-29
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**27a — BUILT 2026-07-29 (`tests/test_duplicate_definitions.py`). THE COUNT IS THIRTEEN, NOT TEN.**
The prototype's ten was measured before the tree grew; re-derived against current code the detector
finds **13** duplicated literal sets across the py↔JS twins, `_CS_COLS` among them. Baseline frozen
at those 13 → **the build fails on the FOURTEENTH**, zero curation required, exactly as the split
specified. Mutation-verified BOTH ways: a 14th duplicate reds the guard; a baseline entry whose
duplicate no longer exists reds the second test, so **the baseline can only ever SHRINK** —
otherwise it silently becomes a list of things that used to be true while the suite stays green
(the assertion-integrity class applied to the guard's own bookkeeping). 27b's curation count is
therefore 13, not 10.
**AND THE BASELINE ALMOST SHIPPED FABRICATED.** The first cut was hand-transcribed from truncated
prototype output that printed only the first five members of each set with an ellipsis — so four
entries carried INVENTED vocabulary that no file contains. It reddened immediately (the
still-exists test caught it), and the baseline is now GENERATED from the detector rather than
copied by eye. Transcribing from a truncated display is the same shape as rendering a truncated
sample: **the source was authoritative and the excerpt was not.**

27b. **CURATE THE TEN DOWN — as each is touched, NOT as a project (operator 2026-07-28).** Each hit
    needs a judgment: genuine shared definition (collapse to one import, or pin) vs short domain
    vocabulary used inline (`["bear","base","bull"]`, where a literal is legitimate).
    **`_CS_COLS` first regardless of what touches it** — `["Type","Principal","Coupon","Floating",
    "Maturity","Sec","Conv","Cur"]`, identically named with identical contents in `render.py` and
    `dossier.js`. Latent today; if those headers ever drift, the md and web dossiers show DIFFERENT
    capital-structure tables with nothing flagging it.
26. **SPLIT INTO 26a / 26b BY THE OPERATOR 2026-07-28 — "the freeze doesn't need the hard half".**
    The spec was corrected twice (both times correctly) with the pipeline frozen throughout, which
    is the signal that the freeze was paying for the item's difficulty rather than for the
    invariant. THE INVARIANT BEHIND THE FREEZE IS: *a reader can tell whether two dossiers are
    comparable.* **A declared version string satisfies that the day it ships**; the drift test only
    stops the string going stale later. So 26a unfreezes and 26b prevents rot.
    **SEPARABILITY — CHECKED, NOT ASSUMED (the operator asked to be told if they are not
    separable).** THEY ARE. 26a is a declared constant + one record field + its rendering, and
    needs NO module set — the question that made 26 hard belongs entirely to 26b. 26b adds a TEST
    and no field, so taking it later causes no churn in the record shape 26a ships. The residual
    risk of running on 26a alone is that someone changes extraction and forgets to bump the
    version — **which is exactly today's state, so it is not a regression**; it stops being a TOTAL
    freeze, which is the whole point.
26a. **DECLARED EXTRACTION VERSION, RENDERED — BUILT 2026-07-28; ~~PR OPEN, PREVIEW-GATED~~ MERGED (stale note corrected 2026-08-18: zero PRs are open and all 14 committed dossiers carry `2026-08-16.1`).**
    SHIPPED: `vinci/dossier/extraction_version.py` (an APPEND-ONLY changelog, last row current);
    `Dossier.extraction_version: str | None` (default None → pre-26a JSON round-trips);
    `assemble` stamps it; BOTH twins render it in BOTH tiers — the identifier beside the document
    date in the MAIN BODY, the gloss ("what this version names") in Record & reproduce.
    **THE OPERATOR'S SPEC POINT, IMPLEMENTED AS A FORCING FUNCTION.** *"The constant should declare
    WHICH STATE IT NAMES, not just be a number."* So the version is not a free-standing string: it
    is the last row of a table whose other column states the change, and a bump that names nothing
    is unrepresentable. v1 = `2026-07-28.1` — "unusual-items surfacing (#238) · multiples read from
    the latest close, NM rather than a stale figure (#241)": the two moves extraction has actually
    made, with no artifacts existing between them, so today is ONE vintage.
    **VERIFIED BY MUTATION, NOT BY GREEN.** Removing the md header stamp reds 2 tests; removing the
    audit row as well reds THE RED itself (two vintages then render identically — the #238 state
    reproduced on demand). Removing the web header stamp reds the parity pin. **The mutation run
    also caught a VACUOUS ASSERTION IN THE NEW TEST**: the web e2e sliced from `ds-meta` to
    end-of-document, so the Record & reproduce stamp satisfied a check written for the HEADER — it
    passed with the header stamp deleted. Scoped to the element and re-mutated before landing.
    **THE FUBO CASE IS THE HEADLINE TEST.** Identical extracted content, different extractor: any
    identifier computed FROM the output collapses those two vintages onto one value (measured:
    `6d170d2fe3` on both sides of #238). A declared version does not. That is the previously-broken
    case, asserted first.
    **PRINT FATE, READ FROM THE CSS rather than assumed** (a class-toggle probe cannot evaluate
    `@media print`): `.ds-meta` carries no print override → the IDENTIFIER prints in BOTH PDF
    scopes; Record & reproduce is appendix-tier (`body.ds-print-brief .ds-tier{display:none}`) →
    the GLOSS prints in the Full dossier PDF only. That is the three-tier rule landing correctly,
    not a gap.
    **ARTIFACT PASS INCLUDED, AS A SEPARATE COMMIT.** The render change made all 11 committed
    `dossier.md` stale against the drift guard, so they are RE-RENDERED from committed JSON — a
    re-render, NOT a re-assembly: no extraction ran and no `dossier.json` changed. They render
    "extraction unstamped", which is the truthful reading of an artifact that was never stamped.
    Stamped values arrive with the re-assemblies, CNXC first.
    **STILL 2 OF 13.** 26a is infrastructure, not a defect fix (operator 2026-07-28). What changes
    is that the pipeline runs again.
    A declared version constant, carried on the dossier record, **rendered wherever the dossier
    states its assembly date** — NOT in the appendix and NOT as a machine-only field (operator
    2026-07-28: a stamp nobody reads cannot stop anyone comparing two dossiers of different
    vintages, which is 17b's failure exactly — the record complete, the harm intact).
    **RED:** two dossiers built under different extraction versions are distinguishable BY THE
    STAMP ALONE. Note the currently-committed pre-#238 dossiers carry NO stamp, and absent-stamp
    reads honestly as "vintage unknown, pre-stamp" — itself distinguishable from any stamped one.
    **WHY DECLARED AND NOT DERIVED — THE MEASUREMENT THAT KILLED DERIVATION.** Two derived forms
    were specified and both were measured before building, per the standing rule.
    **THE PROPOSED HASH WAS WRONG IN BOTH DIRECTIONS.** A content hash over the EMITTED row-label
    set was measured pre-#238 (`2facc5e`) vs post: **FALSE NEGATIVE** — FUBO hashes `6d170d2fe3`
    on BOTH sides, because it carries no unusual items and its output is byte-identical across the
    change, so a reader comparing FUBO-pre with FUBO-post would conclude "same vintage" and be
    wrong; **FALSE POSITIVE** — post-#238 SMPL `be2c3d4ec5`, AORT `03aa28a19d`, FUBO `6d170d2fe3`
    all differ from each other despite being ONE vintage, so the hash is a SHAPE identifier, not a
    VINTAGE identifier, and cannot answer "are these two dossiers comparable?".
    **CORRECTED MECHANISM: hash the extractor's CODE-SIDE SCHEMA** — the emitted model field names
    (`FinRow`/`FinTable`) plus the hand-named row list plus the surfacing-rule marker. VERIFIED to
    behave: pre `57066b8cea` → post `42c81f752d` (it moves, because #238 added `FinRow.material`),
    and it is NAME-INDEPENDENT, so every dossier of one vintage shares it. Not a git SHA, for the
    operator's reason: a SHA moves on unrelated commits and would mark the fleet perpetually
    diverged.
    **BOTH DERIVED FORMS ARE SUPERSEDED BY THE DECLARED VERSION** (operator's option 3, 2026-07-28)
    — the measurements above are retained because they are WHY derivation was abandoned, not
    because either form ships.
    **PRIORITY — THE FREEZE WAS TOTAL, NOT TWO NAMES (operator 2026-07-28), AND 26a IS WHAT LIFTS
    IT.** Nothing could be re-assembled, and that included ANY NEW UNDERWRITE, since a new name
    needs a dossier built on the post-#238 extraction which is unstamped. **26 stood between the
    fund and doing any underwriting at all** — never a hygiene item behind CNXC and SMPL.
    **ORIGIN (queued 2026-07-28 from the #238 blast-radius diagnosis).** Every committed dossier
    carries the extraction version that produced it, because
    after #238 the fleet holds two vintages with nothing distinguishing them — pre-guard tables
    lack the unusual-items rows, post-guard tables carry them — and cross-name comparison in the
    verdict-pending cohort silently assumes a common table. Cheap, makes the divergence legible
    WHILE it exists, and a fleet re-assembly cannot even be verified complete without it. Ships
    BEFORE any fleet re-assembly.
26b. **DRIFT TEST — THE DECLARED VERSION MUST MOVE WHEN BEHAVIOUR DOES. Sequenced after the
    mechanical batch; no freeze rides on it.**
    **THE THIRD CASE IT EXISTS FOR — SEMANTIC CHANGE AT UNCHANGED SHAPE (operator 2026-07-28).** A
    schema hash catches an added row, not item 20's change — `range_position` and `pe_ltm_current`
    now return `NM` where they returned a stale figure on three names, same labels, same fields,
    and 16.0x vs `NM` matters to a reader more than an added row does. The test hashes the
    extraction module sources and FAILS when that hash moved while the declared version did not.
    No false positive at read time; the cost is a red CI on refactor, which is the point — it
    forces a conscious "did behaviour change?" call inside the PR instead of leaving it to a
    reader comparing two dossiers.
    **THE MODULE SET IS A DECLARED LIST, NOT A COMPUTED CLOSURE — CORRECTED 2026-07-28 BEFORE ANY
    BUILD, on three findings.** (i) The transitive import closure from `assemble.py` is **58
    modules** — resolver, store, universe, rank, screens, essentially the package; a drift test
    over that reddens on nearly every commit, and a guard that always fires is switched off, which
    is the unusual-items guard's own filing-date lesson turned on us. (ii) `ciq_balance.py` is
    reached ONLY from `cli.py`, never from `assemble.py`, so seeding at the assembly entry point
    silently omits balance-sheet extraction — the same false-negative shape that sank the row-label
    hash. (iii) **The enumerating walker ITSELF had a false negative** — it missed
    `from vinci.dossier import ciq_sheets, edgar_fundamentals` (submodules arriving as `names`,
    not `module`), and nearly produced a report calling `edgar_fundamentals` unreferenced. Finding
    (iii) is the argument against (i) and (ii) as a strategy: **a computed closure is the wrong
    basis for this boundary.** Declare the set; let a machine catch drift against the declaration —
    the same shape as 27a's baseline, and the same shape as this test itself.
    **INVARIANT (operator 2026-07-28, stated WITHOUT a layer per the new spec rule):** *every
    module that can change what appears in a dossier must be in the watched set; a module joining
    that class without being declared must RED.*
    **HYPOTHESIS, carrying no more weight than the builder's own reading (operator):** if extraction
    output is TYPED, "which modules construct that type" may be a more reliable basis than import
    reachability — AST-checkable rather than graph-traversable. UNVERIFIED; check it against the
    code when 26b is scoped, and re-spec if it differs.
29. **BULL-LEG CONSTRAINT AS A STRUCTURED FIELD — P3 part 2, GIVEN ITS OWN NUMBER by the operator
    2026-07-28 (previously folded into 24).** THE DEFECT: the bull leg sits ABOVE the constraint
    its own method sentence states. **WHY IT IS NOT 24:** 24 is a BLOCKED policy bucket (shares
    basis + regime test) awaiting a ratified line; a schema change parked inside a blocked policy
    item is stranded by it. **WHY IT IS NOT 18a:** 18a is the LEDGER PAYLOAD's structured fact
    fields — this is the SCENARIO RECORD's schema. Same move, different object; the first
    recording of this dependency named 18a and was wrong.
    **MECHANISM (verified 2026-07-28 before queueing, not assumed).** The method sentence is
    ANALYST-AUTHORED — no code constructs one — so the generator-assertion route is unavailable,
    and P1's presence-check route does not transfer either: P1's half works because a typed FIGURE
    must appear, whereas this is a RELATION ("just under X") that lives only in prose. **The
    tractable route is the `bear_basis` precedent** (schema 1.2 turned bear-multiple provenance
    from prose into an enumerated, validated, forward-required field): give the bull leg a TYPED
    constraint — the reference it is set against, plus the relation — after which the check is
    arithmetic rather than parsing. Schema 1.3's `leg`/`role` (item 16) are the plausible carrier;
    HYPOTHESIS, to be checked against the model before building, like every other mechanism here.
    **KIND: ANALYST DATA** under the closure taxonomy → closed only when the guard ships **AND**
    the surfaced SMPL instance is adjudicated; the guard alone leaves the record still wrong.
    **RED:** a record whose bull multiple violates its own declared constraint is REFUSED at write
    — SMPL's live record is the positive instance, and a conforming record the negative one.
    SEQUENCED AFTER 19.
30. **TYPE-CHECK `tests/` — QUEUED 2026-07-28, DELIBERATELY NOT SCHEDULED (operator: "whether to
    actually check `tests/` is a separate item — queue it, don't schedule it").** The standing gate
    runs `mypy` over `vinci` only: **111 source files, and `tests/` excluded, carrying 308 strict
    errors**. Nobody's claim was false, but the line "mypy --strict clean" READS as *the codebase
    type-checks* and MEANS *production type-checks* — the assertion-integrity class (item 19)
    applied to our own gate, which is why it is written down rather than shrugged at.
    **WHY IT MATTERS MORE HERE THAN IT NORMALLY WOULD (operator):** **the tests ARE the safety
    layer.** Every guard in this remediation is a test, and the code asserting those guards is not
    type-checked. The CHEAP half is done immediately and is not this item: the gate line now states
    its own scope (`docs/engineering.md` §Conventions). This item is the expensive half — actually
    clearing `tests/` — and it is unscheduled on purpose.
31. **MUTATION-TEST THE AUDIT-DERIVED GUARDS — queued 2026-07-28 (operator: "the biggest finding
    in #245"). SCOPED DELIBERATELY: not the suite.** ORIGIN: 26a's web e2e **passed with the
    header stamp deleted** — its slice ran from `ds-meta` to end-of-document, so the audit-tier
    stamp satisfied a check written for the HEADER. It was found only by mutating, never by
    reading, and it was written by the same pass that wrote the guard it was checking.
    **WHY IT MATTERS MORE THAN ONE BAD TEST: every guard in this remediation IS a test.** A green
    suite of 1148 says "the guards hold"; a vacuous assertion makes that sentence mean less than it
    reads — **the same shape as `mypy --strict clean` covering `vinci` only.** Both are green
    signals whose SCOPE is narrower than their wording.
    **SCOPE — ~20 assertions, not 1148.** The audit-derived guards only: 17b, item 20's
    per-consumer tests, 26a's pins, and each new guard AS IT LANDS. Method: delete what each one
    guards, confirm it reds, restore. **RUN IT AGAINST THE GUARDS ALREADY SHIPPED BEFORE ADDING
    MORE** — a guard that cannot fail is worse than a missing one, because it is counted.
    RED: for every guard in scope, a recorded mutation that reddens it.
    **SECOND CLASS, ADDED 2026-07-28 (operator) — CORPUS DECAY, and it is distinct from the vacuous
    assertion.** A vacuous assertion is born hollow; **a corpus-driven test crosses from meaningful
    to hollow LATER, silently, when its corpus changes.** Found on CNXC's re-assembly:
    `test_the_material_default_round_trips_every_pre_238_dossier` required every committed dossier
    to be PRE-field. CNXC's re-assembly reddened it — but the other direction is the dangerous one:
    **once the fleet is fully re-assembled there is no pre-field dossier left, and the test would
    PASS ON AN EMPTY CORPUS**, proving nothing while green. **The fleet re-assembles name by name
    from here**, so every corpus-driven test is walking toward its own decay date.
    SO 31 HAS TWO PARTS: (a) mutate each audit-derived guard; (b) **ENUMERATE the corpus-driven
    tests and state, per test, what happens when its corpus EMPTIES or INVERTS** — the answer must
    be "reds", never "passes vacuously". The fix pattern is the TEST-LAYER rule already: a
    value-level pin moves to a CONSTRUCTED fixture (as that test now does), and a
    fleet-invariant asserts a floor on what it saw.
    **31 STAYS AHEAD OF THE BATCH** (operator) — the batch adds guards, and guards must be
    mutation-checked as they land rather than retro-fitted.
    **31(b) MEASURED 2026-07-28 — THIRTEEN TESTS PASS ON AN EMPTY CORPUS. Not a regex estimate: the
    corpora were EMPTIED in a throwaway worktree (never `git stash`) and the suite re-run.** A
    regex first said 14; the measurement disagreed in both directions, which is why the regex is
    not the finding. Baseline in a fresh worktree is **1137 passed / 13 skipped** (vs 1149/1 in a
    working one) because `data/manual/ciq` is git-ignored and PER-WORKTREE — so four CIQ-driven
    SKIPs in the run are an experiment artifact, NOT decay, and are excluded from the count below.
    **DOSSIER CORPUS emptied → 11 red (honest), 8 still green:**
    `test_committed_own_history_agrees_with_its_sibling_range_position` ·
    `test_committed_peer_rosters_have_no_midclause_clip` ·
    `test_committed_peer_rosters_split_to_their_declared_count` ·
    `test_download_menu_offers_three_scopes_and_serves_the_committed_md` ·
    `test_13_fields_reach_both_twins_and_the_mirrors_e2e` ·
    `test_card_verdict_keys_read_by_js_are_emitted_by_build` · `test_ref_value_py_js_parity` ·
    `test_committed_dossiers_carry_no_ratio_as_a_currency_amount`.
    **SCENARIO CORPUS emptied → 5 still green:**
    `test_every_committed_scenario_record_is_register_clean` ·
    `test_new_fields_are_additive_so_existing_records_still_validate` ·
    `test_every_committed_record_is_class_compliant_and_seal_clean` ·
    `test_committed_records_that_opened_a_position_carry_their_entry` ·
    `test_every_committed_record_result_matches_its_own_facts`.
    **MOST ARE NAMED `test_every_committed_…`** — a name promising fleet coverage its assertion
    does not enforce. That is the same sentence as `mypy --strict clean` and the 26a slice: the
    wording is broader than the scope.
    **SHIPPED — the cheap half:** `test_the_committed_corpora_are_not_empty` (mutation-verified
    against a real-but-empty directory, so the FLOOR fires rather than a `FileNotFoundError`) turns
    the EMPTYING mode — which all thirteen share — into ONE loud red.
    **31(b) INVERT MODE — CLOSED 2026-07-29. AND THE COUNT WAS WRONG: 11 GENUINE, 2 FALSE
    POSITIVES.** Re-measured with BOTH corpora empty (the first run emptied only dossiers, so
    scenario-driven tests passed for an experimental reason). `test_ref_value_py_js_parity` already
    carried `len(cases) > 50` and reds honestly; `test_card_verdict_keys_read_by_js_are_emitted_by
    _build` reads only source files and never touches a corpus. Neither was ever at risk.
    **THE RULE (operator), mechanically decidable:** *relational floor where expressible;
    constructed fixture where not.* And the operator's sharpening is what makes it mechanical —
    **inexpressibility IS the signal**: if the relation can't be stated, the test's premise depends
    on the corpus rather than on its claim, which is the fixture branch.
    APPLIED: **4 unfiltered sweeps → RELATIONAL floor** (`checked == len(corpus)`, which cannot
    decay and cannot be quietly lowered the way an absolute `>= N` invites). **7 filtered sweeps →
    a loud red when the filter matches nothing**, plus a constructed fixture for the claim where
    one is meaningful (`test_an_opened_position_without_its_ratio_is_refused`).
    **A THIRD BRANCH THE RULE DIDN'T ANTICIPATE, worth recording:** for
    `test_every_committed_record_result_matches_its_own_facts` the fixture branch is UNAVAILABLE —
    the claim is that PERSISTED numbers still match a recompute, and a constructed record computes
    then compares against that same computation, proving nothing. A divergence can only exist on
    data that was written and left. For claims of that kind the loud red IS the whole guard.
    **ACCEPTANCE, run in a throwaway worktree with both corpora emptied: 27 red, 4 skip
    (environment — no CIQ bundles), 1 green** — the one false positive above.
    **31(a) — CLOSED 2026-07-29. Every audit-derived guard mutation-verified**, each by deleting
    what it guards and confirming the red: item 20's consumer sweep (reds on SMPL, CNXC and WERN —
    exactly the three names the defect was live on); 17b's material marking; the `FinRow.material`
    round-trip (#247); 26a's md-header, both-md-sites and web-header stamps (#245); the preview-path
    guard (#246); the corpus floor (#248).
    **AND 31(a) CAUGHT ITSELF — TWICE.** (1) The first 17b mutation inserted its early `return` in
    the wrong place, changed nothing, and left the suite green — the guard looked VACUOUS and was
    not. **A mutation that does not change behaviour is not a test of the test**; now a standing
    line in docs/engineering.md beside the worktree-baseline rule. (2) **REVIEW OF #249 FOUND THE
    SAME CLASS IN #249's OWN NEW TEST.**
    `test_capital_structure_refuses_a_descending_export_rather_than_mislabel` asserted only on the
    date HELPER: deleting the entire refusal from `_capital_summary` left it GREEN. A test whose
    NAME claims one thing while its ASSERTION checks another — in the PR about vacuous tests.
    Rewritten to drive `_capital_summary` itself (positive: ascending → PRESENT and reads the
    LATEST column; negative: the same sheet reversed → UNKNOWN naming the ordering), and
    re-mutated to confirm it now reds. **Two instances in one PR is the argument for making the
    mutation step routine on every new guard rather than a one-off exercise** — writing the guard
    and writing its test in the same pass is exactly when this blind spot occurs.
32. **`midcycle` REACHES ONE TWIN ONLY — LATENT #227, queued 2026-07-28 (operator: "needs a
    number, or the diagnosis sits latent until something populates it").** `midcycle` is named in
    `render.py` and ABSENT from `dossier.js`; it is `null` on all 11 committed dossiers (absent on
    MVST), so nothing is missing from the web TODAY. The moment a dossier carries one, the markdown
    renders a section the web twin and BOTH PDFs omit — #227's exact shape, pre-diagnosed.
    TWO PARTS, and the second is the general fix: (a) decide whether `midcycle` is web-renderable
    or a declared `twin_exempt` entry with its reason; (b) **WIDEN
    `test_every_assembled_field_reaches_both_dossier_renderers` TO TOP-LEVEL KEYS.** It harvests
    `mechanical`/`synthesis`/`anchor` only, so `assembled_at`, `llm_model`, `sector`, `exchange`
    and `extraction_version` all sit outside the fleet invariant — 26a had to ship its own pin
    because of it. Measured 2026-07-28: widening reds on exactly ONE field, `midcycle`, which is
    why (a) gates (b).
    **THE ARGUMENT FOR (b)'s PRIORITY, in one line (operator 2026-07-28): `extraction_version` —
    the field whose ENTIRE PURPOSE is telling a reader whether two dossiers are comparable — is
    itself unchecked for consistency between the two renderings.** Not live, because 26a shipped a
    dedicated pin for it; but a fleet invariant that excludes the comparability field is the
    cleanest possible case that the exclusion is arbitrary rather than principled.
    **(c) SCOPE WIDENED 2026-07-29 BY THE OPERATOR — FROM FIELDS TO RENDER SURFACES. The md twin
    lagging the web is ONE defect, not four.** Batch A found `reunderwrite_triggers`, `facts` and
    `recipe_formula` all already rendered on the web card and absent from `render.py`; the
    close-aware WATCH chip (item 21's "one of four surfaces") is the fourth; `spot_source` — found
    while fixing clause (e)'s stamp — is the fifth. Every one was discovered by READING, one at a
    time, at a cost of one build each. **This item's check compares FIELD NAMES in source text; a
    check comparing what each twin actually EMITS would have caught all five at once.** That is the
    general fix and it is the reason (b) is worth doing properly rather than as a token widen.
    **(d) THE CONSEQUENCE, and it reframes three queued items (operator 2026-07-29).**
    > **Twin parity checks AGREEMENT, not TRUTH.** A parity check catches DIVERGENCE by
    > construction; a shared error passes it. The `@ 2026-07-27` stamp reached both twins from one
    > wrong assumption, so parity CONFIRMED it.
    And the operative half:
    > **Truth-checking a stamp requires the vintage to be STRUCTURED.** `@ 2026-07-27` cannot be
    > verified against anything while the real date lives in free text.
    Therefore `spot_as_of`, **18a's typed facts** and **29's typed relation** are NOT schema
    hygiene — they are what makes truth-checkable rendering possible at all. Everything short of
    them is agreement between two surfaces that may both be wrong. **These move UP in priority once
    the current run finishes**, and now have a stronger case than item 1(b).
    **INFRASTRUCTURE STAYS FROZEN — do NOT build this now** (operator, same message). Recorded so
    the count is on the board when the freeze lifts.
    **NOTE ON THE PARITY PIN'S OWN BLIND SPOT (found 2026-07-29):** its docstring accepts that a key
    named only in a COMMENT gives a false PASS. The inverse is also true and undocumented — a key
    named only in a comment gives a false FAIL: a Batch A docstring mentioning `d_and_a` reddened
    the check. Symmetric blind spot, currently half-recorded.
33. **~~`.rtf` RELATIONSHIP PARSER READS SHIFTED COLUMNS~~ — BUILT 2026-07-30. AND THE RECORDED
    MECHANISM WAS WRONG.** STATE said the parser "drops empty cells then reads positionally". The
    real cause is a **VARIABLE HEADER** — the export ships TWO layouts:
    · `Customer Name | Relationship Type | Primary Industry | Source` (4 columns)
    · `Customer Name | **Supplier Name** | Relationship Type | Primary Industry | Source` (5)
    `cells[1]` is the relationship type in the first and the **supplier name** in the second, so a
    positional read was correct for exactly half the fleet and silently wrong for the other half.
    AORT rendered `Artivion, Inc. (NYSE:AORT) — Endospan Ltd. · Distributor`: the focal company as
    its own counterparty, the counterparty as the relationship, the relationship as the industry.
    **MEASURED, and the split is exact:** the 5-column names are AORT, CNXC, EPAM, FUBO, IT —
    EXACTLY the five that rendered a company in the relationship slot. **40 rows → 0** (40, not the
    32 first reported: the first count under-measured EPAM, which has 181 relationships and 20 bad
    rows in the rendered window). The five 4-column names are byte-unchanged.
    **FIX:** columns located BY HEADER TEXT, and the split no longer filters empty cells — a blank
    cell is a POSITION, not nothing. Same fix as item 21's `.xls` route and the same class as the
    `[-1]` rule: an unasserted assumption about layout. A reordered or extended export now keeps
    working instead of shifting silently.
    **BOTH PARTIES RENDER when both are named** (`Customer ← Supplier`). Which side is the focal
    company varies row to row — Artivion is the customer in one row and the supplier in the next —
    so inferring "the counterparty" would be a conclusion the export does not make; the direction
    is what `Relationship Type` already states.
    **BYTE-IDENTITY VERIFIED, not inferred (review):** the PR claimed the 4-column names were
    unchanged on the strength of their defect count being 0 both before and after — which is not
    the same claim. Checked directly: all five 4-col names (BRBR, MVST, NCNO, VITL, VRRM) are
    byte-identical, exactly the five 5-col names changed, and every one kept its ROW COUNT — fields
    corrected, no rows gained or lost.
    **DETECTOR NOTE:** the first gate used a whitelist of relationship types and produced SIX false
    positives (`Borrower` and `Client Services` are real CIQ types). The corpus is the authority on
    that vocabulary, so the gate now detects the DEFECT — a company name in the relationship slot —
    rather than encoding a guess about the vocabulary.

34. **SLEEVES — un-hardcode the overshoot framing (SERIES A; briefed 2026-08-08; §4 records
    the decision). BUILT ACROSS NINE PRs AND ALL MERGED TO main 2026-08-09 — #376, #385, #378,
    #379, #380, #381, #382, #383, #384, in that order, each squashed with the full suite green on
    the merged result. (#377 carried PR-1a; GitHub auto-CLOSED it when the #376 merge deleted its
    base branch, then refused to reopen it because the head had been force-pushed in between —
    so the same work landed as #385, its content unchanged but REBASED onto main
    (`55202ea` → `2a1bb3c`, which is why the reopen was refused). Review history stays on #377.)**
    The pipeline was hard-bound to overshoot at seven surfaces; a followed megacap (UBER) was
    therefore asked what broke when nothing had, and its bearish twin label would have written
    "terminal decline" into an append-only ledger against a compounder.
    **What shipped, in order:** #376 the four sleeve definitions + the followed-name INTAKE
    RUNBOOK; #377 `vinci/sleeves.py` (frozenset-validated, the `BEAR_BASES` precedent, never an
    Enum), `followed.json` migrated flat-string → `{reason, sleeve}` with the bare form REFUSED,
    `Dossier.sleeve`; #378 `LedgerEntry.origin`/`.sleeve` optional-with-default, the followed
    name can log a verdict AT ALL (the acceptance red: `log_verdict` refused it), curve
    segmentation with the PRIMARY spread pinned identical on the committed ledger, and
    **`Verdict.PASS` brought forward here by operator decision** rather than waiting for #380;
    #379 `system_for(sleeve)`/`tool_for(sleeve)` with overshoot pinned BYTE-IDENTICAL against a
    git-extracted baseline; #380 the proposal mapping DERIVED from each book's own legs (no second
    table); #381 the per-book page question + case labels, the sleeve-conditional CIQ requirement,
    and the shelf tag; #382 the ledger-READING surfaces (monitor / gate widget / decision log /
    uw-card) which segmented in the engine and still pooled in every human-facing view; #383 the
    residual per-book strings INSIDE the headings #381 had already moved; #384 the gradual-decline
    price path, so a name that BLED rather than broke (UBER: worst day −6.89%, under the −10%
    gap detector) shows a price exhibit instead of an empty panel.
    **THE REVIEW FOUND TEN DEFECTS THE BUILD DID NOT** — worth recording because eight were the
    same shape: a fix applied at the layer it was noticed instead of the layer where the harm
    lands. (a) `by_sleeve` existed only in `to_dict()` while both default paths emit MARKDOWN, so
    a followed verdict was scored and then invisible; (b) the screen-origin scope held for the
    spread but not for the beta/alpha and pending counts printed beside it under the same heading;
    (c) the `llm_call.log` recorded the OVERSHOOT prompt while the model received the quality one
    — a false provenance record in the one artifact that answers "what was this asked"; (d) a
    DORMANT sleeve (`neglect`, sharing overshoot's labels) received a live proposal because the
    gate tested label membership rather than `ledger_active`; (e) a name in BOTH the follow list
    and the candidate set had its stated sleeve and reason silently discarded; (f) an UNKNOWN
    sleeve rendered with overshoot copy — the misleading framing reached through the error path.
    **FOUR MORE FOUND IN THE FINAL PRE-MERGE PASS 2026-08-09**, all fixed and mutation-tested
    before the stack landed: (g) the no-forward-price branch in `score_ledger` incremented
    `pending` before any origin filter — it `continue`s before the row reaches `scores`, so it was
    the ONE path no downstream filter could reach, and the pin meant to cover it asserted on
    `aggregate`, where `n_pending` is already an int INPUT (a pin that could not have caught an
    error made upstream of itself); (h) `bySleeve` grouped on the sleeve alone, so a
    followed-OVERSHOOT row — legal, since `followed.json` admits the default book and `_finalist`
    refuses the screen/follow overlap only when the sleeve DIFFERS — merged into the screen
    majority's bucket, which the renderer drops: out of `primary`, absent from "Other books", and
    chip-less, while the overview tile announced "1 in other books"; now keyed on the (origin,
    sleeve) PAIR, the chip gated on origin too; (i) `resolved_n` counts SCOPED rows and BOTH
    renderers divided it by the snapshot's total row count ("resolved 1/2" on one screen + one
    followed row) — two callers erring identically, so `scoped_n` now travels ON the diagnostic
    rather than being re-derived per caller.
    **(j) INCIDENT — the decision-log page threw on EVERY load and no test saw it.** #382 wrote
    `sleeveChip` as a `const` inside `render()` while its only caller, `entryCard`, is a
    module-scope function: every call raised `sleeveChip is not defined`, so the page stopped at
    "Loading ledger…" — the whole decision log, the fund's own proof number included, blank. It
    was found by OPENING the page, not by 2000+ tests. Every pin on that file greps source text or
    executes one lifted function, and a scope error is invisible to both: the string is present,
    the body is correct, and the WIRING between them is what breaks. Same shape as the two unwired
    `dossier.js` call sites the browser found earlier in the same session — the third landing of
    this class. **Incident→invariant (shipped Y):**
    `test_the_decision_log_page_actually_renders` runs the REAL `render()` over the REAL committed
    snapshots (plain-object `root`, `fetch` stubbed onto the committed files — no DOM, no server)
    and asserts the page reaches its content; mutation-tested against the version this branch had
    already pushed.
    **STANDING RULE EARNED:** when a value becomes per-book, the enumeration of its consumers is
    the fix, not the three call sites that were noticed — the mirror pins now walk every field.
    **SECOND STANDING RULE:** a JS view is not covered by grepping its source or executing one
    lifted function — render it. Three of this session's defects lived in the wiring, which is
    exactly what a source pin cannot see.
    **OPEN, and deliberately not built here:** the UNDERWRITE layer is still book-blind
    (`ScenarioRecord` carries no sleeve; `propose.py` has zero references), and it already holds
    `avoid_priced` + a `"passed"` status — the concept `Verdict.PASS` names, in different words,
    unreconciled. Settle that with the open R2/EV-Revenue template question (§OPERATOR TO-DOs item
    2 layer 2) before the template work starts. A **vocabulary collision** also wants an operator
    call: the underwrite bar test renders a GREEN `PASS` chip meaning *cleared the 2:1 bar*, while
    `Verdict.PASS` means *not at this price* — cheaper to settle before PASS is sealed into
    append-only rows. And UBER has not been RE-ASSEMBLED under `quality` (needs local price bars
    + its CIQ export), so its synthesis prose is still the one written under the overshoot prompt;
    only its framing strings have moved. Brief: `~/.claude/plans/fluffy-foraging-codd.md`.

24. **ANALYST-DECISION BUCKET — HEADLINE CORRECTED 2026-08-03 (disposition render): (a) SHIPPED
    2026-07-31, (b) STILL BLOCKED. The "Item stays BLOCKED" below was true of the whole item for
    three days and of half of it thereafter.** (a) closed via `afc4b08` (diluted shares OUTSTANDING
    as the per-share denominator, delivered through `refresh_record`) + `04d5936` (all seven records
    moved; SMPL 93.678M → 88.461M, r:r 3.83 → 4.78; no name crosses 2:1) — **and it is recorded as
    closed at §"WRITTEN 2026-07-31 (item 24 closed)", 1,700+ lines EARLIER in this same file than
    this entry.** Two statements about one item, in one document, disagreeing — the drift class the
    score line was retired for, this time inside a queue entry rather than beside one. **(b) — the
    REGIME TEST — is audit N2 and is genuinely still blocked** pending a ratified policy line.
    ORIGINAL HEADLINE, kept: ~~BOTH POLICY LINES RETRACTED BY THE OPERATOR 2026-07-28; DO NOT
    IMPLEMENT AS WRITTEN. Item stays BLOCKED pending archetype work.~~ (queued 2026-07-28 —
    DECISIONS, not builds; the machine proposes neither.) (a) SHARES BASIS: weighted-average diluted (recorded 93.678M) vs current shares
    outstanding (~88.5M) vs guided ~90M for FORWARD per-share values while the company retires
    ~11.7% of its equity — the auditor sizes the difference at ~$1.00–1.50/sh of understatement.
    (b) REGIME TEST (operator-added): when is an own-history multiple band admissible after an
    earnings-regime break — window it, down-weight it, or exclude it (audit N2: the 12.5x exit is
    43% above peer NTM median and drawn from the 2018–23 growth era; EPAM's DEAD-REGIME /
    STRADDLES-BREAK exclusions are the existing in-house precedent for the same judgment, now
    expressible as `excluded` fields). Both need a ratified policy line before any build encodes
    them.
