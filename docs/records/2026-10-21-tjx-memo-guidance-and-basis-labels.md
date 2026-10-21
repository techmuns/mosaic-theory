---
id:
status: shipped
date: 2026-10-21
prs: [756]
supersedes:
superseded-by:
---

# TJX's adjusted-EPS guide is read, and reaches the valuation; two labels stop naming a basis their figure does not have

**WHAT.** Three items from an IC memo on TJX (2026-10-19), each found on Burlington too:

1. **The guide.** TJX's Q2 FY27 release states "the Company is increasing its full year outlook for
   adjusted diluted earnings per share to be in the range of $5.15 to $5.20", and the page said the
   release carried NO NUMERIC OUTLOOK. Four parser causes, all fixed in `vinci/edgar/release_parse.py`:
   - **Vocabulary:** `adjusted diluted earnings per share` / `adjusted diluted EPS` were not metric
     names. They are the same adjusted-EPS metric, not the prefix-free forms row 30 holds back.
   - **The full stop:** a range closing its sentence read its high side as `5.20.`. That doesn't
     parse, so the guide was dropped with no refusal. Target's March guide was lost the same way.
     A number now ends in a digit.
   - **The period:** neither TJX range names its period. "For the third quarter of Fiscal 2027, …"
     sits four sentences above the quarter's range. `_opener_period` reads the nearest capitalised
     `For|In the <period>,` opener, but only under four conditions:
     - it is within 1,500 characters;
     - the opener's sentence looks forward;
     - every sentence between the opener and the range looks forward;
     - the run never names the other scope.
     It runs only where the old rules found nothing, so it can only replace the `next-fy` default.
   - **First-wins:** the parser kept one range per metric per release, so TJX's quarter shadowed
     its year. A later range for the same metric is now kept only when its period was READ (never
     the default) and names a scope not yet held. Every range the old rule kept is still kept,
     first and unchanged.

   In `vinci/dossier/mechanical.py`:
   - **`adjusted_eps` falls back to the newest release.** The field was read from the drawdown 8-K's
     revised guidance only. When that holds none, it now takes the NEWEST results release's annual
     adjusted-EPS level guide, or stays UNKNOWN naming what was read; it never reaches past the newest
     release. `eps_resolved` (which silences the EDGAR-vs-CIQ P/E conflict flag) stays keyed on the
     drawdown guide only.
   - **The UNKNOWN note says which absence it is.** It no longer claims a revised guidance was read
     when none was.
   - **`current_guide` prints at the unit's precision.** Per-share bounds keep their cents, through
     the one rule `_fmt_guide_range` already used. It also says when newer releases carry no parsed
     guide.
2. **The forecast-error label.** R4's evidence printed "FY2026 (US GAAP): actual 6957". "US GAAP" is
   CIQ's 'Acctg. Standard' cell, i.e. the filer's accounting standard. 6,957 is the actual CIQ set
   against its consensus, while TJX's reported FY2026 EBIT is 7,178. The line now names both:
   "CIQ's consensus-basis actual … (filer's accounting standard: US GAAP)". The layer's stored note
   gains the same sentence.
3. **The brief's FCF row.** Both brief twins printed the bare "FCF ($M)", while the appendix already
   relabelled the same row as CIQ's levered FCF. Both briefs now print the appendix's label and its
   basis note (`render._brief_financials` with "FCF (levered, CIQ)"; `dossier.js` `financialSnapshot`
   with "FCF (levered)"). The two twins' labels differ by the word "CIQ", exactly as their appendices
   already did. The rows are still SELECTED on the stored label, so the `BRIEF_CORE_ROWS` parity pin
   is untouched.

**WHY.** Each one is a label or an absence that a reader took as a fact about the business:
- "no numeric outlook" read as management saying nothing;
- "US GAAP" read as the figure's basis;
- "FCF ($M)" read as CFO − capex.

The full-stop and first-wins causes are not TJX-specific: they decided which guide every page showed.

