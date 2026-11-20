"""W65 — CIQ's headline TEV/LTM EBITDA is divided only by a TEV of its own date (2026-11-19).

THE DEFECT (W63, found during W62, 2026-11-18). GOOGL's page read CIQ's 22.9x as dividing
$144,827M, "which reproduces neither pairing". That quotient is no EBITDA: it is CIQ's comps TEV of
2026-10-30 ($3,316,548M) over the Multiples sheet's close of 2026-09-30, two dates 30 days apart,
across GOOGL's fall from $344.08 to about $283.72. `headline_basis` never compared the two dates.
AMZN carries the same 30 days, and there the quotient landed on REPORTED EBITDA: a rent-free reading
on a page whose rent is material.

THE CORPUS (measured 2026-11-19, before any pin was written). On the 26 committed pages at main
5e380efc, 20 carry the block; the comps TEV and the multiple's close are 0 days apart on 16, −1 on
UBER, −3 on LLY (the multiple's close the Monday after a Friday TEV), and 30 on AMZN and GOOGL. On
the 43 frozen blocks under `tests/fixtures/frozen_pages/`, 8 are 12 to 119 days apart, and 6 of the
7 "not_reproduced" readings among the 43 are among them: the "neither pairing" reading was mostly a
date mismatch.

THE FIX. The block reads the multiple's close (the own-history band's date, one cell with the
multiple) and measures a pairing only within `SAME_PRICE_DAYS` of the TEV's date. Beyond it, or with
a date unstated, it STATES both dates and divides nothing: no quotient, no ratio, no pairing.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

from tests.frozen_support import CUT, frozen_doc
from vinci.dossier import anchor_split as sp
from vinci.dossier import ev_ebitda_basis as eb
from vinci.dossier import freshness as fr
from vinci.dossier import render as dr
from vinci.dossier import schemas as ds

ROOT = Path(__file__).resolve().parents[1]
_PAGES = sorted((ROOT / "data" / "dossiers").glob("*/dossier.json"))
_MEASURED = frozenset({"ebitda_plus_rent", "reported", "indistinguishable", "not_reproduced"})


def _mech(raw: dict[str, Any]) -> ds.MechanicalLayer:
    return ds.MechanicalLayer.model_validate(raw["mechanical"])


def _frozen_at(folder: str, ticker: str) -> dict[str, Any]:
    """A page frozen in ``folder`` (a committed fixture, never the living page)."""
    path = ROOT / "tests/fixtures/frozen_pages" / folder / ticker / "dossier.json"
    loaded: dict[str, Any] = json.loads(path.read_text())
    return loaded


def _rebuilt(raw: dict[str, Any]) -> dict[str, Any]:
    """``raw`` with its basis block rebuilt by the head code, the way `valuation_bases_transform`
    rebuilds it under a kept synthesis."""
    out: dict[str, Any] = json.loads(json.dumps(raw))
    got = eb.headline_basis(_mech(raw))
    assert got is not None
    out["mechanical"]["valuation"]["ev_ebitda_basis"] = json.loads(got.model_dump_json())
    return out


# --- the positive pins: a TEV and a multiple a month apart divide nothing ----------------------

def test_googl_states_both_dates_and_divides_nothing() -> None:
    """THE RED, on GOOGL's page as frozen at the cut: 22.9x at the 2026-09-30 close, the comps TEV
    at 2026-10-30. Main divided them ($144,827M, "not_reproduced"); the block now states both dates,
    30 days apart against a 4-day limit, and carries no quotient and no ratio."""
    got = eb.headline_basis(_mech(frozen_doc("GOOGL")))
    assert got is not None
    assert got.reading == "dates_differ", got.reading
    assert (got.multiple_close, got.tev_as_of, got.days_apart, got.days_apart_tolerance) == (
        "2026-09-30", "2026-10-30", 30, eb.SAME_PRICE_DAYS)
    assert (got.implied_denominator, got.ratio_to_reported, got.ratio_to_reported_plus_rent) == (
        None, None, None)
    # the reported figures are facts, not divisions, and stay
    assert (got.multiple, got.tev, got.reported_ltm_ebitda) == (22.9, 3316548.0, 185516.0)
    assert "2026-09-30" in got.line and "2026-10-30" in got.line and "30 days later" in got.line
    assert "144,827" not in got.line and "144827" not in got.model_dump_json()
    assert "reproduces neither" not in got.line


def test_amzn_a_mismatch_that_read_as_reported_measures_nothing() -> None:
    """THE SAME 30 DAYS, the other way to be wrong: AMZN's quotient ($184,739M) sat within 5% of
    reported LTM EBITDA, so main read "reported", a rent-free pairing, on a page whose rent is
    material. It is not measured now."""
    raw = frozen_doc("AMZN")
    assert raw["mechanical"]["valuation"]["ev_ebitda_basis"]["reading"] == "reported"
    assert raw["mechanical"]["valuation"]["lease_basis"]["material"] is True
    got = eb.headline_basis(_mech(raw))
    assert got is not None and got.reading == "dates_differ", got
    assert (got.multiple_close, got.tev_as_of, got.days_apart) == ("2026-09-30", "2026-10-30", 30)
    assert got.implied_denominator is None and got.ratio_to_reported is None


def test_an_older_page_twelve_days_apart_read_neither_and_now_measures_nothing() -> None:
    """THE CORPUS, not a synthetic: IT's page frozen 2026-08-18 (TEV 2026-07-29, multiple's close
    2026-07-17) read "not_reproduced"; the same name at one date (its 2026-11-14 page) reads
    "indistinguishable". Twelve days is past the limit, so the older page measures nothing."""
    old = _frozen_at("2026-08-18", "IT")
    assert old["mechanical"]["valuation"]["ev_ebitda_basis"]["reading"] == "not_reproduced"
    got = eb.headline_basis(_mech(old))
    assert got is not None and got.reading == "dates_differ"
    assert (got.multiple_close, got.tev_as_of, got.days_apart) == ("2026-07-17", "2026-07-29", 12)
    same_date = eb.headline_basis(_mech(_frozen_at("2026-11-14", "IT")))
    assert same_date is not None and same_date.reading == "indistinguishable"


# --- the negative pins: one date, or adjacent sessions, measure exactly as before --------------

@pytest.mark.parametrize(("ticker", "apart", "reading"), [
    ("IT", 0, "indistinguishable"),        # one date
    ("UBER", -1, "ebitda_plus_rent"),      # the multiple's close the next day
    ("LLY", -3, "indistinguishable"),      # a Friday TEV, the Monday's close
])
def test_one_date_or_adjacent_sessions_measure_exactly_as_before(ticker: str, apart: int,
                                                                 reading: str) -> None:
    """NEGATIVE, on three pages as frozen at the cut: the reading, the quotient and both ratios are
    the committed block's, to the digit, and the block now states the two dates it measured on."""
    raw = frozen_doc(ticker)
    committed = raw["mechanical"]["valuation"]["ev_ebitda_basis"]
    got = eb.headline_basis(_mech(raw))
    assert got is not None
    assert got.reading == reading == committed["reading"]
    for key in ("implied_denominator", "ratio_to_reported", "ratio_to_reported_plus_rent",
                "line", "multiple", "tev", "tev_as_of"):
        assert getattr(got, key) == committed[key], key
    assert got.days_apart == apart and got.multiple_close is not None
    assert got.days_apart_tolerance == eb.SAME_PRICE_DAYS


