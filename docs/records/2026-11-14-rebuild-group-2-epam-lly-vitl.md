---
id:
status: shipped
date: 2026-11-14
prs: [1068]
supersedes:
superseded-by:
---

# Rebuild of the 10 active pages, group 2: EPAM, LLY and VITL are re-assembled once each on main `1f32cbdf`, priced at the 2026-11-11 close on the cache-filled store with Polygon and Tiingo calls blocked, for $10.65 of a $15.22 cap on anthropic 2.6.0 — each loses only the fix-3b figure the operator accepted, and no machine proposal moves

**WHAT.**
- **The scope and the rulings** are group 1's (`docs/records/2026-11-14-rebuild-group-1-ncno-smpl-tjx.md`):
  - the operator's coverage marking of 2026-11-13;
  - the 2026-11-14 rulings on prices ("Fill to 11-11 from cache (Recommended)"), caps ("#1041's rule, $52.97 total (Recommended)") and reference data ("11-11 cache, calls blocked (Recommended)");
  - the go, "post it and start the rebuild".
- Group 2's losses are the three the operator accepted on 2026-11-13 ("accept all three", issuecomment-6847662066).
- Each page was built once, in the order EPAM, LLY, VITL, one at a time, with no refused re-roll.

| | EPAM | LLY | VITL |
|---|---|---|---|
| committed page before | 2026-11-09, ext `2026-11-09.asof-cut` | 2026-11-03, ext `2026-11-03.ex-lease-share-cut` | 2026-11-09, ext `2026-11-09.asof-cut` |
| $0 precheck on the 11-11 store | exit 1 · the accepted regression only · 0 refusals (117 fields) | exit 1 · the accepted one · 0 (116) | exit 1 · the accepted one · 0 (110) |
| run · cost · calls (0 failed) | `56a96aa8` · $4.46 · 8 | `48120f17` · $3.70 · 6 | `24bce72d` · $2.49 · 6 |
| last cost before (0.112.0 by the records) | $4.49 (`53365700`, 8 calls) | $3.03 (`ac8b8b71`, 6) | $2.59 (`d7e1ac46`, 6) |
| price (close 2026-11-11) | $162.82 (was $159.31, 11-06) | $1,437.29 (was $1,410.99, 11-02) | $9.47 (was $9.52, 11-06) |
| lean (5 draws) | mixed (5 / 5) | strongly-bullish (5 / 5) | mixed (5 / 5) |
| lean before | mixed (5 / 5) | strongly-bullish (5 / 5) | mixed (5 / 5) |
| machine proposal (`verdict.derive_proposal`, as the page derives it) | none → none | BUY → BUY | none → none |
| R1 anchor base $/sh | 391.7766 → 391.7766 | 752.2356 → 752.2356 | none → none |
| covenant table rows | 14 → 16 | 0 → 0 | 0 → 0 |
| UNTRACEABLE caveats | 10 → 15 | 24 → 7 | 4 → 13 |
| customers listed | 172 → 172 | 54 → 54 | 15 → 15 |
| Sourced fields lost | `capital_allocation.buyback_avg_price` (2023-Q1), accepted | `capital_allocation.buyback_shares` (2021-H1), accepted | `capital_allocation.buyback_shares` (2019), accepted |

- **The losses are exactly the accepted three.** `prespend.compare`, committed page against written page, lists the one regression on each, with 0 list members gone and 0 moves.
- **Other value changes, read leaf by leaf against main `1f32cbdf`:**
  - LLY's and VITL's `buyback_cash` keep their values (4,334.0; 35.001). Their "PERIOD MISMATCH" note leaves with the stale share count it compared against.
  - LLY's `catalyst_path.insider_activity` goes unknown → present.
  - EPAM's covenant table gains two rate floors ("Base Rate floor", "Euro-Rate floor") and loses no row. Three of its terms are refused to UNKNOWN because their value states figures their quote doesn't (E5): the financial-maintenance covenant's "4.00 to 1.00", a principal set and a prepayment threshold.
  - EPAM's 10-K exhibit `exhibit1017-epamnonxempl.htm` (`0001352010-26-000015`) is refused as not a debt agreement (E5).
  - `layer_refreshes` empties on all three, as on any fresh assembly.
  - The remaining moves are lists re-drawn by this build (synthesis points, transcript driver rows) or re-read under fix request 2's code (release guides).
- **The store** is group 1's working copy, content sha256 `598a3d2c07f17df5f071742f1a0ea6cc23452f02334c0273bc755de523fa1cb6`, frontier 2026-11-11, unchanged after the three builds.
- **One as-of date, vendor calls blocked.** Every build ran under the guard that refuses `api.polygon.io` and `api.tiingo.com`; 0 were refused. Each page read its 14 Polygon reference responses from the 11-11 cache (`fetched_at` 2026-11-11 03:53–04:00Z in its built-from record), beside price series ending 2026-11-11. Live reads: EPAM 0, LLY 1 FINRA, VITL 1 FINRA.
- **The transcript evidence** went to the operator's spool (`manual/driver-evidence/`), write-once: 100 files added (76 claims, 24 located passages). The 2,333 there after group 1 are unchanged by sha256 and by mtime, and none is missing.
- **One pin moved** (`5619c9ed`): `test_vote_rule::test_an_old_page_renders_as_it_did` read LLY's living page as its pre-rule example. It now reads `tests/fixtures/frozen_pages/2026-11-03/LLY/`, byte-identical to main `1f32cbdf`'s page.
  - Review round 0 (`58189bab`) pins the frozen line whole, and raises the post-rule non-vacuity floor to the six pages built after the rule.

