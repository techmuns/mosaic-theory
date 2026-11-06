"""THE MECHANICAL LAYER'S LABELS DESCRIBE; THEY NEVER JUDGE (fix 3a, 2026-11-06).

THE DEFECT. The 2026-11-05/06 fidelity diagnosis found the largest material class of synthesis
misreads was LABEL: the model repeats a label the CODE wrote as if it were a fact. #920's
pre-registered causality test proved the mechanism on one label — replacing "gradual bleed — no
discrete gap-down detected" with a neutral statement of the detector cut that wording from 5/5
draws to 1/5 (`docs/records/2026-11-05-nflx-synthesis-causality-test.md`). Five labels of that kind
were on the committed pages:

  1. the drawdown shape called EVERY window with no -10% day a "gradual bleed", rising ones too;
  2. "trailing only — no forward basis" sat on every page with a CIQ forward multiple, because it
     fired on the absence of the GUIDANCE-adjusted figure alone;
  3. the survival read wrote its own verdict into the fact: "(a risk)", "solvency risk";
  4. the peer-delta prompt asked whether "the discount" is earned on names trading at a PREMIUM;
  5. the catalyst calendar called a SUPERSEDED drawdown guide "the committed revised outlook".

THE PINS. Each drives the production entry point (`_drawdown_cause`, `_valuation`,
`_survival_capacity`, `peer_comps`, `_catalyst_calendar`, the CLI's `own-history-refresh`, and the
prompt `synthesize` sends) on values frozen from real committed pages at main bcda7ce3
(`tests/fixtures/descriptive_labels/pages.json`) and on seven real CIQ comps sheets cut through
the real decode path (`ciq_comps.json`). Where a label cannot be stated neutrally from structured
data it is DELETED, not explained (coordinator, 2026-11-06) — items 2, 3, 4 (no single direction)
and 5 (a guide that is not current); only item 1 is reworded, to #920's tested words. Each fix has
its negative: the case the old label described correctly reads as before. No assertion reads
LLM-composed text.
"""
from __future__ import annotations

import ast
import copy
import json
import pathlib
import re
import shutil
from datetime import date, timedelta
from types import SimpleNamespace
from typing import Any, cast

import pytest

from vinci.dossier import ciq_sheets as cs
from vinci.dossier import mechanical as mech_mod
from vinci.dossier import synthesis as syn
from vinci.dossier.ciq import CiqBundle, CiqFormat, CiqWorkbook
from vinci.dossier.schemas import (
    Dossier,
    DrawdownCause,
    ForwardMultipleHistory,
    MechanicalLayer,
    ReleaseExtract,
    Sourced,
    SourceStatus,
)
from vinci.edgar.client import EdgarClient, Filing
from vinci.graph.llm import LlmError
from vinci.netcache import CachedHttp
from vinci.schemas.data_record import Identity
from vinci.schemas.market import PriceBar
from vinci.screens.assemble import GAP_DOWN_THRESHOLD, build_price_record

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures" / "descriptive_labels"
PAGES: dict[str, Any] = json.loads((FIX / "pages.json").read_text())["pages"]
COMPS: dict[str, Any] = json.loads((FIX / "ciq_comps.json").read_text())["names"]
CARRIER = ROOT / "tests" / "fixtures" / "frozen_pages" / "2026-08-18" / "SMPL" / "dossier.json"
ANCH = ROOT / "tests" / "fixtures" / "anchored_drawdown"

#: The words #920 tested (V2), with the detector's threshold read from its own constant.
NEUTRAL_SHAPE = "no single-day drop of -10% or worse in the window (detector threshold -10%)"


def _carrier() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(CARRIER.read_text()))


def _mech(update: dict[str, Any]) -> MechanicalLayer:
    """SMPL's frozen page as the vehicle a pin swaps one block into."""
    m = MechanicalLayer.model_validate(_carrier()["mechanical"])
    return m.model_copy(update=update)


class _Capture:
    """Records the prompt `synthesize` sends, then fails the draw (the pattern of
    `test_material_figures_in_prompt`): the prompt is the artifact pinned."""

    def __init__(self) -> None:
        self.users: list[str] = []

    @property
    def model(self) -> str:
        return "capture"

    def extract(self, *, system: str, user: str, tool: dict[str, Any],
                cache: bool = False) -> dict[str, Any]:
        self.users.append(user)
        raise LlmError("captured")


def _sent(mech: MechanicalLayer) -> str:
    llm = _Capture()
    syn.synthesize(mech, llm=llm, ticker="X", name="X Co")  # type: ignore[arg-type]
    assert len(llm.users) == 1
    return llm.users[0]


# --- 1. the drawdown shape: a statement of the detector, never a description of the path --------


