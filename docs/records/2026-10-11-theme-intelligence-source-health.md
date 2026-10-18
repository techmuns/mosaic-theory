---
id:
status: shipped
date: 2026-10-11
prs: [703]
supersedes:
superseded-by:
---

# Theme intelligence source health — every publisher channel checked cheaply for silent failure, its history kept, its state shown apart from the scan's

**WHAT.** Priority 1A, in `vinci/theme_intelligence/` (research attention only, off the decision
path):

- **`health.py`** — a bounded, LLM-free check per channel, run by
  `python -m vinci.theme_intelligence sources --check-health [--json] [--force] [--sources …]` and
  at the start of EVERY scan, scheduled or manual. Seven tests: access (the endpoint discovery starts
  from, under robots.txt and the honest User-Agent), discovery (the channel's own adapter), extraction
  (up to three articles spread across the listing), dates and bylines (each page's own, the
  listing's, and the latest scan's undated share), completeness (full / paywalled preview /
  partial, and the latest scan's outcomes), freshness (newest dated article vs the window; URLs new
  since the last check) and parser integrity (a 200 page whose body is not read, or the SAME page
  reading far shorter than at an earlier check). One status — HEALTHY / DEGRADED / BLOCKED / ERROR /
  UNKNOWN — never "healthy" because a page answered 200; freshness (FRESH / QUIET / UNKNOWN) kept
  apart, so a quiet week is not an unhealthy channel.
- **Politeness.** A 401 / 403 / 451 is never retried and a refusing channel is not re-requested for
  24 hours (`--force` overrides); a robots.txt that cannot be read fails CLOSED, visibly; the
  channel's crawl-delay floor applies on every host it is read from; the scan's discovery reuses
  the check's live fetch, and a channel the check found refused is recorded BLOCKED without a
  second request.
- **History** — migration v3, an append-only `source_health` table, exported with the registry so
  the scheduled job's state branch carries it across restarts. Each row: status and exact reason,
  the seven test results, last checked, last successful discovery, last successful full-text
  extraction, last verified publication date, discovered / dated / in-window counts, the sampled
  articles, the latest scan's full / preview / undated / unreadable counts, consecutive failed
  checks, status since, what changed since the previous check, the alert and what the hook did.
- **Changes and alerts.** HEALTHY → DEGRADED / BLOCKED, extraction → parser failure, a drop to zero
  discovered articles on an accessible page (flagged for review, never read as "published
  nothing"), dates missing at consecutive checks, a BLOCKED channel accessible again. NEW_FAILURE
  on a change into a failing state, RECOVERED on an improvement, one PERSISTENT_FAILURE reminder at
  three checks, then nothing until it changes; `expect_blocked` makes a standing refusal a
  KNOWN_RESTRICTION (shown, not re-alerted) — its status stays BLOCKED. A hook command named by
  `THEME_INTELLIGENCE_HEALTH_HOOK` receives alerts as JSON on stdin; none is required.
- **Manual review / upload.** A failing channel carries an UPLOAD_REQUIRED or MANUAL_REVIEW item:
  publisher, issue, the affected article as discovered (URL and the listing's own title — never an
  invented one), the action. `article --url … --html <saved page>` is the upload route through the
  SAME pipeline, now labelled a manual upload in the article's provenance; it never changes the
  channel's health. The item is lifted when automatic retrieval is shown to work again; uploaded
  articles stay.
- **Dashboard** — a compact "Research source health" block: `Sources healthy: X/8 | Degraded: Y |
  Blocked: Z | Errors: N`, new changes in a banner, only the channels needing attention (reason,
  action, affected article), and all eight with their last successful checks on demand; in the md,
  json and manifest too, and in the scan's CLI output — apart from execution status and research
  verification. No stack traces: reasons are composed sentences (an exception is named by type).
- QA: a scan from schema v3 must have a health record for every channel it covered.

**WHY.** A channel that silently stops yielding articles — a layout change, an expired paywall
treatment, undated pages — reads exactly like a quiet week, and the weekly brief loses coverage
without saying so. Scan execution status (did the run complete?) and research verification (is
what it read accounted for?) do not answer "is each publisher still being read?".

**HOW VERIFIED.** CORPUS FIRST — the check was run against the eight live publishers before the
synthetic tests were believed, and the live runs changed the design three times:

- *Live run 1 (one sampled article per channel):* 6 HEALTHY / 2 BLOCKED. WRONG: the last real
  scan counted 12 of 16 Bank of America pages undated, and most SemiAnalysis posts are previews —
  one sample (the newest page / free post) hid both. → up to three samples.
- *Live run 2 (three samples, top of the listing):* SemiAnalysis DEGRADED (2 of 3 previews), Nomura
  DEGRADED (a page summarising a linked report), Citi DEGRADED — one page answered 200 with ~7,300
  characters of visible text in 14 paragraphs and the parser read 0 words: a TRUE parser gap. But
  Bank of America still HEALTHY: its first three entries are one dated series. → samples spread
  across the listing (first, middle, last) and the latest scan's undated share counted as date
  evidence.
- *Live re-check two minutes later:* Citi's 96-word teasers flagged as "extraction collapsed"
  against a 570-word DIFFERENT article read the check before — a false positive. → collapse is
  judged only against the same page's earlier reading.
- *Final live runs (registry `health-4`, 2026-10-11 08:28–08:30 UTC, the final code):* first check
  `Sources healthy: 2/8 | Degraded: 4 | Blocked: 2 | Errors: 0` — J.P. Morgan and TrendForce
  HEALTHY; Citi DEGRADED (2 of 3 sampled pages short teasers), Bank of America DEGRADED (metadata
  problem: 2 of 3 sampled pages undated on page and listing), Nomura DEGRADED (1 of 3 summarises a
  linked report), SemiAnalysis DEGRADED (1 of 3 a paywalled preview); Morgan Stanley BLOCKED
  (robots.txt unreachable — fail closed, nothing fetched), Goldman Sachs BLOCKED (HTTP 403). Second
  check (`--json`): Morgan Stanley and Goldman Sachs NOT re-requested (refused < 24h ago), failure
  streaks continued (consecutive 2), Bank of America "publication dates missing at 2 consecutive
  checks", no alert repeated, no false parser failure.
- *Weekly scan with the check at its start (registry `weekly-17`, run `R-20261011T083033Z-scan`, window
  2026-10-01 → 10-10, as of 10-10):* health checked first — `2/8 | Degraded: 4 | Blocked: 2`, as the
  standalone check; Morgan Stanley and Goldman Sachs recorded BLOCKED from the check's reason with NO
  second request; the other six discovered and processed as before (6 articles, 10 theses, Research
  Now / Watch / Skip 2 / 7 / 1); scan execution SUCCEEDED, research verification INCOMPLETE (paragraph
  b008); QA 21/22 — the new "source health recorded for every scanned channel" passes, 8 of 8;
  $0.00 (every model answer cached). Worked output: `docs/theme_intelligence/weekly-with-source-health-2026-10-11/`.
- *Tests:* `tests/test_theme_intelligence_source_health.py` (26 items) — H.1–H.13 against a scripted
  web (httpx MockTransport, every request counted): all eight channels get a status and a
  timestamp; a working listing with a broken article parser; 403 BLOCKED and never retried (and not
  re-requested within 24h); an unreadable robots.txt (connection error, 503) fails closed with
  nothing else fetched; a paywalled preview DEGRADED, not full; a quiet channel HEALTHY / QUIET;
  missing dates a visible metadata problem; HEALTHY → BLOCKED raises a change; BLOCKED → accessible
  detected and the upload item lifted; a manual upload processed while the channel is BLOCKED, its
  health unchanged; one failing channel (a broken adapter, a crashed check, a refusal) never stops
  the others, in a check and in a scan, and a refused channel is never asked twice; the health
  module's transitive imports contain no LLM module and the CLI runs with no API key; history
  survives export → import; plus expect_blocked, alert dedupe via a real hook, the dashboard block,
  the live-run regressions (spread sample, scan evidence, same-page collapse) and the append-only
  triggers. `test_theme_intelligence_scan.py` stubs the health check and now REFUSES any live
  request (a BaseException the scan cannot swallow).
- *Mutation:* 24 of 24 guards killed (two first survived and were fixed by stronger tests: the
  check's own fail-closed wording, and a crash past the adapter); round 3's 27 still 27 of 27.
- *Gate on the final code:* `ruff check .` clean; `mypy --strict vinci` clean (177 files);
  `pytest -m "not network"` 4,650 passed, 508 skipped, 37 deselected, 0 failed. The one new skip
  is the store's parametrised append-only case for `source_health` (its fixture runs no health
  check) — the triggers are pinned in the health tests instead.
- *Found on the way, fixed:* the existing scan tests stubbed discovery but not the new health
  check, so they reached the eight LIVE publishers (minutes of crawl delays) — now stubbed, and
  that test module refuses any live request.

**BOUNDARY.** Code commit `83193559` (the final live runs `health-4` and `weekly-17` ran on its
check code; only a dashboard column label changed after them, and the worked output was
re-rendered from `83193559`). Live checks: 2026-10-11 between 08:03 and 08:31 UTC from this
laptop, the honest User-Agent, registries `health-1` … `health-4` and `weekly-17` (fresh each;
the shared page cache reused only within 15 minutes); "window" = the 10 days ending the check date, used only for
freshness; "sampled" = at most three article pages per channel, spread across what discovery
returned. Discovery counts are what each adapter returned in that check (unique canonical article
URLs). No model call is made by any check.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- No LLM spend. Each check is about 2–6 requests per reachable channel (robots, listing page(s),
  three articles) plus crawl delays — a few minutes for the eight.
- Three samples are a sample: a channel whose few bad pages miss the sample reads HEALTHY. The
  latest scan's undated and preview counts partly cover this (the scan reads every candidate).
  Falsifier: a scan finds undated or preview pages on a channel the check last called HEALTHY.
- DEGRADED is broad by the brief's definition: a short teaser page, a page summarising a linked
  report and a paywall all count as partial extraction. Citi, Nomura and SemiAnalysis are DEGRADED
  for that reason, not because anything broke; the reason says which.
- The first live run used the default 5-second spacing instead of the channel's configured floor
  (up to 10 seconds) for one or two requests per host before that was fixed; robots Crawl-delay
  was honoured throughout.
- Uploads are saved HTML pages: no PDF library is installed, and adding one was not built
  speculatively.
