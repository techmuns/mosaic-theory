"""Source health monitoring — is each publisher channel still being READ, or failing silently?

A cheap, bounded, LLM-free check per channel (Priority 1A). It never concludes a channel is
healthy because a page answered HTTP 200: it runs the channel's own discovery adapter, fetches and
parses ONE real article, and reads its metadata. Seven tests:

  1 access            the endpoint discovery starts from, under robots.txt and the honest
                      User-Agent — a 401 / 403 / 451 or a robots refusal is BLOCKED and is never
                      retried within the check (and not re-requested for BLOCKED_RECHECK_HOURS
                      unless forced); a robots.txt that cannot be read FAILS CLOSED, visibly
  2 discovery         genuine article URLs, with titles and listing dates
  3 extraction        up to SAMPLE_ARTICLES articles (the newest dated first) fetched and
                      their bodies read — one sample hides what most pages do
  4 dates_authors     the article page's own publication date and byline; the listing's dates
  5 completeness      full text / paywalled preview / partial — and the latest scan's outcomes
  6 freshness         the newest dated article against the window; URLs new since the last check
  7 parser_integrity  a 200 page whose body the parser cannot read, or an extraction that
                      collapsed against this channel's own earlier ones

STATUS — exactly one: BLOCKED (access denied or cannot safely proceed) · ERROR (transport
failure, unexpected answer, adapter malfunction) · DEGRADED (works in part: discovery, extraction,
dates, previews) · HEALTHY (everything above passed) · UNKNOWN (never checked). FRESHNESS is kept
apart: a channel with nothing new this week is QUIET, not unhealthy. `expect_blocked` in
sources.toml changes only the alert class (a KNOWN_RESTRICTION is shown, not re-alerted) — the
status stays BLOCKED.

HISTORY. Every check is one immutable row (`source_health`); the previous row of the channel is
what detects a change — HEALTHY → DEGRADED / BLOCKED, extraction → parser failure, a sudden drop to
zero discovered articles (flagged for review, never read as "published nothing"), dates missing at
consecutive checks, a BLOCKED channel accessible again. An alert is raised on a change of state (or
once when a failure has persisted PERSISTENT_ALERT_AT checks), never repeated without one; when the
environment names a hook command, alerts are handed to it as JSON on stdin.
"""

from __future__ import annotations

import hashlib
import json
import os
import shlex
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from typing import Any, Literal

from vinci.theme_intelligence.config import SourceConfig
from vinci.theme_intelligence.discovery import (
    ADAPTERS,
    LISTING_TTL_S,
    METHOD,
    Candidate,
    SourceBlockedError,
    canon,
    trendforce_press,
)
from vinci.theme_intelligence.fetch import FetchResult, PoliteFetcher
from vinci.theme_intelligence.parse import parse_document
from vinci.theme_intelligence.schemas import (
    Freshness,
    HealthStatus,
    HealthTest,
    ManualAction,
    RetrievalState,
    SourceCoverage,
    SourceHealthCheck,
)
from vinci.theme_intelligence.store import Store

#: a channel that DENIED access is not re-requested sooner than this (unless forced)
BLOCKED_RECHECK_HOURS = 24
#: a failure that persists this many checks raises ONE reminder; then nothing until it changes
PERSISTENT_ALERT_AT = 3
#: a discovered-URL list longer than this is stored truncated, and says so
URL_CAP = 200
#: articles fetched and parsed per check — the newest dated first, then in listing order
SAMPLE_ARTICLES = 3
#: within one check, a page fetched less than this ago is reused (the access fetch is live)
FRESH_WITHIN_S = 900.0
#: parser integrity: an extraction collapsed when THE SAME PAGE, read at an earlier check with at
#: least BASELINE_MIN_WORDS words, now reads under this share of them — never a comparison between
#: different articles (their natural lengths differ: the live re-check of 2026-10-11 flagged Citi's
#: 96-word teasers against a 570-word article read the check before)
COLLAPSE_RATIO = 0.25
BASELINE_MIN_WORDS = 300
#: the environment variable naming a delivery command for alerts (JSON on stdin)
HOOK_ENV = "THEME_INTELLIGENCE_HEALTH_HOOK"

FAILING = frozenset({HealthStatus.DEGRADED, HealthStatus.BLOCKED, HealthStatus.ERROR})
_RANK = {HealthStatus.HEALTHY: 0, HealthStatus.UNKNOWN: 0, HealthStatus.DEGRADED: 1,
         HealthStatus.ERROR: 2, HealthStatus.BLOCKED: 2}
_DENIED = frozenset({401, 403, 451})
_UPLOAD = ("upload an authorized copy into the same pipeline: python -m vinci.theme_intelligence "
           "ingest-file --path <report.pdf or saved page> --source {sid} [--url <article URL>]")


@dataclass
class HealthRun:
    """One health-check pass: the records (written or carried), and what was not re-requested."""

    checks: list[SourceHealthCheck]
    skipped: dict[str, str] = field(default_factory=dict)  # source id -> why not re-requested
    delivery: str = ""