class _NoEdgar:
    """A window with no gap-down reads no filing; any call is a pin failure, loud."""

    def recent_filings(self, *_a: Any, **_kw: Any) -> list[Filing]:
        raise AssertionError("a window with no gap-down must not read the filing index")


def _closes(t: str) -> tuple[list[PriceBar], date]:
    """The page's own closes, rebuilt from its rebased daily series — a rebased index ratio IS the
    close ratio, so the detector's close-to-close arithmetic reads exactly what it read."""
    pts = PAGES[t]["drawdown"]["stock_performance_points"]
    bars = [PriceBar(internal_id=t, bar_date=date.fromisoformat(p["date"]), open=p["name"],
                     high=p["name"], low=p["name"], close=p["name"], volume=0.0, source="frozen")
            for p in pts]
    return bars, bars[-1].bar_date


def _rolling(t: str) -> DrawdownCause:
    """The block as `assemble_mechanical` builds it on the page's closes: the rolling window
    ending on the last close (#906's price-date window)."""
    bars, end = _closes(t)
    d = PAGES[t]["drawdown"]
    ident = Identity(internal_id=t, issuer_id=t, cik=d["cik"], ticker=t, mic="XNYS",
                     exchange="NYSE", eod_symbol=t, name=d["name"])
    record = build_price_record(ident, price_bars=bars, benchmark_bars=[], reference_date=end,
                                staleness_days=5)
    cause, flags = mech_mod._drawdown_cause(
        record, cast(EdgarClient, _NoEdgar()), cast(CachedHttp, None), bars=bars, current_end=end)
    assert flags == []
    return cause


def _window_return(t: str) -> float:
    """The rolling window's own move, first close in it to the last (its 180 days)."""
    bars, end = _closes(t)
    start = end - timedelta(days=180)
    held = [b for b in bars if start <= b.bar_date <= end]
    return held[-1].close / held[0].close - 1.0


@pytest.mark.parametrize("ticker", ["LLY", "NFLX"])
def test_a_window_with_no_gap_down_states_the_detector_whatever_the_price_did(
        ticker: str) -> None:
    """(+) LLY rose over its window and NFLX fell; neither had a -10% day. Both said "gradual
    bleed" on main — a decline claimed of a name that went up. Each now states what the detector
    found and its threshold, and the same words on both, because the detector reads no direction."""
    committed = PAGES[ticker]["drawdown"]["drawdown_cause"]["shape"]["value"]
    assert committed == "gradual bleed — no discrete gap-down detected"  # the page as committed
    move = _window_return(ticker)
    assert (move > 0) if ticker == "LLY" else (move < 0), move  # the premise: one up, one down
    cause = _rolling(ticker)
    assert cause.shape.status is SourceStatus.PRESENT
    assert cause.shape.value == NEUTRAL_SHAPE
    assert cause.gap_down_dates.status is SourceStatus.UNKNOWN


def test_the_threshold_in_the_words_is_the_detectors_own() -> None:
    """(+) The percentage is read off `GAP_DOWN_THRESHOLD`, never restated beside it."""
    pct = round(abs(GAP_DOWN_THRESHOLD) * 100)
    assert f"-{pct}%" in mech_mod._CURRENT_WORDS.none_shape
    assert mech_mod._CURRENT_WORDS.none_shape.count(f"-{pct}%") == 2


def test_the_prompt_carries_the_detector_statement_not_bleed() -> None:
    """(+) THE ARTIFACT THE MODEL READS: LLY's rebuilt block, in the prompt `synthesize` sends."""
    user = _sent(_mech({"drawdown_cause": _rolling("LLY")}))
    assert f'"value": "{NEUTRAL_SHAPE}"' in user
    assert "bleed" not in user.lower()


def test_a_window_with_gap_downs_still_lists_them() -> None:
    """(-) SMPL's April window, on its real closes and 8-Ks: the discrete read is unchanged."""
    from tests.test_anchored_drawdown import _build

    cause, _ = _build(date(2026, 8, 5), date(2026, 8, 5), None)
    assert cause.shape.value is not None
    assert cause.shape.value.startswith("discrete gap-downs — 2026-04-09")


def test_the_dated_parts_keep_the_words_they_were_built_with() -> None:
    """(-) The at-anchor and since parts already stated the detector neutrally, and a later build
    must not change the at-anchor part (#906): SMPL's committed parts rebuild byte-identical."""
    from tests.test_anchored_drawdown import _UNDERWRITE, _build

    cause, _ = _build(date(2026, 11, 3), date(2026, 11, 3), _UNDERWRITE)
    assert cause.anchor is not None and cause.anchor.since is not None
    frozen = PAGES["SMPL"]["drawdown_anchor_shapes"]
    assert cause.anchor.at_anchor.shape.value == frozen["at_anchor"]["value"]
    assert cause.anchor.since.shape.value == frozen["since"]["value"]
    assert "no discrete gap-down — no single day of -10% or worse" in frozen["since"]["value"]


