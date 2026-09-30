---
id: 2026-09-30-burl-onto-the-basis-work
status: shipped
date: 2026-09-30
prs: [662]
supersedes:
superseded-by:
---

# BURL's page states the window its multiples are struck on

**WHAT.** The artifact pass that puts BURL — the name a team review was written about — onto the
work that review prompted (#659, #660, #661). One name, `1 done · 0 error(s)`, artifacts only.
Assembled on `c273ad18`; the markdown re-rendered on `a860de9a` after #661, which the assembly
itself provoked.

The page gains the two rows whose absence caused the reviewed defect:

    - **Forward multiples:** P/FY27E (normalized) 21.8x (EPS $11.80); P/FY27E (GAAP) 22.4x
      (EPS $11.48); P/FY28E (normalized) 18.8x (EPS $13.68); P/FY28E (GAAP) 19.2x (EPS $13.40)
      — at $256.85 as-of 2026-09-22

    - **Multiple basis — read before the level:** the EV/EBITDA (TEV/LTM) series implies a 19.3%
      EBITDA margin, against 11.1% reported. Its denominator is NOT the reported EBITDA; the same
      TEV over REPORTED EBITDA is nearer 15.6x.

**WHY IT MATTERS HERE SPECIFICALLY.** An underwrite built on this dossier sourced "~22.1x forward
P/E" from outside it, because the dossier published only trailing multiples; applied 22x to FY+2 at
the exit; and reported the difference as ZERO multiple change. The external 22.1x is FY+1-struck —
it sits between the two FY27E rows now printed — and the three-turn gap to FY+2 is exactly what was
called zero. That underwrite also derived 15.6x by hand to localise the EV/EBITDA defect. Both
numbers are now on the page it was built from.

**HOW VERIFIED.**

*The run.* BURL assembled on merged `c273ad18`, exit 0. All four chains confirmed present on the
tree BEFORE the run rather than assumed: the `forward_multiples` builder, the basis renderer, the
`price_as_of` isoformat fix, and #660's `entry_denominator`.

*What moved:*

    lean              Strongly-bullish   ->  mixed
    draws             {s-bullish 3, mixed 1, mixed-to-bullish 1} -> {s-bullish 2, mixed 3}
    forward_multiples absent             ->  present, 4 rows
    caveats / qa      5 / 4              ->  6 / 5

*The gate.* 5 of 5 draws completed, NOT unanimous, so the machine proposal is withheld and the
tally prints as a count.

*The panel-age line, re-rendered after #661.* This assembly is what reddened
`test_every_dated_panel_key_is_consciously_classified`, and the page it produced carried the
consequence:

    - **Panel age:** oldest panel 8d old — 2026-09-22 (valuation.forward_multiples.value[0].price_as_of), …
    + **Panel age:** oldest panel 8d old — 2026-09-22 (stock_info.as_of), …

A computed multiple's own price stamp was being named as the oldest EXPORT behind the build. Same
date, same 8 days; only the attribution was wrong. Re-rendered through `_rerender_only` — the
sealed-name path, which reads the stored record and writes only the markdown: `dossier.json` is
**byte-identical by sha256 across the re-render** (`858a38d5…` before and after), so the five-draw
synthesis was not re-run to fix a rendering. `mirror_to_frontend()` then rebuilt the whole tree
and moved nothing but `frontend/dossiers/BURL.md`, which is byte-identical to its source — no
other name had drifted.

**THE LEAN MOVED ON UNCHANGED DATA, AND THAT IS THE POINT OF THE GATE, NOT A NEW READ.** The
previous assembly of this same name, on the same facts, drew 3 strongly-bullish / 1 mixed / 1
mixed-to-bullish; this one drew 2 / 3. Nothing about BURL's evidence changed between them — the
as-of, the CIQ panel and the filings are identical. Anyone reading "mixed" here against
"strongly-bullish" in the prior version is reading draw variance. It is also why the proposal is
withheld in both.

**BOUNDARY.** Assembled 2026-09-30 off `c273ad18`, re-rendered off `a860de9a`. One name; five files
(`data/dossiers/BURL/dossier.{json,md}`, `frontend/dossiers/BURL.{json,md}`,
`frontend/dossiers/index.json`). Multiples struck at BURL's committed price $256.85 as-of
2026-09-22 — NOT the $268.12 the reviewed underwrite used, which is a later intraday quote; the
two are different as-ofs and every multiple moves with them.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **The synthesis prose is fully rewritten for a name whose facts did not change.** Inherent to a
  full assembly, which re-draws five times. The record states it so a reader does not mistake the
  rewrite for new evidence.
- **THIS DOES NOT ANSWER THE REVIEW'S BLOCKING ISSUE.** That review asked for a recomputed
  exit-date NTM denominator, Base/HPR/IRR, and a roll-versus-re-rating split. Those live in a
  SCENARIO record, and BURL still has none — its page reads "no scenario record for this name".
  This pass fixes the dossier inputs that caused the defect; it does not produce the decomposition.
- **`basis_decomposition` is computable and rendered NOWHERE.** #660 made the split arithmetic;
  no surface publishes it. Until one does, the attribution a reader wants is available only to
  code.
- **The reviewed underwrite lives outside this repo** and is uncorrected wherever it sits. Nothing
  here reaches it.
- **NOT FIXED, unchanged:** `P/LTM EPS` is struck on GAAP LTM EPS and its label says neither.
