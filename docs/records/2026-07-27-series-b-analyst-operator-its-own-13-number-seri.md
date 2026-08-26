---
id: 
status: recorded
date: 2026-07-27
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

#### SERIES B — ANALYST / OPERATOR (its own 13.. number series)

13. **EPAM underwrite — RUN 2026-07-21, VERDICT PENDING.** `scenarios/EPAM.json` written and
   computed standalone (R1, EV/EBITDA); card shipped at `pending_analyst` — the machine
   recorded the bar test, it did NOT decide. Legs (live spot $89.40, Polygon close
   2026-07-20): bear $63.14 · base $163.08 · bull $291.24 (printed, never in the ratio);
   reward 73.68 / risk 26.26 = **2.81:1 PASS** at the 2.0 bar; market-implied bear weight
   **74%**. Margin legs are set on the REGIME-SPLIT post-2022 EDGAR window (median 11.10%,
   base takes a ~60bps trajectory haircut to 10.5%), NOT the 10-FY blend (11.90% — straddles
   the 2022 break) and NOT pre-war (13.27% — dead regime); the multiple sits below the
   post-2022 median (15.16x), not the bubble-era full-blend 22.41x. The three `method`
   sentences are **DRAFT — ratify at review**. **Analyst decision outstanding** — the verdict
   lands as its own data-only pass. **HELD pending the Q2 print (~2026-08-07 — the filer's
   own cadence, an ESTIMATE, not a date certain).** **AMENDED 2026-07-22 (pre-verdict, D&A vintage):** the committed
   `d_and_a` was **45.317 — the abandoned combined tag's FY2019 value**, carried forward six years
   by alias ordering (defect fixed in #182). Corrected to **124.811** (FY2025, accession
   `0001352010-26-000015`). Legs UNTOUCHED; only the fact moved. Recomputed: bear **$71.94** ·
   base **$181.42** · bull **$317.65**; ratio **5.27** at the recorded $89.40 (was 2.81).
   **The 2:1 bar is now met at any spot ≤ $108.43** (was ~$96.45) — headroom at the 2026-07-21
   close of $89.22 is **+21.5%**, against ~8% before. The band cross-check moved with it: EPAM's
   implied-D&A ratio was the book's worst honest reading at **4.20x** and now sits at **1.52x**,
   in line with IT 0.90x / BRBR 1.33x / AORT 1.38x / CNXC 1.68x / SMPL 1.79x — **the stale
   denominator WAS the outlier.** Verdict stays `pending_analyst`; methods stay DRAFT. EPAM now rides the monitor freshness panel as `verdict pending`.
14. **BRBR — QUEUE A FULL R1 UNDERWRITE, POST-AUGUST-WINDOW.** The last of the three dispositions
   still open; CNXC and VITL were closed 2026-07-21 (`R1_NOT_ROBUST` and `R2_NEEDED`). BRBR passes
   both band guards, so its anchor is usable. **Basis = the 2026-07-21 disposition pull**, whose
   one contested item is now settled: `book value/share −$4.28` IS committed and sourced
   (`mechanical.stock_info.book_value_ps`) — the pull's "unsourced" finding was a false negative.
   Hold until after the August print window for the same reason EPAM is held.
15. **HAND-READ PACKAGED-FOOD SECTOR MEDIAN — OPTIONAL DEPTH, NOT REQUIRED.** GIS / BGS / CAG /
    KHC / HAIN need their income statements read BY HAND (impairments isolated per the tag-overlap
    rule above) before a sector median is admissible. **Explicitly optional:** the SMPL
    verification was decided on the clean-comp RANGE (6.08–8.57x), which governed and was
    sufficient. Do this only if a future name's bear leg turns on the median rather than the
    range.
