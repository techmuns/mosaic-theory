"""The anchor's EDGAR FCF refuses a capex leg filed negative (PR #881 round 2; audit E1-D12's rule).

`anchor._latest_fcf` subtracted `abs(capex)`, so a capex filed negative was sign-flipped in
silence: WOR's FY2026 capex negated still read FCF 170.206 $M into `ltm_fcf`, which the R2 runway
divides cash by. #875 refuses that leg in the screen's snapshot and the CIQ-empty fallback with
`concepts.negative_leg`; the anchor now reads the same rule, never a second one.

The fixture is WOR's committed companyfacts subset; the negative leg is its real current capex with
the sign flipped (the shape `tests/test_edgar_fallback_provenance_and_sign.py` pins at the other
readers)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from vinci.dossier.anchor import _bridge_inputs

WOR = json.loads((Path(__file__).resolve().parent / "fixtures" / "companyfacts" / "WOR.json")
                 .read_text())
CAPEX = "PaymentsToAcquirePropertyPlantAndEquipment"
ACC = "0001193125-26-325872"  # WOR's FY2026 10-K, filed 2026-07-30


def _negated_capex(end: str = "2026-05-31") -> dict[str, Any]:
    facts: dict[str, Any] = json.loads(json.dumps(WOR))
    for rows in facts["facts"]["us-gaap"][CAPEX]["units"].values():
        for r in rows:
            if r["end"] == end:
                r["val"] = -r["val"]
    return facts


def test_a_capex_filed_negative_leaves_the_anchors_fcf_unknown_naming_it() -> None:
    fcf = _bridge_inputs({}, _negated_capex())["ltm_fcf"]
    assert fcf.value is None, f"a negative capex was netted into ltm_fcf: {fcf.value}"
    source = fcf.source or ""
    assert source.startswith("UNKNOWN — capex filed negative: ") and CAPEX in source, source
    assert ACC in source and "never sign-flipped" in source, source


def test_wors_real_legs_still_give_its_fcf() -> None:
    """NEGATIVE PIN: a capex filed positive, as payments are, is read as before."""
    fcf = _bridge_inputs({}, WOR)["ltm_fcf"]
    assert fcf.value == 170.206 and fcf.basis == "latest FY2026 (not LTM)"
