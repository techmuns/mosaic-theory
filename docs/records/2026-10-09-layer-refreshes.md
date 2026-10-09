---
id:
status: shipped
date: 2026-10-09
prs: [694]
supersedes:
superseded-by:
---

# A page records each change made to it after assembly, and the code vintage that made it — the stamp keeps naming the assembly

**WHAT.** A new dossier-level field, `layer_refreshes`. It holds one entry per change a writer made to
a committed page after its assembly:

| field | what it is |
|---|---|
| `date` | when the writer ran (UTC) |
| `extraction_version` | the declared version current when it ran: the code vintage that made the change |
| `writer` | `refresh`, `anchor-backfill`, `own-history-refresh` or `financials-backfill` |
| `layers` | what moved, at the page's own grain: a top-level layer (`ev_bridge`, `anchor`) or a `mechanical.<section>` |

**How it is written:**
- **Every writer that changes a page without re-assembling it records itself:**
  - `refresh_dossier` round-trips the model and records the layers that actually moved.
  - The three text writers splice their entry in place, byte-preserving everywhere else, through
    one helper (`layer_refresh.upsert_text`). They are `anchor-backfill`, `own-history-refresh`
    and `financials-backfill`.
- **A no-op writes nothing.**
- **A full assembly writes a fresh page** and carries no entries forward; its stamp then covers
  everything.

**Where it shows:**
- **The header**, beside the stamp: "extraction 2026-08-16.1 · layers refreshed to 2026-10-08.4".
- **Record & reproduce**: each change, one per line, oldest first.
- **Both twins** (`render.py`, `dossier.js`). The field is absent until written, declared
  immediately before `anchor`, and has version row `2026-10-09.1` and its JS twin.

**WHY.** The unlock the 2026-08-17 ruling named
(`2026-08-17-extraction-vintage-residue-closed-2026-08-17-fix.md`): re-stamping on refresh is the
WRONG fix, because a new stamp claims the whole page was re-extracted, and the old stamp then
under-claims. "The artifact must record that a refresh ran and at which vintage." It was never
built and never tracked.

It became pressing on 2026-10-09: 23 pages carried `ev_bridge` (`2026-10-08.4`) under stamps of
`2026-08-16.1`. The first R4 record will be sealed on a bridge. If a bridge builder is later found
wrong, as #689's first cut was on UBER, this is what finds the pages and records built on the bad
version. Operator instruction, 2026-10-09: "start the refresh-vintage record". The preview was
approved the same day.

**WHAT A REAL HISTORY LOOKS LIKE — UBER, reconstructed from git for the preview.** UBER was
assembled 2026-09-17 and stamped `2026-08-16.1`. It has changed six times since:

    2026-10-07 · forward_consensus, mechanical.catalyst_path — refresh at 2026-08-16.1
    2026-10-07 · forward_multiple_history — refresh at 2026-08-16.1
    2026-10-08 · forward_consensus, forward_multiple_history, historical_forecast_error — refresh at 2026-10-08.2
    2026-10-08 · anchor — anchor-backfill at 2026-10-08.2
    2026-10-08 · forward_consensus — refresh at 2026-10-08.3
    2026-10-09 · ev_bridge — refresh at 2026-10-08.4

The two 2026-10-07 passes ran code that added layers without declaring a new version, so they
honestly record `2026-08-16.1`. That is queue item 26b's gap ("an extractor change with no bump"),
now visible on the page instead of hidden by the stamp.

**HOW VERIFIED.**
- **Nothing else moved.** All 26 committed pages render byte-identical on the web twin (`dossier.js`
  under node, main @6dea4ddc against this branch). A no-op `refresh_dossier` over all 26 moved
  nothing, and `git status` is clean. No committed page carries a record yet.
- **Real writers on real data,** in a scratch root:
  - `refresh_dossier` with `ev_bridge_transform` re-landed UBER's bridge, from its real exports,
    on a copy that lacked it. The bridge equals the committed one, and the page recorded
    `{2026-10-09, 2026-10-09.1, refresh, [ev_bridge]}` with the header and audit tier printing it.
    A second, no-op run added nothing.
  - `vinci anchor-backfill --tickers GOOGL`, with live EDGAR, on a copy with a perturbed anchor
    base, restored it to $212.17. It recorded `{anchor-backfill, [anchor]}` before `anchor`, and the
    page round-trips through `dossier_json` byte-identically.
- **The splice on the whole corpus.** Two entries were spliced into each of the 26 committed pages.
  Each round-trips through the shared serializer byte-identically, keeps every other byte, and
  appends in order.
- **Tests** (`tests/test_layer_refreshes.py`, 12) run on real committed pages copied into a temp
  root. They pin:
  - the refresh path recording, and appending, while the stamp stays the assembly's;
  - a no-op recording nothing, on UBER and SMPL;
  - the mechanical grain;
  - the splice on every committed page;
  - the splice refusing a layout it cannot see;
  - an entry refusing an unknown writer or nothing moved;
  - the three text writers' wiring;
  - absent, never null;
  - every recorded version declared, with a positive and a constructed negative;
  - md/web parity on a real page with two entries;
  - no record printed where none exists.
- **The full suite caught one red, fixed before the PR.** `test_extraction_version_changelog_py_js_parity`
  pins the header's stamp by its source literal. The first cut split that f-string, so the stamp
  still rendered but the pin could no longer see it. The header line is now built whole, as before,
  and extended only on a page with entries. The pin is unchanged; the rendering equals the approved
  preview.
- **Mutation.** Fifteen mutants, all killed:

  | mutant | tests failing |
  |---|---|
  | the splice lands after `anchor` | 2 |
  | null written when absent | 2 |
  | the refresh never records | 1 |
  | the refresh records a no-op | 1 |
  | the refresh re-stamps the page | 1 |
  | `mechanical` moved as one layer | 1 |
  | an entry stamps no version | 1 |
  | an unknown writer accepted | 1 |
  | the splice replaces instead of appending | 1 |
  | the splice accepts a wrong layout | 1 |
  | `anchor-backfill` unwired | 1 |
  | the md header shows nothing | 1 |
  | the md audit tier shows nothing | 1 |
  | the web header shows nothing | 1 |
  | the web shows the first, not the newest | 1 |

**BOUNDARY.**
- **Population:** the 26 committed dossiers at main @6dea4ddc; UBER's history is its 7 commits
  since its 2026-09-17 assembly.
- **Date:** measured 2026-10-09.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **No committed page carries its history yet.** Absent means "no change recorded", not "none
  happened": every one of the 26 has had layers landed by refresh passes. The backfill, which
  reconstructs each page's entries from git as the preview did for UBER, is its own artifact pass
  after this merges. Until it lands, the header looks as it did.
- **A reconstructed entry's writer is inferred** (an anchor-only change is `anchor-backfill`; the
  rest `refresh`). From this PR on, writers record themselves.
- **Found, not fixed:** `financials-backfill` writes the whole page with `json.dumps`, not the
  shared `dossier_json`. That is the two-serializer drift `dossier_json`'s docstring records fixing
  in `refresh_dossier`. Its entry splices correctly onto that output; the serializer itself is out
  of scope here.
- **An extractor change with no version bump (26b) still records the old version.** The record
  makes the gap visible, as on UBER's 2026-10-07 entries; it cannot detect it.
