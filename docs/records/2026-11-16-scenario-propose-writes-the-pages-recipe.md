---
id:
status: shipped
date: 2026-11-16
prs: [1083]
supersedes:
superseded-by:
---

# `scenario-propose` writes the page's recipe: an R3 page gets the P/E basis, the EPS and multiple cells and no fact, so GOOGL's template reaches `scenario-create` with no hand edit (§5.0 row 10)

**WHAT.** An R3-tagged page now gets an R3-shaped template (`propose.build_r3_template`). Every
other page keeps its template unchanged.

| part | the R3 template now | what main wrote on an R3 page |
|---|---|---|
| recipe, basis | `R3_forward_pe`, `P/E`, read from `scenarios.BASIS_PE`, the constant `_run_r3` checks | `R3_forward_pe`, `EV/EBITDA` |
| leg cells | `eps` and `multiple`, each EMPTY with its reason and a required `*_derivation`; the base leg's `years_to_terminal` and `leg_fy`, neither proposed; the bear leg's `bear_basis` | R1's cells: revenue, margin and multiple, with the base leg pre-filled (the consensus revenue median, the operating-margin median, and the own-history EV/EBITDA median 17.45x); empty `eps` and `ebit`; `margin_basis` on every leg |
| facts | none | `diluted_shares`, `d_and_a`, `net_debt` |
| evidence | keyed by R3's own axes. `earnings`: the page's R3 earnings basis, the EPS line CIQ's P/E is struck on, EPS (GAAP) and EPS Normalized consensus by fiscal year with their paths, the reported EPS arcs, every guidance row. `multiple`: today's P/E by period and at the page's price, the page's P/NTM EPS band (context only, with its note), the peer row. The operating drivers sit under both | R1's revenue, margin and EV/EBITDA frame |

The rule, set by face validity: where a recipe fixes its basis, the template writes the
validator's own constant, never a second copy of the string. The cells and facts then follow what
the recipe reads and what it refuses. `_run_r3` refuses a margin on a leg, and a `net_debt`,
`d_and_a` or `diluted_shares` fact (a P/E already prices equity per share). It refuses no missing
fact. This follows the R4 template's precedent (#691).

Three smaller changes, none moving an existing output:
- The R1 template's basis is now read from `midcycle.MULTIPLE_BASIS`, the constant `run_recipe`
  checks. It is the same string, so the output is unchanged.
