"""Weekly decision dashboard + per-thesis card files — rendered ONLY from persisted records.

Nothing here composes analysis: every row and every card is read back from the registry (the
immutable `ThesisVersion` content, its contributions, events and verification issues), so a
re-render of an old run reproduces what that run recorded.

DASHBOARD SHAPE (decision-first, not article-by-article):
- top: run status, scan window, and the KPI strip in plain words — accessible sources ("6 of 8"),
  blocked sources BY NAME, articles analysed (full vs partial), Research Now / Watch / Skip, and
  new / upgraded / downgraded / challenged theses — then unresolved caveats;
- then SIX categories in a fixed order — new, upgraded, downgraded, challenged, unchanged but
  material, archived. Every category is always printed with its count, so a downgrade can never
  disappear under upgrades; a category longer than the display collapse prints "showing X of Y"
  and keeps the rest one click below (expanded in print);
- one row per THESIS (several articles on one theme this week = one row with several sources),
  in plain language: the article date and the date the registry first detected the thesis are
  shown apart ("new to the registry" never means "new to the market"); engine codes, thesis ids,
  change classes, claim ids and the rule trace sit behind the audit toggle (print shows all);
- a searchable archive of every thesis, whatever its status.

A run that FAILED or is PARTIAL says so in a banner above everything else — a broken week never
reads as a quiet one.
"""

from __future__ import annotations

import csv
import io
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from vinci.theme_intelligence.cards import (
    _CHANGE_TAG,
    _CSS,
    AUDIT_TOGGLE,
    KIND_LABEL,
    RenderContext,
    clip,
    e,
    render_html,
    render_json,
    render_markdown,
)
from vinci.theme_intelligence.config import DASHBOARD_ROWS_PER_CATEGORY, ENGINE_VERSION, Paths
from vinci.theme_intelligence.schemas import (
    ACTION_RANK,
    ChangeEvent,
    IssueSeverity,
    ResearchAction,
    RetrievalState,
    RunStatus,
    Thesis,
    ThesisKind,
    ThesisStatus,
    ThesisVersion,
    WeeklyCategory,
    WeeklyRun,
)
from vinci.theme_intelligence.store import Store
from vinci.theme_intelligence.verify import card_sentences

#: Issue codes that are retrieval caveats — always listed at the top of the dashboard.
RETRIEVAL_CAVEAT_CODES = frozenset({"RETRIEVAL_BLOCKED", "NO_BODY", "PARTIAL_RETRIEVAL",
                                    "LOOKAHEAD", "DUPLICATE_CONTENT", "RESOLUTION_FAILED"})
#: Open completeness gaps — a figure the article states that no verified claim captured, an
#: argument block nothing accounts for, a completeness pass that did not run. Listed, never hidden.
COMPLETENESS_CAVEAT_CODES = frozenset({"FIGURE_UNCAPTURED", "ARGUMENT_UNACCOUNTED",
                                       "COMPLETENESS_PASS_NOT_RUN"})

#: Research-verification statuses — how much of what a run READ is accounted for. Kept apart from
#: the run's EXECUTION status (RunStatus): a scan can COMPLETE while what it read is not verified.
VERIFICATION_STATUSES = ("FULLY_VERIFIED", "VERIFIED_WITHIN_PREVIEW", "INCOMPLETE",
                         "NOTHING_ANALYSED")


#: run modes whose evidence a weekly SCAN's report takes in — a manual upload or a single
#: article analysed between two scans appears in the next scan's ONE ranked list
MANUAL_MODES = ("ingest", "article")
#: entries listed per intake list before "showing X of Y"
INTAKE_SHOW = 12


def report_runs(store: Store, run: WeeklyRun) -> list[WeeklyRun]:
    """The runs one report covers. A SCAN's report is the week's report: the scan itself plus
    every manual-ingest / single-article run that started after the previous scan began and
    before this one, analysed AS OF a date inside the scan's window (a replay as of July is not
    this week's research), none of them failed or still running. Any other run reports itself."""
    if run.mode != "scan":
        return [run]
    runs = store.runs()
    prev = max((r.started_at for r in runs if r.mode == "scan" and r.started_at < run.started_at),
               default=None)
    manual = sorted((r for r in runs if r.mode in MANUAL_MODES
                     and r.started_at < run.started_at
                     and (prev is None or r.started_at > prev)
                     and (run.window_from is None or r.as_of >= run.window_from)
                     and r.status not in (RunStatus.FAILED, RunStatus.RUNNING)),
                    key=lambda r: r.started_at)
    return [*manual, run]


def source_health_as_of(store: Store, run: WeeklyRun) -> dict[str, Any]:
    """Every configured channel's latest health record written no later than the run finished
    (a scan checks its channels at its start) — a never-checked channel counts UNKNOWN."""
    from vinci.theme_intelligence.config import load_sources
    from vinci.theme_intelligence.health import summary

    until = run.finished_at or datetime.now(tz=UTC)
    return summary(list(store.latest_health(until=until).values()), list(load_sources()))


def research_verification(store: Store, run: WeeklyRun,
                          runs: list[WeeklyRun] | None = None) -> dict[str, Any]:
    """The run's RESEARCH-VERIFICATION status, never folded into its execution status (review of
    PR #703, round 3). Over the completeness ledgers THIS RUN recorded — one per analysed article
    version:
      FULLY_VERIFIED           every stated figure captured or judged immaterial, every argument
                               paragraph accounted for, every completeness pass ran, full text read
      VERIFIED_WITHIN_PREVIEW  as above, but at least one article was read only as a preview —
                               its unread remainder is unread, not verified
      INCOMPLETE               at least one figure or paragraph is OPEN, or a pass did not run
      NOTHING_ANALYSED         the run recorded no ledger
    Every open item is listed with its cause — never truncated. An unverified claim is never
    linked to a thesis (QA checks it), so open material can hold a thesis back, never raise it."""
    runs = runs or [run]
    reps = [x for r in runs for x in store.completeness_for_run(r.run_id)]
    figures = [(r, f) for r in reps for f in r.figures]
    blocks = [(r, b) for r in reps for b in r.blocks]
    open_f = [(r, f) for r, f in figures if f.status == "uncaptured"]
    open_b = [(r, b) for r, b in blocks if b.status == "unreviewed"]
    not_run = sum(1 for r in reps if not r.pass_ran)
    # read only as a preview = the LATEST version of it these runs analysed is PARTIAL — a page
    # whose fuller report was read in the same week was read in full (Citi's ETF page, 2026-10-11)
    by_article: dict[str, list[str]] = {}
    for rep in reps:
        av0 = store.article_version(rep.article_version_id)
        by_article.setdefault(av0.article_id if av0 else rep.article_version_id,
                              []).append(rep.article_version_id)
    partial = 0
    for aid, vids in by_article.items():
        order = [v.version_id for v in store.article_versions(aid)]
        last = store.article_version(max(vids, key=lambda x: order.index(x) if x in order else -1))
        if last is not None and last.retrieval_state is RetrievalState.PARTIAL:
            partial += 1
    unreadable = sum(r.counts.get("articles_blocked", 0) + r.counts.get("articles_no_body", 0)
                     for r in runs)
    causes: dict[str, int] = {}
    for x in [f for _, f in open_f] + [b for _, b in open_b]:
        causes[x.open_cause or "unclassified"] = causes.get(x.open_cause or "unclassified", 0) + 1
    status = ("NOTHING_ANALYSED" if not reps else
              "INCOMPLETE" if open_f or open_b or not_run else
              "VERIFIED_WITHIN_PREVIEW" if partial else "FULLY_VERIFIED")
    # a ledger is per article VERSION: a preview and its fuller version are one article read twice
    n_articles = len({(av.article_id if (av := store.article_version(r.article_version_id))
                       else r.article_version_id) for r in reps})
    read = (f"{n_articles} article(s)" if n_articles == len(reps)
            else f"{n_articles} article(s), {len(reps)} version(s)")
    scope = "this run" if len(runs) == 1 else f"this report's {len(runs)} runs"
    population = (f"over the {read} {scope} analysed: {len(open_f)} of "
                  f"{len(figures)} stated figure(s) and {len(open_b)} of {len(blocks)} argument "
                  f"paragraph(s) open")
    summary = {
        "FULLY_VERIFIED": f"every figure and argument paragraph accounted for, full text read "
                          f"({population})",
        "VERIFIED_WITHIN_PREVIEW": f"everything READ is accounted for, but {partial} article(s) "
                                   f"were read only as a preview — the rest is unread, not "
                                   f"verified ({population})",
        "INCOMPLETE": f"NOT fully verified — {population}"
                      + (f"; {not_run} completeness pass(es) did not run" if not_run else "")
                      + ("; causes: " + ", ".join(f"{k} {v}" for k, v in sorted(causes.items()))
                         if causes else "")
                      + (f"; {partial} article(s) read only as a preview" if partial else "")
                      + ". Open material is never used as evidence, so it can hold a thesis "
                        "back but never raise its research action",
        "NOTHING_ANALYSED": "no article was analysed in this run",
    }[status] + (f"; {unreadable} article(s) unreadable — not analysed" if unreadable else "")
    return {
        "status": status, "summary": summary, "articles": len(reps),
        "figures": len(figures), "figures_open": len(open_f),
        "paragraphs": len(blocks), "paragraphs_open": len(open_b),
        "passes_not_run": not_run, "articles_preview_only": partial,
        "articles_unreadable": unreadable, "open_causes": causes,
        "open_items": [f"{r.article_version_id} {f.block_id} figure {f.figure!r} — "
                       f"{f.open_cause or 'unclassified'}: {f.reason}" for r, f in open_f]
        + [f"{r.article_version_id} {b.block_id} paragraph — {b.open_cause or 'unclassified'}: "
           f"{b.reason}" for r, b in open_b],
    }


