#!/usr/bin/env python3
"""Assemble the static snapshot mirror the dashboard serves.

Copies the lightweight committed snapshots (and DERIVED dossiers — never the raw
CIQ workbooks) into ``frontend/``, and generates ``manifest.json`` (the cheap
index: counts + dates that the UI can't otherwise derive without fetching the
megabyte-scale candidate files). Run by Cloudflare Pages on every deploy, and
locally for preview.

It READS only committed snapshots under ``data/snapshots/`` (+ local
``data/dossiers/`` when present) and WRITES only into ``frontend/snapshots/`` and
``frontend/dossiers/`` (both git-ignored — regenerated, never committed). It is
not a backend and runs no pipeline; it only mirrors existing artifacts.

LICENSING: only the DERIVED ``dossier.json`` is mirrored. The raw licensed CIQ
exports in ``data/manual/ciq/`` are never read or copied here. ``data/dossiers/``
is git-ignored, so on the deploy the dossier mirror is empty until the derived
``dossier.json`` is committed to the PRIVATE repo (gated on private/authed).
"""
from __future__ import annotations

import json
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SNAP = ROOT / "data" / "snapshots"
DOSS = ROOT / "data" / "dossiers"
GRAPH = ROOT / "data" / "graph_coverage.json"  # DERIVED EDGAR-10-K exposure map (private-repo only)
OUT_SNAP = HERE / "snapshots"
OUT_DOSS = HERE / "dossiers"

# The lightweight snapshots the UI fetches at runtime. The MB-scale candidate /
# universe / securities files are intentionally NOT mirrored — their derived
# counts go into manifest.json instead, so the deploy stays small.
_MIRRORED = ("ranked_queue.jsonl", "decision_ledger.jsonl")


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _git_sha() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except Exception:  # noqa: BLE001 — provenance is best-effort; absence is shown as "—"
        return None


def main() -> None:
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
    # Authorized for the private/authed repo as a derived artifact (CLAUDE.md). git-ignored, so on a
    # deploy it is absent until graph_coverage.json is committed; the graph screen degrades to
    # UNKNOWN.
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
    print(
        f"mirror: {len(queue)} queue rows, {len(uni)} universe rows, "
        f"{len(tickers)} dossier(s) [{', '.join(tickers) or 'none'}] → frontend/"
    )


if __name__ == "__main__":
    main()
