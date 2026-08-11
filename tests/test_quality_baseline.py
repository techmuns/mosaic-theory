"""The quality sleeve's kill test — its BUY leg against simply INDEXING the follow list.

`vinci/sleeves.py` states the criterion in words: *"the sleeve's BUY−PASS curve fails to beat
simply INDEXING the same followed names — the judgement adds nothing over passive exposure to a
list we chose anyway"*. Nothing computed it. `vinci/monitor.py` knows only cap-band ETFs, which
answer "how did the market do", not "would holding the whole follow list have done as well".

WHAT THESE PIN, in the order the harm would land:
  1. the rendered report carries the comparator (the artifact, not the helper);
  2. a book that names NO basket prints NO baseline line — the first cut printed "unavailable" for
     overshoot, inventing a missing measurement for a book with nothing to index against;
  3. a partial basket is REFUSED with its reason, never silently reweighted;
  4. the primary BUY−AVOID spread is untouched;
  5. every `score_ledger` call site supplies the basket (#378's lesson: a per-book number reachable
     from one default path and not the other is invisible to half the readers);
  6. this module's follow-list reader and the dossier's agree on the committed corpus.
"""
from __future__ import annotations

import argparse
import ast
import json
import pathlib
from datetime import date, datetime, timedelta

import pytest

from vinci.followed import FollowedListError, followed_by_sleeve
from vinci.schemas.data_record import Identity
from vinci.schemas.ledger import Confidence, LedgerEntry, Verdict
from vinci.schemas.market import PriceBar
from vinci.scoring import score_ledger
from vinci.scoring.baseline import Basket, basket_return, resolve_baskets
from vinci.sleeves import UnknownSleeveError
from vinci.store import Store

ROOT = pathlib.Path(__file__).resolve().parents[1]
ENTRY_D = date(2026, 1, 5)
#: THE SCORING DATE IS THE HORIZON, NOT ``as_of`` (`harness`: ``min(horizon_date, as_of)``), so the
#: closing bar has to sit ON it — an end bar dated after the horizon is simply never read, and the
#: first cut of these fixtures measured a flat 0% while looking like it measured +30%.
HORIZON_D = ENTRY_D + timedelta(days=180)   # 2026-07-04
EXIT_D = date(2026, 8, 10)                  # as_of — comfortably past the horizon → rows RESOLVE

#: The follow list as committed — the corpus every basket claim below is checked against.
COMMITTED_FOLLOWED = ROOT / "data" / "followed.json"


def _bars(iid: str, start: float, end: float) -> list[PriceBar]:
    return [
        PriceBar(internal_id=iid, bar_date=d, open=c, high=c + 1, low=c - 1, close=c,
                 volume=1e6, source="t")
        for d, c in ((ENTRY_D, start), (HORIZON_D, end))
    ]


def _entry(ticker: str, iid: str, verdict: Verdict, sleeve: str, origin: str) -> LedgerEntry:
    return LedgerEntry(
        entry_id=f"V-{ticker}", candidate_id=f"{ticker}-c", internal_id=iid, ticker=ticker,
        verdict=verdict, twin_call="t", entry_price=100.0, entry_price_as_of=ENTRY_D,
        thesis="t", kill_criteria="k", horizon_days=180, confidence=Confidence.MEDIUM,
        decided_at=datetime.combine(ENTRY_D, datetime.min.time()),
        origin=origin, sleeve=sleeve)


def _followed_file(tmp_path: pathlib.Path, tickers: dict[str, str]) -> pathlib.Path:
    p = tmp_path / "followed.json"
    p.write_text(json.dumps(
        {t: {"reason": "followed for the cross-read", "sleeve": s} for t, s in tickers.items()}))
    return p


