---
id: 
status: shipped
date: 2026-06-22
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md governance log
---

2. **Lightweight local frontend — DONE (2026-06-22, §2).** The read-only ops dashboard is built and
   **merged to main code-only** (PR #3); it runs locally against local data (renders committed
   snapshots; never trades or logs via UI). **The DERIVED artifacts are now committed** to the private
   repo — `dossier.json` (PR #22) + `graph_coverage.json` (PR #24, 2026-06-26), **BLOCKER B verified
   CIQ-free**. **The authed deploy is now LIVE at `mosaic-theory.pages.dev`** — the FAIL-CLOSED Basic
   Auth gate (`functions/_middleware.js`, no Zero Trust / no card) was merged to `main` (PR #25), the
   `BASIC_AUTH_*` secrets set in the dashboard, and **BLOCKER A PASSED** (unauthenticated → 401, correct
   credential → 200). §4 CONDITIONAL satisfied; the §2 entry carries the full detail + the weak-test-
   password hygiene follow-up. **Dossier assembly stamp (2026-07-03): `assembled_at` is now UTC-aware
   (`datetime.now(UTC)`) and rendered WITH a time + "UTC" (md `_fmt_assembled` + web `fmtStamp`) — so
   two same-day re-assemblies are distinguishable and the timestamp is machine-comparable; a legacy
   naive JSON stamp is honestly labeled "(local)" until the operator re-assembles.**

The ranker + dossier-assembler are built/verified (§2); the ranker's coverage-gap wire-ups
(EV/EBITDA-pctile + 8-K/guidance text, which also re-splits drawdown-character and turns on the live
Tier-3 LLM pass) are parked in §4 — **monitored in use, not chased**.

Then: operate the weekly loop and accumulate resolved verdicts.

In PARALLEL (per §4's GOVERNOR, not instead): a validation design may be drafted for the next edge —
event-assembly's obvious/non-obvious verdict tagging, theme-anticipation's naive-baseline benchmark —
so long as it never diverts verdict throughput from the lead loop. Design first; build on greenlight.

**Earliness-assay v0 — OPERATOR ACTION (from the feat/theme-assay build):** the FALSIFY-OR-SURVIVE
retrocast RAN 2026-07-06 → **INCONCLUSIVE (price axis gapped)**: the harness SURVIVES (not falsified),
but cannot yet confirm the earliness premise because the pre-re-rate (EARLY-expected) windows for both
themes fall BEFORE Polygon's ~5y price history. **The kill criterion is NOT triggered — the assay
build does NOT stop.** The unlock to a CONCLUSIVE re-run is **deeper EOD price history (back to ~2016)**
for the 2022/2023 8-quarter baselines; only then is a PASS/FALSIFIED evaluable. v1 scope (a fresh
brief — do NOT auto-build): 8-K $-commitment extraction + an attention/search prior + a *weighted*
form-family split, AND the deeper price history. Op note: the retrocast fails LOUD on transient efts
500s under load — re-run cache-first (idempotent) to resume; it completed on that recovery.
**— UPDATE (2026-07-06):** the operator upgraded Polygon (EOD → 2018); the deeper-history re-run
resolved the price gap and the verdict is now **PASS** — defense-demand-shift had a ≥2q EARLY run
(all 4 combos) before its 2022 re-rate. **The kill criterion is NOT triggered — the harness SURVIVES
on evidence.** The price-history blocker is lifted; v1 (8-K $-commitment + attention prior + weighted
form-family split) remains a fresh brief, NOT auto-built. Full detail in the §2 addendum.
**— UPDATE (2026-07-07, v1 velocity-hardening built on `feat/assay-v1`, PR NOT merged):** side-by-side
verdicts AGREE (RECORDED PASS, ANCHORED PASS). **TWO OPERATOR DECISIONS now pending:** (1) SANCTION or
reject the calendar-anchored new-filer definition (it removes window burn-in and LENGTHENS the EARLY
runs — adopt only if that strengthening is judged real, not artifact); (2) confront the CONTROL-SAYS-NO
finding — the placebo ratio ~1 (not rising) + generic-term decomposition show defense's 2021 velocity
rise is substantially a LISTING-WAVE artifact, not theme-specific. Before any live candidate, decide
whether the velocity axis needs a listing-wave/de-registrant-flow control (a v2 brief) — the recorded
PASS is robust to the symmetric band but its velocity signal is confounded. Full detail: §2 v1 entry.

**Deferred audit follow-ups (PR #70 audit, 2026-07-03) — reported, not fixed under audit:**
- **X-2 (covenant governing-term collapse):** two DISTINCT debt facilities that share a family label
  (mechanical.py `_covenant_pointers` derives the family from `description.split(' With ')[0]` + adds
  up to 2 efts hits per family) collapse in `governing_terms` — the later masks the earlier and a
  false base→amendment is implied. X-4 removed the false-amendment SYMPTOM; the MASKING needs a
  per-facility identity in the pointer key (upstream, needs its own PR + real-run validation — risky
  to refactor mid-audit). Latent (MVST's families are genuinely distinct-or-amendment).
- **X-3 (maturity multi-8K):** `extract_maturity_event` reads only the FIRST of possibly-several
  maturity 8-Ks and pairs the first accession with the first `filed` date from independent scans of
  the `;`-joined string — a wrong/UNKNOWN event if the resolution is in a later 8-K or the ordering
  differs. Fix = parse the maturity string into structured `(acc, date)` and pick the resolution 8-K
  (design change). MVST (single resolution 8-K) is correct today.
- **X-5 (`_MAX_EXHIBITS=4`):** a 6th+ distinct debt family's primary exhibit is dropped — ACCEPTED
  cost bound; already loud-flagged ("exhibit not extracted (cost bound)"), so fail-loud, not silent.
- **D-3 (`_citRank` "made-up"):** `dossier.js` omits the Python `"made-up"` citation-rank clause —
  pre-existing (not PR #70 code) + currently UNREACHABLE (no source_ref ever contains "made-up"), so
  zero live impact; a 1-line JS parity add if/when a source_ref can carry that token.

**D3 tier classifier — paraphrase-chasing is CAPPED (accepted residual, PR #71/curation, 2026-07-04).**
The Tier-1 `_TIER_REGEX` now catches "(adjusted) EBITDA … negative", the survival-line "… turned
negative" cases, "cash-negative", AND (K6 FINAL widening) "adjusted EBITDA within ~40 chars of a
negative marker (`-$` / `(` / `negative`)". This is the LAST widening — a synthesis point that
GAAP-qualifies a negative-EBITDA artifact in yet another paraphrase and slips to Tier-2 is an ACCEPTED
residual, not a bug to chase; the point is already IN the doc (the tier only orders it), and endless
regex paraphrase-matching is lower-value than the human's read. Widen no further without a new,
repeatedly-observed shape.

**QUEUED (not the curation PR — that's render-only): exhibit-class filter BEFORE Tier-2 extraction
spend.** Exclude equity-comp / RSU award agreements at DISCOVERY (covenant-pointer stage), before the
fenced Tier-2 LLM extraction runs on them. Observed waste (MVST): the RSU exhibit
(`mvst20251231-ex1013.htm`, "Restricted Stock Unit Award Agreement") was located as a "material
contracts (10-K exhibit index)" pointer and fully extracted as a covenant doc — 7 UNKNOWN covenant
rows + 8 RSU-award rows, none survival-relevant (the curation now routes that whole family to the
appendix, but the extraction spend already happened). Filter the exhibit class up front so the LLM
never reads it. Extractor change → its own PR with real-run cost verification, not the render curation.

**Theme-viewer post-merge operator follow-ups (PR #74 audit, 2026-07-04):**
- **Theme freeze-regen (mechanical, operator-only).** The audit hand-corrected ONE deterministic value
  (`ai-datacenter.json` `cohorts.naive` 450→56) to match the fixed `build.py`. Re-run
  `build.py --themes-src data/forward` from the local (git-ignored) freeze to reproduce it from source and
  refresh anything else — cannot be done in a worktree (freeze absent). Mechanical (no LLM), so distinct
  from the dossier re-assembly, which stays operator-only for a different (fabrication-risk) reason.
- **`chain-layer-specific` tie-gate parity gap (`build.py._eff_basis`, reported not fixed).** build.py
  FULL-ranks the non-`DriverTie`-enum tie `chain-layer-specific`; the backend's `DriverTie(...)` parse
  fails → INDIRECT fallback → caps at committed. HARMLESS today (all 16 ai-datacenter names are grade-2 →
  `committed` under either rule) but UNPINNED (the parity test `test_tie_gate_matches_backend` iterates
  enum members only, never this raw string). Resolve deliberately: (a) promote it to a real `DriverTie`
  enum member + backend rank if it is a deliberate full-rank tie, or (b) let it fall to the backend's
  INDIRECT cap — then pin whichever with a parity case. Author's call (you wrote both the ledger tie and
  the build.py full-rank).

**THE 2026-07-28 SMPL AUDIT IS NOW FULLY DISPOSITIONED (2026-08-03).** The tail §C did not cover —
§C's three retractions, §D's methodological item, four of §G's seven — is rendered in
`docs/audits/2026-07-28-smpl/disposition.md` **§F**, measured against the page as re-assembled
2026-08-03. Two structural results from the pass itself:
**(1) §C's R2 is NOT a separate item — it forwards to §D's note, and its pointer "(P10-adjacent)" names
a defect that does not exist** (the report has P1–P9). Counting R2's residue and §D's note separately
double-counts one finding.
**(2) The twin item RE-OPENED ITSELF during the disposition.** §C had reasoned it stale because neither
unverified name was in SMPL's twin set any more, and predicted the mechanism; the 2026-08-03
re-assembly put **`e.l.f. Beauty` — one of the two — straight back in**, while `Utz Brands` silently
left. Nothing about SMPL changed. And it fails the other way too: the audit INDEPENDENTLY VERIFIED
Medifast's terminal outcome, and the page still prints `Medifast — went terminal (LLM-claimed —
verify)`. **Verification has nowhere to live, so it is re-requested on every assembly.**

**§D RULED 2026-08-04 — OPERATOR ACTION, NO NUMBER MOVES.**
> **The base margin is stated as an ANCHOR PLUS A NAMED ADJUSTMENT, never as an average.**

Anchor: **15.4481%** — the repo-computed 8-FY median, the one candidate that ASSERTS its basis in a
field. The current **14.0%** is a **1.45pp haircut**: state it with its reason and the number stays.
**The anchor choice is nearly free** — 15.4481% against ref[1]'s 15.51% is **0.06pp**, and this pass
showed ref[1]'s *"(FY2025 adjusted)"* qualifier moves its median by **0.0000pp**. **The haircut is
the entire analytical content, and it is the analyst's to state.** Apply via `scenario-supersede`
once the analyst gives the text. **No shown run — nothing moves**, so this is not the decision-path
change that re-striking would have been.

**THE THREE RULINGS WERE GIVEN 2026-08-04. Recorded here as the decisions of record; the pending
statements below are kept for the reasoning that produced them.**
**THE COHORT-PARTNER READ — 2026-08-04, full render in `docs/audits/2026-08-04-cohort-partner-read.md`.
REPORT ONLY; no assembly, no build, no name recommended.**
**COHORT DECIDED 2026-08-04: SMPL + BRBR.**

**SUPERSEDED GUIDANCE IS NOW MARKED IN THE BRIEF (2026-08-04). P2 CAME BACK THROUGH THE BRIEF, NOT
THE EXTRACTOR.** #254 fixed the extractor and the mechanical layer was right the whole time — the
record's base method cites *"management's reinstated $1.345–1.355B guide"* and `current_guide` names
the July 8-K. **Nothing carried that into the digest.** `_primary_source_digest` emitted every
release's guidance as `guidance (metric period): low–high → source_ref` with **NO DATE AND NO
ORDER**, so July's `net sales 2026: 1,345–1,355` sat beside April's `1,310–1,350` as equals and the
synthesis argued the FY26 guide from April. **Five releases, two guidance statements, no ordering
signal.**
**FIXED BY MARKING, NOT DROPPING** — the guidance history IS a bear point (SMPL's three-step cut
sequence), so superseded releases stay and merely stop looking current. **Dates only, no heuristic,
no ranking:** the latest guidance-bearing `filed` is CURRENT, earlier ones are
*SUPERSEDED (filed X; replaced by the guide filed Y) — history, NOT the company's current outlook*.
**Computed over ALL releases, not the four the digest shows**, so a fifth carrying the newest guide
cannot leave a stale one marked current.
**UNORDERABLE IS LABELLED, NOT GUESSED:** MVST's and FUBO's guidance releases carry no `filed` date,
so they render *VINTAGE UNDATED … do not read it as current* rather than being assumed either way.
**REPORT 1 — 9 OF 11 NAMES CARRY MORE THAN ONE GUIDANCE-BEARING RELEASE, and SMPL's two is the LOW
end.** NCNO **5** · AORT, CNXC, VRRM **4** · EPAM, VITL **3** · BRBR, MVST, SMPL **2** · FUBO 1 ·
IT 0. **Fleet-wide, and the names most exposed were never the one that failed.** Measured as
same-(metric, period) collisions inside the shown window: **15 colliding guidance keys across 8
names** — VRRM alone has 5, with `adjusted ebitda next-fy` appearing **four times**.
**REPORT 2 — GUIDANCE IS NOT THE ONLY UNORDERED-VERSION CASE. NAMED, NOT FIXED.** The same release
loop emits four kinds with the same undated shape, and **`reconciliation` collides too: 4 keys
across 2 names** (MVST 3 — `adjusted net income`/`adjusted eps`/`adjusted ebitda` for 2024 each
appearing **three times** — and FUBO 1). `event_impacts` shows **zero** collisions today; `one_offs`
are description-keyed and were not measured on the same key. **So the fix is bounded but not
complete**, and the residue is recorded rather than swept in.
**AND THE FIRST CUT OF THIS FIX SHIPPED A WORSE DEFECT THAN THE ONE IT CLOSED — caught in review.**
The mark began as a per-release SECTION HEADER, `--- SUPERSEDED … history, NOT the company's current
outlook ---`, which **visually scoped over everything beneath it**. On SMPL that was April's guidance
(correct) **plus the Q2, Q1 and FY2025 REPORTED ACTUALS and the $60.9M Atkins impairment** — facts,
none superseded, and **the impairment is the very figure 19c FORCES the synthesis to cite.** It also
**bled into the next guidance-less release**, which emits no header of its own. **A header telling
the model that reported actuals are stale history is a larger error than the unordered guidance it
replaced.** Fixed by marking the LINE, not the block: a per-line mark has no scope to creep and
nothing to bleed into, and reconciliations, one-offs and event impacts now carry no vintage mark at
all — pinned.
4 mutations CAUGHT (mark dropped · undated assumed current · supersession keyed off the window ·
the mark moved back onto a block header).
**The third needed a SYNTHETIC pin and the reason is recorded in the test:** on today's corpus every
name's newest guidance release already falls inside `releases[:4]`, so the corpus provably cannot
drive that property — and nothing asserts `releases` arrives newest-first.

**TWO LIVE FALSE CLAIMS ON SMPL'S COMMITTED PAGE (2026-08-04). RECORDED, NOT REROLLED — a reroll to
fix two sentences would risk the twelve recovered brand-level citations.**
Five verdict-bearing synthesis points were checked figure-by-figure against the Q3 transcript and
the results 8-Ks. **Three verify exactly; two are wrong; BOTH WRONG ONES ARE BEAR POINTS AND BOTH
OVERSTATE THE BEAR.**
· **bear[1] ✓** — Atkins net sales −24.6%, retail takeaway −23.9% vs −23.4% prior, household
  penetration 8.5% down 220bps. All four verbatim, and the subject is Atkins throughout.
· **bull[4] ✓** — Quest household penetration +120bps to 20.5%, net sales +1.1%. Both verbatim,
  subject is Quest.
· **bull[7] ✓** — adj EBITDA $57.0M cites 8-K `-000021` (July) and matches its reconciliation block;
  the transcript's $57.2M is the same figure unrounded. Both are the company's own.
· **bear[6] ✗ WRONG SUBJECT.** It reads *"a mid-teens price increase is being forced"*. The
  transcript says **high-single-digit FOUR TIMES** about the September action; **"mid-teens" occurs
  ONCE and is the CHIPS BRAND'S GROWTH RATE** (*"a $0.5 billion brand… growing in the mid-teens"*).
  A real number attached to the wrong subject — and bull[6] states the correct figure, so the page
  contradicts itself.
· **bear[3] ✗ WRONG VINTAGE — THIS IS AUDIT DEFECT P2, STILL LIVE.** It states the FY26 guide as
  *net sales −10% to −7%, adj EBITDA −22% to −19%, gross margin −300–350bps* and cites 8-K
  **`-000010`, the APRIL (Q2) filing**. The **CURRENT** guide from the Q3 call and 8-K `-000021` is
  **net sales −7% to −6%, adj EBITDA −21% to −19%, gross margin ROUGHLY −375bps.** All three
  figures are superseded. **And bull[7] cites `-000021` while bear[3] cites `-000010`, so ONE
  SYNTHESIS ARGUES FROM TWO GUIDANCE VINTAGES** — precisely what the 2026-07-28 audit recorded as
  P2, unfixed and now inside the points a verdict is being formed on.
**THE DIRECTION, STATED PRECISELY — and my first cut overstated it.** I wrote *"both defects make
the bear look worse"* and then, one clause later, noted bear[3] understating the margin cut. That is
a contradiction inside one sentence: a headline generalising over a MIXED result.
**bear[6] is unambiguous** — it roughly triples the price action, so the bear reads harsher.
**bear[3] is wrong in BOTH directions**, figure by figure: net sales −10% to −7% against an actual
−7% to −6% is **deeper across the range** (harsher); adj EBITDA −22% to −19% against −21% to −19% is
**1pp deeper at the floor, identical at the ceiling** (marginally harsher); gross margin 300–350bps
against roughly 375bps is **25–75bps SHALLOWER** (softer). **Two figures overstate the bear, one
understates it.**
**So the honest claim is not a direction but a vintage: bear[3] is not biased, it is STALE** — every
figure is April's, and a superseded guide is wrong in whatever direction the update happened to
move. A reader forming a verdict from this page is reading numbers the company has since replaced.
**AND THE STRUCTURAL POINT: bear[6] surfaced ONLY because it contradicted bull[6].** A wrong point
with no internal contradiction would not have surfaced at all — **driver rows carry
quote-in-transcript and digit-trace validation; synthesis points carry NEITHER.** That asymmetry is
why this check had to be manual, and it is unclosed.

**THE DIGEST'S CAP WAS ON THE WRONG AXIS — IT DROPPED THE GUIDE HISTORY IT EXISTS TO PRESERVE
(2026-08-12, fix/brief-template-guidance-parity).** Found while re-assembling BRBR/SMPL: the fresh
artifacts reddened `test_the_analyst_template_shows_the_same_vintages_as_the_brief`, and the
diagnosis was not the surfaces but the window. `_primary_source_digest` capped the RAW release list
(`ps.releases[:4]`), so a release carrying NO guidance could hold a slot while a guidance-bearing
one fell outside it. **Measured on the committed fleet: AORT −1, CNXC −1, NCNO −2 guidance-bearing
releases dropped** — and the note said only *"older release(s) omitted"*, never that any of them
carried a guide. The block's own comment is **"MARK, NEVER DROP … the guidance history IS a bear
point — SMPL's three-step cut sequence is evidence"**, so the cap was deleting the very evidence the
vintage marking (the P2 fix above) was built to keep, and a bear case resting on a cut sequence
could lose it silently. **FIX: two windows.** The CONTENT window stays at 4 (reconciliation,
one-offs, event impacts are LTM-shaped — widening them would just add tokens); GUIDANCE selects the
4 most recent releases that actually carry some. They usually coincide; where they do not, this is
the difference between showing a cut sequence and implying there wasn't one. The note now also says
how many omitted releases carried guidance.
**AND THE TEST'S INVARIANT WAS WRONG, not merely stale.** It asserted the template and the brief show
the SAME vintages — true only while no name had >4 guidance-bearing releases, and broken by richer
extraction rather than by a defect. The brief caps BY DESIGN and discloses it; the template is the
analyst surface and carries the full history. Asserting equality would force one of those deliberate
choices to give way. Replaced with what the old message was reaching for — **ONE DERIVATION**: the
brief's vintages are a SUBSET of the template's, the CURRENT/SUPERSEDED mark AGREES on every shared
vintage (a guide current on one surface and superseded on the other is P2 in a new place), and any
omission is DISCLOSED. The sibling P2 pin was likewise re-pointed at the oldest guidance-bearing
release **inside the window**, which keeps its coverage exactly.
*3 pins: the fleet cap-axis pin FAILS on the pre-fix digest naming exactly `AORT, CNXC, NCNO` and
passes after; the two corrected invariants hold on both. ruff + mypy --strict (124) + pytest 2409
green. **No artifact moved** — the digest is an LLM INPUT, not a stored field, so this changes what
the next assembly reads, not any committed page.*

**`scenario-create` NOW REFUSES A NAME THAT ALREADY HAS A RECORD.** `write_record` is an
unconditional `path.write_text`, so a create on SMPL would have DESTROYED the live record and
skipped archive-and-reissue — the supersession chain is unreconstructable once gone. **REFUSES
rather than routing** (a create that silently becomes a supersede is a surprise on a destructive
path, and `scenario-propose` emits a template that LOOKS like it feeds this command); the refusal
names `scenario-supersede` and states that its `--payload` is a COMPLETE record, not the template.
Both directions pinned.
**AND THE GUARDS ARE ON THE WRONG PATH — REPORTED, NOT FIXED.** `scenario-supersede` runs
**`ScenarioRecord.model_validate_json` and NOTHING ELSE** — no `validate_legs`, no `propose_anchors`,
no `check_tier_agreement`. **So a supersede can move a margin with no stated reason: §D is
reintroduced through the path the analyst actually uses**, while the anchor/deviation guards sit on
`scenario-create`, the path that by definition has no live record to fix. SMPL's pending action is a
supersede.
**RIDER SHIPPED: the template's margin trend is now labelled `**EBITDA basis**, NOT the EBIT margin
this leg asks for`** — the one EBITDA figure among an EBIT anchor, an EBIT raw series and an EBIT
leg, where D&A at ~2.7% of revenue makes 16% sit deceptively close to 15.4481%. The axis §D
happened on.

**THE CAP-REMOVAL TEST RAN ON SMPL AND THE PREDICTION HELD (2026-08-04).**
**BRBR WAS THE WRONG SUBJECT AND WAS STOPPED FIRST:** its dossier's own catalyst calendar put the
next results print at **2026-08-04 — the day of the test** (cadence: median 91d over 27 results
8-Ks, last print 2026-05-05), **confirmed by 8-K ITEM CODES rather than by date arithmetic** — the
2026-05-05 filing carries item **2.02** (Results of Operations) while the two since (06-24, 07-08)
carry 5.02/7.01/8.01 only. Re-assembling would have produced a dossier superseded within days, and
that print IS the named observation a watchlist verdict waits on.
**SMPL's TRANSCRIPT WAS VERIFIED CURRENT before starting** — the bundle holds
`Q3 2026 Earnings Call, Jul 09, 2026`, matching the latest results 8-K (2026-07-09, item 2.02).
**HELD CONSTANT: no EOD refresh.** Price frontier stayed **2026-07-29** through the run, so the cap
removal was the only variable and any difference is attributable.
**ROWS: 12 → 24 transcript rows recovered; capped-flags 12 → 0.**
**THE GAP DID NOT MOVE, exactly as it must:** `0.9839 / 0.9463 / 2.2589 / 2.1032`,
multiple-dominant, identical vintages. Nothing but the cap changed.
**THE PREDICTION — do the new points cite brand-level consumption/penetration the old ones did
not? — IS ANSWERED YES, and with the exact metrics the cap had removed:**
· BULL gained **Quest household penetration up 120bps YoY to 20.5%** and **Quest chips consumption
  +17%, milkshakes ~50%** — `Quest household penetration`, `Quest chips consumption` and
  `Quest milkshake segment consumption` were all DROPPED ROWS.
· BEAR gained **Atkins retail takeaway −23.9% vs −23.4% prior quarter** and **Atkins household
  penetration 8.5%, down 220bps**, plus **OWYN takeaway −1.3%** — `Atkins retail takeaway`,
  `Atkins total brand household penetration` and `OWYN retail takeaway` were all DROPPED ROWS.
Counts: bull 1→2 and bear 2→4 points citing brand-level consumption or penetration; totals 9→10
bull and 8→9 bear.
**BUT "NOT THINNER" WAS A COUNT, NOT A READING, AND THE REVIEW FOUND A REAL REGRESSION.** The OLD
bull carried the **FORWARD** peer comparison — *"on a forward basis SMPL trades below the peer median
on every line (**NTM TEV/EBITDA 5.65 vs 8.72; NTM P/E 6.12 vs 13.08**)"*. **All four NTM figures are
absent from the new synthesis**, whose bull[3] argues instead from the **TRAILING** 5.3x vs peer 7.8x.
**AND THE CAVEAT WENT WITH THEM:** the OLD bear[2] explicitly warned *"this is trailing-only with no
forward basis, so it cannot itself distinguish cheap-overshoot from cheap-terminal"* — neither
"trailing-only" nor "forward basis" appears anywhere in the new points. **So the new bull argues from
a trailing multiple that the old synthesis had specifically flagged as insufficient on its own.**
**THE DATA IS NOT LOST, ONLY THE CITATION IS:** NTM TEV/EBITDA 5.65 vs peer 8.72 still renders five
times in the valuation tables, so a reader can find it — but the ARGUMENT no longer rests on it.
Also dropped from the bull: OWYN's +3.6% growth (OWYN now appears only as a negative — losing
distribution, takeaway −1.3%).
**ATTRIBUTION IS NOT ESTABLISHED and both readings are live:** a larger brief may crowd valuation
detail out of a fixed output budget (which would make it cap-caused and connect to the unchecked
output bound), or it is ordinary reroll variance in emphasis. One roll cannot separate them.
**JUDGMENT: NOT REVERTED.** The six recovered brand-level citations are exactly what the fix was for
and they serve the decisive question directly; the loss is one argumentative leg whose data still
renders. **But the trade is real and is recorded as a trade, not as a clean win.**
**THE DECISIVE QUESTION SHARPENED** from *"…structural erosion (led by Atkins) that permanently
resets the earnings base"* to *"…structural erosion of the **Atkins/OWYN base that the growing Quest
engine cannot offset** (value trap)"* — the brand-level split now names which engine offsets which.
**19c NEVER REFUSED** (it accepted `~$392M of LTM asset writedowns` — scale-tolerant), and the run
converged on attempt 2 of 5.
**qa_flags 13 → 1**: the twelve cap flags are gone; the survivor is the pre-existing
*"no anchored pattern matched — EX-99.1 pricing/KPI"*. Four caveats, all carried over.

**ATTEMPT 1 FAILED, AND IT WAS NOT 19c — RECORDED BECAUSE MY OWN HARNESS MISLABELLED IT.**
The failure was *"synthesis tool returned incomplete output — missing required field(s)
['bear_points','twin_reference_cases','decisive_question','key_unknowns'] (likely truncated)"*, and
the assembler REFUSED TO WRITE rather than null a committed synthesis (the AORT-2026-07-30 guard
working). **My reroll harness printed "(19c refused)" for it** — it assumes every failure is the
material-figure guard. Same mislabel class as the rest of this session.
**CAUSE NOT ESTABLISHED, and the honest position is that one sample proves nothing:** the HARD
truncation guard (`llm.py:62`, `stop_reason == "max_tokens"`, `max_tokens=16384`) did **NOT** fire —
the message was synthesis.py's own inference from missing fields. Attempt 2 converged on the same
enlarged brief, so it did not repeat.
**AND A GAP IN MY OWN PRE-CHANGE CHECK, corrected:** asked whether the brief was bounded, I verified
the INPUT assembly (no cap on the `user` string, digest iterates all rows) and reported *"nothing
downstream absorbs the change"*. **I never checked the OUTPUT bound.** One exists — 16,384 tokens.
It is not implicated here on the evidence, but the check as I stated it was incomplete.

**THE TIER-B ROW CAP IS REMOVED (2026-08-04 ruling). EVERY EXTRACTED ROW NOW STAYS.**
No relevance ranking replaces it — none is derivable, at either stage, and inventing one was
forbidden. Takes effect **on the next assembly**: committed dossiers keep their capped rows until
re-assembled, so the fleet counts below are the state that clears.
**THE TWO PRE-CHANGE CHECKS, both measured before touching anything:**
**(a) THE BRIEF READS THE ROWS — TWICE.** They appear in the full `mech` dump (`facts` JSON,
155k–248k chars) **and** in a dedicated `_operating_drivers_digest` (2.9k–6.3k chars), which the
system prompt tells the model to GROUND every operating bull/bear point in. So the cap was starving
the synthesis, not only the page. Today the brief gets **16–30 rows** per name.
**(b) THE BRIEF IS NOT BOUNDED, so removing one cap triggers no other.** The digest iterates ALL
rows with only a 130-char per-VALUE truncation; the assembled `user` string has no cap and goes
straight to `llm.extract`. **Nothing downstream absorbs the change** — the failure I was told to
check for is absent.
**AND THE DELTA IS A ROUNDING ERROR.** Worst case is IT: **+4,592 chars on a 227,125-char facts
block, +2.0%.** Fleet average ~2.5k added chars. The cap was never buying anything measurable.
**SMPL IS THE STRONGEST CASE AND IS RECORDED AS SUCH:** its twelve dropped rows are EVERY
brand-level consumption and penetration metric — Quest retail takeaway, Quest household penetration,
Quest bar and chips consumption, Atkins retail takeaway, Atkins household penetration, OWYN both —
while **its kill criterion is stated on Quest revenue growth**, **its bear point cites Atkins'
falling household penetration**, and **its bull rests on Quest carrying growth**. **THE PAGE CITED
EVIDENCE THE CAP HAD REMOVED FROM THE ARTIFACT.** BRBR's case is the same shape one row wide:
`adjusted gross margin`, the number its own decisive question turns on.
**Fleet state that clears on re-assembly: 113 rows — IT 28, BRBR 17, VRRM 15, AORT 14, SMPL 12,
CNXC 9, FUBO 8, VITL 5, NCNO 4, EPAM 1, MVST 0.** The pin is INVERTED — `test_tier_b_rows_are_never_capped`
drives the real extractor with 20 valid rows and asserts 20 out, no `capped` flag, and that the
constant is gone. Mutation (silently restoring a `>= 12` bound): **CAUGHT**.

**PROSE-VS-COMPUTED RATIO DRIFT IS NOW GUARDED — SHIPPED GREEN, WITH SMPL ON A SELF-CLEARING
EXEMPTION.** `tests/test_rationale_ratio_drift.py`. A ratio stated in `verdict.rationale` must be one
the record computes (`result.ratio` / `ratio_at_entry`), the 2:1 bar excluded.
**THE ESCAPE IS COPIED FROM IT, NOT INVENTED.** IT cites `6.7:1`, `1.90:1` and `5.8:1` — all stale
against its computed 1.52 — and is CORRECT, because they sit in a DATED amendment chain on a closed
record (*"[amended 2026-07-22: position closed…]"*), each tagged to its moment. **The rule: an
UNDATED present-tense ratio must match; a DATED history need not.** IT is pinned as the passing case,
and the pin strips the date and asserts the same text then FAILS — so the guard cannot be keying on
anything but the dating.
**SMPL sits in `RATIONALE_RATIO_AWAITING_SUPERSEDE` with its reason**, on the
`ANCHORS_AWAITING_BACKFILL` exact-set shape: **main stays green, the guard binds on every other
name, and when the supersede lands SMPL stops diverging and the test REDDENS** — so STATE must be
updated rather than the exemption quietly rotting. A third pin refuses an exemption naming a name
that does not exist or no longer diverges. Mutation (guard stops detecting drift): **CAUGHT**.

**THE THESIS TEXT IS IN THE RECORD, NOT THE SYNTHESIS — SO A RE-ASSEMBLY WILL NOT FIX IT
(measured 2026-08-04). OPERATOR ACTION: it needs `scenario-supersede`.**
SMPL's *"Thesis — our rationale"* paragraph is `verdict.rationale` in `scenarios/SMPL.json` —
**sealed analyst text**. `dossier.json` carries **ZERO** occurrences of the string; the dossier
RENDERS it from the record at render time. **Guidance that it would self-correct on re-assembly was
wrong.**
**THE DRIFT, ON ONE PAGE, ELEVEN LINES APART:** `dossier.md:8` computes
**`Reward : risk 4.78 : 1`** while `:19` reads *"the grid reads **3.8 to 1** against our 2:1 bar"* —
**present tense, no amendment tag, no date.** 3.83 was the pre-item-24 ratio; the denominator swap
moved it to 4.78 and the prose did not follow.
**NOTHING GUARDS IT.** `moved_cited_claims` covers MATERIAL FINANCIAL-SUMMARY figures, not the
ratio; 19c demands material rows be stated, it never compares a cited ratio to the computed one;
`prose_lint` checks register and length only; no test pins prose-against-header agreement.
**BLAST RADIUS: ONE LIVE INSTANCE.** Swept all seven records for a prose ratio disagreeing with the
computed one. **IT is a FALSE POSITIVE** — its `6.7:1 / 1.90:1 / 5.8:1` are a DATED AMENDMENT CHAIN
in a closed record (*"[amended 2026-07-22: position closed…]"*), each ratio tagged to its moment,
which is a history and not a stale claim. **SMPL-2026-07-21 is the ARCHIVED record**, frozen by
design. **SMPL alone is live.**

**RENDER-TIER RELEVANCE: THERE IS NO CRITERION. THE ANSWER IS RENDER ALL ROWS.**
The ruling was to move the row cap to render, where the decisive question exists — and to render
everything if no criterion is derivable there either. **Measured: none is.**
**(1) NO USAGE LINKAGE EXISTS.** A synthesis point's `source_ref` is a FREE-TEXT SOURCE NAME
(*"CIQ Estimates→Trends (current vs 12m ago)"*), not a pointer to an `operating_drivers` row.
Nothing records which rows the synthesis actually used, so "rank by what the synthesis cited" is not
available.
**(2) THE ONLY REMAINING SIGNAL IS WORD OVERLAP — AND ITS ANSWER FLIPS ON AN UNRATIFIED CHOICE.**
*(CORRECTED ON SELF-REVIEW: the first cut claimed overlap FAILS on the motivating case and makes the
defect WORSE. That holds ONLY against the `question` string alone, and REVERSES once the window
widens — I measured the narrowest possible reading and generalised from it.)*
Against **`question` alone** (~300 chars, *"the collapse in **profitability**"*): `adjusted gross
margin` → **NONE**, while kept rows `wellness category growth` and `RTD shakes category growth`
overlap on `category`. Overlap would bury the decisive row.
Against the **WHOLE `decisive_question` block** (2,022 chars — question + evidence_for +
evidence_against, which is what a render-tier implementation would naturally read): `adjusted gross
margin` → **`adjusted`+`gross`+`margin`, a three-word full match and the strongest of any row**,
while the KEPT `market share` scores **ZERO**. Overlap would have SAVED it.
**THE SAME CRITERION, ON THE SAME NAME, GIVES OPPOSITE ANSWERS DEPENDING ON WHICH TEXT WINDOW IS
CHOSEN — AND NOBODY HAS RATIFIED THAT CHOICE. That is not a criterion, it is a knob**, and picking
its setting is exactly the heuristic-invention the brief forbids. The refutation does not survive;
the objection to it does, on stronger ground.
**CONCLUSION UNCHANGED, REASONING CORRECTED: keep every extracted row in `dossier.json` (which
DESIGN RULE v2 already requires) and render all of them.** Not because overlap was empirically
refuted — it was not — but because **no USAGE linkage exists** (1), and every text-similarity score
available instead depends on unratified scoping choices whose answers reverse. No score is invented
at render any more than at extraction.

**RECORDED FROM THE SMOKE TEST (labelled not-a-real-underwrite; bear and bull were arbitrary, this
combination was not):** BRBR's own anchor revenue **2,331.0** and anchor margin **16.0404%** with the
**peer LTM median multiple of 6.9x** gives a base of **$13.13 against a spot of $13.66**.
**A generous margin plus the peer multiple lands BELOW today's price** — the cleanest statement of
BellRing's problem, and it uses only computed anchors plus the peer cross-section.

**THE TIER-B ROW CAP IS DROPPING DECISION-RELEVANT DRIVERS ACROSS THE FLEET — REPORTED, NOT FIXED
(2026-08-04). RELEVANCE CANNOT BE DERIVED WHERE THE CAP FIRES, so no ranking was invented.**
**WHAT THE CAP IS:** `driver_extract.py:39` `_MAX_ROWS = 12`, checked at `:157` **inside the loop
over the LLM's emitted drivers** — so it selects by ARRIVAL ORDER. First-hit-wins applied to row
selection.
**ITS STATED REASON IS HALF FALSE.** The comment reads *"depth-stage cost/space bound"*. `_MAX_ROWS`
appears ONLY in the response loop and **the system prompt never tells the LLM to emit at most 12** —
so every dropped row was **already generated and already paid for**. The cap saves **zero** LLM cost;
it is purely a space bound, and the cost half of the justification does not hold as implemented.
**IT ALSO CONTRADICTS A STATED DESIGN RULE.** DESIGN RULE v2: *"`dossier.json` is machine-complete —
every extracted fact stays in it."* The cap DELETES extracted facts from the machine-complete layer.
**BLAST RADIUS, MEASURED: 113 rows dropped across 10 of the 11 names** — IT **28**, BRBR **17**,
VRRM 15, AORT 14, SMPL 12, CNXC 9, FUBO 8, VITL 5, NCNO 4, EPAM 1, MVST 0 (no transcript).
**AND THE CAP BINDS UNIVERSALLY, NOT OCCASIONALLY: every one of the ten transcript names keeps
EXACTLY 12 transcript rows.** Not one lands under the cap. This is not a BRBR anomaly — it is the
steady state of the fleet.
**AND ON BRBR IT DROPPED THE ROW THE UNDERWRITE TURNS ON.** Its decisive question is whether the
margin collapse is structural, and **`adjusted gross margin` is among the 17 dropped** — along with
buy rate, % of category volume on promotion, Premier shake volumes/price-mix, club channel share and
advertising as % of sales. Kept in their place, purely because they arrived earlier: *"single bottle
sales = more than doubled"* and *"wellness category growth = grew 7%"*.
*(CORRECTED ON SELF-REVIEW: the first cut also cited two near-contentless `pricing action` rows
valued "price increases"/"pricing actions" as displacing better ones. They are sourced to 8-K
EX-99.1, i.e. the ANCHORED path, and the cap governs transcript rows only — they never competed for
a slot. The comparison stands on the twelve transcript rows alone.)*
**WHY NO RANKING WAS BUILT — the ordering makes it impossible.** `extract_transcript_drivers` runs at
`assemble.py:413`; `synthesize` runs at `:422`. **The decisive question does not exist when the cap
fires** — it is produced NINE LINES LATER. Ranking by relevance-to-the-decisive-question cannot be
done at extraction, and anything I could rank on there (keyword match, digit density, kind priority)
would be an INVENTED SCORING HEURISTIC, which the brief forbade. **So it is reported and stopped.**
**THE SHAPE OF THE FIX, for the operator to rule on:** the rows are already generated and paid for,
and the machine-complete layer is where they belong — so the bound should MOVE, not shrink or grow.
Keep every extracted row in `dossier.json`; apply any bound at the RENDER tier, where the decisive
question exists and relevance is derivable. That is a re-ordering, not a heuristic.
*(TWO NUANCES FOR WHOEVER BUILDS IT, the second corrected on self-review. (a) A metric can appear
both kept and dropped — the transcript SLICE spans two earnings calls, so the LLM emits the same
metric twice and the later instance hits the cap. (b) `extract_transcript_drivers` is called ONCE
per assembly (`assemble.py:413`), NOT per transcript — the first cut claimed a per-call cap. BRBR
and VITL carry 14 Tier-B-KIND rows because **two of theirs come from the anchored 8-K path**, which
the cap does not govern; their transcript count is 12 like everyone else's.)*

**UNIT/LABEL DEFECTS — the one-name-two-meanings class, now three instances recorded together.**
(1) **`percentile` printed as `p25`** — `own_history.percentile` is WHERE CURRENT SITS (BRBR 0.037 →
3.7th), not a 25th-percentile LEVEL; the first cut of the evidence block put a RANK where a LEVEL
belongs. Caught in self-review of #334, fixed.
(2) **`"shares"` labelling a value in MILLIONS** — my own `build_template` emitted
`{"value": 116.27785, "unit": "shares"}` while SMPL's committed record correctly says **`"M shares"`**.
A unit label that disagrees with its own value. Fixed and pinned.
(3) **`{axis}_basis` colliding with `ScenarioInput.margin_basis`** (which EARNINGS LINE, not
provenance) — renamed `{axis}_derivation` in #333.
**The through-line: a label is load-bearing exactly when a reader cannot tell from the value which
quantity it is.** All three passed every type check and every test.

**RIDER SHIPPED: `test_brief_render_batch_a.py` iterated `DOSSIERS` without filtering to
directories**, so a Finder `.DS_Store` reddened the suite on any Mac. One line, guarded.

**THE BRBR REVENUE GATE — CLEAR, MEASURED 2026-08-04. Nothing reads a single year.** Exactly ONE
BRBR field reads EDGAR revenue: `anchor.margin`, sourced `OperatingIncomeLoss / Revenues` over
**8 FY** via `midcycle`'s longest-coverage pick. `consensus_levels`, the gap's revenue ratio and the
brief are all **CIQ-sourced** — `margin_trend`, `free_cash_flow` and `financial_summary.annual` all
carry CIQ source_refs, so the EDGAR fallback never fired.
**AND THE SHARED EXTRACTOR'S BEHAVIOUR ON BRBR IS ABSENCE, NOT A WRONG NUMBER:**
`extract_points(facts, "revenue")` returns **ZERO** annual points for BRBR (first-hit picks the
ASC-606 tag, which holds only the incomplete FY2026) — so `EdgarFundamentals` would read revenue as
UNKNOWN, fail-loud, rather than as a truncated series. **That is materially less severe than WERN's
4-of-18**, and it only arises at all when CIQ fundamentals are EMPTY, which BRBR's are not.
**So the underwrite is not gated. The shared-extractor fix stays queued** — it could move anchors on
the revenue-affected names, which is a decision-path change wanting its own measurement.

**AND THE MULTIPLE ANCHORS ARE THE SAME CLASS, as suspected — so it is 3 SAFE / 3 CONTAMINABLE /
3 UNANCHORED.** `own_history.low` is a min-statistic: **dropping its single defining close moves the
low +0.77x against the median's +0.21x**. The contamination CHANNEL differs, though — a
writedown-collapsed EBITDA *spikes* a multiple (denominator shrinks), so it inflates `high` (which
would double) and not `low`; what pushes `low` down is a price collapse without an EBITDA collapse,
which is exactly SMPL's present state (current 5.34 BELOW the historical low 6.11).
**THE RESULT IS CLEAN AND PRINCIPLED: the safe anchors are EXACTLY THE MEDIANS** — revenue base
(consensus median), margin base (8-FY median), multiple base (own-history median). **Every
extreme-statistic anchor is contaminable; the unanchored cells have no statistic at all.**

**`scenario-create` BUILT (`vinci/dossier/propose.py`) — the underwrite finally has a writer.**
Until now `scenario-refresh`/`scenario-supersede` both required an existing record and
`write_record()` had ZERO callers, so every record was hand-authored and the one place analyst
judgment enters bypassed every guard.
**IT PROPOSES 3 AND REFUSES 6 — and the count does not decide the design.** The invariant holds on
all nine: **every number either derives from an anchor carrying its `source_ref` + `vintage`, or
states its basis — and both are refused if absent.**
**§D IS NOW STRUCTURALLY IMPOSSIBLE, demonstrated on the real record:** SMPL's committed base margin
is refused with *"base.margin = 14 deviates from its anchor 15.4481% by -1.4481 and states no
reason"*. Stating the adjustment clears it; taking the anchor needs nothing. **The ruling moved into
the write path, where it binds every author.**
Also enforced: **`RefPoint.vintage` inherited from the dossier**, never stamped as "today" (the
absence of which is why SMPL's five references could not be dated); **refusal on a dossier/record
recipe disagreement — AORT is live on day one** (hint `R1_midcycle…` `applicable: True` against a
record that is R2); **refuse-never-default on a missing leg**; and every refusal repeats WHY the cell
had no proposal rather than only that it is absent.
**FOUR DEFECTS IN MY OWN MODULE, CAUGHT IN SELF-REVIEW OF #333 (no reviewer comments; the audit found them):**
(1) **UNIT MISMATCH — the worst of them.** `ScenarioInput.margin` is a DECIMAL FRACTION (SMPL's legs
are 0.1/0.14/0.165) while a `RefPoint` displays a margin as `15.4481` + `"%"`. The first cut carried
ONE value, so a supplied 0.14 was compared against 15.4481 — a 99% deviation reported on a leg that
matches its anchor EXACTLY. `Anchor` now carries `value`/`unit` for display AND `schema_value` for
comparison. **Display formatting made load-bearing, which is a rule this repo already has.**
(2) **`anchor.applicable` was never read, and VITL is a SECOND live case beside AORT** — hint
`R1_midcycle_margin_evebitda` with `applicable: False` (EBITDA dispersion 263.7% → routes two-ratio).
Checking only the hint STRING waved through a record on a recipe the dossier had declined.
(3) **`{axis}_basis` collided with `ScenarioInput.margin_basis`** (EBIT|EBITDA — WHICH LINE, not
where the number came from), so `"EBIT"` would have satisfied a provenance requirement it does not
answer. Renamed `{axis}_derivation`. One name, two meanings — the recurring class.
(4) **A zero anchor made the relative-drift fallback read 0.0**, silently accepting any value.
**7/7 mutations CAUGHT** — deviation-without-reason accepted, basis no longer required, missing leg
skipped, and margin-bear acquiring a min default.
**A NEW RECORD IS A GENUINELY NEW OBJECT, not an append:** `write_record` writes
`scenarios/<TICKER>.json` and the append-only path is `refresh_log`; supersession (archive-and-reissue
under `<TICKER>-<date>`) is a separate act, so creating never mutates an existing record.

**`scenario-create` — STEP 1 REPORTED, STEP 2 NOT BUILT. The stop condition fired.** Full render in
`docs/audits/2026-08-04-scenario-create-derivability.md`. **The underwrite is the critical path and
has NO writer** — `scenario-refresh`/`scenario-supersede` both need an existing record, `write_record()`
has zero callers, every record was hand-authored — so the one place analyst judgment enters bypasses
every guard.
**FOUR OF THE NINE HAVE A SAFE DEFAULT; TWO ARE COMPUTABLE BUT CONTAMINABLE; THREE HAVE NONE.**
SAFE: **revenue base** (`consensus_levels` median at the anchor FY), **margin base**
(`anchor.margin.value`, 8-FY median), **multiple bear** (`own_history.low`), **multiple base**
(`own_history.median`). **NO DEFAULT AT ALL: revenue BEAR, revenue BULL, multiple BULL.**
**CONTAMINABLE — margin BEAR and BULL, and I counted them safe in the first cut; caught in my own
review of #332.** The record labels them *"worst / best CLEAN year"* and today the RAW min/max happen
to equal them (9.579≡9.58, 17.349≡17.35) — **luck, not robustness.** The same record's FY2025
reference is **15.0103% against a raw 10.8129%, a +4.1974pp adjustment**, so the series demonstrably
contains years where raw ≠ clean; FY2020 simply sits below FY2025's contaminated raw. **SMPL's FY2026
carries the −$391.9M writedown**, and adding one such year moves **min −26.63pp (9.579% → −17.050%)
while the median moves −0.063pp**. **A raw-min default would propose a NEGATIVE bear margin on the
very next re-underwrite.** The median absorbs one bad year; **min/max ARE the statistic a one-off
defines.** Cleaning is judgment, so an unguarded min/max default would label an unadjusted extreme
"clean". They could be proposed only behind a cleanliness test.
**AND THE OBVIOUS SUBSTITUTE IS MEASURABLY WRONG, which is why this stops rather than improvises.**
`consensus_levels` carries low/median/high, so a low/high default LOOKS available. SMPL's FY2026
consensus range is **1,345.0–1,357.0 — 0.9% wide** — against a committed bear of **1,180.0**.
Defaulting bear revenue to the consensus low would propose a bear **14.0% too generous**, in the leg
that sets the risk denominator and therefore reward:risk. **The reason is structural: consensus
dispersion measures DISAGREEMENT AMONG FORECASTERS, not the downside scenario** — eleven analysts
modelling one guidance agree within 1%; a bear models a world none of them forecasts. Substituting
one for the other would understate risk on every name, in the direction that flatters. For the bull
multiple, SMPL chose **16.00x — BELOW its own trailing median of 17.85x** — so neither `p75` nor
`high` reflects the practice and no principled anchor exists.
**A 4-of-9 PROPOSER (defaults four, REFUSES on three, gates the two contaminable ones) invents nothing and is buildable** — shape
recorded in §4 of the render, including `RefPoint.vintage` inheritance, the tier check refusing on a
dossier/record disagreement (AORT is a live case day one), and refuse-never-default on a missing leg.
**Whether that clears "a proposer that invents a number is worse than a form" is the operator's call.**
**R2 is the same or worse**: its terminal year sits beyond any consensus row, so even the base-revenue
anchor R1 gets has no R2 counterpart.

**RIDER — SMPL'S FROZEN REFERENCES: THE STATIC ONES ALL REPRODUCE, THE LIVE ONES ALL MOVED.**
Reproduce exactly: FY2025 reported revenue 1,450.9 · **all five MARGIN references** (15.4481 /
15.5107 / 9.5788 / 17.3494 / 15.0103) · trading-range low 6.1094 · trailing median 17.8514.
Moved: **LTM revenue 1,416.208 → 1,392.235** (−23.97) · **consensus FY26E 1,334.0 → 1,351.7** (+17.70)
· **current multiple 5.65 → 5.34** (−0.31). **None is stamped, so you cannot tell whether the three
that moved were right when struck — P3 pt1's cost, demonstrated rather than argued.**
**THE MARGIN REFERENCES ARE THE ONES §D IS ABOUT, AND THEY ALL REPRODUCE: the 14% rests on sound
inputs, so §D is PURELY A DISCLOSURE DEFECT, not a decision-path finding.** The build was not stopped
by the rider; it was stopped by the three undefaultable cells.
**SMPL IS NOT ALIAS-AFFECTED — measured, not looked up:** its ASC-606 tag holds 8 FY (2019–2026), the
longest AND the first alias, so first-hit and longest-coverage agree; `_total_revenue_series` returns
`conflicts: []`.
**BUT BRBR IS THE WERN SHAPE, AND BRBR IS NOW THE COHORT PARTNER.** Its ASC-606 tag holds **ONE** FY
(2026) while `Revenues` holds **seven** (2020–2026). `midcycle` picks longest-coverage so BRBR's
committed anchor is correct (`OperatingIncomeLoss / Revenues`, 8 FY median = 16.0404%) — **the
exposure is the SHARED extractor, still first-hit-wins, which would read BRBR's revenue as a single
year.** The latent issue recorded at PR #149 now has a name on the critical path.

**CORRELATED-SHOCK RISK ON THE SOURCING ROUTE — A HYPOTHESIS WITH A REQUIRED CHECK, not a proved
property** *(corrected on review of #331; my first cut said "by construction")*. **What the selection
rule establishes:** each constituent independently passed a **drawdown gate** (≤ −30% from the 52w
high) and the cluster establishes **business similarity** via residualized co-movement over 365 days.
**What it does NOT establish: that those drawdowns share ONE causal event** — residual co-movement is
equally consistent with a persistent correlated FACTOR carrying no single event, or with several
IDIOSYNCRATIC events falling inside the same year and grouping. Treating the correlated-shock reading
as proved would discount the whole sourcing route on an inference the rule cannot support.
**REQUIREMENT: run an EVENT/DATE ALIGNMENT CHECK before calling any cohort common-shock.** The data
is on disk — each candidate record carries a typed, dated `trigger_reason`.
**THE CHECK, RUN: THREE OF SIX ALIGN, TWO SCATTER, ONE IS UNTESTABLE.** Aligned on ONE date — **T002
gold/silver 15 of 16 on 2026-01-30**, **T023 quantum all three on 2026-02-05**, **T022 cannabis both
on 2026-04-23**. Scattered — **T008 uranium THREE dates spanning 4 months** (02-04 / 03-16 / 06-05),
**T037 solar THREE spanning 2 months** (02-27 / 04-16 / 04-29). Untestable — **T014 coal**, 2 of 3
being undated price-drop triggers. **So the reading is TRUE FOR SOME THEMES AND FALSE FOR OTHERS,
which is precisely why it must be checked per cohort rather than assumed from the route.**
**AND IT LANDS OPPOSITE TO THE INTUITION ABOUT T002** — the mixed-taxonomy cluster (2 sectors, 5
SICs, coherence 0.385, whose own `shared_note` warns of a driver-less momentum bucket) is the **MOST**
date-aligned of the six. Loose taxonomy did not predict scattered events.
**ONE CAVEAT THE CHECK CANNOT RESOLVE:** a shared DATE is evidence of a common MOVE; the label
`earnings_gap_down` attributing it to EARNINGS for fifteen issuers on one day is **not** established
by that field and is implausible on its face — confirming it needs per-name filing dates. **Read the
date alignment; do not read the attribution.**
BRBR does NOT come from this route at all; it comes from the book, and its relation to SMPL is
product-market (protein snacking), so the correlated-shock question does not arise for it.
**BRBR's FY-END VERIFIED FROM ANNUAL DURATION FACTS: Sep-30, a FIXED month-end** (one value across
1,325 facts). **SMPL is 52/53-week and DRIFTS** (Aug-31/29/25/28/27 across years), FY2025 ending
Aug-30-2025 → **offset ≈31 days, and not constant.** *(CPB sits ≈27 days the other side.)*
**CORRECTION TO THE FRAMING: that is NOT tighter than anything in the theme read** — T014, T023 and
T037 are internally ZERO-offset (all Dec-31). The true claim is narrower: **BRBR/SMPL is the tightest
alignment among REACHABLE pairings**, those three themes being blocked on bundles, legs and anchors
whatever their calendars.
**BRBR IS ONE ANALYST RECORD FROM A DECOMPOSED GAP, AND THE ARTIFACT SAYS SO IN ITS OWN WORDS:**
`form: three-ratio`, `status: not-computed`, `reason: "no scenario record for this name — the route
is known, the gap is not"`. **Every MECHANICAL input already exists** — `d_and_a` 18.6, `net_debt`
1,181.9, `diluted_shares` 116,277,850. The analyst supplies only the judgment: three legs
(revenue/margin/multiple + a schema-enforced non-blank `reason`, `bear_basis` on bear,
`margin_basis`) and the per-axis `method` sentences. `tier`/`survival_input`/`years_to_terminal` are
R2-only and stay None.
**CONSENSUS SUPPORTS THE DECOMPOSITION, better than SMPL's:** Revenue **13/13** disp 2.07%, EBITDA
**12/12** disp 6.58%, no caution (SMPL: 9/11 and 10/10). **SHARED ANCHOR FY2026 AND ADJACENT FY2027**,
so the two decompositions compare on one horizon with no year adjustment. BRBR's forward span runs
FY2026→FY2030 against SMPL's →FY2033, but the tail years carry 1–2 estimates and neither anchor
depends on them.
**R1 FITS** (`recipe_hint R1_midcycle_margin_evebitda`, `applicable: True`) — **the gap decomposes**,
it does not route to price-implied-only.
**AND THE R2 SET IS CONFIRMED YOUR WAY, WITH ONE DISCREPANCY.** The R2 marker in a committed record
is **`tier`** (None on R1): **AORT B · MVST B · NCNO A** are the three R2 records; EPAM/IT/SMPL/WERN
are None. **But AORT's DOSSIER hint reads `R1_midcycle_margin_evebitda`, `applicable: True`, while
its RECORD is R2** — hint and record disagree for that one name; the record governs.
**BRBR IS NOT ALONE — THREE dossiers are one underwrite from a computed gap**, all `three-ratio` +
`not-computed` with the identical reason: **BRBR** (13/13, 12/12, no caution), **VRRM** (8/8, 6/6, no
caution), **CNXC** (3/3, 3/3, **caution carried on both legs**). VITL routes `two-ratio` (EBITDA
dispersion 263.7% past the 50% ceiling); FUBO has no recipe.
**CPB, THE FALLBACK:** 52/53-week ending late Jul/early Aug; CIK 0000016732. **Bundle KIND-FOR-KIND
identical to BRBR's** — all nine kinds plus two transcripts (Q2 Mar-11, Q3 Jun-08 2026). **That is a
bundle-completeness INFERENCE, not a demonstration** — no assembly was run, so nothing proves the
extractors succeed on Campbell's exports. Everything downstream (recipe, consensus_levels, anchor,
route) is unknown until it assembles: **CPB needs an assembly AND then the same analyst record BRBR
needs.**
**EPAM + IT ARE ALREADY A COHORT MECHANICALLY — zero further work.** Gaps **2.0196 / 1.6460**, both
`multiple-dominant` at anchor AND adjacent (agree=True), both anchor **FY2026**. **Both revenue
ratios ≈1.00** (1.0012 / 1.0002) — our top line and the street's agree on each, so the disagreement
is the multiple on both, with margin secondary (EPAM 0.76, IT 0.87).
**PEER OVERLAP, MEASURED: raw 6 of 12 each, but that COUNTS EACH OTHER AND THE SYNTHETIC `Peer
median` ROW. Genuine third-party overlap is THREE — CTSH, DOX, EFOR.** EPAM's remainder is IT
services/engineering (ACN, GLOB, DXC, SOP + two non-US rows); IT's is information services/ratings
(EFX, FDS, MCO, SPGI, TRU, VRSK). **A usable pair on horizon, shape and completeness; a weak one on
comparability** — they intersect only at the IT-services tail of Gartner's set.

**THE THEME-COHORT READ — RUN 2026-08-04, full render in `docs/audits/2026-08-04-theme-cohort-read.md`.**
The A5 blocker was a read nobody had run. From the 2026-07-29 output (**331 candidates**) against the
**35** committed theme clusters — **no new screen run**, since `RunManifest` is still unpopulated and a
fresh run would be unattributable.
**SIX of 35 clusters hold ≥2 candidates, covering 32 names** (5 clusters hold exactly one, 24 hold
none): T002 gold/silver **16**, T008 uranium **5**, T014 coal **3**, T023 quantum **3**, T037 solar
**3**, T022 cannabis **2**. All six pass admissibility; **T002 is the loosest** (coherence 0.385,
2 sectors / 5 SICs) and its own `shared_note` demands the analyst name the driver or reject it as a
momentum bucket — unresolved.
**VINTAGE GAP, and it bounds every count: the clusters are as-of 2026-06-17, the candidates 07-29.**
Six weeks. A name that became a candidate after 06-17 cannot appear in any cluster, so **≥2 counts
are a FLOOR, not a census.**
**THE FINDING THAT MATTERS FOR THE PICK — as a SCREENING matter the theme route does not sidestep
G3, it runs into it.** `G3_multiple_floor` is **UNKNOWN for all 32 (100%)** against an **85.2% base
rate across all 331** (282 UNKNOWN / 49 PASS) — the multi-candidate themes are WORSE than the
population.
**BUT G3 IS NOT AN INPUT TO THE GAP, and my first cut said it was** *(corrected on review)*.
`build_ev_gap` takes `levels, leg, tev, net_debt, shares, tev_as_of, consensus_as_of` — **no G3** —
and `G3_multiple_floor` appears NOWHERE in `ev_gap.py` or `assemble.py`; the docstring is explicit
that even the consensus side is optional (*"absent levels … does NOT mean no total"*). Claiming a
name *"needs a G3 resolution before a gap exists"* **promotes a policy gate into a mechanical one**
and overstates what the code enforces.
**THE TWO MECHANICAL PREREQUISITES, both absent for all 32: a TEV** (CIQ comps panel → needs a
bundle) **and OUR OWN BASE LEG** (a scenario record). Measured: the 32 intersect the 14 bundles in
NOTHING and the **7** committed scenario records in NOTHING. Separate the three kinds — mechanical
(no TEV, no leg), policy (*do not advance an unresolved-G3 candidate*), and depth (the **19** with no
EDGAR anchor, which R1 does not reach either).
**AND A STANDING QUESTION ANSWERED IN PASSING: only 7 scenario records exist at all, against 14 CIQ
bundles — so 7 of 14 bundle-holders have no own leg.** Of the eleven dossiers **six carry a record**
(AORT, EPAM, IT, MVST, NCNO, SMPL), confirming the long-standing "6 of 11" note by measurement;
WERN carries one with a bundle but no dossier.
**AND THE BUNDLE SET IS 14, NOT ELEVEN** — `data/manual/ciq/` also holds **CPB, PENG and WERN**,
which carry bundles with no dossier. None of the 32 has one.
**TWO STRUCTURAL FACTS, measured not inferred.** (1) **20 of the 32 are foreign private issuers** —
only 12 file a 10-K; the rest file 20-F/40-F only. All 32 read `country: US`, which is LISTING VENUE,
so a country filter on the candidate record does not surface this — the filing FORM does. (2)
**Running the production anchor derivation over cached companyfacts, a margin computes for only 13 of
32** — **all 16 of T002 produce nothing** (no us-gaap total-revenue tag on IFRS filers), and 7 of the
13 return negative or near-zero medians (QUBT −7,330%, RGTI −734%, QBTS −725%, CGC −214%, UUUU −119%,
TLRY −52%, URG +0.99%). Six return a positive multi-year median (BTU, AMR, CNR, CSIQ, DQ, JKS) —
**recorded as what the pipeline can produce, NOT as a shortlist.**
**FISCAL-YEAR MISMATCH, the thing to know when picking rather than when building A5:** T014, T023 and
T037 are internally clean (all Dec-31). **T008's UEC ends Jul-31 against four Dec-31 mates — five
months**, the largest inside any theme. **T022 is the only theme where NO two members share a
year-end** (TLRY May-31, CGC Mar-31). T002 is 14×Dec-31 with NG at Nov-30 and SVM at Mar-31.
**REPORT ONLY — no name recommended; the cohort pick is the operator's and the analyst's.**

**§D SOURCING STEP — DISCHARGED 2026-08-04. THE FIGURE IS UNFINDABLE AS A STORED VALUE, AND THE
OPERATOR'S OWN SUSPICION IS CONFIRMED: it was their working, not the repo's.**
**Searched by OBJECT, not by label** (the `13.8`/`N1`/`CHRO` lesson): every numeric in margin range
across `dossier.json` AND `frontend/scenarios/SMPL.json`, whatever it was named. **`~13.8%` exists
at exactly ONE place in the repo — `scenarios[1].reason`, the base leg's free-text analyst prose.**
Not a reference, not a field, no unit, no source. The margin axis carries FIVE references
(15.45 / 15.51 / 9.58 / 17.35 / 15.01) and **none is ~13.8**. The axis `method` sentence does not
contain the number either — only the leg reason does, which is why the rendered brief (`md:57`)
shows it and the anchor card (`md:446`) does not.
**WHAT THE PROSE MEANT IS A HYPOTHESIS, NOT A FINDING — and the first cut of this entry got that
wrong** *(corrected on review of #329)*. It read *"the trailing clean margin through the third
quarter"* as **= LTM through FQ3 FY2026** and then called two CIQ calculations *"two routes to the
SAME object"* — **which silently supplies the very binding this entry had just proved is missing.**
Proving a figure is unbound and then identifying it by reading is the same substitution one level
up, and it is the third time this session.

**THE PROSE FIXES NONE OF THE THREE THINGS a binding needs:**
- **the WINDOW** — *"trailing … through the third quarter"* admits LTM-to-FQ3 **and** YTD-FY26-to-Q3.
  Both are live windows for this very name; the audit's own reconciliation uses *"YTD FY26 $331.0M"*
  beside the LTM total, so the ambiguity is real here rather than theoretical. No fiscal year is
  named either.
- **the DEFINITION OF "CLEAN"** — ex-writedown, ex-all-unusuals, CIQ's own convention, or an analyst
  adjustment. Undefined, and these give different numbers.
- **the LINE** — EBIT, or EBITDA less D&A. The two candidates below differ in CONSTRUCTION, not
  merely in value.

**SO: the CIQ figures are CANDIDATE INTERPRETATIONS, not recoveries.** They are listed below because
they are what the repo can produce for a trailing margin — **not** because either is what the prose
meant, which remains unknown and unrecoverable from the record.
**BINDING REQUIREMENT, RETAINED: neither CIQ route may inform the margin choice until it carries an
explicit source AND basis of its own.** Adopting one because it is close to an unbound number would
launder the missing derivation into an apparent one — the exact failure §D exists to name.

**THE CANDIDATE BASES THE REPO CAN ACTUALLY PRODUCE (recomputed offline from cached EDGAR facts +
the committed artifact — measured, not read off a label). The VALUES and BASES below are measured;
any claim that one of them is what the prose meant is NOT — see the hypothesis note above:**

| candidate | value | window | accounting basis | basis ASSERTED or INHERITED? |
|---|---|---|---|---|
| `anchor.margin.value` | **15.4481%** | 8 FY (FY2018–FY2025) | EDGAR `OperatingIncomeLoss / RevenueFromContractWithCustomerExcludingAssessedTax` | **ASSERTS** — a `basis` field (*"operating margin (EBIT / revenue)"*), both tags named in `source`, `anchor_years: 8`. **Verified MEDIAN, exact to 4dp** |
| ref[1] *"7yr clean median (FY2025 adjusted)"* | **15.51%** | 7 FY (FY2019–FY2025) | same EDGAR tags, FY2025 adjusted ex the $60.9M impairment | **STATES** its derivation in `source` but is **NOT a repo-computed field**. **Verified MEDIAN of the last 7 FY = 15.5107%** |
| `own_history[0].implied_ebit_margin` | **13.8933%** | trailing, as-of 2026-07-23 | CIQ Multiples: `TEV/LTM Revenue ÷ TEV/LTM EBIT` | **INHERITS** — CIQ's EBIT definition; nothing in this repo asserts it excludes unusuals |
| `quality.margin_trend` LTM route | **12.8845%** | LTM to May-30-2026 | CIQ Income Statement absolutes: EBITDA 217 / revenue 1,392 = 15.5891%, less implied D&A 2.7046% | **INHERITS** |

**THREE THINGS THAT MATTER FOR THE CHOICE, and none was visible before this pass:**
