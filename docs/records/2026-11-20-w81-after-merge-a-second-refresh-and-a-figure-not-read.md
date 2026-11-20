---
id:
status: open
date: 2026-11-20
prs: []
supersedes:
superseded-by:
---

# W81 after its merge (A's final review of #1147): the $0 LTM-cause refresh can run twice (SF1), a cause that cannot read EBIT or D&A says which and why instead of printing Python's None (NIT 4), and the cause's docstring cites 1-based rows (NIT 5); IN CODE, no committed page moves; SF2 and NIT 3 move request bytes and are recorded OPEN, unchanged

**WHAT.**
- **SF1, the refresh could not be run twice** (`vinci/dossier/refresh.py`,
  `refreshed_ltm_flags`).
  - It took the cause off the re-run (`bare`) and compared that with the page's stored LTM flags,
    cause and all.
  - So a second run, or a run on a page built at W81 (which carries the cause from its build),
    refused with "more than the cause would move; re-assemble instead". That is false, and it
    pointed at a paid re-assembly.
  - **The fix compares each held flag with the re-run, the cause off both sides.** A held flag
    may carry no cause, or a cause in any words where the re-run writes one
    (`ltm_quarters.carries_a_cause`: the flag's own text, then ". " and one of the two openings a
    cause has, `CAUSE_READ` / `CAUSE_NOT_READ`, now held once).
  - So a second run is a no-op, and a cause in older words is rewritten. Nothing else may move:
    a cause on a flag the re-run writes without one still refuses, and so does anything after
    the EBITDA flag's own words that is not a cause.
- **NIT 4, a cause that could not read a figure printed Python's None**
  (`ltm_quarters._ebitda_cause`, the "is not shown to be EBIT plus" branch). It read
  "(EBIT None, Income Statement row …" and "None, Cash Flow row absent".
  - Now each missing figure is named with its reason, in the export's words. Either "EBIT not
    read: the annual Income Statement carries no 'EBIT' row", or "EBIT not read: the LTM cell of
    Income Statement row 88 carries no figure ('-')", and the same for 'Depreciation & Amort.,
    Total' on the Cash Flow.
  - Where both are read, the words are as before: "(EBIT 6,707.0, Income Statement row 88;
    600.0, Cash Flow row 21; …)".
- **NIT 5.** `_ebitda_cause`'s docstring cited MORN's rows 80 and 82, which are the probe's
  0-based rows. The code prints 1-based rows, so the docstring now reads 81 and 83 and says so.
- **The vintage.** NIT 4 changes what a page can carry and SF1 changes what the refresh writes,
  so both modules are re-pinned under a new vintage,
  `2026-11-20.the-ltm-cause-names-a-figure-it-cannot-read`, which follows W81's. A page stamped
  with it still prints W81's names: `render.names_ebitdas_apart` reads `includes()`.
- **Recorded, NOT changed** (each moves request bytes, so each needs a panel measurement first):
  - **SF2.** The reconciliation's no-difference sentence (`vinci/dossier/ebitda_recon.py:481`)
    ends "— CIQ's four-quarter EBITDA is the filings' figure." even when it also says "(N of the
    four quarters could not be rebuilt)". Then the filings rebuilt no four-quarter figure
    (`filing_ltm` is None, as `len(built) != 4`), so the claim is not shown.
    - On the committed pages it is GOOGL (1 of 4) and LLY (3 of 4).
    - Their committed lines are old-vintage and make the same claim in the old words: "— the LTM
      the multiples divide is the reported figure."
    - After the $0 W81 refresh, LLY's line will carry the W81 wording, so the claim stays and
      only its words change.
    - LLY's frozen panel request carries the line in its FACTS (checked: the sentence is in the
      captured user text, JSON-escaped).
  - **NIT 3.** The four-quarter figure still prints as bare "LTM EBITDA" in two refusals:
    - `vinci/dossier/lease_basis.py:597`, "has no positive LTM EBITDA". It sits in
      `mechanical.valuation.lease_basis.refusal` on ORKA, TECX and VITL, and in VITL's
      `anchor.reason`. The layer is sent: `lease_basis` is not in `synthesis.NOT_SENT`.
    - `vinci/dossier/anchor_split.py:247`, "carries no positive LTM EBITDA". No committed page
      carries it.
  - Both are a STATE row 41 item: owner agent, unlocked by a row-53 panel measurement
    (RUNBOOKS §n) under an operator cap.

**WHY.** Coordinator A's final review of #1147 (2026-11-20) found these before the $0 refresh of
W81's pages. SF1 blocks that refresh from being re-run safely: a page refreshed once could never be
refreshed again without a false refusal. The refresh is its own artifact PR after this one merges.
NIT 4 and NIT 5 are words and a docstring. SF2 and NIT 3 change the facts the synthesis is handed,
so under row 53 they wait for a measurement rather than ride a $0 fix.