@dataclass
class _Sample:
    """One sampled article: read, or why not."""

    cand: Candidate
    read: bool = False
    reason: str = ""
    title: str | None = None
    kb: int = 0
    published: date | None = None
    authors: tuple[str, ...] = ()
    words: int = 0
    blocks: int = 0
    retrieval: RetrievalState | None = None
    notes: tuple[str, ...] = ()
    paywall: bool = False
    parser_fail: str = ""
    #: partial only because it summarises a report it links to
    linked_report: bool = False

    def line(self) -> str:
        if not self.read:
            return f"{self.cand.url} — not retrieved: {self.reason}"
        state = ("PARSER FAILURE" if self.parser_fail else "paywalled preview" if self.paywall
                 else self.retrieval.value if self.retrieval else "?")
        return (f"{self.cand.url} — {self.words} words, {state}, "
                + (f"dated {self.published.isoformat()}" if self.published else "page undated")
                + (f", by {', '.join(self.authors)}" if self.authors else ", no byline"))


@dataclass
class _Obs:
    """What one check observed, before it is turned into a record."""

    tests: dict[str, HealthTest] = field(default_factory=dict)
    access_kind: str = "ok"  # ok | denied | robots | missing | error
    adapter_broken: bool = False
    cands: list[Candidate] = field(default_factory=list)
    sample: Candidate | None = None
    samples: list[_Sample] = field(default_factory=list)
    sample_doc_title: str | None = None
    sample_published: date | None = None
    sample_authors: tuple[str, ...] = ()
    sample_words: int | None = None
    sample_retrieval: str | None = None
    sample_notes: tuple[str, ...] = ()
    full_text: bool = False
    decisive: str = ""  # the test that set the status


def _t(name: str, result: Literal["PASS", "WARN", "FAIL", "SKIP"], detail: str) -> HealthTest:
    return HealthTest(name=name, result=result, detail=detail)


def _denial(fr: FetchResult) -> tuple[str, str]:
    """(kind, plain reason) for a fetch that returned no content."""
    if fr.status in _DENIED:
        return "denied", f"access denied (HTTP {fr.status})"
    if fr.status is None and fr.note.startswith("robots.txt"):
        return "robots", fr.note
    if fr.status in (404, 410):
        return "missing", f"the configured page is gone (HTTP {fr.status}) — it may have moved"
    if fr.status is not None:
        return "error", f"unexpected answer (HTTP {fr.status})"
    return "error", f"connection failed — {fr.note.split(':')[0]}"


def _access(src: SourceConfig, f: PoliteFetcher, o: _Obs) -> str:
    url = src.feed_url or src.listing_url or src.entry_url
    ok, why = f.allowed(url)
    if not ok:
        o.access_kind = "robots"
        detail = (f"{why} — cannot safely proceed: nothing is fetched (handled conservatively, "
                  f"re-tested every check)")
        o.tests["access"] = _t("access", "FAIL", detail)
        return url
    fr = f.fetch(url, ttl_s=LISTING_TTL_S)
    if fr.content is None or fr.state is RetrievalState.BLOCKED:
        o.access_kind, reason = _denial(fr)
        o.tests["access"] = _t("access", "FAIL", f"{url}: {reason}")
        return url
    o.tests["access"] = _t("access", "PASS", f"{url} answered HTTP {fr.status} "
                                             f"({len(fr.content) // 1024} KB); {why}")
    return url


def _discover(src: SourceConfig, f: PoliteFetcher, o: _Obs, access_url: str,
              window_from: date) -> None:
    cov = SourceCoverage(source_id=src.id, publisher=src.publisher, channel=src.channel,
                         method=METHOD.get(src.adapter, src.adapter))
    adapter = ADAPTERS.get(src.adapter)
    if adapter is None:
        o.adapter_broken = True
        o.tests["discovery"] = _t("discovery", "FAIL", f"unknown adapter {src.adapter!r}")
        return
    try:
        raw = (trendforce_press(src, f, cov, oldest_needed=window_from)
               if adapter is trendforce_press else adapter(src, f, cov))
    except SourceBlockedError as exc:
        o.tests["discovery"] = _t("discovery", "FAIL", f"a listing page was refused — {exc}")
        return
    except RuntimeError as exc:  # the adapters' own "layout not recognised" signals
        o.tests["discovery"] = _t("discovery", "FAIL", f"the listing was fetched but its "
                                                       f"structure was not recognised: {exc}")
        o.tests["parser_integrity"] = _t("parser_integrity", "FAIL",
                                         f"listing parser: {exc}")
        return
    except Exception as exc:  # noqa: BLE001 — a broken adapter is an ERROR record, not a crash
        o.adapter_broken = True
        o.tests["discovery"] = _t("discovery", "FAIL",
                                  f"the discovery adapter failed ({type(exc).__name__})")
        return
    uniq: dict[str, Candidate] = {}
    for c in raw:
        u = canon(c.url)
        if u != canon(access_url):
            uniq.setdefault(u, c)
    o.cands = [Candidate(url=u, source_id=c.source_id, title=c.title, listed_date=c.listed_date,
                         date_basis=c.date_basis, lastmod=c.lastmod) for u, c in uniq.items()]
    n = len(o.cands)
    if not n:
        o.tests["discovery"] = _t("discovery", "FAIL", "the listing answered but no article URL "
                                                       "was found on it — suspected silent "
                                                       "failure (a layout change?)")
        return
    titled = sum(1 for c in o.cands if c.title)
    dated = sum(1 for c in o.cands if c.listed_date)
    o.tests["discovery"] = _t("discovery", "PASS", f"{n} article URL(s); {titled} with a title, "
                                                   f"{dated} with a listing date")


