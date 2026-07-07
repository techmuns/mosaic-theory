"""Earliness-assay v0 verification — the load-bearing pieces held by STRUCTURE + synthetic math.

Network-free. Four groups:
  1. the pure quadrant/residence math (the kill-criterion metric) on synthetic series — a positive
     control (>=2q EARLY under EVERY boundary combo), a negative control (already-priced), and the
     data-gap case (a missing close is UNKNOWN, never a silent EARLY);
  2. the assemble-not-conclude guard — the AssayCard tree has nowhere to put a score/rank/verdict,
     and the assay modules import neither the ledger nor scoring (mirrors tests/test_dossier.py,
     with ``rank`` added: a quadrant is a factual label, never a ranking);
  3. the candidate terms ARE the driver's prefilter_terms (imported by identity — no drift);
  4. the efts velocity read caches to disk and a re-read is network-free.
"""

from __future__ import annotations

import ast
import re
import typing
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any, cast

import pytest
from pydantic import BaseModel

from vinci.netcache import CachedHttp
from vinci.themes import assay
from vinci.themes.assay_candidates import CANDIDATE_SPECS, PLACEBO_KEY
from vinci.themes.assay_schemas import (
    AssayCard,
    BasketMember,
    QuarterRead,
    Residence,
    TermContribution,
)
from vinci.themes.drivers import DRIVER_SPECS
from vinci.universe import recent_share_periods

# ================================================================================================
# 1. Pure quadrant / residence math
# ================================================================================================


def _quadrants(
    combo: str, velocity: list[int], ex_iwm: list[float | None], ex_spy: list[float | None]
) -> list[str]:
    """Replicate ``assay_candidate``'s per-combo classification (the load-bearing composition):
    a combo picks a price-flat threshold AND an activity-rising test."""
    flatkey, acttest = combo.split("_")
    thr = assay._PRICE_FLAT[flatkey]
    return [
        assay.classify_quadrant(
            ex_iwm[i], ex_spy[i], assay._activity_rising(velocity, i, acttest), thr
        )
        for i in range(len(velocity))
    ]


def test_activity_rising_medrise_and_sloperise() -> None:
    rising = [1, 2, 3, 4, 9]  # i=4: 9 > median(1,2,3,4)=2.5 AND positive slope over (1,2,3,4)
    assert assay._activity_rising(rising, 4, "medrise") is True
    assert assay._activity_rising(rising, 4, "sloperise") is True
    flat = [5, 5, 5, 5, 5]
    assert assay._activity_rising(flat, 4, "medrise") is False  # 5 !> median 5
    assert assay._activity_rising(flat, 4, "sloperise") is False  # zero slope !> 0
    assert assay._activity_rising(rising, 3, "medrise") is None  # i<4 => trailing window incomplete


def test_classify_quadrant_all_five() -> None:
    assert assay.classify_quadrant(0.0, 0.0, True, 0.20) == "EARLY"  # rising + flat
    assert assay.classify_quadrant(0.5, 0.5, True, 0.20) == "PRICED"  # rising + moved
    assert assay.classify_quadrant(0.0, 0.0, False, 0.20) == "QUIET"  # thin + flat
    assert assay.classify_quadrant(0.5, 0.5, False, 0.20) == "NARRATIVE"  # thin + moved
    assert assay.classify_quadrant(None, 0.0, True, 0.20) == "UNKNOWN"  # price gap
    assert assay.classify_quadrant(0.0, 0.0, None, 0.20) == "UNKNOWN"  # activity gap
    # flat is vs BOTH benchmarks: excess >= threshold on EITHER => not flat
    assert assay.classify_quadrant(0.25, 0.0, True, 0.20) == "PRICED"  # iwm moved
    assert assay.classify_quadrant(0.0, 0.25, True, 0.20) == "PRICED"  # spy moved
    # the flat30 band is looser: 0.25 excess is flat under flat30, moved under flat20
    assert assay.classify_quadrant(0.25, 0.25, True, 0.30) == "EARLY"


