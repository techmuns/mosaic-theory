## Summary

A new, isolated package **`vinci/theme_intelligence/`**: a research discovery and prioritisation tool. It:
- reads research from **six publisher channels** (four automatic, two manual-first; Bank of America and Nomura retired) and from documents the operator supplies;
- extracts source-anchored evidence, named companies and risks;
- keeps a persistent, versioned registry of theses;
- writes a weekly dashboard of nine-section **Living Thesis Cards**.

**"RESEARCH NOW" means allocate analyst attention — never buy.** The package stays off the fund's decision path:
- no fund module imports it;
- it imports only `vinci.config`, the existing LLM client and the HTTP cache (AST-pinned);
- it has its own SQLite registry;
- it has no buy, sell, target or weight field;
- its priority rules read no prices, returns or outcomes.

**This update adds re-analysis — articles already held, analysed again under the current taxonomy, the theses they alone built retired as history — and splits the pilot's merged Alzheimer thesis with it; the pilot budget is $25.** Before it: enrichment in the weekly scan, Emerson, healthcare's sub-categories, the enrichment step and the Caffeine re-read, "Who is exposed" by direction and two wrong tickers fixed, the reading page's tabs as plain lists, a collapsible menu and no side panels, Goldman Sachs's Markets page, five Morgan Stanley articles, dates read from the page, Citi's links followed, SemiAnalysis preview-only, a Morgan Stanley article and the publishing decision, the three uploads analysed and Nomura retired, a saved paywalled preview recorded as a preview and plain Sources / Articles / Uploads, the readability pass, the approved research desk, the review-safety fix, and — before merge — the runner fix, one theme, and the desk inside the main app. Records: `docs/records/2026-10-14-theme-intelligence-ms-batch-citi-links.md`, `…-preview-only-and-publishing.md`, `…-uploads-analysed-nomura-retired.md`, `…-columns-and-uploads.md`, `…-readability.md`, `…-research-desk.md`.

**Not merged.** The weekly schedule is off and no production state branch exists. Nothing is deployed and no automation is enabled.

---

## Re-analysis, and the Alzheimer thesis split (this update)

Record: `docs/records/2026-10-14-theme-intelligence-reanalysis-alzheimer-split.md`. Operator request 2026-10-14. Model spend $2.6315; **pilot budget raised to $25 — $17.8535 spent** (registry $15.4533 over 116 paid calls, plus $2.4002 in two scratch demo registries).

- **`reanalyse`** (`Pipeline.run_reanalyse`): articles already held, analysed again under the current taxonomy and prompts from their stored text, through the same pipeline as an upload. Each thesis named to RETIRE must hold evidence from the listed articles only — else nothing is done. A retired thesis is archived with a `RETIRED` event, its key tagged with the run; its history stays, and the engine never matches, updates or reactivates it again (a new thesis on its former key gets a new id). Records whose content id is already stored are kept as first written. New theses are enriched.
- **The split** (`R-20261014T110419Z-reanalyse`): the three healthcare articles re-analysed; the four `healthcare` theses they alone built retired. **The Alzheimer thesis (pharma · neurology) now holds its own article's evidence only — and is WATCH, not Research Now**: its Research Now had rested on a catalyst from the conference article, another economic story. Cash pay, AI tools, services utilization, policy, China biotech and gene editing are each their own thesis. Enrichment: Alzheimer's → Eli Lilly, Biogen, Lantheus (+ Eisai, not SEC-verified).
- **Caught on the real run, fixed:** the desk first read "23 active · 0 archived" (the retired theses listed active, one at Research Now) — status readers knew only `ARCHIVED`; `RETIRED` now archives everywhere → 19 active · 4 archived.

| check | result |
|---|---|
| real run | `R-20261014T110419Z-reanalyse` SUCCEEDED; QA 18/20 — the two failures (an open paragraph, a missing byline) are on these articles' original runs too |
| pins | split into neurology and direct-to-consumer theses, each from its own article; the retired thesis untouched, a hypothesis on its key → new id; stored claim kept; archived on every surface; NEGATIVE: never retire a thesis with evidence from an article not re-analysed |
| mutants | 7 of 7 killed |
| gate | ruff clean · `mypy --strict vinci` clean · offline suite 5,204 passed, 513 skipped, 0 failed |

| brief item | disposition | note |
|---|---|---|
| build the re-analysis path | SHIPPED | `reanalyse` |
| split the Alzheimer thesis | SHIPPED | now WATCH on its own evidence — the Research Now was borrowed |
| increase the pilot budget to $25 | SHIPPED | recorded in STATE; $17.8535 spent |

---

## Enrichment in the weekly scan; Emerson; healthcare's sub-categories

Record: `docs/records/2026-10-14-theme-intelligence-weekly-enrichment-healthcare.md`. Operator decisions 2026-10-14. Model spend $2.4002 (two scratch demo registries, outside the pilot ledger); **pilot $15.2220 of $18** counting them.

- **Weekly enrichment** — `scan` (what both weekly wrappers call) now ends with the enrichment step over every active thesis whose current version has no set, inside the scan's own run and bill; a budget refusal or missing model is a run warning, never a failed scan; `scan --no-enrich` opts out. About $0.03 per thesis.
- **Emerson** — a software description is compatible with an industrial or electrical-equipment issuer (industrial automation is sold as software; Emerson is still filed under SIC 3600). Its enrichment proposal now resolves to EMR. Corpus: 4,793 stored source mentions over 146 local registries, old vs new resolver — **0 changed**.
- **Healthcare** — four children (pharma & biotech; life-science tools; medtech & diagnostics; health services & payers). A real run showed children alone still let a "$26bn biopharma cash-pay" hypothesis key onto the Alzheimer thesis (12 items), so pharma got **segments** (neurology; obesity & metabolic; oncology; direct-to-consumer / cash-pay), read from the hypothesis's own words, never the model's choice. Re-run: **the Alzheimer thesis holds 8 items, all from its article; the cash-pay thesis 13, all from the consumerism article**; AI tools under life-science tools; consumer choice under health services & payers.
- **Not done:** the pilot's four `healthcare` theses keep their keys (added, never renamed), so TH-BF20FBC464 stays merged — splitting it needs its three articles analysed again (~$2–2.5 against $2.78 left) and a re-analysis path for an article already held, which does not exist. Open for the operator.