**HOW VERIFIED.**
- **Fail first, base `ddf0374c`:** 11 new tests in `tests/test_w81_two_ebitdas.py`. 8 fail on
  base:
  - SF1, 4: the second run on IT and VITL, the second `refresh_dossier` of IT end to end, and a
    cause in older words;
  - NIT 4, 4: EBIT '-', EBIT's row gone, D&A 'NA', D&A's row gone.

  The 3 that pass on base are negative controls: a held cause does not excuse a moved quarter; a
  cause on a flag that carries none refuses; a non-cause tail on the EBITDA flag refuses.
- **SF1 reproduced first, then fixed.** On base, the frozen IT page with the fixture bundle passes
  once, then its second run raises `RefreshRefusedError` ("4 held, 4 re-run; first difference: …
  The cause, read:"). VITL is the same with "Its cause was not read:".
- **Mutants: 8 of 8 red.**
  - Dropping the "the re-run writes a cause here" condition; accepting any tail after ". ";
    dropping the bare-equality branch; writing the bare flags back.
  - Dropping the quoted cell words; a 0-based row in the not-read words; dropping EBIT's lead
    word; a `None`-shaped missing-row reason.
- **On the live corpus** ($0; scratch copies of each committed page at `ddf0374c`, each against
  its own CIQ folder; `ltm_quarters_transform` run twice through `refresh_dossier`):

  | pages | head: run 1 | head: run 2 |
  |---|---|---|
  | IT, VITL | moved: the EBITDA flag gains its cause | no-op |
  | EPAM, GOOGL, LLY, NCNO, SMPL, TJX, VRRM, WERN | no-op | no-op |
  | BRBR | refused: the page records no annual Financials export | — |
  | MCK, WLK (watch) | refused: other LTM flags predate the quoting of '-' | — |

  - On base code (`git archive ddf0374c vinci`), IT and VITL move on run 1 and REFUSE on run 2.
  - Head's run-1 `qa_flags` equal base's on both.
  - No committed page reaches NIT 4's branch: the causes on the corpus are IT's named one and
    VITL's "does not reconcile".
- **`qa_flags` never reach the synthesis request** ($0 capture, no model call):
  - **By construction:** `capture_child.capture_calls` hands `synthesize` the mechanical layer
    only, and `qa_flags` sits at the top level.
  - **By bytes, on the panel's frozen pages** (freeze `bcda7ce3`, `replay.panel_inputs`):

    | page | qa_flags | variants | request wire sha256 |
    |---|---|---|---|
    | MCK | 47, an EBITDA DIFFER among them | as frozen; emptied; a NIT-4-worded flag added; the EBITDA flag given a cause | `c1034c71f4c4aaea` on all 4 |
    | LLY | 22, no EBITDA DIFFER | as frozen; emptied; a NIT-4-worded flag added | `40b9b18b1e944b88` on all 3 |

    The flag prefix `ciq-ltm-quarters:` appears in no request.
  - MCK's request is identical at base `ddf0374c` (`capture_at`) and head.
- **NIT 5's rows, on MORN's own exports** (Financials_Annual sha256 `fef17b2405`,
  Financials_Quarterly `b23ba84d1d`): the 'EBITDA' row is 0-based 80 / 1-based 81 on the annual
  Income Statement, and 82 / 83 on the quarterly.
- ruff, `mypy --strict` and `tests/test_w81_two_ebitdas.py` (116, 11 of them new) are green.
- **One existing pin generalised, not weakened.**
  `test_a_w81_page_names_both_figures_and_only_the_lease_line_moves` asserted that every other
  moved line prints W81's vintage id. It meant the version the stamp writes, which was W81's
  until this PR declared a later one. It now asserts `EXTRACTION_VERSION`. `names_ebitdas_apart`
  is still asserted true on the same page, so the stamp must still include W81.

**BOUNDARY.**
- **Code:** base `ddf0374c` (origin/main, #1147's merge); head is this PR.
- **Corpus:** the 13 committed pages above (the coverage roster's 11 active, plus watch MCK and
  WLK), at `ddf0374c`. Each was read against its own folder under `data/manual/ciq/<T>/` on the
  primary checkout, 2026-11-20.
- **SF2's count:** the 25 committed pages carrying `financial_summary.ebitda_reconciliation` at
  `ddf0374c`. 2 carry "could not be rebuilt", GOOGL and LLY, and both have `filing_ltm` None.
- **NIT 3's count:** every string field of the 26 committed `dossier.json` at `ddf0374c`.
- **The byte check:** 2 panel pages (MCK, LLY) at freeze `bcda7ce3`, one draw's request each (the
  request is per-draw identical, `replay._one`).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$0.** No model call. The captures use a recorder in place of the client.
- **SF2 and NIT 3 stay on the pages until each is measured and shipped.** LLY's page will carry
  SF2's claim in W81's words after the $0 refresh, as it carries it in the old words today.
  Falsifier: a reconciliation line saying the four-quarter figure is the filings' where
  `filing_ltm` is None. Today that is GOOGL and LLY.
- **A cause in older words is rewritten by the refresh, not refused.** That is the step's stated
  contract (only the cause moves). The flag's own text must still match the re-run exactly.