def test_two_quarter_early_run_under_every_combo() -> None:
    """Positive control: rising activity + flat price sits in EARLY >=2 consecutive quarters under
    EVERY boundary combo — exactly what the kill criterion looks for."""
    n = 12
    velocity = list(range(1, n + 1))  # strictly rising => rising under medrise AND sloperise
    ex: list[float | None] = [0.0] * n  # price flat under flat20 AND flat30
    for combo in assay.COMBOS:
        quads = _quadrants(combo, velocity, ex, ex)
        assert assay.early_residence(quads).longest_early_run >= 2, f"{combo}: {quads}"
        assert quads[4:] == ["EARLY"] * (n - 4)  # classified quarters are all EARLY
        assert quads[:4] == ["UNKNOWN"] * 4  # i<4 is an activity gap (incomplete window)


def test_no_early_run_when_price_already_moved() -> None:
    """Negative control: rising activity but the basket already re-rated (excess>threshold) =>
    PRICED, never EARLY, under every combo."""
    n = 12
    velocity = list(range(1, n + 1))
    ex: list[float | None] = [0.6] * n
    for combo in assay.COMBOS:
        quads = _quadrants(combo, velocity, ex, ex)
        assert assay.early_residence(quads).longest_early_run == 0
        assert "EARLY" not in quads


def test_price_gap_quarter_is_unknown_not_early() -> None:
    """A missing basket/benchmark close (None) is UNKNOWN — never silently classified as EARLY."""
    n = 8
    velocity = list(range(1, n + 1))
    ex_iwm: list[float | None] = [0.0] * n
    ex_iwm[5] = None  # a price gap at i=5
    quads = _quadrants("flat20_medrise", velocity, ex_iwm, [0.0] * n)
    assert quads[5] == "UNKNOWN"
    assert quads[4] == "EARLY" and quads[6] == "EARLY"  # neighbours still classify normally


def test_early_residence_and_divergence_age() -> None:
    q = ["QUIET", "EARLY", "EARLY", "PRICED", "EARLY", "EARLY", "EARLY"]
    res = assay.early_residence(q)
    assert res.longest_early_run == 3 and res.total_early_quarters == 5
    assert assay.divergence_age(q) == 3  # trailing contiguous EARLY run ending at the as-of
    assert assay.divergence_age([*q, "PRICED"]) is None  # last quarter not EARLY => no divergence
    assert assay.divergence_age(["PRICED"]) is None


def test_new_filers_by_quarter_counts_first_mentions_in_window() -> None:
    ordered = [(2023, 1), (2023, 2), (2023, 3)]
    firsts = {"A": (2023, 1), "B": (2023, 1), "C": (2023, 2), "D": (2022, 4)}  # D is out of window
    counts = assay.new_filers_by_quarter(firsts, ordered)
    assert counts == {(2023, 1): 2, (2023, 2): 1, (2023, 3): 0}  # D's pre-window quarter is dropped


# ================================================================================================
# 2. Assemble-not-conclude guard (schema-walk + AST import guard)
# ================================================================================================

# A conclusion = verdict / recommendation / direction / score / rating / probability / RANK. No
# assay field may carry one; a quadrant is a factual label, not a ranking (``rank`` forbidden too).
_FORBIDDEN = (
    "verdict", "recommend", "rating", "score", "direction", "probability", "conviction",
    "buy", "sell", "avoid", "target_price", "price_target", "fair_value", "upside", "downside",
    "rank",
)


def _reachable_models(root: type[BaseModel]) -> set[type[BaseModel]]:
    """Every pydantic model reachable from ``root`` via its field annotations (incl. generics)."""
    seen: set[type[BaseModel]] = set()
    stack: list[type[BaseModel]] = [root]
    while stack:
        model = stack.pop()
        if model in seen:
            continue
        seen.add(model)
        for field in model.model_fields.values():
            for anno in [field.annotation, *typing.get_args(field.annotation or object)]:
                origin = typing.get_origin(anno) or anno
                for cand in [origin, *typing.get_args(anno)]:
                    if isinstance(cand, type) and issubclass(cand, BaseModel):
                        stack.append(cand)
    return seen


def test_assay_card_has_no_conclusion_field() -> None:
    """No field anywhere in the AssayCard tree may name a verdict/score/rank/direction/prob."""
    models = _reachable_models(AssayCard)
    # non-vacuous: the walk must reach the quarter/basket/residence models AND the v1 decomposition
    assert {QuarterRead, BasketMember, Residence, TermContribution} <= models
    offenders = [
        f"{m.__name__}.{f}"
        for m in models
        for f in m.model_fields
        if any(tok in f.lower() for tok in _FORBIDDEN)
    ]
    assert not offenders, f"assay schema carries conclusion-shaped field(s): {offenders}"


