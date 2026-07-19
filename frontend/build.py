#!/usr/bin/env python3
"""Assemble the static snapshot mirror the dashboard serves.

Copies the lightweight committed snapshots and the DERIVED dossiers (never the raw
CIQ workbooks) into ``frontend/``, and generates ``manifest.json`` (the cheap
index: counts + dates that the UI can't otherwise derive without fetching the
megabyte-scale candidate files). Run by Cloudflare Pages on every deploy, and
locally for preview.

It READS only committed snapshots under ``data/snapshots/`` and committed dossiers
under ``data/dossiers/``, and WRITES the ``frontend/snapshots/`` mirror (git-ignored
— regenerated here every deploy) and the ``frontend/dossiers/`` mirror (committed
for the authed deploy, but idempotently regenerated here too). It is not a backend
and runs no pipeline; it only mirrors existing artifacts.

LICENSING: only the DERIVED ``dossier.json``/``dossier.md`` are mirrored — never the
raw licensed CIQ in ``data/manual/ciq/``. ``data/dossiers/`` is committed to the
PRIVATE/authed repo (verified: {value, source_ref} facts + synthesis + public 10-K
phrases, no licensed CIQ); if the repo or deploy ever becomes public, the dossiers
and ``frontend/dossiers/`` revert to git-ignored.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from collections import Counter
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SNAP = ROOT / "data" / "snapshots"
DOSS = ROOT / "data" / "dossiers"
GRAPH = ROOT / "data" / "graph_coverage.json"  # DERIVED EDGAR-10-K exposure map (private-repo only)
FORWARD = ROOT / "data" / "forward"  # git-ignored staging for the frozen theme-edge freeze
#                                      artifacts
OUT_SNAP = HERE / "snapshots"
OUT_DOSS = HERE / "dossiers"
OUT_THEMES = HERE / "themes"  # COMMITTED display JSON (like dossiers) — the deployable theme copy

# The lightweight snapshots the UI fetches at runtime. The MB-scale candidate /
# universe / securities files are intentionally NOT mirrored — their derived
# counts go into manifest.json instead, so the deploy stays small.
_MIRRORED = ("ranked_queue.jsonl", "decision_ledger.jsonl")


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


# --- SCENARIO CARDS (reusable) ------------------------------------------------------------------
# A committed `scenarios/<TICKER>.json` underwrite record renders as a card attachable under ANY
# watchlist name — no full-dossier dependency. Names WITHOUT a record are untouched (the key is
# omitted entirely, so their display JSON stays byte-identical).
def _scenario_card(rec: Any) -> dict[str, Any]:
    """One underwrite record → the display card: the bear/base/bull grid, the reward/risk ratio
    against the bar, the capital-intensity cross-checks, and the verdict status. The basis and
    recipe travel WITH the card so the multiple's unit can never be misread on screen."""
    r = rec.result
    return {
        "ticker": rec.ticker, "recipeId": rec.recipe_id, "recipeDesc": rec.recipe_desc,
        "multipleBasis": rec.multiple_basis, "underwriteDate": rec.underwrite_date,
        "analyst": rec.analyst, "spot": rec.spot, "spotSource": rec.spot_source,
        "facts": [{"key": k, "value": f.value, "unit": f.unit, "basis": f.basis,
                   "source": f.source} for k, f in rec.facts.items()],
        "scenarios": [
            {"name": n, "revenue": s.revenue, "margin": s.margin, "multiple": s.multiple,
             "reason": s.reason,
             **({"valuePerShare": o.value_per_share, "opIncome": o.op_income, "ebitda": o.ebitda,
                 "ev": o.ev, "equity": o.equity, "evEbit": o.ev_ebit, "normFcf": o.norm_fcf}
                if (o := r.per_scenario.get(n)) is not None else {})}
            for n, s in rec.scenarios.items()],
        "reward": r.reward, "risk": r.risk, "ratio": r.ratio, "bar": r.bar,
        "ratioUndefined": r.ratio_undefined, "passFail": r.pass_fail,
        "verdict": {"status": rec.verdict.status, "recorded": rec.verdict.recorded},
    }


def _scenario_cards() -> dict[str, dict[str, Any]]:
    """Every committed underwrite record, keyed by ticker. Empty when none exist."""
    from vinci.scenarios import all_records

    return {t: _scenario_card(rec) for t, rec in all_records(root=ROOT).items()}


def _git_sha() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except Exception:  # noqa: BLE001 — provenance is best-effort; absence is shown as "—"
        return None


