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
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from vinci.theme_intelligence.cards import (
    _CHANGE_TAG,
    _CSS,
    _FACT_LABELS,
    AUDIT_TOGGLE,
    KIND_LABEL,
    REVEAL_JS,
    ROBOTS,
    STEP_LABEL,
    CarriedFinding,
    NamedGroup,
    RenderContext,
    ReviewCarry,
    _clean_display,
    _line_name,
    cited_claim_ids,
    distinct_sectors,
    e,
    exposure_instruments,
    exposures_of,
    finding_names,
    foot_html,
    ids_to_audit,
    mechanism_step,
    named_groups,
    plain_entities,
    render_html,
    render_json,
    render_markdown,
    topnav,
    watch_of,
    why_reasons,
)
from vinci.theme_intelligence.cards import _anchor as _card_anchor
from vinci.theme_intelligence.config import (
    ENGINE_VERSION,
    Paths,
    SourceConfig,
    load_taxonomy,
)
from vinci.theme_intelligence.display import clip
from vinci.theme_intelligence.parse import clean_title
from vinci.theme_intelligence.schemas import (
    ACTION_RANK,
    SOURCE_LABELS,
    Article,
    ArticleVersion,
    ChangeEvent,
    Claim,
    DocumentRecord,
    IssueSeverity,
    Provenance,
    ResearchAction,
    RetrievalState,
    RunStatus,
    Thesis,
    ThesisClaimLink,
    ThesisKind,
    ThesisStatus,
    ThesisVersion,
    WeeklyCategory,
    WeeklyRun,
    page_prefix,
)
from vinci.theme_intelligence.store import Store
from vinci.theme_intelligence.verify import card_sentences, number_passes

#: Issue codes that are retrieval caveats — always listed at the top of the dashboard.
RETRIEVAL_CAVEAT_CODES = frozenset({"RETRIEVAL_BLOCKED", "NO_BODY", "PARTIAL_RETRIEVAL",
                                    "LOOKAHEAD", "DUPLICATE_CONTENT", "RESOLUTION_FAILED"})
#: Open completeness gaps — a figure the article states that no verified claim captured, an
#: argument block nothing accounts for, a completeness pass that did not run. Listed, never hidden.
COMPLETENESS_CAVEAT_CODES = frozenset({"FIGURE_UNCAPTURED", "ARGUMENT_UNACCOUNTED",
                                       "COMPLETENESS_PASS_NOT_RUN"})

#: Research-verification statuses — how much of what a run READ is accounted for. Kept apart from
#: the run's EXECUTION status (RunStatus): a scan can COMPLETE while what it read is not verified.
#: the card review's WARNINGS on a line it left printed — shown on that line (pilot 2026-10-12:
#: seven such lines printed with no qualification, two of them conditional opinions labelled
#: MEASURED OBSERVATION)
REVIEW_WARNINGS = frozenset({"REVIEW_PARTIAL", "REVIEW_INFERENCE_UNSUPPORTED"})

VERIFICATION_STATUSES = ("FULLY_VERIFIED", "VERIFIED_WITHIN_PREVIEW", "INCOMPLETE",
                         "NOTHING_ANALYSED")


#: run modes whose evidence a weekly SCAN's report takes in — a manual upload or a single
#: article analysed between two scans appears in the next scan's ONE ranked list
MANUAL_MODES = ("ingest", "article", "reassess", "enrich", "reanalyse", "market")


