"""THE DRAWDOWN AT THE ANCHOR, AND SINCE (2026-11-04) — `DrawdownAnchor`.

The drawdown block re-read the screen's 180-day gap-down window at every build, so a page rebuilt
more than 180 days after a drop no longer named the event its underwrite was written on. SMPL is
the case: its committed page (2026-08-18) names the 2026-04-09 (-18.1%) and 04-10 (-11.5%)
gap-downs and the FY26 outlook 8-K that followed; a rebuild at the 2026-10-16 reference starts its
window on 04-19, and `vinci dossier precheck --ticker SMPL` listed both fields as regressions.

Now a name with an underwrite record (else a follow) keeps two DATED parts beside the rolling
window: the 180 days ending on its anchor date, read only from closes on or before it and 8-Ks
filed by it, so no later build changes it; and the days since the anchor to the page's price date.

Fixtures are real: SMPL's Polygon closes 2025-08-01..2026-11-03, its EDGAR 8-K rows and the three
documents the reader fetches for 8-K 0001702744-26-000010, recorded 2026-11-04
(`tests/fixtures/anchored_drawdown`); the committed pages and `data/followed.json`; and this
code's own $0 build of SMPL (`tests/fixtures/prespend/2026-11-04/SMPL-mechanical-anchored.json`).
"""
from __future__ import annotations

import json
import shutil
import subprocess
from datetime import date
from pathlib import Path
from typing import Any, cast

import pytest

from vinci.dossier import prespend
from vinci.dossier.mechanical import AnchorDate, _drawdown_cause, drawdown_anchor_date
from vinci.dossier.schemas import Dossier, DrawdownCause, SourceStatus, dossier_json
from vinci.edgar.asof import AsOfEdgar
from vinci.edgar.client import EdgarClient, Filing
from vinci.netcache import CachedHttp, HttpError
from vinci.schemas.data_record import DataRecord, Identity
from vinci.schemas.market import PriceBar
from vinci.screens.assemble import build_price_record

_ROOT = Path(__file__).resolve().parent
_FIX = _ROOT / "fixtures" / "anchored_drawdown"
_BARS = [PriceBar(**json.loads(line))
         for line in (_FIX / "SMPL-bars.jsonl").read_text().splitlines() if line.strip()]
_EDGAR = json.loads((_FIX / "SMPL-edgar.json").read_text())
_ROWS = [Filing(**r) for r in _EDGAR["filings"]]
_BUILT = _ROOT / "fixtures" / "prespend" / "2026-11-04" / "SMPL-mechanical-anchored.json"
_FROZEN_PAGE = _ROOT / "fixtures" / "frozen_pages" / "2026-08-18" / "SMPL" / "dossier.json"
_ACC = "0001702744-26-000010"
_UNDERWRITE = AnchorDate("underwrite", date(2026, 8, 5), "scenarios/SMPL.json underwrite_date")
_IDENT = Identity(internal_id="SEC-0001702744-SMPL", issuer_id="ISS-0001702744",
                  cik="0001702744", ticker="SMPL", mic="XNAS", exchange="Nasdaq",
                  eod_symbol="SMPL", name="The Simply Good Foods Company")


class _Edgar:
    """EDGAR's 8-K rows for SMPL as recorded, served the way `recent_filings` serves them."""

    def __init__(self, rows: list[Filing]) -> None:
        self.rows = rows

    def recent_filings(self, cik: int | str, *, forms: tuple[str, ...] = ("8-K",),
                       since: date | None = None) -> list[Filing]:
        return [f for f in self.rows
                if f.form in forms and (since is None or f.filing_date >= since)]


class _Http:
    """The recorded documents; anything else is a fetch the fixture never saw, refused loud."""

    def __init__(self) -> None:
        self.docs: dict[str, str] = _EDGAR["documents"]

    def get_text(self, url: str, **_kw: Any) -> str:
        if url not in self.docs:
            raise HttpError(f"not in the fixture: {url}")
        return self.docs[url]

    def get_json(self, url: str, **_kw: Any) -> Any:
        raise HttpError(f"not in the fixture: {url}")


def _record(ref: date) -> DataRecord:
    """SMPL's data record at ``ref``, by the screen's own constructor on the real closes."""
    return build_price_record(_IDENT, price_bars=[b for b in _BARS if b.bar_date <= ref],
                              benchmark_bars=[], reference_date=ref, staleness_days=5)