# --- 2. "trailing only": only when the page has no forward multiple at all ----------------------


def _sourced(raw: dict[str, Any] | None) -> Any:
    return None if raw is None else Sourced[Any].model_validate(raw)


def _valuation_on(monkeypatch: pytest.MonkeyPatch, t: str, *,
                  history: bool = True, comps: bool = True) -> Any:
    """`mechanical._valuation` on the page's own comps sheet (cut, read by the real
    `comps_ntm_multiples`), its other readers returning the page's frozen values: the multiple as
    the reader returns it (no note yet), its guided forward, its consensus forward P/E and its
    forward-multiple history."""
    v = PAGES[t]["valuation"]
    ev = dict(v["ev_ebitda"], note=None)
    unknown = Sourced[Any].unknown(note="not read by this pin")
    monkeypatch.setattr(cs, "ev_ebitda_current", lambda _b: _sourced(ev))
    monkeypatch.setattr(cs, "financial_summary_annual", lambda _b: unknown)
    monkeypatch.setattr(cs, "cross_sectional_valuation", lambda _b: unknown)
    monkeypatch.setattr(cs, "ev_ebitda_percentile", lambda _b: unknown)
    monkeypatch.setattr(cs, "range_position", lambda _b: unknown)
    monkeypatch.setattr(cs, "own_history_bands", lambda _b: unknown)
    # a page committed before the field carries none (`Valuation` drops an unbuilt one); the reader
    # itself always answers, so that page's answer is "not built"
    fwd = _sourced(v["forward_multiples"]) or Sourced[Any].unknown(note="not on the frozen page")
    monkeypatch.setattr(cs, "forward_multiples", lambda *_a, **_k: fwd)
    hist = PAGES[t]["forward_multiple_history"]
    monkeypatch.setattr(cs, "forward_multiple_history", lambda _b: (
        ForwardMultipleHistory.model_validate(hist) if history and hist else None))
    from vinci.dossier import lease_basis as lb_mod

    monkeypatch.setattr(lb_mod, "lease_basis", lambda _b, _f: None)
    bars = [PriceBar(internal_id=t, bar_date=date(2026, 11, 2), open=1, high=1, low=1, close=1,
                     volume=0, source="frozen")]
    ident = Identity(internal_id=t, issuer_id=t, cik="1", ticker=t, mic="XNYS", exchange="NYSE",
                     eod_symbol=t, name=t)
    record = build_price_record(ident, price_bars=bars, benchmark_bars=[],
                                reference_date=date(2026, 11, 2), staleness_days=5)
    bundle = _comps_bundle(t) if comps else CiqBundle(ticker=t, workbooks=())
    return mech_mod._valuation(record, bundle, unknown, _sourced(v["ev_ebitda_adjusted_fwd"]))


@pytest.mark.parametrize("ticker", ["LLY", "EPAM"])
def test_a_page_with_a_ciq_forward_multiple_is_not_called_trailing_only(
        monkeypatch: pytest.MonkeyPatch, ticker: str) -> None:
    """(+) LLY carries a consensus forward P/E, the name's NTM multiples in its peer comps and the
    forward-multiple history; EPAM the last two. Both read "no forward basis" on main. The note is
    now DELETED — the multiple carries its reader's own note (none) — not replaced with words."""
    assert "no forward basis" in PAGES[ticker]["valuation"]["ev_ebitda"]["note"]  # as committed
    assert _valuation_on(monkeypatch, ticker).ev_ebitda.note is None


@pytest.mark.parametrize("history,comps", [(False, False), (True, False), (False, True)])
def test_trailing_only_stands_only_where_no_forward_multiple_exists(
        monkeypatch: pytest.MonkeyPatch, history: bool, comps: bool) -> None:
    """(-/+) EPAM (no consensus forward P/E) with its forward sources taken away: with neither,
    no forward basis exists and the note is the one it always was; either one alone removes it."""
    note = _valuation_on(monkeypatch, "EPAM", history=history, comps=comps).ev_ebitda.note
    assert note == (None if history or comps else mech_mod.TRAILING_ONLY_NOTE)


def test_a_consensus_forward_pe_alone_removes_the_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    """(+) Review of #923 (a surviving mutant dropped `forward_multiples` from the rule): LLY's
    consensus forward P/E, with its comps and history taken away, is a forward basis by itself."""
    assert _valuation_on(monkeypatch, "LLY", history=False, comps=False).ev_ebitda.note is None


def _history(t: str, *, keep: Any = None) -> ForwardMultipleHistory:
    h = ForwardMultipleHistory.model_validate(PAGES[t]["forward_multiple_history"])
    return h if keep is None else h.model_copy(update={"series": [s for s in h.series if keep(s)]})


