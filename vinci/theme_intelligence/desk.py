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

import html
import re
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from vinci.theme_intelligence.cards import (
    AUDIT_TOGGLE,
    REVEAL_JS,
    STEP_LABEL,
    _anchor,
    _clean_display,
    _plain_text,
    e,
    foot_html,
    ids_to_audit,
    review_not_run_words,
    unit_shown,
    why_reasons,
)
from vinci.theme_intelligence.config import STALE_AFTER_DAYS, load_sources, load_taxonomy
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
    report_runs,
    review_carry,
    source_health_as_of,
    theses_as_of_run,
)
from vinci.theme_intelligence.schemas import (
    SECTION_IDS,
    Claim,
    CompletenessReport,
    DocumentRecord,
    Provenance,
    ResearchAction,
    RetrievalState,
    RunStatus,
    Thesis,
    ThesisStatus,
    ThesisVersion,
    WeeklyRun,
)
from vinci.theme_intelligence.store import Store
from vinci.theme_intelligence.timewindow import timing_of, window_of
from vinci.theme_intelligence.verify import card_sentences

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
    "financials": "Financials", "healthcare": "Healthcare", "industrials": "Industrials",
    "consumer": "Consumer", "materials": "Materials", "real_estate": "Real estate",
    "telecom_media": "Telecom & media", "utilities": "Utilities", "other": "Unclassified"}

NEAR_GATE = "Near-term relevance (next 2–4 quarters)"
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


def unit_of(value_text: str | None, unit: str | None) -> str:
    """The unit printed after a value — none after a value written in words ("more than four
    times", "doubling"): the words already carry it."""
    words = re.sub(r"\b(?:around|about|roughly|approximately|nearly|over|under)\b", "",
                   value_text or "")
    return "" if re.search(r"[A-Za-z]{3,}", words) else unit_shown(value_text, unit)


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


