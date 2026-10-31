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
  - **The anchor bridge's lease rows (`ciq_balance.extract`).** Round 2 below: where CIQ's Total
    Debt is shown to carry its lease rows (33 of 34 exports) the net debt says lease-inclusive and
    nothing is added or refused; elsewhere:
    - An absent row is named in the net-debt fact's basis.
    - A marker on one makes the fact unavailable, with its reason.
    - Both rows used to be added as `or 0.0`.
  - **`ev_gap._margin_figures`** shows no EBITDA margin beside the street's when an operating
    margin has no D&A to convert it (round 2: a ratio or an absolute D&A, as `our_ebitda`). It
    used to add an absent ratio as 0, so an EBIT margin stood under the EBITDA label.
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
- **Pages.** The unread lines, and the R4 basis text built from them, change at each page's
  re-assembly (STATE row 41). No committed page is re-assembled here. Two boundaries:
  - the 13 pursued pages: 21 lines (18 absent rows; UBER's preferred '-', LLY's and CNXC's minority
    'NA');
  - all 24 committed bridges: 39 lines (31 absent rows; 8 markers — also BRBR's minority 'NA', MVST's
    preferred '-' and minority 'NA', VITL's preferred '-' and minority 'NA').
  Each bridge was rebuilt 2026-11-01 from the page's own exports, found by sha. Claims are unchanged
  on all 24, and the 23 R4 prefills are equal before and after. AORT refuses both ways: its bridge
  already disagrees with CIQ's TEV by −128.3 $M.
- **Reported, not changed.** The lint's nine REPORTED entries, in seven functions outside Session
  A's files, each a possible stated zero:
  - `lease_basis.observations`'s EDGAR finance lease;
  - `mechanical._split_straddled_trend`'s rose/fell (×2);
  - `primary_source.guide_verification_read`'s highs (×2);
  - `monitor.render_table`'s excess return (+0.00 on the monitor table);
  - `scoring.to_markdown`'s "does NOT beat" on a missing basket return;
  - `desk.gates`' count;
  - `cli.fmt`'s median.

**ROUND 2 (coordinator review of 001b2e32; one commit, each fix behind a test failing there).**
- **CIQ's Total Debt already carries its lease rows.** On 33 of the 34 current non-held quarterly
  exports (2026-11-01), Total Debt at its latest column equals 'Short-term Borrowings' + 'Curr.
  Port. of LT Debt' + 'Curr. Port. of Leases' + 'Long-Term Debt' + 'Long-Term Leases' there within
  0.6 $M; 31 of the 33 carry a valued lease row. The 34th is LLY's press-release column, every row
  of it a marker.
  - CIQ's net debt is therefore lease-inclusive. The first cut's basis ("no lease is added") read
    as lease-exclusive, and its proposed follow-up — changing the add-on labels — would have
    double-counted.
  - `ciq_balance._leases_in_total_debt` now shows it from the sheet's own rows. Where it holds, the
    net-debt fact says "lease-inclusive" and names the lease rows, the 'Capital Leases' /
    'Operating Lease Liabilities' add-on is never added on top, and a marker on it refuses nothing.
  - No value moves; ORKA's fill (−871.1) is unchanged.
- **The R4 block's components carry the reason** (`BridgeComponent.unread`, absent when unset). The
  two living-page tests that summed bridge values (`test_r4_template`, `test_valuation_basis`) sum
  the read lines and name the unread ones. Both now run on the page as its owed rebuild writes it:
  the old bodies raise TypeError there (float + None), which would have turned the AMZN/UBER
  rebuild red. `test_forward_consensus` guards a marker leg the same way.
- **`ev_gap._margin_figures` converts as `our_ebitda` does.** An EBITDA-basis margin needs no
  conversion; an operating margin takes its D&A ratio, or its absolute D&A over its revenue. The
  first cut returned None for both; only with neither is there no figure.
- **`AnchorMidcycleGap.median_years` is None, never 0, when unknown.** Its allowlist entry is gone.
- **The R4-prefill decision-path test** reads MVST's frozen case, a bridge `ev_bridge` built from a
  real '-' preferred and 'NA' minority, instead of a hand-edited dict.
- **`test_the_lint_can_fire`** runs `sites()` on a planted package.
- **DEFERRED, with a census.** Widening the lint to `.get(k, 0)`, `x if … else 0`,
  `getattr(o, k, 0)`, `x or -0.0` and `x or "0"` finds 251 sites in `vinci/` at 08948b5a, mostly
  counters and arithmetic guards. It needs its own reviewed census, not a nit's edit. Reported from
  that census, on EDGAR/CIQ values:
  - `edgar/net_debt.py`'s `_borrowings` and `_unread_debt` (`… if b else 0.0`, A4's file);
  - `ciq_sheets.pe_eps_basis`'s `pe.get(p, 0)`, a `> 0` gate.
