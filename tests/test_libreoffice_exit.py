"""A NON-ZERO LIBREOFFICE EXIT IS A CALL THAT DID NOT READ, NAMED — NEVER A CRASH (audit RA-D11,
fix request 2, order 3; 2026-11-10).

Every CIQ transcript on disk is an OLE Word document behind an `.rtf` name (68 of 68 on
2026-11-10), so every call is read through LibreOffice. `read_text` ran it with `check=True`, and
`subprocess.CalledProcessError` is not the `CiqParseError` its callers catch: one failed conversion
escaped `transcript_for_synthesis` and the skip-and-flag path the G-D4 fix built
(`unparsed_transcript_flag`) never ran. LibreOffice refuses a second conversion while one runs; the
auditor saw exit 1 in 2 of ~25 runs on unmodified transcripts.

The stub stands in for `soffice` and exits 1, as the real one did. The real-export pins read AMZN's
calls (skip where the licensed folder is absent, as on CI); the constructed twin runs everywhere.
"""
from __future__ import annotations

import contextlib
import shutil
import subprocess
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from vinci.config import get_config
from vinci.dossier import ciq_sheets as cs
from vinci.dossier.ciq import (
    CiqBundle,
    CiqFormat,
    CiqParseError,
    CiqWorkbook,
    classify,
    read_text,
)
from vinci.dossier.manual_store import LocalFolderStore
from vinci.graph.llm import LlmClient

_OLE_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"


def _stub(tmp: Path, *, fail_on: str | None = None) -> Path:
    """A `soffice` that exits 1 — for every file, or only for one whose name holds ``fail_on``
    (the others are converted to a one-line `.txt`, as LibreOffice writes it)."""
    script = tmp / "soffice"
    # the source is the last argument and the folder follows `--outdir`, wherever the profile
    # flag puts them (`ciq.libreoffice_convert` passes `-env:UserInstallation` first)
    cond = f'case "$src" in *"{fail_on}"*) fail=1;; *) fail=0;; esac' if fail_on else "fail=1"
    script.write_text(
        "#!/bin/sh\n"
        'prev=""; for a; do [ "$prev" = "--outdir" ] && out=$a; prev=$a; src=$a; done\n'
        + cond + "\n"
        'if [ "$fail" = 1 ]; then echo "Error: source file could not be loaded" >&2; exit 1; fi\n'
        'name=$(basename "$src"); printf "Operator: welcome to the call.\\n" '
        '> "$out/${name%.*}.txt"\n')
    script.chmod(0o755)
    return script


def _use(monkeypatch: pytest.MonkeyPatch, script: Path) -> None:
    real = shutil.which

    def which(cmd: str, *a: object, **k: object) -> str | None:
        return str(script) if cmd == "soffice" else real(cmd)

    monkeypatch.setattr(shutil, "which", which)


def _amzn() -> CiqBundle:
    files = LocalFolderStore.from_config(get_config()).files("AMZN")
    if not files:
        pytest.skip("licensed CIQ bundle for AMZN unavailable (never committed)")
    b = CiqBundle.from_files("AMZN", files)
    if not b.all_workbooks("transcript"):
        pytest.skip("AMZN's folder holds no transcript")
    return b


