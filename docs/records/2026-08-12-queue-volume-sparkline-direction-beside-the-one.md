---
id: 
status: recorded
date: 2026-08-12
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

### QUEUE VOLUME SPARKLINE — direction beside the one-session number (2026-08-12, operator-asked)

The audit's finding 2 was that the volume band is a ONE-SESSION reading that flips 43% of the time,
and the fix so far was a DISCLOSURE (a header tooltip saying so). The operator asked the better
question: show the series instead. A number can only say *today*; a line says *which way*.

- **New extracted field** `PriceFeatures.volume_trend` (`vinci/eod/features.py`) — 13 weekly means
  (5 sessions each ≈ one quarter, matching the months-to-quarters hold), oldest→newest, each on the
  **same 90-day denominator `volume_spike` uses**, so the sparkline and the number share a unit.
  Emitted only with a full 65 sessions: a half-length trend line reads as a shape rather than as
  missing data. Carried through `RankedCandidate.volume_trend`; **display-only, never a rank input.**
- **Weekly buckets, deliberately.** At ~46px a daily series of a small-cap is spike noise, and
  DIRECTION is what was asked for; the number beside it still carries the single day. The cost is
  that a one-day spike is averaged into its week — which is why both are shown, not one.
- **It DRAWS ONLY.** No "building"/"fading" word is derived from the series — that would be the same
  unearned mechanism claim the band labels were just retired for. Pinned: the render is scanned for
  direction words and reddens if one appears.
- **Verified on real tape before the frontend existed** (corpus-before-synthetic): run over 1,356
  cached grouped-daily days for five committed names. VRRM came back
  `[0.27, 0.31, 0.21, **3.70**, 1.31, 1.09, 0.92, 0.89, 0.53, 0.59, 0.38, 1.10, 0.83]` — the +22%
  spike week visible in the middle of an otherwise quiet quarter, which today's `0.72×` shows
  nothing of. VITL `3.27× → 0.65×` over the quarter. That is the information the single ratio
  destroys.
- **DORMANT UNTIL THE NEXT SCREEN, not the next rank.** `volume_trend` is computed from BARS in
  `eod/features`, so it appears when the weekly job re-SCREENS — a `vinci rank` re-run cannot
  produce it from the existing `candidate_records.jsonl`. Until then the cell degrades to exactly
  the pre-sparkline state (the bare ratio, no empty SVG), which is pinned as its own test.
- **Accessibility:** the SVG carries `role="img"` and an `aria-label` reciting the series, so it is
  not a silent decoration.
