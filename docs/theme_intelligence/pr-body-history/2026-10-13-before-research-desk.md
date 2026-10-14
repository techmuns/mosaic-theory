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

## Final evidence and UX acceptance corrections (this update)

Record: `docs/records/2026-10-12-theme-intelligence-final-corrections.md`. **$0 — no model call, no stored record edited.** All four corrections are made at render time from stored records. Nothing is merged, scheduled or published.

| | before | after |
|---|---|---|
| broken evidence links, four cards on screen | **27** (14 targets) | **0** |
| link landings that open their section and land on screen (23 targets × 1440/390) | — | **46 / 46** |
| views that fit with every section open, audit view off and on (9 pages × 2 widths × 2) | — | **36 / 36** |
| review items in the summary | 21 (everything) | **8** (current cards) |
| Nomura card — Review required | 5 lines | **4** (+1 resolved) |
| weekly page height, 1440 / 390 | 5,328 / 11,912 px | **4,304 / 8,392** |
| first thesis from the top, desktop | 357 px | 357 px |

1. **Evidence links.**
   - Every claim a card cites now has a row: section 04 gains a collapsed "Other evidence this card cites" table (counter-evidence, context), each with its role.
   - An id with no record is printed as text, never linked.
   - A link into a collapsed section opens it.
   - On a phone, evidence tables scroll sideways.
2. **Business groups (TrendForce).**
   - "GPU and ASIC manufacturers / vendors" and memory "suppliers" are listed verbatim in section 05 under their own heading: not companies, no ticker implied.
   - The why-line says "the source names business groups only (…), not companies".
   - Priority and action are untouched.
3. **Current versus historical.**
   - J.P. Morgan's '11' and '10%' failed a number check that today's check passes. They now sit under **Resolved or historical** and are still not evidence until re-applied.
   - Nomura's s07.3 label finding is resolved by the relabel and shows as history on the line. s07.2 stays unresolved: its whole finding also objects to content (see the fail-safe update below).
   - The rule is narrow and fail-safe: only a finding about the label alone is resolved.
4. **Readability.**
   - The overview says how each thesis works in the source's own words (its first source-stated, unquestioned step), not a taxonomy category.
   - "Effect on profits" is the step chain plus one sentence.
   - The review queue leads with the current cards' findings, one shortened line each; the rest is collapsed below.

**Verification:**
- integrity on the four WATCH theses (nine sections, every evidence row and cited claim in HTML and print, actions agree);
- QA 22/22;
- 17 new end-to-end tests; 26 of 26 mutants killed (one dropped as equivalent); last round's 31 of 31 still killed;
- offline suite 5,075 passed, 512 skipped, 0 failed; ruff and `mypy --strict` clean.

"Before" is the reviewed preview regenerated exactly, from the code at `4e70eeb0`; it reproduces the 27/14 count.

### Remaining issues

- **The finding reader is lexical, so it errs toward OPEN.** A label-only finding worded in a way it does not recognise stays unresolved on the card. That is the intended failure mode.
- **Not redesigned:** the weekly Markdown still lists every finding in full.

### Fail-safe review resolution (follow-up, 2026-10-12)

Record: `docs/records/2026-10-12-theme-intelligence-failsafe-resolution.md`. `report.finding_scope` reads each finding from its own words:
- **label_only** — every clause is about the label, or plainly affirms support. Resolved by the relabel.
- **mixed** — it names the label AND objects to content ("support only parts", "not in the cited span", "overstates"). Stays open.
- **ambiguous** — some clause is neither about the label nor a plain affirmation. Stays open.

The reviewer's words stay whole on the line, and the original finding is never edited.

On the real data, Nomura **s07.2** is *mixed* (its whole finding also says the cited observations "support only parts"), so it returns to UNRESOLVED. **s07.3** is *label_only* and stays resolved.

**Tests and gate:**
- 4 end-to-end cases (one label-only, two mixed, one ambiguous) and 10 reader cases;
- 5 of 5 mutants killed;
- offline suite 5,091 passed, 512 skipped, 0 failed; ruff and `mypy --strict` clean.

### Disposition

| brief item | disposition | note |
|---|---|---|
| 1 broken `#C-…` links reach their evidence (or a valid alternative) | SHIPPED | 27 → 0; an unheld id is plain text |
| 2 source-named business groups apart from listed-company exposures | SHIPPED | no ticker; no upgrade (F6 unchanged) |
| 3 corrected past failures told apart from unresolved issues | SHIPPED | J.P. Morgan sector count; Nomura labels |
| 4 shorter overview and review queue; material warnings first; the rest expandable | SHIPPED | 7 current first; 3 collapsed groups |
| — plain-English mechanism from existing verified data | SHIPPED | the source-stated step; "Category:" fallback |
| nine sections; no evidence, risk, date or qualification deleted | SHIPPED | integrity check |
| verify links, default view, audit view, print, 390 px | SHIPPED | browser-run checks above |
| no paid calls, sources, ingestion, scheduler, ledger or portfolio features | SHIPPED | $0 |
| tests and CI; final private preview; remaining material issues | SHIPPED | preview local only |
| follow-up: label-only resolves; mixed and ambiguous stay unresolved | SHIPPED | `finding_scope` |
| follow-up: test all three cases; check both Nomura resolutions against their whole findings | SHIPPED | s07.2 mixed, now open; s07.3 label-only |

---

## Earlier updates (condensed; full text: `docs/theme_intelligence/pr-body-history/`)

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