def _build(ref: date, cut: date, anchor: AnchorDate | None,
           rows: list[Filing] | None = None) -> tuple[DrawdownCause, list[str]]:
    """The block as `assemble_mechanical` builds it: closes, the page's cut, the anchor, and the
    rolling window ending on the cut (review of #906 — the production combination)."""
    edgar = cast(EdgarClient, AsOfEdgar(cast(EdgarClient, _Edgar(rows or _ROWS)), cut))
    return _drawdown_cause(_record(ref), edgar, cast(CachedHttp, _Http()),
                           bars=[b for b in _BARS if b.bar_date <= cut], cut=cut, anchor=anchor,
                           current_end=cut)


def _js(model: Any) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(model.model_dump_json()))


# ─── the positive pin: SMPL keeps its April event at today's dates ────────────────────────────

def test_smpl_keeps_its_april_gap_downs_and_outlook_at_the_underwrite() -> None:
    """At a rebuild on today's dates (screen reference 2026-10-16, price date 2026-11-03) the
    rolling window has lost the April drops; the at-the-underwrite part still names both, with
    their moves, the 8-K they are read from, and that 8-K's FY26 outlook exhibit."""
    dc, flags = _build(date(2026, 10, 16), date(2026, 11, 3), _UNDERWRITE)
    assert flags == []
    assert dc.gap_down_dates.status is SourceStatus.UNKNOWN  # the rolling window: gone
    assert dc.anchor is not None and dc.anchor.on == "2026-08-05"
    at = dc.anchor.at_anchor
    assert (at.start, at.end) == ("2026-02-06", "2026-08-05")
    assert at.gap_down_dates.value == ["2026-04-09", "2026-04-10"]
    assert [g.on for g in at.gaps] == ["2026-04-09", "2026-04-10"]
    assert [round(g.move, 3) for g in at.gaps] == [-0.181, -0.115]
    assert {g.accession for g in at.gaps} == {_ACC}
    assert at.revised_guidance.status is SourceStatus.PRESENT
    assert _ACC in str(at.revised_guidance.source_ref)
    assert "-18.1%" in str(at.shape.value) and "-11.5%" in str(at.shape.value)
    # since the underwrite: no single day of -10% or worse to 2026-11-03
    assert dc.anchor.since is not None
    assert (dc.anchor.since.start, dc.anchor.since.end) == ("2026-08-06", "2026-11-03")
    assert dc.anchor.since.gap_down_dates.status is SourceStatus.UNKNOWN
    assert dc.anchor.since.shape.status is SourceStatus.PRESENT


def test_a_dated_parts_moves_cite_the_closes_they_are_read_from() -> None:
    """(Codex P2 on #906) The dated shape states each drop's move ("-18.1%"), read from the stored
    closes, beside its 8-K cause; its source_ref must name BOTH — an EDGAR-only ref left the move
    bound to a filing that cannot state it."""
    dc, _ = _build(date(2026, 10, 16), date(2026, 11, 3), _UNDERWRITE)
    assert dc.anchor is not None
    ref = str(dc.anchor.at_anchor.shape.source_ref)
    assert "-18.1%" in str(dc.anchor.at_anchor.shape.value)
    assert "EOD closes on or before 2026-08-05" in ref
    assert "EDGAR 8-K item codes" in ref and "filed by 2026-08-05" in ref


def test_no_later_build_changes_the_at_anchor_part() -> None:
    """Read only from what was knowable on the anchor date, the part is the same at every later
    price date — the committed page's 2026-08-17, the 10-16 screen run, and 2026-11-03."""
    parts = [_js(_build(date(2026, 8, 14), cut, _UNDERWRITE)[0].anchor.at_anchor)  # type: ignore[union-attr]
             for cut in (date(2026, 8, 17), date(2026, 10, 16), date(2026, 11, 3))]
    assert parts[0] == parts[1] == parts[2]


# ─── the negatives ─────────────────────────────────────────────────────────────────────────────

def test_a_name_with_no_anchor_builds_exactly_as_before() -> None:
    """With no anchor (no underwrite, no follow), the dated parts add nothing: the block is
    byte-identical to the rolling window read alone — no `anchor` key."""
    ref, cut = date(2026, 8, 14), date(2026, 8, 17)
    edgar = cast(EdgarClient, AsOfEdgar(cast(EdgarClient, _Edgar(_ROWS)), cut))
    before, _ = _drawdown_cause(_record(ref), edgar, cast(CachedHttp, _Http()),
                                bars=[b for b in _BARS if b.bar_date <= cut], current_end=cut)
    after, _ = _build(ref, cut, None)
    assert after.model_dump_json() == before.model_dump_json()
    assert "anchor" not in _js(after)
    assert _js(after)["gap_down_dates"]["value"] == ["2026-04-09", "2026-04-10"]