def _listed(items: list[str]) -> dict[str, Any]:
    """A list with its population: every entry is kept in the JSON; the page shows the first
    INTAKE_SHOW and says "showing X of Y"."""
    return {"total": len(items), "items": items}


def _doc_line(store: Store, d: Any, as_of: dict[str, date]) -> str:
    original = (store.path.parent / d.stored_path) if d.stored_path else None
    held = ("original held privately on this machine" if original and original.exists()
            else "original NOT on this machine — its text is not re-verifiable here")
    how = ("linked report fetched automatically" if d.declared.get("via")
           else "manual upload")
    return (f"{d.publisher} — “{d.title or 'title UNKNOWN'}” ({d.filename}; {d.fmt}"
            + (f", {d.pages} page(s)" if d.pages else "") + f") — {d.status}, {how}; "
            f"published {d.published.isoformat() if d.published else 'UNKNOWN'}"
            + (f" ({d.published_source})" if d.published else "")
            + f"; uploaded {d.received_at:%Y-%m-%d %H:%M} UTC; analysed as of "
            f"{as_of.get(d.run_id or '', '—')}; {held}"
            + (f"; article {d.article_id}" if d.article_id else "") + f" [{d.doc_id}]")


def research_intake(store: Store, run: WeeklyRun, runs: list[WeeklyRun],
                    health: dict[str, Any]) -> dict[str, Any]:
    """Research Intake / Manual Action — six lists, each with its population:
    automatically analysed, manually imported, partial awaiting a complete document, publishers
    blocked or degraded, known articles needing an upload or a metadata check, and channels
    whose coverage is unknown. Source health, ingestion coverage and research verification stay
    separate statuses; this section is ingestion coverage."""
    from vinci.theme_intelligence.config import load_retired_sources, load_sources

    rids = {r.run_id for r in runs}
    as_of = {r.run_id: r.as_of for r in runs}
    retired = {r.id for r in load_retired_sources()}  # history only: never asked for anything
    docs_all = [d for d in store.documents() if d.source_id not in retired]
    via_doc = {d.article_id: d for d in docs_all if d.article_id}
    auto: list[str] = []
    auto_by: dict[str, int] = {}
    for r in runs:
        if r.mode == "ingest":
            continue
        aids = sorted({c.article_id for c in store.contributions() if c.run_id == r.run_id}
                      | {str(c["ref"]) for c in store.llm_calls(r.run_id)
                         if c.get("purpose") == "extract"})
        for aid in aids:
            a = store.article(aid)
            vs = store.article_versions(aid)
            if a is None:
                continue
            auto_by[a.source_id] = auto_by.get(a.source_id, 0) + 1
            state = vs[-1].retrieval_state.value if vs else "?"
            auto.append(f"{a.publisher} — “{a.title or 'title UNKNOWN'}” — published "
                        f"{a.published_at.date().isoformat() if a.published_at else 'UNKNOWN'};"
                        f" {state}; analysed as of {r.as_of.isoformat()} ({r.mode} run)"
                        + ("; its linked report read too" if aid in via_doc
                           and via_doc[aid].declared.get("via") else "") + f" [{aid}]")
    manual = [_doc_line(store, d, as_of) for d in docs_all if d.run_id in rids]
    # partial articles still awaiting a complete document (registry-wide, latest version)
    upload_issue: dict[str, str] = {}
    for i in store.issues():
        if i.code == "LINKED_REPORT_UPLOAD":
            upload_issue[i.ref_id] = i.detail
    awaiting: list[str] = []
    needs_upload: list[str] = []
    for a in store.articles():
        if a.source_id in retired:
            continue
        vs = [v for v in store.article_versions(a.article_id)
              if v.retrieval_state is not RetrievalState.BLOCKED]
        if not vs or vs[-1].retrieval_state is not RetrievalState.PARTIAL:
            continue
        line = (f"{a.publisher} — “{a.title or 'title UNKNOWN'}” (published "
                f"{a.published_at.date().isoformat() if a.published_at else 'UNKNOWN'}; "
                f"{vs[-1].body_word_count} words read) [{a.article_id}]")
        awaiting.append(line)
        if a.article_id in upload_issue:
            needs_upload.append(f"{line} — {clip(upload_issue[a.article_id], 300)}")
    for row in health.get("attention", []):
        ma = row.get("manual_action")
        if ma and ma.get("kind") == "UPLOAD_REQUIRED":
            needs_upload.append(f"{row['publisher']} (channel {row['status']}) — {ma['action']}"
                                + (f" — known: {'; '.join(ma['affected'][:3])}"
                                   if ma.get("affected") else ""))
    metadata: list[str] = []
    for url, _st, rec in store.candidates("UNDATED"):
        if rec.get("source_id") in retired:
            continue
        metadata.append(f"{rec.get('source_id', '?')} — “{rec.get('title') or url}” — "
                        f"{rec.get('note') or 'the page states no publication date'} ({url})")
    for d in docs_all:
        if d.status == "HELD":
            why = d.history[-1].split(": ", 1)[-1] if d.history else "held"
            kind = ("cost above the per-document limit" if why.startswith("COST:")
                    else "licence not confirmed for third-party LLM processing")
            metadata.append(f"HELD ({kind}) — {_doc_line(store, d, as_of)} — {clip(why, 220)}")
        elif d.status == "REVIEW":
            metadata.append("REVIEW (which article it is, is uncertain) — "
                            + _doc_line(store, d, as_of))
    for i in store.issues():
        if i.code == "PUBLICATION_DATE_DISAGREES" and i.run_id in rids:
            metadata.append(f"date disagreement — {i.ref_id}: {clip(i.detail, 240)}")
    publishers = [f"{r['publisher']}: {r['status']} — {clip(r['reason'], 200)}"
                  for r in health.get("rows", []) if r["status"] in ("DEGRADED", "BLOCKED",
                                                                      "ERROR")]
    gaps = [f"{r['publisher']}: coverage UNKNOWN ({r['status']}) — what it published cannot be "
            f"seen by this system; no new article from it is NOT evidence it published nothing"
            for r in health.get("rows", []) if r["status"] in ("BLOCKED", "ERROR", "UNKNOWN")]
    for sc in run.sources:
        if sc.truncation:
            gaps.append(f"{sc.source_id}: partial discovery — {sc.truncation}")
    if run.counts.get("articles_queued"):
        gaps.append(f"{run.counts['articles_queued']} in-window article(s) queued by the budget "
                    f"cap — discovered, not yet read")
    # per configured publisher: what it actually got — automatic, manual, or nothing
    health_by = {r["source_id"]: r for r in health.get("rows", [])}
    manual_by: dict[str, int] = {}
    for d in docs_all:
        if d.run_id in rids and d.status in ("INGESTED", "UPGRADED"):
            manual_by[d.source_id] = manual_by.get(d.source_id, 0) + 1
    coverage: list[str] = []
    for src in load_sources():
        st = health_by.get(src.id, {}).get("status", "UNKNOWN")
        n_auto, n_man = auto_by.get(src.id, 0), manual_by.get(src.id, 0)
        if src.mode == "manual_first":
            verdict = (f"MANUAL-FIRST — {n_man} supplied document(s) analysed this week"
                       if n_man else "MANUAL-FIRST — nothing supplied this week: its research "
                                     "this week is MISSING, not absent")
        elif st == "HEALTHY":
            verdict = "automated coverage"
        elif st == "DEGRADED":
            verdict = "PARTIAL automated coverage — see source health"
        elif st in ("BLOCKED", "ERROR"):
            verdict = "automated access BLOCKED — coverage UNKNOWN"
        else:
            verdict = "coverage UNKNOWN (not checked)"
        coverage.append(f"{src.publisher} [{src.mode.replace('_', '-')}; access {st}] — "
                        f"{n_auto} article(s) analysed automatically, {n_man} supplied — "
                        f"{verdict}")
    out = {"automatic": _listed(auto), "manual": _listed(manual), "coverage": _listed(coverage),
           "awaiting_documents": _listed(awaiting), "publishers": _listed(publishers),
           "needs_upload": _listed(needs_upload), "needs_metadata": _listed(metadata),
           "coverage_gaps": _listed(gaps),
           "runs": [f"{r.run_id} ({r.mode}, as of {r.as_of.isoformat()}, {r.status.value})"
                    for r in runs]}
    out["line"] = (f"{len(auto)} analysed automatically · {len(manual)} imported manually · "
                   f"{len(awaiting)} partial awaiting a complete document · {len(publishers)} "
                   f"publisher(s) blocked or degraded · {len(needs_upload)} needing an upload · "
                   f"{len(metadata)} needing a metadata or licence check · {len(gaps)} coverage "
                   f"gap(s)")
    return out


