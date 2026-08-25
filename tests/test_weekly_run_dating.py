"""THE WEEKLY RUN DATES ITSELF FROM THE DATA, AND ITS TWO MIRRORS MOVE TOGETHER.

THE OUTAGE (2026-08-03 → 08-24). Four consecutive weekly runs failed and the served queue sat
frozen at `screen_run_at 2026-08-14`. The cause was not flaky infrastructure and not a stale
artifact — it was that `vinci run-weekly` defaulted `--end` to `date.today()`. The job fires
Monday morning, so on 2026-08-24 (a Monday, 07:04 UTC — six hours before the US market opened) it
stamped the universe as-of, the `reference_date`, and every relative-return window with a date
whose newest possible bar was the previous Friday's.

`test_the_wall_clock_is_unreachable_from_the_reference_date` refused it at the gate every time. THE
FOUR FAILURES WERE THE GUARD WORKING — it kept a queue stamped with an unreachable date out of
main, which is why main's newest manifest is still `2026-08-14-01` and nothing corrupt was ever
committed. The run was structurally incapable of going green, not unlucky.

SAME DEFECT, SECOND ENTRY POINT. `_ref_of` in `assemble.py` had this exact wall-clock fallback and
was fixed in #355 ("a reference date names a moment the data reaches, never the clock"). That fix
is guarded by an AST scan — which reads `assemble.py` only. The orchestrator's entry point kept its
clock, unguarded, for as long as it took a Monday-morning cron to expose it.

NO CALENDAR IS ENCODED. `grouped_daily` returns an empty dict for a non-trading day, so weekends,
holidays and half-days answer themselves — the same trick `test_store_freshness` uses to derive its
staleness tolerance from observed bar gaps. A shipped calendar rots; the data does not.
"""
from __future__ import annotations

import argparse
import ast
import datetime as dt
import inspect
import pathlib

import pytest

from vinci.eod.client import EodClient, RawBar, last_completed_session

ROOT = pathlib.Path(__file__).resolve().parents[1]


class _Sessions(EodClient):
    """A real `EodClient` subclass — the abstract base the production code declares, not a stand-in
    shaped to the test. Only the named dates are sessions; everything else answers empty, exactly
    as Polygon does for a weekend, a holiday, or a session that has not closed."""

    def __init__(self, sessions: set[dt.date]) -> None:
        self.sessions = sessions
        self.asked: list[dt.date] = []

    def grouped_daily(self, day: dt.date) -> dict[str, RawBar]:
        self.asked.append(day)
        if day not in self.sessions:
            return {}
        return {"AAA": RawBar(ticker="AAA", open=1.0, high=1.0, low=1.0,
                              close=1.0, volume=1.0)}


# --- the derivation -----------------------------------------------------------------------------

def test_a_session_still_open_can_never_be_chosen() -> None:
    """IT PROBES FROM YESTERDAY, NEVER TODAY. Grouped-daily can return partial aggregates for a
    session in progress, and stamping a record with a date whose bars are half-formed is the
    lookahead trapdoor this repo already shut once for entry prices. Starting at `today - 1` makes
    the answer safe by construction rather than by what time the job happens to fire."""
    today = dt.date(2026, 8, 25)  # a Tuesday
    client = _Sessions({today, today - dt.timedelta(days=1)})
    assert last_completed_session(client, today=today) == dt.date(2026, 8, 24)
    assert today not in client.asked, (
        "the probe asked about TODAY — a session still open can return partial bars, and this is "
        "how a half-formed close gets stamped onto a record")


def test_the_weekend_answers_for_itself_rather_than_from_an_encoded_calendar() -> None:
    """Monday morning is the case the outage was made of. The newest completed session is Friday's,
    and nothing here knows what a weekend is — Saturday and Sunday simply return no rows."""
    monday = dt.date(2026, 8, 24)
    friday = dt.date(2026, 8, 21)
    assert last_completed_session(_Sessions({friday}), today=monday) == friday


def test_the_weekend_is_not_even_asked_about() -> None:
    """COST, NOT KNOWLEDGE — and pinned because a mutation removing the weekday skip survived
    everything else: the data rejects a Saturday anyway, so correctness never notices. What it
    costs is two API calls on every Monday-morning run. `_trading_days` in the same module skips
    weekdays for exactly this reason, so the two stay consistent."""
    monday = dt.date(2026, 8, 24)
    client = _Sessions({dt.date(2026, 8, 21)})
    assert last_completed_session(client, today=monday) == dt.date(2026, 8, 21)
    weekend = [d for d in client.asked if d.weekday() >= 5]
    assert not weekend, (
        f"the probe spent calls on {weekend} — a weekend it can reject without asking")


