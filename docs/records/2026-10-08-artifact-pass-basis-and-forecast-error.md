---
id: 2026-10-08-artifact-pass-basis-and-forecast-error
status: shipped
date: 2026-10-08
prs: [683]
supersedes:
superseded-by:
---

# Artifact pass: the forward layers carry their basis and the forecast-error cross-check lands — AMZN's stamp names the code that built it

**WHAT.** One pass over the 26 committed dossiers through `refresh_dossier`. Three top-level steps
run on each page:
- `forward_consensus_transform` — #681's basis keys;
- `forward_multiple_history_transform` — #681's quarter-end marks;
- `historical_forecast_error_transform` — #682's layer.

`mirror_to_frontend()` then runs once. There is no LLM call and no re-assembly, and every stored
synthesis is kept.

Before the refresh, AMZN's `extraction_version` was corrected from `2026-08-16.1` to
`2026-10-07.1` by a one-line edit. That is the vintage that built its 2026-10-08 page (#681's
record). The refresh then re-rendered both places the page prints the stamp.

**WHY.** Operator instruction, 2026-10-08: "merge 681 and then 682, then run the artifact pass".

**WHAT MOVED, measured against main @b6d73f1d:**
- **Files.** 54 changed and nothing else: 26 `dossier.json`, AMZN's `dossier.md`, and their
  frontend mirrors.
- **JSON.** +25,212 lines. The 50 removed lines are trailing commas moving (49), plus AMZN's
  stamp line.
- **`forward_consensus`.** The four basis keys landed on 24 pages. ORKA and TECX carry no
  reconciliation, because no line set is complete, so they get three. The existing keys — paths,
  spreads, revisions, withheld, as-of — are unchanged on all 26.
- **`forward_multiple_history`.** `latest_close_quarter_end` and `history_through` landed on the 23
  pages that have the layer. The existing keys are unchanged.
- **`historical_forecast_error`.** Landed on 24 pages. FUBO and ORKA have no Fiscal Years
  company-level block. On every page it came from the same Estimates export as that page's forward
  consensus, matched by hash.
- **Rendered pages.** Byte-identical on 25 names. AMZN's changed only in the two stamp lines.

**HOW VERIFIED.**
- **Per name, printed by the pass:**
  - keys landed;
  - the Estimates export's hash and as-of;
  - every other top-level key unchanged;
  - the existing forward-layer keys unchanged;
  - the forecast-error layer on the same export as the forward consensus;
  - the rendered page unchanged except AMZN's stamp;
  - `anchor` still last.

  No problems on any name.
- **Refusals.** None.
- **Frontend mirror.** Byte-identical: md 26 of 26, json 26 of 26.
- **Claim check, before the pass.** Every open PR (#511, #611, #616) was read file by file; none
  touches `data/dossiers` or `frontend/dossiers`. The claim branch was pushed before the pass ran.
- **Suite.** The full offline suite ran on the refreshed artifacts; the counts are in the PR.

**BOUNDARY.**
- **Population:** the 26 committed dossiers on main @b6d73f1d, and their on-disk CIQ exports. AMZN's
  Estimates export is still `e10ed62223`; the operator's 2026-10-08 re-pull is not installed.
- **Date:** measured 2026-10-08.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Other pages keep their assembly stamps.** A refresh lands layers without re-stamping a page,
  because the stamp names the extractor that ASSEMBLED it. Only AMZN's stamp was wrong about that,
  and only AMZN's was corrected.
