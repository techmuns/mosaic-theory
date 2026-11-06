---
status: recorded
date: 2026-11-07
prs: [926]
supersedes:
superseded-by:
---

# Fix 3a (#923) measured on the panel under the replication rule ($30.72 of $40): M-LABEL 69 → 47 units at p_lower 0.000075, below the 0.01 ship bar, so it ships by the registered rule with no replication; no class worsens; two lean moves (MCK, SMPL) are explained below as within noise; items 3–4 are read only by the no-worsening checks and item 5 is not exercised

**THE APPROVAL.** Operator, 2026-11-07, verbatim: **"Approve, cap $40"**, answering the
coordinator's question "Measure #923 under the replication rule, capped at $40?". One budget ledger
was opened with `python -m vinci.evals budget-open`, carrying the words "Approve, cap $40
(2026-11-07): measure #923 under the replication rule". The ledger, the registration, the raw draws
and the score log are kept OUTSIDE the repository, in this session family's notes folder under
`synthesis-eval-fix3a/`. The requests carry licensed transcript text and stay in the session's
scratch folder only. The cap was not raised, and no other approval was opened.

**THE RESULT IN SIX LINES.**
- **By the registered rule, #923 SHIPS on its first run.** The target M-LABEL fell 69 → 47 units
  over 30 draws per arm (p_lower 7.5 × 10⁻⁵, against the 0.01 ship bar). No replication is needed.
- **No class worsened beyond noise:** M-ABSENT 60 → 48, M-PATH 7 → 4, M-SIGN 0 → 0.
- **Two modal leans moved, and no proposal did.** MCK went mixed 4/1 → bullish 4/1, and SMPL mixed
  3/2 → bearish 4/1. Each is within one page's noise (§5).
- **The fall is real but partial.** The bleed family fell 14 → 1 and the trailing-only family
  37 → 13. The "no adjusted forward" family ROSE 12 → 27, so some of the old framing moved into
  other words (§4).
- **What the measurement does not cover:** items 3–4 (the "(a risk)" tags and the discount
  question) are read only through the no-worsening checks; no metric counts them. Item 5 (the
  print row) is not exercised on the panel (§6).
- **Spend:** $30.7161 of $40; 60 calls, none failed.

## 1. What was measured, and how the change reaches the request

#923 rewrites five labels the fact layer writes. A replay reads the committed layer, so each label
reaches the request only through a transform (`vinci/evals/variants.py`; `FIX_3A` names the five).
Each transform rebuilds its field with the REF's own builder, from the page's own facts:

| # | label | transform | the ref's code it calls |
|---|---|---|---|
| 1 | drawdown shape with no −10% day | `relabel_drawdown_shape` (existed) | `mechanical._CURRENT_WORDS.none_shape` |
| 2 | trailing EV/EBITDA's "trailing only" note | `trailing_only_note` | `mechanical.ev_ebitda_note` (absent at main: the committed note stands) |
| 3 | survival tags "(a risk)", "solvency risk" | `survival_read` | `mechanical._survival_capacity` |
| 4 | the discount-assuming peer question | `peer_gap_question` | `ciq_sheets._comps_deltas` |
| 5 | the catalyst print row on a superseded guide | `print_row_guide` | `mechanical._catalyst_calendar`, its two EDGAR reads replaced for that call by the committed print date and basis |

- **Items 2 and 4 read the page's OWN comps export.** Before using it, the ref's code must rebuild
  the page's committed `valuation.cross_sectional` and `peer_comps.trading_multiples` byte for
  byte, or the transform refuses (`own_comps`). No transform guesses: a field it cannot rebuild
  from the ref's code and the page's facts raises `TransformError`.
- **At main every transform is the identity,** on all 28 frozen pages wherever it can run (main's
  code, freeze `bcda7ce3`). It refuses on five non-panel pages:
  - survival on FUBO, ORKA and TECX (no net leverage, so the line needs CIQ net debt, which the
    layer does not carry);
  - the peer question on NCNO and UBER (no comps export of their own on disk).
