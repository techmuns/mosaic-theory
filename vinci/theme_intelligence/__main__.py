"""CLI — every entry point (manual, scheduled, CI) runs the SAME pipeline.

    python -m vinci.theme_intelligence scan --days 10
    python -m vinci.theme_intelligence scan --from 2026-09-28 --to 2026-10-09
    python -m vinci.theme_intelligence article --url <URL> --as-of 2026-02-09
    python -m vinci.theme_intelligence report --latest | --week 2026-W41 | --run <RUN_ID>
    python -m vinci.theme_intelligence qa --run <RUN_ID|latest>
    python -m vinci.theme_intelligence sources [--check-health [--json] [--force]]
    python -m vinci.theme_intelligence ingest-file --path report.pdf --source ms_research \
        [--url U] [--title T] [--author A] [--published YYYY-MM-DD] [--llm-permitted]
    python -m vinci.theme_intelligence ingest-inbox [--inbox DIR] [--source S]
    python -m vinci.theme_intelligence documents [--status HELD]
    python -m vinci.theme_intelligence enrich --as-of YYYY-MM-DD [--thesis TH-…] [--refresh] \
        [--budget USD]
    python -m vinci.theme_intelligence reanalyse --article A-… [--article A-…] --retire TH-… \
        [--retire TH-…] --reason "…" --as-of YYYY-MM-DD [--budget USD]
    python -m vinci.theme_intelligence state pull|push|status --remote <git remote> \
        [--branch theme-intelligence-state]
    python -m vinci.theme_intelligence upload --remote <git remote> --path report.pdf \
        --source ms_research --budget USD [--llm-permitted] [--dry-run]
    python -m vinci.theme_intelligence author --article A-… --name NAME [--title T] --by NAME \
        --reason "…"
    python -m vinci.theme_intelligence review list [--thesis TH-…] [--history]
    python -m vinci.theme_intelligence review dismiss|reopen --finding F-… --reviewer NAME \
        --reason "…"
    python -m vinci.theme_intelligence init | backup | export-state --out D | import-state --src D

Exit status: 0 = the run succeeded; 2 = PARTIAL (some source or article could not be processed —
the report says which); 1 = FAILED. A failed or partial run is never presented as a quiet week.
"""

from __future__ import annotations

# ruff: noqa: E402
# (the imports below follow the `.env` load on purpose — it must run before any of them)
from vinci.config import load_local_env

if __name__ == "__main__":
    # `python -m vinci.theme_intelligence` only, and FIRST: modules imported below read the
    # environment at import (config.USER_AGENT from SEC_USER_AGENT), so the repo-root `.env` must
    # be in it before they load. On Actions there is none and injected secrets win
    # (override=False). Importing this module (a test) never runs this, so tests stay hermetic.
    # 2026-10-16: `market` failed locally on POLYGON_API_KEY while `.env` was loaded only inside
    # the model-client setup; REVIEW of #739: loading it after these imports missed USER_AGENT.
    load_local_env()

import argparse
import json
import sys
import traceback
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from vinci.theme_intelligence.config import (
    DEFAULT_DATA_DIR,
    DEFAULT_MAX_ARTICLES_PER_RUN,
    DEFAULT_SCAN_DAYS,
    LLM_MAX_TOKENS,
    LLM_MODEL,
    Paths,
    SourceConfig,
    load_sources,
    load_taxonomy,
)
from vinci.theme_intelligence.display import clip
from vinci.theme_intelligence.extract import ToolClient
from vinci.theme_intelligence.fetch import PoliteFetcher
from vinci.theme_intelligence.schemas import RunStatus
from vinci.theme_intelligence.store import Store

_EXIT = {RunStatus.SUCCEEDED: 0, RunStatus.PARTIAL: 2, RunStatus.FAILED: 1,
         RunStatus.RUNNING: 1, RunStatus.INTERRUPTED: 1}


def _client(required: bool) -> ToolClient | None:
    import os

    # the key comes from the environment the `python -m` entry loaded (`.env` locally, Actions
    # secrets in CI); loading it here as well made a test that calls `main` read the real `.env`
    if not os.environ.get("ANTHROPIC_API_KEY"):
        if required:
            raise SystemExit("ANTHROPIC_API_KEY is not set — extraction needs the LLM (cached "
                             "article versions still replay without it: pass --cache-only)")
        return None
    from vinci.theme_intelligence.llm import ThemeLlmClient

    return ThemeLlmClient(model=LLM_MODEL, max_tokens=LLM_MAX_TOKENS)


def source_for_url(url: str, sources: tuple[SourceConfig, ...]) -> str:
    """The channel whose configured entry, listing, sitemap or feed URL is on this URL's host
    (EXACT host). A SemiAnalysis post lives on newsletter.semianalysis.com, its feed's host, not
    on the entry page's semianalysis.com — matched on the entry host alone it was filed
    "UNKNOWN publisher" (observed 2026-10-10). No match → "manual"."""
    host = urlparse(url).netloc.lower()
    for s in sources:
        urls = (s.entry_url, s.listing_url, s.sitemap_url, s.feed_url)
        if host in {urlparse(u).netloc.lower() for u in urls if u}:
            return s.id
    return "manual"


def _iso(s: str) -> date:
    return date.fromisoformat(s)


def _author_name(s: str) -> str:
    """An author's name as the operator states it: the document record keeps names
    "; "-joined, so a name holding ';' would come back as two (review of #771)."""
    if ";" in s:
        raise argparse.ArgumentTypeError(f"an author's name may not contain ';': {s!r}")
    return s


def _week_bounds(week: str) -> tuple[date, date]:
    y, w = week.upper().split("-W")
    start = date.fromisocalendar(int(y), int(w), 1)
    return start, start + timedelta(days=6)


def cmd_init(a: argparse.Namespace) -> int:
    paths = Paths(Path(a.data_dir))
    paths.ensure()
    st = Store(paths.db)
    print(f"registry {paths.db} at schema version {st.schema_version()}")
    return 0