def test_a_history_with_no_current_close_is_no_forward_basis() -> None:
    """(+) Review of #923: ORKA's forward history is NM at the latest close on every series (its
    only number a 2025 EV/NTM EBIT); a series counts only when it has a band, so alone it leaves
    the multiple trailing only."""
    h = _history("ORKA")
    assert any(p.close is not None for s in h.series for p in s.points)  # a number, but stale
    assert all(s.band is None for s in h.series)
    note = mech_mod.ev_ebitda_note(guided_forward=False, forward_multiples=False, peer_ntm=[],
                                   forward_history=h)
    assert note == mech_mod.TRAILING_ONLY_NOTE


def test_a_context_only_history_is_no_forward_basis() -> None:
    """(+/-) Review of #923: EPAM's P/NTM EPS series is context-only (it may not anchor a leg) —
    alone it is no forward basis; EPAM's banded EV/NTM EBITDA series alone is one."""
    ctx = _history("EPAM", keep=lambda s: s.context_only)
    ev = _history("EPAM", keep=lambda s: s.metric == "EV/NTM EBITDA")
    assert ctx.series and all(s.band is not None for s in ctx.series)
    kw: dict[str, Any] = {"guided_forward": False, "forward_multiples": False, "peer_ntm": []}
    assert mech_mod.ev_ebitda_note(forward_history=ctx, **kw) == mech_mod.TRAILING_ONLY_NOTE
    assert mech_mod.ev_ebitda_note(forward_history=ev, **kw) is None


@pytest.mark.parametrize("ticker,want", [
    ("ROST", ["NTM TEV/Rev", "NTM TEV/EBITDA", "NTM P/E"]),
    ("FUBO", ["NTM TEV/Rev", "NTM TEV/EBITDA"]),
    ("ORKA", []),
])
def test_the_names_ntm_multiples_are_its_numeric_forward_cells(ticker: str,
                                                                want: list[str]) -> None:
    """(+/-) Review of #923 (surviving mutants: counting 'NM' cells, counting trailing cells): the
    labels of the name's own NUMERIC NTM cells, in sheet order. ROST's six cells are all numbers
    (its trailing three are not NTM); FUBO's NTM P/E is 'NM'; ORKA's NTM TEV/EBITDA and P/E are
    'NM' and its NTM TEV/Rev blank."""
    assert cs.comps_ntm_multiples(_comps_bundle(ticker)) == want


