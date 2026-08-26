---
id: 
status: superseded
date: 2026-07-27
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md governance log
---

20. **SUPERSEDED NOTES ON AMENDMENTS — 2026-07-27.** `superseded_note` on the sidecar, rendered
   beside the class label INSIDE the "Verdict as recorded" expander. First case: SMPL tag 1, whose
   staleness premise the 2026-07-26 verification refuted (the mechanical facts were current; the
   move to watch stands as an operator decision). The sealed text is never edited — the correction
   travels BESIDE the claim, so a reader meets it there rather than discovering it three tags
   later, if at all. **The IC pack was regenerated** from the current card: it predated #225 and
   so carried neither the current-state block nor the construction-era banner; it now carries
   both, plus the superseded note.

**BUILD RECORD — 2026-07-24 ASSEMBLY-FRESHNESS GATE (branch `feat/assembly-freshness-gate`;
the invariant the SMPL stale-inputs incident owed, INVARIANT RULE).** `_panel_freshness_flag(ie,
latest_print)` + `_latest_earnings_print(edgar, cik)` in mechanical.py, wired into the
assemble_mechanical flag tail beside `_catalyst_stale_flag`. Fires a loud human CAVEAT when a CIQ
VALUATION panel (multiples_as_of / tev_as_of) predates the latest EARNINGS PRINT (newest 8-K item
2.02). ORTHOGONAL to the existing reference-date stale checks — the exact gap that let SMPL
through: its panels (2026-06-03 / 2026-06-25) sat WITHIN the 45d tolerance of the 2026-07-06
reference, but the reference ITSELF predated the 2026-07-09 FQ3 print, so a reference-anchored
check could not see it. ANCHORED / no tunable knob ("older than the newest print" is a hard fact);
fail-quiet on a feed miss / no 2.02 on file / unparseable as-of (never aborts assembly); the print
fetch reuses the HTTP-cached submissions JSON (no extra round-trip). REAL RUN (live EDGAR): SMPL
latest print = 2026-07-09; the committed FRESH panels (07-21 / 07-24) → SILENT; the
pre-disposition panels (06-03 / 06-25) → FIRES ("…predate the latest earnings print (2026-07-09…),
the oldest by 36d…") — the caveat that was missing when the BUY was recorded. Pins: fire/silence/
one-stale/on-the-print-date/fail-quiet (×3) + the 2.02-picking fetch (ignores 7.01, empty→None,
raise→None) + a real-committed-artifact before/after invariant. Gate: ruff · mypy --strict vinci
(110) · offline suite exit 0. SCOPE NOTE: gates the two valuation panels (the SMPL culprits);
financial_summary.as_of carries its own floor/unstamped handling and is deliberately out of this
first slice.

**OPERATOR TO-DO — NCNO price series unavailable for the reference window (2026-07-23).** NCNO's
What-broke chart / 180d returns / stock_performance are all UNKNOWN because its store bars run
**2021-07-01 → 2024-05-20, then a hole, then only 2026-07-08+** — the 52-wk window the dossier needs
(2025-07-07 .. 2026-07-06, ref 2026-07-06) has ZERO bars. A `vinci refresh --start 2021-07-01 …
NCNO` filled 2021-2024 but returned NOTHING for the 2024-2026 window, and a targeted re-run of that
window **HANGS** (3-min timeout, no output — the same reason the first backfill's log came back
empty). So this is a **data-source/pipeline wall, not a render bug**: NCNO stays correctly fail-loud
(no series → no chart, %s omitted; the strip falls to the tile grid on the fully-UNKNOWN name
return). REAL FIX (operator/infra step, NOT a render change): (a) diagnose why Polygon `refresh`
returns a 2024-05→2026-07 gap for NCNO and hangs on re-fetch (ticker remap? plan-history cap? a
silent per-day rate-limit backoff loop with no progress output — the refresh command should stream
progress / fail fast, worth its own fix); OR (b) use the Tiingo deep-history backfill path
(`vinci/eod/tiingo.py`, needs a Tiingo key), then re-assemble NCNO. Until then NCNO is the second
live back-compat case beside MVST — both render honestly.

**OPERATOR TO-DO — MVST cannot be re-assembled (2026-07-22).** MVST is the ONE dossier name absent
from `data/snapshots/candidate_records.jsonl` (the other ten are present), so `dossier assemble`
raises `LookupError: MVST not in candidate_records.jsonl`. Its committed dossier therefore stays on
the OLD driver format — "no 8-K matched" wording, metrics without the stated direction — while the
other ten carry the new one. Re-running screen+rank would fix it but regenerates the RANKED QUEUE,
a decision surface, so it is deliberately not bundled into an extractor PR. Do it as its own
operator step, then re-assemble MVST.

**VERIFICATION LESSON (same day).** The re-assembly loop checked "does `synthesis` exist" and
reported MVST as `synth` — it was reading the PRE-EXISTING synthesis of a dossier that had not been
rewritten at all. A liveness check must assert the artifact was REWRITTEN (`assembled_at` == today),
not merely that a field is populated. Caught by an assembled_at audit, not by the loop.

**INCIDENT 2026-07-22 (recorded risk, no shipped block).** `dossier assemble` OVERWRITES a good
dossier with a synthesis-less one when the LLM call fails: `synthesize` returns None on a transient
error, and the assembler writes `synthesis: null` anyway. Observed live — BRBR's committed
6-bull/8-bear synthesis was wiped by one flaky call; the only signal was the word `NO-synth` in a
summary line, and a plain retry succeeded. Recovered from git; all five names verified
synthesis-present before commit. SHIPPED: a pin that the failure must emit a NAMED flag (never a
bare None). NOT shipped: a block on the write itself — the assembler would need to refuse to
replace an existing synthesis with nothing, or write to a temp path and promote only on success.
~~**ACCEPTED RISK until that lands: never re-assemble without verifying `synthesis` survived.**~~
**CLOSED 2026-07-30 — THE RISK FIRED, AND ACCEPTANCE IS WITHDRAWN.** The acceptance predated any
evidence it fires. It fired: a single-name AORT run during an unstable-LLM window printed
**`1 done · 0 error(s)`** and wrote **`synthesis: null`** over AORT's committed synthesis. Two false
statements in one line — the write happened, and it was not reported as an error. It was caught
only by reading the word `NO-synth` in a summary line, which is exactly the weakness THIS RECORD
already named as the problem. The artifact was reverted, not committed.
**SHIPPED (operator-directed, own PR):** `_require_synthesis()` REFUSES the build when a CONFIGURED
client returns no synthesis — raised BEFORE `_write`, as a `DossierAssemblyError` that
`assemble_cohort` collects, so the CLI's `N done · M error(s)` line COUNTS it. It keys on the VALUE
being absent, never on a flag's wording: the 07-22 guard pinned that a flag is emitted and the
artifact was destroyed anyway.
**THE ONE LEGITIMATE NO-SYNTHESIS CASE is a build with NO client configured** — the mechanical-only
mode, disclosed by its own flag. The guard sits inside `if llm is not None:` so that mode cannot
reach it; a control pins the placement, because hoisting it would freeze every mechanical-only
build. Four mutations, four correct reds (guard removed · raise moved after the write · guard keyed
on flag text · guard hoisted out of the branch).
**THREE REVIEW FINDINGS, all fixed before merge.**
(i) **The collection path was pinned by SOURCE TEXT.** The test asserted `"except Exception" in
`assemble_cohort`'s source — which would pass even if the handler were narrowed to a type that does
NOT catch `DossierAssemblyError`, letting the refusal crash the whole batch instead of failing one
name. Now driven THROUGH `assemble_cohort` with a raising `assemble_one`: mutating the handler to
`except LookupError` reds it.
(ii) **THE COMMENT TRIM BROKE THE ORDER PIN — caught only by re-running the mutations.** Trimming
the duplicated call-site rationale left the comment mentioning `` `_require_synthesis` ``, so
`src.index("_require_synthesis")` found the COMMENT, not the call. The guard-precedes-write
assertion then passed while the call sat AFTER `_write`. The pins now match
`_require_synthesis(synthesis` — the call with its argument. **A cosmetic edit silently disarmed a
guard's test, and only the mutation sweep noticed.**
(iii) **VERIFIED there is no legitimate None**, rather than assuming: `synthesize` returns None on
exactly two paths — an `LlmError` and a truncated/incomplete tool result — both failures. Refusing
on None therefore cannot break a supported build. Recorded in the helper.
**BOUNDARY, RECORDED NOT FIXED (operator 2026-07-30): the guard catches `None`, not DEGRADED.**
A synthesis that RETURNS but is empty, truncated to a single sentence, or otherwise thin still
writes — the refusal keys on absence, not on quality. `None` was the observed failure on both
occasions and is the right target; judging sufficiency is a different question with a different
owner (the prose-register and false-balance guards live nearer it). Noted so "synthesis is
protected" is not read as broader than it is.
**INCIDENT → INVARIANT: shipped Y.** (Was: recorded-and-accepted. The distinction matters — an
accepted risk with no evidence is a prediction, and this one was wrong.)
**API STATE: UNKNOWN, load- or payload-dependent — NOT "recovered" (2026-07-30).** Two full
8-name batches failed 8/8 with `InternalServerError: 500` on the synthesis call. A trivial probe
returned HTTP 200 and was reported as "recovered" — a WRONG CALL: the probe used a different model,
token budget and no tool use. Re-probed with the real shape (`claude-opus-4-8`, `max_tokens=16384`,
forced tool use): also 200, and the failure STILL did not reproduce. So the outage is not
characterised in either direction. **"Recovered" invites a retry; "unknown" invites caution** —
and the one retry taken on the strength of the wrong probe is what destroyed AORT's synthesis.

**BUILD RECORD — 2026-07-21 IT full re-assembly (artifact pass e8181e7) + before/after comparison.**
IT re-assembled against the same-vintage on-disk workbook; committed-vs-fresh compared leaf-by-leaf
(4294→4519 leaves). VINTAGE CLEAN: financial_summary values byte-identical (sole annual diff: the
consensus as-of note healed "as-of ?" → "≥2026-06-24"); return_ratios/ROIC/margin/trajectory WIDENED
to FY17+ with every overlapping value identical (the full-history extractor's first live pass on a
re-assembly). #178's dedup PROVEN LIVE: the fresh parse of the 8-K (which states the impairment
twice) emits one segment. NEW since Jul-10 assembly: operating_drivers (4 anchored events + 12
LLM-fenced leading indicators; 8 Tier-B drops disclosed in qa_flags 4→26 — no-silent-caps honored);
anchor.ltm_fcf; NTM forward multiple. SYNTHESIS (weather + substance): lean still mixed → proposal
still proposes nothing (the sealed ledger record untouched); bull/bear 9/4 → 9/6 and the
FALSE-BALANCE caveat cleared; substance GAINED contract-value mechanics ($5.3B CV +1%, GTS −4%/GBS
−2% new business, federal CV 126→114 named the largest swing factor), engagement metrics, and the
3rd-percentile-of-9y own-history read (unavailable pre-full-history); LLM selection DROPPED the
guidance-credibility bull point (28/30 beat record — data still in the dossier) and churned twins
(Moody's + D&B out, Cognizant in). AS-OF DRIFT, not vintage: P/E 14.13→14.53 / pctile 2.1%→4.8%
(screen data-record refreshed; EDGAR/EOD sourced). FACE-VALIDITY FLAG: a third-party sponsor PR
rides the anchored event tier (CIQ Key Developments noise) — task chip spawned for a
subject-company filter. Suite green on the fresh artifacts (901) before push.

**BUILD RECORD — 2026-07-21 driver-segment dedup (PR #178, audit item 8 closed).** The declutter
record's "heals at re-assembly" claim was FALSE: the release-driver composer had no dedup, so a
re-assembly would have re-emitted IT's doubled "$150.0M Digital impairment" verbatim (the 8-K states
it in both headline and detail paragraph). Fixed at both layers: order-preserving segment dedup in
the composer (`dict.fromkeys` before the "; " join) + the committed IT value patched
byte-preservingly; md + frontend mirror regenerated. Pinned both layers (committed-artifact
no-duplicate-segments invariant + source pin on the guard). ACCEPTED EDGE: two DISTINCT one-offs
with identical amount AND wording would collapse to one segment — the extraction layer cannot
distinguish that pair either, so the join-level dedup loses nothing new. Gate on merged main
8d5c2b8: ruff + mypy --strict clean, 901 passed, generators idempotent.

**BUILD RECORD — 2026-07-21 full-history financials.** The extractor was applying a DISPLAY
window at EXTRACTION (`fy[-4:]`, quarterly `[-8:]`): 51 fiscal-year columns and 277 quarters across
the 12 names never entered dossier.json, unrecoverable without the licensed workbook. It also broke
a derived value — the earliest visible year's growth read "—" forever because nothing preceded it
(IT FY22: "—" → +16%, hand-checked). Now: extraction keeps every exported period; the BRIEF windows
to 4 FY + LTM + consensus and STATES what it hid; the Appendix names its span. Curate the view,
never the record.

**VINTAGE GUARD (incident → invariant).** Re-extracting CNXC/SMPL/VITL did not just widen windows,
it RESTATED committed values (CNXC LTM revenue 9,954→9,999 — the workbook says 9999.042, so the
committed number came from an older export). CIQ stamps no export date and the `≥` as-of is a
FLOOR, so nothing else detects a re-export; refreshing numbers under a synthesis written against
the old ones makes a dossier cite figures it no longer contains. `financials-backfill` now REFUSES
such a name and directs to a full re-assembly. Comparison is POSITIONAL from the end — several
names carry duplicate period labels (BRBR quarterly: FY24, FY24, FY24) and a label lookup compares
the wrong column (it produced a false alarm on the first pass). Shipped as a machine check + tests.

**OPERATOR TO-DO:** re-assemble CNXC, SMPL, VITL so their synthesis matches their (newer) numbers,
then run `financials-backfill` for the widened history. **SMPL is a logged BUY with a live forward
track** — its committed LTM revenue is one export behind.

**BUILD RECORD — 2026-07-21 dossier three-tier redesign (PR #174).** The Brief/Analysis/Appendix
tabs re-designed from first principles as an institutional report; web + md renderers moved
together; NO dossier.json data changed (render layer only + the 11 regenerated dossier.md).
Brief = six decision-ordered cards (At a glance · Scenario analysis · What happened · The case ·
Financial snapshot · Valuation — first cut); a logged name's narrative slot carries the analyst's
recorded rationale (once — the detail card suppresses its copy), a pending name the machine
assessment. Analysis re-ordered to decision logic, analyst caveats only. Appendix gains "How to
read this dossier" + RECORD & REPRODUCE (data window · model · identifiers · underwrite record ·
assembly log · re-run · verdict record) — the §5-item-1 provenance stamp's rendered home.

RETIRED from the reader surface with mechanisms intact: the standing machine-proposal row (still
derived + sealed at assembly, disposition still recorded; revealed by the ledger CLI and md
--show-proposal — pinned both directions), the Recommendation/Target slot, the standing
Verify-first section (now a conditional warning strip that skips RESOLVED caveats — VRRM's
resolved P/E-basis check was firing it), the verdict footer, the header process-meta line (whose
"data as of" contradicted per-fact vintages — the header now carries the DOCUMENT date), raw
recipe ids, the assembly-log line masquerading as an analyst caveat (all 11 dossiers), and the
per-card discipline lectures (stated once in the reading guide).

VERIFIED: 836 offline tests green ON the regenerated artifacts (10 structure pins re-anchored,
each keeping its invariant); scripted invariants 11 documents × 10 checks all hold; mirrors +
monitor idempotent; sweep.json byte-identical; live preview across the four coverage shapes
(pending / logged-with-card / logged-no-card / no-dossier degrade). Anti-anchoring note: removing
the proposal DISPLAY crosses none of the three protected lines (no LLM verdict, no outcome
tuning, no execution path) — the seal/reveal mechanism is untouched and test-pinned.

**BUILD RECORD — 2026-07-21 plain-language restatement pass (all four scenario records).**
Every prose field in IT / SMPL / WERN / EPAM restated into external-reader register; 23 restatements
applied (only fields that needed it — tagging an already-clean field would have made the record lie
about what changed). `Verdict.rationale_plain` + `rationale_plain_recorded` added (additive; every
pre-existing record still validates). The three verdicted names carry analyst-authored plain
rationales — the machine wrote NO rationale prose, consistent with the pivot. EPAM has none: its
verdict is still pending, and none was invented.

INVARIANCE PROVEN, not asserted: `result`, `facts`, every scenario NUMBER, `verdict.rationale` on
all four, and the decision ledger are byte-identical before/after; the mirror rebuild left
`sweep.json` unchanged (ee5416ba…) and WERN's theme-embedded card was re-emitted mechanically via
`_scenario_card()`, never hand-typed.

TWO FINDINGS WORTH KEEPING:
* **The linter's own false positives were caught by linting the ANALYST's supplied text.** Three
  patterns matched ordinary English as if it were house vocabulary — "early Aug" (a date, not the
  `early` grade), "still clears 2.02:1" (the verb, not the `cleared` status), "the company's own
  history" (possessive English, not the `own-history median` statistic). The last was found only
  because the analyst's own restatement tripped it: the linter was wrong, not the prose. Each
  narrowing carries a negative pin quoting the real sentence. A linter that cries wolf gets
  switched off, so a false positive is a defect, not conservatism.
* **Code and data could not be split here without a red commit.** Measured, not assumed: with the
  data stashed, three tests fail — including the pre-existing emit-determinism pin, because a
  changed emitter necessarily changes its emitted artifacts in the SAME commit. The C1/C2 split
  held for the linter+schema+render (7a6fc2c, code-only, zero artifacts moved); the emitter change
  landed with its artifacts, which is the opposite of the failure CLAUDE.md's rule guards against
  (logic smuggled into an artifact commit).

**CLOSED by the 2026-07-21 extraction-hygiene run:** the shared `annual_series` alias item AND
the `extract_points` first-alias/truncation item — ONE root defect, not two.
`ConceptPoint.is_annual` read `fp == "FY" OR days >= 300`; EDGAR stamps every QUARTERLY point
inside a 10-K with `fp="FY"`, so a 90-day quarter passed with **no duration check at all**.
Duration is now NECESSARY (350–380d). One predicate fixed all three surfaces — the anchor's
annual extraction, #160's conflict comparison, and the shared `extract_points` path (the guard
routes through `mc._annual_points`). Blast radius mapped first: all 11 `is_annual` consumers
intend annual semantics, no fixture relied on the loose 300–349d band, suite green on the
predicate change alone. The shared revenue alias order also ranked `Revenues` ABOVE
`606-Including` while the anchor ranked the reverse — the two could pick different denominators
for one filer; now single-ordered by MEANING and drift-pinned.

**#160 DIAGNOSIS CORRECTED — the fix stands, the mechanism story was wrong.** #160 recorded
these flags as a PARTIAL-TAG problem. The audit shows WRONG-DURATION in every case: AORT's
`Revenues` 43M is a 90-day Q1, SMPL's 121M a 90-day quarter, EPAM's 264M a 90-day Q1 — each
stamped `fp="FY"` inside the 10-K. The guard's PROTECTIVE work was REAL (a short-duration
denominator genuinely corrupts an anchor, so capping was correct); only the stated cause is
corrected. Re-audited under duration filtering all three conflicts VANISH: EPAM/SMPL/AORT go
`weak → firm` on the margin leg and overall, with **every committed margin value UNCHANGED at
stored precision** (0.118997 / 0.154481 / 0.038721 — verified before/after; the ~1e-7 recompute
deltas are the values being ROUNDED ON WRITE, not a data change, so the loud re-backfill path
was correctly NOT triggered).

**MONITOR:** the freshness panel selected only `watch`, so a RUN underwrite awaiting a verdict
was invisible; `pending_analyst` rides it too now — that record is precisely the one that must
not go stale, since the next print can move the decision before it is ever made.

**CLOSED by the 2026-07-21 WERN ratification run:** all three operator rulings recorded on
`scenarios/WERN.json` under the visible-amendment discipline (result / facts / scenario
numbers / verdict byte-identical; only the ruled items + tags changed). **Two premises in
the brief were WRONG and are corrected here rather than pattern-matched through:**
(1) there were NO `DRAFT — ratify at review` markers to strip — that was an IT-convention
carry-over; WERN's three method sentences came from the #164 build as clean prose, were
read for conformance to the ratified methodology, and are now stamped
`ratified_by=analyst, ratified=2026-07-21` (the optional fields PR #161 already added to
`AssumptionDerivation` — no schema change). (2) the current Dedicated-mix reference was
mis-attributed: it stored **73.0% sourced to the FY2025 10-K**, but that filing's full-year
mix is **64.46%** (1,149,550 / (1,149,550 + 633,853)) and it carries **no ~73% figure on any
basis**. The ~73% is the **Q1-2026 quarter** — 371,880 / (371,880 + 136,401) = **73.16%**,
10-Q acc 0000793074-26-000096 — now the stored value (73.2) and source. FY2018's 51.5% was
recomputed and reproduces at **51.46%** (FY2019 10-K acc 0000793074-20-000014), basis
stamped. The bull reason's "12–14% peaks" is scoped to TTS-SEGMENT level (consolidated
record 9.59/11.31/9.82%). Thesis logic and every number untouched.
**COUPLING SURFACED (bears on the Truckload freeze-source re-run, still open):**
`frontend/themes/truckload-supply-purge.json` EMBEDS a copy of WERN's scenario card, and
`test_emit_scenarios_matches_theme_embedded_card_and_is_deterministic` enforces ONE SHAPE
between it and `scenarios/WERN.json` — so amending the record desynced the theme file and
reddened the suite. The re-seed guard (correctly) refused to regenerate the theme JSON here
because its freeze source is absent from this worktree, so the embedded card was re-emitted
MECHANICALLY through the same `_scenario_card()` the emitter uses (never hand-typed): +5/-5
lines, the identical ruled items. This ADDS to what the freeze-source re-run must reproduce
byte-identical — that item now covers two surgical patches, not one.

**CLOSED by the 2026-07-21 mirror re-seed guard:** the sweep.json build guard
(`_preserve_unless_source`) — a generated artifact whose SOURCE is absent in the running
worktree is now left BYTE-UNTOUCHED and announced as `SKIPPED <artifact>: source absent`;
it fails loud only when the artifact is ALSO missing (nothing to preserve). Applied to
sweep.json, the theme freezes and the radar inbox/log from ONE helper, so the discipline
cannot drift between emitters. Pinned both ways
(`test_mirror_reseed_guard_leaves_sweep_byte_identical_without_manifest`,
`test_mirror_reseed_guard_fails_loud_when_nothing_to_preserve`).

**CLOSED by the 2026-07-21 monitor build:** position monitor (book vs benchmarks, spread,
freshness panel) · benchmark-by-cap-band assignment + the ledger-supersession artifact · the
SIC-87xx sector miss · entry-price/ratio-at-entry + implied-odds display.

- **SURVIVAL-GATE UPGRADE + THIRD R2 RECORD — MVST (branch `feat/survival-gate-going-concern`,
  2026-07-22).** Falsifier-driven, exactly as the queued pattern asks.
  - **THE FALSIFIER.** MVST's committed `ltm_fcf` is **+$56.074M** (EDGAR FY2025). Fed to the gate
    it returned *"trivial pass — the company funds itself and has no runway question"* — on a
    company whose own 10-Q states **substantial doubt about its ability to continue as a going
    concern** (accession `0001628280-26-033590`) and whose latest quarter annualises to a **$102.6M
    burn**. The gate printed the most reassuring line in the module on the most distressed name in
    the cohort. Found by the read-only basis pull, before any record existed.
  - **THE RULE.** A stated going concern **forbids the trivial pass**, whatever the trailing sign:
    the disclosure is about the FUTURE, the cash flow is about the PAST, so the past cannot overturn
    it. `burn_override` becomes MANDATORY (falling back to the trailing figure would defeat the
    branch — it is the very number the disclosure contradicts). A trailing-vs-latest **sign
    contradiction is always printed**, including on the trivial-pass path, which previously dropped
    its detail list entirely.
  - **SHAPE-READ FIRST, no duplicates.** The gate already had the brief's `committed_facility` as
    `facilities`/`facilities_source` (crediting runway) and the #176 announced-raise branch
    (`raise_shares` + `raise_proceeds` moving together). Both USED, neither re-implemented; the new
    surface is only `going_concern_stated`, `burn_override` and `latest_period_fcf`.
  - **THE RECORD.** `scenarios/MVST.json`, tier **B**, 4y, spot **$0.9188** (close 2026-07-21).
    Survival **FAIL**: runway **2.18y** — (cash 126.1 + ATM remaining 98.0) ÷ burn 102.6 — against
    3.0y to breakeven. Legs bear **−$0.049** · base **$0.602** · bull **$1.505**; **ratio −0.328**.
    **The bear case values the equity BELOW ZERO**, which is the whole read: the price pays nothing
    for the chance of a zero. Verdict `watch`, `avoid_priced`, no ledger row. Engine and an
    independent hand recomputation printed side by side — MATCH.
  - **THE DILUTION OVERRIDE.** Organic 2.30% cannot see the **open $125M at-the-market programme**
    (8-K Item 1.01 + 424B5, 2025-10-03) already drawn **+19% in two quarters** — $27.0M received of
    $125M authorised. Overridden to **10%/yr**, with the ATM's remaining $98M credited to runway AND
    its proceeds to terminal net debt, the coherent pair.
  - **ALL BALANCE-SHEET FACTS ARE VENDOR BASIS** — EDGAR tags no depreciation for this filer at all,
    so CIQ is the only basis available. Flagged in the facts, the methods and every table.
  - **THE CARD WAS HIDING THE EVIDENCE.** The survival panel rendered its one-line note but not its
    `detail`, so the going-concern disclosure and the sign-contradiction warning — the two reasons
    the gate failed — never reached the reader. Fixed: detail lines render, warnings in the danger
    colour. Clean names are unaffected.
  - Gate: ruff + `mypy --strict` clean; suite green; linter 0; mirrors rebuilt with all six other
    cards byte-identical.

- **EPAM PRE-VERDICT AMENDMENT — THE VINTAGE SWEEP PROTECTED A LIVE RECORD (branch
  `data/epam-dep-amort-amendment`, 2026-07-22).** The sweep shipped in #182 existed to prove the R1
  book was current. It was — for eight of eleven names. The ninth was the one name with an OPEN
  underwrite.
  - **WHAT WAS WRONG.** EPAM's committed `d_and_a` of **45.317** is `DepreciationDepletion
    AndAmortization`'s **FY2019** value. That tag stops at FY2019; the filer moved to
    `DepreciationAndAmortization`, which reports through **FY2025 at 124.811**. Both tags agree
    exactly on FY2014-FY2019, so this is a clean tag migration — not a definitional difference —
    and alias ordering carried the dead one forward for six years. Accession
    `0001352010-26-000015`, 10-K filed 2026-02-26.
  - **WHY IT MATTERED HERE.** EPAM is R1, EBITDA-basis: EV = (EBIT + D&A) x multiple. Understating
    D&A by $79.5M understates EBITDA in every leg, so the whole grid was compressed. The legs were
    never wrong — the analyst's revenue, margin and multiple stand untouched — only the fact under
    them was.
  - **EFFECT, legs unchanged:** bear 63.14 → **71.94**, base 163.08 → **181.42**, bull 291.24 →
    **317.65**; ratio 2.81 → **5.27** at the recorded spot, **5.34** at the 2026-07-21 close. The
    **2:1 ceiling moves $96.45 → $108.43**, and headroom at the last close goes ~8% → **+21.5%**.
    Anchor base 306.05 → 338.93 (derived, +11%).
  - **THE GUARD AGREED.** EPAM was the closest honest name to the implied-D&A bound at **4.20x**
    (bound 8x) and I recorded that at the time as "an EDGAR under-capture, not a sheet defect".
    That read was right and now has its cause: corrected, the ratio is **1.52x**. A cross-check
    flagging the name whose fact was stale is the guard working, a fortnight before anyone looked.
  - **AMENDED VISIBLY, per the SMPL precedent.** The fact carries its own amendment tag in
    `source`, so the record shows what changed and why rather than quietly reading differently.
    Legs untouched, methods stay DRAFT, verdict stays `pending_analyst`, no ledger row. One
    reference line added on the multiple axis recording that the band's multiples are computed on
    the filer's actual depreciation, so the corrected fact aligns the grid's EBITDA basis with the
    band's.
  - **ONE THING THE BACKFILL DROPPED, restored by hand.** The re-backfill replaced the committed
    `data_quality_detail` — an operator re-audit note from 2026-07-21 explaining that a prior
    revenue-tag flag was a DURATION artifact. `preserve_operator_tag` REPORTED the drop (it warns
    but does not merge, by design, so a stale narrative cannot outlive its cause); here the note was
    still true, so it was put back. That warning earning its keep is the reason it prints.
  - Gate: ruff + `mypy --strict` clean; suite green; prose linter 0 flags; mirrors rebuilt with
    every other card byte-identical.

- **CIQ BALANCE-SHEET EXTRACTION + THE D&A VINTAGE FIX — MVST AND FUBO UNBLOCKED (branch
  `feat/ciq-balance-sheet-extraction`, 2026-07-22).** Closes two queued items.
  - **THE VINTAGE DEFECT WAS DEEPER THAN QUEUED.** The queued note said `_latest_dep_amort` prefers
    the combined tag over newer split tags. True, but the staleness starts one level up:
    `extract_points` resolves ALIASES BY ORDER — first-with-any-data wins — which is right for
    breadth and wrong for vintage, because an abandoned tag keeps its last value forever and still
    sorts first. EPAM's `DepreciationDepletionAndAmortization` last reported **FY2019**; its
    `DepreciationAndAmortization` reports **FY2025**. Fixed inside `_latest_dep_amort` (scan every
    alias + the split pair, take the freshest, stamp what it overrode); the shared resolver is
    deliberately untouched — other consumers depend on its ordering.
  - **VINTAGE SWEEP — 8 of 11 unchanged, the R1 book is current.** Three would move, REPORTED not
    rewritten: **EPAM 45.317 → 124.811 (+175%)**, a **FY2019** value sitting under a **PENDING
    underwrite** — its EBITDA basis is six years stale and the pending grid should be re-checked
    before any verdict; **FUBO 0.003 → 38.548** (in scope, written); **VRRM None → 114.08** (no
    anchor block, nothing to rewrite).
  - **THE BRIEFED D&A COHERENCE CHECK WAS A FALSE-POSITIVE GENERATOR — designed out with evidence.**
    Cash-flow vs income-statement equality within 20% fires on 2 of 4 honest names (AORT 61% apart,
    FUBO 97%) because the two rows are DIFFERENT MEASURES: CIQ's income-statement line is the
    depreciation inside operating expenses, the cash-flow "Total" is consolidated. AORT settles it —
    EDGAR's combined tag (22.458) matches the cash-flow total (23.35), not the income-statement line
    (9.05). Shipped instead: the CONTAINMENT invariant (operating-expense portion ≤ consolidated
    total), which holds on every name and needs no tolerance. A guard that fires on honest names
    gets switched off.
  - **EXTRACTION MODULE** (`vinci/dossier/ciq_balance.py`): cash + short-term investments, total
    debt, leases, D&A, operating cash flow, capital expenditure, diluted shares — each stamped with
    file + sha. **UNIT scale asserted by MAGNITUDE against revenue**, never off a header: three 1e6
    defects have shipped here, and two survived a green test because the fixture value was zero.
    Net-debt cross-read (balance sheet vs multiple-implied TEV less market cap) available where a
    market cap exists. A failed check REFUSES the whole bundle rather than handing on survivors.
  - **ANCHOR WIRING — EDGAR-FIRST, ALWAYS.** The vendor sheet fills a HOLE and never overrides a
    primary filing; every filled field is stamped `vendor_bridge` in `data_quality` with the fields
    named, so the boundary is visible in the artifact. MVST took D&A + net debt; FUBO took net debt;
    IT took only a free-cash-flow hole (base unchanged, +0%).
  - **FUBO SHARE RESOLUTION — a REVERSE SPLIT, confirmed.** Diluted 30.0M vs 342.7M outstanding was
    a real corporate action, not a stale tag. Evidence: (a) management commentary in the 2026-04-06
    8-K discusses the reverse stock split directly; (b) **both regimes reconcile against their own
    EPS** — −2.1M ÷ 30.715M = −$0.07 and −6.0M ÷ 349.097M = −$0.02, exactly as filed; (c) CIQ's own
    income statement independently reports **30.72M** diluted; (d) the committed market cap ÷ price
    implies ~27M shares, consistent with ~30M and not with 342M. Implied ratio ≈ 1-for-12. **The
    current diluted count is 30.715M** and FUBO's share question is CLOSED.
  - **UNDERWRITABILITY.** **MVST — YES**: facts complete, and G2 is runnable for the first time
    (**pass 1.34x**); G1 passes at 10.01% implied D&A. **FUBO — YES on R2**: facts complete and the
    share question closed, but its band guards stay UNRUN because it has no trailing multiple series
    at all (every multiple NM on a loss-making year). That is structural, unfixable by a balance-
    sheet pull, and precisely the condition R2 exists for. **VITL remains the only flagged band.**
  - **THE CIQ-MANIFEST DRIFT GUARD EARNED ITS KEEP.** It rejected the module three times — a
    parameterised `freq`, a looped sheet name, then an undeclared `("financials", None)` address —
    until every `(kind, sheet, freq)` was a string literal it could read statically. `CIQ_MODULES`
    now declares the quarterly Cash Flow sheet and what consumes it.
  - Gate: ruff + `mypy --strict` clean; `pytest -m "not network"` green. 20 new pins, all
    magnitude-bound with non-zero fixtures.

- **SECOND R2 RECORD — AORT, WATCH + AVOID-PRICED (branch `data/r2-aort-record`, 2026-07-22).**
  `scenarios/AORT.json`, recipe `R2_terminal_margin`, basis EV/EBITDA, **tier B**, 4-year horizon,
  spot **$25.37** (last close 2026-07-20). Freshness CLEAR. Same PRICED family as NCNO: the base
  case is worth less than half the market price and the optimistic case sits below it too.
  - **RESULT.** bear $3.12 · base $10.44 · bull $18.35 in today's terms (terminal $5.45 / $18.26 /
    $32.09). reward −14.93 · risk +22.25 · **ratio −0.67 → FAIL**. Survival **PASS** but tier **B**,
    because the pass is nominal: FY2025 free cash flow **+$0.8M** — cash generation nearly doubled
    while capital spending TRIPLED to $39.0M and consumed it — against 3.7x leverage and 2.5x
    interest coverage. A gate that passes on $0.8M is not a cushion, and the tier says so.
  - **THE DILUTION OVERRIDE, and why it is not a double-count.** The raw 3-year diluted CAGR
    (5.62%) terminates in a **one-off convert-for-stock exchange**: ~$99M of 4.25% notes due 2025
    exchanged for common stock in May 2025 (8-K Item 3.02, accessions `0000784199-25-000080` and
    `-000129`; total debt 314.6 → 215.5 across the quarter). Compounding that forward would charge
    the terminal year for an event whose balance-sheet benefit is ALREADY banked in net debt.
    Override to the **FY2021–FY2024 organic basic CAGR, 2.25%**. **The static inputs are already
    coherent** — the exchange shares are in the 49.731M divisor and the retired principal is out of
    the 202.4 bridge, so there is no double-count to fix; the error would have been dynamic.
  - **THE FY2025 SHARE STEP, decomposed** (+5.486M, +13.16%): **+3.659M basic (67%)** = the
    exchange; **+1.827M (33%)** = dilutive securities re-entering diluted EPS as the company turned
    profitable. Basic equalled diluted EXACTLY in FY2018 and FY2020–24 — every one a loss year,
    where dilutive securities are antidilutive and excluded. That signature is what identified the
    mechanism.
  - **FCF-LAYER PRECEDENT SET.** The house basis is **EDGAR operating cash flow less capital
    expenditure** (+$0.8M, FY2025). The vendor's levered measure reads **−$7.3M** — recorded beside
    it rather than reconciled away, because the two are different definitions over different
    periods and the sign disagreement is itself the finding. The committed dossier carries BOTH
    `quality.free_cash_flow: -7.3` and `quality.survival_capacity: "FCF-positive → self-funding"`;
    that internal contradiction is the vendor layer's, not ours.
  - **THE CONSENSUS LAYER IS NOT GAAP, proven arithmetically.** Street "EBITDA" implies about
    **$62M of depreciation** for a year in which the company reported about **$22M**. Converting
    street EBITDA at our depreciation rate would overstate the operating margin by ~8 points, so the
    record uses the street's own **stated** operating-profit rows (6.93% FY2026, 10.80% FY2027).
  - **MARGIN IS NOT A RAMP.** FY2024's 10.01% — the best year on file — came from operating expenses
    FALLING 11.7% in absolute dollars; FY2025 gave 2.4 points back as spending grew 22.7% against
    13.6% revenue. **Operating leverage ran backwards in the latest year.** The committed 3.87%
    anchor median reconciles exactly but blends FY2016's 12.10% (pre-acquisition CryoLife) with
    FY2020's 0.96% (shutdown) — two business identities in one statistic.
  - **THE BEAR LEG DID NOT NEED REBUILDING.** Unlike NCNO (4/4 bear points pre-rebutted in their own
    sentence), AORT's synthesis is genuinely two-sided — **1 of 8** — and `evidence_balance` reads
    `mixed`, where the machine proposes nothing. The recorded bear leg is the analyst's, informed by
    a real one.
  - Verdict **watch**, `avoid_priced` true, **no ledger row**. Robustness verified: the verdict FAILS
    under BOTH share paths (organic −0.67, raw −0.72), so it does not rest on the override.
  - Gate: ruff + `mypy --strict` clean; `pytest -m "not network"` green; prose linter **0 flags**
    (the rationale tripped the 120-word cap at 122 and was trimmed to 119 — the cap did its job).

- **FIRST R2 RECORD — NCNO, WATCH + AVOID-PRICED (branch `data/r2-ncno-first-record`, 2026-07-21).**
  The instrument's first real use. `scenarios/NCNO.json`, recipe `R2_terminal_margin`, basis
  EV/EBITDA, tier **A** (recurring subscription revenue, 60.6% gross margin, self-funding), 4-year
  horizon on all legs, spot **$17.93** (last close 2026-07-20). Freshness gate CLEAR — zero filings
  post-date the 2026-07-20 evidence window.
  - **RESULT.** bear $4.19 · base $8.09 · bull $14.10 in today's terms (terminal $7.33 / $14.15 /
    $24.67). reward −9.84 · risk +13.74 · **ratio −0.72 → FAIL** at the 2.0 bar. Survival **PASS**
    (trivial — free cash flow +$82.6M; the company funds itself). Verdict **watch**, `avoid_priced`
    true, **no ledger row** (a watch opens no position — precedent stands).
  - **THE READ.** Base value is under half the market price and even the optimistic case sits below
    it; the asymmetry is inverted (−21% up / −77% down, present-value terms) and **invariant to the
    waiting-charge rate — it fails at 0% — and to full credit for interim free cash flow.** A sound
    franchise, fully paid for.
  - **R2 CONVENTIONS FROZEN** per the pre-committed shakedown criterion: 0 of 36 matrix cells cleared
    the bar and **no single flip changed any verdict**, so no convention is modified.
    **HONEST CAVEAT, recorded because it matters more than the result:** the test ran FAR from the
    boundary — the shakedown grids imply exit multiples 2.9–3.3× below what the prices require, so
    the matrix had **no discriminating power**. This is not "the conventions survived a stress
    test"; it is "the test could not have failed them."
  - **STANDING RULE ADOPTED.** Any future R2 run landing **within ±0.5 of the bar** auto-prints its
    flip table before the verdict, adjudicated under the same criterion. That is where the matrix
    would actually discriminate.
  - **COHERENCE, re-verified at the record:** R2 at years→0 reproduces R1's committed IT base
    ($273.8463) to **−0.107%**; the residual is exactly R2's ratio-derived D&A ($198.943M) against
    R1's flat D&A ($200.309M) on a terminal revenue 0.68% below LTM. `years=0` is refused by design.
  - **RENDER DEFECT FOUND BY THE RECORD, fixed in-branch (see the PREVIEW-RULE extension).** The
    chosen-trio row looked its value up by AXIS NAME; R1's three axes are spelled like their leg
    fields, R2's `horizon` is not (`yearsToTerminal`), so it printed `undefined` three times — and
    via T1's force-open, in every PDF. Pinned across every committed card.
  - **PROSE.** Linter **0 flags**. Two words changed from the brief's supplied text: `anchor\w*` is
    a house token, so "exit anchored on…" → "exit set on…" and "mature-anchored terminal" → "set
    against a mature vertical-software peer". Meaning preserved.
  - **HELD, needing dedicated basis pulls (shakedown grids were advisory-grade, not records):**
    **AORT** — its pull must first determine the FY2025 **+13% share-count step** (41.68 → 47.16M:
    issuance or converts?) before any dilution override; the floored 3-year CAGR of 5.62% compounds
    to **+24.4% dilution** over 4 years and is doing more damage to its ratio than any convention on
    the matrix. **VITL** — survival-blocked (0.76y runway vs 4y; **zero** financing on file: no
    S-3/S-1/424B5 and no Item 1.01 or 2.03 in twelve months). Re-engage on an Item 1.01/2.03
    financing filing, or free cash flow turning positive.
  - Gate: ruff + `mypy --strict` clean; `pytest -m "not network"` green on the committed artifacts.

- **R2 ENGINE — TERMINAL MARGIN, SURVIVAL GATE, PV, TAGGER (branch `feat/r2-terminal-margin`,
  2026-07-21). ENGINE ONLY — no underwrites in this build, per the R1 pattern.**
  - **WHY R2 EXISTS, concretely.** R1 needs a history worth reverting to. NCNO/MVST have a negative
    margin history; VITL/AORT are ramps with a guided forward reset that no trailing median
    describes; and **FUBO has no multiple series at all** — its `TEV/LTM EBITDA`, `TEV/LTM EBIT` and
    `P/LTM EPS` are ALL "NM" on a loss-making trailing year (EBIT −$106.2M), so there is no band to
    take a median of. That is a structural property of a loss-making name, not a data gap.
  - **THE RECIPE.** Analyst supplies terminal year / revenue / margin / exit multiple **per leg**;
    the engine builds EBIT_T → D&A_T (ratio × terminal revenue) → EBITDA_T → EV_T → equity_T →
    shares_T → value_T, then discounts at the house hurdle. **EV/EBIT is a first-class basis** (the
    formula adjusts, not a relabelled EBITDA run) because VITL's EBITDA band is vendor-defective
    while its EBIT row reconciles exactly. Conventions ratified in §7.
  - **WORKED EXAMPLE (NCNO facts, illustrative — no record written):** EBIT 900×12% = 108.0; D&A
    0.069264×900 = 62.34; EBITDA 170.34 × 14 = EV 2,384.73; − net debt 223.90 = equity 2,160.83;
    shares 109.4585M×(1.011119)^4 = 114.4085M → **value_T $18.89**; ÷ 1.15^4 → **PV $10.80**.
  - **TWO 1e6 UNIT DEFECTS FOUND AND FIXED — both caught by running real numbers, neither by a
    green test.** (1) **SHIPPED IN #173:** `compute_anchor` passed EDGAR net debt in DOLLARS into
    the $M-denominated reconciliation guard. Latent because nothing had been re-backfilled since the
    merge; the first real backfill spuriously withdrew **AORT's and CNXC's** base values. The pin
    could not see it because its fixture netted to **ZERO** net debt, where dollars and $M are
    indistinguishable — *a unit pin whose value is 0 is not a unit pin*. Fixed; fixture now carries
    $300M; all six R1 names reproduce their committed base exactly (+0%). (2) **IN THE NEW ENGINE:**
    $M equity ÷ a raw share count gave **$0.0000/sh** off $2.16bn of equity — plausible as "cheap"
    rather than obviously broken. Both now pinned by MAGNITUDE, never by not-None.
  - **THE OVERWRITE DEFECT IS CLOSED.** `anchor-backfill` now PRESERVES an operator's hand re-tag
    and REPORTS the machine's competing proposal instead of applying it. Verified on a dry run:
    AORT's, CNXC's and VITL's judgments all survive. Previously one backfill away from vanishing.
  - **THE ANCHOR NOW GATHERS FACTS ON EVERY PATH.** `compute_anchor` used to bail before touching
    EDGAR when R1 did not apply, so the very names R2 exists to underwrite committed an anchor with
    every input null. An unusable RECIPE is not a reason to withhold the EVIDENCE. Adds `ltm_fcf`
    (the survival input) with its basis stamped **annual, stated as such** — summing XBRL
    quarterlies into a claimed LTM is where a fabricated burn would come from.
  - **TAGGER — PROPOSE-ONLY, and it never writes.** On the committed book it independently
    reproduces **10 of 11** hand tags, including CNXC's `R1_NOT_ROBUST` from the leverage signal
    alone and AORT/VITL's `R2_NEEDED` from margin shape. The one disagreement is FUBO, whose
    committed hint is the machine placeholder `unknown` (proposes `R2_NEEDED`). **No hint writes
    this build — the operator ratifies.**
  - **STEP 0 — COHORT CLOSURE, and it did NOT fully close.** Canonical-sync earned its keep
    immediately: **AORT's two workbooks in the `-fix` worktree were STALE** (different bytes from
    canonical). Band values proved identical, so nothing moved — luck, not design. FUBO's canonical
    folder holds a full 10-file export; its local absence was a worktree gap. Guards across the
    cohort: **NCNO became runnable on reconciliation (1.08x pass, previously unrun)**; MVST/FUBO
    stay UNRUN; AORT 1.02x pass; **VITL remains the only trip, on both. No new trips.**
  - **COHORT GAPS, RECORDED NOT PAPERED OVER.** **FUBO is not underwritable from committed data:**
    `dep_amort` resolves to **$0.003M from FY2014** (twelve years stale), debt tags last filed
    **2020-06-30**, FCF is **FY2024**, and diluted WA reads **30.0M against 342.7M shares
    outstanding** — an 11x gap unresolvable from tags alone. **MVST** has no D&A tag at all and its
    net debt is UNKNOWN (the under-capture guard correctly refused). Both net-debt gaps need CIQ
    balance-sheet extraction, not EDGAR. Per operator default, FUBO STAYS in the cohort with its
    gaps recorded — dropping it would hide the problem.
  - **FOUND IN PASSING — NOT FIXED (scope).** `_latest_dep_amort` prefers the COMBINED D&A tag
    regardless of vintage, so FUBO takes a 2014 value of $0.003M over current split tags summing
    $38.5M. Affects any filer that switched tags. Queued.
  - **THE REVIEW OF #176 CAUGHT A REAL DEFECT IN THIS BUILD — fixed in-branch.**
    `burn_to_breakeven` defaulted to **0.0**, so a burning company valued its terminal year as
    though the burn were free: the survival block read FAIL at 1.25y of runway while the SAME
    record carried terminal net debt UNCHANGED from today's balance sheet. That is the exact
    direction of error R2 exists to prevent, and it applied to the whole cohort by definition —
    they burn. Now REFUSES when the survival block shows a burn and the fact is absent. The machine
    does not derive `burn × years` either: filling it in would be the machine proposing an
    assumption. An explicit `0.0` is accepted — that is the analyst stating it. Pinned both ways
    (`test_a_burning_company_must_state_the_cash_it_consumes`,
    `test_a_self_funding_company_needs_no_burn_fact`).
  - **INVARIANT (incident → guard, shipped Y):** `tests/test_terminal_margin.py` (38 pins: worked
    example step-by-step, both unit magnitudes, EV/EBIT basis, dilution/burn/D&A-ratio behaviour,
    degenerate guards, the survival fail/raise/accession/FCF-positive paths, and the
    confirmed-blocked-on-FAIL gate end-to-end) and `tests/test_tagger.py` (18 pins: the
    signal→proposal mapping on synthetic shapes, precedence, purity, absent-vs-disagree).
  - **A LIVING-ARTIFACT PIN WAS AT THE WRONG LAYER, fixed.** `test_dossier_page_logs_anchor_and_
    scenario_panels` used FUBO as its "dossier without an anchor" fixture and went red the moment
    FUBO earned one. The no-anchor case is now CONSTRUCTED — the invariant is a property of the
    RENDERER, and binding it to a live ticker made it a property of the queue.
  - Render: R2 card variant (terminal value AND PV both labelled, hurdle + years shown, survival
    panel with its runway arithmetic, tier badge), previewed light + dark. Prose-register linter:
    **0 flags** on everything this build wrote. Runway rounding aligned to the engine's own note
    (1.3y beside 1.25y was one number disagreeing with itself on one panel); the danger palette uses
    the design-system `--danger-*` tokens, not a hardcoded red that would not follow dark mode.
  - Gate: ruff + `mypy --strict` clean; `pytest -m "not network"` green. R1 scenario cards
    byte-identical after the frontend rebuild (emit-determinism pin holds).

- **BAND COHERENCE + RECONCILIATION GUARDS — FIFTH BAND-DEFECT CLASS, CLOSED (branch
  `feat/band-coherence-guards`, 2026-07-21).** VITL's CIQ Multiples export carried a `TEV/LTM
  EBITDA` row contradicted by its own `TEV/LTM EBIT` row. Nothing in the pipeline could see it: the
  parser read the labelled row correctly, the revenue and EBIT rows on the SAME sheet reconciled to
  EDGAR exactly ($64.272M EBIT, to four decimals), and the band's periodicity/span metadata was
  honest. The row was simply wrong — and a wrong denominator propagates silently into
  `anchor_base_value_per_share`, the number a human reads as the fundamental.
  - **ROOT CAUSE (diagnosed, reproducible — sharper than "vendor defect").** The `TEV/LTM EBITDA`
    row is populated against a **RENT-ADJUSTED** denominator. Backing the denominator out of the
    sheet's own TEV gives **393.1** against the Income Statement's **EBITDAR 390.5 (1.007x)** and
    its **EBITDA 79.5 (4.94x)**; the same ~1.0x-to-EBITDAR relation holds across the four most
    recent columns. VITL carries an imputed operating-lease charge of ~$311M against $79M of
    EBITDA, which is why the distortion is enormous on this name specifically. The EBIT row is
    unaffected — EBIT takes no rent add-back. **A re-pull will not fix it**: this is CIQ's
    calculation for this ticker, not a stale cell.
  - **TWO GUARDS, SHARING NO INPUT** (`vinci/dossier/band_guards.py`) so one vendor defect cannot
    satisfy both. **(1) Internal coherence** (parse time): TEV cancels out of the ratio of any two
    multiples off ONE column, so the sheet alone implies an EBITDA margin, an EBIT margin, and the
    D&A margin between them — asserts the identity (EBITDA ≥ EBIT ⇒ D&A ≥ 0) and an economic
    ceiling on implied D&A as a share of revenue. No market data, no EDGAR, no vintage question.
    **(2) Market reconciliation** (anchor time): `(market cap + net debt) ÷ current multiple` vs
    reported EBITDA. Market cap is read from the committed artifact and feeds `data_quality` ONLY —
    **no anchor value derives from it**, so the base stays the spot-independent fundamental it is
    documented to be (pinned: doubling market cap leaves every anchor value byte-identical).
  - **A TRIP DISQUALIFIES, NOT MERELY DOWNGRADES.** Flag composed onto band + anchor
    (`band_incoherent` / `band_unreconciled`, joined with any existing flag), multiple leg capped
    weak, and **no base value published at all**. "Weak confidence" is not enough when the number
    would still be read as the fundamental. Evidence (`implied_*_margin`) persists ON the band —
    additive/optional so pre-guard JSON round-trips — because the anchor runs from committed JSON
    alone and never re-opens a workbook.
  - **THRESHOLDS ARE FACE-VALIDITY CALIBRATED, NEVER OUTCOME-TUNED.** Set against the full sweep of
    all committed bands; each sits near the geometric midpoint of the worst HONEST reading and
    VITL's. No bound here has ever seen a forward return.

    | check | honest worst | VITL | bound | headroom |
    |---|---|---|---|---|
    | implied D&A / revenue | CNXC 11.14% | 41.91% | 25% | 2.2x / 1.7x |
    | implied D&A / recorded D&A | EPAM 4.20x | 35.53x | 8x | 1.9x / 4.4x |
    | market-implied EBITDA / recorded | CNXC 1.41x | 4.62x | 2.5x | 1.8x / 1.8x |

  - **BEAR-STATE CROSS-CHECK — CONVENTION ADOPTED 2026-07-22.** *"Bear legs are cross-checked
    against bear-state comparables whenever the name's own history contains no bear-state
    precedent; own-history floors from a growth-era-only window are inadmissible as bear
    multiples."* Trigger: IT's committed multiple series **opens in 2017Q1** — 9.3 years, entirely
    inside the growth era — so its own floor (16.95x, the COVID trough) describes a state the
    business is no longer in. The cross-section governs instead: declining information-services
    businesses price at **4.79 / 6.30 / 6.30 / 8.30x** (Ipsos, Clarivate, GTM, Forrester
    ex-impairment), median 6.30x.
    - **CONTAGION CHECK RUN — IT was uniquely exposed.** SMPL's and EPAM's bear legs already sit at
      bear-state levels, so neither needed re-setting. No other record carries a growth-era-only
      floor as its downside multiple.
    - **SMPL VERIFIED 2026-07-22 — THE INSTRUMENT'S FIRST CONFIRMATION.** Until now the
      convention had only ever REJECTED a bear leg (IT). SMPL is the first name run through it
      and CLEARED, which is the more important result: **it discriminates, it does not merely
      reject.** A test that only ever fails everything is not evidence.
      - **The evidence.** Declining US packaged-food comparables with clean income statements
        trade at **6.08x (INGR) – 8.57x (LW)** TEV/EBITDA on the ratified lease-inclusive basis;
        SMPL's recorded bear multiple **7.0x sits inside that range**, while the market prices
        the name **BELOW** the state at **5.65x**. Its recorded 10% bear margin equals the worst
        clean retention observed (**64.5% of normal vs the weakest survivor's 63%**). At the
        2026-07-21 close ($11.04) **no evidence-coherent cell falls below ~2.7:1** against the
        2.0 bar (floor 2.7458 at 9.58% × 6.08x); the recorded grid reads **3.88:1**. The
        entry-boundary pair is unmoved: **2.12 clears / 1.88 fails**.
      - **CONVENTION REFINED (2026-07-22).** *"A bear multiple ABOVE the current multiple is a
        TRIPWIRE that forces the evidence test — not a defect in itself. It is ADMISSIBLE when
        the current multiple sits BELOW the sector's own bear state, i.e. the market is pricing
        past the downside case rather than the bear leg assuming a re-rating up."* `vinci audit
        r1` raises exactly this flag on SMPL (**7.00x vs 5.65x**) and on **EPAM (6.00x vs
        4.87x)**; SMPL's is now DISCHARGED by evidence. **EPAM's is not — it is the next name
        owed this test** (queue item 12).
      - **WHAT THE EVIDENCE PULL COULD NOT ESTABLISH, and why it was not forced.** A full
        sector-median distribution is NOT recorded: reported EBIT is impairment-contaminated
        exactly in the bear state (GIS FY2026 EBIT $886M vs $3,305M prior on a 5.4% revenue
        fall), and the mechanical ex-impairment repair DOUBLE-COUNTS across overlapping XBRL tag
        families (KHC summed to $27.9B; GIS's "ex-impairment" EBIT exceeded its own prior year).
        The clean-comp RANGE governs instead — narrower evidence, honestly bounded, rather than
        a median carrying two charge-depressed denominators. Also unconfirmed at this sample:
        the *a-priori* expectation that packaged food holds margin through decline far better
        than information services — the two clean names point OPPOSITE ways (INGR 120%
        retention, LW 63%), so **n=2 does not establish it** and it is not claimed.
      - **REGISTER RULE ADDITION:** *"A verification tag carries its RUN DATE, its PRICE DATE and
        the PRICE explicitly."* A tag that says "verified" without naming the close it was
        verified at cannot be re-checked, and a run date silently implies a price that may not
        exist yet (this tag ran 2026-07-22 against the 2026-07-21 session — the latest completed
        close; writing "at today's price" would have been false).
  - **LEASE-BASIS CONVENTION — RATIFIED 2026-07-22. THE NET-DEBT BASIS STAYS LEASE-INCLUSIVE, AND
    THIS REVERSES A FINDING.** The 2026-07-22 IC review raised a basis-inconsistency concern: our
    net debt is lease-inclusive while the multiple band is a CIQ TEV multiple, so if CIQ's TEV
    excluded operating leases we would be deducting a liability the multiple never carried.
    **Workbook evidence settles it the other way.** The Historical Capitalization identity:
    **IT CIQ Total Debt 3,355.2 vs EDGAR ex-operating-lease 2,983 / including operating leases
    3,355 — exact to $0.2M**; VITL directional on the same test (54.2 against 17 / 62). CIQ's TEV
    **includes** operating leases, so our construction already matches the band's. **One ruler.**
    - Vendor lease MEASUREMENT diverges slightly on small names (VITL 7.8, SMPL 17.8) — documented
      noise, not a basis difference.
    - Reconciliation tolerance: CIQ prices multiples at FILING dates against quarter-end balance
      sheets, so small timing gaps are expected and are not evidence of a different construction.
    - **The agent's own back-solve was INCONCLUSIVE and said so** rather than calling it: the
      committed multiple is rounded to 1 d.p. and the mcap/multiple/EBITDA vintages are not
      aligned, so the misses (IT 2.6%, SMPL 8.0%, EPAM 9.7%) contradicted each other and were
      larger than the effect being detected. The workbook read at full precision is what resolved
      it — the lesson is that a rounded committed field cannot adjudicate a vendor convention.
    - The read-only impact table computed under the (now-refuted) hypothesis showed **no boundary
      would have moved** in any case: no PASS/FAIL, watch or avoid_priced flip, with WERN closing
      only 17.7% of its base-vs-spot gap. **No record changes.**
  - **KNOWN CIQ DEFECT CLASS #2 — PERIOD SPLICING ACROSS A REVERSE MERGER (found 2026-07-22, FUBO).**
    Distinct from the EBITDAR substitution above, and **neither guard catches it**: the vendor's
    LTM/trailing columns are stitched across a combination, blending the ACQUIREE's pre-deal periods
    with the registrant's post-deal ones into a single "trailing" figure for a legal entity whose
    predecessor changed. FUBO's `Total Revenue 5,304.1` LTM and its `Gross Profit 236.4 / 4.46%`
    are spliced across the **2025-10-29** Up-C combination (item 4): the pre-October periods are
    legacy Fubo's, the post-October ones the Hulu-Live-predecessor registrant's. The peer table and
    every margin computed off that LTM inherit the splice.
    - **WHY THE GUARDS ARE BLIND:** both test INTERNAL coherence of one column, or that column
      against market cap. A spliced column can be perfectly self-consistent and still describe no
      entity that ever existed. The tell is not in the sheet — it is the **predecessor change**
      (here: a fiscal-calendar shift to Disney's 52/53-week year, comparatives showing
      `Pre-combination net contributions`, and an `Acquisition of <the ticker's own name>` line in
      investing).
    - **DETECTION RULE FOR NOW (manual, until something machine-checkable exists):** before
      underwriting any name, check EDGAR for a business combination inside the trailing window. If
      one exists, **the vendor trailing panel is unusable** and the registrant's own filed
      statements are the only basis. A candidate future guard: flag when a filer's fiscal-period end
      dates SHIFT between consecutive filings, which is cheap and would have caught this.

  - **FULL SWEEP RUN — VITL IS THE ONLY NAME THAT TRIPS.** All 11 committed bands, both guards, real
    run. 9 with a CIQ export pass internal coherence (FUBO/VRRM have no local export — check not
    runnable, which is NOT a pass); 7 pass reconciliation (MVST/NCNO/VRRM/FUBO lack EDGAR net debt).
    No silent fixes; nothing else to escalate. **The brief's name list named WERN (no committed
    dossier, no CIQ export) and omitted FUBO (has both)** — swept by committed band, discrepancy
    reported rather than reconciled away.
  - **COVERAGE HOLES, RECORDED NOT PAPERED OVER.** (a) Guard 1 needs a `TEV/LTM EBIT` row and guard
    2 needs EDGAR net debt — a name missing either is UNRUN, and unrun is reported as unrun, never
    as clean. (b) The guard is skipped when implied EBIT margin is negative (the identity stops
    holding) — territory R1's positivity guard already routes to R2, so no live coverage is lost.
  - **DELIBERATE DEVIATION FROM THE BRIEF (flagged).** The brief specified "close from export else
    Polygon at as-of". The CIQ Multiples sheet carries no price row, and every committed dossier
    already has a CIQ market cap, so the Polygon fallback would be unexercisable by any real run —
    not written, per "don't build speculatively".
  - **INVARIANT (incident → guard, shipped Y):** `tests/test_band_guards.py` — real observed VITL
    multiples frozen, synthetic 5x understatement, the negative-D&A identity, vintage noise at
    SMPL's real 1.79x and EPAM's real 4.20x, honest IT/CNXC controls, absent-row gap-not-defect,
    flag composition, and end-to-end through `compute_anchor`. **Living committed artifacts are
    asserted only against phrasing- and value-independent invariants** (a flagged band publishes no
    base; the margin identity holds), so a corrected re-pull turns them green rather than red.
  - **ACCEPTED RISK — CLOSED 2026-07-21 by `feat/r2-terminal-margin`** (`preserve_operator_tag`).
    Was: a hand re-tag of an anchor block is overwritten by `anchor-backfill`, which recomputes from
    EDGAR. This already applied to AORT's re-tag and is
    unchanged by this build — not newly introduced here. Falsifier: a re-tag silently disappearing
    after a backfill run. Fix (queued, not built): make the backfill preserve an operator re-tag the
    way `build.py`'s `_preserve_unless_source` guard preserves mirror sources.
  - **FOUND IN PASSING — NOT FIXED (scope).** `own-history-refresh` would silently DROP a committed
    `ev_ebitda.note`: its branch only re-applies the "trailing only" note when
    `ev_ebitda_adjusted_fwd` is absent, and for VITL it is present. Caught by dry-run diff, so
    VITL's band was written surgically (`own_history` alone, after confirming read-only that
    `range_position` and `ev_ebitda_percentile_5y` are byte-identical on refresh). Queued, not
    silently patched.
  - **DATA (C2).** **VITL → the R2 cohort** (now NCNO / MVST / FUBO / AORT / VITL):
    `recipe_hint="R2_NEEDED"`, `applicable=false`, **anchor base $4.7561 WITHDRAWN** (not
    downgraded) — `valuation.own_history.median` 4.198793x derives from the defective series.
    Reason recorded (trailing ramp 0→11.6% EBIT margin over four years against a guided forward
    reset: FY26E adjusted EBITDA $0–10M, gross margin 28% from 39%, founder exit, cash burn — no
    trailing median describes this business in either direction; it is a forward-margin question),
    with the defect and its source layers in `data_quality_detail`. **CNXC → `R1_NOT_ROBUST`** (new
    enum value, flagged as new — no prior precedent existed): net debt 139% of anchor equity, ±1x
    EV/EBITDA moves value/share ~89% of spot ($21.47 at $24.24), so no R1 grid is robust to one turn
    of multiple error. `applicable` and the base are LEFT STANDING, following the AORT re-tag
    precedent — CNXC passes both guards, so its arithmetic is honest; what the re-tag records is
    that an honest answer cannot DISCRIMINATE at this leverage. Withdrawing the number would
    conflate "not robust" with "not computable", the distinction the enum exists to make. Re-engage:
    reported net-debt/EBITDA below ~3.5x, or absolute EBITDA stable two consecutive quarters. Both
    edits byte-preserving; `frontend/dossiers/{VITL,CNXC}.json` mirrors rebuilt in the same commit
    so the deployed panel never shows the withdrawn $4.76.
  - **BRBR BOOK-VALUE CHECK — THE TRIAGE WAS RIGHT; THE 2026-07-21 PULL WAS WRONG.** `book value/
    share −$4.28` **is** committed, at `mechanical.stock_info.book_value_ps`, `status: present`,
    `source_ref: "CIQ Financials→Balance Sheet→Book Value/Share (latest)"`, and cited in the
    leverage narrative. The 2026-07-20 triage asserted it correctly; the 2026-07-21 disposition pull
    reported it unsourced — a **false negative in that pull**, logged here rather than a
    non-existent unsourced assertion by the triage. Cause: the pull searched prose for "book value"
    instead of the structured key.
  - Gate: ruff + `mypy --strict` clean; `pytest -m "not network"` green (exit 0) on the
    freshly-committed artifacts, per the ARTIFACT-PASS RULE.

