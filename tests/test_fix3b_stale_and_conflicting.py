"""Fix 3b — the fact layer states no buyback leg more than a year old, and one self-funding read.

TWO DEFECTS, both found on the 28 pages committed at the panel's freeze
(`vinci/evals/synthesis_panel.json`'s ``freeze_ref``), never a living page:

(a) A STALE LEG. `capital_allocation._pick` takes a buyback tag's LATEST period however old it is,
    so a filer that stopped using the tag keeps its last value forever. Eleven legs on nine pages
    end 671 to 5,422 days before their page's price date — NFLX's average price $221.88 is from
    2011, before two splits, beside a 2026 close; V's $65.98 straddles its 2015 split; AORT's cash
    and share count are from 2014 — with the date only inside the `source_ref`. Every other leg
    ends at most 361 days before. Such a leg is now NOT STATED: its field is UNKNOWN, and its note
    names the tag and its period.
(b) TWO SELF-FUNDING READS. The survival line closed on a one-input read of the EDGAR fiscal-year
    FCF sign ("FCF-positive → self-funding", "burning cash", "runway not assessable") beside
    `primary_source.self_funding`, the two-input read that replaced it. All 28 pages carried both,
    and eight gave opposite answers. The survival line's FCF leg is DELETED.

END TO END (TEST-LAYER RULE): each pin reads a frozen page, applies this checkout's code through
the harness transform (`vinci/evals/variants.py`, `FIX_3B`), and asserts on the request the model
is sent (`capture_calls`) or on the rendered page (`render._capital_allocation`). Each positive pin
states the defect on the committed page first, so on main — which has neither the transform's rule
nor the shorter survival line — it fails.
"""
from __future__ import annotations

import inspect
import json
import subprocess
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from vinci.dossier import capital_allocation as ca_mod
from vinci.dossier import mechanical
from vinci.dossier.render import _capital_allocation
from vinci.dossier.schemas import MechanicalLayer, Sourced, SourceStatus
from vinci.evals import replay as rp
from vinci.evals import variants as vr
from vinci.evals.capture_child import capture_calls, pre_synthesis_mech

ROOT = Path(__file__).resolve().parents[1]
PANEL = rp.load_panel_file()
FIELDS = ("buyback_cash", "buyback_shares", "buyback_avg_price")
_PAGES: dict[str, dict[str, Any]] = {}


def _frozen() -> list[str]:
    """The pages committed at the freeze, read from git (`git ls-tree <freeze> data/dossiers/`)."""
    out = subprocess.run(["git", "-C", str(ROOT), "ls-tree", "--name-only",
                          f"{PANEL['freeze_ref']}:data/dossiers/"],
                         capture_output=True, text=True)
    if out.returncode != 0:
        pytest.skip("the panel's freeze commit is not in this history")
    return sorted(n for n in out.stdout.split() if n.isupper())


def _page(t: str) -> dict[str, Any]:
    if t not in _PAGES:
        _frozen()
        _PAGES[t] = rp.page_at(t, PANEL["freeze_ref"])
    return _PAGES[t]


def _ctx(t: str) -> tuple[MechanicalLayer, vr.Context]:
    page = _page(t)
    return pre_synthesis_mech(page), vr.Context(page=page)


def _request(t: str, transforms: list[str]) -> str:
    (call,) = capture_calls(_page(t), None, draws=1, transforms=transforms)
    content = call["messages"][0]["content"]
    return content if isinstance(content, str) else str(content[0]["text"])


def _value_in(request: str, key: str) -> Any:
    """The JSON value the request's facts carry under ``key`` (one occurrence, asserted)."""
    head = f'"{key}": '
    assert request.count(head) == 1, (key, request.count(head))
    obj, _ = json.JSONDecoder().raw_decode(request, request.index(head) + len(head))
    return obj


def test_the_frozen_corpus_is_the_28_pages() -> None:
    assert len(_frozen()) == 28


# --------------------------------------------------------------------------- (a) stale legs

