# Fidelity coding taxonomy (fixed 2026-11-05, before any coding)

Unit: one claim from `claims.jsonl` (its `id`). Judge it ONLY against the page's own facts in
`corpus/data/dossiers/<T>/dossier.json` (mechanical layer, caveats, qa_flags, stock_info, anchor,
covenants, etc.). A claim is OK if every figure, date, period, direction and judgment in it is
supported by those facts as stated. Otherwise give ONE primary class (the most serious):

- SIGN — a figure's direction is wrong (gain called a cost, a decline called a rise, + read as −).
- PATH — a cumulative/endpoint change described as a state or as monotone ("every year", "never
  reversed", "without interruption") when the series in the facts has a reversal.
- PERIOD — wrong period (quarter vs LTM vs FY, wrong year, fiscal vs calendar).
- UNIT — wrong scale or unit ($M vs $B, x vs %, per-share vs total), or two different units compared.
- BASIS — GAAP vs adjusted/normalized, ex-lease vs not, levered vs unlevered, or company vs CIQ basis
  mixed or mislabelled.
- STALE — uses a value the facts mark superseded or older than another value the facts give.
- CONFLICT — the facts give two values for the same thing and the claim takes one without saying so.
- ABSENT — a figure or factual statement not present in the page's facts (outside knowledge,
  transcript-only prose, or invented).
- SELECTIVE — true figures, but a cherry-picked subset that the same facts contradict on balance.
- OVERREACH — a causal or judgmental conclusion the cited facts do not support.
- LABEL — repeats a misleading deterministic label from the facts (e.g. "gradual bleed" where
  the price rose, "trailing only" where forward multiples exist) as if it were fact.

For each non-OK claim also give:
- `material`: true if the error bears on the argument's direction or the decision, false if cosmetic.
- `favours`: "bull", "bear" or "neither" — which way the error pushes the reader.
- `fact`: ≤20 words naming the fact it contradicts or lacks, with its JSON path.
Write one JSON line per claim (OK claims too): {"id","verdict","material","favours","fact"}.