def test_a_stacked_holiday_is_skipped_the_same_way() -> None:
    """A Friday holiday before a weekend puts the last session three days back; the derivation does
    not care, because a holiday and a weekend are the same empty response."""
    tuesday = dt.date(2026, 8, 25)
    assert last_completed_session(
        _Sessions({dt.date(2026, 8, 20)}), today=tuesday) == dt.date(2026, 8, 20)


def test_it_raises_rather_than_guessing_a_date() -> None:
    """FAIL LOUD, NEVER FABRICATE. A guessed date here does not stay local — it propagates into
    every stamp the run writes and into the ledger behind them."""
    with pytest.raises(RuntimeError, match="no completed trading session"):
        last_completed_session(_Sessions(set()), today=dt.date(2026, 8, 25))


# --- the call site, which is where the bug actually lived ----------------------------------------

def test_run_weekly_takes_its_date_from_the_data_and_not_the_clock(
    monkeypatch: pytest.MonkeyPatch) -> None:
    """THE CALL SITE, NOT THE HELPER — the trap this session has hit repeatedly. A correct
    `last_completed_session` sitting beside a `_cmd_run_weekly` that still calls `date.today()`
    fixes nothing, and a helper-level pin stays green while the call site rots."""
    from vinci import cli

    friday = dt.date(2026, 8, 21)
    monkeypatch.setattr(cli, "PolygonEodClient",
                        type("_P", (), {"from_config": staticmethod(
                            lambda _cfg: _Sessions({friday}))}))
    seen: dict[str, object] = {}
    monkeypatch.setattr(cli, "run_weekly",
                        lambda **kw: seen.update(kw) or {"ok": True})

    rc = cli._cmd_run_weekly(argparse.Namespace(end=None, benchmark="IWM"))
    assert rc == 0
    assert seen["end"] == friday, (
        f"run-weekly dated itself {seen['end']!r} instead of the last completed session {friday} — "
        "the wall clock is back")


def test_an_explicit_end_overrides_and_spends_no_network(
    monkeypatch: pytest.MonkeyPatch) -> None:
    """`--end` is the operator's override and must not pay for a probe it does not need. Asserted
    by making any client construction an error."""
    from vinci import cli

    def _boom(_cfg: object) -> object:
        raise AssertionError("run-weekly built an EOD client despite an explicit --end")

    monkeypatch.setattr(cli, "PolygonEodClient",
                        type("_P", (), {"from_config": staticmethod(_boom)}))
    seen: dict[str, object] = {}
    monkeypatch.setattr(cli, "run_weekly", lambda **kw: seen.update(kw) or {})
    cli._cmd_run_weekly(argparse.Namespace(end="2026-07-31", benchmark="IWM"))
    assert seen["end"] == dt.date(2026, 7, 31)


def test_the_help_text_does_not_still_promise_today() -> None:
    """The flag's help said `(default: today)`. Leaving that in place would document the defect as
    the contract — and the next reader would 'fix' the code back to match the docs."""
    src = (ROOT / "vinci" / "cli.py").read_text()
    assert '"--end", help="end date YYYY-MM-DD (default: today)"' not in src
    assert "last completed session" in src


# --- the fixture is the other mirror, and it is all-or-nothing ------------------------------------

def test_the_fixture_builder_writes_nothing_until_every_series_is_built() -> None:
    """OBSERVED, NOT THEORISED. Run against a partially-refreshed store this script rewrote six
    names back to 2026-08-07, left WERN at its older 08-14 and never reached IWM at all — the
    BENCHMARK silently carrying different-vintage bars from the names measured against it, which is
    precisely what `rel_ret_vs_market` cannot survive. It wrote inside the loop and returned 1 on
    the first name with no bars. The weekly job now runs it unattended and commits the result, so a
    partial build would be committed.

    Asserted structurally: no write may happen inside the block that reads the store."""
    src = (ROOT / "scripts" / "build_price_fixture.py").read_text()
    main = next(n for n in ast.walk(ast.parse(src))
                if isinstance(n, ast.FunctionDef) and n.name == "main")
    store_blocks = [n for n in ast.walk(main)
                    if isinstance(n, ast.With)
                    and any("Store(" in ast.unparse(i.context_expr) for i in n.items)]
    assert store_blocks, "no `with Store(...)` block found — has the builder been restructured?"
    for block in store_blocks:
        writes = [ast.unparse(n) for n in ast.walk(block)
                  if isinstance(n, ast.Call) and ast.unparse(n.func).endswith("write_text")]
        assert not writes, (
            f"the fixture builder writes while still reading the store: {writes}. A name with no "
            f"bars aborts mid-loop and leaves a MIXED-VINTAGE fixture — build every series first, "
            f"write only once they all succeeded.")


