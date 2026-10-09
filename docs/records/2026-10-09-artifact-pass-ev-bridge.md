---
id:
status: shipped
date: 2026-10-09
prs: [690]
supersedes:
superseded-by:
---

# Artifact pass: 23 pages carry CIQ's current TEV claims — each equal to CIQ's own TEV less market cap, every exit held; FUBO, ORKA and TECX wait for a re-assembly

**WHAT.** One pass over the 26 committed dossiers through `refresh_dossier`, with one top-level
step, `ev_bridge_transform` — #689's `ev_bridge`. `mirror_to_frontend()` then ran once.
- **No LLM, no re-assembly:** every stored synthesis is kept.
- **No code changes.**

**WHY.** Operator instruction, 2026-10-09: "merge 689 and run the ev_bridge artifact pass".

**WHAT MOVED, measured against main @2ac08d02.**
- **Files.** 46 artifacts changed and nothing else: 23 `dossier.json` and their 23 frontend mirrors.
  The PR adds STATE.md row 10 and this record beside them; no code.
- **JSON.** +4,816 lines, none removed. Each page gains one block, before `anchor`.
- **Unchanged.** On every page, no other top-level key moved, `dossier.md` is byte-identical (the
  field is not rendered), and `anchor` is still the last field.
- **Left alone: FUBO, ORKA and TECX,** byte-identical. No structured field on their pages names the
  Financials export (#689's record). None has an NTM EV/EBIT multiple, so R4 loses nothing.

**What the 23 pages now say:**
- **Claims equal CIQ's own current TEV less market cap on 23 of 23**, the largest gap $0.056M (VRRM).
- **Claims differ from CIQ's 'Net Debt' line on 8 of the 23:**

  | name | claims − Net Debt ($M) | why |
  |---|---:|---|
  | GOOGL | +18,023 | CIQ's 'Total Pref. Equity' line — UNVERIFIED: Alphabet reports no preferred stock outstanding to our knowledge; what CIQ books there is not yet identified |
  | UBER | +1,083 | minority interest |
  | V | +514 | preferred (CIQ 'Total Pref. Equity') |
  | WLK | +503 | minority interest |
  | PARR / WERN / NCNO / EPAM | +37 / +27 / +14 / +0.6 | minority interest (each equals its 'Total Minority Interest' line) |

  With FUBO (+1,826) and ORKA, both not landed, these are #689's 10 of 26.
- **Net Debt nets beyond cash** on LLY ($796M) and EPAM ($0.046M).
- **Every exit is held:** 69 rows (3 fiscal years × 23), no consensus line same-basis.
  - 22 lines miss the balance sheet in at least one of their last three reported years;
  - MVST's can be checked on one year only.
  - Two lines are also not CURRENT (the rule requires the latest of the three to be the latest
    completed year): AORT's last three reported years are FY2022, FY2021 and FY2016; MVST's is
    FY2021. Their stored notes name the mismatch only. VITL's three skip FY2024.
- **The EDGAR cross-check is on 21.** MVST's and NFLX's anchors withhold net debt as under-captured,
  so their bridge carries none rather than a guess.
  - **What it shows** (|claims − EDGAR|, $M, the 21 pages, measured 2026-10-09): ≤ $1M on 4
    (EPAM, SMPL, ROST, CNXC); largest GOOGL 18,023 (the preferred line above), AMZN 9,640, UBER
    2,858, LLY 2,158, V 1,905, NKE 1,454, TGT 1,019. Relative to claims the widest is **VITL —
    CIQ $2.8M vs EDGAR $87.0M** (EDGAR's cash $21M against CIQ's $51M cash and ST investments),
    then AORT $202M vs $331M. Reported, not investigated in this pass.
- **Balance-sheet dates** run from 2026-03-29 (VITL) to 2026-08-01 (BURL, ROST, TGT); 12 pages are
  at 2026-06-30.

**HOW VERIFIED.**
- **The page's own exports, by hash.** On every landed page, the bridge's Financials hash is the
  one its own-history bands stamp, and its Estimates hash is the one its `forward_consensus` names.
  Both were found on disk by hash, and the Financials file is the one the bridge names: 23 of 23.
  - *The pass script's first version of this check failed on all 23.* It compared full digests
    against the repo's 10-character hash prefix (`file_provenance`). Re-run on the prefix, it holds
    23 of 23. The transform's own gate, which uses the prefix, had already passed.
- **Re-derived independently.** On every landed page, the stored block equals the builder's output
  on the same on-disk exports.
- **Per-page diff.** Every top-level key except `ev_bridge` was compared against main, as was the
  rendered page. No problems on any name. None refused.
- **Mirror.** Byte-identical to its source: json 26 of 26, md 26 of 26.
- **Claim check, before the pass.** Open PRs #511, #611 and #616 were read file by file. None
  touches `data/dossiers` or `frontend/dossiers`. The claim branch was pushed before the pass ran.
- **Suite.** The full offline suite ran on the refreshed artifacts; the counts are in the PR.

**BOUNDARY.**
- **Population:** the 26 committed dossiers at main @2ac08d02, and each one's on-disk Financials
  (quarterly), Estimates and comps exports (hash-matched).
- **Date:** measured 2026-10-09.
- **Units:** $M.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **#689's merge commit title says "differs from 'CIQ net debt' on 11".** That is the first cut's
  count, from before the review fixes. The correct figure is **10 of 26**, as #689's record and
  STATE row 10 say. The PR title was not updated before the squash, and a commit on main cannot be
  amended.
- **The extraction stamp lags the field.** No page's `extraction_version` moved: 22 still stamp
  `2026-08-16.1` and AMZN `2026-10-07.1`, while the field they now carry is named by
  `2026-10-08.4`. A refresh transform does not re-stamp; a reader comparing stamps will not see
  that these pages carry the bridge.
- **The page does not show the bridge yet.** It is in the JSON (machine-complete). The R4 card
  render is a layout change under the preview rule, due before any R4 record.
- **The build-up is CONFIRMED as the bridge.** Asked after the pass, the operator answered "yes
  confirmed" (2026-10-09). The ruling is recorded as amendments to `2026-10-08-ev-bridge.md` and
  `2026-10-08-r4-forward-ev-ebit.md`, and in STATE row 10.
- **Next in the ruled build order:** the R4 template, reading `exit_claims` (STATE row 10).
