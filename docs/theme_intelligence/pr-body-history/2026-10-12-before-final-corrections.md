## Summary

A new, isolated package **`vinci/theme_intelligence/`**: a research discovery and prioritisation tool. It:
- reads research from **seven publisher channels** (five automatic, two manual-first) and from documents the operator supplies;
- extracts source-anchored evidence, named companies and risks;
- keeps a persistent, versioned registry of theses;
- writes a weekly dashboard of nine-section **Living Thesis Cards**.

**"RESEARCH NOW" means allocate analyst attention — never buy.** The package stays off the fund's decision path:
- no fund module imports it;
- it imports only `vinci.config`, the existing LLM client and the HTTP cache (AST-pinned);
- it has its own SQLite registry;
- it has no buy, sell, target or weight field;
- its priority rules read no prices, returns or outcomes.

**This update is the final acceptance.** It adds no code. Record: `docs/records/2026-10-12-theme-intelligence-acceptance.md`.

**Not merged.** The weekly schedule is off and no production state branch exists. Nothing is deployed and no automation is enabled.

---

## Product redesign and three research corrections (this update)

Record: `docs/records/2026-10-12-theme-intelligence-product-redesign.md`. **$0 — no model call.** Nothing merged, scheduled or published.

### 1. Three J.P. Morgan research defects — corrected from stored evidence

`reassess --corrections` on the pilot registry (`R-20261012T133456Z-reassess`): 4 theses re-graded, 2 changed, QA 20/20. Rehearsed first on two copies, with identical outcomes.
- **A1 — the bottom line.** It said "beaten expectations for eight consecutive quarters". The source projects an eighth consecutive quarter of **double-digit growth**, if realised.
  - Replaced by an **analyst correction**: operator text citing three verified claims the thesis links, keeping the conditional, so it is labelled SOURCE OPINION.
  - The reason shows on the line. The earlier version stands in the history.
- **A2 — the Magnificent 7 lagging the index** is now **price context**: market context, never counter-evidence to *earnings* broadening.
  - Counter-evidence (F8) falls from 2 to 1; the action stays WATCH.
- **A3 — the number check.** A number in a named index or period label ("S&P 500", "Q3", "1H27") is part of a name, not a figure; every other number is still checked.
  - The line withheld for "printing 500" is shown.
  - A figure in words beside digits ("five of the 11") is read as written.
  - The sector-count claim would pass today, but its stored record keeps the failure: **'11' and '10%' stay an explicit open finding** until the article is applied again.
- A correction is **refused whole** when it cites an unlinked or unverified claim, names no card line, or prints a number its claims don't carry.

### 2. The weekly page

- **The research first:** the as-of date, a summary (Research Now / Watch / Skip, review items, verification, articles read), then every thesis as a concise card.
- **Each card shows:** the mechanism, what changed, the effect on profits, why Watch, the next question, the source and dates, and a Review Required link to each affected line.
- **Separate views:** activity, the review queue, sources, the archive, and Operations & audit (run ids, codes, commands, the validation log).
- **One row per thesis with every event of the week:** TrendForce reads "New · Downgraded: Research Now → Watch".

### 3. The Living Thesis Card

- **Header:** the action, the horizon, the three dates, and **Review required** linking each finding to its exact line.
- **At a glance** answers seven questions: the thesis, what changed, the effect on profits, the strongest evidence (units, periods, sources), why this action, what could invalidate it, and the next check. Risks and the next check are open.
- **The nine sections follow unchanged.** Ids, codes and the decision trace sit behind **Audit view**. Print opens everything.

### Measured on the real pilot output — before → after

The weekly page and the four WATCH cards, at 1440 and 390 px. Text inside a collapsed section counts as off-screen.

| | before | after |
|---|---|---|
| first thesis from the top — desktop / mobile | 2,125 / 3,683 px | **357** / 609 px |
| page width at 390 px | 422 (overflow) | **390** |
| "page None" on the whole page (= print) | 18 | **0** |
| double-escaped entities, whole page | 5 | **0** |
| registry ids on screen — weekly page / per card | 13 / 1–3 | **0 / 0** |
| engine codes on screen, per card | `NOT_ASSESSED` | **none** |

**Integrity, on the four real theses:**
- all nine sections, in order;
- every evidence row (4, 20, 6, 18) and every cited claim (4, 22, 9, 27) reachable in HTML and print;
- print opens every section;
- the action agrees across JSON, card and weekly page;
- QA on the preview run: 22/22.

**Tests:** 16 new end-to-end tests; 4 old-layout tests re-pinned on the same invariants; **31 of 31 mutants killed**; offline suite **5,056 passed, 512 skipped, 0 failed**; ruff and `mypy --strict` clean.

### Remaining genuine issues

- **The card review missed the bottom line's paraphrase error.** It had flagged the line for a different element. The operator corrected it; a reviewer can pass a sense-changing paraphrase.
- **The sector-count figures stay open** until that article is applied again under today's rule.
- **Nomura's relabelled lines** carry a review warning that still reads "Labelled MEASURED OBSERVATION…", which was true of the earlier version.
- **Not redesigned:** the weekly Markdown (entities fixed only), and the JSON, which keeps stored values.

### Disposition

| brief item | disposition | note |
|---|---|---|
| A1 bottom line — eighth quarter of double-digit growth, conditional kept | SHIPPED | analyst correction, SOURCE OPINION |
| A2 Magnificent 7 price move ≠ counter-evidence | SHIPPED | price context; F8 2→1 |
| A3 named indices in the number check, not broadly disabled | SHIPPED | names and period labels only |
| — the two unverified sector-count figures | SHIPPED | reviewed: pass today's rule; kept OPEN (stored failure, not edited) |
| B weekly page: research first; summary; concise thesis cards; verification link | SHIPPED | first thesis at 357 px |
| — health, operations, logs, archive in separate views | SHIPPED | navigation + Operations & audit |
| — no ids / codes / commands / traces in the default view | SHIPPED | 0 measured; audit view keeps them |
| — new + downgraded thesis shows both events, no duplicate | SHIPPED | one row, both tags |
| C card: nine sections + provenance kept; seven questions at a glance | SHIPPED | |
| — risks and next action visible; review indicator links the exact line | SHIPPED | |
| D institutional look; navigation; responsive; page None / escapes / overflow | SHIPPED | |
| — no decorative charts, invented metrics, scores or rankings | SHIPPED | none added |
| E four real WATCH theses; before/after at 1440 and 390 | SHIPPED | screenshots local |
| — HTML / JSON / print agree; no regression | SHIPPED | QA 22/22; suite green |
| — private preview and screenshots | SHIPPED | local only; nothing published |
| No LLM call; no merge, scheduling or production state | SHIPPED | $0 |

---

## Earlier updates (condensed; full text: `docs/theme_intelligence/pr-body-history/`)

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

