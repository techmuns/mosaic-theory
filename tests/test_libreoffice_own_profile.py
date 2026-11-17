"""EVERY LIBREOFFICE CONVERSION RUNS UNDER A USER PROFILE OF ITS OWN, REMOVED AFTER (2026-11-17).

VRRM's check build (run `6043fb83`, $5.15) read 1 of its 2 earnings calls: `ciq.read_text` passed
LibreOffice no `-env:UserInstallation`, so every build, precheck and suite conversion on the
machine ran under LibreOffice's ONE default profile, and a second conversion started while one runs
under the same profile is handed to the running instance, which may exit before reading it
(`docs/records/2026-11-17-vrrm-check-build-held.md`). `assemble_all` builds up to 8 names on
threads in one process, so a per-process profile (`vinci.impact.child.own_soffice_profile`) would
not cover it: the profile is per conversion.

Reproduced at $0 on this machine (LibreOffice 26.2.4.2, a generated RTF, 2026-11-17): the second
conversion started 0.0–1.2 s into the first, seven offsets, lost 4 of 14 conversions under the
default profile (each exit 0 with no `.txt` written) and 0 of 14 with a profile each.

The stub pins run everywhere; the concurrent pin runs real LibreOffice on a generated document
(never a licensed call) and skips where LibreOffice is not installed, as on CI.
"""
from __future__ import annotations

import shutil
import subprocess
import threading
import time
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest

from vinci.dossier.ciq import CiqFormat, CiqParseError, classify, libreoffice_convert, read_text

_OLE_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
_FLAG = "-env:UserInstallation="


def _recording_stub(tmp: Path, *, fail: bool = False) -> tuple[Path, Path]:
    """A `soffice` that logs its argument list, writes into the profile it is handed (as
    LibreOffice does on first start), then exits 1 or writes the `.txt` the way LibreOffice
    names it."""
    script, log = tmp / "soffice", tmp / "soffice.log"
    script.write_text(
        "#!/bin/sh\n"
        f'printf "%s\\n" "$*" >> "{log}"\n'
        'out=""; prev=""; prof=""\n'
        'for a; do\n'
        '  [ "$prev" = "--outdir" ] && out=$a\n'
        '  case "$a" in -env:UserInstallation=file://*) prof=${a#-env:UserInstallation=file://};; '
        "esac\n"
        '  prev=$a; src=$a\n'
        "done\n"
        'xcu="$prof/user/registrymodifications.xcu"\n'
        'if [ -n "$prof" ]; then mkdir -p "$prof/user" && : > "$xcu"'
        f' && printf "%s\\n" "$xcu" >> "{log}.made"; fi\n'
        + ('echo "Error: source file could not be loaded" >&2; exit 1\n' if fail else "")
        + 'name=$(basename "$src"); printf "Operator: welcome to the call.\\n" '
        '> "$out/${name%.*}.txt"\n')
    script.chmod(0o755)
    return script, log


def _use(monkeypatch: pytest.MonkeyPatch, script: Path) -> None:
    real = shutil.which

    def which(cmd: str, *a: object, **k: object) -> str | None:
        return str(script) if cmd == "soffice" else real(cmd)

    monkeypatch.setattr(shutil, "which", which)


def _profiles(log: Path) -> list[Path]:
    """Each logged call's profile folder, decoded from its `-env:UserInstallation` URI."""
    out: list[Path] = []
    for line in log.read_text().splitlines():
        arg = next(a for a in line.split(" ") if a.startswith(_FLAG))
        out.append(Path(unquote(urlsplit(arg[len(_FLAG):]).path)))
    return out


def _ole_call(tmp: Path, name: str = "call") -> Path:
    doc = tmp / f"Zinnober Fixture Works Inc, Q1 2027 Earnings Call, Sep 24, 2026 {name}.rtf"
    doc.write_bytes(_OLE_MAGIC + b"\x00" * 504)
    assert classify(doc) is CiqFormat.OLE_DISGUISED
    return doc


