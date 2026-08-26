---
id: 
status: recorded
date: 2026-08-04
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**OPERATOR ACTIONS — RECORDED 2026-08-04, arising from the SMPL re-assembly (see §2).**

**~~O1. RULING NEEDED~~ CLOSED — BUILT AT #347 (`fix(O1): mark the drawdown-moment guide`), candidate (a): `_mark_drawdown_guidance` (synthesis.py) marks the field through the SHARED `guidance_vintage_mark`, mark LEADING the block, accession-matched date, UNDATED mark when none — and this entry stood as an open ruling for two weeks after the fix merged (stale-record class, same as the PR-OPEN notes; corrected 2026-08-18). Original entry:** `drawdown_cause.revised_guidance` is the SECOND, UNMARKED guidance path.
#342 marked `primary_source` in the brief; the 2026-08-04 SMPL roll shows the model reading the
OTHER path and asserting APRIL's superseded guide in the present tense at `bear[1]`, with July's
guide cited nowhere. `synthesis.py:979` excludes `primary_source` from the facts dump and swaps in
the marked digest, but `drawdown_cause` goes in **raw and unmarked**. The field is correctly
historical by design (`mechanical.py:2470` — the drawdown-moment guide); it is simply not labelled
as history. **Three candidate fixes, operator's call, none built:** (a) mark it through the shared
`guidance_vintage_mark`; (b) exclude it from the dump as `primary_source` already is; (c) state the
field's meaning to the synthesis. **This is the SAME defect #343 fixed in the `scenario-propose`
template** — one derivation, two consumers, and the brief is the consumer still on the wrong field.

**O2. `llm_call.log` discards `=== USAGE ===` on every REFUSED attempt.** Written at
`assemble.py:189`, inside the block reached only after the refusal check at `:326` — so the usage
recorded by #340 survives on the converging attempt and is lost on the ones worth diagnosing (two
of three on the 2026-08-04 SMPL roll). One-line move; not done here because it is code, and this
was an artifact pass.

**O3 — FIXED 2026-08-04 in code; clause (e) is now UNMET rather than FALSE until each name
re-assembles.** `comps_as_of_date` is extracted as the ONE derivation — `comps_as_of` renders it,
`_comps_asof_suffix` stamps that onto every comps `source_ref`, and the new
`StockInfo.market_cap_as_of` carries the value; both twins (`render.py`, `dossier.js`) read the
field, and `_brief_snapshot`'s third parameter — the wiring that carried `multiples_as_of` — is
GONE, so the wrong panel cannot be passed back in. **All ten false dates are removed** (BRBR never
rendered one: its neighbour date happened to equal its price date). Verified by mutation: reverting
both twins to the old wiring reddens 3 pins.
- **THE COMMITTED DOSSIERS NOW SHOW NO CAP DATE, AND THAT IS THE DELIBERATE END STATE OF THIS PR.**
  `market_cap_as_of` is populated at ASSEMBLY; every committed dossier predates it, so the label
  falls silent rather than borrowing. **A backfill was considered and REFUSED as unsound:** the
  correct vintage for a committed cap is the one it was struck at, and the live workbooks have
  since been re-exported — AORT's committed cap is as-of `2026-06-25` against a workbook now
  reading `2026-07-30`, IT the same, VITL `2026-06-29` → `2026-07-30`. Backfilling from today's
  workbook would restamp three caps with dates 30–35 days newer than the values they label, which
  is the O3 defect rebuilt by hand. The only in-artifact copy of the true vintage is the
  `source_ref` STRING, and parsing it is the thing this fix exists to avoid.
- **OPERATOR CONSEQUENCE:** an unlabelled cap is a disclosure GAP; a mislabelled one is a FALSE
  STATEMENT. This trades the second for the first, knowingly. Each name recovers its real label the
  next time it is assembled — no separate action needed, but until then clause (e) has no live
  instance on the fleet.
- **Schema migration:** `market_cap_as_of: null` added to the 9 post-schema dossiers so a no-op
  refresh stays byte-identical (`test_a_noop_refresh_is_byte_identical`). FUBO and MVST are SKIPPED
  by derivation, not by name — they carry no `extraction_version`, so a model round-trip would
  back-fill a dozen unrelated defaulted keys (`ev_gap`, `material`, `current_guide`, `filed`).
  Each migrated file was diffed key-by-key against its original: the new key is the ONLY change.
