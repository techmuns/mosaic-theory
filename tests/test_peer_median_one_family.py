"""THE OPERATOR'S RULING ON ONE-FAMILY PEERS (2026-11-10, on #953; Codex's P1, answered halfway).

A peer that tags only one of the two families (COST and TJX goodwill only; NFLX and BHIC intangibles
only):
1. is SHOWN with that one leg, labelled ("goodwill only" / "intangibles only"), as the subject page
   states its own headroom;
2. is left OUT of the goodwill-plus-intangibles medians — a partial total pulls them down — and
   every median says how many peers it covers ("median of 6 of 9 peers");
3. stays IN the impairment base rate, which no longer depends on the acquired total at all: a peer
   is counted where its write-down history was measured over a current window, and that window
   ends at the filer's latest balance date, never at a balance it stopped tagging.

The builder pins drive the real `build_peer_capital_intensity` over synthetic companyfacts; the
page pins read the committed pages.
"""
from __future__ import annotations

import json
import pathlib
import statistics
from datetime import date
from typing import Any

from vinci.dossier.capital_allocation import build_peer_capital_intensity
from vinci.dossier.schemas import PeerRow

ROOT = pathlib.Path(__file__).resolve().parents[1]
END = date(2026, 3, 31)


def _inst(*rows: tuple[str, float]) -> dict[str, Any]:
    return {"units": {"USD": [{"end": e, "val": v, "filed": e, "form": "10-Q", "accn": "x"}
                              for e, v in rows]}}


def _annual(tag_rows: list[tuple[int, float]]) -> dict[str, Any]:
    return {"units": {"USD": [{"start": f"{y - 1}-04-01", "end": f"{y}-03-31", "val": v,
                               "filed": f"{y}-05-01", "form": "10-K", "fy": y, "fp": "FY",
                               "accn": f"a{y}"} for y, v in tag_rows]}}


def _facts(**tags: dict[str, Any]) -> dict[str, Any]:
    return {"facts": {"us-gaap": tags}}


class _Res:
    def __init__(self, t: str) -> None:
        self.cik = t


def _built(specs: dict[str, tuple[float, dict[str, Any]]]) -> Any:
    grid = [PeerRow(name=t, ticker=t, market_cap=mc, is_name=(t == "SUBJ"))
            for t, (mc, _f) in specs.items()]
    facts = {t: f for t, (_mc, f) in specs.items()}
    return build_peer_capital_intensity(grid, resolve=lambda t: _Res(t),
                                        companyfacts=lambda c: facts[c])


def _both(gw: float, it: float, assets: float) -> dict[str, Any]:
    return _facts(Goodwill=_inst((str(END), gw)),
                  FiniteLivedIntangibleAssetsNet=_inst((str(END), it)),
                  Assets=_inst((str(END), assets)))


ZERO_CHARGES = [(y, 0.0) for y in range(2022, 2027)]


def test_a_one_family_peer_is_shown_but_left_out_of_the_medians() -> None:
    """(+) Two peers with both legs and one with goodwill alone: the lone leg is shown, labelled;
    the medians and their counts are over the two."""
    pc = _built({
        "SUBJ": (2000.0, _both(500e6, 100e6, 2e9)),
        "BOTH1": (5000.0, _both(1000e6, 0.0 + 200e6, 4e9)),     # 30% of assets
        "BOTH2": (5000.0, _both(500e6, 500e6, 2e9)),            # 50%
        "GWONL": (5000.0, _facts(Goodwill=_inst((str(END), 100e6)),
                                 Assets=_inst((str(END), 10e9)))),   # 1% — would pull it down
    })
    gw = next(r for r in pc.rows if r.ticker == "GWONL")
    assert gw.acquired == 100.0 and gw.pct_assets is not None
    assert gw.note == "goodwill only — the filer tags no intangible balance"
    assert pc.n_all == 2 and pc.median_all_assets == statistics.median([0.3, 0.5])
    assert pc.n_large == 2 and pc.median_large_assets == statistics.median([0.3, 0.5])


def test_the_base_rate_counts_every_peer_measured_over_a_current_window() -> None:
    """(+) THE DECOUPLING: a large peer whose two balances share no current date states no total
    — and is still in the base rate, because its write-downs were measured; so is a one-family
    peer. The base rate never read the acquired total; it read the median population."""
    stale_it = _facts(Goodwill=_inst((str(END), 400e6)),
                      IntangibleAssetsNetExcludingGoodwill=_inst(("2019-12-31", 50e6)),
                      Assets=_inst((str(END), 4e9)),
                      GoodwillImpairmentLoss=_annual(ZERO_CHARGES))
    gw_only = _facts(Goodwill=_inst((str(END), 400e6)), Assets=_inst((str(END), 4e9)),
                     GoodwillImpairmentLoss=_annual([(2025, 30e6)]))
    pc = _built({"SUBJ": (2000.0, _both(500e6, 100e6, 2e9)),
                 "STALE": (5000.0, stale_it), "GWONL": (5000.0, gw_only)})
    stale = next(r for r in pc.rows if r.ticker == "STALE")
    assert stale.acquired is None and str(stale.note).startswith("no shared balance")
    assert pc.n_all == 0                                   # neither is in the medians
    assert (pc.imp_n_large_assessed, pc.imp_n_large_charged) == (2, 1)