def cmd_article(a: argparse.Namespace) -> int:
    from vinci.theme_intelligence.pipeline import Pipeline
    from vinci.theme_intelligence.report import write_run_outputs

    sources = load_sources()
    taxonomy = load_taxonomy()
    client = None if a.cache_only else _client(required=False)
    fixture = json.loads(Path(a.fixture).read_text()) if a.fixture else None
    html = Path(a.html).read_text() if a.html else None
    pipe = Pipeline(Path(a.data_dir), sources=sources, taxonomy=taxonomy, client=client,
                    review=not a.no_review)
    from vinci.theme_intelligence.config import retired_for

    r = retired_for(source_id=a.source, url=a.url)
    if r is not None:
        print(f"refused: {r.publisher} was retired on {r.retired} ({r.reason}) — its research "
              f"is not analysed")
        return 1
    sid = a.source or source_for_url(a.url, sources)
    note = (f"operator-supplied copy — a MANUAL UPLOAD of an authorized document "
            f"({Path(a.html).name})" if a.html else "supplied fixture HTML")
    h = pipe.store.latest_health().get(sid)
    if a.html and h is not None and h.status.value in ("BLOCKED", "DEGRADED"):
        print(f"channel {sid} is {h.status.value} ({h.reason[:100]}) — this upload is analysed "
              f"through the same pipeline; the channel's health is unchanged (one document is "
              f"not proof its coverage is complete)")
    run, res = pipe.run_article(a.url, as_of=_iso(a.as_of), source_id=sid, html=html,
                                fixture=fixture, publisher=a.publisher, html_note=note,
                                published=_iso(a.published) if a.published else None,
                                budget=a.budget)
    print(f"run {run.run_id}: scan execution {run.status.value} — article {res.status} "
          f"{res.note}".rstrip())
    for o in res.outcomes:
        prev = o.previous_action.value if o.previous_action else "—"
        print(f"  {o.thesis_id}  {o.action.value:<12} (was {prev:<12}) "
              f"{o.evidence_direction.value:<9} {o.contribution.value:<24} {o.title}")
    out = write_run_outputs(pipe.store, run.run_id, Path(a.out) if a.out else None)
    v = out["dashboard"].verification
    print(f"research verification {v['status']} — {v['summary']}")
    print(f"cost ${run.cost_usd if run.cost_usd is not None else 'UNKNOWN'} · tokens {run.tokens}")
    print(f"outputs: {out['dir']}")
    return _EXIT[run.status]


def cmd_scan(a: argparse.Namespace) -> int:
    from vinci.theme_intelligence.pipeline import Pipeline
    from vinci.theme_intelligence.report import write_run_outputs

    sources = load_sources()
    if a.sources:
        wanted = set(a.sources.split(","))
        unknown = wanted - {s.id for s in sources}
        if unknown:
            raise SystemExit(f"unknown source id(s): {sorted(unknown)}")
        sources = tuple(s for s in sources if s.id in wanted)
    taxonomy = load_taxonomy()
    today = datetime.now(tz=UTC).date()
    if a.date_from or a.date_to:
        if not (a.date_from and a.date_to):
            raise SystemExit("--from and --to go together")
        w_from, w_to = _iso(a.date_from), _iso(a.date_to)
    else:
        w_to = today
        w_from = w_to - timedelta(days=a.days - 1)
    if w_from > w_to:
        raise SystemExit("--from is after --to")
    as_of = _iso(a.as_of) if a.as_of else w_to
    client = None if a.cache_only else _client(required=True)
    pipe = Pipeline(Path(a.data_dir), sources=sources, taxonomy=taxonomy, client=client,
                    review=not a.no_review, enrich=not a.no_enrich)
    run = pipe.run_scan(window_from=w_from, window_to=w_to, as_of=as_of,
                        max_articles=a.max_articles, resume_run_id=a.resume, budget=a.budget)
    out = write_run_outputs(pipe.store, run.run_id, Path(a.out) if a.out else None)
    print(f"run {run.run_id}: scan execution {run.status.value} · window {w_from}..{w_to} · "
          f"as-of {as_of}")
    for sc in run.sources:
        print(f"  {sc.source_id:<20} {sc.status:<8} discovered {sc.discovered:>3} · in window "
              f"{sc.in_window:>3} · undated {sc.undated:>3} · new {sc.new:>3} · known "
              f"{sc.already_known:>3} · processed {sc.processed:>3} · queued {sc.queued:>3} · "
              f"out-of-window {sc.skipped_out_of_window:>3} · inaccessible {sc.inaccessible:>3} · "
              f"errors {len(sc.errors):>2}"
              + (f" — the first: {clip(sc.errors[0], 120, 'the run manifest')}"
                 if sc.errors else ""))
    print(f"counts {run.counts}")
    hs = out["dashboard"].source_health
    print(f"source health (checked at the start of this scan) — {hs.get('line', 'not checked')}")
    v = out["dashboard"].verification
    print(f"research verification {v['status']} — {v['summary']}")
    print(f"cost ${run.cost_usd if run.cost_usd is not None else 'UNKNOWN'} · tokens {run.tokens}")
    print(f"outputs: {out['dir']}")
    return _EXIT[run.status]


def cmd_report(a: argparse.Namespace) -> int:
    from vinci.theme_intelligence.report import write_run_outputs

    paths = Paths(Path(a.data_dir))
    st = Store(paths.db)
    runs = st.runs()
    if not runs:
        raise SystemExit("no runs recorded yet")
    if a.run:
        chosen = [r for r in runs if r.run_id == a.run]
    elif a.week:
        lo, hi = _week_bounds(a.week)
        chosen = [r for r in runs if lo <= r.as_of <= hi]
    else:
        chosen = runs
    if not chosen:
        raise SystemExit("no run matches")
    run = max(chosen, key=lambda r: r.started_at)
    out = write_run_outputs(st, run.run_id, Path(a.out) if a.out else None)
    print(f"report for {run.run_id} ({run.status.value}): {out['dir']}")
    return 0


def cmd_publish(a: argparse.Namespace) -> int:
    """Publish one run's research desk into the main app (`frontend/theme-intelligence/`) — see
    publish.py. Commit the folder as an artifact-only commit; Cloudflare Pages deploys it."""
    from vinci.theme_intelligence.publish import PublishError, publication_lag, publish

    st = Store(Paths(Path(a.data_dir)).db)
    if a.check:  # nothing written: is the app's desk behind the registry? (exit 2 when it is)
        lag = publication_lag(st, Path(a.out))
        print(lag or f"the app's research desk shows the registry's latest run ({a.out})")
        return 2 if lag else 0
    runs = st.runs()
    if not runs:
        raise SystemExit("no runs recorded yet")
    chosen = [r for r in runs if r.run_id == a.run] if a.run else runs
    if not chosen:
        raise SystemExit(f"no run {a.run}")
    run = max(chosen, key=lambda r: r.started_at)
    try:
        m = publish(st, run.run_id, Path(a.out), allow_test_data=a.allow_test_data)
    except PublishError as exc:
        print(f"refused: {exc}")
        return 1
    print(f"published {run.run_id} ({m['week']}): {len(m['files'])} file(s), {m['theses']} "
          f"thesis page(s) -> {a.out}")
    return 0


def cmd_reassess(a: argparse.Namespace) -> int:
    from vinci.theme_intelligence.engine import SentenceCorrection
    from vinci.theme_intelligence.pipeline import Pipeline
    from vinci.theme_intelligence.report import write_run_outputs

    corrections = [SentenceCorrection(
        thesis_id=c["thesis_id"], sentence_id=c["sentence_id"], text=c["text"],
        claim_ids=tuple(c["claim_ids"]), reason=c["reason"])
        for c in (json.loads(Path(a.corrections).read_text()) if a.corrections else [])]
    pipe = Pipeline(Path(a.data_dir), sources=load_sources(), taxonomy=load_taxonomy(),
                    client=None, review=False)  # stored evidence only: no model client at all
    run, outs = pipe.run_reassess(as_of=_iso(a.as_of), thesis_ids=a.thesis or (),
                                  corrections=corrections)
    print(f"run {run.run_id}: {run.status.value} — {run.counts.get('theses_reassessed', 0)} "
          f"thesis(es) reassessed from stored evidence, {len(outs)} changed; cost $0.00")
    for o in outs:
        was = o.previous_action.value if o.previous_action else "—"
        print(f"  {o.thesis_id} v{o.new_version}: {was} → {o.action.value} "
              f"({', '.join(o.events)}) — {o.title[:70]}")
    out = write_run_outputs(pipe.store, run.run_id)
    print(f"outputs: {out['dir']}")
    return 0


