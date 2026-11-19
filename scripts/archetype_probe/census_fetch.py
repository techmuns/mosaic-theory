"""Step 3 inputs, fetched once through the repo's SEC client (cache in the scratchpad):
(1) every universe CIK's submissions document → a compact extract; (2) SEC XBRL frames for the
statement-form and economic-model signals. Resumable: re-running skips what is already extracted."""

from __future__ import annotations

import datetime as dt
import json
import sys
import time

from probe_common import OUT, sec_http, universe_rows

SUB = "https://data.sec.gov/submissions/CIK{cik}.json"
TODAY = dt.date(2026, 11, 19)
ANNUAL = ("10-K", "10-K405", "10-KT", "20-F", "40-F")
TRANSITION = ("10-KT", "10-QT", "20-FT")


def extract(cik: str, doc: dict) -> dict:
    rec = (doc.get("filings") or {}).get("recent") or {}
    forms = rec.get("form") or []
    dates = rec.get("filingDate") or []
    items = rec.get("items") or [""] * len(forms)
    rows = [
        (f, dt.date.fromisoformat(d), it or "")
        for f, d, it in zip(forms, dates, items, strict=False)
    ]

    def since(days: int) -> dt.date:
        return TODAY - dt.timedelta(days=days)

    annual = [(f, d) for f, d, _ in rows if f in ANNUAL]
    latest_annual = max(annual, key=lambda x: x[1]) if annual else None
    files = (doc.get("filings") or {}).get("files") or []
    oldest = min(
        [d for _, d, _ in rows]
        + [dt.date.fromisoformat(x["filingFrom"]) for x in files if x.get("filingFrom")],
        default=None,
    )
    biz = (doc.get("addresses") or {}).get("business") or {}
    return {
        "cik": cik,
        "name": doc.get("name"),
        "sic": doc.get("sic"),
        "sic_desc": doc.get("sicDescription"),
        "entity_type": doc.get("entityType"),
        "category": doc.get("category"),
        "fye": doc.get("fiscalYearEnd"),
        "inc": doc.get("stateOfIncorporation"),
        "inc_desc": doc.get("stateOfIncorporationDescription"),
        "biz_country": biz.get("stateOrCountry"),
        "biz_foreign": biz.get("isForeignLocation"),
        "tickers": doc.get("tickers"),
        "exchanges": doc.get("exchanges"),
        "latest_annual": [latest_annual[0], latest_annual[1].isoformat()]
        if latest_annual
        else None,
        "annual_forms_3y": sorted({f for f, d in annual if d >= since(3 * 365)}),
        "transition_3y": sorted({f for f, d, _ in rows if f in TRANSITION and d >= since(3 * 365)}),
        "n_10q_365": sum(1 for f, d, _ in rows if f in ("10-Q", "10-QT") and d >= since(365)),
        "n_6k_180": sum(1 for f, d, _ in rows if f == "6-K" and d >= since(180)),
        "n_6k_365": sum(1 for f, d, _ in rows if f == "6-K" and d >= since(365)),
        "n_8k202_365": sum(
            1 for f, d, it in rows if f.startswith("8-K") and "2.02" in it and d >= since(365)
        ),
        "n_8k201_730": sum(
            1 for f, d, it in rows if f.startswith("8-K") and "2.01" in it and d >= since(730)
        ),
        "spin_reg": sorted(
            {
                f"{f} {d.isoformat()}"
                for f, d, _ in rows
                if f.startswith("10-12B") or f.startswith("10-12G")
            }
        ),
        "ipo_3y": sorted(
            {f for f, d, _ in rows if f in ("S-1", "F-1", "424B4") and d >= since(3 * 365)}
        ),
        "oldest_filing": oldest.isoformat() if oldest else None,
        "recent_page_rows": len(rows),
    }


