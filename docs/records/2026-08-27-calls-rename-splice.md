---
id:
status: shipped
date: 2026-08-27
prs: []
supersedes:
superseded-by:
---

# A cashtag is not always a symbol: the `renamed` map finally gets read

**What was wrong.** `tickers.json` carried `{"SQ": "XYZ", "FB": "META", "TWTR": null}` and NOTHING
read it — `fetch_account_bars` passed the cashtag straight to Polygon, which serves each symbol
only for the span it was live. `$SQ`'s bars stopped dead at **2025-01-17**, the day Block became
XYZ, against a requested window running to 2026-01-09. Nothing said so: the file looked complete,
just short. This is the failure mode the house rule is about — not a missing value that announces
itself, but a truncated series that reads as a whole one.

**What shipped.** `_splice_rename` in `vinci/calls/bars.py`. A cashtag with a live successor is
fetched under BOTH symbols over the same window and joined. A `null` successor (TWTR) is the
cashtag alone — delisted, no handoff, an honestly short series.

The halves do not overlap in practice, so the join is a concatenation. Where they DO overlap the
cashtag's own symbol wins, but only after the closes are checked.

**Three guards, because a bad splice is a CONFIDENT WRONG ANSWER, not a gap** — one clean price
history stitched from two different companies, indistinguishable from a real one forever after.
Each RAISES:

| guard | bound | what it catches |
| --- | --- | --- |
| handoff gap | ≤ 10 calendar days | a suspension or the wrong successor, not a rename |
| seam move | ≤ 50% | an unadjusted split or the wrong symbol |
| overlap agreement | closes within 1% | two symbols that are not one security |

Both bounds are FACE-VALIDITY, read off the real handoff, never tuned: SQ→XYZ hands over in 4
calendar days across the MLK weekend, and the seam is an ordinary session ($86.96 close →
$88.06 open, +1.3%).

**Provenance.** A spliced file records `renamed_to` and `spliced_at`, so a reader never has to
infer from a date why the ticker changed hands mid-file.

**Result: `$SQ` 153 → 398 bars**, the full 2024-06-10 → 2026-01-09 window, seam clean.

**HONEST SCOPE OF THE FIX — no number moved.** Every one of the 5 `$SQ` mentions PREDATES the
rename, so all 5 price anchors are unchanged and the one directional row (2024-10-10, whose
63-day horizon closed before the truncation) scores exactly as before. Zero status moves, zero
verdict changes, direction-correct stays 51.03%.

What it DID fix is the chart. After the last `$SQ` mention the file held **6** trading days; it now
holds **251**. Verified in the running tape: the `$SQ` card reads *"call of 2025-01-09 ·
2024-10-09 → 2026-01-09"* and draws candles a full year past the post, through the rename — the
$85→$45 fall of March 2025 and the recovery were simply not there before. And the mechanism is now
live, so the NEXT rename does not silently truncate.

**Pinned.** `tests/test_calls_bars.py` — the join, the two one-sided windows, overlap precedence,
one negative per guard, and three end-to-end pins through `fetch_account_bars` (a mapped cashtag
is fetched under both symbols and says so; a `null` successor is left alone; an unmapped ticker
still costs exactly one call). MUTATION-CHECKED, four separate mutations including reinstating the
original bug — each reddens exactly its own test.

**Not done.** `BRKB` is the same class of problem in punctuation form (Polygon wants `BRK.B`) and
would now be a one-line map entry recovering 6 rows. It is NOT a rename, and whether an alias
belongs in a map called `renamed` is a judgment left to the operator.
