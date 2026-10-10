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
    first_detected: str | None = None
    sector_exposures: list[str] = field(default_factory=list)
    why_action: str = ""
    rule_trace: list[str] = field(default_factory=list)
    what_changed_audit: list[str] = field(default_factory=list)


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


def _sources_line(store: Store, tid: str, run_id: str) -> list[str]:
    out: list[str] = []
    for c in store.contributions(thesis_id=tid):
        if c.run_id != run_id:
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
    events = store.events(run_id=run_id)
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
        this_run = [v for v in versions if v.run_id == run_id]
        before = [v for v in versions if v.run_id != run_id
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
            sources=_sources_line(store, tid, run_id),
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
            first_detected=(hdr.first_detected or t.created_as_of).isoformat(),
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
    issues = store.issues(run_id=run_id)
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
        articles_read=run.counts.get("articles_processed", 0),
        articles_partial=run.counts.get("articles_partial", 0),
        articles_blocked=run.counts.get("articles_blocked", 0)
        + run.counts.get("articles_no_body", 0),
        themes_created=run.counts.get("theses_created", 0),
        themes_updated=run.counts.get("theses_updated", 0),
        attributions_only=run.counts.get("attributions_only", 0),
        totals_active=totals, archived_total=sum(1 for t, _ in asof.values()
                                                 if t.status is ThesisStatus.ARCHIVED),
        caveats=caveats, categories=cats, no_material_change=no_material, archive=archive,
        validation=val, generated=generated)
    d.kpi = kpis(d, store)
    return d


def kpis(d: Dashboard, store: Store) -> dict[str, Any]:
    """The KPI strip in plain words — counts that state their population."""
    from vinci.theme_intelligence.config import load_sources

    run = d.run
    manual = run["mode"] != "scan"
    names = {sc.id: sc.publisher for sc in load_sources()}
    blocked = [s for s in d.sources if s["status"] in ("BLOCKED", "ERROR")]
    accessible = [s for s in d.sources if s["status"] in ("OK", "PARTIAL")]
    # Every count below is over the theses THIS RUN created or changed (all sections, the
    # archived included) and its EVENTS: a SKIP is archived at once, so counting active theses
    # could never show one; and a thesis created and challenged in one run sits under NEW, so
    # counting sections hid the challenge (both observed in the 2026-10-10 weekly run).
    rows = [r for rs in d.categories.values() for r in rs]

    def rank(a: str) -> int:
        return ACTION_RANK[ResearchAction(a)]

    return {
        "accessible_sources": None if manual else f"{len(accessible)} of {len(d.sources)}",
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
    }


def why_action(rules: tuple[str, ...] | list[str]) -> str:
    """The deterministic rule that set the action, said plainly (the trace stays in the audit)."""
    if not rules:
        return ""
    r = rules[0]
    m = re.match(r"WATCH \(RESEARCH NOW unmet: (.*)\)$", r)
    if m:
        return "Watch — not yet Research Now: " + m.group(1)
    if r.startswith("NOW "):
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
        f'<div class="dates">Article date {e(r.article_date or "UNKNOWN")} · first detected by '
        f'the registry {e(r.first_detected or "UNKNOWN")}'
        + (" — new to the registry, not necessarily new to the market"
           if r.category == WeeklyCategory.NEW.value else "") + "</div>"
        f'<div class="k">What changed</div><ul>{li}</ul>{more}'
        f'<div class="k">Why this action</div><div>{e(r.why_action or change)}</div>'
        f'<div class="k">Exposure the source names</div><div>'
        + e("; ".join([f"sector: {x}" for x in r.sector_exposures] + names)
            or "no company or sector named")
        + '</div><div class="k">Sources (original authors)</div><ul>'
        + ("".join(f"<li>{e(x)}</li>" for x in r.sources) or "<li>—</li>") + "</ul>"
        + f'<div class="k">Next research step</div><div>{e(r.next_action)}</div>'
        + audit + "</div>")


def render_dashboard_html(d: Dashboard, *, print_mode: bool = False,
                          embedded_cards: list[str] | None = None) -> str:
    run = d.run
    parts = [f'<div class="dash"><div class="id">Theme intelligence · weekly decision brief · '
             f'run {e(run["run_id"])} · {e(run["status"])}</div><h1>What to research this week'
             f'</h1><div class="note">Research attention only — no row is a purchase or sale. '
             f'Window {e(d.window)}.</div>']
    if d.banner:
        parts.append(f'<div class="banner">{e(d.banner)}</div>')
    k = d.kpi or {}
    kp: list[tuple[str, ...]] = ([("Sources", "single article (manual URL) — no discovery")]
          if k.get("accessible_sources") is None else
          [("Accessible sources", str(k["accessible_sources"])),
           ("Blocked sources", str(k["blocked_sources"]))])
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
    parts.append('<div class="kpis">' + "".join(
        f'<div class="kpi"><span>{e(t[0])}</span><b>{e(t[1])}</b>'
        + (f"<small>{e(t[2])}</small>" if len(t) > 2 else "") + "</div>" for t in kp)
        + "</div>")
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


def render_dashboard_md(d: Dashboard) -> str:
    run = d.run
    md = [f"# What to research this week — run {run['run_id']} ({run['status']})", "",
         "_Research attention only — no row is a purchase or sale._", "",
         f"- Window: {d.window}"]
    if d.banner:
        md += ["", f"> **{d.banner}**", ""]
    k = d.kpi or {}
    md += ([("- Sources: single article (manual URL) — no source discovery")]
           if k.get("accessible_sources") is None else
           [f"- Accessible sources: {k['accessible_sources']}",
            f"- Blocked sources: {k['blocked_sources']}"])
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
                   f"- Article date {r.article_date or 'UNKNOWN'} · first detected by the registry "
                   f"{r.first_detected or 'UNKNOWN'}"
                   + (" (new to the registry, not necessarily new to the market)"
                      if r.category == WeeklyCategory.NEW.value else ""),
                   f"- Evidence direction: {r.evidence_direction}",
                   f"- Why this action: {r.why_action}", "- What changed:"]
            md += [f"  - {x}" for x in r.what_changed] or ["  - —"]
            md += ["- Sources:"] + ([f"  - {s}" for s in r.sources] or ["  - —"])
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
                "kind", "article_date", "first_detected", "evidence_direction", "what_changed",
                "sources", "sector_exposures", "named_companies", "named_instruments",
                "private_named", "other_named", "sectors", "next_action", "why_action",
                "change_reason", "last_material_update", "status", "flags", "card"])
    for cat in CATEGORY_ORDER:
        for r in d.categories.get(cat.value, []):
            w.writerow([r.category, r.action, r.previous_action or "", r.thesis_id, r.version,
                        r.title, r.kind, r.article_date or "", r.first_detected or "",
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
