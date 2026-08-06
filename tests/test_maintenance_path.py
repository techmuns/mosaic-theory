"""A name the fund maintains stays re-assemblable after it leaves the screen band.

WHY. The cap band is an ENTRY rule — it answers where the fund HUNTS. Membership was doubling as
the maintenance key, so a dossier could not be refreshed once its name left the band. IT is the
first instance and it is the benign one: it PASSED all three gates on 2026-07-29 and then
appreciated past the $10bn ceiling ($135.11 → $165.65, implied cap $11.19bn). The instance that
matters is the one behind it — **any held position that re-rates upward becomes un-maintainable**,
so the defect bites a WINNER first.

THE FIX IS NOT A FABRICATED ROW. `CandidateRecord` means "screen-admitted"; forging one would put
an invented screen verdict under a name about to be underwritten. The maintenance route builds a
`DataRecord` instead — via `build_data_record`, the same constructor the screen's own path composes
— and carries `record=None`, so nothing anywhere can mistake it for a screen admission.

GROWN OUT AND FAILED MUST NEVER RENDER ALIKE. That is `unstated`-versus-`disagrees` again, with a
position on the other side of it, so the caveat reports the LAST REAL VERDICT and its gates rather
than the bare fact of absence.
"""
from __future__ import annotations

import json
import pathlib

import pytest

import vinci.dossier.assemble as asm
from vinci.config import get_config

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _cfg():
    return get_config()


def _candidate_tickers() -> set[str]:
    from vinci.rank import load_candidates_from_snapshot
    snaps = _cfg().snapshots_dir
    return {c.data_record.identity.ticker
            for c in load_candidates_from_snapshot(snaps / "candidate_records.jsonl")}


def _a_maintained_orphan() -> str:
    """A committed-dossier name that is NOT a current candidate — the case under test."""
    cands = _candidate_tickers()
    for p in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json")):
        if p.parent.name not in cands:
            return p.parent.name
    pytest.skip(
        "vacuous: every committed dossier is also a current screen candidate, so the maintenance "
        "route has no live case to exercise. It begins covering names as soon as one leaves the "
        "band — which is the condition it exists for, not a reason to weaken the pin.")


def test_a_maintained_name_assembles_without_a_candidate_record() -> None:
    """THE POSITIVE CASE. `load_finalists` returns a Finalist whose facts came from the store, and
    `record` is None — no `CandidateRecord` was invented to get there."""
    t = _a_maintained_orphan()
    fin = asm.load_finalists(_cfg(), ticker=t)[0]

    assert fin.record is None, (
        f"{t} routed through the maintenance path but still carries a CandidateRecord — that type "
        "asserts screen admission, and this name has none")
    assert fin.standalone is not None
    assert fin.data_record.identity.ticker == t
    # the facts assembly actually consumes must be PRESENT, not a hollow shell
    assert fin.data_record.prices.last.value, "no last price — the record would assemble to nothing"
    assert fin.data_record.prices.adv_90d_shares.value, "no 90d ADV — the liquidity denominator"


def test_the_cohort_path_maintains_the_same_names_as_the_ticker_path() -> None:
    """BOTH CALLERS, not one. The first cut taught only the `--ticker` branch, so `--ticker IT`
    assembled while `--top 20` silently dropped IT at rank 5 — the exact name the path exists for.
    That asymmetry is worse than the symmetric failure it replaced, because a cohort run would have
    reported success while omitting the name.

    Asserted through `load_finalists` itself: a maintained orphan inside the queue's top-N must
    appear in the cohort result, not merely be reachable one at a time."""
    cfg = _cfg()
    t = _a_maintained_orphan()
    queue = [json.loads(x) for x in
             (cfg.snapshots_dir / "ranked_queue.jsonl").read_text().splitlines() if x.strip()]
    queue.sort(key=lambda r: int(r.get("rank", 1_000_000)))
    tickers = [r.get("ticker") for r in queue]
    if t not in tickers:
        pytest.skip(f"{t} has no ranked-queue row, so the cohort loop never reaches it")
    depth = tickers.index(t) + 1

    got = {f.data_record.identity.ticker for f in asm.load_finalists(cfg, top=depth)}
    assert t in got, (
        f"{t} sits at queue position {depth} and is maintained, but the cohort path omitted it — "
        "`--ticker` and `--top` disagree about which names the fund can still assemble")
    fin = next(f for f in asm.load_finalists(cfg, top=depth)
               if f.data_record.identity.ticker == t)
    assert fin.record is None and fin.screen_status, (
        "the cohort path produced a Finalist without the maintenance caveat — the name would "
        "assemble with nothing on the page saying it is outside the candidate set")


