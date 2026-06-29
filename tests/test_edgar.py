"""Step 4 verification — the EDGAR client.

Unit tests use a synthetic ``companyfacts`` dict so the extraction and the non-distress math are
deterministic; network tests hit real SEC endpoints (companyfacts, efts full-text search,
submissions).
"""

from __future__ import annotations

from datetime import date

import pytest

from vinci.edgar import (
    EdgarClient,
    all_unknown_snapshot,
    compute_fundamental_snapshot,
    extract_points,
    latest_annual,
    latest_instant,
    parse_fts_hit,
    parse_fts_response,
)
from vinci.netcache import HttpError
from vinci.schemas.envelope import CoverageStatus

CROCS_CIK = "0001334036"


def _flow(tag: str, end: str, start: str, val: float, filed: str, form: str = "10-K") -> dict:
    return {"end": end, "start": start, "val": val, "filed": filed, "fp": "FY", "form": form}


def _instant(end: str, val: float, filed: str) -> dict:
    return {"end": end, "val": val, "filed": filed, "form": "10-K"}


SYNTHETIC_FACTS = {
    "facts": {
        "us-gaap": {
            # revenue: the modern tag is present; alias fallback must prefer it over "Revenues"
            "RevenueFromContractWithCustomerExcludingAssessedTax": {
                "units": {"USD": [_flow("rev", "2024-12-31", "2024-01-01", 1000.0, "2025-02-01")]}
            },
            "Revenues": {
                "units": {"USD": [_flow("rev", "2024-12-31", "2024-01-01", 999.0, "2025-02-01")]}
            },
            "OperatingIncomeLoss": {
                "units": {
                    "USD": [
                        _flow("op", "2023-12-31", "2023-01-01", 150.0, "2024-02-01"),
                        _flow("op", "2024-12-31", "2024-01-01", 200.0, "2025-02-01"),  # latest
                    ]
                }
            },
            "DepreciationDepletionAndAmortization": {
                "units": {"USD": [_flow("da", "2024-12-31", "2024-01-01", 50.0, "2025-02-01")]}
            },
            "NetCashProvidedByUsedInOperatingActivities": {
                "units": {"USD": [_flow("ocf", "2024-12-31", "2024-01-01", 180.0, "2025-02-01")]}
            },
            "PaymentsToAcquirePropertyPlantAndEquipment": {
                "units": {"USD": [_flow("capex", "2024-12-31", "2024-01-01", 60.0, "2025-02-01")]}
            },
            "EarningsPerShareDiluted": {
                "units": {
                    "USD/shares": [_flow("eps", "2024-12-31", "2024-01-01", 3.5, "2025-02-01")]
                }
            },
            "LongTermDebtNoncurrent": {
                "units": {"USD": [_instant("2024-12-31", 400.0, "2025-02-01")]}
            },
            "DebtCurrent": {"units": {"USD": [_instant("2024-12-31", 50.0, "2025-02-01")]}},
            "CashAndCashEquivalentsAtCarryingValue": {
                "units": {"USD": [_instant("2024-12-31", 150.0, "2025-02-01")]}
            },
        }
    }
}


# --- concept extraction -----------------------------------------------------------------------
def test_alias_priority_prefers_modern_revenue_tag() -> None:
    points = extract_points(SYNTHETIC_FACTS, "revenue")
    assert points and points[0].tag == "RevenueFromContractWithCustomerExcludingAssessedTax"
    assert latest_annual(points).value == pytest.approx(1000.0)


def test_alias_fallback_when_primary_absent() -> None:
    facts = {"facts": {"us-gaap": {"Revenues": SYNTHETIC_FACTS["facts"]["us-gaap"]["Revenues"]}}}
    points = extract_points(facts, "revenue")
    assert points and points[0].tag == "Revenues"


def test_latest_annual_picks_most_recent_period() -> None:
    op = latest_annual(extract_points(SYNTHETIC_FACTS, "operating_income"))
    assert op is not None
    assert op.period_end == date(2024, 12, 31)
    assert op.value == pytest.approx(200.0)


def test_shares_extracted_from_dei_namespace() -> None:
    # shares-outstanding lives in the dei taxonomy, not us-gaap — extract_points must search both
    facts = {
        "facts": {
            "dei": {
                "EntityCommonStockSharesOutstanding": {
                    "units": {
                        "shares": [{"end": "2026-03-31", "val": 1234.0, "filed": "2026-04-01"}]
                    }
                }
            }
        }
    }
    pts = extract_points(facts, "shares")
    assert pts and pts[0].tag == "EntityCommonStockSharesOutstanding"
    assert latest_instant(pts).value == pytest.approx(1234.0)