def test_the_anchor_leaves_the_rolling_window_as_it_was() -> None:
    """The dated parts are added beside the current window; they never move it."""
    ref, cut = date(2026, 10, 16), date(2026, 11, 3)
    plain = _js(_build(ref, cut, None)[0])
    anchored = _js(_build(ref, cut, _UNDERWRITE)[0])
    anchored.pop("anchor")
    assert anchored == plain


def test_a_gap_after_the_anchor_is_only_in_since() -> None:
    """Anchored the day BEFORE the 04-09 drop, both April drops happened after the thesis: they
    are in the since part and not in the part at the anchor."""
    anchor = AnchorDate("followed", date(2026, 4, 8), "data/followed.json SMPL followed_since")
    dc, _ = _build(date(2026, 10, 16), date(2026, 11, 3), anchor)
    assert dc.anchor is not None and dc.anchor.since is not None
    assert "2026-04-09" not in (dc.anchor.at_anchor.gap_down_dates.value or [])
    assert dc.anchor.since.start == "2026-04-09"
    assert dc.anchor.since.gap_down_dates.value == ["2026-04-09", "2026-04-10"]


def test_an_8k_filed_after_the_anchor_never_enters_the_part_at_the_anchor() -> None:
    """THE LOOKAHEAD PIN. The real 04-09 8-K, re-dated to 04-11 — after a 04-10 anchor. On the
    anchor date the drops were known and their cause was not: the part says "no company filing"
    and names no exhibit. The control: the same rows read at the price date DO find it, so the
    cut, not the data, is what keeps it out."""
    late = [f.model_copy(update={"filing_date": date(2026, 4, 11)}) if f.accession == _ACC else f
            for f in _ROWS]
    anchor = AnchorDate("underwrite", date(2026, 4, 10), "scenarios/SMPL.json underwrite_date")
    dc, _ = _build(date(2026, 4, 30), date(2026, 4, 30), anchor, rows=late)
    assert dc.anchor is not None
    at = dc.anchor.at_anchor
    april = [g for g in at.gaps if g.on in ("2026-04-09", "2026-04-10")]
    assert [g.on for g in april] == ["2026-04-09", "2026-04-10"]  # the drops were knowable
    assert [g.cause for g in april] == ["no company filing", "no company filing"]
    assert _ACC not in {f.accession for f in at.filings}
    assert _ACC not in str(at.revised_guidance.source_ref)
    # the control: the rolling window, read at the 04-30 price date, finds the re-dated filing
    assert _ACC in {f.accession for f in dc.filings}
    assert _ACC in str(dc.revised_guidance.source_ref)


def test_an_anchor_after_the_price_date_anchors_nothing() -> None:
    """A page priced before its underwrite was written has no underwrite to anchor at."""
    dc, _ = _build(date(2026, 7, 31), date(2026, 7, 31), _UNDERWRITE)
    assert dc.anchor is None


def test_a_follow_that_ended_anchors_nothing() -> None:
    ended = AnchorDate("followed", date(2026, 3, 1), "data/followed.json SMPL followed_since",
                       until=date(2026, 9, 1))
    assert _build(date(2026, 10, 16), date(2026, 11, 3), ended)[0].anchor is None
    still = AnchorDate("followed", date(2026, 3, 1), "data/followed.json SMPL followed_since",
                       until=date(2026, 12, 1))
    assert _build(date(2026, 10, 16), date(2026, 11, 3), still)[0].anchor is not None


def test_no_session_after_the_anchor_leaves_since_absent() -> None:
    anchor = AnchorDate("followed", date(2026, 11, 3), "data/followed.json SMPL followed_since")
    dc, _ = _build(date(2026, 10, 16), date(2026, 11, 3), anchor)
    assert dc.anchor is not None and dc.anchor.since is None
    assert "since" not in _js(dc.anchor)


