# BUILD BRIEF — `operating_drivers`: the mechanism-coverage tier (PR-B)

> STATUS: **DRAFT — awaiting operator sign-off. No code until signed off.**
> Drafted 2026-07-13 · genesis: the MOSL Mahanagar Gas audit (STATE.md §5 QUEUED entry, 2026-07-13)
> · builds **after PR #116 (verdict-first) merges** · sequenced Tier A → Tier B.
> Vocabulary per CLAUDE.md BRIEF CONTRACT: **anchored** = deterministic (heading/regex, CI-pinned on
> committed real-text fixtures); **LLM-fenced** = an LLM extraction phase. Bare "fenced" is malformed.

## 0. Objective — the 90-second mechanism handover

The Brief's case points are source-bound but ATOMIZED: no leading indicator with its base rate, no
pricing actions vs headwinds, no pass-through structure, no driver sizing. A sell-side page-1 hands
these over in 90 seconds (MOSL audit: its structure scored 8.5 where ours scored 7.5 — the one gap
with teeth). This build assembles those facts as **typed, cited, verbatim-validated rows** on the
mechanical layer and renders a compact **Mechanism** block on the Brief.

**The line (unchanged by the pivot):** assemble-and-cite only. Rows are stated facts with
source_refs; the block POSES, never forecasts (the anti-model: MOSL's "we estimate a further
INR2–3/kg"). No new verdict surface; execution untouched; `Synthesis`'s six-field no-conclusion pin
(tests/test_dossier.py `test_synthesis_is_the_only_llm_output_and_carries_no_conclusion`) stands.

## 1. Schema — supplying layer: NEW assembled field (`vinci/dossier/schemas.py`)

```python
class DriverKind(enum.StrEnum):
    LEADING_INDICATOR = "leading_indicator"      # a unit-volume/KPI run-rate ("536 MWh shipped")
    PRICING_ACTION = "pricing_action"            # a dated price change taken/announced
    ATTRIBUTION = "attribution"                  # MD&A price/volume/mix causality sentence
    PASS_THROUGH_STRUCTURE = "pass_through_structure"  # indexation/contract pass-through facts
    COMPETITIVE_POSITION = "competitive_position"      # stated competitive slack/position

class OperatingDriver(BaseModel, frozen=True):
    kind: DriverKind
    metric: str                 # "battery shipments", "average selling price"
    period: str | None = None   # as STATED ("Q1 2026", "FY26"); None when unstated
    value: str                  # the VERBATIM stated value ("536 MWh", "+7% effective March 1")
    value_num: float | None = None  # structured numeric — ANCHORED rows only (we parsed it);
    unit: str | None = None         # LLM-fenced rows leave these None (verbatim-only discipline)
    verbatim: str               # the exact sentence read from (the human greps for it)
    source_ref: str             # MACHINE-SET by the extractor — the model never invents a citation
    tier: str                   # "anchored" | "llm-fenced" — extraction-path provenance

class OperatingDriversExtract(BaseModel, frozen=True):
    rows: list[OperatingDriver] = Field(default_factory=list)
    qa_flags: list[str] = Field(default_factory=list)  # every miss/drop is a loud flag

# MechanicalLayer — optional-with-default-None, the #98 back-compat precedent
# (STATE.md:2985-2987; mirrors primary_source/key_ratios):
operating_drivers: OperatingDriversExtract | None = None
```

- "Parsers consume structured values": anchored rows ALSO expose `value_num`/`unit`; every code
  consumer reads those, never re-parses `value`. LLM-fenced rows are verbatim-only by design
  (covenant precedent: report AS STATED, never resolve) — no consumer computes on them.
- Committed `dossier.json` round-trips (default None); a name with no drivers renders fail-honest.

## 2. Tier A — ANCHORED extraction (deterministic; zero LLM; builds first)

### A1 — EX-99.1 operating KPIs + pricing actions (`vinci/edgar/release_parse.py`)

A **fifth section extractor** in the existing deterministic parser (precedent: `_guidance` :209,
`_reconciliation` :134 — pure `str → rows`, misses → `qa_flags`): `_operating_drivers(text,
source_ref)` targeting:
- **KPI-with-unit sentences** — number + unit-lexicon token (`MWh|GWh|units|vehicles|members|
  subscribers|customers|locations|stores|procedures|shipments|deliveries|tons|barrels` — FIXED
  lexicon, face-validity, extendable per observed misses) near a shipped/delivered/added/
  opened/processed verb → `LEADING_INDICATOR`.
- **Pricing-action sentences** — `price (increase|decrease|adjustment)` / `pricing action` with a
  % or $ amount and an `effective <date>` where stated → `PRICING_ACTION` (dated).

Feeds from the EXISTING fetch: `mechanical._primary_source` already fetches + parses every
2.02/8.01 EX-99.1 (mechanical.py:1789-1803); raw text is disk-cached (`data/cache/sec/<sha256>.json`,
netcache.py:149-151) → **zero new I/O**; the new section runs inside `parse_release`.

### A2 — 10-Q MD&A price/volume/mix attribution (`vinci/edgar/filing_sections.py`)

A new anchored section `_results_attribution` in the existing 10-Q section parser (precedent:
`_concentration`'s three anchor tiers `_CUST`/`_CUST_EXACT`/`_CUST_FLOOR`, :114-124), targeting the
canonical MD&A shape: *"[revenue|net sales] (increased|decreased) $X million, or Y%, …
(primarily|principally) (due to|driven by) …volume/price/mix…"* → `ATTRIBUTION` rows.
**First consumer of MD&A body text** — the full normalized 10-Q is already materialized at
mechanical.py:1810 and disk-cached; no new fetch. Escalation to more sentence shapes is
coverage-evidenced (per observed misses in `qa_flags`), never speculative.

- **Money handling:** through release_parse's existing numeric path — **VERIFY-AT-BUILD** whether a
  shared money-parse helper exists there; if not, ONE new shared helper used by both A1/A2 (the
  `$1,101.80M`-read-as-`1` thousands incident + the `$0.02-vs-$22.00` bond-convention mis-scale,
  STATE.md:1642-1646, are the observed shapes the helper's pins must reject).

## 3. Tier B — LLM-FENCED transcript extraction (coverage-gated escalation)

### Coverage evidence gating this tier (as-of 2026-07-13)

- CIQ store holds **2 earnings calls per name, 10/10 finalists** (`data/manual/ciq/<T>/…Earnings
  Call….rtf`); `management_commentary` is PRESENT on **10/10** committed dossiers (assembled
  2026-07-10) → the transcript slice pipeline works cohort-wide.
- Anchored EX-99.1 coverage is **0 releases for 3/10 names** (CNXC, EPAM, SMPL — no 2.02/8.01 8-K
  in the recent-filings window): for those names transcripts/MD&A are the ONLY mechanism source.
- STATE.md:364-372 (PR #41 incident) records driver-grade numerics in a real call — MVST's
  "$48.2M GAAP profit, 536 MWh" — direct evidence transcript numbers of exactly this class exist.

### Design — the covenant pattern (`vinci/dossier/covenant_extract.py`), with ONE named upgrade

New `vinci/dossier/driver_extract.py`, modeled row-for-row on covenant_extract:
- **Input:** the SAME `ciq_sheets.transcript_for_synthesis(bundle)` slice (12,000-char/call budget,
  boilerplate-stripped, per-call `--- <file> ---` labels) — no new fetch, no new budget.
- **Tool `operating_drivers`:** one row per driver found — `{kind, metric, period, value (VERBATIM
  stated), quote (exact sentence), call_label}`. Required per row: `kind, metric, value, quote`.
  System-prompt rules inherit covenant `_SYSTEM` (:66-89): verbatim-only, never
  infer/compute/estimate, absent = absent, never reference instructions.
- **Machine-set source_ref** (covenant precedent :226-229): `CIQ transcript: <call filename>` —
  bound to the specific call label the row's quote sits under; the model fills values, never cites.
- **THE UPGRADE vs the covenant template (explicit, load-bearing):** covenant_extract has **no
  code-level validation** of extracted values against source (prompt-only; quotes stored for human
  grep; digit-consistency lives downstream in render RC-1.5d). Transcripts are messier than legal
  exhibits and these rows feed a decision block, so this extractor ships a **code-level verbatim
  validator**: (i) the `quote` must appear in the slice (whitespace-normalized containment);
  (ii) every numeric in `value`/`quote` must digit-trace into the slice (adapt the synthesis
  tracer's scale set + ±2%-or-0.05 tolerance — `_TRACE_SCALES`, synthesis.py:37,543-554). A row
  failing either is **DROPPED to a qa_flag** (`driver row failed verbatim trace — dropped`), never
  attached. Observed shapes justifying it: the PR #41 "536" misbinding (STATE.md:364-372) and the
  covenant $0.02/$22.00 mis-scale (STATE.md:1642-1646).
- **Cost bounds:** ≤1 LLM call per name (both calls arrive in the one slice); ≤12 rows kept
  (flag the excess count — no silent cap); no transcripts → `operating_drivers` stays
  None/UNKNOWN-flagged (the module is OPTIONAL, requirements.py:160-173 — that stays true).
- **Failure honesty (FIX-0 shape):** LLM error / empty extraction → `qa_flags` carries
  `driver extraction failed: <reason>` — never a bare header implying unseen data, never a pointer.

### The fence revision (exact scope)

The synthesis-phase fence **stays**: "Derive NO numbers" (synthesis.py:906-914) still governs the
LLM that writes bull/bear. What changes: a **separate, pre-synthesis, verbatim-validated extraction
phase** may read numbers out of the transcript — the exact precedent covenant extraction set for
Tier-2 docs (STATE.md:2905-2907 pre-authorizes this revision). Concretely:
1. `driver_extract` runs in `assemble.assemble_one` beside covenant extraction (before
   `synthesize()`), attaching `mech.operating_drivers`.
2. The transcript preamble in synthesis.py gains one sentence: *"Extracted driver figures arrive as
   `operating_drivers` facts — cite THOSE source_refs; still derive NO numbers from this text."*
3. `requirements.py` transcript module `used_for` text gains the driver-extraction mention;
   `required` stays **False** (degrades fail-honest).
4. TRANSCRIPT-FIGURE QA flag (synthesis.py:570-589) is UNCHANGED — a synthesis point citing a
   transcript number that isn't in the mechanical layer still flags; validated driver rows ARE in
   the mechanical layer, so citing them traces cleanly (shrinks that flag class honestly).

### Shape contract + ONE literal example (what the synthesis LLM sees)

`operating_drivers` rides inside the MechanicalLayer JSON the synthesis already receives (no
separate digest — the rows ARE term → value → source_ref; the covenant DIGEST existed because its
rows attach post-synthesis, which does not apply here). One literal serialized row:

```json
{"kind": "leading_indicator", "metric": "battery shipments", "period": "Q1 2026",
 "value": "536 MWh", "value_num": null, "unit": null,
 "verbatim": "<the exact sentence from the call>",
 "source_ref": "CIQ transcript: Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf",
 "tier": "llm-fenced"}
```

(Figures above are the shape illustration from the recorded PR #41 incident; the REAL values are
whatever the build's real run extracts — **VERIFY-AT-BUILD**, never trusted from this brief.)

## 4. Deterministic joins — DERIVED-PIN layer discipline

- **Materiality is a JOIN, not a product.** When a driver's segment is nameable, render the CIQ
  segment share (layer: CIQ Segments, `concentration.segments` — PRESENT on 9/10 committed
  dossiers; AORT unknown) BESIDE the driver row (layer: filing/transcript). **No cross-layer
  multiplication** — a "driver ≈ X% of revenue" number would mix layers (the DERIVED-PIN rule
  forbids exactly this; this REFINES the plan's "driver × segment share" phrasing). The human
  multiplies; the machine juxtaposes two cited facts.
- **Actions-vs-headwind is adjacency, not arithmetic.** A pricing action (filing layer) renders
  beside a stated cost headwind (transcript layer) — never netted across layers. Within-ONE-layer
  arithmetic on structured values (two anchored release numbers) is permitted, the
  net-debt/EBITDA precedent.

## 5. Synthesis bridge — prompt-level only, zero schema change

`Synthesis` keeps exactly six fields (the no-conclusion pin is untouched). The bridge is a
tool-description extension on `decisive_question.evidence_for/against`: *"when operating_drivers
rows are present, name the load-bearing driver each case rests on, citing its source_ref — POSE
what must be true for the case to hold; never forecast a value."* Soft expectation, QA-observed;
NOT test-gated (an LLM-behavior gate would be an LLM-string pin in disguise).

## 6. Render — the Mechanism block (three-tier placement)

- **md:** `## Mechanism` between "The case" and "Financial snapshot" (`render.py` `_brief_lines`,
  the :1720-1724 slot). Up to ~6 lines grouped by kind — leading indicators (latest vs prior where
  both extracted), pricing actions (dated), attribution/pass-through/competitive facts — each line
  `_fact`-style with an endnote `[n]` cite. No rows → one honest line: `_no operating drivers
  extracted (anchored patterns missed; transcript tier absent or dry)_`.
- **web:** the mirror block between `briefCase` and `financialSnapshot` (`dossier.js` `briefTier`
  :460 slot), `citeMark`-cited — the `>Source:`-scan guard
  (`test_exhibits_cite_via_endnotes_not_inline_source_caption`) stays green by construction.
- **Tiers:** the block = decision values → MAIN BODY, stays in print. Per-row `verbatim` quotes =
  provenance → ON-DEMAND (`<details>`, excluded from print). JSON = machine-complete rows.
- **Analysis tier:** the full rows table (all rows, quotes, flags) under the mechanical layer.

## 7. Verify gates (each names its supplying layer; real runs shown, not asserted)

| # | Gate | Supplying layer |
|---|---|---|
| V1 | Real committed EX-99.1 fixture (MVST/VITL/VRRM excerpt — **VERIFY-AT-BUILD** which cached release carries a KPI/pricing sentence; the cohort scan says VITL 6 releases/15 recon rows, VRRM 4/11+16 guidance are the likeliest) parses to expected `OperatingDriver` rows; a driver-free release yields `qa_flags`, zero rows | NEW anchored extraction (release_parse §A1) |
| V2 | Real MD&A attribution sentence from a cached 10-Q (**VERIFY-AT-BUILD** which of the 10 has the canonical shape) parses to an `ATTRIBUTION` row; a 10-Q without one → flag, no row | NEW anchored extraction (filing_sections §A2) |
| V3 | REAL RUN on MVST's two local transcripts → extracted rows shown, every numeric digit-traced (validator ON); then a deliberately corrupted copy (one digit changed) → row DROPPED + flag shown | NEW LLM-fenced extraction (driver_extract §3) |
| V4 | One finalist assembled end-to-end (`vinci dossier`) → `dossier.md` + web Brief render the Mechanism block, every line endnote-cited, md↔web parity; a no-driver name renders the honest empty line. **VERIFY-AT-BUILD:** the standing IWM-backfill operator to-do (STATE.md §5) runs first so re-assembly doesn't regress `stock_performance` | assembled field → render |
| V5 | ruff + `mypy --strict` + full `pytest -m "not network"` green; per-assertion sweep: no assertion's truth depends on LLM-composed text through ANY function | suite |

## 8. Pins (positive AND negative; observed failure shapes named)

1. **A1 KPI extractor** — ⊕ real-fixture rows (values + units + periods exact); ⊖ a bare year/date
   numeric near a unit word is NOT a row (the calendar-exclusion precedent, synthesis.py:454-468);
   ⊖ pattern miss → `qa_flags`, never a fabricated row (`test_release_parse_fail_loud_no_pattern`
   precedent).
2. **Money path** — ⊖ `$1,000`-convention and thousands-grouped values must not mis-scale
   (observed: `$0.02` vs `$22.00`, STATE.md:1642-1646; the `$1,101.80M`→`1` re-parse, CLAUDE.md).
3. **A2 attribution** — ⊕ canonical sentence → row carrying the price/volume/mix term; ⊖ an
   attribution verb with NO numeric → no row + flag.
4. **B validator** — ⊕ a valid row attaches with machine-set source_ref; ⊖ a numeric absent from
   the slice → DROPPED + flag (the PR #41 "536"-misbinding class); ⊖ a quote not found in the
   slice → DROPPED; ⊖ a non-str `value` (list/dict) → dropped fail-soft (covenant `_opt_str`
   shape, :182-184); ⊖ `present`-style empty value → not attached (covenant present-gating :226).
5. **Kind guard** — ⊖ an unrecognized `kind` from the LLM → row dropped + flag (never a guessed
   classification).
6. **Failure honesty** — ⊖ LLM error / no transcript / empty extraction → flags with the reason;
   NEVER a bare header or a "see the table" pointer (the FIX-0 shape, STATE.md:1596-1605).
7. **Render** — living-artifact e2e = phrasing-independent invariants ONLY (block present iff rows
   present; every line carries `[n]`; quotes only in the on-demand tier); VALUE pins live on frozen
   fixture mech objects. **Licensing constraint (hard):** Tier-B test fixtures are SYNTHETIC
   transcript-shaped prose — real CIQ transcript text is NEVER committed (CLAUDE.md security
   rule); the real-transcript evidence is the V3 shown run, not a committed fixture. (EX-99.1/10-Q
   fixtures are public-domain EDGAR text — existing convention, fine.)

## 9. Honest scope (accepted, stated up front)

- **US KPI disclosure varies by sector** → UNKNOWN-heavy names are expected and correct (fail-honest
  is the product working). The block narrows the MOSL gap; it does not make every name read like a
  covered-for-years sector note.
- **Competitive slack** (`COMPETITIVE_POSITION`) arrives ONLY via stated management claims
  (cited, tier-marked) or the human's depth work — not generically automatable.
- **3/10 committed names have no EX-99.1 path at all** (CNXC/EPAM/SMPL) — for them the block rests
  entirely on A2 + Tier B; if those also miss, the honest empty line renders.
- Anchored-lexicon breadth grows only on coverage evidence (observed `qa_flags` misses), never
  speculatively.

## 10. Out of scope (this PR)

Peer cost-structure decomposition (MOSL Ex-2 class — CIQ-manual depth-stage); KPI time-series
store; guidance-vs-actuals tracking; auto-repointing synthesis misbindings (the STATE.md:454-457
idea); any change to verdict/proposal surfaces (#116 territory).

## 11. Sequencing & cost

Build after #116 merges (branch from main). Order: **A1 → A2 (pure, fixture-pinned, zero LLM) →
Tier B → joins/render → gates**. Marginal cost: ≤1 LLM call per assembled name (bounded input =
the existing 12k/call slice); Tier A adds zero network I/O (cache hits). Two commits minimum: code
(this brief + implementation) strictly separate from any artifact re-assembly (ARTIFACT-PASS RULE).

## 12. PR completion-contract skeleton

| Brief item | Disposition (at PR time) |
|---|---|
| §1 schema | |
| §2 A1 release KPIs/pricing | |
| §2 A2 MD&A attribution | |
| §3 Tier-B extractor + verbatim validator + fence revision | |
| §4 joins (materiality adjacency; no cross-layer arithmetic) | |
| §5 synthesis bridge (prompt-level) | |
| §6 render (md + web + tiers) | |
| §7 gates V1–V5 (real outputs pasted) | |
| §8 pins 1–7 | |
| STATE.md build entry + invariant table | |
