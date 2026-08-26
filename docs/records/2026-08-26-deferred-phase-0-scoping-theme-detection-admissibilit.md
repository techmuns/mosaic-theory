---
id:
status: recorded
date: 2026-08-26
prs: [506]
supersedes:
superseded-by:
date-source: MIGRATION DATE — this record was cut out of STATE.md on 2026-08-26; the work it describes is earlier and is dated in the body. The filename prefix is therefore the migration date, not the event date.
migrated-from: STATE.md §4 Deferred
status-note: `recorded`, not `open` — STATE.md §4 keeps the item and its unlock trigger and is the authority on whether it is still deferred; a record never is
---

# **PHASE-0 SCOPING (theme DETECTION) — admissibility spec written + data-availability spike run;

*The item and its unlock trigger stay in STATE.md §4, which remains the authority on
whether it is still deferred. This is the detail that stood beneath it, verbatim.*

  - **PHASE-0.6 — residual CO-MOVEMENT tested as the clustering basis: QUALIFIED GO (2026-06-25; a
    DIFFERENT answer from the SIC NO-GO).** Throwaway spike (deleted; finding in
    `theme_admissibility_spike.md` Part 2): 317 overshoot names, 6mo daily residual returns after
    stripping market (IWM) **+** broad-sector beta (LOO coarse-sector cohort — both G2 legs), clustered
    on residual correlation, SIC fetched live for the cross-taxonomy test. **Co-movement does what SIC
    structurally CANNOT** — the tightest cluster (corr **0.81**) is RGTI/QUBT/QBTS (Rigetti / Quantum
    Computing / D-Wave), **3 DIFFERENT SICs (7371/7372/7374) that SIC splits**, re-united as **"quantum
    computing"** — a real nameable theme SIC dismembers. **BUT co-movement also admits the
    momentum-bucket trap, visibly:** loosening τ to gain breadth merges distinct themes into a 13-name
    blob (lithium + eVTOL + quantum + robotics + nuclear + AI-defense, 10 SICs, corr 0.36, **no single
    driver**), and a spurious **RUN/FLGT/WLDN** (solar + genetics-labs + engineering, crosses 3 SICs,
    **no driver at all**). So crossing taxonomy is **NECESSARY-NOT-SUFFICIENT** (blobs cross it too);
    the **Criterion-1 driver-naming filter separates real themes from blobs — empirically vindicating
    the spec's architecture** (Criterion 3 finds candidates, Criterion 1 validates). Failure mode is
    **OPPOSITE SIC's**: SIC too RIGID (can never name a driver finer than the industry → defeats
    Criterion 1 at the root); co-movement too LOOSE (admits blobs → but blobs Criterion 1 is built to
    catch). **⇒ co-movement + Criterion-1 is a workable pairing where SIC + Criterion-1 was not.**
    **CONCLUSION:** residual co-movement is a viable Phase-1 detection basis **on EXISTING data (the
    already-built Polygon EOD — no new ingestion source)**, so **10-K Item-1 parsing is NOT required for
    DETECTION** (it may at most assist driver-NAMING, i.e. support Criterion 1 — re-scope it that way if
    at all). Conditions: **Criterion-1 driver-naming is LOAD-BEARING (not optional)** — without it the
    detector ships blobs as themes; and Phase 1 needs a **more robust method than the throwaway** (broad
    universe not just overshoot, longer/multiple windows, principled cluster selection, explicit
    handling of the pervasive "speculative-beta" factor). **NEXT scoping step (before Phase 1):** re-run
    the co-movement method on the **BROAD universe + a longer window** — does it surface cleaner
    sector-spanning themes (AI-infra, GLP-1) when the winners are present, not only the distressed
    speculative complex? *Method caveat: no `POLYGON_API_KEY` in this worktree and committed snapshots
    hold only price FEATURES (not series), so the throwaway used free keyless Yahoo daily closes as a
    vendor-agnostic stand-in for Polygon EOD — daily closes are daily closes; the residual-co-movement
    answer is source-agnostic. Docs-only change; suite green: ruff + mypy --strict (66) + pytest (204
    offline).* Edge 2 stays the lead horse (§4 GOVERNOR); this parallel scoping did not starve overshoot
    verdict-logging.
  - **PHASE-0.7 — the GATE (broad universe + REAL Polygon source): GO — upgrades the 0.6 QUALIFIED GO
    (2026-06-25).** Tested whether 0.6 survives the universe themes actually live in AND the production
    source. Throwaway (deleted; all caches incl. `data/cache` cleared; finding in
    `theme_admissibility_spike.md` Part 3): **1,639 of the 1,727 broad `in_universe` names** (NOT the
    overshoot screen), 12mo daily from **Polygon via the EXISTING `PolygonEodClient`** (key from `.env`
    via `require_env`, Bearer header, **never printed/logged**; 252 days), R1=market+sector vs
    R2=+size+vol; SIC live from EDGAR for the cross-taxonomy test; regime = IWM **+39%** (a stringent
    risk-on year). **(1) FIDELITY:** Polygon reproduces Yahoo near-exactly — quantum RGTI↔QBTS **0.82
    (Yahoo-0.6 was 0.81)**; vendor sensitivity negligible. **(2) RELIABILITY-AT-SCALE = YES** (the open
    0.6 question): 48 clusters @τ0.5, **56% cross ≥2 SIC**, top ones cleanly **nameable** — **US housing
    (14 SICs / 5 sectors: builders + lumber + flooring + furniture — the cross-taxonomy win SIC can't
    produce), hotels+lodging (REIT + operator), staffing (5 SICs), shipping, regional banks, gold
    miners, commodity chemicals, trucking** — MANY themes, not the lone-quantum case; and the
    cross-taxonomy clusters are nameable, not the driver-less blobs the overshoot universe produced.
    **(3) SPECULATIVE FALSE-DRIVER = handle-able, two independent ways** (the 0.6 chief risk): (a) the
    broad universe **dilutes** it — the spec-beta complex was an OVERSHOOT artifact (distressed
    small-caps are disproportionately speculative); broad top-clusters are sober macro themes. (b) the
    **vol-factor strip MECHANICALLY DISSOLVES it** — at τ0.45 R1 still yields the 19-name spec blob
    (quantum + robotics + nuclear + eVTOL, NO single driver); **R2(+vol) collapses it to exactly
    RGTI/QUBT/QBTS** (real quantum survives, corr 0.82→0.79), while the real macro themes are robust to
    the same strip (genuine, not size/vol artifacts). So the false-driver is removed **before**
    driver-naming — Criterion-1 is never asked to reject "future tech." **⇒ GO: residual co-movement is
    a viable Phase-1 detection basis on EXISTING data via the already-built Polygon EOD client (NO new
    ingestion source); all three gating risks (fidelity / reliability / contamination) clear.** **Phase
    1 is now JUSTIFIED to build:** the `theme_admissibility.md` four criteria, clustering on residual
    co-movement (**market + sector + VOL stripped**) as Criterion-3-as-basis + **Criterion-1
    driver-naming as the human gate**. Build conditions: pair clustering with the vol/speculative-factor
    strip (the lever, not optional); a more robust method than the throwaway (principled cluster
    selection not a single τ, multiple/longer windows, significance); decide the run-universe (broad for
    theme discovery vs the overshoot set for "are these finalists a thematic co-derating?"). **Pre-req
    unchanged: the analyst signs off the `theme_admissibility.md` a-priori review before Phase 1.**
    10-K Item-1 parsing stays NOT-needed-for-detection (may at most assist driver-naming). **Scope
    caveat:** the $10B ceiling excludes mega-cap theme leaders (NVDA/LLY), so AI-infra/GLP-1 surface
    only as small/mid-cap expressions — the right universe for the overshoot fund. *Real Polygon quota
    consumed (accepted); `.env` git-ignored, key never committed/logged. Docs-only repo change; suite
    green: ruff + mypy --strict (66) + pytest (204 offline).* Edge 2 stays the lead horse (§4 GOVERNOR);
    parallel scoping, did not starve overshoot verdict-logging.
  - **PHASE-0.8 — the two load-bearing confounds RESOLVED: GO CONFIRMED (last pre-build spike;
    2026-06-29).** The 0.7 GO rested on two things its single test couldn't isolate; both now tested,
    both clear. Throwaway (deleted; all caches incl. `data/cache`; finding in
    `theme_admissibility_spike.md` Part 4); existing Polygon client, key from env. **TEST 1 — vol-strip
    SELECTIVITY (confound a):** is the strip selective, or does it just keep the tightest knot and kill
    diffuse themes too? Applied R1→R2(+size+vol) to three groups: **HOUSING (diffuse real, vol-pctile
    45)** survived — 22→18 connected @τ0.5, mean corr 0.37→0.35 (barely moved); **QUANTUM (tight real,
    vol-pctile 95)** survived 3→3 (0.76→0.71); **the 19-name SPEC-BLOB (fake, vol-pctile 88)
    DISSOLVED** — 19→[6,3,2,2,2,…] (fragment SIZES matching its real sub-themes — the blob holds exactly
    6 uranium names / 3 quantum / eVTOL; size→theme mapping inferred from membership, not separately
    printed). **⇒ SELECTIVE, not a threshold-raiser** — the discriminator is VOLATILITY
    (low-vol housing untouched; high-vol speculative GLUE removed, unbundling the risk-on amalgam into
    nameable sub-themes). Confound (a) CLEARED. **TEST 2 — REGIME fragility (confound b):** do themes
    recur in a different regime? A genuine drawdown window existed — **Window B 2021-11..2022-10, IWM
    −29%** (vs the 0.7 +39%). Re-ran market+sector+vol clustering on it (1,409 names; recent IPOs
    dropped): **HOUSING / GOLD / SHIPPING / HOTELS all RECUR** across the opposite regimes →
    **not residual-artifacts of the risk-on window.** Caveats: **banks did NOT recur** (regime-specific
    — reassuring, the method isn't mechanically re-finding identical clusters; bank co-movement genuinely
    differed 2021-22 vs 2025-26), and **quantum was untestable** (IPO'd post-Window-B) → tight-high-vol
    regime-robustness DEFERRED to Phase-1's multiple-windows condition, not assumed. Confound (b)
    substantially CLEARED (diffuse themes). **⇒ GO CONFIRMED** — residual co-movement (market+sector+vol
    stripped) + Criterion-1 driver-naming is a sound Phase-1 detection basis on existing data; the
    vol-factor strip is selective + load-bearing (keep it). **Phase 1 remains gated only on the analyst's
    a-priori sign-off of `theme_admissibility.md`** (the data-basis + method confounds are now resolved).
    *Real Polygon quota consumed (accepted); key from env, never logged; `.env` git-ignored. Docs-only
    repo change; suite green: ruff + mypy --strict (66) + pytest (204 offline).* Edge 2 stays the lead
    horse (§4 GOVERNOR); parallel scoping, did not starve overshoot verdict-logging.
  - **SIGN-OFF CHECKLIST WRITTEN (2026-06-29) — `docs/theme_admissibility_review.md`.** The walkable
    analyst review the four spikes gated on: per-criterion (state · concrete judgeable question · real
    spike evidence for/against), plus the **architecture revision** the spikes forced (co-movement-as-
    basis + criterion-1 validation, overturning the spec's §3 "never cluster on price") and the **two
    residual edges** surfaced for explicit acknowledgement — (1) the vol-strip is proven selective for
    low-vol macro themes but UNPROVEN for high-vol event-driven ones (may MISS real GLP-1/AI-infra-class
    themes); (2) emergent cross-taxonomy themes' regime-robustness is structurally FORWARD-only
    (untestable by backtest) — plus the carried caveats (cap-ceiling-as-validation-question,
    handful-not-56% real yield). **NOT self-approved** (machine proposes, human concludes). **Phase 1
    stays gated on the HUMAN walking the checklist and ticking a FINAL DECISION box** — un-ticked = not
    built. Docs-only; suite green (ruff + mypy --strict 66 + pytest 204 offline). Edge 2 stays lead.
  - **THREE SIGN-OFF RESOLUTIONS RECORDED (2026-06-29) — `theme_admissibility.md` §7 (+ §2 amended).**
    The a-priori review produced three analyst design decisions, now captured in the spec as Phase-1
    build requirements + forward-validation items (NOT spike work — the four-spike arc is complete):
    **(1) Strength/lifecycle signals** (resolves the "binary screen under-uses the machine" point, the
    most important) — the layer must ALSO surface machine-assessed momentum/relative-strength, breadth
    (expanding/contracting), crowding/over-extension as **human-judged INPUTS, never an auto-rank**
    (admissibility stays binary; §2 amended). **(2) Emergent-theme validation** (resolves Residual Edge
    2) — regime-robustness of quantum-class emergent themes is a **FORWARD** question via **analogy +
    text/attention footprint**, never backtest. **(3) Unprompted high-vol path** (resolves Residual Edge
    1) — a **separate detection path surfacing high-vol candidates UNPROMPTED** (guards silent
    false-negatives), NOT a circular hand-picked check. **Cross-cutting:** all three lean on
    **text/attention analysis** (a NEW news/transcript pipeline not in `vinci/`). **Phase 1 now gated
    on: (a) the human's FINAL sign-off** (review-doc decision block, still un-ticked) **and (b) two
    SCOPING decisions — text/attention in Phase 1 vs deferred to 1.5, and run-universe (broad vs
    overshoot)** — both the human's, NOT decided here. Docs-only; suite green (ruff + mypy --strict 66 +
    pytest 204 offline). Edge 2 stays the lead horse.
  - **PHASE 1 / STAGE 1 — Component A (co-movement theme-detection candidate-generator) — BUILT +
    VERIFIED (2026-06-29).** The first Phase-1 build (`vinci/themes/`, `vinci themes` CLI): residual
    co-movement clustering that PROPOSES candidate themes for the human to judge — it assembles the
    cluster + the candidate shared-linkage (the criterion-1 surface) + §7.1 strength/lifecycle signals,
    and **concludes nothing** (no driver named, no theme ranked against another, no verdict — a schema
    with no such field, AST-guarded like the ranker/dossier; imports no scoring/ledger). Pipeline:
    broad `in_universe` (~1,727, mega/mid included — NOT the overshoot set) → 12mo daily Polygon (the
    EXISTING `PolygonEodClient`, key from env, never logged) → **multi-factor residualization
    (market + sector + size + vol)** → residual-correlation connected-components (PRINCIPLED selection:
    a τ-band stability check + exact intra-cluster coherence, not a single hardcoded τ) → the
    four-criteria SCREEN (breadth / coherence / persistence PASS-FAIL; criterion-1 nameable-driver is
    the human's). **The genuinely new leg — the SECTOR de-confounding (G2's unbuilt sector leg, §2 G2
    caveat) — built PROPERLY:** a leave-one-out broad-sector cohort factor whose loading is ESTIMATED
    jointly by OLS (NOT the spikes' throwaway 1:1 cohort-mean subtraction), pure-Python (no numpy),
    regression-tested. Fail-loud throughout (insufficient history → dropped + counted, never a
    partial-window number; persistence un-evaluable on a too-short window → NOT-admitted, never a silent
    pass). All thresholds face-validity, never forward-return-tuned. *VERIFIED — the COMMITTED module
    reproduces the spike findings on real Polygon (ref 2026-06-17, 252 trading days, 1,713/1,727
    covered): QUANTUM residual corr RGTI↔QBTS **0.82** / RGTI↔QUBT 0.72 / QUBT↔QBTS 0.73 (= the spike
    numbers exactly); HOUSING is the cross-taxonomy cluster SIC dismembers (19 names / 12 SICs / 6
    sectors — builders + lumber + flooring + furniture); the **vol-strip is SELECTIVE** — diffuse
    low-vol housing SURVIVES (coh 0.36→0.37) while the speculative blob dissolves, the **uranium
    sub-theme crystallising cleanly under R2** (DNN/UEC/URG/UUUU/EU/NXE); plus shipping / gold-miners /
    regional-banks / hotels+lodging / staffing / commodity-chemicals / trucking, all nameable. Full CLI:
    40 clusters → 35 admissible (persistence gate rejects 4 blips + 1 low-coherence). 16 theme
    regression tests incl. the proper sector leg (β estimated, not 1), the vol-strip selectivity, the
    gates, the no-conclusion schema guard, the no-forward-returns AST guard, and the
    persistence-un-evaluable fail-loud case — the last from a pre-PR adversarial review (4 dimensions ×
    verify) that confirmed exactly 1 real defect (a persistence auto-pass on a short window), now fixed.
    ruff + mypy --strict (76) + pytest 253 offline green.* **Stages 2–4 PENDING (NOT built): Component C
    confirmation trigger (Stage 2); the semantic exposure-classifier / text ingestion (Stage 3);
    pipeline composition + forward paper-validation (Stage 4).** A PAPER-VALIDATION track; Edge 2 stays
    the lead horse (§4 GOVERNOR) — this did not starve overshoot verdict-logging.
    - **Post-build verification DIAGNOSIS (2026-06-29) — two findings, NO Stage-1 code change.**
      (1) **The §7.1 strength engine's first real output is CORRECT, not a bug.** Housing's
      rel-strength −50.5% reconciles EXACTLY against raw Polygon: the signal is
      median(member 12mo cumulative return) − IWM 12mo return; housing median **−11.5%** absolute
      (PRGO −61% … MHO +37%) − IWM **+39.0%** ($208.55→$289.88) = **−50.5%** — housing is a genuine
      laggard (flat-to-down while small-caps surged), decision-relevant. All four signals reconcile to
      4dp vs hand-computed (momentum −11.5%; breadth 1/19 = 0.053; crowding +3.3%). NOTE it is a
      TRAILING 12mo cumulative (same window as detection), not a short-horizon momentum — a possible
      future §7.1 enhancement (add a shorter momentum lookback for lifecycle), NOT a defect. (2)
      **IWM size-mismatch on mega-caps is MATERIAL — a STAGE-2 question, not a Stage-1 break.** This
      window IWM (+39%) outran SPY / Russell-3000 (+24% / +24%) by **−15pp**, a constant shift IWM
      adds to every rel-strength number. For the broad/mega-cap names a Stage-2 confirmation trigger
      measures, the size tilt is decisive at the margin (NVDA rel +3% vs IWM but **+18% vs SPY**;
      LLY +1.5% vs +16.5%) — benchmarking a mega-cap leader against a small-cap index under-credits it
      exactly when the trigger should fire. Stage-1 is NOT affected: its detected themes are sub-$10B
      (IWM size-matched), the spikes used IWM too, and R2 already strips the size factor from the
      CLUSTERING (the −15pp rides only the presented strength signal, a human-judged input).
      **PROPOSED (not built) — benchmark-per-universe in Stage 2:** sub-$10B holding-side signals stay
      IWM-relative; the mega-cap confirmation trigger uses a broad-market benchmark (SPY / Russell
      3000), size-matched to mega-caps. The spread is regime-dependent (inverts in a large-cap-led
      year), so size-matching the benchmark to the measured universe is the robust design, not a
      one-off adjustment. No Stage-1 module changed; suite stays green.
    - **§7.1 strength engine → 1/3/6/12mo TRAJECTORY vector (2026-06-29; resolves the Finding-1 design
      note). SIGNALS LAYER ONLY — detection / clustering / residualization / gates / linkage UNTOUCHED
      + re-verified.** momentum + rel-strength-vs-IWM are now presented as a four-horizon SHAPE the
      human reads (1mo now / 3mo quarter / 6mo half-year / 12mo trailing context — one horizon per
      decision timescale; a 5th answers no new question), NOT a single number and with **NO
      slope/composite/rank** (collapsing the vector re-destroys the shape + crosses the dead-signal
      line — a `Trajectory` schema with no such field, test-pinned). Same formula (median member
      window-return; rel = median − IWM), four windows; benchmark stays IWM (Finding-2's split is
      Stage-2's concern, untouched). **Fail-loud PER HORIZON:** a name without history spanning a
      horizon is UNKNOWN for it (real 1mo/3mo, UNKNOWN 6mo/12mo) — never a partial-window fabrication;
      breadth/crowding stay single values (recent/current-state, no natural horizon). *Verified — the
      committed CLI renders the shape; ALL FOUR horizons reconcile to 4dp by hand on housing (rel
      1mo +10.2% / 3mo −7.1% / 6mo −22.6% / 12mo −48.1%), and the shape is decision-relevant: housing's
      12mo −48% laggard is INFLECTING (1mo momentum +16%, rel +10%) — which the single 12mo hid. The
      per-horizon guard also FIXED a latent partial-window fabrication the old single-12mo carried:
      OPTU (a sub-12mo listing) was counted in the old 12mo; it is now UNKNOWN for 12mo (real 1/3/6mo),
      shifting housing's 12mo rel −50.5%→−48.1% — the more-correct number. Detection re-run identical
      (40 clusters → 35 admissible; housing 19-name/12-SIC + quantum unchanged, gate still passes); git
      diff touches only render/schemas/signals. ruff + mypy --strict (76) + pytest 255 green; +3
      trajectory tests (horizons+order, per-horizon fail-loud, no-collapse schema guard).*
    - **STAGE 2 / Components B + C — theme-type signals + megacap confirmation (2026-06-29). READ-ONLY
      over A; A's detection / clustering / residualization / gates / linkage UNTOUCHED + re-verified
      (zero git diff on those files).** New `vinci/themes/{leaders,classify,confirmation,stage2}.py` +
      a `themes-stage2` CLI. **SUB-STEP 0 — leader designation:** A's $10B-capped clusters contain NO
      mega-caps, so the >$10B leaders (whose pattern B reads, whose run C confirms) are ASSEMBLED from
      a read-only >$10B operating-co slice (reusing `build_universe`; A's universe untouched) — a
      mega-cap is a candidate leader iff its SIC ∈ the cluster's classes AND it residually CO-MOVES
      with the cluster (the same test that defined the theme); the machine assembles, the analyst
      RATIFIES (criterion-1). Mega-caps never enter detection or holding. **Component B** (type signals
      fused into criterion-1, NO auto-classification): leaders-vs-members price-pattern
      (leader-first / synchronous / mixed via the trajectory machinery), vol-strip-survival (from A),
      an LLM historical-analog (§7.2 reference class, source-bound, proposed), and an explicit DEFER
      state ('TYPE-AMBIGUOUS → watch, do not fire') — the human judges type. **Component C** (megacap
      confirmation SIGNAL the human reads to act, NOT an autonomous trigger): leaders' median
      cumulative return-from-baseline at +20/+30/+50 × {absolute, vs-IWM, vs-SPY}, scoped to
      human-judged-emergence. **FORWARD BASELINE chosen + recorded:** the start of A's trailing
      detection window (contemporaneous, no hindsight inception; the live form of 'since first
      surfaced in detection' — replaces Part-7's hindsight Part-5 inception). *VERIFIED on real Polygon
      (committed CLI, 39 themes): leader designation surfaces the REAL mega-caps (housing
      HD/LOW/DHI/PHM/NVR/TOL co-move 0.35-0.44; gold NEM/AEM/Barrick… 16 names 0.36-0.53; banks
      PNC/USB/TFC… 15 names; shipping → NO co-moving leader → DEFER). B price-pattern DISCRIMINATES —
      banks read SYNCHRONOUS (cyclical), others MIXED; leader-first is proven by unit test (no sub-$10B
      EMERGENCE theme exists in A's current universe — the AI-infra enablers grew >$10B, the
      Finding-2/Part-7 reason, recorded honestly). C confirmation reconciled BY HAND to 4dp (gold
      leaders' median return-from-baseline +0.7175 = grid absolute; vs IWM +0.3275; vs SPY +0.4775).
      The DUAL-BENCHMARK grid reproduces Finding-2's −15pp EXACTLY (vs SPY − vs IWM = +0.1499 = IWM
      +39% − SPY +24%) and is DECISIVE at the margin — hotels confirm at +20% vs SPY (+34.1%) but NOT
      vs IWM (+19.1%); banks read vs-IWM −4.4% (laggard) vs vs-SPY +10.6%. B.3 LLM analog (opus-4.8)
      assembled a real housing reference class (2004-06 bubble / 2007-09 collapse / 2020-21 boom /
      2022-23 rate-freeze / lumber 2021 / 2012-15 recovery) + what to check, proposed-not-concluded.
      ruff + mypy --strict (80) + pytest (263; +9 Stage-2 tests: leader-designation, price-pattern
      discrimination, defer, forward-baseline, dual-benchmark grid, no-conclusion schema guard) green.*
      (signals.py gained a backward-compatible `min_members` param for the single-leader trajectory —
      A's strength signals byte-unchanged.) **Stages 3-4 PENDING: the semantic exposure-classifier /
      text ingestion (Stage 3 — the unsolved enabler-SELECTION from Part 6/7, where winners and losers
      look alike at confirmation); pipeline composition + enabler-search wiring + forward
      paper-validation (Stage 4).** Edge 2 stays the lead horse.
    - **DIAGNOSTIC (2026-06-29; Part 3 RUN & COMPLETED 2026-06-30) — why Stage 2 surfaced only cyclical
      themes: HYPOTHESIS A (the $10B DETECTION ceiling) primary, C (the breadth gate) secondary. NOT
      B-as-framed; the live Part-3 run surfaced a DISTINCT leader-designation SIC-gate defect (B′). No
      code change.**
      Tested the claim "no sub-$10B emergence theme exists" against the strong prior that emergence is
      always in play. **(0) signals.py backward-compat PROVEN** (the deferred Stage-1.5 check): housing's
      1/3/6/12mo momentum + rel-strength are IDENTICAL to 4dp post-`min_members` (1mo +0.1639/+0.1020 …
      12mo −0.0909/−0.4809) — **A byte-unchanged.** **(1) ALL clusters incl. sub-breadth:** 108
      components ≥2 names; **68 are 2-name pairs the breadth gate filters**; the borderline ones are
      overwhelmingly CYCLICAL (staffing / RV / offshore-drilling / refiners / net-lease-REIT / airlines /
      insurance / banks) — a few early-emergence-ish (biotech modalities WVE/KYMR/GPCR coh 0.73 = a small
      ADMISSIBLE cluster; semicap pair VECO/ACLS coh 0.82 = breadth-FILTERED). **(2) DECISIVE — current
      caps of LIVE mid-2026 emergence enablers (Polygon, external check, not the detector's output):** the
      AI-infra picks&shovels are **100% ABOVE** the $10B ceiling (VRT $122B, GEV $282B, COHR $74B, LITE
      $68B, ALAB $64B, CRDO $46B, CLS $44B, NVT $28B, SMCI $17B, MOD $15B, POWL $11B — **zero** sub-$10B);
      space (RKLB $63B) + nuclear leaders (CCJ $46B, OKLO $10B) + IONQ $20B also grew out. The sub-$10B
      emergence presence is NARROW: **quantum (RGTI $6.7B / QUBT $2.2B / QBTS $8.4B — DETECTED as a
      cluster)** + eVTOL/drones (JOBY $9.2B / ACHR $4B / AVAV $8.3B / RCAT / ONDS — but a 2-name pair
      JOBY/ACHR, breadth-FILTERED) + tiny nuclear-fuel (NNE $1.3B / LTBR $0.3B). Tally: sub-$10B 11 /
      $10-50B 10 / >$50B 6+ (10 no-cap, mostly recent-IPO/foreign and also large). **(3) RUN-VERIFIED (Part 3, 2026-06-30 — reasoned-only on 06-29):** quantum (RGTI/QBTS/QUBT + INFQ;
      coh 0.66, breadth 4 → ADMISSIBLE-size) IS a detected sub-$10B cluster. Component B reads it
      **'no co-moving mega-cap leaders → cannot be read' (DEFER)**, NOT 'cyclical': the >$10B quantum
      leader IONQ ($20B, SIC 7373) is EXCLUDED by leader-designation's EXACT 4-digit SIC match vs the
      cluster's {7371,7372,7374} — a one-digit sibling miss inside the same 737x family. So B does not
      mislabel emergence; a too-strict leader-SIC gate (B′) leaves the one detected sub-$10B emergence
      theme un-confirmable (no leader → no leader-first/synchronous read).
      **VERDICT:** "no sub-$10B emergence theme" is an OVERSTATEMENT — quantum is a detected counterexample
      — but the STRUCTURAL truth is **HYPOTHESIS A**: the $10B DETECTION ceiling selects against MATURE
      emergence enablers, which grow into $10-50B by the time the theme is broadly detectable (AI-infra
      entirely above the band). **HYPOTHESIS C is secondary** (the earliest emergence themes are 2-name
      pairs the breadth gate filters — eVTOL JOBY/ACHR, semicap VECO/ACLS coh 0.82, nuclear-fuel
      NNE/LTBR). **NOT B-as-framed (no mislabel-to-cyclical); but B′ — the leader-designation EXACT-SIC
      gate excluding IONQ — is a real defect the live Part-3 run surfaced.** *PROPOSED (NOT
      implemented): (A) raise the theme-DETECTION ceiling (e.g. ~$50B), SEPARATE from the sub-$10B HOLDING
      ceiling — "detect broad" must mean broader than $10B since the enablers grow out; the Stage-2 >$10B
      leader-slice already proves the machinery extends cleanly to that band, so DETECTION could reuse it.
      (B′) LOOSEN leader-designation SIC-match from EXACT 4-digit to the 3-digit major group (or the
      existing sector map) so IONQ 7373 matches the 737x quantum cluster — else a DETECTED sub-$10B
      emergence theme silently DEFERs for lack of a leader (the live Part-3 finding, the load-bearing
      new evidence vs the 06-29 reasoned pass).
      (C) a NARROW breadth-gate exception for high-coherence cross-taxonomy emergence PAIRS, gated on
      emergence-type signals (carefully — criterion 2: a pair is usually a relationship, not a theme).
      This REFINES the "detect broad / hold sub-$10B" scoping decision: the binding constraint is the
      DETECTION ceiling, not the holding ceiling. Diagnostic only; no detection/B/C/universe change;
      suite unchanged (Part 0 is a re-run).*
    - **B′ FIX — leader-designation SIC match loosened EXACT-4-digit → 3-DIGIT industry group
      (2026-06-30, branch `fix/theme-leader-sic-3digit`). The B′ defect the diagnostic surfaced is
      fixed; A's detection + the cyclical leaders UNTOUCHED.** `designate_leaders` (leaders.py) now
      matches a candidate's 3-digit SIC group, not the exact 4-digit class — FACE-VALIDITY (7371/7372/
      7373/7374 are one "computer services" family), NOT a return-tune; git diff isolated to that gate +
      its docstrings/rule. **SAFE because of the SECOND gate (co-movement ≥0.30), VERIFIED on real
      Polygon — not assumed:** the widening makes 43 737x mega-caps quantum CANDIDATES (MSFT $2.8T, ORCL,
      CRM, NOW, ADBE, INTU…); the co-movement gate REJECTS all 42 false leaders (median residual corr
      −0.09…+0.09, all <0.30) and DESIGNATES only IONQ (+0.649) — the second gate filters what the
      widening's breadth would otherwise admit. **THE UNBLOCK (real run): quantum (RGTI/QBTS/QUBT/INFQ),
      previously silent-DEFERRED, now flows END-TO-END through B+C:** (1) IONQ designated leader (SIC
      7373, $20B, residual corr +0.649); (2) Component B reads a REAL pattern — **MIXED/UNSTABLE
      (choppy)**, not 'no leader → cannot be read' — leader/member 1/3/6/12mo trajectory reconciled to
      4dp (leader 3mo +0.7144 / 6mo +0.1011 vs members +0.3728 / −0.1331 → no clean leader-first gap,
      honestly choppy); (3) Component C confirmation grid — IONQ median +0.4377 from the forward baseline
      = +0.0477 vs IWM / +0.1977 vs SPY (clears +20%/+30% ABSOLUTE only, neither benchmark-excess),
      dual-benchmark spread +0.1499 = Finding-2's −15pp — every cell reconciled BY HAND to 4dp. The
      participation edge has its FIRST testable sub-$10B emergence target (B presents, human judges — no
      machine verdict). **VALIDATION:** cyclical leaders UNCHANGED — housing (DHI/HD/LOW/NVR/PHM/TOL),
      gold (16: AEM/NEM/FNV/WPM/…), banks (15: PNC/USB/TFC/…) IDENTICAL to the 4-digit era, 3-digit added
      ZERO new leaders; A's detection untouched (fix is downstream). Regression test pins 3-digit match +
      the spurious-leader-REJECTED-by-co-movement guard. ruff + mypy --strict (80) + pytest (264; +1
      guard) green. **Hypothesis A (detection ceiling) + Hypothesis C (breadth-gate exception) stay
      recorded findings pending separate decisions — only B′ is fixed here.**
    - **BREADTH emergence-target scan (2026-06-30) — across ~45 live emergence themes the binding
      constraint is GATE 2 (co-movement/breadth), NOT the $10B ceiling (Hyp A); NO clean valid sub-$10B
      leader-first target currently qualifies. Diagnosis only, no code change.** Enumerated TWO ways to
      defeat enumeration bias: Direction-1 top-down web research (10 parallel agents, live mid-2026, all
      sectors, ~250 enabler tickers) + Direction-2 bottom-up from the 108-component census; each theme
      run through the B′-fixed 4 gates (caps from Polygon, B/C from committed code). **Scorecard pattern
      (where ~45 themes fall out):** Gate-1 "grown out of $10B" is RARE (2: AI-compute/EMS, fusion) —
      most themes DO have sub-$10B baskets (Part-5 holds). The wall is **Gate 2: ~29 themes' sub-$10B
      enablers don't residually co-move at τ=0.50** (heterogeneous sub-segments / idiosyncratic
      clinical-or-pre-revenue risk / <12mo IPO history), and **9 co-move only as breadth-FILTERED pairs**
      (semicap VECO/ACLS, crypto-miners→AI CLSK/MARA, eVTOL JOBY/ACHR, gene-edit CRSP/BEAM, nuclear-fuel
      LTBR/NNE, neuro CYTK/MLYS, hydrogen PLUG/BLDP, solar-inverters SEDG/ENPH, drones RCAT/UMAC). Of the
      5 that cluster ≥3, quantum / uranium / RNA(WVE/KYMR/GPCR) read **MIXED** (choppy like quantum) and
      precision-onc has no co-moving leader. **VERDICT — valid sub-$10B leader-first target right now:
      effectively NONE.** Exactly one passes all four MECHANICAL gates — **solar modules/cells**
      (CSIQ/DQ/JKS, leader FSLR leader-first, C +0.38 vs IWM / +0.53 vs SPY) — but it is a **US-vs-China
      tariff DIVERGENCE** (FSLR protected, Chinese solar distressed), not an emergence lead-lag whose
      sub-$10B names play the leader → the analyst would DECLINE (assemble-not-conclude working). Closest
      runners-up are the two leader-first+confirming pairs breadth-filtered out: semicap VECO/ACLS (leader
      LRCX) and crypto-miners→AI CLSK/MARA (leaders IREN/WULF/CIFR/RIOT) — each still needs human scrutiny
      (real AI-semicap vs BTC/AI-pivot beta). **TWO GAPS:** the DETECTION gap (Dir-1 themes that never
      cluster) is large, dominated by Gate-2 "no co-movement"; the RECOGNITION gap (census clusters not in
      Dir-1) is small and almost all CYCLICAL (shipping/banks/housing/gold/REITs/education — correctly not
      emergence; a few borderline growth-services EPAM/GLOB, BAH/SAIC, PLXS/BHE). **WHAT THIS INFORMS
      (surface, do NOT decide A vs C vs Stage-3):** the participation edge is idle largely BY CONSTRUCTION
      — emergence themes exist in breadth but their sub-$10B expressions don't form tradeable leader-first
      baskets. Evidence points the binding constraint at **co-movement/breadth (Hyp C + a co-move/τ/
      short-IPO-history question)**, NOT the ceiling (Hyp A unlocks only the 2-3 grown-out AI-infra-family
      themes) and NOT yet Stage-3 (the semantic enabler-selector only bites once a theme clears gates 1-3,
      which almost none do). Highest-value next probe: a NARROW Hyp-C breadth exception would surface
      semicap + crypto-miners→AI for analyst judgment. Suite unchanged (diagnosis only; the B′-fix branch
      stays ruff+mypy+pytest green).
    - **SEMANTIC-EXPOSURE PROBE (2026-06-30) — reasoning-from-disclosure DISCRIMINATES the driver and
      SURFACES the enablers co-movement can't; strong evidence FOR Stage 3 as the EARLY-detection
      mechanism. Probe only, no code change.** Tested the two breadth-scan leader-first PAIRS as live
      cases for whether SEMANTIC exposure (not co-movement) is the right early basis — the temporal
      tension being that co-movement is intrinsically LATE (needs consolidation) while the edge's value
      is EARLY (Part-6 fork). **PART 1 — both are PAIR-BY-ARTIFACT, not thin themes:** semicap has ~10
      sub-$10B pure-plays that FRAGMENT by sub-segment (VECO/ACLS pair + UCTT/ICHR pair + CAMT/COHU/KLIC/
      AEHR/PLAB/PDFS each idiosyncratic — full-history, residualized, just don't co-move); crypto-miners'
      real-AI names ALREADY GREW OUT (IREN $20.8B / WULF $13.8B / HUT $13.4B / CIFR $10.8B / APLD $13.0B /
      RIOT $10.4B, all >$10B) leaving the sub-$10B co-moving pair CLSK/MARA = the BTC-beta LAGGARDS — so
      co-movement fires too late AND clusters the wrong (beta) names. **PART 2 — the FENCED LLM (committed
      AnthropicLlmClient Opus-4.8, source-bound to real 10-K/20-F text, verdict-free, reusing
      synthesis.py's pattern) READS the disclosures and DISCRIMINATES SHARPLY, INVERTING co-movement (as
      Part 6 showed keyword-text inverts):** CRYPTO driver-discrimination — **CIFR + WULF =
      binding-contracts-with-terms** (CIFR: 15-yr AWS ~300MW + Fluidstack 300MW + 3.4GW pipeline; WULF:
      Fluidstack 378+168MW 25-yr leases + Core42, 522MW contracted) vs **CLSK = committed-capacity, no
      tenant** vs **MARA + IREN = aspirational-intent-only** (MARA AI 'early-stage evaluation'; IREN
      states an HPC strategy, no named tenant in its 10-K). The REAL-AI names (CIFR/WULF, binding
      hyperscaler MW) are exactly the ones that re-rated >$10B; the co-movement cluster (CLSK/MARA) is
      the aspirational BTC-beta residue — co-movement CANNOT tell pivot from beta, disclosure-reasoning
      CAN. SEMICAP exposure-completeness — the co-moving pair **VECO/ACLS read aspirational** (ACLS 98%
      ion-implant / 55% power-EV — not the AI driver; VECO diversified, no AI revenue split), while the
      genuinely AI-exposed names are **CAMT (~50% of revenue from AI-application production: HBM +
      advanced packaging, quantified) and AEHR (AI burn-in, packaged-part $19.8M / 34%)** — both sub-$10B
      and HOLDABLE, both flagged 'idiosyncratic / don't co-move' by detection. So exposure-reasoning
      surfaces BETTER sub-$10B targets (CAMT/AEHR) than co-movement found (VECO/ACLS), and inverts the
      signal. **VERDICT:** on both live cases semantic exposure-reasoning demonstrably does what
      co-movement can't — (a) DISCRIMINATE real driver-exposure from beta/marketing, (b) SURFACE real
      sub-$10B enablers that don't yet co-move. This RESOLVES Part 6's open fork ('semantic LLM-exposure
      untested — the key open path') in FAVOUR of the semantic path, and points the early-detection
      mechanism at **reasoning-from-disclosure, NOT co-movement.** *PROPOSED (NOT decided): Stage 3 (the
      semantic exposure-classifier) is the validated next-build direction — as the PRIMARY EARLY-detection
      basis (read the business → infer theme-exposure → source-bind → human judges), reusing synthesis.py's
      fenced / cite-checked / verdict-free machinery, NOT merely enabler-selection inside an
      already-confirmed theme. CAVEATS: a PROBE (n=5 miners + 6 semicap, latest-annual-only — IREN's
      aspirational read is a timing artifact, its big deals postdate the filing); it proves
      DETECTION-discrimination, NOT the forward edge (the paper track is the arbiter). Build-which-edge
      stays the human's.* Suite unchanged (probe only; the B′-fix branch stays green).
    - **STAGE 3, BUILD 1 — the SEMANTIC-PRIMARY exposure detector (scale-discrimination test on the
      AI-datacenter driver). Discrimination SURVIVES the flood at a 1% false-positive rate; a NEW
      early-detection path PARALLEL to A's co-movement — detection/B/C/co-movement UNTOUCHED.** New
      `vinci/themes/exposure.py` (+ `ExposureAssessment`/`ExposureFact` schemas, a `themes-exposure`
      CLI, 8 tests). Reuses synthesis.py's ARCHITECTURE (fenced LLM, verdict-free tool, cite-check) NOT
      its task: reads each name's RECENT DISCLOSURE STREAM (latest annual BUSINESS section + latest 10-Q
      MD&A/subsequent-events + recent 8-Ks — the IREN lesson: confirming hyperscaler contracts arrive as
      8-Ks, not the stale annual) and the fenced Opus-4.8 assembles source-bound exposure facts.
      **`exposure_basis` is DERIVED from the CITED facts' max concreteness** (binding-contract >
      quantified-revenue > committed-capacity > stated-intent > none), NOT trusted from the LLM — no
      cited concrete fact → none (fail-loud; a mention is NOT exposure). Assemble-not-conclude: NO
      score/rank/membership/buy field (schema-guarded). **GROUND TRUTH reproduced from the recent
      stream:** the 4 binding/quantified reals surface (CIFR/WULF binding hyperscaler leases, CAMT
      quantified ~50% HBM, IREN binding — the recent-stream reader FIXED the probe's annual-only IREN
      miss), the 4 betas reject (CLSK/MARA/VECO/ACLS → aspirational/committed, not REAL). One principled
      precision refinement (binding = a NAMED PAYING customer/tenant, not a development/financing JV — so
      MARA's tenant-less Starwood JV reads committed, not binding): face-validity, NOT return-tuning.
      **THE SCALE TEST (real Polygon/EDGAR/Opus-4.8, committed code):** the keyword FLOOD is massive —
      **1358/1727 (79%) of the sub-$10B universe mention 'artificial intelligence' recently** (Part-6
      inversion at scale: 'AI' is non-discriminating). Stratified scan of 261 = all 141 hardware/HPC-
      phrase names (recall) + a random 120 of the 'AI/data-center'-only flood (FP denominator) + the 6
      ground-truth. **RESULT — discrimination SURVIVES:** flagged REAL (binding+quantified) = 13/261
      (5%); basis dist none 175 / aspirational 64 / committed 9 / binding 8 / quantified 5. **FALSE-
      POSITIVE rate on the cheap-mention flood = 1/120 = 1%** (the lone flood flag is HIMX, a borderline
      'image-sensors → AI market' over-attribution the human audits — it does NOT flag 300 names for
      saying 'AI'). The 13 REAL are dominated by genuine AI-datacenter exposure — CORZ/RXT/BLZE binding
      CoreWeave / GPU-cloud contracts, CAMT 50% HBM, WYFI/BTBT WhiteFiber HPC, DGXX colocation, TSSI rack
      integration — with ~4 borderline (KOPN/FCEL/HIMX/LWLG) for the analyst to audit; 0 LLM errors
      (fail-loud, none fabricated). **SCALE VERDICT: semantic discrimination SCALES** — it surfaces the
      real enablers and rejects the 79%-'AI' flood at a 1% FP rate, producing a tractable, source-bound,
      auditable flagged set. Strong evidence that semantic-primary detection is VIABLE as the early
      mechanism (resolving Part-6's fork in its favour, at scale). ruff + mypy --strict (81) + pytest
      (272; +8 exposure tests) green. *CAVEATS: a build-1 scale test (stratified 261 of 1383 candidates;
      FP measured on a 120-name flood sample; ~30% of the REAL set is borderline-for-audit; AEHR
      conservatively read aspirational; LLM stochastic at the margin). Proves DETECTION-discrimination at
      scale, NOT the forward edge (the paper track is the arbiter). PROPOSED — build 2 (NOT built, GATED
      on this passing, which it did): the FULL multi-driver universe scan (all ~1383 candidates ×
      multiple drivers, batch infra) + a precision pass on borderline REAL flags (is the contract/revenue
      driver-SPECIFIC?). Detection/B/C/co-movement untouched — semantic-primary is a parallel path.*
    - **STAGE-3 build-1 AUDIT-PREP + STABILITY finding (2026-06-30). Build-1's scan persisted only a
      SUMMARY (not the full model_dump) — a PERSISTENCE GAP that blocked an independent citation audit
      and forced a recovery re-run. Two findings + a remediation; no classifier/grading change.** **(1)
      DRIFT / stability:** a full-persistence re-run of the 13 REAL names reproduced **10/13** grades —
      the **9 CONFIDENT names are STABLE** (CORZ/RXT/BLZE/DGXX/TSSI/WYFI binding, BTBT/DUOT/CAMT quantified
      all reproduced), but **3 of the 4 BORDERLINE flipped REAL→not-real** (KOPN binding→committed, LWLG
      quantified→aspirational, HIMX quantified→none — the flood-FP confirmed a STOCHASTIC artifact). So
      the ROBUST REAL set is ~9-10, NOT 13; the borderline flags are LLM-stochastic at the margin — a
      real precision caveat on any single run (the confident/borderline split from build-1 held up). **(2)
      Citation integrity:** all **55 graded facts across the 13 carry a real accession PRESENT in the
      name's stream — 0 out-of-stream, 0 UNCITED, 0 fabrication** (the cite-check / source-binding holds).
      Recovered citations are audit-grade (e.g. CORZ CoreWeave 16→590MW 10-K acc 0001628280-26-013305;
      DGXX Cerebras 40MW/$1.1-2.5B 8-K acc 0001213900-26-053566; CAMT 50%-AI/HBM 20-F acc
      0001178913-26-001561) and split ANNUAL vs RECENT-8K/10-Q — the recent-8K reads (RXT AMD, BLZE/WYFI,
      DGXX, FCEL) are LOAD-BEARING (the IREN-lesson recent-stream reader earns its keep). **(3) REMEDIATION
      (recorded, NOT built here): the scan should persist the full `ExposureAssessment.model_dump()`
      (facts + concreteness + source_ref + stream_refs) so results are audit-grade WITHOUT a re-run.**
      Audit-prep only — the build-1 CLAIM (its grades) is unchanged; the re-run only recovered citations +
      measured drift. Exports: build1_13name_{stream_filings,audit_table}.csv + _rerun.json (scratchpad
      handoff, not committed). Suite unchanged (no code touched).*
    - **INDEPENDENT SOURCE AUDIT of build-1 (2026-07-01) — semantic-primary VALIDATED as a DIRECTION;
      build-1's "13 REAL" is the OPTIMISTIC CEILING, the audited truth is 7 REAL / 4 borderline / 2
      not-real; ZERO fabrications; a CHARACTERIZED, CORRECTABLE, human-catchable UPWARD bias.** The
      load-bearing external check: an analyst source-verified each of the 13 build-1 REAL flags against
      its actual EDGAR filing (price-blind, human-judged — NOT the classifier re-checking itself).
      **Verdicts:** REAL (7) = CORZ, BLZE, DGXX, TSSI, WYFI, BTBT, CAMT; BORDERLINE (4) = RXT, DUOT,
      KOPN, FCEL; NOT-REAL (2) = LWLG, HIMX. (Of the 9 confident+stable names: **7 REAL, 2 downgrade
      (RXT, DUOT), 0 not-real**; every borderline/drifted name broke toward the LESS-generous run — the
      re-run was closer to truth.) **ZERO fabrications** — every checkable grade-determining fact was
      present in its filing (KOPN "Fabric AI" vs "StableX" = an inconsistency in Kopin's OWN filing, not
      a classifier fabrication; 3 secondary/corroborating facts cited non-XBRL filings [DGXX 10-Q + SubQ
      8-K; LWLG Dec-2025 offering] = unverifiable but NONE load-bearing). **THREE error modes, ALL
      UPWARD (over-grades at the margin): (1) LABEL-AS-THING** — reads a document's label as its
      substance (RXT "definitive GPUaaS Master Terms" is a FRAMEWORK, pricing subject to further
      agreement, AMD only backstops unsold capacity under a cap — not contracted revenue; DUOT "Technology
      Solutions revenue" is BLENDED, the real AI piece is a FUTURE GPUaaS build). **(2) INDIRECT
      DRIVER-TIE** — real binding contract, stretched tie (FCEL binding CEPA up to 380MW fuel cells "for
      data center applications" but POWER-equipment, generic "data center", only 30MW firm — terms-binding
      ALONE would pass; the driver-tie fails). **(3) BROAD-AI OVER-ATTRIBUTION** — endpoint/adjacent AI
      read as datacenter (HIMX = 80% display-driver ICs, "AI" = EDGE/endpoint [the OPPOSITE of datacenter];
      datacenter/GPU/HBM/server all = 0 in its 20-F — the flood FP, confirmed). **PRECISION-FIX SPEC (the
      3 type-appropriate discriminators):** NOT "named customer" — TSSI/WYFI/CORZ are REAL with ANONYMIZED
      customers because the TERMS bind (min-volume/make-whole/TCV/prepayment/executed order forms); a
      must-name rule would WRONGLY kill the EARLY, confidentiality-masked exposure the edge wants. (a)
      CONTRACTS: terms-binding vs DEFERRED (framework/sole-option/"subject to further agreement") [RXT
      fails]. (b) REVENUE: quantified + CHAIN-ATTRIBUTABLE vs blended/general [DUOT fails]. (c) DRIVER-TIE
      SPECIFICITY (both types): AI-datacenter-CHAIN vs indirect (generic power / edge-endpoint / "broad AI")
      [FCEL, HIMX fail]. **STABILITY ≠ CORRECTNESS:** FCEL was grade-STABLE across both runs yet audited
      soft — a stable grade can still overstate. Build-1 grades = the OPTIMISTIC CEILING, not a point
      estimate; the human/audit layer shaves the overstatements (machine-proposes / human-judges, working
      as designed); the confidence/drift signal is DIRECTIONALLY calibrated but not perfect. **CAMT /
      UPSTREAM-ENABLER SCOPE DECISION (analyst call):** CAMT REAL — ~50% HBM/advanced-packaging metrology
      revenue is genuine quantified exposure to a critical, non-substitutable AI-datacenter input at the
      semi-equipment LAYER. **DECISION: upstream enablers ARE IN SCOPE** (the edge's structural advantage —
      real, non-obvious, under-covered, invisible to keyword/co-movement because they don't look like
      datacenters). **CONSEQUENCE: the driver expands from "AI-datacenter" to the AI-datacenter VALUE CHAIN**
      (chips → HBM/memory → packaging → thermal → power → optical → operator) — cross-layer exposure to ONE
      driver, semantically coherent but taxonomically scattered, groupable ONLY by semantic reasoning
      (semantic-primary in its strongest form). **VERDICT: semantic-primary VALIDATED as a direction** —
      it discriminates real exposure from the 79% "we do AI" flood (7/9 confident REAL, 0 fabrications,
      calibrated uncertainty) with a characterized correctable upward bias. **NEXT: precision-fix (the 3
      discriminators) BEFORE the multi-layer scale-out, so the scale-out inherits the corrected classifier;
      validation target = reproduce the audited 13 (the 7 REAL, RXT/DUOT/KOPN/FCEL→borderline,
      LWLG/HIMX→not-real).** Forward edge NOT claimed — validates detection-DISCRIMINATION, not that exposed
      names outperform (the forward paper track is the only arbiter). Audit is external/analyst-judged; no
      code change.*
    - **PRECISION-FIX (2026-07-01) — 3 TYPE-APPROPRIATE discriminators correct the audit's 3 upward
      error modes; the refined classifier reproduces the audit on 10/13 (11/13 on the load-bearing
      REAL-vs-not-REAL binary), pulling build-1's 13-REAL optimistic ceiling down to ~6-7 REAL ≈ the
      audited 7. Grading logic ONLY; detection/B/C/co-movement/universe UNTOUCHED.** exposure.py now
      grades each fact on TWO INDEPENDENT axes: **concreteness** (TYPE-appropriate — binding = the TERMS
      BIND [executed order form / min-volume / take-or-pay / make-whole / TCV / prepayment], NOT a
      framework / 'subject to further agreement' / sole-option / backstop; quantified = quantified AND
      CHAIN-ATTRIBUTABLE, NOT blended) and **driver_tie** (a SEPARATE gate: chain-layer-specific vs
      indirect vs not-driver). The exposure_basis derives from the max EFFECTIVE rank — an INDIRECT tie
      caps at committed-capacity, a NOT-DRIVER tie caps at stated-intent (new `_effective_rank`). New
      `DriverTie` schema + a `--out` model_dump-JSONL persistence (audit-grade going forward, no re-run —
      the audit-prep remediation). The driver is now the **AI-DATACENTER VALUE CHAIN**
      (chips→HBM→packaging→thermal→power→optical→operator→AI-cloud; UPSTREAM ENABLERS IN SCOPE). Guard:
      NEVER require a named customer — anonymized-but-terms-binding is REAL. **VALIDATION vs the audit's
      13 (real run, committed code): 10/13 categorical, 11/13 REAL-vs-not-REAL. All 3 discriminators
      demonstrably FIRE:** terms-binding downgrades RXT (framework) + DUOT (blended) to committed while
      CORZ/BLZE/DGXX/WYFI stay binding-REAL; the **DRIVER-TIE gate INDEPENDENTLY catches FCEL** (terms
      bind → committed via `indirect` — proving gate 1 is not subsumed by terms); the value-chain scope
      keeps CAMT REAL (upstream, quantified+chain) and drops HIMX (edge/broad-AI → not-real); the
      anonymity guard keeps WYFI REAL. **3 residual MISSES, reported honestly (NOT tuned away — that
      would overfit the 13):** TSSI over-killed (audit REAL → borderline, a strict terms-read; the OTHER
      anonymized case WYFI passed), KOPN over-graded (audit borderline → REAL, a $15M JDA read as
      binding), LWLG committed-vs-aspirational (BOTH not-REAL — not even a binary miss). The misses are
      marginal, STOCHASTIC terms-reads at the boundary — the human-audit layer still shaves them
      (machine-proposes / human-judges). Regression tests pin each discriminator (indirect-tie caps,
      not-driver caps, anonymized-but-binding stays REAL, missing-tie fail-closed). ruff + mypy --strict
      (81) + pytest (276; +4 discriminator tests) green; git diff isolated to exposure.py grading +
      schemas + the --out one-liner + tests. **THIS refined classifier goes into the multi-layer
      scale-out (build 2), now GATED-OPEN.** Forward edge NOT claimed — detection-discrimination only.*
    - **STAGE 3, BUILD 2 — the SEMANTIC-PRIMARY VALUE-CHAIN UNIVERSE SCAN (the scale-out of the
      precision-fixed classifier). The whole sub-$10B universe on ONE composite driver — the AI-
      datacenter VALUE CHAIN. The classifier reproduces the INDEPENDENT AUDIT on 13/13 EMBEDDED in the
      1,550-name scan (REAL set == the audited 7 exactly), and the scale-out surfaces NEW cross-layer
      enablers co-movement/keywords can't group. Detection/B/C/co-movement/universe/holding-ceiling
      UNTOUCHED — semantic-primary is a parallel path.** exposure.py's pre-filter broadened 8→**18-term
      value-chain vocabulary** (data-center/GPU/HBM/packaging/liquid-cooling/switchgear/optical/neocloud/
      …) + new `chain_layer_of` (a keyword PROVENANCE tag, not a grade) + `grade_driving_fact` (the
      basis-setting fact) + a WIDE-FUNNEL CLI (surfaces every name with ANY chain-attributable signal;
      NO confidence/rank — the human triages legible provenance). **THE HARD SCOPE PROBLEM (wide funnel
      vs pre-filter recall), resolved + MEASURED:** a broad pre-filter over 1,727 → **1,550 candidates
      (90%)**; recall cost = **177 excluded (10%)**, spot-check of 15 = food/furniture/firearms/forms
      (CALM/CAG/GT/RGR/MLKN…), **zero chain enablers** — the broad vocabulary caught the chain; truly
      text-silent names (zero chain vocabulary) remain the one documented limitation (only a full-
      universe scan catches them; the excluded tail suggests near-empty). Flood confirmed: **'artificial
      intelligence' alone hits 1,508/1,727 (87%)** while chain-specific terms are rare (HBM 10, optical-
      interconnect 5) — the exact discrimination problem the semantic layer exists to solve. **THE SCAN
      (real EDGAR/Opus-4.8, committed code):** 1,550 candidates × the precision-fixed classifier, 6
      workers, **full `model_dump` persisted INCREMENTALLY** (audit-grade + crash-safe/resumable), **0
      scan errors, 0 fabrications** (every REAL fact carries a real accession in its stream). **THE
      VOLUME (the first-class deliverable — the input to the DOWNSTREAM calibration decision, NOT decided
      here):** WIDE funnel surfaced **450/1,550 (29%)** — by type: **binding 4 / quantified 3 (REAL = 7)
      / committed 56 / aspirational-intent 387 / none 1,100**; by chain layer (of 450): chips/GPU 154,
      colocation/operator 138, HBM/memory 80, power 42, optical 12, thermal 8, packaging 6, AI-cloud 5.
      **VALIDATION — the scaled classifier reproduces the audit:** embedded in the 1,550-scan it lands
      **13/13 of the audited names on the audited verdict THIS run** (the REAL set == the audit's exact 7
      = CORZ/BLZE/DGXX/TSSI/WYFI/BTBT/CAMT; RXT/DUOT/KOPN/FCEL→committed, LWLG/HIMX→aspirational) and all
      3 discriminators FIRE at scale (RXT 'GPUaaS Master Terms' framework→committed via terms-binding;
      DUOT blended→committed via revenue; FCEL→committed via indirect driver-tie; HIMX edge/broad-AI→
      aspirational). *Caveat: 13/13 is a CLEAN run — the precision-fix small-batch got 10/13; the
      committed↔aspirational boundary is LLM-stochastic (report both honestly, do not claim determinism).*
      **THE SCALE PAYOFF (why build-2 exists):** the scan surfaces NEW cross-layer enablers beyond the
      13 — taxonomically scattered, semantically coherent, groupable ONLY by reasoning — e.g. ADEA
      (hybrid-bonding/DBI packaging), COHU (active thermal management), AEHR (AI-chip burn-in test), CRK
      (gas-to-datacenter power w/ NextEra), FRMI (hyperscale power+AI campus), NRGV/NUAI (new
      colocation), OPTU (datacenter fiber NYC↔Ashburn), MXL (comms SoCs), WLDN (AI-datacenter power) —
      many NOT-yet-co-moving (the early-detection payoff co-movement structurally misses). **THE
      CALIBRATION DECISION (surfaced, DEFERRED — NOT decided here):** the ACTIONABLE tiers
      (binding+quantified+committed = **63**) are TRACTABLE for full human review → the human IS the
      triage, no machine layer needed there; the intent tier (**387** aspirational) is LARGE — IF the
      human mines it, a calibration/triage layer becomes a MEASURED (not assumed) need. **LIMITATIONS
      recorded:** (1) foreign issuers **18/450** read on staler info (20-F/40-F, no 8-K stream, e.g.
      CAMT); (2) text-silent recall gap (the 10% excluded, near-empty on spot-check); (3) LLM boundary
      stochasticity (13/13 vs 10/13); (4) build grades = OPTIMISTIC CEILING, the human-audit shaves.
      Assemble-not-conclude throughout (NO score/rank/verdict/buy — schema-guarded); machine PROPOSES,
      human JUDGES. ruff + mypy --strict (81) + pytest (**282**; +6 universe-scan-path tests: pre-filter
      skip-errors both ways, chain-layer tagging, grade-driving-fact, the value-chain driver) green; git
      diff isolated to exposure.py + cli.py + tests. Scan OUTPUT (JSONL/CSV) is NOT git-committed (not in
      the enumerated committable set — fail-closed); persisted durably to scratchpad + a Desktop handoff
      (scan_valuechain_1550.jsonl + surfaced_triage_450.csv + volume_report). **NEXT (gated on this
      VOLUME): the calibration/triage layer IF the human opts to mine the 387 intent tier; MULTI-DRIVER
      (robotics/GLP-1/nuclear) is a separate later build.** Forward edge NOT claimed — detection-
      discrimination AT SCALE, not that exposed names outperform (the forward paper track is the only
      arbiter). Edge 2 stays the lead horse (governor).*
  - **HOLDING-UNIVERSE study — sub-$10B-at-inception captured the theme return in all 6 themes tested
    (2026-06-29; `theme_admissibility_spike.md` Part 5).** A DISTINCT axis from the 4 detection spikes:
    does the **holding** bound (fund detects broad incl. mega leaders, but HOLDS sub-$10B) capture theme
    returns, or do they concentrate above $10B? **Backward DESCRIPTIVE market-structure study — NOT a
    backtest, NOT forward validation.** 6 themes × 3 types; cap measured **AT INCEPTION** (Polygon
    point-in-time market_cap via the existing client; the cap-timing crux — NVDA Jan-2023 $352B vs today
    $4.66T) not today's cap. **Finding: the sub-$10B-at-inception basket captured the theme return in
    ALL SIX and BEAT the >$10B basket in 5/6** — incl. the HARD tech-emergence case (AI-infra enablers
    VRT/CRDO/CLS/MOD/COHR/SMCI +1648% vs mega chips +955%, **6/6 grew through $10B**); defense sub +245%
    vs primes +56%; uranium entirely sub-$10B (no >$10B names existed); housing/gold sub-captures.
    **The feared "tech-emergence concentrates returns above the bound" hypothesis is REJECTED** — the
    theme is broader than its mega leader, and the sub-$10B enablers start small and grow THROUGH the
    bound (the bound catches them small, rides them up — ideal, not limiting). **REFRAME:** the binding
    constraint is NOT the holding bound (structurally fine across types) but whether **DETECTION can ID
    the sub-$10B enablers EARLY** — which the study ASSUMES (hindsight) and the forward track must prove.
    **HONEST LIMITATION (prominent):** heavily hindsight-prone (constituents picked knowing who won →
    sub-$10B return OVERSTATED), equal-weight buy-and-hold no-exit, small-n (GLP-1 noisiest/lottery),
    one data glitch (anomalous GOLD-symbol cap — likely a ticker/listing change, not verified;
    immaterial). **Suggestive structural evidence that
    INFORMS the holding-ceiling decision (toward "viable across theme types, KEEP") — does NOT settle
    it; the forward paper-track settles it** (do MY sub-$10B theme bets capture the return?). Existing
    Polygon client, key from env never logged; throwaway + caches deleted; docs-only; suite green (ruff
    + mypy --strict 66 + pytest 204 offline). Edge 2 stays the lead horse.
  - **EARLY-DETECTION FORK test — naive text/attention does NOT discriminate sub-$10B enablers from
    noise; it INVERTS (2026-06-29; `theme_admissibility_spike.md` Part 6).** The load-bearing test:
    Part-5's enabler return requires entering EARLY (pre-run, sub-$10B), but co-movement detection is
    structurally LATE; text/attention is the intended early mechanism. FORK = text surfaces enablers
    early+discriminably → build the differentiated sub-$10B enabler edge; else → MEGACAP theme fallback.
    Backward DESCRIPTIVE; AI-infra (sharpest case). WINNERS = Part-5 enablers (VRT/CRDO/MOD/COHR/CLS/
    SMCI) vs LOSERS = sub-$10B loud-AI-text flops (C3.ai/BBAI/VERI/SOUN/REKR — losers INCLUDED, the
    precision test). Signals measurable backward: EDGAR full-text theme-mention counts (disclosure) +
    Polygon news volume. **Result — BOTH fail: (1) PRECISION inverts** — early-2022 EDGAR 'AI' mentions
    winners mean 2.2 vs losers **15.6** (~7× louder); ALL 5 losers rank ABOVE all 6 winners; VRT (biggest
    enabler +2225%) had **0** → a loudest-text screen buys the losers, skips every enabler; news volume
    is coincident/lagging + size-confounded (loudest-news C3.ai flopped −8%). **(2) RECALL fails** —
    winners' AI-text silent through their run. **WHY:** the enabler's real driver-phrase was "data center"
    not "AI" (VRT 14/6/11 vs 0/0/1) — the enabler signal is a **SEMANTIC exposure-inference**
    ("data-center power = AI capex"), NOT a keyword the company emits; keyword-emitters were the
    self-promoting losers. **FORK VERDICT: lean MEGACAP fallback** — naive text is a theme-BUZZ detector,
    not an enabler detector. **Door not closed:** condemns KEYWORD/VOLUME text, not SEMANTIC text; an LLM
    EXPOSURE-CLASSIFIER (read business → judge theme-exposure, the fund's actual edge) is the UNTESTED
    path that could revive the enabler edge (Phase-1.5+, harder, not a cheap screen). **LIMITATIONS:**
    backward/judgment-heavy (some 'losers' SOUN/BBAI ran late on hype — reinforces 'text finds buzz';
    durable enablers were text-silent), 2 text facets only (semantic untested), single theme. Informs
    the build-WHICH-edge fork; forward track settles it. Existing Polygon client + EDGAR EFTS, key from
    env never logged; throwaway + caches deleted; docs-only; suite green (ruff + mypy --strict 66 +
    pytest 204 offline). Edge 2 stays the lead horse.
  - **A+B TIMING test — enablers LAG megacap confirmation for explosive themes (capturable window), but
    theme-type-specific + selection still unsolved (2026-06-29; `theme_admissibility_spike.md` Part 7).**
    Tests the A+B model's load-bearing unknown: does megacap confirmation PRECEDE enabler re-rating (→
    A-triggers-B works) or not? Backward DESCRIPTIVE. **Guard 1 (the crux): ONE mechanical pre-registered
    rule, identical across themes** — baseline = Part-5 inception; **confirmation = first month the mega
    leaders' MEDIAN return-from-baseline ≥ +30%** (sensitivity +20%/+50%). **Guard 2:** 5 themes (AI-infra,
    GLP-1, defense, housing, gold). **Result (primary +30%): 4/5 LAG, housing PRECEDE.** AI-infra dramatic
    — enablers had done **1%** of their run at NVDA confirmation (Feb-2023), **+1183% median capturable
    post-confirmation**; GLP-1/defense/gold lag with ~+100% post-confirm; housing SYNCHRONOUS (cyclical,
    no leader-first gap). **Guard-1 sensitivity (decisive honesty): robust LAG only for AI-infra & GLP-1
    (all thresholds); defense & housing FLIP** (defense confirmation date swings 2022→2024→2025 — the
    hand-picked-date risk, real) → **theme-TYPE-specific, not a universal lifecycle.** **Guard 3: the
    timing window does NOT discriminate** — at confirmation, winners (VRT 0% frac) and losers (SOUN 13%)
    are indistinguishable on price/timing → the window inherits Part-6's selection problem (still needs the
    semantic discriminator). **A+B VERDICT:** timing leg HOLDS for the differentiated emergence/breakthrough
    themes it targets (robust LAG, large capturable window) but (a) doesn't generalize (cyclicals
    synchronous, choppy unstable → scope A+B to emergence/breakthrough themes) and (b) is
    necessary-not-sufficient (enabler SELECTION within the window still needs Part-6's untested SEMANTIC
    exposure-classifier). Net: A+B's timing + holding legs are supported; the unsolved piece is the same
    semantic enabler-selection (Part 6) + forward proof. LIMITATIONS: mechanical rule is a modeling choice
    (threshold-sensitive for defense/housing, robust for explosive themes), price-only confirmation,
    backward/judgment-heavy. Informs the build; forward track settles it. Existing Polygon client, key from
    env never logged; throwaway + caches deleted; docs-only; suite green (ruff + mypy --strict 66 + pytest
    204 offline). Edge 2 stays the lead horse.
  - **★ PHASE 1 UNLOCKED & SCOPED — analyst sign-off + four scoping/build decisions recorded (2026-06-29).**
    The pre-build arc is complete (4 detection spikes + holding/fork/timing studies, Parts 1–7); the
    analyst has decided all gates. **SIGN-OFF: APPROVE WITH CONDITIONS** (`theme_admissibility_review.md`
    FINAL DECISION) — the four criteria + the co-movement-basis architecture revision are approved
    a-priori; conditions carried as forward-validation watch-items (Edge-1 high-vol miss → unprompted
    high-vol path; Edge-2 emergent regime-robustness forward-only via analogy+text-footprint; build the
    sector-deconfounding leg properly, not the throwaway cohort-mean) + the three §7 resolutions.
    **§3 AMENDED** (`theme_admissibility.md` §3.0): the original "cluster on linkage, NEVER price" is
    SUPERSEDED — residual CO-MOVEMENT (market+sector+vol stripped) IS the basis + Criterion-1 as
    blob-filter; the discipline survives (raw price-clustering ALONE still = momentum buckets), only the
    absolute is overturned. **FOUR SCOPING/BUILD DECISIONS (analyst-set; this closes the previously-pending
    scoping):**
    **(1) Phase 1 = ALL THREE components** — co-movement detection + theme-type classification + the
    **semantic exposure-classifier** (text/attention IS in Phase 1, NOT deferred to a 1.5).
    **(2) SCOPED to EMERGENCE themes** — the A-triggers-B timing window is robust only there (Part 7;
    cyclicals synchronous, choppy unstable); accept the theme-type-classification cost.
    **(3) PARTICIPATION fork FIRST** — it rests on the more-proven legs (mechanical megacap confirmation +
    semantic selection in the post-confirmation window); **ANTICIPATION deferred** until the classifier is
    proven in participation. Build the classifier reusable; wire only participation now.
    **(4) Detect BROAD (incl. mega-caps — needed for the confirmation signal); HOLD sub-$10B** (return
    structurally capturable there, Part 5).
    **⇒ Phase 1 is no longer gated — UNLOCKED to build, scoped as above.** The build = *mechanical megacap
    confirmation on an emergence theme → triggers the semantic enabler-exposure search in the
    post-confirmation window → human judges*; detect broad / hold sub-$10B; surface strength/lifecycle
    signals as human-judged inputs (§7.1). **LOAD-BEARING OPEN PIECE (forward, not pre-build): the semantic
    classifier's DISCRIMINABILITY** — Parts 1–5,7 proved detection/holding/timing; Parts 6–7 showed
    SELECTION (enabler-vs-loser) is unsolved by naive text/timing and needs the semantic classifier, whose
    discriminability only the forward paper-track can settle. Still gated on the §4 GOVERNOR
    (validation-design-first, must not starve Edge-2 verdicts) before capital. *Docs-only; suite green
    (ruff + mypy --strict 66 + pytest 204 offline).* Edge 2 stays the lead horse.
