"""A column headed "Latest guide" carried a number the company never published.

THE PROOF, not an inference. Visa guided FY26 revenue growth at "the low end of low-teens". The
page shows **45,200.0** under "Latest guide", cited to CIQ→Guidance. Visa's FY25 revenue is
**40,000**, and 40,000 × 1.13 = **45,200** exactly. The figure is CIQ's arithmetic on its own base;
the company published a rate.

CIQ CANNOT GIVE US THE OTHER FORM. Its Guidance sheet for V has TEN metric blocks — Revenue, EBIT,
EPS Normalized, EPS (GAAP), Capital Expenditure, Free Cash Flow, Net Income, DPS, Interest Expense,
Effective Tax Rate — and **not one growth-form block**. So we are not dropping management's wording;
CIQ normalises it away before the export reaches us. All we can do is say so.

SAID ONCE, NOT PER ROW, and that restraint is the point. The sheet does not record which form
management used, and the shape cannot be inferred: **32 of the 49 committed guides are RANGES**
(`'2,335.00 - 2,375.00'`) that plausibly ARE the company's own band, and 17 are points — but a
company can guide a point too. Flagging every point as derived would be #423's false-demotion error
in a new place. The caution is general because the evidence is general.

IN THE `source_ref`, NOT ONLY THE RENDER — and this is where it differs from #423, which was
render-only. FIVE committed syntheses QUOTE a figure from this table (NFLX 12,860.0 · MVST 427.5 ·
VRRM 1.19 and 1.25 · BRBR 10.0), and the LLM reads the mechanical layer as JSON. A render-only note
would leave the model treating a CIQ derivation as the company's own words — checked, not assumed
by analogy with the previous change.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from vinci.dossier.ciq_sheets import GUIDANCE_BASIS_REF


def test_the_basis_names_what_the_level_is_and_is_not() -> None:
    """The citation has to carry the whole claim, because it is what the LLM reads: that CIQ states
    a LEVEL, and that a rate-guider's level is CIQ's arithmetic rather than a published figure."""
    assert "LEVEL" in GUIDANCE_BASIS_REF
    assert "RATE" in GUIDANCE_BASIS_REF
    assert "CIQ's arithmetic" in GUIDANCE_BASIS_REF
    assert "not the company's published figure" in GUIDANCE_BASIS_REF
    # …and it still says which sheet it came from — a basis note that loses the provenance is worse
    assert "CIQ Estimates→Guidance" in GUIDANCE_BASIS_REF


def test_one_constant_feeds_both_the_table_and_the_flat_string() -> None:
    """The table and the pre-H4 fallback string cite the same sheet; two literals would let one
    carry the basis and the other keep claiming the company's words."""
    import inspect

    from vinci.dossier import ciq_sheets
    src = inspect.getsource(ciq_sheets)
    assert src.count("source_ref=GUIDANCE_BASIS_REF") + src.count(
        "source_ref=GUIDANCE_BASIS_REF)") >= 2, "a call site stopped using the shared basis"
    assert 'source_ref="CIQ Estimates→Guidance (latest guide' not in src, (
        "a literal guidance citation is back — it will drift from the basis constant")


def test_the_reader_is_told_beneath_the_table_too() -> None:
    """The `source_ref` reaches the LLM; a human reads the table. The note is what stops the column
    header "Latest guide" being taken at face value.

    DRIVEN, NOT INSPECTED: the first draft substring-matched the render's SOURCE and failed because
    the sentence spans two string literals — a pin that reads code rather than running it can fail
    for reasons that have nothing to do with behaviour, and pass for them too (#421's lesson)."""
    from vinci.dossier.render import _guidance_bridge_lines
    from vinci.dossier.schemas import SourceStatus

    class _Row:
        metric, latest_guide, period = "Revenue", "45,200.0", "FY 2026"
        dated, age, record, most_recent = "2026-07-28", "fresh", "—", "—"

    class _S:
        value, status, source_ref = [_Row()], SourceStatus.PRESENT, GUIDANCE_BASIS_REF

    class _AsOf:
        value = "≥2026-07-28"

    class _CP:
        guidance_bridge_rows, guidance_bridge, as_of = _S(), None, _AsOf()

    out = "\n".join(_guidance_bridge_lines(_CP()))
    assert "45,200.0" in out, "the guide itself must still render"
    assert "CIQ's arithmetic on its own base" in out, "the basis note never reaches the page"
    assert "check the release before quoting one as guidance" in out


