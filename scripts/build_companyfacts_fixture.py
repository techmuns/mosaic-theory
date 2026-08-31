"""Freeze the companyfacts SUBSET the corpus pins read, so they gate in CI.

WHY THIS EXISTS. `data/cache` is git-ignored, so on any fresh checkout — including every CI run —
the three corpus pins in `tests/test_dilution_denominator.py` find a cold cache and skip. They have
never gated since the day they were written (STATE D17). Committing the data they need removes the
cache dependency entirely, which is the pattern `test_anchor` and `test_band_guards` already use.

SUBSET BY CONCEPT, NOT BY BLOB. A full companyfacts response is megabytes of tags nobody reads;
eleven of them would be a large permanent addition for a handful of facts. :data:`FIXTURE_TAGS` is
DERIVED — it was captured by instrumenting `points_for_tag`/`extract_points` over a real run of all
three pins across the whole fleet, not by reading the code and listing what looked relevant.

VERSIONED WITH THE ARTIFACTS. The pins check committed artifacts against a fresh recompute, so a
fixture frozen at one vintage will disagree with a dossier later re-assembled from newer EDGAR data
— for a reason that has nothing to do with the code. **Re-run this script in the SAME PR that
re-assembles a name**, exactly as `ANCHORS_AWAITING_BACKFILL` is shrunk in the PR that backfills:
the fixture TRACKS the artifacts rather than describing them.

    python scripts/build_companyfacts_fixture.py            # all committed dossier names
    python scripts/build_companyfacts_fixture.py SMPL BRBR  # just these

Needs a warm cache or network; it is an operator tool, never imported by the suite.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "companyfacts"

#: The tags the three corpus pins actually read, DERIVED by instrumenting a real run rather than
#: transcribed from the code. Anything outside this set is dropped, which is what keeps the fixture
#: small; anything a pin later needs must be added here AND the fixture regenerated, or that pin
#: reads an absent tag and reports UNKNOWN instead of failing loudly.
FIXTURE_TAGS: frozenset[str] = frozenset({
    # share counts — the denominator work
    "EntityCommonStockSharesOutstanding",
    "CommonStockSharesOutstanding",
    "CommonStockSharesIssued",
    "WeightedAverageNumberOfSharesOutstandingBasic",
    "WeightedAverageNumberOfDilutedSharesOutstanding",
    # per-share earnings — the share-basis-change detector compares ONE fiscal period as reported
    # by TWO different filings, so this tag must arrive with its restatement history intact rather
    # than one value per period (NFLX FY2023: 12.03 filed 2024-01-26, 1.20 filed 2026-01-23)
    "EarningsPerShareDiluted",
    # revenue — the anchor's margin history, all four tags in the preference order
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "RevenueFromContractWithCustomerIncludingAssessedTax",
    "Revenues",
    "SalesRevenueNet",
    # operating income + D&A
    "OperatingIncomeLoss",
    # (PR-4) PRE-TAX income — the OTHER leg of `pretax − operating`, which IS the non-operating
    # block. Both legs must be in the fixture or `_nonoperating_earnings` reports UNKNOWN offline
    # and its pins check nothing.
    "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
    "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterest"
    "AndIncomeLossFromEquityMethodInvestments",
    "DepreciationDepletionAndAmortization",
    "DepreciationAmortizationAndAccretionNet",
    "DepreciationAndAmortization",
    "Depreciation",
    "AmortizationOfIntangibleAssets",
    # net debt: debt, cash, leases
    "LongTermDebtNoncurrent",
    "LongTermDebt",
    "LongTermDebtCurrent",
    "DebtCurrent",
    "CashAndCashEquivalentsAtCarryingValue",
    "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
    "FinanceLeaseLiabilityCurrent",
    "FinanceLeaseLiabilityNoncurrent",
    "OperatingLeaseLiabilityCurrent",
    "OperatingLeaseLiabilityNoncurrent",
    "ConvertibleDebtNoncurrent",
    "ConvertibleDebtCurrent",
    "ConvertibleNotesPayable",
    "ConvertibleNotesPayableCurrent",
    "SeniorNotes",
    "NotesPayable",
    # free cash flow
    "NetCashProvidedByUsedInOperatingActivities",
    "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
    "PaymentsToAcquirePropertyPlantAndEquipment",
    "PaymentsToAcquireProductiveAssets",
})


def subset(facts: dict[str, Any]) -> dict[str, Any]:
    """Keep only :data:`FIXTURE_TAGS`, preserving the exact companyfacts shape callers expect."""
    out: dict[str, dict[str, Any]] = {}
    for ns, node in (facts.get("facts") or {}).items():
        kept = {tag: body for tag, body in node.items() if tag in FIXTURE_TAGS}
        if kept:
            out[ns] = kept
    return {"cik": facts.get("cik"), "entityName": facts.get("entityName"), "facts": out}


def main(argv: list[str]) -> int:
    sys.path.insert(0, str(ROOT))
    from vinci.config import get_config
    from vinci.edgar.client import EdgarClient
    from vinci.resolver import EntityResolver

    cfg = get_config()
    resolver, edgar = EntityResolver.from_config(cfg), EdgarClient.from_config(cfg)
    # BOTH corpora, because the pins read both: the overlay/anchor pins walk committed DOSSIERS,
    # and the record-period pin walks SCENARIO RECORDS — and the two sets are not equal. WERN has a
    # record and no dossier, and it was the name that caught this.
    dossiers = {p.name for p in (cfg.data_dir / "dossiers").iterdir()
                if p.is_dir() and (p / "dossier.json").is_file()}
    records = {p.stem for p in (ROOT / "scenarios").glob("*.json")
               if not p.stem.startswith("_")}
    names = [t.upper() for t in argv] or sorted(dossiers | records)
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    total = 0
    for ticker in names:
        facts = edgar.companyfacts(resolver.resolve_ticker(ticker).cik)
        thin = subset(facts)
        path = FIXTURE_DIR / f"{ticker}.json"
        # sort_keys so a regeneration produces a byte-identical file when nothing moved — a
        # fixture that churns on every run cannot be reviewed for what actually changed
        path.write_text(json.dumps(thin, indent=1, sort_keys=True) + "\n")
        kb = path.stat().st_size / 1024
        total += kb
        kept = sum(len(v) for v in thin["facts"].values())
        print(f"  {ticker:6} {kept:>3} tags  {kb:>7.1f} KB")
    print(f"\n=== {len(names)} name(s) · {total / 1024:.2f} MB total → {FIXTURE_DIR} ===")
    return 0


if __name__ == "__main__":
    # Run from the repo root: ~28 data roots resolve against the CWD (see the note in
    # build_cohort_pool.py). In __main__ only, so importing this module cannot chdir the suite.
    os.chdir(ROOT)
    raise SystemExit(main(sys.argv[1:]))
