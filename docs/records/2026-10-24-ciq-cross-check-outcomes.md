---
id: 2026-10-24-ciq-cross-check-outcomes
status: shipped
date: 2026-10-24
prs: [793]
supersedes:
superseded-by:
---

# Five CIQ cross-checks store their outcome — agree, differ or not run — and the data-quality scorecard scores them; four leave the coverage map's UNSCORED list

**WHAT.** `schemas.CrossCheck` is a cross-check's OUTCOME — `agree`, `differ` or `not_run` —
stored beside the reading that prints it, for five checks the scorecard (#792) could not score:

| field (beside) | was | outcome built by |
|---|---|---|
| `implied_expectations.vintage_check` (`vintage_coherent`) | bool, True when the FY26 probe cannot run | `mechanical._vintage_probe` |
| `implied_expectations.net_debt_check` (`net_debt_reconciled`) | bool, True with no bridge | `mechanical._net_debt_probe` |
| `primary_source.guide_verification_check` (`guide_verification`) | display text only | `primary_source.guide_verification_read` |
| `primary_source.wall_coherence_check` (`wall_coherence`) + `wall_coherence_near_boundary` | display text only (the boundary reason in a QA flag) | `primary_source.wall_coherence_read` |
| `primary_source.self_funding_check` (`self_funding`) | display text only | `primary_source.self_funding_check` |

Each outcome comes out of the SAME decision as its line or flag; the old string APIs are wrappers
of the reads. Assembly stores them. The fields are OPTIONAL and ABSENT until built
(`DROP_WHEN_NONE`, which now takes a dotted parent), so a page without them round-trips byte for
byte.

The scorecard's CIQ source (`vinci/quality/sources/ciq.py`; the core is untouched) scores them:
four new checks — `guide_vs_release`, `wall_vs_10q`, `fcf_sign_vs_edgar_ocf` (independent) and
`forward_multiple_vintage` (internal) — and `net_debt_vs_implied_bridge` now reads `net_debt_check`,
never the flag. agree → confirmed, differ → differs (stated where the page states why: the wall's
boundary instrument), not run → unchecked; ABSENT → not run, never a pass.

**THE PATH WITHOUT THE WORKBOOKS EXISTS, and it is how the committed pages got the fields.**
`refresh.cross_check_transform`, through `refresh_dossier` (kept synthesis), reads every input off
the page except two, both EDGAR's and public: the latest-quarter OCF sign (as FILED BY the page's
assembly date) and the balance date of the 10-Q the page names. Each outcome is written ONLY where
the producer's own composition re-runs on those inputs and gives back the stored line (or flag)
byte for byte — the `_rebuild_release_lines` proof — so the outcome is the stored line's own and
never a reading of its words. One that does not reproduce is left absent and named.

**THE ANSWER, 2026-10-24** (27 committed pages after the back-fill; the five checks as the
snapshot `data/snapshots/data_quality/ciq/2026-10-24.json` counts them, one unit per page; its
`git_head` f02a5224, inputs matching it, page-set sha256 `1cd4ebfe…`). #792's 2026-10-23 point
stands beside it, unchanged — the series' first, nine checks.

| check | independence | confirmed | differs, stated | differs, unexplained | unchecked | not run |
|---|---|--:|--:|--:|--:|---|
| `guide_vs_release` — CIQ revenue guide vs the 8-K release | independent | 5 | 0 | 2 (LLY, VRRM) | 19 | 1 (MVST: no outcome on the page) |
| `wall_vs_10q` — CIQ panel vs the 10-Q maturity wall | independent | 0 | 1 (MVST, an instrument at the +12m boundary) | 0 | 26 | 0 |
| `fcf_sign_vs_edgar_ocf` — the two signs | independent | 20 | 0 | 7 (AORT BRBR CNXC EPAM MVST PARR WLK) | 0 | 0 |
| `forward_multiple_vintage` — FY26 ladder at TEV vs FY26 consensus | internal | 18 | 0 | 1 (FUBO) | 8 | 0 |
| `net_debt_vs_implied_bridge` — comps net debt vs the bridge | internal | 25 | 0 | 2 (ORKA, UBER) | 0 | 0 |

