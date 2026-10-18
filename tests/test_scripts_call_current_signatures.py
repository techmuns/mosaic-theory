"""Every script calls the library with the library's CURRENT signatures.

The gate type-checks ``vinci/`` (``mypy --strict vinci``) and never ``scripts/``, so a signature
change in the library could not reach the scripts that call it. Two refresh scripts broke that way
and stayed broken, unseen, until 2026-10-18:
- ``refresh_stock_performance.py`` had called ``mechanical._stock_performance`` without its
  keyword-only ``bench`` since 2026-07-21 (``fefadc5a``), across two later edits of its own;
- ``refresh_concentration.py`` called ``mechanical._concentration`` without ``edgar``, ``http`` and
  ``cik``.
Both raised before writing, so no page was harmed. But the obvious one-line repair of the first —
an old record names it as a way to fix STATE row 32 (7) — wrote a chart figure past the refresh
path's citation guards: TGT's 13.7% → 16.6% under prose still reading "vs SPY +13.7%", with no
refresh entry and the frontend left stale. Both were retired rather than repaired
(`docs/records/2026-10-18-stale-refresh-scripts-retired.md`).

THE CHECK IS NARROW ON PURPOSE: a script's use of the library that no longer fits it.
- ``call-arg``: a call that no longer fits the function it calls;
- ``attr-defined`` / ``import-not-found`` / ``import-untyped`` naming a ``vinci`` module: an import
  of a renamed or removed function or module, the commonest way a script goes stale (code review of
  #746). mypy reports a removed ``vinci`` SUBMODULE as ``import-untyped``, because the package
  itself resolves as installed.
The scripts are not otherwise typed (their other findings are annotation noise in one-off analysis
scripts), and a full type-check would bury this one signal. Missing imports are NOT ignored, or a
removed ``vinci`` module would pass; a third-party module without stubs is filtered out.
"""

from __future__ import annotations

from pathlib import Path

from mypy import api

ROOT = Path(__file__).resolve().parents[1]


def _stale_library_uses(paths: list[str], cache: Path) -> list[str]:
    out, _err, _code = api.run([*paths, "--no-error-summary", "--follow-imports=silent",
                                f"--cache-dir={cache}"])
    found = []
    for line in out.splitlines():
        s = line.rstrip()
        if s.endswith("[call-arg]") or (
                s.endswith(("[attr-defined]", "[import-not-found]", "[import-untyped]"))
                and '"vinci' in s):
            found.append(line)
    return found


def test_no_script_calls_the_library_with_a_stale_signature(tmp_path: Path) -> None:
    errors = _stale_library_uses([str(ROOT / "scripts")], tmp_path / "cache")
    assert errors == [], "\n".join(errors)


def test_the_check_reads_a_stale_call(tmp_path: Path) -> None:
    """POSITIVE: the retired script's own broken call, in a script of its own — the check must
    name it, or the green above proves nothing."""
    script = tmp_path / "stale_call.py"
    script.write_text(
        "from datetime import date\n"
        "from vinci.dossier.mechanical import _stock_performance\n"
        "def run(ident, store) -> None:  # type: ignore[no-untyped-def]\n"
        "    _stock_performance(ident, store, date(2026, 9, 22))\n")
    errors = _stale_library_uses([str(script)], tmp_path / "cache")
    assert len(errors) == 1 and 'Missing named argument "bench"' in errors[0], errors


def test_the_check_reads_an_import_of_a_removed_name_or_module(tmp_path: Path) -> None:
    """POSITIVE: a renamed or removed library function, and a removed library module, are named.
    NEGATIVE: a third-party module without stubs is not a stale use of the library."""
    script = tmp_path / "stale_imports.py"
    script.write_text("from vinci.dossier.mechanical import _no_such_function\n"
                      "import vinci.no_such_module\n"
                      "import some_absent_third_party_package\n")
    errors = _stale_library_uses([str(script)], tmp_path / "cache")
    assert len(errors) == 2, errors
    assert any('Module "vinci.dossier.mechanical" has no attribute "_no_such_function"' in e
               for e in errors), errors
    assert any('"vinci.no_such_module"' in e for e in errors), errors
    assert not any("some_absent_third_party_package" in e for e in errors), errors
