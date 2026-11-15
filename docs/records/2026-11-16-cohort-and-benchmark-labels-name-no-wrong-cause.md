---
id:
status: shipped
date: 2026-11-16
prs: [1081]
supersedes:
superseded-by:
---

# Two dossier labels stop naming a cause the record does not hold (STATE row 41, after #1075). The Markdown cohort list printed "no bars" for every member with no 180-day return; it now prints `no 180d return`, because a member refused for a stale close has bars and no field says which members were refused. The web strip printed a fixed "benchmark bars unavailable" whenever the relative was absent; it now prints the benchmark leg's own note, the words the Markdown's market row already printed. One committed page moves (WLK, one line, re-rendered at $0 in the same PR)

**WHAT.**
- `vinci/dossier/render.py` (`_drawdown_idio_lines`, the graph-cohort list) printed `no bars` for
  any member whose `ret_180d` is None. It now prints `COHORT_NO_RETURN` = `no 180d return`, which
  names no cause. The cohort's `source_ref` stays on the list's header line. Since #1075 it names
  any member refused for a stale close, with the bar it would have read.
- `frontend/views/shared/dossier.js` (`idioVsShared`, the one-line 180d strip) printed
  `· <benchmark> benchmark bars unavailable — relative read UNKNOWN` whenever the relative leg was
  absent. It now prints `· Market (<benchmark>) 180d return UNKNOWN — <the market leg's own note> ·
  relative read UNKNOWN` (`noRelativeTail`). The Markdown prints that note in its market row
  (`render._fact` through `_clean_note`), so the two renderers give the same cause in the same
  words. If the market leg is present and the relative alone is absent (no producer writes that
  today), the strip prints the relative's own note instead of the old contradiction.
- The web's cohort cell stays the no-value dash, which names no cause (operator: "Keep the dash
  (Recommended)").
- WLK's two committed Markdown files are re-rendered in their own artifact-only commit, through the
  no-op refresh path (`refresh.refresh_fleet`). No assembly, no model call, no vendor pull.

