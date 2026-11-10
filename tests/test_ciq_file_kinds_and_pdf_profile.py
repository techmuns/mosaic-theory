"""A file's kind comes from an exact name rule, never a keyword anywhere in its name, and a PDF
tearsheet is read as a PDF (fix request 2, order 5: audits RA-D10 = A-D15 = RBC-D2, and RA-D17;
2026-11-10).

* RA-D10 — CIQ names an export "<company> <exchange> <ticker> <kind>", so a kind keyword in the
  COMPANY's name chose the kind: "Synchrony Financial"'s whole pack read as financials and was
  refused as "more than one export of a kind"; with only its Customers file, F27 read MISSING;
  "Customers Bancorp"'s Suppliers file was read as its Customers. The kind is now the stem's end
  (the comps book's start, a call's dated tail): `ciq.workbook_kind`.
* RA-D17 — `gics_industry` decoded the tearsheet with `rtf_to_text` whatever its bytes were, so a
  PDF tearsheet read "no Primary Industry Classification".

The real-export pins link SMPL's exports into a temporary folder under other issuers' CIQ names
(the bytes are not copied) and skip where the licensed folder is absent, as on CI; the
constructed twins run everywhere.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

from vinci.config import get_config
from vinci.dossier import ciq_sheets as cs
from vinci.dossier.ciq import CiqBundle, CiqFormat, _customers_role, workbook_kind
from vinci.dossier.manual_store import LocalFolderStore
from vinci.dossier.schemas import SourceStatus

_SMPL_PREFIX = re.compile(r"^The Simply Good Foods Company NasdaqCM SMPL |^TheSimplyGoodFoods"
                          r"CompanyNasdaqCMSMPL")


def _smpl_files() -> list[Path]:
    files = LocalFolderStore.from_config(get_config()).files("SMPL")
    if not files:
        pytest.skip("licensed CIQ bundle for SMPL unavailable (never committed)")
    return [f for f in files if not f.name.startswith(".")]


def _renamed(tmp: Path, files: list[Path], issuer: str, listing: str) -> list[Path]:
    """SMPL's exports, linked under another issuer's CIQ names: the kind part kept, the company and
    listing replaced."""
    out = []
    for f in files:
        name = f.name
        if _SMPL_PREFIX.search(name):
            name = _SMPL_PREFIX.sub(f"{issuer} {listing} ", name)
        elif name.startswith("Company Comparable Analysis "):
            name = f"Company Comparable Analysis {issuer}{f.suffix}"
        elif "Earnings Call" in name:
            name = re.sub(r"^.*?(, Q\d \d{4} Earnings Call, .*)$", rf"{issuer}\1", name)
        link = tmp / name
        link.symlink_to(f)
        out.append(link)
    return out


@pytest.mark.parametrize(("issuer", "listing"), [
    ("Synchrony Financial", "NYSE SYF"), ("Realty Income Corporation", "NYSE O"),
    ("Customers Bancorp, Inc.", "NYSE CUBI"), ("Consensus Cloud Solutions, Inc.", "NasdaqGS CCSI")])
def test_ra_d10_an_issuer_named_with_a_kind_word_reads_as_its_own_pack(
        issuer: str, listing: str, tmp_path: Path) -> None:
    """(+) Every file of SMPL's pack, renamed to the issuer's CIQ name, has the kind its SMPL
    original has; the bundle builds and the roster reads. Before: refused as ambiguous."""
    files = _smpl_files()
    want = sorted((workbook_kind(f.name), f.suffix) for f in files)
    links = _renamed(tmp_path, files, issuer, listing)
    assert sorted((workbook_kind(f.name), f.suffix) for f in links) == want
    b = CiqBundle.from_files("ZZZ", links)
    roster, _n = cs.customer_roster(b)
    assert roster.status is not SourceStatus.MISSING, roster.note
    assert b.workbook("financials", freq="annual") is not None


def test_ra_d10_a_customers_only_folder_under_a_financial_name_is_not_missing(
        tmp_path: Path) -> None:
    files = [f for f in _smpl_files() if f.name.endswith("Customers.rtf")]
    (link,) = _renamed(tmp_path, files, "Synchrony Financial", "NYSE SYF")
    roster, _n = cs.customer_roster(CiqBundle.from_files("SYF", [link]))
    assert roster.status is not SourceStatus.MISSING, roster.note


@pytest.mark.parametrize(("name", "kind"), [
    ("Synchrony Financial NYSE SYF Customers.rtf", "customers"),
    ("Synchrony Financial NYSE SYF Key Developments.rtf", "key_developments"),
    ("Realty Income Corporation NYSE O Financials_Annual.xls", "financials"),
    ("Customers Bancorp, Inc. NYSE CUBI Suppliers.rtf", "customers"),
    ("Consensus Cloud Solutions, Inc. NasdaqGS CCSI Public Company Profile.rtf", "profile"),
    ("Income Opportunity Realty Investors NYSEAM IOR Credit Health Panel.xls", "credit_health"),
    ("ConsensusCloudSolutionsIncNasdaqGSCCSIEstimatesReport.xls", "estimates"),
    ("Company Comparable Analysis Synchrony Financial.xls", "comps"),
    ("Synchrony Financial, Q3 2026 Earnings Call, Oct 15, 2026.rtf", "transcript"),
    ("Oracle Corporation NYSE ORCL Public Investment Firm Profile.rtf", "profile"),
    ("Oracle Corporation NYSE ORCL Ownership Summary.xls", None),
    ("Oracle Corporation NYSE ORCL Customers 2.rtf", "customers"),
    ("Oracle Corporation NYSE ORCL Financials_Annual (1).xls", "financials"),
    ("Oracle Corporation, Q1 2026 Earnings Call, Sep 09, 2026.rtf", "transcript"),
])
def test_ra_d10_twin_the_kind_is_the_names_end_never_a_word_in_it(
        name: str, kind: str | None) -> None:
    """The exact name rule on CIQ's own shapes. An ownership pull is no known kind and stays
    unrecognised, named by the assembler; a download's duplicate ("… 2", "… (1)") keeps its kind,
    so it meets the one-export refusal beside the original rather than losing to it unseen."""
    assert workbook_kind(name) == kind


def test_ra_d10_twin_the_customers_and_suppliers_files_are_told_apart_by_their_end() -> None:
    assert _customers_role("Customers Bancorp, Inc. NYSE CUBI Suppliers.rtf") == "suppliers"
    assert _customers_role("Supplier Holdings NYSE SUP Customers.rtf") == "customers"


def test_ra_d17_a_pdf_tearsheet_reads_its_industry(tmp_path: Path) -> None:
    """SMPL's real tearsheet converted to PDF by LibreOffice (as the auditor did; not a CIQ-made
    PDF): the industry reads as it does from the RTF."""
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice is None or shutil.which("pdftotext") is None:
        pytest.skip("LibreOffice or pdftotext not installed")
    prof = next(f for f in _smpl_files() if f.name.endswith("Public Company Profile.rtf"))
    rtf = cs.gics_industry(CiqBundle.from_files("SMPL", [prof]))
    assert rtf.status is SourceStatus.PRESENT, rtf.note
    done = subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir",
                           str(tmp_path), str(prof)], capture_output=True, check=False)
    pdf = tmp_path / f"{prof.stem}.pdf"
    if done.returncode != 0 or not pdf.exists():
        pytest.skip("LibreOffice could not convert the tearsheet on this machine")
    b = CiqBundle.from_files("SMPL", [pdf])
    assert b.workbook("profile") is not None and b.workbook("profile").fmt is CiqFormat.PDF
    got = cs.gics_industry(b)
    assert got.status is SourceStatus.PRESENT and got.value == rtf.value, got.note


def test_ra_d17_twin_the_value_on_the_labels_own_line_is_read(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A PDF's layout text puts the value beside its label: it is read from that line."""
    pdf = tmp_path / "Zinnober Fixture Works Inc NasdaqGS ZZFX Public Company Profile.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    monkeypatch.setattr(cs, "read_text", lambda path, fmt=None: (
        "Zinnober Fixture Works Inc.\nPrimary Industry Classification    Industrial Machinery\n"))
    got = cs.gics_industry(CiqBundle.from_files("ZZFX", [pdf]))
    assert got.status is SourceStatus.PRESENT and got.value == "Industrial Machinery", got.note


