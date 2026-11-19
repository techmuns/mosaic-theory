"""W62 (STATE §5.0 row 10 (b)) — the R1 screening anchor withholds a value on a stale multiple.

W50 (#1114) made the anchor price its band's CURRENT multiple, the band's latest close, which can
sit weeks before the page's price date. Since W62 the anchor asks whether that current is today's
BY ITS BAND'S OWN CADENCE (`anchor.close_age`):

* CIQ's history (Multiples sheet: quarter columns plus a partial column at the export date) is
  stale past 30 days before the page's price date (W61's limit). GOOGL's 2026-09-30 close is 42
  days old, BRBR's 2026-09-21 close 32.
* The ex-lease history (one observation per fiscal quarter, at CIQ's pricing date) is stale only
  once the page's price date is past the date its NEXT observation could be priced. TJX's
  2026-08-28 observation is 75 days old and the newest it could carry: not stale.

A stale current withholds the VALUE, never the recipe (coordinator, 2026-11-18): no screen value
and no split, the dated multiple on show with the median beside it, a `multiple_stale` flag and
the reason; `applicable`, the recipe and the tier untouched, so the record gate stays asleep.
Never re-struck at the page's close (that makes the value at current EBITDA the stock's quote
exactly — the 2026-11-13 fence), never the median in its place.

Built from the REAL frozen pages (the cut at 4889ddba, whose dates are main's at 89b15307 on all
26) and their committed companyfacts fixtures; a negative cut from a real page says so.

Positive: exactly BRBR and GOOGL are stale on the cut, and the check alone withheld BRBR's value;
31 days refuses on CIQ's history; an ex-lease page past its next observation's due date refuses;
an undated close or page refuses; GOOGL's real CIQ bridge assembles no value; the flag survives the
R4 reason; the mid-cycle sentence says R1 WOULD price the median; both renderers print no screen
value and say why. Negative: every other page carries no flag; 30 days prices; TJX at 75 days and
at its due date prices, and its split (and PARR's) carries no stale notice; `applicable` stays True
and the record gate lets GOOGL's R3 and BRBR's R1 records through; a page dated by its reference
date alone is measured against it.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from tests.frozen_support import CUT, frozen_doc
from tests.stale_gate_support import stale_gate_held_open
from vinci.dossier import anchor as anc
from vinci.dossier import propose
from vinci.dossier import render as dr
from vinci.dossier.anchor_split import STALE_CLOSE_DAYS
from vinci.dossier.schemas import Dossier

ROOT = Path(__file__).resolve().parents[1]
FACTS = ROOT / "tests" / "fixtures" / "companyfacts"
NOW = datetime(2026, 11, 18, tzinfo=UTC)
#: The pages of the cut whose R1 band's current is not today's (measured 2026-11-18; main 89b15307
#: and #1119's b4e484f6 carry the same dates): both CIQ's history, by age in days.
STALE_ON_THE_CUT = {"BRBR": 32, "GOOGL": 42}
#: TJX's ex-lease history at the cut: its last observation's balance sheet, the longest of its
#: last four quarters, the slowest of their pricing lags, and the date a newer one could be priced.
TJX_DUE = date(2026, 12, 29)   # 2026-08-01 + 91 + 59


def _copy(doc: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = json.loads(json.dumps(doc))
    return out


def _derive(doc: dict[str, Any], **kw: Any) -> anc.Anchor:
    facts = json.loads((FACTS / f"{doc['ticker']}.json").read_text())
    return anc.compute_anchor(doc["mechanical"], facts=facts, computed_at=NOW, **kw)


def _band(doc: dict[str, Any]) -> dict[str, Any]:
    band = anc.r1_multiple_band(doc["mechanical"]).band
    assert isinstance(band, dict), doc["ticker"]
    return band


def _with_close(t: str, close: str | None) -> dict[str, Any]:
    """``t``'s frozen page with its R1 band's close moved (or removed): no committed page carries
    an undated close or one at the limit, so these negatives are cut from a real page."""
    d = _copy(frozen_doc(t))
    band = _band(d)
    if close is None:
        band.pop("as_of")
    else:
        band["as_of"] = close
    return d


def _with_page_date(t: str, day: date) -> dict[str, Any]:
    """``t``'s frozen page with its stored close's date moved to ``day`` (cut from the real one)."""
    d = _copy(frozen_doc(t))
    d["mechanical"]["stock_info"]["as_of"] = day.isoformat()
    return d


def _stale(a: anc.Anchor) -> bool:
    return anc.DQ_STALE_MULTIPLE in (a.data_quality or "")


# --- (+/−) the corpus ------------------------------------------------------------------------
def test_the_cut_finds_exactly_brbr_and_googl_stale() -> None:
    """(+) Every page of the cut whose anchor reaches the multiple leg is measured: BRBR and GOOGL,
    both CIQ's history, carry the flag and no screen value. (−) Every other one carries no flag —
    TJX, PARR, ROST, TGT and BURL among them, ex-lease histories 56 to 79 days old whose next
    observation is not due yet. The counts are held: a sweep that measured nothing is suspect."""
    stale, fresh = {}, []
    for folder in sorted(CUT.iterdir()):
        if not (folder / "dossier.json").is_file():
            continue
        doc = frozen_doc(folder.name)
        a = _derive(doc)
        if a.multiple is None:   # stopped before the multiple leg (NCNO: the R2 hint)
            continue
        if _stale(a):
            assert a.anchor_base_value_per_share is None and a.gap_split is None, folder.name
            assert a.anchor_ev_ebit is None and a.anchor_base_value_per_share_diluted is None
            stale[folder.name] = anc.multiple_close_age(_band(doc)["as_of"],
                                                        anc.price_as_of(doc["mechanical"]))
        else:
            fresh.append(folder.name)
    assert stale == STALE_ON_THE_CUT
    assert len(fresh) == 19, fresh   # 21 anchors reach the multiple leg at the cut
    assert {"TJX", "PARR", "ROST", "TGT", "BURL"} <= set(fresh)


def test_brbr_withholds_its_value_and_keeps_its_recipe() -> None:
    """(+) BRBR (CIQ's history, 32 days): no screen value and no split; the 6.4x current kept on
    show with its close and the median beside it; the flag, one detail line and the reason. (−)
    `applicable`, the recipe and every input stay as they were: staleness is not inapplicability.
    Held open, the same page prices — the check alone withheld the value."""
    doc = frozen_doc("BRBR")
    band = _band(doc)
    a = _derive(doc)
    assert a.anchor_base_value_per_share is None and a.gap_split is None
    assert a.anchor_base_value_per_share_diluted is None and a.anchor_ev_ebit is None
    assert a.applicable is True and a.recipe_hint == anc.RECIPE_R1
    assert a.multiple is not None and a.multiple.statistic == anc.MULTIPLE_CURRENT
    assert a.multiple.value == pytest.approx(band["current"]) and a.multiple.as_of == "2026-09-21"
    assert a.multiple.median == pytest.approx(band["median"])
    assert _stale(a)
    line = [x for x in a.data_quality_detail if x.startswith(anc.DQ_STALE_MULTIPLE)]
    assert len(line) == 1 and "2026-09-21" in line[0] and "2026-10-23" in line[0]
    assert "32 days apart" in line[0]
    why = a.reason or ""
    for part in ("valuation.own_history", "2026-09-21", "32 days", f"{STALE_CLOSE_DAYS}-day limit",
                 "never priced in its place", "R1 still applies",
                 "a CIQ export carries a close within the limit"):
        assert part in why, (part, why)
    with stale_gate_held_open():
        held = _derive(doc)
    assert held.anchor_base_value_per_share is not None and held.gap_split is not None
    for k in ("margin", "multiple", "ltm_revenue", "d_and_a", "net_debt", "shares_outstanding"):
        assert getattr(a, k) == getattr(held, k), k


# --- (+/−) CIQ's history: 30 days ------------------------------------------------------------
def test_thirty_days_prices_and_thirty_one_withholds_on_ciqs_history() -> None:
    """(+/−) LLY (CIQ's history, its page's price date 2026-11-11): a close 30 days before
    prices, 31 days before withholds the value and keeps `applicable`."""
    pdate = date(2026, 11, 11)
    at = _derive(_with_close("LLY", (pdate - timedelta(days=30)).isoformat()))
    assert at.anchor_base_value_per_share is not None and not _stale(at)
    past = _derive(_with_close("LLY", (pdate - timedelta(days=31)).isoformat()))
    assert past.anchor_base_value_per_share is None and past.applicable is True and _stale(past)
    assert "31 days before the page's price date" in (past.reason or "")


# --- (+/−) the ex-lease history: its next observation's due date -----------------------------
def test_tjx_at_75_days_is_the_newest_its_history_could_carry() -> None:
    """(−) TJX's 2026-08-28 observation, 75 days before its page's 2026-11-11: the next quarter
    ends about 2026-10-31 and is priced up to 59 days later, so no export could hold a newer one.
    Priced, split, no flag — the refusal a flat clock would make here is false by construction."""
    doc = frozen_doc("TJX")
    a = _derive(doc)
    assert a.anchor_base_value_per_share is not None and a.gap_split is not None
    assert not _stale(a)
    nxt = anc.ex_lease_next_due(doc["mechanical"])
    assert nxt is not None and nxt[0] == TJX_DUE
    assert "balance sheet 2026-08-01" in nxt[1] and "91 days" in nxt[1] and "59 days" in nxt[1]


def test_an_ex_lease_page_past_its_due_date_withholds_and_on_it_prices() -> None:
    """(+/−) TJX with its stored close moved to its due date prices; one day past it, a newer
    quarter could be in the history, so the value is withheld, `applicable` kept, and the reason
    and the md lease sentence say why. (Cut from the real page.)"""
    on = _derive(_with_page_date("TJX", TJX_DUE))
    assert on.anchor_base_value_per_share is not None and not _stale(on)
    past_doc = _with_page_date("TJX", TJX_DUE + timedelta(days=1))
    past = _derive(past_doc)
    assert past.anchor_base_value_per_share is None and past.applicable is True and _stale(past)
    why = past.reason or ""
    assert "valuation.lease_basis.ex_lease_band" in why and "2026-12-29" in why
    assert "a CIQ export carries the newer quarter" in why
    past_doc["anchor"] = json.loads(past.model_dump_json(
        exclude=anc.anchor_absent_fields(past) or None))
    md = dr.render_markdown(Dossier.model_validate(past_doc))
    assert "R1 prices no value on it: a newer quarter than that current could be in the" in md
    assert "R1 prices that history's current multiple" not in md


@pytest.mark.parametrize(("t", "age", "due"), [("TJX", 75, "2026-12-29"),
                                               ("PARR", 79, "2026-11-25")])
def test_the_splits_notice_follows_the_anchors_verdict(t: str, age: int, due: str) -> None:
    """(−) W61's split notice ran on a flat 30-day clock and called these ex-lease closes stale
    while the anchor priced on them. It now states the anchor's verdict (coordinator, 2026-11-18:
    "the split's stale notice follows the anchor's cadence verdict"): no notice, and the arithmetic
    says why — the next quarterly observation is not due yet."""
    a = _derive(frozen_doc(t))
    gs = a.gap_split
    assert a.anchor_base_value_per_share is not None and gs is not None
    assert gs.close_age_days == age and gs.stale_close is False and gs.stale_line is None
    assert "not stale by its history's cadence: the next quarterly observation is due by " \
        f"{due}" in gs.arithmetic[-1]


def test_the_cadence_reads_every_observation_the_export_carries() -> None:
    """(+) WLK's last year holds one unpriced quarter: read over priced observations only, its
    "quarter" would be 184 days and its due date half a year late. Every observation counts."""
    nxt = anc.ex_lease_next_due(frozen_doc("WLK")["mechanical"])
    assert nxt is not None and "92 days" in nxt[1] and nxt[0] == date(2027, 2, 26)


def test_an_ex_lease_history_too_short_to_state_its_cadence_withholds() -> None:
    """(+) Fewer than five observations cannot state a quarter and a lag: the age is not shown to
    be today's, so the value is withheld (TJX cut to its last four, from the real page)."""
    d = _copy(frozen_doc("TJX"))
    lb = d["mechanical"]["valuation"]["lease_basis"]
    lb["observations"] = lb["observations"][-4:]
    a = _derive(d)
    assert a.anchor_base_value_per_share is None and a.applicable is True and _stale(a)
    assert "cadence is not measurable" in (a.reason or "")
    # review round 0: the remedy and the row's note name the short history, never missing dates
    assert "its history carries five dated observations" in (a.reason or "")
    assert a.value_withheld is not None and "cannot be dated" not in a.value_withheld
    assert "needs five dated observations" in a.value_withheld


