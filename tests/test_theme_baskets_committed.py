"""The frozen theme baskets are a COMMITTED artifact — operator decision 2026-08-12.

WHY THE STANDING RULE WAS REVERSED. `.gitignore` named the ratification ledger and the frozen
baskets local-only. Stage-4's entire product is a number that accrues over CALENDAR TIME, and its
input therefore existed on exactly one machine: on any other checkout the accrual could not be
computed at all. Three themes froze in July 2026 and two passed their 30-day horizon in early
August with their diagnostics still reading "0 days forward from freeze" for precisely that reason.
The reconstruction path that closed the gap (#412) works ONLY for hold-none freezes, so the first
RATIFIED theme would have had no durable record of its BUY leg's entry dates anywhere.

REVERSED FOR THE BASKETS ONLY. The ledger stays git-ignored — it is the analyst's raw dispositioned
worksheet output, and that is not what was decided.
"""
from __future__ import annotations

import json
import pathlib
import subprocess

import pytest

from vinci.themes.forward import BASKETS_SUBDIR, baskets_path, load_baskets, write_baskets

ROOT = pathlib.Path(__file__).resolve().parents[1]
BASKETS = ROOT / "data" / BASKETS_SUBDIR

#: The three frozen drivers, by their REGISTRY key (not the mirror slug — `defense` vs
#: `defense-demand-shift` differ, which is the binding gap recorded on #412).
FROZEN = ("ai-datacenter", "defense-demand-shift", "truckload-supply-purge")


@pytest.mark.parametrize("driver", FROZEN)
def test_every_frozen_theme_has_a_committed_basket(driver: str) -> None:
    """THE POINT OF THE DECISION: the accrual's input exists on every checkout, not one machine."""
    p = BASKETS / f"{driver}.json"
    assert p.is_file(), f"{driver} has no committed basket — the accrual has no durable input"
    b = load_baskets(p)
    assert b.driver == driver, f"{p.name} carries driver {b.driver!r}"
    assert b.all_committed, f"{driver}: an empty basket is not a record"
    assert b.freeze_timestamp, f"{driver}: no freeze timestamp"


@pytest.mark.parametrize("driver", FROZEN)
def test_a_committed_basket_states_where_it_came_from(driver: str) -> None:
    """A basket written by the FREEZE and one RECONSTRUCTED from the published mirror hold the same
    names and are not the same evidence. Committing both without saying which is which would make
    the durable record unauditable at exactly the point it starts being trusted.

    All three today are reconstructions — the freeze-time files were local-only and are gone."""
    b = load_baskets(BASKETS / f"{driver}.json")
    assert b.provenance, f"{driver}: a committed basket with no stated provenance"
    assert "RECONSTRUCTED" in b.provenance, (
        f"{driver}: provenance no longer says this is a reconstruction — if a freeze has since "
        f"rewritten it that is good, but re-read this pin rather than deleting it: {b.provenance}")


@pytest.mark.parametrize("driver", FROZEN)
def test_the_committed_basket_agrees_with_the_frontend_mirror(driver: str) -> None:
    """CROSS-CHECK AGAINST THE OTHER DURABLE ARTIFACT. The basket was derived from the mirror, so
    they must still agree on membership — if they drift, one of the two has been edited by hand."""
    slug = {"defense-demand-shift": "defense"}.get(driver, driver)
    mirror = json.loads((ROOT / "frontend" / "themes" / f"{slug}.json").read_text())
    b = load_baskets(BASKETS / f"{driver}.json")
    names = {str(n["ticker"]) for n in mirror["names"]}
    assert set(b.all_committed) == names, (
        f"{driver}: the committed basket and the frontend mirror disagree on membership — "
        f"basket-only {sorted(set(b.all_committed) - names)}, "
        f"mirror-only {sorted(names - set(b.all_committed))}")
    assert len(b.ratified) == int(str(mirror["ratifiedCount"]))
    assert set(b.watchlist) == {str(n["ticker"]) for n in mirror["names"]
                                if "watchlist" in (n.get("cohorts") or [])}


def test_the_committed_baskets_carry_no_licensed_or_verbatim_filing_text() -> None:
    """SECURITY / LICENSING, checked on the FILES rather than assumed from the schema. A basket is
    tickers, dates, cohorts and layer labels — derived analysis, which is what the private-repo rule
    permits. The verbatim 10-K grade facts and the watchlist trigger prose live in the mirror and
    the ledger, and must not have followed the names in here."""
    for p in sorted(BASKETS.glob("*.json")):
        raw = p.read_text()
        low = raw.lower()
        for marker in ("ciq", "capital iq", "api_key", "secret", "bearer "):
            assert marker not in low, f"{p.name} contains {marker!r}"
        doc = json.loads(raw)
        assert doc["watchlist_triggers"] == {}, (
            f"{p.name} carries verbatim trigger prose — the basket is a membership record; the "
            f"trigger text belongs to the mirror and the ledger")
        # a crude length guard: any single string long enough to be a filing quote
        longest = max((len(v) for v in doc["layer_of"].values()), default=0)
        assert longest < 60, f"{p.name}: a layer label of {longest} chars looks like prose"


def test_the_ledger_is_still_ignored_and_the_basket_path_is_not() -> None:
    """THE DECISION WAS SCOPED TO THE BASKETS. A `.gitignore` edit that swept the ratification
    ledger in with them would commit the analyst's raw dispositioned worksheet output, which is not
    what was decided — and the ledger is the one artifact that could carry a name's disposition
    before the operator has published it."""
    def ignored(rel: str) -> bool:
        return subprocess.run(["git", "check-ignore", "-q", rel], cwd=ROOT).returncode == 0

    assert not ignored(f"data/{BASKETS_SUBDIR}/ai-datacenter.json"), (
        "the committed basket path is ignored — the artifact would silently never be tracked")
    assert ignored("forward_ai-datacenter_ledger.jsonl"), "the ratification ledger became tracked"
    assert ignored("data/forward/anything.json"), "the local-only forward dir became tracked"
    assert ignored("data/themes/scratch.json"), (
        "allowing data/themes/ opened the whole directory — only the baskets subdir is tracked")


def test_write_then_load_round_trips(tmp_path: pathlib.Path) -> None:
    """The durable record must survive the trip it exists to make."""
    b = load_baskets(BASKETS / "truckload-supply-purge.json")
    p = write_baskets(b, data_dir=tmp_path)
    assert p == baskets_path(b.driver, data_dir=tmp_path)
    assert load_baskets(p) == b


def test_the_basket_is_written_under_the_given_data_dir(tmp_path: pathlib.Path) -> None:
    """MUTATION FINDING — the fourth pin in this sequence that proved nothing, same root cause.

    The round-trip above compares `write_baskets(...)` to `baskets_path(...)`, and those two move
    TOGETHER: point the path helper back at `Path.cwd()` and both answers change identically, so
    the assertion holds while every write lands in the repo instead of the caller's directory. That
    is not hypothetical — the first cut of this feature did exactly that, and an existing CLI test
    wrote four synthetic names over the real committed basket.

    Asserted on the property that matters: the file is UNDER the data dir it was handed."""
    b = load_baskets(BASKETS / "truckload-supply-purge.json")
    p = write_baskets(b, data_dir=tmp_path)
    assert p.is_relative_to(tmp_path), (
        f"the basket was written to {p}, outside the data dir it was given ({tmp_path}) — a write "
        f"that escapes its configured root lands in the repo when a test or a script runs it")
    assert not (ROOT / "data" / BASKETS_SUBDIR / "should-not-exist.json").exists()
