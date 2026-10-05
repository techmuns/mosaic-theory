---
id: 2026-10-05-amzn-onto-the-caching-build
status: shipped
date: 2026-10-05
prs: [666]
supersedes:
superseded-by:
---

# AMZN onto fresh estimates and the caching build — the normalized row starts stripping the gain

**WHAT.** AMZN re-assembled on `2c770098` (#665's caching build) after the operator uploaded three
CIQ files on 2026-10-05: a new **Estimates Report**, a new **Public Company Profile** (tearsheet),
and a **standalone Credit Health Panel** the folder never had. The other 8 files were
byte-identical to what the repo held; the old folder is backed up outside the repo. Artifacts only.

**WHAT MOVED** (against AMZN's #663 page, same 2026-09-22 close):

    consensus floor     >=2026-09-02  ->  >=2026-10-01
    lean                strongly-bullish (5/5, unanimous)  ->  mixed (3 mixed / 2 strongly-bullish)
    machine proposal    SEALED  ->  WITHHELD (draws disagree)
    P/FY26E (normalized)  19.8x (EPS $12.87)  ->  30.7x (EPS $8.31)
    P/FY26E (GAAP)        19.8x (EPS $12.88)  ->  19.8x (EPS $12.88)
    P/FY27E (norm / GAAP) 24.6x / 24.4x       ->  24.4x / 24.3x
    caveats / qa        7/5  ->  7/6

## The normalized row now strips the gain — and that answers #663's open oddity

#663 recorded, unresolved, that AMZN's FY26E consensus **net income $140,097M exceeds its FY26E EBIT
$109,863M** with no gain modelled. The new export keeps that GAAP line ($140,133M vs $109,867M) but
its **normalized FY26E EPS falls from $12.87 to $8.31** while GAAP stays $12.88. The gap is a
non-operating gain in the GAAP consensus that the normalized consensus now excludes; FY27E carries
none, so the two agree there ($10.47 vs $10.51). AMZN's normalized path is now FY26E $8.31 →
FY27E $10.47, rising — the inversion #663 flagged is gone.

**This FALSIFIES one of the two options §5.0 row 32 (1) put to the operator.** That item offered to
drop the normalized estimate rows as "≤6% duplicates of GAAP" — measured across 13 estimate columns
on 2026-09-30. On AMZN's new export FY26E normalized is **0.65× GAAP**, and the normalized row is the
one carrying the economically clean number. Dropping it would leave the page showing only 19.8x on
gain-inflated earnings. Row 32 (1) is restated accordingly; naming the basis is the option that
survives.

**The synthesis moved with the data, not only with the draws.** Its lean now reads *"a forward-basis
premium once non-operating gains are stripped"*, and two bear points argue it: the trailing 19.8x is
"flattered by non-operating gains" (Q2-26 alone +$53,396M, 66% of pre-tax), and on a normalized
forward basis the name is a premium to peers. One run cannot separate the input change from draw
variance, but the reasoning it kept is about the input that changed.

## The prompt cache, second real run — and the largest prompt in the fleet

    draw  started   gap  input    write     read  output
     1      0.0s           24  213,096        0   4,018
     2     55.8s    56s    24        0  213,096   4,195
     3    111.5s    56s    24        0  213,096   3,972
     4    164.1s    53s    24        0  213,096   3,817
     5    214.9s    51s    24        0  213,096   4,429

One prompt size (213,120), gaps 51–56s against a 300s lifetime, no miss. **Synthesis ~$2.27 against
~$5.84 uncached — 61.1% saved**, at the top of #664's projected 55–61% range, on the fleet's
largest prompt.

## Credit health — one correction, one gap, one disagreement

**CORRECTION: AMZN's credit health was never missing.** §5.0 row 32 (6) and
`docs/records/2026-10-05-pending-after-the-forward-multiples.md` item 6 said AMZN lacked the Credit
Health Panel and that its credit fields read UNKNOWN. Both were inferred from a FILE COUNT (10 files
against 11 elsewhere) and never checked against the data: AMZN's credit health has always been
`present`, read from the **"Credit Health Panel" sheet inside the Comparable Analysis workbook**. The
item is removed from row 32; that record's body is immutable and this one carries the reversal.

**THE STANDALONE FILE IS SILENTLY DROPPED — fleet-wide.** `CiqBundle.from_files` classifies files by
name keyword, and `_WORKBOOK_KEYWORDS` has none for "credit health", so a standalone
`… Credit Health Panel.xls` is skipped without a word — the failure the `charting` entry's comment
already names. Measured over the 26 CIQ folders: **10 carry a standalone file, and none of them is
read.** It is a different, richer export (Summary, Financials, Liquidity/Solvency/Operational metric
charts) than the comps sheet.

**AND THE TWO DISAGREE ON AMZN, in a way this repo cannot adjudicate:**

    comps sheet  (as-of 2026-09-17)  Overall 2 · Operational 3 · Solvency 2 · Liquidity 4
                 scale 1=strongest … 4=weakest, direction VERIFIED from the data (IG peers ≤ sub-IG)
    standalone   (uploaded 2026-10-05)  Overall Top · Operational Top · Solvency Top · Liquidity Above Average

Read on the verified scale, the page calls liquidity AMZN's WEAKEST dimension; the newer panel calls
it above average. The likeliest reading is two different reference populations — a relative score
within the comp set against CIQ's own relative score — eighteen days apart. Nothing here says which
the reader should trust, so the page keeps the comps reading, unchanged, and the question goes to
§5.0 row 32 as an operator call: read the standalone at all, and if so, which wins.

**HOW VERIFIED.** `dossier --ticker AMZN`, exit 0, `1 done · 0 error(s)`, 18:13–18:22 IST.
ruff clean · `mypy --strict vinci` clean · `pytest -m "not network"` exit 0 on the
freshly-committed artifacts. The FY26E rows are re-derived through `financial_summary_annual` from
both the backed-up and the new CIQ folder, not read off the page.

**BOUNDARY.** One name, AMZN, 2026-10-05, `claude-opus-4-8`. Five files
(`data/dossiers/AMZN/dossier.{json,md}`, `frontend/dossiers/AMZN.{json,md}`,
`frontend/dossiers/index.json`). **Every multiple is struck on the 2026-09-22 close, 13 days stale
at build** (`PRICE STALE AT ASSEMBLY`); a `vinci refresh` would move all of them, and was not run —
it is row 32 (3), the operator's call. The 0.65× is AMZN FY26E on the 2026-10-05 export only; the
other six names' estimate columns are as #663 measured them.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **AMZN's machine proposal is withheld** where #663's page had it sealed. The draws disagree; that
  is the gate working, and the inputs did change.
- **The operator's credit upload changed nothing on the page.** Stated plainly so it is not
  mistaken for an update that took.
- **The synthesis prose is fully rewritten**, as every full assembly does.
- **Not CI-validated** — the `gate` workflow has failed on Actions billing since #652.
