---
id:
status: shipped
date: 2026-11-19
prs: [1129]
supersedes:
superseded-by:
---

# The page body labels a prepayment or default term by its name's start. The combined target term prints as "Prepayment / events of default" and IT's sweep as "Mandatory prepayment". No prepayment prints as "Events of default", and every default line stays: 26 lines on 13 pages change their label only ($0, code + artifacts)

**WHAT.**
- **The matcher.** The curated covenant line in each page body labels a governing term from
  `_SUMMARY_TERMS`. Its last key was the substring "mandatory prepayment", labelled "Events of
  default" and matched anywhere in the term's name.
  - `vinci/dossier/render.py` `_summary_label`, and its mirror `summaryLabel` in
    `frontend/views/shared/dossier.js`, replace it with three keys. Each is matched at the START
    of the name, as #1128 did for the coupon, and the first match wins:

    | name starts with | page-body label |
    |---|---|
    | `mandatory prepayment / events of default` | Prepayment / events of default |
    | `mandatory prepayment` | Mandatory prepayment |
    | `events of default` | Events of default |

  - The first is the extractor's target term (`covenant_extract._TARGET_TERMS`). It asks two
    questions, so its label names both. A bare row is labelled with its own name.
  - The value never chooses a label. A classifier on LLM-composed text is an LLM-string pin in
    disguise (CLAUDE.md).
  - The value lead is unchanged. Both default-named labels keep the old lead: a contiguous 1..k
    enumeration count, and "acceleration" when the clause says so.
- **On the committed pages.** 26 page-body lines on 13 pages change their label only:
  - 25 lines, the combined target term, now read "Prepayment / events of default": BRBR 1,
    BURL 2, CNXC 3, EPAM 1, MCK 1 (its withheld, last-verified line), NKE 2, PARR 3, SMPL 1,
    TJX 4, UBER 1, WERN 2, WLK 4;
  - 1 line, IT's bare `Mandatory prepayment` row (a 50% net-cash-proceeds sweep), now reads
    "Mandatory prepayment".

  No "Events of default" label is left on any committed page. No appendix row or cell moves. No
  `dossier.json` moves.
- **The re-render.** It is committed in its own artifact commit, through the no-op refresh path
  (`refresh.refresh_fleet`): 26 files, `data/dossiers/<T>/dossier.md` and
  `frontend/dossiers/<T>.md` for the 13 pages, 52 lines changed.

**WHY.** #1128's review found it while fixing the coupon key, the same class of defect. The old
label named only the second half of the combined term, so a value stating only a prepayment read
as a default trigger. A reader takes a labelled page-body line as what the label says. The census
(BOUNDARY), reading each stored value by hand for the census only:

| class | lines | where |
|---|---|---|
| (a) a real events-of-default row under its own name | 0 print | IT's one `Events of default` row is UNKNOWN: E5 refused it |
| (b) a bare mandatory-prepayment row | 1 | IT's sweep |
| (c) the combined target term, value states both | 17 | BURL, CNXC ×3, EPAM, MCK, NKE ×2, TJX ×3, UBER, WERN, WLK ×4 |
| (c) … a prepayment only | 3 | BRBR (a repricing premium and a prepayment notice), PARR's asset-based revolver, SMPL (a voluntary prepayment) |
| (c) … a default only | 3 | BURL's security agreement, PARR's uncommitted agreement, WERN's loan and security agreement |
| (c) … neither (a reference or a no-default representation) | 2 | PARR's credit agreement, TJX 2022 |

