# Theme intelligence — operator guide

`vinci/theme_intelligence/` is a **research discovery and prioritisation** tool. It reads permitted
public research pages from eight publisher channels, extracts their source-anchored evidence, named
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
| `scan --days N` / `scan --from D --to D` | discover the window on all eight channels, analyse up to `--max-articles` (default 25; the rest are QUEUED and offered first next run), write the readout |
| `scan --resume RUN_ID` | continue an interrupted scan with its ORIGINAL window and as-of; nothing is processed twice |
| `article --url U --as-of D` | analyse one URL as of a date (publication-time replay: a later-published article is refused, a later-dated figure is blocked) |
| `report --latest` / `--week 2026-10-05` or `2026-W41` / `--run RUN_ID` | re-render the dashboard and every card from the registry |
| `qa --run RUN_ID\|latest` | re-check a run's stored records without any LLM (spans, figures, look-ahead, card facts, section order, hashes, triggers, coverage, render consistency) |
| `backup` · `export-state --out D` · `import-state --src D` | consistent SQLite copy · append-only JSONL export (no article text) · rebuild a fresh registry from an export |
| `sources` | print the eight configured channels |

Common flags: `--data-dir` (default `data/theme_intelligence`), `--cache-only` (never call the
LLM: replay cached extractions only), `--no-review` (skip the pass-2 LLM review — the card then
says the review did not run). Exit status: **0** succeeded · **2** PARTIAL (a source or article
could not be read; the readout says which) · **1** failed.

## What a run writes

`data/theme_intelligence/runs/<RUN_ID>/` (git-ignored; `runs/LATEST` names the newest):

- `dashboard.html` / `.md` / `.json` / `.csv` — the weekly decision page: run status, window, and
  a KPI strip in plain words — *Accessible sources: 6 of 8*, *Blocked sources: Morgan Stanley,
  Goldman Sachs*, *Articles analyzed: N full · M partial*, *Research Now / Watch / Skip*, *New /
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
  drawdown) stays a market risk — never a record of either kind.
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
- **Exposure.** RESEARCH NOW needs a source-named exposure: a point-in-time-verified listed common
  equity OR a sector / theme the source names (a verified span containing the name). A sector
  opportunity needs no ticker. A company's role as the SOURCE states it (e.g. capex spender) is
  kept apart from the THESIS's reading of it (e.g. potential beneficiary), each labelled.
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
- **Authors.** The union of every place the page credits one — JSON-LD, schema.org/Person
  microdata, meta author, the visible byline (multi-line titles joined) — plus people the article
  TEXT credits ("team led by …") as verified spans. A JSON-LD list that omits an author credited
  elsewhere on the page is recorded as AUTHOR_METADATA_DISCREPANCY; declared alternate language
  versions (hreflang) are recorded (none of the eight channels' article pages declares one).

## The eight channels (editable: `vinci/theme_intelligence/config/sources.toml`)

Access as probed on 2026-10-09/10 with the honest research User-Agent (no browser spoofing, robots.txt
honoured per RFC 9309, a robots.txt that cannot be fetched fails CLOSED):

| channel | discovery | state |
|---|---|---|
| Citi Must C | the page's embedded CMS data (`__NEXT_DATA__`): series items + CMS publishDate | OK — the page embeds its ~20 linked items; older ones are not listed there |
| BofA institutional insights | article cards on the insights page | OK, but the insight pages state **no publication date**, so they are counted UNDATED and never placed in a window (analyse one with `article --url`) |
| J.P. Morgan Top Market Takeaways | listing cards with dates (sitemap lastmod as a fallback that can only rule a page OUT) | OK |
| Morgan Stanley Research | entry page links | **BLOCKED** — the connection is dropped on every request, robots.txt included; reported every run, never bypassed |
| Nomura Connects | `/articles/` + pagination, each page's own date | OK |
| TrendForce press center | listing pages `?page=N`, date in the article URL | OK |
| SemiAnalysis | the newsletter's RSS feed (pubDate) | OK — paid posts carry a preview only and are recorded PARTIAL |
| Goldman Sachs Research | entry page links | **BLOCKED** — HTTP 403 on entry, sitemap and insights |

`expect_blocked = true` marks MS and GS as standing refusals: still attempted and reported BLOCKED
every run, but they do not by themselves turn a run PARTIAL. Any other channel that fails does.

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
nothing.

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

## Limitations (also in the PR)

- Morgan Stanley and Goldman Sachs refuse the honest User-Agent — BLOCKED, never bypassed.
- BofA insight pages carry no publication date — UNDATED, never placed in a window.
- SemiAnalysis paid posts expose a preview only — PARTIAL, never analysed as full text.
- Point-in-time listings rest on the issuer's cover-page tagging (required since 2019); a filing
  without tagged cover facts leaves the listing UNVERIFIED, so it never counts as an exposure.
  Fiscal-year windows ("FY27") are read as the calendar year — approximate, and said so.
- Consensus, market expectations and valuation are NOT_ASSESSED: the tool holds no such data.
- The completeness pass and the card review are LLM judgements, checked deterministically where
  they can be (every addition re-verified; an "immaterial" verdict needs a reason; a re-anchored
  line is re-reviewed) — their open gaps are listed, not resolved by fiat.