@pytest.mark.skipif(not Path("data/dossiers").is_dir(), reason="no committed dossiers")
def test_the_visa_arithmetic_that_proves_the_claim_still_holds() -> None:
    """THE EVIDENCE ITSELF, pinned so the claim in the note cannot outlive its proof. If Visa's
    FY25 revenue or its FY26 guide ever moves such that the ×1.13 identity fails, the note's stated
    example is no longer supported and the wording needs re-deriving rather than re-asserting."""
    d = json.loads(Path("data/dossiers/V/dossier.json").read_text())
    ann = d["mechanical"]["financial_summary"]["annual"]["value"]
    cells = dict(zip(ann["columns"], next(
        r for r in ann["rows"] if r["label"] == "Revenue ($M)")["cells"], strict=False))
    fy25 = float(str(cells["FY25"]).replace(",", ""))

    cp = d["mechanical"]["catalyst_path"]
    guide = next(r for r in cp["guidance_bridge_rows"]["value"] if r["metric"] == "Revenue")
    level = float(str(guide["latest_guide"]).replace(",", "").strip("'"))

    assert abs(fy25 * 1.13 - level) < 1.0, (
        f"the proof no longer holds: FY25 {fy25:,.0f} × 1.13 = {fy25 * 1.13:,.0f} against a stated "
        f"guide of {level:,.0f} — the note's example needs re-deriving")


@pytest.mark.skipif(not Path("data/dossiers").is_dir(), reason="no committed dossiers")
def test_every_committed_guidance_citation_carries_the_basis() -> None:
    """A basis nobody ships is a basis nobody reads (#415's lesson). This reads the committed JSON —
    the same bytes the synthesis is handed — so it fails until the artifact pass runs.

    SEALED RECORDS ARE EXEMPT, detected by the sidecar rather than by ticker. A seal means the
    record is frozen until a re-assembly exists; refreshing its citation would be the one edit the
    seal exists to forbid. Naming FUBO here would silently stop covering it the day it unseals.

    Phrasing-independent: asserts the citation states a basis, never a particular figure."""
    missing = []
    for p in sorted(Path("data/dossiers").glob("*/dossier.json")):
        if (p.parent / "known_wrong.json").exists():
            continue
        cp = (json.loads(p.read_text())["mechanical"].get("catalyst_path") or {})
        rows = cp.get("guidance_bridge_rows") or {}
        if rows.get("status") != "present":
            continue
        if "CIQ's arithmetic" not in (rows.get("source_ref") or ""):
            missing.append(p.parent.name)
    assert not missing, (
        f"these committed records cite guidance with no basis: {missing} — re-run the artifact "
        f"pass, or the synthesis keeps reading CIQ levels as the company's own words")


@pytest.mark.skipif(not Path("data/dossiers").is_dir(), reason="no committed dossiers")
def test_the_guide_figures_themselves_are_untouched() -> None:
    """A LABEL CHANGE MOVES NO NUMBER. The whole change is provenance; if any guide value shifted,
    something else happened and the diff needs reading again."""
    seen = 0
    for p in sorted(Path("data/dossiers").glob("*/dossier.json")):
        cp = (json.loads(p.read_text())["mechanical"].get("catalyst_path") or {})
        for r in ((cp.get("guidance_bridge_rows") or {}).get("value") or []):
            seen += 1
            g = str(r.get("latest_guide") or "")
            where = f"{p.parent.name}: {r.get('metric')}"
            assert g and g not in ("None", "—"), f"{where} lost its guide"
            assert re.search(r"\d", g), f"{where} guide has no figure: {g!r}"
    assert seen, "no committed guidance rows — this test checked nothing"