The guide's 19 unchecked: no CIQ guide, a release with no number or only a qualitative one, a
change guide against CIQ's level, a quarter against a year. The wall's 26: the 10-Q states no
12-month figure. The vintage probe's 8 are the case this build exists for — **each page reads
`vintage_coherent: true` and its probe never ran**: BURL NCNO NKE ROST TGT TJX have already
reported FY 2026 (their ladder and Trends start at FY 2027), and ORKA and TECX carry no positive
FY 2026 EV/EBITDA multiple. #792 could not score them; counted on the flag they would have been
eight confirmations. The net-debt counts are #792's (every committed bridge has its structured
floats); the field only makes them read off an outcome rather than a flag.

Coverage, 25 families: **8 independent, 4 internal, 10 single-source, 3 unchecked** (was 5 / 4 /
10 / 6). `financials.cash_flow`, `financials.capital_structure` and `estimates.guidance` become
independent; `estimates.forward_multiples` stays internal with a second check. The UNSCORED list
keeps two entries: `ciq_balance.extract`'s scale check and `anchor.data_quality`, both of which
store no outcome on the page.

| failure class | independent | internal only | nothing, a second source exists | nothing, single-source |
|---|--:|--:|--:|--:|
| wrong file | 7 (was 4) | 1 | 7 | 10 |
| wrong cell | 7 (was 4) | 3 | 5 | 10 |
| wrong unit | 6 (was 4) | 3 (was 2) | 6 | 10 |
| wrong period or vintage | 5 (was 3) | 3 | 7 | 10 |
| different definition | 3 | 1 | 11 | 10 |

The classes are DECLARED per check from what it compares (face validity, never outcomes): the
guide and the wall can surface a wrong file, cell, unit or period; the sign check only a wrong file
or cell (a sign is blind to scale, and the two measures differ in period by construction); the
vintage probe a wrong file, unit or period. None claims a different definition.

**WHY.** #792's coverage map left these UNSCORED because a bool that reads True on a pass AND when
nothing ran cannot be counted (it would be a pass the check never made), and a verdict held in
prose cannot be read without parsing display text — which the house rule forbids.

**HOW VERIFIED.**