- **T1 PRINT AMENDMENT — THE PDF IS THE COMPLETE RECORD (branch `feat/print-audit-tier`,
  2026-07-21; operator decision).** DESIGN RULE v2's tier-2 print fate FLIPPED: the on-demand /
  audit tier now **prints expanded** in both existing exports (Brief and Full) — every `<details>`
  force-opens in the PDF regardless of its on-screen state, its summary printing as the section
  header (disclosure markers hidden; paper cannot be clicked). The WEB surface is unchanged
  (still collapsed). Direction came from the operator reviewing the exports ("why is the pdf not
  loading all the dropdowns and their headers?" → "by default print them irrespective of open
  status"). The cite-scope invariant holds in the new direction: a block's endnote markers and
  its Sources list live inside it and now print TOGETHER — fate still shared. The uw-reasons
  print carve-out is REMOVED as subsumed (one rule, no special case). **CLAUDE.md's DESIGN RULE
  v2 clause amended in the same commit** — the constitution must not describe a print fate the
  build no longer has. Exports run longer (the audit tier adds pages); that is the point.
- **UNDERWRITE TEAR SHEET — THE CARD LEADS WITH THE DECISION (branch `feat/uw-tear-sheet`,
  2026-07-21; PR open, NOT merged).** The underwrite card rebuilt as an institutional tear sheet,
  in the ONE component every surface renders (dossier Brief tab, first-analysis page, theme
  watchlist) — global by construction, future surfaces inherit.
  - **MASTHEAD** (5 stat cells: target / reward:risk / entry / downside / method) leads the card,
    and the card leads the Brief tier (was 9th of 10 — #161 appended it; anti-anchoring
    unaffected: that rule protects the MACHINE's sealed proposal, and the teaser is untouched).
  - **THE LABEL IS A STATE MACHINE, price beats status:** `priced` (base ≤ spot — a WERN-shape
    avoid has no upside to target, whatever the status says) → `target` (recorded verdict above
    spot) → `base` (pending — the machine's only reachable state). Node-pinned with a synthetic
    CONFIRMED-but-priced record; both regressions verified red before landing. The BUY/AVOID word
    is the LEDGER's, joined at build (`_ledger_by_ticker`) because the theme watchlist never
    loads the ledger snapshot — the card never invents a verdict of record. "Verdict · BUY"
    labeling (a bare green BUY chip reads as a sell-side recommendation; this fund's is a sealed
    human verdict). PASS/FAIL renders only while the call is open.
  - **RANGE RAIL beside the scenario table** (the operator's side-by-side idea, unlocked by
    STAGGERED labels — each label owns a row tied to its tick by a hairline lead; the old
    one-row-of-labels layout was the only reason side-by-side "didn't fit"). The bar stays
    HORIZONTAL: one row of a football field, the research convention — a vertical bar was
    prototyped, researched, found to be NO research object, and dropped (recorded in the layout
    study). Table columns sized to ink (938→552px; ~350px was dead), rail fixed 360px. Card
    1,972 → ~880px over the whole pass (−55%) with MORE information on screen.
  - **READ ORDER:** masthead → split (table + rail) → implied-odds (#165) → rationale →
    thesis-breaks → leg reasoning (collapsed; PRINT-FORCED open — a printed grid with no
    justification would contradict the no-reason-no-compute rule) → methodology (collapsed,
    print-EXCLUDED: provenance tier) → sources → inputs → foot. The recipe CHAIN moved to the
    on-demand tier (it is a drift guard, hence provenance); the recipe NAME stays in the
    masthead's Method cell.
  - **PRINT, DIAGNOSED FROM THE OPERATOR'S ACTUAL PDFs:** the Brief export opened with the header
    orphaned on a ~90% blank page 1 — the pre-tear-sheet rule `.uw-card { break-inside: avoid }`
    had turned the now-page-tall card into an unbreakable monolith that jumped whole to page 2
    (`.wl-row` had the same disease waiting). Atomicity moved DOWN a level: card and row
    fragment; their building blocks (masthead, rail stack, split halves, chips, reasoning,
    Sources runs) carry the avoid. Verified with a REAL export (headless Brave print-to-pdf):
    page 1 now carries the entire decision surface. A4 also cannot hold the two-column split —
    explicit `@media print` stack rules, not reliance on the viewport query.
  - **MERGED WITH #165 (position monitor) — same component, both intents kept:** impliedOdds
    ported verbatim (committed mark, dated, never a live fetch); the two-ratio rule holds across
    the masthead (underwrite ratio labeled "at underwrite" in the Reward:risk cell; accepted
    ratio in the Entry cell beside its frozen price; #165's pin re-pointed to the new anchors,
    every semantic assertion unchanged). **The merge caught a real class:** both branches had
    added the entryPrice/ratioAtEntry emit and the auto-merge stacked them as DUPLICATE dict
    keys (silently last-one-wins in Python) — deduped to ONE omit-when-absent emit, so
    un-entered records (WERN) stay byte-identical across re-emits.
  - **THEME EMBED MADE REGENERABLE (INVARIANT SHIPPED):** the theme JSON embeds each watch
    name's card, pinned equal to a fresh build — but the freeze source is git-ignored, so any
    card-shape change was unsatisfiable in CI. `refresh_theme_cards()` re-embeds from committed
    records only; COMPOSES with #166's re-seed guard (theme preserved whole when the freeze
    source is absent; the embedded cards' own source is the committed records, so they refresh —
    with no records it is a no-op, the same discipline one level down). Pinned by
    mutate-the-embed → byte-for-byte restore → idempotent no-op.
  - **Other invariants shipped:** headline state machine node pin (3 states distinct, price
    beats status, ledger word never invented, PASS only while open); summaries restyled from
    11.5px/400/ink-3 ("styled to be ignored") to 12.3px/650 + explanatory names.
  - **DEFERRED, recorded:** Option 2 of the layout study — a TRUE football field (underwrite
    range vs the 52-week trading range on one axis; IT's ranges nearly coincide, 121–427 vs
    124–404 — "the bull case is where the stock traded a year ago"). Needs the 52-week field
    plumbed through build.py: a data change, not a layout one.
- **POSITION MONITOR v1 (A2) — BUILT (2026-07-21, feat/monitor-v1).** The ledger froze what was
  decided; nothing reported what happened since. `vinci/monitor.py` + `python -m vinci monitor`
  (MANUAL — no scheduler), reading the COMMITTED `decision_ledger.jsonl` (the working DB is
  empty on any fresh clone; the JSONL is the durable record).
  - **Benchmark by CAP BAND at ENTRY** — `<$4B → IWM · $4–25B → MDY · >$25B → SPY`, named
    constants, face-validity-chosen. Assigned: **VRRM $0.72B → IWM · IT $9.87B → MDY · SMPL
    $1.02B → IWM**, shares source-stamped (IT/SMPL scenario-record diluted shares; VRRM the
    dossier's EDGAR XBRL shares_out). The ledger has NO amendment row type, so the committed
    `data/monitor/benchmark_assignments.json` **SUPERSEDES** the row's `benchmark` field for
    scoring — IT's logged IWM is wrong for a $9.9B name and is corrected FORWARD; **no row was
    mutated**, and every supersession prints in the run + the snapshot notes + the web card.
  - **Excess** = position return − its assigned benchmark's return over the SAME window. BOTH
    sides PRICE return (dividends excluded on both) — stated in the module, the snapshot, the
    terminal table and the UI; never mixed with a total-return series.
  - **BUY−AVOID spread** = mean(BUY excess) − mean(AVOID excess). An AVOID falling vs benchmark
    has NEGATIVE excess → subtracting it makes the spread MORE positive (being right about a
    terminal decline pays exactly like being right about an overshoot). Pinned BOTH directions.
    An empty leg → `None` + reason, never 0.0. **First read: +14.43 pp — DIAGNOSTIC ONLY**
    (0/3 resolved; both BUY legs 0 days old, so the number is carried entirely by VRRM).
  - **Freshness/trigger panel:** last evidence date = underwrite date OR a later visible
    `[amended …]` tag; EDGAR filings since → UNREAD PRINT flag; next print ESTIMATED from the
    filer's own cadence (labeled); triggers verbatim. **The machine FLAGS, never adjudicates** —
    pinned by asserting the model carries no fired/breach field. All three currently GREEN;
    IT's next print ~2026-08-05, its first trigger window. WERN surfaces as a tracked
    non-position (watch triggers + avoid_priced).
  - **Sector fix, forward-only:** SIC major group 87 (engineering/accounting/research/management
    services) fell through to "Other" — mislabelling the IT leg and 7 queue names
    (HURN/WLDN/ACM/G/BAH/BWMN/STN). Mapped at the FAMILY level → **Industrials** (GICS
    Professional Services); the finer reading still rides on `industry` (IT's CIQ-GICS is "IT
    Consulting and Other Services"). The monitor RE-RESOLVES for display and says so; **the
    frozen row keeps "Other" forever** (pinned).
  - **Display:** decision log gains the spread card (caveats + sign convention ON SCREEN), live
    per-leg columns, and the freshness panel; the scenario card shows **both ratios labeled** —
    underwrite vs accepted-at-entry (**IT 7.04 vs 6.69**, a divergence one number would hide) —
    plus a DERIVED *market-implied bear weight = (base − spot) ÷ (base − bear)* at the COMMITTED
    mark (**SMPL 80% @ $10.92 · IT 87% @ $141.06**). The browser never fetches a live price;
    no mark → no line.
  - **INCIDENT #4 (recurrence, recorded):** the build re-seeded `frontend/radar/sweep.json` to
    2026-06-17 again in the primary worktree (absent component-a manifest) — reverted by hand;
    the guard is queue item 3. Third occurrence.
  - Gate: ruff + `mypy --strict` clean; **761 passed** (+11); build ×2 idempotent; both display
    changes browser-verified; `data/monitor/` allow-listed in `.gitignore` (derived analysis —
    a spread nobody can re-read is not evidence).

- **FIRST BUY RECORDED — IT (PR #161, 2026-07-21). THE FUND NOW HOLDS A LIVE PAPER POSITION.**
  - **THE VERDICT.** Human-recorded **BUY**, `verdict.status="confirmed"`, recorded 2026-07-21.
    **entry_price $141.06** (Polygon close 2026-07-20 — 2026-07-21 had not traded at record time),
    **ratio_at_entry 6.686:1** (legs unchanged; only the spot moved from the 140.19 underwrite).
    The ≥2.0 gate was re-checked at the live spot BEFORE anything was written.
  - **THE MACHINE ABSTAINED.** IT's committed lean is `mixed` → `derive_proposal` returns NO
    proposal → `disposition="no_proposal"`, `machine_lean="mixed"`, sealed from the committed
    artifact (`assembled_at 2026-07-10T07:02:39Z`), `revealed_pre_verdict=false`. **The fund's
    first BUY is a COLD HUMAN CALL** — exactly the cell the 2026-07-13 pivot says is the human's
    product. It also means the machine-proposal spread curve starts EMPTY on this name: entry 1 of
    the human curve has no machine counterpart, so the machine-vs-human decomposition begins at
    n=0 for the proposal leg. Worth remembering before reading any early spread.
  - **LEDGER ROW** `V-IT-screen2-20260706` appended (append-only; VRRM untouched, pinned by a new
    test): candidate `IT-screen2-20260706` (from `ranked_queue.jsonl` — **the dossier carries no
    candidate_id**, the brief's stated source was wrong), internal `SEC-0000749251-IT`,
    horizon **180d**, confidence **medium** (both analyst-answered, not guessed), benchmark IWM.
  - **THESIS-BREAK TRIGGERS** (recorded in `reunderwrite_triggers`, the field that already renders
    on every surface — a parallel `thesis_break_triggers` list would have been a second home for
    one concept): Q2-2026 print (early Aug) contract-value growth decelerating/negative → re-underwrite
    the bear leg · revenue below FY26E consensus two consecutive quarters → re-test base at 12x ·
    operating margin below ~16% ex one-offs → regime assumption fails.
  - **RATIONALE CLAIMS RE-DERIVED BEFORE RECORDING** (the brief asserted them; the record states
    what the math says): stress leg (rev −20%, margin 13%, 8x) → **$75.24 and 2.02:1**, NOT the
    asserted "~$76 / ~2.1:1" — it clears the 2.0 bar **barely**, and the recorded rationale now says
    so. FCF yield 10.8% ≈ "~11%" ✓; base leg reproduced to 1e-6 against the committed result.
  - **BAND REFERENCES RE-POINTED** to the #162-corrected 9.3y band (n 38, as-of 2026-07-17, sha
    `66405c3bc0`): low 9.34→**7.46**, median 22.71→**23.38**, 75th 26.12→**26.82**, current
    7.5→**7.97 @ 3rd pctile** (was labelled 0th). "Base below median" still holds. The three method
    sentences were **ratified** (`ratified_by="analyst"`, `ratified=2026-07-21`).
  - **SMPL RESUMED** via analyst gate adjudication (recorded IN the record, new
    `gate_adjudication` field — a gate that fired and was walked past must leave a trace):
    "~80% one-off bar fired at 72.8%; residual vendor-definitional, not operating; RESUME 2026-07-21".
    Run: bear $6.95 · base $26.90 · bull $40.21 at spot $10.92 (2026-07-20) → reward 15.98 / risk
    3.97 → **4.03:1 PASS**. `verdict.status="pending_analyst"` — **the machine did not ratify.**
    Every statistic the reasons assert was re-derived from EDGAR and matched exactly (7yr clean
    median 15.51%, FY2020 worst 9.58%, FY2022 best 17.35%, FY2025 ex-impairment 15.01%).
  - **SMPL 10-K FINDING — THE IMPAIRED ASSET IS NAMED, AND IT IS THE THESIS.** 10-K
    0001702744-25-000046 Note 5, verbatim: *"…identified potential indicators of impairment for the
    **Atkins brand** indefinite-lived intangible asset and the licensing agreements finite-lived
    intangible asset… resulting in a loss on impairment of $60.9 million"*, triggered by *"declines
    of future revenue projections"*. The one-off is not incidental — the company impaired the exact
    brand the bear leg is about. **This cuts toward the bear/value-trap leg and the analyst should
    weigh it at the verdict**, not read the impairment as a clean add-back.
  - **INVARIANTS SHIPPED (INVARIANT RULE):** `test_entry_price_refuses_a_price_that_never_traded`
    (negative pin: 0/−1 rejected — every forward return divides by this number) + its positive pin;
    `test_committed_ledger_is_coherent_and_append_only` (e2e on the committed ledger: every payload
    re-validates through the disposition-coherence validator, columns must agree with payload,
    entry_ids unique, the original VRRM row can never vanish);
    `test_committed_records_that_opened_a_position_carry_their_entry` (phrasing-independent).
  - **OPERATOR / NEXT (queue, in order):**
    1. **A2 monitor build is ACTIVATED** — a live position with an early-Aug trigger and no monitor
       is a standing instruction nobody is watching (see the deferred-list entry, now un-deferred).
    2. **Assembly-path provenance stamp** — `own_history` gets sha/mtime only on the REFRESH path;
       a fresh `assemble` still writes a band with no file provenance, so the #162 stale-read class
       is only half-closed.
    3. **Shared `annual_series` longest/first-alias rule** — still unfixed (own-history-local and
       anchor-local only). **Fix this BEFORE any `attach_midcycle` work**, which would inherit it.
    4. **IT's ledger benchmark is IWM** (inherited default, VRRM precedent). IT is a ~$9.9B name;
       IWM is small-cap. The excess-return leg of the spread may be measured against the wrong
       index — decide before the 180d horizon closes.
    5. **The card shows the UNDERWRITE ratio (7.04 @ $140.19), not the ENTRY (6.686 @ $141.06)** —
       both are correctly labelled and neither is wrong, but `entry_price`/`ratio_at_entry` are not
       plumbed to the card, so the entry is visible only inside the rationale PROSE. Surfacing them
       structurally is a RENDER change → needs a preview per the PREVIEW RULE.
- **OWN-HISTORY BAND REFRESH + SELF-DESCRIBING PERIODICITY METADATA (PR #162 — **MERGED to main
  2026-07-21**, rebase, head `f87e74d`).**
  - **MISDIAGNOSIS → DETECTION → REAL FINDING.** A brief asserted IT's "quarterly" multiples file
    held ~20 ANNUAL closes mislabelled as quarters. **Detection refuted it:** every committed AND
    on-disk band shows **91-day (quarterly) spacing** — IT's committed 21 dates are quarter-ends
    (2021-06-30 … 2026-06-24), genuinely quarterly over 5.0y. The premise was withdrawn. The REAL
    defect is **window staleness**: 6 committed bands were built from SHORTER exports than what's now
    on disk (IT 21→39 closes / 5.0→9.3y; EPAM 19→38 / 4.8→9.3y; SMPL 20→36; BRBR 19→27; CNXC 19→23;
    VITL 19→24; MVST 4→6). A band could read as more/less history than it holds with nothing on the
    record to say which.
  - **REFRESH RULE ADOPTED:** own-history bands recompute from the CURRENT on-disk CIQ export; every
    band now stores `periodicity_days_median`, `window_span_years`, `periodicity`, `source_file`, and
    a fail-loud `data_quality="periodicity_mismatch"` (annual spacing on the quarterly Multiples tab).
    Computed in the ONE shared loader `_own_history_band` (range_position / bands / refresh can't
    drift). CLI `own-history-refresh --tickers …[--dry-run]` writes ONLY `own_history.value`
    byte-preserving (JSON-surgical `dump(indent=2, ensure_ascii=False)` reproduces committed bytes
    exactly; a model round-trip drifts older-schema dossiers). A name with no on-disk CIQ →
    "awaiting corrected export", left untouched.
  - **CONFIDENCE now span-based:** the multiple leg is `firm` only if **window_span ≥ 5y AND
    periodicity == quarterly** (and no mismatch flag) — never raw close count.
    `ANCHOR_FIRM_MIN_MULT_QUARTERS` retired for `ANCHOR_FIRM_MIN_MULT_YEARS=5.0`. A pre-metadata band
    (span UNKNOWN) → weak (the safe read). This CORRECTED SMPL: 20 closes but only 4.98y span →
    multiple leg now weak.
  - **RE-BACKFILL (scope BRBR/CNXC/EPAM/IT/SMPL/VITL/MVST):** medians moved, anchor bases recomputed
    (byte-preserving, own_history + anchor only): **EPAM $225.55→$306.05 (+36%)** (median 16.2→22.4x,
    leg firm on 9.3y), IT $337.96→$348.64 (+3%, median 22.7→23.4x), VITL $4.35→$4.76 (+9%), BRBR
    $56.20→$55.41 (−1%), CNXC/SMPL bases unchanged (metadata + confidence only), MVST stays R2. **NO
    triage-tier flips** vs the 2026-07-17 spot (EPAM strengthens +154%→+245% but stays PRIORITY).
  - **SCOPE HELD:** AORT NOT touched (PR #161 owns it; its band matched anyway); NCNO/VRRM matched;
    **WERN detect-and-report only** — its on-disk band is 43 quarterly closes / 10.3y, **no mislabel**,
    recorded-verdict inputs left as-used.
  - **IT BUY and the SMPL run remain HELD** pending analyst re-ratification against the corrected
    9.3y band. Report-only: IT's chosen legs barely move (bear 9.5x 5→5%ile, base 15.0x 15→11%ile,
    bull 20.0x 25→24%ile); **"base below median" still holds** (median 22.7→23.4x); current-multiple
    percentile 0→3% (the longer window contains a lower 7.46x trough). The extended window does NOT
    invalidate the pending IT underwrite — it makes the base marginally MORE conservative.
  - **SMPL STALE-READ INCIDENT (found in review of this same PR, 2026-07-21; fixed in-branch).**
    The first pass refreshed SMPL from a STALE same-named export — the worktree copy
    (sha `680fd7bee7`, 21 closes, 4.98y) — because the copy step **skipped SMPL as "already
    present"** while the canonical primary export had been replaced hours later (sha `7bd83a1103`,
    36 closes, 2017-12-29→2026-07-17, **8.55y**). The artifact was internally consistent and
    therefore silently wrong: the new span guard dutifully applied a correct rule to bad input and
    demoted SMPL's multiple leg firm→weak on a window that does not exist. Nothing in the record
    could show it — `source_file` recorded a NAME, and both files share that name.
    **CORRECTED:** SMPL band median 16.34→**17.85x**, n 20→**35**, span 4.98→**8.55y**, multiple leg
    weak→**FIRM**, anchor base $38.43→**$42.31 (+10%)**. Overall stays weak (revenue-tag conflict,
    #160). **Two rules adopted:**
    (a) **HASH-STAMPED PROVENANCE** — every band stores `source_sha256` + `source_mtime` of the file
    actually read, so a stale read is visible IN the artifact rather than reconstructed later;
    (b) **CANONICAL-SYNC-ALWAYS** — the refresh path syncs from the canonical CIQ root and ALWAYS
    overwrites (`--canonical-ciq`); there is no skip-if-present, and a missing canonical folder FAILS
    LOUD rather than reading unknown-vintage bytes. Pinned by a stale-local-copy test.
    The other six were re-stamped with the hashes of the files their refresh actually read —
    **provenance-only; every band value byte-identical** (verified field-by-field).
    ⚠ **SMPL's median moved 16.34→17.85x**, which is the reference the held SMPL underwrite's 12.5x
    base was set against ("just under the 25th pctile") — re-check that reference when SMPL resumes.
  - **SIBLING-DRIFT INCIDENT (found in the second review of this PR, 2026-07-21; fixed in-branch).**
    Refreshing `own_history` ALONE broke the module's own stated invariant. `range_position`,
    `ev_ebitda` and `ev_ebitda_percentile_5y` all read the SAME Multiples close series and share
    `_own_history_band` expressly "so the two can't drift" (ciq_sheets docstrings) — the refresh
    updated the band and left the siblings on the OLD export, so every one of the 7 carried a
    self-contradicting valuation block: SMPL a 35-close band beside a string reading *"median 16.3x
    over 20 closes"*; EPAM band 22.4x vs string 16.2x; `ev_ebitda` stale on all 7 (IT 7.5 vs band
    current 7.97). **`range_position` renders on the dossier page**, so an analyst would have read the
    stale string next to a chart drawn from the new band. **FIXED:** the refresh now recomputes the
    whole multiples-derived CLUSTER atomically (`replace_valuation_fields`, not a single-field
    writer), preserving `_valuation`'s trailing-only blind-flag and touching
    `ev_ebitda_percentile_5y` only when it was CIQ-sourced (it is EDGAR-screen-sourced when the
    screen knew it). Anchors re-verified **0 changed** — the defect was display-layer only, no
    valuation math moved. **INVARIANT SHIPPED:** a coherence pin asserts every committed dossier
    quotes the SAME median and close-count in `own_history` and `range_position` (it failed on the
    pre-fix artifacts, which is how it was caught).
  - **STILL OPEN (unchanged by this):** the shared `extract_points`/`annual_series` longest/first-
    alias rule (this was own-history-local + anchor-local); and the operator may want a standing
    refresh cadence so committed bands don't silently lag new exports.
- **IT UNDERWRITE RUN + DOSSIER-PAGE LOG + AORT→R2 (branch `feat/it-underwrite-anchor-panel`,
  2026-07-20; PR open, NOT merged). TWO VERDICTS PENDING THE ANALYST — the machine set none.**
  - **IT (R1, WERN-method): ratio 7.04 vs the 2.0 bar → PASS, `verdict.status=pending_analyst`.**
    bear $121.20 (EV/EBIT 11.7x, normFCF $560.9M) · base $273.85 (17.5x, $801.6M) · bull $426.63
    (22.9x, $942.5M) at spot $140.19 (Polygon 2026-07-17); reward 133.66 / risk 18.99.
    **CAVEAT THE RATIO HIDES:** 7.04 is driven by a SHALLOW bear, not a conservative base — the
    bear leg sits only −13.5% below spot, so the risk denominator is small. Harden the bear before
    reading the ratio as a 7:1. Facts pulled from the committed anchor block (#158/#160-verified);
    `diluted_shares` converted anchor-raw→MILLIONS (the runner's unit contract — a silent 1e6 trap).
    Assumption `method` sentences are DRAFT — ratify at review (the WERN precedent).
  - **SMPL — STOPPED AT THE STEP-0 GATE, no scenario record written.** The FY2025 gap (EDGAR GAAP
    EBIT 157.3 vs CIQ 241 = 83.7) is explained only **72.8%** by a quantified one-off — the
    **$60.9M** intangible impairment (`ImpairmentOfIntangibleAssetsExcludingGoodwill`, 10-K
    0001702744-25-000046; the 10-K's only other operating one-off is $0.8M transaction costs). The
    residual ~$22.8M traces to CIQ-vs-GAAP normalisation (intangible amortisation $16.9M + those
    costs), NOT a recorded charge. Below the ~80% bar → stopped per the brief.
    **Substantively the finding cuts the other way and is the operator's call:** FY2025 margin ex
    the impairment = **15.0%**, essentially AT the 7yr clean median (15.51%) — i.e. NO structural
    margin break. That is **materially different from the ~16.6% the brief anticipated** (−1.6pp),
    so the base-reason append would be required if SMPL is resumed.
  - **Dossier-page log LIVE (read-only, additive):** every dossier with a committed anchor now
    renders a "Screening anchor — not a verdict" panel (margin+years+confidence, multiple+closes,
    anchor base + EV/EBIT, `data_quality` flags, reason); a dossier with a committed
    `scenarios/<T>.json` also renders the analyst's card via the SAME `uw-card.js` the watchlist
    uses. Dossiers without an anchor are untouched; **WERN's theme-watchlist card is untouched**
    (build.py unchanged, WERN records unchanged). The record is read ONCE for both page paths so
    the #159 "existence from the index, never a 404" pin holds UNCHANGED at one call site.
  - **AORT → the R2 cohort** (joins NCNO, MVST, FUBO): `recipe_hint="R2_NEEDED"`, corrected values
    and `applicable` kept as-is, reason recorded — *"margin history low-single-digit (corrected 5yr
    median 2.72%); bull case is a forward ramp to a regime that has never existed (consensus 20%+
    FY26E) — mean-reversion premise does not fit; route to forward-margin recipe."* No verdict
    recorded. Byte-preserving edit via `replace_anchor_block`.
  - Also caught up: the committed `frontend/dossiers/{EPAM,SMPL}.json` mirrors, stale since #160
    (Cloudflare rebuilds at deploy, so the committed mirror had lagged).
- **ANCHOR REVENUE-TAG DEFECT — FOUND, FIXED, BOOK RE-VALIDATED (branch
  `fix/anchor-revenue-tag`, 2026-07-20; PR open, NOT merged).** The R1 anchor's margin DENOMINATOR
  was chosen by *longest series*, which for AORT selected `Revenues` — a PARTIAL/segment measure
  reading **$30–45M for FY2011–17 where the ASC-606 tag reads $180–190M (~4x)**. That fabricated
  38–50% "margins", a false **15.83%** anchor median over FY2009–2021 (containing **zero** of the
  current business), and a `firm` confidence on invented years. Found by the normalization-basis
  pull, not by a test — the anchor was internally consistent and therefore silently wrong.
  **FIX (anchor-local, by design):** `anchor.py` now selects the denominator by MEANING via
  `_REVENUE_TAG_PREFERENCE` (606-Excluding > 606-Including > `Revenues` > `SalesRevenueNet`) —
  *fewer VALID years beats more invalid ones* — and EBIT is intersected onto exactly those years.
  **Fail-loud guard:** two candidate tags disagreeing >25% on a shared FY set
  `data_quality="revenue_tag_conflict"` + the tag/gap detail, and the TOTAL tag wins; **no**
  total-revenue tag at all → `recipe_hint="ANCHOR_UNRESOLVED"`, `applicable=false` (never a margin
  off a partial denominator). **Confidence gained a VALIDITY component:** any fired flag CAPS the
  margin leg — and the overall — at `weak`, however many years underlie it (AORT read `firm` on
  fabricated years; that cannot recur). **BLAST RADIUS (re-validated all 7 committed anchors in
  `--dry-run` diagnostic mode): 3 of 7 moved, but only ONE value moved** — AORT margin
  15.83%→**3.87%** (13y→10y), base **$57.29→$21.90 (−62%)**, ev/ebit 42.0→**72.7** (the multiple leg
  is now visibly wrong for the margin profile too), `firm`→`weak`. EPAM and SMPL moved
  METADATA-only (conflict flagged against a partial `SalesRevenueNet`/`Revenues`; **bases
  unchanged**) — but **SMPL's overall confidence drops `firm`→`weak`**, so of the three
  firm-confidence PRIORITY names only **IT** survives. BRBR/CNXC/IT/VITL unchanged and left
  **byte-identical** (0/0 diff). **Triage impact:** AORT falls from PRIORITY UNDERWRITE (+129%) to
  ≈**−13%** vs the 2026-07-17 spot. **Tests:** tag-preference, conflict-guard (total wins),
  applicability-flip, confidence-cap, byte-preserving `replace_anchor_block`, `anchor_changed`
  timestamp-only no-op. Green (ruff + mypy --strict 102 + pytest).
  **STILL OPEN — the broader item is NOT closed by this:** the shared `extract_points` /
  `CONCEPT_ALIASES` first-alias resolver and `midcycle.annual_series`'s longest-alias rule are
  **untouched by design** (changing them would hit `_attach_midcycle` + 19 midcycle tests). Any
  OTHER consumer of those (`margin_trend`, `multi_year_trajectory`, screen fundamentals, the
  mid-cycle block's own anchors) can still pick a partial tag. That remains the operator-decision
  item already recorded below.
- **BUILD — dossier-assembly freshness check (queued 2026-07-21, from the SMPL near-miss):** the
  2026-07-10 SMPL assembly missed the 2026-07-09 fiscal-Q3 print by ONE DAY and shipped a
  "no numeric guidance" premise the print had already falsified. Assembly should detect EDGAR
  filings newer than its evidence window and FLAG (not silently absorb) them — pairs with the
  assembly provenance-stamp item. The manual §7 print-freshness gate covers verdicts until built.

- **OPERATOR (from the 2026-07-20 scenario-derivations build):** (a) at PR review, ratify the
  three draft `method` sentences on WERN's assumptions + the two `confirm at review`
  Dedicated-mix ref sources (51.5%→73% — analyst calcs whose filing basis needs naming), and
  rule on the "12-14% peaks" prose vs the verified 9.59/11.31/9.82% consolidated record;
  (b) when the truckload freeze source is restored, re-run the theme build from it and confirm
  the surgically-patched `frontend/themes/truckload-supply-purge.json` reproduces byte-identical.

- **R1 ANCHOR PERSISTENCE ENGINE + 7 backfilled — BUILT (branch `feat/r1-anchor-persist`,
  2026-07-20; PR open, NOT merged).** Triage is now a cheap READ of a committed, source-bound,
  spot-INDEPENDENT anchor instead of a live CIQ+EDGAR recompute (the read-only triage STOP-gate that
  exposed the need). **Engine (`vinci/dossier/anchor.py`):** one shared
  `compute_anchor(mechanical, facts, computed_at)` — margin = EDGAR median operating margin over ALL
  available FY (fallback: committed `financial_summary` EBIT/Rev, forced weak); multiple = committed
  `valuation.own_history.median` (READ, never recomputed); D&A = combined `dep_amort` tag else a
  source-stamped `Depreciation + AmortizationOfIntangibleAssets` split (the CNXC case); net-debt =
  lease-inclusive (debt + finance + operating leases − cash) reusing the tested under-capture guard +
  a stored bridge string; diluted-WA shares + LTM-rev source-stamped. **Value math is the #150
  block's `scenario_value` (EBITDA basis, EV=(EBIT+D&A)×mult) — never reimplemented.** POSITIVITY
  GUARD: margin ≤ 0 → `recipe_hint=R2_NEEDED`, `applicable=false` (the guard for future pre-profit
  names; it does NOT chase turnarounds — analyst override, out of scope). Schema: optional top-level
  `Dossier.anchor` (pre-anchor JSON round-trips byte-identically). **Wired into assembly** (fail-soft:
  any gap/EDGAR error → an inapplicable anchor with a reason, never a crashed dossier). **Backfill
  command** `vinci anchor-backfill --tickers …` writes ONLY the anchor block via a BYTE-PRESERVING
  string insert — a model round-trip drifts OLDER-schema fields (new-default materialisation), the
  incident that earned `insert_anchor_block`. **Backfilled 7** (AORT/BRBR/CNXC/EPAM/IT/SMPL/VITL) —
  every other field byte-identical, verified per name. Confidence: margin firm ≥7 FY, multiple firm
  ≥20 quarterly closes, overall = the weaker. **Incident→invariant (shipped Y):** 6 tests — schema
  pin, EBITDA-basis numeric (frozen + living-artifact consistency), positivity guard,
  byte-preserving insert, missing-multiple non-crash. Green (ruff + mypy --strict 102 files +
  pytest). Frontend unaffected (UI ignores the block; Cloudflare rebuilds the mirror at deploy).
  **Anchor bases:** AORT $57.29 (firm) · BRBR $56.20 (weak) · CNXC $61.99 (weak) · EPAM $225.55
  (weak) · IT $337.96 (firm) · SMPL $38.43 (firm) · VITL $4.35 (weak). **NEXT (not in this PR — the
  brief's scope guard):** run the overshoot triage as a cheap read of these anchors × live spot
  (reward-to-base rank).
- **AORT empty `financial_summary` — CIQ 'No Data Available' export, made loud (PR #155,
  `fix/ciq-aort-financials`, 2026-07-20; NOT merged — agent stops at PR).** AORT's CIQ Financials
  export returned the header-only `No Data Available` sentinel for Income Statement / Balance Sheet /
  Cash Flow (+ Ratios), BOTH Annual & Quarterly, WHILE Key Stats (Revenue 486.4, EBITDA 95.3, EPS
  0.095 FY26) + Multiples (256 numeric) were fully populated on the SAME workbook → the data EXISTS in
  CIQ; a bad/partial export, not missing data. The three `financial_summary` builders surfaced it as a
  cryptic `no Fiscal Period header` / bare `Balance Sheet` UNKNOWN — indistinguishable from a genuine
  header-parse failure. **Fix (shipped):** a shared `_no_data_available` sentinel guard in
  `ciq_sheets.py`, applied to all four financial-TABLE builders (`financial_summary_annual` /
  `_quarterly`, `balance_sheet_posture`, and `return_ratios` — the last added in the #155 self-review)
  → an honest, actionable note naming the sentinel + the re-export; a populated-but-headerless sheet
  still reads `no Fiscal Period header` (the two failure modes stay DISTINCT — a real parse bug is
  never masked by the benign data gap). Green (ruff + mypy --strict + pytest). **Incident→invariant
  (shipped Y):** 5 regression pins (4 positive builder pins + 1 negative distinctness pin), synthetic
  shells, no licensed CIQ data. **OPERATOR TO-DO:** re-export AORT's CIQ Financials workbook (Annual +
  Quarterly) to populate the tables + ratios — the new note makes the gap self-explanatory.
  **FOLLOW-UP (held out of scope in #155):** the ~17 SCALAR financial-subsheet readers (`net_debt`,
  `ltm_ebitda`, margin/trajectory extractors) return UNKNOWN via cell-level absence on a No-Data
  workbook — less cryptic than the table builders, a separate broader pass.
- **DOSSIER-NOW: WERN (theme #3 truckload) — single-name underwrite at the 2:1 bar (2026-07-14).** The
  scan's sole REAL-tier name (quantified / driver-specific asset-based TL). Underwrite on NORMALIZED
  earnings — trailing P/E sits at the 99th percentile of its own history (a trough-earnings artifact, not
  the bar). Thesis-break (all three WATCHLIST names): FMCSA non-domiciled-CDL rule stayed/reversed, or ACT
  driver availability returns to surplus. Gated on the analyst's dossier build; cites the theme-#3 freeze
  (`feat/theme3-freeze`) + `data/research/theme3_truckload_triage_2026-07-14.md`.
- **OPERATOR DECISION — `extract_points` first-alias-wins truncation (found by feat/midcycle-scenarios,
  2026-07-17).** The shared EDGAR extractor resolves concept aliases FIRST-HIT-WINS and silently
  truncates a filer that switched tags mid-history (WERN: 4y under
  `RevenueFromContractWithCustomerExcludingAssessedTax` vs 18y under `Revenues`; VRRM: 9y under the
  606 tag). `midcycle.annual_series` works around it locally (LONGEST-single-alias, one basis, never a
  splice), but the **shared extractor is UNCHANGED and the truncation is latent for any other
  long-history consumer** (`margin_trend`, `multi_year_trajectory`, screen fundamentals). A fix would
  MOVE committed dossier numbers → **needs an operator decision (fix vs leave) + a full artifact
  re-assembly pass if fixed.** Recorded, not chased (scope). Pinned locally by
  `test_longest_alias_wins_not_first_hit`.
- **GREEN-MAIN BREACH RECORDED — #138–#148 merged with a latent ruff red (repaired 2026-07-17).** The
  design series #138–#148 left two E501s in `tests/test_dossier.py` on origin/main (pre-existing, NOT
  from feat/midcycle-scenarios). Repaired in-branch (commit e1c0352, formatting only) so this PR sits
  on green. Standing invariant reaffirmed: **no red main** — a merge that reddens trunk is a breach
  even when pytest passes, because ruff is part of the gate. Incident→invariant (candidate): the merge
  gate should run `ruff check .` repo-wide (not only changed files) as a required check before merge.
- **`themes-priced-check` CLI — SHIPPED 2026-07-15 (feat/priced-check; see §2).** The survivor price
  gate now has a repo home, reproduction-verified exact against `report_all.txt`; runbook §c carries the
  real invocation. (Was: QUEUED — no in-repo generator. Now closed.)
- **DRAFTING-RUBRIC v2 STANDS — 2nd iteration NOT sanctioned; validation PRE-REGISTERED on Aug 13
  (operator ruling 2026-07-15).** v1 (all keep-for-checks) → v2 park-default + runtime few-shot lifted
  the Jul-14 face-validity from **0/11 → 7/11 park-or-reject** (5/11 exact); 4 keep-for-checks
  survivors on lagging clusters the human parked (T006/T007/T040/T043). **The operator ruled: v2
  stands, do NOT re-tune the prompt now.** Validation is **pre-registered on the Aug 13 sweep** —
  `keep-for-checks` is expected to be the EXCEPTION, not the default; disagreements are reviewed THEN,
  on fresh (not-yet-priced) clusters rather than this frothy already-moved set. FACE-VALIDITY only —
  never tuned on forward returns. (If Aug 13 shows keep-for-checks creeping back to the default, THAT
  is the trigger to revisit — a real forward test, not a re-fit to the Jul-14 labels.)
**OPERATING-DRIVERS MECHANISM TIER (PR-B, Tiers A + Tier B code) — BUILT + VERIFIED, LOCAL (branch
feat/operating-drivers, 2026-07-13; NOT yet PR'd — user tests locally first).** The MOSL
"90-second handover" gap, closed with anchored extraction: typed cited `operating_drivers` rows on
the mechanical layer + a Mechanism block on the Brief (between The case and Financial snapshot).
Assemble-and-cite only; POSES, never forecasts; `Synthesis` six-field no-conclusion pin untouched.
- **Schema:** `OperatingDriver{kind, metric, period, value (verbatim), value_num/unit (anchored
  only), verbatim, source_ref (machine-set), tier}` + `OperatingDriversExtract` +
  `MechanicalLayer.operating_drivers` (default None → back-compat; committed dossiers round-trip).
- **A2 (10-Q MD&A attribution, `filing_sections.results_attribution`)** — the canonical
  "<subj> increased/decreased $X, or Y%, … due to <cause>" shape; value_num direction-SIGNED;
  verbatim spans into the cause sentence (MVST's "48.9% reduction in sales volume … 535.7→273.9
  MWh"). **VERIFIED real cached 10-Qs: 5/10 names, 15 rows** (MVST/VRRM/SMPL/BRBR/CNXC). First
  consumer of MD&A body text (already fetched + disk-cached — zero new I/O).
- **A3 (CIQ Key Developments, `ciq_sheets.key_development_drivers`)** — the on-disk, classified,
  previously-UNUSED export; **header-driven** column detection (4-col vs 5-col `…|Company|…`
  layouts vary); INCLUDE filter (guidance/product/client/expansion/impairment; index/earnings/
  governance noise dropped). **VERIFIED: 10/10 names, 88 rows** — incl. EPAM (18 rows, a
  zero-EX-99.1 name the tier rescues). Declared in `requirements.CIQ_MODULES` (optional).
- **A1 (EX-99.1 pricing + narrow KPI, `release_parse.operating_drivers`)** — DEMOTED per the
  diagnosis: pricing real (VITL, qualitative — a headline 7% is revenue growth, value_num stays
  None) with M&A-boilerplate exclusion; KPI requires a governing shipped/added verb, the two
  observed false-positive shapes pinned OUT (FUBO expense-line, MVST "290Ah cell" spec).
- **Fail-loud transcript fix (ships regardless):** `unparsed_transcript_flag` — transcripts on file
  that don't parse (no LibreOffice) now emit a QA flag; the 2026-07-10 silent-None cohort can't
  recur. Routed to dev/QA (an OPS action), not an analyst caveat.
- **Render:** md `_brief_mechanism_lines`/`_mechanism_lines` + web `mechanismCard`/`mechanismFull`
  (parity), grouped by kind, events most-recent-first, endnote-cited (`>Source:` guard green),
  honest empty line when no rows. **VERIFIED live (preview 8791):** MVST Brief shows attribution +
  events cited `[B9-B12]`, zero console errors; AORT (None) shows the honest empty card.
- **Tier B (LLM-fenced transcripts) — BUILT + VERIFIED END-TO-END (live model run, 2026-07-13).**
  Operator installed LibreOffice → `_find_soffice` finds `/opt/homebrew/bin/soffice`;
  `transcript_for_synthesis` returns real parsed slices (~24k chars, 2 calls/name). `driver_extract.py`
  is the covenant pattern + ONE load-bearing UPGRADE — a **code-level validator**: (i) the model's
  `quote` must appear whitespace-normalized in the slice; (ii) every numeric in `value` must
  digit-trace (the synthesis tracer's scales + ±2%/0.05 tol) to a number **in the row's OWN QUOTE**
  — traced against the quote, NOT the 24k slice (a slice-wide universe spuriously traces almost
  anything — caught in dev: `999` matched `99.97%` slice-wide). **VERIFIED LIVE (claude-opus-4-8):**
  MVST → 12 rows incl. `sales volume ~274 MWh (Q1'26) vs ~536 MWh prior` (the exact figure the PR#41
  incident predicted), `Phase 3.2 up to 2 GWh capacity add`, `US rev +173%`; VITL → 12 rows incl. a
  textbook pricing mechanism `price gap closed 35%→25% at a top-10 customer → volume +18% in 2 weeks`,
  `new-household share 55%→50%`, `TDP 149.8 vs 115.8 yoy`. Every row cited to a real call with a
  verbatim quote; the row cap FLAGGED the excess (not silently dropped); ZERO fabrications observed.
  The FakeLlm unit pins (keep/drop/cap/LLM-error) guard the validator deterministically in CI. Fence
  revised (scope-exact): a separate pre-synthesis validated phase reads transcript numbers; the
  synthesis fence still says "derive NO numbers from this text — cite the `operating_drivers` facts".
  `requirements.py` transcript `used_for` updated; `required` stays False.
- **Suite:** ruff + `mypy --strict` (94) + full `pytest -m "not network"` green. Pins: A1/A2 on
  real public-domain EX-99.1/10-Q excerpts + negatives; A3 on a SYNTHETIC KD fixture; Tier-B
  validator on a SYNTHETIC slice via FakeLlm (keep/drop/cap/LLM-error — real CIQ transcript text
  never committed, licensing); fail-loud + render e2e (endnote-cited via real render_markdown).
- **Incident→invariant (shipped Y):** silent transcript-None → `unparsed_transcript_flag` + pin [Y];
  undeclared CIQ kind consumed → `CIQ_MODULES` coverage guard caught it, now declared [Y]; the
  "operating"⊃"rating" substring false-positive in the no-conclusion guard → matcher tightened to
  snake_case word boundaries [Y]; digit-trace-against-slice too permissive → trace against the
  row's own quote [Y]; render endnote-only → `>Source:`-scan guard [Y, pre-existing].
- **CURATION + SYNTHESIS-USE (A+B, 2026-07-13) — operator asked "what's the use of a raw list if
  synthesis doesn't use it".** BOTH shipped: **(A)** the Mechanism line is now mechanism-first and
  concise — ATTRIBUTION renders `metric ±% — <cause clause>` (the causal WHY, period-phrase filler
  stripped) instead of the raw truncated MD&A sentence (which was cutting off the cause), biggest
  move first; LEADING_INDICATOR drops the redundant unit/hedge (`sales volume: 274 MWh`, was
  `sales volume (megawatt hours): approximately 274 megawatt hours`); md+web parity. **(B)** the
  synthesis prompt now surfaces a SALIENT operating-drivers digest (term→value→source_ref) + a
  MECHANISM system rule ("ground any operating bull/bear point in the specific driver, copy its
  source_ref; the decisive question names the load-bearing driver"). **VERIFIED LIVE (MVST):** the
  fresh synthesis grounds its bear case in the mechanism — "Revenue collapsed... down 48.0%...
  driven mechanically by a 48.9% sales-volume reduction" CITING the attribution driver's
  source_ref; the decisive question now reads "reverse the Q1 volume collapse". So the drivers now
  BOTH read cleanly for the human AND feed the machine's reasoning. Pins: curated line format
  (deterministic anchors) + the digest/system-rule (prompt-construction, not an LLM-output string).
- **DIRECTIONAL RESTRUCTURE (2026-07-13) — operator: "not useful, no direction, points
  irrelevant".** After a diagnosis + two clarifying questions, the Mechanism block was rebuilt from
  a flat kind-bucketed list into a **directional "what's changing" strip**: two groups,
  **Deteriorating / Improving**, biggest signed move first. Direction = the machine reading the
  SIGN of a stated change (`_driver_direction`) — top-line attribution by value_num (cost/expense
  EXCLUDED, never a misleading "cost-down = good"), events by type (guidance raised/lowered,
  impairment, client/product; showcase/exhibition/marketing-PR dropped), verb-based for the rest.
  A row with NO derivable sign is DROPPED — which strips exactly the noise the operator flagged:
  bare levels, patents, TAM, lab specs, foreign-regional trivia. This is sign-reading, NOT a
  verdict (stops well short of BUY/AVOID). md+web parity; near-dup plural collapse ("2 GWh
  hour(s)"). VERIFIED (MVST/VITL/EPAM): MVST → Deteriorating: revenue −48% (volume collapse),
  impairment · Improving: Iveco win, +2 GWh capacity, US rev +173%. Pins: `_driver_direction` unit
  (sign/exclude/event/off-thesis/verb) + directional grouping e2e. **PREVIEW CACHING FIX:** the
  stock `http.server` sends no cache headers → the browser hard-cached old ES modules; a
  no-cache dev server (`scratchpad/nocache_server.py`, port 8899) serves fresh — use that URL.
- **STANDALONE BLOCK REMOVED — the drivers FEED SYNTHESIS, they are not a rendered surface
  (operator decision, 2026-07-13, after 4 render iterations).** The honest diagnosis: a
  mechanically-extracted fact list can never render the *directional call* the reader wants — that
  call IS the verdict, which the constitution reserves for the human — so the block was raw
  material in every format (flat list → curated → directional strip) and read as clutter. The one
  place the drivers demonstrably earned their keep is **feeding synthesis** (the bull/bear grounds
  in them and cites the −48%-volume mechanism — proven). So the standalone Mechanism block is
  REMOVED from the Brief AND the Analysis tier (md + web + CSS; ~370 lines of driver-render code
  deleted). KEPT: the extraction (A1/A2/A3 + Tier-B), the schema field (machine-complete in
  `dossier.json` for audit), the assembly wiring, and **B** (`_operating_drivers_digest` + the
  MECHANISM system rule + the fence). A regression guard pins that no `## Mechanism` /
  `## Operating drivers (mechanism)` block renders while `operating_drivers` still rides in the
  mech. Suite green. LESSON: the machine assembles+cites+feeds-reasoning; it does not render a
  standalone "read" — that pretends to a conclusion it isn't allowed to make.
- **NEXT (operator):** (1) test locally, then I open the PR; (2) standing artifact pass
  re-assembles the cohort via
  `vinci dossier` so the COMMITTED dossiers carry real driver rows (both tiers) — the injected
  preview jsons are restored to None after review.

**BRIEF (v2) — `planning/OPERATING_DRIVERS_BUILD_BRIEF.md` (the spec the build followed).** Genesis: the
MOSL Mahanagar Gas audit (full record rides with #116's STATE.md entry). v2 re-grounded on a
PRE-SIGN-OFF DATA DIAGNOSIS over the actual substrate (SEC cache · CIQ store · committed dossiers);
v1's Tier-B coverage claim was WRONG and is corrected: `management_commentary: present` is a
POINTER (files on disk), NOT parse success — **LibreOffice is not installed on this machine, so
`transcript_for_synthesis` silently returns None for 10/10 names** (the 2026-07-10 cohort assembled
with zero transcript text and no flag — a fail-loud violation; the fix ships regardless of PR-B).
Diagnosed yields: 10-Q MD&A attribution CONFIRMED in cached real text (CNXC/MVST/SMPL — rescues 2
of the 3 no-release names) → A2 promoted; EX-99.1 pricing real for VITL but AORT's hits are M&A
boilerplate ("purchase price adjustments" — new negative-pin shape) and KPI yield is thin/noisy
(expense-line + product-spec false-positive shapes) → A1 demoted; **CIQ Key Developments found on
disk 10/10, classified (`key_developments`, ciq.py:169), consumed by NOTHING, striprtf-parseable
(`Date|Type|Headline` + Situation rows, guidance/customer categories)** → NEW anchored A3. Tier B
(LLM-fenced transcripts, covenant pattern + a code-level verbatim/digit-trace validator the
covenant template lacks) is **GATED: operator installs LibreOffice + a shown parsed slice, else
deferred**. Materiality = cross-layer JOIN, never a product; synthesis bridge prompt-level only.
OPERATOR ACTIONS: (1) LibreOffice install (Tier-B unlock); (2) optional fuller-category Key
Developments re-pull; (3) optional per-name CIQ operating-metrics export at depth. **No code until
sign-off.**
- **OPERATOR NOTE (worktrees):** canonical main lives in the `-s2`/`-main` worktrees; the primary dir
  tracks unmerged `feat/own-history-line` — run audits and builds from a main worktree.
- **Sweep cadence: MANUAL — operator decision 2026-07-13 (NO cron).** The Component-A co-movement sweep
  runs on demand, never scheduled. **Run locally** (fresh sweep, latest universe snapshot):
  `.venv/bin/python -m vinci.cli themes` (append `--ref YYYY-MM-DD` to pin an as-of). NO workflow file is
  shipped — the **Actions path was DROPPED**: the push credential (osxkeychain) AND `~/.mosaic_gh_token`
  both report `repo` scope only, NOT `workflow`, so a workflow file cannot be pushed at all; secondarily,
  the authored `monthly-themes.yml` never durably persisted the sweep snapshot (`data/scan_history/` is
  git-ignored and it added no `upload-artifact` — only the `candidate_themes.jsonl` pointer would commit
  via `git add data/snapshots`). **CANONICAL invocation — recorded HERE, the ONE place; the future Radar
  screen MUST source it from here (no second hardcoding):** the June-17 harvest reproduces as
  `python -m vinci.cli themes --ref 2026-06-17` with the `themes` subparser's documented defaults
  `--basis r2 --window-days 365 --min-breadth 3` (the exact June-17 flag string was UNRECORDED, so these
  documented defaults ARE the canonical set; their values live on the argparse subparser, not
  re-hardcoded). **Reminder is display-only:** the (future) Radar screen shows last-run / next-due (+30d)
  from the `component-a` scan_history manifest, amber when overdue — nothing fires automatically.
- **THE THREE-STORE SPREAD IS THE DESIGN, NOT DRIFT — so the fix is a STAMP, not a sync (established
  2026-08-11, PR `spot_as_of` / `price_store`).** The spread had been called a hazard twice without
  anyone checking whether it was one. It is not: the DATA-TOPOLOGY entry directly below already
  records `data/` as PER-WORKTREE, so three checkouts holding three frontiers (`wb` 2026-08-04, `sl`
  2026-08-07, primary 2026-08-05) is the documented arrangement working. **What DOES follow is that
  a reader cannot infer the data behind an artifact from the artifact.** Two names assembled the
  same day out of different worktrees are struck days apart with nothing saying so; comparability
  today rests on reference dates happening to lag every frontier — a coincidence, not a guarantee.
  Hence `Dossier.price_store` (declared path + RESOLVED path + frontier), stamped at assembly.
  **The resolved path is load-bearing:** `-pg`'s `data/vinci.db` is a SYMLINK into `-wb`, so a stamp
  carrying only the declared path would make two dossiers built from ONE store look like two — the
  same confusion that had a corroboration check report "the store cannot see $11.56" while asking a
  store it had not identified.
- **"LATEST GUIDE" CARRIED A NUMBER THE COMPANY NEVER PUBLISHED (2026-08-12, PR-A).** Visa guided
  FY26 revenue at *"the low end of low-teens"* — a RATE. The page showed **45,200.0** under "Latest
  guide", cited to CIQ→Guidance as though quoting the company. **PROVEN, not inferred: Visa's FY25
  revenue is 40,000 and 40,000 × 1.13 = 45,200 exactly.** The level is CIQ's arithmetic on its own
  base. Analyst finding, verified against the live workbook.
  **CIQ CANNOT GIVE US THE OTHER FORM.** Its Guidance sheet for V has TEN metric blocks (Revenue,
  EBIT, EPS Normalized, EPS GAAP, Capex, FCF, Net Income, DPS, Interest Expense, Effective Tax Rate)
  and **not one growth-form block**. We are not dropping management's wording — CIQ normalises it
  away before the export reaches us. The only honest move is to say the level may be derived.
  **SAID ONCE, NOT PER ROW, and the restraint is the finding.** The sheet does not record which form
  management used, and the shape cannot be inferred: **32 of the 49 committed guides are RANGES**
  (`'2,335.00 - 2,375.00'`) that plausibly ARE the company's own band, and a company can guide a
  point too. Flagging every point-valued guide as "derived" would be #423's false-demotion error in
  a new place. The caution is general because the evidence is general.
  **IN THE `source_ref`, NOT ONLY THE RENDER — a deliberate departure from #423, which was
  render-only.** Checked rather than assumed by analogy: **seven committed syntheses cite this sheet
  and five quote a figure off it** (NFLX 12,860.0 · MVST 427.5 · VRRM 1.19/1.25 · BRBR 10.0). The
  LLM reads the mechanical layer as JSON, so a render-only note would leave the model treating a CIQ
  derivation as the company's own words. One `GUIDANCE_BASIS_REF` constant feeds both call sites —
  pinned, because two literals would let one carry the basis and the other keep claiming otherwise.
  **A LABEL CHANGE MUST MOVE NO NUMBER**, so the artifact pass ran under a guard that re-derived
  every guide from the workbook and refused any name whose figures differed. **13 of 14 updated; 0
  refused for a moved figure.** The JSON diff is exclusively `source_ref` lines.
  **FUBO: JSON SEALED, VIEW RE-RENDERED.** The seal refused its `dossier.json` (correctly — it is
  frozen until a post-combination re-assembly). Its `dossier.md` was re-rendered anyway, on the
  seal sidecar's own terms: *"`dossier.json` is untouched. `dossier.md` renders this block at the
  top, because a rendered view is not the record."* Two e2e tests caught the stale twin. The
  artifact pin exempts sealed records **by detecting the sidecar, never by naming FUBO** — a
  hardcoded ticker would silently stop covering it the day it unseals.
  **STILL BARE, DELIBERATELY: eight synthesis citations across seven names** (CNXC, EPAM, NCNO,
  SMPL, UBER, VRRM bull points; SMPL bear; CNXC decisive-question evidence). Those strings were
  copied from the mechanical layer when the synthesis was written, before the basis existed.
  Hand-patching them would make the record show a caution the model never actually saw. They pick
  it up at re-synthesis — which is already an operator to-do for UBER/SMPL/NFLX.
- **A SPOT THAT NAMES NO DAY IS NOW UNRECORDABLE — schema 1.5 (2026-08-12, PR-7).**
  `vinci audit spot` can check a stated date against the store; against a record naming none it
  checks NOTHING and reports UNAUDITABLE forever. `write_record` now refuses a record created at
  **1.5+** without `spot_as_of`, and `scenario-propose` pre-fills it from the dossier's own
  `stock_info.as_of` — the bar date the price came from — so the requirement is satisfiable from
  the one path that creates records. `SCHEMA_VERSION` bumped 1.4 → 1.5.
  **THE ADOPTION TRAP WAS CHECKED BEFORE THE DESIGN, and does not exist.** Every committed record
  is schema **1.3** (8 live + 3 archived, one at 1.2), and `write_record` **PRESERVES** an existing
  record's version — driven through the real path, not read off the code. So BRBR and EPAM, which
  legitimately carry no date (struck at 2026-08-07, visible only to `-sl`), stay at 1.3 and remain
  writable indefinitely. The premise is pinned, because the gate's safety rests on it: if a write
  path ever re-stamps the version those two become unwritable, and the failure would surface far
  from here looking like a bug in something else.
  **THE COHERENCE HALF IS NOT VERSION-GATED** — a stated `spot_as_of` AFTER its own underwrite is
  refused at any schema, since legs cannot have been struck against a close that had not happened.
  #416's lookahead lesson moved to the WRITE seat. Costs no committed record: all six stamped
  spots precede their underwrite by 1–3 days.
  **WHAT IT DOES NOT DO:** it does not verify the date — that stays `vinci audit spot`'s job and
  deliberately a flag, because a refusal there would block correct records whose bar this worktree
  cannot see. The gate requires the CLAIM so that something exists to check.
  **AND IT SURFACED AN ORPHAN-ARCHIVE WINDOW IN `scenario-supersede`** (self-review): that command
  writes the ARCHIVE first and the live record second, so a refusal on the second left a superseded
  record with no successor and an un-updated seal manifest. The window PREDATES this change — the
  basis and fielded-ref gates raise at the same point — but the spot gate makes it far likelier to
  fire, since a fresh hand-written payload commonly omits `spot_as_of` until the field is habit.
  Closed by `validate_for_write`, the write's own refusal set as ONE callable, called by
  `write_record` AND by supersede before it touches disk; extracted rather than duplicated so a
  gate added later cannot be enforced at the write and skipped at the pre-check.
- **A POINT GUIDE INSIDE ITS OWN ROUNDING NOISE IS REFUSED, NOT ADJUDICATED (2026-08-13, #443).**
  Analyst finding on the committed NFLX page: the guidance table read `FQ2 2026 MISSED` for revenue
  while Netflix's own filing called the quarter in line. **VERIFIED AGAINST THE RAW SHEET:** CIQ
  states the guide as a POINT (12,574.0) and the actual landed 0.11% below (12,559.9); the delivery
  rule was `actual ≥ floor` with ZERO tolerance, so a sub-rounding shortfall printed as a miss.
  Same shape FQ3-2025 (−0.14%).
  **THE APPROVED FIX (refuse the point CLASS) WAS MEASURED AND REJECTED.** Fleet census across all
  19 workbooks, taken BEFORE any rule was written: **2,067 resolved calls · 941 (46%) on point
  guides · 142 inside ±0.5% of the point (25 MISSED / 117 MET) · 119 point-misses worse than −5%.**
  A blanket refusal erases 46% of the fleet's delivery evidence, hides all 119 real misses, and
  zeroes ONON outright (its guides are ALL points → record 0/0). **The undecidable thing is the
  CALL IN THE BAND, not the point class.**
  **THE RULE:** `_POINT_DECISION_BAND = 0.005` — an in-band point call leaves the record's
  numerator AND denominator, is disclosed on the record line (`60/65 · 18 at-guide (±0.5% of a
  point, not adjudicated)`), and `AT GUIDE` is a THIRD most-recent state. Ranges are untouched — the
  company stated its own band, and the band IS the tolerance. Direction still comes from
  `_GUIDANCE_HIGHER_IS_DELIVERY` (#437); a zero point adjudicates by sign.
  **NOT OUTCOME-TUNED, AND THE DIRECTION PROVES IT:** the band strips 117 METs vs 25 MISSes, so
  fleet hit-rates FALL on net. 0.5% is face-validity — the scale of a company's own "in line"
  language, with both live false-MISSes well inside it.
  **A THIRD STATE ANNOUNCED UNDER THE SECOND STATE'S NAME IS TWO STATES (review finding).** The
  summary introduced every verdict with `most recent resolved:`, so the new state printed
  `most recent resolved: FQ2 2026 AT GUIDE (… not adjudicated)` — self-contradictory, and it implied
  the refused call had entered the delivery record. One NEUTRAL label
  (`most recent guidance outcome:`) now carries all three.
  **MUTATION-TESTED AGAINST BOTH REJECTED DESIGNS:** zero-tolerance restored → 5 pins redden;
  blanket class-refusal → 4 redden (incl. ONON-keeps-a-record). Artifact pass under the PR-A guard:
  14/14 updated, **0 latest_guide moved**.
  **FLEET SCALABILITY OF THE UBER/NFLX FIXES, swept in the same diagnosis (all 14 names):** FCF
  basis note 14/14 · multi-quarter non-op live on TWO names (UBER 3, MVST 4) · every snapshot
  reconciles or states its cap gap (VITL +18.5%, UBER −13.2%, VRRM −11.1%) · split flag on NFLX
  alone (correct) · panel vintage 14/14 with Item 1.02 flags on NFLX/UBER/VITL · P/E percentile
  withheld on 7, computed on 7. **No fix is name-shaped.**
- **FLEET RE-ASSEMBLED ON THE MERGED FIXES (2026-08-13, #447).** All 14 names clean at
  **reference_date 2026-08-12** (`{'2026-08-12': 14}`), carrying #442/#443/#444/#446. The
  point-guide refusal is now LIVE on the pages: **20 at-guide disclosures across 8 names** (AORT 1 ·
  CNXC 2 · EPAM 4 · IT 3 · NFLX 3 · SMPL 3 · V 2 · VRRM 2); NFLX reads `actual ≥ floor 60/65 · 18
  at-guide` with `FQ2 2026 AT GUIDE` in place of the false MISSED; no page says "most recent
  resolved". Preconditions checked first: the as-of resolves from a real screen-run manifest and
  #442's guard found no identities `first_seen` after it.
  **ONE PIN MOVED, AND ITS PREMISE WAS AN LLM CHOICE.** `test_p6_ordered_points_…` asserted that
  **MVST** carries a cited EX-99.1-reconciliation bear point; its re-rolled synthesis cited the 10-Q
  instead (MVST still carries 9 cited bear points — the machinery is fine, the SOURCE moved). The
  ORDERING invariants (rank monotonicity, crux prefix, py↔js parity) are structural and passed
  throughout. The presence clause now ACCUMULATES across the tickers under test and asserts the
  shape exists SOMEWHERE (VRRM 3, EPAM 1), with a message to re-point rather than delete if both
  stop citing releases. Mutation-tested: an unmatchable shape reddens instead of passing vacuously.
  **Which company supplies an LLM-composed shape is not an invariant; that some name does, is.**
- **STATE ENTRIES WERE LOST TWICE BY REBASE, AND THE RECORD WAS LYING (2026-08-13).** Both entries
  above were written at build time and **silently dropped when their branches were rebased onto a
  moved `main`** — #443 MERGED with no STATE entry at all (its merge commit does not touch
  STATE.md), and #447's went the same way. Caught only by reviewing my own PR's file list and
  noticing STATE.md absent from a 58-file artifact pass.
  **WHY IT HAPPENS:** every build appends near the same region, so a rebase onto a `main` that
  gained entries conflicts there every time, and resolving toward the incoming side drops the local
  addition without a conflict marker surviving to review.
  **THE CHECK THAT CATCHES IT:** after any rebase, `git diff origin/main -- STATE.md` must be
  non-empty for a build that changed reality. A green suite does NOT catch this — no test reads
  STATE.md — which is exactly why the session ritual makes it a standing step rather than a guard.
- **THE RETENTION LAYER WAS DARK IN PRODUCTION — NOW WIRED INTO `run_weekly` (2026-08-13).**
  Diagnosed after #441 recorded "`write_manifest` has no production caller" and recommended wiring
  it into `_cmd_screen`. **THE RECOMMENDATION WAS WRONG ON BOTH COUNTS, and the diagnosis is the
  useful part.**
  **IT IS NOT JUST THE MANIFEST.** `build_universe` AND `screen_universe` each take
  `retain_run_id`/`retain_dir` ("both or neither, enforced"), and no production path supplied them
  — so universe rows, candidate rows AND the manifest were all uncollected. The three committed
  2026-07-29 runs came from a worktree (`bbcb3e0`: *"existed only in one worktree… removing it would
  have destroyed the fund's only screen evidence"*), never from a wired path.
  **IT IS NOT AN AFTER-THE-FACT LOG.** `screen_universe` READS the manifest back and REFUSES a run
  whose `routing_policy` disagrees with its own record. The manifest is a PRE-COMMITMENT; writing it
  after the screen would leave that check reading nothing and passing vacuously on every run.
  **AND `_cmd_screen` IS THE WRONG HOME.** It runs the screen alone, so a run_id filed there carries
  candidate rows and NO universe rows. The manifest's own `universe_as_of` field exists because run
  `2026-07-29-01` screened the **2026-07-06** universe while `build_universe` wrote the 2026-07-29
  one, leaving **72 tickers in both grains** — and that field's docstring names the cause exactly:
  *"nothing binds that to a `build_universe` run in the same session (the build is a separate CLI
  subcommand)"*. Wiring per-subcommand IS the disease. `run_weekly` is that session.
  **THE ORDER IS THE CONTRACT:** `build_universe` (so `universe_as_of` names the population the
  gates will judge) → `write_manifest` → `screen_universe` (which reads it back). Pinned, and
  mutation-tested in both shapes: stripping `retain_*` from a call site reddens, and moving the
  manifest after the screen reddens.
  **PROVEN BY A REAL RUN (2026-08-13).** `vinci run-weekly --end 2026-08-12`, exit 0, filed
  `2026-08-12-01.manifest.json` **and** `2026-08-12-01.jsonl` — **5,857 universe rows + 1,802
  candidate rows under ONE run id**, every name the screen touched rather than the 292 survivors.
  The manifest carries `universe_as_of: 2026-08-12`, which is only correct because it is written
  AFTER `build_universe`; the policy check fired for real and passed (`routing_policy:
  carry_not_evaluated` on both the run and its record). `_fleet_reference_date` now reads
  2026-08-12 from a run that happened.
  **THE CONTRAST IS THE EVIDENCE:** the hand-filed `2026-08-12-01.manifest.json` sat on disk with
  NO `.jsonl` beside it — a record of a run that collected nothing. It has been REMOVED and replaced
  by the real one; a stopgap for a broken pipeline has no reason to outlive the pipeline's repair.
  **TWO GAPS THE RUN EXPOSED — BOTH NOW FIXED, and the review showed one was worse than I filed
  it.** I recorded them as notes; #442's review showed the first is a P1:
  - **`next_run_id` scanned `*.jsonl` only**, so a MANIFEST-ONLY id was invisible and got reissued.
    I called that a deadlock. **The ORDER makes it corrupting**: `build_universe` appends retention
    rows under the reused id BEFORE `write_manifest` raises on the write-once file — so the retry
    dies AND leaves partial rows filed under a DIFFERENT run's recorded configuration, the exact
    misattribution the manifest exists to prevent. Now every artifact kind (`.jsonl`,
    `.manifest.json`, `.caveat.json`) reserves its id.
  - **A FAILED FORWARD-DATED RUN LEAKED INTO A BACKDATED ONE.** My aborted `--end 2026-08-13`
    attempt had already upserted **BBAR, SSMR, AADX at `first_seen 2026-08-13`**; the re-run at
    `--end 2026-08-12` found them in the store, admitted all three to the 2026-08-12 universe and
    filed candidate rows under that manifest — **a committed historical screen carrying names it
    could not have known.** The store is mutable and SHARED: re-running at the earlier date does
    not undo the later write, and I asserted a clean re-run without checking that.
    **RESOLVED BY ROLLBACK + RE-RUN, and the outcome is the honest one:** the three identities were
    deleted from store AND snapshots, the weekly re-run at 2026-08-12 re-discovered them on its own
    evidence, and they now carry `first_seen 2026-08-12`. Their MEMBERSHIP was never wrong — the
    STAMP was. **`Store.identities_first_seen_after` + a `run_weekly` RAISE** now refuse a backdated
    run outright (47 identities would refuse a run dated 2026-08-01); it raises rather than filters,
    because silently dropping them hides the leak and leaves the store dirty.
  **SUPERSEDED — the note below is what I filed before the review:**
  - **`run-weekly --end` defaults to `date.today()`.** My first invocation used `--end 2026-08-13`
    while the price data reaches 2026-08-12, so the fleet as-of outran its own prices and
    `test_the_wall_clock_is_unreachable_from_the_reference_date` refused it — correctly. A cron
    firing before the day's bars settle would do the same every time. `end` should be clamped to
    the store's price frontier.
  - **`next_run_id` scans `*.jsonl` only**, so a manifest with NO rows is invisible to the id
    allocator and its id can be reissued — which `write_manifest` then refuses, deadlocking the
    date. Only reachable via a hand-written manifest, which is now unnecessary.
- **FLEET RE-ASSEMBLED ON ONE AS-OF, AND THE TWO CLOCKS RECONCILED (2026-08-13).** All 14 names
  re-assembled clean at **reference_date 2026-08-12** (`{'2026-08-12': 14}`), the first time the
  fleet has sat on a single as-of since the split opened.
  **THE SPLIT'S ROOT CAUSE: `write_manifest` HAS NO PRODUCTION CALLER.** Verified across two
  vocabularies plus `git log -S` — it is called only from `tests/test_retention.py`. So
  `_fleet_reference_date` reads `screen_runs/*.manifest.json`, which NOTHING writes, and was frozen
  at 2026-07-29 forever; meanwhile #431 advanced `ranked_queue.jsonl`'s `screen_run_at` to
  2026-08-12. Queued names took the queue's date and FOLLOWED names took the stale manifest's —
  hence 8 names at 08-12, 5 at 07-29, MVST at 07-06. **`vinci screen` does not file a manifest**;
  a real `vinci screen --ref 2026-08-12` (exit 0) was run and its manifest filed through the
  sanctioned write-once `write_manifest`, every field read from the live config. **WIRING
  `write_manifest` INTO `_cmd_screen` IS NOT DONE HERE** — it is a decision-path change owed its own
  PR, and until it lands every screen run leaves the same gap.
  **A FAIL-LOUD GUARD DID ITS JOB EN ROUTE:** the first screen aborted with `ROW-DROP on
  issuers.jsonl: writing 2251 row(s) over 2289 would drop 42` — the local store had fewer issuers
  than the committed accumulate-only master. Seeded via `rebuild_from_snapshots` (INSERT OR REPLACE;
  the 2.1M price rows untouched) and re-run.
  **AND ONE SELF-INFLICTED FAULT, CAUGHT BY THE INVARIANT IT VIOLATED:** the 2026-08-12 manifest put
  the fleet as-of AHEAD of the committed price fixture's frontier (2026-08-07) — exactly the state
  `_fleet_reference_date`'s docstring forbids ("a 5-day staleness window would still call that
  fresh"). `test_the_wall_clock_is_unreachable_from_the_reference_date` reads the COMMITTED FIXTURE
  (deliberately — its docstring records main running red for eleven merges when it read the
  git-ignored DB), so the fix was `scripts/build_price_fixture.py`, the repo's own remedy.
  **TWENTY-ONE PINS WENT RED ON THE RE-DRAWN FLEET; ALL RESOLVED, NONE SUPPRESSED.** They sorted
  into four causes, and the pattern is worth keeping: **(A) seal retirement propagating** —
  exemption lists that named FUBO, each of which had anticipated clearing; **(B) the fleet
  legitimately improving** — `NO name fails on the share basis` (the goal, and its constructed
  refusal pins already existed), BRBR now drifting, AORT gaining a cap vintage, 13/14 panels past
  the ceiling instead of 14/14; **(C) VALUE PINS ON LIVING ARTIFACTS** — a broker-day count, three
  CNXC accessions, MVST's exact covenant source line, an ev_gap coverage tally, `>= 3` negative-EPS
  names: every one the class the TEST-LAYER RULE puts on FROZEN fixtures, rewritten as
  phrasing-independent invariants (no accession appears twice; DECOMPOSED and SUPPRESSED stay
  disjoint; the footer names *an* accession and *an* exhibit); **(D)** one sibling pin asserting
  #439's old note wording.
  **A DERIVED POPULATION THAT EMPTIES IS A PIN THAT STOPS TESTING (review finding, #441).**
  Rewriting the share-basis-mismatch pin to find its own subjects was right; letting it SKIP when
  the fleet is clean was not. FUBO's repair emptied the population permanently, so the renderer
  branch that prints `SHARE-BASIS MISMATCH` — the human-facing warning — went unexercised, and the
  constructed pins in `test_freshness.py` cover `reconcile_cap`, the COMPUTATION, not the label.
  The mismatch is now MANUFACTURED from a real record: shares solved so `spot/implied` lands exactly
  on 11 (scaling an existing count inherits the host's own drift — AORT landed at 11.485 and missed
  the integer tolerance). Mutation-tested by deleting the branch: the break then renders
  `⚠ implies $2.60/sh vs CMP (-90.9%)` — drift wording with a percentage, which is precisely the
  reading the label exists to prevent. **GENERAL RULE: when a pin's population is derived, assert it
  is NON-EMPTY or construct the case; a skip is a guard that has quietly stopped guarding.**
  **TWO FIXTURES HAD TO BE REGENERATED IN THE SAME PASS, and both said so themselves.** AORT's and
  VRRM's committed anchors diverged from a fresh recompute (+10.64% / −1.64%) — NOT the stale
  `computed_at` (identical at both dates), but the assembly reading LIVE companyfacts against a
  stale committed fixture. `build_companyfacts_fixture.py`'s own message demands it run "in the SAME
  PR that re-assembles the name, so the fixture cannot drift from the artifacts the pins check it
  against". That is the lesson: **a fleet re-assembly is not done until the fixtures the pins read
  are regenerated with it.**
- **THE GUIDANCE TABLE SHOWED FIVE METRICS OUT OF FIFTEEN (2026-08-12, PR-B).**
  `_GUIDANCE_METRICS` listed Revenue, Capital Expenditure, Gross Margin %, EBITDA, EPS Normalized.
  Everything else management guided was **silently absent** — not UNKNOWN, not flagged, never looked
  for. **THE ONE THAT MATTERS MOST: NFLX guides its own FREE CASH FLOW at 12,500.0 for FY 2026 and
  the page could not show it** — while #421 had just established that the same page's `Levered Free
  Cash Flow` read **25,388**, roughly twice management's own number, and wrote a basis note pointing
  the reader at exactly the figure the whitelist excluded.
  *MEASURED ACROSS 19 WORKBOOKS: **65 current guides → 138 (+73)**. AORT 5→9 · CNXC 3→8 · IT 4→12 ·
  CPB 4→12 · NFLX 4→10 · V 3→10 · WERN 2→7; every name gains. (An earlier note in this file estimated
  +34 — that was wrong; the measured figure is +73.)*
  **WIDENS WHAT CAN BE READ, NEVER WHAT MUST BE:** a block absent from a workbook is not rendered,
  every recovered guide carries `GUIDANCE_BASIS_REF` (#427), and each row states its own `age`.
  **DELIVERY DIRECTION IS A METRIC PROPERTY, NOT A SIGN (review finding, #437).** The delivery read
  inferred "this is a cost guide" from `range_high < 0`, which holds ONLY because CIQ states capex
  and interest expense NEGATIVE — a vendor formatting choice, not a semantic. Widening admitted
  **`Effective Tax Rate %`, cost-like but stated POSITIVE**, so it took the revenue path and a tax
  rate HIGHER than guided was recorded as **MET**. **MEASURED: all 12 names carrying a tax-rate
  guide had an INVERTED record** — VRRM `3/3` → `0/3` (a perfect delivery record that was a perfect
  miss), V `12/32` → `28/32`, WERN `5/13` → `12/13`, NIKE `13/28` → `23/28`, NFLX `0/1` → `1/1`.
  Now `_GUIDANCE_HIGHER_IS_DELIVERY` decides by NAME. **ABSENT MEANS UNRESOLVED, NEVER GUESSED:**
  `Depreciation & Amortization` is a consequence of past capital decisions, not a target — its guide
  still shows and its met/missed record reads `—`. A completeness pin refuses any future whitelist
  addition that is neither classified nor deliberately listed as undirected, so this cannot recur
  the way it just did.
  **REPORTED, NOT DECIDED — a staleness question this makes visible.** More metrics means more names
  that STOPPED guiding something: **V recovers 10 guides of which 6 are 2114–4767 days old**
  (Interest Expense FY 2016, Net Income Excl. Excep FY 2013, EPS GAAP FY 2020…). They are LABELLED
  `(stale)`, so nothing passes as current — but #423's entry argued that an age column two places
  right is weak medicine for a 24-year-old number under a heading reading "Latest guide", and
  widening multiplies the rows that rely on it. **Whether stale guides should be filtered rather than
  labelled is #423's policy, not this whitelist's**, so it is surfaced here and left alone.
- **FORWARD CASH-FLOW CONSENSUS REACHES THE PAGE — AND TWO METRICS DELIBERATELY DO NOT FUSE
  (2026-08-12, PR-D).** `CFO`/`Capex`/`FCF` carried actuals and nothing forward while
  Estimates→Trends carried a consensus for all of them (Capex/CFO/FCF on 18 of 19 workbooks, D&A on
  19 of 19); D&A had no row at all. **CFO and Capex are now fused** into their actuals rows — CIQ
  names the same measure on both sheets and the sign convention matches.
  **FCF IS NOT FUSED, and this is the substance of the change.** The actuals row is **Levered Free
  Cash Flow**; the consensus row is plain **Free Cash Flow**. Measured across the fleet, consensus
  FCF is not even CFO − capex: within 2% on only **4 of 15** measurable names, **SIGN-FLIPPED on AORT
  (−2.16x) and WERN (−7.79x)**, and 19.35x on PENG. And Trends carries no fiscal year overlapping the
  actuals, so **there is no period on which the two bases can be tested against each other** — a fuse
  would assert an identity nobody can establish.
  **WHAT THAT WOULD HAVE COST, MEASURED:** the step from the last actual to the first consensus
  column would have rendered as a real change on every name — **median |step| 51% across 17 names**:
  WERN −982% (sign flip), FUBO +281%, VRRM +184%, PENG −168%, AORT +166%, **NFLX −49%
  (25,388 → 12,868)**. A reader scanning that row sees free cash flow halving. Nothing halved.
  **D&A IS NOT FUSED EITHER, on evidence this repo had already recorded.** UBER's own committed bear
  point reads *"estimate columns imply 2,952 of D&A against 737 in the actuals (4.01x), so the
  forward EBITDA add-back is a DIFFERENT basis"*. NFLX shows the mechanism: its Cash Flow sheet
  carries BOTH `Depreciation & Amort.` (~372) and `Other Amortization` (~9,216 — the content
  assets), so what "D&A" denotes depends on the business. *(The operator's first instruction was to
  fuse D&A; the measurement above was taken after that answer and argued against it, so it was
  treated like FCF — stated here rather than quietly changed.)*
  **THE CONSENSUS IS MOVED, NEVER DROPPED:** `FCF (consensus basis)` and `D&A (consensus basis)` are
  their own rows with the actual columns blank. A mostly-`—` row is the honest shape — the vendor has
  a forward view and we decline to claim it continues the history beside it. A row is omitted
  entirely when the metric is absent, so no name gains an EMPTY row (the defect PR-C just removed).
  **WHICH METRICS FUSE IS DATA, NOT BRANCHES** (`_C1_CF`'s third element + `_C1_CF_CONSENSUS_ONLY`),
  so a future edit has to face the basis question rather than stumble past it. Mutation-tested by
  fusing FCF: the pin reddens with *"this is the 'same window, different basis' defect"*.
  **ARTIFACTS NOT UPDATED** — the pages gain these rows at their next assembly.
- **THE ESTIMATE COLUMNS ASSUMED A DECEMBER FISCAL YEAR — NCNO SHIPPED AN EMPTY `FY26E`
  (2026-08-12, PR-C).** Two sites hardcoded `FY 2026`/`FY 2027`: the financial-summary columns
  (`ciq_sheets.financial_summary_annual`) and the direct consensus anchors
  (`mechanical._implied_expectations._direct_anchors`, whose FAILURE NOTE also named those years).
  **NCNO closes in January and NIKE in May, so both had already REPORTED FY2026** — their
  Estimates→Trends starts at FY 2027, the hardcoded lookup found nothing, and NCNO's committed page
  shipped `columns: […'FY26','LTM','FY26E','FY27E']` with Revenue `[…595, 610, '—', 645]`: **an
  EMPTY estimate column sitting beside an ACTUAL FY26**, which reads as "consensus has no FY26 view"
  when the truth is that FY2026 is history. Their FY2028 consensus never reached a page at all.
  **THE RULE IS "BEYOND THE LAST ACTUAL", not "the first columns offered"** — a vendor sheet can
  still list a year since reported, and taking its first columns blindly would head a PAST year with
  `E`: the same error pointing the other way. LTM is excluded from "last actual" (a trailing window
  is not a fiscal year, and counting it would push the boundary a year early).
  *MEASURED OVER ALL 19 WORKBOOKS BEFORE THE RULE WAS WRITTEN: 17 names derive exactly the pair that
  was hardcoded and only NCNO and NIKE move (`FY26E, FY27E` → `FY27E, FY28E`) — surgical by
  measurement, not by hope. End-to-end on the real workbook, NCNO's table becomes
  `[…'FY26','LTM','FY27E','FY28E']` with Revenue `[…595, 610, 645, 702]`: the empty column is gone,
  FY2028 consensus reaches a page for the first time, and the growth row bases correctly off
  `+8% (vs FY26)`.*
  **ONE HELPER, BOTH SITES** (`forward_estimate_fys`) — two literal year tuples is how the table and
  the anchors come to name different years on one page; PR-A's lesson in a second place.
  **A DESIGN FLAW CAUGHT BY AN EXISTING TEST, not by me:** the first cut anchored the lookup on the
  Trends **Revenue** block, so a sheet carrying only an `EPS (GAAP)` block derived NO estimate column
  at all — the empty-column defect rebuilt in a new place. `test_d5a_eps_absent_basis_renders_dash_
  never_borrows` reddened on exactly that fixture shape. The years are now unioned over every period
  header in the sheet.
  **NOT FIXED, RECORDED — a THIRD hardcode of the same shape:** `_anchor("FY 2026")` in
  `_implied_expectations` feeds the G5 vintage-guard probe, so for NCNO/NIKE that probe is inert.
  Different consumer, different blast radius; it needs its own look rather than a blind sweep.
  **ARTIFACTS NOT UPDATED (deliberate):** NCNO and NIKE gain this at their next assembly. Re-rolling
  a synthesis nobody asked to re-roll is the cost the #426 entry already refused to pay.
- **A QUARTER WAS CHECKED AGAINST A YEAR AND THE PAGE CALLED IT A MISMATCH (2026-08-12,
  fix/guide-period-and-pctile-window).** Analyst review of the committed NFLX page, post-#426.
  The dossier printed `guide verification (revenue): CIQ 12860.0–12860.0 vs release 50.7–51.7 →
  MISMATCH flag`. **Nothing about that was a verification.** CIQ's revenue guide is **FQ3 2026** —
  one quarter, 12,860.0 — and the release guides **FY2026**. Four quarters at CIQ's own number is
  **51,440, INSIDE the annual guide**: the two sources CORROBORATE, and the check reported them as
  contradicting. `guide_verification` compared the numbers and had no idea the periods differed.
  **WHY IT MATTERS BEYOND A LABEL:** a revenue-guidance MISMATCH reads as management missing its own
  number — the analyst's finding was raised as evidence of deteriorating execution — so a spurious
  one manufactures exactly the impression the flag exists to warrant. **NOT NFLX-SPECIFIC:** any
  name whose CIQ guide period differs from the period its release guides gets one.
  **THE FIX IS THE REFUSAL ALREADY BESIDE IT.** Cross-basis (LEVEL vs CHANGE) refuses rather than
  derives; cross-PERIOD now refuses identically. Annualising the quarter to force the comparison
  would manufacture the base the check exists to verify — a guide is not four equal quarters — which
  is the same manufactured-base argument the cross-basis refusal already makes. The period now RIDES
  WITH THE NUMBERS on both sides (`revenue_guide_lohi` → `(lo, hi, period)`, `_release_revenue_guide`
  → `(lo, hi, qual, basis, period)`), for the reason the BASIS does. **REFUSES ONLY WHEN BOTH LABELS
  DECIDE A SCOPE AND THEY DIFFER** — an unrecognised label leaves prior behaviour untouched, because
  inventing a scope would silence REAL mismatches (the opposite failure).
  *Verified on the committed artifact's own inputs (not synthetic): CIQ `FQ3 2026`→quarter, release
  `2026`→annual → the shipped MISMATCH becomes "CIQ guides a QUARTER … the release guides a YEAR …
  NOT CROSS-CHECKED"; same-period pairs still VERIFY and real disagreements still MISMATCH. 16 pins
  incl. the before/after in one test (withholding the periods reproduces the shipped string) and
  every period shape in the corpus (`FQ3 2026`/`FY 2026`/`Q3`/`2026`/`Fiscal 2028`/`next-fy`, and
  `H1 2026`→undecidable). ruff + mypy --strict (124) + pytest 2316 green.*
  **HALF-YEAR IS A SCOPE, NOT AN UNDECIDABLE (review finding, #429).** The first cut returned `None`
  for `H1 2026` on the reasoning that a half-year "decides neither" — but it names a determinate
  six-month span exactly as `FQ3` does, so refusing on it let an H1-vs-FY pair fall straight through
  to the numeric comparison and print the same false MISMATCH this PR was written to stop. Now a
  third scope (`H[12]`/`[12]H`/`first|second half`/`six months ended`).
  **PROTECTIVE, NOT CORRECTIVE — measured, not assumed.** Across every committed dossier the labels
  that actually REACH `guide_verification` are only `FQ*`/`FY*` (CIQ side, from
  `guidance_bridge_rows[].period`) and `2024`/`2025`/`2026`/`Fiscal 2028`/`Q1`–`Q4`/`next-fy`
  (release side, from `primary_source.releases[].guidance[].period`). **No committed name produces a
  half-year guide period today**, so this repairs no live page — it closes the path before one does,
  the same footing as #426's as-of bound. The worded half-year labels that DO exist in the corpus
  (`first half of 2026`, `six months ended June 30, 2026` ×12) sit in `operating_drivers.rows[]`,
  a different consumer that never calls `period_scope`.
  **ORDER IS LOAD-BEARING IN BOTH DIRECTIONS**, and pinned: half must beat annual (`H1 fiscal 2026`
  contains "fiscal", so annual-first would call a six-month guide a YEAR — a wrong scope SILENCES a
  real mismatch, strictly worse than the undecidable it replaced), and quarter must beat half
  (`Q2 2026, second half of quarter` is a QUARTER). Mutation-tested by swapping the two branches:
  `H1 fiscal 2026` → `annual` and the pin reddens. `nine months ended …` stays `None` deliberately —
  a YTD span is none of the three and guessing one would manufacture a refusal.
  **NOT FIXED HERE, RECORDED:** the release leg ALSO carried a unit error — `$50.7-$51.7` **billion**
  parsed as `$M` because the verbatim was truncated before the word "billion". Current
  `parse_release` scales correctly WHEN the word is present (tested: 50,700–51,700), so this is
  likely a stale artifact predating #411 — **unverified against the live filing**, and the period
  refusal above holds either way (it fires on correct units too).
- **A "5-YEAR" PERCENTILE HELD 9.4 YEARS (same PR).** `ev_ebitda_percentile_5y` is the workbook's
  FULL quarterly Close history — NFLX's is **38 closes, 2017-03-31..2026-06-30 = 9.2y** — and the
  source_ref named a COUNT, which does not reveal a span. A reader trusting the field name divides
  38 quarters into the 5 years it claims and reads a different window than the one that produced the
  number. **THE VALUE IS UNCHANGED** (full history is the better distribution — more of the name's
  own cycle — and re-cutting it would move a decision number by relabelling); the SPAN is now stated:
  `— 38 quarters spanning 2017-03-31..2026-06-30 (9.2y)`. **THE FIELD IS NOT RENAMED:** it is a
  REQUIRED field on a frozen model that 11 committed dossiers and the suite parse, and this repo has
  already ruled once that a bare rename breaks committed artifacts (the `ev_ebitda` scalar, §2) —
  an honest label is the non-breaking half; a true rename needs a schema migration + fleet
  re-assembly and is NOT done here. An unparseable header omits the span rather than guessing one.
- **A `B` SUFFIX IS NOT A UNIT THE PARSER KNEW — $51.7bn READ AS $51.7M (2026-08-12,
  fix/guidance-unit-suffix).** Found validating an analyst's reading of the committed NFLX page.
  The dossier carried `revenue 2026: 50.7–51.7 $M` for a company guiding **$50.7–51.7 BILLION**, in
  the exhibit the dossier itself cites: *"We continue to project 2026 revenue of **$50.7-$51.7B**"*
  and *"we forecast 2026 revenue of **$50.7B-$51.7B**"*. `_GUIDE_RANGE` read only the SPELLED-OUT
  `million|billion`; the suffix form did not exist to it. **This is the Concentrix
  billions-as-millions defect a THIRD time** (after BellRing's shared range), against this module's
  own rule that a magnitude error in a decision figure is worse than an absent one.
  **THREE FAILURES IN ONE REGEX, all silent:** (1) a TRAILING suffix was ignored → 50.7 for $50.7bn,
  a **1000x understatement**, and the verbatim stopped at "51.7" so the page showed a sentence
  ending mid-number; (2) a LEADING suffix **broke the match entirely** — `$50.7B-$51.7B` and
  `$985M-$995M` parsed to NOTHING because the `B` sat where the separator had to be, so the guide
  was DROPPED with no flag (the dropped-clause class that cost ten of seventeen clauses on the
  change-basis fix); (3) the trailing unit was applied to BOTH numbers, so `$500 million to $1.2
  billion` produced **low=500,000 against high=1,200** — a floor 400x its own ceiling, and nothing
  rejected it.
  **THE FIX:** `bn`/`mm`/`[MB]` join the unit alternation on BOTH sides, each side scales by ITS OWN
  stated unit, and a bare side inherits the trailing one (so `$2.465 to $2.49 billion` is unchanged).
  The single letters carry `(?![A-Za-z])` because `[MB]` under `re.I` otherwise eats the first letter
  of the next word — *"$2.4 to $2.5 **b**ased on…"* would read billions, the same magnitude error
  inverted; that guard is pinned.
  **AN IMPOSSIBLE RANGE IS NOW REFUSED, AND DELIBERATELY NOT SORTED (review finding, #430).**
  Per-side scaling is what made the reverse order reachable: `$1.2 billion to $500M` arrived as
  **low=1,200 high=500** and was emitted as real guidance — printed and handed to the cross-check —
  with nothing rejecting it. **SORTING IS THE WRONG REPAIR**: it would state 500–1,200 as the
  filing's range when the filing said the reverse, and if the true cause is a MIS-PARSE (unit words
  bound to the wrong sides) sorting hides the evidence instead of surfacing it. The refusal is
  ATTRIBUTED — it carries the bounds it rejected and the sentence — so a reader can settle it from
  the filing, which a silently dropped guide would not allow.
  **NOT the same as the change-basis swap one loop down, which DOES sort**: there the inversion is
  the mechanical consequence of applying a sign (a decline range signs to −350..−300), not an
  anomaly in what was written. That boundary is pinned by its own test so the new refusal cannot
  leak into it and start refusing legitimate decline guides.
  **PROTECTIVE, NOT CORRECTIVE — measured:** 56 committed guidance items carry both bounds and
  **none is inverted**, so no live page changes. Mutation-tested by replacing the refusal with a
  sort: the pin reddens (`an impossible range must not reach GuidanceItem as though it were a
  guide`), so refuse-vs-sort is discriminated rather than merely described.
  *Verified on the REAL exhibit end-to-end (fetched 0001065280-26-000137 EX-99.1): the guide now
  parses **50,700–51,700 $M**, was 50.7–51.7. 20 pins on frozen filed text — the 5 behavioural ones
  FAIL on the pre-fix parser and the "must not change" ones PASS on both, so the pin is
  discriminating rather than incidental. ruff + mypy --strict (124) + pytest 2320 green; the corpus
  guidance pins are unmoved.*
  **BLAST RADIUS (measured, not assumed):** across the 14 committed dossiers, five names carry a
  "no anchored pattern — guidance" flag AND no revenue guide — **BRBR, FUBO, IT, SMPL, V** (IT: 0
  guides against 5 such flags; V: 0 against 3) — the signature of failure (2). These are SUSPECTS
  sized by signature, **not confirmed**: each needs its own exhibit fetched. NFLX is the one proven
  case. **Nothing was re-assembled here** — the artifacts still carry the old numbers until a
  re-assembly runs.
  - **ALL FIVE CONFIRMED AGAINST THEIR FILINGS 2026-08-12 — NONE WAS A SUFFIX DROP, and the
    signature was a FALSE POSITIVE (fix/net-sales-is-the-revenue-line).** Each exhibit fetched and
    re-parsed with the merged parser: **BRBR** guides *"fiscal year 2026 net sales outlook of
    $2.335-$2.375 billion"* → parsed correctly as **2335.0–2375.0 $M**; **SMPL** guides *"$1.345 and
    $1.355 billion"* → **1345.0–1355.0 $M**. Both were extracted ALL ALONG, under the metric name
    **`net sales`** — and the sweep that produced the five filtered on `metric == "revenue"`, so it
    reported its own filter as a parser defect. **IT** points the reader to *"an earnings supplement
    available on the Company's Investor Relations website"* — the guide is not in the 8-K at all;
    **V** and **FUBO** state no numeric revenue guide in the exhibit. So the suffix fix's blast
    radius is **NFLX alone**, as proven, and the sentence above overstated it. *(The lesson is the
    one this repo keeps re-learning: a signature is a hypothesis, and only the filing settles it.)*
  - **BUT THE CONFIRMATION FOUND A DIFFERENT, REAL DEFECT — "net sales" never reached the
    cross-check.** `_release_revenue_guide` matched the string `"revenue"` exactly, so a net-sales
    guide was invisible to it and BRBR's page reads **"CIQ 2335.0–2375.0 vs release NO NUMERIC
    OUTLOOK → not cross-checked"** — while the release it cites states **2335–2375, the same
    numbers**. That is a cross-source **VERIFIED** reported as nothing to compare. **A verification
    that silently declines to run is worse than one that fails:** "not cross-checked" reads as *we
    looked and there was nothing there*, the false-UNKNOWN shape this repo closes elsewhere.
    **FIXED IN THE CONSUMER, NOT THE PARSER** (`_REVENUE_LINE_METRICS = {"revenue", "net sales"}`):
    `_guide_metric` deliberately keeps the filer's own word so BellRing's page says *net sales*;
    normalising at parse time would rename the metric on every page and churn the artifacts and pins
    that carry it. The synonym belongs to the consumer that needs it. *SMPL composes with the period
    refusal: its release guides the YEAR (1345–1355) against a CIQ QUARTER (322–332), so seeing the
    guide is what lets that refusal fire at all — it previously read "NO NUMERIC OUTLOOK", naming
    neither. 6 pins, ALL failing on the pre-fix consumer (behavioural, not an ImportError — the new
    symbol is imported locally so the file still collects). ruff + mypy --strict (124) + pytest
    2414 green.* **ARTIFACT: NOT LANDED.** `guide_verification` is computed at ASSEMBLY, not by
    `recompute_derived` (which rebuilds only TEV + implied levels), so a transform-free refresh
    moves nothing — verified, the pass touched no page. **BRBR and SMPL keep the wrong line until
    re-assembled** (operator item below).
- **A 24-YEAR-OLD NUMBER SAT UNDER "LATEST GUIDE" (2026-08-12, PR-6).** NFLX's guidance table
  opened with `Gross Margin % — '47.00 - 48.00' for FQ4 2002`, dated **2002-10-17**, with the Age
  column two places right reading `8686d (stale)`. Not one odd row: the builder picks the newest
  guide with a PARSEABLE RANGE, so a company that STOPPED guiding a metric keeps surfacing whatever
  it last said — NFLX 2002/2003, EPAM 2016, AORT 2019, UBER 2020 (×2), V 2020.
  **THE TEST IS THE GUIDE'S PERIOD, NOT ITS ISSUE AGE** (review finding, #423). Age was the first
  criterion — a measured 365d bound sitting in the corpus's empty 238d–969d band — and it is WRONG
  IN BOTH DIRECTIONS, with a counterexample each way in the same corpus: **VITL**'s gross-margin
  guide is dated 2023-11-02 (977d) but is **for FY 2027**, still ahead of a 2026 as-of — long-term
  guidance stays applicable without being reissued, so "none current" is simply false. **MVST**'s is
  only **238d** old but is **for FY 2025**, a year already closed and never reguided — genuinely no
  current guide, and the age rule MISSED it. The issue date says nothing about applicability. The
  switch keeps all 10 true positives, drops the VITL false positive, and catches MVST.
  An unreadable period is LEFT ALONE: a false demotion misleads, a missed one leaves the Age column
  still telling the truth.
  **DISPLAY-ONLY, AND NOTHING IS DELETED:** the figure stays in its cell reframed as `none current
  (last: …)`, demoted rows sort BELOW current ones (sheet order put NFLX's two dead guides first),
  and `dossier.json` is byte-untouched — verified, 0 JSON files changed by the pass. Checked before
  choosing that surface: no committed synthesis quotes a figure from any >1y-stale guide, so the
  harm was to a human reader and the fix belongs where a human reads.
- **"FREE CASH FLOW" MEANT TWO DIFFERENT THINGS AND THE PAGE NAMED NEITHER (2026-08-12, PR-5).**
  `quality.free_cash_flow` reads CIQ's `Levered Free Cash Flow`. Against the SAME sheet's
  `Cash from Ops. − Capital Expenditure` the two agree on **exactly one** committed name (V, 0.97×);
  the other thirteen run **NFLX 2.28× · MVST 1.54 · CNXC 1.51 · EPAM 1.35 · NCNO 1.25 · SMPL 0.89 ·
  IT 0.85 · UBER 0.72 · BRBR 0.70 · VITL 0.60 · VRRM 0.51 · FUBO 0.27 · AORT −0.47 (OPPOSITE
  SIGNS)**. So this is not a content-company quirk — they are different measures nearly everywhere.
  **NFLX is why it reaches a reader:** the page carried **$25,388M** against CFO−capex of
  **$11,152M** while management guides ≈$12.5bn, under a synthesis quoting it as self-funding
  evidence. FY17 makes it unmistakable: **+$6,673M** levered while CFO that year was **−$1,786M**.
  **The CIQ figure is KEPT, not replaced** — it is the panel's own measure, consistent across the
  comp set; swapping it for our arithmetic would put a derived number where a reader takes the
  vendor's. Both stated, each named.
- **THE CASH-FLOW ROWS WERE DISPLAY-ONLY — a house-rule violation found while fixing the above
  (2026-08-12, PR-5).** `Revenue ($M)` carried 12 structured `values`; `CFO`/`Capex`/`FCF` carried
  **ZERO** — `cells` only. Anything wanting CFO−capex had to re-parse `"11,971"` out of rendered
  text, which is the forbidden shape ("parsers consume structured values, never rendered strings")
  and the class of the thousands-blind `$1,101.80M` incident. `clean_num` already produced the
  number; the row builder formatted it and discarded it. Fixed at source (`cf_num` returns the
  number, the call site formats), so the basis note derives from values rather than strings.
- **`_fact` DROPS THE NOTE ON A *PRESENT* FACT — 55 of NFLX's 135 present facts carry one nobody
  renders (found 2026-08-12, PR-5; NOT FIXED).** The note reaches `dossier.json` and never the
  page. PR-5 renders the FCF line specially rather than changing `_fact`, because rendering all of
  them would add ~55 mostly-verbatim lines to every page — but some look decision-relevant
  (`valuation.ev_ebitda`: *"trailing only — no forward basis; cannot distinguish a temporarily
  depressed…"*). Wants a curation pass of its own: which of the 55 are decision values and which
  are audit context.
- **THE DEBT SCHEDULE HAD NO AGE, AND ONE STILL LISTS A DEAD FACILITY —
  `capital_structure.panel_vintage` (2026-08-12, PR-3).** NFLX's page lists the Warner Bros.
  Discovery bridge facility; its commitments were terminated **2026-02-27** and the panel is dated
  **2026-01-23**, so the page cannot know.
  **THE AGE WAS INVISIBLE TO A FORMAT MISMATCH.** `freshness._PANEL_KEY` DOES match
  `detail_as_of` — but `freshness._ISO` wants `2026-01-23` and CIQ writes `Jan-23-2026`, so the key
  was found and the date never extracted. Measured across all 14 committed dossiers, source filings
  run **82–280 days** behind their own build (SMPL 280 · V 277 · BRBR 265 · NFLX 199).
  **THE OBVIOUS FIX IS REFUSED, ON THE MEASUREMENT.** Teaching `_ISO` the CIQ format routes the
  panel into `panel_age(kind="export")` → `check_freshness`, a GATE whose ceiling is **45 days**
  that **all fourteen names are past** — it would raise `FreshnessError` on the entire fleet. That
  is the failure `check_freshness`'s own docstring names ("a guard that stops every build is a
  freeze wearing a guard's name"). The age is rendered beside the schedule instead, and
  `test_the_panel_is_deliberately_kept_out_of_the_freshness_gate` pins the decision WITH its
  measurement so a later "improvement" has to confront the number.
  **THE TERMINATION HALF NEEDS NO FILING READ:** item **1.02** is carried in the filer's own
  submissions index, so a 1.02 filed AFTER the panel's source date proves the panel cannot reflect
  it, from dates alone. **BOUNDED AT BOTH ENDS — `panel filed < 1.02 <= reference_date`** (review
  finding, #416): the first cut had no upper bound, and since `recent_filings` returns the CURRENT
  submissions index it reported whatever existed when the code RAN. Two of three committed warnings
  were LOOKAHEAD — UBER's 2026-07-29 record flagged by an 8-K filed 2026-08-07 (+9d), VITL's
  2026-07-06 record by one filed 2026-08-06 (+31d) — the class `close_as_of` refuses one module
  over, arriving through a different door, and it also made the artifacts irreproducible.
  **Fleet as-of-bounded: 1 of 14 warns** — NFLX (WBD, 2026-02-27), the only one that had happened
  by its record's date. UBER's Delivery Hero (2026-08-07) and VITL's refinancing (2026-08-06) are
  REAL and will surface when those names are re-assembled at a later as-of (item 7). A FLAG, never
  a deletion, and never a claim about WHICH instrument died: matching a termination to a facility
  means reading the 8-K, and a wrong match is worse than an honest "something ended".
- **COVENANT POINTERS FOUND NOTHING FOR 4 OF 14 NAMES — DIAGNOSED AND FIXED (2026-08-12).** FUBO,
  SMPL, UBER and VITL returned **zero** `covenant_pointer_rows`. **ROOT CAUSE: `ex-?10\d` demands a
  DIGIT immediately after "10"**, so it matched only the compacted filename form (`ex102` = exhibit
  10.2) — the MINORITY convention. Real filenames in this fleet's own filings: `vitl-ex10_10.htm`,
  `aort-…xexx1032.htm`, `fubo-…exx1026.htm`, `f8k032018ex10-1_simplygood.htm`, `a19-22146_1ex10d1
  .htm`. **NFLX was the only name it matched, and only by its filing agent's naming style.**
  **THE FAILURE WAS TOTAL RATHER THAN PARTIAL** because the fragment appears in BOTH passes — the
  10-K exhibit index filter AND `_AGREEMENT_EXHIBIT_RE` for the efts hits — so one flaw closed both
  routes on the same names. Now one shared `_EX10_RE`, pinned to stay shared.
  **WHAT IT WAS NOT**, each eliminated before landing on the regex: efts works (UBER 17 hits, SMPL
  46, AORT 16); the instruments do qualify for a query (all four generate one); the exhibits exist
  (SMPL's 8-K hits carry a real credit agreement the filter rejected). Nothing to do with company
  type — purely filing-agent filename convention.
  **MEASURED LIVE, all 14: FUBO 0→6 · SMPL 0→3 · UBER 0→8 · VITL 0→3**, and seven already-working
  names gained pointers too (AORT 9→13 · CNXC 5→9 · MVST 6→9 · IT 6→7 · EPAM 4→5 · NCNO 4→5 ·
  VRRM 5→6). `10` stays pinned so exhibit 19.1/21.1 still correctly miss.
  **SECONDARY, also fixed:** `_covenant_query` had no `note` branch, so convertible notes queried
  "Loan Agreement" instead of "Indenture". Not the binding constraint (querying "Indenture" for
  UBER still returned zero exhibit-bearing hits before the regex fix) but it decides what the
  search ASKS.
  **THIRD, also fixed — two failures that read alike:** `covenant_pointers` said "no CIK-scoped
  agreement exhibit located" while `covenant_terms` two fields away said "extraction failed: no
  covenant terms extracted from LOCATED exhibits". One page asserting both, pointing at opposite
  remedies (the LLM phase vs the pointer search). The digest now keys on whether a pointer exists.
  **CORRECTION TO THE ORIGINAL ENTRY:** the "exactly 116 covenant terms" flagged as suspicious was
  `len()` on a STRING — the character count of a shared failure message, not a count of terms. That
  measurement error is what made four names look like they shared a data shape when what they
  shared was a code path.
  **AS-OF BOUNDED (review finding, #426):** `_covenant_pointers` took `tenks[0]` from TODAY's
  submissions index and accepted all efts hits, so re-assembling a historical dossier could attach
  an agreement filed after its own reference date — the #416 lookahead class again, and **the
  widened matcher made it REACHABLE** for the four names that previously located nothing. Both
  passes now bound to `reference_date`. On today's data the bound changes nothing (bounded and
  unbounded runs are identical across all 14), so it is protective rather than corrective — pinned
  by a fixture whose newest filing postdates the as-of.
  **THREE STATES, NOT TWO (review finding, #426):** the digest keyed on `bool(ptrs.value)`, which is
  falsy for BOTH "the search ran and found nothing" AND "the search could not run" (no CIK, EDGAR
  unreachable) — so a lookup that never happened reported a COMPLETED search. Introduced WHILE
  fixing a two-states-must-not-read-alike bug. Now keyed on `COVENANT_SEARCH_FOUND_NOTHING`, a
  shared constant rather than a duplicated literal, so the two cannot drift.
  **ARTIFACTS NOT UPDATED (deliberate):** pointers are ASSEMBLED, not refreshable, and the terms
  they unlock are LLM-extracted. Injecting rows via the transform seam would leave a page carrying
  pointers beside a digest still saying none were located — the PR-1 half-refresh incoherence. The
  committed pages gain this at the next **re-assembly**, which is where the terms arrive too.
- **QUARTERLY ONE-OFFS HAD NO ROUTE ONTO A PAGE — `quality.nonoperating_earnings` (2026-08-12,
  PR-4).** NFLX's Q1-2026 carries a **$2.59bn** Warner Bros. Discovery termination fee below the
  operating line (40% of pre-tax, 21% of revenue) and UBER's Q2-2026 ~**$1.39bn** of investment
  revaluation. Neither reached any surface: the CIQ unusual-items block is **ANNUAL-only**, so a
  quarterly one-off stays invisible until it lands in a fiscal year, and **no XBRL non-operating
  concept was read at all** (verified across two search vocabularies).
  **DERIVED, NOT PICKED — the corpus forced it.** Reading a one-off gain tag directly does not
  survive the filings: UBER's Q2-2026 revaluation is carried by THREE overlapping tags at THREE
  values (`EquitySecuritiesFvNiUnrealizedGainLoss` 1,727M · `DebtAndEquitySecuritiesGainLoss`
  1,612M · `OtherNonoperatingIncomeExpense` 1,342M), and the aggregate `NonoperatingIncomeExpense`
  is absent for ~half the fleet and was abandoned by UBER after 2025-09-30. `pretax − operating` is
  the same block by income-statement arithmetic, from two totals the filer states.
  **BOTH PLANNED PREMISES WERE FALSIFIED BY MEASUREMENT** and the build followed the data instead:
  (a) "add the two XBRL concepts" — there is no stable pair, per above; (b) "reuse the existing
  10%-of-market-cap floor" — **it fires on NEITHER target case** (both ≈1% of cap), because that
  floor was calibrated for balance-sheet-scale impairments, not earnings-scale one-offs. Shipped
  instead: 20% of pre-tax AND 5% of revenue, measured on 13 names × 4 quarters.
  **AN OUTLIER-VS-OWN-HISTORY TEST WAS TRIED FIRST AND REJECTED.** It catches NFLX (19× its median)
  and **misses UBER (2.6×)** — UBER revalues every quarter, so a large non-operating swing IS its
  norm and its median rises to meet it. The reader's question is not "is this unusual for them" but
  "how much of this is operating", which holds however habitual the behaviour. Fleet today: 4 of 15
  flag, 9 clean, 2 UNKNOWN (NCNO and WERN file no quarterly pre-tax tag).
  - **EVERY MATERIAL QUARTER IS NAMED, NOT THE LARGEST ONE (2026-08-12,
    fix/nonoperating-all-quarters).** The analyst's own objection landed on this field: they flagged
    UBER's **Q2-2026 $1.6bn** equity-revaluation benefit, and the page did not mention that quarter.
    It named **only the largest by revenue share** — 2025-09-30's +$1,507M — and called it *"an
    earlier quarter still inside the trailing four"*, which tells a reader the distortion sits
    BEHIND them and the recent quarters are clean. **UBER has THREE material quarters and both
    dropped ones are the RECENT ones:** 2026-03-31 **−$1,427M** (exceeds pre-tax) and 2026-06-30
    **+$1,387M** — the analyst's. The selection rule was defensible in the abstract ("the one that
    most distorts a trailing figure") and wrong in its own live case, because the figure a reader
    divides by is an LTM one, so every quarter inside it counts.
    **AND THE NET IS THE POINT THE MAXIMUM CANNOT MAKE.** UBER's two unnamed quarters point OPPOSITE
    ways and very nearly cancel: the four net to **+$1,521M**, not the +$1,507M the page implied a
    reader should carry. Naming the maximum asserted a distortion the trailing figure does not have.
    The multi-quarter form states the count, every item, and the net; **the single-quarter form is
    UNCHANGED** (NFLX still reads verbatim as pinned — it has one material quarter, and only the
    multi form has no room for the where-clause).
    *Verified on the committed fixtures: UBER now names all three + the net; NFLX and V byte-identical.
    **ARTIFACT PASS via the MECHANICAL-ONLY refresh** (`refresh_dossier(transform=…)`, no
    re-assembly, no synthesis re-roll): **UBER and MVST** moved — MVST is **4 of 4** quarters
    material — and the `moved_cited_claims` guard PASSED rather than being bypassed, because every
    figure UBER's synthesis cites (1,507 · 58% · 2025-09-30) is still on the page; the new text adds
    quarters, it does not restate the one the prose quotes. **FUBO REFUSED, correctly** — it is
    SEALED by its own `known_wrong.json`, and the write path said so. 4 pins (all three quarters
    named · the net · the count leading · the single-quarter form unchanged); 2 FAIL without the fix.
    ruff + mypy --strict (124) + pytest 2377 green.*
- **`extract_points` RETURNS STALE DATA WHEN A FILER ABANDONS ITS PREFERRED ALIAS (found
  2026-08-12, PR-4; BROADER THAN THAT PR).** It is first-alias-**with-data**-wins, and an abandoned
  tag still has data — just old data. **UBER stopped filing
  `RevenueFromContractWithCustomerExcludingAssessedTax` after 2019-06-30** and has used `Revenues`
  ever since, so asking for "revenue" returns a **seven-year-stale** quarter. PR-4's first cut
  silently resolved its whole field to 2019 because of it. Worked around LOCALLY there
  (`_quarterly_map` unions period coverage across aliases, keeping precedence within a period);
  **the general defect is untouched** — any consumer taking "the latest" from a concept whose
  preferred alias was abandoned has the same exposure. Same class as the `dep_amort` and Visa-`dei`
  abandoned-tag findings. Not fixed fleet-wide because it would move revenue everywhere and wants
  its own brief.
- **ANCHORED VERBATIMS WERE CUT MID-WORD ON 40% OF THE CORPUS — bounds measured, not chosen
  (2026-08-12, PR-2).** `_attr_verbatim`'s sentence-end search window (`cause_end + 170`) silently
  degraded to a raw offset cut whenever the real sentence ended later, and `frag[:340]` cut whatever
  survived. Measured across all 14 committed names' 10-Q primary documents — 40 attribution rows —
  **16 were cut mid-word on four names** (UBER 12, SMPL 2, MVST 1, VRRM 1); **four severed a dollar
  figure.** The worst: UBER's UK sentence ended at *"…negatively impacted reven"*, dropping **"by
  $1.1 billion"** — the number explaining why Mobility revenue grew 1% against Gross Bookings +22%.
  A third severed figure surfaced in the fix: a **$808M** Driver-payments offset in cost of revenue.
  True distributions: cause→sentence-end p50 138 / p90 285 / **MAX 477**; full fragment p50 324 /
  p90 482 / **MAX 633** — so 170 and 340 sat *below the p90 of the thing they bounded*. New:
  window **520**, cap **700**, and any cut that still happens is at a WORD boundary with an
  ellipsis. **The second branch was the near-miss**: marking only the cap left the window-bounded
  fallback exactly as silent as the bug — caught by the run-on test, not by reading.
  **WHY WIDENING IS SAFE STRUCTURALLY:** `text.find(". ", cause_end)` returns the FIRST boundary
  after the cause, so the window only decides ACCEPT-vs-offset-cut; it can never reach a second
  sentence. **DIFFERENT SEAT FROM THE BRBR FIX** — BellRing's severed reversal was `llm-fenced`
  (`driver_extract.py`, repaired by the following-paragraph carry); these are `anchored`
  (`filing_sections.py`). Same class, two seats, neither fix covers the other.
  **PRIMARY HARM PATH IS THE SYNTHESIS, not the page**: the rendered `.md` never carried these
  verbatims, but `_operating_drivers_digest` puts `verbatim` in front of the LLM — so the model
  reasoned from truncated evidence. That is the BellRing shape exactly.
- **SPOT WAS UNAUDITABLE, NOT UNVALIDATED — measured across all 8 records × all 3 stores
  (2026-08-11).** Every committed spot is a REAL EOD close, equal to its stored bar with delta
  **exactly 0.0**; not one is an analyst's intraday number. What differs is which store can SEE it:
  BRBR and EPAM are struck at 2026-08-07 and resolve in `-sl` ONLY. **A refuse-on-mismatch check run
  from `-wb` would therefore have blocked two CORRECT records** — every spot is auditable somewhere,
  none everywhere, and a refusal encodes an assumption about which store is asking. Notes, never
  problems. **The nearest-bar VALUE search was designed and then killed by its own corpus:** it is
  one-to-MANY on real data (AORT's 25.37 → 2 bars sixteen months apart, MVST's 0.9188 → 4 spanning
  two years, WERN's 46.04 → 2), and on the two records `-wb` cannot reach it returns a coincidental
  collision (11.55 from June, 97.35 from May) — noise presented as a finding. Keyed by date,
  `prices` is one-to-one. **And the date was already there, in prose:** all 8 `spot_source` strings
  name an ISO date, so `spot_as_of` PROMOTES an existing fact rather than adding one — but BRBR's
  carries THREE (close 08-07, `-wb` frontier 08-04, three-store agreement 07-29), so no regex
  extracts it and the field is WRITTEN. A live instance of "parsers consume structured values, never
  rendered strings". Seats: `vinci audit spot` (whole corpus) + `scenario-supersede` (at the write).
- **DATA-TOPOLOGY of git-ignored artifacts (verified 2026-07-13 by `ls`; `data/` is PER-WORKTREE, NOT
  shared).** `-s2`: `data/assay/` = 14 cards, `data/assay_history/` = 3 driver subdirs + `manifest.jsonl`
  (46 snapshot files), `data/assay_cache/` = 1944 efts files. `-main`: `data/priced_check/report_all.txt`
  present, `data/snapshots/candidate_themes.jsonl` = 35 (the restored June-17 harvest) +
  `candidate_themes.2026-06-17.backup.jsonl`, `data/research/` (the insilico + t012-senior-housing
  adjudication memos, 2026-07-13). `data/scan_history/` is EMPTY in BOTH worktrees — by design,
  until the first post-merge exposure scan or Component-A sweep writes it. **SESSION RULE: print the
  worktree + `pwd` before touching `data/`** — the same path holds different contents per worktree.
- **UNIVERSE-COVERAGE FLAG (report-only; bounds what Component-A can cluster) — SDGR ABSENT from
  `data/snapshots/securities.jsonl` by a COVERAGE GAP, not an exclusion rule.** The file is
  `Store.export_snapshots()` of the `securities` table (`store.py:375`), seeded by `build_universe` from
  `resolver.iter_universe(XNAS/XNYS/XASE)` (7641 considered) then fail-closed-gated. SDGR (CIK 1490978,
  Nasdaq, SIC 2834, 1270 grouped-daily bars) clears exchange / SIC / price / cap-band, but is dropped at
  the **`no_shares` gate (`vinci/universe.py:107-109`)**: the builder reads shares ONLY from the EDGAR
  `dei:EntityCommonStockSharesOutstanding` frame (`vinci/edgar/client.py`, dei-only when this flag was
  written; a us-gaap fallback was since added — see CORRECTED below), and
  SDGR tags its shares under `us-gaap:CommonStockSharesOutstanding` (its `dei` block is public-float only)
  → `shares[cik]=None` → fail-closed drop. Clinching differential: CERT and SLP DO report
  `dei:EntityCommonStockSharesOutstanding`; SDGR does not. So NO attribute rule excludes SDGR — but a
  us-gaap-shares fallback does NOT recover it: **CORRECTED 2026-07-13 (shipped; see the §2
  shares-tag-fallback entry).** The shipped fallback is FRAME-based (recent calendar-quarter
  `us-gaap:CommonStockSharesOutstanding`, matching the dei path); SDGR STOPPED tagging that concept after
  FY2023 (last frame value 2023-12-31), so it is absent from the recent us-gaap frames too — the fallback
  recovers 213 OTHER `no_shares` names but NOT SDGR, which remains an unfixed deeper gap (its recent share
  count lives off the calendar-quarter frame). **RE-CONFIRMED 2026-07-14 (sweep #2):** SDGR (CIK 1490978)
  has no shares in any queried calendar-quarter frame `CY2025Q1I…CY2026Q1I` → `no_shares`
  (`vinci/universe.py:114`); the original claim was CORRECT (an interim "never resolved into the entity
  master" phrasing during the run was imprecise — SDGR IS resolvable on Nasdaq and reaches the gates; it
  dies pre-`upsert` at `no_shares`). **NOTV — CORRECTED 2026-07-14:** the "absent from
  `company_tickers_exchange.json` entirely" claim was WRONG. SEC lists `[720154,"Inotiv, Inc.","NOTVQ","OTC"]`
  (ticker NOTVQ, venue OTC), so NOTV is PRESENT in the source but filtered at the exchange boundary
  `resolver.py:112` (OTC ∉ {Nasdaq, NYSE, NYSE American}); it even carries 34.9M XBRL shares, so it would
  clear `no_shares` on an allowed venue.
- **OPERATOR DECISION PENDING — two fail-closed coverage holes surfaced by sweep #2 (report-only; no fix
  without a decision).** (1) **`no_shares` calendar-quarter frame mismatch:** names whose cover-page
  shares date doesn't land on a calendar quarter-end instant are dropped at `no_shares` even when large
  and liquid — the 2026-07-14 roll-call hit PATH, SMR, HOOD, IBKR, CME (same class as SDGR). The current
  EDGAR frame reader can't see them; a companyconcept-per-CIK fallback would, at a per-name EDGAR cost.
  (2) **BDC blank-SIC exclusion:** HTGC/TSLX/GBDC/MAIN drop at `unknown_sic` (EDGAR submissions return a
  blank SIC → fail-closed) — the intended operating-co gate, but it also sweeps real BDCs. Both are
  DELIBERATE fail-closed behavior; widening either is an operator call, not a silent fix.

**OPERATOR TO-DO — backfill the IWM benchmark before any full `vinci dossier` re-assemble (from
feat/brief-decision-metrics, 2026-07-13).** Grouped-daily ingestion only stores the finalist universe,
so the benchmark index (`IDX-IWM`) is NOT populated by the normal pipeline. Run
`.venv/bin/python -m scripts.fetch_benchmark_iwm` (one cached Polygon call, idempotent) so a fresh
re-assemble computes `market_180d_return` and `mechanical.stock_performance` instead of failing loud to
UNKNOWN. The committed dossiers already carry `stock_performance` (refreshed via
`scripts.refresh_stock_performance`); this only matters when re-deriving from a DB without IWM bars.
Longer-term: fold the benchmark into the standing EOD ingestion so it is never a manual step.

**QUEUED (user-deferred 2026-07-11, "skip for now") — forward-multiple ladder UI.** The
`cross_name_anchor` ladder (Valuation) renders periods-as-ROWS × multiples-as-columns and truncates to
`_LADDER_KEEP` = NTM + FY26–FY28, noting "+N later fiscal years in JSON". Two available tweaks, both
deferred: (a) TRANSPOSE to multiples-as-rows × periods-as-columns to match the financial-summary /
valuation orientation (parser tests are on the derivation, not the render → safe); (b) revisit the
forward-window cap. NOTE FOR THE RECORD: the "+N in JSON" is a DELIBERATE near-term signal cap, NOT a
bug — FY29+ are thin, long-dated consensus (often 1 analyst), kept machine-complete in JSON, mirroring
the financial-summary capping its forward columns at FY27E. Do not "fix" it as a truncation defect.

**QUEUED (operator-approved 2026-07-13) — mechanism-coverage build brief (PR-B, the "90-second
handover").** Genesis: audit of the MOSL Mahanagar Gas note (11 Jun 2026 — the Brief's original
template) against our Brief. Scored: MOSL p1–2 structure 8.5 / reliability 4.5 (causal mechanism +
operational leading indicators, but verdict-first, no bear case, unsourced management-flow numbers,
TP arithmetic = 100% re-rating assumption); our Brief structure 7.5 / reliability 9 (source-bound,
fail-honest, but case points ATOMIZED — no mechanism). The one gap with teeth: forward operating
MECHANISM facts (leading indicator + base rate · pricing actions taken vs headwind · pass-through
structure · driver-materiality sizing). NEXT: draft the BRIEF-CONTRACT brief — `operating_drivers`
typed cited facts; EX-99.1 anchored tier (precedent: `_enrich_drawdown_drivers`) + transcript
LLM-fenced tier via the covenant_extract pattern (verbatim-validated; REVISES the "transcripts:
derive NO numbers" fence for a dedicated extraction phase only); driver × segment-share materiality
(UNKNOWN renders as UNKNOWN); a POSED (never forecast) per-case mechanism slot; Brief "Mechanism"
block. Honest scope: US KPI disclosure varies → UNKNOWN-heavy names expected; competitive-slack not
generically automatable. Brief first, human sign-off, then code.

**VERDICT-FIRST BRIEF — the machine-proposal pivot — BUILT + VERIFIED, PR OPEN
(#116, feat/verdict-first-brief, 2026-07-13).** CONSTITUTION CHANGE, decided by the operator with the
counter-case fully presented (automation-bias risk, no-tuning freeze, track-record
recharacterization) — a recorded pivot, not drift; CLAUDE.md amended in the same PR. The Brief now
LEADS with a machine-proposed directional verdict; the HUMAN's confirm/override is the verdict of
record.
- **Design — deterministic derivation, NOT a new LLM output.** `vinci/dossier/verdict.py`:
  face-validity-FROZEN 3-row mapping over the committed lean label — strongly-bearish→AVOID_TERMINAL
  · strongly-bullish→BUY · mixed→NO proposal (a two-sided read is the human's call, never a
  coin-flip); empty/unparseable/unrecognized → no proposal, fail-honest. The LLM STILL emits no
  verdict field — `Synthesis` unchanged, the no-conclusion schema pin stands, and the dossier
  package still cannot import the ledger writer (AST guard: `vinci.schemas.ledger` ≠ `vinci.ledger`).
- **ONE shared lean parser** (`verdict.split_lean`) now feeds the synthesis FALSE-BALANCE QA, the
  md machine-read, and the proposal — retiring synthesis.py's em-dash-only `eb.split("—")[0]`
  (the two-divergent-parsers bug class; dossier.js mirrors it as `deriveProposal`).
- **Ledger seal:** entries gain `{machine_proposal, machine_lean, proposal_assembled_at,
  disposition confirmed/overridden/no_proposal}`, stamped ONCE at log time; the CLI reads the
  COMMITTED `dossier.json` (never recomputed — as-of discipline; missing artifact → no-proposal
  fail-honest print; corrupt artifact → LedgerError, loud). Schema coherence validator REJECTS a
  disposition contradicting its (proposal, verdict) pair. Legacy payloads load all-None — a
  readable "pre-pivot" state.
- **Scoring — three curves from entry #1:** `ScoreReport` gains the machine shadow curve (machine
  BUY−AVOID spread, honest-None until both legs), disposition counts, and the RAW override subset
  (ticker · both calls · forward outcome). Human-final spread stays PRIMARY.
- **VERIFIED (real runs, committed artifacts):** MVST (lean `strongly-bearish`) renders
  `**Machine proposal:** AVOID — derived from the lean above` (the row names its DERIVATION, never
  re-quoting the lean's rationale — the read line directly above already carries it; operator
  caught the initial reason-echo as a #109-class dup, fixed same-day); AORT (lean `mixed`) renders
  `**Machine proposal:** none — evidence two-sided (mixed) — the human's call`; CLI-sealed a
  paper verdict from the REAL committed MVST artifact into a SCRATCH store — human BUY against
  machine AVOID_TERMINAL → `disposition: "overridden"`, `proposal_assembled_at:
  2026-07-10T07:06:48Z` round-tripped. ruff + mypy --strict (94) + full offline pytest green.
- **Tests:** derivation unit (3 rows + label normalization + 5 no-proposal negatives, incl. "a
  directional REASON never flips a mixed label"); FROZEN-fixture value pins (MVST/AORT leans as-of
  2026-07-13 as literals — ticker→verdict value pins live there, never on living artifacts);
  living-artifact e2e = phrasing-independent invariants only (rendered line == derivation of the
  same committed lean, mapping invariant, confirm/override slot present, pre-pivot slot gone);
  web-mirror static pins; ledger disposition positive+negative pins + legacy-load pin; scoring
  shadow-curve pins + store→harness→report carry-through.
- **ACCEPTED RISK (consciously, operator decision) + PRE-REGISTERED FALSIFIER:** a machine proposal
  ANCHORS the human — the fund's stated edge is the human discriminator, and a confirm-workflow can
  degrade it invisibly. Falsifier: if the override rate collapses toward ~0 OR the human-final
  spread tracks the machine spread within noise over the forward window → the anchoring concern is
  CONFIRMED → revisit verdict placement. The disposition lane makes this measurable from the first
  entry.
- **Incident→invariant:** LLM-free-verdict risk → Synthesis no-conclusion pin + AST
  no-ledger-import guard [shipped, pre-existing, re-verified] · incoherent disposition → schema
  coherence validator + negative pins [shipped] · proposal recomputed at log time → CLI seals from
  the committed artifact only [shipped; the "is it really the committed artifact" provenance has no
  machine check — accepted] · mapping outcome-tuning → no machine check possible (a human-review
  concern, same class as ranker weights) — accepted, guarded by CLAUDE.md language.
- **Blast-radius note:** committed `dossier.md` artifacts are PRE-pivot until the standing artifact
  pass re-renders them (tests render from JSON in-memory, so the suite is green either way).
- **ANTI-ANCHORING SURFACING + SEAL-ONCE DETERMINISM (2026-07-13, same-day revision of the pivot;
  feat/verdict-first-brief, merged current with main).** The pivot's own ACCEPTED-RISK falsifier —
  a SHOWN proposal anchors the human — is now STRUCTURALLY mitigated, not merely measured: **the
  brief HIDES the proposed verdict until the human logs theirs.**
  - **(surfacing)** `render_markdown(show_proposal=False)` is the default — the brief shows the
    machine READ (the evidence lean = assembly) but a SEALED-NOTE where the proposal was; the derived
    verdict is revealed only AFTER the human's verdict is logged (the ledger CLI prints it) or on an
    explicit `dossier --ticker X --show-proposal` peek. Web parity: `dossier.js teaserCard` gates the
    reveal on `!verdict`. Ledger gains `revealed_pre_verdict` (default False = decided blind;
    `log-verdict --saw-proposal` self-reports a peek → True flags an anchored disposition to
    down-weight). The machine READ stays — it is the assembled evidence summary, not the verdict
    (tiers, never the rank).
  - **(a) determinism lives in the SEAL, not the sample.** Reproducing the proposal via sampling is
    IMPOSSIBLE on Opus 4.8: `temperature`/`top_p`/`top_k` are REMOVED (400 "temperature is deprecated
    for this model" — confirmed live + Anthropic API docs), and there is no `seed`. A temp-0 branch
    was built and DISCARDED (it would 400 every real synthesis). It is also UNNECESSARY — the real
    requirement is ANTI-HINDSIGHT: the proposal derives from the COMMITTED artifact (assembly-time
    snapshot) and is SEALED once (append-only, `LedgerEntry(frozen=True)`), never re-derived after
    prices move. **k=1 seal-once is the design;** proposal noise is accepted and averages out across
    the ledger.
  - **(b) majority-of-k REJECTED.** A modal-lean vote over K synthesis runs would de-noise the
    proposal but costs a permanent ~5× per name for ~0 decision value: the proposal is HIDDEN until
    the human's verdict, so per-name split precision helps NO decision, and the ledger averages the
    noise across names.
  - **(c) driver-effect evidence (LOGGED, not re-run — stochastic, do not re-derive):** feeding
    operating drivers into synthesis moves the lean on operating-thesis names. VITL WITHOUT drivers
    ≈ 67% strongly-bearish / 33% mixed (proposal AVOID vs defer); WITH ≈ 8% / 92% mixed (defer).
    VRRM / MVST / EPAM: no material shift. The drivers appropriately escalate a de-rated name with a
    real cited counter-thesis from a confident AVOID to defer-to-human. (n≈12 draws/condition,
    temp≈1 — this is the record, not a reproducible number.)
  - **(d) PRINCIPLE:** machine proposals are MEASURED against the human, never SHOWN before the human
    decides — the same discipline as the theme edge's **tiers-never-ranks**. The disposition
    (confirm/override) is the disagreement ledger the pivot exists to produce; anchoring the human
    destroys that one measurement.
  - **(e) Option-B crude-rule DEMOTED to a future CONTROL lane (design-only, NOT built).** A proposal
    derived from deterministic committed signals (going-concern, drawdown, leverage-vs-peers,
    consensus-cut direction) was considered as the determinism fix; rejected as the PRIMARY proposal
    (cruder than the LLM's holistic lean) but recorded as a naive-baseline lane — a future shadow
    ledger reads human vs LLM-proposal vs crude-rule, making the LLM proposal's lift over a dumb rule
    measurable. Build when enough sealed proposals accumulate.
  - **(f) DUAL-LANE with/without-drivers shadow spread (design-only, NOT built).** Two proposal lanes
    — with-drivers vs without-drivers — sealed at assembly and tracked against the human's actual
    verdicts; the forward BUY−AVOID spread difference is the ONLY measure of whether driver-grounding
    improves the machine's directional skill. Meaningful only ACROSS the ledger (not per-name) and
    only post-seal-once. Trigger: enough sealed proposals accumulate to compare.
  - **Incident→invariant:** proposal anchors the human [the pivot's accepted risk] → brief hides the
    proposal until the human logs + `revealed_pre_verdict` stamp [shipped] · Opus-4.8 non-reproducible
    proposal → determinism relocated to the append-only seal (anti-hindsight); reproducibility
    consciously NOT required [shipped + recorded]. VERIFIED: ruff + mypy --strict (94) + full offline
    pytest green; the MVST brief hides the proposal by default (`sealed at assembly`) and reveals
    `AVOID` only under `--show-proposal`.

**OWN-HISTORY EXHIBIT → shared EXHIBIT frame — DONE (feat/own-history-align-frame, PR OPEN, 2026-07-13).**
After #108 + #110 merged, aligned the own-history exhibit ("Multiple vs its own trailing range") to the
shared `EXHIBIT` frame so all three panel exhibits read as one system: destructures `EXHIBIT` (canvas
760×276 / single 430 / cy0/cy1 band / fs / halo / margin), panels at 44→366 | 412→748, title 15, panel
11.5, axis 10.5, x/point 10 — matching revEbitda/return-ratios. The chart's extra metadata (log scale ·
as-of) + the low-confidence footnote moved BELOW the SVG (a muted caption) so the in-SVG frame stays
identical (title-only, no subtitle band eating cy0); "log scale" gated on per-panel `allLog`; ref-level
labels are value-only (dashed line marks the average) to fit the shared left inset. Confidence
de-escalation preserved (MVST 4-close → grey ▼, not red). Verified in preview: CNXC (dual, matches
return-ratios), MVST (single 430w + low-conf grey). Test pins all three exhibits destructure `EXHIBIT`.

**DOSSIER first-cut BRIEF redesign — BUILT + VERIFIED, PR OPEN (#98, feat/dossier-brief, 2026-07-09).**
The per-ticker dossier is now a THREE-TIER surface — **Brief / Analysis / Appendix** (client-side tabs +
PDF-scope dropdown), md↔web parity held. The **Brief** is reworked from a card into a market-standard
institutional first-cut memo (8 sections: teaser → setup → company & business → the case → financial
snapshot → valuation → catalyst & consensus → verify-first), modelled on a real sell-side report (Motilal
Oswal) adapted to the fund's discipline. **Guardrail held:** the machine renders NO verdict — the
Recommendation/Target slot is the HUMAN's ("not yet logged"); consensus, the implied-value ladder, and the
"machine read" are context, never a conclusion.
- **New assembled fields** (schemas.py, default None → other dossiers stay fail-honest): `sector` (SIC map),
  `industry` (CIQ GICS via `ciq_sheets.gics_industry`, SIC fallback), `exchange`, `business_description`
  (CIQ subject row), `MechanicalLayer.key_ratios` (CIQ Ratios sheet), `FilingRef.drivers` (B1 join).
  `requirements.CIQ_MODULES` gained the `profile` workbook; the coherence test stays green.
- **B1 informative drawdown:** `mechanical._enrich_drawdown_drivers` joins each gap-down 8-K → its parsed
  EX-99.1 drivers; MVST renders `adj EBITDA 2025 $44.7M (vs -$44.8M 2024); adj net income $13.0M (vs
  -$84.6M); $32.5M inventory impairment`.
- **Customers → concentration** (top-customer %, not raw names — names are analytically noise).
- **False-balance QA-check FIX + regression test:** `synthesis.py` read the whole evidence_balance string
  ("…eroding, mixed cash generation") and fired a spurious FALSE-BALANCE caveat; now reads the LABEL
  (`lean`), not the substring. `test_dossier.py` pins it — reverting lean→eb fails the pin.
- **VERIFIED (real-run, MVST):** ratios `RoE -9.3%; RoCE 1.5%; RoA 1.2%; D/E 0.70; current 0.96; div none`;
  GICS `Construction Machinery & Heavy Transportation Equipment` (vs SIC's coarse "Technology"); the
  spurious caveat is GONE from the re-assembled artifact. ruff + mypy --strict (93) + full pytest
  (not network) green; **ARTIFACT-PASS** green on the re-assembled MVST artifact. Commits: code + artifacts
  SEPARATE (never bundle code into an artifact commit).
- **OPERATOR TO-DOs (this build):**
  1. **Re-assemble the other 9 committed dossiers** (AORT, BRBR, CNXC, EPAM, FUBO, IT, SMPL, VITL, VRRM) —
     only MVST carries the new fields today; the standing artifact pass back-fills the cohort.
  2. **DEFERRED — Phase-2 stock-info panel** (price / 52-wk range / shares / book value). UNLOCK: EOD is
     thin for MVST specifically; build when a finalist has a full EOD history to render.
  3. **DEFERRED — Phase-3 dependency-free SVG charts** (P/E own-history band, ROIC trend, rev/EBITDA
     trend). UNLOCK: after the Brief structure is human-reviewed on #98 (don't build charts onto a layout
     that may still change in review).
  4. **OPS — token file REFRESHED (2026-07-09).** The old `~/.mosaic_gh_token` had gone stale (401); the
     user supplied a new repo-scoped token, written + verified (GET /user → 200). (The push + PR had used
     the osxkeychain-cached credential as the fallback.)
- **AUDIT (2026-07-09, post-open) — #98 audited against code; 4 MINOR defects fixed, 0 blockers.** Two
  adversarial sub-agents (render.py + dossier.js) + empirical renders of all 10 committed dossiers and the
  live frontend (MVST full-field · IT/AORT missing-field). CLEAN: None-safety (the 9 non-re-assembled
  dossiers render — new fields fail-honest; the 7 that fail to LOAD do so on the PRE-EXISTING required
  `valuation.cross_sectional`, NOT a #98 regression), the machine-never-concludes guardrail, and md↔web
  parity. FIXED, each with a regression pin, suite green: (a) `render.py _brief_financials` num_cols
  off-by-one — the first period column left-aligned instead of right (e2e alignment pin); (b) `render.py
  _customer_concentration` dropped a disclosed `value_kind='floor'` ≥ qualifier (unit pin; latent — MVST
  customers are 'exact'); (c) `dossier.js` menu-chosen PDF scope (`ds-print-*`) was never cleared → a later
  native Cmd+P printed the wrong scope (now cleared on `afterprint`); (d) `dossier.js` per-render global
  click listener leaked one stale listener per navigation (now a once-registered module-scoped listener).
  key_ratios / B1 drawdown drivers / customer-concentration values re-verified against the real CIQ Ratios
  sheet + committed artifact; `dossier.md` re-rendered (deterministic — the one alignment line).
  Incident→invariant: (a)→alignment e2e pin, (b)→floor unit pin [both shipped]; (c)/(d) web-only, verified
  live in the preview (afterprint clears scope; menu opens/closes; no console errors on MVST/IT/AORT).
- **PHASE-2 STOCK-INFO PANEL — BUILT + VERIFIED on VRRM (added to #98, 2026-07-09).** The Motilal-style
  market-data box on the Brief teaser: CMP + 52-week range (EOD price features), shares outstanding
  (EDGAR XBRL), book value/share + market cap (CIQ) — each source-bound and fail-honest (a field with no
  source is omitted; all-UNKNOWN → no line). New `StockInfo` schema + `MechanicalLayer.stock_info`
  (default None → back-compat), `mechanical._stock_info` (wraps the EXISTING `compute_price_features` +
  `_edgar_shares_outstanding` + new `ciq_sheets.book_value_per_share`), rendered in md (`_stock_info_line`)
  + web (`stockInfoLine`, parity + a `.brief-stock` style). **EOD unblocked:** the `prices` table was
  EMPTY in this env (the committed dossiers' EOD reads predate it); pulled VRRM 2025-05-01..2026-07-08
  (297 bars, `POLYGON_API_KEY` from `.env`) via `vinci refresh`. **VERIFIED (real VRRM):** CMP $4.22
  (2026-07-08) · 52-wk $3.40–$25.73 · shares 151.9M · book value/sh $1.79 · mkt cap $668M — internally
  consistent (price × shares ≈ CIQ cap), a genuine distressed name (Verra Mobility, ~83% off its 52w
  high; the pipeline also fired a stale-CIQ-multiple caveat, correctly preferring the fresh EOD price).
  A full VRRM re-assembly landed it + the Brief fields (exchange Nasdaq, GICS). Pins: a frozen-fixture
  render pin (fail-honest) + a phrasing-independent e2e presence/citation pin on committed VRRM. ruff +
  mypy --strict + full pytest green; md↔web parity + no console errors verified in preview. **MVST stays
  EOD-thin** (no bars pulled) → its CMP/52wk render fail-honest UNKNOWN, correctly.
- **A4 + A3 render cleanups — SHIPPED (2026-07-09, feat/dossier-render-cleanup, stacked on #98).**
  **A4:** the `_TIER_KEYWORDS` space/hyphen miss is fixed — "going-concern" (hyphen) double-listed with
  "going concern" (space) in BOTH renderers (the codebase idiom, cf. net-debt/net debt), + a deterministic
  classifier pin (a bare hyphenated going-concern now lands Tier-1, not 'unclassified' at the bottom).
  MVST already sorted going-concern FIRST via other tier-1 keywords, so zero committed-artifact churn —
  the fix closes the latent recurrence. The `evidence_balance`-lean sort was intentionally NOT built (a
  debatable behavior change, not a bug; the Brief already leads with the lean). **A3:** de-jargoned the
  covenant labels ("Tier-2, fenced" → "from the filed agreement"; "governing; Tier-2 fenced" → "governing
  agreement") and "Revised guidance (catalyst 8-K Ex-99.1)" → "Revised guidance" (matching the already-clean
  JS), both renderers; MVST/VRRM `.md` re-rendered (deterministic — labels only). The `fenced Tier-2`
  **source_ref** is DATA (`covenant_extract.py`) → deferred to the B-phase re-assembly. ruff + mypy + full
  pytest green; web verified (no "Tier-2 fenced" on the surface, no console errors).
- **A2 ENDNOTES — SHIPPED both surfaces (2026-07-10, feat/dossier-endnotes, off main post-#98).** The
  plan under-estimated this ~4×: not 3 shared emitters but ~14 scattered cite sites in render.py + 11 in
  dossier.js (↳ sub-line, ↳ inline-header, bracketed `[\`ref\`]`, the stock-info line, `.cite` spans).
  Every inline citation is now a numbered `[n]` marker + a document-end **Sources** list. **md:** a
  thread-safe `_ENDNOTES` ContextVar registry (the assemble batch renders across threads) + `_cite` /
  `_cite_inline` helpers; ONE global list (linear doc). **web:** a PER-TIER design — each tab / PDF
  scope gets its OWN Sources list (a `[n]` on the Brief tab can't resolve into a hidden Analysis tab),
  via a `withEndnotes()` wrapper + a two-pass numberer (markers are monotonic in READING order even
  though cards pre-compute cites out of DOM order); `[n]` is a `<sup>` with a hover-tooltip of the ref.
  **VERIFIED:** md — every committed dossier renders with ZERO stray ↳, every [n] resolves, deduped,
  pinned by `test_endnotes_complete_on_every_committed_dossier` (the safety net — it caught stock-info);
  web — MVST/VRRM/AORT render with 0 `.cite` spans, 0 `↳`, 0 `[?]` placeholders, per-tier Sources
  (maxMark == source count), sequential first-occurrences, no console errors. MVST/VRRM `.md` re-rendered.
  ruff + mypy --strict + full pytest green.
- **B2 PER-PEER VALUATION — SHIPPED (2026-07-10, feat/dossier-peer-valuation, stacked on A2).** The
  per-peer grid gains the LTM valuation multiples that were the point of a per-peer comparison:
  **TEV/EBITDA · TEV/Rev · P/E**, joined from the CIQ Trading-Multiples sheet BY TICKER (cols 2/1/4) —
  the sheet `_comps_layout` already located but `peer_grid` dropped. `PeerRow` gains `tev_ebitda`/
  `tev_rev`/`pe` (strings, "NM" preserved, None when the sheet/row is absent — the read is OPTIONAL so
  the grid still builds without it). Grid re-ordered to lead with valuation and capped at **8 columns**
  for print (EBITDA growth dropped from the render, kept in JSON). Both renderers. **VERIFIED (real):**
  VRRM name TEV/EBITDA 4.7 / TEV/Rev 1.8 / P/E 5.4 vs peer-median 10.3 / 2.0 / 15.65 (the discount is
  now visible per-peer); MVST Samsung-SDI P/E "NM" preserved. Pins: a deterministic extraction pin
  (join + NM + median + fail-honest absence) + an e2e render-column pin on committed VRRM. VRRM
  re-assembled + frontend-mirrored; ruff + mypy + full pytest green; web grid verified in the preview
  (A2 endnotes intact, no console errors).
- **COHORT RE-ASSEMBLY (CIQ-only) — DONE (2026-07-10, feat/dossier-cohort, stacked on B2).** Re-assembled
  AORT/BRBR/CNXC/EPAM/FUBO/IT/SMPL/VITL (+ MVST for consistency) on the current pipeline. **FIXES the 7
  that failed to load** on the required `valuation.cross_sectional` (fresh assembly) and back-fills every
  field they lacked: sector/industry (CIQ-GICS)/exchange/business-desc, key ratios, B2 per-peer multiples,
  A2 endnotes in the .md. CIQ-only (no EOD pull), so EOD-dependent fields (price/52wk/drawdown/stock-info
  price) render fail-honest UNKNOWN — correct (the prices table holds no bars for these names; the
  operator can pull bars + re-assemble for full data later). All 10 committed dossiers now load + render;
  frontend mirror updated; full offline suite green (ARTIFACT-PASS — endnote-completeness + B2 pins now
  exercise the whole cohort). MVST's fresh synthesis tripped a legitimate audit-tier QA flag (possible
  false-balance, 6 bull vs 10 bear + strong lean — a DIFFERENT check from the fixed `mixed`-label one;
  that regression test still passes) + a CIQ-freshness caveat — the guardrails working, not bugs.
- **REVIEW FOLLOW-UPS L1–L4 + /review FIXES — SHIPPED (2026-07-10, feat/dossier-review-followups #103,
  stacked on #102).** M1 (#102): `guide_verification` — a release stating NO numeric guide reads "not
  cross-checked", not a false MISMATCH (+ pin). L1–L4 (#103): peer-median self-computed (unified with the
  grid), tier-prefixed web endnote markers ([B/A/X n]), print-safe inline audit cites, robust endnote pin.
  Then a max-effort **/review** (10 finder angles) over the whole open stack found 11 issues, ALL fixed on
  #103: **#1** (my L1 re-derive REGRESSION) a reworded `cross_sectional.source_ref` split endnote dedup →
  TWO near-identical Sources rows (AORT/BRBR/CNXC) — reverted the ref to the exact string the synthesis
  copies (value fix stays); **#2** `_ratioC`(web, half-up) vs `_ratioc`(md, banker's) rendered a quarter-tie
  differently (MVST/VITL grid medians 3.2 vs 3.3 — LIVE, not latent) → both half-up via identical IEEE ops,
  matching the `_pctc` convention; **#3** `_ENDNOTES` ContextVar never reset → `@_endnote_scope` (finally);
  **#5/#8** "[LLM-suggested, unverified]" twin promoted to the web Sources list → twin/cohort sources render
  inline on BOTH renderers (never a Sources entry); **#7** the peer median duplicated `_med_mult` → one
  shared `_peer_col_median`; **#4/#6/#9/#10** test-quality. Code + artifacts in SEPARATE commits (511f798 /
  7956b4b); ruff + mypy --strict + full pytest green; preview parity confirmed (grid 3.3 == .md, 0
  "LLM-suggested" in any Sources list, twins inline, no [?] leaks, console clean).
  **Incident→invariant (shipped Y):** #3→fallback-after-render pin; #7→headline==grid pin; #4→orphan-Sources
  completeness pin (robust to a filing `[2024]`); #6/#9/#10→node-free static guard on dossier.js.
  **Residual (accepted):** #1 source_ref↔synthesis dedup + #2/#8 md↔web parity have no node-free behavioural
  pin here (node absent → the node-gated parity tests skip); covered when node is present.
- **PHASE-3 CHARTS 3a — BUILT + VERIFIED, PR OPEN (#104, feat/dossier-charts-3a off main, 2026-07-10).**
  The first financial-trend exhibit + the structured-series extraction it required (the parsers rule:
  the FinTable cells are DISPLAY STRINGS, so charting them would re-parse rendered strings). **Extractor:**
  `FinRow.values: list[float|None]` (the numeric behind each cell — 741.598 behind "742") on the raw
  rows, + `FinTable.is_estimate: list[bool]` (structural per-column consensus flag from the builder's
  `bases`); both default [] → pre-P3 round-trips; both close the "expose structured value(s)" gap the
  FinTable had (display-strings-only). **Render (web/PDF, dependency-free SVG):** `revEbitdaExhibit()` —
  Revenue + EBITDA bars ($M) + EBITDA-margin % line, dual axis, direct data labels, themed via CSS vars;
  consensus columns shaded + reduced-opacity + labelled "consensus (E)" + a source line "not a Nostra
  Vinci forecast" (machine-never-concludes, rendered). Fail-honest (no structured series → no chart, the
  table stays; AORT has no annual → no exhibit). **Tables:** denser dossier rows (9→5px) + forward-FY
  columns tinted (var(--conditional-bg)) across Brief + Appendix via the structural is_estimate.
  Artifact re-derive (9 dossiers): ZERO cell/note drift, NO .md change (values chart-only); code +
  artifacts SEPARATE commits (a297cc0 / 4d00838). ruff + mypy --strict + full pytest green; preview
  verified (exhibit renders, CSS vars resolve, estimate region + column tint, table intact, console clean).
- **PHASE-3 CHARTS 3b — BUILT + VERIFIED, PR OPEN (feat/dossier-charts-3b, stacked on #104, 2026-07-10).**
  The last two exhibits + their structured extractions. **P/E own-history BAND** (`ownHistoryExhibit`) — a
  bullet-style range bar per multiple (trailing low–median–high + current marker, LOG axis so a P/E blown
  out by a near-zero-EPS quarter still reads); fed by `OwnHistoryBand` + `valuation.own_history` via a
  shared `_own_history_band` that `range_position` now also uses (its string BYTE-IDENTICAL on all 10).
  **ROIC TREND** (`roicTrendExhibit`) — a per-period ROIC line (fraction ×100), zero-baseline for a
  distressed name; fed by `TrendPoint` + `quality.roic_trend` via a shared `_trajectory_series` that
  `_trajectory_row` now formats (trajectory string unchanged). Both series default None → pre-P3
  round-trips; both let the charts read STRUCTURED values, never re-parse a display string (the parsers
  rule the STATE note anticipated). Present on 9/10 (AORT CIQ-thin → fail-honest UNKNOWN). **Color audit
  (this build):** the directional marker follows the universal convention — ▼ below its own range = red,
  ▲ above = green, within = neutral accent (was an unintuitive amber; direction is a fact, the human
  judges cheap-vs-dear); estimate/forward columns → neutral grey (amber conflated with the app's
  "conditional" STATUS color); the rev/EBITDA margin line → neutral grey (amber conflated with "warning").
  Swept the other views — no status-color-on-data ambiguity elsewhere. Code + artifacts SEPARATE commits
  (844446d / 118aaf4). ruff + mypy --strict + full pytest green; no range_position/trajectory drift, .md
  unchanged; preview verified (both exhibits render, colors correct, console clean, charts match tables).
  **CHART-ROBUSTNESS PASS (post-review, JS-only):** the rev/EBITDA exhibit's fixed 0–50% right axis +
  positive-only left axis broke on real edge cases — MVST runs to −68% margin with NEGATIVE EBITDA bars,
  FUBO/MVST ROIC is all-negative, VITL EV/EBITDA spans 1.9→110x. Rebuilt as TWO PANELS (bars $M · margin
  %), each AUTO-SCALED to its own data with a zero baseline (no shared/clamped axis), + haloed labels so
  every figure is readable over the bars. ROIC chart already auto-scaled (verified all-negative FUBO);
  P/E band log axis verified on VITL's 58× range; haloed the ROIC labels too. Verified across MVST
  (neg)/VRRM (high)/FUBO (tiny)/VITL (extreme) — all render + match their tables, console clean.
  **Incident→invariant:** the range_position/trajectory byte-identical checks are the anti-drift pins
  (verified in the re-derive; a full-suite e2e pin would need node for the JS charts — accepted residual).
  **REMAINING (whole redesign): NONE — Phase-3 complete.** The dossier redesign (Brief 3-tier → A/B
  render passes → endnotes → peer valuation → cohort → primary-source → L1–L4 review fixes → Phase-3
  charts 3a+3b) is fully built; #99–#103 merged, #104 (3a) + 3b PR open for review.
  **EXHIBIT-PRIMITIVES REFACTOR — BUILT + VERIFIED, PR OPEN (refactor/exhibit-primitives, stacked on 3b,
  2026-07-10).** The 3 exhibits each re-derived their own axis/scale/domain/label math inline — the
  duplication where the axis-rounding (592→1000), phantom-zero-tick, and Math.min(...[])→Infinity bugs
  recurred. Extracted to `frontend/lib/exhibit.js` (pure ESM, node-testable): extent/nums guards, a FINE
  niceCeil, linScale/logScale, barDomain (bars span 0), lineDomain (pads beyond 0 only on a real side),
  labelAnchor/barLabelY. No-conclude guardrail encoded in the module header (DELIBERATELY no trendline/
  regression/extrapolation/projection primitive — a forward point may only come from a cited estimate
  series). revEbitda + ownHistory BYTE-IDENTICAL (rendered all 9 real dossiers before/after via node, diff
  clean); roicTrend changes ONLY its axis — same phantom-zero-tick bug the margin panel had, now floors at
  0 (VRRM −2%→0%) / caps at 0 (FUBO +2%→0%), every data label/point preserved.
  **Incident→invariant CLOSED:** the "a full-suite e2e pin would need node for the JS charts — accepted
  residual" above is now DISCHARGED — `test_exhibit_primitives_edge_cases_node` (node-gated) pins the
  primitive math, + `test_exhibit_module_static_contract_no_node` (node-free) pins the export + guardrail
  contract when node is absent. ruff + mypy --strict + pytest(not network) green; browser verified.
  **3-PR REVIEW-RESPONSE + ordered merge (2026-07-10):** a /review of the #104→#105→#106 stack (3
  parallel agents + adversarial re-verify) confirmed the rendering bugs self-heal within the stack
  (#104 negative-EBITDA exhibit → #105's auto-scaled rebuild; #105 roicTrend phantom tick → #106) and
  surfaced the DURABLE gaps, all fixed before merge: (1) EXTRACTION PINS for the parsers-rule structured
  feed that shipped untested — financial_summary_annual values/is_estimate (#104), own_history_bands +
  roic_trend positive+negative pins (#105); (2) CHART-vs-STRING confidence discipline (#105) — the
  own-history chart drew a confident red ▼ at ≥4 closes while range_position's string caveats below
  `_MIN_CONFIDENT_CLOSES=8`; ownHistoryExhibit now de-escalates below 8 closes (neutral marker + %ile* +
  footnote), coherence-test-pinned to the Python threshold (no drift); (3) #106 — an e2e roicTrend render
  pin (TEST-LAYER RULE: the primitive pin alone missed a wiring revert) + margin `minSpan` / roicTrend
  null-fallback robustness. Merged to main IN ORDER: #104 (5fd72d9) → #105 (df42f6e) → #106. Suite green
  at each gate. **Incident→invariant:** chart-out-confidents-string → a JS↔Python confidence-threshold
  coherence test SHIPPED.
  **RETURN-RATIOS EXHIBIT — BUILT + VERIFIED, PR OPEN (feat/return-ratios-exhibit, stacked on #109, 2026-07-11).**
  Replaced the latest-only "Key ratios (latest)" inline fact (Financial Snapshot) with a per-period line
  exhibit + a YoY ratios table (the Motilal Exhibit-10 pattern). The CIQ Ratios extractor already read a
  MULTI-column sheet but collapsed to the latest — a NEW `return_ratios(bundle)→Sourced[FinTable]`
  (`ciq_sheets.py`) surfaces the full per-period series (RoE/RoCE/RoA % carry structured `values` for the
  chart; total-debt/equity + current ratio + dividend are table-only), new `Mechanical.return_ratios`
  field, wired in `mechanical.py`. Web exhibit (`returnRatiosExhibit`, dossier.js) is TWO scale-grouped
  panels — RoE alone | RoCE + RoA — each on its own honest axis (a single shared axis crushed RoCE/RoA
  under Gartner/IT's distorted 270% RoE; user chose 2-panel). md parity = the YoY table via
  `_fin_table_lines` (no chart in markdown). **GUARDRAIL — actuals only:** the CIQ Estimates panel DOES
  carry forward RoE/RoA, but on a DIFFERENT basis (numbers don't reconcile with the Ratios actuals) and
  NO RoCE — splicing would be a layer-mix + false trend, so the exhibit is single-source actuals, no
  estimate shading, no extrapolation (no-conclude). Surgically re-derived the committed dossiers (no LLM):
  9/10 PRESENT (FUBO 5 periods — later IPO; **AORT UNKNOWN** — its CIQ Ratios sheet is malformed, so it
  keeps its prior no-ratios state, no regression). Verified in preview MVST (negative) + IT (distorted
  RoE) + BRBR (no RoE row → RoCE+RoA only). ruff + mypy --strict + pytest(not network) green (+4 pins:
  extractor frozen-fixture, e2e reconcile-vs-key_ratios + actuals-only, md table-replaces-fact, JS 2-panel
  static). Code + artifacts in separate commits.
  EXHIBIT-CONSISTENCY FOLLOW-UP (same PR): the return-ratios exhibit had invented its own canvas/fonts,
  so it didn't match the revenue/EBITDA exhibit beside it. (1) Rebuilt it on revEbitda's frame (760×276,
  cy0/cy1 band, 15/11.5/10.5/10 fonts, slot-centred x, per-point labels, bottom legend); single-panel
  (no-RoE, e.g. BRBR) renders at 430 wide, NOT stretched. (2) Extracted a shared **`EXHIBIT`** design-
  token constant (frozen: canvas/y-band/wSingle/wDual/font-scale/halo/margin) into `lib/exhibit.js`;
  **revEbitda + return-ratios both DESTRUCTURE it** (one source of truth — revEbitda output byte-identical,
  bar labels stay 9.5). (3) **Removed the ROIC-trend CHART** (Trajectory) — a strict duplicate of the
  return-ratios RoCE line (same data/source/periods); ROIC stays as a table row + the `roic_trend` series
  stays in JSON. Incident→invariant: a JS static pin asserts both exhibits reference `EXHIBIT` (no
  per-exhibit canvas literal remains); the phantom-negative-tick e2e moved onto the return-ratios exhibit
  (IT, all-positive). ruff + pytest(not network) green; revEbitda unchanged + return-ratios/roicTrend
  verified in preview. **Own-history NOT touched here** — PR #108 is independently rebuilding it into a
  line chart; its EXHIBIT-token adoption belongs in #108 (see §Next-steps).
  **DOSSIER-TOP REDESIGN — BUILT + VERIFIED, PR OPEN (feat/dossier-brief-header, 2026-07-11).** The
  header + Brief repeated facts (ticker·name in both the title and brief-idn; market cap in brief-meta
  AND stock-info; the no-verdict framing twice). SLIMMED the header to the title + ONE line
  (`Assembled facts, no verdict · data as of X · assembled Y · model`) — dropped queue rank, CIK, the
  verbose framing + parentheticals. Rebuilt the Brief teaser as a 2/3 NARRATIVE (business one-liner ·
  machine read · the human's Recommendation/Target slot) beside a 1/3 SNAPSHOT table (bold identity +
  exchange · CMP · market cap · 52-wk · shares · book/sh · CIK — the MOFSL stock-info standard),
  responsive→stacks <640px. CIK moved title→snapshot; GICS-industry dropped. Fail-honest: AORT omits
  the Book/sh row (no CIQ Book Value/Share). RENDER-ONLY (no data re-derive) + md↔web parity (render.py
  `_stock_info_line`→`_brief_snapshot`, doc header slimmed; .md regenerated). Verified MVST/AORT/VRRM
  in the browser (side-by-side desktop, stacked mobile); ruff + mypy --strict + pytest(not network)
  green (+3 pins: web no-dup static, md snapshot present/omit, VRRM e2e).
  FOLLOW-UP (same PR, code `fea169e` + .md `fdb3965`): dropped the teaser's own "Brief — first cut"
  title (dup of the active tab) and the "machine read · not a verdict" pill (dup of the header +
  footer framing). The machine READ now leads with its lean word — bold, Sentence-cased, tinted by
  DIRECTION (bearish→danger red, bullish→live green, mixed/neutral→grey) via `machineReadHtml` (web)
  / `_machine_read_md` (md, no tint). GUARDRAIL: still the machine's READ, not a verdict — the human's
  Buy/Avoid stays "not yet logged — the human's call" in the Recommendation slot directly below, and
  the header/footer keep the "no verdict" line; the tint encodes evidence sentiment, never BUY/AVOID.
  Verified MVST=red "Strongly-bearish", AORT=grey "Mixed"; 10 .md re-rendered (lean-line only, no JSON
  change); suite green (+1 pin: shared lean formatter, unit + phrasing-independent e2e sweep).
  **OWN-HISTORY LINE CHART — BUILT + VERIFIED, PR OPEN (feat/own-history-line, 2026-07-10).** Replaced
  the own-history range-BAR with the institutional "multiple band" — a TIME-SERIES LINE of each multiple
  over its trailing quarterly closes (the MOFSL/sell-side standard), lean form (mean/min/max reference
  levels, no SD), EV/EBITDA + P/E side-by-side (one wide panel when a name has only one), log-scaled
  (tames a P/E blown out by a near-zero-EPS quarter). Shows the PATH (de-rate/re-rate, cyclical
  position), not just the snapshot. Data = the SAME quarterly closes the band collapsed — exposed as a
  new structured `OwnHistoryBand.series` + `.mean` (shared _own_history_band, no drift). Honest-data
  note: ours is ~19 quarterly TRAILING closes / ~5y (7/9 names ≥8 closes → clean; MVST 4 = sparse; MVST/
  AORT EV-only), coarser than MOFSL's monthly-forward. Keeps the <8-close confidence de-escalation
  (grey current + footnote). Artifacts: own_history SURGICALLY re-derived (deterministic; synthesis +
  every other field byte-identical; NO LLM re-run). Verified VRRM (2 panels, de-rating below floor),
  MVST (sparse grey), AORT (confident red ▼); ruff + mypy --strict + pytest(not network) green.
  **Polish pass (review):** humanized the exhibit subtitle; a SINGLE-metric name keeps a normal panel
  width (W=430, not full-bleed 760 — full-bleed broke the familiar line aspect); +breathing room
  (margin 18/16). **Incident→invariant — inline exhibit source captions:** three exhibits (rev/EBITDA,
  own-history, ROIC) each grew an inline `Source: …` caption instead of citing via an endnote → SHIPPED
  a `>Source:`-scan guard (`test_exhibits_cite_via_endnotes_not_inline_source_caption`) + a CLAUDE.md
  rule (exhibits cite via endnotes → Sources list, never an inline caption; the sibling table/fact
  already cites the data). All three captions removed; sources now resolve in the Sources list.
  **BRIEF DECISION METRICS + STOCK-PERFORMANCE EXHIBIT — BUILT + VERIFIED, PR OPEN (feat/brief-decision-
  metrics, 2026-07-13).** Two folded changes. **(A · render-only)** moved the price-setup decision
  values INTO the Brief teaser as a 2×2 tile grid (price action 180d · idio vs mkt · net-debt/EBITDA ·
  FCF; going-concern when flagged), dropped the repetitive valuation-vs-peers line, and renamed the
  "The setup" card → **"Decisive question"** (question only — the drawdown prefix was already in the
  tiles). dossier.js + render.py + styles.css (`.brief-tiles` grid, capped 2×200px); md↔web parity.
  **(B · new exhibit + benchmark data)** a compact **52-week stock-performance** exhibit in the Brief
  snapshot column — the name vs the **IWM** benchmark, both **rebased to 100** at the window start
  (MOFSL sidebar standard), reusing the shared EXHIBIT design language (fs · halo · margin ·
  lineDomain-family math) at a sidebar size; index-domain via `extent` (NOT lineDomain's floor-at-0,
  which would waste the 0..min band); name in `--accent`, benchmark in `--ink-3`. Web-only SVG (md
  byte-identical). Required populating the benchmark: **IWM had NEVER been in the local prices DB**, so
  `market_180d_return` was UNKNOWN in every dossier and the idio `rel_vs_market` came from the screen's
  G2 data-record. NEW `PolygonEodClient.daily_bars` + pure `parse_aggregates` (per-symbol Polygon
  aggregates; Bearer-auth/cache/pacing reused) + committed backfill `scripts/fetch_benchmark_iwm.py`
  (546 IWM bars 2024-05-06..2026-07-10 under `IDX-IWM`; idempotent). NEW `StockPerformance`/`PerfPoint`
  schema + `MechanicalLayer.stock_performance` (default None → back-compat) + `mechanical._stock_
  performance(identity, store, ref)` (index-to-100, benchmark as-of-aligned to the name's trading days,
  weekly downsample ≤60 pts, **fail-loud None** when <2 window bars, a point's benchmark None when the
  index is absent — never bridged). Artifacts: the 10 dossiers' `stock_performance` SURGICALLY refreshed
  via `scripts/refresh_stock_performance.py` (recomputes ONLY that mechanical field through the real
  Dossier model — synthesis + every other field byte-identical, **NO LLM re-run**; +331 JSON lines each,
  0 removed, md unchanged). *Verified: IWM 180d = +17.0% (was UNKNOWN); CNXC −59% vs IWM +36% (52w),
  AORT −19% vs +36% — browser-confirmed both (domain adapts, legend fits); ruff + mypy --strict +
  pytest(not network) **571 green** (+9 pins: 3 parse_aggregates fail-loud/date-map, 3 extractor incl. 2
  fail-loud, static-contract, e2e renderDossier on committed CNXC, living-artifact invariants).*
  **Invariant:** the existing `>Source:`-scan guard now also covers the new exhibit (no inline caption).
  **LEAN SEGMENT/GEOGRAPHY CONCENTRATION — BUILT + VERIFIED, PR OPEN (feat/lean-segment-concentration,
  2026-07-13).** The Segments / Geography facts dropped tautological noise: a lone ~100% segment/geo
  ("X 9,826 (100%) of Total 9,826") collapses to "X — single segment/geography"; a real mix is %-only,
  largest share first (magnitude lives in the Financial Summary); the as-of period (was an inline
  "[12 months …]" prefix — noise no other fact carries) moves to the source_ref, so the citation/Sources
  tier keeps the vintage while the main body reads clean. `segment_ebitda` is exempt (`lean=False`) — its
  reconciliation needs the absolute per-segment values + pre-corporate sum + consolidated EBITDA. One
  formatter (`ciq_sheets._segment_section`); the noise was localized there (a full-dossier scan found
  the pattern in no other field). Collapse is guarded on share ≥99.5% (a lone segment at <100% = rest
  unlisted → shown as a share, not falsely "single"). Citations ([B1]/[B2]/…) preserved. Artifacts:
  `concentration` SURGICALLY re-derived via `scripts/refresh_concentration.py` (that field only; no LLM
  re-run; 9 names, AORT has no segment data). *Verified: real CIQ output (CNXC single, IT/VRRM %-mix,
  FUBO single-geo) + browser render; +1 test, 3 updated; ruff + mypy --strict + pytest(not network)
  572 green.*

**RC-1 primary-source text extraction — BUILT + VERIFIED, PR OPEN (feat/primary-source-text, 2026-07-06).**
DETERMINISTIC (anchored, never LLM) parsers of the EX-99.1 release (A, `vinci/edgar/release_parse.py`) and
the 10-Q/10-K sections (B, `vinci/edgar/filing_sections.py`), verified on the REAL cached filings, pinned on
committed public-domain EDGAR excerpts (CI-verifiable, no network).
- **C — consumers + wiring, BUILT + VERIFIED end-to-end on real EDGAR+CIQ for MVST & VRRM** (the survival
  CONTRAST PAIR): a resilient `_primary_source` assembly (`mechanical.py`) fetches the recent 8-K EX-99.1s +
  the latest 10-Q, parses them, runs FOUR cross-source derivations (`vinci/edgar/primary_source.py`), and
  attaches a `PrimarySource` to the mechanical layer — any fetch/parse miss → honest UNKNOWN + QA flag, never
  an abort. **MVST:** self-funding **MIXED** (two-input: latest-Q OCF<0 ∧ LTM FCF>0, superseding the committed
  one-input line); going-concern **SUBSTANTIAL DOUBT** leads; wall **AGREES** (panel same-window $109.6M CIQ
  principal, exclusive +12m boundary, vs filing $111.2M repayment; +$1.7M PIK); triangulation 3.9x/5.8x/**~18.7x**
  (LTM adj EBITDA $10.7M computed end-to-end = FY 44.7 − prior-Q 28.5 + Q1 −5.5)/covenant-UNKNOWN + 28.6/36.2%
  margins; guide **VENDOR-ECHO** (CIQ 427.516 ≈ release FY25 actual 427.5). **VRRM:** self-funding **YES**;
  going-concern **checked-absence**; guide cross-source **VERIFIED** (CIQ 985–995 vs release 985–995); NYCDOT
  15.2%; the Avis **event impact** (revenue −$135–145M, segment profit −$120–125M) renders in drawdown-cause.
  Render adds a `### Primary-source cross-checks` block; synthesis feeds a curated term→value→source_ref
  digest (VERBATIMS EXCLUDED) + three contradiction-lint subjects (event_impact_vs_key_unknown,
  going_concern_vs_survival_framing, filing_wall_vs_panel). Offline: LTM production-path pin + digest/lint/
  render pins; live paths network-marked. ruff + mypy --strict + pytest 498 (not network).
- **KNOWN LIMITATION (record):** deterministic coverage is PARTIAL beyond the pinned names — release/filing
  phrasing varies across the universe; every miss renders **fail-loud UNKNOWN** ('no anchored pattern
  matched'), never a guess. **QUEUED:** an *LLM-fenced escalation tier* for release/section parsing — built
  ONLY on coverage evidence from future finalists, never preemptively (adjudication 0).
- **IC-VRRM-6 disposition — RESOLVED BY EVIDENCE (not by build):** the VRRM Q1-26 10-Q confirms a LONG-DATED
  composition (Term Loan $685M / Senior Notes $350M / Amended Revolver $26M) with **NO ≤12m maturity wall**
  (parser state=`not_stated`, a known). The near-term-wall reconciliation concern was **MVST-class** (the
  $111.2M ≤12m + going-concern), not VRRM. VRRM concentration is **NYCDOT 15.2%/15.4% EXACT** (a single
  Government Solutions customer), not a bare >10% floor — extracted as the disclosed value.
- **RETRACTION (MVST wall — RC-1 checkpoint, 2026-07-06; figure corrected at build):** the earlier "filing
  understates the panel ~2×" claim is **WITHDRAWN** — a window mismatch + double-count. Like-for-like over the
  FILING window `[balance, balance+12m)` EXCLUSIVE (balance = the 10-Q's OWN period end 2026-03-31, threaded
  via `Filing.report_date` — a later 10-K's instant would shift the window and drop the $41.7M bond), the
  filing's **$111.2M ≤12m AGREES with the CIQ panel same-window PRINCIPAL $109.6M** (41.7 + 42.9 + 13.0 + 12.0;
  the $49.5M facility maturing AT +12m is excluded) within tolerance (1.4%). *(The interim "$111.3M" panel
  figure was ITSELF mixed-basis — it folded the filing's $26.7M convertible REPAYMENT into a CIQ-PRINCIPAL sum;
  the clean same-layer principal is $109.6M, and the convertible delta $25.0M→$26.7M is surfaced as +$1.7M
  accrued PIK, never forced to match. This is the DERIVED-PIN source-layer rule the incident earned.)* The
  filing **cross-validates** the panel; a divergence path fires only ≥ tolerance, with a ±7d-boundary
  safety-valve naming a possible window-convention artifact. Going-concern / OCF-mixed / concentration /
  adjusted-EBITDA-basis findings STAND.
- **IC DISPOSITIONS CLOSED BY RC-1 (evidence = the real-data derivations + render + lint, §5 gate run):**
  (a) MVST survival read materially DARKENS — self-funding **MIXED** (not the committed one-input
  "self-funding"), going-concern **SUBSTANTIAL DOUBT** stated, adjusted leverage **~18.7x** on the
  company-defined LTM EBITDA ($10.7M) — all rendered, source-bound. (b) VRRM materially CLEANS — **no**
  ≤12m wall (filing states none, a KNOWN), **no** going-concern doubt (checked-absence), guide
  cross-source **VERIFIED**, and the Avis impact is now **QUANTIFIED** (−$135–145M rev / −$120–125M
  seg-profit) — closing the prior "Avis not quantified" Key-Unknown gap: the digest feeds the number and
  the `event_impact_vs_key_unknown` lint makes a residual "not quantified" claim extinct (QA). (c) The
  MVST wall retraction is CLOSED with the corrected same-layer figure ($109.6M panel principal AGREES
  $111.2M filing). NYCDOT 15.2% exact STANDS.
- **MERGE-HYGIENE CONVENTION (recorded at the RC-1 merge):** a **linear isolation branch** (no
  sync-merge) → **rebase** onto main before merge (the #61 precedent — preserves clean SHAs). A branch
  that **carries a sync-merge** (like this one, which merged origin/main to resolve divergence) → **merge
  commit**, NOT rebase (a rebase would flatten the sync-merge and re-mint the verified SHAs), NOT squash
  (squash loses the isolated-commit bisect granularity the brief required).
- **INCIDENT (post-RC-1 IC-response draw) — TWO linked guard/test failures, both CLOSED** (PR
  "post-artifact guard + test robustness" — 2 isolated-green commits + docs).
  **(A) GUARD FALSE-POSITIVE — going_concern_vs_survival_framing proximity over-match.** The MVST draw
  tripped the survival contradiction lint with a SPURIOUS entry: `_SURVIVAL_SAFE_RE` had a bare
  proximity arm `going[- ]concern\b.{0,15}\bnot` matching ANY "not" within 15 chars of "going-concern"
  — including the benign gap-acknowledgment KU *"the specifics of the going-concern 'plans' are not
  synthesized here and must be read"*. **Fix:** dropped the arm; a genuine denial must NAME the thing
  denied (surviving arms: no/not-a going-concern · no substantial doubt · survival not-at/assured ·
  solvent). **Invariant:** `test_survival_lint_no_proximity_overmatch` (MUST-NOT-FIRE benign / MUST-FIRE
  5 denials / end-to-end). *(Coverage note: "going concern is not a concern" no longer caught — rare;
  accepted trade.)* Artifact `dc53455` ships that ONE documented-spurious qa CONTRADICTION in the MVST
  `dossier.json` dev/JSON channel ONLY — human surface unaffected; the next routine assembly clears it.
  **(B) RED-MAIN — LLM-string pin × artifact refresh (the red pin SWAPPED between the two re-assemblies).**
  Each post-RC-1 re-assembly left main's OFFLINE SUITE RED via a DIFFERENT LLM-composed covenant-string
  pin: at **3859ef9**, `test_t1_provenance` was RED — the principal re-rendered as "RMB [800,000,000.00]"
  so the exact "RMB 800,000,000" pin was absent (the interest clause was NOT yet reworded there;
  `test_t2` was GREEN). At **dc53455**, `test_t2_covenant` was RED — the re-assembly reworded the
  interest clause, dropping the exact composite lead "Term SOFR + 9.75% (Floor 3.00%, +3.75% PIK)" (by
  then the amount rendered "RMB 800,000,000.00 yuan", so `test_t1` was GREEN). Same failure class — an
  EXACT LLM-composed covenant string pinned against an artifact the LLM re-words/re-formats on every
  re-assembly — different pin each draw. **DUAL OWNERSHIP:** (1) the artifact-pass template lacked a
  full-suite gate — the render was verified but `pytest` was NOT, so both reds slipped in; (2) the
  original "pin the exact phrasing" test instruction seeded the brittle pins. **Fix:** BOTH covenant
  tests re-assert the T2 INTENT via deterministic anchors — `test_t2` (interest RATE via the machine
  floating_rate + conversion value-lead) and `test_t1` (amount → digits + accession, which had reddened
  at 3859ef9); a suite audit confirmed no other LLM-string covenant pins remain. **The fix PR was itself
  adversarially audited** (6 confirmed findings), which tightened it: the lint arm-drop was replaced by a
  predicate-keyed arm that recovers the genuine 'going-concern <predicate> is/does not <denial>' class it
  had over-dropped, and two `next()`/`.index()` crash-paths + a still-LLM-prose interest anchor in the
  covenant test were hardened. **BOTH RULES SHIPPED (CLAUDE.md):** TEST-LAYER (never pin an LLM-composed
  string — assert anchors; *facts stable, framing weather, and weather applies to CI*) + ARTIFACT-PASS
  (the standing artifact pass runs the FULL offline suite before pushing — not exempt from green-main).
  No artifact re-run — `dc53455`'s values are verified present and the human surface correct.
- **RC-1.5 RIDER (d) — covenant value-lead COMPOSED FROM STRUCTURE; the string-parser DELETED (the
  render-layer instance of the banned class, CLOSED).** `_labelled_rate` regex-parsed the LLM-composed
  interest clause — the render-layer instance of the "parsers consume structured values, never rendered
  strings" class (PR-6 + finding-B's class). **FIX (isolated commit / PR):** `CovenantTerm` gains FIVE
  OPTIONAL numeric components `{base_rate_label, margin_pct, margin_bps, floor_pct, pik_pct}` (NOT
  `Sourced` — they inherit the parent clause's citation), emitted by the Tier-2 extractor; they ride the
  `governing_terms` collapse onto `GoverningTerm` (the propagation crux — mirrored in `dossier.js`); then
  `render._compose_interest_lead` + `dossier.js composeInterestLead` compose the lead FROM those fields
  (py↔js byte-parity), and `_labelled_rate`/`_labelledRate` are deleted. **COMPONENT-CONSISTENCY GUARD**
  (a local figure-tracer): each numeric's digits must appear in the parent clause AND the two margin units
  are mutually exclusive — a mismatch OR both-margins ⇒ NO lead + a dev/audit-tier ⚠ QA note (a
  transcription slip must never headline the row). Units render **AS DISCLOSED** (bps stays bps — no
  normalization). Verified on real renders: pct composite `Term SOFR + 9.75% (Floor 3.00%, +3.75% PIK)`,
  the LIVE bps instrument `LPR + 115 bps`, the guard suppressing a slipped 9.75-vs-9.50 figure with the
  QA note.
  - **BACK-COMPAT:** the composed lead needs the new fields, so on **pre-RC-1.5d committed JSON (no
    components) the interest lead LAPSES to the raw clause** — verified MVST/VRRM render clean, the
    SOFR/LPR covenant rows carry the clause; the composed nicety returns on the operator's next
    re-assembly. No crash.
  - **FIXED-RATE = ACCEPTED RESIDUAL:** the 5 fields model base+margin (SOFR-pct / LPR-bps); a fixed-rate
    coupon has no base/margin → lapses to the raw clause (the instrument panel's coupon column carries the
    fixed rate). Extend with a `fixed_pct` field only on evidence, not speculatively.
  - **TRIAGE — severity correctly MINOR:** the complete-or-absent fence held and the #90-hardened `test_t2`
    covenant test guards the values via deterministic anchors; fixed for the CLASS (delete the string-parse)
    NOT the instance (regex widening — the D3 precedent caps that). Post-conversion the affected historical
    row is superseded (the live covenant surface is the syndicated facility).
  - **Invariants (INVARIANT RULE):** `test_rc15d_interest_lead_composed_from_structure` (compose + guard +
    propagation-through-collapse + back-compat) and `test_rc15d_interest_lead_py_js_parity` (node: lead AND
    qa byte-identical); `CovenantTerm` added to the no-conclusion schema-guard coverage set. TWO obsolete
    tests that pinned the deleted string-parser (`test_k1`'s interest asserts + the whole
    `test_t2_interest_lead_is_full_composite_or_absent`) are replaced by these structured pins — the brief's
    "test_k1 survives" was inaccurate for its interest block. GATE: ruff · mypy --strict (93 files) · pytest
    525 offline green · node parity.
  - **ADVERSARIAL AUDIT of the rider (5 CONFIRMED defects in the NEW code, all fixed before PR):**
    (1) `f"{v:.2f}"` vs JS `toFixed(2)` both MIS-ROUND an eighth-of-a-point coupon (`6.125%`→`6.12`) AND
    round oppositely (py half-even `6.12` vs JS half-up `6.13`) — a decision-surface fidelity slip + the
    H2 mirror-drift hazard; fixed by `_fmt_pct`/`fmtPct` (shortest exact decimal, pad ≥2, byte-identical),
    pinned by eighth (`9.125`) + `0.125` fixtures. (2) `_fmt_bps` CRASHED on a non-finite component
    (`int(nan)`→ValueError) aborting the whole render; (3) `_opt_float(True)==1.0` FABRICATED a `+1.00%`
    coupon; (4/5) `_opt_str` str()-ified a wrong-shape list into a garbage lead — fixed at the ROOT by
    tightening `_opt_float` (bool + `math.isfinite` gates) / `_opt_str` (isinstance gate) to fail-soft,
    pinned by `test_rc15d_optional_field_coercion_rejects_wrong_shapes`. (2) ALSO earned a compose-level
    DEFENCE-IN-DEPTH (merge gate G2b): `_compose_interest_lead`/`composeInterestLead` treat a non-finite
    component that reaches them directly as guard-suppressed → no lead + a byte-identical QA note, never
    the crashing `int()` — pinned py+node by `test_rc15d_non_finite_component_suppressed_no_crash_py_js`.
    **ACCEPTED-LATENT (PLAUSIBLE, not reached):** `_fmt_bps` else-branch `str(v)` vs JS `String(v)` diverge
    only at exponential magnitudes (`1e-7`/`1e21` bps) — impossible for a real covenant rate, and the
    finite gate removes the inf case.
- **INCIDENT (artifact-pass, post-#92) — TEST-LAYER class recurred across passes, both CLOSED; the p6
  pin was an LLM-string pin IN DISGUISE.** The standing artifact pass (re-assemble MVST+VRRM → suite →
  commit) reddened on a fresh draw TWICE: (1) `test_t2`'s conversion sub-assertion pinned LLM-reworded
  literals (`$0.50/sh`/`2 sh`/`$1.00`) — the draw restructured the clause to "$1.00 divided by …
  Conversion Rate: two (2) shares" so `_derive_conversion` correctly returned "" → fixed in **PR #94**
  (guard-conditional re-derive + an assertion-level sweep). (2) `test_p6`'s `_point_tier(claim)==1.0` —
  the draw phrased the GAAP-artifact recon "adjusted result was a loss" (Tier-3) vs the earlier "adjusted
  EBITDA of NEGATIVE $X" (Tier-1); a **classifier result on LLM text** is a disguised LLM-string pin the
  literal-token sweep MISSED → fixed in **PR fix/p6-invariant-relayer** (invariant-only e2e: monotonic
  non-decreasing tiers on BOTH committed dossiers, py==JS `orderPoints` mirror, + a cited EX-99.1-recon
  bear point EXISTS — no tier pinned). **DUAL OWNERSHIP:** (i) SPEC side — the sweep criterion (operator
  prompt + #94) enumerated LITERAL-token forms, so a classifier/derivation-on-LLM-text pin slipped the
  net; broadened now to "*truth depends on LLM text through ANY function*". (ii) INTERNAL-CONSISTENCY
  side — the p6 pin (this specific claim IS Tier-1) contradicted the recorded stop-chasing / accepted-
  residual adjudication (don't chase LLM phrasing; assert anchors) — two internal artifacts in conflict,
  latent until a fresh draw exposed it. **INVARIANT (INVARIANT RULE):** `test_p6_ordered_points_monotonic_
  tiers_and_recon_present_e2e` + the CLAUDE.md TEST-LAYER sharpening (classifier/deriver/formatter-on-LLM
  = disguised pin; a LIVING-artifact e2e asserts phrasing-independent invariants only, value pins → frozen
  fixtures). **OPEN DESIGN QUESTION — QUEUED (§Next-steps), NOT built here:** should a "GAAP profit is a
  fair-value artifact, reconciled adjusted result = a loss" claim classify **Tier-1**? Today `_point_tier`
  catches "adjusted EBITDA NEGATIVE" (Tier-1) but not the vaguer "adjusted result was a loss" (Tier-3) — a
  FACE-VALIDITY call on bear-point PRIORITIZATION, deferred; the relayer makes the test phrasing-robust
  either way, so this is a quality question, not a CI blocker.
- **INCIDENT (HOTFIX) — live dossier view DOWN, import/const name collision from the #92 audit fix;
  CLOSED.** The deployed dashboard's dossier view threw `SyntaxError: Identifier 'fmtPct' has already
  been declared` — the whole ES module failed to load. Root cause: #92's eighth-coupon rounding fix
  added a LOCAL `function fmtPct` to `views/shared/dossier.js`, which already `import`s a DIFFERENT
  `fmtPct` (the SIGNED-% display formatter) from `lib/format.js` — two bindings, one module scope.
  **FIX:** renamed the #92 formatter to `fmtPctExact` (+ its 3 covenant-composer call sites); the
  import + its display call sites untouched; two names, two semantics (exact coupon repr vs signed-%
  display), never merged. Python `_fmt_pct` unchanged (parity compares outputs, not names). **GATE GAP
  — SPEC-SIDE OWNERSHIP:** #92's validation was FUNCTION-LEVEL parity — the node tests extract a SLICE
  of `dossier.js` and run it in isolation, so they never loaded the module with its top-of-file
  `import`; and `node --check` parses in script mode and does NOT flag the import/declaration dup
  (verified: `node --check` exits 0 on the broken file). Function-level parity is not load-level
  integrity. **INVARIANT (INVARIANT RULE):** `test_frontend_modules_load_as_esm_and_render_smoke` —
  node dynamically imports EVERY frontend module (lib/ + views/) asserting no throw (browser globals
  Proxy-stubbed), renders the committed MVST dossier via the now-exported `renderDossier` asserting the
  composed `LPR + 115 bps` lead is present, and PINS the failure shape (a fixture module with an
  import+const collision MUST fail the smoke). No artifact change — the data was correct; only the
  view module failed to load.

The **dossier-assembler is built and verified (§2)** — the queue-top now flows ranker → `dossier`.
Remaining:
