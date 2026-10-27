"""As-of invariance as PROPERTIES: a read at date d is the same read however the world after d
turns out.

`compute_fundamental_snapshot(..., as_of=d)` (#801) drops every companyfacts row FILED after d
before anything is read (`concepts.facts_as_of`). `test_fundamental_snapshot_as_of.py` shows that on
named restatements at fixed dates. These properties draw the filer, the date and the later filings,
so a change that lets ONE post-cut row reach a reader turns them red: a leg read before the cut,
the filer's newest fiscal year (`filer_fiscal_year`, #821) taken off the whole blob, a cut that
skips a namespace, an off-by-one on the filing day.

EVERY EXAMPLE IS A REAL BLOB. Each starts from a committed companyfacts fixture
(`tests/fixtures/{companyfacts,annual_pairs,stale_annual,net_debt_shapes}/`) and changes only its
rows filed after d: dropped, revalued, re-dated, re-filed later, stripped of their filing date,
moved to another of the blob's own tags, duplicated, or joined by a later 10-K reporting fiscal
years that have not happened yet. Tags come from the blob, never from `CONCEPT_ALIASES`, so the
properties hold through a change to the alias lists.

THE PRICE SIDE. `Store.close_as_of` and `relative_return` each state a cut at their reference date
and are pinned the same way, on the committed real bars (`tests/fixtures/prices/`). The one
permutation property pins a contract line that says so (`compute_price_features`, "any order").

Deterministic and bounded: `derandomize=True`, a fixed `max_examples`, no example database, no
deadline. The mutation evidence — each property red under a mutant that reads one post-cut fact —
is in `docs/records/2026-10-27-as-of-invariance-properties.md`.
"""
from __future__ import annotations

import functools
import json
import pathlib
from collections.abc import Iterator
from datetime import date, timedelta
from typing import Any, cast

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from vinci.edgar.client import EdgarClient, compute_fundamental_snapshot
from vinci.edgar.concepts import ANNUAL_MAX_DAYS, ANNUAL_MIN_DAYS, facts_as_of, filer_fiscal_year
from vinci.eod.features import compute_price_features, relative_return
from vinci.netcache import CachedHttp
from vinci.schemas.envelope import DataField
from vinci.schemas.market import PriceBar
from vinci.store.store import Store

FIXTURES = pathlib.Path(__file__).resolve().parents[1] / "tests" / "fixtures"
_FACT_DIRS = ("companyfacts", "annual_pairs", "stale_annual", "net_debt_shapes")
_BLOBS = sorted(f"{d}/{p.stem}" for d in _FACT_DIRS for p in (FIXTURES / d).glob("*.json"))
_BENCH = "IWM"
_NAMES = sorted(p.stem for p in (FIXTURES / "prices").glob("*.jsonl") if p.stem != _BENCH)
_CIK = "0000000001"

# PER BLOB, so every real blob is exercised on every run: one draw over the corpus reached 25 of the
# 61 in 150 examples (measured 2026-10-27). NOTHING TIMED: no deadline, and no `too_slow` check —
# drawing an example parses and edits a real blob, so a slow CI runner would fail it on timing.
_SETTINGS = settings(max_examples=12, derandomize=True, database=None, deadline=None,
                     suppress_health_check=[HealthCheck.too_slow])

Row = dict[str, Any]
Placed = tuple[str, str, str, Row]  # (namespace, tag, unit, row)


# --- the real blobs --------------------------------------------------------------------------


@functools.cache
def _text(blob: str) -> str:
    return (FIXTURES / f"{blob}.json").read_text()


def _load(blob: str) -> dict[str, Any]:
    """A fresh copy every call: a perturbation edits it in place."""
    facts: dict[str, Any] = json.loads(_text(blob))
    return facts


def _rows(facts: dict[str, Any]) -> Iterator[Placed]:
    for ns, tags in facts["facts"].items():
        for tag, body in tags.items():
            for unit, rows in body["units"].items():
                for r in rows:
                    yield ns, tag, unit, r


def _filed(r: Row) -> date | None:
    return date.fromisoformat(r["filed"]) if r.get("filed") else None


