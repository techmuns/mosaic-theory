> **FOSSIL — superseded, kept for the reasoning.** Last substantive change 2026-06-18. Nothing live
> cites this: it is referenced only by other fossils (`planning/`), which CLAUDE.md already calls
> "the planning fossils". Read it for WHY a decision was made, never for what is true now — the
> current state is STATE.md §5.0 OPEN NOW, and the operating loops are docs/RUNBOOKS.md.
> *Banner added by P0 of the knowledge-ledger plan; the file itself is unchanged below.*

# Loop 1 — Build Plan (Claude Code runbook)

**Version:** v0.2 · **Owner:** Munshot Research · **Goal:** build the **first production slice of the real system** — thin in *scope* (one screen, thin ingestion), production-grade in *quality* — and run it in **paper mode** (records and scores decisions against live data, deploys no capital) as the validation gate before capital. Real software we keep and extend, not a throwaway prototype. This is the **next action** — not another spec.

> **Working rule for Claude Code:** build **one component at a time, and verify each by running it** against real data, not by asserting it's correct. Do not build the deferred layers (harness, portfolio, execution, monitoring). The depth discriminator stays **manual** (your A/B/C source-binding framework + CIQ) — code builds the plumbing around it, never the judgment. Write **production-quality, extensible code** (clear typed modules, tests) — this is the fund's engine; "thin" constrains *scope*, never quality.

## Docs to load (paste/attach these to Claude Code)

- **Primary (build from these):** `MINIMAL_LOOP.md` (what Loop 1 is + the measurement protocol) · `INGESTION_LAYER.md` (the data-spine spec) · `FUNNEL_SCREENS.md` (Screen 2 gates).
- **Context:** `EDGE_THESIS.md` (Edge 2 + its twin — what the discriminator judges) · `OBJECTIVE_FUNCTION.md` (the fences) · `AI_NATIVE_FUND_BUILD_BRIEF.md` (overall architecture).
- **Graph track (alongside):** `GRAPH_LOOP.md` (Test 0 + Test 1).
- **This file:** the build sequence.

## Scope of the slice (deliberately minimal)

US-only, one cap band (this is also the recommended US-first direction — EDGAR is the only free programmatic fundamental feed; the resolver/EOD/store are reusable if you later go global). Thin ingestion → **one** screen (Screen 2, overshot de-rating) → the existing manual discriminator → a decision ledger → a scoring harness → run forward. Nothing else.

---

## Build steps (in order; each ends with a run-to-verify)

**0 · Scaffold & contracts.** Repo + Python env; a config defining the US universe (exchange filter + cap band). Encode the two schemas as code: the **data-record envelope** `(value, as_of, source, coverage_status)` and the **candidate-record** `(data-record + screens_fired + gate_results + trigger + unknown_gates_for_depth + twin_to_rule_out + triage_band)`.
*Verify:* config loads; both schemas instantiate.