def test_a_guided_forward_figure_leaves_the_multiple_unnoted(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """(-) VRRM has the guidance-adjusted forward EV/EBITDA; its multiple carries no note, as on
    its committed page."""
    assert PAGES["VRRM"]["valuation"]["ev_ebitda_adjusted_fwd"]["status"] == "present"
    assert _valuation_on(monkeypatch, "VRRM").ev_ebitda.note is None


@pytest.mark.parametrize("history,peer,fwd_pe", [
    (True, False, False), (False, False, False), (False, True, False), (False, False, True)])
def test_the_own_history_refresh_writes_the_same_note(
        monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path, history: bool, peer: bool,
        fwd_pe: bool) -> None:
    """(+/-) The CLI's multiples-cluster refresh writes the note through the same rule: SMPL's
    frozen page (no consensus forward P/E, no guided forward, a stub export with no comps sheet)
    → trailing only; with any ONE forward source — its forward history, the export's NTM cells,
    or LLY's frozen consensus forward P/E written onto the page — no note (review of #923: a
    refresh passing `peer_ntm=[]` or `forward_multiples=False` survived every other pin)."""
    import vinci.cli as cli
    from tests.test_lease_basis import _transform_env

    _transform_env(monkeypatch, tmp_path)
    page = tmp_path / "dossiers" / "SMPL" / "dossier.json"
    page.parent.mkdir(parents=True)
    doc = _carrier()
    if fwd_pe:
        doc["mechanical"]["valuation"]["forward_multiples"] = PAGES["LLY"]["valuation"][
            "forward_multiples"]
    page.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    page_mech = Dossier.model_validate(doc).mechanical
    assert page_mech is not None and page_mech.valuation is not None
    v = page_mech.valuation
    monkeypatch.setattr(cli, "get_config", lambda: SimpleNamespace(data_dir=tmp_path))
    monkeypatch.setattr(cs, "own_history_bands", lambda _b: v.own_history)
    monkeypatch.setattr(cs, "range_position", lambda _b: v.range_position)
    monkeypatch.setattr(cs, "ev_ebitda_current", lambda _b: v.ev_ebitda.model_copy(
        update={"note": None}))
    monkeypatch.setattr(cs, "ev_ebitda_percentile", lambda _b: v.ev_ebitda_percentile_5y)
    fmh = ForwardMultipleHistory.model_validate(doc["forward_multiple_history"])
    monkeypatch.setattr(cs, "forward_multiple_history", lambda _b: fmh if history else None)
    monkeypatch.setattr(cs, "comps_ntm_multiples",
                        lambda _b: ["NTM TEV/EBITDA"] if peer else [])
    cli._cmd_own_history_refresh(cast(Any, SimpleNamespace(tickers="SMPL", canonical_ciq=None,
                                                           dry_run=False)))
    note = json.loads(page.read_text())["mechanical"]["valuation"]["ev_ebitda"]["note"]
    assert note == (None if history or peer or fwd_pe else mech_mod.TRAILING_ONLY_NOTE)


# --- 3. the survival read: the judgment tags are deleted ---------------------------------------


def _survival(t: str) -> str:
    q = PAGES[t]["quality"]
    out = mech_mod._survival_capacity(_sourced(q["net_debt_to_ebitda"]),
                                      _sourced(q["net_debt_to_ebitda_adjusted"]),
                                      _sourced(q["fcf_sign"]))
    assert out.value is not None
    return out.value


def test_a_negative_fcf_carries_no_verdict() -> None:
    """(+) WLK's FCF is negative; main appended "(cash not derived — a risk)". The verdict is
    deleted; "cash not derived", what the machine did not compute, stays (review of #923)."""
    committed = PAGES["WLK"]["quality"]["survival_capacity"]["value"]
    assert committed.endswith("FCF-negative → burning cash (cash not derived — a risk)")
    assert _survival("WLK") == committed.replace(" (cash not derived — a risk)",
                                                 " (cash not derived)")


def test_an_unknown_fcf_sign_carries_no_verdict() -> None:
    """(+) LLY's FCF sign is UNKNOWN in its screen record (its reason on `quality.fcf_sign`)."""
    committed = PAGES["LLY"]["quality"]["survival_capacity"]["value"]
    assert committed.endswith(" (a risk)")
    assert _survival("LLY") == committed.removesuffix(" (a risk)")


def test_an_unknown_leverage_carries_no_verdict() -> None:
    """(+) A ratio with no CIQ net-debt position wrote "— solvency risk"; deleted."""
    q = PAGES["WLK"]["quality"]
    out = mech_mod._survival_capacity(
        Sourced[float].unknown(note="no CIQ Net Debt/EBITDA"),
        _sourced(q["net_debt_to_ebitda_adjusted"]), _sourced(q["fcf_sign"]))
    assert out.value is not None
    assert out.value.startswith("net-debt/EBITDA UNKNOWN (no CIQ Net Debt/EBITDA) | ")
    assert "risk" not in out.value


def test_a_positive_fcf_reads_as_before() -> None:
    """(-) AORT's read had no judgment tag; it rebuilds byte-identical."""
    assert _survival("AORT") == PAGES["AORT"]["quality"]["survival_capacity"]["value"]


# --- 3b. the lint: no judgment word in a string the fact layer writes ---------------------------

#: THE JUDGMENT VOCABULARY — and its limits, stated rather than hidden:
#:   * a CLOSED LIST: it refuses only a word it names; a new judgment word passes it. The entries
#:     are the four the 2026-11-06 audit found in fact text ("bleed", "a risk", "solvency risk")
#:     and the brief's ("bearish", "concern", "red flag"), plus words of the same kind; each entry
#:     is pinned live (`test_every_entry_of_the_judgment_list_is_live`);
#:   * PYTHON STRING CONSTANTS ONLY: it reads no JS and no rendered page, so the web furniture is
#:     pinned on its own (`test_the_web_page_assumes_no_discount`), and an LLM-written string or a
#:     verbatim quote is outside it by construction;
#:   * the FACT LAYER ONLY (`_SCANNED`). Over all of vinci/ at #923's head it also finds the
#:     ranker's "bleed" (`vinci/rank/ranker.py:234`, the ranked queue), the screen's "distress"
#:     (`vinci/screens/run.py:195`), the sleeves' and the prompt's "value trap", the scoring
#:     report's "concern" and theme intelligence's "a risk" — none of them a dossier fact, none
#:     changed here.
_JUDGMENT = re.compile(
    r"\b(?:a\s+risk|solvency\s+risk|bleed\w*|bearish|bullish|red[- ]flags?|"
    r"(?<!going[- ])concerns?|concerning|alarm\w*|worr\w*|distress\w*|value[- ]trap)\b", re.I)

#: The fact-writing modules — the set `tests/test_extraction_version_drift.py` watches as building
#: page fields: every module of vinci/dossier and vinci/edgar, and the three outside them — less
#: those whose text is not a fact: the prompt (rules are fix 4, a separate PR) and the lean
#: vocabulary.
_SCANNED = ("vinci/dossier", "vinci/edgar", "vinci/verbatim.py", "vinci/finra.py",
            "vinci/eod/features.py")
_NOT_FACTS = {
    "vinci/dossier/synthesis.py": "the synthesis PROMPT — its rules are fix 4, a separate PR",
    "vinci/dossier/verdict.py": "the lean vocabulary ('strongly-bearish') is its contract",
}
_RE_CALLS = {"compile", "search", "match", "fullmatch", "finditer", "findall", "sub", "split"}


def _prose(tree: ast.Module) -> list[ast.Constant]:
    """Every string constant that is not a docstring or a regex pattern — the text a module can
    write into a fact."""
    skip: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            skip.add(id(node.value))  # docstrings and bare attribute docs
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr in _RE_CALLS and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "re" and node.args):
            skip.update(id(n) for n in ast.walk(node.args[0]))
    return [n for n in ast.walk(tree) if isinstance(n, ast.Constant)
            and isinstance(n.value, str) and id(n) not in skip]


