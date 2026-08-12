"""A spot is a claim about a specific bar, and until it names one nothing can check it.

WHAT THE MEASUREMENT FOUND, because the design followed it rather than the other way round. All
eight committed records were checked against all three stores: every spot is a real EOD close,
equal to the stored bar with delta EXACTLY 0.0 — not one is an analyst's intraday number. What
differs is which store can SEE it. BRBR and EPAM are struck at 2026-08-07 and resolve in the `-sl`
store only, because this worktree's frontier is 2026-08-04. So a refuse-on-mismatch check run from
here would have blocked two CORRECT records: every spot is auditable somewhere, none is auditable
everywhere, and a refusal encodes an assumption about which store is asking. Hence notes, never
problems.

WHY THE LOOKUP IS BY DATE AND NOT BY VALUE — the first design, killed by its own corpus. Searching
for the nearest bar matching the spot's VALUE is one-to-MANY on real data (AORT's 25.37 matches two
bars sixteen months apart, MVST's 0.9188 four spanning two years, WERN's 46.04 two), and on the two
records this store cannot reach it returns a coincidental collision — an 11.55 from June for BRBR,
a 97.35 from May for EPAM. Noise presented as a finding. `prices` is keyed (internal_id, bar_date),
so by date the answer is a lookup instead of a search.

AND WHY THE DATE IS A FIELD RATHER THAN A REGEX. All eight records ALREADY name their date, inside
the `spot_source` prose — the field promotes an existing fact, it does not add one. What no rule
can do is extract it: BRBR's `spot_source` carries THREE ISO dates (the close 2026-08-07, this
worktree's frontier 2026-08-04, the date all three stores agree 2026-07-29). First-date is right
only by the accident of that sentence's wording; last-date and max-date each return something else.
The house rule ("parsers consume structured values, never rendered strings") as a live instance.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pytest

import vinci.scenarios as sc
from vinci.dossier.render import _price_store_line
from vinci.dossier.schemas import PriceStoreStamp
from vinci.schemas.market import PriceBar
from vinci.store import Store

IID = "SEC-0000000001-TEST"


@pytest.fixture
def store(tmp_path: Path) -> Store:
    """Fri 2026-07-31 and Tue 2026-08-04, with the weekend BETWEEN them rather than behind them.

    The gap has to be INTERNAL or the reach-back this file is about cannot be shown: with two
    consecutive bars, a date before both simply has nothing to reach back to and `close_as_of`
    raises instead of answering with the wrong day's price. Sat 08-01 → Mon 08-03 sit inside the
    store's coverage, and 08-05 onward is past its frontier — so coverage-hole and frontier-lag
    are both reachable, and they are different states."""
    s = Store(tmp_path / "test.db")
    s.write_prices([
        PriceBar(internal_id=IID, bar_date=date(2026, 7, 31), open=11.0, high=11.5, low=10.9,
                 close=11.11, volume=1e6, source="polygon-grouped"),
        PriceBar(internal_id=IID, bar_date=date(2026, 8, 4), open=11.2, high=11.4, low=11.1,
                 close=11.33, volume=1e6, source="polygon-grouped"),
    ])
    return s


# ─── the store: an exact-date lookup, which is the thing `close_as_of` deliberately is not ────

def test_close_on_does_not_reach_back_to_the_previous_bar(store: Store) -> None:
    """THE DEFECT THIS METHOD EXISTS FOR, and it is not hypothetical — it is how BRBR's spot passed
    its guards. `close_as_of` reaches BACKWARD to the latest bar on or before its reference date,
    which is right for freezing an entry price and wrong for auditing one: a record claiming a
    close on a date the store cannot reach gets the previous bar and reads as verified.

    2026-08-05 is past the frontier; 2026-08-02 is a Sunday inside it. Both must come back None,
    and `close_as_of` is asserted alongside to show the two really do differ — a test that only
    pinned the new method would not show that the old behaviour is the one being avoided."""
    assert store.close_on(IID, date(2026, 8, 5)) is None, "reached back past the frontier"
    assert store.close_on(IID, date(2026, 8, 2)) is None, "reached back across the weekend gap"
    # …while the reach-back method answers both, each with a DIFFERENT day's price. This is the
    # substitution an audit must not make: ask about 08-05 and be told 08-04's number as though it
    # were the answer, which is exactly how a spot dated past the frontier reads as verified.
    assert store.close_as_of(
        IID, reference_date=date(2026, 8, 5), staleness_days=30).value == pytest.approx(11.33)
    assert store.close_as_of(
        IID, reference_date=date(2026, 8, 2), staleness_days=30).value == pytest.approx(11.11)


def test_close_on_returns_the_bar_for_the_date_asked_for(store: Store) -> None:
    """The negative half: a method that returned None for everything would pass the test above."""
    assert store.close_on(IID, date(2026, 7, 31)) == pytest.approx(11.11)
    assert store.close_on(IID, date(2026, 8, 4)) == pytest.approx(11.33)


def test_a_name_the_store_has_never_heard_of_has_no_frontier(store: Store) -> None:
    """`None` frontier and a LAGGING frontier are different states and produce different notes:
    WERN has no bars at all in the `-sl` store while that store's global frontier is the newest of
    the three, so "not refreshed that far" would be the wrong sentence about it."""
    assert store.price_frontier_for("SEC-0000000009-NOPE") is None
    assert store.price_frontier_for(IID) == date(2026, 8, 4)


# ─── the notes: four states, deliberately not three ───────────────────────────────────────────

def _rec(**over: object) -> sc.ScenarioRecord:
    """A FROZEN fixture, never a committed record. Per the TEST-LAYER RULE a VALUE-level pin (this
    spot, that date) belongs on a fixture — `scenarios/*.json` are living artifacts that get
    superseded and re-struck, so pinning their numbers here would rot by design."""
    base = sc.ScenarioRecord.model_validate_json(
        Path("scenarios/SMPL.json").read_text())
    return base.model_copy(update={"spot": 11.33, "spot_as_of": date(2026, 8, 4), **over})


def _notes(rec: sc.ScenarioRecord, store: Store) -> list[str]:
    return sc.spot_notes(
        rec, store="`wb`", name_frontier=store.price_frontier_for(IID),
        bar_close=(store.close_on(IID, rec.spot_as_of) if rec.spot_as_of else None))


def test_a_spot_that_equals_its_own_bar_is_silent(store: Store) -> None:
    """THE CLEAN CASE SAYS NOTHING, as `limit_notes` does. Six of eight committed records are in
    this state; a note on each would train the reader to skip the two that matter."""
    assert _notes(_rec(), store) == []


def test_a_spot_that_differs_from_its_own_bar_is_flagged_loudly(store: Store) -> None:
    """THE STATE THE CHECK EXISTS FOR — and it fires on NOTHING in today's corpus, which is exactly
    why it is pinned here. A guard that has never fired is unproven until it is shown able to."""
    notes = _notes(_rec(spot=11.34), store)
    assert notes and "DOES NOT MATCH ITS OWN BAR" in notes[0], notes
    assert "11.3400" in notes[0] and "11.3300" in notes[0], "the note hides one of the two numbers"


def test_the_tolerance_is_float_insurance_and_not_a_price_tolerance(store: Store) -> None:
    """MEASURED, not chosen: across the six records this worktree can check, |bar − spot| is
    exactly 0.0 — the spot IS the stored bar, not a second rounding of it. So anything a cent wide
    would be inventing slack the data has never needed and would swallow a real mis-transcription.
    A tenth of a cent must already be a finding."""
    assert _notes(_rec(spot=11.33 + 4e-7), store) == []          # float round-trip: silent
    assert _notes(_rec(spot=11.33 + 1e-6), store) != []          # anything real: flagged
    assert _notes(_rec(spot=11.3310), store) != [], "a tenth of a cent passed as a match"


def test_frontier_lag_and_a_coverage_hole_do_not_read_alike(store: Store) -> None:
    """TWO STATES THAT MUST NOT RENDER ALIKE — the class this repo keeps meeting (`unstated` vs
    `disagrees`, `suppressed` vs `absent`, not-detected vs agreement).

    "This store has not refreshed that far" is BENIGN and says nothing about the record: it is the
    ordinary state of BRBR and EPAM here, and the store that wrote them holds the bar. "This store
    reaches PAST that date and still has no bar on it" is a non-trading day or a real gap. Collapse
    them and the fleet's routine lag reads like a defect, or a defect reads like routine lag."""
    lag = _notes(_rec(spot_as_of=date(2026, 8, 7)), store)       # beyond the frontier
    hole = _notes(_rec(spot_as_of=date(2026, 8, 2)), store)      # a Sunday, inside the frontier
    assert lag and "reaches only to" in lag[0] and "not a finding about the record" in lag[0], lag
    assert hole and "yet holds no bar ON it" in hole[0], hole
    assert lag[0] != hole[0]