def test_a_degraded_feed_at_the_anchor_is_unknown_and_flagged() -> None:
    """An unreadable filing index at the anchor is UNKNOWN with its own flag, never "no company
    filing" — the same rule the rolling window follows."""
    class _Down(_Edgar):
        def recent_filings(self, cik: int | str, *, forms: tuple[str, ...] = ("8-K",),
                           since: date | None = None) -> list[Filing]:
            raise HttpError("403")
    edgar = cast(EdgarClient, AsOfEdgar(cast(EdgarClient, _Down(_ROWS)), date(2026, 11, 3)))
    dc, flags = _drawdown_cause(_record(date(2026, 10, 16)), edgar, cast(CachedHttp, _Http()),
                                bars=_BARS, cut=date(2026, 11, 3), anchor=_UNDERWRITE)
    assert dc.anchor is not None
    assert dc.anchor.at_anchor.shape.status is SourceStatus.UNKNOWN
    mine = [f for f in flags if f.startswith("drawdown-cause: (at the underwrite 2026-08-05)")]
    assert mine
    # hidden on the rolling window's ruling: the part's UNKNOWN note renders at the point of use
    from vinci.dossier.flags import is_qa
    assert all(is_qa(f) for f in mine)


# ─── which date is the anchor ──────────────────────────────────────────────────────────────────

def test_the_anchor_is_the_underwrite_else_the_follow_else_none() -> None:
    """ACROSS THE LIVE FILES, as an invariant (they are re-drawn, so no value is pinned on them):
    every committed page's anchor is its record's `underwrite_date` if it has a record, else its
    `followed_since` if it is followed, else none — read here straight from the JSON."""
    from vinci.config import get_config
    from vinci.dossier.assemble import _drawdown_anchor_date

    cfg = get_config()
    followed = json.loads((cfg.data_dir / "followed.json").read_text())
    pages = sorted(p.parent.name for p in Path("data/dossiers").glob("*/dossier.json"))
    kinds = set()
    for t in pages:
        rec = Path("scenarios") / f"{t}.json"
        got = _drawdown_anchor_date(cfg, t)
        if rec.exists():
            uw = json.loads(rec.read_text())["underwrite_date"]
            want = ("underwrite", date.fromisoformat(uw))
        elif t in followed:
            want = ("followed", date.fromisoformat(followed[t]["followed_since"]))
        else:
            assert got is None, t
            kinds.add(None)
            continue
        assert got is not None and (got.kind, got.on) == want, t
        kinds.add(want[0])
    assert kinds == {"underwrite", "followed", None}  # the corpus exercises all three


def test_an_underwrite_wins_over_a_follow_even_an_earlier_one() -> None:
    """On a FROZEN record of the real type: GOOGL's archived 2026-08-17 underwrite (superseded,
    so it never changes) against a later follow — the underwrite is the anchor."""
    from vinci.scenarios import ScenarioRecord

    card = ScenarioRecord.model_validate_json(
        Path("scenarios/archive/GOOGL-2026-08-17.json").read_text())
    got = drawdown_anchor_date(card, date(2026, 8, 27), ticker="GOOGL")
    assert got is not None and (got.kind, got.on) == ("underwrite", date(2026, 8, 17))
    got = drawdown_anchor_date(None, date(2026, 8, 27), ticker="GOOGL")
    assert got is not None and (got.kind, got.on) == ("followed", date(2026, 8, 27))
    assert drawdown_anchor_date(None, None, ticker="X") is None


def test_a_window_the_stored_closes_do_not_cover_is_unknown_never_none_found() -> None:
    """A store whose history begins after the window's start cannot see a drop there: the part is
    UNKNOWN, saying so, and its flag stays on the hidden machine tier — never "no single day of
    -10% or worse", an absence read from missing data."""
    from vinci.dossier.flags import is_qa

    late = [b for b in _BARS if b.bar_date >= date(2026, 3, 1)]  # history starts after 02-06
    edgar = cast(EdgarClient, AsOfEdgar(cast(EdgarClient, _Edgar(_ROWS)), date(2026, 11, 3)))
    dc, flags = _drawdown_cause(_record(date(2026, 10, 16)), edgar, cast(CachedHttp, _Http()),
                                bars=late, cut=date(2026, 11, 3), anchor=_UNDERWRITE)
    assert dc.anchor is not None
    at = dc.anchor.at_anchor
    for field in (at.shape, at.gap_down_dates, at.revised_guidance):
        assert field.status is SourceStatus.UNKNOWN
        assert "begin on 2026-03-02, not before this window's start 2026-02-06" in str(field.note)
    assert at.gaps == [] and at.filings == []
    mine = [f for f in flags if "not before this window's start" in f]
    assert mine and all(is_qa(f) for f in mine)
    # the since part, which the store does cover, is still read
    assert dc.anchor.since is not None and dc.anchor.since.shape.status is SourceStatus.PRESENT


# ─── the committed corpus reads, checks and renders as before ─────────────────────────────────