def _no_discovery(mode: str) -> str:
    return ("none read — a reassessment of stored evidence under the current rules (no fetch, no "
            "model call)" if mode == "reassess" else
            "none read — an enrichment pass over stored theses (the listed companies each one's "
            "steps imply; one model call per thesis, no article read)" if mode == "enrich" else
            "none read — market context for stored theses (prices and filings as of the date; "
            "display only, no model call)" if mode == "market" else
            "none discovered — articles already held, analysed again under the current taxonomy "
            "(re-analysis; their earlier theses retired)" if mode == "reanalyse" else
            "single article (manual URL) — no source discovery")
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
    prev = max((r.started_at for r in runs if r.mode == "scan" and not r.ledger_only
                and r.started_at < run.started_at), default=None)
    manual = sorted((r for r in runs if r.mode in MANUAL_MODES
                     and not r.ledger_only  # carried for its record: its evidence is elsewhere
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
    # an open figure whose claim FAILED the number check but passes TODAY's check: a past failure
    # of a since-corrected rule (J.P. Morgan's "five of the 11", 2026-10-12) — still not evidence
    # (the stored record keeps its failure), told apart from a figure that still fails
    # The failing claim is found by STRUCTURE — same article version and paragraph, quoting the
    # figure, its number check failed — never parsed out of the ledger's reason sentence.
    superseded: dict[int, list[Claim]] = {}
    for rep_f, f in open_f:
        if f.open_cause != "verification_failed":
            continue
        av_f = store.article_version(rep_f.article_version_id)
        got = [x for x in (store.claims_for_article(av_f.article_id) if av_f else [])
               if x.article_version_id == rep_f.article_version_id and x.block_id == f.block_id
               and f.figure in x.quote and x.number_verified is False]
        if got and all(g.span_verified and number_passes(g) for g in got):
            superseded[id(f)] = got
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
    # MECHANISM COVERAGE (coverage.py): a proposition dropped, two merged on distinct evidence,
    # or verified material facts no thesis carries — each an alert for review
    coverage: list[tuple[Any, str]] = []
    for rep in reps:
        if rep.coverage is not None:
            av1 = store.article_version(rep.article_version_id)
            coverage.append((rep, av1.article_id if av1 else rep.article_version_id))
    cov_alerts = [f"{aid}: {a}" for rep, aid in coverage
                  for a in (rep.coverage.alerts if rep.coverage else ())]
    status = ("NOTHING_ANALYSED" if not reps else
              "INCOMPLETE" if open_f or open_b or not_run or cov_alerts else
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
                                   f"were read only in part (a preview, or pages that could not "
                                   f"be read) — the rest is unread, not verified ({population})",
        "INCOMPLETE": f"NOT fully verified — {population}"
                      + (f"; {not_run} completeness pass(es) did not run" if not_run else "")
                      + ("; causes: " + ", ".join(f"{k} {v}" for k, v in sorted(causes.items()))
                         if causes else "")
                      + (f"; {partial} article(s) read only in part (a preview, or pages that "
                         f"could not be read)" if partial else "")
                      + (f"; mechanism coverage: {len(cov_alerts)} alert(s) for review — a "
                         f"proposition dropped or merged on distinct evidence, or verified facts "
                         f"no thesis carries" if cov_alerts else "")
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
        #: the same open items by TITLE and in words, for the review queue (no engine codes)
        "open_items_plain": [
            f"“{_title_of_version(store, r.article_version_id)}” — figure {f.figure!r} not "
            f"captured: {_OPEN_CAUSE.get(f.open_cause or '', 'not accounted for')}"
            for r, f in open_f if id(f) not in superseded] + [
            f"“{_title_of_version(store, r.article_version_id)}” — one argument paragraph not "
            f"accounted for: {_OPEN_CAUSE.get(b.open_cause or '', 'not accounted for')}"
            for r, b in open_b],
        "figures_superseded": len(superseded),
        #: open figures whose claim failed a since-corrected number check (still open, still not
        #: evidence) — history, apart from what still fails
        "superseded_items_plain": [
            f"“{_title_of_version(store, r.article_version_id)}” — figure {f.figure!r}: the claim "
            f"quoting it (“{superseded[id(f)][0].value_text or ''}”) "
            f"failed the number check when the article was read; today's check passes it. The "
            f"stored record keeps the failure, so the figure is not used as evidence until the "
            f"article is applied again"
            for r, f in open_f if id(f) in superseded],
        "coverage_alerts": cov_alerts,
        #: the same alerts by TITLE, for the first view (no engine ids there)
        "coverage_alerts_plain": [
            f"“{_title_of(store, aid)}”: {a}"
            for rep, aid in coverage for a in (rep.coverage.alerts if rep.coverage else ())],
        "coverage": [{"article_id": aid, "article_version_id": rep.article_version_id,
                      **_coverage_detail(store, rep.coverage)}
                     for rep, aid in coverage if rep.coverage is not None],
    }


#: why a figure or paragraph is still open, said plainly (the cause code stays in the audit log)
_OPEN_CAUSE = {
    "capture_not_verified": "the claim meant to capture it could not be verified",
    "verification_failed": "the claim quoting it failed the number check",
    "account_names_no_record": "the review accounted for it without naming a record",
    "pass_not_run": "the completeness pass did not run",
    "unreviewed": "no pass reviewed it",
}


def _title_of_version(store: Store, version_id: str) -> str:
    av = store.article_version(version_id)
    return _title_of(store, av.article_id) if av else version_id


def _title_of(store: Store, article_id: str) -> str:
    a = store.article(article_id)
    return (clean_title(a.title, a.publisher) if a is not None else None) or article_id


def _coverage_detail(store: Store, cov: Any) -> dict[str, Any]:
    """The full mechanism-coverage record of one article version, quotes resolved (on-demand
    tier: every proposition, every uncarried fact, every risk, every unrecorded name)."""
    def q(cid: str) -> str:
        c = store.claim(cid)
        return f"{cid} {c.value_text or ''} — {clip(c.quote, 160)!r}" if c else cid

    return {
        "propositions": [f"{p.fate.upper()} {p.hypothesis_id} “{p.title}” → "
                         f"{p.thesis_id or '—'}" + (f" — {p.detail}" if p.detail else "")
                         for p in cov.propositions],
        "uncarried": [f"{page_prefix(g.page)}{g.status.upper()} — {len(g.claim_ids)} fact(s)"
                      + (f" — {g.reason}" if g.reason else "") + ": "
                      + " · ".join(q(c) for c in g.claim_ids) for g in cov.uncarried],
        "risks": list(cov.risks),
        "unrecorded_names": list(cov.unrecorded_names),
        "source_risks": [
            f"{page_prefix(r.page, sep=' ')}{r.block_id}: “{clip(r.sentence, 200)}” → "
            + (f"carried by: {r.represented_by!r}" if r.represented_by
               else f"EXCLUDED (paragraph judged immaterial: {r.excluded})" if r.excluded
               else f"FLAGGED on {', '.join(r.thesis_ids)}" if r.thesis_ids
               else "ON NO CARD") for r in getattr(cov, "source_risks", ())],
        "reverified": list(getattr(cov, "reverified", ())),
    }


def _listed(items: list[str]) -> dict[str, Any]:
    """A list with its population: every entry is kept in the JSON; the page shows the first
    INTAKE_SHOW and says "showing X of Y"."""
    return {"total": len(items), "items": items}


def _unread_pages(d: Any) -> str:
    """'pages 54–60' / 'page 3' / 'pages 3, 7–9' — the pages whose text could not be read."""
    return _page_runs([q.page for q in d.quarantined])


def _page_runs(pages_in: list[int]) -> str:
    pages = sorted(pages_in)
    runs: list[list[int]] = []
    for p in pages:
        if runs and p == runs[-1][-1] + 1:
            runs[-1].append(p)
        else:
            runs.append([p])
    text = ", ".join(f"{r[0]}–{r[-1]}" if len(r) > 1 else f"{r[0]}" for r in runs)
    return ("pages " if len(pages) > 1 else "page ") + text


_UNREAD_KIND = {"back_matter": "BACK MATTER (likely disclosures)",
                "possibly_material": "POSSIBLY MATERIAL — research text may be missing",
                "unclassified": "UNCLASSIFIED"}


def _unread_kinds(d: Any) -> str:
    """What the READABLE document says the unread pages are, kind by kind, with the basis."""
    by: dict[str, list[Any]] = {}
    for q in d.quarantined:
        by.setdefault(getattr(q, "kind", "unclassified"), []).append(q)
    parts = []
    for kind in ("possibly_material", "unclassified", "back_matter"):
        qs = by.get(kind)
        if qs:
            pages = _page_runs([q.page for q in qs])
            parts.append(f"{pages}: {_UNREAD_KIND[kind]} — {qs[0].basis or 'no basis recorded'}")
    return "; ".join(parts)


def _only_back_matter(d: Any) -> bool:
    return bool(d.quarantined) and all(getattr(q, "kind", "") == "back_matter"
                                       for q in d.quarantined)


def unread_documents(documents: Iterable[DocumentRecord],
                     retired: set[str]) -> dict[str, DocumentRecord]:
    """By article: its supplied document whose pages could not be READ (undecodable glyph output,
    quarantined). A RETIRED channel's documents are left out — its records are history, never
    asked about (U56: the desk kept them, the weekly report did not)."""
    return {d.article_id: d for d in documents
            if d.quarantined and d.article_id and d.source_id not in retired}


def partial_ask(article: Article, versions: Sequence[ArticleVersion], *,
                unread: DocumentRecord | None, source: SourceConfig | None,
                linked_upload: bool, retired: set[str]) -> tuple[str, ArticleVersion] | None:
    """THE partial-awaiting-full rule — what a PARTIAL article asks of the operator — in ONE copy,
    read by the weekly report's intake and the desk's Uploads (U56: two copies in two orders, and
    a preview-only channel's unreadable pages were a visual check on the desk, metadata only in
    the report). With the article's latest unblocked version:

    - None — nothing is asked: a retired channel's article; one whose latest unblocked version is
      not PARTIAL; one whose only unreadable pages are back matter (its analysis text is whole);
      a preview-only channel's preview with no linked report to upload (the operator's decision).
    - "visual" — pages of its supplied document could not be read: a visual / OCR check, never an
      awaited document — on ANY channel, a preview-only one included (that decision is about
      asking for a document; this one was supplied).
    - "full_report" — a complete document is awaited."""
    if article.source_id in retired:
        return None
    vs = [v for v in versions if v.retrieval_state is not RetrievalState.BLOCKED]
    if not vs or vs[-1].retrieval_state is not RetrievalState.PARTIAL:
        return None
    if unread is not None:
        return None if _only_back_matter(unread) else ("visual", vs[-1])
    if source is not None and source.paywalled_posts == "preview_only" and not linked_upload:
        return None
    return "full_report", vs[-1]


def _doc_line(store: Store, d: Any, as_of: dict[str, date]) -> str:
    original = (store.path.parent / d.stored_path) if d.stored_path else None
    held = ("original held privately on this machine" if original and original.exists()
            else "original NOT on this machine — its text is not re-verifiable here")
    how = ("linked report fetched automatically" if d.declared.get("via")
           else "manual upload")
    return (f"{d.publisher} — “{clean_title(d.title, d.publisher) or 'title UNKNOWN'}” "
            f"({d.filename}; {d.fmt}"
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
    from vinci.theme_intelligence.health import affected_shown, asks_only_for_previews

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
            auto.append(f"{a.publisher} — “{clean_title(a.title, a.publisher) or 'title UNKNOWN'}”"
                        f" — published "
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
    # a document whose pages could not be READ is not awaiting another document: those pages need
    # a visual / OCR review (documents.py quarantines undecodable glyph output)
    unread = unread_documents(docs_all, retired)
    active = {s.id: s for s in load_sources()}
    for a in store.articles():
        ask = partial_ask(a, store.article_versions(a.article_id),
                          unread=unread.get(a.article_id), source=active.get(a.source_id),
                          linked_upload=a.article_id in upload_issue, retired=retired)
        if ask is None:
            continue
        kind, latest = ask
        line = (f"{a.publisher} — “{clean_title(a.title, a.publisher) or 'title UNKNOWN'}” "
                f"(published "
                f"{a.published_at.date().isoformat() if a.published_at else 'UNKNOWN'}; "
                f"{latest.body_word_count} words read) [{a.article_id}]")
        if kind == "visual":
            line += (f" — not a missing document: {_unread_pages(unread[a.article_id])} could "
                     f"not be read (undecodable font glyphs) — visual / OCR review")
        awaiting.append(line)
        if a.article_id in upload_issue:
            needs_upload.append(f"{line} — {clip(upload_issue[a.article_id], 300)}")
    for row in health.get("attention", []):
        ma = row.get("manual_action")
        src_r = active.get(str(row.get("source_id")))
        if src_r is not None and asks_only_for_previews(src_r, row):
            continue
        if ma and ma.get("kind") == "UPLOAD_REQUIRED":
            needs_upload.append(f"{row['publisher']} (channel {row['status']}) — {ma['action']}"
                                + (f" — known: {affected_shown(ma, 3)}"
                                   if ma.get("affected") else ""))
    metadata: list[str] = []
    for d in docs_all:
        if d.quarantined:
            metadata.append(
                f"VISUAL / OCR REVIEW — {_doc_line(store, d, as_of)} — {_unread_pages(d)}: "
                f"{sum(q.chars for q in d.quarantined):,} characters of undecodable font glyphs "
                f"left out of the analysis; what those pages say is NOT read. What the readable "
                f"document says they are: {_unread_kinds(d)}")
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
        if i.code in ("PUBLICATION_DATE_DISAGREES", "PUBLICATION_DATE_CONFLICT") \
                and i.run_id in rids:
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
    plain_cov: list[str] = []  # the same, in words, for the report's Sources section
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
        if src.mode == "manual_first":
            plain_cov.append(f"{src.publisher} — by upload (the site refuses automated "
                             f"reading): " + (f"{n_man} supplied this week" if n_man else
                                              "nothing supplied this week — its research this "
                                              "week is missing, not absent"))
        else:
            how = {"HEALTHY": "read automatically", "DEGRADED": "read automatically, in part",
                   "BLOCKED": "automatic reading blocked — what it published is not known",
                   "ERROR": "automatic reading failed — what it published is not known"}.get(
                       st, "not checked — what it published is not known")
            plain_cov.append(f"{src.publisher} — {how}: {n_auto} read this week"
                             + (f", {n_man} supplied" if n_man else ""))
    out = {"automatic": _listed(auto), "manual": _listed(manual), "coverage": _listed(coverage),
           "coverage_plain": _listed(plain_cov),
           "awaiting_documents": _listed(awaiting), "publishers": _listed(publishers),
           "needs_upload": _listed(needs_upload), "needs_metadata": _listed(metadata),
           "coverage_gaps": _listed(gaps),
           "runs": [f"{r.run_id} ({r.mode}, as of {r.as_of.isoformat()}, {r.status.value})"
                    for r in runs]}
    out["line"] = (f"{len(auto)} analysed automatically · {len(manual)} imported manually · "
                   f"{len(awaiting)} partial awaiting a complete document · {len(publishers)} "
                   f"publisher(s) blocked or degraded · {len(needs_upload)} needing an upload · "
                   f"{len(metadata)} needing a metadata, licence or visual check · "
                   f"{len(gaps)} coverage gap(s)")
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


#: the rule a proposition with NO verified material evidence fires — it is never a research
#: opportunity, so the weekly page lists it apart from every category (2026-10-12)
NO_EVIDENCE_RULE = "SKIP-1"
NO_EVIDENCE_HELP = ("no verified material evidence; each kept with its audit record (the "
                    "proposition, why it was skipped, its card)")

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


#: the change events that move a thesis OFF the active list: the archive pass's, and a
#: re-analysis RETIRING the thesis an earlier taxonomy merged (Pipeline.run_reanalyse) — never
#: reactivated, its own `retired` field says why
ARCHIVING = ("ARCHIVED", "RETIRED")


def theses_as_of_run(store: Store, run: WeeklyRun) -> AsOf:
    """Every thesis AS THAT RUN LEFT IT: the version its end-of-run snapshot recorded and the
    status its events had set by then. Re-rendering an old run therefore reproduces what it
    recorded — never a later version, never a thesis born after it, never a retirement that came
    after it (U13). A run with no snapshot yet (still RUNNING) shows the registry as it is now."""
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
        retired = ""
        for ev in sorted(store.events(thesis_id=t.thesis_id), key=lambda x: x.created_at):
            if ev.created_at > end:
                break
            if ev.event_type in ARCHIVING:
                status = ThesisStatus.ARCHIVED
            elif ev.event_type == "REACTIVATED":
                status = ThesisStatus.ACTIVE
            if ev.event_type == "RETIRED":
                retired = t.retired
        out[t.thesis_id] = (t.model_copy(update={
            "current_version": v.version, "status": status, "retired": retired,
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
    vf = _findings(store, t.thesis_id, v, {})
    blocked, flagged, corrected, resolved = vf.blocked, vf.flagged, vf.corrected, vf.resolved
    links = store.links(t.thesis_id)
    groups, unread = _group_read(store, links)
    claims = {i: c for i in cited_claim_ids(v.content) if (c := store.claim(i)) is not None}
    status_note = None
    if t.status is not v.content.header.status:
        ev = _latest_status_event([x for x in store.events(thesis_id=t.thesis_id)
                                   if until is None or x.created_at <= until])
        status_note = (f"Registry status now {t.status.value}"
                       + (f" since {ev.as_of.isoformat()}: {ev.detail}" if ev else ""))
    retrieval_now: dict[str, str] = {}
    for s in v.content.s09_sources:
        vs = store.article_versions(s.article_id) if s.retrieval_state is RetrievalState.FULL \
            else []
        if vs and store.retrieval_corrected(vs[-1].version_id):
            retrieval_now[s.article_id] = (f"{vs[-1].retrieval_state.value} (corrected — recorded "
                                           f"FULL at ingestion; the current reader finds only a "
                                           f"preview)")
    # the latest market context of THIS version (display only), as the registry held it
    market = store.market_context(t.thesis_id, v.version, until=until)
    # the latest enrichment set for this version or an earlier one, as the registry held it
    sets = [x for x in store.enrichments(t.thesis_id) if x.thesis_version <= v.version
            and (until is None or x.created_at <= until)]
    return RenderContext(history=history, attributions=attributions, blocked=blocked,
                         articles=articles, generated_note=generated, status_note=status_note,
                         flagged=flagged, retrieval_now=retrieval_now, corrected=corrected,
                         priority=v.priority, resolved=resolved, claims=claims,
                         roles={lk.claim_id: lk.role.value for lk in links},
                         groups=groups, groups_unread=unread, carry=vf.carry,
                         enrichment=sets[-1] if sets else None,
                         market=market)


def thesis_groups(store: Store, links: list[ThesisClaimLink]) -> tuple[NamedGroup, ...]:
    """Business groups the source names in the paragraphs holding a thesis's verified evidence
    (cards.named_groups) — read from the stored paragraphs, never from a model."""
    return _group_read(store, links)[0]


def groups_unread(store: Store, links: list[ThesisClaimLink]) -> int:
    """How many paragraphs holding a thesis's verified evidence have NO TEXT on this machine — an
    exported registry carries no article text (state.py), so on the weekly runner the business
    groups there cannot be read: a surface then says "not checkable on this machine", never
    "none" (a false negative on every weekly readout before 2026-10-13)."""
    return _group_read(store, links)[1]


def _group_read(store: Store, links: list[ThesisClaimLink]
                ) -> tuple[tuple[NamedGroup, ...], int]:
    claims = list({lk.claim_id: c for lk in links
                   if (c := store.claim(lk.claim_id)) is not None and c.span_verified}.values())
    blocks: dict[tuple[str, str], str] = {}
    for c in claims:
        if (c.article_version_id, c.block_id) not in blocks:
            av = store.article_version(c.article_version_id)
            blocks[(c.article_version_id, c.block_id)] = next(
                (b.text for b in (av.blocks if av else ()) if b.block_id == c.block_id), "")
    return named_groups(claims, blocks), sum(1 for t in blocks.values() if not t.strip())


def line_findings(store: Store, thesis_id: str, v: ThesisVersion
                  ) -> tuple[dict[str, str], dict[str, str], dict[str, str],
                             dict[str, tuple[str, str]]]:
    """(withheld, review-flagged, analyst-corrected) lines of ONE version — sentence id -> what
    the record says — from the issues of the run that wrote it, each naming THIS version's
    sentence; and, for a version written WITHOUT the card review, the earlier open findings read
    onto its lines (`review_carry`). One function, so the card, the weekly overview and the desk
    never disagree."""
    f = _findings(store, thesis_id, v, {})
    return f.blocked, f.flagged, f.corrected, f.resolved


def review_carry(store: Store, thesis_id: str, v: ThesisVersion) -> ReviewCarry:
    """The version's card-review status (see `_findings`)."""
    return _findings(store, thesis_id, v, {}).carry


def review_not_run(store: Store, thesis_id: str, v: ThesisVersion) -> str | None:
    """Why the card review did not run for this version — its run's REVIEW_NOT_RUN for this
    thesis (`--no-review`, the review budget exhausted, or no model client and no cached review);
    None when the review ran."""
    return next((i.detail for i in store.issues(run_id=v.run_id)
                 if i.code == "REVIEW_NOT_RUN" and i.ref_id == thesis_id), None)


@dataclass
class _VersionFindings:
    blocked: dict[str, str]
    flagged: dict[str, str]
    corrected: dict[str, str]
    resolved: dict[str, tuple[str, str]]
    carry: ReviewCarry
    #: every open card-review finding on this version's lines, with where it was made
    open: dict[str, CarriedFinding]


def _findings(store: Store, thesis_id: str, v: ThesisVersion,
              memo: dict[int, _VersionFindings]) -> _VersionFindings:
    """One version's findings. A REVIEWED version shows its own review's findings — a finding a
    successful later review does not raise again is no longer open (and a relabel may resolve
    one: `_resolved_by_relabel`). A version written WITHOUT the card review (REVIEW_NOT_RUN) is
    never read as clean (review of PR #703, 2026-10-13): every open finding of the version before
    it stays open — on the line with the SAME words and the SAME cited evidence as an unresolved
    finding; on a line whose words or evidence changed (the same text elsewhere, or the same
    line id) as NOT RE-REVIEWED; and, when the line is gone, listed as removed, never resolved.
    Nothing is copied or edited: each finding is read from the run that made it, with that
    version and date. The deterministic card checks are each version's own (they always run)."""
    shared = store.derived()  # one render: each version's findings derived once (U41)
    hit = shared.get(("findings", thesis_id, v.version)) if shared is not None else None
    if isinstance(hit, _VersionFindings):
        return hit
    if v.version in memo:
        return memo[v.version]
    sents = card_sentences(v.content)
    blocked: dict[str, str] = {}
    flagged: dict[str, str] = {}
    corrected: dict[str, str] = {}
    codes: dict[str, str] = {}
    own: dict[str, CarriedFinding] = {}
    for i in store.issues(run_id=v.run_id):
        if i.scope != "card_sentence" or (i.severity is not IssueSeverity.BLOCK
                                          and i.code not in REVIEW_WARNINGS
                                          and i.code != "ANALYST_CORRECTION"):
            continue
        tid, _, sid = i.ref_id.partition(":")
        if tid != thesis_id or sid not in sents:
            continue
        if repr(sents[sid][0][:100]) not in i.detail:  # the issue names THIS version's sentence
            continue
        # "<sid>: <the problem / the reason> | '<sentence>'" — the middle part, on the line
        said = i.detail.partition(": ")[2].rpartition(" | ")[0] or i.detail
        if i.severity is IssueSeverity.BLOCK:
            blocked[sid] = f"{i.code} — {i.detail}"
            if i.code.startswith("REVIEW_"):  # the card review withheld it (not a re-run check)
                own[sid] = CarriedFinding(i.code, i.detail, said, True, v.version, v.as_of,
                                          sents[sid][0], False)
        elif i.code == "ANALYST_CORRECTION":
            corrected[sid] = said
        else:
            flagged[sid] = said
            codes[sid] = i.code
            own[sid] = CarriedFinding(i.code, i.detail, said, False, v.version, v.as_of,
                                      sents[sid][0], False)
    reason = review_not_run(store, thesis_id, v)
    carried: dict[str, CarriedFinding] = {}
    removed: list[CarriedFinding] = []
    if reason is not None:
        prev = max((x for x in store.thesis_versions(thesis_id) if x.version < v.version),
                   key=lambda x: x.version, default=None)
        if prev is not None:
            before = _findings(store, thesis_id, prev, memo)
            then = card_sentences(prev.content)
            at = {txt: sid for sid, (txt, _p, _c) in reversed(list(sents.items()))}
            for sid_p, f in before.open.items():
                text_p, _prov, cids_p = then[sid_p]
                here = at.get(text_p) or (sid_p if sid_p in sents else None)
                if here is None or here in carried or here in own:
                    removed.append(f)  # the line is gone (or its place is taken): never resolved
                    continue
                same = sents[here][0] == text_p and tuple(sents[here][2]) == tuple(cids_p)
                carried[here] = CarriedFinding(f.code, f.detail, f.said, f.blocked,
                                               f.origin_version, f.origin_as_of, f.origin_text,
                                               f.changed or not same)
            removed += list(before.carry.removed)
        for sid, f in carried.items():
            if sid in blocked:  # this version's own check withholds the line already
                continue
            if f.blocked and not f.changed:
                blocked[sid] = f"{f.code} — {f.detail}"
            else:
                flagged[sid] = f.said
                codes[sid] = f.code
    resolved = _resolved_by_relabel(store, thesis_id, v, flagged, codes)
    opened = {**{sid: f for sid, f in carried.items() if sid not in resolved}, **own}
    out = _VersionFindings(blocked, flagged, corrected, resolved,
                           ReviewCarry(reason, {k: f for k, f in carried.items()
                                                if k not in resolved}, tuple(removed)), opened)
    memo[v.version] = out
    if shared is not None:  # read only issues and versions: append-only rows (Store.derived)
        shared[("findings", thesis_id, v.version)] = out
    return out


#: a CONTENT objection — something the cited spans do not carry, which no relabel answers. Any one
#: of these anywhere in a finding keeps it open, whatever else it says about the label.
_CONTENT_OBJECTION = re.compile(
    r"not in (?:the |any )?(?:cited |pool )?spans?|not (?:found|stated|shown|supported|reflected|"
    r"in the (?:pool|source|article))|unsupported|no (?:pool )?span|"
    r"does(?:n't| not) (?:say|show|state|support|mention)|support(?:s|ed)? only|only partly|"
    r"only (?:part|partial)|partial(?:ly)? support|overstat|misstat|mix(?:es|ed|ing)? "
    r"(?:scope|period|unit)|wrong (?:figure|number|period|unit|date|company|scope)|incorrect|"
    r"contradict|omit|drops? (?:a |the )?qualifier|missing|absent|unverified", re.I)
#: a clause about the LABEL — what a relabel to SOURCE OPINION answers
_LABEL_TALK = re.compile(r"label|stronger than|conditional|opinion|forecast|projection|inference|"
                         r"not measured|interpretation|speculat", re.I)
#: a clause affirming support — counted only with no negation or hedge in it
_AFFIRM = re.compile(r"\bsupport(?:s|ed)?\b|\bcited observations?\b|\b(?:are|is) cited\b|"
                     r"\bmatch(?:es|ed)?\b|\bconsistent with\b", re.I)
_HEDGE = re.compile(r"\bnot\b|\bno\b|n't\b|\bnever\b|\bonly\b|\bbut\b|\bwithout\b|"
                    r"\blacks?\b|\bhowever\b|\bexcept\b|\bpart(?:ly|ial)?\b", re.I)


def finding_scope(said: str, label: str) -> str:
    """What a card-review finding objects to, read FAIL-SAFE from its own words:
      "label_only"  — every clause is about the label `label` (which the finding names), or affirms
                      support without a hedge: a relabel answers all of it;
      "mixed"       — it names the label AND objects to content the cited spans do not carry;
      "ambiguous"   — it names the label, but some clause is neither about the label nor a plain
                      affirmation;
      "not_label"   — it does not name `label` at all.
    Only "label_only" may be resolved by a relabel; the other three stay open (review of PR #703,
    2026-10-12: a finding naming the label and ALSO saying the cited spans "support only parts" was
    retired whole)."""
    if label.lower() not in said.lower():
        return "not_label"
    if _CONTENT_OBJECTION.search(said):
        return "mixed"
    for clause in re.split(r"(?<=[.;!?])\s+|\s+—\s+", said.strip()):
        if not clause.strip(" .;:—"):
            continue
        if _LABEL_TALK.search(clause) or (_AFFIRM.search(clause) and not _HEDGE.search(clause)):
            continue
        return "ambiguous"
    return "label_only"


def _resolved_by_relabel(store: Store, thesis_id: str, v: ThesisVersion, flagged: dict[str, str],
                         codes: dict[str, str]) -> dict[str, tuple[str, str]]:
    """Review findings a LATER version resolved — moved out of `flagged`, kept as history. One
    case, and only when the record shows it: the review questioned a line's FACT label (its words
    name the label: "Labelled MEASURED OBSERVATION but … conditional") when the line carried it,
    and the line — the same words — now carries SOURCE OPINION, the label that finding asks for.
    FAIL-SAFE: only a finding about the label ALONE is resolved (`finding_scope`); one that also
    objects to content, or that cannot be read as label-only, stays open with its words intact.
    Observed 2026-10-12: Nomura's two conditional risk lines, relabelled by the re-grade, still
    read UNRESOLVED REVIEW."""
    sents = card_sentences(v.content)
    out: dict[str, tuple[str, str]] = {}
    earlier = [x for x in store.thesis_versions(thesis_id) if x.version < v.version]
    for sid in list(flagged):
        text, prov, _ids = sents[sid]
        if codes.get(sid) != "REVIEW_PARTIAL" or prov != Provenance.SOURCE_OPINION.value:
            continue
        for ev in earlier:  # the version the finding was first made on
            then = {t: p for t, p, _c in card_sentences(ev.content).values()}
            if text in then and any(i.scope == "card_sentence" and i.code == "REVIEW_PARTIAL"
                                    and flagged[sid] in i.detail
                                    for i in store.issues(run_id=ev.run_id)):
                if then[text] in {p.value for p in _FACT_LABELS} \
                        and finding_scope(flagged[sid], then[text]) == "label_only":
                    out[sid] = (f"an earlier review (v{ev.version}) questioned its {then[text]} "
                                f"label; this version labels it SOURCE OPINION",
                                flagged.pop(sid))
                break
    return out


def _latest_status_event(events: list[ChangeEvent]) -> ChangeEvent | None:
    st = [x for x in events if x.event_type in (*ARCHIVING, "REACTIVATED", "REVIEW_NEEDED")]
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
    #: RETIRED by a re-analysis (its articles analysed again): history, never a live decision
    retired: bool = False
    article_date: str | None = None
    #: when this registry ACTUALLY first ingested the thesis (wall clock, UTC)
    first_ingested: str | None = None
    #: the ANALYSIS as-of date of this version — simulated in a historical replay
    analysis_as_of: str | None = None
    sector_exposures: list[str] = field(default_factory=list)
    why_action: str = ""
    #: a WATCH's "needs data" / "on hold" (priority.watch_label); "" otherwise
    watch: str = ""
    rule_trace: list[str] = field(default_factory=list)
    what_changed_audit: list[str] = field(default_factory=list)
    #: how this report's evidence for the thesis arrived (automatic / manual upload / linked)
    intake: list[str] = field(default_factory=list)
    #: the analyst-facing summary (the redesigned overview, 2026-10-12): the central mechanism in
    #: words, the change lines without engine tags, the earnings steps, the action in plain words
    mechanism: str = ""
    changed_plain: list[str] = field(default_factory=list)
    implications: list[str] = field(default_factory=list)
    why: list[str] = field(default_factory=list)
    #: (line anchor, line name, what is open) of every withheld / review-flagged line on the card
    review_lines: list[tuple[str, str, str]] = field(default_factory=list)
    #: review findings a later version resolved: (line anchor, line name, why) — history
    resolved_lines: list[tuple[str, str, str]] = field(default_factory=list)
    #: the earnings chain in step names, and the step closest to profits in the source's words
    impact_chain: list[str] = field(default_factory=list)
    impact_line: str = ""
    #: business groups the source names (not companies, not exposures)
    groups: list[str] = field(default_factory=list)
    #: this report's events in words — "New", "Downgraded: Research Now → Watch" — ALL of them:
    #: a thesis created and downgraded in one week shows both, and is still one row
    events: list[str] = field(default_factory=list)
    source_line: str = ""
    partial_source: bool = False


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
    #: [first, last] date of the runs it covers — the report's window
    span: list[str] = field(default_factory=list)
    #: figures in the week's articles and those not captured — each article once (the census)
    figures_in_articles: int = 0
    figures_uncaptured: int = 0
    #: propositions resting on NO verified material evidence (SKIP-1): never research
    #: opportunities, so kept out of the categories — listed apart, with why, for the audit
    no_evidence: list[DashRow] = field(default_factory=list)


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
        out.append(f"{a.publisher} — {authors} — "
                   f"“{clean_title(a.title, a.publisher) or 'title UNKNOWN'}” (article date "
                   f"{pub}) — {what.lower()}")
    return out


def _category(events: list[ChangeEvent], prev_action: ResearchAction | None,
              now_action: ResearchAction) -> WeeklyCategory | None:
    types = {x.event_type for x in events}
    if types & set(ARCHIVING):
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


_ACTION_WORDS = {ResearchAction.RESEARCH_NOW: "Research Now", ResearchAction.WATCH: "Watch",
                 ResearchAction.SKIP: "Skip"}


def _analyst_view(store: Store, t: Thesis, cur: ThesisVersion, before: list[ThesisVersion],
                  this_run: list[ThesisVersion], evs: list[ChangeEvent], rids: set[str],
                  mech_label: dict[str, str]) -> dict[str, Any]:
    """A thesis as the redesigned weekly overview shows it — read from the stored version and the
    report's events, never from rendered text: the central mechanism in words; the change lines
    and earnings steps without engine tags; why the action, in plain words; the card lines still
    open for review (linked); every event of the week (a thesis new AND downgraded in one week
    shows both); and its source with date."""
    c = cur.content
    types = {x.event_type for x in evs}
    events: list[str] = ["New"] if "CREATED" in types else []
    seq = ([before[-1]] if before else []) + sorted(this_run, key=lambda x: x.version)
    for a, b in zip(seq, seq[1:], strict=False):
        pa, pb = a.priority.research_action, b.priority.research_action
        if pa is not pb:
            word = "Upgraded" if ACTION_RANK[pb] > ACTION_RANK[pa] else "Downgraded"
            events.append(f"{word}: {_ACTION_WORDS[pa]} → {_ACTION_WORDS[pb]}")
    if "CHALLENGED" in types:
        events.append("Challenged by new evidence")
    if any(i.code == "ANALYST_CORRECTION" and i.ref_id.startswith(t.thesis_id + ":")
           for r in rids for i in store.issues(run_id=r)):
        events.append("Analyst correction")
    if "RETIRED" in types:
        events.append("Retired — re-analysed")
    elif "ARCHIVED" in types:
        events.append("Archived")
    if not events and types & {"UPDATED", "UPGRADED", "REACTIVATED"}:
        events.append("Updated")
    blocked, flagged, _corr, resolved = line_findings(store, t.thesis_id, cur)
    found, unread = _group_read(store, store.links(t.thesis_id))
    groups = [g.name for g in found]
    skip = set(blocked) | set(flagged)
    mi = mechanism_step(c, skip)
    rest = [(i, st) for i, st in enumerate(c.s03_transmission)
            if st.step != "market_reaction" and i != mi]
    said = [(i, st) for i, st in rest if st.provenance in SOURCE_LABELS and f"s03.{i}" not in skip]
    unknown = any(st.text.startswith("UNKNOWN") for _i, st in rest)
    review = [(sid, blocked.get(sid) and "withheld — failed source verification"
               or flagged[sid]) for sid in card_sentences(c) if sid in blocked or sid in flagged]
    src = c.s09_sources[-1] if c.s09_sources else None
    vs = store.article_versions(src.article_id) if src else []
    partial = bool(vs) and vs[-1].retrieval_state is not RetrievalState.FULL
    return {
        # HOW it works, in the source's words (a verified line of the card); the taxonomy
        # category only when no step is stated by the source
        "mechanism": (_plain(c.s03_transmission[mi].text) if mi is not None else
                      "Category: " + mech_label.get(t.key_mechanism,
                                                    t.key_mechanism.replace("_", " "))),
        "impact_chain": [STEP_LABEL.get(st.step, st.step)
                         + (" (not quantified)" if st.text.startswith("UNKNOWN") else "")
                         for _i, st in rest],
        "impact_line": (f"{STEP_LABEL.get(said[-1][1].step, said[-1][1].step)}: "
                        f"{_plain(said[-1][1].text)}" if said else
                        "The source does not quantify an effect on listed-company earnings."
                        if unknown else "No earnings step stated by the source."),
        "groups": groups,
        "resolved_lines": [(_card_anchor(sid), name, why) for (sid, (why, _w)), name
                           in zip(resolved.items(), finding_names(list(resolved)), strict=True)],
        "changed_plain": [_plain(it.text) for it in c.s02_what_changed.items],
        "implications": [f"{STEP_LABEL.get(st.step, st.step)}: {_plain(st.text)}"
                         for st in c.s03_transmission if st.step != "market_reaction"],
        "why": why_reasons(c, cur.priority, groups, groups_unchecked=unread > 0),
        "review_lines": [(_card_anchor(sid), _line_name(sid), said) for sid, said in review],
        "events": events,
        "source_line": (f"{src.publisher} · published "
                        f"{src.published_at.date().isoformat() if src.published_at else 'UNKNOWN'}"
                        if src else ""),
        "partial_source": partial,
    }


def build_dashboard(store: Store, run_id: str, *, cards: dict[str, dict[str, str]],
                    generated: str, runs: list[WeeklyRun] | None = None,
                    census: tuple[int, int, int, int] | None = None,
                    asof: AsOf | None = None) -> Dashboard:
    """The weekly report of `run_id` over `report_runs` — or over `runs` when given (the research
    desk's week in progress: every manual run since the last weekly scan, desk.desk_weeks).
    `asof`: the run's `theses_as_of_run`, when the caller already holds it (U41)."""
    run = store.run(run_id)
    if run is None:
        raise KeyError(f"no run {run_id}")
    asof = asof if asof is not None else theses_as_of_run(store, run)
    runs = runs or report_runs(store, run)
    rids = {r.run_id for r in runs}
    events = [ev for r in runs for ev in store.events(run_id=r.run_id)]
    by_thesis: dict[str, list[ChangeEvent]] = {}
    for ev in events:
        by_thesis.setdefault(ev.thesis_id, []).append(ev)
    cats: dict[str, list[DashRow]] = {c.value: [] for c in CATEGORY_ORDER}
    no_material: list[str] = []
    no_evidence: list[DashRow] = []
    mech_label = {m.id: m.label for m in load_taxonomy().mechanisms}
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
            if x.event_type in (*ARCHIVING, "REACTIVATED", "REVIEW_NEEDED"):
                changed.append(f"{x.event_type.replace('_', ' ').capitalize()}: {x.detail}")
        av = cur.content.s05_affected
        inst = exposure_instruments(av)
        flags = sorted({x.event_type for x in evs} - {"CREATED", "UPDATED"})
        if t.status is ThesisStatus.REVIEW_NEEDED:
            flags.append("REVIEW_NEEDED")
        hdr = cur.content.header
        view = _analyst_view(store, t, cur, before, this_run, evs, rids, mech_label)
        row = DashRow(
            category=cat.value, thesis_id=tid, title=t.title, action=now_action.value,
            previous_action=prev_action.value if prev_action else None,
            change_reason=cur.priority.change_reason,
            evidence_direction=cur.evidence_direction.value, what_changed=changed,
            sources=_sources_line(store, tid, rids), intake=_intake_labels(store, tid, rids),
            named_companies=[c.name_as_written + (" (" + "/".join(x.ticker for x in c.listings)
                                                  + ")" if c.listings else
                                                  f" ({c.resolution_status.value})")
                             for c in exposures_of(av)[0]],
            # the instruments the source ATTACHES (its exposure, as `named_companies` holds the
            # exposure companies); an instrument only named is another name (2026-10-16)
            named_instruments=[c.name_as_written + (
                f" [fund {'/'.join(x.ticker for x in c.listings)}]" if c.listings
                else " [basket — members not named]" if c.role.value == "cited_basket"
                else f" [{c.resolution_status.value.lower()}]") for c in inst],
            private_named=[f"{c.name_as_written} [private company]"
                           for c in av.private_or_unlisted],
            other_named=[f"{c.name_as_written} ["
                         + ("basket — members not named" if c.role.value == "cited_basket"
                            else "not a security") + "]" for c in av.not_securities
                         if c not in inst] + [
                f"{c.name_as_written} [{c.resolution_status.value.lower()} — named, not "
                f"attached to the thesis]" for c in av.instruments if c not in inst],
            sectors=list(av.sectors), next_action=cur.content.s08_decision.next_step.text,
            last_material_update=t.last_material_update.isoformat(), status=t.status.value,
            flags=sorted(set(flags)), version=cur.version,
            card=cards.get(tid, {}).get("html", ""), kind=hdr.kind.value, retired=bool(t.retired),
            article_date=hdr.latest_article_date.isoformat() if hdr.latest_article_date else None,
            first_ingested=f"{t.created_at:%Y-%m-%d %H:%M} UTC",
            analysis_as_of=cur.as_of.isoformat(),
            sector_exposures=[f"{x.name} ({x.direction.value})" for x in distinct_sectors(av)],
            # the action's reasons ONCE, from the stored factor values (`cards.why_reasons`) —
            # the row's "why" list and this line can never disagree (U53: a regex over the rule
            # trace named a contested WATCH that the list beside it did not)
            why_action=" ".join(view["why"]),
            watch=watch_of(cur.priority, cur.content.s05_affected),
            rule_trace=list(cur.priority.rules_fired), what_changed_audit=audit, **view)
        if any(r.startswith(NO_EVIDENCE_RULE) for r in cur.priority.rules_fired):
            no_evidence.append(row)  # not an opportunity: never under NEW / UPGRADED / …
            continue
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
    # the span of every run the report covers — the desk's week, not the last run's own window
    # (U54: the published report read "14 Oct" beside This week's "12–14 Oct")
    span = [min(r.window_from or r.as_of for r in runs).isoformat(),
            max(r.window_to or r.as_of for r in runs).isoformat()]
    window = f"{span[0]} → {span[1]} (as of {run.as_of.isoformat()}, mode {run.mode})"
    if census is None:  # a report built without a desk counts by the desk's census itself
        from vinci.theme_intelligence.desk import analysed_articles  # the desk reads this module

        census = analysed_articles(store, runs)
    n_read, n_part, n_fig, n_unc = census
    d = Dashboard(
        run=json.loads(run.model_dump_json()), banner=banner, window=window, span=span,
        sources=[json.loads(sc.model_dump_json()) for sc in run.sources],
        sources_checked=sum(1 for sc in run.sources if sc.status != "NOT_RUN"),
        sources_failed=failed,
        # each article ONCE, by the Articles screen's census (a preview a correction record has
        # since found is counted in part, as the store reads it now)
        articles_read=n_read, articles_partial=n_part,
        articles_blocked=sum(r.counts.get("articles_blocked", 0)
                             + r.counts.get("articles_no_body", 0) for r in runs),
        themes_created=sum(r.counts.get("theses_created", 0) for r in runs),
        themes_updated=sum(r.counts.get("theses_updated", 0) for r in runs),
        attributions_only=sum(r.counts.get("attributions_only", 0) for r in runs),
        totals_active=totals, archived_total=sum(1 for t, _ in asof.values()
                                                 if t.status is ThesisStatus.ARCHIVED),
        caveats=caveats, categories=cats, no_material_change=no_material, archive=archive,
        no_evidence=sorted(no_evidence, key=lambda r: r.thesis_id),
        validation=val, generated=generated)
    d.report_runs = [r.run_id for r in runs]
    d.figures_in_articles, d.figures_uncaptured = n_fig, n_unc
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
    # a manual-first channel's AUTOMATED access is still health-checked: say what it found, so
    # "blocked: none" (of the automatic channels) never reads as "nothing is blocked" beside a
    # health block counting it blocked (observed 2026-10-11, the seven-source dashboard)
    access = {r["source_id"]: r["status"] for r in d.source_health.get("rows", [])}
    # Every count below is over the theses THIS RUN created or changed (all sections, the
    # archived included) and its EVENTS: a SKIP is archived at once, so counting active theses
    # could never show one; and a thesis created and challenged in one run sits under NEW, so
    # counting sections hid the challenge (both observed in the 2026-10-10 weekly run).
    rows = [r for rs in d.categories.values() for r in rs] + d.no_evidence
    live = [r for r in rows if not r.retired]  # a retired thesis is history, not an action

    def rank(a: str) -> int:
        return ACTION_RANK[ResearchAction(a)]

    return {
        "accessible_sources": None if manual else f"{len(accessible)} of {len(automatic)}",
        "manual_first_sources": None if manual else (
            ", ".join(names.get(s["source_id"], s["source_id"])
                      + (f" [automated access {access[s['source_id']]}]"
                         if s["source_id"] in access else "") for s in manual_first)
            or "none"),
        # the same channels by name only, for the Sources section (the access code above stays
        # in the Markdown record and Operations & audit)
        "upload_only_sources": None if manual else (
            ", ".join(names.get(s["source_id"], s["source_id"]) for s in manual_first) or "none"),
        "blocked_sources": None if manual else (
            ", ".join(names.get(s["source_id"], s["source_id"]) for s in blocked) or "none"),
        "articles_full": d.articles_read - d.articles_partial,
        "articles_partial": d.articles_partial,
        "articles_blocked": d.articles_blocked,
        "queued": run.get("counts", {}).get("articles_queued", 0),
        "theses_this_run": len(rows),
        "research_now": sum(1 for r in live if r.action == ResearchAction.RESEARCH_NOW.value),
        "watch": sum(1 for r in live if r.action == ResearchAction.WATCH.value),
        "skip": sum(1 for r in live if r.action == ResearchAction.SKIP.value),
        "retired": len(rows) - len(live),
        # EVENTS, not sections: a thesis new this week AND downgraded in it counts in both
        # (observed 2026-10-12: the pilot's re-graded RESEARCH NOW read "downgraded 0")
        "new": sum(1 for r in rows if r.previous_action is None or "New" in r.events),
        "upgraded": sum(1 for r in rows if any(x.startswith("Upgraded") for x in r.events) or (
            r.previous_action is not None and rank(r.action) > rank(r.previous_action))),
        "downgraded": sum(1 for r in rows if any(x.startswith("Downgraded") for x in r.events)
                          or (r.previous_action is not None
                              and rank(r.action) < rank(r.previous_action))),
        "challenged": sum(1 for r in rows if "CHALLENGED" in r.flags),
        "archived": d.archived_total,
        # the week's articles, each once — never one run's counter beside the week's articles
        "figures_uncaptured": d.figures_uncaptured,
        "figures_in_articles": d.figures_in_articles,
        "manually_imported": d.intake.get("manual", {}).get("total", 0) if d.intake else 0,
    }


def dates_line(r: DashRow, *, explain: bool = True) -> str:
    """Three dates, never conflated: the publisher's, the registry's actual first ingestion (wall
    clock, UTC) and the analysis as-of — which a historical replay sets BEFORE ingestion, so it is
    never called a detection."""
    replay = (r.analysis_as_of is not None and r.first_ingested is not None
              and r.analysis_as_of < r.first_ingested[:10])
    return (f"Published {r.article_date or 'UNKNOWN'} · first ingested by the registry "
            f"{r.first_ingested or 'UNKNOWN'}"
            + (" (new to the registry, not necessarily new to the market)"
               if explain and r.category == WeeklyCategory.NEW.value else "")
            + f" · analysed as of {r.analysis_as_of or 'UNKNOWN'}"
            + (" (a historical replay — a simulated date, not a detection)" if replay else ""))


def _plain(text: str) -> str:
    """A card line for the first view: the system labels inside ⟨…⟩ are dropped (they are kept
    in the audit trail and the card)."""
    return re.sub(r"\s*⟨[^⟩]*⟩\s*", " ", text).strip()


# --- dashboard renderers -----------------------------------------------------------------------

_DASH_CSS = """
.dhead{margin:4px 0 18px}.dhead .subline{color:var(--muted);font-size:14px}
.banner{background:var(--now-bg);color:var(--now);padding:10px 12px;border-radius:8px;
font-weight:650;margin:0 0 14px}
.summary{display:flex;flex-wrap:wrap;gap:10px;margin:0 0 6px}
.stat{flex:1 1 120px;min-width:0;background:var(--panel);border:1px solid var(--line);
border-radius:10px;padding:10px 14px;color:var(--ink)}a.stat:hover{text-decoration:none;
border-color:var(--accent)}.stat b{display:block;font-size:22px;line-height:1.2;font-weight:680}
.stat span{display:block;font-size:12.5px;color:var(--muted)}.stat.warn b{color:var(--warn)}
.stat .vt{font-size:15px;line-height:1.9}
.theses{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.thesis{background:var(--panel);border:1px solid var(--line);border-radius:12px;
padding:16px 18px;display:flex;flex-direction:column;gap:8px}
.thesis .ttop{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.thesis h3{font-size:16.5px;margin:2px 0 0}.thesis h3 a{color:var(--ink)}
.mech{font-size:13.5px;color:var(--ink2);margin-top:2px}
.chain{font-size:12.5px;color:var(--muted);margin-bottom:3px}.legend{margin:10px 0 0}
.stat span.sm{font-size:11.5px;margin-top:2px}details.rqd{margin-top:10px}
details.rqd>summary{font-size:14px;font-weight:600}
.tgrid{display:grid;grid-template-columns:118px minmax(0,1fr);gap:6px 12px;margin:4px 0 0;
font-size:14px}.tgrid dt{color:var(--muted);font-size:12px;font-weight:600;letter-spacing:.03em;
padding-top:2px}.tgrid dd{margin:0}.tgrid ul{margin:0;padding-left:16px}
.tfoot{display:flex;flex-wrap:wrap;justify-content:space-between;gap:6px;margin-top:auto;
padding-top:8px;border-top:1px solid var(--line);font-size:13px;color:var(--muted)}
.acts{list-style:none;margin:0;padding:0}.acts li{padding:8px 0;border-bottom:1px solid var(--line);
display:flex;flex-wrap:wrap;gap:6px 10px;align-items:baseline}
.rq{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 18px;
margin:0 0 12px}.rq h3{font-size:14px;margin:0 0 8px}.rq ul{margin:0;padding-left:18px}
.rq li{margin:4px 0}.vstat{border:1px solid var(--line);border-left:4px solid var(--watch);
border-radius:8px;padding:10px 14px;margin:0 0 12px;background:var(--panel)}
.sh{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 16px;
margin:0 0 12px}.sh ul{margin:6px 0 0;padding-left:18px}.sh li{margin:6px 0}
.sh .pill{margin-left:6px}.k{color:var(--muted);font-size:12px;text-transform:uppercase;
letter-spacing:.05em;margin:0 0 4px;font-weight:600}
.empty{color:var(--muted);font-style:italic;margin:4px 0 8px}
input.search{width:100%;padding:9px 10px;border:1px solid var(--line);border-radius:8px;
background:var(--panel);color:var(--ink);margin:6px 0;font:inherit}
.ops>details{margin:0 0 6px}
@media (max-width:820px){.theses{grid-template-columns:minmax(0,1fr)}}
@media (max-width:520px){.tgrid{grid-template-columns:minmax(0,1fr)}.tgrid dt{padding-top:6px}
.stat{flex-basis:44%}}
@media print{.thesis,.rq{break-inside:avoid}details{display:block}input.search{display:none}}
"""

_VERIFICATION_WORD = {"FULLY_VERIFIED": "Fully verified",
                      "VERIFIED_WITHIN_PREVIEW": "Verified within previews",
                      "INCOMPLETE": "Incomplete", "NOTHING_ANALYSED": "Nothing analysed"}
_PILL_CLS = {"RESEARCH NOW": "now", "WATCH": "watch"}
_RANK = {"RESEARCH NOW": 2, "WATCH": 1, "SKIP": 0}


def _active_rows(d: Dashboard) -> list[DashRow]:
    """Every thesis this report covers, ONE row each, ranked by research action, then the
    freshest material evidence (a thesis new and downgraded in one week is one row, two events)."""
    rows = [r for cat in CATEGORY_ORDER for r in d.categories.get(cat.value, [])
            if not r.retired]  # a retired thesis is never something to research this week
    rows.sort(key=lambda r: r.thesis_id)
    rows.sort(key=lambda r: r.last_material_update, reverse=True)
    rows.sort(key=lambda r: -_RANK.get(r.action, 0))
    return rows


def _event_tag(x: str) -> str:
    cls = " down" if x.startswith("Downgraded") else " up" if x.startswith("Upgraded") else ""
    return f'<span class="tag{cls}">{e(x)}</span>'


def _thesis_html(r: DashRow) -> str:
    """One thesis on the weekly overview: what it is, what changed, its effect on profits, why
    the action, the next question and the source — the full record is one click away."""
    act = _ACTION_WORDS.get(ResearchAction(r.action), r.action)
    review = (f'<a class="flag" href="{e(r.card)}#{e(r.review_lines[0][0])}">Review required · '
              f'{len(r.review_lines)} line(s)</a>' if r.review_lines else "")
    kind = (f'<span class="pill kind">{e(KIND_LABEL[ThesisKind(r.kind)])}</span>'
            if r.kind == ThesisKind.MARKET_REGIME.value else "")
    changed = r.changed_plain[:1]
    more = (f' <a class="note" href="{e(r.card)}#sec-s02_what_changed">+{len(r.changed_plain) - 1}'
            f' more</a>' if len(r.changed_plain) > 1 else "")
    chain = " → ".join(r.impact_chain)
    audit = (f'<div class="aud"><div class="cc">{e(r.thesis_id)} · v{r.version} · {e(r.category)}'
             + (" · " + e(", ".join(r.flags)) if r.flags else "") + "</div>"
             + "".join(f'<div class="cc">{e(t)}</div>' for t in r.rule_trace) + "</div>")
    return (
        f'<article class="thesis row"><div class="ttop"><span class="pill '
        f'{_PILL_CLS.get(r.action, "skip")}">{e(act)}</span>{kind}'
        + "".join(_event_tag(x) for x in r.events) + review + "</div>"
        f'<h3><a href="{e(r.card)}">{e(r.title)}</a></h3>'
        f'<div class="mech">{e(r.mechanism)}</div><dl class="tgrid">'
        f'<dt>What changed</dt><dd>'
        + ("".join(e(_clean_display(x)) for x in changed) or "—") + more + "</dd>"
        + "<dt>Effect on profits</dt><dd>"
        + (f'<div class="chain">{e(chain)}</div>' if chain else "")
        + f"{e(_clean_display(r.impact_line))}</dd>"
        + f"<dt>Why {e(act)}</dt><dd><ul>" + "".join(f"<li>{e(x)}</li>" for x in r.why)
        + f"</ul></dd><dt>Next question</dt><dd>{e(r.next_action)}</dd></dl>"
        f'<div class="tfoot"><span>{e(r.source_line.partition(" · ")[0])}'
        + (' · <b>read only in part</b>' if r.partial_source else "") + "</span>"
        f'<a href="{e(r.card)}">Open the thesis card →</a></div>'
        f'<div class="dates">{e(dates_line(r, explain=False))}'
        + (f' · How this evidence arrived: {ids_to_audit(e("; ".join(r.intake)))}'
           if r.intake else "")
        + "</div>" + audit + "</article>")


def _activity_html(rows: list[DashRow]) -> str:
    items = [f'<li>{"".join(_event_tag(x) for x in r.events)}<a href="{e(r.card)}">'
             f'{e(r.title)}</a></li>' for r in rows if r.events]
    return ("<ul class=\"acts\">" + "".join(items) + "</ul>") if items else \
        '<div class="empty">No change this week.</div>'


def _brief(said: str, n: int = 170) -> str:
    """A finding, shortened for the queue at a word boundary — the "…" says it was shortened; the
    whole finding stays on its card line, one link away."""
    if len(said) <= n:
        return said
    return said[:said.rfind(" ", 0, n)].rstrip(" ,;:") + " …"


def review_counts(d: Dashboard, rows: list[DashRow]) -> dict[str, int]:
    """The review queue's four groups, counted: current card lines (withheld or questioned — the
    ones that bear on a decision), incomplete sources, background alerts, resolved/historical."""
    v = d.verification or {}
    partial = (d.intake or {}).get("awaiting_documents", {}).get("items", [])
    return {"current": sum(len(r.review_lines) for r in rows),
            "incomplete": len(v.get("open_items_plain") or []) + len(partial),
            "background": len(v.get("coverage_alerts_plain") or []),
            "historical": len(v.get("superseded_items_plain") or [])
            + sum(len(r.resolved_lines) for r in rows)}


def _review_html(d: Dashboard, rows: list[DashRow], print_mode: bool) -> str:
    v = d.verification or {}
    n = review_counts(d, rows)
    op = " open" if print_mode else ""
    lines = "".join(
        f'<li><a href="{e(r.card)}">{e(r.title)}</a><ul>' + "".join(
            f'<li><a href="{e(r.card)}#{e(a)}">{e(name)}</a> — {ids_to_audit(e(_brief(said)))}'
            f'</li>' for a, name, said in r.review_lines) + "</ul></li>"
        for r in rows if r.review_lines)
    opens = v.get("open_items_plain") or []
    alerts = [_clean_display(x) for x in (v.get("coverage_alerts_plain") or [])]
    partial = (d.intake or {}).get("awaiting_documents", {}).get("items", [])
    # the warning box only while something is open; a fully verified run reads as a plain note
    box = "note" if v.get("status") == "FULLY_VERIFIED" else "vstat"
    vstat = [f'<div class="{box}"><b>Research verification: '
           f'{e(_VERIFICATION_WORD.get(v.get("status", ""), v.get("status", "UNKNOWN")))}</b>'
           + (f' — {v.get("figures_open", 0)} of {v.get("figures", 0)} stated figures and '
              f'{v.get("paragraphs_open", 0)} of {v.get("paragraphs", 0)} argument paragraphs '
              f'open over {v.get("articles", 0)} article version(s); '
              f'{v.get("articles_preview_only", 0)} read only in part'
              + (f'; {v["figures_superseded"]} of the open figures failed a since-corrected '
                 f'check (under Resolved or historical)' if v.get("figures_superseded") else "")
              + '. Open material is never used as evidence.' if v else "") + "</div>"]

    def items(xs: list[str]) -> str:
        return ("<ul>" + "".join(f"<li>{ids_to_audit(e(x))}</li>" for x in xs) + "</ul>"
                if xs else '<div class="empty">None.</div>')

    hist = [x for r in rows for x in r.resolved_lines]
    hist_html = "".join(
        f'<li><a href="{e(r.card)}">{e(r.title)}</a> — ' + "; ".join(
            f'<a href="{e(r.card)}#{e(a)}">{e(name)}</a>: {e(why)}'
            for a, name, why in r.resolved_lines) + "</li>" for r in rows if r.resolved_lines)
    sup = v.get("superseded_items_plain") or []
    out = [f'<div class="rq"><h3>On the current cards — lines withheld or questioned '
           f'({n["current"]})</h3><div class="note">Each finding is shortened here (…); the '
           f'whole finding is on its card line — follow the link.</div>'
           + (f"<ul>{lines}</ul>" if lines else '<div class="empty">None — no line of a current '
                                                'card is withheld or questioned.</div>') + "</div>",
           f'<details class="sec rqd"{op}><summary>Incomplete sources ({n["incomplete"]}) — '
           f'figures and paragraphs not accounted for; articles read only in part</summary>'
           + vstat[0] + '<div class="rq"><h3>Figures and paragraphs not yet accounted for</h3>'
           + items(opens) + '</div><div class="rq"><h3>Articles read only in part — awaiting a '
           'complete copy</h3>' + items(partial) + "</div></details>",
           f'<details class="sec rqd"{op}><summary>Background alerts ({n["background"]}) — '
           f'evidence no thesis carries, or a proposition dropped</summary>' + items(alerts)
           + "</details>",
           f'<details class="sec rqd"{op}><summary>Resolved or historical ({n["historical"]}) — '
           f'past validation failures since corrected; review findings a later version resolved'
           f'</summary><div class="note">Kept as history: the stored records are never edited. '
           f'None of these bears on a current card.</div>'
           + (f"<ul>{hist_html}</ul>" if hist_html else "") + (items(sup) if sup else "")
           + ('<div class="empty">None.</div>' if not hist and not sup else "") + "</details>"]
    return "".join(out)


def _sources_html(d: Dashboard, print_mode: bool) -> str:
    h = d.source_health or {}
    if not h:
        return '<div class="empty">No source-health check recorded.</div>'
    when = (f"checked {h['checked_at'][:16].replace('T', ' ')} UTC"
            if h.get("checked_at") else "not checked yet")
    n = h.get("counts", {})
    head = (f"{n.get('HEALTHY', 0)} of {h.get('total', 0)} sources working"
            + "".join(f" · {n[k]} {w}" for k, w in (("DEGRADED", "partly"), ("BLOCKED", "blocked"),
                                                     ("ERROR", "failing"),
                                                     ("UNKNOWN", "status not known"))
                    if n.get(k)))
    # in words, from the structured test results (health.plain_line) — the check's own reason,
    # with its error names, stays in Operations & audit
    att = "".join(
        f'<li><b>{e(r["publisher"])}</b><span class="pill {_HEALTH_PILL.get(r["status"], "dir")}">'
        f'{e(_HEALTH_WORD.get(r["status"], r["status"].lower()))}</span><div class="note">'
        f'{e(r.get("plain") or _plain_reason(r))}'
        + (". Supply its research by upload." if r.get("manual_action")
           and "upload" not in (r.get("plain") or "") else "")
        + "</div></li>" for r in h.get("attention", []))
    rows = "".join(
        f"<tr><td>{e(r['publisher'])}</td>"
        f"<td>{e(_HEALTH_WORD.get(r['status'], r['status'].lower()))}</td>"
        f"<td>{e(_FRESH_WORD.get(r['freshness'], r['freshness'].lower()))}"
        f"{(' · newest ' + e(r['newest_article_date'])) if r['newest_article_date'] else ''}</td>"
        f"<td>{e((r['last_successful_discovery'] or 'never')[:10])}</td>"
        f"<td>{e((r['last_successful_extraction'] or 'never')[:10])}</td>"
        f"<td>{r['discovered']} found · {r['in_window']} in the window</td></tr>"
        for r in h.get("rows", []))
    intake = d.intake or {}
    cov = (intake.get("coverage_plain") or intake.get("coverage") or {}).get("items", [])
    k = d.kpi or {}
    scan = (f'<div class="note">This scan read <b>{e(k["accessible_sources"])}</b> automatic '
            f'channels · blocked: <b>{e(k["blocked_sources"])}</b> · by upload only: '
            f'{e(k.get("upload_only_sources") or "none")}</div>'
            if k.get("accessible_sources") is not None else "")
    return (f'<div class="sh"><div><b>{e(head)}</b> <span class="note">{e(when)}</span>'
            f'</div>{scan}' + (f"<ul>{att}</ul>" if att else "") + "</div>"
            + '<details class="sec"' + (" open" if print_mode else "") + '><summary>All '
            f'{h.get("total", 0)} publishers</summary><div class="hscroll"><table><tr>'
            "<th>Publisher</th><th>Working?</th><th>New articles</th><th>Last listed</th>"
            "<th>Last read in full</th><th>Articles</th></tr>" + rows
            + "</table></div></details>"
            + '<details class="sec"' + (" open" if print_mode else "") + '><summary>What each '
            f'publisher gave this week ({len(cov)})</summary><ul>'
            + "".join(f"<li>{e(x)}</li>" for x in cov) + "</ul></details>")


def _plain_reason(r: dict[str, Any]) -> str:
    """A channel's health reason without the operator's commands (those stay in Operations)."""
    return re.split(r"\s*(?:→|— upload an authorized copy|Meanwhile upload)", r["reason"])[0]


def _archive_html(d: Dashboard) -> str:
    return ('<input class="search" placeholder="Filter by title, sector, action or status…" '
            'oninput="filt(this.value)" aria-label="Filter the archive"><div class="hscroll">'
            '<table id="arch"><tr><th>Thesis</th><th>Action</th><th>Status</th><th>Sector</th>'
            '<th>Versions</th><th>Last material update</th><th class="aud">Id · node / '
            'mechanism</th></tr>'
            + "".join(
                f'<tr><td><a href="{e(a["card"])}">{e(a["title"])}</a></td>'
                f'<td>{e(_ACTION_WORDS.get(ResearchAction(a["action"]), a["action"]))}</td>'
                f'<td>{e(a["status"].lower())}</td><td>{e(a["sector"])} · {e(a["region"])}</td>'
                f'<td>{a["versions"]}</td><td>{e(a["last_material_update"])}</td>'
                f'<td class="cc aud">{e(a["thesis_id"])} · {e(a["node"])} / '
                f'{e(a["mechanism"])} / {e(a["direction"])}</td></tr>' for a in d.archive)
            + "</table></div>")


def _ops_html(d: Dashboard, print_mode: bool) -> str:
    """Operations & audit — run ids, engine codes, upload commands, the validation log. For the
    operator; the analyst-facing views above never print them."""
    run = d.run
    op = " open" if print_mode else ""
    val = d.validation
    parts = [
        f'<details class="sec"{op}><summary>Run and report scope</summary><div class="s cc">'
        f'run {e(run["run_id"])} · mode {e(run["mode"])} · scan execution {e(run["status"])} · '
        f'research verification {e((d.verification or {}).get("status", "UNKNOWN"))} · window '
        f'{e(d.window)}</div><div class="s note">This report covers '
        f'{len(d.report_runs)} run(s): {e(", ".join(d.report_runs))}</div>'
        f'<div class="s note">Verification log: {val.get("BLOCK", 0)} blocked · '
        f'{val.get("HOLD", 0)} held · {val.get("WARN", 0)} warnings · {val.get("INFO", 0)} info '
        f'(validation_log.json)</div></details>',
        f'<details class="sec"{op}><summary>Research source health (full)</summary>'
        + _health_html(d.source_health, print_mode) + "</details>",
        f'<details class="sec"{op}><summary>Research intake / manual action</summary>'
        + _intake_html(d.intake, print_mode) + "</details>"]
    if d.sources:
        parts.append(
            f'<details class="sec"{op}><summary>Source coverage ({len(d.sources)})</summary>'
            '<div class="hscroll"><table><tr><th>Source</th><th>Status</th><th>Discovered</th>'
            "<th>In window</th><th>Undated</th><th>New</th><th>Processed</th><th>Queued</th>"
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
                for s in d.sources) + "</table></div></details>")
    v = d.verification or {}
    if v.get("open_items"):
        parts.append(f'<details class="sec"{op}><summary>Open items — engine record '
                     f'({len(v["open_items"])})</summary>'
                     + "".join(f'<div class="s note">{e(x)}</div>' for x in v["open_items"])
                     + "</details>")
    parts.append(_coverage_html(v, print_mode))
    if d.caveats:
        parts.append(f'<details class="sec"{op}><summary>Unresolved retrieval / verification '
                     f'caveats ({len(d.caveats)})</summary>'
                     + "".join(f'<div class="s note">{e(c)}</div>' for c in d.caveats)
                     + "</details>")
    if d.no_evidence:
        parts.append(f'<details class="sec"{op}><summary>Not research opportunities '
                     f'({len(d.no_evidence)}) — {e(NO_EVIDENCE_HELP)}</summary>'
                     + "".join(f'<div class="s note">{e(r.title)} — {e(r.why_action)}'
                               f'<span class="aud"> · {e(r.thesis_id)} v{r.version} · '
                               f'{e(r.change_reason)}</span></div>' for r in d.no_evidence)
                     + "</details>")
    if d.no_material_change:
        parts.append(f'<details class="sec"{op}><summary>No material change this run '
                     f'({len(d.no_material_change)})</summary>'
                     + "".join(f'<div class="s note">{e(x)}</div>'
                               for x in d.no_material_change) + "</details>")
    return '<div class="ops">' + "".join(parts) + "</div>"


def _coverage_html(v: dict[str, Any], print_mode: bool) -> str:
    """Mechanism coverage: the alerts, then (on demand) every article's full record."""
    if not v.get("coverage"):
        return ""
    alerts = v.get("coverage_alerts_plain") or []
    body = "".join(f'<div class="s note">⚠ {e(x)}</div>' for x in alerts)
    audit = ""  # the full record names theses and claims by id: the audit view only
    for c in v["coverage"]:
        audit += (f'<div class="s"><b>{e(c["article_id"])}</b> — propositions '
                  f'{len(c["propositions"])}, uncarried fact group(s) {len(c["uncarried"])}, '
                  f'risks {len(c["risks"])}, risks the source states '
                  f'{len(c.get("source_risks", []))}, names not recorded '
                  f'{len(c["unrecorded_names"])}, earlier theses re-verified '
                  f'{len(c.get("reverified", []))}</div>')
        for label in ("propositions", "uncarried", "risks", "source_risks", "unrecorded_names",
                      "reverified"):
            audit += "".join(f'<div class="s note">{e(label.replace("_", " "))}: {e(x)}</div>'
                             for x in c.get(label, []))
    return ('<details class="sec"' + (" open" if print_mode else "")
            + f'><summary>Mechanism coverage — {len(alerts)} alert(s) for review</summary>'
            + body + f'<div class="aud">{audit}</div></details>')


#: the weekly report's own sections — its second nav row (the desk's screens are the first)
REPORT_SECTIONS = (("Overview", "#top"), ("Theses", "#theses"), ("Review queue", "#review"),
                   ("Sources", "#sources"), ("Archive", "#archive"), ("Operations", "#ops"))


def render_dashboard_html(d: Dashboard, *, print_mode: bool = False,
                          embedded_cards: list[str] | None = None) -> str:
    """The weekly research brief. The FIRST screen is the research: title and as-of, a compact
    summary (Research Now / Watch / Skip, review items, verification), then the theses as
    concise cards. Review queue, sources, archive and Operations & audit are their own views
    (navigation at the top); engine ids, codes, commands and gate traces live only in Operations
    and behind the audit switch. The print view opens everything."""
    run = d.run
    v = d.verification or {}
    k = d.kpi or {}
    rows = _active_rows(d)
    rc_n = review_counts(d, rows)
    review_n = rc_n["current"]
    wf, wt = (d.span or ["—", "—"])[0], (d.span or ["—", "—"])[-1]
    parts = [f'<header class="dhead"><div class="eyebrow">Weekly research brief</div>'
             f'<h1>What to research this week</h1><div class="subline">{e(wf)} – {e(wt)} · as of '
             f'{e(run["as_of"])} · research attention only — never a purchase or sale</div>'
             f'</header>']
    if d.banner:
        parts.append(f'<div class="banner">{e(d.banner)}</div>')
    vword = _VERIFICATION_WORD.get(v.get("status", ""), v.get("status", "—"))
    parts.append(
        '<div class="summary">'
        f'<div class="stat"><b>{k.get("research_now", 0)}</b><span>Research Now</span></div>'
        f'<div class="stat"><b>{k.get("watch", 0)}</b><span>Watch</span></div>'
        f'<div class="stat"><b>{k.get("skip", 0)}</b><span>Skip</span></div>'
        f'<a class="stat{" warn" if review_n else ""}" href="#review"><b>{review_n}</b>'
        f'<span>Review items</span><span class="sm">on this week\'s cards</span></a>'
        f'<a class="stat" href="#review"><b class="vt">{e(vword)}</b><span>Verification · '
        # CURRENT open figures — those that failed a since-corrected check are history, told
        # apart in the review queue (the JSON keeps both counts)
        f'{v.get("figures_open", 0) - v.get("figures_superseded", 0)} figure(s), '
        f'{v.get("paragraphs_open", 0)} paragraph(s) open</span></a>'
        f'<div class="stat"><b>{k.get("articles_full", 0) + k.get("articles_partial", 0)}</b>'
        f'<span>Articles read · {k.get("articles_partial", 0)} in part</span></div></div>')
    # the retired are listed in the archive, never as research: said here so the count reads
    # with This week's, which names them beside the live (U54)
    n_retired = sum(1 for rs in d.categories.values() for r in rs if r.retired)
    parts.append(f'<section id="theses"><h2>Theses this week <small class="note">({len(rows)}'
                 + (f' · {n_retired} retired on re-analysis, in the archive' if n_retired else "")
                 + ') — ranked by research action, then the freshest evidence</small></h2>'
                 + ('<div class="theses">' + "".join(_thesis_html(r) for r in rows) + "</div>"
                    if rows else '<div class="empty">No thesis created or changed this week.'
                                 '</div>')
                 + '<div class="note legend">“First ingested” = new to this registry, not '
                   'necessarily new to the market.</div></section>')
    parts.append(f'<section id="activity"><h2>This week\'s activity <small class="note">— '
                 f'{k.get("new", 0)} new · {k.get("upgraded", 0)} upgraded · '
                 f'{k.get("downgraded", 0)} downgraded · {k.get("challenged", 0)} challenged'
                 f'</small></h2>' + _activity_html(rows) + "</section>")
    parts.append(f'<section id="review"><h2>Review queue <small class="note">({review_n} on '
                 f'current cards; the rest grouped below)</small></h2>'
                 + _review_html(d, rows, print_mode) + "</section>")
    parts.append('<section id="sources"><h2>Sources</h2>' + _sources_html(d, print_mode)
                 + "</section>")
    parts.append(f'<section id="archive"><h2>Archive <small class="note">({len(d.archive)} '
                 f'theses, every status)</small></h2>' + _archive_html(d) + "</section>")
    parts.append('<section id="ops"><h2>Operations &amp; audit <small class="note">— run ids, '
                 'engine codes, upload commands and the validation log</small></h2>'
                 + _ops_html(d, print_mode) + "</section>")
    parts.append(foot_html(d.generated))
    if embedded_cards:
        parts.append('<div style="break-before:page"></div>' + "".join(embedded_cards))
    script = ("<script>function filt(q){q=q.toLowerCase();document.querySelectorAll('#arch tr')"
              ".forEach((r,i)=>{if(i)r.style.display=r.textContent.toLowerCase().includes(q)?'':"
              "'none'})}window.addEventListener('beforeprint',()=>document.querySelectorAll("
              "'details').forEach(d=>d.open=true));</script>" + REVEAL_JS)
    return ("<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport "
            "content='width=device-width,initial-scale=1'>" + ROBOTS + "<title>Theme "
            "intelligence weekly</title><style>" + _CSS + _DASH_CSS + "</style></head><body>"
            + AUDIT_TOGGLE + topnav("", sections=REPORT_SECTIONS) + "<div class=wrap>"
            + "".join(parts) + "</div>" + script
            + "</body></html>")


_INTAKE_LISTS = (
    ("coverage", "Coverage by publisher (the configured channels)"),
    ("automatic", "Articles automatically analysed"),
    ("manual", "Articles manually imported"),
    ("awaiting_documents", "Partial articles awaiting a complete document"),
    ("publishers", "Publishers blocked or degraded"),
    ("needs_upload", "Known articles requiring an upload"),
    ("needs_metadata", "Requiring a metadata, licence or visual check"),
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
#: a channel's health and freshness in words (the codes stay in Operations & audit)
_HEALTH_WORD = {"HEALTHY": "working", "DEGRADED": "partly working", "BLOCKED": "blocked",
                "ERROR": "check failed", "UNKNOWN": "status not known"}
_FRESH_WORD = {"FRESH": "new articles recently", "QUIET": "nothing new recently",
               "UNKNOWN": "not known"}


def _health_html(h: dict[str, Any], print_mode: bool) -> str:
    """The compact block: the counts line, NEW changes prominently, only the channels needing
    attention (reason, action, affected article if known), and every channel on demand. Reasons are
    composed sentences — never a stack trace."""
    from vinci.theme_intelligence.health import affected_shown

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
                   f'{e(ma["action"])}' + (f" — affected: {e(affected_shown(ma, 2))}"
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
               '<div class="hscroll"><table><tr><th>Publisher</th><th>Health</th>'
               "<th>Freshness</th><th>Last checked (UTC)</th><th>Last discovery OK</th>"
               "<th>Last full-text OK</th><th>Last verified publication date</th>"
               "<th>Discovered / listing-dated in window</th>"
               "<th>Consecutive failed checks</th><th>Manual upload</th></tr>" + rows
               + "</table></div></details>")
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
    md += ([f"- Sources: {_no_discovery(run['mode'])}"]
           if k.get("accessible_sources") is None else
           [f"- Accessible sources: {k['accessible_sources']} (automatic channels)",
            f"- Blocked automatic channels: {k['blocked_sources']}",
            f"- Manual-first sources (health check only; research arrives as uploads): "
            f"{k.get('manual_first_sources') or 'none'}"])
    md += [f"- Articles analyzed: {k.get('articles_full', 0)} full · "
           f"{k.get('articles_partial', 0)} partial"
           + (f" · {k['articles_blocked']} unreadable" if k.get("articles_blocked") else "")
           + (f"; queued by the budget cap at the end of the last run, not yet read: "
              f"{k['queued']}" if k.get("queued") else ""),
           f"- Research Now / Watch / Skip: {k.get('research_now', 0)} / {k.get('watch', 0)} / "
           f"{k.get('skip', 0)} — of the {k.get('theses_this_run', 0)} theses the week's runs "
           f"created or changed" + (f", {k['retired']} of them retired (counted in none)"
                            if k.get("retired") else "")
           + f" (archived in the registry: {d.archived_total})",
           f"- New / upgraded / downgraded / challenged theses: {k.get('new', 0)} / "
           f"{k.get('upgraded', 0)} / {k.get('downgraded', 0)} / {k.get('challenged', 0)} — "
           f"the week's events; a thesis new this week can also be challenged in it",
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
    if v.get("coverage"):
        md += [f"## Mechanism coverage — {len(v.get('coverage_alerts') or [])} alert(s) for "
               f"review", ""] + [f"- ⚠ {x}" for x in v.get("coverage_alerts") or []] + [""]
        for c in v["coverage"]:
            md += [f"### {c['article_id']}", ""]
            for label in ("propositions", "uncarried", "risks", "unrecorded_names"):
                md += [f"- {label.replace('_', ' ')}: {x}" for x in c[label]]
            md.append("")
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
    if d.no_evidence:
        md += [f"## Not research opportunities ({len(d.no_evidence)}) — {NO_EVIDENCE_HELP}", ""]
        md += [f"- {r.title} — {r.why_action} · audit: `{r.thesis_id}` v{r.version} · "
               f"{r.change_reason} · card: {r.card}" for r in d.no_evidence] + [""]
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
    return plain_entities("\n".join(md))


def render_dashboard_csv(d: Dashboard) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")  # LF: committed readouts stay diff-able
    w.writerow(["category", "research_action", "previous_action", "thesis_id", "version", "title",
                "kind", "article_date", "first_ingested_utc", "analysis_as_of",
                "evidence_direction", "what_changed",
                "sources", "sector_exposures", "named_companies", "named_instruments",
                "private_named", "other_named", "sectors", "next_action", "why_action",
                "change_reason", "last_material_update", "status", "flags", "card"])
    for cat_rows in [d.categories.get(cat.value, []) for cat in CATEGORY_ORDER] + [
            d.no_evidence]:
        for r in cat_rows:
            w.writerow([r.category if r not in d.no_evidence
                        else "NOT AN OPPORTUNITY (no verified material evidence)", r.action,
                        r.previous_action or "", r.thesis_id, r.version,
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

def scoped_ids(body: str, prefix: str) -> str:
    """One embedded card's element ids, and its links to them, prefixed with its thesis id: the
    printed report carries every card, and each card's "L-s01-0" was then one id many times (U32d:
    42 ids repeated in the pilot's report_print.html). A link to an id outside the card is kept."""
    own = set(re.findall(r'\sid="([^"]+)"', body))
    return re.sub(r'(?<![\w:-])(id="|href="#)([^"]+)"',
                  lambda m: f'{m[1]}{prefix}-{m[2]}"' if m[2] in own else m[0], body)


def write_run_outputs(store: Store, run_id: str, out_dir: Path | None = None) -> dict[str, Any]:
    """Every output of one run — the cards, the weekly report, the desk, the manifest — in ONE
    read pass (`Store.reading`: each article version parsed once, U44)."""
    with store.reading():
        return _write_run_outputs(store, run_id, out_dir)


def _write_run_outputs(store: Store, run_id: str, out_dir: Path | None) -> dict[str, Any]:
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
    from vinci.theme_intelligence.desk import Desk  # the desk reads this module

    # ONE week, ONE view: the full weekly report IS the desk's This week report (U54: the
    # published pair read 6 theses / 3 articles beside 18 / 13) — built once, for both
    view = Desk(store, run, cards=cards, generated=generated, asof=asof)
    d = view.d
    (out / "dashboard.html").write_text(render_dashboard_html(d))
    delta_ids = [r.thesis_id for rows in d.categories.values() for r in rows] + [
        r.thesis_id for r in d.no_evidence]  # their cards stay in the printed record
    embedded = []
    for tid in delta_ids:
        if tid not in asof:
            continue
        t, v = asof[tid]
        body = render_html(v.content, card_context(store, t, v, generated=generated,
                                                   until=run.finished_at), print_mode=True)
        embedded.append(scoped_ids(body[body.index("<article"):body.index("</article>") + 10],
                                   tid))
    (out / "report_print.html").write_text(render_dashboard_html(d, print_mode=True,
                                                                 embedded_cards=embedded))
    (out / "dashboard.md").write_text(render_dashboard_md(d))
    (out / "dashboard.json").write_text(json.dumps(asdict(d), indent=1, sort_keys=True,
                                                   default=str))
    (out / "dashboard.csv").write_text(render_dashboard_csv(d))
    issues = store.issues(run_id=run_id)
    (out / "validation_log.json").write_text(json.dumps(
        [json.loads(i.model_dump_json()) for i in issues], indent=1, sort_keys=True))
    desk = view.write(out)
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
        "spend_guard": run.spend,
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
    return {"dir": str(out), "cards": cards, "dashboard": d, "manifest": manifest, "desk": desk}
