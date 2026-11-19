---
id:
status: open
date: 2026-11-19
prs: []
supersedes:
superseded-by:
---

# W80: a $0 refresh may not move a basis-block figure the kept synthesis quotes; `refresh_dossier` refuses it, naming the figure (GOOGL's $144,827M); no page moves ($0, code + record)

**WHAT.**
- `refresh.moved_cited_basis_figures` joins the four guards `refresh_dossier` runs before it writes
  a refreshed page under a kept synthesis (`moved_cited_claims`, `_counts`, `_returns`,
  `_release_figures`).
- **What it watches:** the money figures of the two blocks `valuation_bases_transform` rewrites,
  plus the sum the basis line prints.
  - `valuation.ev_ebitda_basis`: `tev`, `implied_denominator`, `reported_ltm_ebitda`, `rent`.
  - `valuation.ev_ebitda_ex_lease_at_price`: `ev`, `net_debt`, `ltm_ebitda`.
  - Reported LTM EBITDA plus rent, the sum the basis line prints ("= $190,600M").
- **When it refuses:** when a figure moved, or vanished, and the stored prose cites its OLD value.
  "Cites" is dollar-anchored (`_total_cited`, the release guard's matcher). A value its OWN block
  still carries under another key is not a move, as for the release actuals. The other block's
  equal number does not mask one: TJX's reported and ex-lease LTM EBITDA are both $8,903M, with
  different meanings (review round 0).
- `refresh.py` is re-pinned as `refactor`: no page's content changes. The refresh writes the same
  page or refuses, as the watch-page refusal (5c9c7eac) was pinned.
- `moved_cited_claims` itself is unchanged. It reads the financial tables; the basis figures are
  a sibling, one block per guard, as the file's other three are.

**WHY.**
- **W65's GOOGL check found the gap (2026-11-19).** The $0 basis refresh read only the page's own
  stored inputs, proven identical with no CIQ store and with no EDGAR facts. It nulled the
  $144,827M quotient, and a scratch-copy `refresh_dossier` PASSED.
- **GOOGL's kept synthesis quotes that figure**, in `key_unknowns[3]`: "divides TEV $3,316,548M by
  an implied $144,827M denominator that reproduces NEITHER reported LTM EBITDA … nor EBITDA+rent".
  The page would have carried two explanations of one multiple: the Brief line (a 30-day date gap,
  not measured) and the old reading in the prose.
- **No guard saw it.** `material_figures` reads material financial-summary rows only, and the
  other three read counts, returns and release actuals.
- **Coordinator B held GOOGL** for a paid rebuild from the same-date export the operator added
  2026-11-19, rather than lean on the gap. The operator started W80 ("start W80").
- **Both blocks are watched, not one.** One transform rewrites both. On the committed pages, 13
  pages' prose quotes the ex-lease block (TJX its ex-lease EV, about $146.9bn), so leaving it out
  would keep the same blind spot one block over.
- **Does this select on form?** No. It compares a figure's value before and after, and the prose's
  words; it grades no evidence and ranks nothing.

**HOW VERIFIED.**
- **Real run, scratch copies of the committed pages at main `2ecf6da0`** ($0, nothing in the repo
  written):
  - GOOGL with the real `valuation_bases_transform` now REFUSES, naming
    `ev_ebitda_basis.implied_denominator = 144,827.4 → absent`; on main it passed.
  - `refresh_dossier`'s refusal check on every one of the 26 pages under a basis rebuild: the four
    old guards refuse 0 pages, and the basis guard refuses GOOGL alone.
  - AMZN's quotient ($184,739M) also vanishes, but its prose never quotes it, so it passes.
- **Corpus before the code.** 21 of the 26 pages' prose cites a basis figure dollar-anchored
  (mostly reported LTM EBITDA; 13 the ex-lease block too). A basis rebuild moves a figure on 2
  pages (AMZN, GOOGL), both `implied_denominator`.
- **Pins** (`tests/test_w80_refresh_guard_basis_figures.py`, 8, from real committed JSON at the cut):
  - **Positive:** GOOGL end to end (refused, figure named, file unwritten); only the moved figure
    named; TJX's ex-lease EV and GOOGL's printed sum, each one field moved on a real page.
  - **Negative:** IT end to end (one date: the rebuild moves no figure and the refresh writes the
    new fields); AMZN (a move its prose does not quote); a relabel within the block.
  - **Roster walk:** every refusal names a figure that moved.
  - **6 of the 7 FAIL on main `2ecf6da0`** (a full export of main, with `vinci` asserted to load
    from it). The GOOGL pin fails with `DID NOT RAISE RefreshRefusedError`. The seventh, IT's
    negative, passes on both, as a negative should. The eighth, from review round 0 (TJX's equal
    numbers in the two blocks), fails on the PR's first commit `9b46d523`.
- **Mutation: 8 of 8 mutants red:**
  - the guard not wired into `refresh_dossier`;
  - the quotient, the ex-lease block, or the printed sum not watched;
  - a relabel counted as a move;
  - unmoved figures checked;
  - the still-carried test spanning both blocks;
  - the citation test ignored.
- **Gate:** ruff (`vinci tests frontend`), `mypy --strict vinci` and the full
  `pytest -m "not network"` through `bin/commit`; `python -m vinci.impact run` is in the PR body.

**BOUNDARY.**
- **Pages:** `data/dossiers/*/dossier.json` at main `2ecf6da0`, 26 pages (every roster page).
- **Basis rebuild:** the head code's `headline_basis` on each page's stored mechanical layer, the
  block `valuation_bases_transform` writes, with no CIQ export and no EDGAR read (W65's input
  proof on GOOGL).
- **Citations:** `refresh._prose` (the synthesis claim lists and scalars), matched by
  `_total_cited`.
- **Measured** 2026-11-19.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **GOOGL stays as committed until its paid rebuild.** Its page keeps the "neither pairing" line
  and prose until then. The rebuild follows W73's code PR, and its cap is the operator's.
- **AMZN (watch) stays as committed,** under the operator's standing watch rule.
- **Review round 0 (`/code-review high --fix`), not applied:**
  - No money floor, unlike `moved_cited_claims`'s $10M. A small basis figure (NCNO's $8M rent)
    can match an unrelated "$8M" and refuse spuriously. That is the safe direction: it costs a
    re-assembly, never a wrong page. The release guard uses the same matcher with no floor, and a
    floor would also exempt real small figures (NCNO's $98M quotient).
  - A page-wide check (any quoted dollar figure must survive anywhere in the refreshed layer)
    would close the class instead of one more block. It changes every refresh's refusal semantics
    and needs its own corpus measurement: a build of its own.
- **A paraphrased figure is not caught.** The prose has to write the number ("$144,827M",
  "$144.8bn"). This is the limit `moved_cited_counts` states for its own figures.
- **Falsifier:** a basis refresh that passes while the page's prose quotes, in dollars, a basis
  figure the refresh removed.
