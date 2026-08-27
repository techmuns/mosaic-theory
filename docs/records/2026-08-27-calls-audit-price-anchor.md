---
id:
status: shipped
date: 2026-08-27
prs: []
supersedes:
superseded-by:
---

# The audit workbook carries the price the post was written against

**What was wrong.** A post reading `$SPY best case scenario is $530 today` is a BULLISH call if
$530 sits above spot and a BEARISH one if it sits below, and NOTHING on the audit row said which.
The original machine labeller read that exact post (2024-08-06) as `bearish`; the adopted second
reading called it `bullish`. Both are defensible from the text alone. Neither the operator nor a
reviewer could settle it without leaving the sheet.

**What shipped.** `vinci/calls/sheet.py` grows a sixth band, `COLS_PRICE`, joined from the
committed bars (no network, no new fetch):

| column | meaning |
| --- | --- |
| `px_at_post` | the last regular-session close that had ALREADY PRINTED when the post went out |
| `px_session` | the session that close came from — so the anchor is never anonymous |
| `px_close` | the post's OWN session close, carried separately, only where it postdates the post |
| `target_gap` | signed distance from `px_at_post` to the target the scorer used |

**The anchor never reaches forward.** For an intraday post the anchor is the PRIOR session's close.
Anchoring to the post's own close would let the outcome colour the reading — the same
contamination the fund's no-backtest rule exists to prevent, at row scale. `px_close` carries that
number in its own column, labelled, where the reader wants it.

**Half-days are not modelled.** A 13:00 ET close is treated as 16:00, so on those few afternoons
the anchor falls back one session. It is never a price that had not printed, and `px_session`
always names the session, so the fallback is visible rather than silent.

**No bars, no price.** 7,922 of 8,185 rows are anchored. The 263 blanks are all rows whose ticker
has NO bars file at all (214 of ~414 mentioned tickers were ever fetched); ZERO rows fell blank
because the post predated its window. A blank cell, never a borrowed or guessed price.

**How verified.** Real corpus, not fixtures. The four post-timing classes each resolve correctly
across all 8,185 rows — after-close 3,731, intraday 3,700, pre-market 102, weekend 652 — with zero
rows carrying a `px_close` they should not have. The $SPY row above anchors at **$517.38**
(Aug 5 close), putting his `$530` **+2.4% ABOVE spot**: the adoption's `bullish` is right and the
machine's `bearish` was wrong, now visible without leaving the row.

**Pinned.** `tests/test_calls_sheet.py` — five timing cases, an explicit LOOKAHEAD pin
(`test_an_intraday_post_never_anchors_to_its_own_close`), four blank-not-guessed negatives, and one
end-to-end pin through `build_sheet` asserting the band and the gap land in the workbook.
MUTATION-CHECKED: reintroducing the lookahead (`cutoff = posted.date()`) reddens 4 tests; the pin
bites rather than merely passing.

**Also carried to the local review bench** (scratchpad, not a product surface): the same four
values render as a price strip under each post, and the outcome row's target gains
`(+2.4% above spot)`.

**Open.** 200 mentioned tickers have no bars; fetching them is real Polygon quota for rows that are
mostly flow-list mentions, so it is NOT done — the operator's call.
