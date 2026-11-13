---
id: 2026-11-13-w05-followup-bare-sales-and-profit
status: shipped
date: 2026-11-13
prs: [1050]
supersedes:
superseded-by:
---

# The figure trace reads a bare "sales" as Revenue and a bare "profit" as a profit row, so another metric's figure under either word is refused; its comparison guard and its inside-the-print guard get pins; on the 27 committed pages no flag moves (W05 follow-up, the re-review of #1040's round 1)

**WHAT.** The independent re-review of #1040 at `40ae6410` said MERGE and left three LOW items, all
in the synthesis figure trace (`vinci/dossier/synthesis.py`). Built from main `fd1c97f3`:

- **A bare "sales" or "profit" named no row** (`_claim_rows`). Its figure met every row of the
  period carried to it, so TJX's "FY26 EBITDA was $8,425M while sales were $7,178M" passed:
  $7,178M is EBIT's figure. So did "profit was $60,372M" (revenue's).
  - A BARE word now names rows (`_BARE_ROWS`). "sales" names Revenue. "profit" names the profit
    rows, EBITDA, EBIT and net income, because the word does not say which; its figure meets any
    of them and no other.
  - Bare means nothing before it but a function word, a verb of being, "total", a period, a year
    or a clause break (`_BARE_BEFORE`, `_CLAUSE_BREAK`). It never follows "of" or "from" ("cost
    of sales", "proceeds from sales"), and is never "sales and marketing" (`_BARE_NOT_AFTER`).
  - A QUALIFIED word still names no row and meets the cited fact. The committed syntheses write
    "open-market" (an insider's share sales), "European", "hip", "gross", "comp" and
    "same-store" before "sales", and "segment", "consolidated" and "U.S." before "profit". So the
    rule admits the words that are no modifier. A refusal of "comparable", "comp" and
    "same-store" alone, as the re-review proposed, would have bound "open-market sales" to
    Revenue (pinned).
- **`_shares_row`, the comparison guard, had no pin.** It stops a period carrying onto a figure
  whose row another figure of the claim shares. With it off every test passed, and TJX's correct
  "FY26 revenue was $60,372M, up 7% on $56,360M" refused FY25's $56,360M as FY26's. Pinned. It
  now compares the rows THEMSELVES (equal, or both none), never their overlap. A bare "profit"
  beside "EBITDA was $8,425M" is then another metric's figure, so #1040's pin "profit was $5,947M"
  (FY27E net income under FY26) stays refused.
- **The inside-the-print guard had no frozen pin.** It holds a claim that traces to an exact value
  inside a coarse print to lie inside that print too. Only the corpus invariant on IT's living
  page caught its removal. Now pinned on two frozen pages:
  - SMPL's margin trend prints the LTM gross margin "33%" beside an unrelated $32.5M, so "32%" is
    refused;
  - VITL's cross-section prints the peer median P/E "16.7x" beside an unrelated 16.75, so "16.8x"
    is refused.
  Removing the guard clears four TRUE flags on the committed pages, not the three #1040's record
  named: CNXC "2.6", MCK "2.25", VITL "1.5" and IT "-1.5". That record is corrected by a dated
  amendment.

**WHY.** A relaxation that passes a wrong figure removes the caveat the reader most needed. Bare
"sales" was the one word of #1040's (a) that still let another metric's figure through on the
carried period. The two guards were each a single deletion away from clearing true flags with
the suite green.

**HOW VERIFIED.** All at $0.
- **The committed corpus, re-validated** with main's code (`fd1c97f3`) and this branch's: **474
  flags at both, the same set.** The class is latent on today's pages.
- **The re-review's 15 claims** (`cases_r1.json`): n1 ("sales" carrying EBIT's figure) is now
  refused; the other 14 read as on main.
- **Tests,** in `tests/test_figure_trace_false_flags.py`, each on a frozen page:
  - `test_a_bare_word_names_its_rows_on_tjx` fails at `fd1c97f3`, as does `/code-review`'s
    `test_a_bare_word_reads_its_own_clause_and_compound_on_tjx`;
  - `test_the_comparison_guard_keeps_a_shared_rows_every_column_on_tjx` passes at `fd1c97f3` and
    fails with the guard off;
  - `test_a_claim_must_lie_inside_the_print_on_frozen_pages` passes at `fd1c97f3` and fails with
    the guard off.
- **Mutants**, each removed by hand on this branch, fail a pin: the bare rule, the allow-list
  (replaced by a refusal of comp words), the clause break, "sales and marketing", the comparison
  guard, the guard by overlap (#1040's round-1 form) and the inside-the-print guard.
- **No synthesis request moves.** The trace reads the draw and writes nothing the model is sent.
  The impact check (`python -m vinci.impact run`) is in the PR body.

**BOUNDARY.** The corpus is the 27 `data/dossiers/*/dossier.json` with a synthesis (2,201 claim
figures) at main `fd1c97f3`, re-validated on 2026-11-13; "flags" are `_validate`'s whole list. The
four cleared flags are that corpus with the inside-the-print condition removed (474 → 470). The
word counts are every "sales" (26) and "profit" (20) mention in those 27 syntheses' claims, key
unknowns and questions, read with the word before each.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A bare "profit" may be any profit row.** "FY26 net income was $5,494M and profit was $8,425M"
  traces on EBITDA's figure. Falsifier: a rebuilt page whose bare "profit" is a different row's
  figure than the one it meant.
- **A qualified word still meets the cited fact's period.** "European sales" or "segment profit"
  is not held to Revenue or to a profit row, so a wrong segment figure that happens to equal
  another row of its period passes. The table holds no segment rows to bind it to.
- **The claim-wide path is unchanged.** A figure read from a literal (a computed figure's input)
  binds every row the claim names, and a bare word names none there, as on main.
- **A word placing a figure in another period releases it to every column** (#1040's stop words).
  So a wrong year's figure after "versus prior-year" passes: the re-review's n8, FY27E's revenue
  written there. It is unchanged here and outside these three items.

**NOT DONE.** No committed page is rebuilt; the next build of each prints the caveats. STATE.md
is untouched: no §5.0 row opens or closes.
