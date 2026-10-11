"""CLI — every entry point (manual, scheduled, CI) runs the SAME pipeline.

    python -m vinci.theme_intelligence scan --days 10
    python -m vinci.theme_intelligence scan --from 2026-09-28 --to 2026-10-09
    python -m vinci.theme_intelligence article --url <URL> --as-of 2026-02-09
    python -m vinci.theme_intelligence report --latest | --week 2026-W41 | --run <RUN_ID>
    python -m vinci.theme_intelligence qa --run <RUN_ID|latest>
    python -m vinci.theme_intelligence sources [--check-health [--json] [--force]]
    python -m vinci.theme_intelligence init | backup | export-state --out D | import-state --src D

Exit status: 0 = the run succeeded; 2 = PARTIAL (some source or article could not be processed —
the report says which); 1 = FAILED. A failed or partial run is never presented as a quiet week.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
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
from vinci.theme_intelligence.extract import ToolClient
from vinci.theme_intelligence.fetch import PoliteFetcher
from vinci.theme_intelligence.schemas import RunStatus
from vinci.theme_intelligence.store import Store

_EXIT = {RunStatus.SUCCEEDED: 0, RunStatus.PARTIAL: 2, RunStatus.FAILED: 1,
         RunStatus.RUNNING: 1, RunStatus.INTERRUPTED: 1}


def _client(required: bool) -> ToolClient | None:
    import os

    from vinci.config import load_local_env

    load_local_env()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        if required:
            raise SystemExit("ANTHROPIC_API_KEY is not set — extraction needs the LLM (cached "
                             "article versions still replay without it: pass --cache-only)")
        return None
    from vinci.graph.llm import AnthropicLlmClient

    return AnthropicLlmClient(model=LLM_MODEL, max_tokens=LLM_MAX_TOKENS)


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
    sid = a.source or source_for_url(a.url, sources)
    note = (f"operator-supplied copy — a MANUAL UPLOAD of an authorized document "
            f"({Path(a.html).name})" if a.html else "supplied fixture HTML")
    h = pipe.store.latest_health().get(sid)
    if a.html and h is not None and h.status.value in ("BLOCKED", "DEGRADED"):
        print(f"channel {sid} is {h.status.value} ({h.reason[:100]}) — this upload is analysed "
              f"through the same pipeline; the channel's health is unchanged (one document is "
              f"not proof its coverage is complete)")
    run, res = pipe.run_article(a.url, as_of=_iso(a.as_of), source_id=sid, html=html,
                                fixture=fixture, publisher=a.publisher, html_note=note)
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
                    review=not a.no_review)
    run = pipe.run_scan(window_from=w_from, window_to=w_to, as_of=as_of,
                        max_articles=a.max_articles, resume_run_id=a.resume)
    out = write_run_outputs(pipe.store, run.run_id, Path(a.out) if a.out else None)
    print(f"run {run.run_id}: scan execution {run.status.value} · window {w_from}..{w_to} · "
          f"as-of {as_of}")
    for sc in run.sources:
        print(f"  {sc.source_id:<20} {sc.status:<8} discovered {sc.discovered:>3} · in window "
              f"{sc.in_window:>3} · undated {sc.undated:>3} · new {sc.new:>3} · known "
              f"{sc.already_known:>3} · processed {sc.processed:>3} · queued {sc.queued:>3} · "
              f"out-of-window {sc.skipped_out_of_window:>3} · inaccessible {sc.inaccessible:>3} · "
              f"errors {len(sc.errors):>2}" + (f" — {sc.errors[0][:120]}" if sc.errors else ""))
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
        print(f"  [{'PASS' if c.ok else 'FAIL'}] {c.name}: {c.detail}")
    v = research_verification(st, run)
    print(f"QA {run.run_id}: {res.passed}/{len(res.checks)} passed · scan execution "
          f"{run.status.value} · research verification {v['status']} — {v['summary']}")
    return 0 if res.ok else 1


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
    so.add_argument("--sources", help="comma-separated source ids (default: all eight)")
    so.add_argument("--days", type=int, default=DEFAULT_SCAN_DAYS,
                    help="freshness window ending today")
    so.set_defaults(fn=cmd_sources)

    ar = sub.add_parser("article", help="analyse one article URL (publication-time replay)")
    ar.add_argument("--url", required=True)
    ar.add_argument("--as-of", required=True, help="YYYY-MM-DD; later-dated facts are refused")
    ar.add_argument("--source", help="source id (default: matched on the URL host)")
    ar.add_argument("--publisher", help="publisher name for a URL outside the eight channels "
                                        "(default: the matched channel's publisher, else UNKNOWN)")
    ar.add_argument("--html", help="use this saved HTML instead of fetching — the MANUAL "
                                   "UPLOAD route for an authorized copy of an article a "
                                   "blocked or degraded channel will not serve")
    ar.add_argument("--fixture", help="use this extraction JSON instead of the LLM")
    ar.add_argument("--cache-only", action="store_true", help="never call the LLM")
    ar.add_argument("--no-review", action="store_true", help="skip the pass-2 LLM review")
    ar.add_argument("--out")
    ar.set_defaults(fn=cmd_article)

    sc = sub.add_parser("scan", help="discover and process the publication window")
    sc.add_argument("--days", type=int, default=DEFAULT_SCAN_DAYS)
    sc.add_argument("--from", dest="date_from")
    sc.add_argument("--to", dest="date_to")
    sc.add_argument("--as-of", help="default: the window end")
    sc.add_argument("--sources", help="comma-separated source ids (default: all eight)")
    sc.add_argument("--max-articles", type=int, default=DEFAULT_MAX_ARTICLES_PER_RUN)
    sc.add_argument("--resume", help="resume an interrupted run id")
    sc.add_argument("--cache-only", action="store_true")
    sc.add_argument("--no-review", action="store_true")
    sc.add_argument("--out")
    sc.set_defaults(fn=cmd_scan)

    rp = sub.add_parser("report", help="re-render the weekly dashboard + cards")
    g = rp.add_mutually_exclusive_group()
    g.add_argument("--latest", action="store_true")
    g.add_argument("--week", help="ISO week, e.g. 2026-W41")
    g.add_argument("--run")
    rp.add_argument("--out")
    rp.set_defaults(fn=cmd_report)

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