**1 · US entity resolver — build first, harden hardest (the #1 risk).** SEC `company_tickers.json` → CIK ↔ ticker ↔ name → a stable internal ID. **Fail loud** on ambiguity (multiple CIKs, ticker reuse/changes).
*Verify by running:* resolve ~20 known names including tricky ones (dual-class, recent ticker changes) and confirm correct CIK; feed a deliberately ambiguous input and confirm it errors rather than guessing.

**2 · Local store (SQLite).** Tables keyed by internal ID: `universe`, `prices`, `fundamentals`, `events`, `candidate_records`, `decision_ledger`; envelope fields on every data row.
*Verify:* write/read round-trip; `coverage_status` defaults to UNKNOWN where data is absent.

**3 · EOD client (Stooq, free).** Daily OHLCV for the universe → store. Compute Screen-2 price features: drawdown-from-high, trailing return vs index/sector, distance from 52-week low, volume/ADV.
*Verify by running:* pull a known name and eyeball the computed drawdown/features against a chart; confirm stale data flips `coverage_status`.

**4 · EDGAR client.** XBRL `companyfacts`/`frames` → the fundamentals Screen 2's gates need (valuation-vs-own-history, quality/leverage). 8-K **full-text search** → de-rating event detection (the trigger).
*Verify by running:* pull one company's `companyfacts` and confirm key line items; run an 8-K search and confirm event hits; missing fundamentals → UNKNOWN, not a crash.

**5 · Screen 2 (overshot de-rating) as gates.** Implement the **trigger** (recent event + material price drop) and the coarse **overshoot-candidate gates** as PASS / FAIL / **UNKNOWN** (per `FUNNEL_SCREENS` — gates, never a composite score). Emit candidate-records with `trigger`, `twin_to_rule_out = "terminal decline"`, `unknown_gates_for_depth`, `triage_band`.
*Verify by running across the universe:* inspect the candidate list for **face-validity** (do these read as genuine de-ratings?). Tune gates by face-validity **only — never by forward returns** (that's the overfitting trap the spec forbids).

**6 · Decision ledger + entry workflow.** A structured ledger (table + a simple CLI/form) where every candidate the PM runs through the discriminator gets a recorded verdict: **BUY** or **AVOID-terminal**, the twin call, entry price, a short thesis, kill-criteria, horizon, confidence, timestamp. **Log AVOIDs too — they are half the validation set.** The discriminator judgment itself is manual (PM + CIQ + A/B/C); code builds only the ledger/IO and freezes the entry price + `as_of`.
*Verify:* log a sample verdict; confirm all fields persist with a frozen entry price.

**7 · Scoring harness.** For each logged verdict, at interim checkpoints + the thesis horizon, pull forward EOD prices and compute: the **BUY−AVOID spread** (primary), hit-rate (% BUY > benchmark, % AVOID < benchmark), return vs a US small-cap index (gross then net of est. costs), a beta/alpha regression (wide error bars — tiny n), and twin-realisation (did AVOID-terminal keep falling, BUY-overshoot bounce?). Output a short report.
**Pre-register the kill criteria in the README *before* running** (continue if BUY−AVOID clearly positive over ≥2 quarters of resolved verdicts + sound twin-engagement; kill if spread ≈0/negative or all return is beta).
*Verify by running on a few backfilled historical de-ratings* — purely to test the **math**, never as evidence (their outcomes are already known). Then it's ready for live forward verdicts.

**8 · Automate (configure once, never manual).** Put it in a GitHub repo; a **scheduled GitHub Actions** workflow runs the weekly screen + monthly scoring automatically — configure once, runs forever, no manual re-runs. When you later build a results dashboard, wire it **GitHub → Cloudflare Pages** auto-deploy (configure once). The pipeline never needs a manual repeat step.

---

## Graph track — run alongside (cheap, offline, separate)

Per `GRAPH_LOOP.md`, these de-risk the moat in parallel and need no live forward loop:
- **Test 0 (graph quality, now):** build the thin **1-hop** graph — EDGAR full-text "who-names-whom" + LLM extraction, **entity-resolved**, every edge carrying **provenance (the filing line)**. Measure precision / recall / entity-accuracy against CIQ Customers & Suppliers + filing text on a sample. **Kill if poor** — a noisy graph makes the edge uncapturable regardless.
- **Test 1 (does lag exist):** historical event study. Define the connected set from a **pre-shock point-in-time** linkage snapshot (**confirm point-in-time linkage is obtainable before relying on this** — current-only links contaminate it). Measure whether connected names re-rate *after* the obvious names. **Kill if no lag.**

## What you are NOT building now

Verification harness, full depth-integration, portfolio/sizing/risk, execution, monitoring — all **deferred until Loop 1 shows a positive BUY−AVOID spread**. The forward graph-capture rig (Test 2) waits until Loop 1 and Test 1 clear.

---
*This is the real system in its paper phase; the cost of that phase is patience, not money. When Loop 1 has resolved verdicts and the scoring report shows a spread (or doesn't), that result — not another document — decides what gets built next.*
