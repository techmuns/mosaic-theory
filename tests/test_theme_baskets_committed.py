"""The frozen theme baskets AND the ratification ledger are COMMITTED — decisions 2026-08-12.

WHY THE STANDING RULE WAS REVERSED. `.gitignore` named the ratification ledger and the frozen
baskets local-only. Stage-4's entire product is a number that accrues over CALENDAR TIME, and its
input therefore existed on exactly one machine: on any other checkout the accrual could not be
computed at all. Three themes froze in July 2026 and two passed their 30-day horizon in early
August with their diagnostics still reading "0 days forward from freeze" for precisely that reason.
The reconstruction path that closed the gap (#412) works ONLY for hold-none freezes, so the first
RATIFIED theme would have had no durable record of its BUY leg's entry dates anywhere.

REVERSED FOR THE BASKETS FIRST, THEN THE LEDGER. The basket says which names are in which cohort;
the ledger says WHY, in the analyst's own words, one appended row at a time — and `--ledger` was
REQUIRED and arbitrary, so the three July 2026 ledgers went somewhere git-ignored and are gone. Only
the LOOSE `forward_*` filenames stay ignored, so an ad-hoc run still cannot commit itself.
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
        # WHAT the label contains, not how long it is (2026-09-01). This was a crude `len < 60`
        # guard, which the first MULTI-TAG driver to reach a committed basket broke on a legitimate
        # value: glp1-drug-value-chain declares `multi_tag=True`, so
        # "incumbent-franchise+next-gen-assets+manufacturing-infra+access-distribution" is 75 chars
        # of four declared tags, not prose. Length was only ever a proxy for "is this a filing
        # quote" — checking the components against the driver's OWN declared tags is the thing the
        # proxy stood for, and it still refuses a quote, which cannot be a list of declared tags.
        from vinci.themes.drivers import DRIVER_SPECS

        declared = {t for t, _ in DRIVER_SPECS[doc["driver"]].provenance_tags} | {"unspecified"}
        for ticker, label in doc["layer_of"].items():
            unknown = [part for part in label.split("+") if part not in declared]
            assert not unknown, (
                f"{p.name}: {ticker} carries layer label {label!r} whose component(s) {unknown} "
                f"are not declared tags of {doc['driver']} — a filing quote or prose has leaked "
                f"into a membership field")


def test_only_the_canonical_paths_are_tracked_not_the_loose_ad_hoc_names() -> None:
    """THE SCOPE OF BOTH DECISIONS. The canonical per-driver paths are tracked; the loose
    `forward_*` filenames and `data/forward/` stay ignored, so an ad-hoc run cannot commit itself,
    and allowing `data/themes/` must not have opened the whole directory."""
    def ignored(rel: str) -> bool:
        return subprocess.run(["git", "check-ignore", "-q", rel], cwd=ROOT).returncode == 0

    assert not ignored(f"data/{BASKETS_SUBDIR}/ai-datacenter.json"), (
        "the committed basket path is ignored — the artifact would silently never be tracked")
    assert ignored("forward_ai-datacenter_ledger.jsonl"), "a LOOSE ad-hoc ledger became tracked"
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


# --------------------------------------------------------------------------------------------
# Review findings on #422
# --------------------------------------------------------------------------------------------

def test_a_second_freeze_refuses_and_leaves_the_original_basket_intact(
    tmp_path: pathlib.Path,
) -> None:
    """OPERATOR REVIEW P1 ON #422. These are the IMMUTABLE frozen references and their per-name
    entry dates are the input to a calendar-time accrual — but every later `--worksheet` freeze
    wrote a new object over the same filename. Measured before the fix: re-freezing defense moved
    `entry_dates` from {2026-07-03} to {2026-08-12}, shifting the forward window's start by 40 days
    with nothing said. The append-only ledger does not protect this artifact, and committing it made
    the silent rewrite worse — the file now looks authoritative.

    THE SAME CLASS AS THE MONITOR SNAPSHOT OVERWRITE (#418), which this module did not learn from.
    """
    original = load_baskets(BASKETS / "truckload-supply-purge.json")
    write_baskets(original, data_dir=tmp_path)
    later = original.model_copy(update={
        "freeze_timestamp": "2026-09-01T00:00:00",
        "entry_dates": dict.fromkeys(original.entry_dates, "2026-09-01")})

    with pytest.raises(FileExistsError, match="entry dates"):
        write_baskets(later, data_dir=tmp_path)
    assert load_baskets(baskets_path(original.driver, data_dir=tmp_path)) == original, (
        "a refused re-freeze still altered the basket on disk")


def test_a_deliberate_supersession_archives_the_basket_it_replaces(
    tmp_path: pathlib.Path,
) -> None:
    """Re-freezing IS legitimate when the analyst re-dispositions a tier; losing the window it
    replaces is not. `supersede=True` archives first, so a supersession is never destructive."""
    original = load_baskets(BASKETS / "truckload-supply-purge.json")
    write_baskets(original, data_dir=tmp_path)
    later = original.model_copy(update={
        "freeze_timestamp": "2026-09-01T00:00:00",
        "entry_dates": dict.fromkeys(original.entry_dates, "2026-09-01")})

    write_baskets(later, data_dir=tmp_path, supersede=True)
    live = load_baskets(baskets_path(original.driver, data_dir=tmp_path))
    assert live == later, "the supersession did not take effect"
    archived = sorted((tmp_path / BASKETS_SUBDIR / "archive").glob("*.json"))
    assert len(archived) == 1, f"expected one archived basket, found {[a.name for a in archived]}"
    assert load_baskets(archived[0]) == original, "the archive does not hold what was replaced"
    assert original.freeze_timestamp[:10] in archived[0].name, (
        f"the archive is not named for the window it holds: {archived[0].name}")


def test_two_supersessions_on_one_day_do_not_collide_in_the_archive(
    tmp_path: pathlib.Path,
) -> None:
    """A HOLE IN MY OWN FIX, found by reading the archive name back. The freeze timestamp is
    DATE-ONLY, so two supersessions on the same day produced the same archive filename and the
    second overwrote the first — losing precisely what archiving exists to keep. Re-dispositioning
    a tier twice in one session is a normal thing to do, so this is disambiguated rather than
    assumed rare."""
    a = load_baskets(BASKETS / "truckload-supply-purge.json")
    b = a.model_copy(update={"entry_dates": dict.fromkeys(a.entry_dates, "2026-09-01")})
    c = a.model_copy(update={"entry_dates": dict.fromkeys(a.entry_dates, "2026-09-02")})
    write_baskets(a, data_dir=tmp_path)
    write_baskets(b, data_dir=tmp_path, supersede=True)   # archives `a`
    write_baskets(c, data_dir=tmp_path, supersede=True)   # archives `b`, SAME freeze date
    archived = sorted((tmp_path / BASKETS_SUBDIR / "archive").glob("*.json"))
    assert len(archived) == 2, (
        f"a same-day supersession overwrote the earlier archive: {[p.name for p in archived]}")
    # membership, not order: FrozenBaskets is unhashable (it holds dicts) and the archive
    # filenames do not sort in write order ("-2.json" precedes ".json"). What matters is that
    # BOTH replaced windows survived.
    contents = [load_baskets(p) for p in archived]
    assert a in contents and b in contents, "an archived window was lost"


def test_from_baskets_refuses_a_driver_that_is_not_the_baskets_own(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OPERATOR REVIEW P2 ON #422. Unlike the mirror — which carries only a human label and can
    therefore only WARN — this artifact holds the canonical registry key, so a mismatch is
    checkable. Before the fix, passing the defense basket with `--driver ai-datacenter` printed an
    AI-datacenter header over 108 defense names and measured them."""
    import argparse

    from vinci import cli

    args = argparse.Namespace(
        driver="ai-datacenter", worksheet=None, ledger=None, from_mirror=None,
        from_baskets=str(BASKETS / "defense-demand-shift.json"), measure=False, as_of=None,
        horizons="30", ratify_date=None, baskets_out=None, supersede_basket=False,
        exposure_names=None, watchlist=None, watchlist_triggers=None, avoid_controls=None,
        real_tier=None)
    assert cli._cmd_themes_forward(args) == 1
    out = capsys.readouterr().out
    assert "is the 'defense-demand-shift' basket, not 'ai-datacenter'" in out, out

    args.driver = "defense-demand-shift"          # the matching driver still works
    assert cli._cmd_themes_forward(args) == 0


# --------------------------------------------------------------------------------------------
# The ratification ledger — committed too (operator decision, 2026-08-12)
# --------------------------------------------------------------------------------------------

def _seed_thesis(data_dir: pathlib.Path) -> None:
    """The thesis gate (brief Item 1, 2026-08-29) binds every Stage-4 freeze — these tests freeze
    defense in a tmp data_dir, so they declare the card the gate requires. The gate's own
    behavior (refusal, message, ordering) is pinned in test_theme_thesis.py, not here."""
    from datetime import date

    from vinci.scenarios import DatedTrigger
    from vinci.themes.thesis import ThemeThesis, ThesisMechanism, stamped, write_thesis

    write_thesis(stamped(ThemeThesis(
        driver_key="defense-demand-shift", declared_date=date(2026, 8, 29),
        mechanism=ThesisMechanism.POLICY_SIDE,
        market_mistake="test-seed mistake", null_thesis="test-seed null",
        first_confirming=DatedTrigger(trigger="seed", deadline="2026-12-31"),
        falsifiers=(DatedTrigger(trigger="seed falsifier", deadline="2027-06-30"),),
    )), data_dir=data_dir)


def test_a_freeze_with_no_ledger_flag_lands_in_the_committed_home(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """THE FIX FOR HOW THE THREE JULY LEDGERS WERE LOST: `--ledger` was REQUIRED and arbitrary, so
    the analyst's dispositions went wherever the command line happened to point — and that was
    somewhere git-ignored. It now defaults to the committed home.

    The ledger is the record the BASKET is derived from: the basket says which names are in which
    cohort, the ledger says WHY, in the analyst's own words. Losing it keeps the conclusion and
    discards the judgment."""
    from vinci import cli
    from vinci.cli import build_parser
    from vinci.config import Config
    from vinci.themes.forward import ledger_path, load_ledger

    cfg = Config(data_dir=tmp_path / "data")
    cfg.ensure_dirs()
    monkeypatch.setattr(cli, "get_config", lambda: cfg)
    _seed_thesis(cfg.data_dir)
    ws = tmp_path / "ws.csv"
    ws.write_text(
        "category,ticker,cik,grade_concreteness,driver_tie,grade_fact,grade_accession,"
        "DISPOSITION,RATIONALE\n"
        "attritable-air,RCAT,1,binding-contract,driver-specific,Teal,acc-1,PASSED,priced\n")
    args = build_parser().parse_args(
        ["themes-forward", "--worksheet", str(ws), "--driver", "defense-demand-shift",
         "--ratify-date", "2026-08-12"])
    assert args.func(args) == 0

    lp = ledger_path("defense-demand-shift", data_dir=cfg.data_dir)
    assert lp.is_file(), "the freeze wrote no ledger — the dispositions have no durable home"
    rows = load_ledger(lp)
    assert len(rows) == 1
    assert rows[0].rationale == "priced", "the analyst's reasoning did not survive the write"
    assert rows[0].source_ref == "acc-1", "the accession did not survive"


def test_an_explicit_ledger_path_still_wins(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The default is a floor, not a cage — an ad-hoc run can still point somewhere else."""
    from vinci import cli
    from vinci.cli import build_parser
    from vinci.config import Config
    from vinci.themes.forward import ledger_path, load_ledger

    cfg = Config(data_dir=tmp_path / "data")
    cfg.ensure_dirs()
    monkeypatch.setattr(cli, "get_config", lambda: cfg)
    _seed_thesis(cfg.data_dir)
    ws = tmp_path / "ws.csv"
    ws.write_text(
        "category,ticker,cik,grade_concreteness,driver_tie,grade_fact,grade_accession,"
        "DISPOSITION,RATIONALE\n"
        "attritable-air,RCAT,1,binding-contract,driver-specific,Teal,acc-1,PASSED,priced\n")
    elsewhere = tmp_path / "adhoc.jsonl"
    args = build_parser().parse_args(
        ["themes-forward", "--worksheet", str(ws), "--ledger", str(elsewhere),
         "--driver", "defense-demand-shift", "--ratify-date", "2026-08-12"])
    assert args.func(args) == 0
    assert len(load_ledger(elsewhere)) == 1
    assert not ledger_path("defense-demand-shift", data_dir=cfg.data_dir).exists(), (
        "an explicit --ledger ALSO wrote the canonical file — two ledgers for one freeze is two "
        "records of one judgment")


def test_a_bare_ledger_flag_is_still_refused() -> None:
    """`--ledger` with no `--worksheet` has nothing to append. Kept (reversed, not deleted) from
    review P2 on #412, where it died on `Path(None)` with an unrelated TypeError."""
    import argparse

    from vinci import cli

    args = argparse.Namespace(
        driver="defense-demand-shift", worksheet=None, ledger="l.jsonl", from_mirror=None,
        from_baskets=None, measure=False, as_of=None, horizons="30", ratify_date=None,
        baskets_out=None, supersede_basket=False, exposure_names=None, watchlist=None,
        watchlist_triggers=None, avoid_controls=None, real_tier=None)
    with pytest.raises(SystemExit, match="nothing to write"):
        cli._cmd_themes_forward(args)


def test_the_ledger_path_is_tracked_and_the_loose_names_are_not() -> None:
    """The decision extended to the ledger; the LOOSE `forward_*` filenames stay ignored, so an
    ad-hoc run still cannot accidentally commit itself."""
    from vinci.themes.forward import LEDGER_SUBDIR

    def ignored(rel: str) -> bool:
        return subprocess.run(["git", "check-ignore", "-q", rel], cwd=ROOT).returncode == 0

    assert not ignored(f"data/{LEDGER_SUBDIR}/defense-demand-shift.jsonl"), (
        "the committed ledger path is ignored — dispositions would silently never be tracked")
    assert ignored("forward_defense_ledger.jsonl"), "a loose ad-hoc ledger became tracked"
    assert ignored("data/themes/scratch.json"), "allowing the ledger opened the whole directory"


def test_the_three_july_ledgers_are_absent_and_not_fabricated() -> None:
    """THE HONEST GAP, pinned so nobody later mistakes silence for loss-of-nerve or fills it in.

    A ledger is an APPEND-ONLY record whose value is that it records what was appended and WHEN. A
    rebuild from the published mirror would carry one synthetic timestamp for every row and no
    correction history — committing that as "the ledger" would misrepresent the artifact at the
    moment it starts being trusted. The dispositions themselves survive in the mirrors
    (`rationale`, `gradeFact`, `accession` per name), which is the honest surviving record."""
    from vinci.themes.forward import LEDGER_SUBDIR

    # UPDATED DELIBERATELY 2026-09-01, exactly as this pin's own message instructs. The three JULY
    # ledgers are still absent and still must not be fabricated. `glp1-drug-value-chain` is a
    # different thing: it was frozen from a REAL analyst worksheet on 2026-09-01 (44 dispositioned
    # rows, 15 ratified / 29 passed, zero pending), so its ledger records what was appended and
    # when — the property the July rebuilds could not have had. Naming the July three rather than
    # asserting an empty directory keeps the pin pointed at the fabrication it exists to prevent,
    # instead of at any freeze that ever happens again.
    july = {"ai-datacenter.jsonl", "defense-demand-shift.jsonl", "truckload-supply-purge.jsonl"}
    live = sorted(p.name for p in (ROOT / "data" / LEDGER_SUBDIR).glob("*.jsonl")) \
        if (ROOT / "data" / LEDGER_SUBDIR).is_dir() else []
    assert not (july & set(live)), (
        f"a ratification ledger appeared for a July 2026 theme: {sorted(july & set(live))}. Those "
        f"files were lost; if one has been RE-FROZEN from a real worksheet that is good — update "
        f"this pin deliberately rather than deleting it.")
    # and the mirrors still carry what survived, so the gap is documented rather than total
    mirror = json.loads((ROOT / "frontend" / "themes" / "defense.json").read_text())
    assert all(n.get("rationale") for n in mirror["names"]), (
        "the mirrors no longer carry the per-name rationale — the last surviving record of the "
        "three lost ledgers' judgment")


def _freeze_fixture(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch):
    """A config redirected to tmp plus a one-name dispositioned worksheet."""
    from vinci import cli
    from vinci.config import Config

    cfg = Config(data_dir=tmp_path / "data")
    cfg.ensure_dirs()
    monkeypatch.setattr(cli, "get_config", lambda: cfg)
    _seed_thesis(cfg.data_dir)
    ws = tmp_path / "ws.csv"
    ws.write_text(
        "category,ticker,cik,grade_concreteness,driver_tie,grade_fact,grade_accession,"
        "DISPOSITION,RATIONALE\n"
        "attritable-air,RCAT,1,binding-contract,driver-specific,Teal,acc-1,PASSED,priced\n")
    return cfg, ws


def _run_freeze(ws: pathlib.Path, *, driver: str = "defense-demand-shift",
                supersede: bool = False) -> int:
    from vinci.cli import build_parser

    argv = ["themes-forward", "--worksheet", str(ws), "--driver", driver,
            "--ratify-date", "2026-08-12"]
    if supersede:
        argv.append("--supersede-basket")
    args = build_parser().parse_args(argv)
    rc = args.func(args)
    return int(rc)


def test_a_refused_re_freeze_leaves_the_committed_ledger_untouched(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OPERATOR REVIEW P1 ON #424 — A TORN WRITE THAT MY OWN CHANGE CREATED.

    The ledger append ran BEFORE the basket write, and the basket write can refuse (the #422
    supersede guard). So a refused re-freeze left the now-COMMITTED ledger carrying dispositions
    for a basket that was never frozen, and the retry with --supersede-basket appended the same
    judgment a THIRD time. Measured before the fix: 1 row, then 2, then 3.

    Making the ledger durable is what turned a harmless local side effect into a corrupted
    permanent record — the write order had to follow the durability decision, and did not.

    Everything that can fail is preflighted now; the ledger and the basket land as ONE successful
    freeze."""
    from vinci.themes.forward import ledger_path, load_ledger

    cfg, ws = _freeze_fixture(tmp_path, monkeypatch)
    lp = ledger_path("defense-demand-shift", data_dir=cfg.data_dir)

    assert _run_freeze(ws) == 0
    assert len(load_ledger(lp)) == 1

    assert _run_freeze(ws) == 1, "the second freeze was not refused"
    assert len(load_ledger(lp)) == 1, (
        "a REFUSED freeze still appended to the committed ledger — dispositions recorded for a "
        "basket that was never frozen")

    assert _run_freeze(ws, supersede=True) == 0
    assert len(load_ledger(lp)) == 2, (
        "the deliberate re-freeze did not append exactly once")


def test_a_not_ready_worksheet_writes_nothing_at_all(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The same rule at the other early exit. A tier with pending dispositions is NOT frozen, so
    committing a partial ledger for it would record judgment the analyst has not finished giving —
    and the eventual real freeze would then append a second copy of the rows that were complete."""
    from vinci.themes.forward import baskets_path, ledger_path

    cfg, ws = _freeze_fixture(tmp_path, monkeypatch)
    ws.write_text(
        "category,ticker,cik,grade_concreteness,driver_tie,grade_fact,grade_accession,"
        "DISPOSITION,RATIONALE\n"
        "attritable-air,RCAT,1,binding-contract,driver-specific,Teal,acc-1,PASSED,priced\n"
        "counter-uas,ZZZ,9,committed-capacity,indirect,x,acc-2,,\n")   # one PENDING

    assert _run_freeze(ws) == 0, "a not-ready tier should report and exit cleanly"
    assert not ledger_path("defense-demand-shift", data_dir=cfg.data_dir).exists(), (
        "a NOT-READY worksheet appended to the committed ledger — the tier was never frozen")
    assert not baskets_path("defense-demand-shift", data_dir=cfg.data_dir).exists()


def test_the_preflight_has_no_side_effects(tmp_path: pathlib.Path) -> None:
    """It must be safe to ask "would this freeze be refused?" without changing anything — otherwise
    the preflight becomes another write to order correctly."""
    from vinci.themes.forward import assert_basket_writable, baskets_path, load_baskets

    b = load_baskets(BASKETS / "truckload-supply-purge.json")
    data_dir = tmp_path / "data"
    assert_basket_writable(b.driver, data_dir=data_dir)          # no basket yet → silent
    # ASSERTED ON THE DIRECTORY TOO, not just the file — mutation finding. A preflight that
    # `mkdir`s its parent leaves the FILE absent, so a file-only assertion stayed green while the
    # check was quietly touching the tree. "Creates nothing" is the property; "the file is absent"
    # is one visible consequence of it.
    assert not data_dir.exists(), (
        f"the preflight created {data_dir} — it was only asked whether a write WOULD be refused")

    write_baskets(b, data_dir=data_dir)
    with pytest.raises(FileExistsError):
        assert_basket_writable(b.driver, data_dir=data_dir)
    assert load_baskets(baskets_path(b.driver, data_dir=data_dir)) == b, (
        "the refused preflight altered the basket on disk")