def week_articles(reg: _Registry, week: Week, *, latest: bool) -> list[ArticleRow]:
    """Every article of `week`: analysed in full or as a preview (with what it produced, its open
    completeness items and coverage alerts), failed, blocked, held, or — for the latest week —
    queued for the next run."""
    store = reg.store
    rids = week.run_ids
    rows: dict[str, ArticleRow] = {}
    for r in week.runs:
        if r.mode == "reassess":  # a re-grade of stored evidence reads no article
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
                    key=aid, title=html.unescape(a.title or "") or "title not recorded",
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
                    [f"Figure {f.figure!r} not captured — "
                     f"{_OPEN_CAUSE.get(f.open_cause or '', 'not accounted for')}"
                     for f in rep.figures if f.status == "uncaptured"]
                    + [f"One argument paragraph not accounted for — "
                       f"{_OPEN_CAUSE.get(b.open_cause or '', 'not accounted for')}"
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
        if row.state == "PARTIAL":
            row.follow_up = "Supply the full report — see Uploads"
        elif row.open_items:
            row.follow_up = f"{_pl(len(row.open_items), 'completeness item')} to check"
    # manual runs that FAILED: their article listed as failed — or, when a later run of the week
    # completed it, as completed after the failed attempt(s)
    for fr in week.failed:
        for aid in sorted({str(c["ref"]) for c in store.llm_calls(fr.run_id)
                           if c.get("purpose") == "extract"}):
            err = next((w for w in fr.warnings if w.startswith("RUN ERROR")), "")
            if aid in rows:
                rows[aid].notes.append("Completed after a failed attempt (the analysis stopped "
                                       "with an error; nothing from it was recorded).")
                rows[aid].audit.append(f"failed attempt {fr.run_id}: {err.splitlines()[0][:160]}"
                                       if err else f"failed attempt {fr.run_id}")
                continue
            a = reg.article(aid)
            later = sorted({reg.runs[c.run_id].as_of for c in reg.by_article.get(aid, [])
                            if c.run_id in reg.runs
                            and reg.runs[c.run_id].started_at > fr.started_at})
            rows[aid] = ArticleRow(
                key=aid, title=html.unescape(a.title or "") if a else "title not recorded",
                publisher=a.publisher if a else "publisher not recorded",
                source_id=a.source_id if a else "", url=a.canonical_url if a else "",
                published=_todate(a.published_at) if a else None, state="FAILED",
                notes=["The analysis stopped with an error; nothing from it was recorded."]
                + ([f"Completed in a later run (analysed as of {_day(later[0])})."]
                   if later else []),
                follow_up="" if later else "Re-run the article", article_id=aid,
                audit=[f"{aid} · failed run {fr.run_id}"
                       + (f": {err.splitlines()[0][:160]}" if err else "")])
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
                key=url, title=(html.unescape(a.title or "") if a else "")
                or str(pay.get("title") or "") or "title not recorded",
                publisher=a.publisher if a else reg.publisher(sid), source_id=sid, url=url,
                published=_todate(a.published_at) if a else None, state=state,
                notes=[_CHECKPOINT_WHY[state].capitalize() + "."],
                follow_up=("Upload a copy you hold — see Uploads"
                           if state in ("BLOCKED", "NO_BODY") else
                           "Re-run in the next scan" if state == "FAILED" else ""),
                article_id=cid or None, audit=[f"scan {r.run_id}: {status}"
                                               + (f" · {cid}" if cid else "")])
    # documents supplied this week that were not analysed
    for d in reg.documents:
        if d.run_id not in rids or d.status in ("INGESTED", "UPGRADED"):
            continue
        rows[d.doc_id] = ArticleRow(
            key=d.doc_id, title=d.title or f"untitled document ({d.filename})",
            publisher=d.publisher, source_id=d.source_id, url=d.declared.get("url", ""),
            published=d.published, state=d.status if d.status in ARTICLE_STATE else "FAILED",
            route="upload", notes=[_doc_why(d)], follow_up="See Uploads",
            audit=[f"document {d.doc_id} · {d.status}"])
    if latest:
        for url, _st, pay in store.candidates("QUEUED"):
            sid = str(pay.get("source_id") or "")
            pub = pay.get("published")
            rows[url] = ArticleRow(
                key=url, title=str(pay.get("title") or "") or "title not recorded",
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


def gates(v: ThesisVersion, groups: list[str], nt: NearTerm) -> list[Gate]:
    """The Research Now conditions, each met or not, read from the stored factor VALUES (the rule
    trace stays in the audit view). The near-term condition is stated ONCE, from the factor of
    record — the source's horizon framing is shown apart and is never a pass/fail."""
    f = {x.factor_id: x.value for x in v.priority.factors}
    av = v.content.s05_affected
    n = f.get("F2_material_evidence", "0")
    f4 = f.get("F4_profit_transmission", "absent")
    near_ok, near_words = near_term_words(nt)
    exposed = not f.get("F6_recognizable_exposures", "").startswith("0 listed · 0 sector")
    f12 = f.get("F12_fundamental_inflection", "")
    cat = f.get("F7_dislocation_or_catalyst") == "present" or f12 == "qualifies"
    out = [
        Gate(n not in ("0", ""), "Verified evidence",
             _pl(int(n) if n.isdigit() else 0, "verified figure or event",
                 "verified figures or events")
             if n not in ("0", "") else "no verified material evidence"),
        Gate(f4 != "absent", "A stated route to profits",
             {"source-shown": "the source states how it reaches earnings",
              "inferred": "inferred — the source does not state the earnings step"}.get(
                 f4, "a market-regime record — no earnings mechanism argued"
                 if f4.startswith("n/a") else "no earnings step (a price move is not one)")),
        Gate(near_ok, NEAR_GATE, near_words),
        Gate(exposed, "An exposure the source names",
             ("sectors: " + ", ".join(s.name for s in av.sector_exposures)
              if av.sector_exposures else "listed companies named")
             if exposed else ("business groups only (" + "; ".join(groups) + ") — not companies"
                              if groups else "no company or sector named as exposed")),
        Gate(cat, "A dislocation, a dated catalyst or a measured change",
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


def _ingest_cmd(sid: str, url: str = "") -> str:
    return (f"{CLI} ingest-file --path <your copy> --source {sid}"
            + (f" --url {url}" if url else "") + " --llm-permitted")


def upload_items(reg: _Registry, health: dict[str, Any],
                 checkpoints: list[tuple[str, str, date]]) -> list[UploadItem]:
    """Everything the operator can supply or clear, registry-wide — never dismissed by age."""
    store = reg.store
    out: list[UploadItem] = []
    upload_issue = {i.ref_id: i.detail for i in store.issues()
                    if i.code == "LINKED_REPORT_UPLOAD"}
    unread = {d.article_id: d for d in reg.documents if d.quarantined and d.article_id}
    for a in store.articles():
        vs = [v for v in reg.versions(a.article_id)
              if v.retrieval_state is not RetrievalState.BLOCKED]
        if not vs or vs[-1].retrieval_state is not RetrievalState.PARTIAL:
            continue
        doc = unread.get(a.article_id)
        if doc is not None:
            kinds = {q.kind for q in doc.quarantined}
            if kinds == {"back_matter"}:
                continue  # its analysis text is whole — never an awaited document
            pages = sorted(q.page for q in doc.quarantined)
            out.append(UploadItem(
                kind="visual", title=html.unescape(a.title or "") or "title not recorded",
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
               f"only a preview could be read ({vs[-1].body_word_count:,} words)")
        out.append(UploadItem(
            kind="full_report", title=html.unescape(a.title or "") or "title not recorded",
            publisher=a.publisher, source_id=a.source_id, published=_todate(a.published_at),
            first_seen=_todate(a.first_seen_at), why=why,
            command=_ingest_cmd(a.source_id, a.canonical_url), url=a.canonical_url,
            audit=a.article_id + (f" · {upload_issue[a.article_id][:200]}"
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
        cid = str(pay.get("article_id") or "")
        art = reg.article(cid) if cid else None
        out.append(UploadItem(
            kind="blocked_article",
            title=(html.unescape(art.title or "") if art else "") or str(pay.get("title") or "")
            or "title not recorded", publisher=art.publisher if art else reg.publisher(sid),
            source_id=sid, published=_todate(art.published_at) if art else None,
            first_seen=seen, why=_CHECKPOINT_WHY[_CHECKPOINT[status]],
            command=_ingest_cmd(sid or "<source>", url), url=url,
            audit=f"scan outcome {status}" + (f" · {cid}" if cid else "")))
    rows = {r["source_id"]: r for r in health.get("rows", [])}
    for sid, src in reg.sources.items():
        row = rows.get(sid, {})
        ma = row.get("manual_action") or {}
        manual_first = src.mode == "manual_first"
        if not manual_first and ma.get("kind") != "UPLOAD_REQUIRED":
            continue
        out.append(UploadItem(
            kind="channel", title=f"New research from {src.publisher}", publisher=src.publisher,
            source_id=sid, published=None, first_seen=None,
            why=("a manual-first channel — the weekly scan does not read it; upload any new "
                 "report you hold" if manual_first else
                 f"automated access is {str(row.get('status', 'UNKNOWN')).lower()} — upload "
                 f"the reports you hold, starting with the articles listed"),
            command=_ingest_cmd(sid), detail=[str(x) for x in ma.get("affected", [])],
            audit=f"health {row.get('status', 'UNKNOWN')}" + (f" · {row.get('reason', '')[:160]}"
                                                              if row else "")))
    for d in reg.documents:
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
                detail=[f"resembles “{html.unescape(like.title or '')}” ({like.publisher})"]
                if like else [], audit=f"document {d.doc_id} · {d.match_basis[:160]}"))
        elif d.status in ("REJECTED", "FAILED"):
            out.append(_doc_item(d, "rejected", _doc_why(d),
                                 "Save it as PDF or text with a readable text layer, then "
                                 "import it again", audit=f"document {d.doc_id} · "
                                                          f"{plain(last)[:160]}"))
        elif d.status in ("INGESTED", "UPGRADED"):
            made = sorted({c.thesis_id for c in reg.by_article.get(d.article_id or "", [])
                           if c.run_id == d.run_id})
            out.append(_doc_item(
                d, "done", "a fuller copy of an article already held — the same article, "
                           "re-checked" if d.status == "UPGRADED" else "imported as a new article",
                "", theses=made, audit=f"document {d.doc_id} · {d.article_id or ''}"))
    return out


def _doc_item(d: DocumentRecord, kind: str, why: str, command: str, *,
              detail: list[str] | None = None, theses: list[str] | None = None,
              audit: str = "") -> UploadItem:
    return UploadItem(kind=kind, title=d.title or f"untitled document ({d.filename})",
                      publisher=d.publisher, source_id=d.source_id, published=d.published,
                      first_seen=d.received_at.date(), why=why, command=command,
                      url=d.declared.get("url", ""), detail=detail or [], theses=theses or [],
                      audit=audit)


# --- the desk ----------------------------------------------------------------------------------

def _chip(action: str) -> str:
    w, cls = _ACTION.get(action, (action.title(), "skip"))
    return f'<span class="chip {cls}">{e(w)}</span>'


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
                 generated: str) -> None:
        self.store, self.run, self.generated = store, run, generated
        self.reg = _Registry(store)
        self.weeks = desk_weeks(store, run)
        if not self.weeks:
            raise ValueError(f"run {run.run_id} has no week to report")
        self.week = self.weeks[-1]
        self.asof: AsOf = theses_as_of_run(store, run)
        self.cards = cards
        self._uid = 0
        self.d: Dashboard = build_dashboard(store, run.run_id, cards=cards, generated=generated,
                                            runs=list(self.week.runs))
        self.rows: list[DashRow] = [r for rs in self.d.categories.values() for r in rs]
        self.week_of_run = {r.run_id: w.key for w in self.weeks for r in (*w.runs, *w.failed)}
        self.articles = {w.key: week_articles(self.reg, w, latest=w is self.week)
                         for w in self.weeks}
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
        self.groups: dict[str, list[str]] = {}
        self.sources_of: dict[str, set[str]] = defaultdict(set)
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
        rest = [r.replace("<tr", '<tr class="xtra"', 1) for r in rows[cap:]]
        return (f'<input type="checkbox" class="morebox" id="{uid}" hidden>'
                f'<div class="hscroll"><table class="arts {cls}"{idattr}>{head}'
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
        groups = self.groups.get(tid)
        if groups is None:
            groups = self.groups[tid] = [g.name for g in card_context(
                self.store, t, v, generated="", until=self.run.finished_at).groups]
        return [g.name for g in gates(v, groups, self.near[tid]) if not g.ok]

    def page(self, title: str, body: str, active: str, depth: int = 0) -> str:
        up = "../" * depth
        nav = "".join(f'<a href="{up}{h}"{" class=on" if n == active else ""}>{n}</a>'
                      for n, h in NAV)
        banner = ""
        if self.test_articles:
            banner = (f'<div class="testdata">TEST DATA — this registry holds articles from a '
                      f'reserved test domain ({self.test_articles} of {self.n_articles} articles; '
                      f'the rest are supplied documents or other sources). This is not research.'
                      f'</div>')
        return ("<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport "
                "content='width=device-width,initial-scale=1'><title>" + e(title)
                + " · Research desk</title><style>" + CSS + "</style></head><body>"
                + AUDIT_TOGGLE + banner + f'<header class="top"><div class="in"><a class="brand" '
                f'href="{up}index.html">Mosaic Theory <small>Research desk</small></a><nav>{nav}'
                f'</nav><label for="audit" class="auditbar" title="Show engine ids, codes and the '
                f'decision trace">Audit view</label></div></header><main class="wrap">{body}'
                + foot_html(self.generated)
                + f'<div class="foot"><a href="{up}dashboard.html">Full weekly report</a> · '
                  f'<a href="{up}report_print.html">Printable report</a></div></main>'
                + "<script>" + JS + "</script>" + REVEAL_JS + "</body></html>")

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
            rs = sorted(rs, key=lambda r: (_RANK.get(r.action, 3), r.title))
            rows = [self.change_row(r) for r in rs]
            sec.append(f'<div class="area"><h3>{e(name)} <small>{_theses(len(rs))}</small></h3>'
                       f'{capped(rows, "theses", 8)}</div>')
        if d.no_evidence:
            sec.append('<details class="quiet"><summary>' + _pl(len(d.no_evidence), "proposition")
                       + " with no verified evidence — recorded, never a research candidate"
                       "</summary><ul>" + "".join(
                           f'<li><a href="{self.thesis_link(r.thesis_id)}">{e(r.title)}</a></li>'
                           for r in d.no_evidence) + "</ul></details>")
        att = []
        if self.open:
            n_t = len({f.thesis_id for f in self.open})
            att.append(f'<li><a href="review.html"><b>{_pl(len(self.open), "finding")}</b> open on '
                       f'{_theses(n_t, "active")}'
                       f'{f" — {decisive} bear on a research action" if decisive else ""}</a></li>')
        if waiting:
            att.append(f'<li><a href="uploads.html"><b>{_pl(len(waiting), "upload item")}</b> — '
                       f'documents to supply or clear</a></li>')
        if bad:
            att.append(f'<li><a href="articles.html"><b>{_pl(len(bad), "article")}</b> failed or '
                       f'blocked this week</a></li>')
        soon = [t for t, _v in active
                if STALE_AFTER_DAYS - (w.end - t.last_material_update).days <= 21]
        if soon:
            att.append(f'<li><a href="themes.html?sort=stale"><b>{_theses(len(soon))}</b> '
                       f'archive within three weeks unless new evidence arrives</a></li>')
        blocked = [r["publisher"] for r in self.health.get("rows", [])
                   if r["status"] in ("BLOCKED", "ERROR", "DEGRADED")]
        if blocked:
            att.append(f'<li><a href="sources.html"><b>{_pl(len(blocked), "source")}</b> blocked '
                       f'or degraded ({e(", ".join(blocked))})</a></li>')
        produced = self.produced_table(arts, cap=10)
        a_counts: dict[str, list[Thesis]] = defaultdict(list)
        for t, _v in active:
            a_counts[self.area[t.thesis_id]].append(t)
        changed = {r.thesis_id for r in self.rows}
        recent = self.weeks[-12:]
        def n_now(ts: list[Thesis]) -> int:
            return sum(1 for t in ts if self.asof[t.thesis_id][1].priority.research_action
                       is ResearchAction.RESEARCH_NOW)

        arow = [
            f'<tr><td><a href="themes.html?area={e(a)}">{e(a)}</a></td><td>{len(ts)}</td>'
            f'<td>{sum(1 for t in ts if t.thesis_id in changed) or "—"}</td>'
            f'<td>{n_now(ts) or "—"}</td><td>'
            f'{_strip(recent, set().union(*[self.activity[t.thesis_id] for t in ts]))}</td></tr>'
            for a, ts in sorted(a_counts.items(), key=lambda kv: (-len(kv[1]), kv[0]))]
        body = (
            f'<section class="hero"><div class="eyebrow">Weekly research brief</div>'
            f'<h1>{e(w.label)}</h1><p class="lede"><b>{_pl(len(read), "article")} read</b> '
            f'({full} in full, {len(read) - full} preview only)'
            f'{f", {queued} queued" if queued else ""}'
            f'{f", {len(bad)} failed or blocked" if bad else ""}. They created '
            f'<b>{_pl(new, "thesis", "theses")}</b> and changed {len(self.rows) - new}: '
            f'{ups} upgraded, {downs} downgraded'
            + (f" (and {_pl(len(d.no_evidence), 'proposition')} with no verified evidence)"
               if d.no_evidence else "")
            + f'. <b>{_theses(len(active), "active")}</b>, {rn} at Research Now.</p>'
            f'<div class="strip"><a href="articles.html"><b>{len(read)}</b><span>Articles read · '
            f'{full} in full</span></a><div><b>{len(self.rows)}</b><span>Theses created or changed'
            f'</span></div><a href="themes.html"><b>{rn}</b><span>Research Now (active)</span></a>'
            f'<a href="review.html" class="{"warn" if decisive else ""}"><b>{len(self.open)}</b>'
            f'<span>Findings to review · {decisive} decision-affecting</span></a>'
            f'<a href="uploads.html" class="{"warn" if waiting else ""}"><b>{len(waiting)}</b>'
            f'<span>Upload items</span></a></div></section>'
            f'<div class="cols"><section class="main"><h2>Thesis changes by research area</h2>'
            f'<p class="hint">Only theses created or changed this week. Every thesis is under '
            f'<a href="themes.html">Themes</a>.</p>'
            + ("".join(sec) or '<p class="muted">No thesis was created or changed.</p>')
            + '<h2 class="mt">What each article produced</h2>' + produced
            + '</section><aside><h2>Needs your attention</h2><ul class="att">'
            + ("".join(att) or '<li class="muted">Nothing outstanding.</li>')
            + "</ul></aside></div>"
            f'<section><h2>Active theses by area <small>{_pl(len(active), "thesis", "theses")} in '
            f'{_pl(len(a_counts), "area")}</small></h2>'
            + self.table("areas", f'<tr><th>Area</th><th>Active</th><th>Changed this week</th>'
                                  f'<th>Research Now</th><th>Weeks with new evidence (last '
                                  f'{len(recent)})</th></tr>', arow, "areas")
            + '</section>')
        return self.page("This week", body, "This week")

    def change_row(self, r: DashRow) -> str:
        unmet = self.unmet(r.thesis_id) if r.action != "RESEARCH NOW" else []
        n_open = len(self.open_by_thesis().get(r.thesis_id, []))
        return (f'<a class="trow" href="{self.thesis_link(r.thesis_id)}"><div class="ttop">'
                f'{_chip(r.action)}{"".join(_event(x) for x in r.events)}'
                + (f'<span class="ev rv">{_pl(n_open, "finding")}</span>' if n_open else "")
                + f'</div><div class="ttitle">{e(r.title)}</div>'
                f'<div class="tline clamp">{e(plain(r.mechanism))}</div><div class="tmeta">'
                f'{e(r.source_line)}{" · preview only" if r.partial_source else ""}'
                + (f' · <span class="gapi">not yet Research Now: {e(" · ".join(unmet))}</span>'
                   if unmet and r.action != "SKIP" else "") + "</div></a>")

    def produced_cell(self, a: ArticleRow, depth: int = 0) -> str:
        if a.produced:
            return "<br>".join(
                f'<a href="{self.thesis_link(tid, depth)}">{e(self.title(tid))}</a> '
                f'<span class="small">— {e(how)}</span>' if tid in self.asof else
                f'<span class="small">{e(how)} (a thesis not in this run\'s record)</span>'
                for tid, how in a.produced)
        return f'<span class="small">{e(" ".join(a.notes))}</span>'

    def produced_table(self, arts: list[ArticleRow], cap: int) -> str:
        if not arts:
            return '<p class="muted">No article this week.</p>'
        rows = [f'<tr><td><b>{e(a.title)}</b><div class="small">{e(a.publisher)} · '
                f'{e(_day(a.published))}</div></td><td>{_state(a.state)}</td>'
                f'<td>{self.produced_cell(a)}</td></tr>' for a in arts]
        shown = rows[:cap]
        return ('<div class="hscroll"><table class="arts prod"><tr><th>Article</th><th>Read</th>'
                '<th>Produced</th></tr>' + "".join(shown) + "</table></div>"
                + (f'<p class="small">Showing {len(shown)} of {len(rows)} articles — '
                   f'<a href="articles.html">all {len(rows)} on Articles</a></p>'
                   if len(rows) > cap else ""))

    # -- Themes --------------------------------------------------------------------------------
    def themes(self) -> str:
        w = self.week
        by_t = self.open_by_thesis()
        changed = {r.thesis_id for r in self.rows}
        recent = self.weeks[-12:]
        rel: dict[str, int] = Counter()
        for x in self.store.relations():  # a sibling (same broader area) is no direct link
            if x.relation.value != "SIBLING":
                rel[x.from_thesis] += 1
                rel[x.to_thesis] += 1
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
                    f'<div class="stale">archives in {left} days unless new evidence</div>'
                    if not arch else
                    f'<div class="small">archived — {e(self.archived_why(t, v))}</div>')
            n_src = len(v.content.s09_sources)
            figs = len(v.content.s04_key_evidence)
            a = self.area[tid]
            rows.append((a, (
                f'<tr data-area="{e(a)}" data-action="{e(v.priority.research_action.value)}" '
                f'data-status="{"archived" if arch else "active"}" '
                f'data-upd="{t.last_material_update.toordinal()}" '
                f'data-left="{left if not arch else 99999}" data-src="{n_src}" '
                f'data-rv="{len(by_t.get(tid, []))}"><td><a href="{self.thesis_link(tid)}"><b>'
                f'{e(t.title)}</b></a>'
                f'{" " + _event("New") if tid in changed and v.version == 1 else ""}'
                f'<div class="small">{e(a)}'
                f'{" · " + _theses(rel[tid], "related") if rel.get(tid) else ""}</div>{note}'
                f'<span class="aud cc">{e(tid)}</span></td>'
                f'<td>{_chip(v.priority.research_action.value)}</td>'
                f'<td class="nowrap">{e(_day(t.last_material_update))}</td><td>{n_src}</td>'
                f'<td>{figs}</td><td>{len(by_t.get(tid, [])) or "—"}</td>'
                f'<td>{_strip(recent, self.activity[tid])}</td></tr>')))
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
            groups.append(
                f'<details class="agrp"{" open" if ch or rn else ""} data-grp="{e(a)}"><summary>'
                f'<b>{e(a)}</b> <span class="muted">{_theses(len(act), "active")}'
                f'{f" · {ch} changed this week" if ch else ""}'
                f'{f" · {rn} at Research Now" if rn else ""}'
                f'</span></summary>'
                + self.table("themes", '<tr><th>Thesis</th><th>Action</th><th>Last new evidence'
                                       '</th><th>Sources</th><th>Key figures</th><th>Open '
                                       'findings</th><th>Weeks with evidence</th></tr>', rs,
                             "theses")
                + '</details>')
        n_act = len(self.active())
        areas = sorted(by_area)
        body = (f'<section class="hero"><h1>Themes</h1><p class="lede">Every thesis in the '
                f'registry: <b>{n_act} active</b>, {len(self.asof) - n_act} archived, in '
                f'{_pl(len(areas), "research area")}. A thesis archives after {STALE_AFTER_DAYS} '
                f'days without new evidence, or at once when its action is Skip; new evidence '
                f're-activates it.</p></section>'
                '<div class="filters"><input id="q" placeholder="Search titles and areas" '
                'oninput="flt()" aria-label="Search"><select id="fs" onchange="flt()" '
                'aria-label="Status"><option value="active">Active</option><option '
                'value="archived">Archived</option><option value="">All</option></select>'
                '<select id="fa" onchange="flt()" aria-label="Action"><option value="">All '
                'actions</option><option value="RESEARCH NOW">Research Now</option><option '
                'value="WATCH">Watch</option><option value="SKIP">Skip</option></select>'
                '<select id="far" onchange="flt()" aria-label="Area"><option value="">All areas'
                '</option>' + "".join(f"<option>{e(a)}</option>" for a in areas)
                + '</select><select id="so" onchange="srt()" aria-label="Sort"><option '
                  'value="upd">Last new evidence</option><option value="stale">Closest to '
                  'archiving</option><option value="src">Most sources</option><option '
                  'value="rv">Most open findings</option></select><span id="cnt" class="small">'
                  '</span></div>'
                f'<div id="tt">{"".join(groups)}</div>')
        return self.page("Themes", body, "Themes")

    def archived_why(self, t: Thesis, v: ThesisVersion) -> str:
        if v.priority.research_action is ResearchAction.SKIP:
            return "its research action is Skip"
        return f"no new evidence for more than {STALE_AFTER_DAYS} days"

    # -- Articles ------------------------------------------------------------------------------
    def articles_page(self, w: Week) -> str:
        arts = self.articles[w.key]
        chips = [f'<a class="wk{" on" if x.key == w.key else ""}" href="{self.week_file(x)}">'
                 f'{e(_span(x.start, x.end))}<small>{len(self.articles[x.key])}</small></a>'
                 for x in reversed(self.weeks)]
        sel = "".join(chips[:12]) + (
            f'<details class="older"><summary>{_pl(len(chips) - 12, "earlier week")}</summary>'
            + "".join(chips[12:]) + "</details>" if len(chips) > 12 else "")
        count = Counter(a.state for a in arts)
        summary = " · ".join(f"{n} {ARTICLE_STATE[s][0].lower()}" for s, n in count.most_common())
        rows = []
        for a in arts:
            prog = (f'{a.captured} of {a.figures} figures captured' if a.analysed and a.figures
                    else "")
            items = a.open_items + [f"Coverage alert: {x}" for x in a.alerts]
            detail = ("<details><summary>" + _pl(len(items), "open item") + "</summary><ul>"
                      + "".join(f"<li>{ids_to_audit(e(plain(x)))}</li>" for x in items)
                      + "</ul></details>" if items else "")
            link = _link(a.url, a.title)
            rows.append(
                f'<tr data-state="{a.state}" data-pub="{e(a.publisher)}"><td class="nowrap">'
                f'{e(_day(a.published))}</td><td>{e(a.publisher)}'
                + (f'<div class="small">{e(a.route)}</div>' if a.route != "automatic" else "")
                + f'</td><td>{link}'
                + "".join(f'<div class="small">{e(n)}</div>' for n in a.notes
                          if a.produced or not n.startswith("No thesis"))
                + f'<span class="aud cc">{e(" · ".join(a.audit))}</span></td><td>{_state(a.state)}'
                + (f'<div class="small">{a.words:,} words read</div>' if a.state == "PARTIAL"
                   and a.words else "")
                + f'</td><td>{self.produced_cell(a) if a.analysed else ""}</td>'
                f'<td>{f"<span class=small>{e(prog)}</span>" if prog else ""}{detail}</td>'
                f'<td class="small">{e(a.follow_up)}</td></tr>')
        pubs = sorted({a.publisher for a in arts})
        body = (f'<section class="hero"><h1>Articles</h1><p class="lede">{e(w.label)}: '
                f'<b>{_pl(len(arts), "item")}</b>{" — " + e(summary) if summary else ""}.</p>'
                f'<div class="weeks" aria-label="Week">{sel}</div></section>'
                '<div class="filters"><select id="fr" onchange="fa()" aria-label="State"><option '
                'value="">Every state</option>' + "".join(
                    f'<option value="{s}">{e(ARTICLE_STATE[s][0])}</option>' for s in count)
                + '</select><select id="fp" onchange="fa()" aria-label="Publisher"><option '
                  'value="">Every publisher</option>' + "".join(
                      f"<option>{e(p)}</option>" for p in pubs)
                + '</select><span id="cnt2" class="small"></span></div>'
                + self.table("artt", '<tr><th>Published</th><th>Publisher</th><th>Article</th>'
                                     '<th>State</th><th>Produced</th><th>Completeness</th>'
                                     '<th>Follow-up</th></tr>', rows, "articles", tid="at"))
        return self.page(f"Articles — {w.label}", body, "Articles")

    def week_file(self, w: Week) -> str:
        return "articles.html" if w is self.week else f"articles-{w.key}.html"

    # -- Review --------------------------------------------------------------------------------
    def review(self) -> str:
        w = self.week
        items = []
        for f in self.open:
            age = (w.end - f.raised).days
            anchor = self.anchor_of(f)
            items.append(
                f'<li class="rvi" data-dec="{1 if f.decision else 0}" data-act="{e(f.action)}" '
                f'data-age="{age}"><div class="rvhead"><a href="{self.thesis_link(f.thesis_id)}">'
                f'<b>{e(f.title)}</b></a> {_chip(f.action)} <span class="small">{e(f.area)}</span>'
                f'</div><div class="line">“{ids_to_audit(e(f.line))}”</div>'
                f'<div class="said"><b>{_KIND_WORD.get(f.kind, "Review")}:</b> '
                f'{ids_to_audit(e(plain(f.said)))}</div>'
                + (f'<div class="dec">Bears on the research action — {e(f.decision)}</div>'
                   if f.decision else "")
                + f'<div class="small">raised {e(_day(f.raised))} (version {f.raised_version}) · '
                  f'open {_pl(age // 7, "week")} · '
                  f'<a href="{self.card_link(f.thesis_id, 0, anchor)}">'
                  f'open the line in the full record →</a></div>'
                  f'<span class="aud cc">{e(f.audit)}</span></li>')
        dec = sum(1 for f in self.open if f.decision)
        old = sum(1 for f in self.open if (w.end - f.raised).days >= 28)
        hist = [f'<li><b>{e(f.title)}</b> — “{ids_to_audit(e(f.line))}”<div class="small">'
                f'{e(f.history)} Review said: {ids_to_audit(e(plain(f.said)))}</div></li>'
                for f in self.history]
        verif = [it for wk in self.weeks for a in self.articles[wk.key] for it in
                 ([(wk, a, x) for x in a.open_items])]
        comp = [f'<li><a href="{self.week_file(wk)}">{e(a.title)}</a> — {e(x)}</li>'
                for wk, a, x in reversed(verif)]
        body = (f'<section class="hero"><h1>Review</h1><p class="lede"><b>'
                f'{_pl(len(self.open), "unresolved finding")}</b> on '
                f'{_pl(len({f.thesis_id for f in self.open}), "active thesis", "active theses")}, '
                f'whatever week raised them — <b>{dec} bear on a research action</b> and come '
                f'first, then Research Now theses, then the oldest. {old} have been open four '
                f'weeks or more. A questioned line is never counted as verified evidence while it '
                f'is open.</p><p class="hint">Read-only. A finding closes only through the record '
                f'— an analyst correction or a re-read; this page records no resolution.</p>'
                '<div class="filters"><label><input type="checkbox" id="fdec" onchange="fr2()"> '
                'Decision-affecting only</label><label><input type="checkbox" id="frn" '
                'onchange="fr2()"> Research Now only</label><label><input type="checkbox" '
                'id="fold" onchange="fr2()"> Open 4+ weeks</label><span id="cnt3" class="small">'
                '</span></div></section>'
                + '<ul class="rvlist" id="rv">'
                + (capped_li(items, "findings", "rvlist")
                   or '<li class="muted">No open finding.</li>') + "</ul>"
                + (f'<details class="quiet"><summary>Resolved and historical findings '
                   f'({len(hist)})</summary><ul class="plainlist">{"".join(hist)}</ul></details>'
                   if hist else "")
                + (f'<details class="quiet"><summary>Article completeness — open figures and '
                   f'paragraphs ({len(comp)})</summary><p class="small">Open material is never '
                   f'used as evidence: it can hold a thesis back, never raise it.</p>'
                   f'<ul class="plainlist">{capped_li(comp, "items", "plainlist")}</ul></details>'
                   if comp else ""))
        return self.page("Review", body, "Review")

    # -- Uploads -------------------------------------------------------------------------------
    def uploads_page(self) -> str:
        w = self.week
        groups = [
            ("full_report", "Full report needed", "a preview was read; the full copy completes "
                                                  "the same article"),
            ("blocked_article", "Blocked or unreadable articles",
             "the weekly scan found them but could not read them"),
            ("channel", "Manual-first and blocked sources",
             "publishers the scan does not or cannot read"),
            ("held", "Held documents", "supplied, not analysed until released"),
            ("review", "Held — which article is uncertain", "supplied; you decide what it is"),
            ("visual", "Visual check", "pages of a supplied document that could not be read"),
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
            rows = []
            for u in us:
                age = (f"{(w.end - u.published).days} days old" if u.published else "")
                pub = f"published {e(_day(u.published))}" if u.published else "—"
                seen = f"first seen {e(_day(u.first_seen))}" if u.first_seen else "—"
                rows.append(
                    f'<tr><td><b>{_link(u.url, u.title)}</b><div class="why">{e(u.why)}</div>'
                    + "".join(f'<div class="small">{e(x)}</div>' for x in u.detail[:6])
                    + "".join(f'<div class="small">→ <a href="{self.thesis_link(t)}">'
                              f'{e(self.title(t))}</a></div>' for t in u.theses if t in self.asof)
                    + (f'<div class="small">showing 6 of {len(u.detail)}</div>'
                       if len(u.detail) > 6 else "")
                    + f'<span class="aud cc">{e(u.audit)}</span></td><td>{e(u.publisher)}'
                      f'<div class="small"><code>{e(u.source_id)}</code></div></td>'
                      f'<td class="nowrap">{pub}<div class="small">{e(age)}</div></td>'
                      f'<td class="nowrap">{seen}</td>'
                      f'<td>{self.command_html(u.command)}</td></tr>')
            open_ = kind not in ("done", "rejected")
            blocks.append(
                f'<details class="ubk"{" open" if open_ else ""}><summary><b>{e(head)}</b> '
                f'<span class="muted">{len(us)} · {e(help_)}</span></summary>'
                + self.table("upt", '<tr><th>Document · why</th><th>Publisher · source id</th>'
                                    '<th>Published · age</th><th>First seen</th><th>What to do'
                                    '</th></tr>', rows, "documents")
                + "</details>")
        waiting = sum(1 for u in self.uploads if u.kind != "done")
        body = (f'<section class="hero"><h1>Uploads</h1><p class="lede"><b>{_pl(waiting, "item")}'
                f'</b> to supply or clear · {len(by.get("done", []))} completed imports. Nothing '
                f'here is dismissed by age — an older report stays listed until it is supplied or '
                f'cleared.</p></section><div class="cols"><section class="main">'
                + ("".join(blocks) or '<p class="muted">Nothing waiting.</p>')
                + f'</section><aside><h2>Each week</h2><ol class="steps">'
                  f'<li><b>Pull</b> the registry the weekly run keeps: <code class="cmd">{CLI} '
                  f'state pull</code></li>'
                  f'<li><b>Collect</b> the PDFs or saved pages you are licensed to use for the '
                  f'items listed here, and any new report from a manual-first source.</li>'
                  f'<li><b>Import</b> one file with the command on its row, or drop files in '
                  f'<code>data/theme_intelligence/inbox/</code> — each with a '
                  f'<code>&lt;file&gt;.meta.json</code> naming <code>source</code>, '
                  f'<code>url</code>, <code>title</code>, <code>published</code> and '
                  f'<code>llm_permitted</code> — and run <code class="cmd">{CLI} ingest-inbox'
                  f'</code>.</li>'
                  f'<li><b>Clear</b> what is held: <code class="cmd">{CLI} documents --status '
                  f'HELD</code>, then the release command on its row.</li>'
                  f'<li><b>Push</b> before Monday 03:00 UTC: <code class="cmd">{CLI} state push'
                  f'</code> (fast-forward only) — that week\'s brief includes them.</li></ol>'
                  f'<p class="small">State <code>--llm-permitted</code> only when the document\'s '
                  f'licence allows third-party model processing; without it the document is held. '
                  f'A document needs at least 40 words of readable text. A fuller copy of a '
                  f'preview is the SAME article, re-checked — nothing is counted twice. A document '
                  f'whose estimated cost is above the $30 per-document limit waits for your '
                  f'release.</p>'
                  f'</aside></div>')
        return self.page("Uploads", body, "Uploads")

    # -- Sources -------------------------------------------------------------------------------
    def sources_page(self) -> str:
        until = self.run.finished_at or datetime.now(tz=UTC)
        rows_by = {r["source_id"]: r for r in self.health.get("rows", [])}
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
        for sid, src in self.reg.sources.items():
            r = rows_by.get(sid, {})
            st = str(r.get("status", "UNKNOWN"))
            word, cls = _HEALTH.get(st, (st.title(), "mute"))
            hist = [h for h in self.store.health_checks(source_id=sid) if h.checked_at <= until]
            strip = ('<span class="hs">' + "".join(
                f'<i class="h-{h.status.value.lower()}" title="{e(_day(h.checked_at))}: '
                f'{e(h.status.value.lower())}"></i>' for h in hist[-12:]) + "</span>"
                + f' <span class="small">last {min(12, len(hist))} of {len(hist)} stored checks'
                  f'</span>') if hist else '<span class="small">no stored check</span>'
            fresh = {"FRESH": "fresh", "QUIET": "quiet — nothing dated in the window",
                     "UNKNOWN": "unknown"}.get(str(r.get("freshness", "UNKNOWN")), "unknown")
            llm = {"permitted": "sent to the model", "not_permitted": "never sent to the model",
                   "unknown": "held unless you state its licence allows"}.get(
                src.manual_llm_processing, src.manual_llm_processing)
            out["manual_first" if src.mode == "manual_first" else "automatic"].append(
                f'<tr><td><b>{e(src.publisher)}</b><div class="small"><code>{e(sid)}</code></div>'
                f'</td><td><span class="st {cls}">{e(word)}</span><div class="small">'
                f'{e(plain(str(r.get("reason", "not checked yet")))[:200])}</div></td>'
                f'<td>{strip}</td><td class="small">{e(fresh)}<br>newest article '
                f'{e(_day(newest.get(sid)))}</td><td>{n_read[sid]}</td>'
                f'<td class="small">'
                f'{"Weekly scan" if src.mode != "manual_first" else "Manual upload only"}'
                f'<br>Uploaded documents: {e(llm)}<br>Linked reports: '
                f'{"fetched politely" if src.linked_reports == "fetch" else "requested for upload"}'
                f'</td></tr>')

        def table(rs: list[str]) -> str:
            return ('<div class="hscroll"><table class="arts srct"><tr><th>Publisher</th>'
                    '<th>Now</th><th>Stored health checks (oldest → newest)</th><th>Freshness</th>'
                    f'<th>Articles analysed, last {len(recent)} weeks</th><th>Permitted intake'
                    '</th></tr>' + "".join(rs) + "</table></div>")

        body = (f'<section class="hero"><h1>Sources</h1><p class="lede">Each publisher\'s access '
                f'now, its stored health record and how its research may come in. A blocked or '
                f'quiet source publishing nothing here is NOT evidence it published nothing.</p>'
                f'<p class="hint">History shows only stored health-check records; a week with no '
                f'check shows nothing.</p></section>'
                f'<section><h2>Automatic coverage <small>read by the weekly scan</small></h2>'
                f'{table(out["automatic"])}</section><section><h2>Manual-first coverage <small>'
                f'never scanned — research arrives only as documents you supply</small></h2>'
                f'{table(out["manual_first"])}</section>')
        return self.page("Sources", body, "Sources")

    # -- the reading page ----------------------------------------------------------------------
    def thesis_page(self, tid: str) -> str:
        t, v = self.asof[tid]
        c = v.content
        rc = card_context(self.store, t, v, generated="", until=self.run.finished_at)
        groups = [g.name for g in rc.groups]
        self.groups[tid] = groups
        nt = self.near[tid]
        gs = gates(v, groups, nt)
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

        events = next((r.events for r in self.rows if r.thesis_id == tid), [])
        arch = t.status is ThesisStatus.ARCHIVED
        head = (f'<nav class="crumb"><a href="../themes.html">Themes</a> › {e(self.area[tid])}'
                f'</nav><header class="th"><h1>{e(t.title)}</h1><div class="meta">'
                f'{_chip(action)}{"".join(_event(x) for x in events)}'
                + (f'<span class="ev">archived — {e(self.archived_why(t, v))}</span>'
                   if arch else "")
                + (f'<a class="flag" href="#review">'
                   f'{"Not reviewed · " if any(f.kind == "not_reviewed" for f in mine) else ""}'
                   f'Review required · {_pl(len(mine), "finding")}</a>'
                   if mine else "")
                + f'<span>{_pl(len(c.s09_sources), "source")} · first seen '
                  f'{e(_day(t.created_as_of))} · last material update '
                  f'{e(_day(t.last_material_update))}</span></div>'
                  f'<div class="aud cc">{e(tid)} · version {v.version} · run {e(v.run_id)} · '
                  f'{e(t.key_node)} · {e(t.key_mechanism)}</div></header>')
        s01 = c.s01_bottom_line
        thesis = ""
        if s01 and once(s01[0].text):
            thesis = (f'<p class="thesis">{ids_to_audit(e(plain(s01[0].text)))} '
                      f'{_tag(s01[0].provenance.value)}{flag("s01.0")}</p>')
        changed = [f'<li>{ids_to_audit(e(plain(it.text)))}'
                   + (f' <span class="muted">({e(it.period)})</span>' if it.period else "")
                   + f"{flag(f's02.{i}')}</li>"
                   for i, it in enumerate(c.s02_what_changed.items[:3])
                   if f"s02.{i}" not in rc.blocked and once(it.text)]
        last = rc.history[-1] if rc.history else v
        prev = rc.history[-2] if len(rc.history) > 1 else None
        moved = (f"Version {last.version} ({_day(last.as_of)}): "
                 + (f"{_ACTION[prev.priority.research_action.value][0]} → "
                    f"{_ACTION[last.priority.research_action.value][0]}"
                    if prev and prev.priority.research_action is not last.priority.research_action
                    else "research action unchanged" if prev else "first recorded"))
        figs = sorted((r for r in c.s04_key_evidence if r.value_text),
                      key=lambda r: (r.epistemic.value not in ("actual", "forecast"),
                                     not re.search(r"\d", r.value_text or "")))[:4]
        pub = {s.article_id: s for s in c.s09_sources}
        fig_html = "".join(
            f'<div class="num"><b>{e(r.value_text)}</b><span class="unit">'
            f'{e(unit_of(r.value_text, r.unit))}</span><span class="lbl">{e(r.label)}</span>'
            f'<small>{e(_EPI.get(r.epistemic.value, r.epistemic.value))} · '
            f'{e(r.period or "period not stated")} · '
            + (f"measured {e(_day(r.measured_as_of))}" if r.measured_as_of else
               f"published {e(_day(pub[r.article_id].published_at))}"
               if r.article_id in pub else "date not stated")
            + f'</small><small>{e(pub[r.article_id].publisher) if r.article_id in pub else ""}'
              f'</small><span class="aud cc">{e(r.claim_id)}</span></div>' for r in figs)
        steps = []
        for i, st in enumerate(c.s03_transmission):
            if st.step == "market_reaction":
                continue
            unknown = st.text.startswith("UNKNOWN")
            if not unknown and not once(st.text):
                continue
            steps.append(f'<li><span class="sn">{e(STEP_LABEL.get(st.step, st.step))}</span>'
                         + ('<span class="muted">not quantified by the source</span>' if unknown
                            else f'<span>{ids_to_audit(e(plain(st.text)))}</span> '
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
            f'<details class="met"><summary>{_pl(len(met), "condition")} met</summary>'
            '<ul class="gates">' + "".join(
                f'<li class="ok"><span class="ic">✓</span><div><b>{e(g.name)}</b>'
                f'<span>{e(g.detail)}</span></div></li>' for g in met) + "</ul></details>"
            if met else "")
        timing = self.timing_html(nt, near)
        w7 = c.s07_what_could_go_wrong
        n0, n1 = len(w7.counter_evidence), len(w7.alternative_mechanisms)
        risks = [f'<li>{ids_to_audit(e(plain(s.text)))} {_tag(s.provenance.value)}'
                 f'{flag(f"s07.{i}")}</li>'
                 for i, s in enumerate(w7.counter_evidence) if once(s.text)]
        risks += [f'<li>{ids_to_audit(e(plain(s.text)))} {_tag(s.provenance.value)}'
                  f'{flag(f"s07.{n0 + n1 + i}")}</li>'
                  for i, s in enumerate(w7.market_risks) if once(s.text)]
        watch = [f"<li>{ids_to_audit(e(plain(s.text)))}</li>"
                 for s in w7.disconfirming_observables if once(s.text)]
        alt = [f'<li>{ids_to_audit(e(plain(s.text)))} {_tag(s.provenance.value)}</li>'
               for s in w7.alternative_mechanisms
               if not s.text.startswith("Registry link") and once(s.text)]
        dsn = c.s08_decision
        nxt = (f'<p>{ids_to_audit(e(plain(dsn.next_step.text)))}{flag("s08.next")}</p>'
               if once(dsn.next_step.text) else "")
        raise_ = [f"<li>{ids_to_audit(e(plain(s.text)))}</li>" for s in dsn.raise_priority_if
                  if once(s.text)]
        lower = [f"<li>{ids_to_audit(e(plain(s.text)))}</li>" for s in dsn.lower_priority_if
                 if once(s.text)]
        av = c.s05_affected
        listed = [f"{co.name_as_written} ({', '.join(x.ticker for x in co.listings)})"
                  for co in av.companies if co.listings]
        expo = (f'<dl class="expo"><dt>Listed companies the source names</dt><dd>'
                f'{e(", ".join(listed)) or "none"}</dd><dt>Sectors the source names as exposed</dt>'
                f'<dd>{e(", ".join(s.name for s in av.sector_exposures)) or "none"}</dd>'
                f'<dt>Business groups the source names</dt><dd>'
                + (e("; ".join(groups)) + ' <span class="muted">— groups, not companies; no '
                   'ticker is implied</span>' if groups else "none") + "</dd></dl>")
        related = self.related_html(tid)
        rv = "".join(
            f'<li><div class="line">“{ids_to_audit(e(f.line))}”</div><div class="said">'
            f'{ids_to_audit(e(plain(f.said)))}</div>'
            + (f'<div class="dec">Bears on the research action — {e(f.decision)}</div>'
               if f.decision else "")
            + f'<div class="small">raised {e(_day(f.raised))} · <a href="'
              f'{self.card_link(tid, 1, self.anchor_of(f))}">the line in the full record →</a>'
              f'</div></li>' for f in mine)
        evid, n_ev = self.evidence_html(c, rc)
        hist = "".join(
            f'<li><span class="hv">v{h.version}</span><span>{e(_day(h.as_of))}</span>'
            f'{_chip(h.priority.research_action.value)}<span class="muted">'
            f'{e(self.version_how(h))}</span><span class="aud cc">'
            f'{e(plain(h.change_summary)[:400])}</span></li>' for h in reversed(rc.history))
        srcs = "".join(
            f'<li>{_link(s.url, s.title or "title not recorded")} — '
            f'{e(s.publisher)}, {e(_day(s.published_at))} · '
            f'{"full text" if self.read_in_full(s, rc) else "preview only"}'
            f'<span class="aud cc"> {e(s.article_id)}</span></li>' for s in c.s09_sources)
        nine = "".join(f'<li><a href="{self.card_link(tid, 1, "sec-" + fid)}">{e(name.title())}'
                       f'</a></li>' for fid, name in SECTION_IDS)
        trace = "".join(f'<div class="cc">{e(x)}</div>' for x in v.priority.rules_fired) + "".join(
            f'<div class="cc">{e(f.factor_id)} = {e(f.value)} — {e(f.note[:300])}</div>'
            for f in v.priority.factors)
        none = '<p class="muted">No bottom line recorded.</p>'
        q = (f'<section class="panel q1"><h2>The thesis</h2>{thesis or none}'
             f'</section><div class="grid2"><section class="panel"><h2>What changed</h2>'
             f'<p class="small">{e(moved)}</p>'
             + (f"<ul>{''.join(changed)}</ul>" if changed else "")
             + f'</section><section class="panel"><h2>Why {e(_ACTION.get(action, (action,))[0])}'
               f'</h2>{why}{timing}<div class="aud">{trace}</div></section></div>'
             + (f'<section class="panel"><h2>The strongest figures</h2><div class="nums">'
                f'{fig_html}</div></section>' if fig_html else "")
             + f'<div class="grid2"><section class="panel"><h2>How it reaches fundamentals</h2>'
               f'<ol class="chain">'
               f'{"".join(steps) or "<li class=muted>No earnings step stated by the source.</li>"}'
               f'</ol></section><section class="panel"><h2>What could prove it wrong</h2>'
               f'<ul class="risk">'
               f'{"".join(risks) or "<li class=muted>None in the sources so far.</li>"}</ul>'
             + (f'<h3>Watch for</h3><ul class="risk">{"".join(watch)}</ul>' if watch else "")
             + (f'<h3>Competing explanation</h3><ul class="risk">{"".join(alt)}</ul>'
                if alt else "")
             + f'</section></div><section class="panel next"><h2>What to investigate next</h2>'
               f'{nxt}'
             + (f'<h3>Would raise priority</h3><ul>{"".join(raise_)}</ul>' if raise_ else "")
             + (f'<h3>Would lower priority</h3><ul>{"".join(lower)}</ul>' if lower else "")
             + f'</section><section class="panel"><h2>Who is exposed</h2>{expo}</section>'
             + (f'<section class="panel"><h2>Related theses</h2>{related}</section>'
                if related else "")
             + (f'<section class="panel" id="review"><h2>Open review findings '
                f'<small>{len(mine)}</small></h2><ul class="rvlist">{rv}</ul></section>'
                if mine else ""))
        tabs = (f'<section class="tabs" data-tabs><div class="tabbar" role="tablist">'
                f'<button data-tab="ev" class="on">Evidence ({n_ev})</button>'
                f'<button data-tab="hi">History ({len(rc.history)} versions)</button>'
                f'<button data-tab="src">Sources ({len(c.s09_sources)})</button>'
                f'<button data-tab="full">Full record</button></div>'
                f'<div data-panel="ev">{evid}</div>'
                f'<div data-panel="hi" hidden><ol class="timeline">{hist}</ol></div>'
                f'<div data-panel="src" hidden><ul class="plainlist">{srcs}</ul></div>'
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
               "reassess": "re-graded from stored evidence — no article read"}.get(
            r.mode if r else "", "run not recorded")
        return how + (" · includes an analyst correction"
                      if "ANALYST CORRECTION" in h.change_summary else "")

    def timing_html(self, nt: NearTerm, near: Gate) -> str:
        """The source's horizon FRAMING beside the dated near-term evidence — two statements, never
        two verdicts on one test (the Nomura presentation, 2026-10-13)."""
        rows = "".join(
            f'<li>{e(x.claim.metric or x.claim.statement)[:140]} — '
            f'{e(_TIMING_WORD.get(x.timing, x.timing))}'
            f'; dated by {e(x.basis)}<span class="aud cc"> {e(x.claim.claim_id)} · '
            f'{e(x.note)}</span></li>' for x in nt.claims[:6])
        more = (f'<li class="small">showing 6 of {len(nt.claims)}</li>' if len(nt.claims) > 6
                else "")
        conflict = (f'<div class="conflict"><b>Review required.</b> The near-term reading of '
                    f'record (“{e(nt.stored.replace("_", " "))}”) differs from its own cited '
                    f'claims re-dated today (“{e(nt.recomputed.replace("_", " "))}”). The research '
                    f'action of record stands until the thesis is reassessed.</div>' if nt.conflict
                    else "")
        return (f'<div class="timing"><h3>Timing</h3>{conflict}<ul class="gates"><li class="'
                f'{"ok" if near.ok else "unmet"}"><span class="ic">{"✓" if near.ok else "✗"}</span>'
                f'<div><b>{e(near.name)}</b><span>{e(near.detail)}</span></div></li></ul>'
                f'<p class="small"><b>How the source frames it:</b> {e(nt.framing)} — a '
                f'description of the thesis, not a test.</p>'
                + (f'<p class="small"><b>The dated evidence the near-term condition reads:</b></p>'
                   f'<ul class="small">{rows}{more}</ul>' if rows else "")
                + f'<div class="aud cc">{e(nt.note[:400])}</div></div>')

    def related_html(self, tid: str) -> str:
        """Linked theses — never merged: direct links first, then theses sharing a source (the
        same source, not independent confirmation), then the same-broader-area siblings, folded."""
        out: list[str] = []
        siblings: list[str] = []
        for x in self.store.relations(tid):
            other = x.to_thesis if x.from_thesis == tid else x.from_thesis
            if other not in self.asof:
                continue
            item = (f'<li><a href="{e(other)}.html">{e(self.title(other))}</a> '
                    f'<span class="small">— {e(self.area[other])}'
                    + ("" if x.relation.value == "SIBLING" else
                       f'; {e(_RELATION.get(x.relation.value, x.relation.value.lower()))}')
                    + "</span></li>")
            (siblings if x.relation.value == "SIBLING" else out).append(item)
        mine = self.sources_of.get(tid, set())
        shared: dict[str, set[str]] = defaultdict(set)
        for other, arts in self.sources_of.items():
            if other != tid and other in self.asof:
                for aid in mine & arts:
                    shared[other].add(aid)
        for other, aids in sorted(shared.items(), key=lambda kv: self.title(kv[0])):
            names = sorted({(a.publisher if (a := self.reg.article(aid)) else "a source")
                            for aid in aids})
            out.append(f'<li><a href="{e(other)}.html">{e(self.title(other))}</a> '
                       f'<span class="small">— shares {_pl(len(aids), "source article")} '
                       f'({e(", ".join(names))}): the same source, not independent confirmation'
                       f'</span></li>')
        if siblings:
            out.append(f'<li class="morewrap"><details class="more-rows"><summary>'
                       f'{_pl(len(siblings), "thesis", "theses")} in the same broader area, a '
                       f'different part of the chain</summary><ul class="plainlist">'
                       + capped_li(sorted(siblings), "theses", "plainlist")
                       + "</ul></details></li>")
        return f'<ul class="plainlist">{"".join(out)}</ul>' if out else ""

    def evidence_html(self, c: Any, rc: Any) -> tuple[str, int]:
        pub = {s.article_id: s for s in c.s09_sources}
        rows: list[tuple[str, dict[str, Any]]] = []
        for r in c.s04_key_evidence:
            rows.append((r.article_id, {"v": r.value_text, "u": unit_of(r.value_text, r.unit),
                                        "label": r.label, "quote": r.quote, "period": r.period,
                                        "type": _EPI.get(r.epistemic.value, r.epistemic.value),
                                        "role": "key evidence", "id": r.claim_id}))
        key = {r.claim_id for r in c.s04_key_evidence}
        for cid, cl in rc.claims.items():
            if cid in key:
                continue
            role = rc.roles.get(cid, "")
            rows.append((cl.article_id, {
                "v": cl.value_text, "u": unit_of(cl.value_text, cl.unit),
                "label": " — ".join(z for z in (cl.scope, cl.metric) if z) or cl.statement,
                "quote": cl.quote, "period": cl.period,
                "type": _EPI.get(cl.epistemic.value, cl.epistemic.value),
                "role": {"contradicts": "against", "context": "context", "supports": "supports",
                         "competing": "competing"}.get(role, role or "cited"),
                "id": cid}))
        by: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for aid, row in rows:
            by[aid].append(row)

        def when(aid: str) -> datetime:
            s = pub.get(aid)
            return s.published_at if s and s.published_at else datetime.min.replace(tzinfo=UTC)

        out = []
        for i, (aid, xs) in enumerate(sorted(by.items(), key=lambda kv: when(kv[0]), reverse=True)):
            s = pub.get(aid)
            name = f"{s.publisher} · {_day(s.published_at)}" if s else "source"
            against = sum(1 for x in xs if x["role"] == "against")
            trs = [f'<tr><td><b>{e(x["v"] or "—")}</b> {e(x["u"])}</td><td>{e(x["label"])}'
                   f'<div class="q">“{e(x["quote"])}”</div><span class="aud cc">{e(x["id"])}'
                   f'</span></td><td class="nowrap">{e(x["period"] or "—")}</td>'
                   f'<td>{e(x["type"])}</td><td>{e(x["role"])}</td></tr>' for x in xs]
            out.append(f'<details class="evg"{" open" if i == 0 else ""}><summary><b>{e(name)}</b> '
                       f'<span class="muted">— {_pl(len(xs), "figure")}'
                       f'{f", {against} against" if against else ""}</span></summary>'
                       + self.table("evt", '<tr><th>Figure</th><th>What it measures · the '
                                           'source\'s words</th><th>Period</th><th>Type</th>'
                                           '<th>Role</th></tr>', trs, "figures", cap=12)
                       + "</details>")
        return ("".join(out) or '<p class="muted">No cited evidence.</p>'), len(rows)

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


def write_desk(store: Store, run_id: str, out: Path, *, cards: dict[str, dict[str, str]],
               generated: str) -> list[str]:
    """Write the research desk for `run_id` into `out` (beside the run's cards and report)."""
    run = store.run(run_id)
    if run is None:
        raise KeyError(f"no run {run_id}")
    return Desk(store, run, cards=cards, generated=generated).write(out)


NAV = [("This week", "index.html"), ("Themes", "themes.html"), ("Articles", "articles.html"),
       ("Review", "review.html"), ("Uploads", "uploads.html"), ("Sources", "sources.html")]

CSS = """
:root{--bg:#f6f5f1;--panel:#fff;--ink:#16191d;--ink2:#3b4148;--muted:#6b7280;--line:#e6e4dd;
--accent:#1d4f7a;--accent-bg:#eaf1f8;--watch:#8a5a00;--watch-bg:#fbf1d8;--now:#1f6b3a;
--now-bg:#e3f3e8;--skip:#555;--skip-bg:#eee;--bad:#9b2c2c;--bad-bg:#fbe9e7;--part:#7a5b00;
--part-bg:#fdf3dc;--ok:#1f6b3a;--ok-bg:#e3f3e8;--info:#215f86;--info-bg:#e6f0f7}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:15.5px/1.6 -apple-system,
BlinkMacSystemFont,"Segoe UI",Inter,Roboto,Helvetica,Arial,sans-serif;overflow-wrap:break-word}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
.top{background:var(--panel);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5}
.top .in{max-width:1180px;margin:0 auto;padding:0 20px;display:flex;align-items:center;gap:24px;
min-height:56px;flex-wrap:wrap}
.brand{font-weight:700;color:var(--ink)}
.brand small{font-weight:500;color:var(--muted);margin-left:6px}
nav a{color:var(--ink2);margin-right:18px;padding:17px 0;display:inline-block;
border-bottom:2px solid transparent}
nav a.on{color:var(--ink);border-bottom-color:var(--accent);font-weight:600}
nav a:hover{text-decoration:none}
.auditbar{margin-left:auto;font-size:13px;color:var(--muted);cursor:pointer;border:1px solid
var(--line);border-radius:6px;padding:3px 9px;white-space:nowrap}
#audit:checked~.top .auditbar{background:var(--accent-bg);color:var(--accent)}
.aud{display:none}#audit:checked~.wrap .aud,#audit:checked~main .aud{display:revert}
.cc{font:12px/1.4 ui-monospace,Menlo,monospace;color:var(--muted)}
.wrap{max-width:1180px;margin:0 auto;padding:28px 20px 64px}
h1{font-size:30px;line-height:1.2;margin:4px 0 10px;letter-spacing:-.01em}
h2{font-size:18px;margin:0 0 12px}h2 small,h3 small{font-weight:500;color:var(--muted);
font-size:13px;margin-left:6px}h3{font-size:14.5px;margin:16px 0 8px}
.eyebrow{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);
font-weight:600}
.hero{margin-bottom:24px}.lede{font-size:17px;color:var(--ink2);margin:0 0 16px;max-width:820px}
.hint{color:var(--muted);font-size:13.5px;margin:-6px 0 14px}
.muted{color:var(--muted)}.nowrap{white-space:nowrap}.small{font-size:12.5px;color:var(--muted)}
.mt{margin-top:26px}
.strip{display:flex;gap:12px;flex-wrap:wrap}
.strip>*{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 16px;
min-width:140px;flex:1;color:var(--ink)}
.strip b{display:block;font-size:24px;line-height:1.2}.strip span{font-size:13px;color:var(--muted)}
.strip a.warn b{color:var(--bad)}.strip a:hover{text-decoration:none;border-color:var(--accent)}
.cols{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:28px;align-items:start;
margin-bottom:30px}
aside{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:18px 18px 8px;
position:sticky;top:76px}
.att{list-style:none;margin:0;padding:0}.att li{padding:10px 0;border-top:1px solid var(--line);
font-size:14px}.att li:first-child{border-top:0;padding-top:0}
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
.chip{display:inline-block;font-size:12px;font-weight:650;border-radius:20px;padding:2px 10px;
white-space:nowrap}
.chip.watch{background:var(--watch-bg);color:var(--watch)}.chip.now{background:var(--now-bg);
color:var(--now)}.chip.skip{background:var(--skip-bg);color:var(--skip)}
.ev{display:inline-block;font-size:11.5px;border:1px solid var(--line);border-radius:20px;
padding:1px 8px;color:var(--ink2);background:#fff;white-space:nowrap}
.ev.down{color:var(--bad);border-color:#f0c9c4}.ev.up{color:var(--now)}.ev.new{color:var(--info)}
.ev.rv{color:var(--bad);background:var(--bad-bg);border-color:transparent}
.st{display:inline-block;border-radius:6px;padding:1px 8px;font-size:12.5px;white-space:nowrap}
.st.ok{color:var(--ok);background:var(--ok-bg)}.st.part{color:var(--part);background:var(--part-bg)}
.st.bad{color:var(--bad);background:var(--bad-bg)}.st.info{color:var(--info);background:var(--info-bg)}
.st.mute{color:var(--muted);background:#f0efea}
table{border-collapse:collapse;width:100%;background:var(--panel)}
.hscroll{overflow-x:auto;border:1px solid var(--line);border-radius:12px;max-width:100%}
th{font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);text-align:left;
font-weight:600;padding:10px 14px;border-bottom:1px solid var(--line);background:#fbfbf9}
td{padding:10px 14px;border-bottom:1px solid var(--line);vertical-align:top;font-size:14.5px}
tr:last-child td{border-bottom:0}
section{margin-bottom:28px}
code{font-size:12.5px;background:#f1f0eb;border-radius:4px;padding:1px 5px;overflow-wrap:anywhere}
code.cmd{display:inline-block;white-space:normal}
.filters{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:0 0 12px}
.filters input:not([type=checkbox]),.filters select{font:inherit;font-size:14px;padding:7px 10px;
border:1px solid var(--line);border-radius:8px;background:#fff}
.filters input#q{min-width:240px;flex:1}.filters label{display:inline-flex;gap:8px;
align-items:center;font-size:14px}
.weeks{display:flex;gap:6px;flex-wrap:wrap;padding-bottom:4px;max-width:100%}
.wk{white-space:nowrap;border:1px solid var(--line);border-radius:8px;padding:5px 10px;
font-size:13px;background:#fff;color:var(--ink2)}
.wk small{margin-left:6px;color:var(--muted)}.wk.on{border-color:var(--accent);color:var(--ink);
font-weight:600}
details summary{cursor:pointer;color:var(--accent);font-size:13.5px}
details.more-rows>summary{margin:8px 14px 12px}
details.agrp,details.ubk,details.quiet{background:var(--panel);border:1px solid var(--line);
border-radius:12px;padding:10px 16px;margin-bottom:10px}
details.agrp>summary,details.ubk>summary,details.quiet>summary{color:var(--ink);font-size:15px}
details.agrp .hscroll,details.ubk .hscroll{margin-top:10px}
.act{display:inline-flex;gap:2px;vertical-align:middle}.act i{width:9px;height:14px;
border-radius:2px;background:#e9e7e0;display:block}.act i.on{background:var(--accent)}
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
.h-healthy{background:#6aa77d}.h-degraded{background:#e2b950}.h-blocked{background:#c9645a}
.h-error{background:#c9645a}.h-unknown{background:#ccc}
.crumb{font-size:13px;color:var(--muted);margin-bottom:8px}
.th h1{font-size:28px;max-width:920px}.th .meta{display:flex;flex-wrap:wrap;gap:8px 12px;
align-items:center;color:var(--muted);font-size:13.5px;margin-bottom:18px}
.flag{background:var(--bad-bg);color:var(--bad);border-radius:6px;padding:2px 9px;font-size:13px}
.flagi{font-size:11.5px;color:var(--bad);margin-left:4px;white-space:nowrap}
.thesis{font-size:19px;line-height:1.55;margin:0;border-left:3px solid var(--accent);
padding-left:16px}
.tag{font-size:11px;color:var(--muted);border:1px solid var(--line);border-radius:4px;padding:0 5px;
white-space:nowrap;vertical-align:1px;margin-left:4px;background:#fff}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:18px 20px;
margin-bottom:16px}
.grid2{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:16px;margin-bottom:16px}
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
.expo{display:grid;grid-template-columns:260px minmax(0,1fr);gap:6px 16px;margin:0;font-size:14.5px}
.expo dt{color:var(--muted)}.expo dd{margin:0}
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
.timeline li:first-child{border-top:0}.hv{font-weight:700;width:30px}
.btn{display:inline-block;background:var(--accent);color:#fff;border-radius:8px;padding:8px 14px;
margin:0 8px 8px 0}.btn2{display:inline-block;border:1px solid var(--line);border-radius:8px;
padding:8px 14px}.btn:hover,.btn2:hover{text-decoration:none}
.nine{columns:2;font-size:14px}
tr.xtra{display:none}.morebox:checked+.hscroll tr.xtra{display:table-row}
.morelbl{display:inline-block;margin:8px 2px 12px;font-size:13.5px;color:var(--accent);
cursor:pointer}
.morebox:checked~.morelbl{display:none}
.why{font-size:13px;color:var(--ink2);margin-top:3px}
details.cmdd{min-width:150px}details.cmdd code{display:block;margin-top:6px;word-break:break-all}
details.older{display:inline-block;margin-left:4px}details.older[open]{display:block}
td:empty{padding:0}
.testdata{background:#3b2a00;color:#ffe9b0;font-size:12.5px;padding:6px 20px;text-align:center}
.foot{max-width:1180px;margin:18px auto 0;font-size:12.5px;color:var(--muted)}
.hit{outline:2px solid var(--accent);outline-offset:3px}
@media (max-width:880px){.cols{grid-template-columns:1fr}aside{position:static}
.grid2{grid-template-columns:1fr}.expo{grid-template-columns:1fr}.expo dt{margin-top:6px}
h1{font-size:24px}.th h1{font-size:22px}.thesis{font-size:17px}.nine{columns:1}
nav a{margin-right:12px;padding:8px 0}.top .in{gap:4px 16px;padding:8px 16px}
.wrap{padding:20px 16px 48px}.filters input#q{min-width:0;width:100%}
.arts,.arts tbody,.arts tr,.arts td{display:block;width:100%}
.arts tr:first-child{display:none}.arts tr{padding:12px 14px;border-bottom:1px solid var(--line)}
.arts td{border:0;padding:2px 0}.arts td:empty{display:none}.hscroll{border-radius:10px}
.arts tr.xtra{display:none}.morebox:checked+.hscroll .arts tr.xtra{display:block}
.tabbar{flex-wrap:wrap;overflow:visible}.tabbar button{padding:10px 8px}}
@media print{.top,.tabbar,.filters{display:none}[data-panel]{display:block!important}
body{background:#fff}.aud{display:revert!important}}
"""

JS = """document.querySelectorAll('[data-tabs]').forEach(function(g){var b=g.querySelectorAll(
'[data-tab]'),p=g.querySelectorAll('[data-panel]');b.forEach(function(x){x.addEventListener(
'click',function(){b.forEach(function(y){y.classList.toggle('on',y===x)});p.forEach(function(q){
q.hidden=q.dataset.panel!==x.dataset.tab})})})});
function rowsOf(sel){return Array.prototype.slice.call(document.querySelectorAll(sel))}
function openAll(root){rowsOf(root+' details.more-rows').forEach(function(d){d.open=true});
rowsOf('input.morebox').forEach(function(b){b.checked=true})}
function flt(){var q=(document.getElementById('q').value||'').toLowerCase(),
s=document.getElementById('fs').value,a=document.getElementById('fa').value,
ar=document.getElementById('far').value,n=0,all=rowsOf('#tt tr[data-area]');
if(q||a||ar)openAll('#tt');
all.forEach(function(r){var ok=(!s||r.dataset.status===s)&&(!a||r.dataset.action===a)&&
(!ar||r.dataset.area===ar)&&(!q||r.textContent.toLowerCase().indexOf(q)>=0);
r.style.display=ok?'':'none';n+=ok?1:0});
rowsOf('#tt details[data-grp]').forEach(function(g){var v=Array.prototype.slice.call(
g.querySelectorAll('tr[data-area]')).some(function(r){return r.style.display!=='none'});
g.style.display=v?'':'none';if(q||a||ar)g.open=v});
document.getElementById('cnt').textContent='showing '+n+' of '+all.length}
function srt(){var k=document.getElementById('so').value;var v=function(r){return k==='upd'?
-r.dataset.upd:k==='stale'?+r.dataset.left:k==='src'?-r.dataset.src:-r.dataset.rv};
rowsOf('#tt table').forEach(function(t){var rs=Array.prototype.slice.call(t.querySelectorAll(
'tr[data-area]'));rs.sort(function(a,b){return v(a)-v(b)}).forEach(function(r){
(r.parentNode).appendChild(r)})})}
function fa(){var r=document.getElementById('fr').value,p=document.getElementById('fp').value,n=0,
all=rowsOf('#at tr[data-state]');if(r||p)openAll('#at');all.forEach(function(x){var ok=
(!r||x.dataset.state===r)&&(!p||x.dataset.pub===p);x.style.display=ok?'':'none';n+=ok?1:0});
document.getElementById('cnt2').textContent='showing '+n+' of '+all.length}
function fr2(){var d=document.getElementById('fdec').checked,rn=document.getElementById('frn')
.checked,o=document.getElementById('fold').checked,n=0,all=rowsOf('#rv li.rvi');
if(d||rn||o)openAll('#rv');all.forEach(function(x){var ok=(!d||x.dataset.dec==='1')&&(!rn||
x.dataset.act==='RESEARCH NOW')&&(!o||+x.dataset.age>=28);x.style.display=ok?'':'none';
n+=ok?1:0});document.getElementById('cnt3').textContent='showing '+n+' of '+all.length}
(function(){var u=new URLSearchParams(location.search);if(document.getElementById('tt')){
if(u.get('area'))document.getElementById('far').value=u.get('area');if(u.get('sort')){
document.getElementById('so').value=u.get('sort');srt()}flt()}
if(document.getElementById('at'))fa();if(document.getElementById('rv'))fr2()})();"""
