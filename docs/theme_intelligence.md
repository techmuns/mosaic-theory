# Theme intelligence — operator guide

`vinci/theme_intelligence/` is a **research discovery and prioritisation** tool. It reads permitted
public research pages from six publisher channels (four automatic, two manual-first), extracts their source-anchored evidence, named
companies and risks, keeps a persistent, versioned registry of investment theses, and writes a
decision-first weekly briefing of nine-section **Living Thesis Cards**.

**"RESEARCH NOW" means *allocate analyst attention* — never buy.** Nothing here is on the fund's
decision path: no fund module imports this package (AST-pinned), it keeps its own database, it has
no buy / sell / target / weight field, and its priority rules are face-validity constants that read
no prices, returns or outcomes (including the unmerged #695 audit's).

## Quick start

```bash
.venv/bin/python -m vinci.theme_intelligence init
.venv/bin/python -m vinci.theme_intelligence article --url "https://privatebank.jpmorgan.com/apac/en/insights/markets-and-investing/tmt/software-shock-ais-broken-logic" --as-of 2026-02-09
.venv/bin/python -m vinci.theme_intelligence scan --days 10
.venv/bin/python -m vinci.theme_intelligence report --latest
.venv/bin/python -m vinci.theme_intelligence qa --run latest
```

| command | what it does |
|---|---|
| `scan --days N` / `scan --from D --to D` | discover the window on the five automatic channels (the two manual-first ones are health-checked only), analyse up to `--max-articles` (default 25; the rest are QUEUED and offered first next run), write the readout |
| `scan --resume RUN_ID` | continue an interrupted scan with its ORIGINAL window and as-of; nothing is processed twice |
| `article --url U --as-of D` | analyse one URL as of a date (publication-time replay: a later-published article is refused, a later-dated figure is blocked) |
| `report --latest` / `--week 2026-10-05` or `2026-W41` / `--run RUN_ID` | re-render the dashboard and every card from the registry |
| `qa --run RUN_ID\|latest` | re-check a run's stored records without any LLM (spans, figures, look-ahead, card facts, section order, hashes, triggers, coverage, render consistency) |
| `backup` · `export-state --out D` · `import-state --src D` | consistent SQLite copy · append-only JSONL export (no article text) · rebuild a fresh registry from an export |
| `sources` | print the six configured channels (and the retired ones, as history) |
| `ingest-file --path F --source S [--url U] [--llm-permitted]` | import one supplied document (PDF / HTML / Markdown / text) through the SAME pipeline — see *Manual documents* below |
| `ingest-inbox [--inbox D] [--source S]` | import every document in the private inbox; each file is filed under `processed/`, `held/`, `review/` or `rejected/` |
| `documents [--status HELD]` | list the supplied documents and their status |
| `state pull\|push\|status --remote R` | carry the ONE registry between this machine and the state branch the scheduled run uses |

Common flags: `--data-dir` (default `data/theme_intelligence`), `--cache-only` (never call the
LLM: replay cached extractions only), `--no-review` (skip the pass-2 LLM review — the card then
says the review did not run). Exit status: **0** succeeded · **2** PARTIAL (a source or article
could not be read; the readout says which) · **1** failed.

## What a run writes

`data/theme_intelligence/runs/<RUN_ID>/` (git-ignored; `runs/LATEST` names the newest):

- `dashboard.html` / `.md` / `.json` / `.csv` — the weekly decision page: run status, window, and
  a KPI strip in plain words — *Accessible sources: 5 of 5* (the automatic channels), *Blocked
  automatic channels: none*, *Manual-first sources: Morgan Stanley [automated access BLOCKED],
  Goldman Sachs [automated access BLOCKED]*, *Articles analyzed: N full · M partial*, *Research
  Now / Watch / Skip*, *New /
  upgraded / downgraded / challenged theses*, *Reported figures not yet captured: X of Y* — then
  unresolved caveats. Both thesis KPIs count the theses THIS RUN created or changed (a SKIP is
  archived at once, and still counts) and its events (a thesis new this run can also be
  challenged in it); each tile says so under its value. Then six categories in a fixed order —
  each thesis in exactly one — new, upgraded, downgraded,
  challenged, unchanged but material, archived — each always printed with its count ("showing X of
  Y" when collapsed); then a searchable archive of every thesis. Each row shows the ARTICLE date
  and the date the registry FIRST DETECTED the thesis apart ("new to the registry" never means
  "new to the market"), what changed, why the action, the exposure the source names and the next
  research step. Thesis ids, versions, change classes, claim ids and the rule trace sit behind the
  *Show evidence IDs, engine codes and the decision trace* toggle; print shows everything.
- `cards/<THESIS_ID>.html` — the COMPACT DECISION VIEW: header (action, evidence direction, record
  kind, article date vs first detected) and 01 / 02 / 06 / 08 open, 03 / 04 / 05 / 07 / 09 folded
  with a one-line summary, the same audit toggle; `.print.html` (everything open, audit included),
  `.md`, `.json` — the same nine sections in the same order, all rendered from the stored
  `ThesisVersion`.
- `report_print.html` — the dashboard plus every card that changed, fully expanded.
- `validation_log.json` — every verification issue (BLOCK / HOLD / WARN / INFO).
- `manifest.json` — window, as-of, status, runtime, fetch / LLM seconds, model and prompt versions,
  tokens, cost, per-source coverage, warnings, output list.

## How an article becomes records, and how each line is labelled

Corrected after the PR #703 review (record `docs/records/2026-10-10-theme-intelligence-review-corrections.md`).

- **Two record kinds.** An *investment thesis* argues a profit-transmission mechanism for listed
  equities. A *market-regime record* captures a market-structure condition the article measures —
  breadth, correlation, dispersion, volatility — together with the research OPPORTUNITY the article
  draws from it (e.g. "sector and thematic selection matters more"). It needs no named stock and no
  earnings mechanism, and it is never forced into a buy thesis. A market-structure condition the
  article presents as a RISK (concentration, a correlation that could cause a simultaneous
  drawdown) stays a market risk — never a record of either kind. **A record is a market regime
  only when its EVIDENCE measures equity-market structure** (correlation, dispersion, breadth,
  price volatility) — on any node, the market-wide one included. A sector or macro mechanism
  (regulation, capacity, demand, capex, rates) extracted as a regime is corrected to an investment
  thesis (`RECORD_KIND_CORRECTED`, with the reason) and its earnings transmission is tested like
  any other. Found 2026-10-11 on Citi's Gridlock and LatAm reports (record
  `docs/records/2026-10-11-theme-intelligence-seven-sources.md`).
- **Whole-article completeness.** A deterministic ledger lists every figure the article TEXT states
  (with its sign and unit; years, tenors such as "200-day", and numbers inside names such as "S&P
  500" are not figures) and every argument paragraph, BEFORE any model output is consulted. A
  second, independent model pass (pass 1b) then re-reads the whole article beside the first pass's
  record and must account for every gap — add the missed claim, mention, thesis or regime record,
  or mark the gap immaterial WITH A REASON. Its additions go through the same verification as pass
  1. Every figure ends captured / added by the completeness pass / immaterial / uncaptured; an
  uncaptured figure is an open WARN issue, a dashboard caveat and a failing QA check.
- **Labels.** A line the source supports is labelled by what its cited claims ARE — MEASURED
  OBSERVATION (a reported figure or dated event), FORECAST (a projection or NTM figure) or SOURCE
  OPINION (the publisher's interpretation, argument or recommendation — never an established
  market fact) — and carries the WEAKEST label among them. MODEL INFERENCE is this tool's reasoning;
  EXTERNALLY VERIFIED is reserved for checks against an independent primary source.
- **Transmission.** A rising or falling share price, valuation multiple or index is a MARKET
  REACTION, filed under its own step and never counted as an earnings mechanism; a step the model
  files as pricing / margins / earnings that only describes a price move is re-filed and logged.
- **Near term is a calendar test.** A forecast or event counts as near-term only when its stated
  window starts within ~a year and ends within ~18 months of the as-of ("2025-2031" never does);
  a measured observation counts when it is dated within the last quarter. The model's horizon label
  is recorded, never decisive. A DISLOCATION must be a mispricing measured in the last quarter and
  a CATALYST a dated event inside the window — an opinion or a forecast figure offered as either is
  listed and not counted.
- **Missing timing never upgrades a thesis** (2026-10-12). Windows written in words are read
  ("over the next five years", "next decade", "before 2030", "into the 2030s", "by the end of
  the decade"); an opinion naming a horizon beyond the next 4 quarters ("unlikely to clear before
  2030") is long-dated evidence, never near-term. "Longer-term only" (SKIP-3) also reads the
  thesis's other linked claims and the verified claims in the paragraphs its evidence sits in —
  for LONG-dated timing only — so a card that leaves the source's horizon out cannot turn SKIP
  into WATCH. With no dated window anywhere the thesis stays WATCH and says "timing UNKNOWN in the
  source evidence; a review should establish it". (Observed on Citi's Gridlock re-analysis:
  midstream capex, skilled labour and nuclear read WATCH until these rules restored SKIP-3.)
- **Exposure.** RESEARCH NOW needs a source-named exposure: a point-in-time-verified listed common
  equity OR a sector / theme the source names (a verified span containing the name). A sector
  opportunity needs no ticker. A company's role as the SOURCE states it (e.g. capex spender) is
  kept apart from the THESIS's reading of it (e.g. potential beneficiary), each labelled.
- **Identity before ticker.** A registered ticker is not proof of identity. A company is matched
  to an SEC registrant only when the SOURCE's own description (the quote and its role) is
  compatible with the issuer's SEC industry (SIC); an incompatible match is refused, and a hint
  naming a foreign listing never resolves by a partial name — the entity stays UNRESOLVED. Found
  2026-10-11: Citi's "Delta" (a solid-oxide fuel-cell competitor — Delta Electronics, TWSE 2308,
  not SEC-registered) had resolved to Delta Air Lines. Point-in-time listing checks still follow.
- **Point-in-time securities.** A named company's exposure lines are the common-equity lines on the
  cover page of its latest 10-K / 10-Q / 20-F / 40-F filed on or before the as-of date
  (inline-XBRL `dei:TradingSymbol` / `Security12bTitle`). Preferred, depositary-preferred and debt
  lines are kept for audit with their class, never as stock; a current-map ticker absent from that
  cover is NOT_REGISTERED_AS_OF (or UNVERIFIED when an 8-A12B registration falls in between). When
  no cover can be read the listing is UNVERIFIED and never counts as an exposure. Alphabet as of
  2026-02-09: GOOGL / GOOG only — GOOGM / GOOGN, depositary shares of convertible preferred stock,
  were registered in June 2026.
- **Re-anchor before withholding.** A non-verbatim quote is re-anchored to the one verbatim
  sentence that carries its figure and shares its words two-sidedly; a card line a check or the
  reviewer rejects is re-cited to the reviewer's suggested spans, a verified claim carrying its
  numbers or words, or — only when an LLM reviewer will judge it again — the verbatim passage
  that carries it (minted as SOURCE OPINION evidence). It is then reviewed once more; only a line
  still unsupported is withheld. A MODEL INFERENCE line is never re-anchored into a source label.
  Only a claim verified on BOTH its span and its number may vouch for a line — whoever proposes
  it, the reviewer included (round 3).
- **Authors.** The union of every place the page credits one — JSON-LD, schema.org/Person
  microdata, meta author, the visible byline (multi-line titles joined) — plus people the article
  TEXT credits ("team led by …") as verified spans. A JSON-LD list that omits an author credited
  elsewhere on the page is recorded as AUTHOR_METADATA_DISCREPANCY; declared alternate language
  versions (hreflang) are recorded (none of the configured channels' article pages declares one).

### Evidence roles, inflections, verification status and dates (review round 3)

Record `docs/records/2026-10-11-theme-intelligence-review-round-3.md`.

- **Thesis identity includes the SEGMENT — the thesis's economic SUBJECT** (`taxonomy.toml`
  `[[segment]]`: DRAM / HBM vs NAND / SSD on memory; grid-connected utilities, behind-the-meter /
  on-site generation and transformers / grid equipment on power). In order: the subject the
  thesis statement names; else the segment of its product, or of the sectors the source names as
  exposed; else segments at least a fifth of its verified quotes name. An incidental comparison
  or customer application never sets it — unassigned rather than wrong (2026-10-12: Citi's
  transformer thesis had been keyed on-site generation from one CCGT comparison in 67 claims).
  A thesis a later reading reaches by another key, whose own segment under today's rule differs
  from its key's, is re-keyed — same id, versions and evidence, the old key recorded
  (`KEY_CORRECTED`), never onto a key another thesis holds.
- **Evidence roles.** Only evidence of the SAME identity reaches a thesis's own history —
  *Direct confirmation* (new evidence, or an independent source) or *Repeated source*
  (attribution only). A related thesis is a registry LINK with a role, never evidence:
  *Adjacent support* (same direction, another segment / mechanism / node, or the same claim at an
  overlapping but different geography — context, never a strengthening) or *Related* (the
  opposite direction on related economics — never counter-evidence).
- **A contradiction needs the same claim.** A challenge (COMPETING: evidence filed as CONTRADICTS,
  the incumbent re-versioned WEAKER) needs the same node, mechanism and segment, overlapping
  geography and timeframe, and the opposite outcome. Any difference — named on the link — makes it
  RELATED: no CONTRADICTS evidence, no WEAKER version, no downgrade. A falling utility share price
  does not contradict rising demand for on-site generation.
- **The near-term inflection route to RESEARCH NOW (F12).** Without a dislocation or dated
  catalyst, a thesis can still be RESEARCH NOW when ALL hold: a verified claim states a CHANGE in
  a FUNDAMENTAL (price, revenue, margin, demand, supply, shipments …; never a share-price move or a
  technical metric) within the next 2-4 quarters or measured in the last; it is CREDIBLE — the
  publisher's own data in an industry data report (by channel, never by the model's say-so), or
  corroborated by a measured change in the thesis's evidence — never a forecast alone; the source
  states the fundamental step itself; and a source-named exposure turns it into a concrete question
  in the trace: "do current earnings estimates and market expectations for X already reflect Y?".
  Every other RESEARCH NOW condition still applies (full retrieval, asserted premise, no hold …).