def test_latest_instant_balance_sheet() -> None:
    cash = latest_instant(extract_points(SYNTHETIC_FACTS, "cash"))
    assert cash is not None and cash.is_instant and cash.value == pytest.approx(150.0)


# --- non-distress snapshot math ---------------------------------------------------------------
def test_compute_fundamental_snapshot() -> None:
    snap = compute_fundamental_snapshot("0001334036", SYNTHETIC_FACTS)
    assert snap.op_income_sign.value == 1  # operating income > 0
    assert snap.fcf_sign.value == 1  # OCF(180) - capex(60) = 120 > 0
    # EBITDA = op(200) + D&A(50) = 250; net debt = (400+50) - cash(150) = 300; leverage = 300/250
    assert snap.ebitda_annual.value == pytest.approx(250.0)
    assert snap.net_debt.value == pytest.approx(300.0)
    assert snap.net_leverage.value == pytest.approx(1.2)
    assert snap.net_debt_to_ocf.value == pytest.approx(300.0 / 180.0)  # net debt 300 / OCF 180
    assert snap.eps_diluted_annual.value == pytest.approx(3.5)
    assert snap.as_of == date(2025, 2, 1)


def test_leverage_unknown_when_ebitda_nonpositive() -> None:
    facts = {
        "facts": {
            "us-gaap": {
                "OperatingIncomeLoss": {
                    "units": {
                        "USD": [_flow("op", "2024-12-31", "2024-01-01", -100.0, "2025-02-01")]
                    }
                },
                "DepreciationDepletionAndAmortization": {
                    "units": {"USD": [_flow("da", "2024-12-31", "2024-01-01", 20.0, "2025-02-01")]}
                },
                "LongTermDebtNoncurrent": {
                    "units": {"USD": [_instant("2024-12-31", 400.0, "2025-02-01")]}
                },
                "CashAndCashEquivalentsAtCarryingValue": {
                    "units": {"USD": [_instant("2024-12-31", 50.0, "2025-02-01")]}
                },
            }
        }
    }
    snap = compute_fundamental_snapshot("x", facts)
    assert snap.op_income_sign.value == -1  # loss-making → negative sign (a distress tell)
    assert snap.net_leverage.coverage_status is CoverageStatus.UNKNOWN  # EBITDA<=0 → meaningless
    assert "EBITDA<=0" in (snap.net_leverage.note or "")  # the note names the real cause


def test_net_debt_undercaptured_fails_loud() -> None:
    """The MVST case: debt booked under ShortTermBorrowings / convertible tags the long-term+current
    extraction never reads. A single such instrument exceeding the extracted total means the
    extraction missed debt → net-debt fails loud, never a confident false net-cash of 13 - 126."""
    facts = {
        "facts": {
            "us-gaap": {
                "LongTermDebt": {"units": {"USD": [_instant("2026-03-31", 13.2e6, "2026-05-04")]}},
                "ShortTermBorrowings": {
                    "units": {"USD": [_instant("2026-03-31", 111.2e6, "2026-05-04")]}
                },
                "ConvertibleDebtCurrent": {
                    "units": {"USD": [_instant("2026-03-31", 76.5e6, "2026-05-04")]}
                },
                "CashAndCashEquivalentsAtCarryingValue": {
                    "units": {"USD": [_instant("2026-03-31", 126.1e6, "2026-05-04")]}
                },
            }
        }
    }
    snap = compute_fundamental_snapshot("x", facts)
    assert not snap.net_debt.is_known  # NOT a false net-cash of 13.2 - 126.1 = -112.9M
    assert "under-captured" in (snap.net_debt.note or "")
    assert "ShortTermBorrowings" in (snap.net_debt.note or "")  # names the largest witness
    # net-leverage and net-debt/OCF share the numerator → they inherit UNKNOWN, not a false value
    assert not snap.net_leverage.is_known and not snap.net_debt_to_ocf.is_known