def _intake_labels(store: Store, tid: str, rids: set[str]) -> list[str]:
    """How the evidence this report added to a thesis ARRIVED — per contributing article."""
    out: list[str] = []
    docs = store.documents()
    for c in store.contributions(thesis_id=tid):
        if c.run_id not in rids:
            continue
        d = next((x for x in docs if x.article_id == c.article_id and x.run_id == c.run_id
                  and x.status in ("INGESTED", "UPGRADED")), None)
        if d is None:
            label = f"automatic ({c.article_id})"
        elif d.declared.get("via"):
            label = f"linked report fetched automatically ({d.doc_id}, {c.article_id})"
        else:
            label = (f"manual upload ({d.doc_id} “{d.filename}”, uploaded "
                     f"{d.received_at:%Y-%m-%d}, {c.article_id})")
        if label not in out:
            out.append(label)
    return out


CATEGORY_ORDER = (WeeklyCategory.NEW, WeeklyCategory.UPGRADED, WeeklyCategory.DOWNGRADED,
                  WeeklyCategory.CHALLENGED, WeeklyCategory.UNCHANGED_MATERIAL,
                  WeeklyCategory.ARCHIVED)
_CATEGORY_HELP = {
    WeeklyCategory.NEW: "first recorded this run — new to the registry, not necessarily new to "
                        "the market",
    WeeklyCategory.UPGRADED: "research action raised on material evidence",
    WeeklyCategory.DOWNGRADED: "research action lowered — shown in full, never under the upgrades",
    WeeklyCategory.CHALLENGED: "contradictory evidence, a correction or a timing change arrived",
    WeeklyCategory.UNCHANGED_MATERIAL: "material evidence added; research action unchanged",
    WeeklyCategory.ARCHIVED: "moved off the active list (SKIP, or no material evidence for a "
                             "quarter) — still searchable below",
}


# --- the registry as a run left it ----------------------------------------------------------------

AsOf = dict[str, tuple[Thesis, ThesisVersion]]


def theses_as_of_run(store: Store, run: WeeklyRun) -> AsOf:
    """Every thesis AS THAT RUN LEFT IT: the version its end-of-run snapshot recorded and the
    status its events had set by then. Re-rendering an old run therefore reproduces what it
    recorded — never a later version, never a thesis born after it. A run with no snapshot yet
    (still RUNNING) shows the registry as it is now."""
    snaps = store.snapshots(run.run_id)
    vmap = (dict(max(snaps, key=lambda x: x.created_at).thesis_versions) if snaps
            else {t.thesis_id: t.current_version for t in store.theses()})
    end = run.finished_at or datetime.now(tz=UTC)
    out: AsOf = {}
    for t in store.theses():
        ver = vmap.get(t.thesis_id)
        v = store.thesis_version(t.thesis_id, ver) if ver else None
        if v is None:
            continue
        status = v.content.header.status
        for ev in sorted(store.events(thesis_id=t.thesis_id), key=lambda x: x.created_at):
            if ev.created_at > end:
                break
            if ev.event_type == "ARCHIVED":
                status = ThesisStatus.ARCHIVED
            elif ev.event_type == "REACTIVATED":
                status = ThesisStatus.ACTIVE
        out[t.thesis_id] = (t.model_copy(update={
            "current_version": v.version, "status": status,
            "last_material_update": v.content.header.last_material_update}), v)
    return out


# --- per-thesis card context ---------------------------------------------------------------------

def card_context(store: Store, t: Thesis, v: ThesisVersion, *, generated: str,
                 until: datetime | None = None) -> RenderContext:
    """Everything a card needs beyond its frozen content: history up to this version, the
    attribution-only contributions, sentences the verifier withheld, and the status when it moved
    after this version (an archive is a status change, not a new version). With `until`, only what
    the registry held at that moment is shown."""
    history = [x for x in store.thesis_versions(t.thesis_id) if x.version <= v.version]
    started = {r.run_id: r.started_at for r in store.runs()}
    contribs = [c for c in store.contributions(thesis_id=t.thesis_id)
                if until is None or started.get(c.run_id, until) <= until]
    attributions = [(c.article_id, c.contribution.value,
                     f"as of {c.as_of.isoformat()}: repeats evidence already held "
                     f"({len(c.claim_ids)} claim ref(s)) — no new version, priority unchanged")
                    for c in contribs if c.version is None]
    articles = {c.article_id: a for c in contribs if (a := store.article(c.article_id))}
    sents = card_sentences(v.content)
    blocked: dict[str, str] = {}
    for i in store.issues(run_id=v.run_id):
        if i.severity is not IssueSeverity.BLOCK or i.scope != "card_sentence":
            continue
        tid, _, sid = i.ref_id.partition(":")
        if tid != t.thesis_id or sid not in sents:
            continue
        if repr(sents[sid][0][:100]) in i.detail:  # the issue names THIS version's sentence
            blocked[sid] = f"{i.code} — {i.detail}"
    status_note = None
    if t.status is not v.content.header.status:
        ev = _latest_status_event([x for x in store.events(thesis_id=t.thesis_id)
                                   if until is None or x.created_at <= until])
        status_note = (f"Registry status now {t.status.value}"
                       + (f" since {ev.as_of.isoformat()}: {ev.detail}" if ev else ""))
    return RenderContext(history=history, attributions=attributions, blocked=blocked,
                         articles=articles, generated_note=generated, status_note=status_note)


def _latest_status_event(events: list[ChangeEvent]) -> ChangeEvent | None:
    st = [x for x in events if x.event_type in ("ARCHIVED", "REACTIVATED", "REVIEW_NEEDED")]
    return max(st, key=lambda x: x.created_at) if st else None


def write_cards(store: Store, out_dir: Path, *, generated: str, theses: AsOf | None = None,
                until: datetime | None = None) -> dict[str, dict[str, str]]:
    """Every thesis's card — as of a run when `theses` is given, else current — in four forms:
    web HTML (03/04/05/07/09 folded), print HTML (everything open), Markdown and JSON, all from
    the same persisted version."""
    cdir = out_dir / "cards"
    cdir.mkdir(parents=True, exist_ok=True)
    for old in cdir.glob("TH-*"):  # a re-render REPLACES the set — no card left from an earlier
        old.unlink()               # render (e.g. a thesis born after the run being re-rendered)
    out: dict[str, dict[str, str]] = {}
    if theses is None:
        theses = {t.thesis_id: (t, v) for t in store.theses()
                  if (v := store.thesis_version(t.thesis_id, t.current_version)) is not None}
    for t, v in theses.values():
        rc = card_context(store, t, v, generated=generated, until=until)
        files = {
            "html": cdir / f"{t.thesis_id}.html",
            "print": cdir / f"{t.thesis_id}.print.html",
            "md": cdir / f"{t.thesis_id}.md",
            "json": cdir / f"{t.thesis_id}.json",
        }
        files["html"].write_text(render_html(v.content, rc))
        files["print"].write_text(render_html(v.content, rc, print_mode=True))
        files["md"].write_text(render_markdown(v.content, rc))
        files["json"].write_text(json.dumps(render_json(v.content, rc), indent=1,
                                            sort_keys=True, default=str))
        out[t.thesis_id] = {k: str(p.relative_to(out_dir)) for k, p in files.items()}
    return out


# --- the weekly dashboard ---------------------------------------------------------------------

@dataclass
class DashRow:
    category: str
    thesis_id: str
    title: str
    action: str
    previous_action: str | None
    change_reason: str
    evidence_direction: str
    what_changed: list[str]
    sources: list[str]
    named_companies: list[str]
    named_instruments: list[str]
    private_named: list[str]
    other_named: list[str]
    sectors: list[str]
    next_action: str
    last_material_update: str
    status: str
    flags: list[str]
    version: int
    card: str
    kind: str = ThesisKind.INVESTMENT_THESIS.value
    article_date: str | None = None
    #: when this registry ACTUALLY first ingested the thesis (wall clock, UTC)
    first_ingested: str | None = None
    #: the ANALYSIS as-of date of this version — simulated in a historical replay
    analysis_as_of: str | None = None
    sector_exposures: list[str] = field(default_factory=list)
    why_action: str = ""
    rule_trace: list[str] = field(default_factory=list)
    what_changed_audit: list[str] = field(default_factory=list)
    #: how this report's evidence for the thesis arrived (automatic / manual upload / linked)
    intake: list[str] = field(default_factory=list)


@dataclass
class Dashboard:
    run: dict[str, Any]
    banner: str | None
    window: str
    sources: list[dict[str, Any]]
    sources_checked: int
    sources_failed: list[str]
    articles_read: int
    articles_partial: int
    articles_blocked: int
    themes_created: int
    themes_updated: int
    attributions_only: int
    totals_active: dict[str, int]
    archived_total: int
    caveats: list[str]
    categories: dict[str, list[DashRow]]
    no_material_change: list[str]
    archive: list[dict[str, Any]]
    validation: dict[str, int]
    generated: str
    notes: list[str] = field(default_factory=list)
    #: the KPI strip, in the words a reader uses (see `kpis`)
    kpi: dict[str, Any] = field(default_factory=dict)
    #: the RESEARCH-VERIFICATION status (see `research_verification`) — apart from run status
    verification: dict[str, Any] = field(default_factory=dict)
    #: SOURCE HEALTH as of the run (see `health.summary`) — apart from execution and verification
    source_health: dict[str, Any] = field(default_factory=dict)
    #: Research Intake / Manual Action — ingestion coverage, its own status (see research_intake)
    intake: dict[str, Any] = field(default_factory=dict)
    #: the runs this report covers (a scan's report takes in the manual runs since the last scan)
    report_runs: list[str] = field(default_factory=list)