def test_ra_d11_a_failed_conversion_of_a_real_call_is_a_parse_error(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    b = _amzn()
    wb = b.all_workbooks("transcript")[0]
    assert wb.fmt is CiqFormat.OLE_DISGUISED, wb.fmt
    _use(monkeypatch, _stub(tmp_path))
    with pytest.raises(CiqParseError, match=r"LibreOffice exited 1 .*could not be loaded"):
        read_text(wb.path, wb.fmt)


def test_ra_d11_one_failed_call_is_left_out_and_named_and_the_rest_still_read(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """THE SKIP-AND-FLAG PATH, end to end on AMZN's calls: the first call's conversion exits 1.
    The reader does not stop; the slice holds every other call; the flag names the one left out.
    (−) With every conversion failing, the slice is None and the flag says no call reached it.
    The $0 build keeps exactly this; a paid one refuses on it before any model call
    (`test_a_paid_build_refuses_a_call_that_did_not_read_before_any_model_call`)."""
    b = _amzn()
    calls = [w.path.name for w in b.all_workbooks("transcript")]
    if len(calls) < 2:
        pytest.skip("AMZN's folder holds one call; the mixed case needs two")
    _use(monkeypatch, _stub(tmp_path, fail_on=calls[0]))
    sliced = cs.transcript_for_synthesis(b)
    assert sliced is not None and f"--- {calls[0]} ---" not in sliced
    assert all(f"--- {c} ---" in sliced for c in calls[1:])
    flag = cs.unparsed_transcript_flag(b, sliced) or ""
    assert calls[0] in flag and all(c not in flag for c in calls[1:]), flag

    _use(monkeypatch, _stub(tmp_path))
    assert cs.transcript_for_synthesis(b) is None
    assert cs.unparsed_transcript_flag(b, None) is not None


def test_ra_d11_twin_an_ole_file_whose_conversion_fails_raises_the_callers_error(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """(+) Exit 1: `CiqParseError`, naming the exit and LibreOffice's own words — never
    `CalledProcessError`. (−) Exit 0 with its `.txt` written: the text is read."""
    doc = tmp_path / "Zinnober Fixture Works Inc, Q1 2027 Earnings Call, Sep 24, 2026.rtf"
    doc.write_bytes(_OLE_MAGIC + b"\x00" * 504)
    assert classify(doc) is CiqFormat.OLE_DISGUISED
    _use(monkeypatch, _stub(tmp_path))
    with pytest.raises(CiqParseError, match="LibreOffice exited 1") as err:
        read_text(doc)
    assert not isinstance(err.value, subprocess.CalledProcessError)
    _use(monkeypatch, _stub(tmp_path, fail_on="no such call"))
    assert read_text(doc) == "Operator: welcome to the call.\n"


_PAID = object()  # any client: the refusal asks only whether the build is a paid one


def _two_calls() -> CiqBundle:
    def call(q: str) -> CiqWorkbook:
        return CiqWorkbook(kind="transcript", fmt=CiqFormat.OLE_DISGUISED, freq=None,
                           path=Path(f"Zinnober Fixture Works Inc, {q} 2026 Earnings Call.rtf"))
    return CiqBundle(ticker="ZFW", workbooks=(call("Q1"), call("Q2")))


def test_a_paid_build_refuses_a_call_that_did_not_read_before_any_model_call() -> None:
    """A PAID BUILD READS EVERY CALL ON FILE OR SPENDS NOTHING (2026-11-17). VRRM's check build
    (run `6043fb83`) read 1 of its 2 calls, flagged the other, and spent $5.15 on a page that lost
    all 12 of the Q1 call's driver rows, so the page was held. FAILED before the fix: no refusal
    existed and the build went on to its covenant, driver and synthesis calls.
    (+) One of two calls missing from the slice: refused, naming it and not the call that read.
    (+) No call read at all (the slice is None): refused, naming both."""
    from vinci.dossier import assemble

    b = _two_calls()
    q1, q2 = (w.path.name for w in b.all_workbooks("transcript"))
    with pytest.raises(assemble.DossierAssemblyError, match="1 of 2 call") as err:
        assemble._refuse_unread_calls(b, f"--- {q2} ---\nremarks", _PAID)  # type: ignore[arg-type]
    assert q1 in str(err.value) and q2 not in str(err.value)
    with pytest.raises(assemble.DossierAssemblyError, match="2 of 2 call") as err:
        assemble._refuse_unread_calls(b, None, _PAID)  # type: ignore[arg-type]
    assert q1 in str(err.value) and q2 in str(err.value)


def test_the_unread_call_refusal_spares_the_zero_dollar_build_and_a_whole_read() -> None:
    """(−) The $0 build (`llm` None: the precheck's `mechanical_build`, the impact child) keeps
    the skip-and-flag and is never refused. (−) Every call read, one of them cut at the ceiling:
    no refusal, since a cut call is in the model's input. (−) No call on file: nothing to read."""
    from vinci.dossier import assemble
    from vinci.dossier import ciq_sheets as cs

    b = _two_calls()
    q1, q2 = (w.path.name for w in b.all_workbooks("transcript"))
    assemble._refuse_unread_calls(b, None, None)
    whole = f"--- {q1} ---\nremarks{cs._cut_marker(10**6)}\n\n--- {q2} ---\nremarks"
    assemble._refuse_unread_calls(b, whole, _PAID)  # type: ignore[arg-type]
    assert "cut at the ceiling" in (cs.unparsed_transcript_flag(b, whole) or "")
    assemble._refuse_unread_calls(CiqBundle(ticker="ZFW", workbooks=()), None,
                                  _PAID)  # type: ignore[arg-type]


def test_the_unread_call_refusal_comes_before_the_first_paid_phase() -> None:
    """In `assemble_one`'s own source: the refusal reads the slice the build just computed and is
    asked before the covenant phase, the first call the build pays for."""
    from vinci.dossier import assemble

    src = Path(assemble.__file__).read_text()
    read = src.index("transcript = ciq_sheets.transcript_for_synthesis(bundle)")
    refuse = src.index("_refuse_unread_calls(bundle, transcript, llm)")
    assert read < refuse < src.index("extract_covenant_terms(\n") < src.index(
        "extract_transcript_drivers(\n")


def test_a_paid_build_refuses_one_real_call_that_did_not_read(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """On AMZN's real calls (skip where the licensed folder is absent, as on CI): the first call's
    conversion exits 1, and the refusal names it and no other call."""
    from vinci.dossier import assemble

    b = _amzn()
    calls = [w.path.name for w in b.all_workbooks("transcript")]
    _use(monkeypatch, _stub(tmp_path, fail_on=calls[0]))
    sliced = cs.transcript_for_synthesis(b)
    with pytest.raises(assemble.DossierAssemblyError, match=f"1 of {len(calls)} call") as err:
        assemble._refuse_unread_calls(b, sliced, _PAID)  # type: ignore[arg-type]
    assert calls[0] in str(err.value) and all(c not in str(err.value) for c in calls[1:])


class _TrapLlm(LlmClient):
    """A model client that fails the test if the build ever asks it anything."""

    def extract(self, *, system: str, user: str, tool: dict[str, Any],
                cache: bool = False) -> dict[str, Any]:
        raise AssertionError("assemble_one reached a model call")

    @property
    def model(self) -> str:
        return "trap"


def test_assemble_one_refuses_an_unread_call_and_never_reaches_the_model(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """THE REFUSAL DRIVEN THROUGH `assemble_one` (A's review of #1105). Two calls on disk, the
    first one's conversion exiting 1, and a model client that fails the test if called. Everything
    `assemble_one` does before reading the calls that needs a network, a store or a real finalist
    is stood in for; the CIQ loader, the requirements manifest, the LTM check and the transcript
    reader are production's own, on the files in this folder. FAILED with the refusal's line
    removed: the build went on and asked the model."""
    from vinci import eod
    from vinci.dossier import assemble
    from vinci.dossier import driver_evidence as de
    from vinci.dossier.schemas import Dossier

    frozen = Path("tests/fixtures/frozen_pages/2026-10-26/AORT/dossier.json")
    mech = Dossier.model_validate_json(frozen.read_text()).mechanical.model_copy(
        update={"capital_structure": None, "financial_summary": None})
    folder = tmp_path / "ZFW"
    folder.mkdir()
    calls = [folder / f"Zinnober Fixture Works Inc, {q} 2026 Earnings Call, Sep 24, 2026.rtf"
             for q in ("Q1", "Q2")]
    for call in calls:
        call.write_bytes(_OLE_MAGIC + b"\x00" * 504)
    _use(monkeypatch, _stub(tmp_path, fail_on="Q1"))
    (tmp_path / "spool").mkdir()
    monkeypatch.setenv(de.SPOOL_ENV, str(tmp_path / "spool"))
    rec = SimpleNamespace(identity=SimpleNamespace(ticker="ZFW", internal_id="zfw", cik=None,
                                                   name="Zinnober Fixture Works"))
    for name, value in {
        "_price_store_stamp": lambda cfg: None,
        "_with_listing_basis": lambda r, **k: r,
        "Store": lambda path: contextlib.nullcontext(SimpleNamespace()),
        "EdgarClient": SimpleNamespace(from_config=lambda cfg: None),
        "build_sec_http": lambda cfg: None,
        "build_finra_http": lambda cfg: None,
        "_read_scenario_card": lambda ticker: None,
        "_drawdown_anchor_date": lambda cfg, ticker: None,
        "assemble_mechanical": lambda *a, **k: (mech, []),
    }.items():
        monkeypatch.setattr(assemble, name, value)
    monkeypatch.setattr(eod.PolygonEodClient, "from_config",
                        lambda cfg: SimpleNamespace(security_types=dict))
    fin = SimpleNamespace(data_record=rec, reference_date=date(2026, 11, 16), sleeve="overshoot",
                          market_cap_screen=None, reads=None)
    manual = SimpleNamespace(files=lambda t: sorted(folder.iterdir()), location=lambda t: "ZFW")
    cfg = SimpleNamespace(db_path=tmp_path / "never-opened.db")  # `Store` is stood in for
    with pytest.raises(assemble.DossierAssemblyError, match="1 of 2 call") as err:
        assemble.assemble_one(fin, cfg=cfg, resolver=SimpleNamespace(),  # type: ignore[arg-type]
                              graph=None, manual=manual, out_root=tmp_path / "out",  # type: ignore[arg-type]
                              llm=_TrapLlm())
    assert calls[0].name in str(err.value) and calls[1].name not in str(err.value)
    assert not (tmp_path / "out").exists()
