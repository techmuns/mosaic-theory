"""A name's CIQ folder holds ONE export per kind, or the loader refuses (2026-10-11).

THE DEFECT. `CiqBundle.workbook()` answered with the FIRST candidate by sort order, and with a
period type it fell back to the first of ANY period type. CIQ renamed a same-kind export between
pulls in 3 of 6 archived re-exports — BRBR's and UBER's comps "…Inc .xls" → "…Inc.xls", GOOGL's
Key Developments `.xls` → `.rtf` — so a re-export copied in beside the old file leaves two, the
space sorts first, and the page is priced on the stale one with nothing said.

THE FILE NAMES BELOW ARE THE REAL ONES. Selection is decided by NAME (kind keywords, sort order,
the `_annual`/`_quarterly` token), so the observed names are the failure shape; file CONTENT only
matters where a period type is read, and there the workbooks are built from the real type.
"""
from __future__ import annotations

import inspect
import pathlib

import pytest

from vinci.dossier.ciq import (
    MULTI_FILE_KINDS,
    CiqAmbiguousError,
    CiqBundle,
    CiqFormat,
    CiqUnavailableError,
    CiqWorkbook,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
LIVE = ROOT / "data" / "manual" / "ciq"
ARCHIVE = ROOT / "data" / "manual" / "ciq-archive"

UBER_COMPS = ("Company Comparable Analysis Uber Technologies Inc .xls",   # the 08-05 pull
              "Company Comparable Analysis Uber Technologies Inc.xls")    # the 10-11 pull
GOOGL_KEYDEV = ("Alphabet Inc NasdaqGS GOOGL Key Developments.xls",
                "Alphabet Inc NasdaqGS GOOGL Key Developments.rtf")


def _folder(tmp: pathlib.Path, names: tuple[str, ...]) -> list[pathlib.Path]:
    for n in names:
        (tmp / n).write_bytes(b"placeholder")
    return sorted(tmp.iterdir())


def _wb(kind: str, name: str, freq: str | None) -> CiqWorkbook:
    return CiqWorkbook(kind=kind, path=pathlib.Path(name), fmt=CiqFormat.BIFF_XLS, freq=freq)


# --- refused: two exports of one kind ------------------------------------------------------------

@pytest.mark.parametrize("names,kind", [(UBER_COMPS, "comps"), (GOOGL_KEYDEV, "key_developments")])
def test_two_exports_of_one_kind_refuse_at_construction(
    tmp_path: pathlib.Path, names: tuple[str, ...], kind: str,
) -> None:
    with pytest.raises(CiqAmbiguousError) as exc:
        CiqBundle.from_files("X", _folder(tmp_path, names))
    msg = str(exc.value)
    assert kind in msg and all(n in msg for n in names), msg
    assert "ciq-archive/replaced-" in msg, "the refusal must say how to clear it"


def test_a_directly_built_bundle_refuses_in_workbook() -> None:
    b = CiqBundle(ticker="UBER", workbooks=tuple(_wb("comps", n, None) for n in UBER_COMPS))
    with pytest.raises(CiqAmbiguousError):
        b.workbook("comps")
    with pytest.raises(CiqAmbiguousError):
        b.sheet("comps", "Financial Data")


def test_the_ambiguity_is_not_an_unavailable_export() -> None:
    """Every reader catches `CiqUnavailableError` and degrades to a missing section — a guess
    between two exports must not degrade quietly, so the error is a different class."""
    assert not issubclass(CiqAmbiguousError, CiqUnavailableError)


# --- period types: two of them is not two exports, and one is never substituted for another -----

def test_annual_and_quarterly_are_two_period_types_not_two_exports() -> None:
    ann = _wb("financials", "Uber Technologies Inc NYSE UBER Financials_Annual.xls", "annual")
    qtr = _wb("financials", "Uber Technologies Inc NYSE UBER Financials_Quarterly.xls", "quarterly")
    b = CiqBundle(ticker="UBER", workbooks=(ann, qtr))
    assert b.workbook("financials", freq="annual") is ann
    assert b.workbook("financials", freq="quarterly") is qtr
    with pytest.raises(CiqAmbiguousError):
        b.workbook("financials")          # which one? — no caller asks this, and none may


def test_two_exports_of_one_period_type_refuse() -> None:
    """A re-pulled quarterly export beside the old one: the period type matches twice."""
    stem = "Uber Technologies Inc NYSE UBER Financials_Quarterly"
    old = _wb("financials", f"{stem} .xls", "quarterly")
    new = _wb("financials", f"{stem}.xls", "quarterly")
    with pytest.raises(CiqAmbiguousError) as exc:
        CiqBundle(ticker="UBER", workbooks=(old, new)).workbook("financials", freq="quarterly")
    assert "2 exports of that period type" in str(exc.value)


def test_a_period_type_is_never_substituted_when_several_exist() -> None:
    """THE AORT SHAPE: a quarterly request with no quarterly export among several was served the
    annual workbook. Several candidates, none of the period type asked for, now refuse; a LONE
    export whose period type is unread still answers, as it always did (the negative pin)."""
    ann = _wb("financials", "Artivion Inc NYSE AORT Financials_Annual.xls", "annual")
    untagged = _wb("financials", "Artivion Inc NYSE AORT Financials.xls", None)
    with pytest.raises(CiqAmbiguousError) as exc:
        CiqBundle(ticker="AORT", workbooks=(ann, untagged)).workbook("financials", freq="quarterly")
    assert "never substituted" in str(exc.value)
    assert CiqBundle(ticker="AORT", workbooks=(untagged,)).workbook(
        "financials", freq="quarterly") is untagged


# --- not refused: the kinds that legitimately hold several ----------------------------------------

def test_the_multi_file_kinds_hold_several(tmp_path: pathlib.Path) -> None:
    """NEGATIVE PIN on real names: the Customers/Suppliers pair is ONE kind on every name, read by
    its one reader through `all_workbooks`; transcripts are one per call."""
    assert {"customers", "transcript"} == MULTI_FILE_KINDS
    names = ("Uber Technologies Inc NYSE UBER Customers.rtf",
             "Uber Technologies Inc NYSE UBER Suppliers.rtf",
             "Uber Technologies, Inc., Q1 2026 Earnings Call, May 06, 2026.rtf",
             "Uber Technologies, Inc., Q2 2026 Earnings Call, Aug 05, 2026.rtf",
             UBER_COMPS[1])
    b = CiqBundle.from_files("UBER", _folder(tmp_path, names))
    assert len(b.all_workbooks("customers")) == 2 and len(b.all_workbooks("transcript")) == 2
    customers = b.workbook("customers")
    assert customers is not None and customers.path.name == names[0]   # the old answer, kept
    comps = b.workbook("comps")
    assert comps is not None and comps.path.name == UBER_COMPS[1]


# --- the live folders and the real copy-in shapes -------------------------------------------------

def _old_pick(b: CiqBundle, kind: str, freq: str | None) -> CiqWorkbook | None:
    cands = [w for w in b.workbooks if w.kind == kind]
    if not cands:
        return None
    if freq is not None:
        return next((w for w in cands if w.freq == freq), None) or cands[0]
    return cands[0]


def test_every_live_folder_builds_and_picks_what_it_picked_before() -> None:
    """CORPUS FIRST: on every live folder the change refuses nothing a caller asks for and picks
    the SAME file as before — financials by period type (every caller passes one), every other
    kind once. Skips where the licensed exports are not on this machine (CI)."""
    folders = sorted(p for p in LIVE.iterdir() if p.is_dir()) if LIVE.is_dir() else []
    if not folders:
        pytest.skip("no CIQ exports on this machine")
    picks = 0
    for f in folders:
        b = CiqBundle.from_files(f.name, sorted(p for p in f.iterdir() if p.is_file()))
        for kind in sorted({w.kind for w in b.workbooks}):
            for freq in (("annual", "quarterly") if kind == "financials" else (None,)):
                new, old = b.workbook(kind, freq=freq), _old_pick(b, kind, freq)
                assert (new and new.path) == (old and old.path), (f.name, kind, freq)
                picks += 1
    assert picks >= 100, f"only {picks} picks compared"


@pytest.mark.parametrize("replaced,ticker,stale", [
    ("replaced-2026-10-11", "UBER", UBER_COMPS[0]),
    ("replaced-2026-09-22", "BRBR", "Company Comparable Analysis BellRing Brands Inc .xls"),
    ("replaced-2026-09-22", "GOOGL", GOOGL_KEYDEV[0]),
])
def test_the_real_copy_in_shapes_refuse(replaced: str, ticker: str, stale: str) -> None:
    """The archived pull copied in UNDER the live one — same names overwrite, renamed ones are
    left behind — exactly what a copy-in sync produces. Each is refused, naming the stale file."""
    old_dir, live_dir = ARCHIVE / replaced / ticker, LIVE / ticker
    if not (old_dir.is_dir() and live_dir.is_dir()):
        pytest.skip("archived and live exports not on this machine")
    live = {p.name: p for p in live_dir.iterdir() if p.is_file()}
    left = [p for p in old_dir.iterdir() if p.is_file() and p.name not in live]
    with pytest.raises(CiqAmbiguousError) as exc:
        CiqBundle.from_files(ticker, sorted([*live.values(), *left]))
    assert stale in str(exc.value)


# --- the one write path that swallowed everything -------------------------------------------

def test_anchor_backfill_lets_the_ambiguity_through() -> None:
    """`anchor-backfill` reads CIQ inside `except Exception` ("no workbook is normal; EDGAR-only
    then"). An ambiguous folder is not "no workbook", so it is re-raised before that handler."""
    import vinci.cli as cli

    src = inspect.getsource(cli._cmd_anchor_backfill)
    broad = src.index("no workbook is normal; EDGAR-only then")
    assert src.index("except CiqAmbiguousError:") < broad


# --- review fixes (2026-10-11): what is NOT a second export, and what still is ------------------

@pytest.mark.parametrize("dropping", [
    "~$mpany Comparable Analysis Uber Technologies Inc.xls",     # Excel's lock file, comps open
    "._Company Comparable Analysis Uber Technologies Inc.xls",   # AppleDouble sidecar
])
def test_editor_and_sync_droppings_are_not_a_second_export(
    tmp_path: pathlib.Path, dropping: str,
) -> None:
    """A lock file carries its workbook's name, so classified BEFORE the dropping skip it counted as
    a second comps export and an Excel window open on the comps refused the whole folder. The
    AppleDouble `._` sidecar sorted FIRST and was picked. Neither is an export, nor unrecognised."""
    b = CiqBundle.from_files("UBER", _folder(tmp_path, (UBER_COMPS[1], dropping)))
    comps = b.workbook("comps")
    assert comps is not None and comps.path.name == UBER_COMPS[1]
    assert len(b.all_workbooks("comps")) == 1 and dropping not in b.unrecognised


def test_an_unreadable_annual_and_quarterly_pair_is_not_ambiguous(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The filename token names the period type even when the workbook cannot be read (`xlrd` not
    installed — `read_sheets` raises `CiqParseError`). Tagged None, the pair read as two exports of
    one kind and the refusal told the operator to archive a file that was not stale."""
    import vinci.dossier.ciq as ciq

    def _no_xlrd(path: pathlib.Path, fmt: CiqFormat | None = None) -> None:
        raise ciq.CiqParseError(f"{path.name}: legacy .xls needs `xlrd` — not installed")

    monkeypatch.setattr(ciq, "read_sheets", _no_xlrd)
    names = ("Uber Technologies Inc NYSE UBER Financials_Annual.xls",
             "Uber Technologies Inc NYSE UBER Financials_Quarterly.xls")
    for n in names:   # BIFF magic, so classify() says .xls and the read is attempted
        (tmp_path / n).write_bytes(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 64)
    b = CiqBundle.from_files("UBER", sorted(tmp_path.iterdir()))
    ann, qtr = b.workbook("financials", freq="annual"), b.workbook("financials", freq="quarterly")
    assert ann is not None and ann.path.name == names[0]
    assert qtr is not None and qtr.path.name == names[1]


def test_two_customers_exports_refuse_and_the_supplier_pair_does_not(
    tmp_path: pathlib.Path,
) -> None:
    """`customers` is two exports, each held once. Its reader takes the FIRST file named
    Customers, so a re-pulled Customers export beside the old one (the GOOGL `.xls` → `.rtf`
    shape) is the stale-wins defect on an exempt kind. Customers + Suppliers stays accepted."""
    pair = ("Uber Technologies Inc NYSE UBER Customers.rtf",
            "Uber Technologies Inc NYSE UBER Suppliers.rtf")
    CiqBundle.from_files("UBER", _folder(tmp_path, pair))          # the negative pin
    (tmp_path / "Uber Technologies Inc NYSE UBER Customers.xls").write_bytes(b"placeholder")
    with pytest.raises(CiqAmbiguousError) as exc:
        CiqBundle.from_files("UBER", sorted(tmp_path.iterdir()))
    assert "Customers.xls" in str(exc.value) and "Suppliers" not in str(exc.value)