def test_assay_modules_import_no_ledger_or_scoring() -> None:
    """Structural: the assay assembles + cites; it imports NEITHER the ledger NOR scoring (it cannot
    write a verdict or a score if it cannot even reach the modules that do)."""
    import vinci.themes.assay as _a
    import vinci.themes.assay_schemas as _s

    for mod in (_a, _s):
        tree = ast.parse(Path(str(mod.__file__)).read_text())
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        bad = {m for m in imported if "ledger" in m or "scoring" in m or m == "vinci.rank"}
        assert not bad, f"{mod.__name__} imports a concluding module: {bad}"


# ================================================================================================
# 3. Candidate terms track the driver's prefilter_terms (no drift)
# ================================================================================================


def test_candidate_terms_track_driver_prefilter_terms() -> None:
    """Each THEME candidate's ``terms`` ARE the matching driver's ``prefilter_terms`` (imported by
    identity) - the assay + exposure scan cannot drift. The placebo is a validation instrument
    (is_placebo, hand-authored terms, NO DriverSpec to borrow from)."""
    themes = {k: c for k, c in CANDIDATE_SPECS.items() if not c.is_placebo}
    assert set(themes) == {"ai-datacenter", "defense-demand-shift"}
    for key, cand in themes.items():
        assert cand.terms and cand.terms == DRIVER_SPECS[key].prefilter_terms
    placebo = CANDIDATE_SPECS[PLACEBO_KEY]
    assert placebo.is_placebo and placebo.terms and PLACEBO_KEY not in DRIVER_SPECS


# ================================================================================================
# 4. efts velocity read — caches to disk, network-free on re-read
# ================================================================================================


class _FakeEfts:
    """A minimal efts double (duck-typed to CachedHttp): a fixed 2-hit page; counts its calls."""

    def __init__(self) -> None:
        self.calls = 0

    def get_json(self, url: str, *, ttl_seconds: int = 0) -> dict[str, Any]:
        self.calls += 1
        return {
            "hits": {
                "total": {"value": 2},
                "hits": [
                    {"_source": {"ciks": ["123"], "file_date": "2023-05-02", "file_type": "8-K"}},
                    {"_source": {"ciks": ["456"], "file_date": "2023-06-10", "file_type": "10-Q"}},
                ],
            }
        }


def test_term_quarter_read_caches_and_is_network_free_on_reread(tmp_path: Path) -> None:
    fake = _FakeEfts()
    efts = cast(CachedHttp, fake)
    out1 = assay.term_quarter_read(efts, tmp_path, "data center", 2023, 2, max_pages=8)
    assert fake.calls == 1
    assert out1["total"] == 2
    assert out1["first_dates"] == {"0000000123": "2023-05-02", "0000000456": "2023-06-10"}
    assert out1["cik_counts"] == {"0000000123": 1, "0000000456": 1}
    assert out1["forms"] == {"8k": 1, "10k": 1}
    assert out1["capped"] is False
    # a re-read hits the on-disk cache — the stub is NEVER called again (a re-run is network-free)
    out2 = assay.term_quarter_read(efts, tmp_path, "data center", 2023, 2, max_pages=8)
    assert fake.calls == 1
    assert out2 == out1
    assert (tmp_path / f"{assay._slug('data center')}__2023Q2.json").exists()


# ================================================================================================
# 5. efts pagination — REGRESSIONS for the adversarial-review findings (real efts page = 100 hits)
# ================================================================================================


class _FakePagedEfts:
    """Offset-aware efts double: serves 100-hit pages sliced by the URL's ``from=``, with a fixed
    ``total`` and a distinct CIK per hit. Optionally makes the first ``cikless_on_page0`` hits on
    page 0 lack a ciks array. Catches by-10 stepping (overlap inflation) AND cik-less truncation."""

    def __init__(self, total: int, cikless_on_page0: int = 0) -> None:
        self.total = total
        self.cikless_on_page0 = cikless_on_page0
        self.froms: list[int] = []

    def get_json(self, url: str, *, ttl_seconds: int = 0) -> dict[str, Any]:
        m = re.search(r"[?&]from=(\d+)", url)
        frm = int(m.group(1)) if m else 0
        self.froms.append(frm)
        hits = []
        for i in range(frm, min(frm + 100, self.total)):
            src: dict[str, Any] = {"file_date": f"2023-05-{(i % 27) + 1:02d}",
                                   "file_type": "8-K" if i % 2 else "10-K"}
            if not (frm == 0 and i < self.cikless_on_page0):
                src["ciks"] = [str(1000 + i)]  # a distinct CIK per hit
            hits.append({"_source": src})
        return {"hits": {"total": {"value": self.total}, "hits": hits}}