def test_an_unstated_as_of_is_unauditable_which_is_narrower_than_unverified(store: Store) -> None:
    """THE HONEST STATE, and the wording is the whole point. Two of eight committed records carry
    no `spot_as_of` — not because their spots are doubtful (both are real closes, exact to the bar
    in the store that wrote them) but because this checkout cannot see the bar and writing a date
    it cannot verify would assert from another store's authority. The note must not imply the
    number is suspect."""
    notes = _notes(_rec(spot_as_of=None), store)
    assert notes and "UNAUDITABLE" in notes[0], notes
    assert "narrower than unverified" in notes[0], "the note overstates what is wrong"


def test_a_name_absent_from_the_store_is_not_reported_as_lag() -> None:
    """WERN's real shape in the `-sl` store: no bars for the name at all. "Reaches only to None"
    would be nonsense, and "frontier lag" would be a claim about refresh depth that is not true."""
    notes = sc.spot_notes(_rec(), store="`sl`", bar_close=None, name_frontier=None)
    assert notes and "carries NO bars for this name" in notes[0], notes


# ─── the store stamp ──────────────────────────────────────────────────────────────────────────

def test_the_stamp_shows_a_symlinked_store_as_an_arrow_not_as_one_name() -> None:
    """THE REASON BOTH PATHS ARE STORED. This checkout's `data/vinci.db` is a symlink into another
    worktree's store, so declared and resolved differ while the bytes are one file. A stamp
    carrying only the declared path would make two dossiers built from ONE store look like two;
    only the resolved path would hide that this worktree reads data it never refreshed. That is not
    a hypothetical: a corroboration check for BRBR's $11.56 asked `data/vinci.db` here, reported
    the store could not see the price, and was wrong about which store it had asked."""
    line = _price_store_line(PriceStoreStamp(
        declared_path="/x/mosaic-theory-pg/data/vinci.db",
        resolved_path="/x/mosaic-theory-wb/data/vinci.db", frontier=date(2026, 8, 4)))
    assert "mosaic-theory-pg → mosaic-theory-wb" in line, line
    assert "2026-08-04" in line


