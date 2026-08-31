"""Every real identity records WHEN the store learned it — and the leak guard trusts nothing less.

THE HOLE (found 2026-08-31, chasing an unrelated LLY question). `build_universe` stamps
`first_seen=reference_date`; `vinci refresh` never did, so every identity it INTRODUCED carried
NULL — QQQ, TSM and V in the committed master. That is not cosmetic. `identities_first_seen_after`
is the #442 failed-forward-run guard, raising when a backdated `run-weekly` would judge names the
store learned later, and its `first_seen > ?` NEVER MATCHES NULL. So the one command that adds
out-of-band names was precisely the one whose names the guard could not see: a `vinci refresh X`
followed by a backdated run would admit X to a screen that could not have known it — the exact
leak #442 exists to stop, re-opened through a field nobody was filling in.

Fixed on both sides: `refresh` stamps, and the guard fails CLOSED on unknown provenance rather than
trusting a field any writer can omit.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from vinci.schemas.data_record import Identity
from vinci.store import Store

ROOT = Path(__file__).resolve().parents[1]

#: Synthetic benchmark identities have no `first_seen` BY CONSTRUCTION (`benchmark_identity`) and
#: are not SEC issuers — they cannot leak into a backdated run, and counting them would make every
#: such run raise on rows it wrote itself.
SYNTHETIC_PREFIX = "IDX-"


def _identity(internal_id: str = "SEC-0000000001-AAA") -> Identity:
    return Identity(internal_id=internal_id, issuer_id="ISS-0000000001", cik="0000000001",
                    ticker="AAA", mic="XNAS", exchange="Nasdaq", eod_symbol="AAA",
                    name="Alpha Inc", currency="USD")


def test_every_committed_identity_records_when_it_was_first_seen() -> None:
    """THE ARTIFACT PIN. A row without `first_seen` has unrecorded provenance, and the failed-
    forward-run guard cannot reason about it. Three such rows shipped before this was noticed."""
    missing = sorted(
        str(r["ticker"]) for r in
        (json.loads(ln) for ln in
         (ROOT / "data" / "snapshots" / "securities.jsonl").read_text().splitlines() if ln.strip())
        if not str(r["internal_id"]).startswith(SYNTHETIC_PREFIX) and not r.get("first_seen"))
    assert not missing, (
        f"identities with no first_seen: {missing}. `identities_first_seen_after` cannot see them, "
        f"so a backdated run could admit a name it could not have known (#442). Stamp the date the "
        f"record proves the identity existed — never a guess.")


def test_an_identity_with_no_first_seen_fails_the_backdated_run_guard(tmp_path: Path) -> None:
    """THE GUARD, FAIL-CLOSED. Unknown provenance cannot confirm the name was knowable at the
    reference date, so it counts as 'learned after' — the way `unknown_sic` excludes a name whose
    business type the universe cannot confirm. `first_seen > ?` alone silently returned nothing."""
    with Store(tmp_path / "t.db") as store:
        store.upsert_security(_identity("SEC-0000000001-DATED"), first_seen=date(2026, 1, 5))
        store.upsert_security(_identity("SEC-0000000002-NODATE"))            # no first_seen
        store.upsert_security(_identity("SEC-0000000003-LATER"), first_seen=date(2026, 9, 1))
        ahead = store.identities_first_seen_after(date(2026, 6, 1))
    assert "SEC-0000000002-NODATE" in ahead, "an unrecorded first_seen must fail CLOSED"
    assert "SEC-0000000003-LATER" in ahead, "the original behaviour must survive"
    assert "SEC-0000000001-DATED" not in ahead, "a name known before the date must still pass"


def test_the_guard_never_fires_on_a_synthetic_benchmark(tmp_path: Path) -> None:
    """THE EXEMPTION, pinned. SPY/IWM/MDY carry no `first_seen` by construction and are upserted by
    the screen and orchestrator themselves — counting them would make EVERY backdated run raise on
    rows it had just written, i.e. fail closed on nothing real."""
    from vinci.universe import benchmark_identity
    with Store(tmp_path / "t.db") as store:
        store.upsert_security(benchmark_identity("SPY"))
        store.upsert_security(benchmark_identity("IWM"))
        assert store.identities_first_seen_after(date(2026, 6, 1)) == []


def test_refresh_stamps_first_seen_on_an_identity_it_introduces(tmp_path: Path) -> None:
    """THE SOURCE. `build_universe` always stamped; this path never did, which is how the three
    NULLs got in. Pinned on the STORE's behaviour under the same call shape `_cmd_refresh` makes —
    and the COALESCE means an identity already present keeps the date it was really first seen,
    so a later refresh can never overwrite a true earlier date with today's."""
    with Store(tmp_path / "t.db") as store:
        store.upsert_security(_identity(), first_seen=date(2026, 3, 4))      # already known
        store.upsert_security(_identity(), first_seen=date(2026, 8, 31))     # refresh, later
        row = store._conn.execute(                                           # noqa: SLF001
            "SELECT first_seen FROM securities WHERE internal_id = ?",
            ("SEC-0000000001-AAA",)).fetchone()
    assert row["first_seen"] == "2026-03-04", "a refresh must not overwrite a true earlier date"


def test_the_synthetic_prefix_matches_what_benchmark_identity_builds() -> None:
    """TIE THE FILTER TO ITS PRODUCER (review of #533). The exemption used to be a bare `'IDX-%'`
    SQL literal, duplicating a convention that actually lives in `benchmark_identity`. Every other
    consumer greps as `startswith("IDX-")`, but a SQL literal changes nothing loudly — it just
    stops matching, the exemption silently disappears, and every backdated run starts raising on
    the benchmark rows the screen and orchestrator wrote themselves."""
    from vinci.store.store import SYNTHETIC_ID_PREFIX
    from vinci.universe import benchmark_identity
    for symbol in ("SPY", "IWM", "MDY"):
        assert benchmark_identity(symbol).internal_id.startswith(SYNTHETIC_ID_PREFIX), (
            f"benchmark_identity({symbol!r}) no longer builds ids starting "
            f"{SYNTHETIC_ID_PREFIX!r} — the store's exemption filter will stop matching")