def test_the_weekly_job_rebuilds_the_fixture_before_it_gates_and_commits_it() -> None:
    """BOTH MIRRORS MOVE WITH THE DATA. `frontend/` was rebuilt from the refreshed store and
    `tests/fixtures/prices/` was not — but the gate compares the freshly-screened fleet as-of
    against those committed bars (`test_maintenance_path._cfg` builds its store from them on every
    machine), so leaving them behind makes the run fail its own gate.

    ORDER IS LOAD-BEARING: the rebuild must precede the gate, because the gate step MOVES THE STORE
    ASIDE and the builder reads it."""
    wf = (ROOT / ".github" / "workflows" / "weekly-screen.yml").read_text()
    build = wf.index("scripts/build_price_fixture.py")
    gate = wf.index("Gate the refreshed artifacts")
    screen = wf.index("python -m vinci run-weekly")
    assert screen < build < gate, (
        "the price fixture must be rebuilt AFTER the screen refreshes the store and BEFORE the "
        "gate moves that store aside")
    assert "git add data/snapshots frontend tests/fixtures/prices" in wf, (
        "the rebuilt fixture is never committed — the next run would rebuild it again and the "
        "gate would keep failing on the committed one")


def test_the_fixture_and_the_committed_fleet_as_of_still_straddle() -> None:
    """THE INVARIANT THE GATE ACTUALLY CHECKS, pinned here so it is legible outside the failure.
    Every committed fixture must reach at least the newest screen run's reference_date, or the
    maintenance pins are reading bars that stop before the artifact they validate."""
    import json

    from vinci.config import get_config

    cfg = get_config()
    manifests = sorted((cfg.snapshots_dir / "screen_runs").glob("*.manifest.json"), reverse=True)
    if not manifests:
        pytest.skip("no committed screen run")
    fleet = dt.date.fromisoformat(str(json.loads(manifests[0].read_text())["reference_date"])[:10])
    for f in sorted((ROOT / "tests" / "fixtures" / "prices").glob("*.jsonl")):
        last = max(json.loads(line)["bar_date"] for line in f.read_text().splitlines() if line)
        assert dt.date.fromisoformat(last) >= fleet, (
            f"{f.name} stops at {last} but the committed fleet as-of is {fleet} — rebuild it: "
            f"python scripts/build_price_fixture.py")


def test_the_derivation_is_reachable_from_the_package_root() -> None:
    """It is exported, so a second copy never gets written next to it."""
    import vinci.eod as eod

    assert "last_completed_session" in eod.__all__
    assert inspect.isfunction(eod.last_completed_session)


def test_the_fixture_step_fetches_its_own_bars_because_the_screen_never_carries_them() -> None:
    """THE FIRST WIRING OF THIS STEP FAILED IN PRODUCTION (run 32818611056) AND THIS IS WHY.

    The weekly screen refreshes EOD for the SCREENING UNIVERSE. The price fixture covers the
    MAINTENANCE-ROUTE set — which is, by definition, the names the screen does NOT carry. Checked
    against the committed universe snapshot rather than asserted: six of the nine fixture names are
    outside it entirely (the megacaps fail the cap band, and the benchmark is a synthetic `IDX-*`
    identity that was never an SEC issuer). So the job's store can never supply them, the bare
    script aborts on the first one, and `--refresh` is a REQUIREMENT rather than a speed-up.

    Pinned at the CALL SITE — the workflow line, not the script's flag parsing — because a
    correct `--refresh` that nobody passes fixes nothing."""
    wf = (ROOT / ".github" / "workflows" / "weekly-screen.yml").read_text()
    step = wf.split("Rebuild the price fixture", 1)[1].split("- name:", 1)[0]
    assert "build_price_fixture.py --refresh" in step, (
        "the fixture step does not pass --refresh — it will abort on the first maintenance-route "
        "name the screening universe does not carry")
    assert "POLYGON_API_KEY" in step, (
        "--refresh fetches bars and needs the Polygon key in this step's env")


def test_the_fixture_set_really_does_reach_outside_the_screening_universe() -> None:
    """THE REASON THE FLAG ABOVE CANNOT BE OPTIMISED AWAY, asserted against the real committed
    corpus rather than left as a comment. If this ever became empty — every fixture name inside the
    universe — `--refresh` would be redundant and the pin above would be cargo. It is not empty:
    that is the whole shape of the maintenance route."""
    import json

    from vinci.config import get_config

    snap = get_config().snapshots_dir / "universe_snapshot.jsonl"
    if not snap.is_file():
        pytest.skip("no committed universe snapshot")
    in_universe = {json.loads(line)["internal_id"]
                   for line in snap.read_text().splitlines() if line.strip()}
    outside = []
    for f in sorted((ROOT / "tests" / "fixtures" / "prices").glob("*.jsonl")):
        first = json.loads(f.read_text().splitlines()[0])
        if first["internal_id"] not in in_universe:
            outside.append(f.stem)
    assert outside, (
        "every fixture name is inside the screening universe — if that is genuinely true the "
        "weekly job no longer needs --refresh, and this pin plus the one above should be revisited")