#: Every buyback leg on the 28 frozen pages whose period ends more than a year (366 days) before
#: its page's price date: page, field, the committed value, its period end, its age in days.
STALE = [
    ("AMZN", "buyback_cash", 0.0, "2024-12-31", 671),
    ("AORT", "buyback_cash", 5.588, "2014-12-31", 4314),
    ("AORT", "buyback_shares", 585000.0, "2014-12-31", 4314),
    ("BURL", "buyback_avg_price", 52.3, "2015-05-02", 4192),
    ("EPAM", "buyback_avg_price", 283.69, "2023-03-31", 1265),
    ("LLY", "buyback_shares", 0.0, "2021-06-30", 1951),
    ("MCK", "buyback_shares", 13900000.0, "2020-03-31", 2409),
    ("MCK", "buyback_avg_price", 151.23, "2020-09-30", 2226),
    ("NFLX", "buyback_avg_price", 221.88, "2011-12-31", 5422),
    ("V", "buyback_avg_price", 65.98, "2015-06-30", 4133),
    ("VITL", "buyback_shares", 2852770.0, "2019-04-30", 2666),
]


@pytest.mark.parametrize(("t", "field", "value", "end", "days"), STALE)
def test_a_buyback_leg_more_than_a_year_old_is_not_stated(
        t: str, field: str, value: float, end: str, days: int) -> None:
    """(+) The committed page states the old leg; under this code the field is UNKNOWN, its note
    names the tag and the period, and the request the model is sent carries no value there."""
    mech, ctx = _ctx(t)
    committed = getattr(mech.capital_allocation, field)
    assert committed.status is SourceStatus.PRESENT and committed.value == pytest.approx(value)
    assert f"→{end}," in str(committed.source_ref)
    assert mech.stock_info is not None and mech.stock_info.as_of is not None
    assert (mech.stock_info.as_of - date.fromisoformat(end)).days == days
    now = getattr(vr.current_buybacks(mech, ctx).capital_allocation, field)
    assert now.status is SourceStatus.UNKNOWN and now.value is None
    assert str(now.note).startswith("no current figure — the latest ")
    assert f"→{end}, " in str(now.note) and f"ends {days} days before the price date" in str(
        now.note)
    sent = _value_in(_request(t, ["current_buybacks"]), field)
    assert sent["value"] is None and sent["status"] == "unknown" and sent["note"] == now.note


def test_every_leg_inside_the_year_is_stated_as_committed() -> None:
    """(−) On all 28 pages every other leg keeps its value, source and status — the closest to the
    line is ROST's share count, 361 days before its price date, five inside it."""
    stale = {(t, f) for t, f, *_ in STALE}
    kept = 0
    for t in _frozen():
        mech, ctx = _ctx(t)
        ca, out = mech.capital_allocation, vr.current_buybacks(mech, ctx).capital_allocation
        assert ca is not None and out is not None
        for f in FIELDS:
            a, b = getattr(ca, f), getattr(out, f)
            if (t, f) in stale or a.status is not SourceStatus.PRESENT:
                continue
            assert (b.status, b.value, b.source_ref) == (a.status, a.value, a.source_ref), (t, f)
            kept += 1
    assert kept == 36   # the PRESENT legs on the 28 pages (47) less the 11 above
    rost, ctx = _ctx("ROST")
    shares = rost.capital_allocation.buyback_shares   # type: ignore[union-attr]
    assert rost.stock_info is not None and rost.stock_info.as_of is not None
    assert (rost.stock_info.as_of - date(2025, 11, 1)).days == 361
    assert "→2025-11-01," in str(shares.source_ref)
    assert vr.current_buybacks(rost, ctx).capital_allocation.buyback_shares == shares  # type: ignore[union-attr]