def test_an_undated_last_observation_never_lets_an_older_one_set_the_due_date() -> None:
    """Review round 0: the band's current is the LAST observation; with its pricing date gone the
    cadence is not measurable (withheld), never measured from the quarter before it, which would
    put the due date a quarter early (TJX, cut from the real page)."""
    d = _copy(frozen_doc("TJX"))
    d["mechanical"]["valuation"]["lease_basis"]["observations"][-1]["pricing_date"] = None
    assert anc.ex_lease_next_due(d["mechanical"]) is None


def test_a_last_observation_without_its_balance_sheet_date_never_sets_an_older_due_date() -> None:
    """Review round 1 (/code-review high, PR #1122): the same for the last observation's balance
    sheet date. Dropped from the pairs, it let the quarter before set the due date (TJX's would
    read 2026-09-30, and its fresh 2026-08-28 multiple would be withheld on 2026-11-11). The
    cadence is not measurable instead, and the value is withheld for that reason, said so."""
    d = _copy(frozen_doc("TJX"))
    d["mechanical"]["valuation"]["lease_basis"]["observations"][-1]["balance_sheet_date"] = None
    assert anc.ex_lease_next_due(d["mechanical"]) is None


# --- (+/−) undated -----------------------------------------------------------------------------
def test_an_undated_close_or_page_withholds_and_a_reference_date_dates_the_page() -> None:
    """(+) An undated close, or a page that states no price date at all, cannot be shown to be
    today's: withheld, never priced as if fresh. (−) A page with no stored close but a reference
    date is measured against that date, the date its inputs are cut at."""
    undated = _derive(_with_close("LLY", None))
    assert undated.anchor_base_value_per_share is None and _stale(undated)
    assert "cannot be shown to be today's" in (undated.reason or "")
    d = _copy(frozen_doc("LLY"))
    day = date.fromisoformat(d["mechanical"]["stock_info"].pop("as_of"))
    assert _stale(_derive(d)) and _derive(d).anchor_base_value_per_share is None
    dated = _derive(d, reference_date=day)
    assert dated.anchor_base_value_per_share is not None and not _stale(dated)