def test_an_unsymlinked_store_is_named_once_rather_than_pointing_at_itself() -> None:
    same = _price_store_line(PriceStoreStamp(
        declared_path="/x/mosaic-theory-sl/data/vinci.db",
        resolved_path="/x/mosaic-theory-sl/data/vinci.db", frontier=date(2026, 8, 7)))
    assert "→" not in same, same
    assert "mosaic-theory-sl" in same


def test_an_unstamped_dossier_says_so_rather_than_printing_nothing() -> None:
    """`extraction_version`'s rule, for the same reason: "vintage unknown" and "no divergence" must
    not look alike to a reader. Every dossier committed before this field predates it."""
    assert "unstamped" in _price_store_line(None)


def test_a_store_holding_no_bars_is_not_rendered_as_reaching_nowhere() -> None:
    line = _price_store_line(PriceStoreStamp(
        declared_path="/x/w/data/vinci.db", resolved_path="/x/w/data/vinci.db", frontier=None))
    assert "holding no bars" in line, line


# ─── the corpus, as invariants only ───────────────────────────────────────────────────────────

def test_every_committed_record_either_names_a_date_or_is_openly_unauditable() -> None:
    """AN E2E PIN ON LIVING ARTIFACTS, so it asserts a phrasing-independent INVARIANT and never a
    value: records get superseded and re-struck, and a pin on "SMPL is 11.33 as of 2026-08-04"
    would rot on the next underwrite. What must hold for any record, forever, is that the two
    states are distinguishable — a date that can be checked, or an absence that admits it."""
    recs = [p for p in sorted(Path("scenarios").glob("*.json")) if not p.stem.startswith("_")]
    assert recs, "no committed records — this test would pass vacuously"
    for p in recs:
        rec = sc.ScenarioRecord.model_validate_json(p.read_text())
        notes = sc.spot_notes(rec, store="`x`", bar_close=None, name_frontier=None)
        if rec.spot_as_of is None:
            assert notes and "UNAUDITABLE" in notes[0], f"{p.stem}: silent about having no date"
        else:
            assert not any("UNAUDITABLE" in n for n in notes), f"{p.stem}: has a date, denies it"