def _after(r: Row, d: date) -> bool:
    return (f := _filed(r)) is not None and f > d


@functools.cache
def _filing_days(blob: str) -> tuple[date, ...]:
    return tuple(sorted({f for *_, r in _rows(_load(blob)) if (f := _filed(r)) is not None}))


def _as_it_stood(facts: dict[str, Any], d: date) -> dict[str, Any]:
    """THE ORACLE, built here and not by `facts_as_of`: every row filed on or before ``d``, and no
    unit, tag or namespace left with none (an empty node would shadow a later namespace's)."""
    nsmap: dict[str, Any] = {}
    for ns, tags in facts["facts"].items():
        kept_tags: dict[str, Any] = {}
        for tag, body in tags.items():
            units = {unit: kept for unit, rows in body["units"].items()
                     if (kept := [r for r in rows if (f := _filed(r)) is not None and f <= d])}
            if units:
                kept_tags[tag] = {**body, "units": units}
        if kept_tags:
            nsmap[ns] = kept_tags
    return {**facts, "facts": nsmap}


# --- what can happen after the cut -----------------------------------------------------------

_KINDS = ("drop", "revalue", "redate", "refile", "unfile", "retag", "duplicate")
_BULK = ("none", "drop_all", "scale_all", "shift_all", "next_10k")
_VALUES = st.one_of(st.sampled_from((0.0, -1.0, 1e15, -1e15)),
                    st.floats(-1e13, 1e13, allow_nan=False))
_OPS = st.lists(st.tuples(st.sampled_from(_KINDS), st.integers(0, 10**6),
                          st.integers(-4000, 4000), _VALUES), max_size=12)


def _shift(r: Row, days: int) -> None:
    """Move a row's period by ``days``, keeping its duration (an instant has no start)."""
    for k in ("start", "end"):
        if r.get(k):
            r[k] = (date.fromisoformat(r[k]) + timedelta(days=days)).isoformat()


def _is_annual_row(r: Row) -> bool:
    if not (r.get("start") and r.get("end")):
        return False
    days = (date.fromisoformat(r["end"]) - date.fromisoformat(r["start"])).days
    return ANNUAL_MIN_DAYS <= days <= ANNUAL_MAX_DAYS


def _next_10k(facts: dict[str, Any], d: date, years: int, value: float) -> list[Placed]:
    """A 10-K filed after ``d`` reporting a fiscal year ``years`` ahead of the newest one each
    unit of each tag carries — so the WHOLE blob's newest fiscal year moves past the cut's. Filed
    a month after its own period ends, so no reader skips it as a forward-dated context."""
    newest: dict[tuple[str, str, str], Row] = {}
    for ns, tag, unit, r in _rows(facts):
        if _is_annual_row(r) and ((ns, tag, unit) not in newest
                                  or r["end"] > newest[(ns, tag, unit)]["end"]):
            newest[(ns, tag, unit)] = r
    out = []
    for (ns, tag, unit), r in newest.items():
        later = {**r, "val": value, "form": "10-K", "fp": "FY", "accn": "0000000000-99-000001"}
        _shift(later, 365 * years)
        later["fy"] = (r.get("fy") or 0) + years
        end = date.fromisoformat(later["end"])
        later["filed"] = max(d + timedelta(days=1), end + timedelta(days=30)).isoformat()
        out.append((ns, tag, unit, later))
    return out