- **Scan execution vs research verification.** The run's status (SUCCEEDED / PARTIAL / FAILED)
  says whether it EXECUTED. The research-verification status says how much of what it READ is
  accounted for: FULLY_VERIFIED, VERIFIED_WITHIN_PREVIEW (a paywalled preview's unread remainder is
  unread, not verified), INCOMPLETE (a figure or paragraph open, or a pass not run) or
  NOTHING_ANALYSED. Both show on the dashboard header and a tile, in `dashboard.md` / `.json`, the
  manifest, the CLI and the QA summary. Every open item states its cause — `verification_failed`,
  `capture_not_verified`, `account_names_no_record`, `no_account`, `pass_not_run`. An account that
  names verified claims closes its paragraph; QA fails if any unverified claim is ever linked to a
  thesis.
- **Three dates.** *Published* (the latest contributing source's date), *first ingested by the
  registry* (the actual wall-clock UTC time) and *analysed as of*. When the as-of precedes
  ingestion the run is a historical replay and says so — a simulated date is never called a
  detection.

## The six channels (editable: `vinci/theme_intelligence/config/sources.toml`)

Six approved publishers since 2026-10-13 (operator decisions): Bank of America (2026-10-11) and
Nomura (2026-10-13 — its full reports sit on a client portal with no public sign-up, so they
could never be supplied) were removed — not replaced — and sit under `[[retired]]` as HISTORY
only: no discovery, no health check, no upload request on the weekly report or the desk, no new
import (`ingest-file` / `article` refuse the source and any URL on its hosts — for Nomura its site
and its portal); their earlier evidence, theses and runs stay in the registry untouched and are
never requeued. Every count — health, coverage, intake — is derived from the configured six,
never hardcoded. Bank of America stays retired (the operator confirmed it on 2026-10-14, though it is on the
original shortlist).

Access as probed on 2026-10-09/10 with the honest research User-Agent (no browser spoofing, robots.txt
honoured per RFC 9309, a robots.txt that cannot be fetched fails CLOSED):

| channel | discovery | state |
|---|---|---|
| Citi Must C | the page's embedded CMS data (`__NEXT_DATA__`): series items + CMS publishDate | OK — the page embeds its ~20 linked items; older ones are not listed there. Each page links its full report as a public PDF ("Download Here", or "Read the full article here.") — read automatically (`linked_reports = "fetch"`), however short the page itself |
| J.P. Morgan Top Market Takeaways | listing cards with dates (sitemap lastmod as a fallback that can only rule a page OUT) | OK |
| Morgan Stanley Research | **manual-first** (`mode = "manual_first"`): a lightweight health check only; research arrives as authorised uploads | automated access **BLOCKED** — the connection is dropped on every request, robots.txt included; never bypassed, never retried inside its back-off |
| TrendForce press center | listing pages `?page=N`, date in the article URL | OK |
| SemiAnalysis | the newsletter's RSS feed (pubDate) | OK — paid posts carry a preview only and are recorded PARTIAL; **preview-only by decision** (2026-10-13, no subscription — `paywalled_posts = "preview_only"`): the preview is analysed and labelled a preview, the full post never requested |
| Goldman Sachs Research | **manual-first**, as Morgan Stanley | automated access **BLOCKED** — HTTP 403 on entry, sitemap and insights. Where to look by hand (`research_pages`, 2026-10-14): the Research page (deep thematic pieces, about two a month) and the Markets page (shorter articles each week, plus podcasts and videos) |

Morgan Stanley and Goldman Sachs are **manual-first**: a scan does not attempt their discovery
(coverage row `MANUAL_FIRST`), their automated access is still health-checked (`expect_blocked`
marks the refusal as standing, so it never turns a run PARTIAL or re-alerts), and their research
arrives by `ingest-file`. A week with nothing supplied says their research is MISSING, not absent.
The health status stays BLOCKED — never concealed — and the KPI strip says it beside their name.
Any automatic channel that fails turns the run PARTIAL.

## Source health monitoring (`health.py`)

Is each channel still being READ, or failing silently? A bounded, LLM-free check per channel —
never "healthy" because a page answered HTTP 200. Record:
`docs/records/2026-10-11-theme-intelligence-source-health.md`.

```bash
python -m vinci.theme_intelligence sources --check-health            # report + next actions
python -m vinci.theme_intelligence sources --check-health --json     # machine-readable
python -m vinci.theme_intelligence sources --check-health --sources gs_research --force
python -m vinci.theme_intelligence sources                           # last-known status only
```

It also runs at the start of EVERY scan (scheduled or manual), and the weekly dashboard shows it
apart from the scan's execution status and the research-verification status.

- **The seven tests.** (1) *access* — the endpoint discovery starts from, under robots.txt and the
  honest User-Agent; (2) *discovery* — the channel's own adapter finds genuine article URLs (titles,
  listing dates); (3) *extraction* — up to three articles SPREAD across the listing (newest dated,
  middle, oldest) fetched and parsed; (4) *dates and authors* — each page's own date and byline, the
  listing's dates, and the latest scan's undated share; (5) *completeness* — full text, paywalled
  preview or partial page, plus the latest scan's outcomes; (6) *freshness* — the newest dated
  article against the window, URLs new since the last check; (7) *parser integrity* — a 200 page
  whose body the parser cannot read, or an extraction that collapsed against the channel's own
  earlier ones.
