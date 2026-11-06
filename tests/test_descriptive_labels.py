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
(`tests/fixtures/descriptive_labels/pages.json`) and on four real CIQ comps sheets cut through the
real decode path (`ciq_comps.json`). Each fix has its negative: the case the old label described
correctly reads as before. No assertion reads LLM-composed text.
"""
from __future__ import annotations

import ast
import copy
import json
import pathlib
import re
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
    forward-multiple history; EPAM the last two. Both read "no forward basis" on main. Now the note
    says what is absent — the guidance-adjusted figure — and names where the forward multiples
    are, the one the synthesis reads (the peer comps' NTM TEV/EBITDA) among them."""
    assert "no forward basis" in PAGES[ticker]["valuation"]["ev_ebitda"]["note"]  # as committed
    note = _valuation_on(monkeypatch, ticker).ev_ebitda.note
    assert note is not None
    assert "trailing only" not in note and "no forward basis" not in note
    assert "no guidance-adjusted forward EV/EBITDA" in note
    peer = note.split("the name's ", 1)[1].split(" (`peer_comps.trading_multiples`)", 1)[0]
    assert "NTM TEV/EBITDA" in peer.split(", ")
    assert "EV/NTM EBITDA" in note
    assert ("valuation.forward_multiples" in note) is (ticker == "LLY")


@pytest.mark.parametrize("history,comps", [(False, False), (True, False), (False, True)])
def test_trailing_only_stands_only_where_no_forward_multiple_exists(
        monkeypatch: pytest.MonkeyPatch, history: bool, comps: bool) -> None:
    """(-/+) EPAM (no consensus forward P/E) with its forward sources taken away: with neither,
    no forward basis exists and the note is the one it always was; either one alone is enough."""
    note = _valuation_on(monkeypatch, "EPAM", history=history, comps=comps).ev_ebitda.note
    if not (history or comps):
        assert note == mech_mod.TRAILING_ONLY_NOTE
    else:
        assert note is not None and "no forward basis" not in note
        assert ("peer_comps.trading_multiples" in note) is comps
        assert ("forward_multiple_history" in note) is history


