---
id: 2026-10-05-credit-health-names-its-peer-group
status: shipped
date: 2026-10-05
prs: [667]
supersedes:
superseded-by:
---

# A credit-health score names the peer group it ranks within

**WHAT.** The S&P-MI relative credit-health score now renders with its POPULATION, from both CIQ
sources, never merged. Operator rulings 2026-10-05: show both panels each labelled with its peer
group; the INDUSTRY panel is primary wherever one is needed; the standalone export joins the CIQ
upload checklist.

**THE MEASUREMENT THAT DECIDED IT** (the ten names carrying both exports, 2026-10-05):

- **Same score, two populations.** The comps workbook's "Credit Health Panel" sheet ranks the name
  within its 10–11-name comp set; the standalone Credit Health export within its GICS industry,
  21–40 public companies. Both use 1 = top … 4 = bottom — the export's own verbal labels match its
  numeric table **40 of 40**.
- **They agree on 23 of 40 name-dimensions**, and agreement tracks peer-group overlap (BURL, LLY
  share 8 members → 4/4; AMZN shares 3 → 0/4). AMZN's liquidity is a 4 among megacap comps and a 2
  among broadline retailers. Both are true; "which wins" was the wrong question.
- **The page printed the comps panel with no population** — "Liquidity 4 (weakest)" read as an
  absolute weakness. That defect sat on all 20 names showing credit health, standalone or not.
- **The standalone export was silently DROPPED** on all ten folders carrying one: no workbook
  keyword matched its name. The `charting` failure, a second time.

**WHAT CHANGED.**

- *Loader* — `credit_health` registered; any file matching no workbook kind is RECORDED
  (`CiqBundle.unrecognised`) and the assembler raises a caveat naming it. `.DS_Store` / `~$` lock
  files are ignored. After registration the corpus has zero unrecognised files.
- *Model* — `CreditHealthPanel`: population kind and name, size, four scores, `primary`, how the
  scale's orientation was established (`scale_basis`), S&P's rating (`sp_long_term_issuer`), and
  `data_through`. `LeverageSurvival.credit_health_panels`
  is ABSENT until built (DROP_WHEN_NONE).
- *Industry reader* — the panel is accepted only when the export's own Top…Bottom words match its
  numbers on all four dimensions, and only when the declared company count equals the rows held.
  Either failure is a named refusal, never a guess.
- *Comps reader* — refactored into one structured core that both the existing prose and the comps
  panel are built from. **The prose is byte-identical to `main` on all 26 CIQ names.**
- *Page* — one table, a ROW per dimension and a COLUMN per peer group (`Industry (21)` /
  `Comps (11)`), and a note that defines each group and says the score is a rank WITHIN it. A page
  without panels renders exactly as before. Twin renderers, Markdown and web.
- *Date* — the standalone export stamps no date. Its date is the latest "Financials Updated" across
  the table, named `data_through` because it travels with the values; it is not an arrival
  `as_of` and does not gate freshness.
- *Checklist* — the standalone export is listed, optional: a name without it shows the comps panel
  and says the industry panel is not on file, with no "pull CIQ" caveat added to 16 pages.
- *Backfill* — `credit_health_transform` adds the panels under a KEPT synthesis. The comps panel is
  kept only when today's comps reading equals the prose the page already prints, and then carries
  the page's own citation; otherwise it is withheld and named.

**HOW VERIFIED.**

*The corpus.* Of 26 CIQ names: 8 get both panels (AMZN, BURL, GOOGL, NFLX, NKE, ROST, TGT, WERN), 2
the industry panel only (**BRBR, LLY** — their comps panel reads UNKNOWN because its direction
cannot be inferred; the industry export declares it), 9 the comps panel only, 7 nothing and are
untouched. All ten standalone exports accepted, none refused.

*The backfill, run in the worktree and not committed.* 19 pages moved, 7 unchanged, 0 refused. On all
19 the JSON's ONLY change is the new key; outside the credit block every page is identical once
endnote numbers are normalised (a newly-cited table inserts one endnote and shifts later ones).

*The preview — and what it caught.* Rendered on the web and in Markdown, collapsed and with every
`<details>` forced open: the table sits in the main body, prints, and the page shows zero
`undefined`/`NaN`. **The preview changed the design twice.** Group-per-row labels pushed every score
off a phone screen, so the table was transposed; then the uppercase headers were still 55px too wide
at 375px, so they were shortened. All five checked pages now fit at phone width. Also caught: the
grammar error "among a 11-company comp set".

*Tests.* 11 in `tests/test_credit_health_panels.py`, each new behaviour with a positive and a
negative pin, the twin renderers compared by running the real `dossier.js` in node, and one test over
the real exports wherever they exist (they are licensed and never committed, so the synthetic sheets
reproduce the real layout with invented companies). **Eight deliberate breaks, all caught**: the
keyword removed, unrecognised files unrecorded, the label check skipped, the count check skipped, the
industry panel not primary, the renderer ignoring panels, a web header drifting, the backfill keeping
a contradicted comps panel.

*Two standing guards fired on the first full run, and both were right.*
- `test_dossier_schema_has_no_conclusion_field` flagged `direction_basis` and `issuer_rating` — the
  schema bans verdict-shaped words by name. Neither held a conclusion (one says how the SCALE's
  orientation was established, the other is S&P's third-party rating, already printed in prose), so
  they were renamed to what they are: `scale_basis` and `sp_long_term_issuer`. The guard was not
  widened.
- `test_no_new_literal_set_is_duplicated_across_the_python_js_twins` flagged the four field names
  hand-copied into both renderers — the one-sided-edit hazard it exists for. Both now DERIVE them
  from the existing dimension labels; the baseline was not grown.

*The gate.* ruff clean · `mypy --strict vinci` clean · `pytest -m "not network"` exit 0.

**BOUNDARY.** Measured 2026-10-05 over the CIQ folders on this machine (26 names; ten carry a
standalone export). The 23-of-40 and 40-of-40 figures are those ten names on their current exports.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **No page changes in this PR.** The 19 pages move in the artifact pass that follows, through the
  backfill, without re-drawing any synthesis.
- **The industry panel has no export date**, only a floor; it is printed, never gated.
- **"Primary" is display order and a flag today.** Nothing yet gates on credit health; the flag is
  there so the first consumer reads the right panel.
- **§5.0 row 32 (6) closes with this** — left untouched here because #666 also edits that row; it is
  struck once both land.
- **Not CI-validated** — the `gate` workflow has failed on Actions billing since #652.
