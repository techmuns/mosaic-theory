---
id: 2026-10-30-zero-coercion
status: open
date: 2026-10-30
prs: []
supersedes:
superseded-by:
---

# A CIQ marker or an absent row is no value, never 0 — one cell reader, eight sites fixed, and a lint holding the rule (audit RC1: A-D1, A-D2)

**WHAT.**
- **One reader.** `ciq.read_cell(cell)` returns `(value, marker)`.
  - The marker is CIQ's word for "no value" as the cell holds it ('-', 'NA', 'NM', '' for a blank).
  - Text that is neither a number nor a marker reads as neither, so a caller can tell CIQ's "no
    value" from a cell it cannot parse; `clean_num` returned None for both.
  - 'No Data Available' joins `_UNAVAILABLE_CELLS`. `clean_num` is now `read_cell(...).value`.
- **Eight sites fixed** (18 `or 0` expressions on 11 lines at 08948b5a):
  - **A-D1, the revision counts.** `_revision_breadth`, `_forward_revisions` and `_horizon_value`
    print a marker as 'n/a', never 0. `RevisionCount.up` / `down` become `int | None`. Both
    renderers show an 'n/a' line rather than folding it into "no revisions in any window", and
    the theme desk's revisions figure prints 'n/a'.
  - **A-D2, the EV bridge.** A preferred or minority line CIQ does not state has `value: None` and
    `ClaimLine.unread` says why: "the balance sheet carries no '…' row", or "'…' reads 'NA' at
    [column]". The claims sum the legs CIQ states, so no value moves. CIQ's own TEV less market
    cap still checks the total.
  - **The R4 prefill (`propose.r4_bridge_fact`)** states such a leg as "preferred not stated
    (reason)", where it wrote "preferred 0.0". The value is unchanged.
  - **The anchor bridge's lease rows (`ciq_balance.extract`).**
    - An absent row is named in the net-debt fact's basis.
    - A marker on one makes the fact unavailable, with its reason.
    - Both rows used to be added as `or 0.0`.
  - **`ev_gap._margin_figures`** shows no EBITDA margin beside the street's when the recipe leg
    carries no D&A ratio. It used to add it as 0, so an EBIT margin stood under the EBITDA label.
  - **The credit scores** (`_industry_credit_panel`, `credit_health_panels`) are rewritten to
    narrow `None` explicitly. Their `or 0` could not fire, but carried the shape.
- **A lint, `tests/test_zero_coercion_lint.py`.**
  - It finds every `x or 0` / `x or 0.0` in `vinci/` by AST, keyed by file, enclosing function and
    expression, and counted. It refuses any not in a reviewed allowlist.
  - Each of the allowlist's 54 entries states why it carries no figure: a sort key, a gate a None
    must fail, a None already excluded, or run accounting.
  - Nine entries, in seven functions outside Session A's files, are marked REPORTED (see "WHAT IT COSTS").
  - A stale entry also fails.
- **The synthetic Estimates export gains a Revisions sheet** (`tests/fixtures/ciq_synthetic`), in
  the layout of every real one.

**WHY.**
- `x or 0` turned a None — a CIQ marker, a row the sheet does not carry — into a stated zero.
- **Live:** all 13 pursued pages print 21 preferred/minority lines as 0.0 with nothing behind them.
  18 are absent rows and 3 are markers (UBER's preferred '-', LLY's and CNXC's minority 'NA').
  The R4 record's basis is written from those lines.
- **Latent:** the revision counts (CIQ writes explicit zeros; a marker is no count), the lease
  rows, the EV gap's D&A ratio and the credit scores.

**HOW VERIFIED.**
- **Failing first, on main 08948b5a:**
  - The lint fails, naming exactly the 18 expressions on 11 lines and nothing else.
  - `tests/test_zero_coercion.py` fails at import (`read_cell` does not exist). It passes 34 here,
    covering each of the 8 `gen.MARKERS` through `read_cell`, the revision counts, the bridge and
    the lease rows, plus the R4 prefill, the EV gap and both renderers end to end.
  - The strict xfail `test_a_marker_in_the_ev_bridge_is_never_a_zero_claim` passes, and its marker
    is removed.
- **Shown run (decision path, R4 prefill).** Each pursued page's `ev_bridge` was rebuilt on this
  branch from the page's OWN exports, found by sha in `mosaic-theory-ta`'s `ciq/` and
  `ciq-archive/`. Then `r4_bridge_fact` was run on the committed page (before) and with the
  rebuilt bridge (after). Result: 13 of 13 pages, 21 lines become unread with their reasons, the
  claims are unchanged on all 13, the R4 value is unchanged on all 13, and the basis states each
  leg.
- **Replay** under main's code and this branch's, over the 26 committed pages' names on their `-ta`
  exports: 0 differences in the horizon read, the EPS and revenue revision lines, the 1,968
  forward revision counts (none with a marker leg), the credit panels and the bridge's net-debt
  value.
- **`tests/fixtures/ev_bridge_cases.json`'s 8 cases** were rebuilt from their own exports, found by
  sha. Only the preferred/minority lines change, except on LLY, whose frozen line sources predate
  #861's serial-date label (`[46203.0]` → `[Jun-30-2026]`). That case was frozen from the
  mislabelled pair, built directly here.

**BOUNDARY.**
- **Census:** `vinci/` at 08948b5a — 72 `or 0` / `or 0.0` expressions on 62 lines. 18 are fixed;
  54 are allowed, each with its reason.
- **Pages:** the 13 pursued committed pages (PARR, UBER, GOOGL, AMZN, V, ORKA, SMPL, LLY, NFLX,
  ROST, TJX, CNXC, NKE), each rebuilt from its own exports; the replay covers all 26 committed
  pages' names less the held pack.
- **Lease rows:** 0 of 34 current non-held quarterly balance sheets carry 'Capital Leases' or
  'Operating Lease Liabilities'. CIQ's rows are 'Curr. Port. of Leases' and 'Long-Term Leases'
  (34 of 34).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Pages.** The 13 pages' 21 lines, and the R4 basis text built from them, change at each page's
  re-assembly (STATE row 41). No committed page is re-assembled here.
- **Reported, not changed.** The bridge's lease reads match no CIQ row on any export, so `net_debt`
  is debt − cash everywhere, now stated. Whether CIQ's Total Debt already holds the leases decides
  if the labels should change; that is a definition question, not this PR's. The lint's nine
  REPORTED entries (seven functions) also sit outside Session A's files, each a possible stated zero:
  - `lease_basis.observations`'s EDGAR finance lease;
  - `mechanical._split_straddled_trend`'s rose/fell (×2);
  - `primary_source.guide_verification_read`'s highs (×2);
  - `monitor.render_table`'s excess return;
  - `scoring.to_markdown`'s "does NOT beat";
  - `desk.gates`' count;
  - `cli.fmt`'s median.
