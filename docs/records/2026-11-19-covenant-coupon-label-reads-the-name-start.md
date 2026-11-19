---
id:
status: shipped
date: 2026-11-19
prs: [1128]
supersedes:
superseded-by:
---

# The page body prints a covenant term as "Interest / coupon" only when its name starts with "Interest / coupon rate". Six lines leave the page bodies of IT, NKE, VRRM and WLK, and the appendix keeps every row ($0, code + artifacts)

**WHAT.**
- **The matcher.** The curated covenant line in each page body labels a governing term from
  `_SUMMARY_TERMS`. The coupon key was the bare substring "interest", matched anywhere in the
  term's name.
  - `vinci/dossier/render.py` `_summary_label`, and its mirror `summaryLabel` in
    `frontend/views/shared/dossier.js`, now match the coupon key, "interest / coupon rate", at the
    START of the name.
  - That is the extractor's target term (`covenant_extract._TARGET_TERMS`) or a qualified variant
    of it.
  - Every other key still matches anywhere in the name, as before.
  - Both former match sites use the one matcher: the page-body line, and the appendix row's value
    lead.
- **On the committed pages.** A default rate and an interest-payment date no longer print as the
  coupon. Six lines leave the page bodies of four pages:
  - IT, A&R credit agreement: `Default interest`;
  - NKE, 364-day agreement: `Default interest rate`;
  - VRRM, A&R revolver: `Default interest`;
  - WLK, A&R loan agreement: `Interest Payment Date`;
  - WLK, credit agreement: `Default interest`;
  - WLK, Term Loans Due 2026: `Interest Payment Dates`.

  Each row stays in its appendix covenant table under its own name, with an unchanged cell.
- **What stays.** IT's `Interest / coupon rate — Eurodollar Loans` and `— ABR Loans` lines still
  print. An exact-name test would have dropped them.
- **VRRM's revolver.** Its page-body block still prints, carrying its maintenance test. It prints
  no coupon line, because its own `Interest / coupon rate` row is UNKNOWN: E5 refused it
  (`2026-11-18-vrrm-rebuilt-after-the-move.md`). The appendix shows that row, and why.
- **The re-render.** It is committed in its own artifact commit, through the no-op refresh path
  (`refresh.refresh_fleet`): 8 files, `data/dossiers/<T>/dossier.md` and
  `frontend/dossiers/<T>.md` for the four pages. It removes 12 lines and adds none. No
  `dossier.json` moves.

**WHY.** VRRM's rebuild (#1121) found it: the only "Interest / coupon" line under VRRM's A&R
revolver was its default rate. A reader takes a labelled line in the page body as the coupon. The
JSON named every row correctly; only the label was wrong.

**HOW VERIFIED.**
- **Every page, both renderers, base against head.** Each of the 26 committed pages was rendered by
  base code and by head code, in Markdown (`render_markdown`) and on the web (node, the production
  `renderDossier`). The base was main 3586a864 for the preview and the merge base 65a8b863 for the
  impact run's re-render of the committed JSON (its part 4), with the same four pages and six lines
  at both; #1122 between them moved no page (BOUNDARY).
  - 22 pages are byte-identical in both.
  - The 4 that move lose exactly the six lines above, and nothing else, in both renderers.
  - The base render of every page equals its committed `dossier.md`.
- **Pins.** `tests/test_covenant_summary_label.py` holds 21 tests.
  - Matcher pins: 4 coupon names, positive, among them NCNO's hyphenated variant; 4 non-coupon
    names, negative; and 3 controls for the other keys. A further pin ties the coupon key to the
    extractor's target term.
  - End-to-end pins, Markdown and web, from frozen copies: each of the six agreements prints one
    coupon line per real coupon row, each found by its governing value. The non-coupon value is on
    no line of the page-body block, and its appendix row keeps it.
  - A Python↔JS block parity pin.
  - A walk over every covered page, phrasing-free: each family block prints one coupon line per
    shown coupon row, in both renderers.
  - IT, NKE and WLK read the 2026-11-17 cut. VRRM reads a new dated copy,
    `tests/fixtures/frozen_pages/2026-11-18/VRRM/`. It is #1121's page, blob `e8c6a28a`, held to
    that blob in the test, because the cut predates the rebuild.
- **Mutations.**

  | mutation | failing pins |
  |---|---|
  | Python matcher back to the substring rule | 12 |
  | JS matcher alone back to the substring rule | the web parity pin and the corpus walk |
  | an exact-name coupon match | IT's two qualified rows and the matcher pins for them |