def _sources_line(store: Store, tid: str, rids: set[str]) -> list[str]:
    out: list[str] = []
    for c in store.contributions(thesis_id=tid):
        if c.run_id not in rids:
            continue
        a = store.article(c.article_id)
        if a is None:
            continue
        authors = "; ".join(x.name for x in a.authors) if a.authors else "author UNKNOWN"
        pub = a.published_at.date().isoformat() if a.published_at else "date UNKNOWN"
        what = _CHANGE_TAG.get(c.contribution) or "first record of this thesis"
        out.append(f"{a.publisher} — {authors} — “{a.title or 'title UNKNOWN'}” (article date "
                   f"{pub}) — {what.lower()}")
    return out


def _category(events: list[ChangeEvent], prev_action: ResearchAction | None,
              now_action: ResearchAction) -> WeeklyCategory | None:
    types = {x.event_type for x in events}
    if "ARCHIVED" in types:
        return WeeklyCategory.ARCHIVED
    if "CREATED" in types:
        return WeeklyCategory.NEW
    if prev_action is not None and ACTION_RANK[now_action] < ACTION_RANK[prev_action]:
        return WeeklyCategory.DOWNGRADED
    if "CHALLENGED" in types or "DOWNGRADED" in types:
        return WeeklyCategory.CHALLENGED  # a challenge is never hidden under a net upgrade
    if prev_action is not None and ACTION_RANK[now_action] > ACTION_RANK[prev_action]:
        return WeeklyCategory.UPGRADED
    if types & {"UPDATED", "UPGRADED", "REACTIVATED"}:
        return WeeklyCategory.UNCHANGED_MATERIAL
    return None  # attribution only — no material change this run


def build_dashboard(store: Store, run_id: str, *, cards: dict[str, dict[str, str]],
                    generated: str) -> Dashboard:
    run = store.run(run_id)
    if run is None:
        raise KeyError(f"no run {run_id}")
    asof = theses_as_of_run(store, run)
    runs = report_runs(store, run)
    rids = {r.run_id for r in runs}
    events = [ev for r in runs for ev in store.events(run_id=r.run_id)]
    by_thesis: dict[str, list[ChangeEvent]] = {}
    for ev in events:
        by_thesis.setdefault(ev.thesis_id, []).append(ev)
    cats: dict[str, list[DashRow]] = {c.value: [] for c in CATEGORY_ORDER}
    no_material: list[str] = []
    for tid, evs in by_thesis.items():
        if tid not in asof:
            continue
        t, cur = asof[tid]
        versions = store.thesis_versions(tid)
        this_run = [v for v in versions if v.run_id in rids]
        before = [v for v in versions if v.run_id not in rids
                  and (not this_run or v.version < min(x.version for x in this_run))]
        prev_action = before[-1].priority.research_action if before else None
        if "CREATED" in {x.event_type for x in evs}:
            prev_action = None
        now_action = cur.priority.research_action
        cat = _category(evs, prev_action, now_action)
        if cat is None:
            no_material.append(f"{tid} {t.title} — attribution only ("
                               + ", ".join(sorted({x.event_type for x in evs})) + ")")
            continue
        changed: list[str] = []
        audit: list[str] = []
        for v in this_run:
            for it in v.content.s02_what_changed.items:
                tag = _CHANGE_TAG.get(it.change_class, it.change_class.value)
                line = (f"{tag}: " if tag else "") + _plain(it.text)
                if line not in changed:
                    changed.append(line)
                full = (f"[{it.change_class.value}] {it.text}"
                        + (f" [{', '.join(it.claim_ids)}]" if it.claim_ids else ""))
                if full not in audit:
                    audit.append(full)
        for x in evs:
            if x.event_type in ("ARCHIVED", "REACTIVATED", "REVIEW_NEEDED"):
                changed.append(f"{x.event_type.replace('_', ' ').capitalize()}: {x.detail}")
        av = cur.content.s05_affected
        flags = sorted({x.event_type for x in evs} - {"CREATED", "UPDATED"})
        if t.status is ThesisStatus.REVIEW_NEEDED:
            flags.append("REVIEW_NEEDED")
        hdr = cur.content.header
        row = DashRow(
            category=cat.value, thesis_id=tid, title=t.title, action=now_action.value,
            previous_action=prev_action.value if prev_action else None,
            change_reason=cur.priority.change_reason,
            evidence_direction=cur.evidence_direction.value, what_changed=changed,
            sources=_sources_line(store, tid, rids), intake=_intake_labels(store, tid, rids),
            named_companies=[c.name_as_written + (" (" + "/".join(x.ticker for x in c.listings)
                                                  + ")" if c.listings else
                                                  f" ({c.resolution_status.value})")
                             for c in av.companies],
            named_instruments=[c.name_as_written + (
                f" [fund {'/'.join(x.ticker for x in c.listings)}]" if c.listings
                else f" [{c.resolution_status.value.lower()}]") for c in av.instruments],
            private_named=[f"{c.name_as_written} [private company]"
                           for c in av.private_or_unlisted],
            other_named=[f"{c.name_as_written} ["
                         + ("basket — members not named" if c.role.value == "cited_basket"
                            else "not a security") + "]" for c in av.not_securities],
            sectors=list(av.sectors), next_action=cur.content.s08_decision.next_step.text,
            last_material_update=t.last_material_update.isoformat(), status=t.status.value,
            flags=sorted(set(flags)), version=cur.version,
            card=cards.get(tid, {}).get("html", ""), kind=hdr.kind.value,
            article_date=hdr.latest_article_date.isoformat() if hdr.latest_article_date else None,
            first_ingested=f"{t.created_at:%Y-%m-%d %H:%M} UTC",
            analysis_as_of=cur.as_of.isoformat(),
            sector_exposures=[f"{x.name} ({x.direction.value})" for x in av.sector_exposures],
            why_action=why_action(cur.priority.rules_fired),
            rule_trace=list(cur.priority.rules_fired), what_changed_audit=audit)
        cats[cat.value].append(row)
    for rows in cats.values():  # ranked: action first, then the freshest material evidence
        rows.sort(key=lambda r: r.thesis_id)
        rows.sort(key=lambda r: r.last_material_update, reverse=True)
        rows.sort(key=lambda r: -ACTION_RANK[ResearchAction(r.action)])

    totals = {a.value: 0 for a in ResearchAction}
    archive: list[dict[str, Any]] = []
    for t, tv in asof.values():
        if t.status is not ThesisStatus.ARCHIVED:
            totals[tv.priority.research_action.value] += 1
        archive.append({
            "thesis_id": t.thesis_id, "title": t.title,
            "action": tv.priority.research_action.value,
            "evidence_direction": tv.evidence_direction.value, "status": t.status.value,
            "sector": t.sector, "region": t.region, "node": t.key_node,
            "mechanism": t.key_mechanism, "direction": t.key_direction.value,
            "versions": t.current_version, "last_material_update":
                t.last_material_update.isoformat(),
            "card": cards.get(t.thesis_id, {}).get("html", "")})
    archive.sort(key=lambda r: (r["status"] == "ARCHIVED", -ACTION_RANK[ResearchAction(
        r["action"])], r["thesis_id"]))

    caveats: list[str] = []
    issues = [i for r in runs for i in store.issues(run_id=r.run_id)]
    val = {s.value: sum(1 for i in issues if i.severity is s) for s in IssueSeverity}
    for i in issues:
        if i.code in RETRIEVAL_CAVEAT_CODES or i.code in COMPLETENESS_CAVEAT_CODES or (
                i.severity in (IssueSeverity.BLOCK, IssueSeverity.HOLD)
                and i.scope != "card_sentence"):
            caveats.append(f"{i.code} {i.ref_id}: {clip(i.detail, 240)}")
    for sc in run.sources:
        if sc.status in ("BLOCKED", "ERROR", "PARTIAL"):
            caveats.append(f"source {sc.source_id} {sc.status}: "
                           + (clip("; ".join(sc.errors), 240) if sc.errors else "no detail"))

    banner = None
    if run.status in (RunStatus.FAILED, RunStatus.INTERRUPTED, RunStatus.RUNNING):
        banner = (f"THIS RUN DID NOT COMPLETE ({run.status.value}). The rows below are only what "
                  f"was recorded before it stopped — this is NOT a quiet week.")
    elif run.status is RunStatus.PARTIAL:
        banner = ("PARTIAL RUN — at least one source or article could not be processed (see the "
                  "caveats). Absent themes may be unread, not absent.")
    failed = [sc.source_id for sc in run.sources if sc.status in ("BLOCKED", "ERROR")]
    window = (f"{run.window_from.isoformat() if run.window_from else '—'} → "
              f"{run.window_to.isoformat() if run.window_to else '—'} (as of "
              f"{run.as_of.isoformat()}, mode {run.mode})")
    d = Dashboard(
        run=json.loads(run.model_dump_json()), banner=banner, window=window,
        sources=[json.loads(sc.model_dump_json()) for sc in run.sources],
        sources_checked=sum(1 for sc in run.sources if sc.status != "NOT_RUN"),
        sources_failed=failed,
        articles_read=sum(r.counts.get("articles_processed", 0) for r in runs),
        articles_partial=sum(r.counts.get("articles_partial", 0) for r in runs),
        articles_blocked=sum(r.counts.get("articles_blocked", 0)
                             + r.counts.get("articles_no_body", 0) for r in runs),
        themes_created=sum(r.counts.get("theses_created", 0) for r in runs),
        themes_updated=sum(r.counts.get("theses_updated", 0) for r in runs),
        attributions_only=sum(r.counts.get("attributions_only", 0) for r in runs),
        totals_active=totals, archived_total=sum(1 for t, _ in asof.values()
                                                 if t.status is ThesisStatus.ARCHIVED),
        caveats=caveats, categories=cats, no_material_change=no_material, archive=archive,
        validation=val, generated=generated)
    d.report_runs = [r.run_id for r in runs]
    d.source_health = source_health_as_of(store, run)
    d.intake = research_intake(store, run, runs, d.source_health)
    d.kpi = kpis(d, store)
    d.verification = research_verification(store, run, runs)
    return d