def _later(facts: dict[str, Any], d: date, bulk: str, bulk_k: int, bulk_x: float,
           ops: list[tuple[str, int, int, float]]) -> dict[str, Any]:
    """``facts`` with ONLY its rows filed after ``d`` changed (in place, and returned). Every row it
    adds is filed after ``d`` too, so the blob as it stood on ``d`` is untouched."""
    future = [(ns, tag, unit, r) for ns, tag, unit, r in _rows(facts) if _after(r, d)]
    tags = sorted({tag for _, tag, _, _ in _rows(facts)})
    spaces = sorted({*facts["facts"], "dei", "us-gaap"})  # companyfacts' own namespace names
    dropped: set[int] = set()
    added: list[Placed] = []

    if bulk == "drop_all":
        dropped |= {id(r) for *_, r in future}
    elif bulk == "scale_all":
        for *_, r in future:
            r["val"] = (r.get("val") or 0) * (-1, 0, 10, 1e-3)[bulk_k % 4]
    elif bulk == "shift_all":
        for *_, r in future:
            _shift(r, bulk_k)
    elif bulk == "next_10k":
        added += _next_10k(facts, d, 1 + abs(bulk_k) % 4, bulk_x)

    for kind, i, k, x in ops if future else ():
        ns, tag, unit, r = future[i % len(future)]
        if kind == "drop":
            dropped.add(id(r))
        elif kind == "revalue":
            r["val"] = x
        elif kind == "redate":
            _shift(r, k)
        elif kind == "refile":
            r["filed"] = (d + timedelta(days=1 + abs(k))).isoformat()
        elif kind == "unfile":
            r.pop("filed", None)
        elif kind == "retag":  # onto another of the blob's tags, in either namespace
            dropped.add(id(r))
            to = (spaces[abs(k) // len(tags) % len(spaces)], tags[abs(k) % len(tags)])
            added.append((*to, unit, dict(r)))
        elif kind == "duplicate":
            added.append((ns, tag, unit, {**r, "val": x}))

    for by_tag in facts["facts"].values():
        for body in by_tag.values():
            for rows in body["units"].values():
                rows[:] = [r for r in rows if id(r) not in dropped]
    for ns, tag, unit, r in added:
        body = facts["facts"].setdefault(ns, {}).setdefault(tag, {"units": {}})
        body["units"].setdefault(unit, []).append(r)
    return facts


@st.composite
def _case(draw: st.DrawFn, blob: str, bulk: tuple[str, ...] = _BULK, ops: bool = True
          ) -> tuple[date, dict[str, Any], dict[str, Any]]:
    """(cut, the real blob, the same blob with only its post-cut rows changed). The cut is drawn
    ON a filing day, the day before or the day after — the boundaries — or anywhere in the blob's
    filing history; a cut that leaves nothing after it is rejected. ``ops=False`` applies the bulk
    change alone."""
    days = _filing_days(blob)
    d = draw(st.one_of(
        st.tuples(st.sampled_from(days), st.sampled_from((-1, 0, 1))).map(
            lambda t: t[0] + timedelta(days=t[1])),
        st.dates(min_value=days[0] - timedelta(days=30), max_value=days[-1])))
    assume(d < days[-1])
    later = _later(_load(blob), d, draw(st.sampled_from(bulk)), draw(st.integers(-4000, 4000)),
                   draw(_VALUES), draw(_OPS) if ops else [])
    return d, _load(blob), later


class _Http:
    def __init__(self, facts: dict[str, Any]) -> None:
        self._facts = facts

    def get_json(self, url: str, **kw: object) -> dict[str, Any]:
        assert "companyfacts" in url
        return self._facts


@functools.cache
def _dated() -> list[str]:
    """The blobs with a newest fiscal year to move: 48 of the 61 (the 13 `net_debt_shapes` carry
    balance-sheet lines only)."""
    return [b for b in _BLOBS if filer_fiscal_year(_load(b)) is not None]


def test_the_corpus_is_not_empty() -> None:
    """61 real blobs (48 with a fiscal year) and 23 named price series on 2026-10-27; an empty
    glob passes every property vacuously."""
    assert len(_BLOBS) >= 61 and len(_dated()) >= 48
    assert len(_NAMES) >= 23 and (FIXTURES / "prices" / f"{_BENCH}.jsonl").is_file()


# --- THE SNAPSHOT ----------------------------------------------------------------------------


@pytest.mark.parametrize("blob", _BLOBS)
@_SETTINGS
@given(data=st.data())
def test_a_snapshot_as_of_d_is_the_blob_as_it_stood_on_d(blob: str, data: st.DataObject) -> None:
    """CONTRACT (`compute_fundamental_snapshot`): "``as_of`` reads the facts as they stood on that
    date — every row FILED after it is dropped before anything is read".

    Both halves at once: read as of d from a blob whose post-d rows were changed, the snapshot is
    the one read with no cut from the blob as it stood on d (built here). A post-d row reaching
    any reader makes the left side differ; a row filed by d going missing makes it differ too.
    The client's as-of path (`EdgarClient.fundamental_snapshot`) reads the same."""
    d, facts, later = data.draw(_case(blob))
    want = compute_fundamental_snapshot(_CIK, _as_it_stood(facts, d))
    assert compute_fundamental_snapshot(_CIK, later, as_of=d) == want
    assert EdgarClient(cast(CachedHttp, _Http(later))).fundamental_snapshot("1", as_of=d) == want


@pytest.mark.parametrize("blob", _dated())
@_SETTINGS
@given(data=st.data())
def test_a_later_10k_never_moves_what_behind_filer_judges(blob: str, data: st.DataObject) -> None:
    """CONTRACT (`concepts.behind_filer`, through `compute_fundamental_snapshot`): an annual is
    judged against "the filer's newest fiscal year" — the one it had REPORTED by d.

    Every example adds a 10-K filed after d reporting a fiscal year one to four years past the
    blob's newest, so the whole blob's newest fiscal year is later than the cut's (checked: the
    trap is live in every example). Read as of d, every leg's staleness is still judged against
    the year the filer had reported by d. The 10-K comes ALONE: the property above mixes it with
    the other changes, and a row moved to the dei namespace can hide a tag's us-gaap rows from the
    whole blob, which would hide the trap rather than test it."""
    d, facts, later = data.draw(_case(blob, bulk=("next_10k",), ops=False))
    stood = _as_it_stood(facts, d)
    whole, cut = filer_fiscal_year(later), filer_fiscal_year(stood)
    assert whole is not None and (cut is None or whole.period_end > cut.period_end)
    assert compute_fundamental_snapshot(_CIK, later, as_of=d) == \
        compute_fundamental_snapshot(_CIK, stood)


@pytest.mark.parametrize("blob", _BLOBS)
@_SETTINGS
@given(data=st.data())
def test_the_cut_blob_is_every_row_filed_by_d_in_every_namespace(
        blob: str, data: st.DataObject) -> None:
    """CONTRACT (`concepts.facts_as_of`): "every row FILED after it removed, same shape", with
    "a unit, tag or namespace left with no row" dropped.

    At the blob, not through a reader. The snapshot reads no dei VALUE, so the property above sees a
    dei leak only when a later row moved into dei hides a us-gaap tag (`points_for_tag` takes the
    first namespace present); this sees every later dei row, on the 29 blobs that carry one."""
    d, facts, later = data.draw(_case(blob))
    assert facts_as_of(later, d) == _as_it_stood(facts, d)


# --- THE PRICE SIDE --------------------------------------------------------------------------


@functools.cache
def _bars(name: str) -> tuple[PriceBar, ...]:
    lines = (FIXTURES / "prices" / f"{name}.jsonl").read_text().splitlines()
    return tuple(PriceBar(**json.loads(line)) for line in lines)


_BAR_OPS = st.lists(st.tuples(st.sampled_from(("drop", "reprice", "add")), st.integers(0, 10**6),
                              st.integers(1, 400), st.floats(0.01, 1e6)), max_size=12)


def _later_bars(bars: tuple[PriceBar, ...], d: date, ops: list[tuple[str, int, int, float]]
                ) -> list[PriceBar]:
    """``bars`` with ONLY the bars dated after ``d`` changed; an added bar is dated after ``d``."""
    keep = [b for b in bars if b.bar_date <= d]
    after = {b.bar_date: b for b in bars if b.bar_date > d}
    for kind, i, k, x in ops:
        dates = sorted(after)
        if kind == "add" or not dates:
            on = d + timedelta(days=k)
            after[on] = PriceBar(internal_id=bars[0].internal_id, bar_date=on, open=x, high=x,
                                 low=x, close=x, volume=1.0, source="later")
        elif kind == "drop":
            del after[dates[i % len(dates)]]
        else:
            b = after[dates[i % len(dates)]]
            after[b.bar_date] = b.model_copy(update={"open": x, "high": x, "low": x, "close": x})
    return [*after.values(), *keep]  # out of order: every reader here sorts, or must


def _bar_cut(draw: st.DrawFn, bars: tuple[PriceBar, ...]) -> date:
    first, last = bars[0].bar_date, bars[-1].bar_date
    return draw(st.one_of(
        st.tuples(st.sampled_from([b.bar_date for b in bars]), st.sampled_from((-1, 0, 1))).map(
            lambda t: t[0] + timedelta(days=t[1])),
        st.dates(min_value=first - timedelta(days=10), max_value=last)))


def _close_as_of(bars: list[PriceBar], iid: str, d: date, staleness: int) -> object:
    store = Store(":memory:")
    try:
        store.write_prices(bars)
        return store.close_as_of(iid, reference_date=d, staleness_days=staleness)
    except LookupError as e:
        return ("LookupError", str(e))
    finally:
        store.close()


@pytest.mark.parametrize("name", _NAMES)
@_SETTINGS
@given(data=st.data())
def test_close_as_of_never_reaches_past_its_reference_date(name: str, data: st.DataObject) -> None:
    """CONTRACT (`Store.close_as_of`): "Latest close ON OR BEFORE ``reference_date``"; "this never
    reaches past ``reference_date``"; "if there is no bar on or before ``reference_date`` it
    raises, rather than reaching forward".

    The bars dated after the cut are dropped, repriced or joined by new ones, and the answer — a
    value, its date and staleness, or the refusal — is the one a store holding only the bars to
    the cut gives; and it is that latest bar's close."""
    bars = _bars(name)
    d = _bar_cut(data.draw, bars)
    staleness = data.draw(st.integers(0, 10))
    iid = bars[0].internal_id
    got = _close_as_of(_later_bars(bars, d, data.draw(_BAR_OPS)), iid, d, staleness)
    prior = [b for b in bars if b.bar_date <= d]
    assert got == _close_as_of(prior, iid, d, staleness)
    if not prior:
        assert isinstance(got, tuple) and got[0] == "LookupError"
    else:
        assert isinstance(got, DataField)
        assert (got.as_of, got.value) == (prior[-1].bar_date, prior[-1].close)


@pytest.mark.parametrize("name", _NAMES)
@_SETTINGS
@given(data=st.data())
def test_relative_return_never_reads_a_bar_after_its_reference_date(
        name: str, data: st.DataObject) -> None:
    """CONTRACT (`relative_return` → `features.frontier`): each series ends on "its latest bar at
    or before the reference date", and "BOTH LEGS END ON THE COMMON LAST BAR".

    The name's and the benchmark's bars after the cut are changed independently; G2's input — the
    value, its window stamp, or the refusal note — is the one read from the bars to the cut."""
    bars, bench = _bars(name), _bars(_BENCH)
    d = _bar_cut(data.draw, bars)
    lookback = data.draw(st.integers(20, 450))
    got = relative_return(_later_bars(bars, d, data.draw(_BAR_OPS)),
                          _later_bars(bench, d, data.draw(_BAR_OPS)),
                          reference_date=d, lookback_days=lookback)
    want = relative_return([b for b in bars if b.bar_date <= d],
                           [b for b in bench if b.bar_date <= d],
                           reference_date=d, lookback_days=lookback)
    assert got == want


@pytest.mark.parametrize("name", _NAMES)
@settings(_SETTINGS, max_examples=4)
@given(data=st.data())
def test_price_features_read_a_bar_history_in_any_order(name: str, data: st.DataObject) -> None:
    """CONTRACT (`compute_price_features`): "from a bar history (any order; sorted internally)".

    The only permutation property here, because it is the only reader that states one. NOT an
    as-of property: this function reads its LATEST bar whatever the reference date (record)."""
    bars = _bars(name)
    shuffled = data.draw(st.permutations(bars))
    d = _bar_cut(data.draw, bars)
    staleness, cap = data.draw(st.integers(0, 10)), data.draw(st.sampled_from((None, 1e9)))
    assert compute_price_features(list(shuffled), reference_date=d, staleness_days=staleness,
                                  market_cap=cap) == \
        compute_price_features(list(bars), reference_date=d, staleness_days=staleness,
                               market_cap=cap)