def test_the_window_ends_at_the_filers_latest_balance_never_a_stale_one() -> None:
    """(-) A peer whose goodwill was last tagged in 2015 (ROST's shape) and whose Assets run to
    2026: its write-down window ends in 2026, so five zero years are an explicit zero — not a
    2010–2015 window read as current."""
    pc = _built({"SUBJ": (2000.0, _both(500e6, 100e6, 2e9)),
                 "OLDGW": (5000.0, _facts(Goodwill=_inst(("2015-01-31", 3e6)),
                                          Assets=_inst((str(END), 15e9)),
                                          GoodwillImpairmentLoss=_annual(ZERO_CHARGES)))})
    row = next(r for r in pc.rows if r.ticker == "OLDGW")
    assert row.impairment is not None and row.impairment.state == "explicit-zero"
    assert row.impairment.window_end == END


def test_a_row_with_no_total_names_its_case_and_keeps_its_assets() -> None:
    """(-) Review of the ruling's delta, findings 3 and 4. A filer tagging goodwill ALONE, last in
    2015 (ROST's shape), has no CURRENT balance: there is no second family to share a date with, so
    "no shared balance" misnames it. And a row stating no total still states the Assets it reports,
    the fact the row showed before RD-D1."""
    pc = _built({"SUBJ": (2000.0, _both(500e6, 100e6, 2e9)),
                 "OLDGW": (5000.0, _facts(Goodwill=_inst(("2015-01-31", 3e6)),
                                          Assets=_inst((str(END), 15e9)))),
                 "TWO": (5000.0, _facts(Goodwill=_inst((str(END), 400e6)),
                                        IntangibleAssetsNetExcludingGoodwill=_inst(
                                            ("2019-12-31", 50e6)),
                                        Assets=_inst((str(END), 4e9))))})
    old = next(r for r in pc.rows if r.ticker == "OLDGW")
    assert old.acquired is None and old.pct_assets is None
    assert str(old.note).startswith("no current balance — goodwill is last tagged as at 2015-01-31")
    assert old.total_assets == 15000.0
    two = next(r for r in pc.rows if r.ticker == "TWO")
    assert str(two.note).startswith("no shared balance — ") and two.total_assets == 4000.0


def _page(t: str) -> dict[str, Any]:
    return json.loads((ROOT / "data" / "dossiers" / t / "dossier.json").read_text())


def test_the_committed_pages_state_each_medians_count_and_its_population() -> None:
    """END TO END: every committed page prints each median as "median of N of M peers"; on a page
    built under the ruling, its median is over the peers with both legs only (a row with no note),
    never a one-family peer's partial total."""
    from vinci.dossier.render import render_markdown
    from vinci.dossier.schemas import Dossier

    short = []                       # pages whose charge median covers fewer than all charged
    for jp in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json")):
        page = json.loads(jp.read_text())
        pc = page["mechanical"].get("peer_capital_intensity")
        if not pc or not pc.get("rows"):
            continue
        md = render_markdown(Dossier.model_validate(page))
        committed = (jp.parent / "dossier.md").read_text()
        peers = [r for r in pc["rows"] if not r.get("is_subject")]
        large = [r for r in peers if (r.get("market_cap") or 0.0) >= pc["size_floor"]]
        lines = [f"median of {pc['n_all']} of {len(peers)} peers",
                 f"median of {pc['n_large']} of {len(large)} peers"]
        # the charge median's count, and the stored median IS the median over the rows it counts
        ratios = [r["impairment"]["pct_acquired"] for r in large
                  if (r.get("impairment") or {}).get("state") == "charged"
                  and r["impairment"].get("pct_acquired") is not None]
        assert pc.get("imp_median_large_pct") == (statistics.median(ratios) if ratios else None), jp
        assert len(ratios) <= pc["imp_n_large_charged"], jp     # never "median of 4 of 3"
        if pc.get("imp_n_large_assessed"):
            lines.append(f"median of {len(ratios)} of {pc['imp_n_large_charged']} peers")
            if len(ratios) < pc["imp_n_large_charged"]:
                short.append(jp.parent.name)
        for line in lines:
            assert line in md and line in committed, (jp, line)
    assert short, "no page has a charged peer without a ratio — this pin checked nothing"
    for t in ("MCK", "AMZN", "TGT", "BURL"):           # the pages refreshed under the ruling
        pc = _page(t)["mechanical"]["peer_capital_intensity"]
        both = [r["pct_assets"] for r in pc["rows"]
                if not r.get("is_subject") and r.get("note") is None
                and r.get("pct_assets") is not None and r.get("pct_market_cap") is not None]
        assert pc["n_all"] == len(both), t
        assert pc["median_all_assets"] == (statistics.median(both) if both else None), t