So 4 lines printed a prepayment as an event of default (IT's sweep and the 3), and 20 state a real
default clause, which the fix had to keep.

**Options weighed.**
- **Picked: label each name by what it asks.** No prepayment can print as "Events of default", and
  all 25 combined lines still print.
- **"Events of default" only for names that start with or name it, alone.** The combined term
  names events of default. Keeping it under that label leaves 3 prepayment-only values reading as
  default triggers; dropping it from the body loses the 20 lines that state a real default clause.
  It survives only as the third key.
- **Choosing the label by the value:** rejected (above).

**HOW VERIFIED.**
- **Every page, both renderers, base against head.** Each of the 26 committed pages was rendered by
  base code (main e6a6c318) and by head code, in Markdown (`render_markdown` with the scenario
  card, as `refresh._rerender_only` calls it) and on the web (node, the production
  `renderDossier`).
  - The base render of every page equals its committed `dossier.md`.
  - 13 pages are byte-identical in both: AMZN, FUBO, GOOGL, LLY, NCNO, NFLX, ORKA, ROST, TECX, TGT,
    V, VITL and VRRM.
  - On the 13 that move, putting "Events of default" back for each new label makes every head
    file byte-identical to its base file, in Markdown and on the web.
- **Pins.** `tests/test_covenant_summary_label.py`, now 44 tests. The new ones read the 2026-11-17
  cut, which holds the same 26 values.
  - Matcher pins: 3 positives (the combined term, `Mandatory prepayment`, `Events of default`) and
    7 negatives, every name a committed governing row's: `Prepayment right`, `Repricing /
    prepayment premium`, `Repricing premium (prepayment-related)`, `No Default condition / Event
    of Default reference`, `Acceleration remedy`, `Cross-default threshold`, `Default Rate`. A
    further pin ties the combined key to the extractor's target term.
  - End-to-end pins in Markdown, 9 cases, one per census shape: IT's sweep; SMPL, BRBR and PARR,
    prepayment only; NKE, WLK's Term Loans Due 2026 and WLK's 2027 bonds loan, both; WERN and
    BURL, default only. (+) The value prints on exactly one line of its block, under its name's
    label, opening with its old lead (WLK 2027: "acceleration ·"). (−) No line of the block is
    labelled "Events of default". The appendix row keeps the value.
  - IT's UNKNOWN `Events of default` row: no page-body line; its appendix cell reads UNKNOWN.
  - The web, end to end on the same 9 cases: each block equals the Markdown block line for line,
    and the appendix cell matches.
  - A walk over every covered page, both renderers, phrasing-free: per family block, the lines
    under each of the three labels equal the shown rows whose names start with that key.
  - #1128's matcher row for the combined term now expects the new label.
- **Mutations.**

  | mutation | failing pins |
  |---|---|
  | Python matcher back to the substring rule | 17 |
  | JS matcher alone back to the substring rule | 3: both web parity pins and the corpus walk |
  | the combined label loses its value lead, Python / JS | 2 / 1 |
  | the three new keys matched anywhere, not at the start, both renderers | 0: survives (WHAT IT COSTS) |
- **Preview (PREVIEW RULE).**
  - On screen, base and head of each of the 13 pages: the web app's Analysis tab, every covenant
    block, collapsed and with every `<details>` opened (the blocks hold none); and the Appendix
    tab's covenant tables with every `<details>` opened, byte-identical base against head on all 13.
  - Print tier: headless Chrome "Full dossier" PDFs (`body.ds-print-full`, whose `@media print`
    CSS force-opens every `<details>`), base and head.
    - Page counts are unchanged on all 13.
    - With the labels put back, the PDF text equals base on 11. On PARR and UBER the longer label
      moves one line wrap, so a filing date breaks at its hyphen; nothing else differs.
    - The appendix page carrying each moved row is byte-identical base against head, rasterised.
  - The images are in the coordinator's notes folder, not in the repo.
  - **Approved 2026-11-19** by the operator, relayed by the coordinator: "Prepayment ／ events of
    default". The operator typed a full-width slash (U+FF0F). The label stays as built and
    previewed, with the ASCII "/". The coordinator kept the bare "Events of default" key and WLK's
    "acceleration ·" lead as built, by default.
- **The committed pages.** `refresh_fleet()` at main e6a6c318 plus this change reported moved 13,
  unchanged 13, refused 0 and skipped 0.
  - Each re-rendered page is byte-identical to the render the operator approved.
  - Each mirror equals its page.
  - Every one of the 26 files differs from main by label words only.
  - `frontend/build.py` leaves no further diff.
- **The suite.**
  - On the code commit alone, three page-staleness pins fail, the no-op refresh naming exactly the
    13 pages: `test_refresh_path::test_a_noop_refresh_is_byte_identical`,
    `test_dossier::test_analysis_tier_reads_in_decision_order_e2e` and
    `test_parity_pins::test_screening_context_reaches_every_committed_dossier_e2e`. The artifact
    commit clears them.
  - `bin/commit` ran the full serial gate: it ran twice on the artifact tree. Protected-file approval,
    ruff and `mypy --strict` pass; `pytest -m "not network"` gave 12,300 passed, 656 skipped,
    7 xfailed and 1 failed both times. The one failure is the pacing test below. The gate stops at
    its first red step, so its last step, the frontend-mirror check, was run by hand (in sync), and
    the artifact commit was made with `git commit`.

**BOUNDARY.** Every count is over the 26 covered pages, `data/dossiers/*/dossier.json`, at main
e6a6c318, which equals the 2026-11-17 cut on these 26 lines.
- A "line" is one curated covenant line in a page body: one governing term of one agreement family
  that the body prints.
- Row 63's earlier count (26 lines on 13 pages) was taken at main 65a8b863; e6a6c318 moved no such
  line.
- The class column reads each stored value by hand, for the census only.
- The name counts (WHAT IT COSTS) are over all 367 governing rows on the 26 pages, printed or not,
  appendix-only families included: 41 carry the combined target term exactly.

**FOUND, NOT CHASED.** `test_sec_pacing::test_two_processes_on_one_machine_share_one_budget` failed
on this branch three times: once under `pytest -n auto` on the code commit, and in both serial
gate runs on the artifact tree (`min gap 0.000s` and `0.001s across two processes`). It passes
alone, 5 of 5. It reads nothing this build touches. Per the coordinator, it is not this build's.
#1128 recorded it once, under `-n auto`; its serial gate passed.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0: no model call and no vendor pull.
- **ACCEPTED LIMIT: START OR ANYWHERE.** The three new keys match at the name's start, after
  #1128's coupon key. On the committed corpus that is indistinguishable from matching anywhere:
  the mutation survives every pin. Measured 2026-11-19 at main e6a6c318, over the 26 pages:
  - every governing name holding "mandatory prepayment" holds it at its start (42: the 41 combined
    and IT's bare row);
  - the only name holding "events of default" other than at its start is the combined term, which
    its own key takes first.

  Pinning it would need a synthetic name. FALSIFIER: a committed governing name holding "mandatory
  prepayment" or "events of default" other than at its start and outside the combined target term.
  That name is the real fixture the pin then takes.
- **ACCEPTED RISK: A RE-WORDED COMBINED NAME.** A combined row the model names otherwise
  ("Mandatory prepayments / events of default", "Mandatory prepayment/events of default") would
  print as "Mandatory prepayment", or not at all. Measured as above: 0 such names; all 41 combined
  rows carry the target term exactly. `_TARGET_TERMS` makes the model answer it on every exhibit.
  FALSIFIER: a committed governing name naming both a prepayment and events of default that does
  not start with "Mandatory prepayment / events of default". Recorded in STATE row 63 (INVARIANT
  RULE).