def test_multiple_close_age_reads_every_shape_the_close_arrives_in() -> None:
    """A committed close is ISO text; a layer dumped in python mode at assembly may hand a date."""
    p = date(2026, 11, 11)
    assert anc.multiple_close_age("2026-08-28", p) == 75
    assert anc.multiple_close_age(date(2026, 8, 28), p) == 75
    assert anc.multiple_close_age(datetime(2026, 8, 28, tzinfo=UTC), p) == 75
    assert anc.multiple_close_age("2026-11-14", p) == -3
    assert anc.multiple_close_age("Nov-02-2026", p) is None
    assert anc.multiple_close_age(None, p) is None
    assert anc.multiple_close_age("2026-08-28", None) is None


# --- (+/−) GOOGL: its real bridge, its R3 record, the R4 reason --------------------------------
def _googl_on_its_bridge(monkeypatch: pytest.MonkeyPatch) -> tuple[anc.Anchor, anc.Anchor]:
    """GOOGL's anchor as a fresh assembly writes it on the CIQ-bridge cut (its D&A is the
    workbook's; `tests/test_anchor_assembly_ciq_bridge.py`), the operator's R3 tag kept: (as
    written, held open). Its close there is 2026-09-21 against a 2026-10-23 price date, 32 days."""
    from tests import test_anchor_assembly_ciq_bridge as cb
    from vinci.dossier import assemble as asm
    from vinci.dossier import ciq_balance, recipe_proposal
    from vinci.dossier.ciq import CiqBundle

    ciq = cb._ciq("GOOGL")
    monkeypatch.setattr(ciq_balance, "extract", lambda _bundle, _ticker: ciq)
    page = cb.CUT["GOOGL"]["page"]

    def assemble() -> anc.Anchor:
        fresh = asm._assembly_anchor(page["mechanical"], facts=cb.CUT["GOOGL"]["companyfacts"],
                                     bundle=CiqBundle.from_files("GOOGL", []), ticker="GOOGL",
                                     computed_at=cb.T0, reference_date=cb.REF)
        kept, _notes = anc.preserve_operator_tag(cb._committed("GOOGL"),
                                                 recipe_proposal.propose(page, fresh))
        return kept

    got = assemble()
    with stale_gate_held_open():
        held = assemble()
    return got, held