- **The census came first.** Before any code, every committed page's stored line or flag was
  rebuilt from its own inputs: the net-debt flag and the vintage note reproduce on 27 of 27 from the
  page alone (the note's FY26 consensus read off `forward_consensus`, the same Trends read), the
  guide line on 26 of 27 (MVST's point guide is stored `_fig`-rounded), and with EDGAR's OCF sign
  and the 10-Q's balance date the self-funding and wall lines on 27 of 27.
- **The pass, run for real** at d2351ff6 in a checkout with no `data/manual/ciq/`: `refresh_fleet`
  moved 27 pages, refused none, and named one outcome (MVST's guide). Checked page by page against
  HEAD: each JSON gained only the outcome keys and one `layer_refreshes` record, each `dossier.md`
  that record's one line, and nothing else moved.
- **Round-trip.** With the schema change and before the pass, all 27 committed pages serialize
  byte for byte (`dossier_json`), the outcomes absent.
- **The previously-broken case on real pages.** The eight pages whose probe never ran read
  `vintage_coherent: true`; the back-fill calls each not run, the card counts each unchecked, and
  two pins hold it on the committed corpus (`test_the_flag_that_passed_without_running_is_not_run_on_real_pages`,
  `test_no_committed_flag_that_passed_without_running_is_confirmed`), each asserting the case
  exists before asserting about it.
- **The back-fill end to end, offline:** run over every committed page with EDGAR answered from the
  committed companyfacts fixtures and the network refused, every outcome is either written or named
  and none contradicts an outcome a page carries (`test_the_backfill_writes_or_names_every_outcome_and_never_contradicts_a_page`).
- **Each proof refuses on its own**, on a perturbed committed page: an outcome the page already
  holds is kept and named, never overwritten; an edited vintage note refuses only the vintage
  outcome; a wall QA flag the rebuild does not give back refuses the wall; a later quarter of the
  other sign, filed after assembly, neither moves the self-funding outcome nor refuses it; a
  3-decimal point guide stored rounded refuses the guide.
- **Mutation:** 33 mutants of the new production code, run in a scratch copy of the tree (primary_source 10,
  mechanical 6, schemas 2, ciq_sheets 2, refresh 7, the scorecard source 6). The first pins killed
  25. Each of the 8 survivors then got its own pin (`5085cc0b`): an overwritten outcome, the wall
  QA comparison, the as-of OCF filter (twice), the release refresh carrying the guide outcome
  (twice), the vintage note proof, and the guide's low bound. After that, 33 of 33 were killed.
- **The scorecard, by the real command:** `vinci audit quality --source ciq` on the 27 back-filled
  pages prints the table above, and `--write` wrote the snapshot.
- **Review:** `/code-review high --fix` found two real defects in the back-fill, both fixed behind
  pins that were red first (`f02a5224`). A page with no `assembled_at` crashed the whole fleet pass
  instead of being refused. An implied block whose inputs were gone was skipped without being
  named.

**BOUNDARY.** Every count above is over the 27 committed pages (`data/dossiers/*/dossier.json`), as
back-filled at `048fb657` and scored at `f02a5224` (the 2026-10-24 snapshot, written 00:00 IST), with one unit per page per
check. The
coverage and failure-class counts are over the CIQ source's 25 field families. The census ran at
`57471a07` on the same 27 pages before any change. EDGAR was read on 2026-10-23, 23:00–23:30 IST
(companyfacts filtered to points filed on or before each page's `assembled_at` date, plus the
submissions feed for the named 10-Q). The FY 2026 diagnosis of the eight not-run pages is read off
their committed `forward_consensus` EBITDA periods and forward-multiple ladder. The mutation counts
are over the 33 listed mutants and three test files (`test_cross_check`, `test_quality_ciq`,
`test_release_amount_scale`).

**FOUND, NOT FIXED (out of scope; reported).**

- **The vintage probe is hard-coded to FY 2026** (`mechanical._implied_expectations`: the ladder's
  `"FY 2026"` and `trends_fy_level(…, fy_label="FY 2026")`). Six of the 27 pages have already
  reported FY 2026, so it can never run on them, and once every name has reported FY 2026 it runs
  on none — while `vintage_coherent` goes on reading True. The outcome now says so; the probe's
  year is the open item (agent).
- **A guidance-bridge row keeps a POINT guide only as `_fig` rounds it** (`GuidanceRow.latest_guide`,
  427.516 → "427.5"), with no structured value beside it — which is why MVST's guide outcome
  cannot be back-filled. A structured low/high on the row would remove the loss.
- **`self_funding` prints MIXED when both legs are negative** — "neither positive" worded as
  "mixed". Display wording, left as it is; the outcome beside it reads agree, because the two
  sources do agree.
- **`primary_source._TOL`'s comment claimed it was also the guide check's band**; the guide matches
  within 0.01 absolute. The comment is corrected and the band named (`GUIDE_MATCH`); no behaviour
  moved.
- **No extraction-version row** for the new fields: additive optional fields have not carried one
  (`ebitda_reconciliation`, 2026-10-21, did not), and absent keys keep every older page's meaning.

**WHAT IT COSTS / WHAT IS ACCEPTED.** MVST's guide outcome is ABSENT until MVST is next
re-assembled (assembly writes it from the workbook); the card counts it not run, never a pass, and
no other action is owed. The sign check is weak by construction — a SIGN, of two different
measures — and its 7 differs are mostly capex or seasonality, not CIQ errors (the family note says
so); it is counted because #792's map named it, and its failure classes are declared narrowly
(wrong file, wrong cell). The wall check runs on ONE page (only MVST's 10-Q states a 12-month
figure), so `financials.capital_structure`'s "independent" rests on one comparison, and that one
is a stated divergence. The back-fill read EDGAR on 2026-10-23; a line it could not reproduce from
what EDGAR returned that day was refused, never re-derived, so a restatement since assembly can
only leave an outcome absent, not wrong.