def test_pagination_steps_by_100_and_does_not_overlap(tmp_path: Path) -> None:
    """REGRESSION (review #1, HIGH): efts pages are 100 hits, not 10. Stepping by 100 with a
    position-vs-total stop enumerates each distinct CIK EXACTLY once — no ~8x overlap inflation."""
    fake = _FakePagedEfts(total=250)
    out = assay.term_quarter_read(cast(CachedHttp, fake), tmp_path, "t", 2023, 2, max_pages=8)
    assert fake.froms == [0, 100, 200]  # stepped by 100, stopped when (page+1)*100 >= total
    assert out["total"] == 250
    assert len(out["cik_counts"]) == 250  # every distinct CIK enumerated once...
    assert set(out["cik_counts"].values()) == {1}  # ...and counted exactly once (no inflation)
    assert len(out["first_dates"]) == 250
    assert out["capped"] is False


def test_pagination_cikless_hits_do_not_truncate(tmp_path: Path) -> None:
    """REGRESSION (review #2, HIGH): a page carrying cik-less hits must NOT stop pagination early —
    the stop is by POSITION vs total, never the CIK-filtered row count."""
    fake = _FakePagedEfts(total=150, cikless_on_page0=30)
    out = assay.term_quarter_read(cast(CachedHttp, fake), tmp_path, "t", 2023, 2, max_pages=8)
    assert fake.froms == [0, 100]  # did NOT stop after page 0 despite 30 cik-less hits there
    assert len(out["cik_counts"]) == 120  # 150 total − 30 cik-less = 120 enumerated distinct CIKs
    assert out["capped"] is False  # 200 >= 150 → fully enumerated within the page cap


def test_pagination_capped_is_a_loud_lower_bound(tmp_path: Path) -> None:
    """REGRESSION: when total exceeds the page cap, ``capped`` fires (a loud LOWER BOUND) and the
    enumeration is exactly the pages fetched — never silently complete."""
    fake = _FakePagedEfts(total=2000)
    out = assay.term_quarter_read(cast(CachedHttp, fake), tmp_path, "t", 2023, 2, max_pages=3)
    assert fake.froms == [0, 100, 200]  # ran the full 3-page cap
    assert out["capped"] is True  # 300 < 2000 → LOWER BOUND, flagged loudly
    assert len(out["cik_counts"]) == 300  # exactly 3 pages × 100 distinct CIKs


def test_share_periods_are_point_in_time_no_lookahead() -> None:
    """REGRESSION (review #3, MED lookahead): the assay reuses ``universe.recent_share_periods`` so
    basket cap-banding never sees shares disclosed AFTER as_of. At as_of=2022-07-01 the current and
    next quarter-end frames (disclosed later) are excluded by the ~40-day filing-lag gate."""
    keys = recent_share_periods(date(2022, 7, 1))
    assert keys, "expected some admitted share-frame periods"
    assert "CY2022Q2I" not in keys  # qe 2022-06-30, disclosed ~Aug 2022 — postdates as_of
    assert "CY2022Q3I" not in keys  # qe 2022-09-30 — a full quarter in the FUTURE
    assert keys[-1] == "CY2022Q1I"  # latest admitted = the last plausibly-filed quarter


# ================================================================================================
# 6. v1 — anchored filers, ratio, decomposition, warrant exclusion, DERATED, CLI retry loop
# ================================================================================================