def test_every_committed_page_round_trips_with_no_new_drawdown_key() -> None:
    """New fields are ABSENT when None: each committed page's drawdown block re-serialises to
    exactly what is on disk, so a page with no anchor gains no null key. Not "no page carries an
    anchor" — the artifact pass re-assembles anchored names, and that would red on the first."""
    pages = sorted(Path("data/dossiers").glob("*/dossier.json"))
    assert len(pages) >= 26  # 27 until MVST was retired (2026-11-12)
    for p in pages:
        raw = json.loads(p.read_text())["mechanical"]["drawdown_cause"]
        assert json.loads(DrawdownCause.model_validate(raw).model_dump_json()) == raw, p


# ─── the pre-spend check ───────────────────────────────────────────────────────────────────────

def _built() -> dict[str, Any]:
    if not _BUILT.exists():
        pytest.skip("no frozen anchored build")
    return cast(dict[str, Any], json.loads(_BUILT.read_text()))


def test_smpls_precheck_moves_both_fields_to_the_dated_part_and_regresses_nothing() -> None:
    """The real $0 build against SMPL's 2026-08-18 page: the two drawdown fields that read as
    regressions are carried, by value, by the at-the-underwrite part."""
    cmp = prespend.compare(json.loads(_FROZEN_PAGE.read_text()), _built())
    dd = [m for m in cmp.regressions if "drawdown_cause" in m.path]
    assert dd == []
    moved = {m.path: m.note for m in cmp.moved}
    assert set(moved) == {"mechanical.drawdown_cause.gap_down_dates",
                          "mechanical.drawdown_cause.revised_guidance"}
    assert "2026-04-09, 2026-04-10" in str(moved["mechanical.drawdown_cause.gap_down_dates"])
    assert _ACC in str(moved["mechanical.drawdown_cause.revised_guidance"])


def test_a_dated_part_that_carries_another_event_carries_nothing() -> None:
    """By VALUE, never by presence: an at-anchor part holding only one of the two dates leaves the
    rolling window's loss a regression."""
    fresh = _built()
    at = fresh["mechanical"]["drawdown_cause"]["anchor"]["at_anchor"]
    at["gap_down_dates"]["value"] = ["2026-04-09"]
    at["revised_guidance"]["source_ref"] = "EDGAR 8-K 0000000000-00-000000 Ex-99.1 — elsewhere"
    cmp = prespend.compare(json.loads(_FROZEN_PAGE.read_text()), fresh)
    lost = {m.path for m in cmp.regressions}
    assert {"mechanical.drawdown_cause.gap_down_dates",
            "mechanical.drawdown_cause.revised_guidance"} <= lost
    assert cmp.moved == ()


def test_a_dated_part_never_loses_what_it_was_built_with() -> None:
    """Once a page carries its at-anchor part, a rebuild that drops a date or changes the exhibit
    is a regression, and stops the pass — present on both sides is not enough."""
    committed = _built()
    fresh = json.loads(json.dumps(committed))
    at = fresh["mechanical"]["drawdown_cause"]["anchor"]["at_anchor"]
    at["gap_down_dates"]["value"] = ["2026-04-09"]
    at["revised_guidance"]["source_ref"] = "EDGAR 8-K 0000000000-00-000000 Ex-99.1 — elsewhere"
    lost = {m.path: m for m in prespend.compare(committed, fresh).regressions}
    assert "mechanical.drawdown_cause.anchor.at_anchor.gap_down_dates" in lost
    assert "2026-04-10" in lost["mechanical.drawdown_cause.anchor.at_anchor.gap_down_dates"].after
    assert "mechanical.drawdown_cause.anchor.at_anchor.revised_guidance" in lost
    assert prespend.compare(committed, committed).regressions == ()


def test_the_paid_write_refuses_a_degraded_at_anchor_part_over_a_committed_one(
        tmp_path: Path) -> None:
    import vinci.dossier.assemble as asm

    committed = _built()
    folder = tmp_path / "SMPL"
    folder.mkdir()
    (folder / "dossier.json").write_text(json.dumps(committed))
    doc = Dossier.model_validate(committed)
    assert doc.mechanical is not None and doc.mechanical.drawdown_cause.anchor is not None
    asm._refuse_degraded_drawdown_overwrite(doc, folder)  # healthy: writes
    from vinci.dossier.schemas import Sourced
    dc = doc.mechanical.drawdown_cause
    anchor = dc.anchor
    assert anchor is not None
    down = anchor.model_copy(update={"at_anchor": anchor.at_anchor.model_copy(update={
        "shape": Sourced[str].unknown(note="EDGAR filing index unavailable — …")})})
    degraded = doc.model_copy(update={"mechanical": doc.mechanical.model_copy(update={
        "drawdown_cause": dc.model_copy(update={"anchor": down})})})
    with pytest.raises(asm.DossierAssemblyError, match="drawdown at the underwrite 2026-08-05"):
        asm._refuse_degraded_drawdown_overwrite(degraded, folder)
    asm._refuse_degraded_drawdown_overwrite(degraded, tmp_path / "NEW")  # a fresh name writes


