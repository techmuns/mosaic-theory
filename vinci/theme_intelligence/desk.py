"""THE RESEARCH DESK — the analyst's weekly product over the registry (PR #703, the approved
research-desk design, 2026-10-13). Six screens and a thesis reading page, written beside a run's
existing outputs:

  index.html          THIS WEEK — what the week's articles produced, thesis changes by research
                      area, what needs attention
  themes.html         THEMES — every thesis by area: search, filter, sort, the archive
  articles.html       ARTICLES — the week's articles, every state told apart; one
                      `articles-<week>.html` per earlier week
  review.html         REVIEW — every unresolved finding on an active thesis, whatever week raised
                      it; resolved and historical findings kept below
  uploads.html        UPLOADS — the documents the engine could not read or hold, and the existing
                      commands that supply them
  sources.html        SOURCES — publisher health, freshness and permitted intake mode
  theses/<id>.html    the READING PAGE — seven questions answered from the stored card; the full
                      nine-section Living Thesis Card stays at cards/<id>.html (the Full record)

Everything is READ from the registry's structured records — thesis versions, priority factors,
events, contributions, completeness ledgers, documents, candidates, health checks — and nothing is
written to it: no extraction, identity, priority, budget or history changes, and no model call.
Engine ids and codes sit behind the audit switch (as on the card); the default view speaks plain
words. A long list shows a page of rows and says how many it holds ("showing 25 of 140"), the rest
one click away — never silently cut.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, NamedTuple
from urllib.parse import quote, urlparse

from vinci.theme_intelligence.cards import (
    AUDIT_TOGGLE,
    BASIS_LABEL,
    REVEAL_JS,
    ROBOTS,
    STEP_LABEL,
    THEME_CSS,
    _anchor,
    _clean_display,
    _plain_text,
    basis_line,
    card_steps,
    counted_exposures,
    distinct_sectors,
    e,
    enrichment_lines,
    enrichment_listing,
    exposure_instruments,
    exposures_of,
    foot_html,
    groups_unchecked_note,
    ids_to_audit,
    market_html,
    proposal_reading,
    proposal_step,
    review_not_run_words,
    set_card,
    topnav,
    unit_shown,
    watch_of,
    why_reasons,
)
from vinci.theme_intelligence.config import (
    STALE_AFTER_DAYS,
    load_retired_sources,
    load_sources,
    load_taxonomy,
)
from vinci.theme_intelligence.display import clip
from vinci.theme_intelligence.parse import clean_title
from vinci.theme_intelligence.priority import exposures_counted, watch_reasons_of
from vinci.theme_intelligence.report import (
    _OPEN_CAUSE,
    MANUAL_MODES,
    REVIEW_WARNINGS,
    AsOf,
    Dashboard,
    DashRow,
    build_dashboard,
    card_context,
    line_findings,
    partial_ask,
    report_runs,
    review_carry,
    source_health_as_of,
    theses_as_of_run,
    unread_documents,
)
from vinci.theme_intelligence.schemas import (
    EXPOSURE_ROLES,
    SECTION_IDS,
    AffectedCompany,
    AffectedView,
    CardContent,
    Claim,
    CompletenessReport,
    Direction,
    DocumentRecord,
    EnrichmentCandidate,
    EnrichmentSet,
    MentionRole,
    Provenance,
    ResearchAction,
    ResolutionStatus,
    RetrievalState,
    RunStatus,
    SourceHealthCheck,
    Thesis,
    ThesisStatus,
    ThesisVersion,
    WeeklyRun,
    same_area,
)
from vinci.theme_intelligence.store import Store
from vinci.theme_intelligence.timewindow import timing_of, window_of
from vinci.theme_intelligence.verify import (
    card_sentences,
    content_words,
    distinct_listings,
    overlap,
    same_company,
)

#: a short DISPLAY name per taxonomy node — the node KEY stays what it is in every record; only
#: the label a reader sees is short (the long label remains the node's definition)
AREA_NAME: dict[str, str] = {
    "macro_market": "Market-wide", "ai_infrastructure": "AI infrastructure",
    "ai_infrastructure.hyperscaler_capex": "Hyperscaler capex",
    "ai_infrastructure.compute_semis": "AI chips", "ai_infrastructure.memory": "Memory",
    "ai_infrastructure.optical_networking": "Optical & networking",
    "ai_infrastructure.power_grid": "Power & grid",
    "ai_infrastructure.datacenter_physical": "Datacenter build",
    "ai_infrastructure.materials_commodities": "AI materials",
    "ai_infrastructure.semicap_foundry": "Chip equipment & foundry", "software": "Software",
    "software.application_saas": "SaaS", "software.infrastructure": "Infrastructure software",
    "ai_adoption": "AI adoption", "ai_adoption.enterprise_margins": "Adopter margins",
    "ai_models_platforms": "AI models & platforms", "semiconductors_non_ai": "Non-AI semis",
    "consumer_electronics": "Consumer electronics",
    "electronic_components": "Electronic components", "energy": "Energy",
    "financials": "Financials", "healthcare": "Healthcare",
    "healthcare.pharma_biotech": "Pharma & biotech",
    "healthcare.life_science_tools": "Life-science tools",
    "healthcare.medtech_diagnostics": "Medtech & diagnostics",
    "healthcare.services_payers": "Health services & payers", "industrials": "Industrials",
    "consumer": "Consumer", "materials": "Materials", "real_estate": "Real estate",
    "telecom_media": "Telecom & media", "utilities": "Utilities", "other": "Unclassified"}

NEAR_GATE = "Near-term relevance (next 2–4 quarters)"
#: where a line the desk cuts is read in full
_CARD = "the Full record"
#: rows a list shows before "showing N of M — show all"
PAGE_ROWS = 25
#: the factors whose cited claims the research action counts — a review finding on a line citing
#: one of them bears on the decision (said in words; the factor id stays in the audit view)
DECISION_FACTORS = {"F2_material_evidence": "verified evidence",
                    "F5_near_term_relevance": "near-term timing",
                    "F7_dislocation_or_catalyst": "a dislocation or dated catalyst",
                    "F12_fundamental_inflection": "a near-term change in a fundamental"}
_ACTION = {"RESEARCH NOW": ("Research Now", "now"), "WATCH": ("Watch", "watch"),
           "SKIP": ("Skip", "skip")}
_RANK = {"RESEARCH NOW": 0, "WATCH": 1, "SKIP": 2}
_PROV = {Provenance.MEASURED_OBSERVATION.value: "reported", Provenance.FORECAST.value: "forecast",
         Provenance.SOURCE_OPINION.value: "source's view",
         Provenance.MODEL_INFERENCE.value: "our inference",
         Provenance.ARTICLE_FACT.value: "article fact",
         Provenance.EXTERNALLY_VERIFIED.value: "verified", Provenance.UNKNOWN.value: "unknown"}
_EPI = {"actual": "Observed", "forecast": "Forecast", "opinion": "Source's view",
        "mixed": "Observation and view", "unknown": "Type not stated"}
_RELATION = {"SIBLING": "same broader area, a different part of the chain",
             "RELATED": "the same area read the opposite way through another mechanism — "
                        "linked, not a contradiction",
             "COMPETING": "a direct contradiction — the same claim predicted the other way",
             "PARENT_CHILD": "a broader or narrower thesis on the same chain",
             "REVIEW_NEEDED": "possibly the same thesis — held for review"}
#: an article's state on the Articles screen: (words, style)
ARTICLE_STATE = {
    "FULL": ("Read in full", "ok"), "PARTIAL": ("Partial — preview only", "part"),
    "QUEUED": ("Queued — next run", "info"), "FAILED": ("Failed", "bad"),
    "BLOCKED": ("Blocked", "bad"), "NO_BODY": ("No readable text", "bad"),
    "HELD": ("Held — not analysed", "part"), "REVIEW": ("Held — match uncertain", "part"),
    "REJECTED": ("Rejected — unreadable", "bad"), "DUPLICATE": ("Duplicate — nothing new", "mute"),
    "ALREADY": ("Already held — not re-read", "mute"),
    "LOOKAHEAD": ("Published after the as-of — not read", "mute"),
    "SAME_TEXT": ("Same text as an article held", "mute")}
_TIMING_WORD = {"near_term": "inside the next four quarters",
                "current": "measured within the last quarter",
                "straddling": "runs past the next four quarters",
                "long_range": "beyond the next four quarters",
                "historical": "older than a quarter", "undated": "no readable date"}
_KIND_WORD = {"withheld": "Why it is held", "timing": "Timing", "review": "Review",
              "changed": "Not re-reviewed", "not_reviewed": "Not reviewed",
              "removed": "Not re-reviewed"}
#: where a Review item opens on the card when it has no line of its own
_KIND_ANCHOR = {"timing": "sec-s06_why_now", "not_reviewed": "top", "removed": "top"}
#: the order the week's articles are listed in on This Week: analysed, then what needs action
STATE_ORDER = {"FULL": 0, "PARTIAL": 1, "FAILED": 2, "BLOCKED": 2, "NO_BODY": 2, "HELD": 3,
               "REVIEW": 3, "REJECTED": 3, "QUEUED": 4}
_CHECKPOINT = {"BLOCKED": "BLOCKED", "NO_BODY": "NO_BODY", "FAILED": "FAILED",
               "ALREADY_INGESTED": "ALREADY", "LOOKAHEAD": "LOOKAHEAD",
               "DUPLICATE_CONTENT": "SAME_TEXT"}
_CHECKPOINT_WHY = {"BLOCKED": "the page refused automated access",
                   "NO_BODY": "the page held no readable article text",
                   "FAILED": "the fetch or the analysis failed",
                   "ALREADY": "an article this registry already holds",
                   "LOOKAHEAD": "dated after the analysis as-of",
                   "SAME_TEXT": "the same text as an article already held"}
_CONTRIB = {"new": "new evidence", "independent confirmation": "independent confirmation",
            "contradictory": "evidence against", "correction": "correction",
            "timing change": "timing change", "novelty_unverified": "new evidence",
            "repeated": "repeated evidence — no change", "no material change": "no change"}
_HEALTH = {"HEALTHY": ("Healthy", "ok"), "DEGRADED": ("Partial access", "part"),
           "BLOCKED": ("Blocked", "bad"), "ERROR": ("Error", "bad"),
           "UNKNOWN": ("Not checked", "mute")}
_TEST_HOSTS = (".test", ".example", ".invalid")
CLI = "python -m vinci.theme_intelligence"


def area_name(node: str) -> str:
    """A node's short display name — "Parent · Child" for a child node."""
    labels = {n.id: n.label for n in load_taxonomy().nodes}

    def one(n: str) -> str:
        return AREA_NAME.get(n) or re.split(r" \(|:|,", labels.get(n, n))[0].strip()

    parent = node.split(".")[0]
    return one(node) if parent == node else f"{one(parent)} · {one(node)}"


def plain(text: str) -> str:
    """A stored line as a reader sees it: system labels ⟨…⟩, "page None" and an EMPTY "(scope: )"
    dropped. The stored text is unchanged in the record."""
    return re.sub(r"\s*\(scope:\s*\)", "", _clean_display(_plain_text(text)))


def _day(x: date | datetime | None) -> str:
    if x is None:
        return "date not stated"
    d = x.date() if isinstance(x, datetime) else x
    return f"{d.day} {d:%b %Y}"


def _span(a: date, b: date) -> str:
    if a == b:
        return _day(a)
    if (a.year, a.month) == (b.year, b.month):
        return f"{a.day}–{b.day} {b:%b %Y}"
    return f"{a.day} {a:%b} – {b.day} {b:%b %Y}"


def _pl(n: int, one: str, many: str = "") -> str:
    return f"{n} {one if n == 1 else (many or one + 's')}"


def _theses(n: int, kind: str = "") -> str:
    """"1 thesis" / "3 active theses"."""
    return _pl(n, f"{kind} thesis".strip(), f"{kind} theses".strip())


def _todate(x: date | datetime | None) -> date | None:
    return x.date() if isinstance(x, datetime) else x


# --- weeks -------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Week:
    """One week of the desk: the runs whose records it reports (a weekly scan's `report_runs`;
    after the last scan, every manual run since — a week in progress), and the manual runs of
    the same span that FAILED (their articles are listed as failed, never counted read)."""
    key: str
    start: date
    end: date
    runs: tuple[WeeklyRun, ...]
    failed: tuple[WeeklyRun, ...]
    scanned: bool

    @property
    def run_ids(self) -> frozenset[str]:
        return frozenset(r.run_id for r in self.runs)

    @property
    def label(self) -> str:
        return (f"Week of {_span(self.start, self.end)}" if self.scanned else
                f"{_span(self.start, self.end)} — manual runs, no weekly scan yet")


def desk_weeks(store: Store, run: WeeklyRun) -> list[Week]:
    """Every week up to `run` (oldest first). A run rendered later never shows a later week."""
    runs = [r for r in store.runs() if r.started_at <= run.started_at and not r.ledger_only]
    scans = sorted((r for r in runs if r.mode == "scan"), key=lambda r: r.started_at)
    out: list[Week] = []
    prev: datetime | None = None
    for s in scans:
        failed = tuple(r for r in runs if r.mode in MANUAL_MODES and r.status is RunStatus.FAILED
                       and r.started_at < s.started_at
                       and (prev is None or r.started_at > prev))
        out.append(Week(key="", start=s.window_from or s.as_of, end=s.window_to or s.as_of,
                        runs=tuple(report_runs(store, s)), failed=failed, scanned=True))
        prev = s.started_at
    if run.mode != "scan":
        tail = [r for r in runs if (r.mode in MANUAL_MODES or r.run_id == run.run_id)
                and (prev is None or r.started_at > prev)]
        ok = [r for r in tail if r.status not in (RunStatus.FAILED, RunStatus.RUNNING)
              or r.run_id == run.run_id]
        if ok:
            ds = [r.as_of for r in ok]
            out.append(Week(key="", start=min(ds), end=max(ds), runs=tuple(ok),
                            failed=tuple(r for r in tail if r.status is RunStatus.FAILED
                                         and r.run_id != run.run_id), scanned=False))
    seen: Counter[str] = Counter()
    keyed: list[Week] = []
    for w in out:
        base = w.end.isoformat()
        seen[base] += 1
        keyed.append(Week(key=base if seen[base] == 1 else f"{base}-{seen[base]}", start=w.start,
                          end=w.end, runs=w.runs, failed=w.failed, scanned=w.scanned))
    return keyed


# --- articles ----------------------------------------------------------------------------------