def _it_with_tev_dated(day: str) -> ds.MechanicalLayer:
    """IT's real page with ONE field moved: the comps TEV's date."""
    raw = frozen_doc("IT")
    raw["mechanical"]["valuation"]["implied_expectations"]["tev_as_of"] = day
    return _mech(raw)


def test_the_limit_is_a_boundary_both_ways() -> None:
    """IT's close is 2026-11-11 (a Wednesday). A TEV 4 days either side is one price; 5 days is
    not, whichever side it falls."""
    for day, apart in (("2026-11-15", 4), ("2026-11-07", -4)):
        got = eb.headline_basis(_it_with_tev_dated(day))
        assert got is not None and got.reading == "indistinguishable", (day, got.reading)
        assert got.days_apart == apart
    for day, apart, when in (("2026-11-16", 5, "5 days later"),
                             ("2026-11-06", -5, "5 days earlier")):
        got = eb.headline_basis(_it_with_tev_dated(day))
        assert got is not None and got.reading == "dates_differ", day
        assert got.days_apart == apart and when in got.line and got.implied_denominator is None


@pytest.mark.parametrize("cut", ["no_band", "other_multiple", "undated_band"])
def test_an_undated_multiple_divides_nothing(cut: str) -> None:
    """NEGATIVE for the dividing: a multiple the page cannot date is never shown to be of one date
    with the TEV, so nothing is divided (W62's undated rule). The TEV's side is
    `test_a_tev_date_that_is_no_date_is_stated_never_raised`."""
    raw = frozen_doc("IT")
    v = raw["mechanical"]["valuation"]
    band = next(b for b in v["own_history"]["value"] if "EBITDA" in b["metric"])
    if cut == "no_band":
        v["own_history"]["value"] = [b for b in v["own_history"]["value"]
                                     if "EBITDA" not in b["metric"]]
    elif cut == "other_multiple":
        band["current"] = 11.0
    else:
        band["as_of"] = None
    got = eb.headline_basis(_mech(raw))
    assert got is not None and got.reading == "date_unstated", got
    assert got.implied_denominator is None and got.ratio_to_reported is None
    assert got.days_apart is None
    assert "not shown to be of one date" in got.line


