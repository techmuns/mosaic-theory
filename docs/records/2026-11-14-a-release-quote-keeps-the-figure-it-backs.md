---
id:
status: shipped
date: 2026-11-14
prs: [1074]
supersedes:
superseded-by:
---

# A release quote never ends before the figure it backs: a reconciliation actual's or a guide range's stored quote, over the 200-character cap, keeps its end and drops whole words from its start (#829); the window the guidance readers decide on is unchanged, and over the 117 releases on the 26 committed pages one stored quote moves, TJX's Fiscal 2027 EPS guide

**WHAT.**
- **The defect** (#829, deferred since 2026-10-28; STATE row 34). `release_parse._verbatim` snaps a quote back to its bullet or sentence start, joins it to the match's end, then kept the FIRST 200 characters. When the lead-in was long, the cut fell before the figure:
  - WERN's held build (2026-11-14) stored adjusted EPS −0.03 under "…non-GAAP diluted loss per share of" (8-K `0000793074-26-000165` EX-99.1), and `test_release_parse::test_committed_dossiers_carry_no_ratio_as_a_currency_amount` refused the page, so it was held (`docs/records/2026-11-14-rebuild-group-3-it.md`);
  - TJX's committed page stores its Fiscal 2027 GAAP diluted EPS guide, $4.93 to $5.02, under "…and diluted earnings per share to be" (8-K `0000109198-26-000004` EX-99.1).
- **The fix.** `_verbatim(…, keep_end=True)` keeps the window's END when it runs over the cap, and starts on the next whole word. Only the quotes STORED beside a match that ends at its figure ask for it:
  - the reconciliation actuals (three sites);
  - the guide ranges, level and change basis (`_admit_range` now takes the stored `quote` apart from the decision window `vb`).
- **What does not move, on purpose:**
  - **The decision window.** The guidance readers decide on `vb`: the period (`_period_for`), a superseded or withdrawn guide, a sub-line, the metrics a sentence names. The first draft changed `vb` itself, and TJX's Fiscal 2027 guide vanished with no flag, because its period is read from the sentence's opening words. `vb` is main's, byte for byte.
  - **One-offs, event impacts and drivers.** Their match runs past the figure to an arbitrary context cut ("…ingredien", "…ended Jun"), so keeping the end would only drop the sentence's opening. On the corpus their figures are stated in their quotes today, and they keep the start.
  - The refusal messages and the outlook fallback, which back no stored figure.
- **A new vintage,** `2026-11-14.a-release-quote-keeps-the-figure-it-backs`, with `release_parse.py` re-pinned.

**WHY.** A quote is the reader's way to verify a figure without trusting the summary (CLAUDE.md, source-bind everything). One that stops before its figure cannot be verified, and the currency-evidence invariant refuses it.

**HOW VERIFIED.**
- **The corpus first,** before any synthetic case:
  - **On the committed pages at main `6652a242`:** 448 release figures are stored beside a quote. 2 are not stated in it, both cut at the cap: TJX's Fiscal 2027 guide bounds, 4.93 and 5.02. EPAM's and VRRM's cut figures (row 34's 2026-10-28 count: EPAM 1, TJX 2, VRRM 2) are no longer on their pages, both having been re-assembled since.
  - **Base code against head code,** every EX-99.1 release cited on the 26 committed pages, read from the SEC cache only (118 accessions cited; 117 releases parsed, 329 stored items; GOOGL's 8-K `0001652044-26-000043` is cited on its page but is in neither cache, and it carries 0 stored items, so no result changes):
    - 1 stored quote moves, TJX's guide, from "…and diluted earnings per share to be" to "…share to be in the range of $4.93 to $5.02";
    - no value, period, unit, item count or qa flag moves.
  - WERN's held page is not committed, so it is not in that count. Its row re-quotes on the fixture below.
- **Fail first:** two tests on real text and one synthetic. `tests/fixtures/release_verbatim_cap/cases.json` holds the WERN and TJX passages as `normalize_text(html_to_text())` reads them from the SEC cache.
  - `test_a_reconciliation_figure_is_quoted_with_its_figure` (WERN −0.03): red at base.
  - `test_a_guide_range_is_quoted_with_both_of_its_bounds` (TJX 4.93/5.02): red at base; red too under the first draft, where the guide disappeared.
  - `test_a_long_window_keeps_its_end_and_starts_on_a_whole_word` (synthetic): red at base.
  - Negative pins, green at both:
    - `test_a_quote_that_fits_the_cap_is_unchanged`: WERN's 21.0 and 0.16 rows and TJX's first-quarter guide, each pinned to main's exact quote;
    - `test_the_window_the_guidance_readers_decide_on_still_keeps_its_start`.
- **The gate** (`bin/commit`, committing `bf41f93d` only on exit 0, in a clean worktree with no git-ignored data): ruff clean, `mypy --strict` clean on 219 files, 11,373 passed, 661 skipped, 11 xfailed, 0 failed, and the mirror in sync.
- **The cross-setup section** (`python -m vinci.impact run`, head `bf41f93d`, patch-id `a9300b95`):
  - 3 of the 5 tests fail at base and pass at head;
  - of 25 pages built at $0, 2 move, one field each: TJX's guide quote, and WERN's −0.03 quote, which now ends "…non-GAAP diluted loss per share of $0.03" (WERN's $0 build reads 8-K `0000793074-26-000165`, which its committed page does not cite);
  - 0 synthesis requests differ, so no row-53 panel check is owed; 0 committed pages re-render differently.

**THE ROWS ROW 34 NAMED.**
- **TJX:** re-quotes only on a re-assembly, which is paid. The $0 release refresh (`refresh.release_figures_transform`, `vinci/dossier/refresh.py:931`) re-reads actuals only: "GUIDANCE is not re-read" (#1074's review ran it on TJX's committed page from the cache, and the quote stayed cut).
- **EPAM and VRRM:** carry no cut figure on their committed pages today, so there is nothing to re-quote.
- **WERN:** re-quotes on a $0 refresh of its held build, the next step (coordinator: "(b) now, then (a)").

**BOUNDARY.**
- **Code:** main `6652a242`.
- **Pages:** the 26 committed `dossier.json` at `6652a242`.
- **Releases:** the SEC cache as of 2026-11-14, read only; no network call.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- A stored quote over the cap now opens mid-sentence. The period and the metric stay readable from the row's own fields.
- **DEFERRED, review round 0:** the paired-range second quote (`vb2`) still keeps its start.
  - The review's fork changed it and added a test that names itself SYNTHETIC.
  - Measured with the fork's code, the corpus moves exactly as with this PR's: 1 of 329 stored items, TJX's guide. So no committed quote is cut on that path.
  - A latent fix with no observed case is hardening, so the edit and its test were reverted.
  - It is real on synthetic text: #1074's review stored a quote ending before its high bound from a 262-character paired sentence. On real text: 1 paired range, 84 characters, in the 117 releases on the committed pages (the review: 1 in 185 cached exhibit-99 files). Accepted as a risk, named in STATE row 34.
- **Shipped with no observed case and no pin** (#1074's review, re-run here by mutation): removing `keep_end=True` at `release_parse.py` lines 1361 and 1387 (two more reconciliation patterns), 2757 (the second level-guide loop), or 2805 and 2840 (the change-basis guides) leaves every test green. They apply the same rule as the two pinned sites (1300, WERN's row; 2702, TJX's guide), and no committed quote is cut at them.
