---
id: D8
status: recorded
date: 2026-07-31
prs: [282]
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
date-source: git (first commit containing this text)
---

**D8. THE PERIOD FIX HAS TWO CONSUMERS AND THE PR MEASURED ONE** (review finding on #282). Besides
the scenario engine, `anchor.py` computes `anchor_base_value_per_share = equity ÷ dil.value`, and
`tagger._leverage` + `audit_r1.check_leverage` read it — so correcting the period moves a value
**committed in `dossier.json`**. Measured before/after on the fleet: **SMPL 41.60→43.33 (+4.16%),
BRBR 55.41→55.97 (+1.02%), CNXC 62.33→62.55 (+0.35%)**; the other eight are unmoved (five have no
applicable anchor). FUBO's base is None but its anchor `diluted_shares` moves +2.22%. **The
committed values are the ones carrying the defect** — the fix does not corrupt them, it exposes
them — and until a backfill runs, committed JSON and a fresh recompute disagree on three names.
INVARIANT SHIPPED: a corpus pin asserts the divergence set is EXACTLY `{BRBR, CNXC, SMPL}`, so a
new name drifting in reds, and the backfill landing also reds until this record is updated.
**DONE 2026-07-31 — the backfill ran and `ANCHORS_AWAITING_BACKFILL` is now EMPTY**, so the pin has
flipped from "these three diverge" to "nothing diverges", and future drift reds on its first run.
Dry-run confirmed the recorded moves before writing. Three lines changed per `dossier.json`
(`computed_at`, `diluted_shares`, base VPS) and one per rendered page.

**IT RED ON ITS FIRST RUN, EXACTLY AS DESIGNED — BRBR, 2026-08-10 (PR #391).** A re-assembly
(`vinci dossier --ticker BRBR`) picked up a newer filing: diluted **117,500,000 → 116,600,000**,
base VPS **55.9721 → 57.6055 (+2.9%)**, and the point-in-time-vs-diluted gap **1.05% → 0.28%**.
Fewer shares, higher value per share — real inputs, not a regression, and the anchor here is
DECISION-PATH (it feeds the underwrite), so it is recorded rather than absorbed.
**`ANCHORS_AWAITING_BACKFILL` STAYS EMPTY.** Quarantining BRBR would have re-opened the escape
hatch this entry closed; the divergence was not a defective anchor but the committed
**companyfacts fixture going stale** against the re-assembled artifact — the anchor computed from
fresh EDGAR facts, the pin recomputing from the old fixture. Regenerating it (runbook step 5,
which the fixture's own error message requires "in the SAME PR that re-assembles the name")
restored agreement. The lesson is the one the fixture message already states and this build
skipped: **a re-assembly without its fixture regeneration produces a divergence that looks like a
broken anchor.** `test_propose`'s three share literals were re-struck in the same PR, as frozen
literals — deriving them from the artifact would put the oracle in the same place as the subject.
**TWO OTHER THINGS MOVED IN THE SAME RE-ASSEMBLY, recorded because a later reader diffing BRBR
before/after will meet them.** (a) The CIQ **comp set itself changed** — MDLZ and CPB out, NATR and
FitLife in — so every relative-value read (peer median leverage 2.8x → 2.4x) is against a
different, smaller-cap cohort. Not a defect and not our choice: it is the vendor's set in the
2026-08-09 re-pull, and the peer grid was verified cell-for-cell against the workbook by ticker
(BellRing 4.4x, consistent with the page's own 4.3x NET-debt caveat). (b) A whole
`capital_allocation` block APPEARED — 46 new paths — because BRBR's artifact predated that
extractor. Nothing was lost: the structural diff is zero paths dropped.
**A REVIEW NOTE ON HOW TO DIFF THESE.** The peer grid is a TICKER-KEYED list. Comparing two
vintages positionally reports false regressions the moment the vendor's set changes — this review
did exactly that and briefly "found" a leverage misalignment that did not exist. Join on ticker.
**GENERALISED 2026-08-10 (PR #399), because the narrow version did not hold.** The note above named
`peer_grid`, so the next review applied it there and walked straight into the same trap on
`peer_capital_intensity.rows` — reporting six fields "regressing to None" on rows[5] and rows[6]
when the eleven peers were UNCHANGED and merely REORDERED. **The rule is structural, not
per-block: any list of ENTITIES in a dossier is keyed by its entity, and a positional diff of two
vintages is meaningless.** Key on ticker/name and compare the intersection; a bare index diff
answers a question nobody asked. A guard written for one instance of a class stops the instance,
not the class — which is the same lesson as the mirror pins, arriving at the review layer.

**"NOTHING ELSE MOVES" DID NOT HOLD, and the failure is worth keeping.** Dry-running the other
eight flagged **FUBO and IT as CHANGED too** — but for reasons that are NOT this fix. Isolated by
recomputing each anchor under both tie-breaks with the workbook attached: FUBO's `net_debt`
(None → 170.4) and IT's `ltm_fcf` (None → 1257.9, plus its two `data_quality` fields) are
**PRE-EXISTING CIQ-bridge fills** that predate this work; only FUBO's `diluted_shares` (+2.22%) is
the period fix, and its base is None so no value moved. **The backfill is not surgical — it
rewrites the whole anchor block, carrying whatever else has drifted since the last run.** A
fleet-wide "while I'm here" backfill would have landed two unrelated vendor fills inside a PR
labelled for the period fix. Those two names keep their own pending decision.

**AND THE BACKFILL WRITES `dossier.json` ONLY** — it left the pages at `$41.60` while the record
said `43.3326`. Same hole `refresh_dossier` was built to close in #276, in a different writer. A
no-op refresh re-rendered all three pages before the frontend mirror ran. **Every writer that
touches a committed record needs the page checked, not just the one that was caught.**