# --- what the readers do with it -----------------------------------------------------------------

def test_a_tev_date_that_is_no_date_is_stated_never_raised() -> None:
    """Review round 0: `mechanical` writes `tev_as_of` = "UNKNOWN" when the comps date cannot be
    corrected. The block states it (`date_unstated`, no quotient), never raises out of the build."""
    got = eb.headline_basis(_it_with_tev_dated("UNKNOWN"))
    assert got is not None and got.reading == "date_unstated", got
    assert got.implied_denominator is None and got.days_apart is None
    assert got.multiple_close == "2026-11-11"
    assert "'UNKNOWN', not a date" in got.line


def test_the_split_names_the_dates_never_a_pairing() -> None:
    """`anchor_split` read GOOGL's 30-day quotient as "neither reported LTM EBITDA nor that plus
    rent". Handed the rebuilt block it names the two dates and measures no EBITDA."""
    raw = _rebuilt(frozen_doc("GOOGL"))
    why = sp.current_ebitda(raw["mechanical"], ex_lease=False, current=22.888839)
    assert isinstance(why, str), why
    assert "not of one date" in why and "2026-09-30" in why and "2026-10-30" in why
    assert "neither reported" not in why and "unstated" not in why


def test_the_split_claims_no_date_mismatch_it_did_not_measure() -> None:
    """Review round 1 (B, finding A): on `date_unstated` the split said the two "are not of one
    date", more than is known — nothing was dated to differ. It says they are not SHOWN to be of
    one date, as the basis line does. B's repro: IT with no own-history band and a TEV dated
    "UNKNOWN"."""
    raw = frozen_doc("IT")
    v = raw["mechanical"]["valuation"]
    v["own_history"]["value"] = [b for b in v["own_history"]["value"]
                                 if "EBITDA" not in b["metric"]]
    v["implied_expectations"]["tev_as_of"] = "UNKNOWN"
    got = eb.headline_basis(_mech(raw))
    assert got is not None and got.reading == "date_unstated"
    v["ev_ebitda_basis"] = json.loads(got.model_dump_json())
    why = sp.current_ebitda(raw["mechanical"], ex_lease=False, current=got.multiple)
    assert isinstance(why, str), why
    assert "not shown to be of one date" in why and "are not of one date" not in why
    # a measured mismatch still says so plainly
    googl = sp.current_ebitda(_rebuilt(frozen_doc("GOOGL"))["mechanical"], ex_lease=False,
                              current=22.888839)
    assert isinstance(googl, str) and "are not of one date" in googl