def test_no_committed_records_spot_as_of_was_taken_from_a_multi_dated_source_line() -> None:
    """THE BACKFILL'S OWN RULE, pinned so a later top-up cannot quietly relax it. A date was
    written only where `spot_source` states exactly ONE — BRBR's three-date prose is precisely the
    case a regex gets right by luck and a human gets right by reading."""
    import re
    for p in sorted(Path("scenarios").glob("*.json")):
        if p.stem.startswith("_"):
            continue
        rec = sc.ScenarioRecord.model_validate_json(p.read_text())
        if rec.spot_as_of is None:
            continue
        stated = set(re.findall(r"\b20\d\d-\d\d-\d\d\b", rec.spot_source))
        assert stated == {str(rec.spot_as_of)}, (
            f"{p.stem}: spot_as_of {rec.spot_as_of} against a source line naming {sorted(stated)} "
            f"— a date was taken from prose that names more than one")


# ─── THE CALL SITES, because a check nobody calls is not a check ──────────────────────────────
#
# REVIEW FINDING, and it is this repo's most-repeated rung: `test_stated_limit.py` names it as
# "the rung this repo has hit four times", and it was hit a fifth here. Every behaviour above was
# pinned on the HELPERS — `spot_notes`, `close_on`, `price_frontier_for`, `_price_store_line` —
# and NOT ONE of the three places that call them. Proven by mutation, not by inspection: deleting
# `price_store=_price_store_stamp(cfg)` from `assemble_one` left the suite at 2173 passed. The
# PR's second deliverable could be removed entirely without reddening anything.

def test_the_price_store_stamp_follows_a_symlink_rather_than_naming_the_link(
    tmp_path: Path,
) -> None:
    """EXECUTED, not inspected — the resolve is the whole reason both paths are stored.

    A real symlinked store: `declared/` points at `real/`. The stamp must record BOTH, or two
    dossiers built from ONE store compare as two. This is the case that made a corroboration check
    report "the store cannot see $11.56" while asking a store it had not identified."""
    from vinci.config import Config
    from vinci.dossier.assemble import _price_store_stamp

    real = tmp_path / "real-worktree" / "data"
    real.mkdir(parents=True)
    Store(real / "vinci.db").write_prices([
        PriceBar(internal_id=IID, bar_date=date(2026, 8, 4), open=1, high=1, low=1,
                 close=11.33, volume=1.0, source="polygon-grouped")])
    link = tmp_path / "link-worktree" / "data"
    link.mkdir(parents=True)
    (link / "vinci.db").symlink_to(real / "vinci.db")

    stamp = _price_store_stamp(Config(data_dir=link))
    assert stamp.declared_path != stamp.resolved_path, "the symlink was not followed"
    assert "link-worktree" in stamp.declared_path, "the declaring worktree was lost"
    assert "real-worktree" in stamp.resolved_path, "the bytes' worktree was lost"
    assert stamp.frontier == date(2026, 8, 4), "the stamp did not read the store's reach"
    assert "link-worktree → real-worktree" in _price_store_line(stamp)