**WHY.** These are the next three of the 10 active pages, rebuilt so each carries fix request 2's code once. The order agreed with B on #1004 was the venv re-sync, then this rebuild.

**HOW VERIFIED.**
- **The $0 precheck** on the 11-11 working copy (2026-11-14, before any spend). Its boundary lines, per RUNBOOKS §i step 4:
  - EPAM: committed page assembled 2026-11-09T16:20:08Z, `2026-11-09.asof-cut`, reference 2026-10-16; stamps `43be6ee5bf` ×9 and `bc5ae927c4` ×3 on disk; 117 Sourced fields compared.
  - LLY: 2026-11-03T15:19:40Z, `2026-11-03.ex-lease-share-cut`, reference 2026-10-16; stamps `0fa91cd481` ×1, `f78a1d4720` ×3 and `f8c731a5c7` ×8 on disk; 116 compared.
  - VITL: 2026-11-09T17:21:21Z, `2026-11-09.asof-cut`, reference 2026-10-16; stamps `5f7e3a18e3` ×5 and `bf60a27323` ×3 on disk; 110 compared.
- **After each build,** `prespend.compare` gave the accepted regression only (above).
- **The run records** state `sdk_version` 2.6.0, `claude-opus-4-8`, schema 3.
- **The gate, CI-style,** in a clean detached worktree at `28661046` (the merge of `origin/main` `0f5e3eb2`):
  - ruff clean; `mypy --strict` clean on 219 files;
  - `pytest -m "not network"` 11,359 passed, 665 skipped, 11 xfailed, 0 failed;
  - the frontend mirror is in sync.
  - A probe of the same gate before the pin moved failed on exactly that one node.
  - After review round 0 (`58189bab`), `tests/test_vote_rule.py` passes 22 of 22.
- **The local 12-word transcript guard** on this branch, with the calls and the SEC cache on disk:
  - 91 calls read; 3,155 files scanned;
  - 108 runs of 13+ words shared with a call: 96 excused by SEC filings and 12 by Key Developments exports;
  - 0 unexcused. None of the KD-only runs is on EPAM, LLY or VITL.
- **The review's CIQ-linked local run is not green, and not this branch's doing.** PARR's quarterly export, a byte copy of its annual, raises `CiqMislabelledError`, and workbook drift fails `test_forward_consensus[LLY]`, `[GOOGL]` and `test_estimate_year_derivation[V]`. None of those reads a page this branch changes.
- **The cross-setup section** (`python -m vinci.impact run`, head `58189bab`): nothing moves, because `vinci/` is identical; the one changed test file runs 22 nodes, 0 failing at head. It is in #1068's body.
- **Read-only inputs:** the CIQ exports and the primary's `data/vinci.db` are as hashed before group 1.

**THE SDK (#1049's falsifier).** 20 calls, 0 failed, all on 2.6.0. Against each page's last 0.112.0 build: EPAM $4.49 → $4.46, LLY $3.03 → $3.70 and VITL $2.59 → $2.49, each on the same call count. No later draw re-wrote the prompt cache (0 of 12). With group 1, that is 1 of 24 later draws on 2.6.0 against 2 of 176 on 0.112.0, not distinguishable. The code moved too, so this describes the builds and does not test the SDK.

**FOUND, NOT FIXED.**
- **The covenant table's "cost bound / fetch fail" line** (group 1's record; `vinci/dossier/render.py:1943-1944`, `frontend/views/shared/dossier.js:3139`) also stands on EPAM's new page.
  - It names `0001352010-26-000015`, the 10-K exhibit refused as not a debt agreement (E5). NCNO's `0001902733-26-000022` and TJX's `0000109198-26-000008` are the same shape.
  - 15 committed pages carry the line: AMZN, BRBR, BURL, CNXC, EPAM, NCNO, NFLX, NKE, PARR, TGT, TJX, UBER, V, VRRM, WLK.

**BOUNDARY.**
- **Code:** main `1f32cbdf` for the builds, on branch `artifacts/epam-lly-vitl-rebuild-2026-11-14`, merged with `origin/main` `0f5e3eb2` before the gate.
- **Pages:** the three committed `data/dossiers/<T>/dossier.json` at `1f32cbdf`.
- **Store:** the 11-11 working copy above.
- **CIQ:** the operator's Drive `manual/ciq` as of 2026-11-13, read only.
- **Costs:** `usd` of the three run lines, list price; the 0.112.0 side is each page's last committed run line.
- **Spool:** the folder's flat file list, hashed after group 1 (2,333) and after VITL (2,433).
- **Builds:** 2026-11-14 06:15:39Z (EPAM start) to 06:49:00Z (VITL finish), per the run lines.
- **Leaf comparison:** every JSON leaf non-null at `1f32cbdf` and null or absent at the written page.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $10.65 of the $15.22 cap; groups 1 and 2 together $23.59 of $32.92, inside the operator's $170.
- The three fix-3b losses, by the operator's ruling.
- The pages are priced at 11-11, not the latest close, by ruling.
