"""Re-measuring a frozen theme from its COMMITTED mirror — because the ledger is local-only.

THE GAP THIS CLOSES. The ratification ledger and the frozen baskets are git-ignored by an explicit
standing decision (`.gitignore`: "derived, LOCAL-only … never committed"). The Stage-4 forward
measurement reads those files, so on any machine that did not run the freeze there is NO input —
and the entire point of Stage 4 is a number that accrues over CALENDAR TIME. All three themes froze
in July 2026; by 2026-08-12 two had passed their 30-day horizon with their committed diagnostics
still reading "0 days forward from freeze", because nothing could recompute them.

`baskets_from_mirror` rebuilds the baskets from the one durable artifact — the frontend mirror —
WITHOUT committing the ledger, which stays the operator's call.

THE CORPUS IS THE THREE COMMITTED MIRRORS. Every reconstruction claim below is checked against them
rather than a fixture built to the shape the test wants — a hand-rolled mirror would prove only that
the reader parses its own invention.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from vinci.themes.forward import baskets_from_mirror, measure_hold_none

ROOT = pathlib.Path(__file__).resolve().parents[1]
MIRRORS = ROOT / "frontend" / "themes"

#: The frozen themes as committed. Named rather than globbed so a new mirror landing in this
#: directory is a deliberate addition to the corpus, not a silent one.
FROZEN = ("ai-datacenter", "defense", "truckload-supply-purge")


def _mirror(slug: str) -> dict[str, object]:
    return json.loads((MIRRORS / f"{slug}.json").read_text())


@pytest.mark.parametrize("slug", FROZEN)
def test_every_committed_mirror_rebuilds_into_baskets(slug: str) -> None:
    """THE CORPUS PIN. All three must reconstruct; a reader that works on one shape and not the
    others would be discovered the day a theme is re-measured, which is the day it matters."""
    m = _mirror(slug)
    b = baskets_from_mirror(m)
    names = m["names"]
    assert isinstance(names, list)
    assert len(b.all_committed) == len(names) == int(str(m["frozenCount"])), (
        f"{slug}: rebuilt {len(b.all_committed)} names against a mirror claiming "
        f"{m['frozenCount']}")
    assert b.passed == b.all_committed, (
        f"{slug}: every committed name must land in the PASSED (AVOID) leg on a hold-none freeze")
    assert b.ratified == (), f"{slug}: a BUY leg was invented from a mirror that has none"
    assert b.freeze_timestamp == m["freezeTimestamp"]
    # entry == freeze for every name: the hold-none posture, and what `_cohort_fwd_mean` already
    # defaults to. Anything else would be a date this mirror does not carry.
    assert set(b.entry_dates.values()) == {str(m["freezeTimestamp"])[:10]}, (
        f"{slug}: entry dates were invented — the mirror carries no per-name ratification date")


@pytest.mark.parametrize("slug", FROZEN)
def test_the_cohorts_survive_the_round_trip(slug: str) -> None:
    """The watchlist drives diagnostic-2 (the more informative one) and the avoid-controls are the
    near-miss control. A cohort silently lost in reconstruction changes what the diagnostic
    measures while the label stays the same."""
    m = _mirror(slug)
    b = baskets_from_mirror(m)
    names = m["names"]
    assert isinstance(names, list)

    def expected(tag: str) -> set[str]:
        return {str(n["ticker"]) for n in names
                if isinstance(n, dict) and tag in (n.get("cohorts") or [])}

    assert set(b.watchlist) == expected("watchlist"), f"{slug}: watchlist lost in reconstruction"
    assert set(b.avoid_controls) == expected("avoid-control"), f"{slug}: avoid-controls lost"
    assert set(b.real_tier) == expected("real"), f"{slug}: real-tier lost"
    # cross-checked against the mirror's OWN count field, which is written independently
    assert len(b.watchlist) == int(str(m["watchlistCount"])), (
        f"{slug}: watchlist size disagrees with the mirror's own watchlistCount")


def test_a_mirror_with_a_buy_leg_is_refused_rather_than_dated_from_the_freeze() -> None:
    """THE REFUSAL THAT MATTERS. For a RATIFIED name the entry date IS the ratification date, and
    the mirror does not carry it. Dating the BUY leg from the freeze would silently measure a
    window the analyst never held — and it would do so in the fund's only forward theme read.

    SYNTHETIC by necessity: no committed mirror has a BUY leg (that is the whole EMPTY-BUY reality),
    so there is no corpus to draw this from. Built by mutating a REAL mirror rather than inventing
    a shape, so the refusal is exercised against the true structure.
    """
    m = _mirror("truckload-supply-purge")
    m["ratifiedCount"] = 1
    with pytest.raises(ValueError, match="ratification dates"):
        baskets_from_mirror(m)


def test_the_registry_key_wins_over_the_mirrors_human_label() -> None:
    """REVIEW FINDING (mine, on my own diff). The mirror's `driver` field is a HUMAN LABEL, not the
    registry key: ai-datacenter's reads "AI-datacenter value chain". Taking it as identity made one
    report name two different drivers — the CLI header printed the registry key while every
    confound string printed the label ("AI-datacenter value chain-BETA-CONFOUNDED").

    Checked on the live mirror whose label actually diverges, not on a constructed one.
    """
    m = _mirror("ai-datacenter")
    assert m["driver"] != "ai-datacenter", (
        "this pin's subject is gone — the ai-datacenter mirror now carries the registry key, so "
        "re-read whether the divergence it guards still exists")
    assert baskets_from_mirror(m, driver="ai-datacenter").driver == "ai-datacenter"
    # and with no caller key the mirror's own field is still the fallback, so the function stays
    # usable standalone rather than requiring the registry
    assert baskets_from_mirror(m).driver == m["driver"]


def test_a_mirror_with_no_names_is_refused() -> None:
    m = _mirror("truckload-supply-purge")
    m["names"] = []
    with pytest.raises(ValueError, match="no committed names"):
        baskets_from_mirror(m)


def test_malformed_name_entries_are_refused_not_skipped() -> None:
    """A dropped entry silently shrinks the naive baseline every diagnostic is computed over."""
    m = _mirror("truckload-supply-purge")
    names = list(m["names"])  # type: ignore[call-overload]
    m["names"] = [*names, "NOT-AN-OBJECT"]
    with pytest.raises(ValueError, match="malformed"):
        baskets_from_mirror(m)


def test_an_unreached_horizon_reports_pending_and_never_a_number() -> None:
    """FORWARD-ONLY. truckload froze 2026-07-14; at 2026-08-11 its 30-day horizon has NOT passed,
    so every diagnostic must be None with n=0 — never 0.0, never a partial read off whatever bars
    happen to exist. Uses a price function that would answer for ANY date, so a pending result can
    only come from the horizon gate itself."""
    from datetime import date

    b = baskets_from_mirror(_mirror("truckload-supply-purge"))

    def always_priced(ticker: str, day: date) -> float | None:
        return 100.0

    hn = measure_hold_none(b, exposure_names=list(b.watchlist), price_fn=always_priced,
                           horizon_days=30, as_of=date(2026, 8, 11))
    assert hn.avoid_discipline.value is None and hn.avoid_discipline.n == 0, (
        f"a 29-day-old freeze produced a 30-day forward number: "
        f"{hn.avoid_discipline.value!r} (n={hn.avoid_discipline.n})")
    assert hn.exposure_carry.value is None, "exposure-carry resolved before its horizon"
    # and the RATIFIED-dependent measures stay UNDEFINED, never 0.0
    assert len(hn.undefined_measures) == 3, hn.undefined_measures


def test_the_reached_horizon_does_produce_a_number(tmp_path: pathlib.Path) -> None:
    """The complement, so the pin above cannot pass by measuring nothing at all. ai-datacenter
    froze 2026-07-02, so at 2026-08-11 its 30-day horizon HAS passed and every committed name
    should contribute."""
    from datetime import date

    b = baskets_from_mirror(_mirror("ai-datacenter"))

    def priced(ticker: str, day: date) -> float | None:
        return 100.0 if day <= date(2026, 7, 20) else 110.0

    hn = measure_hold_none(b, exposure_names=list(b.watchlist), price_fn=priced,
                           horizon_days=30, as_of=date(2026, 8, 11))
    assert hn.avoid_discipline.n == len(b.all_committed), (
        f"only {hn.avoid_discipline.n} of {len(b.all_committed)} names contributed")
    assert hn.avoid_discipline.value == pytest.approx(0.10), hn.avoid_discipline.value


def _forward_args(**kwargs: object) -> object:
    import argparse

    base = {"driver": "truckload-supply-purge", "measure": False, "as_of": None,
            "horizons": "30", "ratify_date": None, "baskets_out": None, "exposure_names": None,
            "watchlist": None, "watchlist_triggers": None, "avoid_controls": None,
            "real_tier": None}
    return argparse.Namespace(**base, **kwargs)


def test_the_cli_refuses_both_paths_and_neither_path() -> None:
    """The freeze path (--worksheet + --ledger) and the re-measure path (--from-mirror) are
    mutually exclusive. Given both it is ambiguous which is authoritative; given neither there is
    nothing to act on."""
    from vinci import cli

    for kwargs in ({"worksheet": "w.csv", "ledger": "l.jsonl", "from_mirror": "m.json"},
                   {"worksheet": None, "ledger": None, "from_mirror": None},
                   # --from-baskets is the third source; any two together are ambiguous
                   {"worksheet": None, "ledger": None, "from_mirror": "m.json",
                    "from_baskets": "b.json"}):
        kwargs = {"from_baskets": None, **kwargs}
        with pytest.raises(SystemExit, match="EXACTLY ONE source"):
            cli._cmd_themes_forward(_forward_args(**kwargs))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("kwargs", "expect"),
    [
        ({"worksheet": "w.csv", "ledger": None, "from_mirror": None}, "--ledger"),
        ({"worksheet": None, "ledger": "l.jsonl", "from_mirror": None}, "--worksheet"),
    ],
    ids=["worksheet-without-ledger", "ledger-without-worksheet"],
)
def test_a_half_specified_freeze_path_is_rejected_before_any_path_is_built(
    kwargs: dict[str, object], expect: str,
) -> None:
    """REVIEW P2 ON #412. The either/or read `worksheet OR ledger` as "a freeze was requested", so
    `--worksheet rows.csv` alone satisfied it, fell through to the freeze branch, and died on
    `Path(None)` with a TypeError naming NoneType — an error that tells the operator nothing about
    which flag they forgot. The ledger-only case was symmetric.

    Asserted on the MISSING flag's name, so a guard that merely raises SystemExit without saying
    what is absent still fails here."""
    from vinci import cli

    with pytest.raises(SystemExit, match=expect):
        cli._cmd_themes_forward(_forward_args(**kwargs))  # type: ignore[arg-type]


def test_reconstruction_logs_no_disposition_of_its_own(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """§6 DEAD-SIGNAL FIREWALL. Reconstruction must not become a route by which the machine records
    a judgement. Every rebuilt name is PASSED — what the mirror already says — and NOTHING here
    appends to a ledger: a reconstruction that wrote rows would be the machine manufacturing
    dispositions the analyst never gave, in an append-only record.

    Pinned by making the append path itself fail, rather than by inspecting the result — a dump
    that merely lacks the word proves nothing (an earlier cut of this assertion matched the FIELD
    NAME `"ratified": []` and was green for the wrong reason).
    """
    from vinci.themes import forward as fwd

    def _forbidden(*_a: object, **_k: object) -> None:
        raise AssertionError("reconstruction appended to the ratification ledger")

    monkeypatch.setattr(fwd, "append_record", _forbidden)
    b = baskets_from_mirror(_mirror("defense"))
    assert b.ratified == (), "a BUY leg appeared out of a mirror that has none"
    assert set(b.passed) == set(b.all_committed)
