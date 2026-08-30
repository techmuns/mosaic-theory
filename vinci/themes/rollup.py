"""The theme economics roll-up — inform-only, per-member, NO COMPOSITE (brief Item 4, ruling R5).

The predecessor framework's S1.8/D2 answered "does this theme pay?" before capital moved. This
lane had no economics surface at all: admissibility and ratification see breadth, coherence,
persistence and forward returns — never the members' underwritten asymmetry. The roll-up is that
function in this repo's inform-only idiom: it ASSEMBLES, per member, the economics the repo
already computes at name level, and concludes nothing.

**NO theme-level EV is computed — deliberately.** The predecessor weighted scenarios by
probabilities; this repo has none (structurally, by schema), and a naive average would FABRICATE
a theme number. The roll-up shows the distribution; concluding is the human's. The record schema
therefore carries no aggregate/mean/composite/score field (pinned by the forbidden-token walk,
the ``CandidateTheme`` no-conclude pattern), and this module is imported by no gate, screen, or
ranker — it feeds a page.

SUPPLYING LAYERS, each labeled and never mixed into a derived number:
- membership: the committed frozen basket (``data/themes/baskets/<driver>.json``) — the only
  COMMITTED membership surface (exposure scans land in local scan_history, deliberately
  uncommitted). A basket-less driver gets a LOUD empty roll-up (``membership_note`` says why),
  never a silently missing block — the absent-vs-broken rule.
- tiers/eligible/dates: the committed ``scenarios/<TICKER>.json`` records. A record without the
  2026-08-21 ladder stamp (``gate_regime`` absent) renders as UNSTAMPED — judged under the old
  2:1/15% booleans, and the surface says so rather than letting absence read as passage.
- ``ev_gap``: the committed dossier's ``mechanical.ev_gap`` — carried WITH its own vintages,
  always, because the gap can be stale relative to a superseded record (the
  ev_gap-stale-after-supersede class): the vintage beside the number is the honesty.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from pydantic import BaseModel, Field

from vinci.themes import forward as fwd
from vinci.themes.drivers import DRIVER_SPECS


class MemberEconomics(BaseModel, frozen=True):
    """One member's name-level economics, assembled — never graded here."""

    ticker: str
    membership_source: str          # "frozen-basket" — the committed source this row came from
    substructure_tag: str = ""      # the basket's layer/category for this name (surface grouping)
    underwritten: bool = False
    underwrite_date: str | None = None
    #: None + underwritten → the record predates the tiered ladder: judged under the 2:1/15%
    #: booleans. The page prints "unstamped (pre-ladder)" — absence never reads as passage.
    gate_regime: str | None = None
    asymmetry_tier: str | None = None
    return_tier: str | None = None
    eligible: bool | None = None
    eligible_undefined: str | None = None
    avoid_priced: bool | None = None
    avoid_priced_note: str = ""
    #: "computed" | "not-computed" | "no-dossier" — a member without a dossier is a stated state,
    #: never an empty cell.
    ev_gap_status: str = "no-dossier"
    ev_gap: float | None = None     # ratios.ev_gap — our-EV/TEV RATIO (not a %); never aggregated
    ev_gap_reason: str = ""
    #: tev_as_of / consensus_as_of — ALWAYS carried when the dossier carries them (the staleness
    #: honesty: the number never travels without its vintage).
    ev_gap_vintages: dict[str, str] = Field(default_factory=dict)


class ThemeEconomicsRollup(BaseModel, frozen=True):
    """The per-driver roll-up artifact (``data/themes/economics/<driver>.json``; mirrored for the
    page by the stdlib build via ``mirror_slug``). Counts + rows only — no composite, by pin."""

    driver_key: str
    mirror_slug: str                # machine-stamped from the registry, like the thesis card
    as_of: str                      # ISO date the roll-up was assembled
    membership_note: str            # which committed source — or the loud no-basket reason
    n_members: int
    n_underwritten: int
    rows: tuple[MemberEconomics, ...]


def _scenario_fields(path: Path) -> dict[str, object]:
    rec = json.loads(path.read_text())
    res = rec.get("result") or {}
    ver = rec.get("verdict") or {}
    return {
        "underwritten": True,
        "underwrite_date": rec.get("underwrite_date"),
        "gate_regime": res.get("gate_regime"),
        "asymmetry_tier": res.get("asymmetry_tier"),
        "return_tier": res.get("return_tier"),
        "eligible": res.get("eligible"),
        "eligible_undefined": res.get("eligible_undefined"),
        "avoid_priced": ver.get("avoid_priced"),
        "avoid_priced_note": ver.get("avoid_priced_note") or "",
    }


