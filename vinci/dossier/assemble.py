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
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from vinci.config import Config, get_config
from vinci.dossier import ciq_sheets, requirements
from vinci.dossier import flags as dossier_flags
from vinci.dossier.ciq import CiqBundle
from vinci.dossier.covenant_extract import (
    covenant_digest,
    extract_covenant_terms,
    extract_maturity_event,
    governing_terms,
)
from vinci.dossier.manual_store import LocalFolderStore, ManualDataStore
from vinci.dossier.mechanical import assemble_mechanical
from vinci.dossier.render import render_markdown
from vinci.dossier.schemas import Dossier, Sourced, SourceStatus
from vinci.dossier.synthesis import synthesize
from vinci.edgar.client import EdgarClient
from vinci.finra import build_finra_http
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
            finra=build_finra_http(cfg), graph=graph, resolver=resolver, bundle=bundle,
            reference_date=fin.reference_date,
        )
    flags += mech_flags
    synthesis = None
    logs: list[str] = []
    term_rows = None  # (E5) per-exhibit rows — attached to mech AFTER synthesis (render only)
    if llm is not None:
        # (P1/FIX-0) Tier-2 covenant + maturity extraction runs BEFORE synthesis so the LLM reasons
        # with the ACTUAL governing terms via a term→value digest — never a pointer to unseen data.
        # (P3) the maturity-resolution event is extracted here too and fed to synthesis + the wall.
        if mech.capital_structure is not None:
            http = build_sec_http(cfg)
            cik0 = rec.identity.cik or ""
            term_rows, _sum, cov_flags, cov_log = extract_covenant_terms(
                mech.capital_structure, llm=llm, http=http, cik=cik0, ticker=ticker,
                name=rec.identity.name)
            maturity_event, mat_flags, mat_log = extract_maturity_event(
                mech.capital_structure, llm=llm, http=http, cik=cik0, ticker=ticker,
                name=rec.identity.name)
            flags += cov_flags + mat_flags
            logs += [lg for lg in (cov_log, mat_log) if lg]
            ptrs = mech.capital_structure.covenant_pointer_rows
            gov = (governing_terms(term_rows.value or [], ptrs.value)
                   if term_rows is not None and ptrs is not None and ptrs.value else [])
            mat_present = (maturity_event is not None
                           and maturity_event.status is SourceStatus.PRESENT)
            fail = (None if (gov or mat_present)
                    else "no covenant terms extracted from located exhibits")
            digest = covenant_digest(gov, maturity_event, fail_reason=fail)
            cs_pre = mech.capital_structure.model_copy(update={
                "covenant_terms": Sourced.present(digest, source_ref="fenced Tier-2 digest (P1)"),
                "maturity_event": maturity_event})
            mech = mech.model_copy(update={"capital_structure": cs_pre})
        synthesis, synth_flags, synth_log = synthesize(
            mech, llm=llm, ticker=ticker, name=rec.identity.name,
            transcript=ciq_sheets.transcript_for_synthesis(bundle),
        )
        flags += synth_flags
        logs.append(synth_log)
        # (render) attach the structured per-exhibit rows AFTER synthesis (the LLM used the digest).
        if term_rows is not None and mech.capital_structure is not None:
            cs_post = mech.capital_structure.model_copy(update={"covenant_term_rows": term_rows})
            mech = mech.model_copy(update={"capital_structure": cs_post})
    else:
        flags.append("LLM synthesis skipped (no ANTHROPIC client) — mechanical layer only")
    llm_log = "\n\n".join(lg for lg in logs if lg)
    # split the emitted flags by audience: decision caveats → human PDF/web (re-voiced), machine
    # QA self-checks → dev/JSON only (emission logic is untouched; classification is display-layer).
    caveats, qa_flags = dossier_flags.partition(flags)
    dossier = Dossier(
        ticker=ticker, name=rec.identity.name, cik=rec.identity.cik,
        reference_date=fin.reference_date, rank=fin.rank, mechanical=mech, synthesis=synthesis,
        caveats=caveats, qa_flags=qa_flags,
        # UTC-aware so the stamp is unambiguous and comparable across machines/timezones — it lets
        # the human tell two same-day re-assemblies apart (rendered with time + "UTC").
        llm_model=(llm.model if llm else None), assembled_at=datetime.now(UTC),
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
    manual = manual or LocalFolderStore.from_config(cfg)
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