# --------------------------------------------------------------------------------------------------
# Theme-edge freeze → committed display JSON (mirrors the dossier flow, with ONE difference: the
# frozen SOURCE (forward_*_baskets.json + _ledger.jsonl) is GIT-IGNORED, so on the Cloudflare deploy
# it is ABSENT. This step is therefore NON-DESTRUCTIVE when the source is missing — it leaves the
# COMMITTED frontend/themes/*.json in place (never rmtree's them). It only regenerates when a local
# run points --themes-src at the freeze artifacts. Read-only transform; no backend import.
# --------------------------------------------------------------------------------------------------
# slug + display label per driver (falls back to a slugified driver string for a future theme)
_DRIVER_SLUG: dict[str, tuple[str, str]] = {
    "AI-datacenter value chain": ("ai-datacenter", "AI-datacenter"),
    "defense-demand-shift": ("defense", "Defense demand-shift"),
    "truckload-supply-purge": ("truckload-supply-purge", "Truckload supply purge"),
}
# the concreteness → rank ladder + the driver-tie gate, mirroring vinci.themes.exposure so the tier
# shape derives IDENTICALLY from the ledger's (grade, driver_tie) as the backend's exposure_basis.
_CONC_RANK = {"none": 0, "stated-intent": 1, "committed-capacity": 2,
              "quantified-revenue": 3, "binding-contract": 4}
_BASIS = {0: "none", 1: "aspirational", 2: "committed", 3: "quantified", 4: "binding"}
# scan exposure_basis → tier bucket (the FULL theme exposure shape lives in the scan, not the
# freeze; a freeze may scope a subset — ai-datacenter froze only its committed enablers, defense
# froze all 108)
_SCAN_BASIS = {
    "binding-contracts-with-terms": "binding", "quantified-revenue-share": "quantified",
    "committed-capacity-or-capex": "committed", "aspirational-intent-only": "aspirational",
    "no-theme-exposure-disclosed": "none",
}
_ACC_RE = re.compile(r"\d{10}-\d{2}-\d{6}")
# mirrors vinci.themes.forward — the zero-RATIFIED honesty label + the UNDEFINED-with-reason
# measures + the §4 power-floor note. Kept as literals here so build.py stays stdlib-only
# (deploy-safe); a regression test pins them equal to the backend's (tests/test_build_themes.py).
_HOLD_NONE_HONESTY = (
    "No BUY leg exists (zero RATIFIED) -> the core edge-measure (RATIFIED-PASSED) and all "
    "RATIFIED-dependent spreads are UNDEFINED and NOT computed. The outputs below are "
    "AVOID-discipline and exposure-carry DIAGNOSTICS, beta-confounded, and are NOT a validation "
    "of the semantic-primary edge."
)
_UNDEFINED_REASON = "no BUY leg — zero RATIFIED; requires a ratified cohort that does not exist"
_UNDEFINED_MEASURES = [
    ["RATIFIED-PASSED (§3a, the core edge-measure)", _UNDEFINED_REASON],
    ["RATIFIED-NAIVE(equal-weight) (§3b-i)", _UNDEFINED_REASON],
    ["RATIFIED vs keyword/co-movement screen (§3b-ii, deferred)", _UNDEFINED_REASON],
]
_POWER_NOTE = (
    "UNPOWERED — DIRECTIONAL / ANECDOTAL: below the a-priori floor (needs >=8 theme-quarters "
    "across >=4 drivers, sign-consistent). A forward-directional read, never a significance test."
)


def _slug(driver: str) -> tuple[str, str]:
    if driver in _DRIVER_SLUG:
        return _DRIVER_SLUG[driver]
    s = re.sub(r"[^a-z0-9]+", "-", driver.lower()).strip("-") or "driver"
    return s, driver


def _eff_basis(grade: str, tie: str) -> str:
    """Effective basis after the driver-tie gate — mirrors vinci.themes.exposure._effective_rank:
    driver-specific keeps the concreteness rank; indirect caps at committed; not-driver at
    aspirational."""
    r = _CONC_RANK.get(grade, 0)
    if tie in ("driver-specific", "chain-layer-specific"):
        pass
    elif tie == "indirect":
        r = min(r, 2)
    else:  # not-driver (or anything unrecognized — conservative)
        r = min(r, 1)
    return _BASIS[r]


def _acc(source_ref: str) -> str | None:
    m = _ACC_RE.search(source_ref or "")
    return m.group(0) if m else None


def _edgar_url(cik: str | None, source_ref: str) -> str | None:
    acc = _acc(source_ref)
    if not acc or not cik:
        return None
    try:
        c = str(int(cik))
    except (TypeError, ValueError):
        return None
    return f"https://www.sec.gov/Archives/edgar/data/{c}/{acc.replace('-', '')}/{acc}-index.htm"