def test_anchored_vs_window_relative_filers() -> None:
    """Window-relative BURNS IN a filer already active pre-window; the calendar-anchored 12q
    definition (fixed lookback) does not — the exact burn-in fix v1 adds."""
    # window 2020Q1..Q4; A active since 2019Q1 (pre-window, within 12q); B new 2020Q2; C new 2020Q4
    cik_sets: dict[tuple[int, int], set[str]] = {
        (2019, 1): {"A"}, (2019, 2): set(), (2019, 3): set(), (2019, 4): set(),
        (2020, 1): {"A"}, (2020, 2): {"A", "B"}, (2020, 3): {"A"}, (2020, 4): {"A", "C"},
    }
    win = [(2020, 1), (2020, 2), (2020, 3), (2020, 4)]
    wr = assay.window_relative_new_filers(cik_sets, win)
    an = assay.anchored_new_filers(cik_sets, win, lookback=12)
    assert wr[(2020, 1)] == 1 and wr[(2020, 3)] == 0  # A burns in at the window start
    assert an[(2020, 1)] == 0  # A seen 2019Q1 (within 12q) → NOT new under the anchored rule
    assert an[(2020, 2)] == 1 and an[(2020, 4)] == 1  # only the genuinely-new B, C
    assert assay.anchored_new_ciks(cik_sets, (2020, 2), lookback=12) == {"B"}


def test_theme_placebo_ratio_none_safe() -> None:
    assert assay.theme_placebo_ratio(10, 5) == 2.0
    assert assay.theme_placebo_ratio(0, 5) == 0.0
    assert assay.theme_placebo_ratio(7, 0) is None  # placebo = 0 → None, never ZeroDivisionError
    assert assay.theme_placebo_ratio(0, 0) is None


class _TermEfts:
    """efts double keyed by the quoted phrase in the URL: returns a fixed CIK list per term."""

    def __init__(self, by_term: dict[str, list[str]]) -> None:
        self.by_term = by_term

    def get_json(self, url: str, *, ttl_seconds: int = 0) -> dict[str, Any]:
        import urllib.parse
        m = re.search(r"[?&]q=([^&]+)", url)
        phrase = urllib.parse.unquote(m.group(1)).strip('"') if m else ""
        hits = [{"_source": {"ciks": [c], "file_date": "2021-01-01", "file_type": "8-K"}}
                for c in self.by_term.get(phrase, [])]
        return {"hits": {"total": {"value": len(hits)}, "hits": hits}}


def test_per_term_decomposition_aggregation(tmp_path: Path) -> None:
    """Decomposition = per term, how many of the quarter's NEW ciks mentioned it (aggregation from
    the cached reads); sorted desc, zero-contribution terms dropped."""
    terms = ("data center", "gpu", "cooling")
    efts = cast(CachedHttp, _TermEfts(
        {"data center": ["1", "2", "3"], "gpu": ["2", "3"], "cooling": ["9"]}))
    new_ciks = {"0000000001", "0000000002", "0000000003"}  # CIKs are zfilled to 10 by _efts_page
    contrib = assay.per_term_new_contribution(
        terms, (2021, 1), new_ciks, efts=efts, cache_root=tmp_path, max_pages=1)
    assert [(t.term, t.new_filers) for t in contrib] == [("data center", 3), ("gpu", 2)]  # cool:0


def test_warrant_unit_right_exclusion() -> None:
    """Warrant/unit/right excluded: metadata-primary (Polygon type). The type-absent suffix fallback
    fires ONLY on a >=5-char bare-class-letter shape (LIDRW/CORZR/SHAZW), so 4-char common stocks
    ending W/U/R (SNOW, PLTR, ...) are KEPT — and it is DISABLED entirely on a metadata outage."""
    assert assay.is_warrant_unit_right("LIDRW", "WARRANT")[0] is True  # metadata primary
    assert assay.is_warrant_unit_right("SNOW", "CS")[0] is False  # metadata says common → kept
    # type-absent suffix fallback: the real >=5-char rights/warrants ARE excluded (regression pins)
    for t in ("LIDRW", "CORZR", "SHAZW"):
        ex, why = assay.is_warrant_unit_right(t, None)
        assert ex is True and "suffix" in why, t
    # NEGATIVE PINS (audit fix): 4-char common stocks ending W/U/R must NOT be excluded
    for t in ("SNOW", "PLTR", "PANW", "VIEW", "FOUR", "AAPL"):
        assert assay.is_warrant_unit_right(t, None)[0] is False, t
    # OUTAGE: suffix_fallback=False disables the guess (no common mass-excluded on an outage)
    assert assay.is_warrant_unit_right("LIDRW", None, suffix_fallback=False)[0] is False
    # build_basket: metadata drops a warrant, keeps the common
    counts: Counter[str] = Counter({"0000000001": 100, "0000000002": 90})
    ct = {"0000000001": "GOODW", "0000000002": "GOOD"}
    members, drops = assay.build_basket(
        counts, ct, {"0000000001": 1e8, "0000000002": 1e8}, {"GOODW": 5.0, "GOOD": 5.0},
        price_date="2022-01-01", security_types={"GOODW": "WARRANT", "GOOD": "CS"})
    assert [m.ticker for m in members] == ["GOOD"]  # the warrant is dropped, the common kept
    assert any("warrant/unit/right" in d for d in drops)
    # OUTAGE build: security_types=None disables the suffix fallback → a >=5-char W-suffix ticker is
    # KEPT (metadata is the only authority and there is none), rather than mass-excluded on a guess.
    kept, _ = assay.build_basket(
        Counter({"0000000001": 100}), {"0000000001": "ABCDW"}, {"0000000001": 1e8},
        {"ABCDW": 5.0}, price_date="2022-01-01", security_types=None)
    assert [m.ticker for m in kept] == ["ABCDW"]