| check | result |
|---|---|
| real runs (scratch registries) | children only: `R-20261014T104013Z-ingest`, `R-20261014T104332Z-ingest` ($1.371) — partial split · children + segments: `R-20261014T104659Z-ingest`, `R-20261014T104817Z-ingest` ($1.0292) — complete split |
| corpus | Emerson's widening: 4,793 pairs, 0 changed |
| pins | scan enriches in its own run / off asks nothing; `scan` on, `--no-enrich` off; Emerson → EMR / software is not an airline; children offered and two theses / same key updates; neurology vs cash-pay two theses / second Alzheimer article updates |
| mutants | 5 of 5 killed |
| gate | ruff clean · `mypy --strict vinci` clean · offline suite 5,200 passed, 513 skipped, 0 failed |

| brief item | disposition | note |
|---|---|---|
| add enrichment to the weekly run | SHIPPED | inside `scan`; `--no-enrich` opts out |
| build healthcare sub-categories | SHIPPED | four children + pharma segments; proven in a real run |
| — split the pilot's existing merged thesis | SKIPPED | needs a re-analysis path and ~$2–2.5 of $2.78 — the operator's call |
| Emerson is a software/automation company | SHIPPED | identity table; 0 source resolutions changed |
| a wrong cost prediction | — | expected the second demo at ~$0, it cost $1.0292 (registry context and review ids changed) — recorded |

---

## The enrichment step, and the Caffeine article re-read

Record: `docs/records/2026-10-14-theme-intelligence-enrichment.md`. Operator request 2026-10-14: "yes re-analyse Caffeine, and build the enrichment step". **Preview — awaiting approval.** Model spend $1.2021; pilot $12.8218 of $18 (87 paid calls).

- **Caffeine re-read** (`ingest-file --reread`, $0.7336): the new version reads "61%" where the old read "666111%%%" — 36 figures, **0 open** (was 7 garbled); the earlier version and its analysis are kept. Review's open items 21 → 14.
- **Enrichment** (`enrich.py`, `python -m vinci.theme_intelligence enrich`): for each thesis the model proposes the US-listed companies its OWN steps to earnings reach — the card's lines only, never the article's text — each with the step, benefit or hurt, how, and what the company does.
  - Checked: the step must be one of the card's; a company the source names is never proposed again; at most four per side; no call for a thesis without a step.
  - Every name through the **same SEC identity and point-in-time checks** as a source-named company (identity reads the stated business only). An unverified ticker is never shown as one: "not verified by the SEC", or "the US line of a foreign filer".
  - Stored apart (append-only table `enrichments`, schema v5) — never in the sealed thesis version, **never read by a priority rule** (pinned).
  - Shown boxed as **our hypothesis** under "Who is exposed", and in the card's section 05 (HTML, Markdown, JSON).
- **Real pass** (15 theses, $0.4685): 72 proposals (51 benefit, 21 hurt; 19 set aside — over the cap or proposed twice). After the fixes below, re-checked at $0 from the cache: **55 with a verified US listing, 11 foreign filers' US lines, 6 unverified**, each with its reason. E.g. HBM pricing → Micron, SK hynix, Applied Materials, Lam Research benefit, NVIDIA and AMD hurt; Alzheimer's → Eli Lilly, Biogen; energy drinks → Monster, Celsius.
- **Fixed after reading every proposal of the first pass:** the identity check read the mechanism's words (a drug "pipeline" → oil and gas, refusing Merck); foreign filers' US lines said so; a refusal's reason always shown; a ticker listed once.

| check | result |
|---|---|
| real runs | re-read `R-20261014T095734Z-ingest` SUCCEEDED; enrich `R-20261014T100846Z-enrich` SUCCEEDED; re-check `R-20261014T101431Z-enrich` $0 |
| pins | kept / resolved / rendered; set aside (named by the source, no such step); no article text sent; never in the source lists or the stock-exposure table; no new version, same action, skip and `--refresh`; no call without a step; append-only; identity on Merck's real SEC record (pharma → MRK, "oil pipeline operator" refused) |
| mutants | 8 of 8 killed |
| live preview | the HBM, Alzheimer and energy-drink pages and the HBM card read; Caffeine's garbled items gone from every screen |
| gate | ruff clean · `mypy --strict vinci` clean · offline suite 5,192 passed, 513 skipped, 0 failed |

| brief item | disposition | note |
|---|---|---|
| re-analyse Caffeine | SHIPPED | $0.7336; 0 open figures |
| build the enrichment step | SHIPPED | on demand (`enrich`); adding it to the weekly run is your call |
| — Emerson Electric refused identity | SKIPPED | the industry table does not pair "software" with electrical equipment; widening it changes source-named resolution — reported |

---

## Who is exposed, two wrong tickers, the thesis page, the four audit findings

Record: `docs/records/2026-10-14-theme-intelligence-exposure-and-thesis-page.md`. Operator request 2026-10-14. **Preview — awaiting approval.** $0.

**Diagnosis** (pilot registry copy at `R-20261014T070200Z-ingest`):
- "Who is exposed" showed **neither beneficiaries nor adversaries**: names only, the direction dropped — and the Alzheimer thesis's one listed name was **Morgan Stanley, the publisher**.
- The sources name almost no companies: 13 articles, 109 mentions, **0 beneficiaries**, 2 harmed (both private). **0 of 15 theses name a US-listed exposure**; 12 of 15 name sectors (25 benefit, 3 hurt). A recall sweep of the text found no company the extractor missed.
- The priority rules were never misled (they count exposure roles only); three display surfaces did not filter.
- **Two wrong tickers**, both from a bare name-prefix match: "Citi" (hint C) → Citi Trends (CTRN); "Cognition" (the private AI lab) → Cognition Therapeutics (CGTX). Every hint-verified match (13) is right.
- The Alzheimer thesis absorbed two other healthcare articles: **healthcare has no sub-nodes**, so `healthcare|demand_volume_shift|positive|US` takes any rising-demand healthcare piece.
- Proposing companies a theme implies (an "enrichment" list, labelled as our hypothesis) is designed in the schema but never built.