def _text(node: ast.Constant) -> str:
    return str(node.value)


def judgment_words(root: pathlib.Path = ROOT) -> list[str]:
    hits: list[str] = []
    for pkg in _SCANNED:
        base = root / pkg
        paths = sorted(base.rglob("*.py")) if base.is_dir() else [base] if base.exists() else []
        for path in paths:
            rel = path.relative_to(root).as_posix()
            if rel in _NOT_FACTS:
                continue
            for node in _prose(ast.parse(path.read_text())):
                for m in _JUDGMENT.finditer(_text(node)):
                    hits.append(f"{rel}:{node.lineno}: {m.group(0)!r} in {_text(node)[:80]!r}")
    return hits


def test_no_judgment_word_in_the_fact_layers_prose() -> None:
    """(+) The fact layer writes what it found; the human judges it. On main bcda7ce3 this found
    four strings, all in `mechanical.py` — the drawdown's "gradual bleed", the survival read's two
    "(a risk)" and its "solvency risk" — and nothing else in the two packages."""
    assert judgment_words() == []


@pytest.mark.parametrize("phrase", [
    "a risk", "solvency risk", "gradual bleed", "bearish", "bullish", "a red flag", "red-flags",
    "a concern", "concerns", "concerning", "alarming", "worrying", "distressed", "a value trap",
    "value-trap"])
def test_every_entry_of_the_judgment_list_is_live(phrase: str) -> None:
    """(+) Review of #923: dropping `bleed\\w*` or `solvency\\s+risk` from the regex passed every
    other pin. One phrase per entry, each matching that entry and no other."""
    hits = [m.group(0) for m in _JUDGMENT.finditer(phrase)]
    assert len(hits) == 1, (phrase, hits)


@pytest.mark.parametrize("phrase", ["going concern", "going-concern", "riskless", "bleeding-edge"])
def test_the_judgment_list_spares_terms_of_art(phrase: str) -> None:
    """(-) The going-concern term of art, and words that only begin like a listed one, except
    `bleed`'s own forms (`bleed\\w*`: "bleeding-edge" is a hit, stated here)."""
    hit = _JUDGMENT.search(phrase)
    assert (hit is not None) is (phrase == "bleeding-edge"), phrase


def test_the_lint_reads_the_text_a_fact_carries(tmp_path: pathlib.Path) -> None:
    """(-/+) Its precision, on a tree: a judgment word in a fact string is found; the same word in
    a docstring, a regex pattern, a going-concern term or the prompt is not."""
    for pkg in ("vinci/dossier", "vinci/edgar"):
        (tmp_path / pkg).mkdir(parents=True)
    (tmp_path / "vinci/dossier/a.py").write_text(
        '"""A bleed here is prose about the code."""\n'
        'import re\n'
        'P = re.compile(r"going.?concern|red flag")\n'
        'X = "going-concern language: none"\n'
        'Y = f"FCF negative ({1}) — a risk"\n')
    (tmp_path / "vinci/dossier/synthesis.py").write_text('S = "a BEARISH risk"\n')
    hits = judgment_words(tmp_path)
    assert len(hits) == 1 and "a.py:5: 'a risk'" in hits[0], hits


# --- 4. the peer-delta question: the gaps' one direction, or no question --------------------


def _comps_bundle(t: str) -> CiqBundle:
    path = pathlib.Path("/frozen") / f"{t}-comps.xls"
    sheets = {k.split("|")[1]: copy.deepcopy(v) for k, v in COMPS[t]["sheets"].items()}
    return CiqBundle(ticker=t, workbooks=(CiqWorkbook(kind="comps", path=path,
                                                     fmt=CiqFormat.BIFF_XLS, freq=None),),
                     _cache={path: sheets})


def _deltas(t: str) -> str:
    v = cs.peer_comps(_comps_bundle(t)).fundamental_deltas.value
    assert isinstance(v, str)
    return v