16. **CIQ ESCALATION — VITL `TEV/LTM EBITDA` (LOW PRIORITY, operator).** Reproducible statement
   drafted: *VITL (NasdaqGM:VITL), Financials→Multiples — `TEV/LTM EBITDA` is populated against a
   rent-adjusted denominator. Backing it out of the sheet's own TEV gives ~393 against EBITDAR
   ~390.5 (1.007x) and EBITDA 79.5 (4.94x), across every recent period; `TEV/LTM EBIT` on the same
   sheet reconciles to EDGAR exactly.* Low priority: the guard already disqualifies the band, so
   nothing downstream depends on CIQ answering. Worth sending because the same rent-adjustment
   substitution would silently distort ANY lease-heavy name.
17. **Truckload freeze-source re-run** — confirm the surgically-patched
   `frontend/themes/truckload-supply-purge.json` reproduces byte-identical from the freeze.
18. **Sweep-#2 fail-closed coverage holes (2)** — operator decision, report-only.
19. **Drafting-rubric v2 validation — DATED 2026-08-13** (pre-registered; do not run early).

**HOUSEKEEPING**
20. **UNIT-BOUNDARY AUDIT — priority raised; operator records this as the FIFTH instance.**
    Latest (2026-07-22, the SMPL bear-state pull): `_lease_inclusive_net_debt` returns **DOLLARS**
    while its sibling anchor fields are **$M**, and a consumer that read it as $M produced a TEV of
    $1.99 **trillion** for B&G Foods. Caught by face validity, not by a type — the return is
    `float` either way. Sweep every cross-module numeric boundary for an implicit unit and make it
    explicit (name, wrapper type, or a stated-unit return). **NOTE: no unit-boundary item existed
    in STATE before this entry** — the operator's "fifth instance" count is recorded as given and
    was not independently verified here; earlier instances are not enumerated in this file.
21. **Refresh cadence → docs/RUNBOOKS.md** (it is operating practice, not state).
22. **Full STATE split** — §5 build records → a fossils/decisions file; this block is the interim.