def test_ra_d17_twin_a_second_layout_column_is_not_read_into_the_value(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """(−) Layout text carries the next column on the label's line: only the first is the value."""
    pdf = tmp_path / "Zinnober Fixture Works Inc NasdaqGS ZZFX Public Company Profile.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    monkeypatch.setattr(cs, "read_text", lambda path, fmt=None: (
        "Primary Industry Classification    Industrial Machinery      Website  zz.example\n"))
    got = cs.gics_industry(CiqBundle.from_files("ZZFX", [pdf]))
    assert got.status is SourceStatus.PRESENT and got.value == "Industrial Machinery", got.note


def test_ra_d17_twin_a_pdf_the_tool_cannot_read_is_unknown_not_a_crash(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """(−) `pdftotext` exits 1 on a corrupt or encrypted PDF (`CalledProcessError`): the profile is
    unreadable and the SIC fallback stands — the assembler calls this unguarded."""
    pdf = tmp_path / "Zinnober Fixture Works Inc NasdaqGS ZZFX Public Company Profile.pdf"
    pdf.write_bytes(b"%PDF-1.4\ngarbage\n")

    def _fail(path: Path, fmt: object = None) -> str:
        raise subprocess.CalledProcessError(1, ["pdftotext", "-layout", str(path), "-"])
    monkeypatch.setattr(cs, "read_text", _fail)
    got = cs.gics_industry(CiqBundle.from_files("ZZFX", [pdf]))
    assert got.status is SourceStatus.UNKNOWN and "unreadable" in (got.note or ""), got.note
    assert str(tmp_path) not in (got.note or ""), "a page note never carries a local path"


def test_ra_d10_every_registered_kind_has_a_name_rule_and_no_rule_names_another() -> None:
    """The kind REGISTRY (`_WORKBOOK_KEYWORDS`, read by the assembler's requirements and the
    quality map) and the name RULES that decide a file's kind are one set: a kind registered with
    no rule would never be recognised."""
    from vinci.dossier.ciq import _KIND_NAME_RULES, _WORKBOOK_KEYWORDS
    assert {k for k, _rule in _KIND_NAME_RULES} == set(_WORKBOOK_KEYWORDS)
