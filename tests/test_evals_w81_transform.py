"""W81's panel transform (`variants.w81_ebitda_names`, RUNBOOKS §n step 2): the identity at a ref
without the change; on real pages (as frozen at the cut, so CI needs no licensed data) it writes
only the basis, at-price and reconciliation lines; each line it writes is exactly what the
candidate's own builder writes from that line's stored block; and a line the ref's code would not
rebuild, words aside, is left as committed.

The builder check on precheck builds (the impact run's $0 builds of every page at both refs, from
one set of inputs) is in the record: the transform on base's build reproduces head's three lines on
all 25 built pages."""
from __future__ import annotations

import json
from typing import Any

import pytest

from tests.frozen_support import frozen_doc
from vinci.dossier import ebitda_recon as er
from vinci.dossier import ev_ebitda_basis as eb
from vinci.dossier.schemas import MechanicalLayer
from vinci.evals import variants as v

PANEL = ("BURL", "CNXC", "LLY", "MCK", "ROST", "SMPL")
LINES = (("valuation", "ev_ebitda_basis", "line"),
         ("valuation", "ev_ebitda_ex_lease_at_price", "line"),
         ("financial_summary", "ebitda_reconciliation", "line"))


def _mech(t: str) -> tuple[dict[str, Any], MechanicalLayer]:
    """The stored layer, validated as it is. The replay's `pre_synthesis_mech` also rehydrates the
    transcript driver rows from the private store, which CI never holds; this transform reads no
    driver row, so the stored layer is its input as much as the replay's is."""
    page = frozen_doc(t)
    return page, MechanicalLayer.model_validate(page["mechanical"])


def _get(d: dict[str, Any], path: tuple[str, ...]) -> Any:
    for k in path:
        d = (d or {}).get(k)  # type: ignore[assignment]
    return d


def _without_lines(d: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = json.loads(json.dumps(d))
    for *parent, key in LINES:
        node = _get(out, tuple(parent))
        if isinstance(node, dict) and key in node:
            node[key] = None
    return out


def test_it_is_registered() -> None:
    assert v.TRANSFORMS["w81_ebitda_names"] is v.w81_ebitda_names
    assert v.W81 == ("w81_ebitda_names",)


def test_the_identity_at_a_ref_without_the_change(monkeypatch: pytest.MonkeyPatch) -> None:
    """(−) A ref with no `ev_ebitda_basis.FOUR_QUARTER` (main) gets its layer back untouched."""
    page, mech = _mech("MCK")
    monkeypatch.delattr(eb, "FOUR_QUARTER")
    assert v.w81_ebitda_names(mech, v.Context(page=page)) is mech


@pytest.mark.parametrize("t", PANEL)
def test_it_writes_only_the_three_lines(t: str) -> None:
    """(+) On each panel page, every one of the three lines the page carries is written; (−)
    nothing else in the layer moves."""
    page, mech = _mech(t)
    before = mech.model_dump(mode="json")
    after = v.w81_ebitda_names(mech, v.Context(page=page)).model_dump(mode="json")
    assert _without_lines(before) == _without_lines(after)
    for path in LINES:
        if _get(before, path) is not None:
            assert _get(after, path) != _get(before, path), (t, path)


@pytest.mark.parametrize("t", PANEL)
def test_each_written_line_is_the_candidate_builders_own(t: str) -> None:
    """(+) The written lines are the builders' own, from the same stored blocks: the basis block's
    (`headline_basis`), the at-price block's (`at_price_line`, the one writer `ex_lease_at_price`
    uses) and the reconciliation's (`_line`)."""
    page, mech = _mech(t)
    new = v.w81_ebitda_names(mech, v.Context(page=page))
    val = new.valuation
    if val.ev_ebitda_basis is not None:
        built = eb.headline_basis(mech)
        assert built is not None and val.ev_ebitda_basis.line == built.line
    at = val.ev_ebitda_ex_lease_at_price
    if at is not None:
        assert at.line == eb.at_price_line(
            price=at.price, price_as_of=at.price_as_of, shares=at.shares,
            shares_basis=at.shares_basis, net_debt=at.net_debt, ltm_ebitda=at.ltm_ebitda,
            ltm_through=at.ltm_through, value=at.value)
    rec = new.financial_summary.ebitda_reconciliation if new.financial_summary else None
    if rec is not None and rec.ciq_ltm is not None:
        assert rec.line == er._line(list(rec.quarters), rec.ciq_ltm, rec.filing_ltm, rec.ltm_gap)


def test_the_at_price_builder_writes_through_the_one_writer() -> None:
    """(+) `ex_lease_at_price` (TJX's frozen page, its frozen companyfacts) writes its line through
    `at_price_line`, so the transform's re-read is the builder's sentence, not a copy of it."""
    from tests.test_ev_ebitda_basis import _fixture, _frozen_doc

    at = eb.ex_lease_at_price(_frozen_doc("TJX").mechanical, _fixture("TJX"))
    assert at is not None
    assert at.line == eb.at_price_line(
        price=at.price, price_as_of=at.price_as_of, shares=at.shares,
        shares_basis=at.shares_basis, net_debt=at.net_debt, ltm_ebitda=at.ltm_ebitda,
        ltm_through=at.ltm_through, value=at.value)


def test_a_line_the_ref_would_not_rebuild_is_left_as_committed() -> None:
    """(−) AMZN's basis block predates W65: this code reads its TEV and multiple 30 days apart and
    writes another reading, so the re-read, words undone, is not the committed line, and the
    transform leaves it exactly as committed."""
    page, mech = _mech("AMZN")
    new = v.w81_ebitda_names(mech, v.Context(page=page))
    assert mech.valuation.ev_ebitda_basis is not None
    assert new.valuation.ev_ebitda_basis == mech.valuation.ev_ebitda_basis
