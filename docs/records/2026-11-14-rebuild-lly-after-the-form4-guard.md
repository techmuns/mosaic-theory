---
id:
status: shipped
date: 2026-11-14
prs: [1071]
supersedes:
superseded-by:
---

# LLY is re-assembled once on main `188e0476`, after the Form 4 price guard: priced at the 2026-11-11 close with Polygon and Tiingo calls blocked, $3.81 of group 2's remaining $4.57 on anthropic 2.6.0, its insider line names its largest sale UNKNOWN with the refused-price reason in place of $57,664.29M, it loses only the accepted `buyback_shares` (2021-H1), and its proposal stays BUY

**WHAT.**
- **The rulings.**
  - The paid build: the operator, through the coordinator, 2026-11-14: "Rebuild LLY after the fix (Recommended)". It followed #1069's merge (`188e0476`), the guard its held build had needed (`docs/records/2026-11-14-rebuild-group-2-epam-lly-vitl.md`, LLY IS HELD).
  - The field loss: the operator, 2026-11-13: "accept all three" (#1004, issuecomment-6847662066). Group 2's record lists LLY's accepted loss as `capital_allocation.buyback_shares` (2021-H1).
  - The go was conditional, and the condition was checked before any paid call: the precheck's one regression is that field over 2021-01-01→2021-06-30, with 0 post-spend refusals.
- **The build:** once, run `fccad3e8`, **$3.81** (6 calls, 0 failed, 570 s), with no refused re-roll. Group 2 has now spent $14.46 of its $15.22 cap, LLY's held $3.70 included; the rebuild's spend is $36.22 of $46.29 (groups 1–3, $32.41, and this build), summed from each run line's unrounded `usd`.

| | LLY |
|---|---|
| committed page before | 2026-11-03T15:19:40Z, ext `2026-11-03.ex-lease-share-cut`, reference 2026-10-16 |
| $0 precheck on the 11-11 store, main `188e0476` | exit 1 · the accepted regression only · 0 post-spend refusals (116 fields) |
| run · cost · calls (0 failed) | `fccad3e8` · $3.81 · 6 |
| last cost before | $3.70 (`48120f17`, group 2's held build, 2.6.0) |
| price (close 2026-11-11) | $1,437.29 (was $1,410.99, 11-02) |
| lean (5 draws) | strongly-bullish (5 / 5), as before |
| machine proposal (`verdict.derive_proposal`, sleeve quality) | BUY → BUY, now proposed under the 5-of-5 rule |
| R1 anchor base $/sh | 752.2356 → 752.2356 |
| `valuation_basis.priceable` | false → false |
| UNTRACEABLE caveats | 24 → 5 |
| disclosure gaps | absent → 5 |
| Sourced fields lost | `capital_allocation.buyback_shares` (2021-H1), accepted |

- **The insider line**, on the committed page (`mechanical.catalyst_path.insider_activity`, present):
  - "… largest sale UNKNOWN — 19 of 729 sales in the 3y scanned carry a stated price this reader refuses (first: Form 4 0000316011-25-000073: its 4 'S' prices run $1,030.31 to $1,032,319.00, more than 5-fold apart, so none is used) …";
  - neither "57664" nor "57,664" appears in the page JSON. The rendered page (`dossier.md:657` and its mirror) names "$57664.29M" once, in its Extraction note, quoting #1069's vintage on the figure it refuses;
  - main's page had stated the line UNKNOWN (5 of 392 Form 4 filings unreadable in its 11-03 build); the 182-day counts read "sells 6 (5 insiders, $34.59M)".
- **The covenant table's "cost bound / fetch fail" line** (STATE row 63): LLY carries none; its table has 0 rows, before and after.
- **The as-of snapshot, the vendor guard and the store** are group 1's: content sha256 `598a3d2c07f17df5f071742f1a0ea6cc23452f02334c0273bc755de523fa1cb6` (2,543,246 rows, frontier 2026-11-11), re-read before this build. The page's 14 Polygon reference responses came from the 11-11 cache; 0 were refused and 0 fetched live.
- **The spool,** write-once: 82 files added (50 claims, 32 located passages). The 2,671 there after group 3 are unchanged by sha256 and mtime, and none is missing: 2,753 now.

**WHY.** LLY is one of the 10 active pages. Its group 2 build was held because its insider line priced a sale from a malformed Form 4 price, and that line reached its synthesis request. #1069 refuses such a price, so the page can carry fix request 2's code now.

**HOW VERIFIED.**
- **The $0 precheck**, boundary lines per RUNBOOKS §i step 4: committed page assembled 2026-11-03T15:19:40Z, `2026-11-03.ex-lease-share-cut`, reference 2026-10-16; its export stamps `0fa91cd481` ×1, `f78a1d4720` ×3 and `f8c731a5c7` ×8 are on disk; 116 fields compared.
- **After the build,** `prespend.compare` (main's committed page against the written one) lists the 1 accepted regression, 0 list members gone and 0 moves; it gains the insider line and the two drawdown-anchor shapes.
- **The run record** states `sdk_version` 2.6.0, `claude-opus-4-8`, schema 3; the 4 later framing draws each read the 281,672-token prompt cache, 0 re-writes.
- **The gate, CI-style,** in a clean worktree at `444ad2ef` (the artifact commit `bd8343bd` merged with `origin/main` `e17ceee9` and `6652a242`): ruff clean, `mypy --strict` clean on 219 files, 11,368 passed, 661 skipped, 11 xfailed, 0 failed (pytest exit 0, counted from its progress line), and the mirror in sync.
- **The local 12-word transcript guard,** at head `9cfe4153`: 91 calls read; 3,168 files scanned; 112 runs shared with a call, 96 excused by SEC filings and 16 by Key Developments exports (IT's 4 from #1070 among them); 0 unexcused; no LLY file carries a KD-only run.
- **The cross-setup section** (`python -m vinci.impact run`, head `444ad2ef`, patch-id `da016fe1`): nothing moves, because `vinci/` is identical; the PR changes no test.

**THE SDK (#1049's falsifier).** 6 calls, 0 failed, on 2.6.0, and 0 of 4 later draws re-wrote the prompt cache. Across the rebuild that makes 70 calls, 0 failures, and 1 cache re-write in 36 later draws on 2.6.0, against 2 in 176 on 0.112.0.

**BOUNDARY.**
- **Code:** main `188e0476` for the build, on branch `artifacts/lly-after-form4-guard-2026-11-14`; the gate and the cross-setup section at `444ad2ef`.
- **Page:** LLY's committed `dossier.json` at `188e0476` (= `1f32cbdf`'s).
- **CIQ:** the operator's exports on disk, read only.
- **Build:** 2026-11-14 12:51:34Z → 13:01:04Z.
- **Spool:** hashed before (2,671) and after (2,753) this build.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $3.81 of the $4.57 left in group 2's cap.
- The accepted `buyback_shares` loss: the latest TreasuryStockSharesAcquired covers 2021-H1, 1,960 days before the price date.