def _ev_gap_fields(dossier_path: Path) -> dict[str, object]:
    if not dossier_path.exists():
        return {"ev_gap_status": "no-dossier"}
    doc = json.loads(dossier_path.read_text())
    gap = (doc.get("mechanical") or {}).get("ev_gap") or {}
    if not gap:
        return {"ev_gap_status": "not-computed",
                "ev_gap_reason": "dossier carries no ev_gap block"}
    return {
        "ev_gap_status": gap.get("status") or "not-computed",
        "ev_gap": (gap.get("ratios") or {}).get("ev_gap"),
        "ev_gap_reason": gap.get("reason") or "",
        "ev_gap_vintages": gap.get("vintages") or {},
    }


def build_rollup(
    driver: str,
    *,
    data_dir: Path,
    scenarios_root: Path,
    dossiers_dir: Path,
    as_of: date,
) -> ThemeEconomicsRollup:
    """Assemble the roll-up from committed artifacts only. Pure read; the CLI writes.

    ``scenarios_root`` is the repo root holding ``scenarios/`` (the ``records_dir`` convention);
    ``dossiers_dir`` is ``data/dossiers``. ``as_of`` is passed in, never taken from the clock
    here, so a re-run over the same corpus is byte-identical."""
    spec = DRIVER_SPECS.get(driver)
    if spec is None:
        raise ValueError(f"unknown driver {driver!r} (live: {sorted(DRIVER_SPECS)})")
    baskets_file = fwd.baskets_path(driver, data_dir=data_dir)
    if not baskets_file.exists():
        return ThemeEconomicsRollup(
            driver_key=driver, mirror_slug=spec.mirror_slug, as_of=as_of.isoformat(),
            membership_note=(
                "no frozen basket for this driver — no committed membership to roll up "
                "(exposure scans are local-only; freeze a basket with themes-forward)"),
            n_members=0, n_underwritten=0, rows=())
    baskets = fwd.load_baskets(baskets_file)
    # FAIL LOUD ON A MISSING SCENARIOS ROOT rather than reporting every member "no underwrite".
    # `scenarios/` is cwd-relative by the repo's convention, so running this from anywhere but the
    # repo root finds no records — and the roll-up would COMMIT an artifact stating that nothing
    # in the theme is underwritten, which is a false claim about the book rather than a missing
    # file. Checked HERE, after membership: a driver with no basket has nothing to look up, and
    # its loud-empty roll-up is a real state that must not depend on the caller's directory.
    scenarios_dir = scenarios_root / "scenarios"
    if baskets.all_committed and not scenarios_dir.is_dir():
        raise FileNotFoundError(
            f"no scenarios directory at {scenarios_dir} — every one of "
            f"{len(baskets.all_committed)} members would render 'no underwrite' and the committed "
            f"roll-up would say so falsely. Run from the repo root (or pass the root holding "
            f"scenarios/).")
    rows: list[MemberEconomics] = []
    for ticker in sorted(baskets.all_committed):
        fields: dict[str, object] = {
            "ticker": ticker,
            "membership_source": "frozen-basket",
            "substructure_tag": baskets.layer_of.get(ticker, ""),
        }
        rec_path = scenarios_root / "scenarios" / f"{ticker}.json"
        if rec_path.exists():
            fields.update(_scenario_fields(rec_path))
        fields.update(_ev_gap_fields(dossiers_dir / ticker / "dossier.json"))
        rows.append(MemberEconomics.model_validate(fields))
    return ThemeEconomicsRollup(
        driver_key=driver, mirror_slug=spec.mirror_slug, as_of=as_of.isoformat(),
        membership_note=f"frozen basket ({baskets.freeze_timestamp[:10]}) — all_committed",
        n_members=len(rows),
        n_underwritten=sum(1 for r in rows if r.underwritten),
        rows=tuple(rows))


ECONOMICS_SUBDIR = "themes/economics"


def economics_path(driver: str, *, data_dir: Path) -> Path:
    return data_dir / ECONOMICS_SUBDIR / f"{driver}.json"


def write_rollup(rollup: ThemeEconomicsRollup, *, data_dir: Path) -> Path:
    """Write the committed artifact (derived, regenerable — the auto-committable class)."""
    path = economics_path(rollup.driver_key, data_dir=data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rollup.model_dump_json(indent=1) + "\n")
    return path