def test_an_unmaintained_name_is_still_refused() -> None:
    """THE NEGATIVE. The path opens for names the fund already carries — NOT for anything absent
    from the candidate set. Without this the guard is 'assemble whatever you are asked for', which
    is the screen's whole purpose deleted."""
    cands = _candidate_tickers()
    ghost = next(t for t in ("ZZZZ", "QQQQ", "XXXX")
                 if t not in cands and not (ROOT / "data" / "dossiers" / t).exists())
    with pytest.raises(LookupError, match="not maintained"):
        asm.load_finalists(_cfg(), ticker=ghost)


def test_the_caveat_reports_the_last_real_verdict_not_the_bare_absence() -> None:
    """GROWN OUT != FAILED. The caveat must carry the last run that actually EVALUATED the name and
    what its gates said, so a reader can tell an appreciation from a rejection. A caveat that only
    said "not a candidate" would render those two identically."""
    t = _a_maintained_orphan()
    fin = asm.load_finalists(_cfg(), ticker=t)[0]
    cav = fin.screen_status or ""

    assert "NOT A CURRENT SCREEN CANDIDATE" in cav
    assert "not a rejection" in cav, "absence must not be presented as a verdict"
    assert "read the verdict, not the absence" in cav
    assert "HUNTS" in cav, "the caveat must state the band's actual scope"
    verdict = asm._last_screen_verdict(_cfg(), t)
    if verdict is not None:
        run_id, outcome = verdict
        assert run_id in cav and outcome.split(" ")[0] in cav, (
            f"the caveat omits the last real verdict ({run_id}: {outcome}) — without it, a name "
            "that PASSED and then grew out of the band reads exactly like one that FAILED")


def test_the_standalone_record_is_truncated_to_its_own_reference_date() -> None:
    """THE VINTAGE PIN, and the bug it caught. `compute_price_features` takes `bars[-1]` as
    "latest" and never filters — it uses `reference_date` only for staleness and window starts. The
    screen gets away with passing full history because at screen time the frontier IS the reference
    date. Here it is not, and the first cut stamped IT's 2026-08-04 close ($185.79) onto a
    2026-07-06 record: a value contradicting its own vintage mark, which is the class this repo
    keeps paying for.

    Asserted against the STORE, not a literal, so it cannot rot as bars accumulate."""
    import datetime as dt

    from vinci.store import Store

    t = _a_maintained_orphan()
    cfg = _cfg()
    fin = asm.load_finalists(cfg, ticker=t)[0]
    ref = fin.reference_date

    from vinci.resolver import EntityResolver
    iid = EntityResolver.from_config(cfg).resolve_ticker(t).internal_id
    with Store(cfg.db_path) as store:
        bars = store.get_price_history(iid)
    upto = [b for b in bars if b.bar_date <= ref]
    if not upto:
        pytest.skip(f"{t} has no bars at or before {ref} — nothing to compare")
    assert fin.data_record.prices.last.value == pytest.approx(upto[-1].close), (
        f"the record's last price is not the last bar at or before its own reference_date {ref} — "
        "it is carrying a price from the future of its own stamp")
    later = [b for b in bars if b.bar_date > ref]
    if later:
        assert fin.data_record.prices.last.value != pytest.approx(later[-1].close), (
            "the record carries the STORE FRONTIER's close under an older reference_date stamp")
    assert isinstance(ref, dt.date)


def test_assembly_reads_the_property_not_the_candidate_record() -> None:
    """THE CALL SITE, not the helper — the rule this session has had to learn repeatedly. A
    `Finalist` on the maintenance route has `record=None`, so any surviving `fin.record.data_record`
    raises AttributeError at assembly time on exactly the names this path exists to serve. Asserted
    on the SOURCE, because the failure is in a branch a unit test of the property never enters."""
    import inspect

    src = inspect.getsource(asm)
    assert "fin.record.data_record" not in src, (
        "assemble.py still reaches through `fin.record` for the data record; on the maintenance "
        "route `record` is None and that is an AttributeError, not a caught failure")
    assert "fin.data_record" in src, "nothing reads the property — the route is unreachable"


