---
id: 
status: shipped
date: 2026-08-21
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**TIERED GATES SHIPPED 2026-08-21 (`feat/tiered-gates`) — FOUR OPERATOR RULINGS, RECORDED HERE
because they were given in chat and chat is not a ledger (OPERATOR-ACTION RULE).** Context: the
operator generalized the GOOGL memo's hurdle ladder FUND-WIDE (all names, all recipes — not
per-book), which decoupled this from the book-blind ruling and R3 entirely.
- **RULING 1 — the BUY-eligibility line is ratio ≥1.75 AND base IRR ≥12%;** 2.0x/15% become the
  PREFERRED tier. Ladders (half-open upward): asymmetry <1.0 poor · <1.75 below_target · <2.0
  target_met · ≥2.0 preferred; return <12% fails · <15% minimum_met · ≥15% preferred.
- **RULING 2 — INFORM-ONLY.** Tiers and `eligible` label the record; no validator reads them.
  Survival stays the only hard block (it guards a WRONG number, not a low one).
- **RULING 3 — THE SEALED BOOK FREEZES, with the regime made visible.** A record without
  `gate_regime` was judged under the 2:1/15% booleans alone and every surface SAYS so.
- **RULING 4 — THE IRR STAYS PRICE-ONLY,** convention stamped on the record ("price-only —
  excludes dividends; conservative for dividend payers"). A dividend forecast is an assumption,
  and assumptions are analyst-stated.
**PROVENANCE:** face validity; the thresholds are the GOOGL memo's pre-existing hurdles, set
before any name was pending on them — GOOGL itself FAILED its own 1.75x. Never outcome-tuned.
**HOW IT SHIPPED — add-beside, the 2026-08-05 precedent applied again:** the preferred lines ARE
the legacy constants, so `pass_fail`/`irr_pass_fail`/`gate`/`bar`/`irr_floor` keep their
arithmetic on every record ever written. Nine new `Result` fields (`gate_regime`,
`asymmetry_tier`, `return_tier`, `eligible_ratio/irr`, `eligible`, `eligible_undefined`,
`ceiling_eligible`, `irr_convention`) default None and serialize as a DROP-GROUP keyed on the
regime (`LADDER_FIELDS`), so the committed book is byte-identical on disk and its cards gain no
keys. **REFRESH SEMANTICS, the subtle half of Ruling 3:** `_with_irr_gate` is LEGACY-PRESERVING —
recompute of a record whose result carries no regime reproduces that result EXACTLY (the no-op
refresh stays a no-op); the ladder stamps only on a FIRST compute. **WHICH PATHS REACH IT —
TRACED, AND THE FIRST DRAFT OF THIS ENTRY GOT IT WRONG (review, #487):** `scenario-create`
(validate → run_recipe → write) is the MIGRATION path; `scenario-refresh` recomputes with the
result present and is the case the preservation branch exists for; **`scenario-supersede` never
calls `run_recipe` at all** — the incoming payload's `result` is written verbatim, so a supersede
carries whatever regime its payload holds. The draft claimed "a superseded reissue" stamps the
ladder; it does not. **PRE-EXISTING, NOT THE LADDER'S DOING** — the 2026-08-05 IRR gate has the
identical exposure, visible in the committed corpus (both archived SMPL records carry
`gate: UNDEFINED, irr: null` beside a live record with a computed gate). Pinned as BEHAVIOUR
(`test_supersede_writes_the_payloads_result_verbatim`) so the corrected sentence is
machine-checked rather than merely reworded.
**OPERATOR TO-DO — should `scenario-supersede` recompute the incoming payload's `result`?**
Today it trusts the analyst's payload. Recomputing would make supersede a migration path and
close the gate-staleness window, but it would also silently re-run the engine over
analyst-authored numbers — a decision about who owns that block, not a cleanup, which is why
this build recorded it instead of taking it. Affects the IRR gate identically, so the ruling
covers both. **CORPUS RUN (all 8 live records, in memory):** zero reclassifications; EPAM is the
acceptance case (below_target asymmetry + preferred return → NOT eligible — the levered-bet
refusal); IT pins the determinate-false AND (below-line ratio + undefined IRR → False); SMPL
alone is ELIGIBLE (2.10x / 44.3%). The 12–15% divergence zone (old boolean FAILs while the
record is ELIGIBLE) is unreachable on the corpus and is pinned on a frozen SMPL derivative —
which is how mutation M4 (irr boolean rebased onto 12%) survived the first sweep and got its
pin. **SIDE EFFECT:** the tier pills replace the bare green PASS chip on new-regime cards, which
retires the card half of the PASS-chip / `Verdict.PASS` vocabulary collision (the book-blind
entry's ruling is still owed for the rest). **ARTIFACTS:** the 8 committed dossier.md (+ mirrors)
gained one line — "_judged under the 2:1 / 15% regime (pre-2026-08-21; tiers not applied)_" —
re-rendered from committed JSON, no re-assembly, no synthesis touched. **INVARIANT (INVARIANT
RULE):** `tests/test_tiered_gates.py`, 49 pins — edge pins at every half-open boundary,
legacy-preservation on all 8 records, the stamped round-trip, and the card EXECUTED under node
for both states (the #469 render-don't-grep rule). Mutation-verified: threshold shift,
determinate-false inversion, truthiness emit dropping `eligible: false`, irr-boolean rebase,
legacy-line deletion — all killed.

**OPERATOR TO-DOs — MEGACAP + NON-US-FILER (FPI) READINESS, measured from code, recorded
2026-08-20 (OPERATOR-ACTION RULE — the assessment happened in chat, and chat is not a ledger).**
"FPI" = SEC *foreign private issuer*, a non-US filer (20-F/6-K, IFRS) — NOT the house sense of
"foreign figures" (another name's figures on a page, the BRBR incident); glossary line added in
the same PR. Context: the operator asked whether the setup can underwrite megacaps
(NFLX/GOOGL/NVDA/AMZN/AMD) and non-US names (Novo Nordisk, AstraZeneca, Nokia — plus Eli Lilly,
a plain US filer).

**READY, so the gaps below are scoped and not re-found:** followed-entry with mandatory sleeve
(`vinci/followed.py`; a screen-candidate conflict refused at `assemble.py:399`); per-book framing
end-to-end (`system_for`/`tool_for` sent at `synthesis.py:1199`; unknown sleeve REFUSED, no
overshoot fallback); `Verdict.PASS` with write-time vocabulary enforcement
(`ledger/workflow.py:52`); per-sleeve proposal legs (`dossier/verdict.py`); cap-band benchmarks
IWM/MDY/SPY (`monitor.py:43` — V's committed page carries SPY at $665B); ADR/foreign security
types admissible (`config.py:61` — CS/ADRC/OS/GDR); dei-based share counts with a 20-F/40-F-aware
staleness bound (`mechanical.py:2537`); 13D/G on US-listed names. Three committed megacaps
(V, UBER, NFLX) are the existence proof. **LLY is onboardable today on the same terms as any US
megacap.**

**THE GAPS — MC = megacap, FPI = non-US filer. Absence claims state the searches tried.**

- **MC1. XBRL tag-level freshness has no guard.** `edgar/concepts.py` is ONE global
  priority-ordered us-gaap alias list, first-present-wins, point-in-time by filed date; no
  freshness assertion at the tag level (searched stale/STALE/coverage_status/fresh across
  `vinci/edgar/`). **PER-TAG is the missing grain, not staleness as such** — two staleness bounds
  DO exist and neither is per-tag: `price_staleness_days` (`config.py:93`, price coverage) and the
  share-count age bound (`mechanical.py:2501/2517`, 180d vs 540d chosen by 20-F/40-F-vs-10-Q
  cadence — named in the READY list above and again in FPI2). The first draft of this line said
  "the only staleness knob is `price_staleness_days`", which its own record falsified twice in the
  same block; the corrected claim is narrower and survives. A filer
  that ABANDONS a tag still carries old data under it, so first-present-wins can serve a dead
  series under a confident filed date. The GOOGL monitoring workstream reports this shape live at
  megacaps (AMZN/META/NVDA tags years stale, MSFT untagged) — those specifics are
  VERIFY-AT-BUILD; the CLASS is what this records. ACTION: per-tag freshness assertions before
  any megacap's XBRL diversity is trusted.
- **MC2. Segment ECONOMICS are not extracted — only segment revenue SHARES.** `_segment_roster`
  (`ciq_sheets.py:1349`) reads (name, share of total revenue) for concentration; no per-segment
  operating-income/margin series exists (searched "segment" across `vinci/` and READ every hit —
  the roster plus GICS/peer wording; `git log --all -i --grep=segment` surfaces split/books work,
  no extractor). Megacap theses ARE segments (AWS, Google Cloud, NVDA data-center): today their
  economics reach the record only as synthesis prose. DECISION: does the followed-megacap book
  justify a segment-note extractor (10-K/10-Q via the FilingSummary/R-file route), or does the
  book accept prose-only segment evidence?
- **MC3. No P/E-basis recipe — a P/E-framed underwrite is REFUSED today.** Recipes are R1
  (midcycle margin × EV/EBITDA) and R2 (terminal margin × EV/EBITDA|EV/EBIT|EV/Revenue)
  (`scenarios.py:830`, `AXES_BY_RECIPE`); no P/E basis (searched P/NTM, price_earnings,
  pe_multiple; `git log --all -S"BASIS_PE"` — not found under those searches). Refusal is the
  DESIGNED failure mode (#374) — nothing mangles — but a GOOGL-shape underwrite (P/NTM EPS ×
  Bear/Base/Bull) cannot become a ScenarioRecord. **GATED behind the book-blind ruling already
  recorded in this section** ("the UNDERWRITE layer is still book-blind" — `ScenarioRecord`
  carries no sleeve; the green bar-test PASS chip vs `Verdict.PASS` vocabulary collision): settle
  that ruling FIRST, then decide whether to commission a P/E recipe (declared in
  `AXES_BY_RECIPE`; never speculatively).
- **MC4. The CIQ parser is unproven off December fiscal years.** Header-label parsing with a
  (kind, fiscal-year) compare (`ciq_sheets.py:1072`) SHOULD handle NVDA's late-January FY — but
  every committed name is a December filer, so per CORPUS BEFORE SYNTHETIC it is unverified.
  ACTION: the first non-December onboarding (NVDA) runs the real workbook and pins what it finds.
- **FPI1. The DOSSIER altitude reads only us-gaap; the IFRS wall is already MEASURED one
  altitude up.** `edgar/client.py:129` takes `facts["us-gaap"]`; every concept alias is us-gaap;
  the annual reader gates on `form=="10-K"` + `units.USD` (`mechanical.py:2091`); SBC is one
  us-gaap tag (`mechanical.py:2066`). Searched ifrs case-insensitively across `vinci/` — the only
  source hits are the THEME altitude (`themes/exposure.py`, `themes/assay.py`), where the wall is
  already measured and recorded (the theme-scan record "TWO STRUCTURAL FACTS, measured not
  inferred": 20 of 32 scanned names are FPIs; **all 16 of T002 produce nothing — no us-gaap
  total-revenue tag on IFRS filers**). NEW here is the same wall at the DOSSIER/underwrite
  altitude: an NVO/NOK dossier assembles with every EDGAR-fed block honestly EMPTY (financial
  backfill, SBC, guidance, events). DECISION: does non-US coverage justify an `ifrs-full` alias
  branch PLUS a non-USD units/FX policy? The FX question is NEW to this repo — nothing prices a
  DKK fact today. **AZN is the cheapest pilot: an IFRS filer that reports natively in USD.**
- **FPI2. Event detection is 8-K-bound; FPIs furnish 6-K.** `forms=("8-K",)` is hardcoded at
  `mechanical.py:281/2715/2822/2877` and is the client default (`client.py:340`); the ONE
  20-F/40-F-aware path is the share-count staleness bound (`mechanical.py:2537`). The staler-info
  limitation is already recorded at the SCAN altitude ("foreign issuers 18/450 read on staler
  info… no 8-K stream"); at the dossier altitude the consequence is ZERO event coverage on FPI
  names. ACTION: add 6-K with its OWN semantics — a 6-K is a furnish-anything wrapper, not an
  itemized 8-K; the item-code routing does not transfer.
- **FPI3. Section-16-exempt names: the insider signal is empty and UNLABELED.** The Form 4 scan
  (`mechanical.py:2329`) returns nothing for FPIs forever, and the surface cannot distinguish
  "no insider activity" from "exempt — not applicable". ACTION: an explicit N/A state keyed on
  filer status, so absence is honest rather than quiet.
- **FPI4. No ADS-ratio handling.** Searched ADR / American Depositary / adr_ratio /
  ordinary-share conversion across `vinci/`, plus `git log --all -i --grep="ADR|depositary"` —
  not found under those searches (`config.py:61` admits ADRC as a security TYPE; nothing converts
  a ratio). Where 1 ADS ≠ 1 ordinary (AZN), a bridge mixing a filing share count with the ADR
  price is silently wrong. ACTION: a per-name listing-basis ratio BEFORE any per-share bridge on
  a non-1:1 name — REFUSE rather than assume 1:1.
- **FPI5. The CIQ parser is unverified on a foreign-currency workbook.** The cap policy assumes
  CIQ $M→USD (`mechanical.py:669`) and one section title is byte-pinned "Company Level (USD)"
  (`ciq_sheets.py:2279`). A USD-exported workbook (CIQ converts) likely parses; a native DKK/EUR
  export is unproven. ACTION: pilot on a real AZN (USD) export; treat DKK/EUR as its own gate.

**CROSS-REFERENCE, not duplicated:** the GLP-1 demand-shift driver (#484,
`themes/drivers.py:201`) is registered with ZERO tickers — NVO and LLY are its natural names, so
the THEME altitude can attach them now while FPI1–FPI5 gate the DOSSIER altitude for NVO. The
ordering that falls out: **LLY now → AZN pilot (USD IFRS) → NVDA workbook check (MC4) → NVO/NOK
behind the FX policy (FPI1)**. MC1–MC2 bind trust in any megacap's numbers; MC3 binds any
P/E-framed underwrite and waits on the book-blind ruling. No build is queued by this record —
each item is an operator decision or a verify-at-onboarding gate.
## Amendments

**2026-09-01 — the supersede recompute to-do is RULED: yes, recompute AND refuse a mismatch.**
The body's OPERATOR TO-DO asked whether `scenario-supersede` should recompute the incoming
payload's `result`. Ruled by the operator today. `_cmd_scenario_supersede` now recomputes from the
incoming legs and REFUSES when the supplied figure disagrees, naming both numbers.

The body's stated objection — that recomputing "would also silently re-run the engine over
analyst-authored numbers" — is answered by the shape of the fix rather than set aside: it refuses
instead of overwriting, so a disagreement reaches the analyst rather than being quietly corrected.
Silent overwrite was offered and explicitly NOT taken.

The `supersede_record` PRIMITIVE stays verbatim by design, and the body's claim about it remains
true. Recomputing there would re-value a sealed archived record under today's engine, which is the
opposite of what an archive is for; the guard belongs at the command, where it can refuse.

COST MEASURED BEFORE THE RULING WAS TAKEN: all nine committed records recompute to their stored
ratio exactly, so the guard refuses nothing that exists on disk. Pinned by
`test_supersede_refuses_a_result_its_own_legs_do_not_produce` plus a corpus cost check; the two
pins that guarded the old behaviour are re-ruled rather than deleted — both had said in their own
words that a change here required this ruling first.

**2026-09-01 — MC3 is DONE and MC1 is tracked elsewhere.** The body lists MC1–MC4 / FPI1–FPI5 as
open. MC3 ("no P/E-basis recipe — a P/E-framed underwrite is REFUSED today") shipped with R3, and
GOOGL is the first record written through it. MC1's detection half shipped (`stale_served`,
`filer_frontier`); its reporting half is dead by construction and is tracked as STATE §5.0 row 11.
MC2, MC4 and FPI1–FPI5 remain — restated in STATE §5.0 row 4 with the operator's build order.