def cmd_enrich(a: argparse.Namespace) -> int:
    """The enrichment step: the listed companies each thesis's own steps imply, as EXTERNAL
    HYPOTHESES checked against the SEC (enrich.py) — one paid call per thesis, never a new
    thesis version, never read by a priority rule."""
    from vinci.theme_intelligence.pipeline import Pipeline
    from vinci.theme_intelligence.report import write_run_outputs

    pipe = Pipeline(Path(a.data_dir), sources=load_sources(), taxonomy=load_taxonomy(),
                    client=_client(required=False), review=False)
    run, done = pipe.run_enrich(as_of=_iso(a.as_of), thesis_ids=a.thesis or (),
                                refresh=a.refresh, budget=a.budget)
    print(f"run {run.run_id}: enrich {run.status.value} — "
          f"{run.counts.get('theses_enriched', 0)} thesis(es) enriched")
    for tid, what in done:
        print(f"  {tid}: {what}")
    out = write_run_outputs(pipe.store, run.run_id, Path(a.out) if a.out else None)
    print(f"cost ${run.cost_usd if run.cost_usd is not None else 'UNKNOWN'} · outputs: "
          f"{out['dir']}")
    return _EXIT[run.status]


def cmd_market(a: argparse.Namespace) -> int:
    """MARKET CONTEXT ("is it priced?", market.py): where each thesis's counted exposures stand as
    of a date — display only, never read by a research-action rule. $0, no model call (Polygon
    prices and SEC XBRL; needs POLYGON_API_KEY)."""
    from vinci.theme_intelligence.pipeline import Pipeline
    from vinci.theme_intelligence.report import write_run_outputs

    pipe = Pipeline(Path(a.data_dir), sources=load_sources(), taxonomy=load_taxonomy(),
                    client=None, review=False)
    run, done = pipe.run_market(as_of=_iso(a.as_of), thesis_ids=a.thesis or ())
    print(f"run {run.run_id}: market {run.status.value} — "
          f"{run.counts.get('theses_priced', 0)} thesis(es) priced")
    for tid, what in done:
        print(f"  {tid}: {what}")
    out = write_run_outputs(pipe.store, run.run_id, Path(a.out) if a.out else None)
    print(f"outputs: {out['dir']}")
    return _EXIT[run.status]


def cmd_reanalyse(a: argparse.Namespace) -> int:
    """Re-analyse articles already held under the current taxonomy, retiring the theses an
    earlier one merged (Pipeline.run_reanalyse) — paid like an upload."""
    from vinci.theme_intelligence.pipeline import Pipeline
    from vinci.theme_intelligence.report import write_run_outputs

    pipe = Pipeline(Path(a.data_dir), sources=load_sources(), taxonomy=load_taxonomy(),
                    client=_client(required=True), review=not a.no_review)
    from vinci.theme_intelligence.pipeline import ReanalysisIncompleteError

    try:
        run, results = pipe.run_reanalyse(article_ids=a.article, retire=a.retire or (),
                                          reason=a.reason, as_of=_iso(a.as_of), budget=a.budget)
    except ReanalysisIncompleteError as exc:  # something WAS changed: never called a refusal
        print(f"INCOMPLETE: {exc}")
        return 1
    except ValueError as exc:
        print(f"refused: {exc}")
        return 1
    print(f"run {run.run_id}: reanalyse {run.status.value} — "
          f"{run.counts.get('theses_retired', 0)} thesis(es) retired, {len(results)} article(s) "
          f"analysed again")
    for r in results:
        print(f"  {r.article_id}: {r.status}")
        for o in r.outcomes:
            print(f"    {o.thesis_id} v{o.new_version} {o.action.value:12} "
                  f"{'created' if o.created else o.contribution.value} — {o.title[:70]}")
    out = write_run_outputs(pipe.store, run.run_id, Path(a.out) if a.out else None)
    print(f"cost ${run.cost_usd if run.cost_usd is not None else 'UNKNOWN'} · outputs: "
          f"{out['dir']}")
    return _EXIT[run.status]


#: `qa`'s exit when nothing is broken but research is left open — the weekly job warns on it
QA_RESEARCH_OPEN = 3


def cmd_qa(a: argparse.Namespace) -> int:
    from vinci.theme_intelligence.qa import run_qa
    from vinci.theme_intelligence.report import research_verification

    paths = Paths(Path(a.data_dir))
    st = Store(paths.db)
    runs = st.runs()
    if not runs:
        raise SystemExit("no runs recorded yet")
    run = (max(runs, key=lambda r: r.started_at) if a.run in (None, "latest")
           else next((r for r in runs if r.run_id == a.run), None))
    if run is None:
        raise SystemExit(f"no run {a.run}")
    res = run_qa(st, run.run_id)
    for c in res.checks:
        print(f"  [{'PASS' if c.ok else 'OPEN' if c.research else 'FAIL'}] {c.name}: {c.detail}")
    v = research_verification(st, run)
    print(f"QA {run.run_id}: {res.passed}/{len(res.checks)} passed · scan execution "
          f"{run.status.value} · research verification {v['status']} — {v['summary']}")
    # 0: every check passed · 3: nothing broken, research left OPEN (a figure or an argument) —
    # said, never a failure · 1: an integrity check FAILED (the weekly job fails only on this)
    return 1 if not res.ok else QA_RESEARCH_OPEN if res.open_research else 0


def cmd_backup(a: argparse.Namespace) -> int:
    paths = Paths(Path(a.data_dir))
    st = Store(paths.db)
    print(st.backup(paths.backups))
    return 0


def cmd_export(a: argparse.Namespace) -> int:
    st = Store(Paths(Path(a.data_dir)).db)
    counts = st.export_jsonl(Path(a.out))
    print(json.dumps(counts, indent=1))
    return 0


def cmd_import(a: argparse.Namespace) -> int:
    paths = Paths(Path(a.data_dir))
    paths.ensure()
    st = Store.import_jsonl(Path(a.src), paths.db)
    print(f"imported into {paths.db} (schema {st.schema_version()})")
    return 0


def _health_fetcher(paths: Paths) -> PoliteFetcher:
    """The fetcher a manual health check uses (a seam for tests — no other behaviour)."""
    return PoliteFetcher(paths.http_cache)


def _selected(spec: str | None) -> tuple[SourceConfig, ...]:
    sources = load_sources()
    if not spec:
        return sources
    wanted = set(spec.split(","))
    unknown = wanted - {s.id for s in sources}
    if unknown:
        raise SystemExit(f"unknown source id(s): {sorted(unknown)}")
    return tuple(s for s in sources if s.id in wanted)