def kpis(d: Dashboard, store: Store) -> dict[str, Any]:
    """The KPI strip in plain words — counts that state their population."""
    from vinci.theme_intelligence.config import load_sources

    run = d.run
    manual = run["mode"] != "scan"
    names = {sc.id: sc.publisher for sc in load_sources()}
    automatic = [s for s in d.sources if s["status"] != "MANUAL_FIRST"]
    blocked = [s for s in automatic if s["status"] in ("BLOCKED", "ERROR")]
    accessible = [s for s in automatic if s["status"] in ("OK", "PARTIAL")]
    manual_first = [s for s in d.sources if s["status"] == "MANUAL_FIRST"]
    # Every count below is over the theses THIS RUN created or changed (all sections, the
    # archived included) and its EVENTS: a SKIP is archived at once, so counting active theses
    # could never show one; and a thesis created and challenged in one run sits under NEW, so
    # counting sections hid the challenge (both observed in the 2026-10-10 weekly run).
    rows = [r for rs in d.categories.values() for r in rs]

    def rank(a: str) -> int:
        return ACTION_RANK[ResearchAction(a)]

    return {
        "accessible_sources": None if manual else f"{len(accessible)} of {len(automatic)}",
        "manual_first_sources": None if manual else (
            ", ".join(names.get(s["source_id"], s["source_id"]) for s in manual_first)
            or "none"),
        "blocked_sources": None if manual else (
            ", ".join(names.get(s["source_id"], s["source_id"]) for s in blocked) or "none"),
        "articles_full": d.articles_read - d.articles_partial,
        "articles_partial": d.articles_partial,
        "articles_blocked": d.articles_blocked,
        "queued": run.get("counts", {}).get("articles_queued", 0),
        "theses_this_run": len(rows),
        "research_now": sum(1 for r in rows if r.action == ResearchAction.RESEARCH_NOW.value),
        "watch": sum(1 for r in rows if r.action == ResearchAction.WATCH.value),
        "skip": sum(1 for r in rows if r.action == ResearchAction.SKIP.value),
        "new": sum(1 for r in rows if r.previous_action is None),
        "upgraded": sum(1 for r in rows if r.previous_action is not None
                        and rank(r.action) > rank(r.previous_action)),
        "downgraded": sum(1 for r in rows if r.previous_action is not None
                          and rank(r.action) < rank(r.previous_action)),
        "challenged": sum(1 for r in rows if "CHALLENGED" in r.flags),
        "archived": d.archived_total,
        "figures_uncaptured": run.get("counts", {}).get("figures_uncaptured", 0),
        "figures_in_articles": run.get("counts", {}).get("figures_in_articles", 0),
        "manually_imported": d.intake.get("manual", {}).get("total", 0) if d.intake else 0,
    }


def dates_line(r: DashRow) -> str:
    """Three dates, never conflated: the publisher's, the registry's actual first ingestion (wall
    clock, UTC) and the analysis as-of — which a historical replay sets BEFORE ingestion, so it is
    never called a detection."""
    replay = (r.analysis_as_of is not None and r.first_ingested is not None
              and r.analysis_as_of < r.first_ingested[:10])
    return (f"Published {r.article_date or 'UNKNOWN'} · first ingested by the registry "
            f"{r.first_ingested or 'UNKNOWN'}"
            + (" (new to the registry, not necessarily new to the market)"
               if r.category == WeeklyCategory.NEW.value else "")
            + f" · analysed as of {r.analysis_as_of or 'UNKNOWN'}"
            + (" (a historical replay — a simulated date, not a detection)" if replay else ""))


def why_action(rules: tuple[str, ...] | list[str]) -> str:
    """The deterministic rule that set the action, said plainly (the trace stays in the audit)."""
    if not rules:
        return ""
    r = rules[0]
    m = re.match(r"WATCH \(RESEARCH NOW unmet: (.*)\)$", r)
    if m:
        return "Watch — not yet Research Now: " + m.group(1)
    if r.startswith("NOW "):
        # the inflection route says WHY in the first view: its research question (no ids in it)
        q = re.search(r"research question: (.*?\?)", r)
        if "a near-term fundamental inflection" in r and q:
            return ("Research Now — no dislocation or dated catalyst, but a credible near-term "
                    f"change in a fundamental: {q.group(1)} (an investigation, not a trade)")
        return "Research Now — every condition met (an investigation, not a trade)"
    return re.sub(r"^SKIP-\d+ ", "Skip — ", r)


def _plain(text: str) -> str:
    """A card line for the first view: the system labels inside ⟨…⟩ are dropped (they are kept
    in the audit trail and the card)."""
    return re.sub(r"\s*⟨[^⟩]*⟩\s*", " ", text).strip()


# --- dashboard renderers -----------------------------------------------------------------------

_DASH_CSS = """
.dash h1{font-size:22px;margin:0 0 4px}.banner{background:var(--now-bg);color:var(--now);
padding:10px 12px;border-radius:8px;font-weight:700;margin:0 0 12px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px;margin:12px 0}
.kpi{border:1px solid var(--line);border-radius:8px;padding:8px 10px;background:var(--card)}
.kpi b{display:block;font-size:17px;line-height:1.3}
.kpi small{display:block;color:var(--muted);font-size:11px;margin-top:2px}
.vstat{border:1px solid var(--line);border-left:4px solid var(--watch);border-radius:8px;
padding:8px 12px;margin:0 0 12px}
.sh{border:1px solid var(--line);border-radius:8px;padding:8px 12px;margin:0 0 12px}
.sh ul{margin:6px 0 0;padding-left:18px}.sh li{margin:4px 0}
.sh .pill{margin-right:6px}.sh table{font-size:12px}
.kpi span{display:block;color:var(--muted);
font-size:12px}
.cat{margin:18px 0 6px;font:700 14px/1.3 ui-sans-serif,system-ui;text-transform:uppercase;
letter-spacing:.05em}.cat small{font-weight:400;text-transform:none;letter-spacing:0;
color:var(--muted)}.row{border:1px solid var(--line);border-radius:8px;padding:10px 12px;
margin:6px 0;background:var(--card)}.row h3{margin:2px 0 4px;font-size:16px}
.row ul{margin:4px 0 4px 18px;padding:0}.row li{margin:2px 0}.k{color:var(--muted);font-size:12px;
text-transform:uppercase;letter-spacing:.04em;margin-top:6px}.empty{color:var(--muted);
font-style:italic;margin:4px 0 8px}input.search{width:100%;padding:8px;border:1px solid var(--line);
border-radius:6px;background:var(--card);color:var(--ink);margin:6px 0}
@media print{.row{break-inside:avoid}details{display:block}input.search{display:none}}
"""


def _standing(d: Dashboard) -> list[str]:
    return [s["source_id"] for s in d.sources
            if any("standing access limitation" in w for w in s.get("warnings", []))]


def _failed_label(d: Dashboard) -> str:
    standing = set(_standing(d))
    new = [x for x in d.sources_failed if x not in standing]
    return f"{len(new)} new" + (f" + {len(standing)} standing ({', '.join(sorted(standing))})"
                                if standing else "")