def test_the_new_date_is_not_a_panel_stamp() -> None:
    """The multiple's close dates a VALUE, like the own-history band's `as_of` the gate already
    skips. Named `multiple_close`, the freshness gate does not collect it, so no page's oldest
    export panel moves: GOOGL's stays the comps TEV's 2026-10-30, never 2026-09-30."""
    raw = _rebuilt(frozen_doc("GOOGL"))
    keys = [k for k, _ in fr.panel_dates(raw["mechanical"])]
    assert "valuation.ev_ebitda_basis.tev_as_of" in keys
    assert not any("multiple_close" in k or "days_apart" in k for k in keys), keys
    before = fr.panel_age(frozen_doc("GOOGL")["mechanical"], "2026-11-19", kind="export")
    after = fr.panel_age(raw["mechanical"], "2026-11-19", kind="export")
    assert before == after


def _brief(raw: dict[str, Any]) -> str:
    doc = ds.Dossier.model_validate(raw)
    return dr.render_markdown(doc).split("# Analysis — full dossier", 1)[0]


def test_the_brief_states_why_the_basis_is_unknown_md_e2e() -> None:
    """REAL committed JSON → render → assertion. GOOGL printed its "neither pairing" line and keeps
    a line, now the dates one; AMZN printed nothing (a "reported" reading is not worth stating) and
    now states why its basis is unknown. A same-date page (IT) is unchanged."""
    for t in ("GOOGL", "AMZN"):
        raw = _rebuilt(frozen_doc(t))
        line = raw["mechanical"]["valuation"]["ev_ebitda_basis"]["line"]
        assert f"- **What CIQ's EV/EBITDA divides:** {line}" in _brief(raw), t
    it = frozen_doc("IT")
    assert _brief(_rebuilt(it)) == _brief(it)


def test_the_web_states_the_same_line_e2e(tmp_path: Path) -> None:
    """THE TWIN: dossier.js prints GOOGL's and AMZN's rebuilt line, from the same JSON."""
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    pages = {}
    for t in ("GOOGL", "AMZN"):
        p = tmp_path / f"{t}.json"
        p.write_text(json.dumps(_rebuilt(frozen_doc(t))))
        pages[t] = str(p)
    dj = (ROOT / "frontend/views/shared/dossier.js").as_uri()
    driver = f"""
const handler = {{ get: () => stub, apply: () => stub, construct: () => ({{}}) }};
const stub = new Proxy(function(){{}}, handler);
for (const g of ["window","document","location"]) {{ try {{ globalThis[g] = stub; }} catch {{}} }}
import {{ readFileSync }} from "node:fs";
const {{ renderDossier }} = await import("{dj}");
const pages = {json.dumps(pages)};
const out = {{}};
for (const t of Object.keys(pages)) {{
  const h = renderDossier(JSON.parse(readFileSync(pages[t])), null, null);
  out[t] = h.includes("not of one date") || h.includes("within which the two are one price");
}}
console.log(JSON.stringify(out));
"""
    res = json.loads(subprocess.run(["node", "--input-type=module", "-e", driver],
                                    capture_output=True, text=True, check=True, cwd=ROOT).stdout)
    assert res == {"GOOGL": True, "AMZN": True}, res


# --- the committed pages -------------------------------------------------------------------------