# ─── the synthesis brief ───────────────────────────────────────────────────────────────────────

def test_the_brief_marks_the_dated_outlooks_and_asks_if_the_cause_played_out() -> None:
    """The at-the-anchor outlook is the oldest guide on the page; it is marked SUPERSEDED like
    the rolling one, and the digest gives both parts with the question. Structure only."""
    from vinci.dossier.synthesis import (
        DRAWDOWN_ANCHOR_HEADER,
        _drawdown_anchor_digest,
        _mark_drawdown_guidance,
    )

    doc = Dossier.model_validate(_built())
    assert doc.mechanical is not None
    dumped = doc.mechanical.model_dump(exclude={"primary_source"})
    _mark_drawdown_guidance(dumped, doc.mechanical.primary_source)
    rg = dumped["drawdown_cause"]["anchor"]["at_anchor"]["revised_guidance"]["value"]
    assert rg.startswith("[SUPERSEDED — filed 2026-04-09")
    digest = _drawdown_anchor_digest(dumped)
    assert digest is not None and digest.startswith(DRAWDOWN_ANCHOR_HEADER)
    assert "at the underwrite (2026-02-06 to 2026-08-05): discrete gap-downs" in digest
    assert "since the underwrite (2026-08-06 to " in digest
    assert "has the cause named at the underwrite played out?" in digest
    assert "`at_anchor`, the 180 days ending on the anchor date" in digest
    # no anchor, no section: the prompt every earlier build sent
    del dumped["drawdown_cause"]["anchor"]
    assert _drawdown_anchor_digest(dumped) is None


def test_the_digest_example_is_smpls_real_at_anchor_line() -> None:
    """The ONE literal example is not invented: its at-anchor line is SMPL's build, verbatim."""
    from vinci.dossier.synthesis import _DRAWDOWN_ANCHOR_EXAMPLE

    at = _built()["mechanical"]["drawdown_cause"]["anchor"]["at_anchor"]
    line = (f"at the underwrite ({at['start']} to {at['end']}): "
            f"{str(at['shape']['value']).removeprefix('discrete gap-downs — ')} → source_ref: "
            f"{at['shape']['source_ref']}")
    assert line in _DRAWDOWN_ANCHOR_EXAMPLE
    assert at["revised_guidance"]["source_ref"] in _DRAWDOWN_ANCHOR_EXAMPLE


# ─── the render ────────────────────────────────────────────────────────────────────────────────

def test_the_page_labels_both_parts_end_to_end() -> None:
    """The real build → markdown: the Brief and the Analysis section each say the drawdown at the
    underwrite and since; the committed SMPL page (no anchor) says neither."""
    from vinci.dossier.render import render_markdown

    md = render_markdown(Dossier.model_validate(_built()))
    assert "**Shape (last 180 days):** gradual bleed" in md  # the rolling window, labelled
    assert "**Drawdown at underwrite (2026-08-05):** 2026-04-09 -18.1% earnings; " in md
    assert "**Since underwrite (2026-08-06 → " in md
    assert "- **Drawdown at underwrite (2026-08-05)** · 2026-02-06 → 2026-08-05" in md
    assert f"[`{_ACC}`]" in md
    plain = render_markdown(Dossier.model_validate(json.loads(_FROZEN_PAGE.read_text())))
    assert "Drawdown at underwrite" not in plain and "Since underwrite" not in plain
    # a page built before the window moved to the price date names the window it read
    assert "**Shape (180 days to 2026-08-14):**" in plain