def _row_html(r: DashRow) -> str:
    pill = {"RESEARCH NOW": "now", "WATCH": "watch"}.get(r.action, "skip")
    change = (f"{r.previous_action} → {r.action}" if r.previous_action else f"new → {r.action}")
    shown, rest = r.what_changed[:3], r.what_changed[3:]
    li = "".join(f"<li>{e(x)}</li>" for x in shown) or "<li>—</li>"
    more = (f'<details><summary class="note">show the other {len(rest)} of '
            f'{len(r.what_changed)}</summary><ul>' + "".join(f"<li>{e(x)}</li>" for x in rest)
            + "</ul></details>") if rest else ""
    names = r.named_companies + r.named_instruments + r.private_named
    kind = (f'<span class="pill kind">{e(KIND_LABEL[ThesisKind(r.kind)])}</span>'
            if r.kind == ThesisKind.MARKET_REGIME.value else "")
    audit = (f'<div class="aud"><div class="k">Audit</div><div class="cc">{e(r.thesis_id)} · '
             f'v{r.version}' + (" · " + e(", ".join(r.flags)) if r.flags else "")
             + f'</div><div class="note">{e(change)} — {e(r.change_reason)}</div>'
             + "".join(f'<div class="cc">{e(t)}</div>' for t in r.rule_trace)
             + "".join(f'<div class="note">{e(x)}</div>' for x in r.what_changed_audit)
             + "</div>")
    return (
        f'<div class="row"><div class="meta"><span class="pill {pill}">{e(r.action)}</span>'
        f'<span class="pill dir">Evidence {e(r.evidence_direction)}</span>{kind}</div>'
        f'<h3><a href="{e(r.card)}">{e(r.title)}</a></h3>'
        f'<div class="dates">{e(dates_line(r))}</div>'
        f'<div class="k">What changed</div><ul>{li}</ul>{more}'
        f'<div class="k">Why this action</div><div>{e(r.why_action or change)}</div>'
        f'<div class="k">Exposure the source names</div><div>'
        + e("; ".join([f"sector: {x}" for x in r.sector_exposures] + names)
            or "no company or sector named")
        + '</div><div class="k">Sources (original authors)</div><ul>'
        + ("".join(f"<li>{e(x)}</li>" for x in r.sources) or "<li>—</li>") + "</ul>"
        + (f'<div class="note">How this evidence arrived: {e("; ".join(r.intake))}</div>'
           if r.intake else "")
        + f'<div class="k">Next research step</div><div>{e(r.next_action)}</div>'
        + audit + "</div>")


def render_dashboard_html(d: Dashboard, *, print_mode: bool = False,
                          embedded_cards: list[str] | None = None) -> str:
    run = d.run
    v = d.verification or {}
    parts = [f'<div class="dash"><div class="id">Theme intelligence · weekly decision brief · '
             f'run {e(run["run_id"])} · scan execution {e(run["status"])} · research '
             f'verification {e(v.get("status", "UNKNOWN"))}</div><h1>What to research this week'
             f'</h1><div class="note">Research attention only — no row is a purchase or sale. '
             f'Window {e(d.window)}.</div>']
    if d.banner:
        parts.append(f'<div class="banner">{e(d.banner)}</div>')
    if v.get("status") != "FULLY_VERIFIED":
        parts.append(f'<div class="vstat"><b>Research verification '
                     f'{e(v.get("status", "UNKNOWN"))}</b> (the scan itself '
                     f'{e(run["status"])}) — {e(v.get("summary", "not computed"))}.'
                     + ('<details class="sec"' + (" open" if print_mode else "")
                        + f'><summary>Open items ({len(v["open_items"])})</summary>'
                        + "".join(f'<div class="s note">{e(x)}</div>' for x in v["open_items"])
                        + "</details>" if v.get("open_items") else "") + "</div>")
    k = d.kpi or {}
    kp: list[tuple[str, ...]] = ([("Sources", "single article (manual URL) — no discovery")]
          if k.get("accessible_sources") is None else
          [("Accessible sources", str(k["accessible_sources"]),
            "automatic channels read this run"),
           ("Blocked sources", str(k["blocked_sources"])),
           ("Manual-first sources", str(k.get("manual_first_sources") or "none"),
            "health-checked only — research arrives as uploads")])
    kp += [("Articles analyzed", f"{k.get('articles_full', 0)} full · "
                                 f"{k.get('articles_partial', 0)} partial"
            + (f" · {k['articles_blocked']} unreadable" if k.get("articles_blocked") else "")),
           ("Research Now / Watch / Skip",
            f"{k.get('research_now', 0)} / {k.get('watch', 0)} / {k.get('skip', 0)}",
            f"of the {k.get('theses_this_run', 0)} theses this run created or changed"),
           ("New / upgraded / downgraded / challenged theses",
            f"{k.get('new', 0)} / {k.get('upgraded', 0)} / {k.get('downgraded', 0)} / "
            f"{k.get('challenged', 0)}",
            "this run's events — a thesis new this run can also be challenged in it")]
    if k.get("queued"):
        kp.append(("Queued by the budget cap (not yet read)", str(k["queued"])))
    if k.get("figures_in_articles"):
        kp.append(("Reported figures not yet captured",
                   f"{k.get('figures_uncaptured', 0)} of {k['figures_in_articles']}"))
    if v:
        kp.append(("Research verification", str(v["status"]),
                   f"{v['figures_open']} of {v['figures']} figures · {v['paragraphs_open']} of "
                   f"{v['paragraphs']} paragraphs open — apart from the scan's "
                   f"{run['status']}"))
    parts.append('<div class="kpis">' + "".join(
        f'<div class="kpi"><span>{e(t[0])}</span><b>{e(t[1])}</b>'
        + (f"<small>{e(t[2])}</small>" if len(t) > 2 else "") + "</div>" for t in kp)
        + "</div>")
    parts.append(_health_html(d.source_health, print_mode))
    parts.append(_intake_html(d.intake, print_mode))
    if d.sources:
        parts.append('<details class="sec"' + (" open" if print_mode else "")
                     + '><summary>Source coverage (' + str(len(d.sources)) + ')</summary><table>'
                     "<tr><th>Source</th><th>Status</th><th>Discovered</th><th>In window</th>"
                     "<th>Undated</th><th>New</th><th>Processed</th><th>Queued</th>"
                     "<th>Inaccessible</th><th>Errors / warnings</th></tr>"
                     + "".join(
                         f"<tr><td>{e(s['source_id'])}<div class=note>{e(s['method'])}</div></td>"
                         f"<td>{e(s['status'])}</td><td>{s['discovered']}</td>"
                         f"<td>{s['in_window']}</td><td>{s['undated']}</td><td>{s['new']}</td>"
                         f"<td>{s['processed']}</td><td>{s['queued']}</td>"
                         f"<td>{s['inaccessible']}</td><td>"
                         + e(clip("; ".join(s["errors"] + s["warnings"]), 300) or "—")
                         + (f"<div class=note>{e(s['truncation'])}</div>"
                            if s.get("truncation") else "") + "</td></tr>"
                         for s in d.sources) + "</table></details>")
    if d.caveats:
        parts.append('<details class="sec"' + (" open" if print_mode else "")
                     + f'><summary>Unresolved retrieval / verification caveats '
                       f'({len(d.caveats)})</summary>'
                     + "".join(f'<div class="s note">{e(c)}</div>' for c in d.caveats)
                     + "</details>")
    for cat in CATEGORY_ORDER:
        rows = d.categories.get(cat.value, [])
        n = len(rows)
        shown = rows[:DASHBOARD_ROWS_PER_CATEGORY]
        rest = rows[DASHBOARD_ROWS_PER_CATEGORY:]
        head = (f"showing {len(shown)} of {n}" if rest else f"{n}")
        parts.append(f'<div class="cat">{e(cat.value)} <small>({head}) — '
                     f'{e(_CATEGORY_HELP[cat])}</small></div>')
        if not rows:
            parts.append('<div class="empty">None this run.</div>')
            continue
        parts.extend(_row_html(r) for r in shown)
        if rest:
            parts.append('<details' + (" open" if print_mode else "") + f'><summary>show the '
                         f'other {len(rest)} of {n}</summary>'
                         + "".join(_row_html(r) for r in rest) + "</details>")
    if d.no_material_change:
        parts.append('<details class="sec"' + (" open" if print_mode else "")
                     + f'><summary>No material change this run ({len(d.no_material_change)})'
                       f'</summary>' + "".join(f'<div class="s note">{e(x)}</div>'
                                               for x in d.no_material_change) + "</details>")
    parts.append(f'<div class="cat">Searchable archive <small>({len(d.archive)} theses, every '
                 f'status)</small></div><input class="search" placeholder="filter by id, title, '
                 f'sector, action, status…" oninput="filt(this.value)"><table id="arch"><tr>'
                 f'<th>Thesis</th><th>Action</th><th>Evidence</th><th>Status</th><th>Sector'
                 f'</th><th class="aud">Node / mechanism</th><th>Versions</th>'
                 f'<th>Last material update</th></tr>'
                 + "".join(
                     f'<tr><td><a href="{e(a["card"])}">{e(a["title"])}</a><div class="cc aud">'
                     f'{e(a["thesis_id"])}</div></td><td>{e(a["action"])}</td>'
                     f'<td>{e(a["evidence_direction"])}</td><td>{e(a["status"])}</td>'
                     f'<td>{e(a["sector"])} · {e(a["region"])}</td><td class="cc aud">'
                     f'{e(a["node"])} / {e(a["mechanism"])} / {e(a["direction"])}</td>'
                     f'<td>{a["versions"]}</td>'
                     f'<td>{e(a["last_material_update"])}</td></tr>' for a in d.archive)
                 + "</table>")
    v = d.validation
    parts.append(f'<div class="foot">Verification log this run: {v.get("BLOCK", 0)} blocked · '
                 f'{v.get("HOLD", 0)} held · {v.get("WARN", 0)} warnings · {v.get("INFO", 0)} '
                 f'info (validation_log.json). {e(d.generated)}</div></div>')
    if embedded_cards:
        parts.append('<div style="break-before:page"></div>' + "".join(embedded_cards))
    script = ("<script>function filt(q){q=q.toLowerCase();document.querySelectorAll('#arch tr')"
              ".forEach((r,i)=>{if(i)r.style.display=r.textContent.toLowerCase().includes(q)?'':"
              "'none'})}window.addEventListener('beforeprint',()=>document.querySelectorAll("
              "'details').forEach(d=>d.open=true));</script>")
    return ("<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport "
            "content='width=device-width,initial-scale=1'><title>Theme intelligence weekly"
            "</title><style>" + _CSS + _DASH_CSS + "</style></head><body>" + AUDIT_TOGGLE
            + "<div class=wrap>" + "".join(parts) + "</div>" + script + "</body></html>")