def _extract(src: SourceConfig, f: PoliteFetcher, o: _Obs,
             history: list[SourceHealthCheck]) -> None:
    """Fetch and parse up to SAMPLE_ARTICLES articles SPREAD across the listing (newest dated
    first, then listing order: its first, middle and last). The live runs of 2026-10-11 showed why
    — one sample hid SemiAnalysis's paid previews (its newest post was free), and the FIRST three
    of Bank of America's listing were one dated series while most of its pages state no date."""
    dated = sorted((c for c in o.cands if c.listed_date), key=lambda c: c.listed_date or date.min,
                   reverse=True)
    order = dated + [c for c in o.cands if not c.listed_date]
    k = min(SAMPLE_ARTICLES, len(order))
    picks = ([order[i] for i in sorted({round(j * (len(order) - 1) / (k - 1))
                                        for j in range(k)})] if k > 1 else order[:k])
    before: dict[str, int] = {}
    for h in history:  # oldest first: the latest reading of each page wins
        before.update(dict(h.sample_words_by_url))
    for c in picks:
        fr = f.fetch(c.url)
        if fr.content is None or fr.state is RetrievalState.BLOCKED:
            o.samples.append(_Sample(c, reason=_denial(fr)[1]))
            continue
        doc = parse_document(fr.text or "", c.url, fr.final_url)
        sm = _Sample(c, read=True, title=doc.title, kb=len(fr.content) // 1024,
                     published=doc.published_at.date() if doc.published_at else None,
                     authors=tuple(a.name for a in doc.authors), words=doc.word_count,
                     blocks=len(doc.body_blocks), retrieval=doc.retrieval_state,
                     notes=tuple(doc.notes))
        sm.paywall = any("paywall" in n for n in doc.notes)
        sm.linked_report = bool(doc.linked_reports) and not sm.paywall and not any(
            "short body" in n for n in doc.notes)
        if doc.retrieval_state is RetrievalState.BLOCKED:
            sm.parser_fail = (f"{c.url} answered HTTP 200 ({sm.kb} KB) but the parser recovered "
                              f"{sm.words} words — its structure is not read")
        elif (before.get(c.url, 0) >= BASELINE_MIN_WORDS and not sm.paywall
              and sm.words < COLLAPSE_RATIO * before[c.url]):
            sm.parser_fail = (f"{c.url}: {sm.words} words read now; the same page read "
                              f"{before[c.url]} at an earlier check — extraction collapsed")
        o.samples.append(sm)
    read = [x for x in o.samples if x.read]
    first = read[0] if read else None
    o.sample = (first or o.samples[0]).cand
    if first is not None:
        o.sample_doc_title, o.sample_published = first.title, first.published
        o.sample_authors, o.sample_words = first.authors, first.words
        o.sample_retrieval = first.retrieval.value if first.retrieval else None
        o.sample_notes = first.notes
    n = len(o.samples)
    broken = [x for x in read if x.parser_fail]
    gone = [x for x in o.samples if not x.read]
    if broken:
        o.tests["parser_integrity"] = _t(
            "parser_integrity", "FAIL", f"{len(broken)} of {n} sampled article page(s) answered "
                                        f"but were not read (parser failure suspected): "
                                        f"{broken[0].parser_fail}")
    elif read:
        words = sorted(x.words for x in read)
        o.tests["parser_integrity"] = _t(
            "parser_integrity", "PASS", f"{len(read)} of {n} sampled page(s) read, "
                                        f"{words[0]}–{words[-1]} words"
            + (f"; {sum(1 for x in read if x.cand.url in before)} re-read against an earlier "
               f"check" if before else ""))
    o.full_text = any(x.retrieval is RetrievalState.FULL and not x.parser_fail for x in read)
    if broken:
        o.tests["extraction"] = _t("extraction", "FAIL", o.tests["parser_integrity"].detail)
    elif gone:
        o.tests["extraction"] = _t("extraction", "FAIL", f"{len(gone)} of {n} sampled article "
                                                         f"page(s) could not be retrieved — "
                                                         f"{gone[0].cand.url}: {gone[0].reason}")
    else:
        full = sum(1 for x in read if x.retrieval is RetrievalState.FULL)
        o.tests["extraction"] = _t("extraction", "PASS" if full else "WARN",
                                   f"{len(read)} of {n} sampled article(s) read; {full} full text")