def test_window_words_twin() -> None:
    """render._window_words and dossier.js windowWords agree on the real build's two parts."""
    from vinci.dossier.render import _window_words
    from vinci.dossier.schemas import DrawdownWindow

    a = _built()["mechanical"]["drawdown_cause"]["anchor"]
    parts = [a["at_anchor"], a["since"]]
    py = [_window_words(DrawdownWindow.model_validate(w), -0.10) for w in parts]
    assert py[0] == "2026-04-09 -18.1% earnings; 2026-04-10 -11.5% earnings"
    if not shutil.which("node"):
        return
    driver = """
const handler = { get: () => stub, apply: () => stub, construct: () => ({}) };
const stub = new Proxy(function(){}, handler);
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const { windowWords } = await import("__URI__");
console.log(JSON.stringify(__P__.map((w) => windowWords(w, -0.10))));
""".replace("__URI__", Path("frontend/views/shared/dossier.js").resolve().as_uri()) \
        .replace("__P__", json.dumps(parts))
    out = subprocess.run(["node", "--input-type=module", "-e", driver],
                         capture_output=True, text=True, check=True)
    assert json.loads(out.stdout) == py


def test_anchor_words_twin() -> None:
    """THE PARITY PIN binding the label table's two copies (`schemas.DRAWDOWN_ANCHOR_WORDS`,
    dossier.js `ANCHOR_WORDS`, both on `test_duplicate_definitions.BASELINE`): a one-sided edit
    reds here."""
    from vinci.dossier.schemas import DRAWDOWN_ANCHOR_WORDS as _ANCHOR_WORDS

    if not shutil.which("node"):
        pytest.skip("node is not installed")
    driver = """
const handler = { get: () => stub, apply: () => stub, construct: () => ({}) };
const stub = new Proxy(function(){}, handler);
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const { ANCHOR_WORDS } = await import("__URI__");
console.log(JSON.stringify(ANCHOR_WORDS));
""".replace("__URI__", Path("frontend/views/shared/dossier.js").resolve().as_uri())
    out = subprocess.run(["node", "--input-type=module", "-e", driver],
                         capture_output=True, text=True, check=True)
    assert json.loads(out.stdout) == {k: list(v) for k, v in _ANCHOR_WORDS.items()}


def test_the_frozen_build_is_this_codes_serialisation() -> None:
    """The fixture is what `dossier_json` writes for it — a hand edit would not round-trip."""
    raw = _BUILT.read_text() if _BUILT.exists() else pytest.skip("no frozen anchored build")
    assert dossier_json(Dossier.model_validate(json.loads(raw))) == raw


def test_the_rolling_window_ends_on_the_price_date() -> None:
    """(item 3) A screen run on 2026-04-01 and a page priced 2026-04-30: the record's window ends
    before the 04-09/04-10 drops, the price-date window classifies them."""
    edgar = cast(EdgarClient, AsOfEdgar(cast(EdgarClient, _Edgar(_ROWS)), date(2026, 4, 30)))
    bars = [b for b in _BARS if b.bar_date <= date(2026, 4, 30)]
    old, _ = _drawdown_cause(_record(date(2026, 4, 1)), edgar, cast(CachedHttp, _Http()))
    new, _ = _drawdown_cause(_record(date(2026, 4, 1)), edgar, cast(CachedHttp, _Http()),
                             bars=bars, cut=date(2026, 4, 30), current_end=date(2026, 4, 30))
    assert "2026-04-09" not in (old.gap_down_dates.value or [])
    assert new.gap_down_dates.value is not None
    assert {"2026-04-09", "2026-04-10"} <= set(new.gap_down_dates.value)
    assert new.gap_window_end == "2026-04-30" and old.gap_window_end is None
    assert new.gap_down_dates.source_ref == "EOD gap-down detector, 2025-11-01 to 2026-04-30"


def test_a_drop_after_the_price_date_never_enters_the_rolling_window() -> None:
    """(item 3, NEGATIVE) The store holds closes past the page's price date (2026-04-08, the day
    before the drop): the window is cut there, so 04-09/04-10 are not in it — the price-date cut's
    discipline (#884), not "the latest bar the store happens to hold"."""
    edgar = cast(EdgarClient, AsOfEdgar(cast(EdgarClient, _Edgar(_ROWS)), date(2026, 4, 8)))
    dc, _ = _drawdown_cause(_record(date(2026, 4, 1)), edgar, cast(CachedHttp, _Http()),
                            bars=_BARS, cut=date(2026, 4, 8), current_end=date(2026, 4, 8))
    assert not {"2026-04-09", "2026-04-10"} & set(dc.gap_down_dates.value or [])
    assert dc.gap_window_end == "2026-04-08"