- **Preview (PREVIEW RULE).**
  - On screen: base and head of each of the four pages, in the web app's Analysis tab. VRRM's
    appendix is shot collapsed, then with every `<details>` opened.
  - Print tier: headless Chrome "Full dossier" PDFs (`body.ds-print-full`, whose `@media print`
    CSS force-opens every `<details>`), base and head.
    - Page counts are unchanged: IT 20, NKE 17, VRRM 20, WLK 21.
    - The PDF text differs only by the six lines' words.
    - Coupon lines in print: IT 3 → 2, NKE 3 → 2, VRRM 2 → 1, WLK 7 → 4.
  - The images are in the coordinator's notes folder, not in the repo.
  - **Approved 2026-11-19** by the operator, relayed by the coordinator: "Approve as shown".
- **The committed pages.** `refresh_fleet()` at main 65a8b863 plus this change reported moved 4,
  unchanged 22, refused 0 and skipped 0.
  - Each re-rendered page is byte-identical to the render the operator approved.
  - Each mirror equals its page.
  - `frontend/build.py` leaves no further diff.
- **The suite.**
  - On the code commit alone, three page-staleness pins fail, naming exactly IT, NKE, VRRM and
    WLK: `test_refresh_path::test_a_noop_refresh_is_byte_identical`,
    `test_dossier::test_analysis_tier_reads_in_decision_order_e2e` and
    `test_parity_pins::test_screening_context_reaches_every_committed_dossier_e2e`. The artifact
    commit clears them, as #1084's did.
  - `bin/commit` ran the full serial gate on the artifact commit (ruff, `mypy --strict`, `pytest -m "not network"`, then the frontend-mirror check): 12,332 passed, 665 skipped, 7 xfailed, 0 failed, and it committed.

**BOUNDARY.** Every count is over the 26 covered pages, `data/dossiers/*/dossier.json`.
- The label census was taken at main 3586a864, and the re-render at main 65a8b863. #1122 moved no
  page.
- A "line" is one curated covenant line in the page body: one governing term of one agreement
  family that the body prints.
- The "Events of default" census below was taken at main 65a8b863 with this change, which does not
  touch that label.

**FOUND, NOT FIXED: THE "EVENTS OF DEFAULT" LABEL NAMES HALF OF ITS TERM.**
- The key "mandatory prepayment" prints "Events of default" for any name containing it.
- 26 lines on 13 pages print under that label: BRBR, BURL, CNXC, EPAM, IT, MCK, NKE, PARR, SMPL,
  TJX, UBER, WERN and WLK.
  - 25 are the combined target term `Mandatory prepayment / events of default`. The label names
    only its second half, so a value that states only a prepayment reads as an event of default.
  - 1 is IT's bare `Mandatory prepayment` row (its 50% net-cash-proceeds sweep).
- Examples, read from the stored values:
  - IT's sweep;
  - SMPL's clause, which states a voluntary prepayment and its repricing premium;
  - WLK's Term Loans Due 2026, the borrower's prepayment for the bonds' extraordinary mandatory
    redemption.
- The value lead `_covenant_value_lead` composes for that label counts enumerated items and an
  acceleration word, so it is a default-shaped lead.
- Routed to STATE §5.0 row 63 as a new ALSO OPEN clause, owner agent. It is unlocked by a $0 render
  PR and a preview: how the label should read is a wording call.

**FOUND, NOT CHASED.** `test_sec_pacing::test_two_processes_on_one_machine_share_one_budget` failed
once under `pytest -n auto` on this branch's code commit. It passes alone (8 of 8). Per the
coordinator, it is not this build's.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0: no model call and no vendor pull.
- **ACCEPTED RISK: the coupon prefix.** A real coupon row the model names otherwise, such as
  "Interest rate" or "Interest/coupon rate", would silently lose its page-body line; it would stay
  in the appendix. The corpus walk cannot catch it, because it derives its expected count from the
  same rule. Measured 2026-11-19 at main 65a8b863, over the 26 committed pages: 0 such rows. Every
  PRESENT governing term whose name contains "interest" or "coupon" and does not start with the
  target term is one of the six removed (6 of 6).
- Falsifier: a committed governing term naming a coupon that does not start with "Interest /
  coupon rate". `_TARGET_TERMS` makes the model answer the target term on every exhibit. Recorded
  in STATE row 63 (INVARIANT RULE).