**THE TRAP BESIDE THE FIX (Target).** The full-stop fix makes Target's March guide ($7.50–$8.50)
readable, but its August raise to $9.90–$10.90 is worded in a form the parser does not read ("An
updated GAAP and Adjusted EPS guidance range of"). Taking "the newest release that happens to parse"
would have printed March's guide as Target's earnings power. That's why `adjusted_eps` reads the
newest release or nothing, and why `current_guide` now marks newer releases that carry no parsed
guide. The same hazard was already live on FUBO, LLY, MVST and NFLX, each printing an older release's
guide as "current". Their unread newer releases are row 30's territory and are not widened here.

**HOW VERIFIED.**
- **The corpus, before any pin** (`scratchpad` harness: every EX-99.1 the committed pages cite,
  re-parsed from the SEC cache with main's parser and with this one):
  - 82 → 100 guidance items: 21 added, 3 relabelled, 0 lost.
  - The 3 relabels are Burlington's year, `next-fy` → its own "Fiscal 2025" / "Fiscal 2026".
  - Every added item was read against its own sentence:
    - TJX ×2 (Q3 2027 $1.30–$1.32; Fiscal 2027 $5.15–$5.20);
    - Burlington ×3 (each quarter beside its year);
    - Concentrix ×4 (the full-year revenue guide beside the quarter's);
    - nCino ×5 (the fiscal-year revenue guide beside the quarter's);
    - EPAM ×1 (Q4 revenue beside the year's);
    - Simply Good ×2 (the quarter's net sales beside the year's);
    - Target ×1 (the March guide).
  - One existing first item carries a prior year ("AORT adjusted EBITDA … in 2025"). That is the
    filer's own wording, unchanged by this diff.
- **What re-assembly will print**, computed from each page's cited releases re-parsed with this
  branch, its own filing dates and its stored close:

  | page | `current_guide` before → after | `adjusted_eps` after |
  |---|---|---|
  | TJX | "no guide in any of the 6 parsed release(s)" → "adjusted eps Q3 2027: 1.30–1.32 $/sh; adjusted eps Fiscal 2027: 5.15–5.20 $/sh" | "Fiscal 2027 adjusted EPS guide $5.15–$5.20; adj P/E ~28.5x at $147.33 (2026-10-16 close)" |
  | BURL | "11.8–12.0" → "11.77–11.97 $/sh; adjusted eps Q3 2026: 1.60–1.70 $/sh" | "next-fy adjusted EPS guide $11.77–$11.97; adj P/E ~21.6x at $256.85 (2026-09-22 close)" |
  | TGT | March's guide, marked "2 newer releases (filed 2026-05-20, 2026-08-19) carry no parsed guide" | UNKNOWN, naming the August release it read |
  | FUBO, LLY, MVST, NFLX | unchanged guide, now marked with their newer unparsed releases | — |
- **The FCF render**, previewed from committed JSON before and after. Web (screen and print-to-PDF
  with every `<details>` forced open) and the markdown twin: the row label and one basis line change,
  nothing else moves.
- **Pins:** `tests/test_guidance_opener_period.py` (11), `tests/test_release_adjusted_eps.py` (8),
  `tests/test_basis_labels.py` (4).
  - The parser pins are built from the three filings' own sentences.
  - The FCF and forecast-error pins run end to end over every committed page, in both twins.
  - 9 of the 11 parser pins are red on main's parser. The 2 that pass on both are the
    "stays unread" negatives.
- **Two suite failures on this machine are not this change.** Both fail identically on a clean
  checkout of main 07665419, and both arrived with the 2026-10-20 CIQ mirror into the assembler's
  copy:
  - `test_share_basis::…reconciles_cap_shares_and_price_exactly`: V's committed page was built on
    the export now archived under `ciq-archive/replaced-2026-10-20/V/`, so its cap ÷ shares
    ($362.50) no longer meets the new panel's close ($385.45). V needs a re-assembly.
  - `test_capital_panel_selection::…stamped_with_its_own_provenance`: MCK's `Financials_Annual.xls`
    and `Financials_Quarterly.xls` are the same file (identical SHA-256, on Drive too), so the
    "annual" panel reads a quarter. MCK needs a fresh annual export.
- **Mutation battery:** 22 mutations, 22 killed. Every opener guard, both dedupe conditions, the
  full stop, the vocabulary, the newest-release rule, the annual-only rule, the change-basis
  exclusion, the stale mark, the cents, the absence note, both twins' label and note, the evidence
  label and the stored note sentence.

**ROW 30, MEASURED (in memory, no code shipped for it).** With the held-back vocabulary added
(operating income, prefix-free and non-GAAP diluted EPS), the same corpus yields 34 new ranges:
- 15 now read a period through the opener: EPAM's and TJX's GAAP diluted EPS.
- 19 still land on the `next-fy` default: AMZN and CNXC operating income, NCNO non-GAAP operating
  income, CNXC and UBER non-GAAP EPS. These are the bullet-header shape the row describes.

The opener lifts part of row 30's blocker, not all of it. The vocabulary stays held.

**BOUNDARY.**
- **Corpus:** the 118 `primary_source.releases` EX-99.1 exhibits cited by the 27
  `data/dossiers/*/dossier.json` at `origin/main` 07665419. Read from the SEC cache on 2026-10-21;
  every exhibit URL resolves through `release_parse.exhibit_991_urls`.
- **Unit:** one `GuidanceItem` per (metric, period, low, high).
- **Forecast-error comparison:** 25 pages carry both `historical_forecast_error` and a financial
  summary. 601 year-observations of Revenue, EBIT, EBITDA and net income each match an
  actual-column label `FY<yy>`; 308 of them, on 23 names, differ from that column by >0.5%.
- **"26 of 27 pages":** the `valuation.adjusted_eps` notes on those 27 pages at 07665419.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Assembly-only fields.** `current_guide`, `adjusted_eps` and the release items are written at
  assembly, so no committed page changes in this PR except the brief's FCF row, which is re-rendered
  here (render only, no JSON). TJX and Burlington take one re-assembly after merge (operator's
  decision, 2026-10-21). Every other page picks the changes up at its next re-assembly. The stored
  forecast-error note updates through `historical_forecast_error_transform` or a re-assembly.
  The evidence label is code, live now.
- **An opener can be wrong where every sentence of its run looks forward but the range belongs
  elsewhere.**
  - Falsifier: a corpus item whose opener-read period disagrees with its own sentence. None of the
    21 added items does.
  - The 60-character look-back that runs BEFORE the opener has its own latent defect: it reads a
    previous bullet's comparison year. Burlington's Aug-2025 Q3 range reads "2024". It is a second
    range, dropped by the held-scope rule, so no item carries it; it would matter only for a first
    range.
- **The `next-fy` label stays on Burlington's newest year guide.** "This excludes any potential
  costs…" ends its opener's run, so the year guide keeps the annual default. It does not get
  "Fiscal 2026".

**REVIEW FIXES (same PR, 2026-10-21).** A review of #756 found four ways the new code could print a
wrong label. Each is pinned by a test that fails on the first cut and passes now:
- **A results opener labelled a guide.** The opener's sentence passed the "looks forward" check on
  nouns: "…above the high end of the Company's guidance", "better than expected", "exceeded its
  outlook". The next sentence's guide was labelled **Q2 2027**, a closed quarter. Fix: the opener's
  own sentence now needs a forward VERB. That covers the act of guiding in the present tense
  ("is raising its … outlook", "has updated its … guidance"), but not a past-tense result.
- **A quarter opener labelled a year or a half.** The scope words read only "full year", "fiscal
  year" and "annual". So "For the remainder of the year, … $4.05 to $4.15" under a Q3 opener read
  **Q3 2026**. Fix: "the year" (but not "the year-ago" quarter), a half, and twelve months now
  count as the other scope. A year run now also refuses "fourth-quarter" and "Q4".
- **The opener must start a word.** Before, "LinkedIn 2026," read as "In 2026,".
- **`adjusted_eps`.** Three changes:
  - It reads every exhibit of the newest filing. Before, a guide-less sibling made the field
    UNKNOWN.
  - A level range stated in % is not a per-share figure, so no P/E is struck on it.
  - The note says "newest EX-99.1 release", not "newest results release". The list holds every
    2.02/8.01 exhibit, and PARR's newest (filed 2026-08-25) is an asset-sale announcement.
- **`current_guide`'s newer-release mark** now counts filings, not exhibits.

Corpus, same boundary as above (118 cited EX-99.1s, cached texts): the fixed parser gives 100
items, identical to the first cut (0 added, 0 removed). Row 30's probe is unchanged at 34 new / 19
default / 15 read. Of the 118 openers the corpus holds, 49 pass the run's forward check, and all
49 also pass the new verb check. So these fixes are PROTECTIVE: no live item moves, and the pins
are synthetic.

**STILL OPEN, NOT FIXED HERE.**
- `adjusted_eps` and `current_guide` cannot tell a results release from an 8.01 announcement, since
  `ReleaseExtract` carries no item codes. A non-results 8-K filed after results will make
  `adjusted_eps` UNKNOWN until the next results release. Its note names the release it read.
- The stored forecast-error `eligibility_note` carries the new sentence on 0 of 25 committed
  pages. It lands on the next `historical_forecast_error_transform` or re-assembly, as stated above.
