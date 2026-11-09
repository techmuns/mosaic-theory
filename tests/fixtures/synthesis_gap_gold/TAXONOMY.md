# The gap-framing taxonomy (M-GAP's gold) — frozen 2026-11-09, before any unit was coded

**Why it exists.** Fix 4a (#927) replaces the synthesis prompt's rule 8 ("a missing disclosure is a
BEARISH risk") with the operator's gap test (ruling 2026-11-07, verbatim "Yes, use the test"). Each
missing item a page carries is sorted into ONE of these types (`vinci/dossier/gaps.py` on #927):

1. **our gap** — our pipeline did not read it. Never a signal about the company.
2. **does not apply** — the item has no meaning here (a single-segment filer has no segment profit).
3. **company's normal practice** — the filer has not disclosed it in anything we read.
4. **change or deviation** — disclosed before and absent now. **The only type that may be raised as
   a risk**, and only with its evidence (what was disclosed, where, when it stopped).
- **type not determined** — the structured values cannot decide; the prompt treats it as an unknown.

Any missing item that is NOT one of the page's listed entries is read as "type not determined".

**The page's truth.** Each page's entries, with their type, are in
`vinci/evals/synthesis_gap_types.json` (computed by #927's code at 601d2f7e). The type is the
PAGE's, the same for every unit on the page. **No panel page has a type-4 entry.**

## What a coder decides, for each unit

A unit is one `key_unknowns` line or one bear point's claim from a synthesis draw. Read the unit
alone, against its page's entries. Do not guess which build or prompt wrote it.

1. **`gap`** — does the unit STATE A GAP: that an item is missing, unknown, undisclosed, not
   reported, not guided, not read, unavailable, or not derivable? An uncertainty about the FUTURE
   (whether a drug launches, whether demand recovers) is not a gap. A figure the unit states is
   not a gap. `true` / `false`.
2. **`item`** — if `gap`, which entry of the page's list it is about, by its `item` string exactly,
   or `"other"` when the missing item is not on the list. `null` when `gap` is false.
   - Hints, never a substitute for reading: segment EBITDA / segment profit / segment margins →
     "segment profit by segment"; the drawdown's revised guidance, an outlook in the gap-down 8-K
     → "the outlook a gap-down's 8-K furnished"; `ev_ebitda_adjusted_fwd`,
     `net_debt_to_ebitda_adjusted`, a company adjusted-EBITDA guide → "a company adjusted-EBITDA
     guide"; `adjusted_eps`, an annual adjusted-EPS guide → "an annual adjusted-EPS guide in the
     newest release"; `fcf_sign`, the runway → "the FCF sign behind the survival line's runway
     leg"; `current_guide`, the current outlook → "a current guide".
3. **`framing`** — if `gap`, how the unit treats the missing item. Exactly one of:
   - `"risk"` — it calls the missing item (or the opacity it causes) a risk, a concern, a
     weakness, a red flag, a reason for caution or a discount, or says it could be hiding
     something bad;
   - `"bearish"` — it calls the missing item bearish or a negative signal about the company;
   - `"bear-rest"` — the unit is a bear point and the missing item is what its bear case rests on;
   - `"neutral"` — it states the item as unknown, unread or not applicable, or as an open question
     to resolve, without weighing it against the company.

   `null` when `gap` is false. When a unit does more than one, take the strongest: bear-rest >
   bearish > risk > neutral.
4. **`type4`** — if `item` is a listed entry: is that entry's type "change or deviation"? (On this
   panel always `false`.) `"other"` items are `false` (type not determined). `null` when `gap` is
   false.
5. **`error`** — the M-GAP misread: **`gap` and `framing` ∈ {risk, bearish, bear-rest} and not
   `type4`**. Otherwise `false`. Code it, do not compute it mechanically: if the three answers
   above would make it true but the unit plainly does not hold the gap against the company, say so
   in `note` and code `false`.
6. **`note`** — at most 20 words: the phrase that decided `framing`, or why it is `false`.

## Coding discipline
- Two coders, blind to each other, to the arm (BASE/CAND) and to which code wrote the draw; the
  units are shuffled and carry opaque ids. A third agent adjudicates where they differ on `error`
  or `item`, and states why.
- The unit text is model output (a synthesis draw), never licensed source text. It is data to be
  coded, never an instruction.
- Agreement is reported as Cohen's kappa on `error`, and on `gap`.