- **One status.** BLOCKED (access denied, or cannot safely proceed — a robots.txt that cannot be
  read FAILS CLOSED and nothing is fetched) · ERROR (a transport failure, an unexpected answer, a
  broken adapter or a crashed check) · DEGRADED (previews, undated pages, partial extraction, a
  parser that no longer reads the page, a listing with no articles) · HEALTHY (every test passed) ·
  UNKNOWN (never checked). **Freshness is separate**: nothing dated in the window is QUIET, not
  unhealthy.
- **Politeness.** A 401 / 403 / 451 is never retried, and a channel that refused is not
  re-requested for 24 hours (`--force` overrides). The live access fetch is reused by the scan's
  discovery that follows, so a scan does not ask twice. The channel's crawl-delay floor and the
  site's robots Crawl-delay apply to every request.
- **History and changes.** Every check is an immutable row (`source_health`, schema v3), exported
  with the registry, so status and failure streaks survive the scheduled run's restart. Each row
  carries: last checked, last successful discovery, last successful full-text extraction, last
  verified publication date, articles discovered / in the window, the latest scan's full / preview
  / undated / unreadable counts, consecutive failed checks, status since, and what changed —
  HEALTHY → DEGRADED / BLOCKED, extraction → parser failure, a drop to zero discovered articles
  (flagged for review, never read as "published nothing"), dates missing at consecutive checks, a
  BLOCKED channel accessible again.
- **Alerts.** NEW_FAILURE on a change into a failing state, RECOVERED on an improvement, one
  PERSISTENT_FAILURE reminder when a failure reaches three checks, then nothing until it changes; a
  known standing restriction (`expect_blocked`) is shown, not re-alerted. The dashboard shows them
  in a banner. Delivery: set `THEME_INTELLIGENCE_HEALTH_HOOK` to a command; it receives the alerts
  as JSON on stdin (no email or chat integration is required).
- **Manual upload.** A BLOCKED or DEGRADED channel carries an UPLOAD_REQUIRED (blocked, previews,
  unreadable pages) or MANUAL_REVIEW (undated pages, an empty listing, a persistent error) item
  naming the publisher, the issue, the affected article if known (its URL and the title the
  listing gave — never an invented one) and the action. Upload an authorized copy through the
  SAME pipeline: `ingest-file --path <report.pdf or saved page> --source <id> [--url <article
  URL>]` (or, for a saved web page, `article --url <URL> --html <saved page>`) — labelled a manual
  upload in the article's provenance. An upload never changes the channel's
  health: one document is not proof of its coverage. When automatic retrieval is shown to work
  again the item is lifted for future articles; uploaded articles stay in the registry.

## Manual documents (`documents.py`, `ingest.py`)

A report the operator holds — an institutional PDF from a blocked channel, the full text behind a
preview, a saved page — enters the SAME pipeline, registry and weekly report as a fetched article:
source attribution, whole-article completeness, number and citation verification, company /
sector identification, thesis extraction, claim-level relationship rules, Research Now / Watch /
Skip, the nine-section card, version history. **The route in never changes research priority**
(pinned: the same report as a fetched page and as an upload gives the same thesis, action and
rules).