def test_a_mismatch_note_names_only_legs_still_stated() -> None:
    """(+) MCK's, LLY's and VITL's cash carried a PERIOD MISMATCH against a share count that is
    no longer stated; the clause goes with it. (−) EPAM's cash and share count are both current
    (78 and 259 days before), and their mismatch stays."""
    for t in ("MCK", "LLY", "VITL"):
        mech, ctx = _ctx(t)
        assert "PERIOD MISMATCH" in str(mech.capital_allocation.buyback_cash.note)  # type: ignore[union-attr]
        cash = vr.current_buybacks(mech, ctx).capital_allocation.buyback_cash  # type: ignore[union-attr]
        assert cash.status is SourceStatus.PRESENT and cash.note is None, t
        page = "\n".join(_capital_allocation(vr.current_buybacks(mech, ctx)))
        assert "PERIOD MISMATCH" not in page, t
    epam, ctx = _ctx("EPAM")
    out = vr.current_buybacks(epam, ctx).capital_allocation
    assert out is not None and "PERIOD MISMATCH — cash covers" in str(out.buyback_cash.note)
    assert out.buyback_shares.note == epam.capital_allocation.buyback_shares.note  # type: ignore[union-attr]


def test_the_rendered_page_prints_no_pre_split_average() -> None:
    """(+) THE HUMAN SURFACE. NFLX's page printed "$221.88" — a 2011 average, before the 2015 7:1
    and 2025 10:1 splits — as its buyback cost per share; V's printed a 2015 figure across its 4:1
    split. Under this code each prints the absence and its period instead."""
    for t, figure, end in (("NFLX", "$221.88", "2011-12-31"), ("V", "$65.98", "2015-06-30")):
        mech, ctx = _ctx(t)
        assert figure in "\n".join(_capital_allocation(mech)), t
        page = "\n".join(_capital_allocation(vr.current_buybacks(mech, ctx)))
        assert figure not in page and "no current figure" in page and end in page, t


def test_an_average_refused_beside_old_legs_says_they_are_not_current() -> None:
    """(+) AORT states no average, and its refusal named the 2014 legs as "the only available
    legs"; those legs are not stated now, so it says so. (−) A page whose legs are ABSENT (FUBO)
    keeps "absent"."""
    aort, ctx = _ctx("AORT")
    assert "the only available legs" in str(aort.capital_allocation.buyback_avg_price.note)  # type: ignore[union-attr]
    note = str(vr.current_buybacks(aort, ctx).capital_allocation.buyback_avg_price.note)  # type: ignore[union-attr]
    assert "the cash leg is not current" in note and "2014" not in note
    fubo, fctx = _ctx("FUBO")
    assert vr.current_buybacks(fubo, fctx) is fubo
    assert "the cash leg is absent" in str(fubo.capital_allocation.buyback_avg_price.note)  # type: ignore[union-attr]


