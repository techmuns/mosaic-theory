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

## Final acceptance (this update)

### Authorization

Recorded as **operator-confirmed authorization** (2026-10-12): the required processing rights are held for internal research use.
- The licensing discussion is not reopened.
- Access controls and privacy restrictions are unchanged.

### 1. J.P. Morgan acceptance test — **PASS**, $0.3851

**What ran.** The article in the pilot registry, once, under a **$2.00** limit.
- Pass 1 came from the answer an earlier run already paid for, at **$0**, with the salvage stated.
- Paid: the completeness pass **$0.2052** and two card reviews (**$0.0917**, **$0.0881**). No call exceeded its pre-send bound.
- Pilot total: **$4.3345 of $18**.

**Result.**

| Check | Result |
|---|---|
| Thesis | one, `TH-FBDC863613` — earnings broadening beyond the mega-caps; WATCH |
| Numbers | every figure printed on the card (22) matches its source paragraph |
| Citations | 36 of 36 spans re-found |
| Card sections | all nine, in order |
| Priority | WATCH is correct — no verified dislocation or catalyst; the forecast is a commentator's, with no corroborating measurement |
| QA | 19 of 20 — the miss is stated: two figures of one claim failed the number check and stay open, never used |

**Card findings, recorded but not fixed.**
- A bottom-line paraphrase: "beat expectations for eight consecutive quarters" should be "eight consecutive quarters of double-digit growth". The line carries a review warning.
- One risk line was withheld because "S&P 500" was read as a figure.
- A supporting fact is shown as counter-evidence.

### 2. Readiness — **READY TO MERGE** (no genuine blocker found)

- **CI:** `gate` and Cloudflare Pages passed. The offline suite: 4,996 passed, 511 skipped, 0 failed.
- **Environment, all documented in `docs/theme_intelligence.md`:**
  - `ANTHROPIC_API_KEY` and `SEC_USER_AGENT` (secrets);
  - `THEME_INTELLIGENCE_SCHEDULE_ENABLED` (repository variable, opt-in cron);
  - `THEME_INTELLIGENCE_HEALTH_HOOK` (optional);
  - the TOML configuration.
- **Schedule off:** no repository variable is set, and the `theme-intelligence-state` branch doesn't exist.
- **Spend controls:**
  - a per-call pre-send bound;
  - a run limit (scan default $40; the workflow defaults to 25 articles);
  - a $30 per-document hold;
  - a salvaged answer is never paid for twice.
- **Integrity and duplicates:**
  - history tables are append-only, enforced by triggers;
  - QA runs 20 checks;
  - an already-applied version adds nothing;
  - evidence is counted by independent origin.

### 3. Product preview — local only

The real weekly report and cards: the weekly page of a **$0 scan** (no article analysed, no model call) run on a **copy** of the pilot registry.
- It covers the pilot's 10 runs: 5 articles and 4 theses.
- It is viewed on the operator's machine and published nowhere. Screenshots are held locally.

### Disposition

| brief item | disposition | note |
|---|---|---|
| Record operator-confirmed authorization | SHIPPED | record + STATE row 32 |
| J.P. Morgan acceptance: completeness + reviews within $2 | SHIPPED | $0.3851; PASS |
| — verify numbers, completeness, citations, priority, nine sections | SHIPPED | as above; three findings recorded |
| — the other four articles not re-run | SHIPPED | |
| Readiness review: CI / tests / env docs / schedule off | SHIPPED | READY TO MERGE |
| Product preview: real dashboard, cards, health, coverage, priority; screenshots | SHIPPED | local; nothing published or committed |
| Do not merge / deploy / enable automation; no refactor | SHIPPED | |

---

## Earlier updates (condensed; full text: `docs/theme_intelligence/pr-body-history/`)

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