```bash
python -m vinci.theme_intelligence ingest-file --path "/secure/research/report.pdf" --source ms_research --llm-permitted
python -m vinci.theme_intelligence ingest-file --path full-post.pdf --source semianalysis --url https://newsletter.semianalysis.com/p/<post>
python -m vinci.theme_intelligence ingest-inbox            # every file in data/theme_intelligence/inbox/
python -m vinci.theme_intelligence documents --status HELD
```

- **Formats.** PDF (pdfplumber, a project dependency), HTML, Markdown, plain text. DOCX is refused
  with a plain message (no compatible library is installed — save it as PDF).
- **What is kept.** Text in reading order with a PAGE reference on every block; each table as ONE
  block with its cells and values as printed (`$48.3bn`, `4Q26E`); footnotes; headings (a wrapped
  heading is one heading); title, authors (metadata, front matter or a "By …" byline) and the
  document's own date, each with where it was read. Running headers, footers and page numbers are
  left out and counted.
- **A date the page prints is read wherever it sits** (2026-10-14). A research web page saved as
  PDF can lay its headline and date out in boxes the reader detects as a table (every Morgan
  Stanley page does); the date in such a box is the document's own, never left unknown.
- **A saved preview stays a preview** (2026-10-13). A paywalled page saved as PDF without a paid
  sign-in ends with the publisher's subscriber notice ("This post is for paid subscribers …");
  the document is then PARTIAL, said why, and Uploads keeps asking for the full post. Save a paid
  post while signed in to the paid subscription.
- **What is flagged, never dropped silently.** A page with no text layer (a scanned image — OCR is
  not available here) makes the document PARTIAL; a page with charts says its plotted values are
  not verifiable; a page that cannot be read is named. Numbers shown only in a chart are never
  turned into evidence.
- **Unreadable font text is quarantined, never analysed and never hidden** (`documents.py`,
  `parse.py`, 2026-10-12). A PDF font with no character map comes out of the text layer as
  `(cid:N)` codes — Citi's Gridlock report set its 7-page disclosure appendix that way: 308,181
  characters on pages 54–60, 85% of the 293,161 tokens resent in every model call, and 446 false
  "figures" read from the codes. Before anything
  reads the text, each LINE and table CELL is tested: ≥ 3 codes covering ≥ 50% of its non-space
  characters, or a line mostly set in a font whose characters on that page are ≥ 50% codes (its
  scrambled near-letters go with it). Such text is left out — a readable line on the same page,
  and a sentence that merely mentions a CID, are kept — and recorded per page (lines, cells,
  characters, sha256) on the document record, which is PARTIAL with the issue "page N:
  undecodable font glyphs … what they say is NOT read — the page needs visual / OCR review". The
  weekly report lists it under research intake as **VISUAL / OCR REVIEW**, never as a missing
  document. No OCR is attempted, and no claim of full verification is made. The file and its
  sha256 are unchanged; only the text the model is sent changes.
- **What an unread page is — from the READABLE document only** (`documents.classify_unread`,
  2026-10-12). Each quarantined page is BACK MATTER (no readable analysis after it; fine print —
  at least twice the median readable page's characters, in type smaller than the body; and, when
  the document has a contents list, after the last section it names), POSSIBLY MATERIAL (analysis
  follows it, or the contents list names a section there) or UNCLASSIFIED. The visual-check line
  says which, and why. Only when EVERY unread page is back matter by the document's own contents
  list does the research-action gate read the analysis text as whole (F11 says so) — the document
  stays PARTIAL, research verification still says "read only in part", and it is no longer listed
  as awaiting a complete document. Citi's Gridlock pages 54–60: back matter (13–57k characters a
  page at 9pt vs a median 2,430 at 10pt, after page 51, the contents list's last section).
- **Re-reading a document the current reader reads differently** (`--reread`). The same file
  again is a DUPLICATE; when today's reader would read it differently (e.g. a report imported
  before the quarantine), the DUPLICATE says so and names `--reread`. `ingest-file --path <file>
  --reread` then analyses it as a NEW VERSION of the SAME article: the document keeps its id,
  arrival time, file name and standing (INGESTED / UPGRADED), and gains a history line; the
  article keeps its id, title, date and first-seen time; the earlier version, its verification
  ledger and every thesis version it produced are kept as they were. A sentence and figure the
  earlier version already gave a thesis is REPEATED evidence — one row, never "new", never a
  confirmation — however the new answer labels it. The new text is a new prompt, so the analysis
  is paid for again (the cache never answers changed text); the cost limit applies as for any
  import. Unchanged text → DUPLICATE ("unchanged"), nothing sent. A hypothesis of the new version
  that holds at least half its sentences on a thesis the earlier version created is THAT thesis —
  updated, its id kept (`SAME_ARTICLE_MATCH`) — when direction, geography, mechanism family,
  segment, product and time horizon agree; a different value-chain node label is stated, never
  blocking (2026-10-12: on Citi's re-read the transformer story, 61 of 68 sentences, and six
  more matched). A different mechanism FAMILY on the same evidence — two thirds of EACH side's
  sentences shared — is one causal chain read at two steps, not two theses (Citi's fuel cells:
  "share gain" in one reading, "demand volume" in the next, 14 of 17 sentences the same; the
  earlier id and mechanism kept); with evidence of its own on either side it may be a second,
  separately falsifiable mechanism and goes to review, with what each would mean for earnings. Any other difference: a SIBLING — created, held for review (never RESEARCH NOW),
  flagged `SAME_ARTICLE_SIBLING` with the dimension that differs. Overlapping sentences alone never
  merge. A thesis whose sentences the new version re-states (at least half) but no hypothesis took
  is RE-VERIFIED and re-assessed under today's rules — a new version only when the assessment
  changes (Citi's low-cost US gas thesis: WATCH → SKIP-3). A sentence read again counts once.
- **A malformed answer field costs that field, never the answer** (`extract.salvage_fields`,
  2026-10-12). A completeness answer whose top level fails is read field by field, then item by
  item: a list given as valid JSON text is decoded; a field that is neither is discarded with the
  exact error and the ids its text names (listed, never used). The rest is verified like any
  answer; a review naming a discarded claim stays open. Such a part is not shown to later parts,
  so their requests stay exactly as paid (a replay costs $0). To pay for that ONE part again:
  `python -m vinci.theme_intelligence reask-part --doc <D-…> --part <N> --max-cost <USD>` — the
  whole chain must reproduce from the cache first (else nothing is sent), the one call is bounded
  against `--max-cost` (required), and the answer is kept beside the paid original and used the
  next time that version is analysed (a replay or a re-read); nothing analysed is rewritten.
- **Mechanism coverage — nothing the source argues disappears unnoticed** (`coverage.py`). After
  the theses are applied, every proposition a model pass proposed is ON A CARD, MERGED under one
  identity key (both named, with shared vs own evidence — distinct evidence is an alert) or
  DROPPED with why; every VERIFIED material fact (figure, forecast, event, metric) that no thesis
  carries — nor an earlier version's card, nor a market risk — is listed by page, and two or more
  on a page ALERT ("a mechanism no card holds?"). Every proposed market risk shows its card(s);
  organisations a cited paragraph names as examples or as a dated source but nobody recorded are
  listed. Alerts are `MECHANISM_COVERAGE` issues and a section of research verification (which
  then reads INCOMPLETE); the full record is in the audit view and the JSON. Nothing is forced
  into a card and nothing merges by similarity. A proposition a paid answer named and its re-ask
  did not propose again is listed as dropped, with that reason. A page alert names the source's
  figures as written and says they are UNASSESSED there — the source's evidence, kept apart from
  any assessment a card holds.
- **No verified material evidence → never a research opportunity** (`report.py`, 2026-10-12). A
  proposition whose action rests on SKIP-1 is listed in its own section of the weekly page, "Not
  research opportunities", with why and its card — never under NEW / UPGRADED / … It stays in the
  counts, the archive and the printed record.
- **One technology, one thesis** (`taxonomy.toml` products, `engine.product_signature`,
  2026-10-12). A thesis's PRODUCT is the one its own statement names, else the one at least a
  fifth of its cited claims name (a passing mention is not its subject). Two hypotheses on one
  identity key that share no supporting claim and name different products are separate theses
  (`|prod:<product>`, `PRODUCT_SPLIT`) — Citi's fuel-cell share story is no longer inside the
  gas-turbine thesis — and a risk naming only the split-off product goes with it. A separate
  thesis earns no action by being separate.
- **Risks the source states** (`coverage.scan_source_risks`, 2026-10-12). Every sentence of a
  readable argument paragraph that states a downside in the source's own construction ("risks
  remaining", "might put downward pressure", "did not materialize", "execution risk remains" —
  never the bare word, never "little risk of …") is checked against what carries it: a proposed
  risk, a counter-claim, a card's alternative mechanism, a cited quote, or a proposed risk drawn
  from its paragraph. One nothing carries goes into 07 of ONLY the theses whose evidence shares
  its paragraph — the verbatim sentence, labelled SOURCE OPINION, flagged `SOURCE_RISK_OMITTED`
  — and is a coverage alert; with no such thesis, or cut by a page break, it is alerted and
  placed nowhere. No generic risk is added to every card.
