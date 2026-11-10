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

import shutil
import subprocess
from pathlib import Path

import pytest

from vinci.config import get_config
from vinci.dossier import ciq_sheets as cs
from vinci.dossier.ciq import CiqBundle, CiqFormat, CiqParseError, classify, read_text
from vinci.dossier.manual_store import LocalFolderStore

_OLE_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"


def _stub(tmp: Path, *, fail_on: str | None = None) -> Path:
    """A `soffice` that exits 1 — for every file, or only for one whose name holds ``fail_on``
    (the others are converted to a one-line `.txt`, as LibreOffice writes it)."""
    script = tmp / "soffice"
    cond = f'case "$6" in *"{fail_on}"*) fail=1;; *) fail=0;; esac' if fail_on else "fail=1"
    script.write_text(
        "#!/bin/sh\n" + cond + "\n"
        'if [ "$fail" = 1 ]; then echo "Error: source file could not be loaded" >&2; exit 1; fi\n'
        'name=$(basename "$6"); printf "Operator: welcome to the call.\\n" '
        '> "$5/${name%.*}.txt"\n')
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
    The build does not stop; the slice holds every other call; the flag names the one left out.
    (−) With every conversion failing, the slice is None and the flag says no call reached it."""
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
