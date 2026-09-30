"""A forward multiple's ``price_as_of`` travels with the multiple — it is not a panel arrival.

THE FAILURE THAT PRODUCED THIS. #659 gave the dossier forward multiples; BURL's re-assembly then
reddened `test_every_dated_panel_key_is_consciously_classified` with four new dated keys —
`valuation.forward_multiples.value[0..3].price_as_of` — "defaulting to the GATING class with
nobody deciding they should". The guard did exactly its job: a dated field had joined the age
ceiling silently. This file records the decision it asked for.

THE DECISION IS EXCLUSION, AND THE ARGUMENT IS THAT THE DATE IS ALREADY COUNTED. Each row stamps
the close ITS OWN multiple divides by, so a name with four estimate columns emits four copies of
one date — and that date is `stock_info.as_of`, which gates and always did. Both are
`max(bars).bar_date` off the same `store.get_price_history` call: `_refresh_price_and_pe` takes
the max directly, and `compute_price_features` reads `bars[-1]`, using its `reference_date` only
to decide whether to flag the close stale. So the ceiling — which reads the OLDEST panel date —
cannot move whichever way this is classified. The alternative, enumerating `value[0]`…`value[N]`
in `_CLASSIFIED_PANEL_KEYS`, would have reddened on the next name with a different column count
while asserting nothing the export stamp does not already assert.

THE FIXTURE IS REAL AND FROZEN. `tests/fixtures/burl_price_as_of_2026-09-22.json` is the
`stock_info` and `valuation.forward_multiples` nodes lifted verbatim from BURL's 2026-09-30
assembly on `c273ad18` — the run that reddened the guard. It is frozen because these are
VALUE-level pins ($256.85, 2026-09-22, four rows); the corpus sweep below is where the living
fleet is checked, and it asserts only the phrasing-independent invariant.
"""

from __future__ import annotations

import json
import pathlib
import re

from vinci.dossier import freshness as fr

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURE = json.loads(
    (ROOT / "tests" / "fixtures" / "burl_price_as_of_2026-09-22.json").read_text())


#: The exclusion list AS IT STOOD before 2026-09-30, written out rather than derived from the
#: live one by string surgery. A `pattern.replace("|price_as_of", "")` helper — the first cut here
#: — is BLIND to a mutation that RENAMES the term: broadening it to `|as_of` leaves nothing to
#: replace, so "before" and "after" come out equal and a guard that had swallowed every export
#: stamp in the fleet reads as no change. That mutation survived this pin and was caught only by
#: three others, so the reference is a constant now, not a derivation from the thing under test.
_TERMS_BEFORE = frozenset({"own_history", "stock_performance", "gap_date", "filing_date",
                           "maturity", "expected_date", "dated", "points"})


def _without() -> re.Pattern[str]:
    """`_NOT_A_PANEL` as it stood before this change."""
    return re.compile("|".join(sorted(_TERMS_BEFORE)))


def _fleet() -> dict[str, dict]:
    out = {}
    for d in sorted((ROOT / "data" / "dossiers").iterdir()):
        j = d / "dossier.json"
        if j.exists():
            out[d.name] = json.loads(j.read_text()).get("mechanical") or {}
    return out


def _price_as_ofs(node: object, path: str = "") -> list[tuple[str, str]]:
    """Every `price_as_of` in a mechanical record, excluded or not — the population the pins
    below are measured over, harvested independently of the thing under test."""
    out: list[tuple[str, str]] = []
    if isinstance(node, dict):
        for k, v in node.items():
            p = f"{path}.{k}" if path else k
            if k == "price_as_of" and isinstance(v, str):
                out.append((p, v))
            else:
                out.extend(_price_as_ofs(v, p))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            out.extend(_price_as_ofs(v, f"{path}[{i}]"))
    return out


# --- the fixture: the real rows that reddened the guard ----------------------------------------

def test_the_fixture_carries_the_rows_that_reddened_the_guard() -> None:
    """(+) VACUITY CHECK FIRST. Every pin below is worthless if the fixture has no
    `price_as_of` in it, so the population is asserted before anything is concluded from it."""
    found = _price_as_ofs(FIXTURE)
    assert len(found) == 4, f"expected BURL's four estimate rows, got {found}"
    assert {p for p, _ in found} == {
        f"valuation.forward_multiples.value[{i}].price_as_of" for i in range(4)}
    assert {d for _, d in found} == {"2026-09-22"}


def test_a_forward_multiples_price_as_of_is_not_a_panel_arrival() -> None:
    """(+) THE FIX. None of the four reaches `panel_dates`, so none joins the age ceiling."""
    keys = {k for k, _ in fr.panel_dates(FIXTURE)}
    assert not [k for k in keys if "price_as_of" in k or "forward_multiples" in k], (
        f"a value-borne price stamp reached the panel inventory: {sorted(keys)}")