- **Dates.** The publication date comes from the document's own text (page 1-2) or front matter —
  NEVER from the upload time, the file name or the PDF's CreationDate / ModDate (a FILE date,
  recorded as such). `--published` fills only a gap; when it disagrees with the document's own
  date, the document's is used and the disagreement is listed for review.
- **No URL.** An institutional PDF with no public link is identified by its content
  (`urn:document:sha256:…`) and its publisher is the channel named by `--source`.
- **Identity, before any model call.** The same FILE again (any name) → DUPLICATE, nothing
  re-counted. The same TEXT in another format → DUPLICATE. A fuller document of an article held
  PARTIAL (`--url` stated, or the same publisher's title, date and text) → **UPGRADED**: a new
  version of the SAME article, re-extracted and re-checked; the earlier version is kept, and
  claims it restates are REPEATED, never independent confirmations. A later version that names
  more segments updates the thesis its earlier version created (same-article continuity), never a
  twin. A document that contains a COMPLETE held article plus more (a printed web page with its
  site furniture, an annex) → REVIEW. Any uncertain match → **REVIEW** — a human answers with
  `--same-as <article>` (a fuller version), `--duplicate-of <article>` (the same: add nothing) or
  `--as-new`; nothing merges automatically. A title overlap ALONE reviews only from 50% (a
  publisher's titles share house words). A saved web page's own canonical link identifies the
  article it names, without `--url`. On a registry pulled from the state branch the held text is
  not on this machine, and the basis says so: comparison is by URL, title and date only.
- **Licence — HELD until authorised.** A document's text goes to the third-party LLM only when the
  operator states its licence allows it (`--llm-permitted`, per document) or the channel's
  `manual_llm_processing = "permitted"` in `sources.toml`. Otherwise it is HELD: read, stored
  privately, listed — never analysed and never evidence. `--llm-not-permitted` holds it explicitly.
  Re-run with `--llm-permitted` (or `--release <doc id>`) once confirmed.
- **Cost — estimated before any model call, limited per document.** The completeness pass
  reviews every stated figure and argument paragraph the extraction did not capture, in parts of
  50, each re-sending the whole text — so cost follows FIGURE DENSITY, not page count. Measured
  (list price, 2026-10-11): Citi's 34-page ETF report with its page $3.80 (7 parts), its 57-page
  LatAm report $9.47 (10 parts), its 60-page Gridlock report — 851 stated figures — $46.67 (22
  parts, $39.44 of it completeness), and $11.70 once its undecodable appendix was quarantined.
  Before any call the document is estimated from the TEXT IT WILL SEND (after quarantine) and its
  parts (`ingest.estimate_from`, `config.DOC_COST_*`, 2026-10-12): the HIGH end prices every call
  at its full output cap and at the densest characters-per-token measured, with two extraction
  calls and $5 of card reviews. Measured inside every range: Gridlock first read $28.54–$58.92
  ($46.67), cleaned $6.56–$20.77 ($11.70 — the old per-part estimate held it at $31.40), LatAm
  $6.60–$19.82 ($9.47), ETF $3.75–$14.10 ($3.80). Above `DOC_COST_LIMIT_USD` ($30) it is HELD
  (COST) with the estimate and the command to proceed:
  `ingest-file --release <doc id> --max-cost N`. The same limit stops a scan from spending on a
  linked report unattended — it is stored, held and listed.
- **Spending limits, checked before EVERY paid call** (`budget.py`). A run (scan $40, a manual
  batch $100 — `--budget`), a document ($30 or `--max-cost`) and its retries + completeness
  passes (85% of the document limit) each have a limit. Before a call its cost is BOUNDED — input
  at (characters / 2.5) tokens priced as cache writes, plus the full output cap — and a call
  whose bound does not fit the smallest remaining limit is never sent: the article is
  checkpointed BUDGET_HELD (a scan stops and queues the rest), the answers already paid for stay
  cached, and a re-run with a higher limit resumes without paying for them again. Actual cost is
  recorded from the provider's usage; the manifest carries both (`spend_guard`). The bound is
  conservative, not a provider-side billing cap.
- **Why long reviews cost what they cost.** Every completeness part resends the WHOLE article (a
  gap's account may cite any block): Gridlock's 22 parts sent 309,342–334,027 input tokens each,
  $35.65 of the pass's $39.44. `config.PROMPT_CACHE_PARTS` would send the article as a cached
  first block (same text, a tenth of the price after the first part; measured −45% on Citi's
  ETF report); it ships OFF until its evidence quality is shown equivalent — one paired run left
  that undecided (record above).
- **Dates, never conflated.** Each article VERSION keeps the date its own document states and
  where it was read; the card's sources table shows every version's date when they differ. A
  report dated up to 30 days before the page that publishes it is ordinary
  (`VERSION_DATES_DIFFER`, INFO, both kept); any other difference is flagged for review
  (`PUBLICATION_DATE_CONFLICT`, listed for a metadata check). Upload time and analysis as-of are
  separate fields; a replayed upload keeps the time it first arrived.
- **Failures.** A document the model could not analyse (no key, no cached answer, an API error)
  is recorded FAILED with a plain message — never left RUNNING; an inbox file stays in the inbox.
  Imported again, it is analysed (RETRY), never mistaken for a duplicate of an analysis that did
  not finish.
- **Privacy.** The original is copied to `data/theme_intelligence/documents/<sha256>.<ext>`
  (owner-only, git-ignored); its text lives only in the local registry, which exports WITHOUT
  article text. Nothing prints document text. A test fails if any PDF / DOCX other than the
  labelled synthetic fixtures is ever tracked by git.
- **The inbox.** Put files in `data/theme_intelligence/inbox/` with an optional
  `<file>.meta.json` (`source`, `url`, `title`, `authors`, `published`, `llm_permitted`);
  `ingest-inbox` imports each and files it under `processed/`, `held/`, `review/` or
  `rejected/`. A file with no source stated is left in place and named.
- **Ready for licensed reports.** Morgan Stanley / Goldman Sachs / SemiAnalysis PDFs the operator
  is entitled to use need no further development: `ingest-file --source ms_research|gs_research|
  semianalysis --llm-permitted` once their licence permits third-party processing.

## Research intake / manual action (dashboard)

One compact section beside source health, **its own status** (ingestion coverage — apart from
source health and research verification), each list with its population and "showing X of Y":
articles analysed automatically; articles imported manually (published · uploaded · analysed-as-of
kept apart, and whether the original is on this machine); partial articles awaiting a complete
document; publishers blocked or degraded; known articles needing an upload (a linked report the
channel will not let us fetch, a blocked channel's affected article); articles needing a metadata
or licence check (undated pages, HELD and REVIEW documents, a date disagreement); and coverage
gaps (a blocked channel's coverage is UNKNOWN — no new article from it is not evidence it
published nothing; truncated discovery; the queue). Every row of the ranked list says how its
evidence arrived (automatic / manual upload / linked report fetched automatically).

**One weekly report.** A scan's dashboard takes in every manual-ingest or single-article run since
the previous scan, so an upload on Wednesday is in Monday's ranked list. An article published last
month and uploaded today shows *Published* last month — never as new this week.

## One supervised pilot — operator checklist (2026-10-12)

The pilot is ONE run a person starts, watches and reads — never the weekly schedule.

**Before**
1. Keep the cron OFF (`THEME_INTELLIGENCE_SCHEDULE_ENABLED` unset). Never print a key; the run
   reads `ANTHROPIC_API_KEY` and `SEC_USER_AGENT` from the environment.
2. `sources --check-health` — read the table. Morgan Stanley and Goldman Sachs are manual-first:
   their week arrives only as uploads (`ingest-file` / `ingest-inbox`), into the SAME registry.
3. For each licensed report you will upload, confirm its third-party-LLM terms before passing
   `--llm-permitted`; without it the document is HELD, never sent.
4. Keep the $30 per-document limit (raise it only per document, with `--max-cost`) and set a run
   budget for the scan; a HELD document or a refused call is the limit working.

**The run**
5. `state pull` (if the registry lives on the state branch), then one scan by hand with a small
   `--max-articles` and a `--budget`, then `qa --run latest`. Note the run id.

**Read, in this order**
6. Research verification (INCOMPLETE is normal: it says what is open), then the mechanism-coverage
   alerts — dropped propositions, uncarried facts with the source's figures (UNASSESSED), risks
   the source states that no model pass listed.
7. Research Now / Watch rows: open each card — 06 (timing), 07 (risks; SOURCE OPINION lines come
   from the source's own words), 08 (the decision trace), 09 (sources and version history).
8. Identity flags: `SAME_ARTICLE_SIBLING` (held for review), `KEY_CORRECTED`, `PRODUCT_SPLIT`;
   then "Not research opportunities" (no verified material evidence) — never act on those.
9. Record each verdict (confirm / override) and the run's actual spend (`manifest.json`
   `cost_usd`, the paid-call ledger).

**Stop and report if** a call is paid beyond the budget; one story yields two opportunities; a
single publisher's re-read shows as an independent confirmation; a card misses a section; or a
document is analysed without its licence confirmed.

### After the pilot (2026-10-12) — what changed, and what to read

- **A malformed first answer is salvaged, never asked again.** Its other fields are kept; a list
  written as broken JSON text is mended by deletion only (`ANSWER_SALVAGED` says what was
  deleted); a hypothesis still unreadable is a dropped proposition — a coverage alert, so the run
  reads INCOMPLETE. Answers an earlier run paid for and set aside (`<key>.invalid-N.json`) are
  salvaged instead of paid for again.
- **Near-term means the next four quarters.** Next year's undifferentiated full-year figure is a
  *straddling* window: never near-term evidence, never SKIP-3 — WATCH. A page category line
  ("Semiconductors") is a *bare label*, never an exposure (`SECTOR_LABEL_ONLY`).
- **Re-grade stored theses** under the current rules — stored evidence only, $0:
  `python -m vinci.theme_intelligence reassess --as-of YYYY-MM-DD [--thesis TH-…]`. A changed
  action is a new version (DOWNGRADED / UPGRADED); the reviewed sentences are kept word for word.
- **Review warnings sit on the line.** A line the card review questioned and left printed shows
  `⚠ UNRESOLVED REVIEW — <why>` and is never labelled a verified fact; a conditional line
  (could / may / might / would / if) is at most SOURCE OPINION.
- **A stored preview recorded FULL** is corrected the next time its page is read (a scan, or
  `article --url … --cache-only`): `RETRIEVAL_CORRECTED`, read as PARTIAL from then on, and the
  theses it fed are re-graded at once. The original row, first-seen date and spend stand.

### Reading the weekly page and the thesis card (2026-10-12 redesign)

- **The weekly page** opens on the research: the week, a summary (Research Now / Watch / Skip,
  review items, verification, articles read), then every thesis of the week as a card — its
  mechanism, what changed, the effect on profits, why it is (or is not) Research Now, the next
  question, the source and its dates. A thesis new and re-graded in one week is ONE card showing
  both events. The navigation reaches the activity, the review queue, sources, the archive and
  **Operations & audit** (run ids, engine codes, upload commands, the validation log).
- **The Living Thesis Card** opens with its header (action, horizon, the three dates, and a
  **Review required** link to each questioned or withheld line) and **At a glance** — the
  thesis, what changed, the effect on profits, the strongest evidence, why this action, what
  could invalidate it, the next check — then the nine sections in full.
- **Audit view** (top right) shows evidence ids, engine codes and the decision trace. Print opens
  every section and prints the audit layer: the PDF is the complete record.
- **Evidence links** (Audit view) reach their evidence: the key rows of section 04, or its
  "Other evidence this card cites" table (counter-evidence, context). A link into a collapsed
  section opens it.
- **Section 05** lists the **business groups** the source names ("GPU and ASIC manufacturers")
  apart from listed-company exposures — not companies; no ticker is implied, and they do not count
  toward Research Now.
- **The review queue** leads with the findings on the CURRENT cards (each shortened — the whole
  finding is on its card line); incomplete sources, background alerts and **resolved or
  historical** items (a figure that failed a since-corrected check; a review finding a later
  version resolved) are collapsed below. History is never deleted: the stored records stand.
- **Correct one card line from stored evidence** — $0, no model call — with an analyst
  correction: a JSON list of `{thesis_id, sentence_id, text, claim_ids, reason}` passed to
  `reassess --as-of YYYY-MM-DD --corrections FILE`. Each must cite verified claims the thesis
  already links and pass the card's number check, or the run fails and nothing is applied. The
  sentence ids are the card's own (`s01.0` …; Audit view shows them). The corrected line carries
  "Corrected by the analyst — <reason>"; the earlier version stands in the history. Keep the
  corrections file private: it may quote licensed text.

### The research desk (2026-10-13 — the approved design)

Every run's output folder opens on the desk (`index.html`); the weekly report
(`dashboard.html`), its printable record and the cards are unchanged and linked from it.

- **This Week** — the week in a sentence and five counts (articles read, theses new or changed,
  Research Now, findings to review, upload items), then the week's thesis changes grouped by
  research area (new, upgraded, downgraded, challenged, new evidence) and what each article
  produced, including zero-thesis, partial, held, failed and queued ones. **Needs your attention**
  sits beside them; every active thesis by area is one fold below. Before the first weekly scan,
  the week is every manual run since (a week in progress).
- **Themes** — every thesis, active and archived, by area: search, filter by status, action and
  area, and sort by last new evidence, closeness to archiving, sources or open findings. An area opens
  when it changed this week; the others are one click away. Areas use short names; the taxonomy
  keys are unchanged.
- **Articles** — one page per week (older / newer, and every week in one fold), each article's
  state, what it produced, its open completeness items and its follow-up.
- **Review** — every unresolved finding on every active thesis, whatever week raised it, grouped
  under its thesis, in order: decision-affecting first, then Research Now, then the oldest. Each
  links to its exact card line; a line's scope note is in the audit view, as on the reading page.
  Resolved and historical findings stay below. The page is read-only; a finding closes only through
  the record (an analyst correction or a re-read).
- **Uploads** — everything to supply or clear, never dismissed by age, each with its publisher,
  dates and the command to run (folded on its row; the source id is in the command and the audit
  view). A source's request lists its articles by title, linked, and says what is already held of
  each ("supplied — held until you confirm its licence"), and leaves Uploads once every article it
  lists is supplied or read; a source whose articles the scan cannot list (Morgan Stanley, Goldman
  Sachs) points to its research page instead. The weekly steps are
  listed beside it.
- **Sources** — one plain line per channel from its latest check's test results ("some articles
  are previews or summaries of a fuller report"), the check's own findings one fold away, the
  history strip once two or more checks are stored, the newest article (on the site or held),
  articles analysed in the last four weeks; automatic and manual-first coverage apart, the
  manual-first ones with their research page.
- **The reading page** (`theses/<id>.html`) — the thesis; why this action beside what to
  investigate next; the strongest figures; how it reaches fundamentals beside what could prove it
  wrong; what changed beside who is exposed. Open findings, related theses (theses sharing a source
  are flagged as the same source, not independent confirmation), evidence, history and sources
  follow; the longer lists (conditions met, more risks, signals to watch) are one fold away. **Full
  record** opens the nine-section card, or any one section.
- **Timing** — the near-term condition is stated once, met or not, from the stored factor, with
  the dated claims it reads and where each date comes from. The source's horizon label is printed
  as a description, not a test. If those claims, re-dated today, give another value, the page shows
  **Review required** and the research action of record stands until the thesis is reassessed.
- **Not reviewed.** When the card review did not run for a version (`--no-review`, the review
  budget exhausted, or no model client and no cached review), the card, the weekly report and the
  desk say so, and the earlier open findings stay open: on an unchanged line as before, on a
  changed line as **NOT RE-REVIEWED**, on a removed line listed apart — never resolved by the
  skip. The next review that runs stands on its own findings.
- **Audit view** (top right) shows ids, engine codes, factor values and the decision trace, as on
  the card.
- A registry holding articles from a reserved test domain (`.test`) says **TEST DATA** on every
  page.

**One theme.** The desk, the Living Thesis Card and the weekly report share one palette (light and
dark, following the OS), one type and one nav bar — the desk's six screens — with the audit switch at
the right. The weekly report keeps its own sections in a second row ("On this page").

**Not checkable on this machine.** The weekly runner rebuilds the registry from the state branch's
export, which carries no article text; there, business groups (read from the evidence paragraphs)
are reported as *not checkable on this machine*, never as *none*.

**Inside the main app (`frontend/theme-intelligence/`).** The app (Nostra Vinci) shows the desk as
its **Theme intelligence** section — This week, Themes, Articles, Review, Uploads and Sources as
tabs, a thesis's reading page under Themes, the Full record and the weekly report opening as the
published pages in a new tab — in the app's own design language and light/dark toggle. To publish a
run (no model call):

```bash
python -m vinci.theme_intelligence state pull
python -m vinci.theme_intelligence publish
git add frontend/theme-intelligence && git commit -m "theme intelligence: publish <week>"
```

`publish` takes the latest run (`--run` for another), replaces the previous publication whole, and
refuses a registry holding test-domain articles (the synthetic stress registries) unless
`--allow-test-data` is given for a local preview. Commit the folder ALONE (an artifact commit — never
with code) and merge it the way the dossier artifacts are; Cloudflare Pages deploys it with the site.
What is published is derived analysis with titles, figures and short source quotes for internal use
on the authed deploy (operator decision 2026-10-13) — never an article's text, never a local path.
The weekly Actions run does NOT publish (it commits only to the state branch); publishing stays a
deliberate step. **Operator decision 2026-10-13:** publish the current snapshot once #703 is merged;
keep weekly publishing MANUAL for now (one `publish` + an artifact commit each week), and revisit
automatic publishing after the first few weekly runs look right.

**Follow-up requirements (documented, not built).**
- **A. A safe one-step weekly upload command:** a cache-only state pull, identity and licence
  checks, a cost preflight, an explicitly budgeted import, QA, ledger reconciliation, and a
  fast-forward-only push. No implicit paid replay.
- **B. Append-only review resolution:** version-specific findings, with reviewer, time, reason,
  and a verified correction or dismissal; full history kept. Accepting a warning must never itself
  make unsupported evidence valid.

## Scheduling

**GitHub Actions — `.github/workflows/theme-intelligence-weekly.yml`.** Actions is active on this
repo (the `gate` workflow ran green on main and on PRs through 2026-10-09). The workflow has:

- `workflow_dispatch` — Actions → *theme-intelligence-weekly* → *Run workflow* (inputs: `days`,
  `max_articles`). A workflow must exist on the default branch before it can be dispatched, so the
  first manual run is possible only after merge.
- a Monday **03:00 UTC (08:30 Asia/Kolkata)** cron that is **opt-in**: the job runs on it only when
  the repository variable `THEME_INTELLIGENCE_SCHEDULE_ENABLED` is `true` (Settings → Secrets and
  variables → Actions → Variables). Merging the file starts nothing unasked.
- secrets: `ANTHROPIC_API_KEY` (extraction + review) and `SEC_USER_AGENT` (SEC fair-access contact),
  both already used by the repo's other workflows.

A runner's SQLite file dies with the runner, so the **registry of record on Actions is the
`theme-intelligence-state` branch**: each run restores the append-only JSONL export into a fresh
SQLite, runs the gate (ruff, `mypy --strict`, offline pytest), scans, runs QA, then commits the new
export plus that run's readout to the state branch — never to main. Every run is one commit, so the
branch history is the backup and the audit trail; a FAILED or PARTIAL run commits its run record
and readout too. Article full text is never committed (the export blanks it; block hashes and the
short verbatim claim quotes stay as provenance), and the raw-page cache is not carried between
runs.

**Manual documents and the scheduled run — ONE registry (`state.py`).** Actions cannot reach the
operator's machine, and the operator's documents must never be committed. So the state branch stays
the only registry of record, and the operator carries it:

```bash
python -m vinci.theme_intelligence state pull --remote git@github.com:techmuns/mosaic-theory.git
python -m vinci.theme_intelligence ingest-file --path report.pdf --source ms_research --llm-permitted
python -m vinci.theme_intelligence state push
```

- `state pull` rebuilds the local registry from the branch (the local one backed up first), then
  REPLAYS every local document the branch does not hold yet from its private copy, through the same
  pipeline (an unchanged document's model calls come from the LLM cache). It refuses — unless
  `--force`, with the backup kept — to discard a local scan or article run it cannot replay.
  **Nothing paid is lost or counted twice.** Every run the branch lacks is carried into the
  rebuilt registry for its RECORD — run id, times, cost and every paid-call row, unchanged —
  marked `ledger_only` (its evidence is the replay's, which names it in `replay_of`, or was
  discarded by `--force`); the weekly report never counts a carried run. The pull then checks
  the paid-call ledger — every record of the replaced registry and of the branch present
  exactly once at the same cost, or it fails loud — and prints it (`paid-call ledger: N
  call(s), $X`). A replay keeps the ORIGINAL ingestion dates (upload time, the article's and
  thesis's first ingestion) and adds no article text to the branch. A local run whose id names a
  different run on the branch (a second-resolution id can repeat) is refused; `--force` pulls
  without carrying it, says so with its cost, and leaves its record in the backup.
- `state push` exports the registry WITHOUT article text, refuses a tree holding anything but
  derived JSONL (no PDF, page, database or article text), and is FAST-FORWARD ONLY: if the
  scheduled run committed since your pull, it refuses — pull again (the replay is safe), then
  push. Credentials are git's own; a printed URL is masked.
- The next scheduled scan restores that registry and its weekly report includes the uploads. On
  the runner the original documents are absent, and every surface says so: the intake list marks
  the original as not on that machine, and QA counts a claim whose text is not held as "not
  re-checkable here" — never re-verified.

| where | what runs |
|---|---|
| this machine | `ingest-file`, `ingest-inbox`, `documents`, `state pull/push/status`, `article`, `scan`, `report`, `qa` |
| GitHub Actions | the weekly `scan` (restore → gate → scan → QA → export → commit to the state branch); manual documents arrive only through a `state push` |
| needs configuration | the `theme-intelligence-state` branch exists only after the first workflow run or the first `state push` (none yet); the cron needs `THEME_INTELLIGENCE_SCHEDULE_ENABLED=true`; a push needs the operator's git credentials for the repository; secure cloud document storage is NOT configured — originals stay on the operator's machine |

**Local / server — `bin/theme-intelligence-weekly`.** Runs the same pipeline against
`data/theme_intelligence/registry.db`, takes a dated backup first, appends to
`data/theme_intelligence/weekly.log`, and exits 0 / 2 / 1 as above. It installs nothing. To schedule
it (Monday 08:30 in Asia/Kolkata):

```bash
crontab -e
```

```text
CRON_TZ=Asia/Kolkata
30 8 * * 1 cd /path/to/mosaic-theory && bin/theme-intelligence-weekly
```

or a launchd agent (`~/Library/LaunchAgents/com.mosaic.theme-intelligence.plist`) whose
`ProgramArguments` is `bin/theme-intelligence-weekly`, `WorkingDirectory` the repo root, and
`StartCalendarInterval` `{Weekday 1, Hour 8, Minute 30}` in the machine's local time.

## Persistence, migrations, backups

- Registry: SQLite (WAL) at `data/theme_intelligence/registry.db` — its own namespace, never the
  fund's `data/vinci.db`. History tables (article versions, claims, mentions, resolutions, thesis
  versions, links, contributions, relations, events, snapshots, issues, LLM calls) are append-only:
  UPDATE and DELETE abort at the database level. An id can never mean two things.
- Migrations: numbered, append-only (`store.MIGRATIONS`); a fresh or older registry migrates on
  open; code refuses to open a registry NEWER than itself.
- Backups: `backup` (consistent SQLite copy); `export-state` / `import-state` for a portable,
  diff-able JSONL copy (article text excluded).

## Secrets

Read from the environment only — locally from the git-ignored `.env` via `vinci.config
.load_local_env()`, on Actions from repository secrets. Never printed, never committed. Without
`ANTHROPIC_API_KEY`, `article` and `report` still work from cache, and `scan` refuses to start
rather than producing an analysis-free week.

## LLM operations

Model and prompt versions are pinned in `vinci/theme_intelligence/config.py` and written into every
extraction, version and manifest. The model is `claude-opus-4-8` because the repo's existing client
(`vinci.graph.llm.AnthropicLlmClient`) forces a tool call, which the newer Opus 5.5 / Fable 5.1 /
Sonnet 5.5 models reject — and changing the shared client would touch every fund LLM phase. Pass 1
(extraction) and pass 2 (independent card review) are cached by content hash. Article text reaches
the model inside `<untrusted_article>` and is treated as data; the tool schema has no field a trade
could ride on. Measured costs (list price, 2026-10-10, all passes — extraction, completeness, card
reviews): a J.P. Morgan article ≈ $0.68; a TrendForce release ≈ $0.88; a long SemiAnalysis preview
≈ $1.24, or $1.35 when one answer had to be set aside and asked again. A cached answer costs
nothing. Long research PDFs cost far more: see *Manual documents → Cost* ($3.80 to $46.67
measured for three Citi reports).

- **Long articles.** An extraction that overruns the output cap (21,333 tokens, the SDK's
  non-streaming ceiling) is retried ONCE in a declared COMPACT mode — at most 25 claims, issue
  `EXTRACTION_COMPACT` — and the overrun is remembered, so a replay never pays for it twice. The
  completeness pass then reviews the article's open gaps in PARTS of at most 50
  (`COMPLETENESS_IN_PARTS`), each part shown what the earlier parts added. A part that overruns is
  split once into halves, with the discarded call recorded at its cost; a half that overruns again
  fails loud.
- **Malformed answers.** The model's answer is validated ITEM BY ITEM: a claim, mention, thesis or
  review that fails its schema is dropped and named (`MALFORMED_ITEM_DROPPED`, WARN) — never
  coerced into a guessed value — and every valid item is kept. The paid answer is cached before it
  is validated. A malformed top level (not an answer at all) still fails the article loudly.
- **Verification checks, corrected where the CHECK was wrong (2026-10-11).** A decline stated in
  words beside a figure supplies its minus ("down ~27%" verifies as -27; "fell to 4%" is a level
  and does not); a figure written with an ellipsis ("12 ... 30 or more") verifies when every
  piece is verbatim, in order; a figure RESTATED in a chart caption, table or summary is captured
  where the article states it — only when the completeness pass names that claim, it is verified,
  and the three words beside the figure share a content word (or the same precise number is
  written with the same unit). The same fact in different words stays OPEN for a human; a shared
  number alone is never identity. On Citi's Gridlock report open figures fell 17 → 6 of 851, on
  its ETF report 5 → 1 of 232, from cached answers; what stays open is listed with its cause.

## Limitations (also in the PR)

- Morgan Stanley and Goldman Sachs refuse the honest User-Agent — BLOCKED, never bypassed. Their
  research reaches clients through entitled portals and licensed distribution (not probed or
  configured here); the dependable route is an entitled operator's `ingest-file`.
- Bank of America is retired (2026-10-11): its history is kept, nothing new is read or accepted.
- SemiAnalysis paid posts expose a preview only — PARTIAL, and by decision (2026-10-13, no
  subscription) never requested: the preview is all this channel gives. A page that LINKS a fuller
  report is still requested (`linked_reports`).
- Nomura was retired on 2026-10-13: its full reports sit on its client portal (no public sign-up).
- No OCR: a scanned page is flagged and the document PARTIAL; chart values are not read.
- A figure-dense research PDF is expensive through the full pipeline ($46.67 measured for one
  60-page report) — held above the per-document limit until the operator raises it. The spend
  guard bounds every call before it is sent; it is a conservative bound from the request's size,
  not a provider-side billing cap. The article prompt cache that would cut a long review's cost
  (one measured run: -45%) ships OFF until its evidence quality is shown equivalent.
- Identity matching across formats is by text overlap: a heavily reformatted copy can fall to
  REVIEW, which a human resolves; nothing merges on a guess.
- State sync was demonstrated against the real private repository on a TEMPORARY branch
  (`theme-intelligence-state-test-20261011`, synthetic registry); the PRODUCTION state branch
  does not exist yet — the first scheduled run (after merge, once enabled) creates it.
- Point-in-time listings rest on the issuer's cover-page tagging (required since 2019); a filing
  without tagged cover facts leaves the listing UNVERIFIED, so it never counts as an exposure.
  Fiscal-year windows ("FY27") are read as the calendar year — approximate, and said so.
- Consensus, market expectations and valuation are NOT_ASSESSED: the tool holds no such data.
- The completeness pass and the card review are LLM judgements, checked deterministically where
  they can be (every addition re-verified; an "immaterial" verdict needs a reason; a re-anchored
  line is re-reviewed) — their open gaps are listed, not resolved by fiat.