def test_googl_withholds_its_value_and_its_r3_record_still_writes(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """(+) No screen value on GOOGL's real bridge, the flag and its detail line; held open, the
    same bridge prices. (−) `applicable` stays True and the R3 tag stays, so the record gate lets
    GOOGL's R3 record through — STATE row 10's coupling stays asleep."""
    from tests import test_anchor_assembly_ciq_bridge as cb

    got, held = _googl_on_its_bridge(monkeypatch)
    assert got.anchor_base_value_per_share is None and got.applicable is True
    assert got.recipe_hint == held.recipe_hint == "R3_forward_pe"
    assert _stale(got) and anc.DQ_VENDOR_BRIDGE in (got.data_quality or "")
    assert any(x.startswith(anc.DQ_STALE_MULTIPLE) and "32 days apart" in x
               for x in got.data_quality_detail)
    assert held.anchor_base_value_per_share is not None
    doc = _copy(cb.CUT["GOOGL"]["page"])
    doc["anchor"] = json.loads(got.model_dump_json(exclude=anc.anchor_absent_fields(got) or None))
    propose.check_tier_agreement(doc, "R3_forward_pe")   # raises on a refusal


def test_brbrs_r1_record_still_writes() -> None:
    """(−) BRBR's page with the anchor a backfill now writes: no screen value, `applicable` True,
    so writing its R1 record is not refused."""
    d = _copy(frozen_doc("BRBR"))
    a = _derive(d)
    assert a.anchor_base_value_per_share is None
    d["anchor"] = json.loads(a.model_dump_json(exclude=anc.anchor_absent_fields(a) or None))
    propose.check_tier_agreement(d, anc.RECIPE_R1)   # raises on a refusal


def test_the_flag_survives_the_r4_proposal_rewriting_the_reason() -> None:
    """(+) On the cut's GOOGL page (42 days) the machine's R4 proposal holds and REPLACES R1's
    reason (`recipe_proposal.propose`): the flag and its detail line keep the cause on the page."""
    from vinci.dossier import recipe_proposal

    doc = frozen_doc("GOOGL")
    got = recipe_proposal.propose(doc, _derive(doc))
    assert got.recipe_hint == recipe_proposal.RECIPE_R4
    assert "today's multiple" not in (got.reason or "")
    assert _stale(got)
    assert any(x.startswith(anc.DQ_STALE_MULTIPLE) and "42 days apart" in x
               and "2026-09-30" in x for x in got.data_quality_detail)


# --- (+/−) the mid-cycle sentence never says R1 prices a withheld value -----------------------
def test_the_midcycle_sentence_says_r1_would_price_where_the_value_is_withheld() -> None:
    """(+) GOOGL (stale) and LLY with no usable current: the sentence says R1 WOULD price the
    median and why no value is shown. (−) LLY as committed keeps W50's words."""
    googl = _derive(frozen_doc("GOOGL")).midcycle_gap
    assert googl is not None
    assert ("R1 would price that median at the multiple the name trades on today, though no "
            "screen value is priced here (its current multiple, the 2026-09-30 close, is not "
            "today's), so an R1 value would answer") in googl.read
    lly = _copy(frozen_doc("LLY"))
    _band(lly)["current"] = None
    none = _derive(lly).midcycle_gap
    assert none is not None and "(its history carries no usable current multiple)" in none.read
    priced = _derive(frozen_doc("LLY")).midcycle_gap
    assert priced is not None and "R1 prices that median at the multiple" in priced.read
    assert "would" not in priced.read.split("R1 reverts to.")[1][:60]


# --- (+/−) both renderers, end to end ----------------------------------------------------------
def _page_with_derived_anchor(t: str) -> dict[str, Any]:
    d = _copy(frozen_doc(t))
    a = _derive(d)
    d["anchor"] = json.loads(a.model_dump_json(exclude=anc.anchor_absent_fields(a) or None))
    return d


def _md_screen(md: str) -> str:
    i = md.index("### Screening context")
    ends = [x for x in (md.find("\n## ", i), md.find("\n### ", i + 5)) if x > 0]
    return md[i:min(ends)] if ends else md[i:]


def test_the_markdown_prints_no_screen_value_and_says_why() -> None:
    """(+) BRBR: the method row reads applicable, the multiple row stays, the screen-value row
    reads "not priced" with its cause (operator: "Approve, add the row"), no split, the flag and the
    reason print. (−) SMPL keeps its screen value and W50's lease
    sentence. Neither block carries a signed percentage (the fence's own shape)."""
    blk = _md_screen(dr.render_markdown(Dossier.model_validate(_page_with_derived_anchor("BRBR"))))
    assert "| Method | mid-cycle margin × today's multiple of its own history | applicable |" in blk
    assert "| Current multiple, own history | 6.4x | latest close 2026-09-21" in blk
    assert ("| Screen value / share | not priced | the multiple is the 2026-09-21 close, 32 days "
            "before the page's close; a fresh CIQ export clears it |") in blk
    assert "spot-independent" not in blk and "How the screen value splits" not in blk
    assert f"**data_quality: {anc.DQ_STALE_MULTIPLE}**" in blk
    assert "32 days before the page's price date" in blk and "R1 still applies" in blk
    smpl = dr.render_markdown(Dossier.model_validate(_page_with_derived_anchor("SMPL")))
    assert "Screen value / share" in _md_screen(smpl)
    assert "R1 prices that history's current multiple" in smpl
    for md in (blk, _md_screen(smpl)):
        assert not re.search(r"[+-]\d+(\.\d+)?%", md)


def test_the_web_prints_no_screen_value_and_says_why_collapsed_and_open() -> None:
    """(+) BRBR on `renderDossier`: applicable, the screen-value row reading "not priced" with its
    cause, the flag and the reason; the block holds no <details>, so collapsed and force-open are
    one. (−) SMPL keeps its priced row."""
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    driver = r"""
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import path from "node:path";
const stub = new Proxy(function(){}, { get: () => stub, apply: () => stub, construct: () => ({}) });
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const dj = pathToFileURL(path.resolve("frontend/views/shared/dossier.js")).href;
const { renderDossier } = await import(dj);
const pages = JSON.parse(readFileSync(process.argv[2], "utf8"));
const out = {};
for (const [k, doc] of Object.entries(pages)) out[k] = renderDossier(doc, null);
process.stdout.write(JSON.stringify(out));
"""
    pages = {t: _page_with_derived_anchor(t) for t in ("BRBR", "SMPL")}
    tmp = ROOT / ".pytest_w62_tmp"
    tmp.mkdir(exist_ok=True)
    try:
        (tmp / "drv.mjs").write_text(driver)
        (tmp / "pages.json").write_text(json.dumps(pages))
        res = subprocess.run(["node", str(tmp / "drv.mjs"), str(tmp / "pages.json")], cwd=ROOT,
                             capture_output=True, text=True, check=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    out: dict[str, str] = json.loads(res.stdout)

    def block(h: str) -> str:
        i = h.index('<div class="uw-screen">')
        depth = 0
        for m in re.finditer(r"<div\b|</div>", h[i:]):
            depth += 1 if m.group(0) == "<div" else -1
            if depth == 0:
                return h[i:i + m.end()]
        raise AssertionError("unclosed screening block")

    brbr = block(out["BRBR"])
    assert ">applicable<" in brbr and "spot-independent" not in brbr
    assert "Screen value / share" in brbr and ">not priced<" in brbr
    assert "the multiple is the 2026-09-21 close, 32 days before the page&#39;s close" in brbr
    assert "uw-screen-split" not in brbr
    assert f"data_quality: {anc.DQ_STALE_MULTIPLE}" in brbr
    assert "32 days before the page&#39;s price date" in brbr
    assert "<details" not in brbr
    assert "Screen value / share" in block(out["SMPL"])


# --- (+/−) the "not priced" row (operator 2026-11-18: "Approve, add the row") ------------------
_FENCE = ("spot", "upside", "discount", "price")


def _googl_priceable() -> dict[str, Any]:
    """The cut's GOOGL page with the anchor `compute_anchor` writes when its CIQ read supplies the
    D&A EDGAR lacks — the one the committed page records it read (28,540 $M over the twelve months
    to 2026-09-30, Financials_Annual sha 482debf275), as the real `CiqFacts` type the bridge
    returns. R1 can then price GOOGL, and its 42-day close withholds the value."""
    from vinci.dossier.ciq_balance import CiqFact, CiqFacts

    d = _copy(frozen_doc("GOOGL"))
    da = d["anchor"]["d_and_a"]
    wb = ("Alphabet Inc NasdaqGS GOOGL Financials_Annual.xls", "482debf275")
    fact = CiqFact(value=da["value"], unit="$M", basis="depreciation and amortisation, LTM "
                   "(cash-flow statement)", source=da["source"], workbooks=(wb,), period="LTM",
                   period_end=date(2026, 9, 30))
    ciq = CiqFacts(ticker="GOOGL", as_of=None, source_file=wb[0], source_sha256=wb[1],
                   facts={"d_and_a": fact}, checks=[], failures=[])
    a = _derive(d, ciq=ciq)
    assert a.d_and_a is not None and a.d_and_a.value == da["value"]
    d["anchor"] = json.loads(a.model_dump_json(exclude=anc.anchor_absent_fields(a) or None))
    return d


GOOGL_NOTE = ("the multiple is the 2026-09-30 close, 42 days before the page's close; a fresh "
              "CIQ export clears it")


def test_googl_keeps_the_screen_value_row_not_priced_with_its_cause_on_the_markdown() -> None:
    """(+) END TO END on GOOGL's page: R1 applies, its value is withheld, and the main table keeps
    a "Screen value / share" row reading "not priced", its note the cause and what clears it —
    dates and days, never the stock's quote or a difference from it."""
    d = _googl_priceable()
    a = Dossier.model_validate(d).anchor
    assert a is not None and a.applicable is True and a.anchor_base_value_per_share is None
    assert a.value_withheld == GOOGL_NOTE
    blk = _md_screen(dr.render_markdown(Dossier.model_validate(d)))
    assert f"| Screen value / share | {anc.SCREEN_VALUE_WITHHELD} | {GOOGL_NOTE} |" in blk
    assert "spot-independent" not in blk
    for bad in _FENCE:
        assert bad not in GOOGL_NOTE.lower(), bad
    assert not re.search(r"[+-]\d+(\.\d+)?%", blk)


def test_a_priced_or_unpriceable_page_carries_no_not_priced_row() -> None:
    """(−) SMPL (priced) prints its value; GOOGL held open (priced) prints its value; GOOGL with no
    CIQ read (R1 cannot price it: no D&A) carries no withheld note — the row names staleness only
    where staleness is the one thing withholding the value. The note is ABSENT, never null, where
    unset, so committed pages round-trip."""
    smpl = _derive(frozen_doc("SMPL"))
    assert smpl.value_withheld is None
    assert "value_withheld" not in smpl.model_dump_json(
        exclude=anc.anchor_absent_fields(smpl) or None)
    with stale_gate_held_open():
        held = Dossier.model_validate(_googl_priceable())
    assert held.anchor is not None and held.anchor.anchor_base_value_per_share is not None
    assert held.anchor.value_withheld is None
    blk = _md_screen(dr.render_markdown(held))
    assert "| Screen value / share | $" in blk and anc.SCREEN_VALUE_WITHHELD not in blk
    bare = _derive(frozen_doc("GOOGL"))
    assert bare.applicable is False and _stale(bare) and bare.value_withheld is None


def test_an_ex_lease_note_names_its_next_observations_due_date() -> None:
    """(+) TJX one day past its due date: the note names the next quarterly observation's due
    date, not a day count against a flat limit."""
    a = _derive(_with_page_date("TJX", TJX_DUE + timedelta(days=1)))
    assert a.value_withheld == (
        "the multiple is the 2026-08-28 close, and its history's next quarterly observation was "
        "due by 2026-12-29, before the page's close of 2026-12-30; a CIQ export carrying that "
        "quarter clears it")


def test_googl_keeps_the_screen_value_row_not_priced_on_the_web() -> None:
    """(+) The web twin (`anchorInner`) on the same GOOGL page: the row reads "not priced" with the
    note, written once in anchor.py; collapsed and force-open alike (no <details> in the block)."""
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    driver = r"""
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import path from "node:path";
const stub = new Proxy(function(){}, { get: () => stub, apply: () => stub, construct: () => ({}) });
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const dj = pathToFileURL(path.resolve("frontend/views/shared/dossier.js")).href;
const { renderDossier } = await import(dj);
process.stdout.write(JSON.stringify(renderDossier(JSON.parse(readFileSync(process.argv[2], "utf8")),
                                                  null)));
"""
    tmp = ROOT / ".pytest_w62_row_tmp"
    tmp.mkdir(exist_ok=True)
    try:
        (tmp / "drv.mjs").write_text(driver)
        (tmp / "page.json").write_text(json.dumps(_googl_priceable()))
        res = subprocess.run(["node", str(tmp / "drv.mjs"), str(tmp / "page.json")], cwd=ROOT,
                             capture_output=True, text=True, check=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    html: str = json.loads(res.stdout)
    i = html.index('<div class="uw-screen">')
    blk = html[i:html.index("</table>", i)]
    row = re.search(r"<tr><td>Screen value / share</td><td[^>]*>([^<]*)</td><td[^>]*>([^<]*)</td>",
                    blk)
    assert row is not None, blk[-600:]
    assert row.group(1) == "not priced"
    assert row.group(2) == GOOGL_NOTE.replace("'", "&#39;")
    assert "spot-independent" not in blk and "<details" not in blk