def _theme_display(baskets: dict[str, Any], ledger: list[dict[str, Any]],
                   scan: list[dict[str, Any]] | None) -> dict[str, Any]:
    """The display subset the 4 theme views read — cohorts, tier shape, per-name grade_fact +
    accession + rationale + trigger, the UNDEFINED-spread reasons, and the honesty label."""
    driver = baskets["driver"]
    slug, label = _slug(driver)
    wl_set, ac_set = set(baskets.get("watchlist", [])), set(baskets.get("avoid_controls", []))
    rt_set = set(baskets.get("real_tier", []))
    triggers = baskets.get("watchlist_triggers", {}) or {}

    tier = {"binding": 0, "quantified": 0, "committed": 0, "aspirational": 0}
    cats: Counter[str] = Counter()
    names: list[dict[str, Any]] = []
    for r in ledger:
        tag = r.get("chain_layer") or r.get("substructure_tag") or "unspecified"
        grade = r.get("machine_grade") or r.get("grade") or "none"
        tie = r.get("driver_tie", "")
        basis = _eff_basis(grade, tie)
        if basis in tier:
            tier[basis] += 1
        cats[tag] += 1
        cohorts = ([c for c, s in
                    (("watchlist", wl_set), ("avoid-control", ac_set), ("real", rt_set))
                    if r["ticker"] in s])
        names.append({
            "ticker": r["ticker"], "substructureTag": tag, "driverTie": tie, "grade": grade,
            "basis": basis, "gradeFact": r.get("grade_fact", ""),
            "accession": _acc(r.get("source_ref", "")),
            "edgarUrl": _edgar_url(r.get("cik"), r.get("source_ref", "")),
            "rationale": r.get("rationale", ""), "cohorts": cohorts,
        })
    _rank = {"binding": 0, "quantified": 1, "committed": 2, "aspirational": 3, "none": 4}
    names.sort(key=lambda n: (_rank.get(n["basis"], 9), n["ticker"]))
    by_ticker = {n["ticker"]: n for n in names}

    # FROZEN tier = the dispositioned ledger set (defense 108 = all surfaced; ai-datacenter 56 =
    # the committed enablers only). The TIER SHAPE is the theme's FULL exposure shape from the scan
    # (so none + surfaced + tiers reconcile to the universe); it degrades to the frozen breakdown
    # (no none/universe) when no scan is present.
    frozen = len(ledger)
    if scan is not None:
        sc: Counter[str] = Counter(
            _SCAN_BASIS.get(s.get("exposure_basis", ""), "none") for s in scan
        )
        surfaced = len(scan) - sc["none"]
        tier_shape = {"binding": sc["binding"], "quantified": sc["quantified"],
                      "committed": sc["committed"], "aspirational": sc["aspirational"],
                      "none": sc["none"], "surfaced": surfaced, "universe": len(scan)}
    else:
        surfaced = frozen
        tier_shape = {**tier, "none": None, "surfaced": frozen, "universe": None}

    cards = _scenario_cards()

    def _detail(t: str, extra: dict[str, Any]) -> dict[str, Any]:
        n = by_ticker.get(t, {})
        base = {k: n.get(k, "") for k in
                ("substructureTag", "grade", "basis", "gradeFact", "accession", "edgarUrl",
                 "rationale")}
        # attach ONLY when an underwrite record exists — names without one stay byte-identical
        card = {"scenarioCard": cards[t]} if t in cards else {}
        return {"ticker": t, **base, **extra, **card}

    watchlist = [_detail(t, {"trigger": triggers.get(t, "")}) for t in baskets.get("watchlist", [])
                 if t in by_ticker]
    avoid_controls = [_detail(t, {}) for t in baskets.get("avoid_controls", []) if t in by_ticker]
    categories = [{"tag": k, "n": v} for k, v in cats.most_common()]

    # NAIVE cohort = the equal-weight baseline over the WHOLE committed tier — mirrors the
    # backend's len(baskets.all_committed) (forward.py "NAIVE-N", cli.py:689). NOT `surfaced`
    # (scan breadth): a theme that froze a SUBSET of the surfaced universe (ai-datacenter: 56
    # committed of 450 surfaced) would otherwise render an ~8x-overstated NAIVE cohort next to
    # the tier-scale buy/passed pills. Fall back to the frozen ledger size for a freeze that
    # predates the all_committed field.
    naive_n = len(baskets.get("all_committed") or []) or frozen
    forward = {
        "cohorts": {"buy": len(baskets.get("ratified", [])), "naive": naive_n,
                    "passed": len(baskets.get("passed", [])),
                    "watchlist": len(baskets.get("watchlist", [])),
                    "avoidControls": len(ac_set), "realTier": len(rt_set)},
        "undefinedMeasures": _UNDEFINED_MEASURES,
        "diagnostics": [
            {"name": "avoid-discipline", "status": "PENDING",
             "confound": f"{driver}-BETA-CONFOUNDED + regime-dependent — was declining to buy the "
                         f"committed tier costly or vindicated in THIS window? Largely a "
                         f"{driver}-beta bet, NOT selection skill.",
             "note": "0 days forward from freeze — accrues over calendar time."},
            {"name": "exposure-carry", "status": "PENDING",
             "confound": f"PARTIALLY beta-controlled — both cohorts are {driver}-labelled so the "
                         f"common {driver}-beta largely cancels in the divergence; isolates "
                         "whether the exposure GRADE (real vs not) carries forward info. The more "
                         "informative of the two — still NOT an edge verdict.",
             "note": "genuine-exposure (watchlist) vs other-PASSED divergence; pending forward."},
        ],
        "honestyLabel": _HOLD_NONE_HONESTY,
        "powerNote": _POWER_NOTE,
    }
    # frozen tier counts — the DRILLABLE buckets (every count here has per-name detail in names[]):
    # firm = REAL (binding + quantified), partial = committed, early = aspirational. The magnitude
    # words are the portfolio-altitude labels; the underlying grade tiers are unchanged.
    frozen_tiers = {
        "firm": sum(1 for n in names if n["basis"] in ("binding", "quantified")),
        "partial": sum(1 for n in names if n["basis"] == "committed"),
        "early": sum(1 for n in names if n["basis"] == "aspirational"),
    }
    return {
        "driver": driver, "slug": slug, "label": label,
        "freezeDate": (baskets.get("freeze_timestamp") or "")[:10],
        "freezeTimestamp": baskets.get("freeze_timestamp", ""),
        "ratifiedCount": len(baskets.get("ratified", [])), "surfacedCount": surfaced,
        "frozenCount": frozen, "watchlistCount": len(baskets.get("watchlist", [])),
        "tierShape": tier_shape, "frozenTiers": frozen_tiers, "categories": categories,
        "names": names, "watchlist": watchlist, "avoidControls": avoid_controls,
        "realTier": list(baskets.get("real_tier", [])), "forward": forward,
    }


