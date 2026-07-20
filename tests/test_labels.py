"""The ONE label resolver — precedence truth-table + the committed-GICS index reader.

Pins: CIQ-GICS wins WHEN PRESENT; official-SIC otherwise; blank/non-numeric SIC → Unknown
(fail-honest, never guessed); ``sector`` is ALWAYS the coarse bucket regardless of GICS (the
stable grouping axis — a manual CIQ pull must never reshuffle the per-sector spread grouping);
the index reader takes ONLY status=="present" industry fields from committed dossier.json trees.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from vinci.labels import committed_gics_index, resolve_label


def test_precedence_truth_table() -> None:
    # SIC only → official-SIC title, source "sic"
    lbl = resolve_label("7372")
    assert lbl.industry == "Services-Prepackaged Software" and lbl.industry_source == "sic"
    assert lbl.sector == "Technology"
    # GICS present → GICS wins the INDUSTRY, source "ciq-gics", ref carried
    lbl = resolve_label("7372", gics="Data Processing and Outsourced Services",
                        gics_source_ref="CIQ Public Company Profile→Primary Industry")
    assert lbl.industry == "Data Processing and Outsourced Services"
    assert lbl.industry_source == "ciq-gics"
    assert lbl.industry_source_ref and "CIQ" in lbl.industry_source_ref
    # …but the SECTOR stays the coarse SIC bucket — the grouping axis never reshuffles
    assert lbl.sector == "Technology"
    # blank / non-numeric / None → Unknown, source "unknown" (never a guess)
    for bad in (None, "", "   ", "abc"):
        lbl = resolve_label(bad)
        assert lbl.industry == "Unknown" and lbl.industry_source == "unknown"
        assert lbl.sector == "Unknown"
    # a whitespace-only gics is NOT present — falls through to SIC
    assert resolve_label("7372", gics="   ").industry_source == "sic"


def test_committed_gics_index_reads_present_only(tmp_path: Path) -> None:
    def write(ticker: str, industry: object) -> None:
        d = tmp_path / ticker
        d.mkdir()
        (d / "dossier.json").write_text(json.dumps({"ticker": ticker, "industry": industry}))

    write("AAA", {"status": "present", "value": "Health Care Equipment", "source_ref": "CIQ x"})
    write("BBB", {"status": "unknown", "value": None, "source_ref": None})   # UNKNOWN → skipped
    write("CCC", None)                                                        # pre-#98 → skipped
    (tmp_path / "DDD").mkdir()                                                # no dossier.json
    idx = committed_gics_index(tmp_path)
    assert idx == {"AAA": {"industry": "Health Care Equipment", "source_ref": "CIQ x"}}
    # a missing root is empty, not an error (the deploy may have no dossiers)
    assert committed_gics_index(tmp_path / "nope") == {}


def test_real_committed_dossiers_all_resolve() -> None:
    """The 10 committed dossiers all carry present CIQ-GICS — the index picks up every one."""
    root = Path(__file__).resolve().parents[1] / "data" / "dossiers"
    if not root.is_dir():
        pytest.skip("no committed dossiers")
    idx = committed_gics_index(root)
    assert len(idx) >= 10
    assert idx["MVST"]["industry"] == "Construction Machinery and Heavy Transportation Equipment"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
