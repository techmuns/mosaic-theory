"""STATE row 35 — THE INSIDER LINE READS ONLY THIS ISSUER'S INSIDERS, ONLY TO ITS DATE, AND SAYS SO
WHEN IT CANNOT READ THEM.

THE DEFECTS, each observed on a committed page (measured 2026-10-28):
1. A Form 4 a company files as a HOLDER of another issuer entered its own line. EDGAR files a Form
   4 under both its issuer's and its reporting owner's CIK, so UBER's index lists Uber's sales of
   Aurora Innovation stock, and its page read "sells 4 (2 insiders, $1135.10M)" — $1,133.09M of it
   Uber selling Aurora. GOOGL's "last purchase $4.95M, 10% owner" was Alphabet buying Prime
   Medicine.
2. A Form 4 whose documents failed to fetch was dropped silently, so every count shrank with no
   mark on the line (GOOGL read 462 grants against 464 on a loaded pass).
3. The domestic read was not bounded at the reference date: UBER's page, dated 2026-10-16, counts
   filings to 2026-10-20.
4. An UNKNOWN value kept the label "(Form 4, 6m)", a six-month read that never happened.

Fixtures are REAL: every SEC document the block reads, fetched 2026-10-28, the submissions index
trimmed to the rows named in each fixture's `frozen` note. `origin_main` is main's (68da34ae) code
on those same rows, so each pin shows the defect on the shape it was found in.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from datetime import date
from pathlib import Path
from typing import Any, cast

import pytest

from vinci.dossier import mechanical as mech
from vinci.dossier import render
from vinci.dossier.schemas import Dossier, Sourced, SourceStatus
from vinci.edgar.client import EdgarClient
from vinci.netcache import CachedHttp, HttpError

ROOT = Path(__file__).resolve().parents[1]
FIX = Path(__file__).parent / "fixtures"


class _Frozen:
    """Serves the frozen pages; a URL that was not frozen FAILS the test. `fail` names URLs that
    raise the transport error `CachedHttp` raises when its retries run out — the shape GOOGL's
    loaded pass hit."""

    def __init__(self, pages: dict[str, str], fail: frozenset[str] = frozenset()) -> None:
        self.pages, self.fail = pages, fail

    def get_text(self, url: str, **_: object) -> str:
        if url in self.fail:
            raise HttpError(f"Exhausted retries for {url}")
        if url not in self.pages:
            raise AssertionError(f"not frozen: {url}")
        return self.pages[url]

    def get_json(self, url: str, **_: object) -> Any:
        return json.loads(self.get_text(url))


def _case(group: str, name: str) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads((FIX / group / f"{name}.json").read_text()))


def _run(name: str, *, group: str = "insider_own_issuer",
         fail: frozenset[str] = frozenset()) -> Sourced[str]:
    case = _case(group, name)
    http = cast(CachedHttp, _Frozen(case["pages"], fail))
    return mech._insider_activity(EdgarClient(http), http, case["cik"],
                                  date.fromisoformat(case["reference_date"]))


def _ownership_xml(case: dict[str, Any], accession: str) -> str:
    acc = accession.replace("-", "")
    return next(v for k, v in case["pages"].items() if f"/{acc}/" in k and k.endswith(".xml"))


# --- 1. a filing about another issuer ----------------------------------------------------------


def test_ubers_sales_of_aurora_stock_are_not_its_insiders_selling() -> None:
    """The observed failure, on its own documents. Three of the frozen filings are Uber's own
    Forms 4 as a 10% owner of Aurora Innovation (issuerCik 1828108): $479.25M, $471.60M and
    $182.24M. main counted them as Uber's insiders selling; the line now counts one real sale."""
    case = _case("insider_own_issuer", "UBER")
    for acc in ("0001552781-26-000357", "0001552781-26-000454", "0001552781-26-000495"):
        assert "<issuerCik>0001828108</issuerCik>" in _ownership_xml(case, acc), acc
    was = case["origin_main"]["value"]
    assert "sells 4 (2 insiders, $1135.10M)" in was and "largest sale $479.25M, 10% owner" in was
    got = _run("UBER")
    assert got.status is SourceStatus.PRESENT and got.value is not None
    assert "sells 1 (1 insider, $2.01M)" in got.value
    assert "$479.25M" not in got.value and "$1135.10M" not in got.value
    # …and the $74.00M "largest purchase" was Uber buying Aurora in 2023, not an insider buying Uber
    assert "largest purchase $74.00M" in was and "$74.00M" not in got.value
    assert ("6 more filed by this company as a holder of another issuer's stock, not counted"
            in (got.source_ref or ""))