# a-priori power floor — mirrors vinci.themes.forward.MIN_DRIVERS (never tuned on returns)
_MIN_THEMES = 4


def _theme_index(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(summaries)
    total_buys = sum(s["ratifiedCount"] for s in summaries)
    total_wl = sum(s["watchlistCount"] for s in summaries)
    return {
        "drivers": summaries,
        "crossDriver": {
            "driversFrozen": n, "totalRatified": total_buys, "totalWatchlist": total_wl,
            "line": (f"{n} theme{'s' if n != 1 else ''} in snapshot; exposure-carry diagnostic "
                     f"poolable but UNPOWERED ({n} < {_MIN_THEMES} themes)."),
        },
        # the POOLED forward state — cross-theme facts that live at the portfolio altitude (not per
        # theme). On the snapshot day every horizon is 0 days forward → everything PENDING.
        "pooledForward": {
            "totalBuys": total_buys,
            "totalWatchlist": total_wl,
            "powerFloor": {
                "themes": n, "needed": _MIN_THEMES,
                "pct": min(100, round(100 * n / _MIN_THEMES)),
                "label": f"{n} of ~{_MIN_THEMES}-{_MIN_THEMES + 1} themes — unpowered",
            },
            "undefinedMeasures": _UNDEFINED_MEASURES,
            "honestyLabel": _HOLD_NONE_HONESTY,
            "diagnostics": [
                {"name": "exposure-carry", "status": "PENDING",
                 "note": "genuine-exposure vs other-PASSED divergence, pooled across themes — "
                         "PARTIALLY beta-controlled; the more informative of the two; pending "
                         "forward."},
                {"name": "avoid-discipline", "status": "PENDING",
                 "note": "was declining to buy the committed tier costly or vindicated, pooled — "
                         "beta-confounded; pending forward."},
            ],
        },
    }


def build_themes(themes_srcs: list[Path]) -> list[str]:
    """Transform each discovered freeze (one driver per src dir: forward_*_baskets.json + its
    _ledger.jsonl (+ any *scan*.jsonl for the none count)) into COMMITTED
    frontend/themes/<slug>.json + index.json. NON-DESTRUCTIVE: if NO source is found (the Cloudflare
    deploy — the source is git-ignored), it leaves the committed output untouched and WARNs, so the
    Edge-2 frontend and any prior theme commit still build/serve."""
    pairs: list[tuple[Path, Path, Path | None]] = []
    for d in themes_srcs:
        if not d.exists():
            continue
        for bp in sorted(d.glob("forward_*_baskets.json")):
            lp = bp.with_name(bp.name[: -len("_baskets.json")] + "_ledger.jsonl")
            if not lp.exists():
                print(f"WARN theme: {bp.name} has no sibling {lp.name} — skipped")
                continue
            scans = sorted(d.glob("*scan*.jsonl"))
            pairs.append((bp, lp, scans[0] if scans else None))
    if not pairs:
        print("themes: no freeze source (forward_*_baskets.json) found — leaving committed "
              "frontend/themes/ untouched (WARN; not an error)")
        return []
    OUT_THEMES.mkdir(parents=True, exist_ok=True)
    summaries: list[dict[str, Any]] = []
    for bp, lp, sp in pairs:
        baskets = json.loads(bp.read_text())
        display = _theme_display(baskets, _jsonl(lp), _jsonl(sp) if sp else None)
        (OUT_THEMES / f"{display['slug']}.json").write_text(json.dumps(display, indent=1))
        summaries.append({k: display[k] for k in ("slug", "label", "freezeDate", "ratifiedCount",
                          "surfacedCount", "frozenCount", "watchlistCount", "tierShape",
                          "frozenTiers")})
    summaries.sort(key=lambda s: s["slug"])
    (OUT_THEMES / "index.json").write_text(json.dumps(_theme_index(summaries), indent=1))
    return [s["slug"] for s in summaries]


# --------------------------------------------------------------------------------------------------
# Radar sweep bar — last-run / next-due (+30d) for the Component-A co-movement sweep. The CANONICAL
# invocation is recorded ONCE here (and in STATE §5 "CANONICAL invocation — recorded HERE, the ONE
# place; the future Radar screen MUST source it from here, no second hardcoding"); the frontend
# RENDERS this string, never hardcodes it. Display-only reminder — nothing fires automatically.
# --------------------------------------------------------------------------------------------------
_SWEEP_COMMAND = "python -m vinci.cli themes"
_SWEEP_SEED_DATE = "2026-06-17"  # the June-17 harvest — seeded last_run until a manifest exists
_SWEEP_CADENCE_DAYS = 30


def _radar_sweep_payload(manifest: Path) -> dict[str, str]:
    """Compute the sweep payload: last_run (latest ts of a COMPONENT-A row in the ROOT scan-history
    manifest, else the seeded June-17 harvest), source (manifest|seeded), next_due (+30d), and the
    canonical command. Pure — testable without the frontend dir. Refreshes on the next site build.

    `record_snapshot` writes ONE multi-driver manifest at data/scan_history/manifest.jsonl (each row
    carries a `driver_slug`), so the sweep bar must FILTER to `component-a` before taking the latest
    ts — a later row from another driver must not masquerade as the co-movement sweep's last run."""
    if manifest.exists():
        rows = [json.loads(line) for line in manifest.read_text().splitlines() if line.strip()]
        ca_ts = (str(r.get("ts", "")) for r in rows if r.get("driver_slug") == "component-a")
        ts = max(ca_ts, default="")
        last_run, source = (ts[:10] if ts else _SWEEP_SEED_DATE), ("manifest" if ts else "seeded")
    else:
        last_run, source = _SWEEP_SEED_DATE, "seeded"
    next_due = (date.fromisoformat(last_run) + timedelta(days=_SWEEP_CADENCE_DAYS)).isoformat()
    return {"last_run": last_run, "source": source, "next_due": next_due, "command": _SWEEP_COMMAND}


def emit_radar_sweep() -> None:
    """Write frontend/radar/sweep.json for the sweep bar (display-only — nothing fires). Reads
    the ROOT manifest where record_snapshot writes (data/scan_history/manifest.jsonl); the prior
    component-a/manifest.jsonl path never existed, so the bar re-seeded silently (the #125 bug)."""
    out = HERE / "radar"
    out.mkdir(parents=True, exist_ok=True)
    manifest = ROOT / "data" / "scan_history" / "manifest.jsonl"
    (out / "sweep.json").write_text(json.dumps(_radar_sweep_payload(manifest), indent=1) + "\n")


# --------------------------------------------------------------------------------------------------
# Radar INBOX + REVIEW LOG — join the latest component-a snapshot × analyst-owned reviews.json.
# The machine ASSEMBLES: match clusters to reviewed groups by MEMBER OVERLAP (ids are per-run,
# never match on id), sorting into inbox (unjudged) vs log (reviewed). It NEVER decides —
# reviews.json is the single record; a drifted match re-entering the inbox is CORRECT, not an
# error. Non-destructive: absent snapshot/reviews → keep the committed files (deploy-safe).
# --------------------------------------------------------------------------------------------------
_MATCH_MIN = 0.5  # member overlap as a fraction of the SMALLER set


def _overlap(a: set[str], b: set[str]) -> float:
    """|a ∩ b| / min(|a|, |b|) — overlap as a fraction of the smaller set (0 if either is empty)."""
    return len(a & b) / min(len(a), len(b)) if a and b else 0.0


def _latest_component_a(root: Path) -> Path | None:
    """Newest local/committed component-a snapshot (timestamp-prefixed filename → lexical max)."""
    snaps = sorted((root / "data" / "scan_history" / "component-a").glob("*.jsonl"))
    return snaps[-1] if snaps else None


def _sig(cluster: dict[str, Any], *keys: str) -> float | None:
    """Dig a numeric strength/admissibility value; None if any hop is missing (never fabricate)."""
    node: Any = cluster
    for k in keys:
        if not isinstance(node, dict) or k not in node:
            return None
        node = node[k]
    return node if isinstance(node, (int, float)) else None


# Static 4-digit SIC → industry-name map — only the codes in the current inbox. The repo has no
# SIC-name source (sectors.py is coarse sectors, not 4-digit names); nothing is fetched here.
# Display-only hint for an unreviewed cluster — the machine never names or decides a theme.
_SIC_NAME = {
    "1000": "Metal mining", "1040": "Gold & silver ores", "1600": "Heavy construction",
    "2080": "Beverages", "2810": "Industrial inorganic chemicals",
    "2833": "Medicinal chemicals", "2836": "Biological products", "3674": "Semiconductors",
    "3825": "Electrical measuring instruments", "3827": "Lab analytical instruments",
    "4911": "Electric utilities", "6199": "Finance services", "6282": "Investment advice",
    "7363": "Staffing services", "7370": "Computer services", "7371": "Computer programming",
    "7372": "Prepackaged software", "7373": "Systems integration",
    "7374": "Data processing services", "7389": "Business services",
    "8200": "Educational services", "8742": "Management consulting",
}


def _sic_name(code: str) -> str:
    return _SIC_NAME.get(code, f"SIC {code}")


def _industry_hint(cluster: dict[str, Any]) -> str | None:
    """Most common member SIC + coverage ("Semiconductors · 5/5"); a single industry or a majority →
    that. Else (≥2 industries, none a majority) → "mixed: <top> N · <second> M". Assemble-only hint
    for an unreviewed cluster — never a verdict. None when no member has a SIC. Deterministic."""
    members = cluster.get("members", [])
    sics = Counter(str(m.get("sic") or "").strip() for m in members)
    sics.pop("", None)
    if not sics:
        return None
    total = len(members)
    ranked = sics.most_common()
    top_code, top_n = ranked[0]
    if len(ranked) == 1 or top_n * 2 > total:  # single industry, or a strict majority
        return f"{_sic_name(top_code)} · {top_n}/{total}"
    sc, sn = ranked[1]
    return f"mixed: {_sic_name(top_code)} {top_n} · {_sic_name(sc)} {sn}"


def _draft_pairs(out: Path) -> list[tuple[set[str], dict[str, Any]]]:
    """DRAFTED records from radar/drafts.json as (member-set, record) pairs for a member-overlap
    join into the inbox. Only status=='drafted' with a name (unassessed-errors carry no draft).
    Empty when the file is absent (deploy-safe). The draft is ADVISORY — never marks a decision."""
    path = out / "drafts.json"
    if not path.exists():
        return []
    drafts = json.loads(path.read_text()).get("drafts", [])
    return [({t for t in d.get("members", []) if t}, d)
            for d in drafts if d.get("status") == "drafted" and d.get("draft_name")]


def _match_draft(cluster_set: set[str],
                 pairs: list[tuple[set[str], dict[str, Any]]]) -> dict[str, Any] | None:
    """Best-overlap drafted record for a cluster (≥ _MATCH_MIN of the smaller set), else None.
    Member-overlap join, not cluster_id (ids are per-run) — mirrors the reviews matcher above."""
    cand = [(s, d) for s, d in pairs if _overlap(cluster_set, s) >= _MATCH_MIN]
    if not cand:
        return None
    return max(cand, key=lambda sd: _overlap(cluster_set, sd[0]))[1]


def _inbox_entry(cluster: dict[str, Any], first_seen: str,
                 draft: dict[str, Any] | None = None) -> dict[str, Any]:
    """One inbox row for an unreviewed cluster (display-only stats; machine never decides). When an
    advisory draft matches, carry its name / read (terse reason) / suggestion — advisory, not a
    verdict; the fuller hypothesis stays in drafts.json (the machine-complete record)."""
    members = [m["ticker"] for m in cluster.get("members", [])]
    label = " ".join(members[:2]) + (f" +{len(members) - 2}" if len(members) > 2 else "")
    return {
        "cluster_id": cluster["cluster_id"], "first_seen": first_seen, "members": members,
        "label": label, "industry_hint": _industry_hint(cluster),
        "rel12": _sig(cluster, "strength_signals", "rel_strength_vs_market", "h12mo", "value"),
        "mom12": _sig(cluster, "strength_signals", "momentum", "h12mo", "value"),
        "coherence": _sig(cluster, "admissibility", "coherence_value"),
        "breadth_exp": _sig(cluster, "strength_signals", "breadth_expanding", "value"),
        "crowding": _sig(cluster, "strength_signals", "crowding_overextension", "value"),
        "draft_name": draft.get("draft_name") if draft else None,
        "draft_read": draft.get("reason") if draft else None,
        "draft_suggested": draft.get("suggested") if draft else None,
    }


def emit_radar_inbox_log() -> None:
    """Sort the latest component-a clusters into inbox (unreviewed) vs log (matched to a review), by
    member overlap ≥ _MATCH_MIN of the smaller set. Emits frontend/radar/{inbox,log}.json; assembles
    only — reviews.json is the single record. Non-destructive when a source is absent."""
    out = HERE / "radar"
    reviews_path = out / "reviews.json"
    snap_path = _latest_component_a(ROOT)
    if snap_path is None or not reviews_path.exists():
        return  # deploy / no local run → keep the committed inbox.json/log.json
    reviews = json.loads(reviews_path.read_text())["reviews"]
    clusters = [json.loads(line) for line in snap_path.read_text().splitlines() if line.strip()]
    m = re.match(r"(\d{4})(\d{2})(\d{2})", snap_path.name)
    scan_iso = "-".join(m.groups()) if m else ""

    review_sets = {r["key"]: set(r["members"]) for r in reviews}
    cluster_sets = {c["cluster_id"]: {mem["ticker"] for mem in c.get("members", [])}
                    for c in clusters}

    # LOG: every review + its current match status (best-overlap current cluster + membership delta)
    log_reviews = []
    for r in sorted(reviews, key=lambda r: r["key"]):
        rset = review_sets[r["key"]]
        cand = sorted((cid for cid, cs in cluster_sets.items() if _overlap(cs, rset) >= _MATCH_MIN))
        if cand:
            best = max(cand, key=lambda cid: _overlap(cluster_sets[cid], rset))  # ties → lowest cid
            cs = cluster_sets[best]
            match = {"status": "matched", "cluster_id": best,
                     "added": sorted(cs - rset), "dropped": sorted(rset - cs)}
        else:
            match = {"status": "gone", "cluster_id": None, "added": [], "dropped": []}
        log_reviews.append({**r, "match": match})

    # INBOX: current clusters matched by NO review (not yet judged). An advisory draft (if any) is
    # joined by member overlap — it informs the row, never marks it reviewed.
    draft_pairs = _draft_pairs(out)
    inbox = sorted(
        (_inbox_entry(c, scan_iso, _match_draft(cluster_sets[c["cluster_id"]], draft_pairs))
         for c in clusters
         if not any(_overlap(cluster_sets[c["cluster_id"]], rs) >= _MATCH_MIN
                    for rs in review_sets.values())),
        key=lambda e: e["cluster_id"])

    (out / "inbox.json").write_text(
        json.dumps({"scan_date": scan_iso, "inbox": inbox}, indent=1, ensure_ascii=False) + "\n")
    (out / "log.json").write_text(
        json.dumps({"scan_date": scan_iso, "reviews": log_reviews},
                   indent=1, ensure_ascii=False) + "\n")
    gone = sum(1 for r in log_reviews if r["match"]["status"] == "gone")
    print(f"radar inbox+log: {len(clusters)} clusters → {len(clusters) - len(inbox)} matched / "
          f"{len(inbox)} inbox; {len(log_reviews)} reviews ({gone} gone)")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(
        description="Assemble the static snapshot mirror the dashboard serves."
    )
    ap.add_argument("--themes-src", nargs="*", dest="themes_src", default=None,
                    help="dir(s) each holding ONE driver's frozen freeze (forward_*_baskets.json + "
                         "_ledger.jsonl, + any *scan*.jsonl for the none count). "
                         "Default: data/forward/. Absent → the committed frontend/themes/ is left "
                         "untouched.")
    args = ap.parse_args(argv)

    for d in (OUT_SNAP, OUT_DOSS):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)

    for name in _MIRRORED:
        shutil.copyfile(SNAP / name, OUT_SNAP / name)
    # universe gate-exclusion health stats — present once the universe has been built with the
    # stats emit (vinci/universe.py). Absent on older snapshots → the ingestion screen degrades.
    if (SNAP / "universe_stats.json").exists():
        shutil.copyfile(SNAP / "universe_stats.json", OUT_SNAP / "universe_stats.json")

    # DERIVED dossiers only (data/dossiers/<TICKER>/dossier.json → dossiers/<TICKER>.json).
    tickers: list[str] = []
    if DOSS.exists():
        for folder in sorted(p for p in DOSS.iterdir() if p.is_dir()):
            f = folder / "dossier.json"
            if f.is_file():
                ticker = folder.name.upper()
                shutil.copyfile(f, OUT_DOSS / f"{ticker}.json")
                tickers.append(ticker)
    (OUT_DOSS / "index.json").write_text(json.dumps({"tickers": tickers}, indent=2))

    # DERIVED EDGAR-10-K exposure map → slim graph.json (edges + shared nodes + headline stats).
    # Authorized for the private/authed repo as a derived artifact (CLAUDE.md) and COMMITTED there
    # (verbatim PUBLIC 10-K phrases + relationship-TYPE taxonomy only, no CIQ workbook data); the
    # deploy regenerates graph.json from it. If absent (e.g. a public repo) the graph screen
    # degrades to UNKNOWN.
    if GRAPH.exists():
        g = json.loads(GRAPH.read_text())
        slim = {
            "model": g.get("model"),
            "stats": {
                "names": g.get("n_names"),
                "withEdges": g.get("names_with_edges"),
                "totalEdges": g.get("total_edges"),
                "realEdges": g.get("real_edges"),
                "realUsListed": g.get("real_us_listed"),
            },
            "edges": [
                {
                    "focal": e.get("focal_ticker"),
                    "counterpartyName": e.get("counterparty_name"),
                    "counterpartyTicker": e.get("counterparty_ticker"),
                    "relType": e.get("relationship_type"),
                    "direction": e.get("direction"),
                    "resolution": e.get("node_kind"),
                    "evidence": e.get("evidence"),
                }
                for e in g.get("edges", [])
            ],
            "sharedNodes": g.get("shared_nodes", []),
            "superConnectors": g.get("super_connectors", []),
        }
        (OUT_SNAP / "graph.json").write_text(json.dumps(slim))

    # manifest.json — the cheap index. Regenerated every build, so it cannot drift
    # from the snapshots. Only carries what the UI can't cheaply derive client-side.
    queue = _jsonl(SNAP / "ranked_queue.jsonl")
    uni_path = SNAP / "universe_snapshot.jsonl"
    uni = _jsonl(uni_path) if uni_path.exists() else []
    manifest = {
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        "source_commit": _git_sha(),
        "universe": {"count": len(uni), "as_of": (uni[0].get("as_of") if uni else None)},
        "screen": {
            "candidates": len(queue),
            "as_of": (
                str(queue[0].get("screen_run_at"))[:10]
                if queue and queue[0].get("screen_run_at")
                else None
            ),
        },
        # Queue summary counts so the overview reads two numbers from this ~200-byte file instead
        # of fetching + parsing the full ~440 KB ranked_queue.jsonl to show them. The full queue
        # still loads lazily on the Ranker screen, where it's actually needed.
        "queue": {
            "total": len(queue),
            "demoted": sum(1 for r in queue if r.get("structurally_disqualified")),
            "gated": sum(1 for r in queue if r.get("tradeability_gated")),
        },
    }
    (OUT_SNAP / "manifest.json").write_text(json.dumps(manifest, indent=2))

    # G3 (multiple) UNKNOWN disambiguation — split the ambiguous "XBRL absent / negative earnings"
    # into the actual per-name reason (label-integrity), derived from the committed candidate facts.
    cand_path = SNAP / "candidate_records.jsonl"
    g3: dict[str, str] = {}
    if cand_path.exists():
        for row in _jsonl(cand_path):
            payload = row.get("payload")
            p = json.loads(payload) if isinstance(payload, str) else (payload or row)
            dr = p.get("data_record", p)
            f = dr["fundamentals"]
            ev = f.get("ev_ebitda_pctile_vs_history") or {}
            pe_pct = f.get("pe_pctile_vs_history") or {}
            if ev.get("coverage_status") == "present" or pe_pct.get("coverage_status") == "present":
                continue  # multiple is known — no disambiguation needed
            pe = f.get("pe") or {}
            ois = f.get("op_income_sign") or {}
            fcf = f.get("fcf_sign") or {}
            neg = (ois.get("value") is not None and ois["value"] < 0) or (
                fcf.get("value") is not None and fcf["value"] < 0
            )
            if neg:
                reason = "negative earnings — no meaningful P/E"
            elif pe.get("coverage_status") != "present":
                reason = "multiple data absent — EDGAR XBRL gap"
            else:
                reason = "P/E present, no 5y percentile — insufficient history"
            g3[dr["identity"]["ticker"]] = reason
    (OUT_SNAP / "g3_reasons.json").write_text(json.dumps(g3))

    # THEME-EDGE display JSON — non-destructive when the (git-ignored) freeze source is absent.
    theme_srcs = [Path(p) for p in (args.themes_src or [FORWARD])]
    theme_slugs = build_themes(theme_srcs)

    # Radar sweep bar — regenerated every build (manifest git-ignored → seeded; a run refreshes).
    emit_radar_sweep()
    # Radar inbox + review log — sort latest clusters into unreviewed vs reviewed (non-destructive).
    emit_radar_inbox_log()

    print(
        f"mirror: {len(queue)} queue rows, {len(uni)} universe rows, "
        f"{len(tickers)} dossier(s) [{', '.join(tickers) or 'none'}], "
        f"{len(theme_slugs)} theme(s) [{', '.join(theme_slugs) or 'none'}] → frontend/"
    )


if __name__ == "__main__":
    main()
