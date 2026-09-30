---
id: 2026-09-30-a-price-stamp-travels-with-its-multiple
status: shipped
date: 2026-09-30
prs: [661]
supersedes:
superseded-by:
---

# A forward multiple's price stamp travels with the multiple

**WHAT.** `price_as_of` joins `freshness._NOT_A_PANEL` on both twins. #659 gave the dossier
forward multiples, each row stamping the close its own multiple divides by; BURL's re-assembly
then reddened `test_every_dated_panel_key_is_consciously_classified` with four new dated keys
"defaulting to the GATING class with nobody deciding they should". **The guard did its job — a
dated field had joined the age ceiling silently.** This is the decision it asked for.

**THE DECISION IS EXCLUSION, BECAUSE THE DATE IS ALREADY COUNTED.** Four rows emitted four copies
of ONE date, and that date is `stock_info.as_of`, which gates and always did. Both are
`max(bars).bar_date` off the same `store.get_price_history` call: `_refresh_price_and_pe`
(`mechanical.py:191`) takes the max directly, and `compute_price_features`
(`eod/features.py:139`) reads `bars[-1]`, using its `reference_date` only to decide whether to
flag the close stale. Neither can be older than the other, so the ceiling — which reads the
OLDEST panel — cannot move whichever way this is classified.

That is the same object the exclusion list already names: an own-history band's observation date,
a per-point series date. The alternative, enumerating `value[0]`…`value[N]` in the test's
`_CLASSIFIED_PANEL_KEYS`, would have reddened on the next name with a different estimate-column
count while asserting nothing `stock_info.as_of` does not already assert.

**HOW VERIFIED.**

*The real run, on the artifact that reddened the guard* — BURL's 2026-09-30 assembly
(`data/dossiers/BURL/dossier.json`, on branch `artifact/burl-onto-the-basis-work`, built on
`c273ad18`), through `panel_age(..., kind="export")`:

    BEFORE  oldest panel 8d old — 2026-09-22 (valuation.forward_multiples.value[0].price_as_of)
            12 panel keys (4 price stamps)   date set ['2026-09-22', '2026-09-28']
    AFTER   oldest panel 8d old — 2026-09-22 (stock_info.as_of)
            8 panel keys (0 price stamps)    date set ['2026-09-22', '2026-09-28']

**Same date, same 8 days, same date SET — only the ATTRIBUTION changes**, which is the claim
stated as a measurement rather than an argument. The page had been telling its reader that a
computed multiple's own price stamp was the oldest export behind the build.

*The rendered page moves, and a render pin caught it.* `test_screening_context_...e2e` re-renders
live from committed JSON: BURL's committed `dossier.md` names the forward-multiple key in its
panel-age line and now names `stock_info.as_of`. The note is **render-time, not stored** — zero
occurrences of it in `dossier.json` — so BURL's markdown needs a RE-RENDER after this merges, not
a re-assembly, and the five-draw synthesis is not re-run.

*Mutation — six, all caught.* M1 the term removed from Python; M2 from the JS twin only; M3 from
BOTH (the parity pin correctly stays GREEN — that is the gap `..._is_on_both_sides_of_the_twin`
exists to close); M4 broadened to `|as_of`, which would swallow every export stamp in the fleet;
M5 the fixture's stamps decoupled from `stock_info.as_of`, which is the invariant the whole
argument rests on; M6 a second term smuggled in beside it. Source restored byte-identical.

*A pin that survived a mutation, and was rebuilt rather than adjusted.* The first cut derived its
"before" pattern by `pattern.replace("|price_as_of", "")` — **blind to a mutation that RENAMES the
term**, since M4 leaves nothing to replace and "before" and "after" come out equal. A guard that
had swallowed every export stamp read as no change. The reference is now a written-out constant,
`_TERMS_BEFORE`, and M4 is caught by the pin that should catch it.

*A second pin that was simply wrong, found by running against the real artifact rather than the
corpus.* `..._changes_nothing_for_the_committed_fleet` asserted the inventory was IDENTICAL before
and after — true on a fleet carrying no forward multiples, and RED the moment the first
re-assembled name lands. Measured against BURL's real re-assembly it failed immediately. The
invariant is "removes price stamps and NOTHING ELSE".

**BOUNDARY.** Measured 2026-09-30 off `c273ad18`. *The fleet sweep*: all committed dossiers under
`data/dossiers/*/dossier.json` (unit: dossiers), panel inventory unchanged for every one — because
**no committed dossier carries forward multiples yet**, BURL's assembly being unmerged. The
frozen fixture is therefore the only live instance today, and
`..._matches_its_own_export_stamp` covers 0 committed names and begins covering them as the fleet
re-assembles; it is written as a sweep rather than a skip for that reason. *8d / 12→8 keys /
2026-09-22*: BURL alone, its own `assembled_at` 2026-09-30, `kind="export"`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **The four stamps are no longer visible to the freshness inventory at all.** Accepted because
  they are copies of `stock_info.as_of`, which remains. *Falsifier:*
  `test_every_committed_price_as_of_matches_its_own_export_stamp` — if a name ever strikes its
  forward rows on a different close, this classification owes a re-argument.
- **`price_as_of` is matched anywhere in the path**, so a future field of that name elsewhere is
  excluded without a second decision. Deliberate: the name describes the object. The ledger's
  `entry_price_as_of` / `exit_price_as_of` would also match, and never reach `panel_dates` —
  they are not in a mechanical record.
- **BURL's committed markdown is stale until re-rendered.** It names the old key. The re-render
  rides the artifact PR that follows this one; nothing here touches an artifact.
- **Nothing CI-validated.** The `gate` workflow has been failing on GitHub Actions billing since
  #652; every figure above is a local run.