def test_alphabet_buying_prime_medicine_is_not_an_insider_purchase() -> None:
    """GOOGL's page read "last purchase $4.95M, 10% owner": Alphabet's own Form 4 buying 1,500,000
    Prime Medicine shares at $3.30 (issuerCik 1894562). No Alphabet insider bought in the scan."""
    case = _case("insider_own_issuer", "GOOGL")
    assert "<issuerCik>0001894562</issuerCik>" in _ownership_xml(case, "0001415889-25-021025")
    assert "last purchase $4.95M, 10% owner, 2025-08-01" in case["origin_main"]["value"]
    got = _run("GOOGL")
    assert got.value is not None
    assert "no purchase in the 3y scanned" in got.value and "$4.95M" not in got.value
    assert "sells 1 (1 insider, $0.03M)" in got.value     # main: sells 16 (2 insiders, $15.15M)
    assert "11 more filed by this company as a holder" in (got.source_ref or "")


def test_an_insider_sale_of_the_issuers_own_stock_still_counts() -> None:
    """POSITIVE PIN — the filter removes the holder's filings and nothing else. Uber's 2026-09-11
    sale and its CEO's 2026-09-10 purchase, and an Alphabet director's 2026-09-30 sale, are each
    a Form 4 about the issuer's own stock and stay on the line."""
    uber, googl = _run("UBER").value or "", _run("GOOGL").value or ""
    assert "last sale $2.01M, insider, 2026-09-11" in uber
    assert "last purchase $10.01M, Chief Executive Officer, 2026-09-10" in uber
    assert "Open-market buys 3 (2 insiders, $15.31M)" in uber
    assert "last sale $0.03M, director, 2026-09-30" in googl


# --- 2. a filing that cannot be read ------------------------------------------------------------


def _doc_urls(case: dict[str, Any], accession: str) -> tuple[str, str]:
    acc = accession.replace("-", "")
    index = next(k for k in case["pages"] if f"/{acc}/index.json" in k)
    return index, next(k for k in case["pages"] if f"/{acc}/" in k and k.endswith(".xml"))


@pytest.mark.parametrize("which", ["index", "xml"])
def test_a_form4_that_cannot_be_read_makes_the_line_unknown_and_says_how_many(which: str) -> None:
    """FAIL LOUD. The failing filing is Uber's 2026-09-11 sale — the one real sale in the window —
    so a silent drop would print "sells 0" in the flattering direction. The value is UNKNOWN and
    states the count: 1 of the 17 filings to the reference date (the fixture's 23 rows less the 6
    filed after it)."""
    case = _case("insider_own_issuer", "UBER")
    index, xml = _doc_urls(case, "0001775297-26-000012")
    assert "2026-09-11" in case["pages"][xml]          # this IS the sale's filing
    got = _run("UBER", fail=frozenset({index if which == "index" else xml}))
    assert got.status is SourceStatus.UNKNOWN and got.value is None
    note = got.note or ""
    assert note.startswith("1 of 17 Form 4 filings in the 1095d scanned could not be read"), note
    assert "0001775297-26-000012" in note and "more)" not in note


def test_an_fpis_unreadable_form3_makes_its_line_unknown_too() -> None:
    """The FPI path reads every Form 3/4/5 since 2026-03-18 for its issuer, so an unreadable
    Form 3 is as loud as a Form 4: IPX's 29 filings (10 Form 3, 18 Form 4, 1 Form 4/A)."""
    case = _case("section16", "IPX")
    sub = json.loads(next(v for k, v in case["pages"].items() if "/submissions/CIK" in k))
    recent = sub["filings"]["recent"]
    form3 = next(a for a, f, d in zip(recent["accessionNumber"], recent["form"],
                                     recent["filingDate"], strict=True)
                 if f == "3" and d >= "2026-03-18")
    got = _run("IPX", group="section16", fail=frozenset({_doc_urls(case, form3)[0]}))
    assert got.status is SourceStatus.UNKNOWN
    assert (got.note or "").startswith(
        "1 of 29 Form 3/4/5 filings since 2026-03-18 could not be read"), got.note