23. **REFERENCE-LABEL REGISTER + de-couple the median lookup (PAIRED — do not split).**
    `assumptions[].references[].label` renders to the reader but is not linted; 14 labels across
    the four records still carry house vocabulary (`own-history band low`, `committed anchor
    median`, EPAM's `DEAD REGIME`). Restating them is blocked on a real coupling: `uw-card.js:188`
    finds the median reference by `/median/i.test(p.label)` — a CLASSIFIER on display prose, which
    the parsers-consume-structured-values rule forbids. So: give references a structured `role`
    (`median` / `band_low` / `p75` / …), switch the lookup to it, THEN restate the labels with
    analyst ratification. Splitting them means either a broken card or a rule left violated.

24. **MIRROR-SYNC CI CHECK.** A generator run dirties BOTH its source and its `frontend/` mirror;
    an artifact pass that commits only the source leaves the deployed site reading stale data
    SILENTLY — nothing is red, the page is just wrong. Found 2026-07-21: `92feab0` committed
    `data/monitor/2026-07-20.json` without its mirror, so the live freshness panel was still
    missing EPAM (fixed in `a982900`). Ship a CI step that rebuilds and fails if `git status` is
    dirty — the artifact pass is complete when the tree is clean, not when the source commit lands.

25. **SINGLE-REGISTER POLICY — FORMALIZED 2026-07-22 (supersedes the two-field arrangement below).**
    **`verdict.rationale` is THE rationale.** Renderer, tear-sheet, card emitter and linter bind it
    alone; **`rationale_plain` is DEPRECATED** — schema keeps it nullable so historical JSON loads,
    and nothing reads it. *Why:* the two-field split did not hold in practice. The four restated
    records populated `rationale_plain` while the three R2 records written afterwards populated
    `rationale`, so "the reader-facing text" resolved to a DIFFERENT field per record and the
    linter's coverage moved with it. One field cannot drift from itself.
    - **SEALED POST-VERDICT, AMENDMENT-APPEND ONLY (`vinci/seal.py`, `scenarios/_seal.json`).** Once
      a verdict is recorded, its rationale may grow ONLY by an appended `[amended <date>: …]` tag.
      Rewording, truncating, prepending, appending untagged prose, or nulling all FAIL a repo test.
      *Why it matters:* if a rationale can be quietly re-worded, every past call reads as
      well-reasoned in hindsight and the forward spread proves nothing.
    - **The word cap binds the THESIS, not the audit trail** — `seal.base_text()` strips amendment
      tags before the count, or recording an amendment and passing the linter become mutually
      exclusive and the amendment loses. The register checks still scan the tags.
    - **RESIDUAL RISK, recorded not papered over:** the baseline lives in a committed manifest, so a
      deliberate regeneration of `scenarios/_seal.json` defeats the seal. It guards against silent
      drift and careless edits, NOT a determined rewrite. For names that opened a position the
      append-only ledger remains the untamperable copy; **a watch has no such backstop** (the
      2026-07-21 WERN loss is the precedent).
    - Migration 2026-07-22: IT/SMPL/WERN copied `rationale_plain` → `rationale` **verbatim**
      (byte-identical, verified); AORT/MVST/NCNO already canonical; EPAM stays null (pending). The
      `.uw-rationale-orig` expander and its CSS are removed.

26. **RATIONALE STYLE RULE (adopted 2026-07-21; binds FUTURE verdicts, never sealed ones).**
    `verdict.rationale` is plain thesis prose — the market-standard shape: thesis, the two or
    three numbers that carry it, the risk accepted. **Accession numbers, vendor names (CIQ /
    Polygon), verification arithmetic ("1,100 × 8% × 6.0x → $3.54 → 2.17:1"), and process
    narration ("re-verified at entry against the …-session close") live in `facts` /
    `source_refs` / the record's structured fields — never in the rationale text.** Trigger:
    SMPL's recorded rationale (audited 2026-07-21) violates all three — an accession
    mid-sentence, CIQ arithmetic inline, formula chains as prose. THE SEALED TEXT STANDS: the
    ledger copy is append-only forever, and the machine never rewrites analyst words — the
    scenario-record copy is the analyst's to re-word (meaning-preserving, by hand) if they
    choose. This rule makes the standard checkable at the NEXT verdict instead of re-discovered
    after it. (IT's rationale largely conforms and needs nothing.)

    **EXTENDED 2026-07-21 (restatement pass — all four records).** The rule now covers EVERY prose
    field in a scenario record, because a record is read by an outside buy-side analyst who has
    never seen this repo, and the registers differ by field:

    | field | register |
    |---|---|
    | `rationale_plain` | plain thesis, ≤~120 words: action + asymmetry → the variant view with its carrying numbers → the kill condition |
    | `reunderwrite_triggers` | measurable condition → threshold → action |
    | leg `reason` | investment-committee register — statistics cited BY NAME |
    | `assumptions[].method` | technical replication detail (a reader must be able to rebuild the number) |

    Binding on every field regardless of register: **accessions and vendor names live in the
    structured `references` / `source` fields only**, and **house-internal labels appear nowhere —
    state the claim, not the label** ("the sell-off has overshot fair value", never "overshoot";
    "the full-history screening median", never "the anchor"; "a regime no longer representative",
    never "DEAD REGIME"). Build/PR numbers are repo provenance and never appear in prose.

    **WHICH rationale the rule binds: the reader-facing one.** `rationale_plain` carries the
    restatement. Once a restatement exists the original is a historical artifact and is exempt from
    the linter; with no restatement, the original IS reader-facing and is bound. Anything else would
    mean no restated record could ever read clean, and a linter that cries wolf gets switched off.

    **AMENDED 2026-07-21 (same day): the scenario-record originals were DROPPED.** The record now
    carries the plain restatement only; `verdict.rationale` is null on all four. §7 always made the
    record copy the analyst's to change — this is that call, exercised. Where the sealed copy lives
    now:
    * **IT / SMPL** — losslessly, in the append-only ledger: `payload.thesis` was verified
      BYTE-IDENTICAL to the dropped text before removal. This is the ledger doing its job.
    * **WERN** — nowhere. A WATCH opens no position, so it has no ledger row, and its record was the
      only committed copy. Dropped as a **conscious, recorded loss** (analyst decision): the two
      statistics the prose carried — EV/EBIT 16.1x at base, ~3.7% normalized FCF yield — survive
      structurally in the card's cross-check rows, so only the wording is gone.
    * **EPAM** — never had one (verdict pending).
    The render still supports original + restatement together (pinned on synthetic fixtures) — the
    path is live for any FUTURE record that keeps both. **Standing consequence:** a verdict that
    opens no position has no append-only backstop, so dropping its original is irreversible. Check
    for a ledger row BEFORE dropping — the check is one line and the loss is permanent.

    **Draft status is STRUCTURED, never prose.** `ratified_by`/`ratified` already carry it, so the
    "DRAFT — ratify at review" marker is gone from method text; the card badges "draft — unratified"
    from the structured field. A prose duplicate of structured state is exactly what this rule
    removes.

    Machine check shipped: `vinci/prose_lint.py` — **flag-only, never rewrites** (a linter that
    edited analyst prose would violate the very line this rule protects), wired at `write_record` as
    a non-blocking warning plus a repo check pinning all four records clean. Boundary: scenario
    records are the EXTERNAL register; **the dossier layer stays internal** until a name graduates
    (543 flags there are out of scope by definition, not a backlog).

    **KNOWN GAP — `references[].label` is NOT scanned (found in review of PR #172).** "Zero flags"
    means the four scanned surfaces (rationale, triggers, leg reasons, methods), NOT the whole
    reader-facing record. Reference labels DO render to the reader (`uw-card.js` reference table)
    and **14 of them still carry house vocabulary** — including EPAM's `DEAD REGIME`, the exact
    token this pass set out to remove. Not fixed in-pass for two reasons, both real: the labels are
    analyst-facing prose that needs ratification like the other restatements, and `uw-card.js:188`
    CLASSIFIES on label text (`/median/i.test(p.label)`) to find the median reference — so
    restating a label can silently break the card. That classifier is itself a standing violation
    of the parsers-consume-structured-values rule. Queued as item 20.

27. **RENDER-COMPLETENESS CHECK (from #185's dropped survival `detail`).** The survival panel
    silently dropped its `detail` list — the runway arithmetic and the going-concern sentence were
    IN the record and absent from the card. This is the second instance of the same shape (#179's
    `undefined` reference table was the first), so the pin belongs at the class level, not the
    instance: a check that every populated field of a committed record reaches the rendered surface
    (or is DELIBERATELY tiered per the three-tier design rule), rather than one more per-field
    assertion added after each miss. Both instances were invisible to a preview that checked only
    the visible tier — so the check must run against the FORCE-OPEN print state too.

28. **TESTING NOTE — `model_copy` DOES NOT RE-RUN PYDANTIC VALIDATORS.** Found 2026-07-22 building
    the EV/Revenue axes pin: a test helper that built its record with `rec.model_copy(update=...)`
    sailed past the record-level guards it existed to exercise, and the test passed for the wrong
    reason. Any test asserting a `@model_validator` REFUSES something must construct through
    `ScenarioRecord(...)` or `model_validate(...)`. Worth a sweep of existing `model_copy` uses in
    tests — this one was caught because the assertion was a `pytest.raises` that did not raise; a
    helper used for a POSITIVE assertion would have failed silently and still be green.

29. **NCI TERM FOR THE R2 ENGINE — GATES ANY COMBINED-ENTITY UNDERWRITE (FUBO is the live case).**
    `terminal_value` bridges `EV_T − net_debt_T → equity_T ÷ shares_T` with no non-controlling
    interest term, so it implicitly hands 100% of a consolidated enterprise to the parent's
    shareholders. That is wrong for any Up-C or partly-owned structure, and it is wrong by a factor
    (FUBO: 30% NCI plus a Class A/Class B share basis, ≈5× combined — item 4). Needs: an NCI
    deduction on the bridge, a ratified ECONOMIC-share convention, and a guard that REFUSES to
    compute when a record's share count is an EPS denominator rather than the economic count. Until
    this exists, no name with a material NCI can be underwritten on R2 — and the engine should say
    so rather than quietly produce a number.

30. **IR-DOCUMENT INGESTION TIER** — company documents that are NOT SEC filings (earnings
    supplements, IR decks) need first-class provenance: URL + retrieval date + sha256. IT's
    covenant ratio and FY26 guidance exist ONLY there, with no accession to cite.
31. **PERIMETER WATCHER reading FOOTNOTES AND RELEASES, not 8-K only** — Gartner's Digital Markets
    sale completed with **no Form 8-K at all**; it surfaced in a 10-K subsequent-events note.
32. **ENTITY-STRUCTURE GATE BEFORE ANY PER-SHARE MATH** — check for NCI / multi-class / Up-C before
    dividing anything by a share count (the FUBO lesson; pairs with item 26).
33. **FORM-4 TRANSACTION-CODE CLASSIFIER** — the insider leaf read twelve director compensation
    grants (codes A/J, $0 paid) as an open-market purchase off the grant reference price.
34. **STALENESS BANNERS ON MARKET-SENSITIVE DISPLAY FIELDS** — IT's committed market cap is
    as-of 2026-06-25 and 12.3% light; it renders as "$8.7B" with no staleness mark. Stamp until it
    lands.
35. **COMPANY-METRIC PRIMACY SWEEP** — where a metric is computable from filings, the filings
    number is primary and the vendor number becomes a guarded cross-check (trigger: the $193.8M
    free-cash-flow gap, item 34).
36. **INTERIM-FCF SENSITIVITY OPTION IN THE R2 ENGINE, printed per record.** Falsifier already
    observed: crediting NCNO's four guided years moves the optimistic case to roughly the market
    price, so a verdict note claiming "even the optimistic case sits below the price" holds only
    before interim cash. The engine should print the sensitivity rather than leave it to prose.
37. **CIQ ESCALATION #2 — the levered-free-cash-flow gap (DRAFTED).** Vendor 'Levered Free Cash
    Flow' reads **1,064.2** for LTM to Mar-31-2026 against the company's own **1,258.0** on the
    same period and nominally the same construction. **Debt service does not explain it**: interest
    paid is $99.5M and long-term-debt repayments are $0.0M, so ~$194M is unaccounted for. Same
    shape as the VITL defect (a row populated against a denominator its label does not describe) —
    **suspect until diagnosed, not concluded.** Dossier leaf now carries the filings figure with
    the vendor reading recorded as a caveat.
38. **DATED + SHA-STAMPED VENDOR-EXPORT SNAPSHOTS, surfaced per record** — so a record states which
    export vintage it was built from.
39. **DOSSIER GOVERNANCE BLOCK (proxy-sourced)** — board, auditor, compensation, related-party.
40. **ANALOGUE SECTIONS — rebuild or remove** under the external review pack format.
41. **MVST NET-DEBT LEASE DECOMPOSITION UNKNOWN** — its bridge is a CIQ vendor figure on a
    "classified total debt less total cash" basis with no lease split, and the basis string does
    not even claim lease-inclusivity. Any lease-basis question is uncomputable for this name.
42. **WERN HAS NO DOSSIER** — `data/dossiers/` covers 11 names, not WERN; its band provenance lives
    only in the scenario record's `assumptions`.