def _dates(o: _Obs, scan: dict[str, Any]) -> None:
    """The sampled pages' own dates and bylines, the listing's dates — and the latest scan's
    undated share, which reads EVERY candidate's page (a sample of three can miss it)."""
    if not o.cands:
        o.tests["dates_authors"] = _t("dates_authors", "SKIP", "no article discovered")
        return
    read = [x for x in o.samples if x.read]
    if not read:
        o.tests["dates_authors"] = _t("dates_authors", "SKIP", "no article was read")
        return
    listed = sum(1 for c in o.cands if c.listed_date)
    paged = sum(1 for x in read if x.published)
    undatable = [x for x in read if x.published is None and x.cand.listed_date is None]
    bylined = sum(1 for x in read if x.authors)
    facts = (f"{paged} of {len(read)} sampled page(s) state a publication date; the listing dates "
             f"{listed} of {len(o.cands)}; {bylined} of {len(read)} carry a byline"
             + (f"; latest scan {scan['run_id']}: {scan['undated']} of {scan['discovered']} "
                f"undated" if scan.get("run_id") and scan.get("discovered") else ""))
    scan_undated = bool(scan.get("discovered")) and scan.get("undated", 0) * 2 >= scan[
        "discovered"]
    if scan_undated and not undatable:
        o.tests["dates_authors"] = _t(
            "dates_authors", "FAIL", f"metadata problem: the latest scan found {scan['undated']} "
                                     f"of {scan['discovered']} article(s) with no publication "
                                     f"date — undated articles are never placed in a window "
                                     f"({facts})")
    elif undatable:
        o.tests["dates_authors"] = _t(
            "dates_authors", "FAIL", f"metadata problem: {len(undatable)} of {len(read)} sampled "
                                     f"article(s) carry no publication date on the page or the "
                                     f"listing — undated articles are never placed in a window "
                                     f"({facts})")
    elif paged < len(read) or bylined < len(read):
        o.tests["dates_authors"] = _t("dates_authors", "WARN", facts)
    else:
        o.tests["dates_authors"] = _t("dates_authors", "PASS", facts)


def _completeness(o: _Obs, scan: dict[str, Any], *, fetches_linked: bool = False) -> None:
    last = (f"; latest scan {scan['run_id']}: {scan['full']} full, {scan['partial']} preview / "
            f"partial, {scan['unreadable']} unreadable" if scan.get("run_id") else "")
    read = [x for x in o.samples if x.read and not x.parser_fail]
    if not read:
        o.tests["completeness"] = _t("completeness", "SKIP", "no article was read" + last)
        return
    n = len(read)
    previews = [x for x in read if x.paywall]
    partial = [x for x in read if x.retrieval is RetrievalState.PARTIAL and not x.paywall
               and not (fetches_linked and x.linked_report)]
    fetched = [x for x in read if fetches_linked and x.linked_report]
    last += (f"; {len(fetched)} sampled page(s) summarise a report they link to — the scan "
             f"READS it (linked_reports = \"fetch\")" if fetched else "")
    if previews:
        why = f"{len(previews)} of {n} sampled article(s) are paywalled previews — only the " \
              f"preview is readable"
    elif partial:
        note = next((m for m in partial[0].notes if "short body" in m or "summarises" in m),
                    "partial page")
        why = f"{len(partial)} of {n} sampled article(s) partial ({note})"
    elif scan.get("partial"):
        why = "the latest scan read previews / partial pages"
    else:
        o.tests["completeness"] = _t("completeness", "PASS", f"{n} of {n} sampled article(s) "
                                                             f"full text" + last)
        return
    o.tests["completeness"] = _t("completeness", "WARN", f"partial: {why}" + last)


def _freshness(o: _Obs, window_from: date, prev: SourceHealthCheck | None
               ) -> tuple[Freshness, date | None, int | None]:
    dates = [c.listed_date for c in o.cands if c.listed_date]
    if o.sample_published:
        dates.append(o.sample_published)
    newest = max(dates) if dates else None
    new = (len({c.url for c in o.cands} - set(prev.discovered_urls))
           if prev is not None and prev.discovered_urls and not prev.discovered_urls_truncated
           else None)
    if not o.cands:
        o.tests["freshness"] = _t("freshness", "SKIP", "no article discovered")
        return Freshness.UNKNOWN, None, new
    if newest is None:
        o.tests["freshness"] = _t("freshness", "SKIP", "no dated article to judge by")
        return Freshness.UNKNOWN, None, new
    fresh = newest >= window_from
    o.tests["freshness"] = _t(
        "freshness", "PASS" if fresh else "WARN",
        f"newest dated article {newest.isoformat()}" + (
            "" if fresh else f" — nothing dated since {window_from.isoformat()}: QUIET, not "
                             f"unhealthy") + (f"; {new} URL(s) new since the last check"
                                              if new is not None else ""))
    return (Freshness.FRESH if fresh else Freshness.QUIET), newest, new


def _status(o: _Obs) -> tuple[HealthStatus, str]:
    t = o.tests
    if o.access_kind in ("denied", "robots"):
        o.decisive = "access"
        return HealthStatus.BLOCKED, t["access"].detail
    if o.access_kind in ("missing", "error"):
        o.decisive = "access"
        return HealthStatus.ERROR, t["access"].detail
    if o.adapter_broken:
        o.decisive = "discovery"
        return HealthStatus.ERROR, t["discovery"].detail
    for name in ("discovery", "parser_integrity", "extraction", "dates_authors"):
        if name in t and t[name].result == "FAIL":
            o.decisive = name
            return HealthStatus.DEGRADED, t[name].detail
    if "completeness" in t and t["completeness"].result == "WARN":
        o.decisive = "completeness"
        return HealthStatus.DEGRADED, t["completeness"].detail
    return HealthStatus.HEALTHY, "discovery, a full-text article, its date and byline all read"