# --- 3. the reference date ----------------------------------------------------------------------


@pytest.mark.parametrize(("name", "late"), [("UBER", "2026-10-20"), ("GOOGL", "2026-10-27")])
def test_the_domestic_read_stops_at_the_reference_date(name: str, late: str) -> None:
    """Both pages are dated 2026-10-16. main read filings to `late` while stating "in the last 182
    days"; no date on the line may now fall after the reference date."""
    case = _case("insider_own_issuer", name)
    ref = date.fromisoformat(case["reference_date"])
    assert f"last filing {late}" in case["origin_main"]["value"]
    got = _run(name).value or ""
    dates = [date.fromisoformat(d) for d in re.findall(r"\b\d{4}-\d{2}-\d{2}\b", got)]
    assert dates and max(dates) <= ref, (max(dates), got)


# --- 4. the label, end to end on a committed page ----------------------------------------------


def _wern_with(insider: Sourced[str]) -> Dossier:
    d = Dossier.model_validate_json((ROOT / "data/dossiers/WERN/dossier.json").read_text())
    assert d.mechanical.catalyst_path is not None
    cp = d.mechanical.catalyst_path.model_copy(update={"insider_activity": insider})
    return d.model_copy(update={"mechanical": d.mechanical.model_copy(
        update={"catalyst_path": cp})})


def _md_row(d: Dossier) -> str:
    return next(r for r in render._positioning_lines(d.mechanical) if "Insider activity" in r)


def _web_label(d: Dossier, tmp_path: Path) -> str:
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    src = tmp_path / "WERN.json"
    src.write_text(d.model_dump_json())
    driver = r"""
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
const stub = new Proxy(function(){}, { get: () => stub, apply: () => stub, construct: () => ({}) });
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const { renderDossier } = await import(pathToFileURL(process.argv[1]).href);
process.stdout.write(renderDossier(JSON.parse(readFileSync(process.argv[2])), null));
"""
    js = ROOT / "frontend/views/shared/dossier.js"
    page = subprocess.run(["node", "--input-type=module", "-e", driver, str(js), str(src)],
                          capture_output=True, text=True, check=True).stdout
    labels = re.findall(r'<div class="fact-label">(Insider activity[^<]*)</div>', page)
    assert len(labels) == 1, labels
    return labels[0]


def test_an_unknown_insider_value_never_claims_six_months(tmp_path: Path) -> None:
    """The committed WERN page with its insider value replaced by the REAL UNKNOWN the fail-loud
    rule produces, through both renderers. main labelled it "(Form 4, 6m)"."""
    unknown = _run("UBER", fail=frozenset(_doc_urls(_case("insider_own_issuer", "UBER"),
                                                    "0001775297-26-000012")[1:]))
    assert unknown.status is SourceStatus.UNKNOWN
    d = _wern_with(unknown)
    assert _md_row(d).startswith("- **Insider activity (Form 4):** _UNKNOWN_ — 1 of 17 Form 4")
    assert _web_label(d, tmp_path) == "Insider activity (Form 4)"


def test_a_present_value_with_no_window_of_its_own_keeps_6m(tmp_path: Path) -> None:
    """NEGATIVE PIN — the label still supplies the horizon where the value does not (#319). The
    value is the real one #319 shipped: a count with no window in it."""
    shipped = ("Open-market buys 2 · sells 0 (net +90.0K sh) · grants 12 · last 2026-07-24 · "
               "other F×4")
    d = _wern_with(Sourced.present(shipped, source_ref="EDGAR Form 4 (#319's committed line)"))
    assert _md_row(d).startswith("- **Insider activity (Form 4, 6m):** Open-market buys 2")
    assert _web_label(d, tmp_path) == "Insider activity (Form 4, 6m)"