def cmd_sources(a: argparse.Namespace) -> int:
    """List the channels with their last-known health, or (`--check-health`) CHECK them now:
    bounded, LLM-free, persisted. Exit 0 when the check ran — the report says what is wrong."""
    from vinci.theme_intelligence.health import check_sources, render_text, to_json

    sources = _selected(a.sources)
    paths = Paths(Path(a.data_dir))
    paths.ensure()
    st = Store(paths.db)
    if not a.check_health:
        latest = st.latest_health()
        for s in sources:
            h = latest.get(s.id)
            print(f"{s.id:<20} {s.adapter:<18} {s.reliability:<7} "
                  f"{(h.status.value if h else 'UNKNOWN'):<9} "
                  f"{(h.checked_at.strftime('%Y-%m-%d %H:%M') if h else 'never checked'):<16} "
                  f"{s.entry_url}")
        return 0
    w_to = datetime.now(tz=UTC).date()
    w_from = w_to - timedelta(days=a.days - 1)
    run = check_sources(list(sources), _health_fetcher(paths), st, trigger="manual",
                        window_from=w_from, window_to=w_to, force=a.force)
    if a.json:
        print(json.dumps(to_json(run, list(sources)), indent=1, sort_keys=True, default=str))
    else:
        print(f"source health — window {w_from}..{w_to} (newest-article freshness), "
              f"{len(sources)} channel(s)")
        print(render_text(run, list(sources)))
    return 0


_INBOX_DIRS = {"INGESTED": "processed", "UPGRADED": "processed", "DUPLICATE": "processed",
               "HELD": "held", "REVIEW": "review", "REJECTED": "rejected"}


def _ingest_pipeline(a: argparse.Namespace) -> Any:
    from vinci.theme_intelligence.pipeline import Pipeline

    client = None if a.cache_only else _client(required=False)
    return Pipeline(Path(a.data_dir), sources=load_sources(), taxonomy=load_taxonomy(),
                    client=client, review=not a.no_review)


def _print_ingest(res: Any) -> None:
    print(f"  {res.doc_id}  {res.status:<10} article {res.article_id or '—'}  {res.note[:240]}")
    for i in res.issues[:6]:
        print(f"      flagged: {i[:200]}")
    if len(res.issues) > 6:
        print(f"      … {len(res.issues) - 6} more flagged item(s) on the document record")


def cmd_ingest_file(a: argparse.Namespace) -> int:
    """One manually supplied document through the SHARED pipeline (see ingest.py)."""
    from vinci.theme_intelligence.documents import Declared, DocumentError
    from vinci.theme_intelligence.ingest import ingest_file
    from vinci.theme_intelligence.report import write_run_outputs

    pipe = _ingest_pipeline(a)
    permitted = True if a.llm_permitted else False if a.llm_not_permitted else None
    if a.release:
        rec = pipe.store.document(a.release)
        if rec is None or rec.stored_path is None:
            raise SystemExit(f"no stored document {a.release}")
        path = Path(a.data_dir) / rec.stored_path
        declared = Declared.recorded(rec.source_id, rec.declared)  # as recorded, `via` included
        if permitted is not None:  # the operator's licence statement now overrides the recorded
            declared = replace(declared, llm_permitted=permitted)
    else:
        if not (a.path and a.source):
            raise SystemExit("--path and --source are required (or --release <doc id>)")
        path = Path(a.path)
        declared = Declared(source_id=a.source, url=a.url, title=a.title,
                            authors=tuple(a.author or ()),
                            published=_iso(a.published) if a.published else None,
                            llm_permitted=permitted)
    as_of = _iso(a.as_of) if a.as_of else datetime.now(tz=UTC).date()
    run = pipe.start_run("ingest", as_of=as_of, budget=a.budget)
    try:
        res = ingest_file(pipe, path, declared, as_of=as_of, force_new=a.as_new,
                          same_as=a.same_as, duplicate_of=a.duplicate_of,
                          max_cost=a.max_cost, reread=a.reread)
    except DocumentError as exc:
        pipe.finish_run(RunStatus.FAILED, error=str(exc))
        print(f"refused: {exc}")
        return 1
    except Exception as exc:  # noqa: BLE001 — recorded FAILED, said plainly, never left RUNNING
        pipe.finish_run(RunStatus.FAILED, error=f"{type(exc).__name__}: {exc}\n"
                                                f"{traceback.format_exc()[-1500:]}")
        print(f"failed: {type(exc).__name__}: {exc}")
        return 1
    run = pipe.finish_ingest(RunStatus.SUCCEEDED if res.status in (
        "INGESTED", "UPGRADED", "DUPLICATE", "HELD", "REVIEW") else RunStatus.PARTIAL)
    print(f"run {run.run_id}: ingest {run.status.value} — {path.name}")
    _print_ingest(res)
    out = write_run_outputs(pipe.store, run.run_id, Path(a.out) if a.out else None)
    print(f"cost ${run.cost_usd if run.cost_usd is not None else 'UNKNOWN'} · outputs: "
          f"{out['dir']}")
    return _EXIT[run.status]


def cmd_reask_part(a: argparse.Namespace) -> int:
    """Pay for ONE completeness part again — never the whole document (see ingest.reask_part)."""
    from vinci.theme_intelligence.budget import BudgetExceeded
    from vinci.theme_intelligence.documents import DocumentError
    from vinci.theme_intelligence.ingest import reask_part

    a.no_review = True
    pipe = _ingest_pipeline(a)
    rec = pipe.store.document(a.doc)
    run_as_of = (pipe.store.run(rec.run_id).as_of if rec is not None and rec.run_id
                 and pipe.store.run(rec.run_id) is not None
                 else datetime.now(tz=UTC).date())
    run = pipe.start_run("ingest", as_of=run_as_of)
    try:
        res = reask_part(pipe, a.doc, a.part, max_cost=a.max_cost)
    except (DocumentError, RuntimeError, BudgetExceeded) as exc:
        pipe.finish_run(RunStatus.FAILED, error=str(exc))
        print(f"refused — nothing sent: {exc}")
        return 1
    except Exception as exc:  # noqa: BLE001 — recorded FAILED, said plainly
        pipe.finish_run(RunStatus.FAILED, error=f"{type(exc).__name__}: {exc}\n"
                                                f"{traceback.format_exc()[-1500:]}")
        print(f"failed: {type(exc).__name__}: {exc}")
        return 1
    run = pipe.finish_ingest(RunStatus.SUCCEEDED)
    print(f"run {run.run_id}: re-asked part {res.part} of {res.doc_id} (article "
          f"{res.article_id}, version {res.version_id}) — cost ${res.cost_usd:.4f}")
    print(f"  {res.recovered}")
    print(f"  kept as {res.kept_as} (the paid original is unchanged)")
    for n in res.notes:
        print(f"  {n[:240]}")
    print("  used whenever this version is analysed again (a replay into a rebuilt registry, "
          "or a re-read); the records already analysed are not rewritten")
    return 0