def _identity(ticker: str) -> Identity:
    """A real `Identity`, so `iter_securities` round-trips it as production does."""
    return Identity(
        internal_id=f"SEC-{ticker}", issuer_id=f"ISS-{ticker}", cik="0000000001", ticker=ticker,
        mic="XNAS", exchange="Nasdaq", eod_symbol=ticker, name=f"{ticker} Inc")


class _FakeIdentity:
    """Only what `resolve_baskets` reads, under the REAL attribute names — a rename breaks it."""

    def __init__(self, ticker: str, internal_id: str) -> None:
        self.ticker, self.internal_id = ticker, internal_id


# --------------------------------------------------------------------------------------------
# 1 + 4. The rendered artifact
# --------------------------------------------------------------------------------------------

def test_the_kill_test_renders_with_its_members_and_leaves_the_primary_alone(
    tmp_path: pathlib.Path,
) -> None:
    """THE ARTIFACT PIN. A helper-level assertion would stay green if the render dropped the line.

    Two BUYs and a PASS: one screen-origin overshoot BUY (the primary's leg) and one followed
    quality BUY, so the same report exercises the book WITH a basket and the book WITHOUT one.
    """
    followed = _followed_file(tmp_path, {"AAA": "quality", "BBB": "quality"})
    rows = [
        _entry("AAA", "SEC-AAA", Verdict.BUY, "quality", "followed"),
        _entry("BBB", "SEC-BBB", Verdict.PASS, "quality", "followed"),
        _entry("CCC", "SEC-CCC", Verdict.BUY, "overshoot", "screen"),
        _entry("DDD", "SEC-DDD", Verdict.AVOID_TERMINAL, "overshoot", "screen"),
    ]
    with Store(tmp_path / "s.db") as store:
        store.write_prices(_bars("IDX-IWM", 100.0, 105.0))
        # basket members: AAA +30%, BBB +10% → equal-weight +20%
        store.write_prices(_bars("SEC-AAA", 100.0, 130.0))
        store.write_prices(_bars("SEC-BBB", 100.0, 110.0))
        store.write_prices(_bars("SEC-CCC", 100.0, 150.0))
        store.write_prices(_bars("SEC-DDD", 100.0, 90.0))
        for r in rows:
            store.append_ledger(r)
        ids = [_FakeIdentity("AAA", "SEC-AAA"), _FakeIdentity("BBB", "SEC-BBB")]
        baskets = resolve_baskets(followed, ids)  # type: ignore[arg-type]
        _s, with_b = score_ledger(store, as_of=EXIT_D, baskets=baskets)
        _s, without = score_ledger(store, as_of=EXIT_D)

    md = with_b.to_markdown()
    assert "vs equal-weight follow basket (AAA, BBB)" in md, (
        f"the kill-test line is absent from the rendered report, or does not name the basket it "
        f"was measured against:\n{md}")
    q = with_b.by_sleeve["quality"]
    assert q.basket_mean == pytest.approx(0.20), f"equal-weight basket read {q.basket_mean}"
    # the quality BUY is AAA itself (+30%) → beats the basket by 10pts
    assert q.vs_basket == pytest.approx(0.10), f"long-vs-basket read {q.vs_basket}"

    # 4. THE PROOF NUMBER IS UNTOUCHED — asserted on the primary itself, not on the absence of a
    # string, so a basket that leaked into the spread would fail here regardless of how it printed.
    assert with_b.buy_avoid_spread == without.buy_avoid_spread, (
        "supplying a basket moved the primary BUY−AVOID spread")
    assert with_b.n_resolved_buy == without.n_resolved_buy == 1, (
        "the followed quality BUY entered the screen-origin primary count")