def test_a_guided_forward_figure_leaves_the_multiple_unnoted(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """(-) VRRM has the guidance-adjusted forward EV/EBITDA; its multiple carries no note, as on
    its committed page."""
    assert PAGES["VRRM"]["valuation"]["ev_ebitda_adjusted_fwd"]["status"] == "present"
    assert _valuation_on(monkeypatch, "VRRM").ev_ebitda.note is None


@pytest.mark.parametrize("history", [True, False])
def test_the_own_history_refresh_writes_the_same_note(
        monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path, history: bool) -> None:
    """(+/-) The CLI's multiples-cluster refresh writes the note through the same rule: SMPL's
    frozen page (no consensus forward P/E, no guided forward) with its forward history → the
    absence named; without it → trailing only."""
    import vinci.cli as cli
    from tests.test_lease_basis import _transform_env

    _transform_env(monkeypatch, tmp_path)
    page = tmp_path / "dossiers" / "SMPL" / "dossier.json"
    page.parent.mkdir(parents=True)
    doc = _carrier()
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
    cli._cmd_own_history_refresh(cast(Any, SimpleNamespace(tickers="SMPL", canonical_ciq=None,
                                                           dry_run=False)))
    note = json.loads(page.read_text())["mechanical"]["valuation"]["ev_ebitda"]["note"]
    if history:
        assert "no guidance-adjusted forward EV/EBITDA" in note and "EV/NTM EBITDA" in note
        assert "no forward basis" not in note
    else:
        assert note == mech_mod.TRAILING_ONLY_NOTE


# --- 3. the survival read states what is unknown and why, never "a risk" -----------------------


def _survival(t: str) -> str:
    q = PAGES[t]["quality"]
    out = mech_mod._survival_capacity(_sourced(q["net_debt_to_ebitda"]),
                                      _sourced(q["net_debt_to_ebitda_adjusted"]),
                                      _sourced(q["fcf_sign"]))
    assert out.value is not None
    return out.value


def test_a_negative_fcf_says_what_the_block_does_not_read() -> None:
    """(+) WLK's FCF is negative; main appended "(cash not derived — a risk)". The block reads no
    cash balance, so it derives no runway — stated, without the verdict."""
    assert "a risk" in PAGES["WLK"]["quality"]["survival_capacity"]["value"]  # as committed
    text = _survival("WLK")
    assert "risk" not in text
    assert "FCF-negative" in text and "no cash balance" in text


def test_an_unknown_fcf_sign_says_why() -> None:
    """(+) LLY's FCF sign is UNKNOWN in its screen record; the read now carries that field's own
    reason instead of "(a risk)"."""
    note = PAGES["LLY"]["quality"]["fcf_sign"]["note"]
    text = _survival("LLY")
    assert "risk" not in text
    assert f"FCF sign UNKNOWN ({note})" in text


def test_an_unknown_leverage_says_what_it_leaves_unread() -> None:
    """(+) A ratio with no CIQ net-debt position wrote "— solvency risk"; it now names what the
    missing ratio leaves unassessed."""
    q = PAGES["WLK"]["quality"]
    out = mech_mod._survival_capacity(
        Sourced[float].unknown(note="no CIQ Net Debt/EBITDA"),
        _sourced(q["net_debt_to_ebitda_adjusted"]), _sourced(q["fcf_sign"]))
    assert out.value is not None
    assert "risk" not in out.value
    assert "net-debt/EBITDA UNKNOWN (no CIQ Net Debt/EBITDA) — leverage not assessable" in out.value


def test_a_positive_fcf_reads_as_before() -> None:
    """(-) AORT's read had no judgment tag; it rebuilds byte-identical."""
    assert _survival("AORT") == PAGES["AORT"]["quality"]["survival_capacity"]["value"]


# --- 3b. the lint: no judgment word in a string the fact layer writes ---------------------------

#: THE JUDGMENT VOCABULARY — a closed list, so the lint can only refuse a word it names: a new
#: judgment word passes it (stated, not hidden). The four the 2026-11-06 audit found in fact text
#: ("bleed", "a risk", "solvency risk", and the brief's "bearish"/"concern"/"red flag"), and the
#: words of the same kind a fact layer might write.
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


# --- 4. the peer-delta question: premium or discount from the sign, nothing when unknown --------


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


def test_a_name_at_a_discount_reads_as_before() -> None:
    """(-) PARR trades at −57% and −70%: the question it was always asked."""
    want = "is the discount EARNED (worse fundamentals) or RESIDUAL (unexplained)?"
    assert want in _deltas("PARR")


def test_a_premium_on_one_multiple_and_a_discount_on_the_other_names_each() -> None:
    """(+) GOOGL: +11% on EV/EBITDA, −25% on P/E. One word for both would be false on one."""
    text = _deltas("GOOGL")
    assert "the premium on EV/EBITDA and the discount on P/E" in text
    assert "(worse fundamentals)" not in text and "(better fundamentals)" not in text


def test_no_known_gap_says_nothing_directional() -> None:
    """(+) FUBO's EV/EBITDA and P/E are both NM: neither sign is known, so neither word is used."""
    text = _deltas("FUBO")
    assert "premium" not in text and "discount" not in text
    assert "is any gap to the peer median EARNED" in text


def test_the_statistics_themselves_are_unchanged() -> None:
    """(-) Only the bracketed question moves: every name-vs-peer statistic is byte-identical."""
    for t in COMPS:
        stats = _deltas(t).split("  [", 1)[0]
        committed = json.loads((ROOT / "data" / "dossiers" / t / "dossier.json").read_text())
        assert stats == committed["mechanical"]["peer_comps"]["fundamental_deltas"][
            "value"].split("  [", 1)[0], t


# --- 5. the print row leads with the guide's vintage, never "committed" -------------------------


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


def _print_row(t: str, *, newest_only: bool = False) -> str:
    p = PAGES[t]["print_row"]
    releases = [ReleaseExtract.model_validate(r) for r in p["releases"]]
    rg = Sourced[str].model_validate(p["revised_guidance"])
    if newest_only:
        # the drawdown guide's own release is the newest guide-bearing one: CURRENT
        acc = re.search(r"\d{10}-\d{2}-\d{6}", rg.source_ref or "")
        assert acc is not None
        releases = [r for r in releases if acc.group(0) in r.source_ref]
    carrier = _mech({})
    assert carrier.drawdown_cause is not None and carrier.primary_source is not None
    m = carrier.model_copy(update={
        "drawdown_cause": carrier.drawdown_cause.model_copy(update={"revised_guidance": rg}),
        "primary_source": carrier.primary_source.model_copy(update={"releases": releases}),
        "capital_structure": None, "operating_drivers": None})
    cal = mech_mod._catalyst_calendar(cast(EdgarClient, _PrintEdgar(t)), p["cik"],
                                      date.fromisoformat(p["reference_date"]), m)
    row = next(r for r in cal.rows if r.event == mech_mod.PRINT_EVENT)
    return row.tests_what


@pytest.mark.parametrize("ticker", ["BRBR", "VITL", "VRRM"])
def test_a_superseded_drawdown_guide_is_marked_superseded_first(ticker: str) -> None:
    """(+) Each page's drawdown guide was replaced by a later one (BRBR's May guide by August's),
    yet its print row called it "the committed revised outlook". The vintage now LEADS the row,
    the same mark the prompt puts on the guide itself."""
    assert "committed" in PAGES[ticker]["print_row"]["catalyst_print_row"]["tests_what"]
    text = _print_row(ticker)
    assert text.startswith("[SUPERSEDED — filed ")
    assert "committed" not in text and "confirms or refutes" not in text


def test_a_current_drawdown_guide_is_marked_current_and_still_tested() -> None:
    """(-) The same guide as the newest one on file: CURRENT, and the print is its checkpoint."""
    text = _print_row("BRBR", newest_only=True)
    assert text.startswith("[CURRENT GUIDE, filed 2026-05-05]")
    assert "confirms or refutes it" in text and "committed" not in text


def test_the_row_marks_the_guide_as_the_prompt_does() -> None:
    """(+) One derivation: the print row's mark is the one `_mark_drawdown_guidance` puts on the
    same field in the prompt."""
    p = PAGES["BRBR"]["print_row"]
    ps = SimpleNamespace(releases=[ReleaseExtract.model_validate(r) for r in p["releases"]])
    dumped = {"drawdown_cause": {"revised_guidance": dict(p["revised_guidance"])}}
    syn._mark_drawdown_guidance(dumped, ps)  # type: ignore[arg-type]
    prompt_mark = dumped["drawdown_cause"]["revised_guidance"]["value"].split("\n", 1)[0]
    assert _print_row("BRBR").startswith(prompt_mark)