def _affected(o: _Obs, store: Store, sid: str) -> tuple[str, ...]:
    """Articles affected, as KNOWN — a URL with the title the listing gave, never an invented
    one."""
    out = []
    if o.sample is not None:
        out.append(o.sample.url + (f" — {o.sample.title}" if o.sample.title else
                                   " — title not known"))
    for url, st, meta in store.candidates():
        if meta.get("source_id") == sid and st in ("INACCESSIBLE", "BLOCKED", "NO_BODY"):
            t = meta.get("title")
            out.append(url + (f" — {t}" if t else " — title not known"))
    return tuple(dict.fromkeys(out))[:10]


def _action(src: SourceConfig, status: HealthStatus, o: _Obs, store: Store,
            consecutive: int) -> tuple[str, ManualAction | None]:
    upload = _UPLOAD.format(sid=src.id)
    d = o.decisive
    if status is HealthStatus.HEALTHY:
        return "none — automatic retrieval works", None
    if status is HealthStatus.UNKNOWN:
        return "run `python -m vinci.theme_intelligence sources --check-health`", None
    if status is HealthStatus.BLOCKED:
        act = (f"automatic access is refused or unsafe — never bypassed; re-tested every check. "
               f"Meanwhile {upload}")
        aff = _affected(o, store, src.id) or ("unknown — the channel cannot be read",)
        return act, ManualAction(kind="UPLOAD_REQUIRED", issue=o.tests["access"].detail,
                                 affected=aff, action=act)
    if status is HealthStatus.ERROR:
        act = (f"re-check: python -m vinci.theme_intelligence sources --check-health --sources "
               f"{src.id} --force; if it persists, inspect the configured endpoint")
        if consecutive >= 2:
            return act, ManualAction(kind="MANUAL_REVIEW", issue=o.tests[d].detail,
                                     affected=_affected(o, store, src.id), action=act)
        return act, None
    if d in ("extraction", "parser_integrity", "completeness"):
        act = (("review the article parser for this publisher; " if d != "completeness" else "")
               + f"{upload} if you are entitled to the full text")
        return act, ManualAction(kind="UPLOAD_REQUIRED", issue=o.tests[d].detail,
                                 affected=_affected(o, store, src.id), action=act)
    if d == "dates_authors":
        act = ("review: publication dates are not on the pages, so articles are counted UNDATED "
               "and never placed in a window — analyse one on demand with `article --url`")
    else:
        act = ("review the listing — no article was found on an accessible page; do NOT conclude "
               "the publisher published nothing")
    return act, ManualAction(kind="MANUAL_REVIEW", issue=o.tests[d].detail,
                             affected=_affected(o, store, src.id), action=act)


def _scan_stats(store: Store, sid: str) -> dict[str, Any]:
    """The latest finished SCAN that covered this channel: its articles by retrieval outcome."""
    for run in sorted(store.runs(), key=lambda r: r.started_at, reverse=True):
        if run.mode != "scan" or run.finished_at is None:
            continue
        cov = next((c for c in run.sources if c.source_id == sid), None)
        if cov is None:
            continue
        sts = [st for _u, st, m in store.candidates()
               if m.get("source_id") == sid and m.get("run_id") == run.run_id]
        return {"run_id": run.run_id, "discovered": cov.discovered,
                "full": sts.count("PROCESSED"),
                "partial": sts.count("PARTIAL_PROCESSED"), "undated": cov.undated,
                "unreadable": cov.inaccessible + sum(1 for s in sts
                                                     if s in ("BLOCKED", "NO_BODY", "FAILED"))}
    return {}


def _changes(prev: SourceHealthCheck | None, status: HealthStatus, o: _Obs, n: int,
             history: list[SourceHealthCheck]) -> list[str]:
    if prev is None:
        return ["first check of this channel"]
    out = []
    if prev.status is not status:
        out.append(f"{prev.status.value} → {status.value}")
    t = o.tests
    if prev.status is HealthStatus.BLOCKED and t.get("access") and t["access"].result == "PASS":
        out.append("a previously BLOCKED channel is accessible again — automatic retrieval "
                   "re-tested")
    before = {x.name: x.result for x in prev.tests}
    if before.get("extraction") == "PASS" and (
            t.get("extraction") and t["extraction"].result == "FAIL"):
        out.append(f"extraction worked at the last check ({prev.sample_words} words); it fails "
                   f"now — parser failure suspected")
    if prev.discovered > 0 and n == 0 and t.get("access") and t["access"].result == "PASS":
        out.append(f"discovered articles dropped to zero (was {prev.discovered}) on an accessible "
                   f"page — suspected silent failure: review before concluding nothing was "
                   f"published")
    elif prev.discovered >= 5 and 0 < n < 0.2 * prev.discovered:
        out.append(f"discovered articles fell from {prev.discovered} to {n} — review")
    if t.get("dates_authors") and t["dates_authors"].result == "FAIL":
        streak = 1
        for h in reversed(history):
            if next((x.result for x in h.tests if x.name == "dates_authors"), "") != "FAIL":
                break
            streak += 1
        if streak >= 2:
            out.append(f"publication dates missing at {streak} consecutive checks")
    return out