def test_the_stamp_is_wired_into_the_assembler() -> None:
    """A SOURCE PIN, and deliberately so — the same trade `test_no_false_unknown.py` documents for
    `assemble_one`, which cannot be driven offline (CIQ + EDGAR + LLM). So the helper above is
    EXECUTED and only the wiring is observed. Matches the exact call rather than the bare name: a
    comment naming the helper would satisfy a name search while the call sat nowhere.

    This is the assertion the surviving mutation proves is needed."""
    import inspect

    import vinci.dossier.assemble as asm
    assert "price_store=_price_store_stamp(cfg)" in inspect.getsource(asm.assemble_one), (
        "the store stamp is not wired into assemble_one — every new dossier would say 'unstamped' "
        "forever, and no committed artifact would show the difference")


def test_the_spot_check_is_wired_into_the_supersede_write_path() -> None:
    """The write-path seat, pinned the same way and for the same reason: `_cmd_scenario_supersede`
    needs a record, a ledger, a store and a resolver to drive. What must not silently vanish is the
    CALL — and that it prints rather than joining `problems`, because a refusal here would block
    the two correct records the corpus measurement found."""
    import inspect

    import vinci.cli as cli
    src = inspect.getsource(cli._cmd_scenario_supersede)
    assert "sc.spot_notes(" in src, "the spot check is no longer called at the write path"
    i = src.index("sc.spot_notes(")
    assert "problems" not in src[i:i + 400], (
        "spot notes joined `problems` — that turns a note into a refusal, which the measurement "
        "specifically rejected")


def test_the_audit_subcommand_runs_end_to_end_and_never_changes_the_exit_code(
    tmp_path: Path, monkeypatch: Any, capsys: Any,
) -> None:
    """DRIVEN THROUGH THE REAL PARSER — this one CAN be executed, so it is.

    Two records against one store: one whose date the store holds (silent) and one dated past the
    frontier (a note). The exit code must stay 0 with a note outstanding, which is the property
    that makes this an audit rather than a gate."""
    import json

    import vinci.cli as cli
    from vinci.config import Config

    data = tmp_path / "data"
    data.mkdir()
    Store(data / "vinci.db").write_prices([
        PriceBar(internal_id=IID, bar_date=date(2026, 8, 4), open=1, high=1, low=1,
                 close=11.33, volume=1.0, source="polygon-grouped")])
    (tmp_path / "scenarios").mkdir()
    base = json.loads(Path("scenarios/SMPL.json").read_text())
    for tk, asof in (("CLEAN", "2026-08-04"), ("LAGGED", "2026-08-07")):
        rec = {**base, "ticker": tk, "spot": 11.33, "spot_as_of": asof}
        (tmp_path / "scenarios" / f"{tk}.json").write_text(json.dumps(rec))

    class _Ident:
        internal_id = IID

    class _Res:
        @staticmethod
        def resolve_ticker(t: str) -> Any:
            return _Ident()

    monkeypatch.setattr(cli, "get_config", lambda: Config(data_dir=data))
    monkeypatch.setattr(cli.EntityResolver, "from_config", staticmethod(lambda cfg: _Res()))
    monkeypatch.chdir(tmp_path)

    args = cli.build_parser().parse_args(["audit", "spot"])
    assert args.func is cli._cmd_audit_spot, "the `audit spot` subcommand is not registered"
    assert args.func(args) == 0, "a note changed the exit code — this is a gate, not an audit"

    out = capsys.readouterr().out
    assert "CLEAN" in out and "matches this store's bar exactly" in out
    assert "reaches only to 2026-08-04" in out, "the lagged record produced no note"
    assert "1 clean · 1 note(s)" in out, out
