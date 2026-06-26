"""Orchestrate per-finalist dossier assembly — PARALLEL across the cohort, fail-loud per name.

Parallel assembly is the AI-native leverage: the ~10/week the ranked queue surfaces are independent,
so they assemble concurrently (I/O-bound on EDGAR/LLM). Each name opens its own store + EDGAR
clients (SQLite/HTTP aren't safely shared across threads); the resolver index and graph are shared
read-only. A name whose CIQ export is missing still produces a dossier (CIQ sections MISSING + a
'pull CIQ' flag); any other per-name failure becomes an error and the batch continues — fail-loud.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from vinci.config import Config, get_config
from vinci.dossier import ciq_sheets, requirements
from vinci.dossier.ciq import CiqBundle
from vinci.dossier.manual_store import ManualDataStore, make_manual_store
from vinci.dossier.mechanical import assemble_mechanical
from vinci.dossier.render import render_markdown
from vinci.dossier.schemas import Dossier
from vinci.dossier.synthesis import synthesize
from vinci.edgar.client import EdgarClient
from vinci.graph.exposure import ExposureGraph
from vinci.graph.llm import LlmClient
from vinci.rank import load_candidates_from_snapshot
from vinci.resolver import EntityResolver
from vinci.schemas.candidate import CandidateRecord
from vinci.sec import build_sec_http
from vinci.store import Store


@dataclass(frozen=True)
class Finalist:
    """A ranked-queue finalist: the screen record, its queue rank, and the as-of reference date."""

    record: CandidateRecord
    rank: int | None
    reference_date: date


def _ref_of(row: dict[str, Any]) -> date:
    sra = row.get("screen_run_at")
    return date.fromisoformat(str(sra)[:10]) if sra else date.today()


def load_finalists(
    cfg: Config, *, top: int | None = None, ticker: str | None = None
) -> list[Finalist]:
    """Join the ranked-queue order (top N) to candidate-records facts. ``--ticker`` picks one."""
    snaps = cfg.snapshots_dir
    cands = load_candidates_from_snapshot(snaps / "candidate_records.jsonl")
    by_cid = {c.candidate_id: c for c in cands}
    by_ticker = {c.data_record.identity.ticker: c for c in cands}
    queue_path = snaps / "ranked_queue.jsonl"
    queue: list[dict[str, Any]] = (
        [json.loads(line) for line in queue_path.read_text().splitlines() if line.strip()]
        if queue_path.exists()
        else []
    )
    queue.sort(key=lambda r: int(r.get("rank", 1_000_000)))

    if ticker:
        t = ticker.upper()
        row = next((r for r in queue if r.get("ticker") == t), None)
        rec = by_ticker.get(t) or (by_cid.get(str(row["candidate_id"])) if row else None)
        if rec is None:
            raise LookupError(f"{t} not in candidate_records.jsonl — run screen then rank first")
        return [Finalist(rec, int(row["rank"]) if row else None, _ref_of(row or {}))]

    out: list[Finalist] = []
    for r in queue[: top or len(queue)]:
        rec = by_cid.get(str(r.get("candidate_id"))) or by_ticker.get(str(r.get("ticker")))
        if rec is not None:
            out.append(Finalist(rec, int(r["rank"]) if "rank" in r else None, _ref_of(r)))
    return out


def _load_graph(cfg: Config) -> ExposureGraph:
    path = cfg.data_dir / "graph_coverage.json"
    edges = json.loads(path.read_text())["edges"] if path.exists() else []
    return ExposureGraph.from_edges(edges)


def _write(dossier: Dossier, llm_log: str, out_root: Path) -> Path:
    folder = out_root / dossier.ticker
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "dossier.json").write_text(dossier.model_dump_json(indent=2))
    (folder / "dossier.md").write_text(render_markdown(dossier))
    (folder / "llm_call.log").write_text(llm_log or "(no LLM call — synthesis skipped)")
    return folder


def assemble_one(
    fin: Finalist,
    *,
    cfg: Config,
    resolver: EntityResolver,
    graph: ExposureGraph,
    manual: ManualDataStore,
    out_root: Path,
    llm: LlmClient | None,
) -> Dossier:
    """Assemble + persist one finalist's dossier. Opens its own store/edgar (thread-safe)."""
    rec = fin.record.data_record
    ticker = rec.identity.ticker
    bundle = CiqBundle.from_files(ticker, manual.files(ticker))
    location = manual.location(ticker)
    # MISSING-manifest: per-module 'pull CIQ' flags from the ONE requirements definition (so this
    # and `vinci dossier requirements` can't drift). Empty/partial folder → what's still owed.
    flags: list[str] = requirements.manifest_flags(bundle, ticker=ticker, location=location)
    with Store(cfg.db_path) as store:
        mech, mech_flags = assemble_mechanical(
            rec, store=store, edgar=EdgarClient.from_config(cfg), http=build_sec_http(cfg),
            graph=graph, resolver=resolver, bundle=bundle, reference_date=fin.reference_date,
        )
    flags += mech_flags
    synthesis = None
    llm_log = ""
    if llm is not None:
        synthesis, synth_flags, llm_log = synthesize(
            mech, llm=llm, ticker=ticker, name=rec.identity.name,
            transcript=ciq_sheets.transcript_for_synthesis(bundle),
        )
        flags += synth_flags
    else:
        flags.append("LLM synthesis skipped (no ANTHROPIC client) — mechanical layer only")
    dossier = Dossier(
        ticker=ticker, name=rec.identity.name, cik=rec.identity.cik,
        reference_date=fin.reference_date, rank=fin.rank, mechanical=mech, synthesis=synthesis,
        flags=flags, llm_model=(llm.model if llm else None), assembled_at=datetime.now(),
    )
    _write(dossier, llm_log, out_root)
    return dossier


def assemble_cohort(
    finalists: list[Finalist],
    *,
    cfg: Config | None = None,
    llm: LlmClient | None = None,
    manual: ManualDataStore | None = None,
    max_workers: int = 8,
) -> tuple[list[Dossier], list[str]]:
    """Assemble the cohort in parallel → (dossiers, per-name errors). The batch never crashes."""
    cfg = cfg or get_config()
    cfg.ensure_dirs()
    resolver = EntityResolver.from_config(cfg)
    _ = resolver.index  # preload once so worker threads only do read-only lookups
    graph = _load_graph(cfg)
    manual = manual or make_manual_store(cfg)
    out_root = cfg.data_dir / "dossiers"

    def task(fin: Finalist) -> tuple[Dossier | None, str | None]:
        try:
            return assemble_one(
                fin, cfg=cfg, resolver=resolver, graph=graph, manual=manual,
                out_root=out_root, llm=llm,
            ), None
        except Exception as exc:  # noqa: BLE001 — one bad name must not crash the cohort batch
            return None, f"{fin.record.data_record.identity.ticker}: {type(exc).__name__}: {exc}"

    dossiers: list[Dossier] = []
    errors: list[str] = []
    with ThreadPoolExecutor(max_workers=min(max_workers, max(1, len(finalists)))) as pool:
        for dossier, error in pool.map(task, finalists):
            if dossier is not None:
                dossiers.append(dossier)
            if error is not None:
                errors.append(error)
    return dossiers, errors
