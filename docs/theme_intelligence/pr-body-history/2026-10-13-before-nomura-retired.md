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

**This update records a saved paywalled preview as a preview and makes Sources, Articles and Uploads read plainly.** Before it: the readability pass, the approved research desk, the review-safety fix, and — before merge — the runner fix, one theme, and the desk inside the main app. Records: `docs/records/2026-10-13-theme-intelligence-columns-and-uploads.md`, `…-readability.md`, `…-research-desk.md`.

**Not merged.** The weekly schedule is off and no production state branch exists. Nothing is deployed and no automation is enabled.

---

## Columns and uploads: plain Sources / Articles / Uploads, and a saved preview stays a preview (this update)

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






