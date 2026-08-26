---
id:
status: recorded
date: 2026-08-26
prs: [506]
supersedes:
superseded-by:
date-source: MIGRATION DATE — this record was cut out of STATE.md on 2026-08-26; the work it describes is earlier and is dated in the body. The filename prefix is therefore the migration date, not the event date.
migrated-from: STATE.md §2 Built and verified
---

# **Read-only ops dashboard** (`frontend/`, static; `frontend/build.py` snapshot mirror) — a

*The one-line summary stays in STATE.md §2; this is the detail that stood beneath it,
verbatim.*

  - **Frontend eager-load / memory fix (2026-06-24):** the OVERVIEW landing page was fetching +
    parsing the full ~440 KB `ranked_queue.jsonl` just to show two counts, and `manifest`/`ledger` were
    each fetched TWICE (the caches stored the resolved VALUE, so concurrent `Promise.all` callers
    raced). Fixed: `build.py` emits the queue counts into `manifest.json` (the ~200-byte index) → the
    overview reads them there and **no longer loads the queue** (it loads lazily only on the Ranker);
    the snapshot loaders now memoize the in-flight PROMISE (`_once`) so concurrent callers share one
    fetch. *Verified via fresh-module import (the live tab's ES-module cache is stale, like the
    screenshot tooling this session): `getUniverseHealth().queue = {total 317, demoted 47}` from the
    manifest, 0 ranked_queue fetches, and 2 concurrent manifest/ledger calls → 1 fetch each; landing-
    page data ~447 KB → ~4 KB, overview heap roughly halves. NO leak existed — heap was 2–4 MB, stable
    across 24 navigations; the Ranker's 318-row table is the heaviest DOM, and OS-process memory is the
    per-tab renderer baseline, not this app.* All 5 dossiers were re-assembled so each carries
    peer_comps (now rendered as TABLES, NM preserved); BRBR's 'premium brand' drew 0 peer-comp
    guardrail false-fires (the narrowed _REL_VAL_CUE held live).
  - **Authed Cloudflare deploy — ✅ LIVE + AUTHED at `mosaic-theory.pages.dev` (Basic Auth, 2026-06-26).**
    The §4 CONDITIONAL authed Pages deploy is DONE and serving the licensed-adjacent dossiers/graph only
    behind auth. In-repo pieces: **`wrangler.toml`** (declares
    `pages_build_output_dir=frontend` + enables Pages Functions); **`functions/_middleware.js`** — a
    **FAIL-CLOSED HTTP Basic Auth gate** that requires a credential matching the Pages env vars
    `BASIC_AUTH_USER`/`BASIC_AUTH_PASS` (constant-time compared) on **every** request incl.
    `/dossiers/*`, returns **401** otherwise, and **denies everything when the env vars are unset**; and
    **`docs/DEPLOY.md`** — the operator runbook. **PIVOT (why Basic Auth, not Cloudflare Access):** the
    Access-JWT design was built + tested first, but standing up Cloudflare Zero Trust/Access requires
    account activation **and a payment method the operator declined**, so the gate was rewritten to Basic
    Auth — no Zero Trust, no card, Pages Functions only. *Verified WITHOUT Cloudflare: `python
    frontend/build.py` runs clean; `node --check` clean; a **13-case Basic-Auth allow/deny harness on the
    real middleware** — correct user/pass (incl. a colon-bearing password + lowercase scheme) → serves;
    missing/wrong-user/wrong-pass/empty/Bearer/malformed-base64/no-colon/UNCONFIGURED-env/partial-env →
    all 401; the 401 carries `WWW-Authenticate: Basic`. The harness caught a REAL bug — an em-dash in the
    `WWW-Authenticate` realm is an invalid HTTP header byte (Latin-1 only); fixed to ASCII (would have
    500'd on Cloudflare).* **BLOCKER B — ✅ VERIFIED PASS 2026-06-26:** the operator committed
    `data/graph_coverage.json` to `main` (with a `!data/graph_coverage.json` `.gitignore` exception); it
    is **CIQ-free** — 339 edges of EDGAR-10-K relationship data (customer/supplier/manufacturer/
    distributor/vendor) + verbatim 10-K `evidence`; the only financial words (`revenue/margin/multiple`)
    occur **solely inside that public 10-K prose (37×, 0 in structured fields)**; aggregates are pure
    graph counts. **BLOCKER A — ✅ PASSED:** an unauthenticated request returns `401` (the gate's Basic
    challenge), a correct credential returns `200` (verified by `curl -u`); the licensed `/dossiers/*`
    path is covered uniformly. **Gate merged to `main` via PR #25** (the production branch — without
    which the deploy serves unauthed; the *first* connect FAILED BLOCKER A for exactly this reason, the
    gate having been on a feature branch — **LESSON pinned in DEPLOY.md: the gate MUST be on the
    production branch**). **Two operator gotchas hit + resolved:** (1) `wrangler.toml`'s presence puts the
    Pages project into "env vars managed via wrangler.toml" mode → plaintext vars must live in the file,
    but **Secrets can still be set in the dashboard** (the supported path — never commit creds to
    `wrangler.toml`); (2) the first credentials didn't take because the dashboard Secrets weren't actually
    saved/bound — re-adding both as **dashboard Secrets** + redeploy bound them. **FOLLOW-UP (hygiene, not
    a blocker):** the live password was a weak test value (`nostra`) — replace with a strong secret +
    redeploy. The deploy auto-redeploys on push to `main`; `build.py` re-mirrors snapshots + the slimmed
    graph each time.
  - **Dossier → PDF export (2026-06-30):** a **Download PDF** button on each per-ticker dossier header
    triggers the browser's NATIVE print-to-PDF (`window.print()`) — **no library; the frontend stays
    dependency-free** (no external CDN script pulled into the authed app, no rasterised output). A
    `@media print` stylesheet turns the on-screen app into a clean report: strips the sidebar /
    breadcrumb / the button itself, expands `.main` to full width, forces `print-color-adjust: exact`
    so the flag / synthesis-fence / pill colours (which carry meaning) survive into the PDF, and
    `break-inside: avoid` keeps facts / flags / filings / points from splitting across pages. A
    module-level `beforeprint`/`afterprint` pair names the saved file (`<TICKER> · dossier · Nostra
    Vinci`) then restores `document.title`, so a native Cmd+P gets the same filename — not just the
    button. **Read-only / assemble-not-conclude preserved:** it prints what is already shown, renders no
    new judgment, touches no decision path, and carries the "no verdict" framing into the export.
    *Verified on a REAL served dossier (VRRM, full `build.py` mirror on `:8765`): the button renders
    top-right of the header (desktop inline via `flex: 1 1 360px`; wraps below on a narrow viewport),
    click → `window.print()` fired once, beforeprint set the title to "VRRM · dossier · Nostra Vinci" +
    afterprint restored it; flipping the `@media print` rule live confirmed sidebar/breadcrumb/button →
    `display:none`, `.main` max-width:none + padding:0, `.fact`/`.flag` break-inside:avoid, body white,
    and the print-layout screenshot is a clean full-width report; 0 console errors.*
    **Header de-duplication (same pass):** the dossier DETAIL page rendered TWO stacked header blocks —
    the shared `frame()`'s generic "Dossier" h1 + its `does`/persistent "assembled facts · no verdict"
    subtitles, then `renderDossier()`'s own ticker header repeating the same framing. `frame()` gained a
    `bare` option; the detail render path passes `bare:true` so only the ticker header shows (the
    breadcrumb already names the section, and the ticker subtitle carries the no-verdict framing). The
    **dossier INDEX** keeps the full generic header (its only orientation). *Verified by loading the
    fresh modules into detached containers: DETAIL → 1 header block, generic subtitles absent, ticker
    header + Download-PDF button present; INDEX → generic header + subtitles kept, cards render.* Touches
    `frontend/views/dossier.js` + `frontend/assets/styles.css` + `frontend/app.js`.
    **Follow-ups (2026-06-30):** (1) the breadcrumb section label ("Dossier") is now a LINK to its index
    (`#/dossier`) on a detail page — `frame()` links the middle crumb when `crumbExtra` is present and
    keeps it plain text (current page) on the index; (2) the PDF left/right inset moved off `@page`
    margins (which the print dialog's "Margins: None" overrides) into `.main` padding (`0 6mm`) so the
    report never touches the page edge, `@page` keeping top/bottom only and surviving every dialog margin
    setting per page. *Verified live: detail breadcrumb "Dossier" → `#/dossier` link, index breadcrumb
    "Dossier" plain text; flipping `@media print` on → `.main` L/R padding 22.68px (= 6mm), max-width
    none, breadcrumb display:none.*
    **Print-density pass (2026-06-30) — a deep dossier exported to ~10 A4 pages, too long to review.**
    Right-sized to ~6 pages with NO content dropped or summarised: a print-only `.main { zoom: 0.85 }`
    scales the whole report (print is high-DPI, so type stays crisp); the on-screen reading spacing is
    tightened for paper (`.fact` / `.card` / `.flag` / `.point` / `.filing` / table-cell padding +
    section margins); and table-bearing fact rows go FULL-WIDTH via `.fact:has(table.data){display:block}`
    (label above the table) so the peer-roster "Business" column stops wrapping into 5-6 short lines. The
    zoom + padding density stay inside `@media print` (screen reading view unchanged). *Verified on the
    real FUBO dossier (the 10-page case): measured print-layout height 11,194px → 6,963px ≈ 10 → ~6.2
    pages (≈38% fewer, ~6-7 with Default dialog margins); the peer-roster table renders full-width with
    1-2-line descriptions; a clean reload confirms screen unaffected by the print-only rules (sidebar
    visible, `.main` zoom 1, `.fact` padding 9px). Diagnosis first ruled out mid-document blank space
    (pages were 100% full; only the last overflowed) and over-long tables — the slack was screen-comfort
    spacing + genuinely substantial content.*
    **Full-width tables generalised to the screen too (2026-06-30, by request):** the
    `.fact:has(table.data){display:block}` rule was moved OUT of `@media print` into the general dossier
    CSS, so the 5 table-bearing facts (peer roster, trading multiples, fundamental deltas, margin-trend +
    multi-year-trajectory series, graph cohort) render label-above-full-width **on screen and in the PDF
    alike** — the squeeze hit on-screen too (worse on narrow viewports). Scalar facts keep the 210px
    label-left grid. *Verified live (desktop, zoom 1): all 5 table-facts compute `display:block` with the
    peer table at the full 906px content width; scalar facts stay `display:grid`; screenshot shows the
    peer/margin/trajectory tables full-width with single-line descriptions.*
  - **Dossier valuation re-centered on the cross-section (MERGED as #48, 2026-07-01).** Acting
    on an equity-analyst review, validated from first principles: the Valuation block LED with an
    own-history multiple percentile that is ~0th for nearly every finalist (the screen selects
    drawdowns), so it barely discriminated, while the cross-sectional read (the fund's edge) was
    siloed in Peer comps. Fix (`vinci/dossier/{schemas,ciq_sheets,mechanical,render}.py`): (1) new
    `cross_sectional_valuation` — name EV/EBITDA & P/E vs the peer MEDIAN with the discount, NUMBERS
    ONLY (the repetitive "earned-vs-residual?" framing tail was dropped pre-merge as boilerplate that
    duplicated Peer comps) — now LEADS the Valuation section; (2) `range_position` carries the trailing
    low–median–high RANGE + a sample-size CONFIDENCE label and SUPPRESSES the "near-floor" verdict
    below ~2y of closes (`_MIN_CONFIDENT_CLOSES=8`, mirroring the P/E percentile's ~2y bar); (3) the
    two bare "Nth %ile" render lines dropped (folded into the contextualized own-history line).
    Display-only — no gate/ranker/scoring/ledger touched; assemble-not-conclude intact. *Verified:
    ruff + mypy --strict (67) + pytest 246 incl. 3 new tests (thin→LOW-CONFIDENCE, rich→band+range,
    cross-sectional discount). Cloud-validated on all 10 committed dossiers (derived data, no raw
    CIQ): the confidence gate fires ONLY on MVST (4 closes), band trusted on the 19–20-close names;
    the cross-sectional discount spans −83% (VITL) to +165% (MVST) — MVST reads own-history
    "near-floor" yet +165% RICH vs peers, the context the old lead masked. The FINAL rendered
    re-assembly on the real CIQ workbooks is the operator's step (CIQ absent in-cloud).* Live
    re-assembly (MVST/IT/AORT/VITL) confirmed the render; PR 3 (flag audience-split + body concision)
    follows.
  - **Comps subject mis-identification + stale-Close — valuation data-integrity (PR open — not
    merged, 2026-07-01; folds in the retired #49 conflict-flag scope).** PR #49 had flagged the two
    CIQ EV/EBITDA figures (Financials→Multiples TEV/LTM vs Comparable-Analysis Trading-Multiples) as
    a "basis conflict" (MVST 10.0x vs 38.4x). **Validating #49 against the operator's raw CIQ
    workbooks (in-session only, never committed) FALSIFIED that premise** and uncovered two real data
    bugs the "conflict" was a symptom of:
    - **Bug A — comps subject mis-identified.** `_comps_layout` picked the SUBJECT by a positional
      "first company row after a gap" heuristic. A no-ticker peer (Proterra/Boston-Power for MVST)
      breaks the contiguous block, so MVST resolved to **Samsung SDI** (a peer, 38.4x, $24.8B cap)
      instead of **Microvast** (11.1x, $423M) — and dropped Microvast from its own dossier while
      dropping Samsung SDI from the peer roster. The 38.4x "conflict" was this mis-read, not a basis
      difference. **Fix:** `_comps_layout(rows, ticker)` now matches the subject by the bundle
      ticker in the col-0 `(EXCH:SYMBOL)` paren (fallback: last company row before Summary Stats),
      threaded through `peer_comps` / `_comps_multiples` / `_comps_deltas` /
      `cross_sectional_valuation` / `comps_ev_ebitda`. After the fix MVST comps EV/EBITDA = 11.1x ≈
      Financials 11.3x → the "conflict" is GONE (was a parse artifact); Samsung SDI is restored as a
      peer.
    - **Bug B — stale Financials Close.** For a recently-crashed name the Financials→Multiples "latest
      Close" is a clean prior quarter-end that predates the drawdown: VRRM reads 8.5x "near-floor"
      as-of **2026-03-31** (83d before the 2026-06-22 reference) vs a current comps 4.7x — and that
      stale Close also drives the PR#48 own-history range/percentile. **Fix:** `range_position` now
      renders the Close's as-of DATE; `ev_ebitda_asof` exposes it; the reworked
      `mechanical._ev_ebitda_integrity_flag(bundle, reference_date)` fires a **stale-price caveat**
      (names the date, the day-gap, and prefers the current comps figure) when the Close trails the
      reference by > `_STALE_CLOSE_DAYS` (45), and otherwise a plain "cross-sheet gap — verify"
      caveat (the inaccurate "different EBITDA/EV bases" wording is retired). Display-only; the caveat
      POSES, never concludes. *Verified: ruff + mypy --strict (67) + pytest 251 incl. 5 tests
      (subject-by-ticker picks the real name not the positional mis-pick + fallback; `ev_ebitda_asof`;
      range_position renders as-of date; integrity flag → stale-price vs cross-sheet-gap vs quiet).
      Re-ran the real MVST/VRRM/IT CIQ workbooks end-to-end: MVST cross-sectional now Microvast 11.1x
      (was Samsung SDI 38.4x), no integrity flag; VRRM fires the stale-price caveat (8.5x@2026-03-31,
      83d, prefer comps 4.7x); IT quiet (7.5x = 7.5x, fresh 2026-06-24 Close) — every case ties to the
      name's real market cap.* PR #49 is superseded/folded here (its `comps_ev_ebitda` value-exposure
      is kept and reused).
    - **Refinement (operator-validated, 2026-07-01):** the stale-price caveat now fires only on
      MATERIAL staleness — `material_stale = stale and not (comps_present and not disagree)`. When a
      present current comps figure AGREES with the stale Financials multiple the staleness is
      immaterial (price didn't move) and the inline as-of date already discloses it, so the bottom
      caveat is SUPPRESSED as noise (MVST: stale 10.0x vs comps 11.1x); it still fires when comps
      DISAGREES (VRRM) or is ABSENT (can't cross-check). Operator re-assembly of MVST/VRRM/IT on #51
      confirmed Fix A (MVST → Microvast 11.1x, was Samsung SDI 38.4x; synthesis now fed the right
      name's multiples) + Fix B; pytest 251 green (integrity test extended: stale+agree→suppressed,
      stale+comps-absent→soft-fire). **#51 MERGED (squash `8f7b670`); operator committed the 3
      dossier artifacts into it.**
  - **Dossier flags split by audience + body-tail concision (PR open — not merged, 2026-07-01).**
    Acting on analyst claim-2 ("flags are mostly jargon"): the human-review block mixed machine-QA
    guardrails (validator-speak — `UNCITED`/`UNTRACEABLE`/`TWIN`/`DIRECTIONAL`/…) with real decision
    caveats. New `vinci/dossier/flags.py` classifies each emitted flag at the SCHEMA boundary
    (`partition` → caveats + qa_flags; `revoice` strips the ALL-CAPS token + humanises the field
    name, keeping the explanation) — **the guardrail-emission logic in `synthesis._validate` is
    untouched, so no guardrail and none of its ~18 tests can regress.** `Dossier.flags` → `caveats`
    (human PDF/web, re-voiced, incl. the visible `pull CIQ …` incomplete-input notes) + `qa_flags`
    (dev/JSON only, FULLY hidden from the human view). DIRECTIONAL + VERIFICATION-CLAIM → qa
    (machine-overstep self-checks); default for an unrecognised flag = caveat (fail toward
    transparency). Wired through `schemas`/`assemble`/`render`/`cli` + `frontend/views/dossier.js`
    (renders `d.caveats`, `d.flags` fallback for un-re-assembled JSONs). Plus a body-tail concision
    pass — 4 assumed tails trimmed (comps "LTM+NTM forward", surprise "fiscal-year…99.1 guide",
    survival "no runway constraint" / "runway=cash÷burn"), the ~9 load-bearing misread-guards KEPT
    (NM-as-real-state, margin-%-vs-absolute-EBITDA, justified-vs-residual, opacity-as-signal, …).
    Display-only; assemble-not-conclude intact. *Verified: ruff + mypy --strict (68) + pytest 254
    incl. 3 new flag tests (partition routes QA out; re-voice strips the token keeps the
    explanation; render shows caveats, hides QA). Cloud-validated on all 10 committed dossiers
    (their raw flag strings partition correctly — MVST 1 caveat / 4 qa, VRRM 2/1, BRBR 2/2 with
    DIRECTIONAL+VERIFICATION-CLAIM hidden; ~15 of ~34 flags routed to dev). Operator re-assembly is
    the final rendered gate; committed `data/dossiers/*` + `frontend/dossiers/*` refresh then.*
  - **Post-merge audit of the analyst series (#47/#48/#51/#53) — 4-agent finder + fixes (2026-07-01).**
    #51 (comps subject-by-ticker) verified CLEAN and robust: the `IT`/Gartner 2-letter substring
    worst-case resolves both directions (`==` on the parsed `EXCH:SYMBOL`), every peer value matches
    the committed dossiers across all 9 real workbooks, stale-Close dates no off-by-one. Actionable
    findings fixed: (1, HIGH/fail-loud) `UNTRACEABLE` — a figure mis-cited to STRUCTURED data that
    lacks it — had been swept into the hidden `qa_flags` by #53 and, keeping `cited=True`, rendered as
    a normally-cited claim with NO human-visible warning; reclassified to a visible, re-voiced CAVEAT
    (its source_ref LOOKS legit, so the human can't catch it from the citation). `TRANSCRIPT-FIGURE`
    stays hidden (operator call — its `CIQ transcript` source_ref is honest, matching the earlier
    "redundant noise" read). (2, HIGH) #48's `cross_sectional` (the edge, the md Valuation lead) was
    never rendered in the web UI or the #47 PDF — `frontend/views/dossier.js valuation()` now mirrors
    the md (leads with it, drops the folded own-history percentile rows, fixes the stale subtitle).
    (3, HIGH) `net_debt_to_ocf` (sourced in all 10) was never rendered either (pre-existing) — row
    added in `quality()`. (5, MED) `caveats`/`qa_flags` now default `[]` so JSON predating the split
    round-trips; `cross_sectional` stays REQUIRED (fail-loud on a missing analytical value). *Verified:
    frontend by a real headless-Chrome MVST render (cross_sectional value + Net-debt/OCF now show;
    stale subtitle + percentile rows gone); the flag reclassify by unit test + a no-UNTRACEABLE-leaks-
    to-qa invariant across all 10; ruff + mypy --strict (68) + pytest green; dossier.js node --check
    clean. On a branch → PR (the series is already on main).*
  - **PR A — Catalyst path: the five previously-unparsed CIQ Estimates sheets, horizon-matched
    (2026-07-02).** The Estimates workbook was already pulled but only Consensus / Revisions-FY /
    Surprise were consumed; the **Trends / Guidance / Multiples / Recent-Changes / (deeper) Consensus**
    sheets carried the Edge-2 revision-breadth evidence UNPARSED — MVST rendered "0↑/0↓" while its FY26
    EBITDA consensus was cut **146.5 → 62.1** over six months. New mechanical block `catalyst_path`
    (schema `CatalystPath` + `RevisionEvent`, **optional-with-default** so a pre-PR `dossier.json`
    round-trips — the flags-PR precedent), assembled by seven extractors in `ciq_sheets.py` (as-of /
    horizon-read / acceleration-read / cross-name-anchor / guidance-bridge / revision-events /
    consensus-stats), wired in `mechanical._catalyst_path` + a **shared-45d** staleness caveat (reuses
    `_STALE_CLOSE_DAYS`), declared in `CIQ_MODULES` (the AST coverage guard forced it), and rendered IN
    PLACE of the thin "Consensus context" slot (legacy facts relocated under it; transcript pointer
    stays last) in BOTH `render.py` and `frontend/views/dossier.js` (event log capped at 10 + "+N more
    in JSON"). **Assemble-not-conclude held:** no field carries an upside / fair-value / direction (the
    no-conclusion schema-walk was extended to `catalyst_path` + `RevisionEvent`); CIQ's
    conclusion-shaped "Potential Upside/Downside" is deliberately NOT read; the guidance track-record is
    a mechanical beat-count over **resolved-only** periods (both guidance AND actual present). *Verified
    on the REAL MVST Estimates export (legacy BIFF `.xls`, git-ignored, never committed): the FY26
    EBITDA path renders `146.5 (6m) → 62.1 (now)` with 2m/3m labelled n/a and NO fabricated points; the
    FQ 2-month-window downward revisions the FY-only line hid; the guidance bridge with the 2026-03-16
    date decoded; the multiples ladder NTM P/E 14.33 / FY26 32.25 / FY27 8.6; the dated H.C. Wainwright
    EBITDA cut in the event log; as-of 2026-05-15 on the header, staleness silent at the current gap and
    firing on a stale reference. The source-aware figure-tracer covers the new STRUCTURED refs (numbers
    join the universe → citations trace; refs never match the transcript soft-note → a mis-cite still
    hard-flags UNTRACEABLE). Frontend confirmed by a real preview render (section in place, legacy facts
    under it, event log "+37 more", no console errors). ruff + mypy --strict (68) + `pytest -m "not
    network"` green; 16 new synthetic-fixture tests. On a branch → PR; the agent never merges.*
    - **Contract deviation REPORTED (not improvised):** sub-block (f)'s rating-distribution rows are
      **not in `Consensus`** as the spec assumed — in the real export they live in `Trends`
      ("Non-Periodic Trends": Buy/Outperform/Hold/…). Read from their ACTUAL location by label (a
      declared `Trends` read), never positionally guessed; the target-price stats + NTM level block ARE
      in `Consensus` as specified. The operator re-assembles + commits the refreshed dossiers (per the
      #51 precedent); the assembled artifacts are NOT committed in this PR.
  - **PR A.1 — catalyst-path integrity + readability fixes (2026-07-02).** Six fixes on the #55
    catalyst path; scoped to `ciq_sheets`/`mechanical`/`render`/`flags`/`synthesis` + `dossier.js` +
    tests (no new sheets, no schema change, no reorder beyond deleting the legacy block).
    - **BUG 1 (#51-class as-of, load-bearing) → ROOT CAUSE:** `estimates_as_of` returned the max
      Recent-Changes EVENT date (MVST 2026-05-15) presented as an authoritative as-of — but the CIQ
      Estimates export carries NO as-of stamp (verified: the sibling Comparable-Analysis book stamps
      `As-Of Date: 2026-06-24` on every sheet; Estimates has none), and Trends '1 month ago' already
      reflects the 05-15 cut, so the true export is ≥ mid-June. The 05-15 as-of was a **false floor
      read as a point** — the same class as #51's stale-Close (a dated column mistaken for "current").
      **Fix:** prefer an explicit `As-Of Date:` header (scanned by label; implemented + tested for
      generality); absent one, render a FLOOR — a `≥`-prefixed value + "export date unverified" note —
      NEVER a plain as-of. Staleness keys off a header date (hard 45d gate) but emits a soft
      "as-of UNVERIFIABLE" caveat on a floor (no false pass); lookback labels stay export-relative
      ('latest', not 'now'). *Regression-pinned: header-wins-over-event; floor '≥'+note; soft-vs-hard
      staleness at the boundary.*
    - **REFINED (PR #79, 2026-07-06) — a recent floor PROVES freshness; the "any floor → UNVERIFIABLE"
      rule was over-conservative.** The floor `≥F` is a lower bound on the true export date E (E ≥ F),
      hence an UPPER bound on staleness (R − E ≤ R − F). When R − F ≤ 45d even the worst case is within
      tolerance → the data is provably fresh → the caveat is SUPPRESSED (the `≥F · export date
      unverified` suffix on each read still flags the un-stamped vintage — no info lost); it fires only
      when R − F > 45d, now stating the worst-case bound. A floor at/after the reference (export
      post-dates the screen) is fresher still. This **REVERSED a deliberately-pinned test** (a 5d floor
      no longer fires) — the test was updated + expanded (MVST/VRRM-real, F≥R edge, >45d bound). Also
      DROPPED the caveat's "corroborate against a dated sibling CIQ export" advice: file mtimes show the
      sibling comps export can be days newer than the estimates (MVST/VRRM estimates 06-19 vs comps
      06-24), so it is not a reliable corroborator → replaced with the AS_OF sidecar. *Adversarially
      verified (3 reviewers: the bound arithmetic is sound; the design reversal is the human call).
      Verified on the real MVST/VRRM/EPAM/AORT exports (ref 2026-06-22): all four now SILENT (worst-case
      38 / 13 / 4 / −1 d ≤ 45); a synthetic 113d floor still fires with the "113d" bound. ruff + mypy
      --strict (87) + pytest 464 green. Incident→invariant: the expanded floor-bound test
      `test_catalyst_stale_flag_header_hard_gate_floor_bound_caveat`.*
    - **BUG 2 (sign-blind reads):** (a) a negative/zero-crossing consensus path rendered a bare signed
      % — misreading a shrinking interest expense (−13.7→−4.9) as a "−64% decline"; now direction
      words ("improving (magnitude toward zero)"). (b) the guidance track-record used "≥ floor" for
      ALL metrics; a cost-like (negative) guide (capex) now reads "≤ ceiling". (c) the track-record now
      surfaces the MOST-RECENT resolved MET/MISSED (MVST Revenue FY2025 MISSED, previously buried in an
      N/M count). *Regression-pinned incl. a sign-crossing series + the cost-semantic + recency.*
    - **BUG 3 (guide staleness):** the latest guide now flags "(stale guide — DATE)" when older than
      the shared 45d window vs the reference (MVST capex FY2023 guide surfaces it). *Pinned.*
    - **READABILITY 4 (table renders + curation; JSON stays complete):** frontend now TABLE-renders
      horizon (metric×FQ, zero-breadth rows collapsed), acceleration (metric×lookback + net, GAAP
      adjacent to Normalized), and the multiples ladder (NTM+FY26–28, later years noted); revision
      events GROUP by (date, broker) — MVST's ~18 same-day H.C. Wainwright rows collapse to one entry
      (top line items by |Δ|), groups cap 3. Markdown applies the same collapse/trim/group curation.
      *Pinned via render-layer unit tests (`_horizon_lines`/`_ladder_lines`/`_grouped_events_lines`).*
    - **READABILITY 5:** the "Consensus context (legacy light facts)" section is DELETED (eps/revenue/
      revision-history duplicated the catalyst reads); the one non-duplicate — Surprise history — is
      folded into the catalyst path. A pre-catalyst_path `dossier.json` still renders the legacy
      fallback (regression-pinned).
    - **GUARDRAIL 6:** the DIRECTIONAL rating-context exemption (`synthesis._RATING_CTX` — the
      exemption's real home, a surgical one-arm addition) now also exempts the `consensus_stats`
      rating-count phrasing ("Ratings: Buy N"); a real "BUY, undervalued" conclusion still flags.
    *Verified on the REAL MVST export (git-ignored): the floor as-of line + soft caveat; interest
    expense reads "improving"; capex cost-semantics + stale-guide; horizon zero-rows collapsed; the
    single 2026-05-15 H.C. Wainwright group; ladder trimmed; frontend tables via a real preview render,
    no console errors. ruff + mypy --strict (68) + `pytest -m "not network"` green. On a branch → PR;
    agent never merges. Artifacts re-assembled + committed by the operator post-merge (#51 precedent).*
  - **PR B — comps-workbook upgrades (2026-07-02).** Consume four comps sheets the parser previously
    read only partially — Financial Data, Operating Statistics, Credit Health Panel, Implied Valuation
    (all validated against the real MVST export; row/column LABELS matched the contract, no deviation).
    Scoped to `ciq_sheets`/`mechanical`/`render`/`schemas`/`flags` + `dossier.js` + tests; all comps
    row-lookups key BY TICKER (the #51 discipline — the sheets differ in row order).
    - **B1 per-peer grid** (`peer_grid`, `PeerRow`): one row per peer + the subject (visually distinct)
      + a peers-only median footer — cap · EBITDA margin · rev/EBITDA growth · Debt/EBITDA · net debt,
      sorted by cap; joins Financial Data ⨝ Operating Statistics by ticker; NM preserved. The
      median-only `fundamental_deltas` line collapses into the footer (the field stays for synthesis).
    - **B2 unified leverage & survival** (`LeverageSurvival`): ONE block, the CIQ NET-debt/EBITDA AND
      the comps TOTAL-debt/EBITDA (name vs peer median) side by side, EACH BASIS LABELED — this retires
      the net-vs-total 3.9x/5.8x incoherence permanently; + interest coverage, survival, and the S&P-MI
      credit-health scores whose **scale direction is verified FROM THE DATA** (rated peers score low,
      distressed high ⇒ 1=strongest…4=weakest; UNKNOWN if the correlation is absent). The Quality
      leverage lines moved here (a pre-B2 dossier.json falls back to them — regression-pinned).
    - **B3 implied valuation** (`ImpliedValuation`, POSED not concluded): CIQ's implied EQUITY table
      (basis × Low/Median/Mean/High) + the TEV→equity bridge + the name's ACTUAL market cap adjacent,
      with the heterogeneity gate verbatim on the header. **HARD FENCE: no computed %/delta/discount/
      upside field anywhere** (no-conclusion schema-walk extended to B1/B2/B3; a test asserts no `%` in
      the rendered block).
    - **B4 table-style unification:** ONE shared table renderer (`render._table` with a `<!-- ds-table
      -->` marker; frontend `dataTable`) — trading multiples, the B1 grid, margin/trajectory/surprise,
      and the catalyst tables all route through it; the legacy frontend `catTable`/`seriesTable`-HTML
      path is deleted. A grep-style test confirms every table carries the marker.
    - **Riders:** R1 optional `data/manual/ciq/<T>/AS_OF` sidecar (precedence: workbook header >
      operator-attested sidecar > floor; an attested date downgrades the staleness caveat to none —
      three branches pinned). R2 any `Entitlement Needed` cell → "undisclosed (CIQ entitlement)"; a
      revision broker → "broker undisclosed". R3 stale guide reads "(stale — Nd old)" once (no repeated
      date); a point guide renders numeric (427.5), a range verbatim.
    *Verified on the REAL MVST export (git-ignored): the per-peer grid (name row distinct, median
    footer, NM intact); the unified leverage block with BOTH bases labeled + peer median + credit
    scores scale-labeled; the implied table with the heterogeneity gate on its header and NO % anywhere;
    every comps block stamped as-of 2026-06-24 from the header; the trading-multiples table in the
    shared compact style; the AS_OF-sidecar precedence. Frontend confirmed by a real preview render
    (grid name-row/median-footer styling, leverage/implied sections, no console errors). ruff + mypy
    --strict (68) + `pytest -m "not network"` green; regression tests for B1/B2/B3 + R1/R2/R3 + B4 +
    old-JSON fallback. On a branch → PR; the agent never merges. Operator re-assembles + commits the
    artifacts post-merge (#51 precedent).*
  - **PR B.1 — table-unification completion + grid legibility (2026-07-02).** Display-only follow-up
    (`render.py` + `dossier.js` + tests; no extractor/schema change).
    - **B4 completed:** the Trading-multiples table AND the Peer-set roster now route through the ONE
      shared table renderer (they were the last plain-text holdouts); the legacy frontend
      `peerFactTable` + `PC_NAME`/`PC_PEER` path is DELETED. The unification test was rewritten to
      ENUMERATE every GFM table in the rendered markdown and assert each carries the `<!-- ds-table
      -->` marker — it fails before this fix (roster/multiples were `_fact` text) and passes after
      (the test PR B needed). Also fixed a latent md-grid misalignment (the `cols` list included
      "Company", double-counting the label column).
    - **Grid headers:** full words — "EBITDA margin", "Rev growth (1y)", "EBITDA growth (1y)",
      "Total debt/EBITDA", "Net debt ($M)" (md + frontend + PDF).
    - **Numeric hygiene (ONE shared formatter set per layer):** ratios to one decimal (2.0 not 2);
      negative-zero suppressed (`round()`→int, so −0.4% → 0%); a negative net-debt renders "(net
      cash)" (CATL −42,108 → "42,108 (net cash)"); consistent thousands separators. Pinned incl. the
      −0.4%→"0%" and CATL net-cash cases.
    - **R1 CONFIRM:** the AS_OF-sidecar precedence (header > operator-attested sidecar > floor;
      attested downgrades the staleness caveat to none) **had already shipped in PR B** — confirmed
      present (`_sidecar_as_of`/`comps_as_of` + the three-branch test), no re-implementation needed.
    *Verified on the REAL MVST export: the roster + trading-multiples + grid + implied all render as
    tables in the shared compact idiom; the grid's full headers; CATL "42,108 (net cash)"; Cummins
    "0%"; and — with an AS_OF sidecar placed — the catalyst as-of reads "operator-attested" and the
    unverified-export caveat is gone (sidecar removed after; data/ stays git-clean). Frontend
    confirmed by a real preview render (4 tables, no console errors). ruff + mypy --strict (68) +
    `pytest -m "not network"` green. On a branch → PR; agent never merges.*
  - **PR C — Financial-Summary appendix (actuals + consensus fusion) + three riders (2026-07-02).**
    A new **APPENDIX — FINANCIAL SUMMARY** section (rendered AFTER the twins, before the verdict
    footer) plus riders R1–R3. Scope: `ciq_sheets`/`mechanical`/`render`/`schemas`/`flags`/
    `synthesis` + `dossier.js` + tests. New schema: `FinancialSummary`/`FinTable`/`FinRow` (a table
    of FACTS — the no-conclusion schema-walk now reaches them, asserted).
    - **C1 annual + estimates** — last-4-FY + LTM actuals (Income Statement + Cash-Flow essentials,
      C4) fused with **FY2026E/FY2027E consensus** (Estimates→Trends 'Current'). E columns are
      marked + as-of-stamped (header > sidecar > floor); revenue growth is **NEVER computed across a
      basis change** ("— (basis)") and the actual→estimate boundary reads "E vs actual". Core rows
      fail-loud UNKNOWN; supplementary render-if-present.
    - **C2 trailing-8-quarter** — Revenue, gross margin, EBITDA (+margin) *iff* the quarterly export
      carries EBITDA else the rows are OMITTED and the note says so, QoQ, and **same-basis-only YoY**
      (a Reclassified quarter four back reads "— (basis)").
    - **C3 balance-sheet posture** (period-labelled) + the **BS↔bridge coherence gate**: the Balance
      Sheet cash/debt must reconcile with the implied-valuation bridge (a DIFFERENT CIQ sheet); on
      disagreement it renders BOTH with sources + a soft caveat — never silently prefers one.
      Net-debt/EBITDA is NOT recomputed (cross-refs the leverage block).
    - **R1 credit-health completion** — all four dimensions AND the **peer median per dimension**
      (was Overall-only): "peer-median O/Op/S/L …".
    - **R2 twin-integrity guard (bug → root cause → regression-pinned).** *Bug:* the LLM sometimes
      emitted a "twin" that is the SUBJECT compared to itself — fluent self-referential noise. *Root
      cause:* twin validation checked citations/numerics but never that a twin is ANOTHER entity.
      *Fix:* a schema-level guard drops a twin naming the subject UNLESS it cites an explicit resolved
      past period ('2022-2024 arc'); each drop emits a **dev-only QA flag** (hidden from the human
      caveats). *Pinned:* a synthetic self-ref twin is dropped, a dated self-arc + a genuine
      other-company twin both survive.
    - **R3 internal-rule leak (bug → root cause → regression-pinned).** *Bug:* synthesis text could
      leak an internal instruction reference ("per rule 8"). *Fix:* a `_SYSTEM` clause forbids it +
      a QA lint flags any `rule \d+` in the rendered synthesis fields (dev-only). *Pinned:* a
      "rule 8" leak is flagged and classified hidden-QA.
    - **All appendix tables born through the shared compact renderer** — the B.1 enumeration test is
      extended to them (every GFM table carries the `<!-- ds-table -->` marker; C1 + C2 included).
    *Verified on the REAL MVST export (6 cases): (1) annual FY26E/FY27E marked + floor-stamped
    (≥2026-05-15), FY26E rev 444 / EBITDA 62 — coherent with the catalyst acceleration read; the
    FY23(R)→FY24 growth reads "— (basis)", the FY25→LTM reads "— (basis)", the LTM→FY26E reads
    "E vs LTM +20%" (naming its TRUE base). (2) 8Q Q1-2026 collapse visible (96→61, QoQ −37%) with
    same-quarter/same-basis YoY guards ("— (basis)" across the Reclassified quarters, a clean +9%
    where same-basis). (3) BS posture cash 126 / debt 326 / net debt 200 RECONCILES with the bridge
    (126/326). (4) credit health all four peer-median dims (2.5/2.5/3/3). (5) a synthetic
    self-referential twin dropped with its hidden QA flag. (6) every appendix table via the shared
    renderer (2 tables = 2 markers). Frontend confirmed by a real preview render — appendix sits
    after the twins / before the verdict, both tables + posture + coherence render, no console errors
    (the injected preview artifact was reverted; the PR carries code+tests only).*
    - **Post-review AUDIT hardening (3 parallel adversarial reviewers + empirical MVST probes; each
      fix regression-pinned).** Six defects found and fixed before merge — none broke MVST (all were
      latent on the specific export), but each corrupts the analyst's numbers on other inputs:
      (a) **coherence fail-loud** — a bridge that omits the debt row no longer renders a false
      "DISAGREE" with a fabricated "$0M"; the absent leg reads "not cross-checked" (a "never
      fabricate" fix). (b) **quarterly YoY same-quarter guard** — a duplicated/gapped quarter no
      longer produces a cross-quarter number mislabelled "YoY" (restores the check the pre-existing
      `_quarterly_revenue_yoy` already had). (c) **cash-flow join** by fiscal-period identity
      (short, is_ltm) + duplicate→"—" — NOT the bare short (collision) and NOT the reclass flag (CIQ
      tags a P&L reclass on the IS but not the CF for the SAME year — real MVST FY22/FY23 — so a
      basis match would drop valid CF). (d) **BS posture as-of anchoring** — every line read at the
      cash column's period; a partial latest quarter no longer stitches a stale debt or a
      period-mixed NWC under one "as of". (e) **FY↔LTM is its own basis** — growth never spans the
      FY↔ttm boundary ("— (basis)"), and the estimate boundary names its true base ("E vs LTM"/"E vs
      FY") not a misleading "E vs actual". (f) **R2 twin-guard false-DROP** — whole-token matching +
      a generic/industry denylist, so a short ticker inside another name ("BA"⊂"Alibaba") or a shared
      lead ("General"/"First"/"Solar") no longer silently drops a legitimate peer twin.
    *ruff + mypy --strict (68) + `pytest -m "not network"` (293, incl. the 6 audit regressions) green.
    Audited, fixed, and merged on explicit per-PR approval.*
  - **Retro-AUDIT of the MERGED PRs #57 (PR B) and #58 (PR B.1) (2026-07-02).** 3 parallel adversarial
    reviewers + empirical MVST probes over the comps extraction/math + the shared renderer/formatters.
    Leverage/schema/wiring came back CLEAN (net-vs-total invariant, field-reuse, back-compat, manifest
    all correct); all comps indices/medians/bridge verified correct against the real MVST export. Fixes
    (own branch → PR, not merged):
    - **CRITICAL — implied-EQUITY markdown table was column-MISALIGNED (#57).** `_implied_lines` listed
      "Basis" in `cols` AND `r.basis` in the row, so with `_table`'s prepended blank header the header
      was one column wider than each data row — every Low/Median/Mean/High rendered one header to the
      LEFT in `dossier.md` (e.g. the High implied-equity $1,794.7M shown under "Mean"). The web view was
      already correct; only the committed `.md` was wrong. Fix: `cols = [Low, Median, Mean, High]`, basis
      is the row label. **Regression-pinned by a new column-alignment sweep over EVERY rendered table.**
    - **MEDIUM (latent) — S&P disclaimer row admitted as a peer (#57).** `_comps_layout` treated any
      `"("`-bearing row as a company; the Credit Health Panel (no "Summary Statistics" delimiter) pulled
      the "No content (including ratings…" boilerplate into the peer set — benign today (None-filtered)
      but a hazard via the `company[-1]` subject fallback. Fix: require a real `(EXCHANGE:SYMBOL)` ticker
      (`_row_ticker is not None`); verified it drops ONLY the disclaimer, no real peer, on every sheet.
    - **PY↔JS formatter parity (the "ONE shared formatter set" was two that drifted).** `_pctc` now uses
      half-up (`floor(x+0.5)`) to match the web/PDF `Math.round` (they disagreed at every x.5% — 12.5% →
      12 vs 13); `_numc` suppresses negative-zero; the JS `_ratioC` no longer fabricates "0.0" from a
      blank (`Number("")===0`) and `_pctC` no longer masks NaN as "0%"; JS thousands pinned to en-US.
      (0 MVST cells were actually diverging — latent, but real.) Node-verified parity + PY pins extended.
    - **Not fixed (noted):** en-dash vs em-dash for empty cells (`.md` "–" vs web "—") — cosmetic, not a
      number; unifying would churn the pinned B.1 formatter test for no numerical gain.
    *ruff + mypy --strict (68) + `pytest -m "not network"` (296) green; JS fixes node-verified. On a
    branch → PR; NOT merged (awaiting review).*
  - **PR D — facts-first restructure + bull/bear ordering + caveat shape + C-riders (2026-07-02).**
    A display/prompt-layer restructure of the dossier (render.py + flags via synthesis + dossier.js +
    schemas), phase-gated (Phase-1 render preview → operator approval-with-notes → Phase-2 build).
    - **D1 facts-first section order** (md + web/PDF agree): caveats FIRST → drawdown cause &
      idiosyncrasy (CLUBBED) → leverage & survival (+ FCF + liquidity) → trajectory → valuation &
      own-history → peer comps (+ implied) → catalyst → concentration → synthesis (balance → bull →
      bear → decisive → unknowns → **twins LAST**) → appendix (+ the relocated management-commentary
      pointer) → verdict footer. Old committed JSONs still render (optional-safe; an appendix umbrella
      keeps the mgmt pointer from orphaning pre-C).
    - **D2 merged trajectory table**: 'Margin trend' + 'Multi-year trajectory' (two free-text views,
      parsed display-only) → ONE table (revenue · EBITDA · EBITDA margin · gross margin · ROIC) + the
      same-quarter YoY footnote; zero value drift; ROIC (whose source omits the (R) marker) matched
      marker-insensitively so it fills the reclassified columns; footnote fragments deduped (N6).
    - **D3 deterministic bull/bear ordering** (render-side sort, NEVER a schema/LLM field): tier
      taxonomy 1 solvency/cash · 2 revenue trajectory · 3 margin structure · 4 competitive/
      concentration · 5 valuation & relative price action; within a tier structured-cited >
      transcript-cited > LLM-suggested; multi-tier → HIGHEST tier; unclassifiable → 4.5 (never
      dropped); ties → emission order (stable). **N1 concession-clause stripping** classifies on the
      claim's PRIMARY assertion (text after 'though/but/however/offset by/posing whether/the human
      must weigh' is dropped pre-classification). **The keyword map is declared in `render._TIER_KEYWORDS`
      and set by FACE-VALIDITY only** (never tuned on outcomes). Tier tags are DEV-VIEW only. *(PR-E R1
      adds a `render._TIER_REGEX` layer checked BEFORE the keyword map — word-boundary patterns with
      interposition tolerance, e.g. 'EBITDA … negative' with ≤3 words between; same face-validity
      governance, same dev-view-only status, no outcome tuning.)* *(Audit follow-up: the bare
      'turned negative' — both the keyword and the regex alt — was SUBJECT-SCOPED to solvency/cash
      lines (EBITDA/cash-flow/FCF/OCF), so a subject-less 'competitor guidance turned negative' no
      longer false-classifies Tier-1; the real cases still land Tier-1.)*
    - **D4 caveat shape**: a guardrail caveat renders the FULL offending sentence (synthesis no longer
      `_snip`s the human caveats — truncation retained for the dev-only QA flags) in the what / where /
      why-it-matters / how-to-verify shape; a mechanical / 'pull CIQ …' caveat stays one full bullet.
    - **D5 appendix riders**: (a) EPS split into same-basis **EPS (GAAP, dil.)** (Trends 'EPS (GAAP)',
      FY26E 0.18) + **EPS (Normalized)** (0.04) — a basis absent from Trends renders "—", never borrows
      the other; (b) FCF row relabeled "FCF (levered, CIQ)" + "NOT CFO − capex" footnote (display-side);
      (c) an FY estimate's growth is vs the **prior fiscal year** ("+4% (vs FY25)"), not the overlapping
      LTM. **SCOPE AMENDMENT (spec self-contradiction, found-and-resolved):** the plan said "NO extractor
      changes" but D5(a)/(c) require `ciq_sheets.financial_summary_annual` (the GAAP-EPS series isn't in
      the assembled FinTable, and the growth cell is extractor-computed). Operator authorized a minimal,
      contained `financial_summary_annual`-only change, ISOLATED as its own commit for independent
      bisect; the "no extractor changes" line was in error for D5a/c. Everything else stays display/
      prompt-layer.
    - **D6 twin rules**: (a) single-entity guard — a twin name with '/' or 'cohort' is DROPPED (dev-only
      qa_flag); an '&' name (AT&T, S&P) is a legitimate single entity → FLAGGED for QA but RENDERED;
      (b) synthesis prompt gains a grounding PREFERENCE (peer roster / the name's own resolved arc →
      prefer sourced twins over unsourced) — a preference, not a mandate; no outcome-direction steering.
    - **D7 (maturity-wall quantification) DETACHED** here → **LANDED in PR E** (next entry): the flat
      `liquidity_covenant_flags` string is replaced by structured `capital_structure` instruments +
      a deterministic month-precision wall. Per the D conditional it was NOT regex-parsed inside D;
      it moved to (and is delivered by) the survival-completion PR.
    *Verified on the REAL MVST export (6 cases): new section order end-to-end (md + web); ONE trajectory
    table, values identical to the old pair; bull/bear in taxonomy order (the wall/cash points sort T1
    ahead of the T5 relative-price point; the GAAP-illusion earnings-quality point sorts T1 via
    'adjusted EBITDA was negative'); a long caveat un-truncated in the four-part shape; appendix EPS rows
    0.18/0.04 labeled, FCF relabeled, growth '+4% (vs FY25)'; a synthetic compound twin dropped + an
    '&'-named twin surviving with a QA flag. Frontend confirmed by a real preview render (no console
    errors; the injected preview artifact reverted). ruff + mypy --strict (68) + `pytest -m "not network"`
    green; the extractor D5a/c isolated in its own commit. On a branch → PR; NOT merged (awaiting review).
    Reader-feedback points 3, 9, 10, 11 close with this restructure.*
  - **PR E — survival completion: structured capital structure + month-precision maturity wall +
    covenant/8-K pointers (2026-07-03).** Closes the flat-string survival gap (D7 landed): the pre-
    joined `liquidity_covenant_flags` string is replaced by structured, source-bound facts. Root cause
    of the prior gap recorded: the 8-K fetch was **gap-down-anchored only**, so a facility maturing
    with no price gap (the common case) was never linked to its resolution filing.
    - **E1 structured instruments** (`CapitalInstrument`/`CapitalStructure` on the mechanical layer):
      the latest CIQ Capital-Structure-Details panel parsed by header LABEL (the `\xa0` float header
      normalised so SOFR shows; `Principal Due`/`Repayment Currency` prefix-matched; the `Convertible`
      column's `Convertible`/`No` string → bool; `-` maturity is undated=None, never a fabricated
      date) + the Summary aggregates (term-loan QoQ + latest-quarter total debt). Renders as the
      shared-idiom table (RENAMED "Capital structure (instruments)"); a pre-E JSON falls back to the
      legacy liquidity string.
    - **E2 deterministic month-precision maturity wall**: calendar-year grouped vs the reference —
      matured-pre-reference (resolution NOT in this data → "verify each against its 8-K; NEVER assume
      repaid or defaulted"), due-≤12m (this ref year), later years, undated floor + an itemized
      reconciliation to the latest-quarter aggregate. No probability / risk / conclusion language.
    - **E3 maturity-anchored 8-K fetch**: extends the drawdown 8-K logic to fetch 8-Ks within ±10d of
      ANY instrument maturity in the trailing 12m — POINTERS ("read for resolution"), never an
      assumption. **E4 covenant pointers (Tier 1)**: the latest 10-K exhibit index (ex-10.x, substring-
      matched) + EDGAR efts on the instrument-family description → accession-bound pointers, or an
      honest-absence UNKNOWN. **E5 covenant terms (Tier 2, fenced)**: stays UNKNOWN in the deterministic
      mechanical layer; the note is opacity-as-signal (whether an exhibit exists to read vs a wholly
      undocumented facility) — extraction is fenced to the LLM phase. The no-conclusion walk now reaches
      both new models (non-vacuous).
    - **Riders — R1** D3 tier regex tolerates words interposed between 'EBITDA' and 'negative'
      ("adjusted EBITDA of NEGATIVE $5.5M" → Tier 1, was 4.5); **R2** a self-referential twin is
      suppressed UNLESS the resolved period is in the twin NAME ("Microvast (2021–2025 arc)"), a bare
      "Microvast Holdings" suppressed even with a year hiding in the outcome; **R3** the frontend clubs
      drawdown + idiosyncrasy under one section header to match the md.
    *Verified on the REAL MVST export + LIVE EDGAR: 8 instruments parse (SOFR+9.750% floating shows,
    CNY currency, serials→ISO, undated `-`→None); the wall pins reproduce exactly (matured $25.0M @
    2026-05-28 / ≤12m $42.9M @ 2026-12-10 / 2027 $105.1M / undated $95.6M / reconciliation itemized
    $268.6M); E3 hits accession 0000947871-26-000585 (filed 2026-05-28); E4 hits ex1013/ex1021 in
    0001628280-26-018264 + an efts family pointer. Frontend confirmed by a real preview render (E1
    table + E2 wall + R3 club; injected artifact reverted, no artifact commit). +12 tests (10 offline +
    2 network-marked E3/E4 live pins); the no-conclusion walk extended to both new models. ruff + mypy
    --strict (68) + `pytest -m "not network"` green. On a
    branch → PR; NOT merged (awaiting review). Reader-feedback point 6 (survival completion) closes.*
    **Post-merge audit fix (self-audit #62 → PR #65): the maturity-wall JS mirror bucketed by
    `getUTCFullYear()` on a LOCAL-midnight Date, so a `YYYY-01-01` maturity mis-bucketed into "≤12m
    prior-year" for any UTC-ahead viewer (IST/Europe/Asia) — the JS silently violated the pinned
    calendar-year contract the Python test enforces. Fixed to bucket by the ISO date STRING
    (timezone-free, matches `date.year`); also routed `_mM` through en-US thousands to match
    `render._musd` for $1B+ totals. Verified under Asia/Calcutta + a browser render.**
  - **PR F — positioning inputs: EDGAR Form-4 insider activity + FINRA short interest (2026-07-03).**
    Two NEW free, DATED feeds slotted into the catalyst path — the objective inflection markers
    EDGE_THESIS names in the Edge-2 discriminator ("*multiple at floor; **short interest peaking;
    insiders beginning to buy***"). Face-validity basis, never tuned; the machine COUNTS and CITES,
    it does not conclude.
    - **F1 insider activity** (`mechanical._insider_activity`): trailing-6m Form 4s via the CIK
      submissions feed; each raw ownership XML parsed for non-derivative codes — open-market **P/S**
      drive the counts + net shares (net = ΣP − ΣS), routine **A/M/F** tallied separately, any other
      code (e.g. a conversion **C**) LABELED not dropped. Renders "P×n / S×m · net ±K sh · last date
      · routine … · other …", source-bound to the latest accession; fail-loud UNKNOWN when none on
      file. Counts + dates only — no interpretation.
    - **F2 short interest** (`vinci/finra.py` + `mechanical._short_interest`): FINRA's public query
      API (`api.finra.org`, delayed, no entitlement) — latest settlement's shares short + FINRA's own
      Δ% + days-to-cover computed against the SCREEN 90d ADV (no ADV recompute; the DTC basis is
      bound in the citation). DATED as-of (no export-floor). The column layout is PINNED — a
      renamed/dropped column raises `FinraLayoutError` (the STOP-AND-REPORT rule: never guess a
      column). Filtering is POST-only (the endpoint ignores GET params), so `netcache.CachedHttp`
      gained a cached `post_json` (GET path untouched). Both feeds registered in the input manifest
      (`requirements.EDGAR_FREE_INPUTS` Form-4 entry updated to "now consumed"; new `FREE_FEED_INPUTS`
      for FINRA — the don't-double-pull-from-CIQ rule).
    *Verified on the REAL MVST export + LIVE EDGAR/FINRA: F1 → "P×0 / S×7 · net -121.0K sh · last
    2026-06-12 · routine A×20 · other C×1" (18 Form 4s, incl. 3× on 2026-06-12; zero open-market buys
    — the honest picture) pinned to accession 0000947871-26-000620; F2 → "Short interest (FINRA,
    settle 2026-06-15): 26.3M sh (+22.9%) · DTC 5.7d" (DTC = 26,323,600 ÷ 4,607,454 screen ADV, vs
    FINRA's own 6.25 on its ADV). Frontend confirmed by a real preview render (both blocks in the
    catalyst section, cited; injected artifact reverted, no artifact commit). +14 tests (12 offline
    incl. the FINRA layout-pin + post_json cache + the limit-cap guard, 2 network-marked live pins).
    The no-conclusion walk already reaches CatalystPath → the two `Sourced[str]` positioning fields
    are covered (asserted). **Post-audit fix (self-audit #63): FINRA's query API returns rows
    OLDEST-first and can't be server-sorted, so the old `limit=8` silently DROPPED the newest
    settlements once a window held ≥9 (latent — a 120-day window holds ~7 today); raised the cap to 50
    AND fail loud (`FinraLayoutError`) if the cap is ever hit, so a stale settlement can never be
    dressed as "the latest".** ruff + mypy --strict (69) + `pytest -m "not network"` green. On a
    branch → PR; NOT merged (awaiting review).*
  - **PR G — implied expectations: price-inverted, multiples-space (2026-07-03).** Stacked on PR F
    (branched off `feat/positioning-inputs`, the post-F state — F was not yet merged). NO new
    extraction: every input is an ALREADY-ASSEMBLED field; deterministic arithmetic only.
    - **G1/G3 the block** (`Valuation.implied_expectations`, renders after cross-sectional, before
      own-history): for a FIXED declared multiple set — name NTM TEV/EBITDA, peer-median NTM & LTM
      TEV/EBITDA (+ the same trio on TEV/Rev) — `implied_level = TEV ÷ multiple`. TEV is **DERIVED**
      (mcap + net debt = simple-TEV basis, labeled in the source_ref) since it is NOT surfaced as a
      field: the workbook TEV cell carries a stale SECOND pricing vintage (Historical-Capitalization
      TEV 872.8 @ ~$2.02) alongside the Latest mcap (423.1 @ $1.27), so deriving from Latest-mcap is
      vintage-coherent by construction. Each row {multiple(source), implied_level, adjacent anchors};
      NM/negative/absent multiple → UNKNOWN row (guarded division, never a synthetic multiple).
      FENCE (block-scoped, NOT global — 'value' would trip `Sourced.value`): the two G models carry no
      price/equity/value/upside/discount field; render has ZERO % or value-space tokens.
    - **G2 render** (shared table): heterogeneity gate VERBATIM on the header + the framing line +
      BOTH pricing as-ofs; anchors juxtaposed, NEVER differenced; footnote names the fixed set as
      declared-in-code. **G4**: the block rides the full `mech.model_dump()` into the synthesis input
      AND the number-trace universe automatically (no synthesis change) — asserted by a test.
    - **G5 vintage-coherence guard** (this incident earned it): the residual |derived-FY26 −
      direct-FY26 consensus| ÷ direct ≤ 0.10 (a DECIMAL, never a %); measured at FY26 — the nearest
      DIRECTLY-sourced consensus EBITDA (NTM consensus is not a sourced level; the shared-TEV ladder
      makes FY26-coherence certify all horizons). Within tolerance → render normally; beyond → a
      "multiple-pricing vintage differs — re-pull comps" caveat + both as-ofs stamped. Plus the
      condition-b net-debt gate (net_debt vs the cash/debt bridge, C3 soft-caveat).
    *Verified on the REAL MVST export (values reproduced by synthetic fixtures — no artifact read):
    TEV $623.0M; the EBITDA triangle **identity $82.6M / peer-NTM $48.3M / peer-LTM $43.0M** (the
    identity = the NTM anchor EXACTLY by construction), the TEV/Rev trio $494.4M/$244.3M/$194.7M;
    consensus anchors **FY26 $61.4M / FY27 $146.2M / NTM $82.6M** (1dp so the NTM anchor prints the
    SAME as the identity row); vintage-coherent (residual 0.011 ≤ 0.10, on the UNROUNDED derived FY26)
    and net-debt reconciled (bridge 326.0 − 126.1 = 199.9). Frontend confirmed by a real preview
    render (block in Valuation, order correct, zero % in the block; injected artifact reverted, no
    artifact commit). +9 tests (parsers, triangle, both coherence branches, net-debt caveat,
    NM/negative guard, block-scoped fence, G4 trace-coverage, back-compat, + a table-column-alignment
    regression) + the no-conclusion walk extended to the two G models. **Post-audit fix (self-audit
    #64): the implied-metric table had 2 data cells under a 3-column header — every implied level
    rendered under the WRONG "Multiple" header; split into label · multiple · level (Python + JS),
    pinned by a column-count regression test.** **Audit follow-up: added the parallel REVENUE
    consensus anchors (FY26 $438.7M / FY27 $587.7M / NTM $494.4M = TEV ÷ the TEV/Rev ladder), so the
    TEV/Rev name-row identity (†) is SUBSTANTIATED — the NTM revenue anchor equals the name-NTM
    revenue implied level, shown not merely asserted.** ruff + mypy --strict (69) + `pytest -m "not network"`
    green. On a branch → PR;
    NOT merged (awaiting review). **Reader-feedback point 2 (implied expectations / reverse-DCF)
    closes: perpetuity REFUTED as a method → the forward-multiple ladder (catalyst_path) + the CIQ
    implied-valuation (B3) + THIS price-inverted block are the standard — all POSED, none concluding
    an implied price or upside.***
  - **PR H (PR 1 of a 2-way split) — covenant-pointer INTEGRITY fix + fenced Tier-2 covenant-term
    extraction (2026-07-03).** Two isolated commits (`--rebase` merge, PR-D precedent), each green
    on its own. **Root cause of the E4 pointer bug, recorded:** the efts full-text search was
    (a) UNSCOPED — no `ciks=` — and (b) queried on GENERIC balance-sheet labels ("Convertible Bond",
    "Notes Payable"). A generic phrase matches ANY filer, so MVST's "covenant exhibit pointer"
    surfaced **AXESSTEL INC's 2005 8-K (`0001193125-05-034397`, a different CIK)** as if it were the
    subject's execution filing. It stayed hidden because the approval probe read the summary STRING,
    not the filer CIK behind it — **a method error: verify the pointer, not the prose.**
    - **Commit A (H1a–c) — pointer integrity.** `EdgarClient.fulltext_search` gains `ciks=`
      (10-digit zero-padded; a bare int returns empty from efts); `_covenant_pointers` REJECTS any
      hit whose filer CIK differs (AXESSTEL dropped). An AGREEMENT-CLASS WHITELIST maps an
      instrument's class to the filing's canonical contract phrase (`_covenant_query`: "Convertible
      Loan With Shareholder" → query "Loan Agreement", which is what the filing actually names it);
      a generic BS aggregate (Notes Payable, a lease) renders an honest "no contract-level filing
      expected (aggregate line item)" note, never a pointer. EXHIBIT-VERIFIED: a kept pointer must
      point to a filing that CONTAINS the agreement as an exhibit (per-accession index.json), not
      merely mention it. Returns `Sourced[list[CovenantPointer]]` → source-bound table (family ·
      filing · date · accession/exhibit-or-note), deduped per family; back-compat to the flat string.
    - **Commit B (H1d/E5) — fenced covenant TERMS.** New `vinci/dossier/covenant_extract.py`: reads
      the located exhibit(s) and extracts named terms — the CONVERSION PRICE / SHARE MECHANICS above
      all — as `CovenantTerm {name, value: Sourced[str]}` rows, each verbatim + source-bound or an
      explicit UNKNOWN. FENCES: verbatim only (never infer/compute — a stated FORMULA is rendered as
      a formula, not a fabricated $/share); **machine-set `source_ref`** (the code sets it to the
      exhibit actually fetched, so the model cannot invent a citation — it fills only the value + a
      grep-able quote); fail-loud (fetch failure / >600K-char exhibit / LLM error → UNKNOWN + flag,
      never a silent blank); assembly-and-cite (the tool schema has no verdict/risk field). Runs in
      `assemble_one` after synthesis, LLM-gated, `model_copy` (frozen). Render + frontend show a
      source-bound term table; pre-H1d JSON falls back to the flat `covenant_terms` line.
    *Verified — Commit A on LIVE EDGAR: `_covenant_pointers` returns the latest-10-K ex1013/ex1021
    (`0001628280-26-018264`), the 2024 Wu Loan & Security execution 8-K (`0001760689-24-000021`, with
    `wu_microvast-loanandsecuri.htm`), the 2022 syndicated-loan 8-K; Notes Payable → aggregate note;
    ZERO cross-CIK accessions (AXESSTEL gone). Commit B — REAL Opus 4.8 on the live Wu exhibit (the
    deliverable, cond. b): Conversion = "$1.00 ÷ Conversion Rate; Rate = 2 shares per $1.00 principal;
    partial-conversion min $100,000; 9.99% ownership blocker" (formula + rate, NOT a fabricated
    $/share); principal $12M+$13M (Yang Wu 100%); interest Term SOFR + 9.75% + 3.75% PIK; min-liquidity
    covenant $5M weekly — all source-bound to `wu_microvast-loanandsecuri.htm`. Cross-exhibit: the
    2025-03-17 amendment 8-K surfaced maturity AMENDED Nov-28-2025 → May-28-2026, with conversion/
    principal honestly UNKNOWN ("not stated in the amendment"). +6 tests (AXESSTEL cross-CIK rejection
    pin, `_covenant_query` mapping, 4 E5: present-verbatim/absent-UNKNOWN source-bound, fetch-fail
    fail-loud, no-pointer no-op, picker-prefers-loan-security) + 1 live network pin. ruff + mypy
    --strict (70) + `pytest -m "not network"` (326) green in isolation per commit. On a branch → PR;
    NOT merged (awaiting review). PR 2 (H2–H7: R1 verify, survival clubbing/dedup, guidance-bridge
    table, positioning display, twin-outcome rule, FY-E anchor) branches after PR 1 merges.*
    **PR 1 MERGED (--rebase, commits preserved on origin/main): 5b0c646 (A) · 9fc8bd2 (B) ·
    0a4970f (STATE).**
  - **PR H (PR 2 of the split) — H2–H7 dossier polish (2026-07-03), off the merged PR-1 main.**
    Five logically-isolated commits; each green. **H2 (R1 verify):** the draw phrasing "adjusted
    EBITDA of NEGATIVE $5.5M" already classifies Tier-1 via the interposition-tolerant
    '(adjusted) EBITDA … negative' regex arm ('of' = the 1 interposed word) — NO fix needed; pinned
    the EXACT string. **H7 (FY-E anchor):** the G EBITDA consensus anchors switch from TEV÷ladder to
    the DIRECT Estimates→Trends latest levels (single source of truth: FY26E $62.1M / FY27E $147.7M —
    the spec's "148" rounded); new `ciq_sheets.trends_fy_level` reads a SPECIFIC FY column (accel-read
    is FY-current only); the ladder-derived FY26 now lives ONLY in the vintage-guard line; the REVENUE
    anchors keep the ladder basis (they substantiate the TEV/Rev † identity — a different job). **H6
    (twin outcome):** an '[LLM-suggested, unverified]' twin's outcome renders "… (LLM-claimed —
    verify)"; a roster/self-sourced twin renders plain (deterministic, render-side; MVST QuantumScape
    + Romeo Power flagged, Amprius/Forsee/Leclanché plain). **H5 (positioning display):** short
    interest → "prior → latest (±%, rising/falling) · X% of shares out (EDGAR XBRL count) · DTC ·
    recent: latest-4 settlements" (new `_edgar_shares_outstanding`, dei+us-gaap; % omitted when
    absent); insider → PLAIN LABELS "Open-market buys n · sells m (net ±K) · grants g · last date"
    (grants = A code; M/F/C preserved under 'other'); sign-descriptors only — the no-conclusion walk
    EXTENDED to these strings by a test asserting neither matches the directional regex nor an
    interpretive-token list. **H4 (guidance-bridge table):** metric | latest guide | for | dated |
    age | record | most-recent, via a new `GuidanceRow` + optional `guidance_bridge_rows`; the flat
    string and the rows share one `_guidance_reads()` extraction (no drift, string contract
    preserved). **H3 (survival clubbing + dedup):** retire the coarse "nearest maturity wall: YYYY"
    line (delete the orphaned `_nearest_maturity`) — the month-precision E2 wall in the single
    "### Leverage & survival" section supersedes it; a render-level dedup folds repeated identical
    UNKNOWN reasons to ONE line with the affected-fields list (MVST 99.1 case: 3 renders → 1, no fact
    suppressed); the heterogeneity gate renders verbatim ONCE (Peer-comps head) and short-ref
    "comparability: HETEROGENEOUS (see Peer comps gate)" at the G + Implied-Valuation headers.
    *Verified on REAL MVST (render of the committed dossier.json + live CIQ/EDGAR/FINRA): H7 anchors
    "FY26E $62.1M · FY27E $147.7M (direct Trends)" with the ladder FY26 $61.4M in the vintage-guard
    (residual 0.010); H6 QuantumScape "recovered (LLM-claimed — verify)"; H5 insider "buys 0 · sells 7
    (net -121.0K) · grants 20 · last 2026-06-12 · other C×1" + short "21.4M → 26.3M sh (+22.9%, rising)
    · 7.9% of shares out (EDGAR XBRL) · DTC …"; H4 guidance table (Revenue/Capex/GrossMargin, sign-aware
    records, stale ages); H3 the 99.1 UNKNOWN once + gate short-ref'd. +~8 tests (trends_fy_level,
    the exact-tier pin, twin QuantumScape, positioning no-interpretation guard + new SI/insider
    formats, guidance rows, gate short-ref + dedup) — existing IE/survival/short-interest tests
    updated for the new shapes; the guidance STRING contract preserved. ruff + mypy --strict (70) +
    `pytest -m "not network"` green. On a branch → PR; NOT merged (awaiting review).*
    **Post-audit fix (H1–H7 audit, 4 parallel review passes + real-run checks; math traced clean).
    4 confirmed defects fixed on PR #69: (1) DISPLAY — a `|`/newline in a table cell shattered the
    GFM table; `_table` now sanitises every cell (`_gfm_cell`), the E5 verbatim covenant value/quote
    was the exposure (frontend HTML already immune); (2) EXTRACTION — a `.html`-named agreement
    exhibit was dropped by the covenant-pointer `.htm`/`.txt`-only filter (documented facility →
    "undocumented"); now accepts `.html` (H1 / PR #68 code, riding in #69); (3) DISPLAY — H7 made the
    EBITDA anchors UNKNOWN-able but the render printed the bare word "None"; `_sourced_str` shows the
    note (render + frontend); (4) HARDENING — the H3 cross-section reason-fold now fires only for
    DISTINCTIVE reasons (≥30 chars) so a coincidental short-generic collision can't relocate a fact
    (the 99.1 case still folds). +4 regression tests; gate green.**
  - **PR 3 (feat/dossier-integration) — synthesis-integration completion + contradiction lint
    (2026-07-03), off the merged PR-2 main.** Three logically-isolated commits (each green in
    isolation; --rebase merge to preserve them) + a STATE commit. **FIX-0 (the load-bearing find):
    E5 covenant extraction ran AFTER `synthesize()` in `assemble_one` — at synthesis time
    `covenant_term_rows` was `None` and `covenant_terms` still held the `(E5) extract in the LLM
    phase` PLACEHOLDER, so the LLM was handed a pointer to a fact it could not see and wrote
    "Covenant terms are UNKNOWN (extract pending)" while the finished JSON held 16 extracted values;
    the "16 of 20 … see the table" line was a post-synthesis render digest.** Fix = reorder
    extraction BEFORE synthesis + feed the model a curated term→value DIGEST. **Commit A (pipeline
    core, `24bd99b`):** covenant + maturity extraction now run before `synthesize()`; P1
    `covenant_digest` (curated survival terms, leads with the derived $/sh conversion, ≤1500-char
    cap, and on failure emits an honest `extraction failed: <reason>` string — NEVER a pointer, so a
    failed extract can't reintroduce FIX-0); P3 `extract_maturity_event` + `maturity_event: Sourced`
    (a `_primary_body` picker skips index/header/metalinks/filingsummary/`^r\d+\.htm` scaffolding and
    prefers the `8-k|form8` body — MVST resolves to the May-28 Notice of Conversion, not the
    index-headers stub); P4 round-robin `_core_agreement_exhibits` (`_MAX_EXHIBITS=4`, distinct
    live-wall families extracted before amendments). **Commit B (guards, `02df88a`):** P2
    `contradiction_flags` — flags any synthesis pending/unread claim whose SUBJECT is a PRESENT
    `covenant_term_rows`/`maturity_event` block (specific subjects only, never bare "8-K"); QA
    channel ("CONTRADICTION"). P6 e2e pin asserts the GAAP-artifact point's rendered POSITION inside
    the Tier-1 group on the committed JSON + a python↔JS classifier/sort PARITY test — which exposed
    that **PR-E's R1 interposition-tolerant regex was NEVER mirrored into `views/dossier.js`** (GAAP
    point was T1 in Python, T2 in JS); R1 now mirrored → zero divergence. **Commit C (render/policy,
    `827eff7`):** P5 `governing_terms` collapses per-exhibit rows to ONE governing value per
    (family, term) — latest-dated PRESENT wins, amendment supersedes base — rendered as per-family
    governed tables (Python + JS byte-identical); P7 survival clubbed to ONE `### Leverage &
    survival` section; P8 generalized `_direct_ebitda_anchors` → `_direct_anchors(metric)` so REVENUE
    anchors read the DIRECT Estimates→Trends latest levels (not the ladder); FIX-2 routes the
    `(E5)`/`(P3)` machine notes (cost bound / fetch fail) to the QA channel, out of the analyst
    caveats. *Verified on REAL MVST fresh full assembly (166s; write to a TEMP dir — committed
    `data/dossiers/MVST/` untouched): Key-Unknowns lint-clean (no covenant-pending) = **True** — the
    FIX-0 target; the digest is now VISIBLE ("Minimum Liquidity covenant of not less than
    $5,000,000"); CONTRADICTION QA flags on the fresh draw = **0**; synthesis REASONS with the
    conversion — "A $25.0M shareholder convertible loan due 2026 was resolved by conversion into
    common stock" + "Ongoing dilution (+2.9% … plus the $25M shareholder-loan conversion)"; all 4
    core-agreement exhibits extracted incl. the **syndicated facility** (`exhibit101-syndicatedloana`);
    `maturity_event` = the Notice of Conversion; EBITDA anchors `FY26E $62.1M · FY27E $147.7M` +
    REVENUE anchors `FY26E $444.4M · FY27E $591.5M` (both direct consensus); analyst caveats 3 · QA 6
    (cost-bound routed to QA); ONE survival section; the 3 leverage fields fold to ONE 99.1-blocked
    UNKNOWN line; zero "extract pending" in the render. **Latency/cost delta:** the reorder is ~0
    (extraction was already sequential — only its position moved); P4 adds ~46s by extracting 4
    exhibits vs 2 (86s vs ~40s). +11 tests (round-robin, governing_terms, digest, derive_conversion,
    maturity_event, P2 lint, py↔JS parity, e2e GAAP position, P5 governed render, FIX-2 QA routing).
    ruff + mypy --strict (70) + `pytest -m "not network"` (357) + `node --check` green. On a branch →
    PR; NOT merged (awaiting review).*
    **Post-audit fix (PR #70 audit — 4 parallel finders across critical-code / extraction / math /
    display + real-run reproductions; the artifact-leak gate passed — GitHub file list is 10
    code+STATE files, zero `data/dossiers/`). 9 CONFIRMED defects fixed, all concentrated in the P1
    digest path the FIX-0 reorder put on the critical line: (1) MATH/FABRICATION — `_CONV_RATE_RE`
    matched "$1" inside "$1,000", mis-scaling the "N shares per $1,000" BOND convention by 1000×
    ($0.02/sh vs the true $22.00) and front-loading that fabricated dilution figure into the digest;
    the regex now CAPTURES the denomination ($D ÷ N) + is numerator-boundary-anchored + clause-break
    (`;`) bounded → $22.00 (M-1/M-4/M-5); (2) MATH — the per-value (`_DIGEST_VAL`) and maturity
    (`_MAT_DIGEST_VAL`, raised to 300) truncations cut mid-number ("$5,00…"); a new `_clip` backs off
    to a whitespace boundary so a figure is never chopped mid-digit (M-2/M-3); (3) EXTRACTION/
    RESILIENCE — `covenant_digest` emitted a bare header (implying unseen data — the FIX-0 failure
    mode) when the governing set was all-UNKNOWN or non-decision-only; it now returns an honest "no
    survival-critical … terms" line, and `assemble` keys the fail-reason on an actually-PRESENT term
    (`gov_present`), not on `gov` being non-empty (CC-1/CC-2); (4) EXTRACTION/SOURCE-BINDING —
    `governing_terms` fabricated an `amended by` chain on tied/empty filing dates; it now asserts the
    chain ONLY on a real chronology (distinct, non-empty dates), mirrored into `dossier.js` for parity
    (X-4); (5) CODE — `contradiction_flags` false-positived on an all-UNKNOWN covenant block (keyed on
    the row CONTAINER, not a PRESENT value) → require a PRESENT term value (CC-3, QA-channel);
    (6) DISPLAY/PARITY — the FIX-2 "N located exhibit(s) not extracted this run" completeness line was
    Python-only; mirrored into `dossier.js` (D-1, live on MVST) + the maturity verbatim is
    whitespace-collapsed at extraction so it's one clean line in both renderers (D-2); + the stale
    `rev_anchors` "ladder/always-PRESENT" comment corrected (P8). +6 regression tests (each pins the
    exact failing input — the $22-not-$0.02 bond case, boundary-safe truncation, honest empty digest,
    tied-date non-amendment, all-UNKNOWN non-contradiction, JS FIX-2 mirror). REPORTED, not fixed
    under audit (see §Next-steps): X-2 (two distinct facilities sharing a family label collapse —
    needs an upstream per-facility identity, risky to refactor under audit), X-3 (maturity multi-8K:
    only the first is read + acc↔date paired from independent scans — a design change), X-5
    (`_MAX_EXHIBITS=4` drops a 5th distinct family — already loud-flagged, ACCEPTED cost bound), D-3
    (`_citRank` "made-up" clause absent in JS — pre-existing + currently unreachable). Finders CLEARED
    LLM-response handling, `_primary_body` scaffold filter, `_acc_of`, `_direct_anchors`, the
    cs_pre/cs_post chain, schemas back-compat. Re-ran the REAL MVST assembly (160s, temp dir):
    Key-Unknowns lint-clean, 0 contradiction flags, syndicated extracted, maturity present + one clean
    line, conversion reasoned (no fabricated $/sh — MVST is a $25M loan, not a bond), the REAL
    2024→2025 amendment chain preserved (distinct dates), direct EBITDA+Revenue anchors unchanged.
    ruff + mypy --strict (70) + `pytest` (363) + `node --check` green. Rides on PR #70; NOT merged.**