**Fixed:**
- **Who is exposed** — *Could benefit* / *Could be hurt* / *Named, direction not stated*, companies and sectors together, each company with its ticker or why it has none; the publisher, data sources and context counted apart; one split (`exposures_of`) for the desk, the card's exposure table and the weekly report.
- **Resolver** — a valid SEC hint naming one issuer blocks a prefix match to another business (one corporate family stays one); a company classed private needs the registrant's exact name.
- **Thesis page** — a decision order (thesis → why / next → who is exposed / what could go wrong → figures → mechanism / what changed); figures the thesis cites first; "checks passed", "a recent mispricing", "newest evidence published …"; since when the action stands; a root-node "related" link folded with the area; "$413 per year"; a figure stated twice is one line.
- **The four audit findings** — the weekly report's Sources in words (one shared helper with the desk; the raw reasons stay in Operations & audit); the card's "At a glance" folded away and out of the print; " | Morgan Stanley" dropped from titles (import and every screen); overprinted PDF glyphs read once ("666111%%%" → "61%").

| check | result |
|---|---|
| corpus — reader | 83 real PDFs, with and without the change: 6 changed, all corrections (Caffeine ×3, VRSK, ServiceNow footers, an asset-class note); 77 unchanged |
| corpus — resolver | 4,790 (registry, mention) pairs over 146 local registries, old vs new, offline: 15 changed, all corrections (Citi→CTRN 1, Cognition→CGTX 13, xAI 1); listed-equity 914 → 900, no correct listing lost |
| pins | exposure end to end (Micron benefits, Microsoft hurt, FactSet the data source in no group — desk, card, weekly report); thesis-cited figure first; stated-twice merge (another year apart); unit and title; root-node fold (a shared source stays listed); report Sources in words (raw kept in Operations); glance folded / not printed; resolver Citi / Cognition / Entergy; glyphs; importer title |
| mutants | 15 of 15 killed |
| live preview | TH-BF20FBC464, TH-188B31F187, TH-38CA111885 read section by section and whole; before / after from the same registry |
| gate | ruff clean · `mypy --strict vinci` clean · offline suite 5,185 passed, 512 skipped, 0 failed |

