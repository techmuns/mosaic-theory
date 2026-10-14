## Summary

A new, isolated package **`vinci/theme_intelligence/`**: a research discovery and prioritisation tool. It:
- reads permitted public research pages from eight publisher channels;
- extracts source-anchored evidence, named companies and risks;
- keeps a persistent **versioned registry of theses**;
- writes a decision-first **weekly dashboard** of nine-section **Living Thesis Cards**.

**"RESEARCH NOW" means allocate analyst attention — never buy.**

The package stays off the fund's decision path (unchanged by this update):
- no fund module imports it; it imports only `vinci.config`, the existing LLM client and the HTTP cache (AST-pinned);
- its own SQLite registry under `data/theme_intelligence/`;
- no buy / sell / target / weight field anywhere (schema-walk-pinned);
- its priority rules are face-validity constants that read no prices, returns or outcomes.

**Priority 1A (this update) adds source health monitoring** — see the next section. **Round 3 answered the review of 2026-10-11** — no false contradictions, no over-broad confirmation, a narrow near-term-inflection route, QA honesty, three dates — see the next section. **Round 2 answered the review of 2026-10-10** ("the architecture is accepted, the analytical acceptance criteria have NOT yet been met"):
- **Code:** all corrections are inside `vinci/theme_intelligence/`.
- **Changed outside the package:** `STATE.md` (the §2 line and §5.0 row 32 item 8), `docs/engineering.md` (glossary), `docs/theme_intelligence.md` (operator guide), `docs/records/` (a new record and an amendment to the first), tests, fixtures and the worked output.
- **Untouched:** fund screen / ranker / dossier / verdict / scoring / valuation / ledger / portfolio / trading / historical-alpha-audit code.
- **Branch hygiene:** main's #704 is merged in; the only conflict was STATE.md row 32, resolved by keeping both sides.

Guide: `docs/theme_intelligence.md` · Records: `docs/records/2026-10-10-theme-intelligence.md` (build), `docs/records/2026-10-10-theme-intelligence-review-corrections.md` (round 2), `docs/records/2026-10-11-theme-intelligence-review-round-3.md` (round 3), `docs/records/2026-10-11-theme-intelligence-source-health.md` (source health) · Worked output: `docs/theme_intelligence/`

---

## Priority 1A — Source health monitoring (this update)

**Why:** a channel that silently stops yielding articles reads exactly like a quiet week. Scan execution status (did the run complete?) and research verification (is what it read accounted for?) don't answer "is each publisher still being read?". This adds a third, separate status.

**Commits:** code `83193559`; live demonstration, record, guide and STATE `9b91cef7`.
**Record:** `docs/records/2026-10-11-theme-intelligence-source-health.md` · **Guide:** `docs/theme_intelligence.md` § Source health monitoring.

### What it does

The check is bounded, makes no LLM call, and is never "healthy" just because a page answered HTTP 200. It runs on demand with `python -m vinci.theme_intelligence sources --check-health [--json] [--force] [--sources …]`, and at the start of every scan, scheduled or manual.

**The seven tests, per channel**
1. **Access:** the endpoint discovery starts from, under robots.txt and the honest User-Agent.
2. **Discovery:** the channel's own adapter finds genuine article URLs, with titles and listing dates.
3. **Extraction:** up to three articles, spread across the listing, are fetched and parsed.
4. **Dates and bylines:** each sampled page's own date and byline, the listing's dates, and the latest scan's undated share.
5. **Completeness:** full text, paywalled preview, or partial page.
6. **Freshness:** the newest dated article against the window, and URLs new since the last check. A quiet channel is QUIET, not unhealthy.
7. **Parser integrity:** a 200 page whose body isn't read, or the *same* page reading far shorter than at an earlier check.

**Status:** exactly one per channel: HEALTHY / DEGRADED / BLOCKED / ERROR / UNKNOWN. `expect_blocked` only changes the alert class; the status stays BLOCKED.

**Politeness**
- A 401/403/451 is never retried, and the channel isn't re-requested for 24 hours (`--force` overrides).
- An unreadable robots.txt fails closed, and says so.
- The channel's crawl-delay floor applies on every host it is read from.
- The scan's discovery reuses the check's live fetch, and records a refused channel BLOCKED without asking twice.

**History:** migration v3 adds an append-only `source_health` table, exported with the registry so it survives the scheduled job's restarts. Each row records:
- status and exact reason, plus all seven test results;
- last checked, last successful discovery, last successful full-text extraction, last verified publication date;
- articles discovered and in the window, and the latest scan's full / preview / undated / unreadable counts;
- consecutive failed checks, status since, what changed since the previous check, and the alert.

**Changes and alerts**
- **Detected changes:** HEALTHY → DEGRADED / BLOCKED; extraction → parser failure; a drop to zero discovered articles (flagged for review, never read as "published nothing"); dates missing at consecutive checks; a BLOCKED channel accessible again.
- **NEW_FAILURE / RECOVERED** fire on a change of state.
- **PERSISTENT_FAILURE** fires once, when a failure reaches three checks; then nothing until it changes.
- **Known standing restrictions** are shown but not re-alerted.
- **Delivery:** optional. Set `THEME_INTELLIGENCE_HEALTH_HOOK` to a command and it receives alerts as JSON on stdin.