def test_a_name_at_a_premium_is_asked_about_its_premium() -> None:
    """(+) ROST trades at +124% EV/EBITDA and +108% P/E to its peer median; main asked whether
    "the discount" is EARNED by "worse fundamentals"."""
    assert "+124%" in cs.cross_sectional_valuation(_comps_bundle("ROST")).value  # type: ignore[operator]
    text = _deltas("ROST")
    assert "discount" not in text and "worse fundamentals" not in text
    assert "is the premium EARNED (better fundamentals) or RESIDUAL (unexplained)?" in text


def _frozen_deltas(t: str) -> str:
    """The page's `fundamental_deltas` as committed at main bcda7ce3 — FROZEN (`pages.json`), never
    the living page: a rebuild that moves the page must not move the pin (review of #923)."""
    return str(PAGES[t]["peer"]["fundamental_deltas"]["value"])


def test_a_name_at_a_discount_reads_as_before() -> None:
    """(-) PARR trades below its peer median on all six trading multiples, LTM and NTM:
    byte-identical to its frozen committed line."""
    assert _deltas("PARR") == _frozen_deltas("PARR")


#: What is left of the bracket when no single direction can be stated — the question deleted.
_NO_QUESTION = "  [justified-vs-residual inputs: the human judges — not computed here]"


@pytest.mark.parametrize("ticker", ["GOOGL", "FUBO", "WLK", "AMZN"])
def test_no_single_direction_deletes_the_question(ticker: str) -> None:
    """(+) One word would be false on some multiple, or no sign is known:
    GOOGL +11% on EV/EBITDA, −25% on P/E; FUBO −80% on TEV/Rev, +64% on NTM TEV/EBITDA;
    WLK's ONE known trailing gap of its two cross-sectional multiples (+27% EV/EBITDA, P/E NM)
    against −11% on NTM TEV/EBITDA; AMZN at a discount on all three trailing multiples and a
    premium on NTM TEV/EBITDA and NTM P/E (review of #923: the trailing gaps alone asked WLK about
    its "premium"). The question is deleted, not reworded; the signs sit in `cross_sectional` and
    `trading_multiples` beside it."""
    text = _deltas(ticker)
    assert text.endswith(_NO_QUESTION)
    assert "premium" not in text and "discount" not in text and "EARNED" not in text


def test_a_gap_that_rounds_to_zero_has_no_direction() -> None:
    """(+) Review of #923 (a surviving mutant dropped `round()`): a gap is signed as the headline
    prints it, so +0.3% — "+0%" — is neither. PARR's real sheet with every one of the name's six
    multiples set 'NM' but its EV/EBITDA, put 0.3% above the peer median."""
    b = _comps_bundle("PARR")
    tm = b.sheet("comps", "Trading Multiples")
    _hdr, peers, tgt = cs._comps_layout(tm, "PARR")
    assert tgt is not None
    for _lab, col in cs._COMPS_MULTIPLES:
        tm[tgt][col] = "NM"
    med = cs._peer_col_median(tm, peers, 2)
    assert med is not None
    tm[tgt][2] = round(float(f"{med:g}") * 1.003, 4)
    assert "(+0%)" in (cs.cross_sectional_valuation(b).value or "")
    assert _deltas_of(b).endswith(_NO_QUESTION)


def _deltas_of(b: CiqBundle) -> str:
    v = cs.peer_comps(b).fundamental_deltas.value
    assert isinstance(v, str)
    return v


def test_the_statistics_themselves_are_unchanged() -> None:
    """(-) Only the bracketed question moves: every name-vs-peer statistic is byte-identical to
    the FROZEN committed line, and so is the cross-sectional headline."""
    for t in COMPS:
        assert _deltas(t).split("  [", 1)[0] == _frozen_deltas(t).split("  [", 1)[0], t
        assert (cs.cross_sectional_valuation(_comps_bundle(t)).value
                == PAGES[t]["peer"]["cross_sectional"]["value"]), t


@pytest.mark.skipif(not shutil.which("node"), reason="node unavailable")
def test_the_web_page_assumes_no_discount(tmp_path: pathlib.Path) -> None:
    """(+) END TO END through the web twin (`renderDossier` in node) on SMPL's frozen page: the
    Peer comparison subtitle read "the reader judges whether the discount is earned or residual"
    on every page, premium or not (review of #923). The render keeps the section."""
    from tests.test_layer_refreshes import _web

    html = _web(_carrier(), tmp_path)
    assert "Peer comparison" in html
    assert "the discount is earned" not in html


# --- 5. the print row names the drawdown guide only when it is current ------------------------

#: The row every page without a drawdown guide carries (unchanged by this fix).
_NO_GUIDE_ROW = "the next reported quarter against the committed trajectory"