def test_net_debt_witness_within_extracted_still_computes() -> None:
    """The guard fires ONLY on genuine under-capture: a debt witness that does NOT exceed the
    long-term+current extraction (the clean common case) leaves net-debt computed as usual."""
    facts = {
        "facts": {
            "us-gaap": {
                "LongTermDebtNoncurrent": {
                    "units": {"USD": [_instant("2024-12-31", 400e6, "2025-02-01")]}
                },
                "DebtCurrent": {"units": {"USD": [_instant("2024-12-31", 50e6, "2025-02-01")]}},
                "ShortTermBorrowings": {  # present but well within the 450 extracted → no fire
                    "units": {"USD": [_instant("2024-12-31", 100e6, "2025-02-01")]}
                },
                "CashAndCashEquivalentsAtCarryingValue": {
                    "units": {"USD": [_instant("2024-12-31", 150e6, "2025-02-01")]}
                },
            }
        }
    }
    snap = compute_fundamental_snapshot("x", facts)
    assert snap.net_debt.is_known and snap.net_debt.value == pytest.approx(300e6)  # 450 - 150


def test_net_debt_guard_ignores_stale_repaid_witness() -> None:
    """Period alignment: an instrument tagged only in an OLD period (since repaid, its last value
    persists at the stale date) must NOT over-fire the guard against a current, fully-captured
    extraction — only witnesses at/after the captured-debt period count."""
    facts = {
        "facts": {
            "us-gaap": {
                "LongTermDebtNoncurrent": {
                    "units": {"USD": [_instant("2026-03-31", 50e6, "2026-05-04")]}
                },
                "ConvertibleDebtNoncurrent": {  # big convertible last tagged 2023, since repaid
                    "units": {"USD": [_instant("2023-12-31", 500e6, "2024-02-01")]}
                },
                "CashAndCashEquivalentsAtCarryingValue": {
                    "units": {"USD": [_instant("2026-03-31", 30e6, "2026-05-04")]}
                },
            }
        }
    }
    snap = compute_fundamental_snapshot("x", facts)
    # the stale 2023 convertible (older than the 2026 extraction) is excluded → net-debt computes
    assert snap.net_debt.is_known and snap.net_debt.value == pytest.approx(20e6)  # 50 - 30


def test_net_debt_guard_fires_when_all_debt_is_witness_only() -> None:
    """A filer with ALL debt under witness tags (no LongTermDebt/current) still fails loud
    'under-captured' — not the misleading 'no debt/cash' that reads as debt-free."""
    facts = {
        "facts": {
            "us-gaap": {
                "ShortTermBorrowings": {
                    "units": {"USD": [_instant("2026-03-31", 200e6, "2026-05-04")]}
                },
                "CashAndCashEquivalentsAtCarryingValue": {
                    "units": {"USD": [_instant("2026-03-31", 50e6, "2026-05-04")]}
                },
            }
        }
    }
    snap = compute_fundamental_snapshot("x", facts)
    assert not snap.net_debt.is_known and "under-captured" in (snap.net_debt.note or "")


def test_leverage_unknown_note_names_missing_debt_not_negative_ebitda() -> None:
    """The net-leverage UNKNOWN note names the SPECIFIC missing input. A positive-EBITDA name
    with no debt/cash line reads 'no net-debt …', NOT the misleading 'EBITDA<=0 …' (the MVST
    case — its EBITDA is clearly positive, the gap is just that EDGAR has no debt/cash line)."""
    facts = {
        "facts": {
            "us-gaap": {
                "OperatingIncomeLoss": {
                    "units": {"USD": [_flow("op", "2024-12-31", "2024-01-01", 200.0, "2025-02-01")]}
                },
                "DepreciationDepletionAndAmortization": {
                    "units": {"USD": [_flow("da", "2024-12-31", "2024-01-01", 50.0, "2025-02-01")]}
                },
                # no debt/cash lines → net-debt unavailable; EBITDA = 250 > 0
            }
        }
    }
    snap = compute_fundamental_snapshot("x", facts)
    assert snap.ebitda_annual.value == pytest.approx(250.0)  # EBITDA clearly positive
    assert snap.net_leverage.coverage_status is CoverageStatus.UNKNOWN
    note = snap.net_leverage.note or ""
    assert "debt/cash not in XBRL" in note and "EBITDA<=0" not in note  # names the gap