def test_each_conversion_is_handed_a_profile_of_its_own_and_it_is_removed_after(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """(+) Two reads: each conversion names `-env:UserInstallation`, the two profiles differ, and
    neither folder is left once the read returns. FAILED before the fix: the logged calls carried
    no `-env:UserInstallation` at all, so every conversion ran under the default profile."""
    script, log = _recording_stub(tmp_path)
    _use(monkeypatch, script)
    doc = _ole_call(tmp_path)
    assert read_text(doc) == "Operator: welcome to the call.\n"
    assert read_text(doc) == "Operator: welcome to the call.\n"
    lines = log.read_text().splitlines()
    assert len(lines) == 2 and all(line.startswith(_FLAG) for line in lines), lines
    first, second = _profiles(log)
    assert first != second
    # each profile really held a file while its conversion ran, so "removed" is the code's doing
    made = [Path(p) for p in Path(f"{log}.made").read_text().splitlines()]
    assert [p.parents[1] for p in made] == [first, second]
    assert not first.exists() and not second.exists()


def test_a_failed_conversion_is_loud_and_its_profile_is_removed_too(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """(+) Exit 1 raises `CiqParseError` naming the exit and LibreOffice's own words, and the
    profile it was handed is gone. (−) `CalledProcessError` never escapes (RA-D11)."""
    script, log = _recording_stub(tmp_path, fail=True)
    _use(monkeypatch, script)
    with pytest.raises(CiqParseError, match=r"LibreOffice exited 1 .*could not be loaded") as err:
        read_text(_ole_call(tmp_path))
    assert not isinstance(err.value, subprocess.CalledProcessError)
    (prof,) = _profiles(log)
    assert not prof.exists()


@pytest.fixture(scope="module")
def generated_ole_calls(tmp_path_factory: pytest.TempPathFactory) -> list[Path]:
    """Four OLE Word documents behind `.rtf` names, as CIQ ships a call — generated here from
    synthetic text by LibreOffice under a profile of the fixture's own, never a licensed call."""
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice is None:
        pytest.skip("LibreOffice not installed")
    root = tmp_path_factory.mktemp("generated-calls")
    body = " ".join(f"Paragraph {i} of a generated fixture call." for i in range(1500))
    src = root / "fixture.rtf"
    src.write_text("{\\rtf1\\ansi{\\fonttbl\\f0 Helvetica;}\\f0 " + body + "}")
    done = libreoffice_convert(soffice, src, "doc", root)
    made = root / "fixture.doc"
    if done.returncode != 0 or not made.exists():
        pytest.skip("LibreOffice could not write the fixture document on this machine")
    calls = []
    for k in range(4):
        call = root / f"Zinnober Fixture Works Inc, Q{k + 1} 2026 Earnings Call, Sep 24, 2026.rtf"
        shutil.copyfile(made, call)
        assert classify(call) is CiqFormat.OLE_DISGUISED
        calls.append(call)
    return calls


def test_four_conversions_at_once_all_read(generated_ole_calls: list[Path]) -> None:
    """(+) Four real conversions, each started 0.15 s after the last (inside the window where the
    shared profile lost a conversion), all read their whole call. FAILED before the fix: under
    the default profile at least one raised "produced no .txt output" or a non-zero exit."""
    got: dict[int, str | Exception] = {}

    def read(k: int) -> None:
        time.sleep(0.15 * k)
        try:
            got[k] = read_text(generated_ole_calls[k])
        except Exception as exc:  # noqa: BLE001 — any failure is a result, never a lost thread
            got[k] = exc

    threads = [threading.Thread(target=read, args=(k,)) for k in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(got) == [0, 1, 2, 3], got  # every thread reported, so none passes by absence
    failed = {k: v for k, v in got.items() if isinstance(v, Exception)}
    assert not failed, failed
    for text in got.values():
        assert isinstance(text, str)
        assert "Paragraph 1499 of a generated fixture call." in text