_INTAKE_LISTS = (
    ("coverage", "Coverage by publisher (the configured channels)"),
    ("automatic", "Articles automatically analysed"),
    ("manual", "Articles manually imported"),
    ("awaiting_documents", "Partial articles awaiting a complete document"),
    ("publishers", "Publishers blocked or degraded"),
    ("needs_upload", "Known articles requiring an upload"),
    ("needs_metadata", "Requiring a metadata or licence check"),
    ("coverage_gaps", "Unknown publisher-level coverage gaps"),
)


def _intake_html(it: dict[str, Any], print_mode: bool) -> str:
    """Research Intake / Manual Action — compact: the counts line, then each list on demand
    (print: open), each saying "showing X of Y" when long."""
    if not it:
        return ""
    out = [f'<div class="sh"><div class="k">Research intake / manual action</div><div><b>'
           f'{e(it["line"])}</b> <small class="note">ingestion coverage over '
           f'{len(it.get("runs", []))} run(s) — apart from source health and research '
           f'verification; one ranked list below, whatever the route in</small></div>']
    for key, title in _INTAKE_LISTS:
        lst = it.get(key) or {"total": 0, "items": []}
        items = lst["items"]
        shown = items[:INTAKE_SHOW]
        head = (f"showing {len(shown)} of {lst['total']}" if len(items) > len(shown)
                else str(lst["total"]))
        out.append('<details class="sec"' + (" open" if print_mode and items else "")
                   + f'><summary>{e(title)} ({head})</summary>'
                   + ("".join(f'<div class="s note">{e(x)}</div>' for x in shown)
                      or '<div class="s note">none</div>') + "</details>")
    return "".join(out) + "</div>"


_HEALTH_PILL = {"HEALTHY": "skip", "DEGRADED": "watch", "BLOCKED": "now", "ERROR": "now",
                "UNKNOWN": "dir"}


def _health_html(h: dict[str, Any], print_mode: bool) -> str:
    """The compact block: the counts line, NEW changes prominently, only the channels needing
    attention (reason, action, affected article if known), and every channel on demand. Reasons are
    composed sentences — never a stack trace."""
    if not h:
        return ""
    when = (f"checked {h['checked_at'][:16].replace('T', ' ')} UTC"
            if h.get("checked_at") else "not checked yet")
    out = [f'<div class="sh"><div class="k">Research source health</div><div><b>'
           f'{e(h["line"])}</b> <small class="note">{e(when)} — the health of the publisher '
           f'channels, apart from the scan\'s execution and research verification</small></div>']
    if h.get("new_alerts"):
        out.append('<div class="banner">Source-health changes: ' + " · ".join(
            e(f"{r['publisher']} [{r['alert'].replace('_', ' ').lower()}] — "
              f"{'; '.join(r['changes'])}") for r in h["new_alerts"]) + "</div>")
    if h.get("attention"):
        items = []
        for r in h["attention"]:
            ma = r.get("manual_action")
            items.append(
                f'<li><b>{e(r["publisher"])}</b> <span class="pill '
                f'{_HEALTH_PILL.get(r["status"], "dir")}">{e(r["status"])}</span>'
                + (" <small>(known standing restriction)</small>" if r["expect_blocked"]
                   and r["status"] == "BLOCKED" else "")
                + f'<div class="note">{e(r["reason"])}</div>'
                + (f'<div class="note"><b>{e(ma["kind"].replace("_", " ").title())}</b>: '
                   f'{e(ma["action"])}' + (f" — affected: {e('; '.join(ma['affected'][:2]))}"
                                           if ma["affected"] else "") + "</div>"
                   if ma else f'<div class="note">{e(r["next_action"])}</div>') + "</li>")
        out.append("<ul>" + "".join(items) + "</ul>")
    rows = "".join(
        f"<tr><td>{e(r['publisher'])}</td><td>{e(r['status'])}</td><td>{e(r['freshness'])}"
        f"{(' · newest ' + e(r['newest_article_date'])) if r['newest_article_date'] else ''}</td>"
        f"<td>{e((r['checked_at'] or '—')[:16].replace('T', ' '))}</td>"
        f"<td>{e((r['last_successful_discovery'] or '—')[:10])}</td>"
        f"<td>{e((r['last_successful_extraction'] or '—')[:10])}</td>"
        f"<td>{e(r['last_verified_publication_date'] or '—')}</td>"
        f"<td>{r['discovered']} / {r['in_window']}</td>"
        f"<td>{r['consecutive_failed_checks']}</td>"
        f"<td>{'yes' if r['manual_upload_recommended'] else '—'}</td></tr>"
        for r in h["rows"])
    out.append('<details class="sec"' + (" open" if print_mode else "")
               + f'><summary>All {h["total"]} publishers — last successful checks</summary>'
               "<table><tr><th>Publisher</th><th>Health</th><th>Freshness</th><th>Last checked "
               "(UTC)</th><th>Last discovery OK</th><th>Last full-text OK</th><th>Last verified "
               "publication date</th><th>Discovered / listing-dated in window</th>"
               "<th>Consecutive failed checks</th><th>Manual upload</th></tr>" + rows
               + "</table></details>")
    return "".join(out) + "</div>"