- **The CIQ root** is the primary checkout's `data/manual/ciq` (the Drive mirror), read only:
  - the panel's transcripts verify there by sha256;
  - every panel page's comps export there rebuilds its committed comps lines;
  - the assembler's copy (`mosaic-theory-ta`) holds stale LLY and SMPL comps exports, which the
    transforms refuse.
- **A harness bug found on the way:** the capture child loads `variants.py` by path, and a
  dataclass in it crashed every transformed capture. Fixed and pinned in `fc79a7be`.

**The $0 cross-check, before any registration** (main `e00db8cd` against #923 `e91490ae`, the
frozen panel). With no transform the two refs send IDENTICAL requests on all six pages. With the
five transforms every page differs, SYSTEM and the tool schema are equal, and only USER spans of
the facts move. The per-item character deltas against #923's own table:

| page | 1 shape | 2 note | 3 survival | 4 question | 5 print | total | #923's total |
|---|--:|--:|--:|--:|--:|--:|--:|
| BURL | +25 | −117 | 0 | +0 (discount → premium) | 0 | −92 | −92 (item 4 not measured) |
| CNXC | 0 | −117 | 0 | 0 | 0 | −117 | −117 |
| LLY | +25 | −117 | −18 | +0 (discount → premium) | 0 | −110 | −110 |
| MCK | +25 | −117 | 0 | −71 (question deleted: mixed gaps) | 0 | −163 | −92 (item 4 not measured) |
| ROST | +25 | −117 | 0 | +0 (discount → premium) | 0 | −92 | −92 |
| SMPL | +25 | −117 | 0 | 0 | 0 | −92 | −92 |

- Every item #923 measured matches item for item.
- **MCK and BURL item 4** are new. #923 could not measure them, because the exports on its disk
  were not those pages' own; here they rebuild the committed lines. That adds MCK's −71: the panel
  totals −666 here against −595 in #923's table.
- **The absolute prompt sizes do not reproduce #923's "before" column.** BURL is 437,144 USER
  characters with transcripts and 334,693 without, against #923's 369,053; LLY is 631,783 and
  508,312 against 509,444. The figures are the same at `bcda7ce3` and at `e00db8cd`, and adding
  SYSTEM does not reach them either. Not explained here. The deltas are what the cross-check
  compares, and they match.

## 2. What was registered, before any draw

- **Registration** `cceba9d939692bfcb5a2c78d27cad778d92e032e3d873b1d28e1fb668e5b975e`. It
  compares `e00db8cd` → `e91490ae` on the frozen panel v2 (BURL, CNXC, LLY, MCK, ROST, SMPL), with
  the five transforms in order, five draws per page per arm, target **M-LABEL**, alpha 0.05 and
  ship alpha **0.01**.
  - It pins the sha256 of all 12 requests as sent; the draw's re-capture matched every one.
  - Held out from the change: none. #923's record names every panel page.
- **The rule, as registered:**
  - p_lower ≤ 0.01 after Holm: ships;
  - 0.01 < p_lower ≤ 0.05: counts only if a FRESH, separately registered replication of the same
    design reaches p_lower ≤ 0.05;
  - above 0.05: does not ship;
  - in every case, no other class metric may worsen at p_upper ≤ 0.05, and every lean, proposal
    and committed-lean move is explained in writing.
- **The scorer:** the files at **`fc79a7be`**, fingerprint
  `e3c385cad1ec67a8ed863e9892a4f931096185a1943e2db9407f7a8cfa5c53e2`. `score` refuses any other.