def _alert(prev: SourceHealthCheck | None, status: HealthStatus, decisive: str,
           consecutive: int, expect_blocked: bool) -> str:
    failing = status in FAILING
    if prev is None or prev.status is HealthStatus.UNKNOWN:
        if not failing:
            return ""
        return ("KNOWN_RESTRICTION" if expect_blocked and status is HealthStatus.BLOCKED
                else "NEW_FAILURE")
    if _RANK[status] < _RANK[prev.status]:
        return "RECOVERED"
    if not failing:
        return ""
    prev_decisive = _decisive_of(prev)
    if _RANK[status] > _RANK[prev.status] or (status, decisive) != (prev.status, prev_decisive):
        return "NEW_FAILURE"
    if expect_blocked and status is HealthStatus.BLOCKED:
        return "KNOWN_RESTRICTION" if consecutive == 1 else ""
    return "PERSISTENT_FAILURE" if consecutive == PERSISTENT_ALERT_AT else ""


def _decisive_of(h: SourceHealthCheck) -> str:
    """The test that set an earlier record's status (its first FAIL, else a WARN completeness)."""
    order = ("access", "discovery", "parser_integrity", "extraction", "dates_authors")
    res = {t.name: t.result for t in h.tests}
    for name in order:
        if res.get(name) == "FAIL":
            return name
    return "completeness" if res.get("completeness") == "WARN" else ""


def check_source(src: SourceConfig, f: PoliteFetcher, store: Store, *, trigger: str,
                 window_from: date, window_to: date, run_id: str | None = None,
                 now: datetime | None = None) -> SourceHealthCheck:
    """One channel, one bounded check (the live access fetch, the adapter's listing page(s),
    one article)."""
    now = now or datetime.now(tz=UTC)
    history = store.health_checks(src.id)
    prev = history[-1] if history else None
    o = _Obs()
    scan: dict[str, Any] = {}
    for u in (src.entry_url, src.listing_url, src.feed_url, src.sitemap_url):
        if u:  # the channel's own politeness floor on every host it is read from
            f.set_host_floor(u, src.min_crawl_delay_s)
    req0 = f.stats.requests
    cap = f.ttl_cap
    try:
        f.ttl_cap = 0.0  # the access test is LIVE
        access_url = _access(src, f, o)
        f.ttl_cap = FRESH_WITHIN_S  # the rest reuses what this check just fetched
        if o.access_kind == "ok":
            _discover(src, f, o, access_url, window_from)
            if o.cands:
                _extract(src, f, o, history)
            scan = _scan_stats(store, src.id)
            _dates(o, scan)
            _completeness(o, scan, fetches_linked=src.linked_reports == "fetch")
    finally:
        f.ttl_cap = cap
    freshness, newest, new = _freshness(o, window_from, prev)
    status, reason = _status(o)
    failed = status in FAILING
    consecutive = (prev.consecutive_failed_checks + 1 if prev and failed else 1 if failed else 0)
    next_action, manual = _action(src, status, o, store, consecutive)
    disc_ok = "discovery" in o.tests and o.tests["discovery"].result == "PASS"
    ext_ok = "extraction" in o.tests and o.tests["extraction"].result == "PASS" and o.full_text
    dated_ok = "dates_authors" in o.tests and o.sample_published is not None
    if o.access_kind != "ok":
        scan = {}
    urls = sorted(c.url for c in o.cands)
    order = ("access", "discovery", "extraction", "dates_authors", "completeness", "freshness",
             "parser_integrity")
    tests = tuple(o.tests.get(n) or _t(n, "SKIP", "not reached — an earlier test failed")
                  for n in order)
    return SourceHealthCheck(
        check_id="SH-" + hashlib.sha256(f"{src.id}|{now.isoformat()}".encode()).hexdigest()[:14],
        source_id=src.id, publisher=src.publisher, checked_at=now, trigger=trigger,
        run_id=run_id, status=status, reason=reason, next_action=next_action,
        expect_blocked=src.expect_blocked, tests=tests, freshness=freshness,
        newest_article_date=newest, window_from=window_from, window_to=window_to,
        discovered=len(o.cands), dated=sum(1 for c in o.cands if c.listed_date),
        titled=sum(1 for c in o.cands if c.title),
        in_window=sum(1 for c in o.cands if c.listed_date
                      and window_from <= c.listed_date <= window_to),
        new_since_last_check=new, discovered_urls=tuple(urls[:URL_CAP]),
        discovered_urls_truncated=len(urls) > URL_CAP,
        sample_url=o.sample.url if o.sample else None,
        sample_title=o.sample_doc_title or (o.sample.title if o.sample else None),
        sample_published=o.sample_published, sample_authors=o.sample_authors,
        sample_words=o.sample_words, sample_retrieval=o.sample_retrieval,
        sample_notes=o.sample_notes, samples=tuple(x.line() for x in o.samples),
        sample_words_by_url=tuple((x.cand.url, x.words) for x in o.samples
                                  if x.read and not x.parser_fail),
        last_scan_run_id=scan.get("run_id"),
        last_scan_full=scan.get("full", 0), last_scan_partial=scan.get("partial", 0),
        last_scan_undated=scan.get("undated", 0), last_scan_unreadable=scan.get("unreadable", 0),
        last_successful_discovery=now if disc_ok else (
            prev.last_successful_discovery if prev else None),
        last_successful_extraction=now if ext_ok else (
            prev.last_successful_extraction if prev else None),
        last_verified_publication_date=o.sample_published if dated_ok else (
            prev.last_verified_publication_date if prev else None),
        consecutive_failed_checks=consecutive,
        status_since=prev.status_since if prev and prev.status is status else now,
        manual_action=manual, changes=tuple(_changes(prev, status, o, len(o.cands), history)),
        alert=_alert(prev, status, o.decisive, consecutive, src.expect_blocked),
        requests=f.stats.requests - req0)