**Manual review / upload:** a failing channel carries an UPLOAD_REQUIRED or MANUAL_REVIEW item. It names the publisher, the issue, the affected article as discovered (its URL and the listing's own title, never an invented one) and the action.
- **Upload route:** `article --url … --html <saved page>`, through the same pipeline, now labelled a manual upload in the article's provenance.
- An upload never changes the channel's health.
- The item is lifted once automatic retrieval works again; uploaded articles stay.

**Dashboard:** a compact "Research source health" block, `Sources healthy: X/8 | Degraded: Y | Blocked: Z | Errors: N`.
- New changes appear in a banner.
- Below it, only the channels needing attention, each with reason and action.
- All eight, with their last successful checks, sit on demand.
- The same block is in the md, json, manifest and scan CLI output. No stack traces.

### Live demonstration, the eight real publishers (2026-10-11, final code)

`python -m vinci.theme_intelligence sources --check-health`, full output in `docs/theme_intelligence/weekly-with-source-health-2026-10-11/health-check-1.txt`:

```
Sources healthy: 2/8 | Degraded: 4 | Blocked: 2 | Errors: 0

  Citi                       DEGRADED  QUIET    checked 2026-10-11T08:28  partial: 2 of 3 sampled article(s) partial (short body (96 words) — treated as a teaser / excerpt)
  Bank of America            DEGRADED  QUIET    checked 2026-10-11T08:28  metadata problem: 2 of 3 sampled article(s) carry no publication date on the page or the listing …
  J.P. Morgan Private Bank   HEALTHY   FRESH    checked 2026-10-11T08:28  discovery, a full-text article, its date and byline all read
  Morgan Stanley             BLOCKED   UNKNOWN  checked 2026-10-11T08:28  robots.txt unreachable (RemoteProtocolError) — FAIL CLOSED, nothing fetched …
  Nomura                     DEGRADED  FRESH    checked 2026-10-11T08:28  partial: 1 of 3 sampled article(s) partial (the page summarises a fuller report it links to …)
  TrendForce                 HEALTHY   FRESH    checked 2026-10-11T08:29  discovery, a full-text article, its date and byline all read
  SemiAnalysis               DEGRADED  FRESH    checked 2026-10-11T08:29  partial: 1 of 3 sampled article(s) are paywalled previews — only the preview is readable
  Goldman Sachs              BLOCKED   UNKNOWN  checked 2026-10-11T08:29  https://www.goldmansachs.com/insights/goldman-sachs-research/: access denied (HTTP 403)
```

`--json`, run two minutes later; full output in `health-check-2.json`:
- Morgan Stanley and Goldman were not re-requested.
- Failure streaks continued.
- Bank of America reports "dates missing at 2 consecutive checks".
- No alert was repeated.

Excerpt:

```json
{
 "summary": "Sources healthy: 2/8 | Degraded: 4 | Blocked: 2 | Errors: 0",
 "counts": {
  "BLOCKED": 2,
  "DEGRADED": 4,
  "ERROR": 0,
  "HEALTHY": 2,
  "UNKNOWN": 0
 },
 "checked_at": "2026-10-11T08:30:04.597764+00:00",
 "skipped": {
  "gs_research": "not re-requested: access was refused at 2026-10-11 08:29 UTC; next re-test after 2026-10-12 08:29 UTC (or pass --force)",
  "ms_research": "not re-requested: access was refused at 2026-10-11 08:28 UTC; next re-test after 2026-10-12 08:28 UTC (or pass --force)"
 },
 "sources (2 of 8 shown)": [
  {
   "source_id": "bofa_institutional",
   "status": "DEGRADED",
   "reason": "metadata problem: 2 of 3 sampled article(s) carry no publication date on the page or the listing — undated articles are never placed in a window (1 of 3 sampled page(s) state a publication date; the listing dates 0 of 16; 1 of 3 carry a byline)",
   "freshness": "QUIET",
   "checked_at": "2026-10-11T08:29:36.452941+00:00",
   "last_successful_discovery": "2026-10-11T08:29:36.452941+00:00",
   "last_successful_extraction": "2026-10-11T08:29:36.452941+00:00",
   "last_verified_publication_date": "2026-06-25",
   "discovered": 16,
   "consecutive_failed_checks": 2,
   "manual_upload_recommended": false,
   "changes": [
    "publication dates missing at 2 consecutive checks"
   ],
   "alert": ""
  },
  {
   "source_id": "gs_research",
   "status": "BLOCKED",
   "reason": "https://www.goldmansachs.com/insights/goldman-sachs-research/: access denied (HTTP 403)",
   "freshness": "UNKNOWN",
   "checked_at": "2026-10-11T08:29:20.607492+00:00",
   "last_successful_discovery": null,
   "last_successful_extraction": null,
   "last_verified_publication_date": null,
   "discovered": 0,
   "consecutive_failed_checks": 1,
   "manual_upload_recommended": true,
   "changes": [
    "first check of this channel"
   ],
   "alert": "KNOWN_RESTRICTION"
  }
 ]
}
```

**The weekly scan** (window 2026-10-01 → 10-10, as of 10-10; `weekly-with-source-health-2026-10-11/`):
- Health is checked first.
- Morgan Stanley and Goldman are recorded BLOCKED from the check's reason, with no second request.
- The other six are processed as before.
- Scan execution SUCCEEDED; research verification INCOMPLETE (one paragraph open).
- QA 21/22: the new "source health recorded for every scanned channel" check passes, 8 of 8.
- Cost $0.00 (all model answers cached).

![dashboard with source health](https://github.com/techmuns/mosaic-theory/blob/claude/theme-intelligence/docs/theme_intelligence/screenshots/weekly-dashboard-source-health.png?raw=true)

The block alone, with all eight publishers expanded:

![source health expanded](https://github.com/techmuns/mosaic-theory/blob/claude/theme-intelligence/docs/theme_intelligence/screenshots/source-health-block-expanded.png?raw=true)

### What the live runs changed (corpus before synthetic)

**Run 1 — one sampled article per channel:** 6 HEALTHY, 2 BLOCKED, which was **wrong**.
- The last real scan counted 12 of 16 Bank of America pages undated, and most SemiAnalysis posts are previews.
- One sample (the newest page, or a free post) hid both.
- Fix: three samples.

**Run 2 — three samples from the top of the listing:** SemiAnalysis, Nomura and Citi became DEGRADED.
- Citi's flag is a true parser gap: one page has about 7,300 characters of visible text in 14 paragraphs, and the parser reads 0 words.
- Bank of America was still HEALTHY, because its first three entries are one dated series.
- Fix: spread the samples across the listing, and count the latest scan's undated share as evidence.

**Re-check two minutes later:** Citi's 96-word teasers were flagged as "extraction collapsed" against a *different* 570-word article.
- Fix: judge collapse only against the same page.

**The scan tests:** they stubbed discovery but not the new check, so they reached the live publishers.
- Fix: the health check is stubbed there, and that test module now refuses any live request.

### Tests, mutation, gate

`tests/test_theme_intelligence_source_health.py` has 26 items, all run against a scripted web (httpx MockTransport, with every request counted).

| brief test | pinned by |
|---|---|
| 1 all eight get a status and last-checked time | `test_all_eight_channels_receive_a_status_and_a_last_checked_time` |
| 2 working homepage, broken article parser | `test_a_working_listing_with_a_broken_article_parser_is_detected`, `…same_page_read_far_shorter…` |
| 3 HTTP 403 → BLOCKED | `test_http_403_is_blocked_and_never_retried` (one request; not re-requested within 24h) |
| 4 robots.txt failure handled conservatively and visibly | `test_an_unreadable_robots_txt_…` (connection error and 503; nothing else fetched) |
| 5 paywalled preview DEGRADED, not FULL | `test_a_paywalled_preview_is_degraded_not_full`, `…judged_on_several_articles_not_one` |
| 6 accessible, zero new articles ≠ unhealthy | `test_an_accessible_channel_with_no_new_article_is_not_unhealthy` (HEALTHY, QUIET) |
| 7 missing dates → visible metadata problem | `test_missing_publication_dates_…`, `…spread_across_the_listing…`, `…latest_scans_undated_share…` |
| 8 working → blocked raises a change | `test_a_previously_working_channel_becoming_blocked_raises_a_change` |
| 9 blocked → accessible detected | `test_a_blocked_channel_becoming_accessible_is_detected` (RECOVERED; upload item lifted) |
| 10 manual ingestion continues while blocked | `test_manual_ingestion_continues_while_the_publisher_is_blocked` (processed; health unchanged) |
| 11 one failure can't stop the other seven | `test_one_channel_failing_never_stops_the_others` (broken adapter, crashed check, refusal), `test_a_scan_checks_health_first_and_never_asks_a_refusing_channel_twice` |
| 12 health checks never call the LLM | `test_health_checks_import_and_call_nothing_of_the_llm_pipeline` (transitive imports), `test_the_health_cli_runs_without_an_llm_key` |
| 13 status and history survive restarts | `test_health_history_survives_a_scheduled_restart` (export → import), `test_a_recorded_health_check_can_never_be_rewritten` |
| expect_blocked never conceals | `test_expect_blocked_never_conceals_a_blocked_channel` |
| alerts not repeated without a state change | `test_alerts_go_to_the_hook_once_per_change` (a real hook command) |

**Mutation:** 24 of 24 guard mutants were killed. Two survived at first and were closed with stronger tests:
- the check's own fail-closed wording;
- a crash past the adapter.

Round 3's 27 mutants are still 27 of 27.

**Gate (final code):**
- `ruff check .` clean;
- `mypy --strict vinci` clean (177 files);
- `pytest -m "not network"`: **4,650 passed**, 508 skipped, 37 deselected, 0 failed.

The one new skip is the store's parametrised append-only case for `source_health`, whose fixture runs no check; the triggers are pinned in the health tests instead. Main had no new commits.

### Limitations

- **Three samples are a sample.** The latest scan's counts (it reads every candidate) partly cover the gap. Falsifier: a scan finds undated or preview pages on a channel the check last called HEALTHY.
- **DEGRADED is broad, by the brief's definition.** A short teaser, a summary of a linked report and a paywall all count as partial. Citi, Nomura and SemiAnalysis are DEGRADED for that reason, not because something broke; the reason says which.
- **Uploads are saved HTML pages.** No PDF library is installed, and I didn't add one speculatively.
- **First live run spacing.** It used the default 5-second spacing instead of the channel floor (up to 10 s) for one or two requests per host, before that was fixed. The robots Crawl-delay was honoured throughout.
- **No email or chat integration.** The hook is the delivery seam.

### Priority 1A completion

| item | disposition | note |
|---|---|---|
| A — one status per publisher; freshness separate; never healthy on a bare 200 | SHIPPED | |
| B — the seven tests; bounded, no LLM; robots, rate limits; no repeated retry of a 403 | SHIPPED | |
| C — `sources --check-health` and `--json`, independent of the LLM pipeline | SHIPPED | the CLI runs with no API key |
| D — at the start of each scheduled and manual scan, on demand; persisted history; every listed field; separate from execution and verification | SHIPPED | "articles in the current window" is listing-dated in the check; the scan's own counts are beside it |
| E — change detection; silent failures flagged for review; prominent new failures; notification hook; no repeated alerts | SHIPPED | the hook is optional, no channel is required |
| F — other publishers keep scanning; MANUAL_REVIEW / UPLOAD_REQUIRED items; upload through the same pipeline; no invented titles; one upload ≠ coverage; recheck and lift | SHIPPED | the upload is saved HTML (no PDF library) |
| G — compact dashboard section, attention-only list, expandable all-eight, no stack traces, expect_blocked never conceals | SHIPPED | |
| H — acceptance tests 1–13 | SHIPPED | table above |
| CLI demonstration, JSON report, dashboard screenshot, regression tests in PR #703 | SHIPPED | above |
| Living Thesis Cards, priority rules, evidence system, fund-code isolation preserved | SHIPPED | no card, priority or evidence rule changed; the isolation tests pass |
| Do not merge | STOPPED here | awaiting review |

---

## Review round 3 (previous update) — what changed

All code changes are inside `vinci/theme_intelligence/` (commit `0b75b811`). The worked output, record and STATE are in `cd75a018`. The architecture, the nine-section card, the immutable history, source verification and fund-code isolation are unchanged. Record: `docs/records/2026-10-11-theme-intelligence-review-round-3.md`.

| fix | what changed |
|---|---|
| **1 — no false contradictions** | A challenge (COMPETING: evidence filed as CONTRADICTS, the incumbent re-versioned WEAKER) now needs a **direct contradiction**: the same node, mechanism and segment, overlapping geography and timeframe, and the opposite outcome. Any difference is named on the link and makes it **RELATED**: no CONTRADICTS evidence, no WEAKER version, no downgrade. Two unclassified (`other`) theses are never compared by key. |
| **2 — no over-broad confirmation** | The **segment** is now part of thesis identity: DRAM / HBM vs NAND / SSD on memory, grid-connected utilities vs behind-the-meter / on-site generation on power (`taxonomy.toml` `[[segment]]`). It is read from the verbatim evidence quotes, never from the model's wording. Evidence roles: **DIRECT_CONFIRMATION** and **REPEATED_SOURCE** reach a thesis's own history; **ADJACENT_SUPPORT** (same direction, not the same claim) and **RELATED** (opposite direction, not the same claim) are links only, never a strengthening or a weakening. **CONTRADICTION** is the only role that weakens. |
| **3 — a narrow RESEARCH NOW route** (F12 `fundamental_inflection`) | With no dislocation or dated catalyst, a thesis can still be RESEARCH NOW when **all** of these hold: (a) a verified claim's verbatim quote states a **change in a fundamental** (price, revenue, margin, demand, supply, shipments …), never a share-price move or a technical metric; (b) the change falls in the next 2–4 quarters, or was measured in the last one; (c) it is **credible**: either the publisher's own data in an industry data report (the article class comes from the channel, never the model) or corroborated by a measured change in the thesis's evidence — **never a forecast alone**; (d) the source states the fundamental step itself; (e) the source names an exposure, which turns it into a **research question** printed in the dashboard's first view. |
| **4 — QA honesty** | **Research verification** (FULLY_VERIFIED / VERIFIED_WITHIN_PREVIEW / INCOMPLETE) is shown **apart from scan execution** in the dashboard header and a tile, `dashboard.md` / `.json`, the manifest, the CLI and the QA summary. Every open item states its cause. The % unit rule now binds the number the value reads ("22 (52%)" read as 22 texts is a count). An account that names verified claims closes its paragraph. New QA check: no unverified claim is ever linked to a thesis. |
| **4, found by that check on real data** | The card reviewer had suggested two claims whose **number checks failed** as anchors for a partly supported bottom line (Nomura, weekly sample). Re-anchoring accepted them, so the line was not withheld and the claims were linked as context. Re-anchoring now accepts only claims verified on **span and number**, whoever proposes them. |
| **5 — point-in-time dates** | Cards and dashboard rows show **Published** (the latest source), **first ingested by the registry** (actual wall-clock UTC) and **analysed as of**. A historical replay says so ("a simulated date, not a detection"). The old "first detected by the registry <as-of>" label is gone. |

## Round 3 acceptance — real articles, fresh registries, final engine

Run 2026-10-10 19:15 UTC, registries `*-16`, model `claude-opus-4-8`, prompts unchanged (`ti-extract-6` / `ti-complete-1` / `ti-review-4`). Every folder is re-rendered from `0b75b811`.

| case | result | QA (execution · research verification) |
|---|---|---|
| **Software Shock** (J.P. Morgan, as of 2026-02-09) | exactly **three theses, all WATCH**; Alphabet = **GOOGL / GOOG** VERIFIED common equity point-in-time | 20/20 · SUCCEEDED · FULLY_VERIFIED (0 of 34 figures, 0 of 12 paragraphs open) |
| **Calm Index** (J.P. Morgan, 2026-10-02, as of 10-10) | the **utilities thesis and the dispersion market-regime record are both kept, both RESEARCH NOW**. The utilities id changed (`TH-98FD8D046C` → `TH-30F6348B8B`) because its identity now carries the grid-utilities segment | 20/20 · SUCCEEDED · FULLY_VERIFIED |
| **SemiAnalysis + J.P. Morgan** (no false weakening) | "Grid friction pushes datacenters behind-the-meter" (segment: on-site generation) **stays v1, WATCH**: no CONTRADICTS link, no CHALLENGED event. J.P. Morgan's utilities thesis is linked **RELATED** ("a different mechanism (demand_volume_shift vs policy_regulation); a different segment (Behind-the-meter / on-site generation vs Grid-connected utilities); no overlapping timeframe"). 0 challenges in the registry | SemiAnalysis (paywalled preview): 19/20 · PARTIAL · INCOMPLETE (1 paragraph, `no_account`). J.P. Morgan: 20/20 · SUCCEEDED · FULLY_VERIFIED |
| **SemiAnalysis + TrendForce** (direct vs adjacent) | "Sparse attention does not reduce overall AI memory capacity demand" (DRAM / HBM) **stays v1** with only SemiAnalysis's evidence. TrendForce's pricing thesis (DRAM / HBM + NAND / SSD) and enterprise-SSD thesis (NAND / SSD) are **separate, linked ADJACENT SUPPORT** — never merged, never a confirmation. Direct confirmation stays pinned on a same-identity case | SemiAnalysis (preview): 19/20 · PARTIAL · INCOMPLETE ("GLM's 5.2 / 5.3", `capture_not_verified`). TrendForce: 20/20 · SUCCEEDED · FULLY_VERIFIED |
| **TrendForce 4Q26 alone** | **both theses RESEARCH NOW by the inflection route.** The tracker's own forecasts: conventional DRAM contract prices +10–15% and NAND +15–20% QoQ in 4Q26; enterprise-SSD bit demand >80% YoY in 2026. The pricing step is stated by the source. The first view reads: "no dislocation or dated catalyst, but a credible near-term change in a fundamental: do current earnings estimates and market expectations for Semiconductors already reflect NAND Flash contract price change of 15–20% QoQ in 4Q26?" | 20/20 · SUCCEEDED · FULLY_VERIFIED |
| **Weekly sample** (scan 2026-10-01 → 10, as of 10-10) | 6 of 8 channels (Morgan Stanley, Goldman Sachs BLOCKED, never bypassed); 6 dated articles; 10 theses; Research Now / Watch / Skip **2 / 7 / 1**; **0 challenges**. Round 2's "SemiAnalysis thesis challenged twice" ("Anthropic subscriptions outvalue OpenAI's" vs "China's frontier labs race ahead …") is RELATED | **20/21 · SUCCEEDED · INCOMPLETE** — 0 of 228 figures and 1 of 170 paragraphs open |

**Why the TrendForce result is justified, and why it is not hardcoded.** The rule names no article, publisher or segment. It fires because the article supplies everything the route requires:
- a measurable change in a fundamental — contract prices next quarter;
- from the party that tracks those prices, published in its own data channel;
- with the price → earnings step stated by the source;
- with sectors to ask about.

The same rule refuses the SemiAnalysis memory thesis. Its changing figure, "the share of prompt tokens reused from GPU memory falls from 90.3% to 54.8%", is a workload metric. It *qualified* before I added the fundamentals test, which the real run exposed.

The pins also refuse, on the same article shape:
- a commentator's forecast;
- the tracker's own forecast from a non-data channel;
- a forecast with no source-stated economics;
- a 2030 forecast;
- a forecast "corroborated" only by a measured fact that states no change.

**One caveat to read the card with:** TrendForce says DRAM increases *moderate* in 4Q26. The route tests a stated, material change, not a turning point. Whether estimates already reflect +10–15% is exactly the question it puts to the analyst.

**The weekly sample's open items, resolved or classified:**
- **The three open figures** ("42", "22", "52%") are now captured. "22 (52%)" read as 22 texts is a count; the unit rule had been failing it on the parenthetical's % sign.
- **Paragraph b002** is closed: pass 1b's account names the verified claims c1–c3.
- **Paragraph b008 stays OPEN**, cause `account_names_no_record`. Pass 1b said "carried by first-pass market risk on silent limit changes"; a risk is not a checkable record, so the account cannot be verified.
- **Inaccessible content stays marked:** the SemiAnalysis previews are PARTIAL, and Morgan Stanley and Goldman Sachs are BLOCKED.

## Round 3 screenshots

**Weekly dashboard.** Scan execution SUCCEEDED and research verification INCOMPLETE, side by side; the open-items panel and the verification tile; three dates on every row:

![weekly](https://github.com/techmuns/mosaic-theory/blob/claude/theme-intelligence/docs/theme_intelligence/screenshots/weekly-dashboard.png?raw=true)

**SemiAnalysis + J.P. Morgan: the utilities card, sections 07 / 09.** The RELATED link with what differs. The behind-the-meter card is untouched: `screenshots/contradiction-card-btm-unchanged.png`.

![related](https://github.com/techmuns/mosaic-theory/blob/claude/theme-intelligence/docs/theme_intelligence/screenshots/contradiction-card-related.png?raw=true)

**SemiAnalysis + TrendForce: TrendForce's pricing card, sections 07 / 09.** The ADJACENT SUPPORT link to the sparse-attention thesis:

![adjacent](https://github.com/techmuns/mosaic-theory/blob/claude/theme-intelligence/docs/theme_intelligence/screenshots/overlap-card-adjacent-support.png?raw=true)

**TrendForce alone: section 08 with the audit view on.** The decision trace names the route and the research question. The dashboard's first view says it in plain words: `screenshots/trendforce-dashboard.png`.

![inflection](https://github.com/techmuns/mosaic-theory/blob/claude/theme-intelligence/docs/theme_intelligence/screenshots/trendforce-card-inflection.png?raw=true)

The focused card images are the real print cards, unchanged except for one added style rule that hides the other sections.

## Round 3 tests, mutants, gate, spend

**New tests**
- `tests/test_theme_intelligence_evidence_roles.py` (16 items):
  - the real SemiAnalysis / J.P. Morgan and SemiAnalysis / TrendForce pairs, replayed from **frozen fixtures**;
  - the real TrendForce inflection route, including the rendered first view;
  - per-dimension contradiction pins (same claim → COMPETING; geography / timeframe / segment → RELATED; unclassified);
  - the inflection refusals.
- `tests/test_theme_intelligence_verification_status.py` (15 items):
  - the unit rule, claim-named accounts and every open cause;
  - INCOMPLETE / FULLY_VERIFIED / preview end to end;
  - the unverified-link QA check (positive and negative);
  - the reviewer re-anchor regression;
  - three dates and the replay flag.

**Re-pinned round-2 tests:** "bull vs seat-erosion" is now RELATED; a direct-contradiction positive pin is added; the challenge-twice and KPI tests now use direct contradictions; the change tags and date labels are updated.

**Fixtures:** four new authentic fixtures, `semianalysis_moratoriums`, `jpm_calm_index_after_semianalysis`, `semianalysis_glm53` and `trendforce_4q26_after_semianalysis`.
- **Second-article extractions:** the second article of each pair is the extraction the run made *with* the first article's theses in the registry. I located it by recomputing that exact request; all four keys hit the cache.
- **Multi-part completeness pass:** frozen exactly as the pipeline merged it.
- **Excerpts:** the cited sentences only. Each SemiAnalysis fixture is under 1,250 words of the publicly served preview.

**Mutation testing:** **27 of 27** guard mutants were killed.
- One mutant survived at first: setting the card's detection date from the as-of. The calm pin's as-of happens to equal the UTC run date, so it could not tell the two apart.
- That pin moved to the replay test (as of 2026-03-02), and the mutant is now killed.

**Gate (final code):** `ruff check .` clean; `mypy --strict vinci` clean (176 files); `pytest -m "not network"` **4,612 passed**, 507 skipped, 37 deselected, 0 failed (on `cd75a018`, docs and artifacts included). Main had no new commits, so no merge was needed.

**Model spend this round: $2.28 across 26 billed calls** (24 card reviews, 1 extraction, 1 completeness pass; 250,211 input / 41,353 output tokens, list price). On top of that, at most two calls may have been lost in flight when I stopped runs to change code (≲ $0.3). Every case re-ran from fresh registries, mostly on cached answers.

**Not changed:** the fund's screen, ranker, dossier, verdict, scoring, valuation, ledger, portfolio, trading and historical-alpha-audit code. Nothing approaches execution.

## Round 3 limitations — stated, not hidden

- **"A timeframe only one of them states" counts as a difference.** A contradiction that cannot be shown to concern the same window is RELATED, never a weakening.
  - *Falsifier:* same-claim opposite reads left RELATED for that reason alone.
  - *Response:* read an undated claim's window from its article date.
- **F12 has no magnitude threshold.** The figure is printed in the question for the analyst.
  - *Falsifier:* F12 rows are repeatedly dismissed as immaterial.
  - *Response:* add a face-validity threshold, never one tuned on outcomes.
- **Industry-data-report status is channel configuration.** A tracker from an unconfigured host is treated as commentary.
- **ADJACENT_SUPPORT is a structural label, not a judgement of relevance.** For example, a rates thesis and a dispersion record share `macro_market`.
- **Re-anchoring now excludes number-failed claims.** A line whose only support failed a possibly false word-number check ("A hike" → 1) is withheld rather than guessed right.
- **Operator decision (8)(a) stays open:** whether a qualitative "swept up in the sell-off" observation may count as a dislocation. (b) is closed by this review.

## Round 3 completion

| review item | disposition | note |
|---|---|---|
| FIX 1 — no challenge without an actual incompatibility; RELATED / ADJACENT otherwise; no CONTRADICTS, WEAKER or downgrade | SHIPPED | real pair pinned end to end from frozen fixtures |
| FIX 1 — pin the SemiAnalysis behind-the-meter vs J.P. Morgan utilities regression | SHIPPED | `test_semianalysis_behind_the_meter_vs_jpm_utilities_is_related_never_a_contradiction` |
| FIX 2 — distinguish DIRECT_CONFIRMATION / ADJACENT_SUPPORT / CONTRADICTION / REPEATED_SOURCE; only directly relevant evidence strengthens | SHIPPED | `EvidenceRole`; segment in identity; change tags |
| FIX 2 — parent / child or sibling links where the technology or mechanism differs; corrected real two-publisher example; no forced merge | SHIPPED | SemiAnalysis / TrendForce: separate, ADJACENT SUPPORT |
| FIX 3 — a narrow near-term fundamental-inflection route; tested on the real TrendForce 4Q26 article; never a forecast alone; credible, 2–4 quarters, clear economics, concrete question | SHIPPED | F12; six refusal pins; no article hardcoded — the same rule refuses the SemiAnalysis thesis |
| FIX 3 — explain why the resulting priority is justified | SHIPPED | above; the reason is also in the dashboard's first view |
| FIX 4 — scan execution and research verification shown separately | SHIPPED | header, tile, md / json, manifest, CLI, QA summary |
| FIX 4 — resolve or classify the 3 open figures and 2 paragraphs | SHIPPED | 3 figures and b002 resolved; b008 classified `account_names_no_record`, still open |
| FIX 4 — inaccessible / incomplete content stays marked | SHIPPED | PARTIAL previews, BLOCKED channels, VERIFIED_WITHIN_PREVIEW status |
| FIX 4 — material unverified claims never cause automatic upgrades | SHIPPED | unverified-link QA check; the re-anchor leak it found on real data is fixed |
| FIX 5 — three separate timestamps; a simulated as-of never labelled a detection | SHIPPED | card header and dashboard / md / csv rows; replay flag |
| Acceptance re-runs: Software Shock, Calm Index, SemiAnalysis + TrendForce, SemiAnalysis + J.P. Morgan, weekly sample | SHIPPED | the table above; worked output in `docs/theme_intelligence/` |
| New tests, corrected cards, dashboards, QA reports, explanations | SHIPPED | — |
| Lint, strict typing, full suite, CI | SHIPPED (local) | CI on the pushed head: see the PR checks |
| Do not merge | STOPPED here | awaiting review |

---

# Round 2 (previous update, 2026-10-10) — kept for the record

> **Two results below were REVERSED by round 3:**
> - the SemiAnalysis → TrendForce *merge* — the theses are now separate, ADJACENT SUPPORT;
> - the SemiAnalysis vs J.P. Morgan *challenge* — the theses are now RELATED, with no weakening.
>
> Their screenshots were removed. Counts and gates in this part refer to commit `5c9f3b9a`.

## What changed, by review item

| # | review item | what changed |
|---|---|---|
| 1 | Whole-article completeness; the calm-index dispersion argument | `completeness.py`: a deterministic ledger of every figure and argument paragraph, read from the article TEXT. Then an independent second pass must account for every gap: add the missed claim / mention / thesis / regime record, extend a thesis, or call the gap immaterial **with a reason**. New record kind **`MARKET_REGIME`**: a measured market-structure condition plus the research OPPORTUNITY the source draws from it — never forced into a buy thesis, never dropped for naming no stock. A market-structure RISK stays a risk. |
| 2 | Research Now without a source-named ticker | The exposure condition is a point-in-time-verified listed common equity **or** a sector / theme the source names (a verified span). The source's role for a company is kept apart from the thesis's reading of it. |
| 3 | Historical security mapping | `securities.py`: listings are the common-equity lines on the inline-XBRL cover of the latest 10-K / 10-Q / 20-F / 40-F filed **on or before the as-of date**. Preferred / depositary-preferred / debt lines are kept for audit with their class, never as stock. A current-map ticker missing from that cover is NOT_REGISTERED_AS_OF; with an 8-A12B in between, or no readable cover, it is UNVERIFIED and never an exposure. |
| 4 | Transmission and labels | A share-price / valuation / index move is a `market_reaction`, never an earnings mechanism; a step filed otherwise is re-filed and logged. Labels: SOURCE OPINION / MEASURED OBSERVATION / FORECAST / MODEL INFERENCE / EXTERNALLY VERIFIED; a line carries the WEAKEST label of the claims it cites. |
| 5 | Real 2–4-quarter relevance | `timewindow.py`: a forecast or event counts only if its stated window starts within a year and ends within ~18 months; a measured observation only if dated within the last quarter. The model's horizon label is recorded, never decisive. A dislocation must be a mispricing measured in the last quarter; a catalyst must be a dated event inside the window. |
| 6 | Authors | The union of JSON-LD, schema.org/Person microdata, meta author and the visible byline, plus people the text credits. **Why Nick Roberts was missing:** the page's JSON-LD `Article.author` lists only Kriti Gupta; the visible byline credits both as schema.org/Person items, and the old parser stopped at JSON-LD (frozen authentic markup: `tests/fixtures/theme_intelligence/jpm_calm_index/byline.html`). The disagreement is recorded as `AUTHOR_METADATA_DISCREPANCY`. |
| 7 | Completeness checked after pass 1, not against its own claims | The ledger comes from the text before any model output is read. Long articles are reviewed in parts of ≤ 50 gaps. Coverage is re-derived from **verified quotes**, never taken from the model's verdict. |
| 8 | Re-anchor before withholding | A non-verbatim quote is re-anchored to the one verbatim sentence that carries its figure and shares its words two-sidedly. A rejected card line is re-cited — reviewer suggestions first, then a verified claim carrying its numbers / words, then the verbatim passage (minted as SOURCE OPINION only when an LLM reviewer will judge it again) — and reviewed once more. A MODEL INFERENCE line is never re-anchored. |
| 9 | Reprocess the weekly sample | Reprocessed from scratch into a fresh registry on the final code (below); no re-render of older records. |
| 10 | Cross-publisher merging on real material | Real two-publisher cases below. Each publisher keeps its own source line, and the card shows the contribution class each one recorded. |
| 11–14 | Readability | Plain-word KPIs, each stating its population; article date and first-detected date apart; codes and ids behind one audit toggle; the nine-section card opens on a compact decision view (01 / 02 / 06 / 08), the rest on demand, print shows all. |

## Acceptance — real articles, fresh registries, final code (`5c9f3b9a`)

### J.P. Morgan, "Software Shock: AI's Broken Logic" — as of 2026-02-09

**Exactly three distinct living theses**, all WATCH under the corrected rules:

| thesis | key | action and why |
|---|---|---|
| `TH-8DA46A49DB` Indiscriminate software sell-off oversold the whole software sector | software · valuation dislocation · positive · US | WATCH — the source's premise is conditional ("if Claude Code is just another DeepSeek moment") |
| `TH-04140F1CA8` Hyperscalers, chipmakers and materials mispriced after being swept into the software rout | ai_infrastructure · valuation dislocation · positive · US | WATCH — no verified dislocation or catalyst: its only offered dislocation is the article's rhetorical question, a SOURCE OPINION (this was RESEARCH NOW in the first build) |
| `TH-A56902FFB6` AI adopters show measurable margin expansion versus non-adopters | ai_adoption.enterprise_margins · margin expansion · positive · US | WATCH — no verified dislocation or catalyst |

- **Facts and qualifications intact:** the completeness ledger lists 34 figures: 13 captured by pass 1, 1 added by pass 1b, 20 judged immaterial with a reason, 0 uncaptured. It lists 12 argument paragraphs: 11 anchored, 1 immaterial. The top-10 pairwise correlation "in the 99th percentile" is captured (`C-1d705296dc93cb`) and stays a market risk, not a fourth thesis. Chart-read figures keep "approximate, read from a chart; data as of …"; the premise stays conditional; association stays "not causation".
- **No future security information:** Alphabet resolves to **GOOGL** (Class A Common Stock) and **GOOG** (Class C Capital Stock), VERIFIED from the cover page of the 10-K filed 2026-02-05 (accession 0001652044-26-000018). **GOOGM / GOOGN** are `NOT_REGISTERED_AS_OF`: absent from that cover, with no 8-A12B registration before 2026-02-09. They never enter the record as stock.
- QA **19/19**.

### J.P. Morgan, "A calm index, a restless market" — published 2026-10-02, as of 2026-10-10

| record | key | action and why |
|---|---|---|
| `TH-4BC577D53A` **market-regime record** — "Low implied correlation makes equity sector and theme selection the new diversifier" | macro_market · dispersion_selection · positive · US | **RESEARCH NOW** — four measured observations dated 2026-10-02; the exposure is the source's own "at both a sector and thematic level"; no stock named, no buy thesis forced |
| `TH-98FD8D046C` utilities thesis — "Rates, data-center moratoriums pressure utilities despite AI power demand" | ai_infrastructure.power_grid · policy_regulation · negative · US | **RESEARCH NOW** — sector "utilities", measured observations dated 2026-09-30 / 10-02; the utilities price fall is filed as a market reaction, never as an earnings mechanism |

- **All material figures:** the ledger lists 19 figures: 16 captured, 3 judged immaterial with a reason, 0 uncaptured. Among them:
  - ~43% of constituents above their 200-day average (`C-a97bbb9aa2d733`);
  - 75% in mid-August (`C-a8e001324178a8`);
  - 3-month implied correlation 11.2 (`C-61a7adf78143ca`);
  - long-run average 41 (`C-61a7adf78143ca`, `C-b141683e305af8`);
  - the sector / thematic stock-selection implication is the regime record's opportunity.
- **Authors:** Kriti Gupta and Nick Roberts. The page's JSON-LD lists only Kriti Gupta; the visible byline credits both as schema.org/Person items. The disagreement is recorded as `AUTHOR_METADATA_DISCREPANCY`.
- QA **19/19**. Genuine open issues stay visible:
  - an entity the model named that the text never names ("J.P. Morgan Private Bank") is dropped (BLOCK);
  - one sector span that does not name "utilities" is dropped (WARN);
  - one "what could go wrong" line is withheld as unsupported by its cited spans (BLOCK).

## Real two-publisher cases

### Overlap — SemiAnalysis (2026-09-28) then TrendForce (2026-09-30): one thesis, two publishers

- **SemiAnalysis**, "Inside GLM-5.3: How Sparse Attention Affects DRAM Memory TAM" (a paid post: only the public preview is read, recorded PARTIAL), creates `TH-91CA483676` "Sparse attention does not reduce overall AI memory capacity demand" (`ai_infrastructure.memory` · demand_volume_shift · positive · Global).
- **TrendForce**, "AI Server Demand Sustains Memory Contract Price Increases in 4Q26, While Consumer-Side Pressure Persists", confirms it. The result is the **same thesis id, version 2**:
  - 6 new claims from an origin the thesis did not yet hold: enterprise-SSD bit demand >80% YoY in 2026; supply already committed; demand shifting from training to deployment;
  - evidence **STRONGER**; the action stays WATCH (no verified dislocation or catalyst).
- **Each publisher keeps its own source line:**
  - SemiAnalysis: 6 named authors, 2026-09-28, origins "SemiAnalysis InferenceX" plus its own analysis — the initial record;
  - TrendForce: organisation, 2026-09-30, its own analysis — *new evidence*.
- **Linked, not merged:** TrendForce's pricing argument becomes a separate **SIBLING**, `TH-A7FF458FB3` (same node, `pricing_cycle`). Its weak-consumer argument is a separate thesis, SKIP (no verified material evidence).
- QA: TrendForce step 19/19; SemiAnalysis step 18/19. The failure is two figures in "GLM's 5.2 / 5.3 model" that stay open: pass 1b named a claim as capturing them, but that claim does not quote them, and coverage is re-derived from verified quotes, never taken from the model's word.

### Contradictory evidence — SemiAnalysis (2026-09-15) then J.P. Morgan (2026-10-02)

- **SemiAnalysis**, "Everyone Says Datacenter Moratoriums Are Killing the US Buildout. We Mapped All 300 of Them" (PARTIAL), yields two theses:
  - "Grid friction pushes datacenters behind-the-meter, benefiting on-site generation suppliers" (`ai_infrastructure.power_grid` · positive);
  - "Datacenter moratoriums barely dent the US AI buildout pipeline" (`datacenter_physical`).
- **J.P. Morgan**'s utilities thesis (`power_grid` · negative) is linked as **COMPETING** with the behind-the-meter thesis. They are never merged:
  - its supporting claims are filed against it as CONTRADICTS evidence: **version 2, WEAKER, event CHALLENGED**;
  - the J.P. Morgan source line reads *contradictory*;
  - the card states the basis as the rule found it: *the same value-chain node, different mechanisms (demand_volume_shift vs policy_regulation)*.
- **Read on its merits, this challenge is weak.** The two theses address different segments of one node (behind-the-meter suppliers vs grid-tied utilities), and 2 of the 5 claims filed against it are utilities price moves. The rule is the first build's: its own acceptance case pairs two mechanisms on one node. I left it unchanged and recorded it as an **operator decision**: split the node, or require the same mechanism.
- QA: J.P. Morgan step 19/19; SemiAnalysis step 18/19 (one argument paragraph left unaccounted, visible).

### The weekly sample, reprocessed from scratch — window 2026-10-01 → 10, as of 2026-10-10

| channel | status | discovered | in window | processed | note |
|---|---|---|---|---|---|
| Citi Must C | OK | 20 | 0 | 0 | 20 out of window |
| BofA insights | OK | 16 | 0 | 0 | 12 UNDATED (pages state no date) · 4 out of window |
| J.P. Morgan TMT | OK | 51 | 1 | 1 | "A calm index, a restless market" |
| Morgan Stanley | **BLOCKED** | 0 | — | — | robots.txt unreachable → fail closed |
| Nomura Connects | OK | 14 | 1 | 1 | 1 undated |
| TrendForce | OK | 5 | 2 | 2 | |
| SemiAnalysis | OK | 20 | 2 | 2 | paid posts → PARTIAL |
| Goldman Sachs | **BLOCKED** | 0 | — | — | HTTP 403 |

- **Sample:** the same six articles as the first build's weekly sample, reprocessed from scratch on the final code. Nothing was re-rendered from older records.
- **What came out:**
  - 192 claims extracted, all span-verified;
  - the completeness ledger: 228 figures, 3 open;
  - 61 claims added by pass 1b;
  - 10 theses, among them J.P. Morgan's regime record and utilities thesis, both RESEARCH NOW.
- **New paths exercised:** item-level validation dropped 2 malformed items, and the parts path ran on 2 long articles.
- **The run that had crashed:** one article's two new theses both challenge a SemiAnalysis thesis, and that thesis now reaches v3 with two distinct challenge records. This scenario stopped the previous weekly run (see the fixes below).
- **QA 18/20.** Both failures are genuine pass-1b gaps, kept visible:
  - 3 figures in one SemiAnalysis post ("42 … 22 (52%)") left open;
  - 2 argument paragraphs in another left unaccounted.

## Screenshots

Re-rendered by round 3 under the same file names — see **Round 3 screenshots** above and `docs/theme_intelligence/screenshots/`.

## Found by this round's real runs — fixed, pinned and mutation-checked

None of these was anticipated; each surfaced on a real page.

| # | what the live run showed | fix |
|---|---|---|
| 1 | One mention typed `other` discarded a whole paid extraction (the contradiction run failed). | Answers are validated **item by item**: a malformed item is dropped and named (`MALFORMED_ITEM_DROPPED`), never coerced. |
| 2 | The completeness pass over a long SemiAnalysis post (124 open figures + 91 paragraphs) overran the 21,333-token output cap. | Gaps are reviewed in **parts** of ≤ 50; each part sees what earlier parts added; an overrun part is split once, with its cost recorded. |
| 3 | SemiAnalysis URLs were filed **"UNKNOWN publisher"**: the channel was matched on its entry host only, but posts live on its feed host. | Match on every host the channel is configured with. |
| 4 | Several number readings were wrong: <ul><li>"GLM-5.3" read as the figure 5.3 — it blocked a card's bottom line and put 8 false figures in the ledger;</li><li>a verbatim "doubling" claim failed its number check;</li><li>"three-four months" was split;</li><li>"75GW", "930MW", "744B" and J.P. Morgan's "99th percentile" were missed by the ledger;</li><li>"(1) … (5)" list markers were read as five figures.</li></ul> | **One shared number reading** (`stated_numbers` / `word_numbers`) used by every check and by the ledger. |
| 5 | Evidence tables printed "~43% %" and "15–20% % QoQ". | A unit prints once. |
| 6 | Twice, on two long SemiAnalysis extractions, `hypotheses` came back as **broken JSON text**. The article failed and the run reported $0. | The answer is set aside (kept on disk) and the request asked **once more**; both cases recovered, with costs recorded. Nothing is repaired into shape. |
| 7 | An update's source line said "initial record" (its contribution row is written after the card). | The current article's recorded class is passed in. |
| 8 | A COMPETING line claimed "same node and mechanism" for two different mechanisms. | The line states the basis as found. |
| 9 | One article challenged a thesis twice and the weekly run **stopped** (duplicate contribution id). | One id per challenger. |
| 10 | KPI "Skip 0" (a SKIP is archived at once) and "challenged 0" (a thesis created and challenged in one run sits under NEW). | Counts over this run's theses and events; each tile states its population. |
| 11 | Thesis / article ids appeared in the first view of challenged cards. | They sit behind the audit toggle. |

## Tests, mutants, gate

- **Gate on the merged tree (`048753db`):**
  - `ruff check vinci tests frontend`: clean.
  - `mypy --strict vinci`: clean (176 files).
  - `pytest -m "not network"`: **4,576 passed**, 507 skipped (pre-existing), 37 deselected, 0 failed.
- **Theme suite:** 194 test items across `tests/test_theme_intelligence_*.py`.
  - New files: `…_corrections.py`, `…_calm_index.py`, `…_long_articles.py` (21), `…_numbers.py` (22).
  - The acceptance tests replay **authentic excerpts and frozen model outputs** (re-frozen from the final run) through the real engine.
- **Mutation, on the final code — 64 of 65 killed:**
  - **25 of the 26** review-correction guards. The survivor (`passage-needs-llm-review`) is **equivalent in practice**: `FACT_WITHOUT_CLAIM` was raised 0 times in this round's 32 run registries, because a line citing no verified claim is labelled MODEL INFERENCE by composition. The test's docstring says so rather than implying it reaches the branch.
  - **39 of 39** for this round's fixes.
  - The mutation run also exposed an unpinned guard (re-anchoring needs the sentence to carry the figure); a negative pin now kills it.

## Model spend of this round

- **Recorded in the shared cache: $21.14 across 138 calls.** List price ($5 / $25 per M input / output tokens); 1,737,926 input and 498,084 output tokens:

  | call type | calls |
  |---|---|
  | extraction | 19 |
  | extraction set aside | 2 |
  | extraction overrun | 1 |
  | completeness | 27 |
  | card review | 89 |

- **Left no cache file: ≈ $1.7.** Two SemiAnalysis overruns before the compact retry existed, and one answer lost to the old whole-answer check.
- **Killed in flight: up to two calls,** when I stopped runs to fix a defect. Cost unknown, at most ≈ $1.2.
- **In all: ≈ $22.8–24.**
- The final verification runs replay from cache at **$0**.

## Limitations — stated, not hidden

- **Source access:**
  - Morgan Stanley (robots.txt unreachable → fail closed) and Goldman Sachs (HTTP 403) refuse the honest User-Agent: BLOCKED every run, never bypassed.
  - BofA pages state no date: counted UNDATED, never placed in a window.
  - SemiAnalysis paid posts: the public preview only, recorded PARTIAL — never presented as full-text analysis.
- **Operator decisions recorded** (STATE §5.0 row 32 item 8):
  - (a) Should a qualitative "swept up in the sell-off" observation count as a dislocation? Today it does not, which is why AI infrastructure is WATCH.
  - (b) Should a challenger that shares only the value-chain NODE weaken a thesis? Today it does — see the contradiction case. The fix would be to split the node or require the same mechanism.
- **Open gaps the completeness pass leaves are listed, not resolved by fiat.** Version strings in prose ("GLM's 5.2 / 5.3 model") stay open rather than being skipped by a guess.
- **Unchanged from the first build:**
  - The model is pinned to `claude-opus-4-8`: the shared client forces a tool call that newer models reject.
  - Consensus and valuation are NOT_ASSESSED: the tool holds no such data.
  - The Monday cron is opt-in; Actions scheduling is verifiable only after merge.

## Completion — the review's items

| review item | status | note |
|---|---|---|
| P0.1 whole-article completeness; dispersion argument preserved | **SHIPPED** | regime record RESEARCH NOW; ~43% / 75% / 11.2 / 41 captured; 19 of 19 figures accounted for |
| P0.2 Research Now without a ticker | **SHIPPED** | sector / theme exposure counts; companies' source role kept apart |
| P0.3 point-in-time securities; GOOGL / GOOG vs GOOGM / GOOGN | **SHIPPED** | as-of cover pages; GOOGM / GOOGN NOT_REGISTERED_AS_OF on 2026-02-09 |
| P0.4 transmission and provenance labels | **SHIPPED** | price moves are market reactions; five labels, weakest wins |
| P0.5 real 2–4-quarter relevance | **SHIPPED** | calendar windows; AI infrastructure WATCH on the corrected typing |
| P1.6 all authors | **SHIPPED** | Kriti Gupta and Nick Roberts; the metadata disagreement recorded |
| P1.7 recheck after pass 1 | **SHIPPED** | text ledger + independent pass 1b, in parts for long articles |
| P1.8 re-anchor before withholding | **SHIPPED** | inference never re-anchored; genuinely unsupported lines withheld and visible |
| P1.9 reprocess the weekly sample | **SHIPPED** | fresh registry, final code; QA 18/20 with its open gaps listed |
| P1.10 real cross-publisher merging | **SHIPPED** | SemiAnalysis → TrendForce merge (v2, STRONGER); per-publisher contribution and origins |
| P2.11 KPI labels | **SHIPPED** | plain words; populations stated |
| P2.12 codes out of the first view | **SHIPPED** | first-view scan of every web card and dashboard: 0 with codes |
| P2.13 article date vs first detected | **SHIPPED** | "new to the registry", never "new to the market" |
| P2.14 nine sections, compact default | **SHIPPED** | 01 / 02 / 06 / 08 open; print shows all |
| Acceptance: Software Shock — three theses, facts intact, no future securities | **SHIPPED** | QA 19/19 |
| Acceptance: calm index — utilities + dispersion, figures, authors | **SHIPPED** | QA 19/19 |
| Acceptance: a genuine two-publisher overlap case | **SHIPPED** | real articles; QA 18/19 (2 genuine open figures) and 19/19 |
| Acceptance: a contradictory-evidence case | **PARTIAL** | runs and records the challenge as designed; on its merits the challenge is weak (node granularity) — an operator decision, not re-tuned |
| Acceptance: dashboards, cards, QA reports, screenshots | **SHIPPED** | `docs/theme_intelligence/` |
| Acceptance: all tests and CI checks | **SHIPPED** | local gate green on the merged tree; CI runs on the PR |
| Do not modify decision logic / valuation / portfolio / trading / alpha audit | **SHIPPED** | no change outside the package beyond docs and STATE |
| Update PR #703 and wait for review | **SHIPPED** | not merged |

🤖 Generated with [Claude Code](https://claude.com/claude-code)