- **The scorer counts the OLD labels** (coordinator, condition 1). The bleed family is fixed
  regex (`\bbleed\w*` plus a "gradual" clause test). The trailing-only family reads
  `mechanical.TRAILING_ONLY_NOTE`, which `test_sleeves` forbids retyping. It is the scorer's own
  import, never the code under test's, and it is pinned by sha256 (`cbf0eed9…`, the same text at
  main and at `e91490ae`): a changed constant stops the scorer loading.
- **The registration's own note,** in its sha: the target covers items 1–2 only; items 3–4 are
  read only through the no-worsening checks; item 5 is not exercised; the CIQ root is read only.
- **Inputs, by sha256** (in the registration's `inputs`), under the root
  `/Users/work/Documents/GitHub/mosaic-theory/data/manual/ciq`:

  | page | comps export | transcripts |
  |---|---|---|
  | BURL | `e302c4c0be914ba2…` | `55a8d412caa6…`, `14109f0b194b…` |
  | CNXC | `aa822ebf0da4c6e9…` | `44c3b9d51da0…`, `9b476b2b4ee6…` |
  | LLY | `ce7897dc0ba715c4…` | `aa50a6db99b4…`, `94373789d94d…` |
  | MCK | `158bc7e18c5163f9…` | `1dc52d3954c0…`, `e4ca4d9a3bd6…` |
  | ROST | `7171baefb59f7f06…` | `842c74e50068…`, `8db6aa9429a2…` |
  | SMPL | `647fa7075524cccb…` | `e8b109c0710b…`, `da5b14080652…` |

## 3. Spend, against the cap

| ledger | approved cap | spent | calls | per page |
|---|---:|---:|---:|---|
| `ledger-fix3a.jsonl` | $40.00 | **$30.7161** | 60 | BURL $5.1285, CNXC $4.5511, LLY $6.2341, MCK $4.9826, ROST $5.0420, SMPL $4.7778 |

Every call was served by `claude-opus-4-8`, stopped on `tool_use`, and made one HTTP attempt.
$9.2839 is unspent. A replication would have cost about $30 and would not have fitted; the first
run's result made one unnecessary.

## 4. The result, by the registered rule

| metric | BASE → CAND (units, 30 draws each) | p |
|---|---|---|
| **M-LABEL (target)** | **69 → 47** | **p_lower 0.0000754** |
| M-ABSENT | 60 → 48 | p_upper 0.951 |
| M-PATH | 7 → 4 | p_upper 0.911 |
| M-SIGN | 0 → 0 | — |
| M-ECHO (reported) | 54 → 60 | p_upper 0.274 |

- **The score's decision:** "ships once the moves listed are explained in writing" (§5 is that
  writing). It falls in the ship band, below 0.01, so the replication rule asks for nothing more.
- **Per page, M-LABEL units per draw:**

  | page | BASE | CAND |
  |---|---|---|
  | BURL | 2, 2, 3, 3, 2 | 0, 2, 1, 1, 1 |
  | CNXC | 3, 2, 3, 2, 2 | 1, 1, 1, 2, 2 |
  | LLY | 2, 1, 2, 2, 1 | 1, 2, 1, 1, 2 |
  | MCK | 2, 2, 3, 3, 3 | 3, 2, 3, 2, 2 |
  | ROST | 1, 1, 2, 2, 1 | 2, 2, 1, 1, 1 |
  | SMPL | 3, 3, 4, 3, 4 | 2, 1, 3, 1, 2 |

- **By family** (each unit counted once, under its first family): bleed 14 → 1; trailing-only
  37 → 13; no-adjusted-forward **12 → 27**; segment-undisclosed 5 → 5; runway-not-derivable 1 → 1.
- **The two labels #923 targets mostly leave the prose,** but not wholly, and not cleanly:
  - "Trailing only" survives in 13 units, even though the note is deleted on all six pages. The
    synthesis schema still asks a trailing multiple to carry "its forward or a 'trailing-only'
    blind-flag" (`synthesis.py`'s `bear_points` text). That is fix 4's prompt rule, which #923
    names as its dependency.
  - The rise in "no adjusted forward" (+15 units) looks like the same framing restated as the
    absence of a guided forward. It is still counted, inside the target, and the target still
    falls 22 units net.