def test_the_maintenance_reason_names_what_makes_a_name_maintained() -> None:
    """THE KEY ITSELF: a committed dossier or an open underwrite. Both are things the fund already
    carries; neither is a screen verdict."""
    cfg = _cfg()
    t = _a_maintained_orphan()
    assert asm._maintenance_reason(cfg, t) is not None
    assert asm._maintenance_reason(cfg, "ZZZZ") is None
    # and it is keyed on the ARTIFACT, so the reason it gives is checkable
    assert (ROOT / "data" / "dossiers" / t / "dossier.json").exists()


def test_a_finalist_with_neither_source_fails_loud() -> None:
    """FAIL LOUD, never fabricate. A Finalist carrying no record at all is a construction bug; it
    must raise rather than return an empty shell that assembles into a dossier of UNKNOWNs."""
    import datetime as dt

    empty = asm.Finalist(None, rank=None, reference_date=dt.date(2026, 7, 6))
    with pytest.raises(asm.DossierAssemblyError, match="nothing to assemble"):
        _ = empty.data_record


def test_every_committed_dossier_can_still_be_located() -> None:
    """THE FLEET-WIDE CONSEQUENCE. Before this path, a committed dossier whose name had left the
    candidate set could not be re-assembled at all — the artifact was frozen. Every name the fund
    carries must now resolve by one route or the other."""
    cfg = _cfg()
    unreachable = []
    for p in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json")):
        t = p.parent.name
        try:
            asm.load_finalists(cfg, ticker=t)
        except Exception as exc:                                  # noqa: BLE001 - reported below
            unreachable.append(f"{t}: {type(exc).__name__}: {exc}")
    assert not unreachable, (
        "committed dossiers that cannot be re-assembled by either route — a frozen artifact is a "
        f"name the fund can no longer maintain: {unreachable}")


def test_the_caveat_reaches_the_artifact_as_a_caveat_not_a_qa_flag() -> None:
    """THE TIER. `screen_status` is DECISION surface — a reader who does not know the name sits
    outside the candidate set reads every screen-relative number on the page as current. It must
    land in `caveats` (main body, always printed) and must LEAD them, for the same reason a vintage
    stamp leads the block it marks: read after the numbers, it no longer changes how they are
    read."""
    import inspect

    src = inspect.getsource(asm)
    assert "caveats.insert(0, fin.screen_status)" in src, (
        "the screen-status caveat is not inserted at the head of `caveats` — either it is not a "
        "caveat at all (wrong tier: audit, not decision) or it trails the numbers it qualifies")
    # and it must NOT be routed into qa_flags, which are dev/JSON-only
    assert "qa_flags.append(fin.screen_status)" not in src
    assert "qa_flags.insert(0, fin.screen_status)" not in src


def test_the_fleet_snapshot_of_which_names_take_which_route(capsys) -> None:
    """AN INVENTORY, not an assertion about any one name. Records which committed dossiers now
    route through maintenance, so a change in that set is visible in a diff rather than silent."""
    cfg = _cfg()
    cands = _candidate_tickers()
    rows = []
    for p in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json")):
        t = p.parent.name
        rows.append((t, "candidate" if t in cands else "maintenance"))
    maint = [t for t, r in rows if r == "maintenance"]
    # the property under test: routing agrees with candidate-set membership, by construction
    for t, route in rows:
        fin = asm.load_finalists(cfg, ticker=t)[0]
        assert (fin.record is None) is (route == "maintenance"), (
            f"{t} is {route} by the candidate set but routed the other way")
    with capsys.disabled():
        print(f"\n    maintenance-route dossiers ({len(maint)}/{len(rows)}): {maint or 'none'}")


def test_json_snapshots_are_not_mutated_by_reading_them() -> None:
    """A read path must not write. `load_finalists` now touches the screen-run snapshots and the
    dossier tree; none of it may change a committed byte."""
    snaps = _cfg().snapshots_dir
    before = {p: p.read_bytes() for p in sorted(snaps.glob("*.jsonl"))}
    for p in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json")):
        asm.load_finalists(_cfg(), ticker=p.parent.name)
    after = {p: p.read_bytes() for p in sorted(snaps.glob("*.jsonl"))}
    assert before == after, "reading finalists mutated a committed snapshot"
    assert json.loads((snaps / "ranked_queue.jsonl").read_text().splitlines()[0])