- *Verified:* 1881 passed, 3 skipped; ruff + `mypy --strict` clean. Web preview on IT confirms
  `Market cap $8.7B` with no date today and `$8.7B (2026-06-25)` once the field is populated; the
  Snapshot sits outside any `<details>`, so the collapsed and print/force-open tiers are the same
  surface (checked, not assumed).

**O3 (ORIGINAL REPORT). THE CAP'S CLAUSE-(e) VINTAGE LABEL NAMES ANOTHER PANEL'S DATE — 11 of 11.**
`render.py:2668` passes `valuation.implied_expectations.multiples_as_of` into
`_brief_snapshot(cap_as_of=…)`, so the snapshot renders `cap $909M (2026-07-21)` while the cap's own
`source_ref` reads `as-of 2026-07-24`. Clause (e) exists so a frozen value beside a live one is
marked *with its vintage*; this marks it with a different panel's. **IT is the worst case — label
`2026-07-27`, cap actually `2026-06-25`** (five weeks presented as three days). The label is the
only thing discharging clause (e) — `reconcile_cap`'s result is used solely as a gate
(`assemble.py:253`) and is never stored or rendered — so when it is wrong, nothing else covers it.
**Blocked on an extractor change:** no structured cap as-of exists; the vintage is only inside the
`source_ref` string, and parsing it there would be the divergent-string-parse bug class. The fix is
to have the CIQ cap extractor expose its as-of as a structured value, then bind the label to it.
Newly urgent because SMPL's cap-vs-spot divergence is now 9.2%, not 0.3%.

**O3 (SECOND HALF) — CLAUSE (e) NOW RENDERS THE MAGNITUDE, NOT ONLY THE VINTAGE (2026-08-12,
fix/render-cap-drift).** Found by the analyst reading UBER's page, and the sentence above named the
gap before anyone hit it: *"`reconcile_cap`'s result is used solely as a gate and is NEVER STORED OR
RENDERED"*. It computes `implied_price` and `gap` on every build; `check_freshness` deliberately
does not fail on ordinary drift (failing would stop 8 of 14 — "a freeze wearing a guard's name") and
hands the disclosure to rendering; rendering shipped the DATE and dropped the NUMBER. UBER printed
`CMP $78.54 · cap $139.3B (2026-08-06)` — two figures 13.2% apart, unreconciled — so the analyst had
to fetch the share count and recompute to find that NTM EV/EBITDA reads 11.89x where the current
price gives ~13.6x. **A reader cannot infer 13% from a date.**
**KEYED ON THE GAP, NOT THE VINTAGE, and that is the load-bearing choice:** 8 of the 14 names carry
**no `market_cap_as_of` at all**, so a date-keyed caveat renders blank on the three LARGEST drifts
(AORT −18.4%, VITL −19.0%, MVST +17.6% — all undated). The gap is computable whenever cap, shares
and spot are present, which is what the reconciliation already requires. Pinned, so a future
re-keying on the vintage reddens.
**SILENT INSIDE THE TOLERANCE the guard itself uses** — BRBR/CNXC/EPAM/NFLX/V/VRRM say nothing, so
the mark means something wherever it appears. **A SHARE-BASIS mismatch is worded differently**
(FUBO: `⚠ SHARE-BASIS MISMATCH: implies $0.75/sh vs CMP`, no percentage): drift invites re-dating
the cap and reading on, which is the wrong remedy for a page where no per-share figure holds.
*DERIVED at render from the three fields already in the JSON — no schema change, no stored field, and
the machine-complete tier still reproduces it (pinned). Real run over all 14 committed names; the
ARTIFACT PASS re-rendered the 8 that moved (AORT/FUBO/IT/MVST/NCNO/SMPL/UBER/VITL), render-only via
`_rerender_only` — `dossier.json` untouched, no synthesis re-rolled, and every artifact diff is
EXACTLY ONE LINE (the Snapshot). 6 pins incl. the fleet sweep (any name drifting past tolerance whose
page is silent reddens); 4 of them FAIL without the renderer change. ruff + mypy --strict (124) +
pytest 2380 green.* **PREVIEW RULE: this is a render change — the preview is in the PR body and it
awaits approval before merge.** **Does NOT fix O3's original defect** (the label still names another
panel's date where a vintage exists) — that is blocked on the structured cap as-of, unchanged above.