def test_a_book_with_no_follow_basket_prints_no_baseline_line(tmp_path: pathlib.Path) -> None:
    """THE REGRESSION, found by running the report rather than the tests.

    The first cut gated the line on `basket_note`, which is set for EVERY sleeve — so a resolved
    overshoot row printed `vs equal-weight follow basket: unavailable — no basket supplied for this
    sleeve`. Overshoot names no indexing comparator; its kill criterion is the standing fund-wide
    falsifier. Reporting a book as missing a measurement it never claims is a false negative in the
    one place the fund reads its own falsifiers.
    """
    followed = _followed_file(tmp_path, {"AAA": "quality"})
    with Store(tmp_path / "s.db") as store:
        store.write_prices(_bars("IDX-IWM", 100.0, 105.0))
        for t, end in (("SEC-AAA", 130.0), ("SEC-CCC", 150.0), ("SEC-DDD", 90.0)):
            store.write_prices(_bars(t, 100.0, end))
        store.append_ledger(_entry("CCC", "SEC-CCC", Verdict.BUY, "overshoot", "screen"))
        store.append_ledger(
            _entry("DDD", "SEC-DDD", Verdict.AVOID_TERMINAL, "overshoot", "screen"))
        baskets = resolve_baskets(followed, [_FakeIdentity("AAA", "SEC-AAA")])  # type: ignore[arg-type]
        _s, report = score_ledger(store, as_of=EXIT_D, baskets=baskets)

    md = report.to_markdown()
    assert "**overshoot**" in md, "fixture broken: the overshoot row did not render"
    assert "unavailable" not in md, (
        f"a book that names no passive comparator was reported as missing one:\n{md}")


# --------------------------------------------------------------------------------------------
# 3. The refusal
# --------------------------------------------------------------------------------------------

def test_a_partial_basket_is_refused_and_names_the_missing_member() -> None:
    """Reweighting two names into a three-name basket answers a question nobody asked. The reason
    has to name the member, because 'unavailable' alone is indistinguishable from 'it lost'."""
    basket = Basket("quality", ("AAA", "BBB", "CCC"),
                    {"AAA": "SEC-AAA", "BBB": "SEC-BBB", "CCC": "SEC-CCC"})
    bars = {"AAA": _bars("SEC-AAA", 100.0, 130.0), "BBB": _bars("SEC-BBB", 100.0, 110.0)}
    got, note = basket_return(basket, bars, ENTRY_D, EXIT_D)
    assert got is None, f"a 2-of-3 basket was averaged and returned {got}"
    assert note is not None and "CCC" in note, f"the refusal does not name the member: {note!r}"


def test_an_unresolved_ticker_still_counts_as_a_member(tmp_path: pathlib.Path) -> None:
    """A followed name with no security row must not quietly leave the basket — that would shrink
    the comparator to whatever happened to resolve, under the same label."""
    followed = _followed_file(tmp_path, {"AAA": "quality", "GHOST": "quality"})
    baskets = resolve_baskets(followed, [_FakeIdentity("AAA", "SEC-AAA")])  # type: ignore[arg-type]
    assert baskets["quality"].members == ("AAA", "GHOST")
    assert "GHOST" not in baskets["quality"].internal_ids
    got, note = basket_return(
        baskets["quality"], {"AAA": _bars("SEC-AAA", 100.0, 130.0)}, ENTRY_D, EXIT_D)
    assert got is None and note is not None and "GHOST" in note, (
        f"an unresolvable followed name vanished from its own basket instead of refusing it: "
        f"{got!r} / {note!r}")


def test_the_basket_is_equal_weight_not_return_weighted() -> None:
    """Equal DOLLARS at entry — the mean of member returns. A cap- or price-weighted read would
    answer a different counterfactual while printing the same words."""
    basket = Basket("quality", ("AAA", "BBB"), {"AAA": "SEC-AAA", "BBB": "SEC-BBB"})
    bars = {"AAA": _bars("SEC-AAA", 10.0, 20.0),      # +100%, cheap share price
            "BBB": _bars("SEC-BBB", 1000.0, 1000.0)}  # flat, expensive share price
    got, note = basket_return(basket, bars, ENTRY_D, EXIT_D)
    assert note is None
    assert got == pytest.approx(0.50), (
        f"read {got} — a price-weighted basket would land near 0.0099 here, an equal-weight one "
        f"at 0.50")