def test_the_transform_rebuilds_every_committed_field_through_the_builders_code(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """THE HARNESS PARSE, PINNED: with the staleness line lifted, `buyback_legs` over
    `buyback_point`'s reading of each committed field rebuilds all three fields exactly — value,
    source, note and status — on all 28 pages. So the transform is the builder's code on the
    page's own points, and the only thing it adds is the date test."""
    monkeypatch.setattr(ca_mod, "CURRENT_DAYS", 10**6)
    for t in _frozen():
        mech, _ = _ctx(t)
        ca = mech.capital_allocation
        assert ca is not None and mech.stock_info is not None and mech.stock_info.as_of
        got = ca_mod.buyback_legs(vr.buyback_point(ca.buyback_cash, scale=1_000_000.0),
                                  vr.buyback_point(ca.buyback_shares),
                                  vr.buyback_point(ca.buyback_avg_price),
                                  as_of=mech.stock_info.as_of)
        assert got == (ca.buyback_cash, ca.buyback_shares, ca.buyback_avg_price), t


def test_current_buybacks_moves_only_its_fields_and_is_idempotent() -> None:
    moved = []
    for t in _frozen():
        mech, ctx = _ctx(t)
        out = vr.current_buybacks(mech, ctx)
        assert vr.current_buybacks(out, ctx) == out, t
        assert out.model_copy(update={"capital_allocation": mech.capital_allocation}) == mech, t
        assert out.capital_allocation is not None and mech.capital_allocation is not None
        rest = {k: v for k, v in out.capital_allocation if k not in FIELDS}
        assert rest == {k: v for k, v in mech.capital_allocation if k not in FIELDS}, t
        if out != mech:
            moved.append(t)
    assert moved == ["AMZN", "AORT", "BURL", "EPAM", "LLY", "MCK", "NFLX", "V", "VITL"]


def test_current_buybacks_is_the_identity_at_a_ref_without_the_rule(
        monkeypatch: pytest.MonkeyPatch) -> None:
    mech, ctx = _ctx("NFLX")
    monkeypatch.delattr(ca_mod, "buyback_legs")
    assert vr.current_buybacks(mech, ctx) is mech


def test_current_buybacks_refuses_rather_than_guesses() -> None:
    """No price date to date the legs against, or a stated leg whose source is not the span the
    builder writes: refused (`TransformError`), never a guessed date."""
    mech, ctx = _ctx("NFLX")
    assert mech.stock_info is not None
    undated = mech.model_copy(update={"stock_info": mech.stock_info.model_copy(
        update={"as_of": None})})
    with pytest.raises(vr.TransformError, match="no price date"):
        vr.current_buybacks(undated, ctx)
    ca = mech.capital_allocation
    assert ca is not None
    odd = mech.model_copy(update={"capital_allocation": ca.model_copy(update={
        "buyback_cash": ca.buyback_cash.model_copy(update={"source_ref": "EDGAR FY2026"})})})
    with pytest.raises(vr.TransformError, match="not the companyfacts span"):
        vr.current_buybacks(odd, ctx)


# ------------------------------------------------------------------- (b) one self-funding read

#: The eight frozen pages whose two reads gave opposite answers: the survival leg, then the
#: two-input read's own word.
CONFLICT = [
    ("AORT", "FCF-positive → self-funding", "MIXED"),
    ("EPAM", "FCF-positive → self-funding", "MIXED"),
    ("GOOGL", "FCF-positive → self-funding", "MIXED"),
    ("MVST", "FCF-positive → self-funding", "MIXED"),
    ("WERN", "FCF-negative → burning cash", "YES"),
    ("WLK", "FCF-negative → burning cash", "YES"),
    ("IT", "FCF sign UNKNOWN — runway not assessable", "YES"),
    ("LLY", "FCF sign UNKNOWN — runway not assessable", "YES"),
]
LEG_WORDS = ("→ self-funding", "burning cash", "runway not assessable", "FCF sign")


@pytest.mark.parametrize(("t", "leg", "word"), CONFLICT)
def test_the_request_carries_one_self_funding_read(t: str, leg: str, word: str) -> None:
    """(+) The committed page's survival line answers the self-funding question against the
    two-input read; under this code it carries no answer, and the request the model is sent holds
    the two-input read alone."""
    mech, ctx = _ctx(t)
    assert leg in str(mech.quality.survival_capacity.value)
    assert mech.primary_source is not None
    assert str(mech.primary_source.self_funding.value).startswith(f"self-funding: {word} ")
    sent = _request(t, ["survival_read"])
    for key in ("survival_capacity", "survival"):
        line = str(_value_in(sent, key)["value"])
        assert not any(w in line for w in LEG_WORDS), (t, key, line)
    assert sent.count("self-funding (two-input read): ") == 1


def test_the_leverage_leg_and_the_fcf_sign_are_untouched() -> None:
    """(−) On every page the survival transform reaches, the line is its committed leverage leg
    byte for byte, the source names no FCF sign, and `quality.fcf_sign` and the two-input read are
    the committed ones."""
    reached = 0
    for t in _frozen():
        mech, ctx = _ctx(t)
        try:
            out = vr.survival_read(mech, ctx)
        except vr.TransformError:
            continue
        reached += 1
        committed = str(mech.quality.survival_capacity.value)
        assert out.quality.survival_capacity.value == committed.split(" | ")[0], t
        assert "FCF" not in str(out.quality.survival_capacity.source_ref), t
        assert out.quality.fcf_sign == mech.quality.fcf_sign
        assert out.primary_source == mech.primary_source
        assert vr.survival_read(out, ctx) == out, t
    assert reached == 25   # FUBO, ORKA and TECX need the CIQ net debt the layer does not carry


def test_the_survival_line_reads_no_fcf_sign() -> None:
    """The builder's own signature: no FCF-sign parameter, so no caller can hand it one."""
    assert "fcf_sign" not in inspect.signature(mechanical._survival_capacity).parameters
    lev = Sourced.present(1.2, source_ref="CIQ Net Debt ÷ CIQ LTM EBITDA")
    line = mechanical._survival_capacity(lev, Sourced[str].unknown(note="no guide"))
    assert line.value == "net-debt/EBITDA 1.2x (CIQ)"


def test_survival_read_still_hands_a_pre_3b_ref_its_fcf_sign(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """The harness loads this file against BOTH arms' code, and main's builder takes the FCF sign:
    it is passed exactly when the ref's `_survival_capacity` asks for it."""
    seen: list[Any] = []

    def main_shape(net_lev: Any, adj_lev: Any, fcf_sign: Any, *, net_debt: Any = None) -> Any:
        seen.append(fcf_sign)
        return Sourced.present("net-debt/EBITDA 0.9x (CIQ) | FCF-positive → self-funding",
                               source_ref="CIQ Net Debt ÷ CIQ LTM EBITDA (EDGAR XBRL breadth "
                                          "fallback) + FCF sign (survival capacity)")
    mech, ctx = _ctx("MCK")
    monkeypatch.setattr(mechanical, "_survival_capacity", main_shape)
    vr.survival_read(mech, ctx)
    assert seen == [mech.quality.fcf_sign]


def test_fix3b_names_its_transforms() -> None:
    assert vr.FIX_3B == ("survival_read", "current_buybacks")
    assert set(vr.FIX_3B) <= set(vr.TRANSFORMS)


# ---------------------------------------- the gap test's FCF-sign item, after #927 merged (#930)

FCF_ITEM = "the FCF sign (quality.fcf_sign)"
OLD_FCF_ITEM = "the FCF sign behind the survival line's runway leg"


def test_no_gap_entry_names_a_survival_line_leg() -> None:
    """(+) #927's gap test named its FCF-sign item "the FCF sign behind the survival line's runway
    leg"; this PR deletes that leg, so the item names its field instead. On all 28 frozen pages no
    entry names the survival line or a runway, and the two pages whose FCF sign is UNKNOWN (IT,
    LLY) carry the field's name — in the request the model is sent, too."""
    named = []
    for t in _frozen():
        mech, ctx = _ctx(t)
        for g in vr.gap_types(mech, ctx).disclosure_gaps or []:
            assert "runway" not in g.item and "survival line" not in g.item, (t, g.item)
            if "quality.fcf_sign" in g.fields:
                named.append((t, g.item))
    assert named == [("IT", FCF_ITEM), ("LLY", FCF_ITEM)]
    sent = _request("LLY", ["gap_types"])
    assert f'"item": "{FCF_ITEM}"' in sent and "runway leg" not in sent


def test_the_fcf_sign_entry_keeps_its_type_and_basis() -> None:
    """(−) Only the words moved: LLY's entry has the type, fields and basis the frozen M-GAP gold
    recorded at #927's 601d2f7e (`vinci/evals/synthesis_gap_types.json`), which keeps the old item
    text on purpose — it is the gold's own vocabulary, and `metrics.GAP_ITEM_WORDS` keys on it. A
    future re-freeze of the gap types takes the new wording."""
    from vinci.evals import metrics as mt
    frozen = json.loads(mt.GAP_TYPES_FILE.read_text())["pages"]["LLY"]["gaps"]
    (old,) = [g for g in frozen if "quality.fcf_sign" in g["fields"]]
    assert old["item"] == OLD_FCF_ITEM and OLD_FCF_ITEM in mt.GAP_ITEM_WORDS
    mech, ctx = _ctx("LLY")
    (new,) = [g for g in vr.gap_types(mech, ctx).disclosure_gaps or []
              if "quality.fcf_sign" in g.fields]
    assert new.item == FCF_ITEM
    assert (new.fields, new.type, new.basis) == (old["fields"], old["type"], old["basis"])
