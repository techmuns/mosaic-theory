"""ENTITY-MASTER SIC COHERENCE — pinned over the REAL committed artifacts.

The SIC is an ISSUER-level fact from EDGAR submissions. These pin what that implies about the
committed `securities.jsonl` / `issuers.jsonl`, so a write that half-applies it — the partial-upsert
clobber of #523, or any future writer holding an un-enriched identity — fails here instead of
surfacing months later as a sector label on a decision surface.

Phrasing-independent structural invariants only: no exact SIC values, no counts of a population
that legitimately moves as the universe turns over. The one thing every assertion refuses is a
SIC-shaped hole where the entity master already knows the answer.
"""
from __future__ import annotations

import json
from pathlib import Path

from vinci.sectors import industry_for_sic

ROOT = Path(__file__).resolve().parents[1]
SNAPS = ROOT / "data" / "snapshots"

#: Synthetic benchmark identities (`benchmark_identity`: SPY/IWM/MDY/sector ETFs) — `issuer_id`
#: "IDX", `cik` "". Not SEC issuers, so they have no submissions record and no SIC to have.
SYNTHETIC_PREFIX = "IDX-"


def _rows(name: str) -> list[dict[str, object]]:
    return [json.loads(ln) for ln in (SNAPS / f"{name}.jsonl").read_text().splitlines()
            if ln.strip()]


def _real_securities() -> list[dict[str, object]]:
    return [r for r in _rows("securities")
            if not str(r["internal_id"]).startswith(SYNTHETIC_PREFIX)]


def test_an_issuer_never_half_carries_its_sic() -> None:
    """THE CLOBBER'S SIGNATURE (#523 → the 2026-08-31 backfill).

    One CIK, one EDGAR SIC — so within an issuer, either EVERY security row carries it or NONE
    does. A PARTIAL hole is only reachable by a writer that rewrote some of an issuer's rows
    without knowing the fact: `INSERT OR REPLACE` from an un-enriched identity. It is exactly how
    the committed file looked before the backfill — ASB 6022 beside ASBA null, SLNH 6199 beside
    SLNHP null, HWC beside HWCPZ, 59 issuers in that state — and how Gartner's row was destroyed.
    """
    by_cik: dict[str, list[dict[str, object]]] = {}
    for r in _real_securities():
        by_cik.setdefault(str(r["cik"]), []).append(r)

    partial = {
        cik: sorted((str(r["ticker"]), r.get("sic")) for r in rs)
        for cik, rs in by_cik.items()
        if any(r.get("sic") for r in rs) and any(not r.get("sic") for r in rs)
    }
    assert not partial, (
        f"{len(partial)} issuer(s) carry a SIC on some securities and not others — an issuer-level "
        f"fact cannot be half-true. A partial/un-enriched upsert is the way this happens: "
        f"{dict(list(partial.items())[:5])}")


def test_a_cik_never_disagrees_with_itself_about_its_sic() -> None:
    """One issuer, one SIC — across its share classes AND between the two committed tables. Two
    rows of the same issuer reporting different codes would make a name's sector depend on which
    row a consumer happened to read."""
    per_cik: dict[str, set[str]] = {}
    for r in _real_securities():
        if r.get("sic"):
            per_cik.setdefault(str(r["cik"]), set()).add(str(r["sic"]))

    split = {c: sorted(v) for c, v in per_cik.items() if len(v) > 1}
    assert not split, f"securities of one issuer report different SICs: {split}"

    for r in _rows("issuers"):
        cik, sic = str(r["cik"]), r.get("sic")
        if sic and cik in per_cik:
            assert str(sic) in per_cik[cik], (
                f"issuer {cik} ({r['name']}) carries SIC {sic}, which none of its securities do "
                f"({sorted(per_cik[cik])}) — the two tables disagree about one issuer")


def test_every_present_sic_is_a_real_edgar_code() -> None:
    """A SIC that is PRESENT must be a real EDGAR code — a garbage write wearing a value's clothes
    is worse than a null, which at least reports itself absent (`monitor.sector_for_display`).

    CHECKED AGAINST THE VENDORED OFFICIAL TABLE, not against `industry_for_sic`. Resolving is far
    too weak a test to state this: `industry_for_sic` FALLS BACK to `sector_for_sic`, which answers
    "Other" for every unmapped numeric code, so `9999` and `0000` both "resolve" and only a
    NON-NUMERIC string could ever have failed. The real invariant is the format EDGAR publishes
    (four digits) and membership of the SEC's own list — every one of the 332 distinct codes
    committed today satisfies both.
    """
    from vinci.sic_table import SIC_TABLE

    malformed = sorted({(str(r["ticker"]), str(r["sic"])) for r in _real_securities()
                        if r.get("sic")
                        and not (str(r["sic"]).isdigit() and len(str(r["sic"])) == 4)})
    assert not malformed, f"stored SIC(s) that are not 4-digit EDGAR codes: {malformed}"

    off_table = sorted({(str(r["ticker"]), str(r["sic"])) for r in _real_securities()
                        if r.get("sic") and str(r["sic"]) not in SIC_TABLE})
    assert not off_table, (
        f"stored SIC(s) absent from the vendored official SEC list: {off_table}. Either the code "
        f"is a garbage write, or the table needs re-vendoring — check which before relaxing this.")

    unreadable = sorted({(str(r["ticker"]), str(r["sic"])) for r in _real_securities()
                         if r.get("sic") and industry_for_sic(str(r["sic"])) == "Unknown"})
    assert not unreadable, f"stored SIC(s) that resolve to nothing: {unreadable}"


def test_synthetic_benchmark_rows_never_carry_a_sic() -> None:
    """THE NEGATIVE PIN. SPY/IWM/MDY and the sector ETFs are synthetic identities with an empty
    CIK — they have no EDGAR submissions record, so any SIC on one was invented. The backfill
    excludes them by construction; this refuses a future one that does not."""
    synthetic = [r for r in _rows("securities")
                 if str(r["internal_id"]).startswith(SYNTHETIC_PREFIX)]
    assert synthetic, "no synthetic benchmark rows found — this pin would be vacuous"
    invented = [(str(r["ticker"]), r.get("sic")) for r in synthetic if r.get("sic")]
    assert not invented, f"a SIC was invented for a synthetic benchmark identity: {invented}"


def test_no_name_in_the_current_universe_lacks_a_sic() -> None:
    """The universe is the other decision surface (the ledger is pinned in `test_monitor.py`).
    `build_universe` EXCLUDES a name whose SIC it cannot read — `unknown_sic`, fail-closed — so an
    in-universe row without one means the fact was destroyed after admission, which is the exact
    #523 failure."""
    in_universe = {str(r["internal_id"]) for r in _rows("universe_snapshot")
                   if r.get("in_universe")}
    assert in_universe, "empty universe snapshot — this pin would be vacuous"
    by_id = {str(r["internal_id"]): r for r in _rows("securities")}
    missing = sorted(i for i in in_universe if not (by_id.get(i) or {}).get("sic"))
    assert not missing, (
        f"in-universe name(s) with no SIC: {missing}. `build_universe` cannot admit one, so the "
        f"value was destroyed after admission — look for an un-enriched upsert.")