def render_dashboard_md(d: Dashboard) -> str:
    run = d.run
    v = d.verification or {}
    md = [f"# What to research this week — run {run['run_id']}", "",
         "_Research attention only — no row is a purchase or sale._", "",
         f"- Scan execution: {run['status']}",
         f"- Research verification: {v.get('status', 'UNKNOWN')} — "
         f"{v.get('summary', 'not computed')}",
         f"- Window: {d.window}"]
    if d.banner:
        md += ["", f"> **{d.banner}**", ""]
    k = d.kpi or {}
    md += ([("- Sources: single article (manual URL) — no source discovery")]
           if k.get("accessible_sources") is None else
           [f"- Accessible sources: {k['accessible_sources']} (automatic channels)",
            f"- Blocked sources: {k['blocked_sources']}",
            f"- Manual-first sources (health check only; research arrives as uploads): "
            f"{k.get('manual_first_sources') or 'none'}"])
    md += [f"- Articles analyzed: {k.get('articles_full', 0)} full · "
           f"{k.get('articles_partial', 0)} partial"
           + (f" · {k['articles_blocked']} unreadable" if k.get("articles_blocked") else "")
           + (f"; queued by the budget cap, not yet read: {k['queued']}" if k.get("queued")
              else ""),
           f"- Research Now / Watch / Skip: {k.get('research_now', 0)} / {k.get('watch', 0)} / "
           f"{k.get('skip', 0)} — of the {k.get('theses_this_run', 0)} theses this run created "
           f"or changed (archived in the registry: {d.archived_total})",
           f"- New / upgraded / downgraded / challenged theses: {k.get('new', 0)} / "
           f"{k.get('upgraded', 0)} / {k.get('downgraded', 0)} / {k.get('challenged', 0)} — "
           f"this run's events; a thesis new this run can also be challenged in it",
           f"- Reported figures not yet captured: {k.get('figures_uncaptured', 0)} of "
           f"{k.get('figures_in_articles', 0)}", ""]
    h = d.source_health
    if h:
        md += ["## Research source health", "", f"**{h['line']}** — "
               + (f"checked {h['checked_at'][:16].replace('T', ' ')} UTC"
                  if h.get("checked_at") else "not checked yet")
               + "; the channels' health, apart from execution and research verification", ""]
        md += [f"- **Change — {r['publisher']}** [{r['alert']}]: {'; '.join(r['changes'])}"
               for r in h.get("new_alerts", [])]
        for r in h.get("attention", []):
            ma = r.get("manual_action")
            md.append(f"- **{r['publisher']}** — {r['status']}: {r['reason']} → "
                      + (f"{ma['kind']}: {ma['action']}" if ma else r["next_action"]))
        md += ["", "| Publisher | Health | Freshness | Last checked | Last discovery OK | "
               "Last full-text OK | Last verified publication date | Discovered / "
               "listing-dated in window | Consecutive failed | Manual upload |",
               "|---|---|---|---|---|---|---|---|---|---|"]
        md += [f"| {r['publisher']} | {r['status']} | {r['freshness']} | "
               f"{(r['checked_at'] or '—')[:16]} | {(r['last_successful_discovery'] or '—')[:10]}"
               f" | {(r['last_successful_extraction'] or '—')[:10]} | "
               f"{r['last_verified_publication_date'] or '—'} | {r['discovered']} / "
               f"{r['in_window']} | {r['consecutive_failed_checks']} | "
               f"{'yes' if r['manual_upload_recommended'] else '—'} |" for r in h["rows"]]
        md.append("")
    it = d.intake
    if it:
        md += ["## Research intake / manual action", "", f"**{it['line']}** — ingestion coverage "
               f"over {len(it.get('runs', []))} run(s), apart from source health and research "
               f"verification", ""]
        for key, title in _INTAKE_LISTS:
            lst = it.get(key) or {"total": 0, "items": []}
            shown = lst["items"][:INTAKE_SHOW]
            head = (f"showing {len(shown)} of {lst['total']}" if len(shown) < lst["total"]
                    else str(lst["total"]))
            md.append(f"**{title}** ({head})")
            md += [f"- {x}" for x in shown] or ["- none"]
            md.append("")
    if d.sources:
        md += ["## Source coverage", "",
              "| Source | Status | Discovered | In window | Undated | New | Processed | Queued | "
              "Inaccessible | Errors / warnings |", "|---|---|---|---|---|---|---|---|---|---|"]
        for s in d.sources:
            md.append(f"| {s['source_id']} | {s['status']} | {s['discovered']} | {s['in_window']} "
                     f"| {s['undated']} | {s['new']} | {s['processed']} | {s['queued']} | "
                     f"{s['inaccessible']} | "
                     + (clip("; ".join(s["errors"] + s["warnings"]), 300).replace("|", "/")
                        or "—") + (f" ({s['truncation']})" if s.get("truncation") else "")
                     + " |")
        md.append("")
    if v.get("open_items"):
        md += [f"## Research verification — open items ({len(v['open_items'])})", ""] + [
            f"- {x}" for x in v["open_items"]] + [""]
    if d.caveats:
        md += ["## Unresolved caveats", ""] + [f"- {c}" for c in d.caveats] + [""]
    for cat in CATEGORY_ORDER:
        rows = d.categories.get(cat.value, [])
        md += [f"## {cat.value} ({len(rows)}) — {_CATEGORY_HELP[cat]}", ""]
        if not rows:
            md += ["_None this run._", ""]
        for r in rows:
            md += [f"### [{r.action}] {r.title}"
                   + (f" — {KIND_LABEL[ThesisKind(r.kind)]}"
                      if r.kind == ThesisKind.MARKET_REGIME.value else ""),
                   f"- {dates_line(r)}",
                   f"- Evidence direction: {r.evidence_direction}",
                   f"- Why this action: {r.why_action}", "- What changed:"]
            md += [f"  - {x}" for x in r.what_changed] or ["  - —"]
            md += ["- Sources:"] + ([f"  - {s}" for s in r.sources] or ["  - —"])
            if r.intake:
                md.append(f"- How this evidence arrived: {'; '.join(r.intake)}")
            names = ([f"sector: {x}" for x in r.sector_exposures] + r.named_companies
                     + r.named_instruments + r.private_named)
            md += [f"- Exposure the source names: {'; '.join(names) or 'no company or sector'}",
                   f"- Next research step: {r.next_action}",
                   f"- Audit: `{r.thesis_id}` v{r.version}"
                   + (f" · flags {', '.join(r.flags)}" if r.flags else "")
                   + f" · {r.change_reason} · card: {r.card}", ""]
    if d.no_material_change:
        md += ["## No material change this run", ""] + [f"- {x}" for x in d.no_material_change]
        md.append("")
    md += ["## Archive (every thesis)", "",
          "| Thesis | Action | Evidence | Status | Sector | Ver | Last material update |",
          "|---|---|---|---|---|---|---|"]
    for a in d.archive:
        md.append(f"| {a['title']} (`{a['thesis_id']}`) | {a['action']} | "
                 f"{a['evidence_direction']} | {a['status']} | {a['sector']} | {a['versions']} | "
                 f"{a['last_material_update']} |")
    v = d.validation
    md += ["", f"_Verification log: {v.get('BLOCK', 0)} blocked · {v.get('HOLD', 0)} held · "
              f"{v.get('WARN', 0)} warnings · {v.get('INFO', 0)} info. {d.generated}_", ""]
    return "\n".join(md)


def render_dashboard_csv(d: Dashboard) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")  # LF: committed readouts stay diff-able
    w.writerow(["category", "research_action", "previous_action", "thesis_id", "version", "title",
                "kind", "article_date", "first_ingested_utc", "analysis_as_of",
                "evidence_direction", "what_changed",
                "sources", "sector_exposures", "named_companies", "named_instruments",
                "private_named", "other_named", "sectors", "next_action", "why_action",
                "change_reason", "last_material_update", "status", "flags", "card"])
    for cat in CATEGORY_ORDER:
        for r in d.categories.get(cat.value, []):
            w.writerow([r.category, r.action, r.previous_action or "", r.thesis_id, r.version,
                        r.title, r.kind, r.article_date or "", r.first_ingested or "",
                        r.analysis_as_of or "",
                        r.evidence_direction, " | ".join(r.what_changed),
                        " | ".join(r.sources), " | ".join(r.sector_exposures),
                        " | ".join(r.named_companies),
                        " | ".join(r.named_instruments), " | ".join(r.private_named),
                        " | ".join(r.other_named),
                        " | ".join(r.sectors), r.next_action, r.why_action, r.change_reason,
                        r.last_material_update, r.status, " | ".join(r.flags), r.card])
    return buf.getvalue()


# --- one call: everything a run produces ---------------------------------------------------------

def write_run_outputs(store: Store, run_id: str, out_dir: Path | None = None) -> dict[str, Any]:
    run = store.run(run_id)
    if run is None:
        raise KeyError(f"no run {run_id}")
    out = out_dir or Path(run.output_dir or Paths(store.path.parent).runs / run_id)
    out.mkdir(parents=True, exist_ok=True)
    generated = (f"Generated {datetime.now(tz=UTC).strftime('%Y-%m-%d %H:%M UTC')} from the "
                 f"registry ({ENGINE_VERSION}; run {run_id}, extract {run.extract_prompt_version}"
                 f", review {run.review_prompt_version}, model {run.llm_model}).")
    asof = theses_as_of_run(store, run)
    cards = write_cards(store, out, generated=generated, theses=asof, until=run.finished_at)
    d = build_dashboard(store, run_id, cards=cards, generated=generated)
    (out / "dashboard.html").write_text(render_dashboard_html(d))
    delta_ids = [r.thesis_id for rows in d.categories.values() for r in rows]
    embedded = []
    for tid in delta_ids:
        if tid not in asof:
            continue
        t, v = asof[tid]
        body = render_html(v.content, card_context(store, t, v, generated=generated,
                                                   until=run.finished_at), print_mode=True)
        embedded.append(body[body.index("<article"):body.index("</article>") + 10])
    (out / "report_print.html").write_text(render_dashboard_html(d, print_mode=True,
                                                                 embedded_cards=embedded))
    (out / "dashboard.md").write_text(render_dashboard_md(d))
    (out / "dashboard.json").write_text(json.dumps(asdict(d), indent=1, sort_keys=True,
                                                   default=str))
    (out / "dashboard.csv").write_text(render_dashboard_csv(d))
    issues = store.issues(run_id=run_id)
    (out / "validation_log.json").write_text(json.dumps(
        [json.loads(i.model_dump_json()) for i in issues], indent=1, sort_keys=True))
    secs = ((run.finished_at - run.started_at).total_seconds() if run.finished_at else None)
    manifest = {
        "run_id": run.run_id, "mode": run.mode, "status": run.status.value,
        "window_from": run.window_from.isoformat() if run.window_from else None,
        "window_to": run.window_to.isoformat() if run.window_to else None,
        "as_of": run.as_of.isoformat(), "started_at": run.started_at.isoformat(),
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "runtime_seconds": round(secs, 1) if secs is not None else None,
        "fetch_seconds": run.fetch_seconds, "llm_seconds": run.llm_seconds,
        "llm": {"provider": run.llm_provider, "model": run.llm_model,
                "extract_prompt_version": run.extract_prompt_version,
                "review_prompt_version": run.review_prompt_version},
        "parser_version": run.parser_version, "engine_version": run.engine_version,
        "db_schema_version": run.db_schema_version, "counts": run.counts, "tokens": run.tokens,
        "cost_usd": run.cost_usd,
        "cost_note": ("UNKNOWN — a call's model has no price entry" if run.cost_usd is None
                      else "list price; cached calls cost 0"),
        "sources": [json.loads(sc.model_dump_json()) for sc in run.sources],
        "warnings": run.warnings,
        "verification": d.validation,
        "research_verification": dict(d.verification),
        "source_health": {k: d.source_health[k] for k in ("line", "counts", "checked_at",
                                                          "attention", "new_alerts")
                          if k in d.source_health},
        "theses_in_registry": len(d.archive),
        "outputs": sorted(str(p.relative_to(out)) for p in out.rglob("*") if p.is_file()),
        "output_dir": str(out),
        "generated_at": datetime.now(tz=UTC).isoformat(),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True))
    newest = max(store.runs(), key=lambda r: r.started_at).run_id
    if out.parent.name == "runs" and run_id == newest:  # names the NEWEST run, not the last
        (out.parent / "LATEST").write_text(run_id + "\n")  # one re-rendered
    return {"dir": str(out), "cards": cards, "dashboard": d, "manifest": manifest}


def week_of(d: date) -> tuple[date, date]:
    start = date.fromordinal(d.toordinal() - d.weekday())
    return start, date.fromordinal(start.toordinal() + 6)