- **What n cannot show here:**
  - which of items 1–2 moved which family beyond the counts above;
  - anything about items 3–5 (§6);
  - a per-page effect: the unit of the test is the draw, five per arm per page.

## 5. The two lean moves, explained in writing as the rule requires

- **MCK: mixed 4 / bullish 1 → bullish 4 / mixed 1. The proposal is withheld in both arms**, since
  neither is unanimous.
  - MCK's request lost items 1, 2 and 4 (its question was deleted: its six gaps are mixed).
  - Every draw in both arms names the same offset, a multiple at its own-history ceiling. The BASE
    "mixed" leans weigh that ceiling as decisive, and the CAND "bullish" leans weigh it as the one
    live offset.
  - On this page alone, four or more of five CAND draws committed has p_upper 0.103. This n cannot
    attribute the move to #923.
- **SMPL: mixed 3 / bearish 2 → bearish 4 / mixed 1. Proposal withheld in both arms.**
  - SMPL's request lost items 1 and 2.
  - Both arms cite the same facts (falling consumption, revenue and EBITDA; a re-cut guide; a
    strong balance sheet). One BASE "mixed" lean called the business "genuinely cheap"; no CAND
    lean does.
  - On this page, four or more bearish of five has p_upper 0.262. Not attributable.
- **The panel's committed-lean draws** moved 10 → 14 (two-sided p 0.29), in both directions: MCK
  +3, SMPL +2, BURL +1, ROST −2. That is not a panel shift at p ≤ 0.05.
- **No proposal moved anywhere:** LLY's BUY holds 5/5 in both arms; every other page is withheld
  in both.

## 6. What this measurement does not cover

- **Items 3–4 are read only through the no-worsening checks** (coordinator's ruling, option A).
  M-LABEL has no family for "(a risk)", "solvency risk" or "is the discount EARNED". Adding one
  after TEST was read once, knowing #923's change, would be in-sample (RUNBOOKS §n step 7). So
  whether the model stops repeating those two labels is not measured here. A separately
  calibrated metric for them needs fresh gold.
- **Item 5 is not exercised.** No panel page carries a drawdown guide, so its print row is the
  no-guide row at both refs. The three corpus pages it changes (BRBR, VITL, VRRM) are not on the
  panel.
- **The transforms cover the panel and the pages they can rebuild.** They refuse FUBO, ORKA, TECX
  (survival) and NCNO, UBER (the question), none of which is on the panel.

**BOUNDARY.**
- **Draws:** 60, `claude-opus-4-8`, 2026-11-07, between the ledger's opening (01:29 +05:30) and
  the score (03:05 +05:30). Five per page per arm; BASE then CAND, page by page.
- **Requests:** main `e00db8cd` and #923 `e91490ae`, each with the five `FIX_3A` transforms, all
  12 pinned in the registration. Pages: the frozen panel v2, freeze `bcda7ce3`.
- **Units:** prose units of `units.draw_units` with at least one hit, per draw. The family
  breakdown counts a unit once, under its first family.
- **Scorer:** the files at `fc79a7be`. p: the exact stratified permutation test over each page's
  ten draws.
- **Cross-check deltas:** USER characters, draws=1, at each ref with each transform alone, against
  the same ref with none. #923's table is its PR body's, 28 pages at main `bcda7ce3`.
- **Identity at main:** the 28 frozen pages at `bcda7ce3`, main's code.
- **Spend:** production's `cost_usd`, summed from the ledger.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $30.7161 of $40.
- **Accepted, with its falsifier: the "no adjusted forward" substitution.** The target improved
  net, while one family inside it rose. It is falsified as harmless if fix 4, which retires the
  prompt's trailing-only rule, is measured and the substitution does not fall with it.
