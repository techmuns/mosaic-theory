---
id:
status: shipped
date: 2026-11-05
prs: [909]
supersedes:
superseded-by:
---

# A forward-year consensus row's ref names its sheet, then its row: #903's ref ran the metric into the sheet name, and the first page built on it turned the CIQ map guard red

**WHAT.** `ciq_sheets.consensus_level_ref` — the one function assembly
(`mechanical._consensus`) and the refresh transform (`refresh.consensus_transform`) both call to
name a `consensus_context.consensus_levels` row (#903, item 29) — now writes
`CIQ Estimates→Consensus · EBITDA FY2027 (median, high, low, std dev, estimates)`. #903 wrote
`CIQ Estimates→Consensus EBITDA FY2027 (…)`, with no delimiter between the sheet and the row. Every
other ref keeps the `CIQ <workbook>→<sheet>` convention with ` '`, ` (`, ` —`, ` ·` or `[` after the sheet,
and `tests/test_quality_ciq.py`'s `_CITED` reader of that convention took "Consensus EBITDA FY2027"
for a sheet. Extraction version `2026-11-05.consensus-ref-names-its-sheet` (both twins; drift
table re-pinned). The figures are unchanged.

**WHY.** SMPL's 2026-11-04 page (run `29e8038c`, branch `artifacts/smpl-2026-11-04`) is the first
committed page built on #903's code. It carries 14 such refs (Revenue and EBITDA, FY2027..FY2033),
and `test_every_sheet_the_committed_pages_cite_is_in_the_map` went red on all 14 as undeclared
sheets. No committed page on main carries one yet, so main is green; every page built from now on
would carry them. The operator's coordinating session ruled the fix belongs to the ref, not the
test: the reader reads the convention correctly, and the ref broke it.

**HOW VERIFIED.**
- **The pin fails first.** `test_a_consensus_level_ref_names_the_consensus_sheet_then_its_row`
  runs the real function over the metrics the builder reads (`ciq_sheets.CONSENSUS_METRICS`,
  which `ciq_sheets.consensus_levels` iterates for both callers) at FY2027 and
  FY2033. On the unfixed function it fails ("Extra items in the left set:
  'Estimates→Consensus Revenue FY2027'"); on the fix it passes. It asserts the ref still names its
  row (`EBITDA FY2027` after the sheet), and keeps the observed failure shape — the old string,
  copied from SMPL's page — reading as the undeclared sheet it looks like, so the guard can still
  catch it.
- **Real page, $0.** A copy of SMPL's built page (`29e8038c`), run through
  `refresh_dossier(path, transform=consensus_transform("SMPL"))` on this code with the 2026-11-04
  exports linked: `_CITED` finds 38 sheets cited, 14 undeclared, before; 24 cited, 0 undeclared,
  after. The refresh changes 15 JSON paths: the 14 refs and one `layer_refreshes` entry
  (`writer: refresh`, `layers: ["mechanical.consensus_context"]`, the new extraction version).
  Nothing else moves. This is the path SMPL's artifact branch uses to re-stamp its refs after this
  merges; `dossier.json` is not hand-edited.
- **Every consumer.** The string is built in one place and read by: assembly
  (`mechanical._consensus`), the refresh transform (`refresh.py:407`),
  `test_both_consensus_level_builders_name_a_row_alike` (equality through the function — green),
  and `_CITED`. No synthesis point on SMPL's page cites one, the Markdown renderer does not print
  them, and `frontend/` carries no twin of the string. The frozen
  `tests/fixtures/prespend/2026-11-04/SMPL-mechanical*.json` builds keep the old refs: they are
  frozen vintages read for drawdown and field statuses, never for ref strings. One reader of the
  rows does not use the function: `propose.propose_anchors` cites its revenue base as
  `CIQ Estimates→consensus_levels Revenue FY{fy} (…)`, a ref of its own that `_CITED` cannot read
  (its sheet starts lower-case). It is unchanged here and left as found.

**BOUNDARY.** Refs counted on SMPL's page as built by run `29e8038c` (2026-11-04 18:58Z), every
string field whose key contains `source`; the map is `vinci.quality.sources.ciq.FAMILIES[*].cited_as`
at main `2771d9a1`.

**WHAT IT COSTS / WHAT IS ACCEPTED.** Nothing re-stamps a page by itself: a page built on #903's
code before this merges keeps the old refs until its refresh or re-assembly. SMPL is the only one,
and its artifact PR re-stamps it at $0.