@dataclass
class ArticleRow:
    """One article (or one document / one fetch) of a week, as the Articles screen lists it."""
    key: str
    title: str
    publisher: str
    source_id: str
    url: str
    published: date | None
    state: str
    route: str = "automatic"
    figures: int = 0
    captured: int = 0
    words: int | None = None
    open_items: list[str] = field(default_factory=list)
    alerts: list[str] = field(default_factory=list)
    #: (thesis id, what this article did to it, in words)
    produced: list[tuple[str, str]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    follow_up: str = ""
    #: where the follow-up is done (a desk page), when it is done on the desk
    follow_link: str = ""
    audit: list[str] = field(default_factory=list)
    article_id: str | None = None

    @property
    def analysed(self) -> bool:
        return self.state in ("FULL", "PARTIAL")


def _fates(rep: CompletenessReport | None) -> str:
    """Why an analysed article produced no thesis, from its mechanism-coverage record — counted,
    never guessed; the record's own words stay in the audit view."""
    cov = rep.coverage if rep else None
    if cov is None:
        return "No thesis created or changed (no coverage record for this article)."
    if not cov.propositions:
        return "No thesis: the analysis proposed none."
    n = Counter(p.fate for p in cov.propositions)
    parts = [f"{_pl(n[k], 'proposition')} {w}" for k, w in
             (("dropped", "dropped"), ("merged", "merged into another"), ("card", "on a card"))
             if n.get(k)]
    return "No thesis created or changed — " + ", ".join(parts) + "."


class _Registry:
    """The registry rows the desk reads, each read once."""

    def __init__(self, store: Store) -> None:
        self.store = store
        self.contributions = store.contributions()
        self.by_article: dict[str, list[Any]] = defaultdict(list)
        for c in self.contributions:
            self.by_article[c.article_id].append(c)
        self.documents = store.documents()
        self.sources = {s.id: s for s in load_sources()}
        self.runs = {r.run_id: r for r in store.runs()}
        self.ledgers: dict[str, list[CompletenessReport]] = {}
        self.article_cache: dict[str, Any] = {}
        self.versions_cache: dict[str, list[Any]] = {}

    def article(self, aid: str) -> Any:
        if aid not in self.article_cache:
            self.article_cache[aid] = self.store.article(aid)
        return self.article_cache[aid]

    def versions(self, aid: str) -> list[Any]:
        if aid not in self.versions_cache:
            self.versions_cache[aid] = self.store.article_versions(aid)
        return self.versions_cache[aid]

    def ledger(self, run_id: str) -> list[CompletenessReport]:
        if run_id not in self.ledgers:
            self.ledgers[run_id] = self.store.completeness_for_run(run_id)
        return self.ledgers[run_id]

    def publisher(self, sid: str) -> str:
        s = self.sources.get(sid)
        return s.publisher if s else sid


class ArticleCensus(NamedTuple):
    """A week's articles as the Articles screen lists them — EACH ARTICLE ONCE (U54: the weekly
    report's sum of the runs' counters counted an article re-analysed in the week twice, 18
    "read" of 13)."""

    read: int
    partial: int
    figures: int
    uncaptured: int


def census_of(rows: Iterable[ArticleRow]) -> ArticleCensus:
    """The census of a week's article rows: the analysed ones, their figures from each article's
    latest completeness record."""
    read = [a for a in rows if a.analysed]
    return ArticleCensus(len(read), sum(1 for a in read if a.state == "PARTIAL"),
                         sum(a.figures for a in read), sum(a.figures - a.captured for a in read))


def analysed_articles(store: Store, runs: list[WeeklyRun]) -> ArticleCensus:
    """`census_of` the articles of `runs`, for a report built without a desk."""
    if not runs:
        return ArticleCensus(0, 0, 0, 0)
    span = [r.as_of for r in runs]
    week = Week(key="", start=min(span), end=max(span), runs=tuple(runs), failed=(),
                scanned=False)
    return census_of(week_articles(_Registry(store), week, latest=False))


def week_articles(reg: _Registry, week: Week, *, latest: bool) -> list[ArticleRow]:
    """Every article of `week`: analysed in full or as a preview (with what it produced, its open
    completeness items and coverage alerts), failed, blocked, held, or — for the latest week —
    queued for the next run."""
    store = reg.store
    rids = week.run_ids
    retired = {r.id: r for r in load_retired_sources()}
    linked = {i.ref_id for i in store.issues() if i.code == "LINKED_REPORT_UPLOAD"}
    rows: dict[str, ArticleRow] = {}
    for r in week.runs:
        if r.mode in ("reassess", "enrich", "market"):  # none of these reads an article
            continue
        reps: dict[str, list[CompletenessReport]] = defaultdict(list)
        for rep in reg.ledger(r.run_id):
            av = store.article_version(rep.article_version_id)
            if av is not None:
                reps[av.article_id].append(rep)
        aids = set(reps) | {c.article_id for c in reg.contributions if c.run_id == r.run_id} | {
            str(c["ref"]) for c in store.llm_calls(r.run_id) if c.get("purpose") == "extract"}
        for aid in sorted(aids):
            a = reg.article(aid)
            if a is None:
                continue
            row = rows.get(aid)
            if row is None:
                row = rows[aid] = ArticleRow(
                    key=aid, title=clean_title(a.title, a.publisher) or "title not recorded",
                    publisher=a.publisher, source_id=a.source_id, url=a.canonical_url,
                    published=_todate(a.published_at), state="FULL", article_id=aid)
            vs = reg.versions(aid)
            order = [v.version_id for v in vs]
            mine = sorted(reps.get(aid, []), key=lambda x: order.index(x.article_version_id)
                          if x.article_version_id in order else -1)
            if mine:
                rep = mine[-1]
                last = next((v for v in vs if v.version_id == rep.article_version_id), None)
                row.state = ("FULL" if last is not None
                             and last.retrieval_state is RetrievalState.FULL else "PARTIAL")
                row.words = last.body_word_count if last is not None else None
                row.figures = len(rep.figures)
                row.captured = sum(1 for f in rep.figures if f.status != "uncaptured")
                row.open_items = (
                    [f"Figure {f.figure!r} not captured"
                     + (f" — {_OPEN_CAUSE[f.open_cause]}" if f.open_cause in _OPEN_CAUSE else "")
                     for f in rep.figures if f.status == "uncaptured"]
                    + ["One argument paragraph not accounted for"
                       + (f" — {_OPEN_CAUSE[b.open_cause]}" if b.open_cause in _OPEN_CAUSE
                          else "")
                       for b in rep.blocks if b.status == "unreviewed"])
                row.alerts = list(rep.coverage.alerts) if rep.coverage else []
                row.audit.append(f"{aid} · version {rep.article_version_id} · run {r.run_id}")
            elif vs:
                row.state = "FULL" if vs[-1].retrieval_state is RetrievalState.FULL else "PARTIAL"
            doc = next((d for d in reg.documents if d.article_id == aid and d.run_id in rids
                        and d.status in ("INGESTED", "UPGRADED")), None)
            if doc is not None:
                row.route = "linked report" if doc.declared.get("via") else "upload"
                row.audit.append(f"document {doc.doc_id}")
    for aid, row in rows.items():
        made: dict[str, str] = {}
        for c in reg.by_article.get(aid, []):
            if c.run_id not in rids:
                continue
            how = ("created" if c.version == 1 else
                   "repeated evidence — no change" if c.version is None else
                   _CONTRIB.get(c.contribution.value, c.contribution.value))
            if made.get(c.thesis_id) != "created":
                made[c.thesis_id] = how
        row.produced = list(made.items())
        if not row.produced:
            rep_last = next((x for r in week.runs for x in reg.ledger(r.run_id)
                             if (av := store.article_version(x.article_version_id))
                             and av.article_id == aid), None)
            row.notes.append(_fates(rep_last))
        if row.state == "PARTIAL" and row.source_id in retired:  # history: never asked for
            gone = retired[row.source_id]
            row.follow_up = (f"Not requested — {gone.publisher} retired "
                             f"{_day(date.fromisoformat(gone.retired))}")
        elif (row.state == "PARTIAL" and aid not in linked
              and (s := reg.sources.get(row.source_id)) is not None
              and s.paywalled_posts == "preview_only"):
            row.follow_up = "Preview only — by decision, never requested"
        elif row.state == "PARTIAL":
            row.follow_up, row.follow_link = "Supply the full report", "uploads.html"
    # manual runs that FAILED: their article listed as failed — or, when a later run of the week
    # completed it, as completed after the failed attempt(s)
    for fr in week.failed:
        for aid in sorted({str(c["ref"]) for c in store.llm_calls(fr.run_id)
                           if c.get("purpose") == "extract"}):
            err = next((w for w in fr.warnings if w.startswith("RUN ERROR")), "")
            if aid in rows:
                rows[aid].notes.append("Completed after a failed attempt (the analysis stopped "
                                       "with an error; nothing from it was recorded).")
                rows[aid].audit.append(f"failed attempt {fr.run_id}: "
                                       f"{clip(err.splitlines()[0], 160, 'the run record')}"
                                       if err else f"failed attempt {fr.run_id}")
                continue
            a = reg.article(aid)
            later = sorted({reg.runs[c.run_id].as_of for c in reg.by_article.get(aid, [])
                            if c.run_id in reg.runs
                            and reg.runs[c.run_id].started_at > fr.started_at})
            rows[aid] = ArticleRow(
                key=aid, title=clean_title(a.title, a.publisher) if a else "title not recorded",
                publisher=a.publisher if a else "publisher not recorded",
                source_id=a.source_id if a else "", url=a.canonical_url if a else "",
                published=_todate(a.published_at) if a else None, state="FAILED",
                notes=["The analysis stopped with an error; nothing from it was recorded."]
                + ([f"Completed in a later run (analysed as of {_day(later[0])})."]
                   if later else []),
                follow_up="" if later else "Re-run the article", article_id=aid,
                audit=[f"{aid} · failed run {fr.run_id}"
                       + (f": {clip(err.splitlines()[0], 160, 'the run record')}" if err else "")])
    # the weekly scan's other outcomes, url by url
    for r in week.runs:
        if r.mode != "scan":
            continue
        for url, status in r.checkpoint.items():
            state = _CHECKPOINT.get(status)
            if state is None:
                continue
            cand = store.candidate(url)
            pay = cand[1] if cand else {}
            cid = str(pay.get("article_id") or "")
            if cid and cid in rows:
                continue
            a = reg.article(cid) if cid else None
            sid = str(pay.get("source_id") or (a.source_id if a else ""))
            rows[url] = ArticleRow(
                key=url, title=(clean_title(a.title, a.publisher) if a else "")
                or str(pay.get("title") or "") or "title not recorded",
                publisher=a.publisher if a else reg.publisher(sid), source_id=sid, url=url,
                published=_todate(a.published_at) if a else None, state=state,
                notes=[_CHECKPOINT_WHY[state].capitalize() + "."],
                follow_up=("Upload a copy you hold" if state in ("BLOCKED", "NO_BODY") else
                           "Re-run in the next scan" if state == "FAILED" else ""),
                follow_link="uploads.html" if state in ("BLOCKED", "NO_BODY") else "",
                article_id=cid or None, audit=[f"scan {r.run_id}: {status}"
                                               + (f" · {cid}" if cid else "")])
    # documents supplied this week that were not analysed
    for d in reg.documents:
        if d.run_id not in rids or d.status in ("INGESTED", "UPGRADED"):
            continue
        rows[d.doc_id] = ArticleRow(
            key=d.doc_id,
            title=clean_title(d.title, d.publisher) or f"untitled document ({d.filename})",
            publisher=d.publisher, source_id=d.source_id, url=d.declared.get("url", ""),
            published=d.published, state=d.status if d.status in ARTICLE_STATE else "FAILED",
            route="upload", notes=[_doc_why(d)], follow_up="Decide on Uploads",
            follow_link="uploads.html",
            audit=[f"document {d.doc_id} · {d.status}"])
    if latest:
        for url, _st, pay in store.candidates("QUEUED"):
            sid = str(pay.get("source_id") or "")
            pub = pay.get("published")
            rows[url] = ArticleRow(
                key=url, title=clean_title(str(pay.get("title") or ""), reg.publisher(sid))
                or "title not recorded",
                publisher=reg.publisher(sid), source_id=sid, url=url,
                published=date.fromisoformat(str(pub)[:10]) if pub else None, state="QUEUED",
                notes=["Found in the window; left for the next run by the per-run article cap."],
                follow_up="Read in the next run", audit=[f"candidate QUEUED · {url}"])
    by_date = sorted(rows.values(), key=lambda x: (x.published or date.min, x.title), reverse=True)
    return sorted(by_date, key=lambda x: STATE_ORDER.get(x.state, 9))


def _doc_why(d: DocumentRecord) -> str:
    last = d.history[-1].split(": ", 1)[-1] if d.history else ""
    if d.status == "HELD":
        if last.startswith("COST:"):
            return "Held: its estimated analysis cost is above the per-document limit."
        if last.startswith("BUDGET:"):
            return "Held: the run's budget ran out before it was analysed."
        return "Held: its licence is not confirmed for third-party model processing."
    if d.status == "REVIEW":
        return "Held: it resembles an article already held — which one it is needs your call."
    if d.status == "DUPLICATE":
        return "The same document (or the same text) as one already held — nothing added."
    if d.status == "REJECTED":
        return "Rejected: no readable text."
    return f"Not imported ({d.status.lower()})."


# --- the near-term reading of record -----------------------------------------------------------

@dataclass(frozen=True)
class TimedClaim:
    claim: Claim
    timing: str  # near_term | current | straddling | long_range | historical | undated
    note: str
    basis: str  # where its date comes from, in words


@dataclass(frozen=True)
class NearTerm:
    """The near-term factor of record beside the source's own horizon framing — two different
    things, never one pass/fail. `recomputed` re-times the factor's OWN cited claims today; a
    value that differs from the one of record is a conflict for review (the research action of
    record stands until a reassessment)."""
    stored: str
    framing: str
    claims: tuple[TimedClaim, ...]
    recomputed: str
    note: str

    @property
    def conflict(self) -> bool:
        return self.recomputed != self.stored


def _value_of(timings: Iterable[str]) -> str:
    ts = set(timings)
    return ("yes" if ts & {"near_term", "current"} else "runs_past" if "straddling" in ts else
            "longer_term_only" if "long_range" in ts else "not shown")


def near_term_reading(store: Store, v: ThesisVersion) -> NearTerm:
    f5 = next((f for f in v.priority.factors if f.factor_id == "F5_near_term_relevance"), None)
    stored = f5.value if f5 else "not shown"
    pub = {s.article_id: s.published_at.date() for s in v.content.s09_sources if s.published_at}
    out: list[TimedClaim] = []
    missing = False
    for cid in (f5.claim_ids if f5 else ()):
        c = store.claim(cid)
        if c is None:
            missing = True
            continue
        if c.article_id not in pub:
            a = store.article(c.article_id)
            if a is not None and a.published_at:
                pub[c.article_id] = a.published_at.date()
        cls, note = timing_of(c, v.as_of, pub.get(c.article_id))
        w = window_of(c.period, v.as_of)
        basis = ("its stated measurement date" if c.measured_as_of else
                 "the period it states" if cls in ("near_term", "straddling", "long_range") else
                 "the article's publication date — a change since a date runs to the source's "
                 "own date" if w is not None and w.to_date else
                 "the end of the period it states" if w is not None and w.end <= v.as_of else
                 "the article's publication date — the source states no measurement date")
        out.append(TimedClaim(c, cls, note, basis))
    recomputed = "claims missing" if missing else _value_of(t.timing for t in out)
    return NearTerm(stored=stored, framing=v.content.header.horizon, claims=tuple(out),
                    recomputed=recomputed, note=f5.note if f5 else "")


def near_term_words(nt: NearTerm) -> tuple[bool, str]:
    """(met?, the near-term condition in words) — one statement per thesis."""
    if nt.conflict:
        return False, ("Review required — the near-term reading of record does not match its own "
                       "cited claims re-dated today; the research action of record stands until "
                       "the thesis is reassessed")
    kinds = Counter(t.timing for t in nt.claims)
    if nt.stored == "yes":
        parts = []
        if kinds.get("near_term"):
            parts.append(f"{_pl(kinds['near_term'], 'dated window')} inside the next four quarters")
        if kinds.get("current"):
            parts.append(f"{_pl(kinds['current'], 'measured observation')} dated within the last "
                         f"quarter")
        pub_dated = sum(1 for t in nt.claims if t.timing == "current"
                        and t.basis.startswith("the article's publication date"))
        return True, ("; ".join(parts) + (
            f" ({pub_dated} dated only by the article's publication date — the source states no "
            f"measurement date)" if pub_dated else ""))
    if nt.stored == "runs_past":
        return False, (f"its dated figures run past the next four quarters "
                       f"({_pl(len(nt.claims), 'claim')}) — a full-year figure for next year is "
                       f"not a 2–4-quarter window")
    if nt.stored == "longer_term_only":
        return False, "longer-term only — no dated window inside the next 2–4 quarters"
    return False, "no dated window anywhere in the evidence — timing unknown"


# --- why the research action -------------------------------------------------------------------

@dataclass(frozen=True)
class Gate:
    ok: bool
    name: str
    detail: str


def gates(v: ThesisVersion, groups: list[str], nt: NearTerm, *,
          groups_unread: int = 0) -> list[Gate]:
    """The Research Now conditions, each met or not, read from the stored factor VALUES (the rule
    trace stays in the audit view). The near-term condition is stated ONCE, from the factor of
    record — the source's horizon framing is shown apart and is never a pass/fail."""
    f = {x.factor_id: x.value for x in v.priority.factors}
    av = v.content.s05_affected
    n = f.get("F2_material_evidence", "0")
    f4 = f.get("F4_profit_transmission", "absent")
    near_ok, near_words = near_term_words(nt)
    exposed = exposures_counted(v.priority) > 0  # what the stored RULE counted (its F6 value)
    counted = counted_exposures(av)
    unverified = next((r for r in watch_reasons_of(v.priority, counted.unverified)
                       if r.code == "listing_unverified"), None)
    f12 = f.get("F12_fundamental_inflection", "")
    cat = f.get("F7_dislocation_or_catalyst") == "present" or f12 == "qualifies"
    out = [
        Gate(n not in ("0", ""), "Verified evidence",
             _pl(int(n) if n.isdigit() else 0, "verified figure or event",
                 "verified figures or events")
             if n not in ("0", "") else "no verified figure or event"),
        Gate(f4 != "absent", "A stated route to profits",
             {"source-shown": "the source states how it reaches earnings",
              "inferred": "inferred — the source does not state the earnings step"}.get(
                 f4, "a market-regime record — no earnings mechanism argued"
                 if f4.startswith("n/a") else "no earnings step (a price move is not one)")),
        Gate(near_ok, NEAR_GATE, near_words),
        Gate(exposed, "An exposure the source names",
             "; ".join(x for x in (
                 "listed companies: " + ", ".join(f"{n} ({tk})" for n, tk in counted.listed)
                 if counted.listed else "",
                 "ETFs, indices or baskets: " + ", ".join(counted.instruments)
                 if counted.instruments else "",
                 "sectors: " + ", ".join(s.name for s in distinct_sectors(av))
                 if av.sector_exposures else "") if x)
             if exposed else (unverified.text.removeprefix("no source-named exposure counted — ")
                              if unverified is not None else
                              "business groups only (" + "; ".join(groups) + ") — not companies"
                              if groups else "no company or sector named; whether the source "
                              "names business groups is not checkable on this machine (the "
                              "article text is not held here)" if groups_unread else
                              "no company or sector named as exposed")),
        Gate(cat, "A recent mispricing, a dated catalyst or a measured change",
             "present" if cat else {"not credible": "a forecast without a corroborating "
                                                     "measurement",
                                    "incomplete": "no stated step from the change to profits"}
             .get(f12, "none verified")),
        Gate(f.get("F9_premise_in_source", "asserted") == "asserted", "The source asserts it",
             "asserted" if f.get("F9_premise_in_source", "asserted") == "asserted" else
             f"{f['F9_premise_in_source'].replace('_', ' ')} in the source"),
        Gate(f.get("F11_retrieval", "FULL") == "FULL", "The whole text was read",
             "full text" if f.get("F11_retrieval", "FULL") == "FULL" else "only part was read"),
        Gate(f.get("F10_verification_hold") != "HOLD", "No verification hold",
             "clear" if f.get("F10_verification_hold") != "HOLD" else
             "on hold until a failed check is resolved"),
        Gate(f.get("F1_source_reliability") != "low", "Source reliability",
             f.get("F1_source_reliability", "not stated")),
    ]
    action = v.priority.research_action.value
    if action == "WATCH" and all(g.ok for g in out):
        out.append(Gate(False, "Not outweighed by counter-evidence",
                        "the decision trace records the counter-evidence as outweighing the "
                        "support (audit view)"))
    return out


# --- review findings ---------------------------------------------------------------------------

@dataclass
class Finding:
    """One review finding on a card line — or a near-term timing conflict — with its age."""
    thesis_id: str
    title: str
    action: str
    area: str
    sid: str
    line: str
    said: str
    kind: str  # withheld | review | timing
    decision: str  # why it bears on the research action ("" when it does not)
    raised: date
    raised_version: int
    audit: str = ""
    history: str = ""  # for a finding no longer open: why it is history


def decision_claims(v: ThesisVersion) -> dict[str, str]:
    out: dict[str, str] = {}
    for f in v.priority.factors:
        for cid in (f.claim_ids if f.factor_id in DECISION_FACTORS else ()):
            out.setdefault(cid, DECISION_FACTORS[f.factor_id])
    return out


def _first_raised(store: Store, tid: str, versions: list[ThesisVersion], text: str,
                  said: str) -> ThesisVersion | None:
    for ev in versions:  # oldest first: the version whose review first made this finding
        if text not in {t for t, _p, _c in card_sentences(ev.content).values()}:
            continue
        if any(i.scope == "card_sentence" and i.code in REVIEW_WARNINGS
               and i.ref_id.startswith(tid + ":") and said in i.detail
               for i in store.issues(run_id=ev.run_id)):
            return ev
    return None


def thesis_findings(store: Store, t: Thesis, v: ThesisVersion, *, area: str,
                    nt: NearTerm | None = None) -> tuple[list[Finding], list[Finding]]:
    """(open, history) findings of one thesis's version: the lines withheld or questioned
    (report.line_findings — the card's own reading, earlier findings included when this version
    was not reviewed), a version the card review never read, a near-term timing conflict; and, as
    history, findings a later version resolved, analyst corrections, and findings on lines no
    longer on the card."""
    blocked, flagged, corrected, resolved = line_findings(store, t.thesis_id, v)
    carry = review_carry(store, t.thesis_id, v)
    sents = card_sentences(v.content)
    versions = [x for x in store.thesis_versions(t.thesis_id) if x.version <= v.version]
    decisive = decision_claims(v)
    action = v.priority.research_action.value
    base = {"thesis_id": t.thesis_id, "title": t.title, "action": action, "area": area}
    opened: list[Finding] = []
    for sid, (text, _prov, cids) in sents.items():
        cf = carry.carried.get(sid)  # an earlier version's finding: its own date and version
        since = (f" Not re-reviewed since version {cf.origin_version}." if cf else "")
        if sid in blocked:
            opened.append(Finding(**base, sid=sid, line=plain(text), kind="withheld",
                                  said="Withheld from the card — the line failed source "
                                       "verification." + since,
                                  decision="a withheld line is never evidence until it is "
                                           "verified",
                                  raised=cf.origin_as_of if cf else v.as_of,
                                  raised_version=cf.origin_version if cf else v.version,
                                  audit=blocked[sid]))
        elif sid in flagged:
            first = ((cf.origin_as_of, cf.origin_version) if cf else next(
                ((x.as_of, x.version) for x in [_first_raised(
                    store, t.thesis_id, versions, text, flagged[sid])] if x is not None),
                (v.as_of, v.version)))
            hit = sorted({decisive[c] for c in cids if c in decisive})
            opened.append(Finding(**base, sid=sid, line=plain(text),
                                  kind="changed" if cf and cf.changed else "review",
                                  said=flagged[sid] + (
                                      f" (said of the line when it read “{plain(cf.origin_text)}”;"
                                      f" changed since, not re-reviewed)" if cf and cf.changed
                                      else since),
                                  decision=("the line restates evidence the research action "
                                            "counts (" + ", ".join(hit) + ")") if hit else "",
                                  raised=first[0], raised_version=first[1],
                                  audit=f"{t.thesis_id}:{sid} · " + ", ".join(cids)))
    if carry.not_run is not None:
        opened.append(Finding(
            **base, sid="", line=f"Version {v.version} was not reviewed", kind="not_reviewed",
            said=(f"The card review did not run for this version: "
                  f"{review_not_run_words(carry.not_run)}. A skipped review is never a clean "
                  f"one; earlier findings stay open until a review runs."),
            decision="", raised=v.as_of, raised_version=v.version, audit=carry.not_run))
    for f in carry.removed:
        opened.append(Finding(
            **base, sid="", line=plain(f.origin_text), kind="removed",
            said=f"{f.said} (the line was removed by a version the review never read — not "
                 f"re-reviewed, not resolved)", decision="", raised=f.origin_as_of,
            raised_version=f.origin_version, audit=f.detail))
    nt = nt or near_term_reading(store, v)
    if nt.conflict:
        opened.append(Finding(
            **base, sid="", line="Near-term relevance", kind="timing",
            said=(f"The factor of record reads “{nt.stored.replace('_', ' ')}”; its own cited "
                  f"claims, re-dated today, read “{nt.recomputed.replace('_', ' ')}”."),
            decision="near-term relevance is a Research Now condition", raised=v.as_of,
            raised_version=v.version, audit=f"F5 {nt.stored} · re-timed {nt.recomputed}"))
    hist: list[Finding] = []
    for sid, (why, said) in resolved.items():
        hist.append(Finding(**base, sid=sid, line=plain(sents[sid][0]), kind="review", said=said,
                            decision="", raised=v.as_of, raised_version=v.version,
                            history=f"Resolved — {why}."))
    for sid, why in corrected.items():
        hist.append(Finding(**base, sid=sid, line=plain(sents[sid][0]), kind="review",
                            said=why, decision="", raised=v.as_of, raised_version=v.version,
                            history="Corrected by the analyst."))
    now = {txt for txt, _p, _c in sents.values()}
    seen: set[tuple[str, str]] = set()
    still = {f.said for f in (*carry.carried.values(), *carry.removed)}  # open, never history
    for ev in versions[:-1]:
        _b, fl, _c, _r = line_findings(store, t.thesis_id, ev)
        old = card_sentences(ev.content)
        for sid, said in fl.items():
            text = old[sid][0]
            if text in now or (text, said) in seen or said in still:
                continue
            seen.add((text, said))
            hist.append(Finding(**base, sid="", line=plain(text), kind="review", said=said,
                                decision="", raised=ev.as_of, raised_version=ev.version,
                                history=f"Raised on version {ev.version}; the line is no longer "
                                        f"on the card (version {v.version})."))
    return opened, hist


def review_order(f: Finding) -> tuple[int, int, date, str]:
    """Decision-affecting first, then Research Now, then the oldest."""
    return (0 if f.decision else 1, _RANK.get(f.action, 3), f.raised, f.title)


# --- uploads -----------------------------------------------------------------------------------

@dataclass
class UploadItem:
    kind: str  # full_report | blocked_article | channel | held | review | visual | rejected | done
    title: str
    publisher: str
    source_id: str
    published: date | None
    first_seen: date | None
    why: str
    command: str
    url: str = ""
    detail: list[str] = field(default_factory=list)
    #: theses the document produced (completed imports) — linked by title, never by id
    theses: list[str] = field(default_factory=list)
    audit: str = ""
    #: a channel's articles to supply: (url, title as listed, what is already held of it)
    links: list[tuple[str, str, str]] = field(default_factory=list)
    #: a channel whose articles the scan cannot list: its research pages, to look there by hand
    where: list[str] = field(default_factory=list)


def _ingest_cmd(sid: str, url: str = "") -> str:
    return (f"{CLI} ingest-file --path <your copy> --source {sid}"
            + (f" --url {url}" if url else "") + " --llm-permitted")


def upload_items(reg: _Registry, health: dict[str, Any],
                 checkpoints: list[tuple[str, str, date]]) -> list[UploadItem]:
    """Everything the operator can supply or clear, registry-wide — never dismissed by age. A
    RETIRED channel's records are history only: nothing of it is ever asked for (as the weekly
    report's intake, `report.research_intake`)."""
    store = reg.store
    out: list[UploadItem] = []
    retired = {r.id for r in load_retired_sources()}
    upload_issue = {i.ref_id: i.detail for i in store.issues()
                    if i.code == "LINKED_REPORT_UPLOAD"}
    unread = unread_documents(reg.documents, retired)
    for a in store.articles():
        # the ONE partial-awaiting-full rule, shared with the weekly report's intake (U56)
        ask = partial_ask(a, reg.versions(a.article_id), unread=unread.get(a.article_id),
                          source=reg.sources.get(a.source_id),
                          linked_upload=a.article_id in upload_issue, retired=retired)
        if ask is None:
            continue
        kind, latest = ask
        if kind == "visual":
            doc = unread[a.article_id]
            pages = sorted(q.page for q in doc.quarantined)
            out.append(UploadItem(
                kind="visual", title=clean_title(a.title, a.publisher) or "title not recorded",
                publisher=a.publisher, source_id=a.source_id, published=_todate(a.published_at),
                first_seen=_todate(a.first_seen_at),
                why=(f"{_pl(len(pages), 'page')} of the supplied document could not be read "
                     f"(undecodable font glyphs) — a visual check, not a missing document"),
                command="Open the original and read the listed pages; OCR is not available here",
                detail=[f"pages {', '.join(str(p) for p in pages)}"],
                audit=f"{a.article_id} · document {doc.doc_id}"))
            continue
        why = ("the page links a fuller report that needs an authorised copy"
               if a.article_id in upload_issue else
               f"only a preview could be read ({latest.body_word_count:,} words)")
        out.append(UploadItem(
            kind="full_report", title=clean_title(a.title, a.publisher) or "title not recorded",
            publisher=a.publisher, source_id=a.source_id, published=_todate(a.published_at),
            first_seen=_todate(a.first_seen_at), why=why,
            command=_ingest_cmd(a.source_id, a.canonical_url), url=a.canonical_url,
            audit=a.article_id + (f" · {clip(upload_issue[a.article_id], 200, 'Review')}"
                                  if a.article_id in upload_issue else "")))
    done_urls = {a.canonical_url for a in store.articles()
                 if any(v.retrieval_state in (RetrievalState.FULL, RetrievalState.PARTIAL)
                        for v in reg.versions(a.article_id))}
    seen_urls: set[str] = set()
    for url, status, seen in checkpoints:
        if url in done_urls or url in seen_urls or status not in ("BLOCKED", "NO_BODY"):
            continue
        seen_urls.add(url)
        cand = store.candidate(url)
        pay = cand[1] if cand else {}
        sid = str(pay.get("source_id") or "")
        if sid in retired:
            continue
        cid = str(pay.get("article_id") or "")
        art = reg.article(cid) if cid else None
        out.append(UploadItem(
            kind="blocked_article",
            title=(clean_title(art.title, art.publisher) if art else "")
            or clean_title(str(pay.get("title") or ""), reg.publisher(sid)) or "title not recorded",
            publisher=art.publisher if art else reg.publisher(sid),
            source_id=sid, published=_todate(art.published_at) if art else None,
            first_seen=seen, why=_CHECKPOINT_WHY[_CHECKPOINT[status]],
            command=_ingest_cmd(sid or "<source>", url), url=url,
            audit=f"scan outcome {status}" + (f" · {cid}" if cid else "")))
    from vinci.theme_intelligence.health import asks_only_for_previews, split_affected

    rows = {r["source_id"]: r for r in health.get("rows", [])}
    supplied = {d.declared.get("url", ""): d.status for d in reg.documents
                if d.declared.get("url")}
    for sid, src in reg.sources.items():
        row = rows.get(sid, {})
        ma = row.get("manual_action") or {}
        manual_first = src.mode == "manual_first"
        if not manual_first and ma.get("kind") != "UPLOAD_REQUIRED":
            continue
        if asks_only_for_previews(src, row):
            continue
        links: list[tuple[str, str, str]] = []
        rest: list[str] = []
        for line in (str(x) for x in ma.get("affected", [])):
            at, title = split_affected(line)
            if at is None:
                if not line.startswith("unknown"):  # "… and N more" keeps its count
                    rest.append(line)
                continue
            held = store.article_by_url(at)
            vs = reg.versions(held.article_id) if held else []
            state = vs[-1].retrieval_state if vs else None
            links.append((at, title, _HELD_WORDS.get(supplied.get(at, ""), "")
                          or ("already read in full" if state is RetrievalState.FULL else
                              "a preview is held — see Full report needed"
                              if state is RetrievalState.PARTIAL else "")))
        if not manual_first and links and not rest and all(note for _u, _t, note in links):
            # every article the check listed is already supplied, held or read: nothing is left
            # to ask until the next check finds more (a held copy stays under Held documents)
            continue
        out.append(UploadItem(
            kind="channel", title=f"New research from {src.publisher}", publisher=src.publisher,
            source_id=sid, published=None, first_seen=None,
            why=("a manual-first channel — the weekly scan does not read it; upload any new "
                 "report you hold" if manual_first else
                 f"automated access is {str(row.get('status', 'UNKNOWN')).lower()} — upload "
                 f"the reports you hold, starting with the articles listed"),
            command=_ingest_cmd(sid), detail=rest, links=links,
            where=[src.entry_url, *src.research_pages] if not links else [],
            audit=f"health {row.get('status', 'UNKNOWN')}"
            + (f" · {clip(row.get('reason', ''), 160, 'Sources')}" if row else "")))
    for d in reg.documents:
        if d.source_id in retired:
            continue
        last = d.history[-1].split(": ", 1)[-1] if d.history else ""
        if d.status == "HELD":
            licence = not last.startswith(("COST:", "BUDGET:"))
            out.append(_doc_item(
                d, "held", _doc_why(d),
                f"{CLI} ingest-file --release {d.doc_id} --llm-permitted" if licence
                else f"{CLI} ingest-file --release {d.doc_id} --max-cost <USD> --llm-permitted",
                detail=[plain(last)] if last and not licence else [],
                audit=f"document {d.doc_id} · {d.filename}"))
        elif d.status == "REVIEW":
            like = reg.article(d.article_id) if d.article_id else None
            aid = d.article_id or "<article id>"
            out.append(_doc_item(
                d, "review", _doc_why(d),
                f"{CLI} ingest-file --release {d.doc_id} --same-as {aid}   (or --as-new, or "
                f"--duplicate-of {aid})",
                detail=[f"resembles “{clean_title(like.title, like.publisher)}” ({like.publisher})"]
                if like else [], audit=f"document {d.doc_id} · "
                f"{clip(d.match_basis, 160, 'the document record')}"))
        elif d.status in ("REJECTED", "FAILED"):
            out.append(_doc_item(d, "rejected", _doc_why(d),
                                 "Save it as PDF or text with a readable text layer, then "
                                 "import it again",
                                 audit=f"document {d.doc_id} · "
                                       f"{clip(plain(last), 160, 'the document record')}"))
        elif d.status in ("INGESTED", "UPGRADED"):
            made = sorted({c.thesis_id for c in reg.by_article.get(d.article_id or "", [])
                           if c.run_id == d.run_id})
            out.append(_doc_item(
                d, "done", "a fuller copy of an article already held — the same article, "
                           "re-checked" if d.status == "UPGRADED" else "imported as a new article",
                "", theses=made, audit=f"document {d.doc_id} · {d.article_id or ''}"))
    return out


#: what a supplied document's status says about the article it was supplied for
_HELD_WORDS = {"HELD": "supplied — held until you confirm its licence",
               "REVIEW": "supplied — waiting for your match decision",
               "INGESTED": "supplied and analysed", "UPGRADED": "supplied and analysed",
               "DUPLICATE": "supplied — the same text as already held",
               "REJECTED": "supplied but unreadable", "FAILED": "supplied — analysis failed"}


def _doc_item(d: DocumentRecord, kind: str, why: str, command: str, *,
              detail: list[str] | None = None, theses: list[str] | None = None,
              audit: str = "") -> UploadItem:
    return UploadItem(kind=kind, title=clean_title(d.title, d.publisher)
                      or f"untitled document ({d.filename})",
                      publisher=d.publisher, source_id=d.source_id, published=d.published,
                      first_seen=d.received_at.date(), why=why, command=command,
                      url=d.declared.get("url", ""), detail=detail or [], theses=theses or [],
                      audit=audit)


# --- the desk ----------------------------------------------------------------------------------

def _chip(action: str, watch: str = "") -> str:
    """The action pill — a WATCH with what it waits for: "Watch · needs data" when only missing
    data holds it, "Watch · on hold" when the evidence itself falls short (priority.watch_label)."""
    w, cls = _ACTION.get(action, (action.title(), "skip"))
    return f'<span class="pill {cls}">{e(w + (f" · {watch}" if watch else ""))}</span>'


def _state(state: str) -> str:
    w, cls = ARTICLE_STATE.get(state, (state.title(), "mute"))
    return f'<span class="st {cls}">{e(w)}</span>'


def _tag(prov: str) -> str:
    w = _PROV.get(prov, prov.lower())
    return f'<span class="tag">{e(w)}</span>' if prov else ""


def _event(x: str) -> str:
    word = {"Updated": "New evidence"}.get(x, x)
    cls = ("down" if x.startswith(("Downgraded", "Challenged")) else
           "up" if x.startswith("Upgraded") else "new" if x == "New" else "")
    word = word.replace("Downgraded: ", "↓ ").replace("Upgraded: ", "↑ ")
    return f'<span class="ev {cls}">{e(word)}</span>'


def capped(items: list[str], what: str, cap: int = PAGE_ROWS) -> str:
    """A list longer than `cap` shows its first `cap` and SAYS SO; the rest is one click away."""
    if len(items) <= cap:
        return "".join(items)
    return ("".join(items[:cap]) + f'<details class="more-rows"><summary>Showing {cap} of '
            f'{len(items)} {e(what)} — show all {len(items)}</summary>' + "".join(items[cap:])
            + "</details>")


def capped_li(items: list[str], what: str, cls: str = "", cap: int = PAGE_ROWS) -> str:
    """`capped` for list items — the rest sit in a list inside the last item."""
    if len(items) <= cap:
        return "".join(items)
    return ("".join(items[:cap]) + f'<li class="morewrap"><details class="more-rows"><summary>'
            f'Showing {cap} of {len(items)} {e(what)} — show all {len(items)}</summary>'
            f'<ul class="{cls}">' + "".join(items[cap:]) + "</ul></details></li>")


def _strip(weeks: list[Week], active: set[str]) -> str:
    return ('<span class="act" title="weeks with new evidence, oldest to newest">' + "".join(
        f'<i class="{"on" if w.key in active else ""}"></i>' for w in weeks) + "</span>")


#: article states whose badge says all there is to say — no per-row note repeats it
_SELF_EXPLAINED = frozenset({"QUEUED"})
_SCOPE = re.compile(r"\s*\((scope:\s*[^()]*(?:\([^()]*\)[^()]*)*)\)\s*$")


def split_scope(text: str) -> tuple[str, str]:
    """(the line, its trailing "(scope: …)" note) — the reading page shows the line and keeps the
    note in the audit view; the full record prints both."""
    m = _SCOPE.search(text)
    return (text[:m.start()], m.group(1)) if m else (text, "")


def figure_label(store: Store, claim_id: str, label: str) -> str:
    """A figure's label as the reading page shows it: a metric that already names its scope
    ("observability software prices change" under "observability software") is not repeated after
    it. Read from the claim's structured scope and metric, never by re-parsing the sealed label —
    which the Full record still prints as sealed."""
    c = store.claim(claim_id)
    if c is not None and c.scope and c.metric and c.scope.casefold() in c.metric.casefold():
        return c.metric
    return label


#: a health test that did not pass, in plain words (the test's own detail stays one fold away)
def _health_line(h: SourceHealthCheck | None) -> str:
    """One plain line for a channel's latest check (`health.plain_line`, shared with the weekly
    report)."""
    from vinci.theme_intelligence.health import plain_line

    return plain_line(h)


#: a named company's ROLE in words, where the source states no direction for it
_ROLE_WORD = {"sector_example": "named as an example of the sector", "disruptor": "a disruptor",
              "spending_customer": "a customer / spender", "supplier": "a supplier",
              "investor": "an investor", "recommendation": "the source recommends it",
              "potential_beneficiary": "could benefit", "potentially_harmed": "could be hurt",
              "market_instrument": "the ETF / index the source names for it",
              "cited_basket": "a basket the source cites"}


def _lean(direction: Direction, role: MentionRole) -> str:
    """up / down / flat — the thesis's reading of a name, else the role the source states."""
    if direction is Direction.POSITIVE or (direction is not Direction.NEGATIVE
                                           and role is MentionRole.POTENTIAL_BENEFICIARY):
        return "up"
    if direction is Direction.NEGATIVE or role is MentionRole.POTENTIALLY_HARMED:
        return "down"
    return "flat"


def _where(c: AffectedCompany) -> str:
    """Where a named company trades — or why no listing is shown."""
    if c.listings:
        return ", ".join(dict.fromkeys(x.ticker for x in c.listings))
    if c.resolution_status is ResolutionStatus.PRIVATE:
        return "private"
    if c.resolution_status in (ResolutionStatus.FUND, ResolutionStatus.INDEX):
        return c.resolution_status.value.lower()
    if c.resolution_status is ResolutionStatus.NOT_A_SECURITY:  # a cited basket
        return "not a security"
    unver = [x.ticker for x in c.other_securities]
    return (f"{', '.join(unver)} — listing not verified" if unver
            else "no verified US listing")


def exposure_html(av: AffectedView, groups: list[str], groups_unread: int,
                  enrichment: EnrichmentSet | None = None, version: int = 0,
                  steps: dict[str, str] | None = None,
                  set_card: CardContent | None = None) -> str:
    """Who is exposed, as a fund reads it: who could BENEFIT, who could be HURT, and who the
    source names without a direction — companies (listed or not) and sectors together, each with
    its listing or why it has none. Only names in an exposure role (the priority rules' own set,
    `exposures_of`); the publisher, data sources and context are counted apart. A company the
    source does not name is never added."""
    exp, named = exposures_of(av)
    inst = exposure_instruments(av)  # the ETFs / indices / baskets the count takes
    others = [c for c in av.private_or_unlisted if c.role in EXPOSURE_ROLES] + inst
    rest = named + [c for c in av.private_or_unlisted if c.role not in EXPOSURE_ROLES] + [
        c for c in av.instruments if c not in inst] + list(av.also_named)
    buckets: dict[str, list[str]] = {"up": [], "down": [], "flat": []}
    seen: dict[str, list[AffectedCompany]] = {"up": [], "down": [], "flat": []}
    for c in [*exp, *others]:
        side = _lean(c.direction, c.role)
        # one name spelt two ways in one article ("Zhipu Z.ai", "Zhipu (Z.ai)") is listed once —
        # by the enrichment's own rule (U60a), never two companies the SEC verified apart
        if any(same_company(c.name_as_written, s.name_as_written)
               and not distinct_listings(c.listings, s.listings) for s in seen[side]):
            continue
        seen[side].append(c)
        role = ("" if side != "flat"
                else _ROLE_WORD.get(c.role.value, c.role.value.replace("_", " ")))
        buckets[side].append(
            f'<li><b>{e(c.name_as_written)}</b> <span class="tk">{e(_where(c))}</span>'
            + (f' <span class="muted">{e(role)}</span>' if role else "")
            + (f'<div class="small">{e(c.role_detail)}</div>' if c.role_detail else "")
            + "</li>")
    for x in distinct_sectors(av):
        side = {Direction.POSITIVE: "up", Direction.NEGATIVE: "down"}.get(x.direction, "flat")
        kind = ("" if re.search(r"\b(?:sectors?|industr(?:y|ies))$", x.name, re.I)
                else ' <span class="tk">sector</span>')
        buckets[side].append(f'<li><b>{e(x.name)}</b>{kind} {_tag(x.provenance.value)}</li>')
    heads = {"up": "Could benefit", "down": "Could be hurt",
             "flat": "Named as exposed — direction not stated"}
    out = "".join(f'<h3>{heads[k]}</h3><ul class="who">'
                  f'{capped_li(v, "names", "who", cap=6)}</ul>' for k, v in buckets.items() if v)
    if not out:
        out = ('<p class="muted">The source names no company or sector as exposed. A company '
               'the source does not name is never added.</p>')
    elif not any(c.listings for c in exp):
        out += ('<p class="small">No US-listed company is named as exposed. A company the source '
                'does not name is never added.</p>')
    out += _hypotheses_html(enrichment, version, steps or {}, set_card)
    if groups or groups_unread:
        out += ('<p class="small"><b>Business groups the source names:</b> '
                + (f'{e("; ".join(groups))} — groups, not companies' if groups else "")
                + (f' {e(groups_unchecked_note(groups_unread))}' if groups_unread else "")
                + "</p>")
    if rest:
        shown = [f"{c.name_as_written} ({c.role.value.replace('_', ' ')})" for c in rest[:4]]
        out += (f'<p class="small muted">Also named, not exposures: {e(", ".join(shown))}'
                + (f" — showing 4 of {len(rest)}; all in the full record" if len(rest) > 4
                   else "") + "</p>")
    return f'<div class="expo">{out}</div>'


def _merge_restated(rows: list[tuple[str, dict[str, Any]]]) -> list[tuple[str, dict[str, Any]]]:
    """One Evidence line per figure an article states twice: the same value and unit, on the same
    side of the thesis, periods that do not disagree, labels sharing at least half their content
    words (the healthcare-consumerism article gave "36%" and "$413" twice each, 2026-10-14).
    Every claim and quote stays on the merged line; a different period or measure never merges."""
    def side(x: dict[str, Any]) -> str:
        return ("against" if x["role"] == "against" else
                "support" if x["role"] in ("key evidence", "supports") else "other")

    out: list[tuple[str, dict[str, Any]]] = []
    for aid, x in rows:
        x = {**x, "quotes": [x["quote"]], "ids": [x["id"]]}
        if x["period"] and x["period"].lower() in (x["u"] or "").lower():
            x["period"] = None  # "per year" beside the unit "per year" is the unit, not a period
        words = content_words(x["label"])
        twin = next((y for a2, y in out if a2 == aid and x["v"] and y["v"] == x["v"]
                     and y["u"] == x["u"] and side(y) == side(x)
                     and not (x["period"] and y["period"] and x["period"] != y["period"])
                     and max(overlap(words, content_words(y["label"])),
                             overlap(content_words(y["label"]), words)) >= 0.5), None)
        if twin is None:
            out.append((aid, x))
            continue
        twin["quotes"].append(x["quote"])
        twin["ids"].append(x["id"])
        twin["period"] = twin["period"] or x["period"]
    return out


def _hypotheses_html(es: EnrichmentSet | None, version: int, steps: dict[str, str],
                     card: CardContent | None = None) -> str:
    """The companies the thesis's own steps imply (enrich.py) — OUR hypotheses, boxed apart from
    what the source names, each with its SEC-verified ticker or "not verified", the step it
    rests on and how. A direction resting on a step that is not a fact is shown as the
    condition it is, under "Exposed" — never under "Could be hurt" (2026-10-15). The basis the
    model stated sits beside it with what the company's own annual report says, and that
    report's sentence on demand. `card`: the card version the set was proposed from. Nothing
    when no set was proposed."""
    if es is None:
        return ""
    head, _rows = enrichment_lines(es, version, steps, card)
    # ONE ROW PER COMPANY, grouped under the step it rests on: the step — and so its condition —
    # is said once per group, never once per company (2026-10-15: eight companies repeated two
    # step sentences eight times; the box ran to ~1,100 words). A row opens to its rationale,
    # the basis and the company's own 10-K sentence.
    by_step: dict[str, list[EnrichmentCandidate]] = {}
    for x in es.candidates:
        by_step.setdefault(x.step_id, []).append(x)
    body = ""
    for sid, xs in by_step.items():
        cond, _how = proposal_reading(xs[0], steps, card)
        text, label = proposal_step(xs[0], card)
        support = _PROV.get(label.value, label.value.lower()) if label else "support not recorded"
        lead = ("If this holds" if cond
                else f"Through {STEP_LABEL.get(steps.get(sid, ''), sid).lower()}")
        body += (f'<h4 class="cond">{e(lead)}: “{e(text)}” <span class="tag">{e(support)}</span>'
                 f'<span class="aud cc"> {e(sid)}</span></h4><div class="hrows">'
                 + "".join(_hrow(x, cond) for x in xs) + "</div>")
    none = next((r for r in es.refused if r.startswith("none proposed:")), "")
    return (f'<div class="hypo"><h3>Companies the thesis implies <span class="tag">our '
            f'hypothesis</span></h3><p class="small muted">{e(head)}</p>'
            + (_HHEAD + body if body else
               f'<p class="small">None proposed{e(": " + none[15:]) if none else "."}'
                       f'</p>')
            + (f'<div class="aud cc">set aside: {e("; ".join(es.refused))}</div>'
               if es.refused else "") + "</div>")


#: the implied companies' column headings — over rows only: an empty set says "None proposed"
_HHEAD = ('<div class="hhead" aria-hidden="true"><span>Ticker</span><span>Company</span>'
          '<span>Direction</span><span>Earns from (stated)</span><span>10-K</span></div>')
#: a proposal's basis as its 10-K reads it: (mark, words)
_BASIS_MARK = {"IN_FILING": ("✓", "its 10-K's revenue sentence names it"),
               "FILING_NAMES_OTHER": ("≠", "its 10-K's revenue sentence names another way"),
               "NOT_DESCRIBED": ("–", "its 10-K states no revenue sentence in these words"),
               "UNCHECKED": ("·", "not checked")}


def _hrow(x: EnrichmentCandidate, cond: bool) -> str:
    """One implied company as a row: ticker, name, which way (a condition says "would"), how it
    earns (the model's) and what its 10-K says of that — opening to the rationale, the basis,
    the filing's own sentence and the SEC check."""
    pos = x.direction is Direction.POSITIVE
    side = ("would " if cond else "could ") + ("benefit" if pos else "be hurt")
    tick = ", ".join(dict.fromkeys(v.ticker for v in x.listings)) or (x.ticker_hint or "—")
    mark, why = _BASIS_MARK.get(x.basis_check, ("·", "not checked"))
    earns = BASIS_LABEL.get(x.revenue_model, x.revenue_model) if x.revenue_model else "not stated"
    basis = basis_line(x)
    return (f'<details class="hrow"><summary><span class="tkr">{e(tick)}</span>'
            f'<b>{e(x.name)}</b><span class="side {"up" if pos else "down"}">{e(side)}</span>'
            f'<span class="earn">{e(earns)}</span><span class="ck" title="{e(why)}">{mark}</span>'
            f'</summary><div class="hbody"><p>{e(x.rationale)}</p>'
            f'<p class="small">Listing: {e(enrichment_listing(x))}</p>'
            + (f'<p class="small basis">{e(basis)}</p>' if basis else "")
            + "".join(f'<p class="filing">“{e(q)}”</p>' for q in x.basis_quote)
            + f'<span class="aud cc">{e(x.resolution_status.value)} · {e(x.resolution_note)}'
            f'</span></div></details>')


def _ml(label: str) -> str:
    """A cell's label shown only where the table stacks into cards (a phone), whose column
    headers are hidden — so a bare "1" or "—" never stands without its meaning."""
    return f'<span class="ml">{e(label)}: </span>'


def _page_links(urls: list[str]) -> str:
    """Research pages as links named by host and path, one after another."""
    return " · ".join(f'<a href="{e(u)}">{e(_host(u))}</a>' for u in urls)


def _host(url: str) -> str:
    """A web address as a reader names it: its host and path, no scheme."""
    u = urlparse(url)
    return (u.netloc.removeprefix("www.") + u.path).rstrip("/")


def _lead(note: str) -> tuple[str, str]:
    """A history note as (its lead word, the rest): "Resolved — an earlier review …" → ("Resolved",
    "an earlier review …"); "Corrected by the analyst." → ("Corrected by the analyst", "")."""
    head, _sep, rest = note.partition(" — ")
    return head.rstrip(". "), rest


def _no_thesis(a: ArticleRow) -> str:
    return next((n for n in a.notes if n.startswith("No thesis")),
                "No thesis created or changed.")


def _link(url: str, text: str) -> str:
    """A link only to a web address — a document's own identifier (urn:document:…) is text."""
    return (f'<a href="{e(url)}">{e(text)}</a>' if url.startswith(("http://", "https://"))
            else e(text))


def _test_domain(url: str) -> bool:
    host = urlparse(url).hostname or ""
    return host.endswith(_TEST_HOSTS)


class Desk:
    """The desk's view model over one run of the registry, and its pages."""

    def __init__(self, store: Store, run: WeeklyRun, *, cards: dict[str, dict[str, str]],
                 generated: str, asof: AsOf | None = None) -> None:
        """`asof`: the run's `theses_as_of_run`, when the caller already holds it (U41: one
        render built it three times)."""
        self.store, self.run, self.generated = store, run, generated
        self.reg = _Registry(store)
        self.weeks = desk_weeks(store, run)
        if not self.weeks:
            raise ValueError(f"run {run.run_id} has no week to report")
        self.week = self.weeks[-1]
        self.asof: AsOf = asof if asof is not None else theses_as_of_run(store, run)
        self.cards = cards
        self._uid = 0
        self.week_of_run = {r.run_id: w.key for w in self.weeks for r in (*w.runs, *w.failed)}
        self.articles = {w.key: week_articles(self.reg, w, latest=w is self.week)
                         for w in self.weeks}
        # the weekly report counts the week's articles by THIS census (one registry read)
        self.d: Dashboard = build_dashboard(store, run.run_id, cards=cards, generated=generated,
                                            runs=list(self.week.runs),
                                            census=census_of(self.articles[self.week.key]),
                                            asof=self.asof)
        self.rows: list[DashRow] = [r for rs in self.d.categories.values() for r in rs]
        self.health = source_health_as_of(store, run)
        self.area = {tid: area_name(t.key_node) for tid, (t, _v) in self.asof.items()}
        self.activity: dict[str, set[str]] = defaultdict(set)
        for tid in self.asof:
            for x in store.thesis_versions(tid):
                if x.run_id in self.week_of_run:
                    self.activity[tid].add(self.week_of_run[x.run_id])
        self.near = {tid: near_term_reading(store, v) for tid, (_t, v) in self.asof.items()}
        self.open: list[Finding] = []
        self.history: list[Finding] = []
        for tid, (t, v) in self.asof.items():
            o, h = thesis_findings(store, t, v, area=self.area[tid], nt=self.near[tid])
            if t.status is ThesisStatus.ARCHIVED:
                for f in o:
                    f.history = "The thesis is archived — kept for the record."
                self.history += o + h
            else:
                self.open += o
                self.history += h
        self.open.sort(key=review_order)
        self.history.sort(key=lambda f: (f.title, f.raised))
        checkpoints = [(url, status, w.end) for w in self.weeks for r in w.runs
                       if r.mode == "scan" for url, status in r.checkpoint.items()]
        self.uploads = upload_items(self.reg, self.health, checkpoints)
        self.test_articles = sum(1 for a in store.articles() if _test_domain(a.canonical_url))
        self.n_articles = len(store.articles())
        self.groups: dict[str, tuple[list[str], int]] = {}
        self.sources_of: dict[str, set[str]] = defaultdict(set)
        self._related: dict[str, tuple[dict[str, list[str]], set[str]]] | None = None
        for c in self.reg.contributions:
            if c.thesis_id in self.asof and c.run_id in self.week_of_run:
                self.sources_of[c.thesis_id].add(c.article_id)

    # -- helpers -------------------------------------------------------------------------------
    def table(self, cls: str, head: str, rows: list[str], what: str, *, cap: int = PAGE_ROWS,
              tid: str = "") -> str:
        """A table that shows `cap` rows and SAYS how many it holds; the rest are one click away
        (a CSS switch — a table cannot hold a <details>), and a filter reaches every row."""
        n = len(rows)
        idattr = f' id="{tid}"' if tid else ""
        if n <= cap:
            return (f'<div class="hscroll"><table class="arts {cls}"{idattr}>{head}'
                    + "".join(rows) + "</table></div>")
        self._uid += 1
        uid = f"more{self._uid}"
        rest = [r.replace("<tr", '<tr class="xtra"') for r in rows[cap:]]
        return (f'<input type="checkbox" class="morebox" id="{uid}" hidden>'
                f'<div class="hscroll"><table class="arts {cls}"{idattr} data-cap="{cap}" '
                f'data-box="{uid}" data-what="{e(what)}">{head}'
                + "".join(rows[:cap] + rest) + f'</table></div><label class="morelbl" '
                f'for="{uid}">Showing {cap} of {n} {e(what)} — show all {n}</label>')

    def thesis_link(self, tid: str, depth: int = 0) -> str:
        return f'{"../" * depth}theses/{e(tid)}.html'

    @staticmethod
    def anchor_of(f: Finding) -> str:
        return _anchor(f.sid) if f.sid else _KIND_ANCHOR.get(f.kind, "top")

    def card_link(self, tid: str, depth: int = 0, anchor: str = "") -> str:
        path = self.cards.get(tid, {}).get("html", f"cards/{tid}.html")
        return f'{"../" * depth}{e(path)}' + (f"#{e(anchor)}" if anchor else "")

    def title(self, tid: str) -> str:
        return self.asof[tid][0].title if tid in self.asof else tid

    def active(self) -> list[tuple[Thesis, ThesisVersion]]:
        return [(t, v) for t, v in self.asof.values() if t.status is not ThesisStatus.ARCHIVED]

    def open_by_thesis(self) -> dict[str, list[Finding]]:
        out: dict[str, list[Finding]] = defaultdict(list)
        for f in self.open:
            out[f.thesis_id].append(f)
        return out

    def unmet(self, tid: str) -> list[str]:
        t, v = self.asof[tid]
        if tid not in self.groups:
            rc = card_context(self.store, t, v, generated="", until=self.run.finished_at)
            self.groups[tid] = ([g.name for g in rc.groups], rc.groups_unread)
        groups, unread = self.groups[tid]
        return [g.name for g in gates(v, groups, self.near[tid], groups_unread=unread)
                if not g.ok]

    def page(self, title: str, body: str, active: str, depth: int = 0) -> str:
        up = "../" * depth
        banner = ""
        if self.test_articles:
            banner = (f'<div class="testdata">TEST DATA — this registry holds articles from a '
                      f'reserved test domain ({self.test_articles} of {self.n_articles} articles; '
                      f'the rest are supplied documents or other sources). This is not research.'
                      f'</div>')
        return ("<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport "
                "content='width=device-width,initial-scale=1'>" + ROBOTS + "<title>" + e(title)
                + " · Research desk</title><style>" + CSS + "</style></head><body>"
                + AUDIT_TOGGLE + banner + topnav(up, active=active)
                + f'<main class="wrap">{body}' + foot_html(self.generated)
                + f'<div class="foot"><a href="{up}dashboard.html">Full weekly report</a> · '
                  f'<a href="{up}report_print.html">Printable report</a></div></main>'
                + "<script>" + JS + "deskInit(document,new URLSearchParams(location.search));"
                + "</script>" + REVEAL_JS + "</body></html>")

    # -- This Week -----------------------------------------------------------------------------
    def home(self) -> str:
        w, d = self.week, self.d
        arts = self.articles[w.key]
        read = [a for a in arts if a.analysed]
        full = sum(1 for a in read if a.state == "FULL")
        queued = sum(1 for a in arts if a.state == "QUEUED")
        bad = [a for a in arts if a.state in ("FAILED", "BLOCKED", "NO_BODY", "REJECTED")]
        new = sum(1 for r in self.rows if "New" in r.events)
        ups = sum(1 for r in self.rows if any(x.startswith("Upgraded") for x in r.events))
        downs = sum(1 for r in self.rows if any(x.startswith("Downgraded") for x in r.events))
        active = self.active()
        rn = sum(1 for _t, v in active if v.priority.research_action is ResearchAction.RESEARCH_NOW)
        decisive = sum(1 for f in self.open if f.decision)
        waiting = [u for u in self.uploads if u.kind not in ("done",)]
        by_area: dict[str, list[DashRow]] = defaultdict(list)
        for r in self.rows:
            by_area[self.area.get(r.thesis_id, "Unclassified")].append(r)
        areas = sorted(by_area.items(), key=lambda kv: (-len(kv[1]), kv[0]))
        sec = []
        for name, rs in areas:
            # a retired thesis is history: listed after every live one, whatever its action
            rs = sorted(rs, key=lambda r: (r.retired, _RANK.get(r.action, 3), r.title))
            rows = [self.change_row(r) for r in rs]
            sec.append(f'<div class="area"><h3>{e(name)} <small>{len(rs)}</small></h3>'
                       f'{capped(rows, "theses", 6)}</div>')
        if d.no_evidence:
            sec.append('<details class="quiet"><summary>' + _pl(len(d.no_evidence), "proposition")
                       + " with no verified evidence — kept for the record</summary><ul>" + "".join(
                           f'<li><a href="{self.thesis_link(r.thesis_id)}">{e(r.title)}</a></li>'
                           for r in d.no_evidence) + "</ul></details>")
        # what the tiles above do not already say — one line, never a side panel beside the week
        notes: list[str] = []
        if bad:
            notes.append(f'<a href="articles.html">{_pl(len(bad), "article")} failed or blocked'
                         f'</a> this week')
        soon = [t for t, _v in active
                if STALE_AFTER_DAYS - (w.end - t.last_material_update).days <= 21]
        if soon:
            notes.append(f'<a href="themes.html?sort=stale">{_theses(len(soon))} close to '
                         f'archiving</a> (no new evidence for about three months)')
        blocked = [r["publisher"] for r in self.health.get("rows", [])
                   if r["status"] in ("BLOCKED", "ERROR", "DEGRADED")]
        if blocked:
            notes.append(f'<a href="sources.html">{len(blocked)} of '
                         f'{len(self.health.get("rows", []))} sources blocked or partial</a> '
                         f'({e(", ".join(blocked))})')
        heads_up = (f'<p class="headsup">{" · ".join(notes)}</p>' if notes else "")
        a_counts: dict[str, list[Thesis]] = defaultdict(list)
        for t, _v in active:
            a_counts[self.area[t.thesis_id]].append(t)
        changed = {r.thesis_id for r in self.rows}
        recent = self.weeks[-12:]

        def n_now(ts: list[Thesis]) -> int:
            return sum(1 for t in ts if self.asof[t.thesis_id][1].priority.research_action
                       is ResearchAction.RESEARCH_NOW)

        arow = [
            f'<tr><td><a href="themes.html?area={e(quote(a))}">{e(a)}</a></td><td>{len(ts)}</td>'
            f'<td>{sum(1 for t in ts if t.thesis_id in changed) or "—"}</td>'
            f'<td>{n_now(ts) or "—"}</td><td>'
            f'{_strip(recent, set().union(*[self.activity[t.thesis_id] for t in ts]))}</td></tr>'
            for a, ts in sorted(a_counts.items(), key=lambda kv: (-len(kv[1]), kv[0]))]
        n_retired = sum(1 for r in self.rows if r.retired)
        tiles = [
            ("articles.html", len(read), "Articles read",
             f"{full} in full · {len(read) - full} preview" + (f" · {queued} queued" if queued
                                                               else ""), False),
            ("", len(self.rows), "New or changed theses", f"{new} new · {ups} up · {downs} down"
             + (f" · {n_retired} retired" if n_retired else ""), False),
            ("themes.html", rn, "Research Now", f"of {len(active)} active", False),
            # every ACTIVE thesis's, not only this week's: said, so the count reads beside the
            # weekly report's review items on this week's cards (U54)
            ("review.html", len(self.open), "Findings to review",
             f"on {_theses(len(active), 'active')} · "
             + (f"{decisive} affect an action" if decisive else "none affect an action"),
             bool(decisive)),
            ("uploads.html", len(waiting), "Upload items", "to supply or clear", bool(waiting))]
        strip = "".join(
            (f'<a href="{h}" class="{"warn" if warn else ""}">' if h else "<div>")
            + f"<b>{n}</b><span>{e(label)}</span><small>{e(sub)}</small>"
            + ("</a>" if h else "</div>") for h, n, label, sub, warn in tiles)
        body = (
            f'<section class="hero"><h1>{e(w.label)}</h1><p class="sum">'
            f'{_pl(len(read), "article")} read · {_theses(len(self.rows), "new or changed")} · '
            f'{rn} at Research Now</p><div class="strip">{strip}</div>{heads_up}</section>'
            f'<h2>Changes this week '
            f'<small>{_theses(len(self.rows))} in {_pl(len(areas), "area")}</small></h2>'
            + ("".join(sec) or '<p class="muted">No thesis was created or changed.</p>')
            + f'<h2 class="mt">Articles this week <small>{len(arts)}</small></h2>'
            + self.produced_list(arts, cap=8)
            + f'<details class="quiet mt"><summary>All active theses by area '
            f'<span class="muted">{_theses(len(active))} in {_pl(len(a_counts), "area")}</span>'
            f'</summary>'
            + self.table("areas", '<tr><th>Area</th><th>Active</th><th>Changed</th>'
                                  '<th>Research Now</th><th>Weeks with new evidence</th></tr>',
                         arow, "areas")
            + '</details>')
        return self.page("This week", body, "This week")

    def latest_source(self, tid: str) -> tuple[str, date | None]:
        """The publisher and date of a thesis's latest source."""
        srcs = self.asof[tid][1].content.s09_sources if tid in self.asof else ()
        s = max(srcs, key=lambda x: x.published_at or datetime.min.replace(tzinfo=UTC),
                default=None)
        return (s.publisher, _todate(s.published_at)) if s else ("", None)

    def change_row(self, r: DashRow) -> str:
        unmet = self.unmet(r.thesis_id) if r.action == "WATCH" and not r.retired else []
        n_open = len(self.open_by_thesis().get(r.thesis_id, []))
        mech = plain(r.mechanism)
        same = re.sub(r"\W+", " ", mech).strip().lower() in re.sub(
            r"\W+", " ", r.title).strip().lower()
        pub, when = self.latest_source(r.thesis_id)
        meta = [x for x in (pub, _day(when) if when else "") if x]
        if r.partial_source:
            meta.append("preview only")
        gap = (f'<span class="bdg" title="Not yet Research Now: {e("; ".join(unmet))}">'
               f'{_pl(len(unmet), "condition")} open</span>' if unmet else "")
        return (f'<a class="trow" href="{self.thesis_link(r.thesis_id)}"><div class="ttop">'
                f'{_chip(r.action, r.watch)}{"".join(_event(x) for x in r.events)}'
                + (f'<span class="ev rv">{_pl(n_open, "finding")}</span>' if n_open else "")
                + f'</div><div class="ttitle">{e(r.title)}</div>'
                + ("" if same or not mech else f'<div class="tline clamp">{e(mech)}</div>')
                + f'<div class="tmeta">{e(" · ".join(meta))}{gap}</div></a>')

    def produced_cell(self, a: ArticleRow, depth: int = 0) -> str:
        if a.produced:
            return "<br>".join(
                f'<a href="{self.thesis_link(tid, depth)}">{e(self.title(tid))}</a> '
                f'<span class="small">· {e(how)}{e(self.gone(tid))}</span>' if tid in self.asof else
                f'<span class="small">{e(how)} (a thesis not in this run\'s record)</span>'
                for tid, how in a.produced)
        return f'<span class="small">{e(_no_thesis(a))}</span>'

    def produced_list(self, arts: list[ArticleRow], cap: int) -> str:
        if not arts:
            return '<p class="muted">No article this week.</p>'
        items = [f'<li>{_state(a.state)}<div><div class="atl">{e(a.title)}</div>'
                 f'<div class="small">{e(a.publisher)} · {e(_day(a.published))}</div>'
                 + (f'<div class="aprod">{self.produced_cell(a)}</div>' if a.analysed else "")
                 + "</div></li>" for a in arts]
        return ('<ul class="alist">' + "".join(items[:cap]) + "</ul>"
                + (f'<p class="small">Showing {cap} of {len(items)} articles — '
                   f'<a href="articles.html">all {len(items)} on Articles</a></p>'
                   if len(items) > cap else ""))

    # -- Themes --------------------------------------------------------------------------------
    def themes(self) -> str:
        w = self.week
        by_t = self.open_by_thesis()
        changed = {r.thesis_id for r in self.rows}
        recent = self.weeks[-12:]
        rel = {tid: len(self.related_of(tid)[0]) for tid in self.asof}
        rows: list[tuple[str, str]] = []
        items = sorted(self.asof.values(), key=lambda tv: (
            tv[0].status is ThesisStatus.ARCHIVED,
            _RANK.get(tv[1].priority.research_action.value, 3),
            -tv[0].last_material_update.toordinal(), tv[0].title))
        for t, v in items:
            tid = t.thesis_id
            arch = t.status is ThesisStatus.ARCHIVED
            left = STALE_AFTER_DAYS - (w.end - t.last_material_update).days
            note = ("" if not arch and left > 21 else
                    f'<span class="stale">archives in {left} days</span>' if not arch else
                    f'<span class="small">archived — {e(self.archived_why(t, v))}</span>')
            n_src = len(v.content.s09_sources)
            a = self.area[tid]
            sub = [x for x in (note, f'<span class="small">{_theses(rel[tid], "related")}</span>'
                               if rel.get(tid) else "") if x]
            wq = watch_of(v.priority, v.content.s05_affected)
            rows.append((a, (
                f'<tr data-area="{e(a)}" data-ord="{len(rows)}" '
                f'data-action="{e(v.priority.research_action.value)}" '
                f'data-status="{"archived" if arch else "active"}" '
                f'data-upd="{t.last_material_update.toordinal()}" '
                f'data-left="{left if not arch else 99999}" data-src="{n_src}" '
                f'data-rv="{len(by_t.get(tid, []))}"><td><a href="{self.thesis_link(tid)}">'
                f'{e(t.title)}</a>'
                f'{" " + _event("New") if tid in changed and v.version == 1 else ""}'
                + (f'<div>{" · ".join(sub)}</div>' if sub else "")
                + f'<span class="aud cc">{e(tid)}</span></td>'
                  f'<td>{_chip(v.priority.research_action.value, wq)}</td>'
                  f'<td class="nowrap">{_ml("last evidence")}{e(_day(t.last_material_update))}'
                  f'</td><td>{_ml("sources")}{n_src}</td>'
                  f'<td>{_ml("open findings")}{len(by_t.get(tid, [])) or "—"}</td>'
                  f'<td>{_ml("weeks with new evidence")}{_strip(recent, self.activity[tid])}'
                  f'</td></tr>')))
        by_area: dict[str, list[str]] = defaultdict(list)
        for a, r in rows:
            by_area[a].append(r)
        groups = []
        for a, rs in sorted(by_area.items()):
            act = [(t, v) for t, v in self.asof.values() if self.area[t.thesis_id] == a
                   and t.status is not ThesisStatus.ARCHIVED]
            ch = sum(1 for t, _v in act if t.thesis_id in changed)
            rn = sum(1 for _t, v in act
                     if v.priority.research_action is ResearchAction.RESEARCH_NOW)
            facts = [f"{len(act)} active"] + ([f"{rn} Research Now"] if rn else []) + (
                [f"{ch} changed this week"] if ch else [])
            groups.append(
                f'<details class="agrp"{" open" if ch else ""} data-grp="{e(a)}"><summary>'
                f'<b>{e(a)}</b><span class="muted">{" · ".join(facts)}</span></summary>'
                + self.table("themes", '<tr><th>Thesis</th><th>Action</th><th>Last evidence'
                                       '</th><th>Sources</th><th>Findings</th><th>Activity'
                                       '</th></tr>', rs, "theses")
                + '</details>')
        n_act = len(self.active())
        areas = sorted(by_area)
        body = (f'<section class="hero"><h1 class="tabtitle">Themes</h1><p class="sum">'
                f'{n_act} active · {len(self.asof) - n_act} archived · '
                f'{_pl(len(areas), "area")}</p><p class="hint">Areas with a change this week '
                f'are open. A thesis archives after {STALE_AFTER_DAYS} days without new evidence, '
                f'or at once when Skip.</p></section>'
                '<div class="filters"><input id="q" placeholder="Search theses and areas" '
                'oninput="flt()" aria-label="Search"><select id="fs" onchange="flt()" '
                'aria-label="Status"><option value="active">Active</option><option '
                'value="archived">Archived</option><option value="">All</option></select>'
                '<select id="fa" onchange="flt()" aria-label="Action"><option value="">All '
                'actions</option><option value="RESEARCH NOW">Research Now</option><option '
                'value="WATCH">Watch</option><option value="SKIP">Skip</option></select>'
                '<select id="far" onchange="flt()" aria-label="Area"><option value="">All areas'
                '</option>' + "".join(f"<option>{e(a)}</option>" for a in areas)
                + '</select><select id="so" onchange="srt()" aria-label="Sort"><option '
                  'value="">Research action, then latest evidence</option><option '
                  'value="upd">Latest evidence</option><option value="stale">Closest to '
                  'archiving</option><option value="src">Most sources</option><option '
                  'value="rv">Most findings</option></select><span id="cnt" class="small">'
                  '</span></div>'
                f'<div id="tt">{"".join(groups)}</div>')
        return self.page("Themes", body, "Themes")

    def gone(self, tid: str) -> str:
        """" · retired" / " · archived" for a thesis this run's record no longer holds open — an
        article list names it beside what the article gave it (U13), never as a live thesis."""
        t = self.asof[tid][0]
        return (" · retired — replaced on re-analysis" if t.retired else
                " · archived" if t.status is ThesisStatus.ARCHIVED else "")

    def archived_why(self, t: Thesis, v: ThesisVersion) -> str:
        if t.retired:
            return ("retired — its articles were analysed again under the current taxonomy, and "
                    "the theses that created replace it")
        if v.priority.research_action is ResearchAction.SKIP:
            return "its research action is Skip"
        return f"no new evidence for more than {STALE_AFTER_DAYS} days"

    # -- Articles ------------------------------------------------------------------------------
    def articles_page(self, w: Week) -> str:
        arts = self.articles[w.key]
        order = list(reversed(self.weeks))  # newest first
        i = order.index(w)
        newer, older = (order[i - 1] if i else None), (order[i + 1] if i + 1 < len(order) else None)
        allw = "".join(f'<a class="wk{" on" if x.key == w.key else ""}" href="{self.week_file(x)}">'
                       f'{e(_span(x.start, x.end))} <small>{len(self.articles[x.key])}</small></a>'
                       for x in order)
        nav = ('<nav class="weeknav">'
               + (f'<a href="{self.week_file(older)}">‹ {e(_span(older.start, older.end))}</a>'
                  if older else '<span class="muted">‹ no earlier week</span>')
               + f'<b>{e(_span(w.start, w.end))}</b>'
               + (f'<a href="{self.week_file(newer)}">{e(_span(newer.start, newer.end))} ›</a>'
                  if newer else '<span class="muted">latest week</span>')
               + f'<details class="older"><summary>All weeks ({len(order)})</summary>'
                 f'<div class="weeks">{allw}</div></details></nav>')
        count = Counter(a.state for a in arts)
        states = "".join(f'<span class="cnt">{_state(s)} {n}</span>'
                         for s, n in sorted(count.items(),
                                            key=lambda kv: STATE_ORDER.get(kv[0], 9)))
        rows = []
        for a in arts:
            items = a.open_items + [f"Coverage alert: {x}" for x in a.alerts]
            # under the article, at the table's full width — never inside the narrow column
            items_row = ('<tr data-sub><td colspan="5" class="subrow"><details class="fold">'
                         '<summary>'
                   + _pl(len(items), "item") + " to check"
                   + (f' <span class="muted">· {a.captured} of {a.figures} figures captured'
                      f'</span>' if a.figures else "") + "</summary><ul>"
                   + "".join(f"<li>{ids_to_audit(e(plain(x)))}</li>" for x in items)
                   + "</ul></details></td></tr>" if items else "")
            act = (f'<a href="{a.follow_link}">{e(a.follow_up)}</a>' if a.follow_link
                   else e(a.follow_up))
            notes = [n for n in a.notes if a.state not in _SELF_EXPLAINED
                     and (a.produced or not n.startswith("No thesis"))]
            sub = " · ".join(x for x in (e(a.publisher), e(a.route) if a.route != "automatic"
                                         else "", f"{a.words:,} words read"
                                         if a.state == "PARTIAL" and a.words else "") if x)
            rows.append(
                f'<tr data-state="{a.state}" data-pub="{e(a.publisher)}"'
                f'{" data-hassub" if items_row else ""}><td class="nowrap">'
                f'{e(_day(a.published))}</td><td class="art">{_link(a.url, a.title)}'
                f'<div class="small">{sub}</div>'
                + "".join(f'<div class="small">{e(n)}</div>' for n in notes)
                + f'<span class="aud cc">{e(" · ".join(a.audit))}</span></td><td>{_state(a.state)}'
                + f'</td><td>{self.produced_cell(a) if a.analysed else ""}</td>'
                f'<td class="small">{act}</td></tr>{items_row}')
        pubs = sorted({a.publisher for a in arts})
        legend = ('<p class="hint">Queued: found in the window and left for the next run by the '
                  'per-run article cap.</p>' if count.get("QUEUED") else "")
        body = (f'<section class="hero"><h1 class="tabtitle">Articles</h1><p class="sum">'
                f'{e(w.label)} · {_pl(len(arts), "item")}</p>{nav}'
                f'<div class="counts">{states}</div>{legend}</section>'
                '<div class="filters"><select id="fr" onchange="fa()" aria-label="State"><option '
                'value="">Every state</option>' + "".join(
                    f'<option value="{s}">{e(ARTICLE_STATE[s][0])}</option>' for s in count)
                + '</select><select id="fp" onchange="fa()" aria-label="Publisher"><option '
                  'value="">Every publisher</option>' + "".join(
                      f"<option>{e(p)}</option>" for p in pubs)
                + '</select><span id="cnt2" class="small"></span></div>'
                + self.table("artt", '<tr><th>Published</th><th>Article</th><th>State</th>'
                                     '<th>Produced</th><th>Follow-up</th></tr>', rows, "articles",
                             tid="at"))
        return self.page(f"Articles — {w.label}", body, "Articles")

    def week_file(self, w: Week) -> str:
        return "articles.html" if w is self.week else f"articles-{w.key}.html"

    # -- Review --------------------------------------------------------------------------------
    def finding_item(self, f: Finding, depth: int = 0) -> str:
        """One finding: the line, the review's words, and one meta row — badges, never repeated
        sentences (the reason a finding affects an action is its badge's tooltip)."""
        age = (self.week.end - f.raised).days
        weeks = age // 7
        line, scope = split_scope(f.line)  # the scope note is the audit view's, as on the page
        badges = (f'<span class="bdg bad" title="{e(f.decision)}">Affects action</span>'
                  if f.decision else "")
        return (f'<li class="rvi" data-dec="{1 if f.decision else 0}" data-act="{e(f.action)}" '
                f'data-age="{age}"><div class="line clamp2">“{ids_to_audit(e(line))}”'
                + (f'<span class="aud scope"> ({e(scope)})</span>' if scope else "")
                + f'</div>'
                f'<div class="said clamp3"><b>{_KIND_WORD.get(f.kind, "Review")}:</b> '
                f'{ids_to_audit(e(plain(f.said)))}</div><div class="rvmeta">{badges}'
                f'<span>raised {e(_day(f.raised))} (version {f.raised_version})</span>'
                f'<span>{"this week" if weeks == 0 else _pl(weeks, "week") + " open"}</span>'
                f'<a href="{self.card_link(f.thesis_id, depth, self.anchor_of(f))}">'
                f'Open in the full record ↗</a></div>'
                f'<span class="aud cc">{e(f.audit)}</span></li>')

    def finding_line(self, f: Finding) -> str:
        """A finding on the THESIS page as one line — whether it affects the action, its kind,
        the line it questions (clamped) — opening to the review's words and the record. The
        Review tab keeps the full item (`finding_item`)."""
        line, scope = split_scope(f.line)
        return ('<li class="rvi"><details><summary>'
                + (f'<span class="bdg bad" title="{e(f.decision)}">Affects action</span> '
                   if f.decision else "")
                + f'<b>{_KIND_WORD.get(f.kind, "Review")}</b> '
                f'<span class="clamp1">“{ids_to_audit(e(line))}”</span></summary>'
                + (f'<span class="aud scope"> ({e(scope)})</span>' if scope else "")
                + f'<div class="said">{ids_to_audit(e(plain(f.said)))}</div>'
                f'<div class="rvmeta"><span>raised {e(_day(f.raised))} (version '
                f'{f.raised_version})</span><a href="'
                f'{self.card_link(f.thesis_id, 1, self.anchor_of(f))}">Open in the full record ↗'
                f'</a></div><span class="aud cc">{e(f.audit)}</span></details></li>')

    def review(self) -> str:
        w = self.week
        groups: dict[str, list[Finding]] = defaultdict(list)
        for f in self.open:  # already in review order: a thesis is placed by its first finding
            groups[f.thesis_id].append(f)
        blocks = []
        for tid, fs in groups.items():
            f0 = fs[0]
            blocks.append(
                f'<li class="rvg"><div class="rvgh"><a href="{self.thesis_link(tid)}">'
                f'{e(f0.title)}</a>{_chip(f0.action)}<span class="small">{e(f0.area)} · '
                f'{_pl(len(fs), "finding")}</span></div><ul class="rvitems">'
                + "".join(self.finding_item(f) for f in fs) + "</ul></li>")
        dec = sum(1 for f in self.open if f.decision)
        old = sum(1 for f in self.open if (w.end - f.raised).days >= 28)
        hist = [f'<li class="rvi"><div class="line clamp2">“{ids_to_audit(e(f.line))}”</div>'
                f'<div class="said clamp2" title="Review said: {e(plain(f.said))}">'
                f'<b>{e(_lead(f.history)[0])}:</b> {e(_lead(f.history)[1])} '
                f'<span class="muted">Review said: {ids_to_audit(e(plain(f.said)))}</span></div>'
                f'<div class="rvmeta"><a href="{self.thesis_link(f.thesis_id)}">{e(f.title)}</a>'
                f'</div></li>' for f in self.history]
        n_comp = 0
        comp = []
        for wk in reversed(self.weeks):  # one entry per article, its open items under it
            for a in self.articles[wk.key]:
                if a.open_items:
                    n_comp += len(a.open_items)
                    comp.append(f'<li><a href="{self.week_file(wk)}">{e(a.title)}</a> '
                                f'<span class="muted">{e(a.publisher)} · '
                                f'{_pl(len(a.open_items), "item")}</span><ul class="small">'
                                + "".join(f"<li>{e(x)}</li>" for x in a.open_items)
                                + "</ul></li>")
        body = (f'<section class="hero"><h1 class="tabtitle">Review</h1><p class="sum">'
                f'{_pl(len(self.open), "open finding")} · '
                f'{_theses(len(groups))} · {dec} affect a research action · '
                f'{old} open 4+ weeks</p><p class="hint">Findings that affect a research action '
                f'come first, then Research Now, then the oldest. Read-only: a finding closes '
                f'through an analyst correction or a re-read.</p>'
                '<div class="filters"><label class="pillcheck"><input type="checkbox" id="fdec" '
                'onchange="fr2()"> Affects action</label><label class="pillcheck"><input '
                'type="checkbox" id="frn" onchange="fr2()"> Research Now</label><label '
                'class="pillcheck"><input type="checkbox" id="fold" onchange="fr2()"> Open 4+ '
                'weeks</label><span id="cnt3" class="small"></span></div></section>'
                + '<ul class="rvlist" id="rv">'
                + (capped_li(blocks, "theses", "rvlist")
                   or '<li class="muted">No open finding.</li>') + "</ul>"
                + (f'<details class="quiet"><summary>Resolved and historical findings '
                   f'<span class="muted">{len(hist)}</span></summary><ul class="rvitems">'
                   f'{"".join(hist)}</ul></details>' if hist else "")
                + (f'<details class="quiet"><summary>Article completeness — open figures and '
                   f'paragraphs <span class="muted">{n_comp} in {_pl(len(comp), "article")}'
                   f'</span></summary><p class="small">'
                   f'Open material is never used as evidence: it can hold a thesis back, never '
                   f'raise it.</p><ul class="plainlist compl">'
                   f'{capped_li(comp, "articles", "plainlist compl")}'
                   f'</ul></details>' if comp else ""))
        return self.page("Review", body, "Review")

    # -- Uploads -------------------------------------------------------------------------------
    def uploads_page(self) -> str:
        w = self.week
        groups = [
            ("full_report", "Full report needed", "a preview was read; the full copy completes "
                                                  "the same article"),
            ("blocked_article", "Blocked articles", "found by the scan, could not be read"),
            ("channel", "Manual-first and blocked sources", "the scan does not or cannot read "
                                                            "them"),
            ("held", "Held documents", "supplied; analysed only once released"),
            ("review", "Match uncertain", "supplied; you decide which article it is"),
            ("visual", "Visual check", "pages of a supplied document could not be read"),
            ("rejected", "Not imported", "supplied but unreadable"),
            ("done", "Completed imports", "analysed — kept for the record")]
        by: dict[str, list[UploadItem]] = defaultdict(list)
        for u in self.uploads:
            by[u.kind].append(u)
        blocks = []
        for kind, head, help_ in groups:
            us = sorted(by.get(kind, []), key=lambda u: (u.published or date.min, u.title),
                        reverse=True)
            if not us:
                continue
            items = []
            for u in us:
                dates = " · ".join(x for x in (
                    f"published {_day(u.published)}" if u.published else "",
                    f"{(w.end - u.published).days} days old" if u.published else "",
                    f"first seen {_day(u.first_seen)}" if u.first_seen else "") if x)
                extra = (u.detail[:4] + ([f"showing 4 of {len(u.detail)}"]
                                         if len(u.detail) > 4 else []))
                items.append(
                    f'<li class="ui"><div class="uimain"><div class="atl">{_link(u.url, u.title)}'
                    f'</div><div class="why">{e(u.why)}</div>'
                    + "".join(f'<div class="small clamp">{e(x)}</div>' for x in extra)
                    + "".join(f'<div class="small">• {_link(url, title)}'
                              + (f' <span class="muted">· {e(note)}</span>' if note else "")
                              + "</div>" for url, title, note in u.links)
                    + (f'<div class="small">Where to look: {_page_links(u.where)} — the scan '
                       f'cannot list its articles</div>' if u.where else "")
                    + "".join(f'<div class="small">→ <a href="{self.thesis_link(t)}">'
                              f'{e(self.title(t))}</a></div>' for t in u.theses if t in self.asof)
                    + f'<span class="aud cc">{e(u.audit)}</span></div><div class="uiside">'
                      f'<div>{e(u.publisher) or "publisher not recorded"}'
                    + (f' <code class="aud">{e(u.source_id)}</code>' if u.source_id else "")
                    + '</div>'
                    + (f'<div class="small">{e(dates)}</div>' if dates else "")
                    + f'</div>'
                      f'<div class="uiact">{self.command_html(u.command)}</div></li>')
            open_ = kind not in ("done", "rejected")
            blocks.append(
                f'<details class="ubk"{" open" if open_ else ""}><summary><b>{e(head)}</b>'
                f'<span class="muted">{len(us)} · {e(help_)}</span></summary>'
                f'<ul class="uilist">{capped_li(items, "documents", "uilist", cap=10)}</ul>'
                f'</details>')
        waiting = sum(1 for u in self.uploads if u.kind != "done")
        cli = f'<span class="nw">{CLI}</span>'  # a narrow panel wraps after it, never inside it
        body = (f'<section class="hero"><h1 class="tabtitle">Uploads</h1><p class="sum">'
                f'{_pl(waiting, "item")} to supply or clear · {len(by.get("done", []))} imported'
                f'</p><p class="hint">Nothing here is dismissed by age — an item stays until it is '
                f'supplied or cleared.</p></section>'
                # the weekly routine is reference, read once: one line, folded — never a side
                # panel narrowing the list it is about
                f'<details class="quiet howto"><summary>How to supply documents each week '
                f'<span class="muted">pull · import · clear · push</span></summary>'
                f'<ol class="steps4">'
                f'<li><b>1. Pull</b> the registry<code class="cmd">{cli} state pull</code></li>'
                f'<li><b>2. Import</b> each file with the command on its row, or put them in '
                f'<code>data/theme_intelligence/inbox/</code> and run '
                f'<code class="cmd">{cli} ingest-inbox</code></li>'
                f'<li><b>3. Clear</b> what is held with the release command on its row</li>'
                f'<li><b>4. Push</b> before Monday 03:00 UTC<code class="cmd">{cli} state push'
                f'</code></li></ol><details class="fold"><summary>Rules</summary>'
                f'<ul class="small"><li>Add <code>--llm-permitted</code> only when the '
                f'document\'s licence allows third-party model processing; without it the '
                f'document is held.</li><li>A document needs at least 40 words of readable '
                f'text.</li><li>A fuller copy of a preview is the same article, re-checked — '
                f'nothing is counted twice.</li><li>A document estimated above the $30 '
                f'per-document limit waits for your release.</li><li>An inbox file may carry a '
                f'<code>&lt;file&gt;.meta.json</code> with <code>source</code>, '
                f'<code>url</code>, <code>title</code>, <code>published</code>, '
                f'<code>llm_permitted</code>.</li></ul></details></details>'
                + ("".join(blocks) or '<p class="muted">Nothing waiting.</p>'))
        return self.page("Uploads", body, "Uploads")

    # -- Sources -------------------------------------------------------------------------------
    def sources_page(self) -> str:
        until = self.run.finished_at or datetime.now(tz=UTC)
        recent = self.weeks[-4:]
        n_read: Counter[str] = Counter()
        newest: dict[str, date] = {}
        for wk in recent:
            for a in self.articles[wk.key]:
                if a.analysed:
                    n_read[a.source_id] += 1
        for art in self.store.articles():
            d = _todate(art.published_at)
            if d and (art.source_id not in newest or d > newest[art.source_id]):
                newest[art.source_id] = d
        out: dict[str, list[str]] = {"automatic": [], "manual_first": []}
        attention = 0
        analysed = ("analysed this week" if len(recent) == 1 else
                    f"analysed, last {len(recent)} weeks")
        for sid, src in self.reg.sources.items():
            hist = [h for h in self.store.health_checks(source_id=sid) if h.checked_at <= until]
            last = hist[-1] if hist else None
            st = last.status.value if last else "UNKNOWN"
            attention += st != "HEALTHY"
            word, cls = _HEALTH.get(st, (st.title(), "mute"))
            strip = ('<span class="hs">' + "".join(
                f'<i class="h-{h.status.value.lower()}" title="{e(_day(h.checked_at))}: '
                f'{e(h.status.value.lower())}"></i>' for h in hist[-12:]) + "</span>"
                + f'<span class="small"> last {min(12, len(hist))} of {len(hist)} checks</span>'
                if len(hist) >= 2 else "")
            odd = [t for t in (last.tests if last else ()) if t.result in ("WARN", "FAIL")]
            details = ('<details class="fold"><summary>What the check found</summary><ul>'
                       + "".join(f"<li><b>{e(t.name.replace('_', ' '))}</b> — {e(plain(t.detail))}"
                                 f"</li>" for t in odd) + "</ul></details>" if odd else "")
            site = last.newest_article_date if last else None  # what the check saw listed
            seen = max((d for d in (site, newest.get(sid)) if d), default=None)
            fresh = e(_day(seen)) if seen else '<span class="muted">not known</span>'
            quiet = (' <span class="small">· quiet</span>'
                     if last and last.freshness.value == "QUIET" else "")
            note = ('<div class="small">linked reports read by the scan</div>'
                    if src.linked_reports == "fetch" else "") + (
                '<div class="small">paid posts read as their preview — by decision</div>'
                if src.paywalled_posts == "preview_only" else "")
            pages = [src.entry_url, *src.research_pages]
            where = (f'<div class="small">research {"pages" if len(pages) > 1 else "page"}: '
                     f'{_page_links(pages)}</div>' if src.mode == "manual_first" else "")
            out["manual_first" if src.mode == "manual_first" else "automatic"].append(
                f'<tr><td><b>{e(src.publisher)}</b>{note}{where}'
                f'<div class="aud"><code>{e(sid)}</code></div></td>'
                f'<td><span class="st {cls}">{e(word)}</span> '
                f'<span class="small">{e(_health_line(last))}</span>'
                + (f'<div class="small">checked {e(_day(last.checked_at))}</div>' if last else "")
                + f'{strip}{details}</td>'
                f'<td class="nowrap">{_ml("newest article")}{fresh}{quiet}</td>'
                f'<td>{_ml(analysed)}{n_read[sid] or "—"}</td></tr>')

        def table(rs: list[str]) -> str:
            return ('<div class="hscroll"><table class="arts srct"><tr><th>Publisher</th>'
                    '<th>Access now</th><th>Newest article</th>'
                    + f'<th>{analysed.capitalize()}</th></tr>' + "".join(rs)
                    + "</table></div>")

        permit = {"permitted": "analysed as soon as they arrive",
                  "not_permitted": "never sent to the model",
                  "unknown": "analysed once you confirm the licence allows it"}
        policies = {permit.get(x.manual_llm_processing, x.manual_llm_processing)
                    for x in self.reg.sources.values()}
        body = (f'<section class="hero"><h1 class="tabtitle">Sources</h1><p class="sum">'
                f'{len(out["automatic"])} automatic · {len(out["manual_first"])} manual-first · '
                f'{attention} need attention</p><p class="hint">A blocked or quiet source is not '
                f'evidence it published nothing. Documents you upload are '
                f'{" / ".join(sorted(policies))} (<code>--llm-permitted</code>).</p></section>'
                f'<section><h2>Automatic coverage <small>read by the weekly scan; a report a page '
                f'links to is listed on Uploads</small></h2>{table(out["automatic"])}</section>'
                f'<section><h2>Manual-first coverage <small>the scan does not read these; '
                f'research arrives only as documents you supply</small></h2>'
                f'{table(out["manual_first"])}</section>')
        return self.page("Sources", body, "Sources")

    # -- the reading page ----------------------------------------------------------------------
    def thesis_page(self, tid: str) -> str:
        t, v = self.asof[tid]
        c = v.content
        rc = card_context(self.store, t, v, generated="", until=self.run.finished_at)
        groups = [g.name for g in rc.groups]
        self.groups[tid] = (groups, rc.groups_unread)
        nt = self.near[tid]
        gs = gates(v, groups, nt, groups_unread=rc.groups_unread)
        action = v.priority.research_action.value
        mine = self.open_by_thesis().get(tid, [])
        flagged_sids = {f.sid for f in mine if f.sid}
        shown: set[str] = set()

        def once(text: str) -> bool:
            k = re.sub(r"\W+", " ", plain(text)).strip().lower()
            if not k or k in shown:
                return False
            shown.add(k)
            return True

        def flag(sid: str) -> str:
            return (' <a class="flagi" href="#review">under review</a>' if sid in flagged_sids
                    else "")

        def line(text: str) -> str:
            """A card line as the page reads it: its scope note goes to the audit view."""
            body, scope = split_scope(plain(text))
            return ids_to_audit(e(body)) + (f'<span class="aud scope"> ({e(scope)})</span>'
                                            if scope else "")

        events = next((r.events for r in self.rows if r.thesis_id == tid), [])
        arch = t.status is ThesisStatus.ARCHIVED
        head = (f'<nav class="crumb"><a href="../themes.html">Themes</a> › {e(self.area[tid])}'
                f'</nav><header class="th"><h1>{e(t.title)}</h1><div class="meta">'
                f'{_chip(action, watch_of(v.priority, c.s05_affected))}'
                f'{"".join(_event(x) for x in events)}'
                + (f'<span class="ev">archived — {e(self.archived_why(t, v))}</span>'
                   if arch else "")
                + (f'<a class="flag" href="#review">'
                   f'{"Not reviewed · " if any(f.kind == "not_reviewed" for f in mine) else ""}'
                   f'Review required · {_pl(len(mine), "finding")}</a>'
                   if mine else "")
                + f'</div><div class="meta2">{e(self.area[tid])} · '
                  f'{_pl(len(c.s09_sources), "source")} · newest evidence published '
                  f'{e(_day(t.last_material_update))} · on the desk since '
                  f'{e(_day(t.created_as_of))}</div>'
                  f'<div class="aud cc">{e(tid)} · version {v.version} · run {e(v.run_id)} · '
                  f'{e(t.key_node)} · {e(t.key_mechanism)}</div></header>')
        s01 = c.s01_bottom_line
        thesis = ""
        if s01 and once(s01[0].text):
            thesis = (f'<p class="thesis">{line(s01[0].text)} '
                      f'{_tag(s01[0].provenance.value)}{flag("s01.0")}</p>')
        changed = [f'<li>{line(it.text)}'
                   + (f' <span class="muted">({e(it.period)})</span>'
                      if it.period and re.sub(r"^per ", "", it.period) not in plain(it.text)
                      else "")
                   + f"{flag(f's02.{i}')}</li>"
                   for i, it in enumerate(c.s02_what_changed.items)
                   if f"s02.{i}" not in rc.blocked and once(it.text)]
        last = rc.history[-1] if rc.history else v
        prev = rc.history[-2] if len(rc.history) > 1 else None
        moved = (f"Version {last.version}, {_day(last.as_of)} — "
                 + (f"{_ACTION[prev.priority.research_action.value][0]} → "
                    f"{_ACTION[last.priority.research_action.value][0]}"
                    if prev and prev.priority.research_action is not last.priority.research_action
                    else "new evidence, research action unchanged" if prev else "first recorded"))
        # when the action of record last moved, if not in this version (the header's chips name
        # the week's moves; this says since when the action stands)
        turns = [(h, p) for p, h in zip(rc.history, rc.history[1:], strict=False)
                 if h.priority.research_action is not p.priority.research_action]
        if turns and turns[-1][0] is not last:
            h, p = turns[-1]
            up = _RANK[h.priority.research_action.value] < _RANK[p.priority.research_action.value]
            moved += (f" · {_ACTION[h.priority.research_action.value][0]} since version "
                      f"{h.version} ({_day(h.as_of)}), {'raised' if up else 'lowered'} from "
                      f"{_ACTION[p.priority.research_action.value][0]}")
        # the figures the thesis statement itself cites lead (the Alzheimer thesis led with a
        # gene-editing market size while its own $70bn sat fourth, 2026-10-14)
        lead = {cid for s in s01 for cid in s.claim_ids}
        ranked = sorted((r for r in c.s04_key_evidence if r.value_text),
                        key=lambda r: (r.claim_id not in lead,
                                       r.epistemic.value not in ("actual", "forecast"),
                                       not re.search(r"\d", r.value_text or "")))
        # three DISTINCT figures: one value and label twice ("$26 billion · DTC cash-pay market
        # size", at peak / at its peak) is one figure on a tear sheet
        seen_fig: set[tuple[str, str]] = set()
        figs: list[tuple[Any, str]] = []  # (row, its label) — the label read once
        for r in ranked:
            lbl = figure_label(self.store, r.claim_id, r.label)
            k = (r.value_text or "", lbl.lower())
            if k not in seen_fig:
                seen_fig.add(k)
                figs.append((r, lbl))
                if len(figs) == 3:
                    break
        pub = {s.article_id: s for s in c.s09_sources}
        fig_html = "".join(
            f'<div class="num"><b>{e(r.value_text)}</b><span class="unit">'
            f'{e(unit_shown(r.value_text, r.unit))}</span><span class="lbl">{e(lbl)}</span>'
            f'<small>{e(_EPI.get(r.epistemic.value, r.epistemic.value))} · '
            f'{e(r.period or "period not stated")}</small><small>'
            + (f"{e(pub[r.article_id].publisher)}, " if r.article_id in pub else "")
            + (f"measured {e(_day(r.measured_as_of))}" if r.measured_as_of else
               f"published {e(_day(pub[r.article_id].published_at))}"
               if r.article_id in pub else "date not stated")
            + f'</small><span class="aud cc">{e(r.claim_id)}</span></div>' for r, lbl in figs)
        steps = []
        for i, st in enumerate(c.s03_transmission):
            if st.step == "market_reaction":
                continue
            unknown = st.text.startswith("UNKNOWN")
            if not unknown and not once(st.text):
                continue
            steps.append(f'<li><span class="sn">{e(STEP_LABEL.get(st.step, st.step))}</span>'
                         + ('<span class="muted">not quantified by the source</span>' if unknown
                            else f'<span>{line(st.text)}</span> '
                                 f'{_tag(st.provenance.value)}{flag(f"s03.{i}")}')
                         + "</li>")
        near = next(g for g in gs if g.name == NEAR_GATE)
        unmet = [g for g in gs if not g.ok and g is not near]
        met = [g for g in gs if g.ok and g is not near]
        route = (why_reasons(c, v.priority, groups)[0] if action == "RESEARCH NOW" else "")
        why = (f'<p class="small">{e(route)}</p>' if route else "") + (
            '<ul class="gates">' + "".join(
                f'<li class="unmet"><span class="ic">✗</span><div><b>{e(g.name)}</b>'
                f'<span>{e(g.detail)}</span></div></li>' for g in unmet) + "</ul>"
            if unmet else "") + (
            f'<details class="met fold"><summary>{_pl(len(met), "check")} passed</summary>'
            '<ul class="gates">' + "".join(
                f'<li class="ok"><span class="ic">✓</span><div><b>{e(g.name)}</b>'
                f'<span>{e(g.detail)}</span></div></li>' for g in met) + "</ul></details>"
            if met else "")
        timing = self.timing_html(nt, near)
        w7 = c.s07_what_could_go_wrong
        n0, n1 = len(w7.counter_evidence), len(w7.alternative_mechanisms)
        risks = [f'<li>{line(s.text)} {_tag(s.provenance.value)}{flag(f"s07.{i}")}</li>'
                 for i, s in enumerate(w7.counter_evidence) if once(s.text)]
        risks += [f'<li>{line(s.text)} {_tag(s.provenance.value)}'
                  f'{flag(f"s07.{n0 + n1 + i}")}</li>'
                  for i, s in enumerate(w7.market_risks) if once(s.text)]
        watch = [f"<li>{line(s.text)}</li>" for s in w7.disconfirming_observables if once(s.text)]
        alt = [f'<li>{line(s.text)} {_tag(s.provenance.value)}</li>'
               for s in w7.alternative_mechanisms
               if not s.text.startswith("Registry link") and once(s.text)]
        dsn = c.s08_decision
        nxt = (f'<p>{line(dsn.next_step.text)}{flag("s08.next")}</p>'
               if once(dsn.next_step.text) else "")
        raise_ = [f"<li>{line(s.text)}</li>" for s in dsn.raise_priority_if if once(s.text)]
        lower = [f"<li>{line(s.text)}</li>" for s in dsn.lower_priority_if if once(s.text)]
        expo = exposure_html(c.s05_affected, groups, rc.groups_unread, rc.enrichment, v.version,
                             card_steps(c), set_card(rc.enrichment, rc.history))
        related = self.related_html(tid)
        evid, n_ev, per_src = self.evidence_html(c, rc)
        hist = "".join(
            f'<li><span class="hv">Version {h.version}</span><span>{e(_day(h.as_of))}</span>'
            f'{_chip(h.priority.research_action.value)}<span class="muted">'
            f'{e(self.version_how(h))}</span><span class="aud cc">'
            f'{e(clip(plain(h.change_summary), 400, _CARD))}</span></li>'
            for h in reversed(rc.history))
        def gave(aid: str) -> str:
            n, a = per_src.get(aid, (0, 0))
            return (f" · {n} cited" + (f", {a} against" if a else "")) if n else ""

        srcs = "".join(
            f'<li>{_link(s.url, clean_title(s.title, s.publisher) or "title not recorded")}'
            f'<div class="small">'
            f'{e(s.publisher)} · {e(_day(s.published_at))} · '
            f'{"read in full" if self.read_in_full(s, rc) else "preview only"}'
            f'{e(gave(s.article_id))}</div>'
            f'<span class="aud cc"> {e(s.article_id)}</span></li>' for s in c.s09_sources)
        # the card names its sections "01 BOTTOM LINE"; the list numbers them itself
        nine = "".join(f'<li><a href="{self.card_link(tid, 1, "sec-" + fid)}">'
                       f'{e(re.sub(r"^[0-9]+[ .]*", "", name).capitalize())}</a></li>'
                       for fid, name in SECTION_IDS)
        trace = "".join(f'<div class="cc">{e(x)}</div>' for x in v.priority.rules_fired) + "".join(
            f'<div class="cc">{e(f.factor_id)} = {e(f.value)} — {e(clip(f.note, 300, _CARD))}</div>'
            for f in v.priority.factors)
        none = '<p class="muted">No bottom line recorded.</p>'

        def folded(items: list[str], keep: int, one: str, many: str) -> str:
            if len(items) <= keep:
                return "".join(items)
            return ("".join(items[:keep]) + f'<li class="morewrap"><details class="fold">'
                    f'<summary>{_pl(len(items) - keep, "more " + one, "more " + many)}</summary>'
                    f'<ul>' + "".join(items[keep:]) + "</ul></details></li>")

        # THE TEAR SHEET (operator, 2026-10-15: "make the views how an expert would look at"):
        # the decision and its reasons beside the thesis and its key figures on the first
        # screen; who is exposed as rows; the long lists folded to counts. Nothing is dropped —
        # every line is one click away, and the card is the complete printed record.
        q = watch_of(v.priority, c.s05_affected)
        decide = (f'<aside class="decide"><h2>Why {e(_ACTION.get(action, (action,))[0])}'
                  + (f' · {e(q)}' if q else "") + '</h2>'
                  f'{why}{timing}'
                  + (f'<h3>Next step</h3>{nxt}' if nxt else "")
                  + ('<details class="fold"><summary>When to raise or lower priority</summary>'
                     + (f'<h3>Would raise priority</h3><ul>{"".join(raise_)}</ul>'
                        if raise_ else "")
                     + (f'<h3>Would lower priority</h3><ul>{"".join(lower)}</ul>'
                        if lower else "") + "</details>" if raise_ or lower else "")
                  + f'<div class="aud">{trace}</div></aside>')
        wrong = ('<section class="panel"><h2>What could prove it wrong</h2><ul class="risk">'
                 + (folded(risks, 3, "risk", "risks") or
                    "<li class=muted>None in the sources so far.</li>") + "</ul>"
                 + (f'<details class="fold"><summary>Signals to watch '
                    f'({len(watch)})</summary><ul class="risk">{"".join(watch)}</ul></details>'
                    if watch else "")
                 + (f'<details class="fold"><summary>Competing explanation</summary>'
                    f'<ul class="risk">{"".join(alt)}</ul></details>' if alt else "")
                 + "</section>")
        no_step = "<li class=muted>No earnings step stated by the source.</li>"
        chain = (f'<section class="panel"><h2>How it reaches fundamentals</h2><ol class="chain">'
                 f'{"".join(steps) or no_step}</ol></section>')
        what = (f'<p class="small">{e(moved)}</p>'
                + (f"<ul class=\"changed\">{folded(changed, 3, 'change', 'changes')}</ul>"
                   if changed else ""))
        review = (f'<section class="panel" id="review"><h2>Open review findings '
                  f'<small>{len(mine)}</small></h2><ul class="rvitems rvcompact">'
                  + "".join(self.finding_line(f) for f in mine) + "</ul></section>"
                  if mine else "")
        rel = (f'<section class="panel"><h2>Related theses</h2>{related}</section>'
               if related else "")
        # IS IT PRICED? beside the verdict — display only; the research action never reads it
        priced = market_html(rc.market, missing=(
            '<p class="muted">Not computed for this version — prices and filings as of a date, '
            '$0, no model call.</p>'
            + self.command_html(f"{CLI} market --as-of {self.run.as_of.isoformat()} "
                                f"--thesis {tid}")))
        q = (f'<section class="panel sheet q1"><div class="sheetmain"><h2>The thesis</h2>'
             f'{thesis or none}'
             + (f'<h3 class="numh">Key figures</h3><div class="nums">{fig_html}</div>'
                if fig_html else "")
             + f'<h3 class="numh">What changed</h3>{what}'
             + f'</div>{decide}</section>'
             + f'<section class="panel mkts"><h2>Is it priced?</h2>{priced}</section>'
             + f'<section class="panel"><h2>Who is exposed</h2>{expo}</section>'
             + f'<div class="grid2">{wrong}{chain}</div>'
             + (f'<div class="grid2">{review}{rel}</div>' if review and rel else review + rel))
        tabs = (f'<section class="tabs" data-tabs><div class="tabbar" role="tablist">'
                f'<button data-tab="ev" class="on">Evidence ({n_ev})</button>'
                f'<button data-tab="hi">History ({len(rc.history)})</button>'
                f'<button data-tab="src">Sources ({len(c.s09_sources)})</button>'
                f'<button data-tab="full">Full record</button></div>'
                f'<div data-panel="ev">{evid}</div>'
                f'<div data-panel="hi" hidden><ol class="timeline">{hist}</ol></div>'
                f'<div data-panel="src" hidden><ul class="plainlist srcl">{srcs}</ul></div>'
                f'<div data-panel="full" hidden><p>The complete nine-section Living Thesis Card — '
                f'every line with its label and citations, all evidence and counter-evidence, the '
                f'history and the audit record.</p><p><a class="btn" href="'
                f'{self.card_link(tid, 1)}">Open the full record</a> <a class="btn2" href="'
                f'{"../" + e(self.cards.get(tid, {}).get("print", f"cards/{tid}.print.html"))}">'
                f'Printable record</a></p><ol class="nine">{nine}</ol></div></section>')
        return self.page(t.title, head + q + tabs, "Themes", depth=1)

    @staticmethod
    def read_in_full(s: Any, rc: Any) -> bool:
        """A source row as READ NOW: a correction record overrides a stored FULL."""
        return s.retrieval_state is RetrievalState.FULL and s.article_id not in rc.retrieval_now

    @staticmethod
    def command_html(cmd: str) -> str:
        """The existing command for one row, folded (it may carry the document id it needs)."""
        if not cmd:
            return '<span class="small">nothing to do</span>'
        if not cmd.startswith(CLI):
            return f'<span class="small">{e(cmd)}</span>'
        verb = ("Release command" if "--release" in cmd else "Import command")
        return (f'<details class="cmdd"><summary>{verb}</summary><code class="cmd">{e(cmd)}'
                f'</code></details>')

    def version_how(self, h: ThesisVersion) -> str:
        """How a version came to be, in words — from its run's mode (the engine's change summary,
        with its factor codes, sits in the audit view)."""
        r = self.reg.runs.get(h.run_id)
        how = {"scan": "from the weekly scan", "article": "from a new article",
               "ingest": "from an uploaded document",
               "reanalyse": "from its articles analysed again under the current taxonomy",
               "reassess": "re-graded from stored evidence — no article read"}.get(
            r.mode if r else "", "run not recorded")
        return how + (" · includes an analyst correction"
                      if "ANALYST CORRECTION" in h.change_summary else "")

    def timing_html(self, nt: NearTerm, near: Gate) -> str:
        """The source's horizon FRAMING beside the dated near-term evidence — two statements, never
        two verdicts on one test (the Nomura presentation, 2026-10-13). The dated claims are folded;
        a date basis they all share is said once."""
        bases = {x.basis for x in nt.claims}
        common = next(iter(bases)) if len(bases) == 1 else ""
        rows = "".join(
            f'<li>{e(clip(x.claim.metric or x.claim.statement, 120, "the Evidence tab"))} — '
            f'{e(_TIMING_WORD.get(x.timing, x.timing))}'
            + ("" if common else f'; dated by {e(x.basis)}')
            + f'<span class="aud cc"> {e(x.claim.claim_id)} · {e(x.note)}</span></li>'
            for x in nt.claims[:8])
        more = (f'<li class="small">showing 8 of {len(nt.claims)}</li>' if len(nt.claims) > 8
                else "")
        conflict = (f'<div class="conflict"><b>Review required.</b> The near-term reading of '
                    f'record (“{e(nt.stored.replace("_", " "))}”) differs from its own cited '
                    f'claims re-dated today (“{e(nt.recomputed.replace("_", " "))}”). The research '
                    f'action of record stands until the thesis is reassessed.</div>' if nt.conflict
                    else "")
        return (f'<div class="timing"><h3>Timing</h3>{conflict}<ul class="gates"><li class="'
                f'{"ok" if near.ok else "unmet"}"><span class="ic">{"✓" if near.ok else "✗"}</span>'
                f'<div><b>{e(near.name)}</b><span>{e(near.detail)}</span></div></li></ul>'
                f'<p class="small">The source itself calls it <b>{e(nt.framing[:1].lower())}'
                f'{e(nt.framing[1:])}</b> — a description of the thesis, not a test.</p>'
                + (f'<details class="fold"><summary>Dated evidence ({len(nt.claims)})</summary>'
                   f'<ul class="small">{rows}{more}</ul>'
                   + (f'<p class="small">All dated by {e(common)}.</p>' if common else "")
                   + "</details>" if rows else "")
                + f'<div class="aud cc">{e(clip(nt.note, 400, _CARD))}</div></div>')

    def related_of(self, tid: str) -> tuple[dict[str, list[str]], set[str]]:
        """(direct links: another thesis → every reason, the same-broader-area theses) — ONE
        reading of the registry's links, which the reading page lists and Themes counts (U47,
        U32c: Themes said "2 related theses" of two area-root links the page folds away)."""
        if self._related is None:
            direct: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
            area: dict[str, set[str]] = defaultdict(set)
            for x in self.store.relations():
                a, b = x.from_thesis, x.to_thesis
                if a not in self.asof or b not in self.asof:
                    continue
                # a thesis filed at an AREA's root (no sub-node) is "parent" of every thesis in
                # the area: that link says only "same area" (Canada's power and minerals was
                # listed as related to HBM memory pricing, 2026-10-14) — the broader-area fold
                root = "." not in self.asof[a][0].key_node or "." not in self.asof[b][0].key_node
                if x.relation.value == "SIBLING" or (x.relation.value == "PARENT_CHILD" and root):
                    area[a].add(b)
                    area[b].add(a)
                else:
                    why = _RELATION.get(x.relation.value, x.relation.value.lower())
                    direct[a][b].append(why)
                    direct[b][a].append(why)
            # the broader area itself, read from the keys: the engine no longer links two theses
            # that only share an area (U43) — the stored links above are an older registry's
            by_sector: dict[str, list[str]] = defaultdict(list)
            for th, (tt, _v) in self.asof.items():
                if not tt.retired:
                    by_sector[tt.key_node.split(".")[0]].append(th)
            for members in by_sector.values():
                for i, a in enumerate(members):
                    for b in members[i + 1:]:
                        if same_area(self.asof[a][0].key_node, self.asof[b][0].key_node):
                            area[a].add(b)
                            area[b].add(a)
            by_art: dict[str, set[str]] = defaultdict(set)
            for th, arts in self.sources_of.items():
                if th in self.asof:
                    for aid in arts:
                        by_art[aid].add(th)
            shared: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
            for aid, ths in by_art.items():
                for th in ths:
                    for other in ths - {th}:
                        shared[th][other].add(aid)
            for th, others in shared.items():
                for other, aids in others.items():
                    names = sorted({(ar.publisher if (ar := self.reg.article(aid)) else
                                     "a source") for aid in aids})
                    direct[th][other].append(
                        f"shares {_pl(len(aids), 'source article')} ({', '.join(names)})"
                        f" — the same source, not independent confirmation")
            self._related = {th: ({o: list(rs) for o, rs in direct[th].items()},
                                  area[th] - set(direct[th])) for th in self.asof}
        return self._related.get(tid, ({}, set()))

    def related_html(self, tid: str) -> str:
        """Linked theses — never merged: direct links first, then theses sharing a source (the
        same source, not independent confirmation), then the same-broader-area siblings, folded."""
        why, sibling = self.related_of(tid)
        out = [f'<li><a href="{e(other)}.html">{e(self.title(other))}</a>'
               f'<div class="small">{e(self.area[other])} · {e("; ".join(rs))}</div></li>'
               for other, rs in sorted(why.items(), key=lambda kv: self.title(kv[0]))]
        siblings = [f'<li><a href="{e(other)}.html">{e(self.title(other))}</a>'
                    f'<div class="small">{e(self.area[other])}</div></li>'
                    for other in sibling]
        if not out and not siblings:
            return ""
        return ((f'<ul class="rel">{"".join(out)}</ul>' if out else "")
                + (f'<details class="more-rows fold"><summary>'
                   f'{_pl(len(siblings), "thesis", "theses")} in the same broader area</summary>'
                   f'<ul class="rel">{capped_li(sorted(siblings), "theses", "rel")}</ul>'
                   f'</details>' if siblings else ""))

    def evidence_html(self, c: Any, rc: Any
                      ) -> tuple[str, int, dict[str, tuple[int, int]]]:
        """The Evidence tab: what the figures say for and against the thesis, one line each —
        the value and what it measures; the source's own words one click away (provenance,
        on demand); against first. Also each source's contribution (figures, against)."""
        pub = {s.article_id: s for s in c.s09_sources}
        rows: list[tuple[str, dict[str, Any]]] = []
        for r in c.s04_key_evidence:
            rows.append((r.article_id, {"v": r.value_text, "u": unit_shown(r.value_text, r.unit),
                                        "label": figure_label(self.store, r.claim_id, r.label),
                                        "quote": r.quote, "period": r.period,
                                        "type": _EPI.get(r.epistemic.value, r.epistemic.value),
                                        "role": "key evidence", "id": r.claim_id}))
        key = {r.claim_id for r in c.s04_key_evidence}
        for cid, cl in rc.claims.items():
            if cid in key:
                continue
            role = rc.roles.get(cid, "")
            rows.append((cl.article_id, {
                "v": cl.value_text, "u": unit_shown(cl.value_text, cl.unit),
                "label": figure_label(self.store, cid, " — ".join(
                    z for z in (cl.scope, cl.metric) if z) or cl.statement),
                "quote": cl.quote, "period": cl.period,
                "type": _EPI.get(cl.epistemic.value, cl.epistemic.value),
                "role": {"contradicts": "against", "context": "context", "supports": "supports",
                         "competing": "competing"}.get(role, role or "cited"),
                "id": cid}))
        rows = _merge_restated(rows)

        def when(aid: str) -> datetime:
            s_ = pub.get(aid)
            return s_.published_at if s_ and s_.published_at else datetime.min.replace(tzinfo=UTC)

        def src_name(aid: str) -> str:
            s_ = pub.get(aid)
            return f"{s_.publisher} · {_day(s_.published_at)}" if s_ else "source"

        def item(aid: str, x: dict[str, Any], *, with_source: bool) -> str:
            kind = ("" if x["type"] in ("Observed", "Type not stated") else
                    f' <span class="tag">{e(x["type"].lower())}</span>')
            # a period the unit already says ("per year" after "$413 per year") is not repeated
            per = x["period"] if x["period"] and x["period"].lower() not in x["u"].lower() else ""
            when_ = f' <span class="muted">· {e(per)}</span>' if per else ""
            src = (f'<span class="muted"> — {e(src_name(aid))}</span>' if with_source else "")
            val = (f'<span class="v">{e(x["v"])}{" " + e(x["u"]) if x["u"] else ""}</span> '
                   if x["v"] else "")  # a statement has no number: no placeholder dash
            twice = (f' <span class="muted">· stated {len(x["quotes"])} times</span>'
                     if len(x["quotes"]) > 1 else "")
            quotes = "".join(f"<blockquote>“{e(q)}”</blockquote>" for q in x["quotes"])
            return (f'<li><details><summary>{val}{e(x["label"])}{when_}{kind}{twice}'
                    f'{src}</summary>{quotes}</details>'
                    f'<span class="aud cc">{e(" · ".join(x["ids"]))}</span></li>')

        groups: dict[str, list[Any]] = {"against": [], "support": [], "other": []}
        for aid, x in rows:
            grp = ("against" if x["role"] == "against" else
                   "support" if x["role"] in ("key evidence", "supports") else "other")
            groups[grp].append((aid, x))
        n_src = len({aid for aid, _x in rows})
        per_source: dict[str, tuple[int, int]] = {}
        for aid, x in rows:
            n, a = per_source.get(aid, (0, 0))
            per_source[aid] = (n + 1, a + (x["role"] == "against"))
        out = [f'<p class="evsum">{_pl(len(rows), "cited item")} from {_pl(n_src, "source")} · '
               f'{len(groups["support"])} supporting · '
               + (f'<b class="against">{len(groups["against"])} against</b>'
                  if groups["against"] else "none against")
               + (f' · {len(groups["other"])} context' if groups["other"] else "")
               + ' <span class="muted">— click a figure for the source\'s words</span></p>']
        if groups["against"]:
            ag = sorted(groups["against"], key=lambda r: when(r[0]), reverse=True)
            out.append(f'<h3 class="evh">Against the thesis <small>{len(ag)}</small></h3>'
                       f'<ul class="evl against">'
                       + capped_li([item(a, x, with_source=n_src > 1) for a, x in ag],
                                   "items", "evl against", cap=10) + "</ul>")
        if groups["support"]:
            out.append(f'<h3 class="evh">Supporting <small>{len(groups["support"])}</small></h3>')
            by: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for aid, x in groups["support"]:
                by[aid].append(x)
            for i, (aid, xs) in enumerate(sorted(by.items(), key=lambda kv: when(kv[0]),
                                                 reverse=True)):
                out.append(f'<details class="evg"{" open" if i == 0 else ""}><summary>'
                           f'<b>{e(src_name(aid))}</b> <span class="muted">'
                           f'{_pl(len(xs), "item")}</span></summary><ul class="evl">'
                           + capped_li([item(aid, x, with_source=False) for x in xs],
                                       "items", "evl", cap=10) + "</ul></details>")
        if groups["other"]:
            ot = sorted(groups["other"], key=lambda r: when(r[0]), reverse=True)
            out.append(f'<details class="evg"><summary><b>Context and other cited figures</b> '
                       f'<span class="muted">{len(ot)}</span></summary><ul class="evl">'
                       + capped_li([item(a, x, with_source=n_src > 1) for a, x in ot],
                                   "items", "evl", cap=10) + "</ul></details>")
        if not rows:
            return '<p class="muted">No cited evidence.</p>', 0, {}
        return "".join(out), len(rows), per_source

    # -- write ---------------------------------------------------------------------------------
    def write(self, out: Path) -> list[str]:
        tdir = out / "theses"
        tdir.mkdir(parents=True, exist_ok=True)
        for old in tdir.glob("TH-*.html"):  # a re-render REPLACES the set
            old.unlink()
        for old in out.glob("articles-*.html"):
            old.unlink()
        files = {"index.html": self.home(), "themes.html": self.themes(),
                 "review.html": self.review(), "uploads.html": self.uploads_page(),
                 "sources.html": self.sources_page()}
        for w in self.weeks:
            files[self.week_file(w)] = self.articles_page(w)
        for tid in self.asof:
            files[f"theses/{tid}.html"] = self.thesis_page(tid)
        for name, text in files.items():
            (out / name).write_text(text)
        return sorted(files)



CSS = THEME_CSS + """
table.mktt td.n{text-align:right;white-space:nowrap}.mkt .nh{color:var(--muted)}
.mkt td.mkw{color:var(--warn,#8a5a00);font-size:13px}
.mkt .mktl{margin:0 0 4px}.mkt .note{font-size:12.5px;color:var(--muted)}details.mkth{margin:6px 0}
h1{font-size:26px;line-height:1.2;margin:0 0 4px;letter-spacing:-.01em}
h2{font-size:17px;margin:0 0 12px}h2 small,h3 small{font-weight:500;color:var(--muted);
font-size:13px;margin-left:6px}h3{font-size:14px;margin:14px 0 6px}
.eyebrow{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);
font-weight:600}
.hero{margin-bottom:20px}.lede{font-size:16px;color:var(--ink2);margin:0 0 14px;max-width:820px}
.sum{font-size:15px;color:var(--ink2);margin:0 0 10px}
.hint{color:var(--muted);font-size:13px;margin:0 0 12px;max-width:820px}
.muted{color:var(--muted)}.nowrap{white-space:nowrap}.small{font-size:12.5px;color:var(--muted)}
.mt{margin-top:26px}
.strip{display:flex;gap:12px;flex-wrap:wrap}
.strip>*{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 16px;
min-width:150px;flex:1;color:var(--ink);display:flex;flex-direction:column;gap:1px}
.strip b{font-size:24px;line-height:1.15}
.strip span{font-size:13px;font-weight:600;color:var(--ink2)}
.strip small{font-size:12px;color:var(--muted)}
.strip a.warn b{color:var(--bad)}.strip a:hover{text-decoration:none;border-color:var(--accent)}
.cols{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:28px;align-items:start;
margin-bottom:30px}
aside{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:18px 18px 8px;
position:sticky;top:76px}
.att{list-style:none;margin:0;padding:0}.att li{padding:10px 0;border-top:1px solid var(--line);
font-size:14px;display:flex;flex-direction:column;gap:2px}.att li:first-child{border-top:0;
padding-top:0}.att li span{font-size:12.5px;color:var(--muted)}
.area{margin-bottom:20px}.area h3{font-size:12.5px;letter-spacing:.06em;text-transform:uppercase;
color:var(--muted);margin:0 0 8px}
.trow{display:block;background:var(--panel);border:1px solid var(--line);border-radius:12px;
padding:12px 16px;margin-bottom:8px;color:var(--ink)}
.trow:hover{border-color:var(--accent);text-decoration:none}
.ttop{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-bottom:4px}
.ttitle{font-weight:650;font-size:16px;line-height:1.35;margin-bottom:2px}
.tline{color:var(--ink2);font-size:14.5px}.tmeta{color:var(--muted);font-size:12.5px;margin-top:4px}
.clamp{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.gapi{color:var(--ink2)}
.ev{display:inline-block;font-size:11.5px;border:1px solid var(--line);border-radius:20px;
padding:1px 8px;color:var(--ink2);background:var(--panel);white-space:nowrap}
.ev.down{color:var(--bad);border-color:var(--bad-bg)}.ev.up{color:var(--ok)}.ev.new{color:var(--info)}
.ev.rv{color:var(--bad);background:var(--bad-bg);border-color:transparent}
.st{display:inline-block;border-radius:6px;padding:1px 8px;font-size:12.5px;white-space:nowrap}
.st.ok{color:var(--ok);background:var(--ok-bg)}.st.part{color:var(--watch);background:var(--watch-bg)}
.st.bad{color:var(--bad);background:var(--bad-bg)}.st.info{color:var(--info);background:var(--info-bg)}
.st.mute{color:var(--muted);background:var(--soft)}
table{border-collapse:collapse;width:100%;background:var(--panel)}
.hscroll{overflow-x:auto;border:1px solid var(--line);border-radius:12px;max-width:100%}
th{font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);text-align:left;
font-weight:600;padding:10px 14px;border-bottom:1px solid var(--line);background:var(--soft)}
td{padding:10px 14px;border-bottom:1px solid var(--line);vertical-align:top;font-size:14.5px}
tr:last-child td{border-bottom:0}
section{margin-bottom:28px}
code{font-size:12.5px;background:var(--soft);border-radius:4px;padding:1px 5px;
overflow-wrap:anywhere}
code.cmd{display:inline-block;white-space:normal}
aside code.cmd,.howto code.cmd{display:block;margin:4px 0;font-size:12px}.nw{white-space:nowrap}
.headsup{margin:12px 0 0;font-size:13.5px;color:var(--ink2)}
.steps4{list-style:none;padding:0;margin:12px 0 6px;display:grid;
grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}
.steps4 li{background:var(--soft);border-radius:8px;padding:10px 12px;font-size:13.5px}
.filters{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:0 0 12px}
.filters input:not([type=checkbox]),.filters select{font:inherit;font-size:14px;padding:7px 10px;
border:1px solid var(--line);border-radius:8px;background:var(--panel);color:var(--ink)}
.filters input#q{min-width:240px;flex:1}.filters label{display:inline-flex;gap:8px;
align-items:center;font-size:14px}
.weeks{display:flex;gap:6px;flex-wrap:wrap;padding-bottom:4px;max-width:100%}
.wk{white-space:nowrap;border:1px solid var(--line);border-radius:8px;padding:5px 10px;
font-size:13px;background:var(--panel);color:var(--ink2)}
.wk small{margin-left:6px;color:var(--muted)}.wk.on{border-color:var(--accent);color:var(--ink);
font-weight:600}
details summary{cursor:pointer;color:var(--accent);font-size:13.5px}
details.more-rows>summary{margin:8px 14px 12px}
details.agrp,details.ubk,details.quiet{background:var(--panel);border:1px solid var(--line);
border-radius:12px;padding:10px 16px;margin-bottom:10px}
details.agrp>summary,details.ubk>summary,details.quiet>summary{color:var(--ink);font-size:15px}
details.agrp .hscroll,details.ubk .hscroll{margin-top:10px}
.act{display:inline-flex;gap:2px;vertical-align:middle}.act i{width:9px;height:14px;
border-radius:2px;background:var(--line);display:block}.act i.on{background:var(--accent)}
.stale{display:inline-block;font-size:12px;color:var(--bad);margin-top:3px}
.rvlist{list-style:none;padding:0;margin:0}
.rvi{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 18px;
margin-bottom:10px}
.rvlist .panel li,.panel .rvlist li{padding:10px 0;border-top:1px solid var(--line)}
.rvhead{margin-bottom:6px}.line{font-size:15px}
.said{font-size:13.5px;color:var(--ink2);margin:4px 0}
.dec{font-size:13px;color:var(--bad);margin:4px 0}
.plainlist{padding-left:18px;margin:8px 0}.plainlist li{margin-bottom:10px}
.steps{padding-left:18px;margin:0 0 10px;font-size:14px}.steps li{margin-bottom:9px}
.hs{display:inline-flex;gap:2px;vertical-align:middle}.hs i{width:10px;height:14px;
border-radius:2px;display:block}
.h-healthy{background:var(--ok)}.h-degraded{background:var(--watch)}.h-blocked{background:var(--bad)}
.h-error{background:var(--bad)}.h-unknown{background:var(--line)}
.crumb{font-size:13px;color:var(--muted);margin-bottom:8px}
.th h1{font-size:28px;max-width:920px}.th .meta{display:flex;flex-wrap:wrap;gap:8px 12px;
align-items:center;color:var(--muted);font-size:13.5px;margin-bottom:18px}
.flag{background:var(--bad-bg);color:var(--bad);border-radius:6px;padding:2px 9px;font-size:13px}
.flagi{font-size:11.5px;color:var(--bad);margin-left:4px;white-space:nowrap}
.thesis{font-size:19px;line-height:1.55;margin:0;border-left:3px solid var(--accent);
padding-left:16px}
.tag{font-size:11px;color:var(--muted);border:1px solid var(--line);border-radius:4px;padding:0 5px;
white-space:nowrap;vertical-align:1px;margin-left:4px;background:var(--panel)}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:18px 20px;
margin-bottom:16px}
.grid2{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:16px;margin-bottom:16px}
.sheet{display:grid;grid-template-columns:minmax(0,1.55fr) minmax(0,1fr);gap:0 28px}
.sheet .decide{border-left:1px solid var(--line);padding-left:24px}
.sheet .decide h2{margin-top:0}.sheet .numh{margin:18px 0 8px}
.sheet .nums{grid-template-columns:repeat(auto-fit,minmax(160px,1fr))}
.rvcompact .rvi summary{cursor:pointer;display:flex;gap:8px;align-items:baseline;
list-style:none}.rvcompact .rvi summary::-webkit-details-marker{display:none}
.rvcompact .clamp1{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0;flex:1}
.rvcompact .said{font-size:13.5px;margin:6px 0}
.grid2 .panel{margin-bottom:0}
.nums{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}
.num{border:1px solid var(--line);border-radius:10px;padding:12px 14px}
.num b{font-size:24px;line-height:1.1}.num .unit{color:var(--muted);font-size:13px;margin-left:5px}
.num .lbl{display:block;font-size:13.5px;color:var(--ink2);margin-top:6px;line-height:1.35}
.num small{display:block;color:var(--muted);font-size:12px;margin-top:3px}
.chain{list-style:none;padding:0;margin:0;counter-reset:s}
.chain li{position:relative;padding:0 0 14px 34px;font-size:14.5px}
.chain li:before{counter-increment:s;content:counter(s);position:absolute;left:0;top:1px;width:22px;
height:22px;border-radius:50%;background:var(--accent-bg);color:var(--accent);font-size:12px;
font-weight:700;text-align:center;line-height:22px}
.sn{display:block;font-weight:650;font-size:13px}
.gates{list-style:none;padding:0;margin:0}.gates li{display:flex;gap:10px;padding:7px 0;
border-top:1px solid var(--line)}.gates li:first-child{border-top:0}
.gates .ic{width:20px;flex:none;font-weight:700}.gates .ok .ic{color:var(--ok)}
.gates .unmet .ic{color:var(--bad)}.gates b{display:block;font-size:14px;font-weight:600}
.gates span:not(.ic){font-size:13px;color:var(--muted)}
details.met{margin-top:8px}
.timing{border-top:1px solid var(--line);margin-top:12px;padding-top:4px}
.timing ul{padding-left:18px;margin:4px 0}
.conflict{background:var(--bad-bg);color:var(--bad);border-radius:8px;padding:8px 12px;
font-size:13.5px;margin:6px 0}
.risk,.next ul{padding-left:18px;margin:0;font-size:14.5px}.risk li{margin-bottom:6px}
.next p{font-size:15.5px;margin:0 0 6px}
.who{list-style:none;padding:0;margin:0 0 10px;font-size:14.5px}.who li{padding:5px 0;
border-top:1px solid var(--line)}.who li:first-child{border-top:0}.who .small{margin-top:2px}
.hypo{border:1px dashed var(--line);border-radius:10px;padding:10px 14px;margin:12px 0}
.hypo h3{margin:0 0 4px}.hypo h4{font-size:13px;margin:10px 0 2px;color:var(--ink2)}
.hypo .basis{color:var(--ink2)}
.hypo h4.cond{font-size:13px;font-weight:500;color:var(--ink2);margin:12px 0 4px}
.hrows{border-top:1px solid var(--line)}
details.hrow{border-bottom:1px solid var(--line)}
details.hrow>summary,.hhead{display:grid;grid-template-columns:64px minmax(0,220px) 130px
minmax(0,170px) 40px;gap:12px;align-items:baseline;padding:6px 2px;font-size:14px}
details.hrow>summary{cursor:pointer;list-style:none}
.hhead{font-size:11.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;
padding-top:2px}
details.hrow>summary::-webkit-details-marker{display:none}
details.hrow .tkr{font-family:ui-monospace,Menlo,monospace;font-size:12.5px;font-weight:600}
details.hrow .side.up{color:var(--ok)}details.hrow .side.down{color:var(--bad)}
details.hrow .earn{color:var(--muted);font-size:13px}details.hrow .ck{text-align:center}
.hbody{padding:2px 2px 10px 82px;font-size:13.5px}.hbody p{margin:4px 0}
.hbody .filing{color:var(--ink2);border-left:2px solid var(--line);padding-left:8px}
@media (max-width:880px){.hhead{display:none}
details.hrow>summary{display:flex;flex-wrap:wrap;gap:2px 10px}
details.hrow .tkr{width:52px}details.hrow>summary>b{flex:1 1 60%}
details.hrow .side{margin-left:62px}details.hrow .ck{margin-left:auto}.hbody{padding-left:0}
.rvcompact .rvi summary{flex-wrap:wrap}.rvcompact .clamp1{flex-basis:100%;white-space:normal}}
.tk{font-size:12px;color:var(--muted);border:1px solid var(--line);border-radius:6px;
padding:0 6px;margin-left:4px;white-space:nowrap}
.tabs{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:0 20px 18px}
.tabbar{display:flex;gap:4px;border-bottom:1px solid var(--line);margin:0 -20px 16px;padding:0 12px;
overflow-x:auto}
.tabbar button{border:0;background:none;padding:14px 10px;font:inherit;font-size:14px;
color:var(--ink2);border-bottom:2px solid transparent;cursor:pointer;white-space:nowrap}
.tabbar button.on{color:var(--ink);border-bottom-color:var(--accent);font-weight:600}
details.evg{border-top:1px solid var(--line);padding:8px 0}details.evg:first-child{border-top:0}
details.evg>summary{color:var(--ink);font-size:14.5px}details.evg .hscroll{margin-top:8px}
.q{color:var(--muted);font-size:13px;font-style:italic;margin-top:3px}
.timeline{list-style:none;padding:0;margin:0}.timeline li{display:flex;gap:12px;align-items:center;
padding:8px 0;border-top:1px solid var(--line);flex-wrap:wrap;font-size:14px}
.timeline li:first-child{border-top:0}.hv{font-weight:650;min-width:78px;white-space:nowrap}
.btn{display:inline-block;background:var(--accent);color:var(--panel);border-radius:8px;
padding:8px 14px;margin:0 8px 8px 0}
.btn2{display:inline-block;border:1px solid var(--line);border-radius:8px;padding:8px 14px}
.btn:hover,.btn2:hover{text-decoration:none}
.nine{columns:2;font-size:14px}
tr.xtra{display:none}.morebox:checked+.hscroll tr.xtra{display:table-row}
.morelbl{display:inline-block;margin:8px 2px 12px;font-size:13.5px;color:var(--accent);
cursor:pointer}
.morebox:checked~.morelbl{display:none}
.why{font-size:13px;color:var(--ink2);margin-top:3px}
details.cmdd{min-width:150px}details.cmdd code{display:block;margin-top:6px;word-break:break-all}
details.older{display:inline-block;margin-left:4px}details.older[open]{display:block}
td:empty{padding:0}
.bdg{display:inline-block;font-size:11.5px;border-radius:999px;padding:1px 8px;white-space:nowrap;
background:var(--soft);color:var(--ink2)}.bdg.bad{background:var(--bad-bg);color:var(--bad)}
.tmeta{display:flex;flex-wrap:wrap;gap:4px 10px;align-items:center}
.alist{list-style:none;padding:0;margin:0;border:1px solid var(--line);border-radius:12px;
background:var(--panel)}
.alist li{display:grid;grid-template-columns:170px minmax(0,1fr);gap:4px 14px;padding:10px 14px;
border-top:1px solid var(--line);align-items:start}.alist li:first-child{border-top:0}
.alist li>.st{justify-self:start}
.atl{font-weight:600;line-height:1.35}.aprod{font-size:13.5px;margin-top:3px}
.weeknav{display:flex;flex-wrap:wrap;gap:6px 16px;align-items:center;margin:6px 0;font-size:14px}
.weeknav details.older{display:inline-block}.weeknav details[open]{flex-basis:100%}
.weeknav .weeks{margin-top:8px}
.counts{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:13px;margin:8px 0}
.cnt{display:inline-flex;gap:5px;align-items:center}
.rvg{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px 18px 6px;
margin-bottom:10px}
.rvgh{display:flex;flex-wrap:wrap;gap:4px 10px;align-items:center;margin-bottom:2px}
.rvgh a{font-weight:650}
.rvitems{list-style:none;padding:0;margin:0}
.rvitems li.rvi{background:none;border:0;border-top:1px solid var(--line);border-radius:0;
padding:10px 0 8px;margin:0}.rvitems li.rvi:first-child{border-top:0}
.rvmeta{display:flex;flex-wrap:wrap;gap:4px 14px;align-items:center;font-size:12.5px;
color:var(--muted);margin-top:4px}
.clamp2{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.clamp3{display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.uilist{list-style:none;padding:0;margin:8px 0 0}
.ui{display:grid;grid-template-columns:minmax(0,1fr) 230px 150px;gap:6px 18px;padding:12px 0;
border-top:1px solid var(--line);align-items:start}.uilist>.ui:first-child{border-top:0}
.uiside{font-size:13.5px}.uiact{font-size:13px}
details.fold{margin-top:8px}details.fold>summary{font-size:13px}
.pillcheck{border:1px solid var(--line);border-radius:999px;padding:4px 12px;
background:var(--panel)}
.meta2{font-size:13px;color:var(--muted);margin:-10px 0 16px}
.rel{list-style:none;padding:0;margin:0}.rel li{margin:0 0 10px}
.evsum{font-size:14px;color:var(--ink2);margin:0 0 6px}.evsum .against{color:var(--bad)}
.evh{font-size:14px;margin:18px 0 4px}
.evl{list-style:none;padding:0;margin:0}.evl>li{border-top:1px solid var(--line);padding:7px 0}
.evl>li:first-child{border-top:0}
.evl details>summary{cursor:pointer;color:var(--ink);font-size:14px;list-style:none;
line-height:1.45}
.evl details>summary::-webkit-details-marker{display:none}
.evl details>summary::before{content:"▸";color:var(--muted);font-size:10px;
margin-right:8px}
.evl details[open]>summary::before{content:"▾"}
.evl .v{font-weight:650;margin-right:4px}.evl.against .v{color:var(--bad)}
.evl blockquote{margin:6px 0 2px 18px;padding:4px 10px;border-left:3px solid var(--line);
color:var(--muted);font-style:italic;font-size:13px}
details.evg{margin:10px 0 0}details.evg>summary{font-size:14px;color:var(--ink)}
.srcl li{margin:0 0 10px}
.arts tr[data-hassub] td{border-bottom:0}.arts td.subrow{padding-top:0;font-size:13px}
.compl>li{margin:0 0 10px}.compl ul{margin:4px 0 0;padding-left:18px}
.grid2{align-items:start}
.testdata{background:#3b2a00;color:#ffe9b0;font-size:12.5px;padding:6px 20px;text-align:center}
.foot{margin:18px 0 0;font-size:12.5px;color:var(--muted)}
.hit{outline:2px solid var(--accent);outline-offset:3px}
details.agrp>summary .muted,details.ubk>summary .muted{margin-left:10px;font-size:13px}
.ml{display:none}.arts.artt{table-layout:fixed}.arts.artt th:nth-child(1){width:110px}
.arts.artt th:nth-child(3){width:170px}.arts.artt th:nth-child(5){width:180px}
.arts.themes{table-layout:fixed}.arts.themes th:nth-child(2){width:156px}
.arts.themes th:nth-child(3){width:140px}.arts.themes th:nth-child(4),
.arts.themes th:nth-child(5){width:84px}.arts.themes th:nth-child(6){width:170px}
@media (max-width:880px){.cols{grid-template-columns:minmax(0,1fr)}
aside{position:static;min-width:0}
.ui{grid-template-columns:1fr;gap:4px}.alist li{grid-template-columns:1fr}
.steps4{grid-template-columns:1fr}
.grid2{grid-template-columns:1fr}.sheet{grid-template-columns:1fr}
.sheet .decide{border-left:0;padding-left:0;border-top:1px solid var(--line);margin-top:16px}
h1{font-size:24px}.th h1{font-size:22px}.thesis{font-size:17px}.nine{columns:1}
.filters input#q{min-width:0;width:100%;flex-basis:100%}
.arts,.arts tbody,.arts tr,.arts td{display:block;width:100%}
.arts tr:first-child{display:none}.arts tr{padding:12px 14px;border-bottom:1px solid var(--line)}
.arts td{border:0;padding:2px 0}.arts td:empty{display:none}.hscroll{border-radius:10px}
.arts tr.xtra{display:none}.morebox:checked+.hscroll .arts tr.xtra{display:block}
.ml{display:inline;color:var(--muted);font-size:12.5px}
.tabbar{flex-wrap:wrap;overflow:visible}.tabbar button{padding:10px 8px}}
@media print{.tabbar,.filters{display:none}[data-panel]{display:block!important}}
"""

#: the desk's behaviour — tabs, filters, sorts, "show all" — ONE script for the standalone pages
#: (inline) and the main app's Theme intelligence section (published as desk.js, run on each view
#: it shows): `deskInit(root, params)` wires one rendered page; the filters are global functions
#: the page's controls call.
JS = """function rowsOf(sel){return Array.prototype.slice.call(document.querySelectorAll(sel))}
function openAll(root){rowsOf(root+' details.more-rows').forEach(function(d){d.open=true});
rowsOf('input.morebox').forEach(function(b){b.checked=true})}
function recap(root){rowsOf(root+' table[data-cap],table'+root+'[data-cap]').forEach(
function(t){var cap=+t.dataset.cap,k=0;
Array.prototype.slice.call(t.rows).forEach(function(r){if(r.querySelector('th'))return;
if(!r.hasAttribute('data-sub')&&r.style.display!=='none')k++;r.classList.toggle('xtra',k>cap)});
var l=document.querySelector('label[for="'+t.dataset.box+'"]');if(l){l.style.display=k>cap?'':
'none';if(k>cap)l.textContent='Showing '+cap+' of '+k+' '+t.dataset.what+' \u2014 show all '+k}})}
function flt(){var q=(document.getElementById('q').value||'').toLowerCase(),
s=document.getElementById('fs').value,a=document.getElementById('fa').value,
ar=document.getElementById('far').value,n=0,all=rowsOf('#tt tr[data-area]');
if(q||a||ar)openAll('#tt');
all.forEach(function(r){var ok=(!s||r.dataset.status===s)&&(!a||r.dataset.action===a)&&
(!ar||r.dataset.area===ar)&&(!q||(r.textContent+' '+r.dataset.area).toLowerCase().indexOf(q)>=0);
r.style.display=ok?'':'none';n+=ok?1:0});
rowsOf('#tt details[data-grp]').forEach(function(g){var v=Array.prototype.slice.call(
g.querySelectorAll('tr[data-area]')).some(function(r){return r.style.display!=='none'});
g.style.display=v?'':'none';if(q||a||ar)g.open=v});recap('#tt');
document.getElementById('cnt').textContent=n+' of '+all.length+' match'}
function srt(){var k=document.getElementById('so').value;var v=function(r){return k==='upd'?
-r.dataset.upd:k==='stale'?+r.dataset.left:k==='src'?-r.dataset.src:k==='rv'?-r.dataset.rv:
+r.dataset.ord};
rowsOf('#tt table').forEach(function(t){var rs=Array.prototype.slice.call(t.querySelectorAll(
'tr[data-area]'));rs.sort(function(a,b){return v(a)-v(b)||a.dataset.ord-b.dataset.ord})
.forEach(function(r){(r.parentNode).appendChild(r)})});recap('#tt')}
function fa(){var r=document.getElementById('fr').value,p=document.getElementById('fp').value,n=0,
all=rowsOf('#at tr[data-state]');if(r||p)openAll('#at');all.forEach(function(x){var ok=
(!r||x.dataset.state===r)&&(!p||x.dataset.pub===p);x.style.display=ok?'':'none';n+=ok?1:0});
rowsOf('#at tr[data-sub]').forEach(function(x){var t=x.previousElementSibling;
x.style.display=t&&t.style.display==='none'?'none':''});recap('#at');
document.getElementById('cnt2').textContent=n+' of '+all.length+' match'}
function fr2(){var d=document.getElementById('fdec').checked,rn=document.getElementById('frn')
.checked,o=document.getElementById('fold').checked,n=0,all=rowsOf('#rv li.rvi');
if(d||rn||o)openAll('#rv');all.forEach(function(x){var ok=(!d||x.dataset.dec==='1')&&(!rn||
x.dataset.act==='RESEARCH NOW')&&(!o||+x.dataset.age>=28);x.style.display=ok?'':'none';
n+=ok?1:0});rowsOf('#rv li.rvg').forEach(function(g){g.style.display=Array.prototype.slice
.call(g.querySelectorAll('li.rvi')).some(function(x){return x.style.display!=='none'})?'':'none'});
document.getElementById('cnt3').textContent=n+' of '+all.length+' match'}
function deskInit(root,u){root.querySelectorAll('[data-tabs]').forEach(function(g){
var b=g.querySelectorAll('[data-tab]'),p=g.querySelectorAll('[data-panel]');b.forEach(function(x){
x.addEventListener('click',function(){b.forEach(function(y){y.classList.toggle('on',y===x)});
p.forEach(function(q){q.hidden=q.dataset.panel!==x.dataset.tab})})})});
if(document.getElementById('tt')){if(u.get('area'))document.getElementById('far').value=
u.get('area');if(u.get('sort'))document.getElementById('so').value=u.get('sort');srt();flt()}
if(document.getElementById('at'))fa();if(document.getElementById('rv'))fr2()}
window.addEventListener('beforeprint',function(){rowsOf('details').forEach(function(d){
d.open=true});rowsOf('input.morebox').forEach(function(b){b.checked=true})});
"""
