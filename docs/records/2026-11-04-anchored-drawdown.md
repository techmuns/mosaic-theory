---
id: 2026-11-04-anchored-drawdown
status: shipped
date: 2026-11-04
prs: []
supersedes:
superseded-by:
---

# A name's drawdown is kept as it stood on its underwrite (else its follow) and since: SMPL's April gap-downs and FY26 outlook 8-K no longer fall out of a rebuild, and its pre-spend check goes from 2 regressions to 0

**WHAT.** `drawdown_cause` gains an optional `anchor` block (`DrawdownAnchor`, schema
`vinci/dossier/schemas.py`; built by `mechanical._drawdown_anchor`):

- **The anchor date.** The live underwrite record's `underwrite_date` (`scenarios/<T>.json`),
  else the follow's `followed_since` (`data/followed.json`, read through `vinci.followed`), else
  none (`mechanical.drawdown_anchor_date`, `assemble._drawdown_anchor_date`). An underwrite wins
  over a follow (GOOGL: followed 2026-08-27, underwritten 2026-09-01 → 09-01). A reissued record
  anchors at its own date. An anchor after the page's price date, or a follow that ended
  (`followed_until` on or before it), anchors nothing.
- **The at-anchor part** (`at_anchor`): the screen's own detector (`screens.assemble.
  detect_gap_downs`, threshold −10% untouched) over the 180 days ending ON the anchor date, read
  only from closes on or before it and from EDGAR through a second `AsOfEdgar` cut at it — so an 8-K
  filed after the anchor never enters it and no later build can change it. Each gap-down carries
  its move, its 8-K item labels and the revised-outlook exhibit (`gaps`, `filings`,
  `revised_guidance`), and the shape states each move beside its cause so a point can cite it.
- **The since part** (`since`): the same reader from the day after the anchor to the page's price
  date, on the page's own cut; absent when there is no session after the anchor.
- **A window the stored closes do not cover is not read**: when the store's history begins on or
  after a part's start, the part is UNKNOWN, saying so, never "no single day of -10% or worse"
  (an absence read from missing data, which a later backfill would change).
- **The rolling window is unchanged**: `shape`, `gap_down_dates`, `filings`, `revised_guidance`
  are still the screen record's events (the window ending on its reference date), and every
  reader of them (adjusted facts, P/E reconciliation, catalyst path) reads what it read before.

`anchor` is ABSENT when None (`DrawdownCause` serialiser), so the 27 committed pages read, check
and render exactly as before until each is rebuilt. Extraction `2026-11-04.anchored-drawdown`
(Python and JS twin).

Around it: **the pre-spend check** (`prespend.compare`) lists a rolling-window field
(`MOVABLE`: `gap_down_dates`, `revised_guidance`) that left the window as MOVED, not a regression,
when a dated part of the build carries the same dates or the same exhibit — by value, never by
presence (`carried_by`); and compares the dated parts by value, so a date or exhibit a committed
at-anchor part holds and the build's does not is a regression and stops the pass
(`dated_part_losses`). **The paid write** refuses a degraded at-anchor part over a committed one
(`assemble._refuse_degraded_at_anchor_overwrite`). **The synthesis brief** marks each dated
part's outlook with its vintage (`_mark_drawdown_guidance` — SMPL's at-anchor guide is the April
guide that once became a false bear point) and, for an anchored name only, adds a section with
both parts, a shape contract, ONE literal example (SMPL's real at-anchor line, pinned against the
build) and the question *has the cause named at the underwrite played out?*, answered inside the
existing points; `Synthesis` has no new field and no verdict field. **The render** (Python
`render.py`, JS `dossier.js`) labels both parts — "Drawdown at underwrite (2026-08-05): …" and
"Since underwrite (2026-08-06 → 2026-11-03): …" on the Brief; the Analysis drawdown section leads
with them, the verbatim outlook and 8-Ks in a collapsed `<details>` (force-open in print), and a
pre-window chart drop a dated part classifies is no longer captioned "not classified".

**WHY.** The block re-read a ROLLING 180-day window at every build: a candidate's record is the
screen's, a maintained name's is rebuilt by `_standalone_record` at the fleet reference date. For
a held or underwritten name, a rebuild more than 180 days after the drop erased the event the
underwrite was written on, and nothing else kept it — `scenarios/SMPL.json` holds the date and the
thesis text, not the gap-downs or the 8-K. An expert team keeps a thesis log: the original event
stays, dated, and what has happened since is added. This is a different question from the fact
layer's (#896, "what was known on date X"): it is "which date the page should ask about".

**DOES THIS SELECT ON FORM? No.** Nothing here selects or ranks: the anchor is a date the fund
already recorded (an underwrite or a follow), the detector and its −10% threshold are the
screen's, unchanged, and the parts are read for every anchored name alike. No threshold,
window or mapping was chosen or tuned on any outcome; the 180 days are `DECLINE_WINDOW_DAYS`.

**THE ROLLING WINDOW AT THE PRICE DATE (brief item 3) — MEASURED, NOT KEPT, REPORTED.** The brief
asked to end the rolling window on the page's price date instead of the screen's reference date,
and to report before keeping it if it moved non-anchored pages. It does. On the 2026-11-03 store
(reference 2026-10-16 → price date 2026-11-03 for every page), the gap-down set moves on two of
the four non-anchored pages: **FUBO** loses 2026-05-06 (it falls before the new window start
2026-05-07) and **VRRM** gains 2026-10-30 (a drop after the last screen run, charted and not
classified today); CNXC and VITL do not move. Among anchored pages GOOGL gains 2026-10-29, IT
2026-11-03, PARR 2026-10-27 — each already in its since part — and BRBR loses 2026-05-05, which its
at-anchor part carries. So it is left out of this change: the switch is a ready patch, and the
operator decides.

**HOW VERIFIED.**

- **SMPL at $0** (`vinci dossier precheck --ticker SMPL`, 2026-11-04, store copy refreshed per
  RUNBOOKS §i): **exit 0, 0 regressions** (was 2 on #902's run, b22b0c81). MOVED (2):
  `drawdown_cause.gap_down_dates` "carried by drawdown_cause.anchor.at_anchor (2026-02-06 to
  2026-08-05): 2026-04-09, 2026-04-10"; `drawdown_cause.revised_guidance` "carried by … EDGAR 8-K
  0001702744-26-000010 Ex-99.1". Newly present: the three at-anchor fields and the since shape.
- **The 27 committed pages, $0** (each page's block built twice on identical inputs — the code
  before (the record alone) and after (record + store closes + anchor), each page's record as
  `load_finalists` builds it at reference 2026-10-16, EDGAR cut at its price date 2026-11-03):
  **the rolling window is byte-identical on all 27**. 23 are anchored (9 underwritten, 14 followed
  only), 4 are not (CNXC, FUBO, VITL, VRRM). 11 gain dated gap-downs: AORT, BRBR, EPAM, IT, MVST,
  NCNO, NKE, PARR, SMPL and TECX at the anchor, GOOGL since it only (2026-10-29); IT and PARR also
  have one since (2026-11-03, 2026-10-27). Against each COMMITTED page's drawdown block, **no
  page loses a field**: SMPL's two rolling-window losses are carried by its at-anchor part, and
  no other page loses one. The at-anchor parts name drops no committed page names: IT 2026-02-03
  (−20.9%), NCNO 2026-02-03 (−10.6%), NKE 2026-04-01 (−15.5%), EPAM 2026-02-19 (−17.0%), PARR
  2026-04-17 (−10.0%).
- **Pins** (`tests/test_anchored_drawdown.py`, 24, on real fixtures — SMPL's Polygon closes,
  its EDGAR 8-K rows and the three documents the reader fetches, cut after what each reader reads
  and checked identical): SMPL keeps 04-09/04-10 (−18.1%, −11.5%) and the outlook 8-K at today's
  dates; the at-anchor part is identical at price dates 2026-08-17, 10-16 and 11-03; a name with
  no anchor builds byte-identically; a window the closes do not cover is UNKNOWN; the anchor rule
  as an invariant over the live `scenarios/` and `followed.json` and as a precedence pin on a
  frozen (archived) record; a gap after the anchor is in since only; **the lookahead
  pin** — the real 8-K re-dated after the anchor never enters the at-anchor part while the
  rolling window, read at the price date, does find it; the precheck carries by value and the
  dated parts never lose; the paid write's refusal; the brief's vintage mark and digest; the
  render end to end; the `windowWords` and label-table twins through node (the label table is
  on `test_duplicate_definitions.BASELINE`, bound by that pin); the committed corpus round-trips
  with no new key.
- **Mutations the pins catch — 13 of 13**, each applied alone and the file restored: the
  at-anchor EDGAR left uncut at the anchor (the lookahead pin); its closes left uncut (a gap after
  the anchor leaks into the part); carried by presence instead of value; the dated parts not
  compared by value; the dated outlook not vintage-marked; `anchor` written as null; an anchor
  after the price date still anchoring; the follow winning over the underwrite; the paid write
  ignoring the at-anchor part; the Brief dropping the dated lines; the JS twin printing the move
  unsigned; a window the closes do not cover read anyway; the dated-part outage flag escaping the
  hidden QA tier.
- **Review** (`/code-review high --fix`, round 0): 10 findings, 8 fixed — the dated-part outage
  flag had escaped `flags._QA_MARKERS` and would have printed as a decision caveat; an uncovered
  window read as "no drop"; the round-trip pin would have gone red at the first anchored rebuild;
  a value pin sat on the live follow list and records; the brief restated the labels and the
  180 days; an 8-K with no URL rendered an empty link; unanchored names read their closes for
  nothing; a version-table row shared a line with the one before. 2 dismissed: a moved anchor
  stopping the precheck is deliberate (its message names the move, the operator decides), and the
  anchor helper's second read of the same committed record keeps the pinned call shape.
- **Render preview** (PREVIEW RULE): SMPL's real $0 build, collapsed and force-open,
  `docs/dossier/anchored-drawdown-2026-11-04/screenshots/`.

**BOUNDARY.** Store: a copy of the primary's `data/vinci.db`, the 27 page names plus IWM, MDY and
SPY refreshed by `vinci refresh … --aggs --start 2021-07-01 --end 2026-11-03` on 2026-11-04 (Polygon
served 501 bars each). Exports: the operator's Drive folder as linked on 2026-11-04 (SMPL: Financials
annual `cc99900b61`, quarterly `3a3e2873fa`, Estimates `fd3fbcf38f`, comps `647fa70755`). Code: main
`1b8a5a2f` plus this change. The 27 pages: `data/dossiers/*/dossier.json` at that commit. Anchors:
`scenarios/*.json` (9 records) and `data/followed.json` (16 entries, none ended) at that commit.
Gap-down moves are close-to-close on the stored closes, rounded to 0.1 pt.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- The at-anchor part is invariant to later builds only as far as its INPUTS are: a vendor
  revision of a stored close on or before the anchor, or EDGAR re-serving an old 8-K row
  differently, would move it. The precheck then STOPS (`dated_part_losses`) rather than letting it
  pass, and the operator decides. Falsifier: a rebuild whose at-anchor part changes with no such
  input change.
- The dated parts carry no parsed EX-99.1 drivers (the rolling window's "what the results showed"
  card, B1): those come from `primary_source.releases`, a set cut at the page's price date whose
  population moves with it, so they could not be held invariant. The verbatim outlook exhibit is
  carried instead. A follow-up if the operator wants the card.
- A reissued underwrite moves the anchor to the reissue's date, so its at-anchor part changes; the
  precheck stops on that change and names the moved anchor.
- The rolling window's own 180-day return comparison (`idiosyncratic_vs_shared`) still ends on the
  reference date; not touched (hold scope).