def test_no_committed_page_is_divided_across_more_than_the_limit_e2e() -> None:
    """A ROSTER WALK, phrasing-free: on every committed page, the head code measures a pairing only
    where the two dates are within the limit, and divides nothing otherwise."""
    seen = 0
    for p in _PAGES:
        got = eb.headline_basis(_mech(json.loads(p.read_text())))
        if got is None:
            continue
        seen += 1
        if got.days_apart is not None and abs(got.days_apart) <= eb.SAME_PRICE_DAYS:
            assert got.reading in _MEASURED and got.implied_denominator is not None, p
        else:
            assert got.reading in eb.DATE_READINGS and got.implied_denominator is None, p
    assert seen >= 15, seen


def test_a_page_built_before_the_fields_round_trips_byte_identical() -> None:
    """PRESENCE PARITY through the one writer: a committed block built before W65 gains no null
    `multiple_close`/`days_apart`/`days_apart_tolerance`, and a rebuilt one writes all three."""
    for p in _PAGES:
        text = p.read_text()
        written = ds.dossier_json(ds.Dossier.model_validate_json(text))
        for key in ("multiple_close", "days_apart", "days_apart_tolerance"):
            assert (f'"{key}"' in written) is (f'"{key}"' in text), (p.parent.name, key)
    rebuilt = ds.dossier_json(ds.Dossier.model_validate(_rebuilt(frozen_doc("GOOGL"))))
    assert '"multiple_close": "2026-09-30"' in rebuilt and '"days_apart": 30' in rebuilt
    assert '"implied_denominator": null' in rebuilt


def test_a_page_built_before_the_fields_sends_the_same_synthesis_facts() -> None:
    """The synthesis request dumps the layer itself (`mech.model_dump(exclude=NOT_SENT)`), not the
    page writer, so `DROP_WHEN_NONE` does not reach it. A committed block built before W65 must
    send no `multiple_close`/`days_apart`/`days_apart_tolerance`, not even as null, or every page
    with the block would prompt differently before it is rebuilt. A rebuilt block sends them.

    PRESENCE PARITY, as its round-trip twin above: a key is sent exactly when the committed block
    carries it. The first cut asserted that NO committed page sends one, which held only while every
    page predated W65; GOOGL's paid rebuild (2026-11-19), the one W65 left waiting, carries them."""
    from vinci.dossier.synthesis import NOT_SENT

    for p in _PAGES:
        raw = json.loads(p.read_text())
        block = (raw["mechanical"].get("valuation") or {}).get("ev_ebitda_basis")
        if block is None:
            continue
        sent = json.dumps(_mech(raw).model_dump(exclude=NOT_SENT), default=str)
        committed = json.dumps(block)
        for key in ("multiple_close", "days_apart", "days_apart_tolerance"):
            assert (f'"{key}"' in sent) is (f'"{key}"' in committed), (p.parent.name, key)
    rebuilt = json.dumps(_mech(_rebuilt(frozen_doc("GOOGL"))).model_dump(exclude=NOT_SENT),
                         default=str)
    assert '"multiple_close": "2026-09-30"' in rebuilt and '"days_apart": 30' in rebuilt


def test_the_readings_worth_stating_are_one_set_in_both_twins() -> None:
    """PARITY: the readings whose line the page prints are one set in render.py and dossier.js
    (the JS cannot import the Python set; `test_duplicate_definitions` records the copy)."""
    import re

    js = (ROOT / "frontend/views/shared/dossier.js").read_text()
    m = re.search(r"const _BASIS_WORTH_STATING = new Set\(\[([^\]]*)\]\)", js)
    assert m is not None
    assert frozenset(re.findall(r'"([^"]+)"', m.group(1))) == dr._BASIS_WORTH_STATING
    assert eb.DATE_READINGS <= dr._BASIS_WORTH_STATING


def test_the_cut_holds_the_pages_these_pins_read() -> None:
    """The pins read the cut, never the living page (a re-export moves the living dates)."""
    for t in ("GOOGL", "AMZN", "IT", "UBER", "LLY"):
        assert (CUT / t / "dossier.json").is_file(), t