| brief item | disposition | note |
|---|---|---|
| "Who is exposed": beneficiaries or adversaries? | SHIPPED | it showed neither; now grouped by direction |
| right public company names / tickers per theme? | PARTIAL | diagnosed; two wrong tickers fixed; the sources name almost no companies, and proposing the companies a theme implies (enrichment) is not built — an operator decision (a new, labelled model step) |
| re-read the two thesis pages, each section and whole | SHIPPED | order, figures, wording, related, Evidence repeats |
| audit 1 — weekly report raw output | SHIPPED | |
| audit 2 — card "At a glance" | SHIPPED | folded away, not printed |
| audit 3 — " \| Morgan Stanley" titles | SHIPPED | stored titles cleaned on display |
| audit 4 — "666111%" | PARTIAL | the reader is fixed; the stored Caffeine article shows the old text until re-read (~$0.68, the operator's call) |
| healthcare thesis drift | SKIPPED | reported: a taxonomy change re-keys theses — decision path, operator's call |

---

## The reading page's tabs as plain lists, and the same audit across the screens

Record: `docs/records/2026-10-14-theme-intelligence-tabs-audit.md`. Operator request 2026-10-14. **Preview — awaiting approval.** Render-time only; $0; nothing stored changed.

- **Evidence:** three lists in place of a five-column table: **against the thesis first**, then supporting figures by article (one fold each), then context. Each item is one line (figure, what it measures, period, source) that opens to the source's words; "Observed" and "key evidence" are no longer repeated on every row. A summary line counts them ("54 cited items from 2 sources · 38 supporting · 9 against · 7 context").
- **History** says "Version 2"; **Sources** counts what each article gave ("39 cited, 4 against"); **Full record** prints its section numbers once; **Related theses** names each thesis once.
- **The card:** line labels are small lowercase tags, ⟨…⟩ system notes muted; words unchanged.
- **Articles:** an article's open items are a full-width row under it (they were squeezed into the Follow-up column), filtered and capped with it.
- **Review:** resolved findings in three lines (the line, what resolved it, the thesis); completeness items grouped by article ("21 in 6 articles").
- **Found, reported, not fixed:** the weekly report's raw diagnostics ("BLOCKED UNKNOWN … — — — 0 / 0", "RemoteProtocolError — FAIL CLOSED", "value=50.0 value_text=…"); the card's "At a glance" repeating its sections (by design — the operator's call); the " | Morgan Stanley" title suffix; the Caffeine PDF's tripled chart labels ("666111%" is 61%), correctly held by the number check but unreadable as printed.

| check | result |
|---|---|
| TH-38CA111885 (pilot registry at `R-20261014T070200Z-ingest`) | 9 against, then 29 + 9 supporting under two articles, then 7 context; Sources 15 / 5 and 39 / 4 sum to 54 / 9; one related entry |
| live preview | Articles filtered by publisher: each items row shown or hidden with its article, 0 mismatched; no page overflow at 390 px on the four tabs, Articles or Review, folds open |
| pins | no table in Evidence, quotes open from their line; against first and counted; related unique; no double numbering; items row under its article; completeness grouped — 6 of 6 mutants killed |
| existing pin | the long-list pin counts entries, not the new items rows |
| gate | ruff clean · `mypy --strict vinci` clean · offline suite 5,173 passed, 512 skipped, 0 failed |

| brief item | disposition | note |
|---|---|---|
| Evidence / History / Sources / Full record readable | SHIPPED | Evidence as three lists; the other three tabs tightened |
| similar sections on other screens (full audit) | SHIPPED | Articles' items, Review's resolved and completeness, the card's labels, Related |
| the weekly report's raw diagnostics | SKIPPED | found by the audit; a separate change to the weekly report — reported for the operator's call |
| show the preview | SHIPPED | local preview; stopping for approval |

---

## More room for content: a collapsible menu, no side panels

Record: `docs/records/2026-10-14-theme-intelligence-layout-room.md`. Operator request 2026-10-14. **Preview — awaiting approval.**

- **The app's menu** is slimmer (236 → 212 px) and **collapses** to a 52 px strip with a button beside the theme switch; remembered, applied before first paint. App-wide. On a phone, collapsed, it is just the brand row.
- **This week:** the "Needs your attention" panel is gone (it repeated the tiles); what the tiles do not say is one line of links under them; the content takes the full width.
- **Uploads:** the weekly steps are one closed fold above the list; the list takes the full width.

| check | result |
|---|---|
| This week at 1280 px | 4,284 → 3,508 px tall (menu open), 3,468 (collapsed) |
| layout | no overflow at 1280 / 390 px, open and collapsed; the brand fits one line |
| live preview | the collapse button collapses, remembers and restores |
| pin | no side panels; the heads-up line and tiles link right; a vacuous selector in an older test fixed |
| gate | ruff clean · `mypy --strict vinci` clean · `node --check` · offline suite 5,168 passed, 512 skipped, 0 failed |

| brief item | disposition | note |
|---|---|---|
| menu smaller or collapsible | SHIPPED | both: slimmer, and collapsible |
| remove the repetitive "Needs your attention", fix the squeeze on other screens | SHIPPED | This week and Uploads were the two screens with side panels |
| show the preview | SHIPPED | local preview; stopping for approval |

---

## Goldman Sachs's Markets page, Bank of America stays retired

Record: `docs/records/2026-10-14-theme-intelligence-gs-markets-page.md`. Operator decisions 2026-10-14.

- **Goldman Sachs Markets** is a second place to look: a channel setting `research_pages` (pages for a person to check — shown on Uploads and Sources, never fetched). Goldman's Research page stays the main one.
- **Bank of America stays retired.**

| check | result |
|---|---|
| pins | Goldman's two pages on Sources and Uploads, Morgan Stanley's one (negative); config — 2 of 2 mutants killed |
| live local preview | Goldman's request links both pages; no console errors |
| gate | ruff clean · `mypy --strict vinci` clean · offline suite 5,165 passed, 512 skipped, 0 failed |

| brief item | disposition | note |
|---|---|---|
| add Goldman's Markets page as a second "where to look" | SHIPPED | `research_pages` |
| bring Bank of America back | SKIPPED | the operator's answer: no — stays retired |
| run preview | SHIPPED | local preview of the app with the pilot published (not committed) |

---

## Five Morgan Stanley articles, dates read from the page, Citi's links followed

Record: `docs/records/2026-10-14-theme-intelligence-ms-batch-citi-links.md`.

- **Five Morgan Stanley September articles analysed** (operator-supplied PDFs of public pages): $3.7318, every date read from the page. New theses include one **Research Now** ("Alzheimer's innovation opens a $70bn drug market with broader healthcare value") and four Watch. Pilot spend $11.6196 of $18 (69 calls).
- **A printed date in a layout box is read** (`documents.py`): Morgan Stanley's saved pages put headline and date in boxes the PDF reader takes for a table, and all six MS PDFs had gone undated.
- **Citi's "Read the full article here." is followed** (`parse._report_links`): the anchor's full stop made the rule miss it, so "Money" read as a teaser and its PDF was asked of the operator although Citi's linked reports are fetched automatically. A teaser that links its report is no longer counted as one to supply under `"fetch"` (`health.py`).
- **A source's request leaves Uploads once every listed article is supplied** (`desk.upload_items`): the reason "New research from Citi" stayed pending.

| check | result |
|---|---|
| real runs | 5 ingest runs SUCCEEDED, each dated from the document |
| corpus before synthetic | dates over 296 real files: 7 changed, exactly the six MS PDFs · links over 62 cached pages: 1 changed, Citi "Money" |
| rendered desk | Uploads asks only for Morgan Stanley's and Goldman Sachs's standing requests; 13 articles, 15 theses; 0 broken links; no overflow at 1440 / 390 px |
| pins | boxed date (new synthetic fixture), "here." link, linking teaser under fetch / request, request leaves once supplied — 4 of 4 mutants killed |
| gate | ruff clean · `mypy --strict vinci` clean · offline suite 5,163 passed, 512 skipped, 0 failed |

| brief item | disposition | note |
|---|---|---|
| GS Research vs GS Markets | SHIPPED (answered) | Research for themes, Markets for weekly freshness; adding Markets as a second link awaits the operator |
| analyse five Morgan Stanley articles | SHIPPED | $3.7318; one Research Now |
| Citi articles from Must C via each PDF link | SHIPPED | already the scan's route; the "here." miss fixed |
| audit the shortlisted source links | SHIPPED (answered) | six match; Bank of America retired 2026-10-11 by decision — reinstating awaits the operator |
| why "New research from Citi" stayed pending | SHIPPED | fixed: a request leaves once every listed article is supplied |

---

## SemiAnalysis preview-only, a Morgan Stanley article, publishing decided

Record: `docs/records/2026-10-13-theme-intelligence-preview-only-and-publishing.md`. Operator decisions 2026-10-13.

- **SemiAnalysis is preview-only** (no subscription). New channel setting `paywalled_posts` (`"request"` default, `"preview_only"` for SemiAnalysis). A paid post's free preview is analysed and labelled a preview (still PARTIAL), never requested:
  - the health check stays DEGRADED and says so, but asks for nothing;
  - the desk's Uploads and the weekly report's intake no longer list the previews, nor the channel request stored before the decision (`health.asks_only_for_previews`, read from the stored test results);
  - Articles says "Preview only — by decision", and Sources says so on SemiAnalysis's row.
  - It covers paid posts only: a page linking a fuller report, or a teaser, is still requested.
- **Morgan Stanley "China's Next Industrial Revolution: The Industry 5.0 Opportunity"** (supplied by the operator; the scan cannot read Morgan Stanley — its site drops our honest research user agent, robots.txt included, and the channel is manual-first). Analysed for **$0.8075**: 32/32 figures, two new theses (both SKIP). Pilot spend $7.8878 of $18.
- **Publishing decided:** publish the current snapshot once this PR is merged; weekly publishing stays manual for now (guide updated).
- **Goldman Sachs link checked, not changed:** it opens in a browser in every form; the earlier chat reply had written it without `https://`.

| check | result |
|---|---|
| real run | Morgan Stanley ingest SUCCEEDED, $0.8075, 5 model calls |
| rendered desk (copy of the updated registry) | no SemiAnalysis request on Uploads; "Preview only — by decision" on Articles; 0 broken links, 0 default-view ids; no overflow at 1440 / 390 px |
| pins | health: the same paywalled site asks under "request", not under "preview_only"; a teaser still asks · desk + report: previews never requested, a linking page and a request channel's preview still are · config · mutants 7 of 7 killed |
| gate | ruff clean · `mypy --strict vinci` clean · offline suite 5,158 passed, 512 skipped, 0 failed |

| brief item | disposition | note |
|---|---|---|
| publish the current snapshot after merge, weekly publishing manual | SHIPPED (decision recorded) | the publish itself runs once the PR is merged |
| Goldman Sachs link broken | SHIPPED (checked) | the page opens in every form; no change needed |
| SemiAnalysis: stay on previews, no subscription | SHIPPED | `paywalled_posts = "preview_only"` |
| the Morgan Stanley article | SHIPPED | analysed, two theses; why the scan cannot fetch it is in the record |

---

## The three uploads analysed, and Nomura retired

Record: `docs/records/2026-10-13-theme-intelligence-uploads-analysed-nomura-retired.md`. Operator decisions 2026-10-13.

**Analysed into the pilot registry** (`--llm-permitted` on the operator's instruction — these PDF downloads are the publishers' official route; backup taken first):

| document | cost | imported as | result |
|---|---|---|---|
| Citi — "Money: The Evolution to Digital" (dated 2024-10-30, as Citi's page states) | $0.3468 | new article, read in full | 14 figures, 10 captured; no thesis proposed |
| SemiAnalysis — "Are Open Models Catching Up?" | $0.689 | new article, **preview** | new thesis "Open models catch up to frontier faster each era, risking model-layer commoditization" (WATCH) |
| SemiAnalysis — "Beijing Will Not Pace the Frontier" | $1.71 | new version of the article held, **preview** | new thesis "China's frontier-safety governance is decided by leadership…" (SKIP); evidence against the open-models thesis |

$2.7458 in all; the pilot has now spent $7.0803 of $18 (36 calls). Both SemiAnalysis PDFs end with the subscriber notice, so their full posts stay requested on Uploads.

**Nomura retired** (its full reports sit on a client portal with no public sign-up). As Bank of America: a named `[[retired]]` channel (hosts `nomuraconnects.com`, `nomuranow.com`), its adapter removed, nothing discovered, checked, requested or imported; its two articles and its thesis stay as history. **Six active publishers** now. The desk now applies the weekly report's retired-channel rule: Uploads never asks for a retired channel's material, and Articles says "Not requested — Nomura retired 13 Oct 2026" instead of "Supply the full report".

| check | result |
|---|---|
| real runs | 3 ingest runs SUCCEEDED; costs as above |
| rendered desk (copy of the updated registry) | no Nomura on Uploads or Sources; "Money" / "Open Models" read "supplied and analysed"; 0 broken links, 0 default-view ids over 24 pages; no overflow at 1440 / 390 px |
| pins | six channels; Nomura refused by source and host; a retired preview never requested (desk Uploads + Articles), an active one still is; mutants 2 of 2 killed |
| gate | ruff clean · `mypy --strict vinci` clean · offline suite 5,150 passed, 512 skipped, 0 failed |

**Open decision (yours):** both SemiAnalysis requests can be met only with a paid subscription — stop requesting SemiAnalysis full posts (keeping it as a source)?

| brief item | disposition | note |
|---|---|---|
| analyse Citi and the two SemiAnalysis previews | SHIPPED | $2.7458; two new theses; both SemiAnalysis documents recorded as previews |
| stop requesting Nomura's portal-only reports | SHIPPED | desk and weekly report request nothing from a retired channel |
| remove Nomura from the sources list altogether | SHIPPED | retired as BofA was: history kept, nothing new accepted |

---

## Columns and uploads: plain Sources / Articles / Uploads, and a saved preview stays a preview

Record: `docs/records/2026-10-13-theme-intelligence-columns-and-uploads.md`. $0, no model call, nothing written to the pilot registry.

- **Importer defect (found dry-running the operator's three uploads).** A paywalled page saved as PDF without a paid sign-in ends with the subscriber notice ("This post is for paid subscribers…") and is still the preview. The web scan checked for it; the importer did not. One SemiAnalysis PDF would have been recorded **read in full**. Now the notice makes a supplied document PARTIAL and Uploads keeps asking for the full post (one marker definition, `parse.paywall_marker`).
- **Sources:** one plain line per channel from its check's structured test results, the check's own sentences in a fold, the history strip only from two stored checks, the newest article on the site or held, the licence rule said once, research-page links for Morgan Stanley and Goldman Sachs.
- **Articles:** follow-up is one action linked to Uploads; open items fold, with the figure count inside; fixed column widths.
- **Uploads:** requested articles as linked titles (`health.split_affected`, the one reader of the "url — title" lines), each saying what is held of it ("supplied — held until you confirm its licence"); channels that list nothing show "Where to look: <research page>"; weekly commands wrap after the CLI name.
- **Phone width:** stacked number cells carry their label; the Themes search box spans the width.

**The three PDFs, dry run only** (a scratch copy of the pilot registry, `--cache-only`, no licence statement):

| PDF | what it is | dry-run result | estimate (list price) |
|---|---|---|---|
| SemiAnalysis — "Beijing Will Not Pace the Frontier" | ends with the subscriber notice: the same preview already held (48 of its 50 paragraphs of ≥12 words already held) | Match uncertain | $1–8 |
| SemiAnalysis — "Are Open Models Catching Up?" | ends with the subscriber notice: a preview | HELD, now PARTIAL | $1–7 |
| Citi — "Money: The Evolution to Digital" | complete document (7 pages) | HELD (licence) | $1–7 |

| check | result |
|---|---|
| importer, real files | "Open Models" FULL → PARTIAL; Citi stays FULL |
| corpus before synthetic | the marker matches none of the 10 documents stored locally (incl. Citi ETF, Gridlock, LatAm) and exactly the 2 SemiAnalysis PDFs |
| layout | no horizontal overflow — Sources, Articles, Uploads at 1440 and 390 px, real pilot + synthetic 12-week |
| standalone pages | 0 broken links, 0 default-view ids/codes over 386 pages |
| pins | 1 ingestion (positive + negative) + 4 desk; 8 of 8 mutants killed |
| gate | ruff clean · `mypy --strict vinci` clean · offline suite 5,146 passed, 512 skipped, 0 failed |

**Open decisions (yours):** analyse Citi's "Money" (`--llm-permitted`, $1–7 list); import the two SemiAnalysis previews or not; stop requesting Nomura's portal-only reports (a pipeline policy, not built).

| brief item | disposition | note |
|---|---|---|
| crammed / illegible / non-required content — Sources | SHIPPED | plain line, fold, no repeated intake |
| … and the other tabs | SHIPPED | Articles follow-up, Uploads lines, phone labels; This week / Themes / Review / reading page checked, no crammed column left |
| upload the three requested articles | STOPPED | dry-run only: analysis needs your licence statement and spend approval; both SemiAnalysis PDFs are previews |
| is this the right weekly process? | SHIPPED | answered to the operator; the guide now says to save paid posts while signed in |
| Nomura portal has no public sign-up | SKIPPED | stopping its requests is a pipeline policy — your decision |
| no link on Goldman Sachs / Morgan Stanley requests | SHIPPED | their research pages linked on Uploads and Sources |

---

## Readability pass: the desk's screens re-laid for reading

Record: `docs/records/2026-10-13-theme-intelligence-readability.md`. $0, no model call, render-time only: no record, stored card or research action changes.

Each screen now answers its one question first; everything else is one fold away.
- **This week:** a sentence and five counts; the week's changes as cards grouped by area (action, events, findings, title, mechanism, source, open WATCH conditions as one badge); the articles as a list; *Needs your attention* beside them; every active thesis one fold below.
- **Themes:** one table per area, open only if it changed this week; columns line up across areas; no area label repeated per row.
- **Articles:** older / newer week navigation; title, publisher and route in one column; open items fold.
- **Review:** findings grouped under their thesis; each finding is three short lines (the line, the review's words, one meta row).
- **Uploads:** a list per group, not a wide table (ten shown, the rest one click away); four short weekly steps beside it, the rules folded.
- **Sources:** status now with its reason, health history, freshness, intake.
- **Reading page:** the thesis, then three side-by-side pairs (why / what next · how it reaches fundamentals / what could prove it wrong · what changed / who is exposed); long lists fold.
- **Said once, engine detail hidden:** a figure whose metric already names its scope reads once (from the claim's structured fields; the Full record keeps the sealed label); a finding's "(scope: …)" note and a source's registry id are in the audit view; no blank publisher or lone "—".

| check | result |
|---|---|
| page height, in the app at 1440 px (synthetic 12-week registry: 229 articles, 111 theses) | This week 4,472 → 3,214 px · Themes 8,347 → 4,054 · Review 4,761 → 4,218 · Uploads 14,501 → 4,132 |
| layout | no horizontal overflow on 7 routes at 1440 and 390 px, synthetic and real pilot; dark mode on 3 routes; a 390 px Uploads overflow found and fixed |
| standalone pages | 0 broken links, 0 default-view ids/codes over 368 pages; every reading page reaches all nine card sections |
| new pins | figure label (positive + negative); source ids audit-only on Sources and Uploads; a finding's scope note audit-only (negative too) — 4 of 4 mutants killed |
| gate | ruff clean · `mypy --strict vinci` clean · `node --check` on the changed JS · offline suite 5,141 passed, 512 skipped, 0 failed |

**Accepted:** Themes on a phone stays long for a large registry (13,171 px for 96 active synthetic theses; search, filters and closed areas are the way through). Uploads' list of articles to supply prints the web address before the title, because that line is built upstream as one string and splitting it would mean parsing a rendered string.

| brief item | disposition | note |
|---|---|---|
| go through the six screens: readability and hierarchy | SHIPPED | each screen re-laid; before/after screenshots |
| internal screens (thesis reading page, findings) | SHIPPED | reading page and every finding item |
| remove verbose / non-useful information | SHIPPED | repeated labels, scope notes, source ids, empty cells |
| scalability | SHIPPED | checked on the 12-week, 111-thesis registry; phone Themes length accepted |
| easy navigation | SHIPPED | week navigation, folds, open-when-changed areas |
| the Full record (nine-section card) and the weekly report | SKIPPED | not re-laid here: redesigned 2026-10-12 and kept as the complete record; say if you want them in this pass |
| preview with screenshots, stop for approval | SHIPPED | local only; nothing published or committed to `frontend/theme-intelligence/` |

---

## Before merge: the runner's blind spot, one theme, the desk inside the main app

Record: `docs/records/2026-10-13-theme-intelligence-app-integration.md`. $0, no model call, nothing written to the registry.

1. **"Not checkable on this machine."** The weekly runner rebuilds the registry from the state branch's export, which carries no article text, so it could not read business groups and printed "none" / "the source names no company or sector" — false on every weekly readout. A paragraph whose text is not held is now *not checkable on this machine* — card (HTML, Markdown, JSON), weekly report and desk. Locally nothing changes. Verified by simulating the runner on a copy of the real pilot (export → re-import → render): the 4 affected pages now say "not checkable".
2. **One theme (option A).** The desk, the Living Thesis Card and the weekly report share one palette (light and dark), one type and one nav bar — the desk's six screens — with the audit switch. Research Now is one colour everywhere; the card's links lead to the desk; the weekly report keeps its sections as a second row. Every page is `noindex`.
3. **Inside the main app (option C).** `python -m vinci.theme_intelligence publish` writes a run's desk into `frontend/theme-intelligence/`; the app (Nostra Vinci) shows it as a **Theme intelligence** edge: This week · Themes · Articles · Review · Uploads · Sources as tabs, a thesis's reading page under Themes, the Full record and weekly report in a new tab. **One renderer:** the app frames the published pages (links mapped to its routes, the desk's own script, styles scoped under `.intel` on the app's tokens — light/dark follow its toggle); no screen is re-implemented. Refused, nothing written: a test-domain registry, a foreign folder, a page carrying a local path. Never published: card JSON/Markdown, report exports, validation log, run manifest.
   - **Operator decision recorded** (CLAUDE.md §Security, `.gitignore`): `frontend/theme-intelligence/` is committable for the authed internal deploy — derived analysis with short source quotes, never article text; reverts to ignored if the repo/deploy goes public.
   - The py↔JS duplicate-definition guard skips `frontend/theme-intelligence/`: its `desk.js` is generated from `desk.py` byte for byte (pinned equal), not a hand-copied twin.
   - **No publication is committed here** — the app says "No theme-intelligence run is published yet" until one is (see the open decisions below).

| check | result |
|---|---|
| app, local preview (real pilot published, not committed) | every tab, filter and the thesis drill-down work; 32 new-tab links resolve; 0 console errors |
| layout | no horizontal overflow — 1440 px (5 screens), 390 px (7 screens); dark mode follows the app's toggle |
| tests | 8 publish + 1 runner-parity end to end; 8 of 8 mutants killed (7 publish guards + the runner detection) |
| gate | ruff clean · `mypy --strict vinci` clean · `node --check` on the changed JS · offline suite 5,136 passed, 512 skipped, 0 failed |

**Open decisions (yours):** (1) which run to publish first — the 12 Oct pilot now, or wait for the first weekly run; (2) whether the weekly run should publish automatically — that means committing to `main` from Actions (today it commits only to the state branch), a policy change.

| brief item | disposition | note |
|---|---|---|
| business groups: "not checkable on this machine" instead of "none" | SHIPPED | card, report, desk; runner simulated |
| option A — theme intelligence consistent with itself | SHIPPED | one palette, type, nav, audit switch, action colours, dark mode |
| option C — inside the main app, licensed quotes on the internal pages.dev | SHIPPED (code) | publish + app section; publication itself awaits your choice of run |
| preview with screenshots, stop for approval | SHIPPED | local only |

---

## Review-safety fix (2026-10-13)

Record: `docs/records/2026-10-13-theme-intelligence-review-carry.md`. $0, no model call, nothing written to the registry, no action recomputed, no UI redesign.

A version whose run recorded `REVIEW_NOT_RUN` (`--no-review`, the review budget exhausted, or no model client and no cached review) is never read as clean. Every open finding of the last reviewed version stays open:
- **same words + same cited evidence:** the finding stays on that line as UNRESOLVED REVIEW, "raised by the review of version N (date)";
- **changed words or evidence:** the line reads **NOT RE-REVIEWED**, quoting the line as the review read it;
- **line removed:** the finding is listed as removed, never resolved;
- **a line the review withheld** stays withheld;
- the carry chains across consecutive unreviewed versions.

Every such version says **Not reviewed** — card header and Markdown, the desk's Review screen and reading page — even with no earlier finding. Nothing is copied: each finding is read from the run that made it, with its original version and date. A review that **runs** stands on its own findings (the existing rule): a finding it does not raise again clears; one it raises again stays.

| check | result |
|---|---|
| `--no-review` · budget exhausted (guard sends nothing) · no client and no cache | old warning kept on the card AND on the desk's Review screen, all three |
| a changed flagged line, unreviewed | NOT RE-REVIEWED |
| a brand-new thesis the review never read | says Not reviewed (all three paths) |
| two unreviewed versions in a row | still carried from version 1 |
| a later successful review raising nothing / raising it again | cleared / kept |
| stored findings | only the original review's, unedited — no duplicate |
| mutants | 8 of 8 killed |
| real pilot desk | unchanged (no `REVIEW_NOT_RUN` in it): 0 broken links, 0 default-view ids or codes |
| gate | ruff clean · `mypy --strict vinci` clean · offline suite 5,123 passed, 512 skipped, 0 failed |

Tests: `tests/test_theme_intelligence_review_carry.py` (11 tests; the real `Pipeline._review` path, an offline fake reviewer, synthetic articles on the reserved `.test` domain). The private preview adds a labelled synthetic demo (v1 reviewed, v2 with `--no-review`).

**Accepted (recorded):** the research action of an unreviewed version stays as the engine computed it — a line an earlier review withheld shows withheld (and decision-affecting on Review), but the version is not re-held.

| brief item | disposition | note |
|---|---|---|
| 1 carry unresolved findings on unchanged, identically evidenced lines when review did not run | SHIPPED | words AND cited evidence must match |
| 2 a changed flagged line, unreviewed → Review Required / Not Re-reviewed | SHIPPED | NOT RE-REVIEWED on the line |
| 3 an unreviewed new version discloses it, even with no earlier finding | SHIPPED | card, Markdown, desk |
| 4 original finding, first-raised date, provenance, history kept; no duplicate; no silent resolution | SHIPPED | read from the original run; removed lines listed |
| 5 research action and evidence safeguards intact; a skipped review is never a successful one | SHIPPED | no recompute; label cap holds |
| 6 a genuinely successful later review resolves under the existing rules | SHIPPED | cleared when not raised again |
| tests: `--no-review`, exhausted budget, missing client/cache; card + desk; the opposite case | SHIPPED | 11 tests |
| focused regressions, full offline suite, ruff, strict mypy, GitHub CI | SHIPPED | CI read once after push |
| no paid calls, features, redesign, upload automation, merge or scheduling change | SHIPPED | |

---

## The research desk

Record: `docs/records/2026-10-13-theme-intelligence-research-desk.md`. **$0 — no model call; nothing written to the registry; no extraction, identity, priority, budget, scheduling or history change.** Not merged; the schedule stays off; no production state.

`vinci/theme_intelligence/desk.py`, written by `write_run_outputs` beside the existing outputs (the weekly report, its print record and the nine-section cards are unchanged and linked):

| screen | what it shows |
|---|---|
| **This Week** (`index.html`) | the week in one sentence; thesis changes grouped by research area (new / upgraded / downgraded / challenged / new evidence); what each article produced — zero-thesis, partial, held, failed, queued; what needs attention |
| **Themes** | every thesis, active and archived, by area (short names; keys unchanged); search, filters, sort; related theses linked, never merged |
| **Articles** | one page per week with a week selector; read in full / partial / queued / failed / blocked / held told apart, with what each produced, its completeness items and follow-up |
| **Review** | every unresolved finding on every ACTIVE thesis, whatever week raised it — decision-affecting first, then Research Now, then oldest; age, thesis, the review's words, a link to the exact card line; resolved and historical kept below; read-only |
| **Uploads** | everything to supply or clear, never dismissed by age — publisher, source id, dates, age, why, and the existing command (folded) |
| **Sources** | health now, stored health checks only, freshness, articles in the last four weeks, permitted intake; automatic and manual-first apart |
| **Reading page** (`theses/<id>.html`) | the thesis, what changed, the strongest figures (unit, period, observed/forecast, date), how it reaches fundamentals, why this action, what could prove it wrong, what to investigate next; then exposures, related theses (a shared source is flagged as the same source, not confirmation), open findings, evidence, history, sources — the Full record (all nine sections) one click away; no line printed twice |

**The Nomura horizon issue.** No conflict of record: `TH-2FFD9B58A8`'s near-term factor (yes) rests on 5 measured claims dated by the article's publication date (no measurement date stated), all within the last quarter; the "Longer term" label is the source's framing. The page now states the near-term condition **once**, met or not, with the claims and where each date comes from, and prints the framing as a description, not a test. When a factor's own claims, re-dated today, give another value, the page shows **Review required**, a timing finding joins Review, and the research action of record stands.

**An engine defect the stress test found (separate commit).** Two articles of one run that split one key into different products raised two issues with one id (`Engine._issue` left the detail out of the hash); the append-only store refused the second and that article failed. The id now includes the detail, as `verify._issue` does. Regression test fails on the unfixed engine with `StoreIntegrityError`.

### Verification (real runs)

| registry | articles | theses | desk pages | local links (broken) | default-view ids / codes | page overflow 1440 · 390 |
|---|---|---|---|---|---|---|
| **real pilot** (a copy of `pilot-2026-10-12`, latest run) | 5 (3 full, 2 preview) | 4 | 10 | 635 (0) | 0 | none (10 pages) |
| **synthetic, 6 weeks** | 110 | 62 | 73 | 6,247 (0) | 0 | none (2 pages measured) |
| **synthetic, 12 weeks** | 229 | 111 (96 active, 12 RN) | 128 | 14,622 (0) | 0 | none (7 pages measured) |

- Real pilot: 8 open findings on 3 active theses (5 decision-affecting); 7 upload items (2 full reports, 5 manual-first or degraded sources).
- 12 weeks: 38 open findings, 27 open four weeks or more — still on Review; 58 upload items; rendered in ~1.3 s.
- The synthetic registries are built through the REAL engine on the reserved `.test` domain, every article titled "[SYNTHETIC STRESS TEST]"; every desk page of such a registry says **TEST DATA**. They live in a git-ignored folder and never touch the real registry.
- **Tests:** 17 desk tests end to end + 1 engine regression test; **7 of 7 mutants killed** (capped table dropping rows, timing conflict never raised, review reading only this week, a document id linked, a preview read as full, the near-term condition listed twice, an audit id leaking).
- **Gate:** ruff (`vinci tests frontend`) clean; `mypy --strict vinci` clean; offline suite 5,111 passed, 512 skipped, 0 failed (at `3db0a3d4` plus the docs commit).

### Remaining issues (genuine, not cosmetic)

- ~~**OPEN — a new version written without the card review drops open findings.**~~ **CLOSED** by the review-safety fix below.
- **Observed:** a card's source row links an uploaded document's `urn:document:…` id as a web link (section 09). The desk prints it as text. Not changed.

### Follow-up requirements (documented, not built)

- **A. Safe one-step weekly upload command:** cache-only state pull, identity and licence checks, cost preflight, explicitly budgeted import, QA, ledger reconciliation, fast-forward-only push. No implicit paid replay.
- **B. Append-only review resolution:** version-specific findings with reviewer, time, reason, verified correction or dismissal; full history kept. Accepting a warning never makes unsupported evidence valid.

### Disposition

| brief item | disposition | note |
|---|---|---|
| 1 This Week — summary; changes by area; upgrades/downgrades/new evidence/new; what each article produced | SHIPPED | zero-thesis, partial, held, failed, queued shown |
| 1 Themes — all theses by area; search/filter/sort/archive; short area names; related theses, shared source not confirmation | SHIPPED | keys unchanged; siblings folded |
| 1 Articles — weekly history, week selector; every state told apart; theses, dates, completeness, follow-up | SHIPPED | |
| 1 Review — all active theses, any week; priority order; age, thesis, link, reason; history kept; read-only | SHIPPED | no resolution state invented |
| 1 Uploads — documents, why, dates, age, true publisher/source id; kinds told apart; exact commands; no age dismissal | SHIPPED | existing commands only |
| 1 Sources — health, availability, freshness, intake mode; stored history only; automatic vs manual-first | SHIPPED | |
| 2 Thesis reading page — seven questions; full nine-section card under Full record; no repeated prose | SHIPPED | pinned: no line twice |
| 3 Nomura horizon — stored label vs dated claims; one statement per criterion; Review Required on genuine conflict | SHIPPED | Nomura: no conflict of record |
| 4 Real pilot + labelled 6/12-week stress registries; never mixed with the real registry | SHIPPED | real registry never opened (copy) |
| 4 Verify scale, truncation, earlier findings, partials, links, unsupported content, nine sections, 1440/390, ids/codes, no spend | SHIPPED | tables above |
| 5 Follow-ups A and B documented, not built | SHIPPED | record, guide, STATE |
| 6 Focused tests, ruff, mypy, offline suite, CI | SHIPPED | CI read once after push |
| 6 Private preview with screenshots, real + stress | SHIPPED | local server; screenshots local, not committed |
| 6 No merge, no scheduling, no production state, no fund code | SHIPPED | |

---

## Earlier updates (condensed; full text: `docs/theme_intelligence/pr-body-history/`)

- **Final evidence and UX corrections; fail-safe review resolution** (`docs/records/2026-10-12-theme-intelligence-final-corrections.md`, `…-failsafe-resolution.md`): every evidence link lands (27 → 0 broken); business groups listed apart from exposures; history told from open findings; a relabel resolves a finding only when it is about the label alone (Nomura s07.2 back to open).
- **Product redesign and three research corrections** (`docs/records/2026-10-12-theme-intelligence-product-redesign.md`):
  - the J.P. Morgan bottom line was corrected by an analyst correction;
  - the Magnificent 7 price move is now price context;
  - a named index's number is no longer read as a figure;
  - the weekly page and Living Thesis Card were redesigned (first thesis 2,125 → 357 px);
  - 31/31 mutants killed.
- **Final acceptance** (`docs/records/2026-10-12-theme-intelligence-acceptance.md`): operator-confirmed authorization recorded; J.P. Morgan acceptance PASS ($0.3851); readiness READY TO MERGE; a local product preview.
- **Pilot corrections** (`docs/records/2026-10-12-theme-intelligence-pilot-corrections.md`):
  - malformed first answers are salvaged by deletion only, never re-asked;
  - a page label is not an exposure;
  - "near-term" means the next four quarters, and a window running past them gives WATCH;
  - stored theses can be re-graded with `reassess`;
  - review warnings show on the card line;
  - a stored preview is corrected to PARTIAL;
  - 31/31 mutants killed.
- **Supervised pilot** (`docs/records/2026-10-12-theme-intelligence-supervised-pilot.md`): five web articles from four publishers, and the paywall-window fix.
- **Pilot closeout · coverage and identity · analytical safeguards · targeted PDF cost reduction · state-pull ledger · seven-source corrections · hybrid ingestion · source health · review rounds 2–3 · the original build:** see the records named in `STATE.md` §2.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
















