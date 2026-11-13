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
  - Bare (`_bare_word`) means nothing before it but a function word, a verb of being, "total", a
    period, a year, a possessive or a clause break (`_BARE_BEFORE`, `_CLAUSE_BREAK`: a comma,
    colon, semicolon, dash, "(", a spaced " - " or a full stop). It never follows "of" or "from"
    ("cost of sales", "proceeds from sales").
  - And nothing after it but a verb, a preposition (never "per"), a conjunction, a few adverbs or
    the end of its clause (`_BARE_AFTER`, `_BARE_CLAUSE_END`, review round 1). So no compound is
    bare: "sales leverage", "the sales mix", "profit per share", "profit growth", "sales and
    marketing", "sales, general and administrative", "profit and loss" (`_BARE_NOT_AFTER`).
  - A bare word that opens its own clause belongs to that clause's figure, never to the figure
    before it: in "$8,425M (sales were $7,178M)" the $8,425M keeps EBITDA.
  - A QUALIFIED word still names no row and meets the cited fact. The committed syntheses write
    "open-market" (an insider's share sales), "European", "hip", "gross", "comp" and
    "same-store" before "sales", and "segment", "consolidated" and "U.S." before "profit". So the
    rule admits the words that are no modifier. A refusal of "comparable", "comp" and
    "same-store" alone, as the re-review proposed, would have bound "open-market sales" to
    Revenue (pinned).
- **`_shares_row`, the comparison guard, had no pin.** It stops a period carrying onto a figure
  whose row another figure of the claim shares. With it off every test passed, and TJX's correct
  "FY26 revenue was $60,372M, up 7% on $56,360M" refused FY25's $56,360M as FY26's. Pinned. It
  now compares the rows THEMSELVES (equal, or both none), never their overlap, each set less its
  rate variants (`_base_rows`, review round 1: "revenue growth" names Revenue Growth and Revenue,
  and "a revenue base of $56,360M" Revenue, one comparison). A bare "profit" beside "EBITDA was
  $8,425M" is then another metric's figure, so #1040's pin "profit was $5,947M" (FY27E net income
  under FY26) stays refused.
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
- **Review round 1's 24 claims** (`rev1050_tools/cases.txt`, frozen TJX, TGT and NCNO), main
  against round 1's head:
  - every correct one reads as on main, but T5 ("up 7% on sales of $56,360M"), refused on main,
    which now traces;
  - every wrong one (F1 to F7) is refused, F3 to F5 for the first time (main passes them);
  - at `c06061d6` seven correct ones were refused (T1 to T4, T8, T10, T14).
- **How the committed mentions read.** Of the 54 "sales" and "profit" mentions (below), the rule
  at `c06061d6` read 8 as bare. Round 1 reads 2 as bare, and both mean revenue: SMPL's "FY26 sales
  decline" and TGT's "as sales recover". The other 6 are compounds or segment uses: BURL's "sales
  productivity", IT's "sales engines" twice, MCK's "profit growth", "the profit split" and "where
  profit actually sits".
- **Tests,** in `tests/test_figure_trace_false_flags.py`, each on a frozen page:
  - `test_a_bare_word_names_its_rows_on_tjx` fails at `fd1c97f3`, as does `/code-review`'s
    `test_a_bare_word_reads_its_own_clause_and_compound_on_tjx`;
  - (round 1) `test_a_bare_word_is_no_compound_on_tjx_tgt_and_ncno`,
    `test_a_rate_row_and_its_amount_row_are_one_comparison_on_tjx` and
    `test_a_bare_word_after_a_possessive_a_parenthesis_or_a_dash_on_tjx` fail at `c06061d6`;
    `test_a_bare_word_after_a_period_or_a_year_on_tjx` passes there and fails with the period and
    year lead removed;
  - `test_the_comparison_guard_keeps_a_shared_rows_every_column_on_tjx` passes at `fd1c97f3` and
    fails with the guard off;
  - `test_a_claim_must_lie_inside_the_print_on_frozen_pages` passes at `fd1c97f3` and fails with
    the guard off.
- **Mutants**, each removed by hand on this branch, fail a pin: the bare rule, the allow-list
  (replaced by a refusal of comp words), the clause break, "sales and marketing", the comparison
  guard, the guard by overlap (#1040's round-1 form) and the inside-the-print guard; and (round
  1) the rate variants kept, the word after not read, SG&A and P&L not refused, the possessive
  (not read, or read without its apostrophe), "(" and " - ", the clause-opening rule and the
  period and year lead.
- **No synthesis request moves.** The trace reads the draw and writes nothing the model is sent.
  The impact check (`python -m vinci.impact run`) is in the PR body.

**BOUNDARY.** The corpus is the 27 `data/dossiers/*/dossier.json` with a synthesis (2,201 claim
figures) at main `fd1c97f3`, re-validated on 2026-11-13; "flags" are `_validate`'s whole list. The
four cleared flags are that corpus with the inside-the-print condition removed (474 → 470). The
word counts are every "sales" or "profit"/"profits" token (`_WORD`, case-folded) in those 27
syntheses at round 1's head (corrected in review round 1; the first count, 26 and 20, read a
regex that missed a mention starting its text):
- claims (bull and bear points, evidence for and against): sales 26, profit 12;
- with the key unknowns and the decisive question: sales 29, profit 24;
- with `evidence_balance` too: sales 30, profit 24 — 54 mentions, the population the bare
  classification above reads.

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
- **What may follow a bare word is a closed list** (`_BARE_AFTER`). A verb it does not hold
  ("sales soared to …") leaves the word unbound, as on main, so another metric's figure there
  passes. On the 54 committed mentions the word after un-bares 6, none of which means revenue.
  Revenue meant through a qualifier stays unbound, as at `c06061d6` and on main: SMPL's "13–17%
  sales drop" (its question) and "guided sales decline" (its evidence balance).

**REVIEW ROUND 1** (an independent review at `c06061d6`, FIX FIRST; one fix commit):
- the comparison guard's equality refused correct growth-on-base claims main passed (FIXED,
  `_base_rows`);
- "bare" read only the word before, so a compound was bare: 2 of 8 committed bare readings meant
  revenue (FIXED, the word after; 2 of 2 now);
- the amendment and the extraction version still said a bare "profit" drops the rows a claim
  names, which `/code-review`'s finding 3 had removed (FIXED, both texts);
- the period and year lead had no pin (FIXED, pinned);
- a possessive, "(" and a spaced " - " broke no clause, as on main (FIXED, pinned);
- this record's word counts did not reproduce (FIXED, re-counted with the boundary above).

**NOT DONE.** No committed page is rebuilt; the next build of each prints the caveats. STATE.md
is untouched: no §5.0 row opens or closes.
