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

- `dashboard.html` / `.md` / `.json` / `.csv` — the weekly decision page: run status, window,
  sources checked / failed, articles read, queued, themes created / updated, RESEARCH NOW / WATCH /
  SKIP totals, retrieval caveats; then six categories in a fixed order — new, upgraded, downgraded,
  challenged, unchanged but material, archived — each always printed with its count ("showing X of
  Y" when collapsed); then a searchable archive of every thesis.
- `cards/<THESIS_ID>.html` (web: header + 01/02/06/08 open, 03/04/05/07/09 on demand),
  `.print.html` (everything open), `.md`, `.json` — the same nine sections in the same order, all
  rendered from the stored `ThesisVersion`.
- `report_print.html` — the dashboard plus every card that changed, fully expanded.
- `validation_log.json` — every verification issue (BLOCK / HOLD / WARN / INFO).
- `manifest.json` — window, as-of, status, runtime, fetch / LLM seconds, model and prompt versions,
  tokens, cost, per-source coverage, warnings, output list.

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
could ride on. Measured costs: the J.P. Morgan article ≈ $0.53 (extraction + three card reviews);
the 2026-10-10 capped scan ≈ $0.84 for three articles.

## Limitations (also in the PR)

- Morgan Stanley and Goldman Sachs refuse the honest User-Agent — BLOCKED, never bypassed.
- BofA insight pages carry no publication date — UNDATED, never placed in a window.
- SemiAnalysis paid posts expose a preview only — PARTIAL, never analysed as full text.
- The SEC ticker map is current, not point-in-time; every resolution says so on replay runs. A
  registrant with several tickers lists all of them, because the map does not state security type.
- Consensus, market expectations and valuation are NOT_ASSESSED: the tool holds no such data.