# --------------------------------------------------------------------------------------------
# 5. Both production paths
# --------------------------------------------------------------------------------------------

def test_every_score_ledger_call_site_supplies_a_basket() -> None:
    """#378'S LESSON, MADE MECHANICAL. `by_sleeve` once existed in `to_dict()` alone, so a resolved
    followed verdict was correctly excluded from the primary and then invisible to every reader.

    The same shape is available here: `vinci score` and `run_monthly` are BOTH default paths, and a
    basket wired into one leaves the other's report silently comparator-less. AST-scoped rather than
    grep-scoped so a call spanning several lines still reads as one call.
    """
    missing: list[str] = []
    for path in sorted((ROOT / "vinci").rglob("*.py")):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", None)
            if name != "score_ledger":
                continue
            if not any(kw.arg == "baskets" for kw in node.keywords):
                missing.append(f"{path.relative_to(ROOT)}:{node.lineno}")
    assert not missing, (
        f"score_ledger call site(s) with no `baskets=`: {missing}. Every default path must supply "
        f"the passive comparator, or the book's own kill test is missing from that path's report.")


def test_the_score_command_renders_the_baseline_end_to_end(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`vinci score` is the path a human actually runs. Pinned on its STDOUT, so wiring that
    type-checks but never reaches the printed report still fails here."""
    from vinci import cli

    followed = _followed_file(tmp_path, {"AAA": "quality", "BBB": "quality"})
    db = tmp_path / "s.db"
    with Store(db) as store:
        store.write_prices(_bars("IDX-IWM", 100.0, 105.0))
        store.write_prices(_bars("SEC-AAA", 100.0, 130.0))
        store.write_prices(_bars("SEC-BBB", 100.0, 110.0))
        # SECURITIES UPSERTED DELIBERATELY. Without them `iter_securities` is empty, the basket
        # resolves to nothing, and the report prints "unavailable" — which still contains the
        # words this test looks for. The pin would pass while proving only that a REFUSAL renders.
        for t in ("AAA", "BBB"):
            store.upsert_security(_identity(t))
        store.append_ledger(_entry("AAA", "SEC-AAA", Verdict.BUY, "quality", "followed"))
        store.append_ledger(_entry("BBB", "SEC-BBB", Verdict.PASS, "quality", "followed"))

    class _Cfg:
        db_path = db
        data_dir = followed.parent

    monkeypatch.setattr(cli, "get_config", lambda: _Cfg())
    args = argparse.Namespace(ref=EXIT_D.isoformat(), cost_bps=25.0, benchmark="IWM", json=False)
    assert cli._cmd_score(args) == 0
    out = capsys.readouterr().out
    assert "vs equal-weight follow basket (AAA, BBB): basket +20.0%" in out, (
        f"`vinci score` did not print the computed passive comparator for the quality book — a "
        f"refusal or a missing line would both be wrong here:\n{out}")


# --------------------------------------------------------------------------------------------
# 6. One file, two readers
# --------------------------------------------------------------------------------------------

def test_this_reader_and_the_dossier_reader_agree_on_the_committed_follow_list() -> None:
    """TWO PARSERS OF ONE FILE IS A BUG CLASS THIS REPO HAS PAID FOR. Checked against the LIVE
    committed corpus, not a fixture built to the shape the test wants."""
    from vinci.dossier.assemble import _follow_entry

    class _Cfg:
        data_dir = COMMITTED_FOLLOWED.parent

    mine = followed_by_sleeve(COMMITTED_FOLLOWED)
    assert mine, "data/followed.json parsed to nothing — this pin is checking an empty corpus"
    for sleeve, tickers in mine.items():
        for t in tickers:
            theirs = _follow_entry(_Cfg(), t)  # type: ignore[arg-type]
            assert theirs is not None, f"{t}: this reader lists it, the dossier reader does not"
            assert theirs.sleeve == sleeve, (
                f"{t}: sleeve disagreement — baseline reads {sleeve!r}, dossier reads "
                f"{theirs.sleeve!r}; the basket and the page would describe different books")


@pytest.mark.parametrize(
    ("doc", "exc"),
    [
        ({"AAA": {"reason": "r", "sleeve": "quality"}, "aaa": {"reason": "r2",
                                                               "sleeve": "quality"}},
         FollowedListError),                       # case collision drops a basket member
        ({"AAA": "a bare reason string"}, FollowedListError),   # the pre-sleeve shape
        ({"AAA": {"reason": "r", "sleeve": "nonesuch"}}, UnknownSleeveError),
        ({"AAA": {"reason": "r"}}, UnknownSleeveError),         # sleeve omitted entirely
    ],
    ids=["case-collision", "bare-string", "unknown-sleeve", "sleeve-omitted"],
)
def test_the_follow_list_reader_refuses_what_the_dossier_reader_refuses(
    tmp_path: pathlib.Path, doc: dict[str, object], exc: type[Exception],
) -> None:
    """THE NEGATIVE PINS. Each shape would silently redefine a basket: a dropped member, an
    untagged name, or a name filed under a book that does not exist."""
    p = tmp_path / "followed.json"
    p.write_text(json.dumps(doc))
    with pytest.raises(exc):
        followed_by_sleeve(p)


def test_an_absent_follow_list_is_the_normal_state(tmp_path: pathlib.Path) -> None:
    """Nothing followed yet is not a failure — it is where every new deployment starts."""
    assert followed_by_sleeve(tmp_path / "nope.json") == {}


def test_the_baseline_uses_each_verdicts_own_window(tmp_path: pathlib.Path) -> None:
    """THE PAIRING THAT MAKES THE COMPARISON HONEST. Two BUYs entered months apart must each be
    compared to the basket over THEIR window; one basket return reused across both would compare
    the judgement's windows to a window nobody held."""
    followed = _followed_file(tmp_path, {"AAA": "quality"})
    late = ENTRY_D + timedelta(days=90)
    with Store(tmp_path / "s.db") as store:
        store.write_prices(_bars("IDX-IWM", 100.0, 105.0))
        # The EARLY row's horizon lands on HORIZON_D; the LATE row's horizon falls beyond `as_of`,
        # so it scores at EXIT_D. Distinct closes on both dates make the two windows separable.
        store.write_prices([
            PriceBar(internal_id="SEC-AAA", bar_date=d, open=c, high=c + 1, low=c - 1, close=c,
                     volume=1e6, source="t")
            for d, c in ((ENTRY_D, 100.0), (HORIZON_D, 120.0), (EXIT_D, 130.0))])
        store.append_ledger(_entry("AAA", "SEC-AAA", Verdict.BUY, "quality", "followed"))
        early = _entry("AAA", "SEC-AAA", Verdict.BUY, "quality", "followed").model_copy(
            update={"entry_id": "V-AAA-late", "entry_price_as_of": late,
                    "decided_at": datetime.combine(late, datetime.min.time())})
        store.append_ledger(early)
        baskets = resolve_baskets(followed, [_FakeIdentity("AAA", "SEC-AAA")])  # type: ignore[arg-type]
        scores, _r = score_ledger(store, as_of=EXIT_D, baskets=baskets)

    by_id = {s.entry_id: s.basket_return for s in scores}
    assert by_id["V-AAA"] == pytest.approx(0.20), by_id       # ENTRY_D 100 → HORIZON_D 120
    assert by_id["V-AAA-late"] == pytest.approx(0.30), by_id  # late (still 100) → EXIT_D 130
    assert by_id["V-AAA"] != by_id["V-AAA-late"], (
        "both verdicts got the same basket return — the window is not being read per row")