def test_the_export_stamp_for_that_same_close_still_gates() -> None:
    """(+) THE OTHER HALF, and the reason exclusion is safe rather than merely tidy. The date
    removed is a COPY of one that remains — so the ceiling still sees 2026-09-22, and a stale
    price is refused exactly as before. A guard that only proved the removal would be proving
    that a gate got weaker."""
    dates = dict(fr.panel_dates(FIXTURE))
    assert dates.get("stock_info.as_of") == "2026-09-22"
    assert {d for _, d in _price_as_ofs(FIXTURE)} == {dates["stock_info.as_of"]}, (
        "the excluded stamps are no longer a copy of the gating one — the argument for excluding "
        "them was that they duplicate `stock_info.as_of`, and that is now false")
    assert min(dates.values()) == "2026-09-22", (
        "the OLDEST panel date is what the ceiling reads; if the forward rows had been the "
        "oldest, removing them would have moved it")


def test_without_the_exclusion_the_four_keys_come_back() -> None:
    """(−) THE MUTATION, IN THE SUITE. Drop the term and the fixture must produce exactly the
    four keys the real run reddened on — otherwise these pins could pass over a fixture that
    never exercised the exclusion at all."""
    orig = fr._NOT_A_PANEL
    try:
        fr._NOT_A_PANEL = _without()  # type: ignore[assignment]
        keys = {k for k, _ in fr.panel_dates(FIXTURE)}
    finally:
        fr._NOT_A_PANEL = orig  # type: ignore[assignment]
    assert {k for k in keys if "price_as_of" in k} == {
        f"valuation.forward_multiples.value[{i}].price_as_of" for i in range(4)}


# --- the living fleet --------------------------------------------------------------------------

def test_the_exclusion_takes_price_stamps_and_nothing_else_from_the_fleet() -> None:
    """(+) NO COLLATERAL LOSS. Measured over every committed dossier: the ONLY keys the new term
    removes from the panel inventory are `price_as_of` ones. A term that also swallowed, say,
    `stock_info.as_of` would weaken the ceiling on every name at once, and nothing else in this
    file would notice.

    WRITTEN AS "ONLY price stamps", NOT "nothing at all". The first cut asserted the inventory was
    IDENTICAL before and after — true on a fleet that carries no forward multiples, and RED the
    moment the first re-assembled name lands. Measured that way against BURL's real re-assembly it
    failed immediately, which is the whole reason the pin was run against that artifact rather than
    only against the committed corpus."""
    fleet = _fleet()
    assert len(fleet) >= 8, f"corpus too small to mean anything: {sorted(fleet)}"
    orig = fr._NOT_A_PANEL
    without = _without()
    wrong = {}
    try:
        for name, mech in fleet.items():
            after = {k for k, _ in fr.panel_dates(mech)}
            fr._NOT_A_PANEL = without  # type: ignore[assignment]
            before = {k for k, _ in fr.panel_dates(mech)}
            fr._NOT_A_PANEL = orig  # type: ignore[assignment]
            collateral = {k for k in before - after if "price_as_of" not in k}
            if collateral or (after - before):
                wrong[name] = sorted(collateral | (after - before))
    finally:
        fr._NOT_A_PANEL = orig  # type: ignore[assignment]
    assert not wrong, f"the new exclusion moved keys that are not price stamps: {wrong}"


def test_every_committed_price_as_of_matches_its_own_export_stamp() -> None:
    """(+) THE INVARIANT THE EXCLUSION RESTS ON, over whatever the fleet carries. A name whose
    forward rows are struck on a DIFFERENT close than `stock_info.as_of` would be hiding a real
    date behind this exclusion, and the classification would owe a re-argument.

    POPULATION IS PRINTED, NOT ASSUMED: at 2026-09-30 on `c273ad18` no committed dossier carries
    forward multiples (BURL's assembly is not yet merged), so this covers 0 names and the frozen
    fixture is the live instance. It begins covering names as the fleet re-assembles, and is
    written as a sweep for that reason rather than skipped."""
    bad = {}
    for name, mech in _fleet().items():
        stamp = (mech.get("stock_info") or {}).get("as_of")
        off = [(p, d) for p, d in _price_as_ofs(mech) if d != stamp]
        if off:
            bad[name] = (stamp, off)
    assert not bad, (
        f"price stamps that are NOT a copy of their own `stock_info.as_of`: {bad}. The exclusion "
        f"in freshness._NOT_A_PANEL assumes they are duplicates of a date that still gates.")


def test_the_exclusion_is_on_both_sides_of_the_twin() -> None:
    """(+) A TWO-SIDED DELETION PASSES THE PARITY PIN. `test_panel_date_exclusions_py_js_parity`
    compares the lists to each other, so removing `price_as_of` from BOTH stays green while the
    defect returns. This names the term on each side."""
    live = set(fr._NOT_A_PANEL.pattern.split("|"))
    assert live - _TERMS_BEFORE == {"price_as_of"}, (
        f"the exclusion list gained or lost something other than `price_as_of`: "
        f"added={sorted(live - _TERMS_BEFORE)} removed={sorted(_TERMS_BEFORE - live)}")
    js = (ROOT / "frontend" / "views" / "shared" / "dossier.js").read_text()
    m = re.search(r"const _NOT_A_PANEL = /([^/]+)/", js)
    assert m and "price_as_of" in set(m.group(1).split("|")), (
        "dossier.js would count a forward multiple's price stamp as a panel arrival")