class _PrintEdgar:
    """The page's own results releases as 2.02 8-Ks — the history the cadence is read from."""

    def __init__(self, t: str) -> None:
        rel = PAGES[t]["print_row"]["releases"]
        self.rows = [Filing(cik=PAGES[t]["print_row"]["cik"], form="8-K",
                            filing_date=date.fromisoformat(r["filed"]),
                            accession=f"0000000000-00-{i:06d}", items=["2.02", "9.01"],
                            primary_doc=None)
                     for i, r in enumerate(rel) if r["filed"]]

    def recent_filings(self, *_a: Any, **_kw: Any) -> list[Filing]:
        return sorted(self.rows, key=lambda f: f.filing_date, reverse=True)


def _releases(t: str, keep: str = "all") -> list[ReleaseExtract]:
    """The page's releases; ``keep`` "own" leaves only the guide's own release (CURRENT), "other"
    every release but it (the guide UNDATED), "own-unparsed" only the guide's own release with no
    guide row parsed from it (no newest guide-bearing release at all: CURRENT, as the prompt's
    mark reads it)."""
    p = PAGES[t]["print_row"]
    acc = re.search(r"\d{10}-\d{2}-\d{6}", p["revised_guidance"]["source_ref"] or "")
    assert acc is not None
    rel = [ReleaseExtract.model_validate(r) for r in p["releases"]]
    if keep == "own":
        return [r for r in rel if acc.group(0) in r.source_ref]
    if keep == "own-unparsed":
        return [r.model_copy(update={"guidance": []}) for r in rel
                if acc.group(0) in r.source_ref]
    if keep == "other":
        return [r for r in rel if acc.group(0) not in r.source_ref]
    return rel


def _print_row(t: str, keep: str = "all") -> tuple[str, str]:
    p = PAGES[t]["print_row"]
    rg = Sourced[str].model_validate(p["revised_guidance"])
    carrier = _mech({})
    assert carrier.drawdown_cause is not None and carrier.primary_source is not None
    m = carrier.model_copy(update={
        "drawdown_cause": carrier.drawdown_cause.model_copy(update={"revised_guidance": rg}),
        "primary_source": carrier.primary_source.model_copy(
            update={"releases": _releases(t, keep)}),
        "capital_structure": None, "operating_drivers": None})
    cal = mech_mod._catalyst_calendar(cast(EdgarClient, _PrintEdgar(t)), p["cik"],
                                      date.fromisoformat(p["reference_date"]), m)
    row = next(r for r in cal.rows if r.event == mech_mod.PRINT_EVENT)
    return row.tests_what, row.source_ref


@pytest.mark.parametrize("ticker", ["BRBR", "VITL", "VRRM"])
def test_a_superseded_drawdown_guide_leaves_the_print_row(ticker: str) -> None:
    """(+) Each page's drawdown guide was replaced by a later one (BRBR's May guide by August's),
    yet its print row called it "the committed revised outlook". A replaced guide is not what the
    next print tests: the row is the one every page with no drawdown guide carries, and cites it
    no more."""
    committed = PAGES[ticker]["print_row"]["catalyst_print_row"]
    assert committed["tests_what"].startswith("the committed revised outlook")
    tests, src = _print_row(ticker)
    assert tests == _NO_GUIDE_ROW
    assert "guide:" not in src


def test_a_current_drawdown_guide_is_still_the_checkpoint() -> None:
    """(-) The same guide as the newest one on file: the row names it, without "committed"."""
    tests, src = _print_row("BRBR", "own")
    assert tests == ("the revised outlook (see Revised guidance — the print is the checkpoint "
                     "that confirms or refutes it)")
    assert "guide: " in src


def test_an_undated_drawdown_guide_leaves_the_print_row() -> None:
    """(+) Review of 3a: a guide no release dates is marked "do not read as current" in the
    prompt, so the row does not call the print its checkpoint."""
    assert _print_row("BRBR", "other")[0] == _NO_GUIDE_ROW


@pytest.mark.parametrize("keep", ["all", "own", "other", "own-unparsed"])
def test_the_row_reads_the_guide_as_the_prompt_marks_it(keep: str) -> None:
    """(+/-) One derivation: the row names the guide exactly when the mark
    `_mark_drawdown_guidance` puts on the same field in the prompt is CURRENT — a guide with no
    newest guide-bearing release to replace it included (review of #923: a mutant reading that
    as not current survived)."""
    p = PAGES["BRBR"]["print_row"]
    ps = SimpleNamespace(releases=_releases("BRBR", keep))
    dumped = {"drawdown_cause": {"revised_guidance": dict(p["revised_guidance"])}}
    syn._mark_drawdown_guidance(dumped, ps)  # type: ignore[arg-type]
    current = dumped["drawdown_cause"]["revised_guidance"]["value"].startswith("[CURRENT GUIDE")
    assert (_print_row("BRBR", keep)[0] != _NO_GUIDE_ROW) is current