FRAMES = [
    # (namespace, concept, unit, period) — CY2025 annual duration / CY2025Q4I instant, CY2024 too
    *[
        ("us-gaap", c, "USD", p)
        for p in ("CY2025", "CY2024")
        for c in (
            "Revenues",
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "RevenueFromContractWithCustomerIncludingAssessedTax",
            "SalesRevenueNet",
            "OperatingIncomeLoss",
            "NetIncomeLoss",
            "InterestAndDividendIncomeOperating",
            "InterestIncomeExpenseNet",
            "PremiumsEarnedNet",
            "PolicyholderBenefitsAndClaimsIncurredNet",
            "ShareBasedCompensation",
            "AllocatedShareBasedCompensationExpense",
            "PaymentsToAcquirePropertyPlantAndEquipment",
            "ResearchAndDevelopmentExpense",
            "DepreciationDepletionAndAmortization",
            "DepreciationAndAmortization",
            "DepreciationAmortizationAndAccretionNet",
            "OperatingLeaseCost",
            "RegulatedOperatingRevenue",
            "RoyaltyRevenue",
            "OperatingLeasesIncomeStatementLeaseRevenue",
        )
    ],
    *[
        ("us-gaap", c, "USD", "CY2025Q4I")
        for c in (
            "Assets",
            "Deposits",
            "LoansAndLeasesReceivableNetReportedAmount",
            "RealEstateInvestmentPropertyNet",
            "StockholdersEquity",
            "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
            "OperatingLeaseLiability",
            "ContractWithCustomerLiability",
            "ContractWithCustomerLiabilityCurrent",
            "RevenueRemainingPerformanceObligation",
            "LiabilityForFuturePolicyBenefits",
            "LiabilityForClaimsAndClaimsAdjustmentExpense",
            "PublicUtilitiesPropertyPlantAndEquipmentNet",
            "RegulatoryAssetsNoncurrent",
            "PartnersCapital",
            "LimitedPartnersCapitalAccount",
            "MembersEquity",
            "LongTermDebt",
            "LongTermDebtNoncurrent",
        )
    ],
]


def main() -> None:
    http = sec_http()
    ciks = sorted({r["cik"] for r in universe_rows()})
    path = OUT / "subs_extract.jsonl"
    done = set()
    if path.exists():
        done = {json.loads(line)["cik"] for line in path.read_text().splitlines() if line.strip()}
    failures = []
    t0 = time.time()
    with path.open("a") as fh:
        for n, cik in enumerate(c for c in ciks if c not in done):
            try:
                doc = http.get_json(SUB.format(cik=cik), ttl_seconds=7 * 86400)
                fh.write(json.dumps(extract(cik, doc)) + "\n")
            except Exception as exc:  # noqa: BLE001 — recorded, never guessed
                failures.append({"cik": cik, "error": f"{type(exc).__name__}: {exc}"[:300]})
            if n % 200 == 0:
                print(f"submissions {n} ({time.time() - t0:.0f}s)", flush=True)
    (OUT / "subs_failures.json").write_text(json.dumps(failures, indent=1))
    print("submissions failures:", len(failures), flush=True)
    fdir = OUT / "frames"
    fdir.mkdir(exist_ok=True)
    for ns, concept, unit, period in FRAMES:
        dest = fdir / f"{ns}__{concept}__{unit}__{period}.json"
        if dest.exists():
            continue
        url = f"https://data.sec.gov/api/xbrl/frames/{ns}/{concept}/{unit}/{period}.json"
        try:
            data = http.get_json(url, ttl_seconds=7 * 86400)
            out = {
                str(r["cik"]).zfill(10): r["val"]
                for r in data.get("data", [])
                if r.get("val") is not None
            }
            dest.write_text(json.dumps(out))
            print("frame", concept, period, len(out), flush=True)
        except Exception as exc:  # noqa: BLE001
            dest.with_suffix(".err").write_text(f"{type(exc).__name__}: {exc}"[:300])
            print("frame FAILED", concept, period, type(exc).__name__, flush=True)


if __name__ == "__main__":
    sys.exit(main())