def cmd_ingest_inbox(a: argparse.Namespace) -> int:
    """Every document in the private inbox, as one run. Each file's statements come from a
    `<file>.meta.json` beside it (or --source for all); the file then moves to processed/,
    held/, review/ or rejected/ — never anywhere tracked by git."""
    from vinci.theme_intelligence.documents import SUPPORTED, Declared, DocumentError
    from vinci.theme_intelligence.ingest import declared_from, ingest_file, sidecar
    from vinci.theme_intelligence.report import write_run_outputs

    inbox = Path(a.inbox) if a.inbox else Path(a.data_dir) / "inbox"
    inbox.mkdir(mode=0o700, parents=True, exist_ok=True)
    files = sorted(f for f in inbox.iterdir() if f.is_file()
                   and f.suffix.lower() in (*SUPPORTED, ".docx"))
    if not files:
        print(f"inbox {inbox}: nothing to import")
        return 0
    pipe = _ingest_pipeline(a)
    as_of = _iso(a.as_of) if a.as_of else datetime.now(tz=UTC).date()
    run = pipe.start_run("ingest", as_of=as_of, budget=a.budget)
    failed = 0
    for f in files:
        try:
            declared = declared_from(sidecar(f), a.source)
        except ValueError as exc:  # its sidecar is unreadable or says something invalid
            print(f"  {f.name}: refused — {f.name}.meta.json: {exc} (left in the inbox)")
            failed += 1
            continue
        if declared is None and f.suffix.lower() in SUPPORTED:
            print(f"  {f.name}: skipped — no source stated (add {f.name}.meta.json or --source)")
            continue
        try:
            if declared is None:  # an unsupported format: refused whatever its source
                declared = Declared(source_id="unknown")
            res = ingest_file(pipe, f, declared, as_of=as_of, max_cost=a.max_cost)
        except DocumentError as exc:
            print(f"  {f.name}: refused — {exc}")
            failed += 1
            dest_dir = inbox / "rejected"
        except Exception as exc:  # noqa: BLE001 — not the file's fault: it stays for a retry
            print(f"  {f.name}: failed — {type(exc).__name__}: {exc} (left in the inbox)")
            failed += 1
            continue
        else:
            _print_ingest(res)
            dest_dir = inbox / _INBOX_DIRS.get(res.status, "processed")
        dest_dir.mkdir(mode=0o700, exist_ok=True)
        f.rename(dest_dir / f.name)
        meta = f.with_name(f.name + ".meta.json")
        if meta.exists():
            meta.rename(dest_dir / meta.name)
    run = pipe.finish_ingest(RunStatus.PARTIAL if failed else RunStatus.SUCCEEDED)
    out = write_run_outputs(pipe.store, run.run_id, Path(a.out) if a.out else None)
    print(f"run {run.run_id}: ingest {run.status.value} · {len(files)} file(s) · cost "
          f"${run.cost_usd if run.cost_usd is not None else 'UNKNOWN'} · outputs: {out['dir']}")
    return _EXIT[run.status]


def cmd_state(a: argparse.Namespace) -> int:
    """The ONE registry between this machine and the scheduled run (see state.py)."""
    from vinci.theme_intelligence import state

    data = Path(a.data_dir)
    remote = a.remote or state.sync_state(Paths(data)).get("remote")
    if not remote or "***" in remote:
        raise SystemExit("--remote is required (a git remote path or URL; credentials stay in "
                         "git's own credential helper)")
    try:
        if a.action == "pull":
            res = state.pull(data, remote, a.branch, replay=not a.no_replay, force=a.force,
                             make_pipeline=lambda: _ingest_pipeline(a))
        elif a.action == "push":
            res = state.push(data, remote, a.branch, message=a.message)
        else:
            res = state.status(data, remote, a.branch)
    except state.StateSyncError as exc:
        print(f"state {a.action} refused: {exc}")
        return 1
    print(f"state {res.action} — {res.remote} {res.branch}")
    for line in res.lines:
        print(f"  {line}")
    return 0


def cmd_upload(a: argparse.Namespace) -> int:
    """ONE STEP for a weekly upload (upload.py): a cache-only pull, a read-only preflight
    (identity, licence, cost against the stated --budget), the import within that budget, QA,
    the paid-call ledger reconciled, a fast-forward push. Nothing is paid that --budget does not
    state; a refusal at any step pushes nothing."""
    from vinci.theme_intelligence import state
    from vinci.theme_intelligence.documents import Declared
    from vinci.theme_intelligence.pipeline import Pipeline
    from vinci.theme_intelligence.upload import DONE, UploadError, upload

    data = Path(a.data_dir)
    remote = a.remote or state.sync_state(Paths(data)).get("remote")
    if not remote or "***" in remote:
        raise SystemExit("--remote is required (a git remote path or URL; credentials stay in "
                         "git's own credential helper)")
    declared = Declared(source_id=a.source, url=a.url, title=a.title,
                        authors=tuple(a.author or ()),
                        published=_iso(a.published) if a.published else None,
                        llm_permitted=True if a.llm_permitted else False
                        if a.llm_not_permitted else None)

    def pipeline(client: Any) -> Pipeline:
        return Pipeline(data, sources=load_sources(), taxonomy=load_taxonomy(), client=client,
                        review=True)

    try:
        res = upload(data, remote, Path(a.path), declared, budget=a.budget,
                     as_of=_iso(a.as_of) if a.as_of else datetime.now(tz=UTC).date(),
                     branch=a.branch, same_as=a.same_as, duplicate_of=a.duplicate_of,
                     as_new=a.as_new, dry_run=a.dry_run,
                     make_pipeline=lambda: pipeline(_client(required=False)),
                     make_replay_pipeline=lambda: pipeline(None))  # the replay: cache only
    except UploadError as exc:  # what it did before it stopped, then why it stopped
        for line in exc.lines:
            print(line)
        print(f"upload refused at {exc}")
        return 1
    for line in res.lines:
        print(line)
    print(f"upload: {res.outcome}" + (f" — {res.status}, cost ${res.cost_usd or 0:.4f} of a "
                                      f"${a.budget:,.2f} budget" if res.run_id else ""))
    # 2: pushed, but the document did not end analysed (HELD for budget, REVIEW): said
    return 2 if res.status is not None and res.status not in DONE else 0