def test_net_debt_to_ocf_resolves_when_ebitda_is_untaggable() -> None:
    """The MVST case: operating income IS tagged but NO D&A concept is, so GAAP net-debt/EBITDA is
    UNKNOWN ('no EBITDA in XBRL') — never fabricated from partial D&A scraps. Yet net-debt/OCF
    RESOLVES, because OCF is reliably tagged and already carries the D&A add-back EBITDA needs."""
    facts = {
        "facts": {
            "us-gaap": {
                "OperatingIncomeLoss": {
                    "units": {"USD": [_flow("op", "2024-12-31", "2024-01-01", 7.0, "2025-02-01")]}
                },
                # NO Depreciation/Amortization concept at all — the MVST gap that breaks EBITDA
                "NetCashProvidedByUsedInOperatingActivities": {
                    "units": {
                        "USD": [_flow("ocf", "2024-12-31", "2024-01-01", 120.0, "2025-02-01")]
                    }
                },
                "LongTermDebtNoncurrent": {
                    "units": {"USD": [_instant("2024-12-31", 250.0, "2025-02-01")]}
                },
                "CashAndCashEquivalentsAtCarryingValue": {
                    "units": {"USD": [_instant("2024-12-31", 70.0, "2025-02-01")]}
                },
            }
        }
    }
    snap = compute_fundamental_snapshot("x", facts)
    # GAAP net-debt/EBITDA correctly UNKNOWN — D&A untaggable, the ratio is not fabricated
    assert snap.net_leverage.coverage_status is CoverageStatus.UNKNOWN
    assert "no EBITDA in XBRL" in (snap.net_leverage.note or "")
    # ...but net-debt/OCF resolves: net debt (250 - 70 = 180) / OCF (120) = 1.5
    assert snap.net_debt_to_ocf.value == pytest.approx(180.0 / 120.0)


def test_all_unknown_snapshot_is_graceful() -> None:
    snap = all_unknown_snapshot("0000000000")
    assert snap.op_income_sign.coverage_status is CoverageStatus.UNKNOWN
    assert snap.net_leverage.value is None  # never a silent 0


# --- efts hit parsing -------------------------------------------------------------------------
def test_parse_fts_hit() -> None:
    # real efts shape: plural ciks/root_forms, adsh accession; root_forms is canonical even for /A
    hit = parse_fts_hit(
        {
            "_id": "0001193125-24-000123:d12345.htm",
            "_source": {
                "adsh": "0001193125-24-000123",
                "ciks": ["0000320193"],
                "root_forms": ["8-K"],
                "file_type": "8-K/A",
                "file_date": "2024-08-01",
                "display_names": ["APPLE INC (AAPL)"],
            },
        }
    )
    assert hit.accession == "0001193125-24-000123"
    assert hit.cik == "0000320193"
    assert hit.form == "8-K"  # canonical root form, not the "8-K/A" file_type
    assert hit.file_date == date(2024, 8, 1)


def test_parse_fts_response_fails_loud_on_error() -> None:
    # efts throttle/error responses lack a 'hits' structure → must raise, not return []
    with pytest.raises(HttpError):
        parse_fts_response({"message": "rate limited"})
    # a valid empty result is fine (0 hits is a real answer, not an error)
    assert parse_fts_response({"hits": {"total": {"value": 0}, "hits": []}}) == []


# --- network: real EDGAR ----------------------------------------------------------------------
@pytest.mark.network
def test_fundamental_snapshot_real_company() -> None:
    client = EdgarClient.from_config()
    snap = client.fundamental_snapshot(CROCS_CIK)
    # Crocs is profitable and cash-generative → signs present and positive
    assert snap.op_income_sign.coverage_status is CoverageStatus.PRESENT
    assert snap.op_income_sign.value == 1
    assert snap.fcf_sign.value == 1
    assert snap.ebitda_annual.coverage_status is CoverageStatus.PRESENT
    assert snap.ebitda_annual.value and snap.ebitda_annual.value > 0


@pytest.mark.network
def test_fulltext_search_finds_guidance_8ks() -> None:
    client = EdgarClient.from_config()
    # exact-phrase search over all dates — reliably non-empty; a single (paced, cached) efts call
    hits = client.fulltext_search("lowered guidance", forms="8-K")
    assert len(hits) > 0
    assert all(h.accession for h in hits)
    assert all(h.form == "8-K" for h in hits if h.form)


@pytest.mark.network
def test_recent_8k_filings_real_company() -> None:
    client = EdgarClient.from_config()
    filings = client.recent_filings(CROCS_CIK, forms=("8-K",), since=date(2023, 1, 1))
    assert len(filings) > 0
    assert all(f.form == "8-K" for f in filings)


@pytest.mark.network
def test_non_xbrl_cik_degrades_to_unknown() -> None:
    client = EdgarClient.from_config()
    # a CIK with no companyfacts → all UNKNOWN, never a crash
    snap = client.fundamental_snapshot(1)
    assert snap.op_income_sign.coverage_status is CoverageStatus.UNKNOWN
