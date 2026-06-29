# Theme-detection data-availability spike — finding & go/no-go

> **Seven findings. Parts 1–4 = DETECTION; Part 5 = HOLDING; Part 6 = EARLY-DETECTION fork; Part 7 = A+B
> TIMING.** Part 1 (SIC/attributes): NO-GO. Part 2 (co-movement, overshoot/Yahoo): QUALIFIED GO. Part 3
> (co-movement, BROAD/Polygon): GO. Part 4 (confound resolution): GO CONFIRMED. Part 5 (holding-universe):
> sub-$10B-at-inception CAPTURED the return in all 6 themes. Part 6 (text/attention fork): naive
> text/attention does NOT discriminate enablers from noise (INVERTS) → semantic classifier untested.
> **Part 7 (A+B timing): enablers LAG megacap confirmation robustly for explosive tech/event themes
> (AI-infra/GLP-1; +100–1183% capturable post-confirmation) but NOT cyclicals (housing synchronous) /
> unstable for choppy (defense) — and the window is necessary-not-sufficient (selection still needs
> Part-6's semantic discriminator).** Jump to
> [Part 7](#part-7--timing-sub-10b-enabler-re-rating-vs-megacap-theme-confirmation).

> **Phase-0 deliverable, companion to `docs/theme_admissibility.md`.** This records the result of a
> THROWAWAY spike (script deleted after running) that answered one question **before** committing to
> build Phase 1: does the existing pipeline carry **economic-linkage data fine enough to cluster names
> at theme-grade resolution** (the §3 KEY DESIGN DECISION — cluster on economic linkage, not price)?
> The script is gone; this finding is the deliverable. _Run: 2026-06-25, against the committed
> 317-name overshoot snapshot + live EDGAR submissions._

## What the spike did

Took a **deterministic, unbiased stride sample of 28 names** from the committed overshoot universe
(`candidate_records.jsonl`, 317 names — every ~11th, spanning the whole list, **not** cherry-picked to
known themes), fetched each name's **real SIC** live from free EDGAR submissions (stdlib `urllib`, no
deps, no key), and grouped by (a) 4-digit SIC and (b) the coarse sector map (`vinci/sectors.py`).
Then inventoried the other two candidate linkage sources from real on-disk state. SIC fetch: **28/28
succeeded.**

## What the economic-linkage data actually is — inventory

| Source | What linkage it encodes | Coverage | Granularity | Usable as the clustering basis? |
|---|---|---|---|---|
| **EDGAR SIC** | issuer's primary industry code | **universe-wide, but NOT persisted** — 0% populated in every committed snapshot (`issuers`/`securities`/`candidate_records` all carry a `sic` field = `None`); the universe gate computes it live from EDGAR submissions (Axis 1) and discards it. Re-fetchable live per CIK (free). | **4-digit SIC** → e.g. `7372 Services-Prepackaged Software`, `2834 Pharmaceutical Preparations`. The coarse map collapses further to **~11 GICS-like sectors**. | **NO — too coarse** (see proof below). |
| **graph-exposure** | customer/supplier *who-names-whom* edges, from 10-K customer-concentration disclosure | **NOT present** — `graph_coverage.json` is git-ignored and absent here; built **live** via EDGAR + LLM + judge. **Sparse** (Test-0 ~2% recall on focals; STATE.md §3 "provenance gap, sparse edges"). | relationship edges, not a grouping | **NO — wrong linkage TYPE + too sparse.** A supply-chain edge ("A names B as a customer") is not an end-market theme grouping; and the graph is too sparse to cover a cross-section. |
| **CIQ segments** | business/geographic segment revenue & EBITDA | **per-FINALIST only** — `data/manual/ciq/*` = 0 dirs here; manual export, git-ignored, populated only for names the analyst has deep-pulled (a handful). | fine (segment-level) but | **NO — not universe-wide.** Can't cluster a cross-section you haven't already deep-pulled name-by-name. |
| **Polygon price/volume** | EOD bars (5y) | universe-wide | daily | **Not the basis by design** — price co-movement is **criterion-3 CONFIRMATION** (do economically-linked names also cohere?), explicitly forbidden as the clustering basis (§3: price-clustering → driver-less blobs that fail criterion 1). |

## The proof — SIC is too coarse for theme-grade clusters

Grouping the 28 names by **4-digit SIC** yields 15 groups; only **4** have ≥2 names. The two largest
collisions are the whole story:

- **SIC 7372 "Services-Prepackaged Software" = BILL, DSGX, ESTC, GWRE, PCTY, QLYS, TDC** (7 names).
  Their *actual* drivers are completely different: BILL = SMB payments/fintech, DSGX = logistics /
  supply-chain SaaS, ESTC = search / observability, GWRE = P&C insurance software, PCTY = HR / payroll,
  QLYS = cybersecurity, TDC = data-warehouse / analytics. **"All software" is not a theme** — no single
  nameable driver covers the basket. A theme detector that admitted this group would fail criterion 1.
- **SIC 2834 "Pharmaceutical Preparations" = AMPH, CRNX, GERN, MLYS, NUVB, VERA** (6 names). Generics
  (AMPH), endocrine/rare-disease (CRNX), telomerase oncology (GERN), hypertension (MLYS), oncology
  (NUVB), immunology (VERA). **"All pharma" is not "GLP-1 names"** — the exact failure the spec §3
  warned about, reproduced on real data.

The coarse sector map is worse: 28 names → **6 sectors** (Technology n=12, Health Care n=6, Materials
n=5, …). That is sector beta — precisely what criterion 3 *strips out*, not a driver.

**Read against admissibility:** the only nameable attribute a SIC group offers is the **SIC label
itself** — a sub-sector ("prepackaged software"), never an economic **driver** ("hyperscaler AI
capex"). SIC groups *industries*; themes cut *across and within* industries (a GLP-1 theme spans
pharma + devices + contract manufacturers; an AI-capex theme spans semis + power + cooling + REITs).
SIC cannot express either the within-industry split or the cross-industry join a theme needs.

## Finding

The economic-linkage data the detection basis requires (§3) **does not exist in the pipeline at
theme-grade resolution**:
- **SIC** is universe-wide but **too coarse** — it resolves to sub-sectors, not drivers; it groups
  "all software" / "all pharma," exactly the granularity the spec said is insufficient.
- **graph-exposure** is the **wrong linkage type** (supply-chain relationship edges, not end-market
  grouping) **and too sparse** (~2% recall, uncommitted).
- **CIQ segments** are **per-finalist and manual** — not a universe-wide clustering input.
- **Polygon** is price — criterion-3 confirmation, never the basis.

This is the honest answer the spike was built to surface: **SIC is too broad, graph-exposure too
sparse and wrong-typed, segments not universe-wide — detection-as-specified needs a finer
economic-linkage source the pipeline does not currently have.**

## GO / NO-GO

**NO-GO on building Phase 1 detection on existing data as the clustering basis.** Clustering on SIC
would manufacture sector/sub-sector buckets that fail criterion 1 (nameable driver) by construction —
i.e. it would build a dressed-up sector momentum screen, the exact failure mode the spec exists to
avoid. The blocker is **a finer economic-linkage source**, not the detection logic.

**What would unblock Phase 1 (a new ingestion capability, separately scoped — NOT in this step):**
- **Extract the 10-K Item-1 "Business" narrative → end-market / product / customer-base tags** at
  theme-grade resolution (the natural next linkage source; EDGAR has the text, the pipeline does not
  yet parse Item 1 — it reads only XBRL concepts + 8-K text + SIC). This is the strongest candidate.
- **Densify graph-exposure** into a real cross-sectional linkage layer (cost: it is sparse and
  live-built today; would need the active cross-section assembler, itself a §4 second-wave widener).
- **A licensed thematic/taxonomy feed** (e.g. CIQ industry-specific or a revenue-segment taxonomy
  universe-wide) — heavier, licence-gated, manual.

**Recommendation:** record the NO-GO; do **not** build Phase 1 on SIC/graph/segments. The next move
toward theme detection is the **10-K Item-1 end-market extraction spike** — a separate Phase-0.5
scoping step (does Item-1 parsing yield theme-grade tags?), gated like this one. Edge 2 stays the lead
horse (STATE.md §4 GOVERNOR); none of this starves overshoot verdict-logging. **[SUPERSEDED as the
next move by Part 2 below — co-movement is tested FIRST because it may make Item-1 unnecessary for
detection.]**

---

# Part 2 — Phase-0.6: residual co-movement as the basis

> _Run 2026-06-25, against the committed 317-name overshoot snapshot + live daily prices + live EDGAR
> SIC. Throwaway script deleted._ **Tests the basis Part 1's framing excluded.**

## Why test this — the hypothesis

Part 1 sank SIC and recommended 10-K Item-1 parsing. But Item-1 is **still a company ATTRIBUTE** (what
a company *is*), and a theme is a **shared driver that CROSSES stated-industry lines** ("GLP-1
beneficiaries" = pharma + devices + food; "AI infrastructure" = semis + power + cooling + REITs). So a
better *taxonomy* may hit the **same cross-taxonomy wall** that sank SIC — a better taxonomy is still a
taxonomy. The one basis that is **not** a company attribute is **residual co-movement** (Criterion 3):
names moving together after stripping market + sector beta. A shared driver expresses itself as
cross-industry co-movement no classification captures. The spec relegated co-movement to "confirmation
only"; this spike tests **inverting** that — Criterion 3 *finds* candidate clusters, Criterion 1
driver-naming then *validates* (rejecting the momentum buckets co-movement alone admits).

## What the spike did

317/317 screened names: 6mo daily closes (free keyless Yahoo as a **stand-in for the existing Polygon
EOD** — no `POLYGON_API_KEY` in this worktree, and the committed snapshots hold only price *features*,
not series; the residual-co-movement answer is vendor-agnostic). Stripped **market beta** (vs IWM) then
**broad-sector beta** (vs the leave-one-out coarse-sector cohort mean — both legs of the G2 control
discipline). Clustered on residual-return correlation (threshold graph → connected components), swept
the threshold τ, and fetched each clustered name's **SIC live from EDGAR** for the cross-taxonomy test.
Coarse/transparent by design (a throwaway, **not** the real detector): 122 daily obs, simple
correlation, connected-components.

τ sweep (clusters of size ≥3): τ0.45 → 5 clusters / 26 names `[13,4,3,3,3]`; τ0.50 → 3 / 15; τ0.55 →
4 / 12 `[3,3,3,3]`; τ0.60 → 2 / 6; τ0.65 → 1 / 3. **Most of the 317-name universe does not cluster** —
residual co-movement is concentrated in a few tight pockets.

## The decisive evidence

**① Co-movement DOES cross taxonomy — the proof SIC could never produce.** At τ0.55 the tightest
cluster (residual corr **0.81**) is **RGTI + QUBT + QBTS** (Rigetti, Quantum Computing, D-Wave) — SIC
codes **7371 / 7372 / 7374**, three *different* codes SIC-clustering splits apart, re-united under one
obvious driver: **"quantum computing."** This is exactly the cross-taxonomy theme attributes cannot
capture, and it is the single strongest result of either spike: a real, cleanly nameable theme that
SIC actively dismembers, recovered by co-movement alone.

**② But co-movement also admits the momentum-bucket trap — visibly.** Loosening τ to gain breadth
(τ0.45) merges distinct themes into a **13-name blob** (corr 0.36, 10 SICs, 4 sectors): lithium (LAC,
SLI), eVTOL (ACHR, JOBY, EVEX), quantum (RGTI, QUBT, QBTS), robotics/drones (SERV, ONDS), nuclear
(NNE, LTBR), AI-defense (BBAI). **No single driver names this** — it is the "speculative pre-revenue
future-tech / high-retail-beta" complex co-moving as one risk-appetite factor. Criterion 1 *fails* on
it (you can name sub-themes, not one driver). And a smaller cluster — **RUN + FLGT + WLDN** (Sunrun
solar / Fulgent genetics-labs / Willdan engineering, 3 SICs, 3 sectors) — **crosses taxonomy yet
admits NO shared driver at all**: a spurious co-movement blob.

**③ Therefore the cross-taxonomy metric ALONE is misleading.** 50–60% of clusters cross ≥2 SICs — but
the cross-taxonomy ones split into *real themes* (quantum) **and** *driver-less blobs* (RUN/FLGT/WLDN;
the 13-name mash). Crossing taxonomy is **necessary but not sufficient** — a blob crosses it too. The
**Criterion-1 driver-naming filter is what separates them**, precisely as the spec predicted
("coherence necessary but not sufficient; criterion 1 does the real discriminating"). The spike
*empirically vindicates* that architecture.

Other clusters were **single-SIC, re-deriving SIC** with nameable drivers SIC already captures:
gold/silver miners (BTG, FSM, EXK, OR — SIC 1040) and cannabis (CGC, TLRY, SNDL — SIC 2833). Useful
to the overshoot fund as **thematic-co-derating** signals ("these aren't independent overshoots, they
derated as one theme — judge the driver once"), but adding nothing *over* SIC for those.

## Finding

Residual co-movement is **structurally able to do what SIC fundamentally cannot** — cross taxonomy to
unite a real, nameable theme (quantum: 3 SICs → 1 driver, proven). Its failure mode is the **opposite**
of SIC's: SIC is too **rigid** (false industry splits/joins, can never name a driver finer than the
industry — defeating Criterion 1 *at the root*); co-movement is too **loose** (false joins by shared
sentiment — admitting blobs, but blobs Criterion 1 is *designed to catch*). So **co-movement + Criterion-1
is a workable pairing where SIC + Criterion-1 was not.** Caveats (robustness, for Phase 1, not
viability): threshold-sensitive (no clean τ separates "one theme" from "the speculative complex"); the
window is short/noisy (122 obs); clusters are small and sparse; and the **overshoot universe skews the
dominant factor toward "distressed speculative beta"** — a real detector should run on the **broad**
universe, over longer/multiple windows, with a more robust clustering method.

## GO / NO-GO

**QUALIFIED GO** — and a *different* answer from Part 1's clean NO-GO. Residual co-movement **is** a
viable Phase-1 detection basis **on existing data (no new ingestion source — only the already-built
Polygon EOD)**, because it clears the bar SIC structurally could not. Conditions, all from the spec:
- **Criterion-1 driver-naming is LOAD-BEARING, not optional** — the detector *must* pair co-movement
  clustering with the analyst's driver-naming, or it ships blobs (RUN/FLGT/WLDN) as "themes."
- **The 10-K Item-1 path is NOT required for DETECTION** — co-movement finds candidates without it,
  cheaper. (Item-1 / business-text may still help *propose* the candidate driver to the analyst — i.e.
  support Criterion 1 — but that is driver-naming assistance, not the detection basis. Re-scope it
  that way, if at all.)
- **Phase 1 needs a more robust method than this throwaway** — broad universe, longer/multiple
  windows, principled cluster selection, and explicit handling of the pervasive "speculative-beta"
  factor that merges distinct themes.

**Recommendation (supersedes Part 1's):** pursue **residual co-movement + Criterion-1 driver-naming**
as the Phase-1 basis; do **not** build 10-K Item-1 parsing as a detection prerequisite. Before Phase 1,
one more scoping step is warranted — re-run this co-movement method on the **broad universe** (not just
overshoot) over a longer window to confirm it surfaces cleaner sector-spanning themes (AI-infra, GLP-1)
when the winners are present, not only the distressed speculative complex. Analyst still owns the
a-priori review of `theme_admissibility.md` and the driver-naming verdicts. Edge 2 stays the lead horse
(STATE.md §4 GOVERNOR); this remains parallel scoping. **[Done — see Part 3.]**

---

# Part 3 — Phase-0.7: broad universe + Polygon — the gate

> _Run 2026-06-25. The GATING test: does the Phase-0.6 QUALIFIED GO survive (a) the BROAD universe
> (where real themes live and the speculative skew is diluted) and (b) the REAL production source
> (Polygon, via `vinci.eod.client.PolygonEodClient` — key from env, never logged)? Throwaway script +
> all caches deleted._

## What the spike did

**1,727-name broad operating-company universe** (the full `in_universe` set, $301M–$10B — NOT the
overshoot screen), **12-month** daily closes from **Polygon grouped-daily via the existing client**
(252 trading days; 1,639 names at ≥92% coverage). Stripped market (IWM) **+** broad-sector beta
(**R1** = the 0.6 method); then also stripped a **size + volatility factor** (**R2**) to test whether
the speculative complex is an unremoved factor better residualization dissolves. Clustered on residual
correlation; SIC live from EDGAR for the cross-taxonomy test. Regime context: **IWM +39% over the
window** (a strong small-cap risk-on year — a stringent setting for the speculative-contamination
test).

## ① FIDELITY — Polygon reproduces Yahoo almost exactly

The Phase-0.6 quantum trio on Polygon: **RGTI↔QBTS = 0.82** (Yahoo 0.6 was 0.81), RGTI↔QUBT 0.72,
QUBT↔QBTS 0.73, and the same speculative-tech nearest-neighbours (LAES, SERV, NNE, BBAI). **Vendor
sensitivity is negligible** for these residual correlations — the 0.6 finding was not a Yahoo artifact.

## ② RELIABILITY-AT-SCALE — YES: many clean cross-taxonomy themes, not just quantum

At τ=0.50, R1 yields **48 clusters, 56% spanning ≥2 SICs**, and the top ones are **legibly nameable
economic themes** — a decisive improvement over the overshoot universe's thin, blobby output:

| Cluster | Members (sample) | Span | Driver — nameable? |
|---|---|---|---|
| **US housing** | KBH/TMHC/MTH/MHO/LGIH/GRBK/CCS (builders) + LPX/TREX/UFPI/FBIN (lumber/products) + MHK (flooring) + MBC (furniture) | **14 SICs / 5 sectors** | ✅ housing / mortgage-rate cycle — **the cross-taxonomy win SIC can't produce** (builders 1531, lumber 2400, flooring 2273, furniture 2511 all split by SIC) |
| **Shipping/tankers** | INSW/NAT/STNG/TRMD/SBLK/GNK/DAC… | 4400/4412 | ✅ shipping-rate cycle (tankers + dry-bulk + container) |
| **Gold/silver miners** | AG/EXK/BTG/FSM/OR/EGO/NG… | 1000/1040 | ✅ precious-metals price (mostly single-SIC — re-derives SIC) |
| **Regional banks** | ZION/ONB/FNB/HOMB/UBSI/SSB… | 6021/6022 | ✅ regional-bank / rates / deposits |
| **Hotels & lodging** | APLE/RLJ/DRH/RHP/PEB (REITs) + PK/XHR/SHO (operators) | **6798 + 7011, 2 sectors** | ✅ lodging/travel — **cross-taxonomy** (REITs + operators, which SIC splits) |
| **Staffing / white-collar labor** | KFY/MAN/RHI/NSP + EPAM/GLOB + EXLS/TNET | **5 SICs** | ✅ labor-market / staffing cycle — **cross-taxonomy** |
| **Commodity chemicals** | CC/OLN/HUN/TROX/CE/EMN | 2800–2821 | ✅ commodity-chemical cycle |
| **Trucking/freight** | ARCB/WERN/MRTN/LSTR/HTLD + RXO | 4213/4700 | ✅ freight cycle |

Two grades surface, both useful: **genuine cross-taxonomy DRIVER themes SIC cannot express** (housing,
hotels+operators, staffing, quantum) — the unique value-add — **and** coherent sub-sector cohorts
(gold, banks, shipping, trucking) a sector map would also find. Crucially, unlike the overshoot
universe, the cross-taxonomy clusters here are **nameable, not blobs** (occasional spurious member —
COLM in chemicals, PRGO in housing — is analyst-handled, not a driver-less blob). **Reliability is HIGH:
theme recovery happens many times over, not once.**

## ③ THE SEDUCTIVE FALSE-DRIVER — handle-able, two independent ways

The chief risk (Phase-0.6): the speculative-beta complex is a risk-factor that *looks* like a nameable
driver ("future tech"). Two findings resolve it:

- **Universe dilution.** On the broad universe the speculative complex **no longer dominates** — the
  top clusters are sober macro themes (housing, banks, shipping, gold); the spec-tech pocket is one
  small cluster among ~48. Its dominance in Phase-0.6 was an **overshoot-universe artifact** (distressed
  small-caps are disproportionately the speculative complex), not an inherent property of the basis.
- **Factor stripping mechanically dissolves it — the clean proof.** At a loose τ=0.45, R1 still produces
  the **19-name speculative blob** (RGTI/QUBT/QBTS + SERV/NNE/JOBY/ACHR/LAES — quantum + robotics +
  nuclear + eVTOL + crypto-chips, *no single driver*). Stripping the **volatility/speculative factor
  (R2) collapses it to exactly the 3 real quantum names** (RGTI/QUBT/QBTS), evaporating the speculative
  halo **while preserving the genuine theme** (RGTI↔QBTS only 0.82→0.79). So the false-driver is
  **removed mechanically, before driver-naming** — Criterion-1 is not asked to reject "future tech"; the
  residualization dissolves the halo and hands the analyst the clean core. The real macro themes
  (housing, shipping, gold, banks, hotels, trucking) are **robust to the same strip** (present in both
  R1 and R2), confirming they are genuine drivers, not size/vol artifacts.

## Finding

On the universe themes actually live in, and on the real production source, residual co-movement
**reliably surfaces multiple clean, nameable, cross-taxonomy themes** (housing across 14 SICs, hotels
across REIT+operator, staffing across 5 SICs, quantum across 3 computing SICs), and the **chief
contamination risk is doubly handle-able** — diluted by the broad universe and mechanically dissolved
by a volatility-factor strip that leaves real themes intact. The Phase-0.6 QUALIFIED GO **survives and
strengthens**. (Scope caveat: the $10B ceiling excludes mega-cap theme leaders, so the themes that
surface are the small/mid-cap expressions — housing, shipping, miners, banks, hotels, quantum-small-caps
— **not** mega-cap-led AI-infra / GLP-1, whose bellwethers (NVDA, LLY) are out of band. For the
overshoot fund, which operates on exactly this band, that is the right universe.)

## GO / NO-GO

**GO** — residual co-movement is a viable Phase-1 detection basis **on existing data via the
already-built Polygon EOD client (no new ingestion source)**. The three risks that gated it are
cleared: fidelity (Polygon ≈ Yahoo), reliability-at-scale (many nameable cross-taxonomy themes), and
speculative contamination (handle-able by universe choice + a volatility-factor strip). Build conditions
carried into Phase 1:
- **Pair clustering with the volatility/speculative-factor strip** — it is the lever that separates real
  themes from the risk-on halo; not optional.
- **Criterion-1 driver-naming remains the gate** (CLAUDE.md: machine proposes, analyst concludes) — far
  less stressed than feared, but still owns the verdict and the occasional spurious member.
- **A more robust method than this throwaway** — principled cluster selection (not a single τ),
  multiple/longer windows, significance testing; and decide the run universe (broad for theme discovery
  vs the overshoot set for "are these finalists a thematic co-derating?").

**Recommendation:** Phase 1 (the real detection layer + the admissibility screen) is now **justified to
build on existing data** — `theme_admissibility.md`'s four criteria, clustering on residual co-movement
(market + sector + vol stripped) as Criterion-3-as-basis, with Criterion-1 driver-naming as the human
gate. Pre-requisite unchanged: the analyst signs off the `theme_admissibility.md` a-priori review.
10-K Item-1 parsing remains **not needed for detection** (may at most assist driver-naming). Edge 2
stays the lead horse (STATE.md §4 GOVERNOR); parallel scoping only. **[Confounds tested — see Part 4.]**

---

# Part 4 — Phase-0.8: resolving the two load-bearing confounds (last pre-build spike)

> _Run 2026-06-29. The 0.7 GO rested on two things the single test that "proved" them could not
> isolate: **(a) vol-strip SELECTIVITY** — the blob collapsed to the quantum trio, but quantum was
> simultaneously the real theme AND the tightest cluster AND the highest-vol, so "selective" was
> indistinguishable from "keeps only the tightest knot"; **(b) REGIME-fragility** — 0.7 ran in a +39%
> risk-on window, where a dominant market factor makes residual correlation most fragile. Two
> tightly-scoped tests (no other exploration); throwaway + caches deleted. Existing Polygon client,
> key from env._

## TEST 1 — vol-strip selectivity: **SELECTIVE** (confound a CLEARED)

Applied the R1→R2 (+size+vol) strip to three groups derived from the risk-on window and measured
survival (within-group connected component) + cohesion (mean pairwise residual corr):

| Group | vol-pctile | mean pairwise corr  (R1 → +vol → +size+vol) | sub-clusters @τ  (R1 → +size+vol) | verdict |
|---|---|---|---|---|
| QUANTUM (tight real) | 95 | 0.76 → 0.71 → 0.71 | [3] → [3] | SURVIVES |
| **HOUSING (diffuse real)** | **45** | 0.37 → 0.35 → 0.35 | [22] → **[18,1,1,1,1]** | **SURVIVES** |
| **SPEC-BLOB (fake)** | 88 | 0.30 → 0.27 → 0.27 | [19] → **[6,3,2,2,2,…]** | **DISSOLVES** |

The decisive result: **the diffuse real theme (housing) survived nearly intact** (18 of 22 stay
connected; mean corr 0.37→0.35, barely moved) **while the fake blob fragmented** (19 → [6,3,2,2,2,…]).
A threshold-raiser would have dissolved housing too; it didn't. The strip is **SELECTIVE.**

The mechanism is **volatility, not correlation-tightness**: housing sits at the **45th** vol-pctile, so
the high-vol factor is not its shared movement and the strip barely touches it; the blob sits at the
**88th**, so the vol factor IS its shared movement. And the blob's "dissolution" is actually
**RESOLUTION into its real constituent themes** — the fragments are **uranium** (DNN/UUUU/URG/NXE/UEC/EU,
the 6), **quantum** (RGTI/QUBT/QBTS, the 3), and **eVTOL** (the 2s). The strip removed the spurious
**cross-theme speculative glue** that the +39% risk-on regime had fused into one blob, leaving each real
sub-theme standing. That is the ideal selective behaviour: preserve diffuse real themes, trim-but-keep
tight real themes, and unbundle a risk-on amalgam into its nameable parts. **Confound (a) cleared.**

## TEST 2 — regime fragility: themes **RECUR** (confound b substantially CLEARED)

A genuinely different regime was available on Polygon: **Window B = 2021-11..2022-10, IWM −29%** (a
drawdown) — the opposite of Window A's +39%. (History before ~2021-11 is outside the Starter window;
honest classification: 2022 windows = −22% to −29% drawdowns, 2023-24 ≈ +7% choppy, 2025-26 = +39%.)
Re-ran the full method (market+sector+vol, cluster @0.50) on Window B (1,409 names — recent IPOs
auto-dropped) and checked whether each Window-A theme re-forms:

| Theme (seed) | Window-B component | recurs? |
|---|---|---|
| HOUSING (KBH) | 10 names, 3 SIC (builders + IBP + WHR) | ✅ |
| GOLD (BTG) | 13 names, 4 SIC | ✅ |
| SHIPPING (STNG) | 8 names (tankers) | ✅ |
| HOTELS (PK) | 15 names, 4 SIC (REITs + operators + timeshare + franchisors) | ✅ |
| BANKS (ZION) | 1 name (isolated) | ✗ regime-specific |
| TRUCKING (ARCB) | 2 names | ~ thin |
| QUANTUM (RGTI) | no Window-B history | untestable |

The core cross-taxonomy / sector themes **recur across opposite regimes** — housing, gold, shipping,
hotels all re-form in a −29% drawdown just as in a +39% melt-up, so they are **not residual-artifacts
of the risk-on window**. Two honest caveats: **banks did NOT recur** (a regime-specific cluster — and
that the method does *not* mechanically re-find identical clusters every regime is itself reassuring:
it reflects real co-movement, which genuinely differed for banks between 2021-22 and 2025-26); and
**quantum could not be regime-tested** (it IPO'd after Window B), so the tight-high-vol theme's
regime-robustness is the one corner **deferred to Phase-1's multiple-windows condition**, not silently
assumed. **Confound (b) substantially cleared for the diffuse themes.**

## COMBINED VERDICT: **GO CONFIRMED**

Both confounds resolve favourably: the vol-strip is **selective** (a diffuse real theme survives while
the fake blob dissolves — by volatility, not tightness), and the core themes are **regime-robust**
(recur across +39% and −29%). The Phase-0.7 GO **stands**, with the two things that could have hollowed
it out now tested and cleared. Residual co-movement (market + sector + vol stripped) + Criterion-1
driver-naming is a sound Phase-1 detection basis on existing data via the Polygon client. Carry into
Phase 1: **(1)** the vol-factor strip is selective and load-bearing — keep it; **(2)** regime-robustness
of TIGHT high-vol themes (quantum-class) is still untested for lack of pre-IPO history → fold into the
multiple-windows build condition; **(3)** some clusters are legitimately regime-specific (banks) — a
theme can be live in one regime and dormant in another, which the analyst names per-period. Pre-req
unchanged: the analyst signs off `theme_admissibility.md`'s a-priori review before Phase 1 is built.

---

# Part 5 — Backward holding-universe study: does a sub-$10B basket capture theme returns?

> _Run 2026-06-29. **A DISTINCT axis from Parts 1–4** (which were about DETECTION). The fund DETECTS
> themes broad (incl. mega-cap leaders) but HOLDS sub-$10B expressions; this checks whether that
> **holding bound** actually captures theme returns or whether returns concentrate in cap-excluded
> names. **BACKWARD DESCRIPTIVE market-structure study — NOT a strategy backtest, NOT forward edge
> validation.** Throwaway + caches deleted; existing Polygon client, key from env._

## Method (and the two traps handled)

6 themes across 3 structural types; **near-inception constituents as-understood-then** (judgment-heavy,
hindsight-prone — see Limitations). **Trap 1 — CAP-TIMING (the crux):** each name's market cap measured
**AT INCEPTION** (Polygon **point-in-time** `market_cap` via the dated reference endpoint — correct
historical cap, splits/shares handled; validated: NVDA Jan-2023 = $352B, today $4.66T), not today's cap.
Both reported so growth-through-bound is visible. **Trap 2 — HINDSIGHT:** constituents picked as
near-inception membership, not "who won" — but still hindsight-prone (flagged). Return = equal-weight
buy-and-hold inception→2026-06-17 (Polygon adjusted closes). Compare sub-$10B-at-inception basket vs
>$10B-at-inception basket vs all.

## Result — the sub-$10B-at-inception basket CAPTURED the theme return in ALL SIX themes (beat the >$10B basket in 5/6)

| Theme | Type | sub-$10B mean | >$10B mean | capture | grew through $10B |
|---|---|---|---|---|---|
| **AI-infra** | tech-emergence | **+1648%** | +955% | sub WINS | **6/6** (MOD,VRT,CRDO,CLS,COHR,SMCI) |
| **GLP-1** | tech-emergence | +192% (noisy) | +84% | sub wins | 0/3 |
| **Housing** | macro/cyclical | +96% | +66% | sub wins | 1/10 (TOL) |
| **Defense** | macro/cyclical | **+245%** | +56% | sub WINS | 3/5 (HII,CW,BWXT) |
| **Uranium** | commodity | +191% | *(none >$10B existed)* | 100% sub | 1/8 (CCJ) |
| **Gold** | commodity | +243% | +175% | sub wins | 1/6 (KGC) |

## Key patterns

1. **The "tech-emergence fails" hypothesis is REJECTED.** The fear was tech returns concentrate above
   the bound (NVDA goes mega fast). They didn't: the sub-$10B AI-infra **enabler** cohort (VRT
   power/cooling, CRDO/COHR optical, CLS EMS, MOD thermal, SMCI servers) captured **+1648%** vs the mega
   chips' +955%. **The theme is broader than its leader, and the enablers start sub-$10B.** NVDA-the-
   leader was mega at inception, but you did **not** need to own NVDA to capture AI-infra.
2. **Growth-through-bound is real and STRONGEST in the hard case.** AI-infra: **6/6** sub-$10B enablers
   grew through $10B (MOD $1.0B→$13.5B, VRT $5.0B→$117B, CRDO $1.9B→$44B). The bound **catches them small
   and rides them up** — arguably ideal, not limiting.
3. **Macro/cyclical + commodity confirmed favorable** (as hypothesized): housing, defense, uranium
   (entirely sub-$10B — *no* >$10B names existed at inception), gold all captured sub-$10B, the sub-$10B
   cohort often beating the megas (defense +245% vs primes +56%; the big primes LMT/NOC/GD barely moved).
4. **Bound-viability did NOT differ by type in the feared direction** — all six captured sub-$10B; if
   anything sub-$10B OUTperformed (5/6), because smaller names have more room to grow and the theme grows
   them through the bound.

## The reframe this produces

The binding constraint is **NOT the holding bound** — structurally, the return **is** capturable sub-$10B
across all theme types tested. It is whether **DETECTION can identify the sub-$10B enablers EARLY** —
which this study **ASSUMES** (hindsight) and the forward track must prove. So the study moves the
question from "is the $10B holding bound right?" (looks robustly fine) to "can we detect the sub-$10B
theme expressions contemporaneously?" (the detection + forward-validation problem). It also sharpens the
run-universe scoping question (`theme_admissibility.md` §7.4): **detect BROAD** (incl. mega leaders, to
SEE the theme) while the **holdable expression — and, this study suggests, the return — lives sub-$10B.**

## LIMITATIONS — suggestive structural evidence, NOT proof (read this)

- **HINDSIGHT theme-selection (the big one).** Constituents were chosen KNOWING which themes/names won.
  "AI power/cooling/optical" was *not* obviously the AI-infra theme in Jan-2023; VRT/CRDO/MOD weren't
  widely tagged "AI" then. The study shows "**IF** you correctly ID'd the sub-$10B enablers near
  inception, they captured the return" — the hard part (contemporaneous ID) is **assumed away**.
  → the sub-$10B basket return is almost certainly **OVERSTATED** (hindsight picked enablers that worked;
  faded sub-$10B candidates omitted). This is an existence-and-magnitude check, **not a capture-RATE
  estimate.**
- **Equal-weight buy-and-hold, no exit discipline** — some names round-tripped (ALT −83%, LGIH −45%);
  descriptive only, not a strategy.
- **Small n** per theme; **GLP-1 (n=5) is the noisiest** — lottery-like (ALT −83%, NVO −36%, HIMS/VKTX
  won); its "capture" is weak evidence.
- **Data caveat:** Barrick (GOLD) cap_today glitched ($1.2B) from its 2025 GOLD→B ticker change;
  excluding it moves the gold >$10B mean <2pp (immaterial).
- **It does NOT settle the holding ceiling.** The **forward paper-track settles it**: do MY actual
  sub-$10B theme bets capture the return? This study **informs** that and generates the hypothesis — it
  is structural evidence pointing toward "the $10B holding bound is viable across theme types," **not** a
  ceiling decision (which stays the human's, with the forward track as arbiter).

---

# Part 6 — Can text/attention surface sub-$10B enablers EARLY *and discriminably*? (the fork test)

> _Run 2026-06-29. Part 5's reframe made this load-bearing: the sub-$10B enabler RETURN requires
> entering EARLY (pre-run, while sub-$10B — Part 5's +1648% came from names that grew THROUGH the bound),
> but co-movement detection is structurally LATE (fires only once names already co-move = mid-run).
> Text/attention is the INTENDED early mechanism. **THE FORK:** text surfaces enablers early AND
> discriminably → build the differentiated **sub-$10B enabler edge**; else → fall back to the **MEGACAP
> theme edge** (obvious leaders, but far more replicable/crowded, outside the holding band). Backward
> DESCRIPTIVE — NOT a backtest. Throwaway + caches deleted; existing Polygon client, key from env._

## Method (and the trap a naive test skips)

AI-infra (the sharpest case — it has an obvious loud-text LOSER set). **WINNERS** = Part-5 sub-$10B
enablers (VRT, CRDO, MOD, COHR, CLS, SMCI). **LOSERS** = sub-$10B names that screamed AI early and were
NOT durable enablers (C3.ai `AI`, BigBear.ai `BBAI`, Veritone `VERI`, SoundHound `SOUN`, Rekor `REKR`).
**Including the losers is the whole point** — the precision/false-positive test; omitting them repeats
Part-5's hindsight error in a new form. Signals measurable backward (free): **EDGAR full-text
theme-mention counts/yr** (disclosure-attention, CIK-precise) + **Polygon news article volume/yr**
(news-attention, size-confounded). The honest bar: early-enabler-detection is ACHIEVABLE only if BOTH
**recall** (text leads price for real enablers) AND **precision** (text discriminates enablers from
same-theme losers) hold.

## Result — BOTH fail; the discriminability signal INVERTS

**Precision — FAILS, perfectly inverted.** Early-2022 EDGAR "artificial intelligence" filing-mentions:
winners mean **2.2** (median 1.5); losers mean **15.6** (median 11) — the losers were **~7× louder**.
Ranked by 2022 AI-mentions, **all five LOSERS rank above all six WINNERS**: SOUN(30), BBAI(20), VERI(11),
AI(9), REKR(8), then SMCI(5), CRDO(4), COHR(2), MOD(1), CLS(1), **VRT(0)**. The biggest enabler (VRT,
**+2225%**) had **zero** AI-mentions; a 2022 "loudest-AI-text" screen buys exactly the five losers and
skips every enabler. News volume doesn't save it: it is **coincident/lagging** (VRT 45→206, MOD 38→222
as price ran in 2023, not before), **size-confounded**, and the loudest-news name (C3.ai, 672 in 2023)
**flopped** (−8% total).

**Recall — FAILS for the obvious phrase.** The winners' AI-text was silent/flat *throughout* their run
(VRT 0/0/1, MOD 0/1/2, CLS 1/1/2 across 2021/22/23). It did not lead price; it barely existed.

**WHY — the enabler signal is SEMANTIC, not keyword (phrase-dependence).** The winners' real driver-text
was **"data center," not "AI"**: VRT `data center` 14/6/11 vs `AI` 0/0/1; MOD 9/9/10 vs 0/1/2; CLS 6/7/12
vs 1/1/2. A "data center" screen WOULD have flagged the enablers early — but (a) it also flags non-enabler
REITs/telcos (different noise), and (b) **knowing to search "data center" (not "AI") as THE
AI-infra-enabler phrase IS the hindsight insight.** The connection "data-center power/cooling/optical =
AI-capex beneficiary" is a **semantic, causal-chain inference**, not a keyword the company emits. The
companies that *emitted* "AI" were the self-promoters (losers); the companies that *were* AI-infra
described their actual business and left the inference to the analyst.

## THE FORK VERDICT — lean MEGACAP fallback (naive text fails); semantic path untested

By the honest bar (BOTH recall AND precision), **NEITHER holds for naive text/attention** (keyword
mentions + news volume): it is a theme-**BUZZ** detector (finds the loud self-promoters), **not** an
enabler detector. Per the user's fallback logic → **lean MEGACAP theme fallback** (hold the obvious large
liquid leaders — identifiable precisely because obvious, but far more replicable/crowded, and outside the
current sub-$10B holding band). **Door not fully closed:** this condemns KEYWORD/VOLUME text, *not*
SEMANTIC text. The winning insight is a semantic exposure-inference ("data-center power = AI capex"),
which is exactly the human-judgment / LLM-assembly the fund is built on. An **LLM exposure-classifier**
(read the business, reason about theme-exposure, rather than count keywords) is the **untested path** that
could revive the differentiated enabler edge — but it is harder (semantic reasoning at breadth), not the
cheap attention screen, and is a Phase-1.5+ question, **not settled here**.

## LIMITATIONS (prominent)

- **Backward, judgment-heavy:** theme-membership AND the loser-set are subjective/hindsight-prone. Some
  "losers" ran LATE on AI-hype (SOUN +293%, BBAI +476% — buzz-driven round-trips, not durable enablers),
  which *reinforces* "text finds buzz, not enablers" but shows "loser" is fuzzy. The durable +2000%
  enablers (VRT/CLS/CRDO) were the text-silent ones.
- **Only 2 text facets measurable backward** (EDGAR disclosure + Polygon news); analyst/social/transcript
  attention untested; **semantic LLM-exposure classification untested — the key open path.**
- **Single theme** (AI-infra, the sharpest case); defense / GLP-1 not tested here.
- **Informs the build-which-edge fork; does NOT settle it.** The forward track settles it: can a LIVE
  detector surface enablers early AND discriminably (likely only via semantic exposure-classification)?

## What it informs

The fork now has evidence: **(a)** the cheap-text sub-$10B-enabler shortcut is **not viable** (naive
attention is anti-discriminating — it finds buzz); **(b)** the differentiated enabler edge, IF pursued,
requires **semantic exposure-reasoning** (LLM reads the business → judges theme-exposure), the fund's
actual edge, not a keyword/volume screen — untested, Phase-1.5+; **(c)** absent that, the **megacap theme
fallback** is the lower-differentiation default. This sharpens the text/attention scoping question
(`theme_admissibility.md` §7.4): naive keyword/volume text is **not** the answer; semantic classification
is the only version worth scoping. The build-which-edge decision stays the human's, with the forward track
as arbiter.

---

# Part 7 — Timing: sub-$10B enabler re-rating vs megacap theme confirmation

> _Run 2026-06-29. Tests the load-bearing unknown of the A+B model: megacap confirmation TRIGGERS a
> semantic enabler-search (confirmation removes the prediction problem — reason about a CONFIRMED driver).
> Viability rests on TIMING: do enablers re-rate AFTER confirmation (→ A-triggers-B works, capturable gap),
> OVERLAPPING (tight window), or BEFORE (→ needs anticipation)? Backward DESCRIPTIVE — NOT a backtest.
> Throwaway + caches deleted; existing Polygon client, key from env._

## Method — ONE mechanical rule, applied identically (guard 1), across 5 themes (guard 2)

**Pre-registered rule (stated before computing, identical for every theme):** baseline = the theme's
Part-5 inception; designate the mega-cap (>$10B) **leaders**; **confirmation = first month the leaders'
MEDIAN cumulative return-from-baseline ≥ +30%** (primary). For each Part-5 sub-$10B **enabler**: the
fraction of its total (baseline→2026-06) re-rating already realized BY confirmation (low = lag), and the
**post-confirmation return** (what entering at confirmation would have captured). LAG if median frac
<40%, PRECEDE if >60%, else OVERLAP. **Sensitivity** reported at +20%/+50% (does the verdict survive?).
5 themes: AI-infra, GLP-1, defense, housing (cyclical), gold (commodity).

## Result (primary +30%)

| Theme | confirmation | median frac-done@confirm | verdict | median enabler POST-confirm return |
|---|---|---|---|---|
| **AI-infra** | 2023-02 (NVDA/AVGO/AMD) | **1%** | **LAG** | **+1183%** |
| GLP-1 | 2023-09 (LLY/NVO) | 15% | LAG | +109% |
| Defense | 2024-08 (LMT/RTX/NOC/GD) | 34% | LAG | +106% |
| Gold | 2025-04 (NEM/AEM/…) | 26% | LAG | +105% |
| **Housing** | 2023-07 (DHI/LEN/PHM/NVR) | **67%** | **PRECEDE** | +15% |

**4/5 LAG, housing PRECEDE.** The AI-infra case is dramatic: enablers had realized **1%** of their run
when NVDA confirmed (Feb-2023), leaving **+1183% median** capturable by entering at confirmation — a huge,
clean A-triggers-B gap. GLP-1/defense/gold also lag with ~+100% post-confirmation. Housing is
**synchronous** (cyclical): builders and sub-$10B builders re-rated together early-2023, so by the time
the big builders confirmed, the enablers were ~2/3 done (+15% left) — **no leader-first gap to trigger on.**

## Guard 1 — sensitivity (the verdict-flips-with-the-date risk, measured)

| theme | +20% | +30% | +50% |
|---|---|---|---|
| AI-infra | LAG | LAG | LAG | **robust** |
| GLP-1 | LAG | LAG | LAG | **robust** |
| Gold | LAG | LAG | OVERLAP | robust-ish |
| Defense | LAG (22-11) | LAG (24-08) | **PRECEDE (25-08)** | **FLIPS** |
| Housing | LAG (23-05) | PRECEDE (23-07) | PRECEDE (24-01) | **FLIPS** |

The lag verdict is **robust only for the explosive themes (AI-infra, GLP-1)** where the leader re-rates
fast and far (stable, early confirmation). It is **threshold-UNSTABLE for choppy (defense — confirmation
date swings 2022→2024→2025 as the Ukraine spike faded and resumed) and synchronous (housing) themes** —
exactly the "hand-picked date produces any answer" risk the guard exists to expose. So the relationship is
**theme-TYPE-specific, not a universal lifecycle.**

## Guard 3 — does the timing window DISCRIMINATE enablers from losers? NO (it inherits Part 6)

At AI-infra confirmation (2023-02), frac-done-by-confirmation: winners VRT 0% / CRDO 2% / MOD 2% / COHR
3% / CLS 1% / SMCI −2% — all lagged. But losers were mixed: SOUN 13% (also lagged, ran later on hype),
BBAI 86%, and AI/VERI/REKR net-negative. **At the confirmation moment, winners and losers are
indistinguishable on price/timing** (everyone ~flat, pre-run). So the timing window tells you *when* to
look (post-confirmation) but **not *which* names** — selecting enablers from same-theme noise within the
window still requires the **semantic discriminator Part 6 showed naive text lacks.** The timing gap is
**necessary but not sufficient.**

## THE A+B VERDICT

**The A+B timing premise HOLDS for the differentiated themes it targets — but is not universal, and does
not escape the selection problem.** Concretely: **(1)** enablers robustly LAG megacap confirmation for
**explosive tech-emergence / breakthrough themes (AI-infra, GLP-1)** — a large, threshold-robust,
capturable post-confirmation window (+100% to +1183%); lag-ish for commodity (gold). So **A-triggers-B is
viable for that theme-type subset** (which is the differentiated edge's target). **(2)** It does **NOT
generalize**: cyclical themes (housing) are synchronous (no leader-first gap), and choppy themes (defense)
have unstable confirmation dates that flip the verdict — so there is **no universal lifecycle to trade**;
A+B must be **scoped to emergence/breakthrough themes.** **(3)** Even where the window exists, it is
**necessary-not-sufficient**: enabler selection within it still needs the **semantic exposure-classifier**
(Part 6's untested path), because at confirmation winners and losers look alike. Net: A+B's timing leg is
**sound for the right theme types**; the unsolved piece is the same **semantic enabler-selection** Part 6
identified — not the timing.

## LIMITATIONS (prominent)

- **The mechanical rule is a modeling choice**, and the verdict is **threshold-sensitive for defense &
  housing** (reported above) — robust only for AI-infra/GLP-1/gold. A different rule would move
  defense/housing; it would not overturn the explosive-theme LAG (the gap there is too large: 1–26% frac).
- Price-based confirmation only (consensus-estimate confirmation not available backward); single rule
  family.
- Backward, judgment-heavy constituent/leader/loser selection; the long window (to 2026) inflates
  post-confirmation returns (but that IS the "enter-at-confirmation" capture).
- **Informs the build; the forward track settles it** — can a LIVE detector, triggered by megacap
  confirmation, surface AND discriminate enablers in the window (the semantic-classifier question)?

## What it informs

Composes the arc into a build picture: detection basis viable (Parts 1–4); sub-$10B holds the return
(Part 5); naive text can't pick enablers (Part 6); **a confirmation-triggered timing WINDOW exists for
emergence/breakthrough themes (Part 7)**. So the A+B edge, IF built, is: **megacap confirmation (mechanical,
on an emergence/breakthrough theme) → triggers a SEMANTIC enabler-exposure search in the window → human
judges.** The two open pieces are the **semantic discriminator** (Part 6) and **forward proof**; the timing
leg and the holding bound are supported. Decision stays the human's.