def test_every_fixture_series_shares_one_vintage() -> None:
    """THE BENCHMARK MUST NOT DRIFT FROM THE NAMES MEASURED AGAINST IT. `rel_ret_vs_market` compares
    a name to IWM, so a fixture where IWM stops earlier than the names silently changes every
    relative return it feeds. This is the exact corruption the old non-atomic builder produced —
    six names rewritten, WERN left three days behind, IWM never written at all."""
    import json

    fronts = {}
    for f in sorted((ROOT / "tests" / "fixtures" / "prices").glob("*.jsonl")):
        fronts[f.stem] = max(json.loads(line)["bar_date"]
                             for line in f.read_text().splitlines() if line.strip())
    assert len(set(fronts.values())) == 1, (
        f"the fixture carries mixed vintages {fronts} — rebuild it in one pass: "
        f"python scripts/build_price_fixture.py --refresh")


def test_both_pushes_rebase_so_a_slow_run_cannot_lose_a_race() -> None:
    """THE JOB TAKES ~26 MINUTES AND MAIN IS NOT FROZEN WHILE IT RUNS. The reporting step already
    rebased; the SNAPSHOT commit — the one that actually advances the queue — pushed bare, so any
    merge landing mid-run would fail the whole thing after the screen, both mirrors and the gate had
    all succeeded. Both commits carry derived data only, so replaying onto a newer main is safe."""
    wf = (ROOT / ".github" / "workflows" / "weekly-screen.yml").read_text()
    for step in ("Commit refreshed snapshots", "Report the run's outcome"):
        body = wf.split(step, 1)[1].split("- name:", 1)[0]
        assert "git pull --rebase" in body, (
            f"the {step!r} step pushes without rebasing — a merge to main during the run loses the "
            f"race and marks a successful run failed")


def test_a_name_that_flips_out_of_the_maintained_set_is_still_rebuilt(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """THE FLIP IS THE WHOLE POINT, AND IT IS INVISIBLE TODAY. `maintained_names` is `committed
    dossiers MINUS current screen candidates`, so it moves every time the screen re-ranks — MVST,
    NCNO and WERN are all inside the universe and can be admitted any week. Right now the derived
    set and the files on disk happen to MATCH, so a mutation removing the union survives every
    state-based assertion. Simulated here instead: a fixture file whose name is no longer
    maintained must still be rebuilt, or it keeps its old vintage while the rest advance and
    `_cfg` — which globs the whole directory — loads a mixed-vintage store."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_bpf", ROOT / "scripts" / "build_price_fixture.py")
    assert spec and spec.loader
    bpf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bpf)

    (tmp_path / "STILLHERE.jsonl").write_text("")   # on disk, no longer maintained
    (tmp_path / "KEPT.jsonl").write_text("")        # on disk AND maintained
    monkeypatch.setattr(bpf, "OUT_DIR", tmp_path)
    monkeypatch.setattr(bpf, "maintained_names", lambda _cfg: ["KEPT", "BRANDNEW"])

    got = bpf.names_to_rebuild(object())
    assert got == ["BRANDNEW", "KEPT", "STILLHERE"], (
        f"names_to_rebuild returned {got} — a name that flipped out of the maintained set is not "
        f"being rebuilt, so it will keep an older vintage than every other series")


def test_the_benchmark_is_not_double_counted() -> None:
    """`main` always appends the benchmark, so `names_to_rebuild` must not also return it — a
    duplicate would resolve and fetch IWM twice and break the strict zip that pairs names to
    identities."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_bpf2", ROOT / "scripts" / "build_price_fixture.py")
    assert spec and spec.loader
    bpf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bpf)
    from vinci.config import get_config

    assert bpf.BENCHMARK_SMALL not in bpf.names_to_rebuild(get_config())


def test_main_actually_calls_names_to_rebuild() -> None:
    """PIN THE CALL SITE, NOT THE HELPER — the fourth time this exact trap has bitten in this
    session. A perfectly-tested `names_to_rebuild` that `main` no longer calls is worth nothing:
    the mutation replacing the call with a bare `maintained_names(cfg)` survived every behavioural
    pin above, because those exercise the helper directly."""
    src = (ROOT / "scripts" / "build_price_fixture.py").read_text()
    main = next(n for n in ast.walk(ast.parse(src))
                if isinstance(n, ast.FunctionDef) and n.name == "main")
    called = {ast.unparse(n.func) for n in ast.walk(main) if isinstance(n, ast.Call)}
    assert "names_to_rebuild" in called, (
        "main no longer calls names_to_rebuild — the union with the existing files is bypassed and "
        "a name that flips out of the maintained set will keep a stale vintage")
    assert "maintained_names" not in called, (
        "main calls maintained_names directly, bypassing the union in names_to_rebuild")

