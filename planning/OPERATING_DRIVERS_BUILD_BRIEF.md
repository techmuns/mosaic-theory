# BUILD BRIEF — `operating_drivers`: the mechanism-coverage tier (PR-B)

> STATUS: **DRAFT v2 — awaiting operator sign-off. No code until signed off.**
> v2 (2026-07-13): re-grounded on a PRE-SIGN-OFF DATA DIAGNOSIS over the actual local substrate
> (SEC cache · CIQ store · committed dossiers) — v1's Tier-B coverage claim was WRONG and is
> corrected below; one new anchored source (Key Developments) was found on disk, unconsumed.
> Drafted 2026-07-13 · genesis: the MOSL Mahanagar Gas audit (STATE.md §5 QUEUED entry in #116)
> · builds **after PR #116 (verdict-first) merges**.
> Vocabulary per CLAUDE.md BRIEF CONTRACT: **anchored** = deterministic (heading/regex, CI-pinned on
> committed real-text fixtures); **LLM-fenced** = an LLM extraction phase. Bare "fenced" is malformed.

## 0. Objective — the 90-second mechanism handover

The Brief's case points are source-bound but ATOMIZED: no leading indicator with its base rate, no
pricing actions vs headwinds, no attribution of results to price/volume/mix, no dated event trail.
This build assembles those facts as **typed, cited, verbatim-validated rows** on the mechanical
layer and renders a compact **Mechanism** block on the Brief.

**The line (unchanged by the #116 pivot):** assemble-and-cite only. Rows are stated facts with
source_refs; the block POSES, never forecasts (anti-model: MOSL's "we estimate a further
INR2–3/kg"). No new verdict surface; execution untouched; `Synthesis`'s six-field no-conclusion pin
(tests/test_dossier.py `test_synthesis_is_the_only_llm_output_and_carries_no_conclusion`) stands.

## 0.5 PRE-SIGN-OFF DATA DIAGNOSIS (2026-07-13, this machine) — what actually exists

Run over the disk-cached EDGAR texts of the 10 committed finalists' own filings
(`data/cache/sec/`, 89 cache entries matched to dossier accessions), the local CIQ store
(`data/manual/ciq/`), and the committed dossiers (assembled 2026-07-10):

| Source | Diagnosed reality | Consequence |
|---|---|---|
| 10-Q MD&A (cached, unparsed today) | Canonical attribution sentences CONFIRMED in real text — CNXC ("increased $9.0M, or 0.6%, due to … currency"), MVST ("decreased by $32.0M, or 43.6%, … primarily due to the decrease in sales volumes"), SMPL (2 hits) — with a strict single-regex probe; looser tiered anchors will catch more | **A2 is the strongest anchored source** — and it rescues CNXC/SMPL, two of the three no-release names |
| EX-99.1 (cached, parsed today for other sections) | Pricing-action language REAL for VITL ("Strategic Pricing Actions; … raise our full-year revenue g[uidance]"); AORT's 12 probe hits are ALL M&A boilerplate ("purchase price adjustments" in a merger exhibit). KPI-with-unit yield THIN and noisy: 3 tickers hit; 2 of 3 fragments are false-positive-class (FUBO: an expense line item; MVST: a product spec "290Ah cell", not a volume) | **A1 pricing kept WITH an M&A-boilerplate exclusion (new observed negative shape); A1 KPI demoted** — narrow lexicon, low expected yield on this cohort |
| CIQ **Key Developments** (on disk 10/10, classified kind `key_developments` at ciq.py:169, consumed by NOTHING) | Real-RTF (striprtf parses — NO LibreOffice needed). Structured `Date \| Type \| Headline \| Other Parties` rows + a "Situation:" detail line; MVST 67 dated rows / AORT 54 (1-year window). Export categories INCLUDE "Company Forecasts and Ratings" (guidance events) and "Customer/Produc[t]…" | **NEW anchored source A3** — dated, typed event rows for free; replaces much of what v1 over-assigned to A1-KPI and Tier B |
| CIQ transcripts (2 calls × 10/10 on file) | **`transcript_for_synthesis` returns None for ALL names on this machine — LibreOffice is NOT installed** (the OLE-disguised RTFs need it; `vinci/ciq/manual.py:56` fails loud per file, but `ciq_sheets.transcript_for_synthesis` swallows per-workbook `CiqParseError` → silent None). The committed 2026-07-10 MVST dossier cites ZERO transcript points; `management_commentary` is a POINTER ("2 transcripts on file") — it proves file EXISTENCE, NOT parse success. v1 read it as pipeline-works-cohort-wide: **wrong** | **Tier B is BLOCKED today** — gated below on the LibreOffice unlock + a SHOWN parsed slice. Plus a standalone fail-loud fix: transcripts-on-file-but-unparsed must FLAG, never silently vanish |
| Segments (CIQ) | PRESENT 9/10 (AORT unknown) | materiality JOIN available for 9/10 |

Historical note: transcript-sourced figures DID reach a synthesis once (the PR #41 "$48.2M / 536
MWh" incident, STATE.md:364-372) — the pipe works when LibreOffice exists; it does not exist here
now.

## 1. Schema — supplying layer: NEW assembled field (`vinci/dossier/schemas.py`)

```python
class DriverKind(enum.StrEnum):
    LEADING_INDICATOR = "leading_indicator"      # a unit-volume/KPI run-rate
    PRICING_ACTION = "pricing_action"            # a dated price change taken/announced
    ATTRIBUTION = "attribution"                  # MD&A price/volume/mix causality sentence
    EVENT = "event"                              # a dated Key-Developments row (typed headline)
    PASS_THROUGH_STRUCTURE = "pass_through_structure"  # indexation/contract pass-through facts
    COMPETITIVE_POSITION = "competitive_position"      # stated competitive slack/position

class OperatingDriver(BaseModel, frozen=True):
    kind: DriverKind
    metric: str                 # "average selling price", "revenue attribution", KD event type
    period: str | None = None   # as STATED; None when unstated
    value: str                  # the VERBATIM stated value
    value_num: float | None = None  # structured numeric — ANCHORED rows only (we parsed it);
    unit: str | None = None         # LLM-fenced rows leave these None (verbatim-only discipline)
    verbatim: str               # the exact sentence/row read from (the human greps for it)
    source_ref: str             # MACHINE-SET by the extractor — the model never invents a citation
    tier: str                   # "anchored" | "llm-fenced" — extraction-path provenance

class OperatingDriversExtract(BaseModel, frozen=True):
    rows: list[OperatingDriver] = Field(default_factory=list)
    qa_flags: list[str] = Field(default_factory=list)  # every miss/drop/parse-failure is loud

# MechanicalLayer — optional-with-default-None, the #98 back-compat precedent
# (STATE.md:2985-2987; mirrors primary_source/key_ratios):
operating_drivers: OperatingDriversExtract | None = None
```

- "Parsers consume structured values": anchored rows ALSO expose `value_num`/`unit`; code consumers
  read those, never re-parse `value`. LLM-fenced rows are verbatim-only (covenant precedent).
- KD rows are CIQ-DERIVED facts (`{value, source_ref}`) — committable per the existing rule (same
  class as `key_ratios`); never the raw RTF.

## 2. Tier A — ANCHORED extraction (deterministic; zero LLM; zero new dependencies; builds first)

Build order **A2 → A3 → A1** (strongest diagnosed yield first).

### A2 — 10-Q MD&A price/volume/mix attribution (`vinci/edgar/filing_sections.py`) — PROMOTED

New anchored section `_results_attribution` in the existing 10-Q section parser (anchor-tier
precedent: `_CUST`/`_CUST_EXACT`/`_CUST_FLOOR`, :114-124), targeting the canonical MD&A shape
CONFIRMED in the cached real texts (§0.5): *"[metric] (increased|decreased) [by] $X million, or
Y%, … (primarily|principally) (due to|driven by|attributable to) …"* → `ATTRIBUTION` rows with
`value_num` (the $ and % deltas) + the attribution clause verbatim. **First consumer of MD&A body
text** — the full normalized 10-Q is already materialized (mechanical.py:1810) and disk-cached; no
new fetch. Anchor tiers widen only on observed `qa_flags` misses.

### A3 — CIQ Key Developments (NEW module `vinci/dossier/ciq_sheets.py` extractor) — NEW IN v2

The on-disk, classified, unconsumed export (10/10 names). Anchored RTF parse (striprtf — real RTF,
no LibreOffice): the `Date | Type | Headline | Other Parties` table + per-row "Situation:" detail →
`EVENT` rows `{kind=EVENT, metric=<KD Type>, period=<date>, value=<headline>, verbatim=<situation
line>, source_ref="CIQ Key Developments: <filename> · <date>"}`. Type-filter at face-validity to
mechanism-relevant categories (guidance/forecast changes, client/product announcements, capacity/
transactions); exec-change/board noise excluded — the filter list is declared in code, extendable
per observed misses. Rows are derived facts; the raw RTF stays git-ignored.

### A1 — EX-99.1 pricing actions (+ narrow KPI) (`vinci/edgar/release_parse.py`) — DEMOTED in v2

A fifth section extractor `_operating_drivers(text, source_ref)` (precedent: `_guidance` :209):
- **Pricing-action sentences** (diagnosed REAL: VITL) → `PRICING_ACTION`, dated where stated.
  **With the diagnosed exclusion:** M&A/legal boilerplate — `purchase price adjustment|merger|
  acquisition agreement` context — must NOT match (observed false-positive shape: AORT's merger
  exhibit, §0.5).
- **KPI-with-unit sentences** → `LEADING_INDICATOR`, but expectations set by the diagnosis: thin
  yield on this cohort, and the two observed false-positive classes are pinned OUT (an expense
  line item carrying a unit word — FUBO shape; a product spec — MVST "290Ah cell" shape: require a
  shipped/delivered/added/served verb governing the number, not adjacency alone). FIXED narrow
  lexicon; widen only on observed misses.

Feeds from the EXISTING fetch (mechanical.py:1789-1803); raw text disk-cached → zero new I/O.

## 3. Tier B — LLM-FENCED transcript extraction — **GATED (blocked today)**

**GATE (hard, per the don't-build-speculatively rule):** Tier B code is written only after BOTH:
1. **Operator installs LibreOffice** (`brew install --cask libreoffice` — machine dependency, not a
   CIQ export; `_find_soffice` already probes `/Applications/LibreOffice.app/...`, manual.py:22-24).
2. A **shown real run**: `transcript_for_synthesis` returns a non-None parsed slice for ≥1 finalist
   on this machine.

Until then Tier B is DEFERRED-in-brief; Tiers A2/A3/A1 ship without it (the Mechanism block renders
from anchored rows alone).

**Ships NOW regardless (fail-loud fix, small):** `transcript_for_synthesis`'s silent degrade —
transcripts on file but ZERO parsed (`CiqParseError` swallowed per workbook, ciq_sheets:1830-1838)
→ assembly must flag `transcripts on file but unparseable (LibreOffice missing?)` into the dossier
QA flags. The 2026-07-10 cohort assembled in exactly this state with no trace — that is the
fail-loud principle violated, independent of PR-B.

### Design once unlocked — the covenant pattern with ONE named upgrade

New `vinci/dossier/driver_extract.py`, modeled on covenant_extract:
- **Input:** the SAME `transcript_for_synthesis` slice (12,000-char/call budget, per-call labels) —
  no new fetch, no new budget.
- **Tool `operating_drivers`:** one row per driver — `{kind, metric, period, value (VERBATIM),
  quote (exact sentence), call_label}`. System rules inherit covenant `_SYSTEM` (:66-89):
  verbatim-only, never infer/compute, absent = absent.
- **Machine-set source_ref** (covenant precedent :226-229): `CIQ transcript: <call filename>`.
- **THE UPGRADE (explicit):** covenant_extract has NO code-level validation of values against
  source (prompt-only; quotes for human grep; digit-consistency lives downstream in render
  RC-1.5d). Transcripts are messier and these rows feed a decision block → this extractor ships a
  **code-level verbatim validator**: (i) `quote` must appear in the slice (whitespace-normalized
  containment); (ii) every numeric in `value`/`quote` must digit-trace into the slice (adapt the
  synthesis tracer's scales + ±2%-or-0.05 tolerance — `_TRACE_SCALES`, synthesis.py:37,543-554).
  A failing row is **DROPPED to a qa_flag**, never attached. Observed shapes: the PR #41 "536"
  misbinding (STATE.md:364-372); the covenant $0.02/$22.00 mis-scale (STATE.md:1642-1646).
- **Cost bounds:** ≤1 LLM call/name; ≤12 rows kept (excess flagged — no silent cap); no
  transcripts → None + flag (module stays OPTIONAL, requirements.py:160-173).
- **Failure honesty (FIX-0 shape):** LLM error / empty extraction → `qa_flags` carries
  `driver extraction failed: <reason>` — never a bare header, never a pointer.

### The fence revision (exact scope; unchanged from v1)

The synthesis-phase fence **stays** ("Derive NO numbers", synthesis.py:906-914). A separate,
pre-synthesis, verbatim-validated extraction phase may read transcript numbers — the covenant
precedent (STATE.md:2905-2907 pre-authorizes). Concretely: (1) `driver_extract` runs beside
covenant extraction in `assemble_one`, before `synthesize()`; (2) the transcript preamble gains:
*"Extracted driver figures arrive as `operating_drivers` facts — cite THOSE source_refs; still
derive NO numbers from this text."*; (3) requirements.py `used_for` text updated, `required` stays
False; (4) TRANSCRIPT-FIGURE QA flag unchanged (validated rows ARE mechanical → cite-traceable).

### Shape contract + ONE literal example (what the synthesis LLM sees)

Rows ride inside the MechanicalLayer JSON (no separate digest — the covenant digest existed because
its rows attach post-synthesis; not applicable here). One literal serialized row:

```json
{"kind": "leading_indicator", "metric": "battery shipments", "period": "Q1 2026",
 "value": "536 MWh", "value_num": null, "unit": null,
 "verbatim": "<the exact sentence from the call>",
 "source_ref": "CIQ transcript: Microvast Holdings, Inc., Q1 2026 Earnings Call, May 11, 2026.rtf",
 "tier": "llm-fenced"}
```

(Shape illustration from the recorded PR #41 incident; REAL values come from the build's shown
run — VERIFY-AT-BUILD, never trusted from this brief.)

## 4. Deterministic joins — DERIVED-PIN layer discipline (unchanged from v1)

- **Materiality is a JOIN, not a product:** the CIQ segment share (layer: CIQ Segments; PRESENT
  9/10, AORT unknown) renders BESIDE a driver row (layer: filing/CIQ-KD/transcript). NO cross-layer
  multiplication (DERIVED-PIN rule; refines the plan's "×" phrasing). The human multiplies; the
  machine juxtaposes.
- **Actions-vs-headwind is adjacency, not arithmetic.** Within-ONE-layer arithmetic on structured
  values is permitted (the net-debt/EBITDA precedent).

## 5. Synthesis bridge — prompt-level only, zero schema change (unchanged from v1)

Tool-description extension on `decisive_question.evidence_for/against`: *"when operating_drivers
rows are present, name the load-bearing driver each case rests on, citing its source_ref — POSE
what must be true; never forecast."* Soft, QA-observed; NOT test-gated (an LLM-behavior gate is an
LLM-string pin in disguise).

## 6. Render — the Mechanism block (three-tier placement; unchanged from v1)

- **md:** `## Mechanism` between "The case" and "Financial snapshot" (`_brief_lines` :1720-1724
  slot); ≤6 lines grouped by kind, each endnote-cited; no rows → one honest line: `_no operating
  drivers extracted (anchored patterns missed; transcript tier gated/dry)_`.
- **web:** between `briefCase` and `financialSnapshot` (`briefTier` :460), `citeMark`-cited — the
  `>Source:` guard stays green by construction.
- **Tiers:** block = decision values → MAIN BODY, in print. Row `verbatim` quotes = provenance →
  ON-DEMAND. JSON = machine-complete. Analysis tier carries the full rows table + flags.

## 7. Verify gates (each names its supplying layer; real runs shown, not asserted)

| # | Gate | Supplying layer |
|---|---|---|
| V1 | The DIAGNOSED real sentences parse: CNXC/MVST/SMPL cached-10-Q attribution sentences (§0.5 fragments) → `ATTRIBUTION` rows with correct $/% `value_num`; a 10-Q without the shape → flag, no row | NEW anchored extraction (filing_sections §A2) |
| V2 | MVST/AORT Key Developments RTFs parse to typed dated `EVENT` rows (counts shown; type-filter applied); a KD file with no mechanism-relevant rows → flag, no rows | NEW anchored extraction (ciq_sheets §A3) |
| V3 | VITL cached EX-99.1 pricing sentence → `PRICING_ACTION` row; AORT's merger-exhibit "purchase price adjustments" text → ZERO rows (the exclusion, shown) | NEW anchored extraction (release_parse §A1) |
| V4 | **Gated:** post-LibreOffice-install, a shown non-None parsed slice, THEN the Tier-B real run (rows + validator drop on a corrupted copy) | NEW LLM-fenced extraction (§3) |
| V5 | One finalist assembled end-to-end → Mechanism block on md + web, every line cited, md↔web parity; a no-driver name renders the honest empty line. **VERIFY-AT-BUILD:** run the standing IWM-backfill first (STATE.md §5) | assembled field → render |
| V6 | ruff + `mypy --strict` + full `pytest -m "not network"` green; per-assertion sweep: no assertion depends on LLM-composed text through ANY function | suite |

## 8. Pins (positive AND negative; observed failure shapes named)

1. **A2 attribution** — ⊕ the three diagnosed real sentences (frozen as committed public-domain
   fixtures, the test_filing_sections convention) → exact rows; ⊖ attribution verb with no numeric
   → no row + flag.
2. **A1 pricing** — ⊕ VITL sentence → dated row; ⊖ **"purchase price adjustment" / merger-exhibit
   context → NO row** (observed shape: AORT, §0.5 diagnosis).
3. **A1 KPI** — ⊕ a genuine volume sentence (fixture TBD from cache at build); ⊖ **an expense line
   item carrying a unit word → NO row** (FUBO shape); ⊖ **a product spec ("290Ah cell") → NO row**
   (MVST shape); ⊖ bare year/date numerics excluded (calendar precedent, synthesis.py:454-468).
4. **A3 KD** — ⊕ dated typed rows from the real RTF structure; ⊖ excluded categories
   (exec/board changes) yield no rows; ⊖ a criteria/header line is never a row.
5. **Money path** — ⊖ `$1,000`-convention and thousands-grouped values must not mis-scale
   (observed: $0.02-vs-$22.00, STATE.md:1642-1646; the `$1,101.80M`→`1` re-parse, CLAUDE.md);
   ONE shared numeric helper across A1/A2 (VERIFY-AT-BUILD whether release_parse already has one).
6. **Transcript fail-loud fix** — ⊕ transcripts-on-file + zero-parsed ⇒ a qa_flag (the 2026-07-10
   silent state, now impossible); ⊖ no-transcripts-on-file ⇒ NO flag (absence is not failure).
7. **B validator (gated)** — ⊕ valid row attaches; ⊖ numeric absent from slice → DROPPED + flag
   (PR #41 "536" class); ⊖ quote not found → DROPPED; ⊖ non-str value → dropped fail-soft
   (covenant `_opt_str` shape); ⊖ unrecognized `kind` → dropped + flag.
8. **Render** — living-artifact e2e = phrasing-independent invariants ONLY; VALUE pins on frozen
   fixtures. **Licensing (hard):** KD/transcript test fixtures are SYNTHETIC structure-alikes —
   real CIQ text is NEVER committed; the real-CIQ evidence is the shown run. (EX-99.1/10-Q fixtures
   are public-domain EDGAR — existing convention.)

## 9. Honest scope (v2-corrected)

- Per the diagnosis: A2 rescues 2 of the 3 no-release names TODAY; EPAM showed 0 attribution hits
  with the strict probe → it may render the honest empty block until anchors widen or Tier B
  unlocks. **That is the product working**, not a defect.
- A1-KPI yield on this cohort is LOW — stated up front; the lexicon grows only on observed flags.
- Competitive slack arrives only via stated management claims (Tier B, gated) or human depth work.
- Tier B is BLOCKED on an environment unlock the operator owns; the brief ships value without it.

## 10. Operator asks (the §0.5 consequences — nothing else needed)

1. **Required for Tier B only:** install LibreOffice (`brew install --cask libreoffice`). No new
   CIQ export is required for ANY tier — A1/A2 read the SEC cache; A3 reads the on-disk KD files.
2. **Optional, single re-pull, operator's call:** the current Key Developments exports were pulled
   with a category subset ("Announced/Completed Transactions, Bankruptcy Updates, Company Forecasts
   and Ratings, Corporate Structure Related, Customer/Produc[t]…", 1-year window). If CIQ's export
   dialog offers product/client-announcement or guidance categories NOT in that subset, a fuller
   re-pull per name raises A3 yield — useful, never blocking.
3. **Optional, per-name at depth stage:** where CIQ offers an industry-specific OPERATING-METRICS
   panel for a finalist (subs/capacity/store counts), that single-name export feeds
   `LEADING_INDICATOR` rows directly — the one export class that would materially add what filings
   under-disclose. Not required for this build.

## 11. Sequencing & cost

After #116 merges: **fail-loud transcript flag → A2 → A3 → A1 → render/joins → (gate) Tier B**.
Marginal cost: zero LLM calls until Tier B unlocks; then ≤1 call/name bounded by the existing 12k
slice. Tier A adds zero network I/O (cache + local RTF). Code commits strictly separate from any
artifact re-assembly (ARTIFACT-PASS RULE).

## 12. PR completion-contract skeleton

| Brief item | Disposition (at PR time) |
|---|---|
| §1 schema | |
| §3-now fail-loud transcript flag | |
| §2 A2 MD&A attribution | |
| §2 A3 Key Developments | |
| §2 A1 release pricing/KPI (+ exclusions) | |
| §4 joins | |
| §5 synthesis bridge (prompt-level) | |
| §6 render (md + web + tiers) | |
| §7 gates V1–V6 (real outputs pasted) | |
| §8 pins 1–8 | |
| §3 Tier B (GATED — built only post-unlock + shown slice) | |
| STATE.md build entry + invariant table | |