def cmd_author(a: argparse.Namespace) -> int:
    """The operator states an analysed article's author(s) (attribution.py) — $0, no model call,
    a run of its own; never names anyone the operator did not state."""
    from vinci.theme_intelligence.attribution import (
        AttributionError,
        retract_author,
        state_authors,
    )
    from vinci.theme_intelligence.pipeline import Pipeline
    from vinci.theme_intelligence.report import write_run_outputs

    pipe = Pipeline(Path(a.data_dir), sources=load_sources(), taxonomy=load_taxonomy(),
                    client=None, review=False)  # the record only: no model client at all
    as_of = _iso(a.as_of) if a.as_of else datetime.now(tz=UTC).date()
    try:
        if a.retract:
            run, art = retract_author(pipe, a.article, a.retract, by=a.by or "",
                                      reason=a.reason or "", as_of=as_of)
        else:
            run, art = state_authors(pipe, a.article, a.name or [], by=a.by or "",
                                     reason=a.reason or "", title=a.title, as_of=as_of)
    except AttributionError as exc:
        print(f"author refused: {exc}")
        return 1
    print(f"run {run.run_id}: {art.article_id} ({clip(art.title or '', 80)}) now credits "
          f"{'; '.join(x.name for x in art.authors) or 'no author (UNKNOWN)'}; cost $0.00")
    out = write_run_outputs(pipe.store, run.run_id, Path(a.out) if a.out else None)
    print(f"outputs: {out['dir']} · push the registry (`state push`) for the weekly run and the "
          f"desk to carry it")
    return _EXIT[run.status]


def cmd_review(a: argparse.Namespace) -> int:
    """A REVIEWER's resolution of card-review findings (resolve.py): list the open findings with
    their keys, dismiss a warning with a name and a reason, or reopen a dismissal. $0, no model
    call; each dismissal or reopening is a run of its own."""
    from vinci.theme_intelligence.pipeline import Pipeline
    from vinci.theme_intelligence.report import write_run_outputs
    from vinci.theme_intelligence.resolve import (
        ResolutionError,
        current_findings,
        finding_state,
        not_dismissible,
        resolve,
    )

    if a.action == "list":
        st = Store(Paths(Path(a.data_dir)).db)
        found = current_findings(st, tuple(a.thesis or ()))
        shown: set[str] = set()
        for x in found:
            tid = x.thesis.thesis_id
            if tid not in shown:
                shown.add(tid)
                print(f"{tid} v{x.version.version} — {clip(x.thesis.title, 90)}")
            lf, f = x.finding, x.finding.finding
            print(f"  {lf.key}  {finding_state(x):<15} [{f.code}] line {lf.sentence_id} — raised "
                  f"by the review of version {f.origin_version} ({f.origin_as_of.isoformat()})")
            print(f"      line: “{clip(lf.text, 200)}”")
            print(f"      said: {clip(f.said, 240)}")
            if x.conflict:
                print("      CONFLICT: dismissed and reopened apart (" + ", ".join(
                    f"{h.action} by {h.reviewer} {h.created_at.date().isoformat()}"
                    for h in x.heads) + ") — read OPEN until a new resolution supersedes both")
            if x.dismissed and x.state is not None:
                print(f"      dismissed by {x.state.reviewer} on "
                      f"{x.state.created_at.date().isoformat()}: {x.state.reason}")
            elif lf.dismissible:
                print(f"      to dismiss: review dismiss --finding {lf.key} --reviewer NAME "
                      f'--reason "…"')
            else:
                print(f"      not dismissible: {not_dismissible(lf)}")
        if a.history:  # every row ever recorded — a finding gone from the card included
            rows = ([r for tid in a.thesis for r in st.review_resolutions(tid)] if a.thesis
                    else st.review_resolutions())
            gone = {s for r in rows for s in r.supersedes}
            for r in rows:
                print(f"  history {r.thesis_id}: {r.created_at.isoformat(timespec='seconds')} "
                      f"{r.action} {r.finding_key} by {r.reviewer} — {r.reason} "
                      f"(version {r.version}, line {r.sentence_id}, run {r.run_id}; "
                      f"{'superseded' if r.resolution_id in gone else 'current'})")
            print(f"{len(rows)} resolution(s) recorded"
                  + (f" for {', '.join(a.thesis)}" if a.thesis else ""))
        n_open = sum(1 for x in found if not x.dismissed)
        print(f"{len(found)} card-review finding(s) on the current versions of {len(shown)} "
              f"thesis(es){'' if a.thesis else ' not archived'}: {n_open} open "
              f"({sum(1 for x in found if x.finding.dismissible and not x.dismissed)} "
              f"dismissible), {len(found) - n_open} dismissed")
        return 0
    if not a.finding or not a.reviewer or not a.reason:
        raise SystemExit(f"review {a.action} needs --finding, --reviewer and --reason")
    pipe = Pipeline(Path(a.data_dir), sources=load_sources(), taxonomy=load_taxonomy(),
                    client=None, review=False)  # the record only: no model client at all
    try:
        run, r = resolve(pipe, a.finding, "dismissed" if a.action == "dismiss" else "reopened",
                         reviewer=a.reviewer, reason=a.reason,
                         as_of=_iso(a.as_of) if a.as_of else datetime.now(tz=UTC).date())
    except ResolutionError as exc:
        print(f"review {a.action} refused: {exc}")
        return 1
    print(f"run {run.run_id}: {r.finding_key} {r.action} by {r.reviewer} — {r.reason} "
          f"({r.thesis_id} v{r.version}, line {r.sentence_id}); cost $0.00")
    out = write_run_outputs(pipe.store, run.run_id, Path(a.out) if a.out else None)
    print(f"outputs: {out['dir']} · push the registry (`state push`) for the weekly run and "
          f"the desk to carry it")
    return _EXIT[run.status]