def test_derated_early_flag() -> None:
    assert assay._derated(-0.25, -0.30) is True  # both < −20%
    assert assay._derated(-0.10, -0.30) is False  # iwm not < −20%
    assert assay._derated(-0.25, -0.10) is False  # spy not < −20%
    assert assay._derated(0.30, 0.30) is False  # priced up, not derated
    assert assay._derated(None, -0.30) is False  # a price gap is never derated


def _tiny_card(*, derated: bool, excess: float) -> AssayCard:
    qr = QuarterRead(
        quarter="2021Q1", new_filers=5, new_filers_anchored=4, total_mentions=10,
        mentions_8k_family=1, mentions_10k_family=1, basket_excess_iwm=excess,
        basket_excess_spy=excess, quadrant_by_combo=dict.fromkeys(assay.COMBOS, "EARLY"),
        quadrant_by_combo_anchored=dict.fromkeys(assay.COMBOS, "EARLY"), rising_median_4q=3.0,
        rising_slope_4q=1.0, top_terms=(TermContribution(term="t", new_filers=2),),
        derated_early=derated)
    res = {c: Residence(longest_early_run=1, total_early_quarters=1) for c in assay.COMBOS}
    return AssayCard(
        candidate_key="x", as_of="2021-01-01", quarters=(qr,), basket=(), basket_rule="rule",
        residence_by_combo=res, residence_by_combo_anchored=res, residence_by_combo_symmetric=res,
        divergence_age_quarters=None)


def test_render_annotates_derated_early() -> None:
    """An EARLY + DERATED quarter renders a † on the reference-combo quadrant + a footnote; a
    non-derated EARLY quarter does not."""
    md = assay.render_markdown(_tiny_card(derated=True, excess=-0.30))
    assert "EARLY†" in md and "DERATED-EARLY" in md
    assert "EARLY†" not in assay.render_markdown(_tiny_card(derated=False, excess=0.05))


def test_assay_retry_loop_recovers_then_fails_loud(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The CLI self-healing loop retries transient efts 5xx (cache-first) and returns once a build
    succeeds; on exhaustion it fails LOUD naming the missing read."""
    from vinci.cli import _assay_with_retries
    from vinci.netcache import HttpError

    monkeypatch.setattr("time.sleep", lambda *_: None)  # no real backoff wait in the test
    card = _tiny_card(derated=False, excess=0.0)
    calls = {"n": 0}

    def build() -> AssayCard:
        calls["n"] += 1
        if calls["n"] < 3:
            raise HttpError("500 from https://efts.sec.gov/LATEST/search-index?q=%22x%22&from=100")
        return card

    assert _assay_with_retries(build, label="t", attempts=5) is card
    assert calls["n"] == 3  # failed twice, then succeeded — cache-first resumption

    def always_fail() -> AssayCard:
        raise HttpError("500 from https://efts.sec.gov/LATEST/search-index?q=%22BADQ%22")

    with pytest.raises(HttpError, match="missing read.*BADQ"):
        _assay_with_retries(always_fail, label="t", attempts=2)