def test_with_no_closes_the_rolling_window_is_the_records_own() -> None:
    """(item 3, NEGATIVE) A caller holding the record alone gets the screen's window, ending on
    its reference date, with no `gap_window_end` key — what every page built before reads."""
    edgar = cast(EdgarClient, AsOfEdgar(cast(EdgarClient, _Edgar(_ROWS)), date(2026, 4, 30)))
    dc, _ = _drawdown_cause(_record(date(2026, 4, 1)), edgar, cast(CachedHttp, _Http()),
                            current_end=date(2026, 4, 30))
    assert dc.gap_window_end is None and "gap_window_end" not in _js(dc)
    assert "2026-04-09" not in (dc.gap_down_dates.value or [])


def test_the_assembly_ends_the_rolling_window_on_the_page_price_date() -> None:
    """(item 3, END TO END) LLY's page assembled at a 2026-10-02 reference on closes that run to
    its 2026-10-16 price date (`test_asof_cut`'s real fixtures): through the whole assembly the
    rolling window is the 180 days ending on the price date — so dropping the call site's
    `current_end` fails here, which no unit pin above can see."""
    from tests.test_asof_cut import _assemble_lly, _LlySec

    dc = _assemble_lly(_LlySec()).drawdown_cause
    assert dc.gap_window_end == "2026-10-16"
    stated = f"{dc.gap_down_dates.source_ref} {dc.gap_down_dates.note} {dc.shape.source_ref}"
    assert "2026-04-19 to 2026-10-16" in stated
    assert dc.anchor is None  # no anchor was passed: the rolling window alone


def test_the_rolling_label_twin() -> None:
    """render._rolling and dossier.js rollingLabel agree on all three spans: "last 180 days" for a
    window that ends on the price date; "180 days to <reference date>" for a page built before it,
    whose window ended there (review of #906 — never the later window claimed); the bare label
    when the length is not stated."""
    from vinci.dossier.render import _rolling

    dc = Dossier.model_validate(_built()).mechanical.drawdown_cause  # type: ignore[union-attr]
    old = dc.model_copy(update={"gap_window_end": None})
    bare = dc.model_copy(update={"gap_window_days": None, "gap_window_end": None})
    py = [_rolling("Shape", dc, "2026-10-16"), _rolling("Read", old, date(2026, 8, 14)),
          _rolling("Gap-down dates", bare, "2026-08-14")]
    assert py == ["Shape (last 180 days)", "Read (180 days to 2026-08-14)", "Gap-down dates"]
    if not shutil.which("node"):
        pytest.skip("node is not installed")
    driver = """
const handler = { get: () => stub, apply: () => stub, construct: () => ({}) };
const stub = new Proxy(function(){}, handler);
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const { rollingLabel } = await import("__URI__");
console.log(JSON.stringify([
  rollingLabel("Shape", {gap_window_days: 180, gap_window_end: "2026-11-03"}, "2026-10-16"),
  rollingLabel("Read", {gap_window_days: 180}, "2026-08-14"),
  rollingLabel("Gap-down dates", {gap_window_days: null}, "2026-08-14")]));
""".replace("__URI__", Path("frontend/views/shared/dossier.js").resolve().as_uri())
    out = subprocess.run(["node", "--input-type=module", "-e", driver],
                         capture_output=True, text=True, check=True)
    assert json.loads(out.stdout) == py


def test_a_store_that_does_not_cover_the_rolling_window_keeps_the_records_window() -> None:
    """(item 3, NEGATIVE — review of #906) Closes that begin after the window's start, or none at
    all, cannot see a drop in it: the window is the record's own (its 04-09/04-10 gap-downs kept,
    no `gap_window_end`), flagged — never "no discrete gap-down" read from missing closes."""
    edgar = cast(EdgarClient, AsOfEdgar(cast(EdgarClient, _Edgar(_ROWS)), date(2026, 4, 30)))
    record = _record(date(2026, 4, 30))
    want = {"2026-04-09", "2026-04-10"}
    assert want <= set(_drawdown_cause(record, edgar, cast(CachedHttp, _Http()))[0]
                       .gap_down_dates.value or [])
    for bars in ([], [b for b in _BARS if date(2026, 3, 1) <= b.bar_date <= date(2026, 4, 30)]):
        dc, flags = _drawdown_cause(record, edgar, cast(CachedHttp, _Http()), bars=bars,
                                    cut=date(2026, 4, 30), current_end=date(2026, 4, 30))
        assert dc.gap_window_end is None and "gap_window_end" not in _js(dc)
        assert want <= set(dc.gap_down_dates.value or [])
        assert any("the rolling window's start 2025-11-01" in f for f in flags)