def cmd_documents(a: argparse.Namespace) -> int:
    st = Store(Paths(Path(a.data_dir)).db)
    for d in st.documents(a.status):
        print(f"{d.doc_id}  {d.status:<9} {d.source_id:<18} {d.fmt:<8} "
              f"{(d.published.isoformat() if d.published else 'undated'):<10} "
              f"article {d.article_id or '—':<15} {d.filename}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m vinci.theme_intelligence")
    p.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init").set_defaults(fn=cmd_init)
    so = sub.add_parser("sources", help="list the channels, or check their health")
    so.add_argument("--check-health", action="store_true",
                    help="check every channel now (bounded, LLM-free) and record the result")
    so.add_argument("--json", action="store_true", help="machine-readable report")
    so.add_argument("--force", action="store_true",
                    help="re-test a channel that refused access less than 24h ago")
    so.add_argument("--sources", help="comma-separated source ids (default: every active "
                                      "channel)")
    so.add_argument("--days", type=int, default=DEFAULT_SCAN_DAYS,
                    help="freshness window ending today")
    so.set_defaults(fn=cmd_sources)

    ar = sub.add_parser("article", help="analyse one article URL (publication-time replay)")
    ar.add_argument("--url", required=True)
    ar.add_argument("--as-of", required=True, help="YYYY-MM-DD; later-dated facts are refused")
    ar.add_argument("--source", help="source id (default: matched on the URL host)")
    ar.add_argument("--publisher", help="publisher name for a URL outside the channels "
                                        "(default: the matched channel's publisher, else UNKNOWN)")
    ar.add_argument("--html", help="use this saved HTML instead of fetching — the MANUAL "
                                   "UPLOAD route for an authorized copy of an article a "
                                   "blocked or degraded channel will not serve")
    ar.add_argument("--published", help="YYYY-MM-DD you VERIFIED, for a page that states no "
                                        "publication date (used only then; labelled "
                                        "operator-verified)")
    ar.add_argument("--fixture", help="use this extraction JSON instead of the LLM")
    ar.add_argument("--budget", type=float, help="USD this run may spend on the model "
                                                 "(default config.BATCH_BUDGET_USD)")
    ar.add_argument("--cache-only", action="store_true", help="never call the LLM")
    ar.add_argument("--no-review", action="store_true", help="skip the pass-2 LLM review")
    ar.add_argument("--out")
    ar.set_defaults(fn=cmd_article)

    sc = sub.add_parser("scan", help="discover and process the publication window")
    sc.add_argument("--days", type=int, default=DEFAULT_SCAN_DAYS)
    sc.add_argument("--from", dest="date_from")
    sc.add_argument("--to", dest="date_to")
    sc.add_argument("--as-of", help="default: the window end")
    sc.add_argument("--sources", help="comma-separated source ids (default: every active "
                                      "channel)")
    sc.add_argument("--max-articles", type=int, default=DEFAULT_MAX_ARTICLES_PER_RUN)
    sc.add_argument("--budget", type=float, help="USD this scan may spend on the model "
                                                 "(default config.SCAN_BUDGET_USD)")
    sc.add_argument("--resume", help="resume an interrupted run id")
    sc.add_argument("--cache-only", action="store_true")
    sc.add_argument("--no-review", action="store_true")
    sc.add_argument("--no-enrich", action="store_true",
                    help="skip the enrichment step at the end of the scan (default: every "
                         "active thesis whose current version has no set is enriched)")
    sc.add_argument("--out")
    sc.set_defaults(fn=cmd_scan)

    ig = sub.add_parser("ingest-file", help="import one manually supplied document "
                                            "(PDF / HTML / Markdown / text)")
    ig.add_argument("--path")
    ig.add_argument("--source", help="the publisher channel id (sources.toml)")
    ig.add_argument("--url", help="the article's original URL, when it has one")
    ig.add_argument("--title")
    ig.add_argument("--author", action="append", type=_author_name, help="repeatable")
    ig.add_argument("--published", help="YYYY-MM-DD — used only when the document states none")
    lic = ig.add_mutually_exclusive_group()
    lic.add_argument("--llm-permitted", action="store_true",
                     help="its licence allows third-party LLM processing (else it is HELD)")
    lic.add_argument("--llm-not-permitted", action="store_true")
    ig.add_argument("--as-of", help="analysis as-of (default: today, UTC)")
    same = ig.add_mutually_exclusive_group()
    same.add_argument("--same-as", help="the article id this document is a version of")
    same.add_argument("--duplicate-of", help="the article id this document merely repeats — "
                                            "recorded, nothing added")
    same.add_argument("--as-new", action="store_true", help="a new article, whatever it resembles")
    ig.add_argument("--release", help="process a HELD / REVIEW document by its id")
    ig.add_argument("--reread", action="store_true",
                    help="the same file, which the current reader reads differently from the "
                         "version held: analyse it as a NEW VERSION of the same article")
    ig.add_argument("--budget", type=float, help="USD this run may spend on the model "
                                                 "(default config.BATCH_BUDGET_USD)")
    ig.add_argument("--max-cost", type=float,
                    help="USD: analyse even when the estimate exceeds the per-document limit "
                         "(default config.DOC_COST_LIMIT_USD)")
    ig.add_argument("--cache-only", action="store_true")
    ig.add_argument("--no-review", action="store_true")
    ig.add_argument("--out")
    ig.set_defaults(fn=cmd_ingest_file)

    rq = sub.add_parser("reask-part", help="pay for ONE completeness part whose answer failed, "
                                           "not the whole document")
    rq.add_argument("--doc", required=True, help="the document id (D-…)")
    rq.add_argument("--part", required=True, help="the part label, e.g. 4")
    rq.add_argument("--max-cost", type=float, required=True,
                    help="USD this one call may cost (bounded before it is sent)")
    rq.set_defaults(fn=cmd_reask_part, cache_only=False)

    ib = sub.add_parser("ingest-inbox", help="import every document in the private inbox")
    ib.add_argument("--inbox", help="default: <data-dir>/inbox")
    ib.add_argument("--source", help="default source for files without a .meta.json")
    ib.add_argument("--max-cost", type=float, help="USD per document (default: the limit)")
    ib.add_argument("--budget", type=float, help="USD for the whole batch "
                                                 "(default config.BATCH_BUDGET_USD)")
    ib.add_argument("--as-of")
    ib.add_argument("--cache-only", action="store_true")
    ib.add_argument("--no-review", action="store_true")
    ib.add_argument("--out")
    ib.set_defaults(fn=cmd_ingest_inbox)

    ss = sub.add_parser("state", help="carry the ONE registry to / from the state branch")
    ss.add_argument("action", choices=("pull", "push", "status"))
    ss.add_argument("--remote", help="git remote path or URL (default: the last one used)")
    ss.add_argument("--branch", default="theme-intelligence-state")
    ss.add_argument("--no-replay", action="store_true",
                    help="pull without re-ingesting the local documents the branch lacks")
    ss.add_argument("--force", action="store_true",
                    help="pull even when local non-document runs would be discarded (backed up)")
    ss.add_argument("--message", help="push: the commit message")
    ss.add_argument("--cache-only", action="store_true", help="replay: never call the LLM")
    ss.add_argument("--no-review", action="store_true")
    ss.set_defaults(fn=cmd_state)

    up = sub.add_parser("upload", help="ONE STEP for a weekly upload: a cache-only pull, a "
                                       "read-only preflight (identity, licence, cost), the "
                                       "import within --budget, QA, the paid-call ledger "
                                       "reconciled, a fast-forward push — nothing paid that "
                                       "--budget does not state")
    up.add_argument("--remote", help="git remote path or URL (default: the last one used)")
    up.add_argument("--branch", default="theme-intelligence-state")
    up.add_argument("--path", required=True)
    up.add_argument("--source", required=True, help="the publisher channel id (sources.toml)")
    up.add_argument("--budget", type=float, required=True,
                    help="USD the import may spend — it must cover the estimate's HIGH end")
    up.add_argument("--url", help="the article's original URL, when it has one")
    up.add_argument("--title")
    up.add_argument("--author", action="append", type=_author_name, help="repeatable")
    up.add_argument("--published", help="YYYY-MM-DD — used only when the document states none")
    ulic = up.add_mutually_exclusive_group()
    ulic.add_argument("--llm-permitted", action="store_true",
                      help="its licence allows third-party LLM processing (else refused)")
    ulic.add_argument("--llm-not-permitted", action="store_true")
    usame = up.add_mutually_exclusive_group()
    usame.add_argument("--same-as", help="the article id this document is a version of")
    usame.add_argument("--duplicate-of", help="the article id this document merely repeats")
    usame.add_argument("--as-new", action="store_true",
                       help="a new article, whatever it resembles")
    up.add_argument("--as-of", help="analysis as-of (default: today, UTC)")
    up.add_argument("--dry-run", action="store_true",
                    help="stop after the preflight: nothing imported, nothing pushed")
    up.set_defaults(fn=cmd_upload)
    au = sub.add_parser("author", help="state an analysed article's author(s) — when its page "
                                       "names none (QA requires one): recorded with who states "
                                       "it and why; $0, never touches a thesis")
    au.add_argument("--article", required=True, help="the article id (A-…)")
    who = au.add_mutually_exclusive_group(required=True)
    who.add_argument("--name", action="append", type=_author_name,
                     help="an author's name to state (repeatable)")
    who.add_argument("--retract", type=_author_name,
                     help="an author the OPERATOR stated, to remove (never one the page names)")
    au.add_argument("--title", help="the role or kind, e.g. 'institution — the page names no "
                                    "individual author'")
    au.add_argument("--by", help="who states it (recorded)")
    au.add_argument("--reason", help="why, in words (recorded)")
    au.add_argument("--as-of", help="YYYY-MM-DD the run is dated (default: today, UTC)")
    au.add_argument("--out", help="where the run's outputs are written")
    au.set_defaults(fn=cmd_author)

    rv = sub.add_parser("review", help="a reviewer's resolution of card-review findings: list "
                                       "them with their keys, dismiss a warning (never a "
                                       "withheld line) with a name and a reason, or reopen one "
                                       "— a dismissal verifies nothing; $0")
    rv.add_argument("action", choices=("list", "dismiss", "reopen"))
    rv.add_argument("--thesis", action="append", help="list: a thesis id (repeatable; default: "
                                                      "every thesis not archived)")
    rv.add_argument("--history", action="store_true",
                    help="list: every resolution recorded, in force or not")
    rv.add_argument("--finding", help="dismiss/reopen: the finding's key (F-…, from `list`)")
    rv.add_argument("--reviewer", help="dismiss/reopen: who decides (recorded)")
    rv.add_argument("--reason", help="dismiss/reopen: why, in words (recorded)")
    rv.add_argument("--as-of", help="YYYY-MM-DD the run is dated (default: today, UTC)")
    rv.add_argument("--out", help="dismiss/reopen: where the run's outputs are written")
    rv.set_defaults(fn=cmd_review)

    dc = sub.add_parser("documents", help="list the manually supplied documents")
    dc.add_argument("--status")
    dc.set_defaults(fn=cmd_documents)

    rp = sub.add_parser("report", help="re-render the weekly dashboard + cards")
    g = rp.add_mutually_exclusive_group()
    g.add_argument("--latest", action="store_true")
    g.add_argument("--week", help="ISO week, e.g. 2026-W41")
    g.add_argument("--run")
    rp.add_argument("--out")
    rp.set_defaults(fn=cmd_report)

    pb = sub.add_parser("publish", help="publish a run's research desk into the main app "
                                        "(frontend/theme-intelligence/) — no model call")
    pb.add_argument("--run", help="run id (default: the latest run)")
    pb.add_argument("--out", default="frontend/theme-intelligence")
    pb.add_argument("--allow-test-data", action="store_true",
                    help="publish a registry holding test-domain articles (a local preview only)")
    pb.add_argument("--check", action="store_true",
                    help="write nothing: say whether the published desk is behind the registry's "
                         "latest run (exit 2 when it is)")
    pb.set_defaults(fn=cmd_publish)

    ra = sub.add_parser("reassess", help="re-grade stored theses under the current rules — "
                                         "stored evidence only, no fetch, no model call ($0)")
    ra.add_argument("--as-of", required=True, help="YYYY-MM-DD the rules are applied as of")
    ra.add_argument("--thesis", action="append", help="a thesis id (repeatable; default: every "
                                                      "thesis not archived)")
    ra.add_argument("--corrections", help="JSON list of ANALYST CORRECTIONS — {thesis_id, "
                                          "sentence_id, text, claim_ids, reason}; each must cite "
                                          "verified claims the thesis links and pass the card "
                                          "checks, or nothing is applied")
    ra.set_defaults(fn=cmd_reassess)

    en = sub.add_parser("enrich", help="propose the listed companies each thesis's own steps "
                                       "imply — external hypotheses, checked against the SEC, "
                                       "never read by a priority rule (one model call per thesis)")
    en.add_argument("--as-of", required=True, help="YYYY-MM-DD the SEC listings are checked as of")
    en.add_argument("--thesis", action="append", help="a thesis id (repeatable; default: every "
                                                      "active thesis not yet enriched)")
    en.add_argument("--refresh", action="store_true",
                    help="run the pass again for a version that already has a set: the "
                         "model's paid answer comes from the cache (set its file aside to "
                         "have the model asked anew) and every name is checked against the "
                         "SEC again as of --as-of")
    en.add_argument("--budget", type=float, help="the run's spending limit in USD")
    en.add_argument("--out", help="where the run's outputs are written")
    en.set_defaults(fn=cmd_enrich)

    mk = sub.add_parser("market", help="is it priced? — where each thesis's exposures stand "
                                       "as of a date (price vs its 200-day average and 52-week "
                                       "high, return vs SPY, P/E vs its own history): display "
                                       "only, never read by a research-action rule; $0")
    mk.add_argument("--as-of", required=True, help="YYYY-MM-DD the prices and filings are read "
                                                   "as of (nothing later is read)")
    mk.add_argument("--thesis", action="append", help="a thesis id (repeatable; default: every "
                                                      "active thesis)")
    mk.add_argument("--out", help="where the run's outputs are written")
    mk.set_defaults(fn=cmd_market)

    rn = sub.add_parser("reanalyse", help="analyse articles already held again under the "
                                          "current taxonomy, retiring the theses an earlier one "
                                          "merged (paid like an upload)")
    rn.add_argument("--article", action="append", required=True,
                    help="an article id to analyse again (repeatable)")
    rn.add_argument("--retire", action="append",
                    help="a thesis id to retire (repeatable) — it must hold evidence from the "
                         "listed articles only")
    rn.add_argument("--reason", required=True, help="why, in words (recorded on each retirement)")
    rn.add_argument("--as-of", required=True, help="YYYY-MM-DD the analysis is as of")
    rn.add_argument("--budget", type=float, help="the run's spending limit in USD")
    rn.add_argument("--no-review", action="store_true")
    rn.add_argument("--out", help="where the run's outputs are written")
    rn.set_defaults(fn=cmd_reanalyse)

    qa = sub.add_parser("qa", help="re-check a run's stored records")
    qa.add_argument("--run", default="latest")
    qa.set_defaults(fn=cmd_qa)

    sub.add_parser("backup").set_defaults(fn=cmd_backup)
    ex = sub.add_parser("export-state")
    ex.add_argument("--out", required=True)
    ex.set_defaults(fn=cmd_export)
    im = sub.add_parser("import-state")
    im.add_argument("--src", required=True)
    im.set_defaults(fn=cmd_import)

    a = p.parse_args(argv)
    rc: int = a.fn(a)
    return rc


if __name__ == "__main__":
    sys.exit(main())