def _carry_reason(prev: SourceHealthCheck, now: datetime) -> str | None:
    """A channel that DENIED access (HTTP 401 / 403 / 451 or robots) is not re-requested before
    BLOCKED_RECHECK_HOURS have passed — the previous record stands, said plainly."""
    if prev.status is not HealthStatus.BLOCKED:
        return None
    due = prev.checked_at + timedelta(hours=BLOCKED_RECHECK_HOURS)
    if now >= due:
        return None
    return (f"not re-requested: access was refused at {prev.checked_at:%Y-%m-%d %H:%M} UTC; next "
            f"re-test after {due:%Y-%m-%d %H:%M} UTC (or pass --force)")


def notify(alerts: list[SourceHealthCheck]) -> str:
    """Hand NEW / PERSISTENT / RECOVERED alerts to the configured hook command (JSON on stdin).
    No hook configured is not an error: alerts stay on the dashboard and in the CLI report."""
    send = [h for h in alerts if h.alert in ("NEW_FAILURE", "PERSISTENT_FAILURE", "RECOVERED")]
    if not send:
        return ""
    cmd = os.environ.get(HOOK_ENV, "").strip()
    if not cmd:
        return f"not delivered — no channel configured ({HOOK_ENV} unset); shown on the dashboard"
    payload = json.dumps([{
        "source_id": h.source_id, "publisher": h.publisher, "alert": h.alert,
        "status": h.status.value, "reason": h.reason, "next_action": h.next_action,
        "changes": list(h.changes), "checked_at": h.checked_at.isoformat()} for h in send],
        indent=1)
    try:
        r = subprocess.run(shlex.split(cmd), input=payload, text=True, capture_output=True,
                           timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"delivery FAILED ({type(exc).__name__}) — shown on the dashboard"
    return (f"delivered to the hook ({len(send)} alert(s))" if r.returncode == 0
            else f"delivery FAILED (hook exit {r.returncode}) — shown on the dashboard")


def check_sources(sources: Iterable[SourceConfig], f: PoliteFetcher, store: Store, *,
                  trigger: str, window_from: date, window_to: date, run_id: str | None = None,
                  force: bool = False, now: datetime | None = None) -> HealthRun:
    """Check every channel; one channel's failure never stops the others. Records are written
    (append-only) after alerts are delivered, each carrying what the hook did with it."""
    srcs = list(sources)
    out = HealthRun(checks=[])
    fresh: list[SourceHealthCheck] = []
    for src in srcs:
        t = now or datetime.now(tz=UTC)
        hist = store.health_checks(src.id)
        why = None if force or not hist else _carry_reason(hist[-1], t)
        if why is not None:
            out.checks.append(hist[-1])
            out.skipped[src.id] = why
            continue
        try:
            h = check_source(src, f, store, trigger=trigger, window_from=window_from,
                             window_to=window_to, run_id=run_id, now=t)
        except Exception as exc:  # noqa: BLE001 — a crashed check is an ERROR record
            prev = hist[-1] if hist else None
            h = SourceHealthCheck(
                check_id="SH-" + hashlib.sha256(f"{src.id}|{t.isoformat()}".encode())
                .hexdigest()[:14], source_id=src.id, publisher=src.publisher, checked_at=t,
                trigger=trigger, run_id=run_id, status=HealthStatus.ERROR,
                reason=f"the health check itself failed ({type(exc).__name__})",
                next_action="re-run the check; if it persists, inspect the adapter",
                expect_blocked=src.expect_blocked,
                consecutive_failed_checks=(prev.consecutive_failed_checks + 1) if prev else 1,
                status_since=prev.status_since if prev and prev.status is HealthStatus.ERROR
                else t, last_successful_discovery=prev.last_successful_discovery if prev
                else None, last_successful_extraction=prev.last_successful_extraction if prev
                else None, last_verified_publication_date=prev.last_verified_publication_date
                if prev else None, changes=(f"{prev.status.value} → ERROR",) if prev
                and prev.status is not HealthStatus.ERROR else (),
                alert="NEW_FAILURE" if not prev or prev.status is not HealthStatus.ERROR else "")
        fresh.append(h)
    out.delivery = notify(fresh)
    for h in fresh:
        if h.alert in ("NEW_FAILURE", "PERSISTENT_FAILURE", "RECOVERED") and out.delivery:
            h = h.model_copy(update={"notified": out.delivery})
        with store.tx():
            store.add_health_check(h)
        out.checks.append(h)
    order = {s.id: i for i, s in enumerate(srcs)}
    out.checks.sort(key=lambda h: order.get(h.source_id, 0))
    return out


# --- readouts ------------------------------------------------------------------------------------

def summary(checks: list[SourceHealthCheck], configured: list[SourceConfig]) -> dict[str, Any]:
    """The compact dashboard block: counts over the CONFIGURED channels (a never-checked channel
    is UNKNOWN), the channels needing attention, and every channel's row."""
    by = {h.source_id: h for h in checks}
    rows = []
    for s in configured:
        h = by.get(s.id)
        rows.append({
            "source_id": s.id, "publisher": s.publisher,
            "status": h.status.value if h else HealthStatus.UNKNOWN.value,
            "reason": h.reason if h else "not checked yet",
            "next_action": h.next_action if h else "run `sources --check-health`",
            "freshness": h.freshness.value if h else Freshness.UNKNOWN.value,
            "newest_article_date": h.newest_article_date.isoformat()
            if h and h.newest_article_date else None,
            "checked_at": h.checked_at.isoformat() if h else None,
            "last_successful_discovery": h.last_successful_discovery.isoformat()
            if h and h.last_successful_discovery else None,
            "last_successful_extraction": h.last_successful_extraction.isoformat()
            if h and h.last_successful_extraction else None,
            "last_verified_publication_date": h.last_verified_publication_date.isoformat()
            if h and h.last_verified_publication_date else None,
            "discovered": h.discovered if h else 0, "in_window": h.in_window if h else 0,
            "last_scan": {"run_id": h.last_scan_run_id, "full": h.last_scan_full,
                          "partial": h.last_scan_partial, "undated": h.last_scan_undated,
                          "unreadable": h.last_scan_unreadable} if h else None,
            "consecutive_failed_checks": h.consecutive_failed_checks if h else 0,
            "manual_upload_recommended": bool(h and h.manual_upload_recommended),
            "manual_action": json.loads(h.manual_action.model_dump_json())
            if h and h.manual_action else None,
            "changes": list(h.changes) if h else [], "alert": h.alert if h else "",
            "expect_blocked": s.expect_blocked,
            "tests": [json.loads(t.model_dump_json()) for t in h.tests] if h else [],
        })
    counts = {st.value: sum(1 for r in rows if r["status"] == st.value) for st in HealthStatus}
    line = (f"Sources healthy: {counts['HEALTHY']}/{len(rows)} | Degraded: {counts['DEGRADED']} | "
            f"Blocked: {counts['BLOCKED']} | Errors: {counts['ERROR']}"
            + (f" | Unknown: {counts['UNKNOWN']}" if counts["UNKNOWN"] else ""))
    return {"line": line, "counts": counts, "total": len(rows),
            "checked_at": max(h.checked_at for h in checks).isoformat() if checks else None,
            "attention": [r for r in rows if r["status"] != HealthStatus.HEALTHY.value],
            "new_alerts": [r for r in rows if r["alert"] in ("NEW_FAILURE", "RECOVERED",
                                                              "PERSISTENT_FAILURE")],
            "rows": rows}


def render_text(run: HealthRun, configured: list[SourceConfig]) -> str:
    s = summary(run.checks, configured)
    out = [s["line"], ""]
    for r in s["rows"]:
        skip = run.skipped.get(r["source_id"])
        out.append(f"  {r['publisher']:<26} {r['status']:<9} {r['freshness']:<8} "
                   f"checked {(r['checked_at'] or '—')[:16]}  {r['reason'][:110]}")
        if skip:
            out.append(f"      {skip}")
    if s["new_alerts"]:
        out += ["", "Changes needing attention:"]
        for r in s["new_alerts"]:
            out.append(f"  [{r['alert']}] {r['publisher']}: {'; '.join(r['changes'])}")
    att = list(s["attention"])
    if att:
        out += ["", "Next actions:"]
        for r in att:
            out.append(f"  {r['publisher']} ({r['status']}): {r['next_action']}")
            if r["manual_action"]:
                out.append(f"      {r['manual_action']['kind']}: "
                           + "; ".join(r["manual_action"]["affected"][:3]))
    if run.delivery:
        out += ["", f"Alerts: {run.delivery}"]
    return "\n".join(out)


def to_json(run: HealthRun, configured: list[SourceConfig]) -> dict[str, Any]:
    s = summary(run.checks, configured)
    return {"summary": s["line"], "counts": s["counts"], "total": s["total"],
            "checked_at": s["checked_at"],
            "skipped": run.skipped, "alert_delivery": run.delivery, "sources": s["rows"]}