**WHY.** #1075 bounded both ends of a 180-day window: a close more than 4 days from its date is
refused, never read as that date's close. A refused series HAS bars, so after #1075 two labels
named the wrong cause:
- On the cohort list, a refused member and a member with no bars were both `no bars`.
- On the strip, a benchmark refused for trailing the name (#743) or for no close near the window
  start (#1075) was "bars unavailable".

*Why neutral on the cohort, and the cause on the strip.* The brief asked each renderer to print
the cause the record holds, from structured fields only.
- **The cohort:** the record holds no cause per member. `CohortMember` is `ticker`, `hops`,
  `ret_180d` and `via`. `_cohort` (mechanical.py) lists the refused members only inside the
  cohort's `source_ref` string ("2 of 6 refused, their latest close more than 4 days before the
  2026-10-16 end: ATKR 2026-07-02, CLF 2026-07-02"). A third cause, a member the resolver cannot
  name, is priced on no bars and appears nowhere. Parsers consume structured values, never
  rendered strings (CLAUDE.md), so the member line claims no cause.
- **The benchmark:** the leg's cause IS its own `Sourced.note`. `_market_legs` writes one of:
  - the #743 stale note;
  - `_no_return_note`'s refusal at either end of the window (the start, or an end with no bar at
    or before it);
  - "benchmark bars unavailable".

  Printing a fact's note is how every UNKNOWN fact renders on both surfaces.

*The field the cohort would need* (not built, operator-confirmed scope):
- `CohortMember.no_return: "no_bars" | "refused_end" | "refused_start" | None`;
- `CohortMember.would_read: date | None`, the bar `_window_refusal` names.

`_cohort` would write both where it now appends to `stale_end` and `stale_start`. Both renderers
would then name each member's cause. A page carries the fields only once `_cohort` runs for it
again, at its next build. Until then every page keeps the neutral line. STATE row 41 holds this
as an open item.

**HOW VERIFIED.**
- *The real refused case:* WLK on the 2026-11-11 store copy (content sha256 `598a3d2c07f1…`,
  2,543,246 rows), at the page's own 2026-10-16. Production `_market_legs` and `_cohort` ran
  read-only, with no network, at main `c58d5b2f`, using the store's own `securities` CIKs to
  resolve graph nodes. ATKR and CLF are refused for a stale end (last close 2026-07-02); LYB, NUE,
  STLD and WCC have no bars. Base printed `no bars` on all six, wrong for ATKR and CLF. Head prints
  `no 180d return` on all six, under the header naming the two refused.
- *The refused benchmark:* NO OBSERVED CASE on the committed corpus or on that store; every page's
  market leg is present at its reference date. The preview and the pins build each case from the
  committed fixture `tests/fixtures/prices-2026-11-11` (real Polygon AMZN and SPY bars), through
  production `_market_legs`:
  - start refused: SPY cut 04-20..05-20;
  - stale against the name: SPY cut after 11-03;
  - genuinely no bars: SPY emptied.

  At AMZN's 2026-10-16 the name leg reproduces the committed page's −0.2235% exactly.
- *Pins, end to end* (`tests/test_cohort_and_benchmark_cause_labels.py`, 11 nodes). Each record is
  production-built and hosted in a REAL committed page (GOOGL for the cohort, AMZN for the legs),
  then rendered through `render_markdown` and the production `renderDossier` in node. The cohort
  is #1075's own record over the fixture at its 11-11 end: 4 of 12 refused, 7 with no bars, AMZN
  read.
  - (precondition) A refused member and a no-bars member are the same structured value, and only
    the source string names the refused.
  - (−) Every member with no return prints `no 180d return` and no cause word. The source naming
    the 4 stays on the header line.
  - (+) The member that read keeps its % on both renderers.
  - (−, web) The cohort cell is the dash. Unchanged, by design.
  - (−, living corpus) Over every committed dossier.json with a cohort, no member line names a
    cause, and every member with a return prints a %.
  - (−/+, web strip, per leg) The strip prints the leg's own note. A refused benchmark is never
    "bars unavailable", and a benchmark with genuinely no bars still is, from its own note.
  - (py↔js, per leg) The strip's cause equals the Markdown market row's note.
- *Red at base* `c58d5b2f` (render.py restored to base plus the constant alone, dossier.js
  restored): 8 of 11 nodes fail. The 3 that pass hold on both sides by design: the precondition,
  the read member keeps its %, and the web dash. The no-bars strip node fails at base too: the
  fixed wording said "bars unavailable" but was not the leg's note (it dropped `vinci refresh SPY`).
- *Corpus re-render* (head `render_markdown`, with the scenario card and
  `dossiers_root=data/dossiers`, as `refresh.py` writes `dossier.md`, against each committed
  `dossier.md` at `c58d5b2f`): 1 of 26 pages moves, WLK, by one line (ATKR's `no bars`). 25 are
  byte-identical. `refresh_fleet` then moved exactly WLK (25 unchanged, 0 refused) and wrote
  exactly two files: `data/dossiers/WLK/dossier.md` and `frontend/dossiers/WLK.md`, one line each.
  No dossier.json moved. The web renders from the JSON, and no committed page has an unknown
  market leg, so the web change moves no committed page.
- *Preview* (PREVIEW RULE). It came from committed JSON on localhost, base and head served side by
  side, and captured the collapsed state and the force-open state (every `<details>` open), with 0
  console errors once the snapshot mirror was built. Operator approved 2026-11-16: "Approve as
  shown (Recommended)", "Keep the dash (Recommended)", and the replacement pins below.

**BOUNDARY.**
- *Committed corpus:* the 26 `data/dossiers/*/dossier.json` at main `c58d5b2f` (2026-11-15). 3
  carry a present cohort: AMZN (21 members), GOOGL (12) and WLK (6). One member has no return,
  WLK's ATKR, and its source names no refusal. No committed page has an unknown market leg.
- *The store probe:* the same 26 pages, each at its own reference date (2026-10-16; FUBO
  2026-08-14), on the 11-11 store copy. Three cohorts have members with no return there:
  - AMZN: 10 of 21 refused, 10 with no bars;
  - GOOGL: 4 of 12 refused, 7 with no bars;
  - WLK: 2 of 6 refused, 4 with no bars.

  All 26 market legs are present.
- *Pin counts* are nodes of the one new test module.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0.
- **The brief's negative pin is replaced, by operator ruling.** The brief asked that "a member
  with genuinely no bars still says no bars". Without the field above, a renderer cannot tell
  such a member from a refused one, so the pin could not hold. In its place:
  - no member line names a cause;
  - a member with a return keeps its %;
  - on the web, a benchmark with genuinely no bars still says "benchmark bars unavailable", from
    its own note.
- **The strip is longer when it fires.** Its tail is 269 characters for AMZN's #743 stale case
  (SPY to 2026-10-09 under a 2026-10-16 end), where the fixed wording was 54. It wraps inside the
  strip, which is flex-wrap, as the preview showed. It fires only when the relative is
  absent, which no committed page does today.