- `scenario-propose`'s "N of M pre-filled" count reads `scenarios.axes_for`, so GOOGL's reads "0 of
  6" where it read "3 of 9". A hint that maps to no recipe keeps the R1 trio it always counted
  (CNXC's `R1_NOT_ROBUST`).
- R4's band evidence line is now written by one helper shared with R3 (`_band_line`). AMZN's R4
  template is byte-identical.

**WHY.** Row 10 has carried this since 2026-09-01: the validator was recipe-aware and the proposer
was not. GOOGL's R3 record was written by hand-correcting the template. Row 10 named two edits
(the basis and the revenue/margin stubs). The real run below shows that main needs three: the
enterprise facts were the third.

**R2 — NOT BUILT (coordinator, plan B).** Measured at main `b64be6f1` over the 26 committed pages:
- A page's R2 tag is `R2_NEEDED` (`anchor.RECIPE_R2`). The record's recipe is
  `R2_terminal_margin` (`terminal_margin.RECIPE_R2`), and no page carries that tag.
- `scenarios.axes_for` returns None for `R2_NEEDED`, and `run_recipe` refuses it as an unknown
  recipe. So a template that wrote the page's tag as its recipe could not be computed.
- NCNO is the only page tagged `R2_NEEDED`. It reads `applicable=False`, so
  `_refuse_if_recipe_unresolved` refuses it before any template is built. No committed page
  reaches an R2 template.
- `scenario-create` never carries `survival_input` into the record it builds, and `_run_r2`
  requires one. So no R2 record can be created through create, whatever the template says.

Building R2 now could be shown only on a page re-tagged in memory, and it would add a create
refusal that no real run exercises. That would be a speculative build. The coordinator decides
whether R2 gets its own build.

**HOW VERIFIED.**
- **Every other template is unchanged.** Templates were built for all 26 committed pages with
  main's code and with this branch's. They are byte-identical, refusals included, on 25 of 26:
  16 build and 10 refuse on both sides. GOOGL is the one that moved.
- **The shown run, stage 1: the template as proposed.** `scenario-propose` and then
  `scenario-create` ran through the CLI in a scratch directory, with an empty `scenarios/`.
  - GOOGL on the branch: 7 refusals, every one an empty-by-design cell (`eps` and `multiple` on
    three legs, and the base horizon).
  - GOOGL on main: 6 refusals. The base multiple was not among them, because the template's
    `EV/EBITDA` basis let the own-history EV/EBITDA median "anchor" a P/E cell.
  - BURL, an R1 page: the same 7 refusals on both sides.
- **The shown run, stage 2: the template filled.** The empty cells were filled with GOOGL's
  COMMITTED record's own analyst inputs (`scenarios/GOOGL.json`: its EPS, P/E, horizon, bear basis,
  reasons and derivations). The one value that record does not state is its entry window, since it
  predates the field (#658). The base leg's own year was used, labelled as a run value. Every
  record went to the scratch directory, and none is committed.

  | side | hand edits | `scenario-create` |
  |---|---|---|
  | main | none | REFUSED: base multiple 24.5 "deviates from its anchor 17.4518x" (the EV/EBITDA median) |
  | main | basis → `P/E` | REFUSED: R3 "carries fact 'net_debt'" |
  | main | basis, facts dropped | REFUSED: the base leg "stating margin 0.262717" |
  | main | basis, revenue/margin cells dropped, facts dropped | written |
  | branch | none | written, `facts: {}` |

  The branch's record values each leg at the committed record's own figures: $315.45, $397.41 and
  $432.87. No create check refused a missing fact. Its verdict reads `pending_analyst`. Its
  reward:risk reads UNDEFINED because the page's 2026-11-11 close ($293.45) sits below the
  committed bear ($315.45). That is the committed legs' arithmetic at today's close, not an
  underwrite.
- **The committed record agrees with what the template pre-fills.** `ticker`, `recipe_id`,
  `multiple_basis` (`P/E`) and `facts` (`{}`) all agree.
  - The spot fields differ by design: the template takes the page's close (2026-11-11, $293.45),
    and the record carries its own (2026-08-31, $339.35).
  - The template pre-fills no leg value.
  - The committed record states a horizon (1.0) on all three legs. The template offers that cell
    on the base leg only, as R1's and R4's do. Create carries a bear or bull horizon if the
    analyst adds the key.
- **Tests** (`tests/test_r3_template.py`, 8, on the living GOOGL page and the committed record):
  - 6 fail on main and pass on the branch: the basis and cells; no fact; the settable fields; the
    propose count; create on the empty template refusing only the empty cells; and propose → fill
    → create writing the record with no hand edit.
  - 2 pass on main by design, and a mutant kills each. One pins that R1's and R4's shapes are kept
    across the corpus. The other pins the scope: an R3 page whose R1 bit is False is still refused.
  - `test_r4_template`'s GOOGL case pinned main's R1 shape on an R3 page, which was the defect.
    That case is moved here; its SMPL case is unchanged.
- **Mutation.** Ten mutants, all killed:

  | mutant | tests failing |
  |---|---|
  | an R4 page takes the R1/R3 path | 13 |
  | an R3 page gets the R1 template | 6 |
  | `scenario-propose` counts R1's trio | 3 |
  | the R1 template writes an empty basis | 2 |
  | the R3 template writes R1's basis | 2 |
  | the R3 template emits a share fact | 2 |
  | the R3 template emits a margin cell | 1 |
  | the R3 `leg_fy` pre-filled from the EV-gap year | 1 |
  | the R3 evidence keyed by an axis R3 does not model | 1 |
  | R3 dispatched before the applicable refusal (R4's exception widened) | 1 |

**BOUNDARY.**
- **Population:** the 26 committed dossiers and 7 committed scenario records at main `b64be6f1`,
  measured 2026-11-16.
- **GOOGL's page history:** the 37 commits touching `data/dossiers/GOOGL/dossier.json` from
  2026-08-31 to 2026-11-16, read at `b64be6f1`.
- **Units:** EPS in $ per share, P/E in turns, values in $ per share.
- **The shown run:** each side's code read the committed pages at `b64be6f1`, and records were
  written into a scratch directory only.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **R1's `applicable` bit still gates an R3 page. Unchanged, the other half of row 10.**
  - `check_tier_agreement` refuses an R3 record on a page whose R1 bit is False.
  - `_refuse_if_recipe_unresolved` refuses the template there before the R3 branch is reached.
    Its message still calls the template "R1-shaped", which is now true of R1 pages only.
  - It is dormant on the corpus: 30 of GOOGL's 37 committed page versions are R3-tagged, and all
    30 read `applicable=True`. The 3 versions that read False are R1-tagged.
  - Pinned both sides: `test_an_r3_tag_keeps_the_applicable_coupling` (create) and
    `test_an_r3_page_whose_r1_bit_is_false_is_still_refused` (propose).
- **Found, not fixed.**
  - `validate_legs` attaches R1's reason table to any empty cell. So create's refusal for an empty
    R3 or R4 bear or bull multiple cites R1's own-history EV/EBITDA reason. R4 has done this since
    #691. The text is wrong; the behaviour is not.
  - CNXC's `R1_NOT_ROBUST` tag still gets the R1 template with that tag as its recipe.
    `run_recipe` refuses it as unknown.
  - The R1 template's empty `eps`/`ebit` cells, and the comment beside them, assume the analyst
    may choose another recipe. `check_tier_agreement` refuses a non-R1 record on an R1-tagged page.
- **Falsifier.** The next R3 name needs a hand edit to its template before `scenario-create`
  accepts it.
