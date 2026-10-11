"""One shared, deterministic pipeline behind every entry point (scan / article / report / qa).

PER ARTICLE: fetch → parse → (duplicate-content and look-ahead guards) → article + immutable
version records → idempotency guard → extraction (LLM pass 1, cached by content, with the
registry's existing thesis keys offered as alignment candidates) → WHOLE-ARTICLE completeness
(a deterministic figure / argument ledger from the text, then the independent pass 1b re-read;
its additions merged) → deterministic verification → text-credited authors added to the article
record → point-in-time SEC security resolution → engine (match / version / prioritise) → pass-2
review with re-anchoring → the completeness report persisted.

GUARANTEES
- A BLOCKED fetch is RECORDED (article + BLOCKED version) and counted — never silently omitted.
- Re-ingesting an article version that was already applied writes NOTHING: same version id, same
  extraction, and the engine is not re-run (no new records, no priority change, no confirmation).
- The same body under a changed URL is caught by its content hash and treated as one article.
- Replay (`--as-of`): an article published after the as-of date is refused (look-ahead), and any
  figure dated after it is blocked by verification.
- A run that fails is marked FAILED with its error; a scan that processed nothing because sources
  failed is never reported as a quiet week (the run status and coverage say what happened).
"""

from __future__ import annotations

import hashlib
import json
import traceback
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from vinci.graph.llm import LlmError
from vinci.theme_intelligence.budget import BudgetExceeded, GuardedClient, SpendGuard
from vinci.theme_intelligence.completeness import (
    CompletenessOutput,
    CompletenessResult,
    build_report,
    merge_completeness,
    run_completeness,
    scan_article,
)
from vinci.theme_intelligence.config import (
    COMPLETE_PROMPT_VERSION,
    ENGINE_VERSION,
    EXTRACT_PROMPT_VERSION,
    LLM_MODEL,
    LLM_PROVIDER,
    PARSER_VERSION,
    REVIEW_PROMPT_VERSION,
    Paths,
    SourceConfig,
    Taxonomy,
)
from vinci.theme_intelligence.discovery import METHOD, Discovery, discover_source
from vinci.theme_intelligence.engine import ArticleContext, Engine, ThesisOutcome
from vinci.theme_intelligence.extract import (
    COMPACT_MAX_CLAIMS,
    Extraction,
    ExtractionResult,
    InvalidAnswerError,
    ToolClient,
    cost_of,
    run_extraction,
)
from vinci.theme_intelligence.fetch import FetchResult, PoliteFetcher
from vinci.theme_intelligence.health import HealthRun, check_sources
from vinci.theme_intelligence.parse import ParsedDocument, parse_document
from vinci.theme_intelligence.schemas import (
    DB_SCHEMA_VERSION,
    Article,
    ArticleClass,
    ArticleVersion,
    Author,
    CardContent,
    Claim,
    FieldStatus,
    HealthStatus,
    IssueSeverity,
    RetrievalState,
    RunStatus,
    SecurityResolution,
    Snapshot,
    SourceCoverage,
    ThesisStatus,
    VerificationIssue,
    WeeklyRun,
)
from vinci.theme_intelligence.securities import SecResolver
from vinci.theme_intelligence.store import Store
from vinci.theme_intelligence.verify import (
    ReviewOutcome,
    deterministic_card_checks,
    norm_name,
    review_card,
    verify_extraction,
)


def _sha(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p.encode())
        h.update(b"\x00")
    return h.hexdigest()


def article_id_for(canonical_url: str) -> str:
    return "A-" + _sha(canonical_url.rstrip("/").lower())[:12]


@dataclass
class ArticleResult:
    url: str
    status: str  # PROCESSED | BLOCKED | PARTIAL_PROCESSED | ALREADY_INGESTED | DUPLICATE_CONTENT
    #              | LOOKAHEAD | NO_BODY | FAILED
    article_id: str | None = None
    version_id: str | None = None
    outcomes: list[ThesisOutcome] = field(default_factory=list)
    note: str = ""
    extraction_cost: float | None = None


class Pipeline:
    def __init__(self, data_dir: Path, *, sources: tuple[SourceConfig, ...], taxonomy: Taxonomy,
                 client: ToolClient | None, fetcher: PoliteFetcher | None = None,
                 resolver: SecResolver | None = None, review: bool = True,
                 store: Store | None = None) -> None:
        self.paths = Paths(data_dir)
        self.paths.ensure()
        self.store = store or Store(self.paths.db)
        self.sources = {s.id: s for s in sources}
        self.taxonomy = taxonomy
        #: every paid model call goes through the spend guard (budget.py) — bound, check, record
        self.guard = SpendGuard()
        self.client: Any = GuardedClient(client, self.guard) if client is not None else None
        self.fetcher = fetcher or PoliteFetcher(self.paths.http_cache)
        for s in sources:
            self.fetcher.set_host_floor(s.entry_url, s.min_crawl_delay_s)
        self.resolver = resolver or SecResolver(self.paths.http_cache)
        self.review = review
        self.run: WeeklyRun | None = None
        #: the source-health pass taken at the start of the current scan (None before one)
        self.health: HealthRun | None = None
        self._calls = 0
        # the deterministic card checks ALWAYS run; `review=False` skips only the pass-2 LLM
        # review, and says so in the validation log rather than passing silently
        self.engine = Engine(self.store, taxonomy, reviewer=self._review)

    # -- runs -----------------------------------------------------------------------------------
    def start_run(self, mode: str, *, as_of: date, window_from: date | None = None,
                  window_to: date | None = None, run_id: str | None = None) -> WeeklyRun:
        now = datetime.now(tz=UTC)
        rid = run_id or f"R-{now.strftime('%Y%m%dT%H%M%SZ')}-{mode}"
        if run_id is None:  # two runs in one second must never share — and overwrite — an id
            base, n = rid, 2
            while self.store.run(rid) is not None:
                rid, n = f"{base}-{n}", n + 1
        elif self.store.run(rid) is not None:
            raise ValueError(f"run {rid} already exists — resume it with --resume instead")
        run = WeeklyRun(
            run_id=rid, mode=mode, window_from=window_from, window_to=window_to, as_of=as_of,
            started_at=now, status=RunStatus.RUNNING, llm_provider=LLM_PROVIDER,
            llm_model=self.client.model if self.client is not None else LLM_MODEL,
            extract_prompt_version=EXTRACT_PROMPT_VERSION,
            review_prompt_version=REVIEW_PROMPT_VERSION, parser_version=PARSER_VERSION,
            engine_version=ENGINE_VERSION, db_schema_version=DB_SCHEMA_VERSION,
            complete_prompt_version=COMPLETE_PROMPT_VERSION,
            output_dir=str(self.paths.runs / rid))
        self.store.upsert_run(run)
        self.run = run
        self.guard.start_run(mode)
        return run

    def finish_run(self, status: RunStatus, *, error: str | None = None) -> WeeklyRun:
        assert self.run is not None
        run = self.run
        if error:
            run.warnings.append(f"RUN ERROR: {error}")
        calls = self.store.llm_calls(run.run_id)
        tok: dict[str, int] = {}
        replayed: dict[str, int] = {}
        cost: float | None = 0.0
        llm_s = 0.0
        for c in calls:
            bucket = replayed if c.get("cached") else tok  # a cache hit spends nothing now
            for k, v in (c.get("usage") or {}).items():
                if k != "max_tokens":
                    bucket[k] = bucket.get(k, 0) + int(v)
            if c.get("cost_usd") is None and not c.get("cached"):
                cost = None
            elif cost is not None:
                cost += float(c.get("cost_usd") or 0.0)
            llm_s += float(c.get("seconds") or 0.0)
        run.tokens = tok
        for k, v in replayed.items():
            run.counts[f"replayed_from_cache_{k}"] = v
        run.cost_usd = round(cost, 4) if cost is not None else None
        run.llm_seconds = round(llm_s, 1)
        run.fetch_seconds = round(self.fetcher.stats.seconds, 1)
        run.counts["llm_calls"] = len(calls)
        run.counts["llm_calls_cached"] = sum(1 for c in calls if c.get("cached"))
        run.spend = self.guard.summary()
        if self.guard.refusals:
            run.warnings.append(f"spend guard: {len(self.guard.refusals)} paid call(s) refused "
                                f"for want of budget — {self.guard.refusals[0]}")
        run.counts["http_requests"] = self.fetcher.stats.requests
        run.counts["http_cache_hits"] = self.fetcher.stats.cache_hits
        run.finished_at = datetime.now(tz=UTC)
        run.status = status
        self.store.upsert_run(run)
        theses = self.store.theses()
        snap = Snapshot(snapshot_id="SN-" + _sha(run.run_id, run.finished_at.isoformat())[:14],
                        run_id=run.run_id,
                        as_of=run.as_of,
                        thesis_versions=tuple((t.thesis_id, t.current_version) for t in theses),
                        created_at=datetime.now(tz=UTC), report_paths=())
        self.store.add_snapshot(snap)
        return run

    def _count(self, key: str, n: int = 1) -> None:
        assert self.run is not None
        self.run.counts[key] = self.run.counts.get(key, 0) + n

    def _llm_call(self, purpose: str, ref: str, res_cached: bool, usage: dict[str, int] | None,
                  cost: float | None, seconds: float, model: str, prompt_version: str) -> None:
        assert self.run is not None
        self._calls += 1
        self.store.add_llm_call(
            "LC-" + _sha(self.run.run_id, purpose, ref, str(self._calls),
                         datetime.now(tz=UTC).isoformat())[:14], self.run.run_id, purpose,
            {"purpose": purpose, "ref": ref, "model": model, "prompt_version": prompt_version,
             "cached": res_cached,
             "usage": usage, "cost_usd": cost, "seconds": round(seconds, 2),
             "at": datetime.now(tz=UTC).isoformat()})

    # -- review hook ------------------------------------------------------------------------------
    def _review(self, card: CardContent, claims: dict[str, Claim]) -> ReviewOutcome:
        assert self.run is not None
        issues = deterministic_card_checks(card, claims, self.run.run_id)
        if not self.review:
            issues.append(VerificationIssue(
                issue_id="VI-" + _sha(self.run.run_id, card.header.thesis_id, "review-off",
                                      card.header.title)[:14],
                run_id=self.run.run_id, scope="thesis", ref_id=card.header.thesis_id,
                severity=IssueSeverity.WARN, code="REVIEW_NOT_RUN",
                detail="pass-2 LLM review disabled for this run (--no-review); only the "
                       "deterministic card checks ran", created_at=datetime.now(tz=UTC)))
            return ReviewOutcome(issues)
        try:
            rr = review_card(card, claims, client=self.client, cache_dir=self.paths.llm_cache,
                             run_id=self.run.run_id)
        except BudgetExceeded as exc:  # refused for want of budget: said, never pretended
            issues.append(VerificationIssue(
                issue_id="VI-" + _sha(self.run.run_id, card.header.thesis_id, "budget")[:14],
                run_id=self.run.run_id, scope="thesis", ref_id=card.header.thesis_id,
                severity=IssueSeverity.WARN, code="REVIEW_NOT_RUN",
                detail=f"pass-2 review not run — budget: {exc}",
                created_at=datetime.now(tz=UTC)))
            return ReviewOutcome(issues)
        except RuntimeError as exc:  # no client and no cache: say so, never pretend reviewed
            issues.append(VerificationIssue(
                issue_id="VI-" + _sha(self.run.run_id, card.header.thesis_id, "noreview")[:14],
                run_id=self.run.run_id, scope="thesis", ref_id=card.header.thesis_id,
                severity=IssueSeverity.WARN, code="REVIEW_NOT_RUN", detail=str(exc),
                created_at=datetime.now(tz=UTC)))
            return ReviewOutcome(issues)
        self._llm_call("review", card.header.thesis_id + ":" + card.header.title[:40], rr.cached,
                       rr.usage, rr.cost_usd, rr.seconds,
                       self.client.model if self.client else LLM_MODEL, REVIEW_PROMPT_VERSION)
        return ReviewOutcome(issues + rr.issues, rr.anchors)

    # -- one article ------------------------------------------------------------------------------
    def process_url(self, url: str, *, source_id: str, as_of: date,
                    html: str | None = None, fixture: dict[str, Any] | None = None,
                    publisher_override: str | None = None,
                    listed: tuple[date, str] | None = None,
                    completeness_fixture: dict[str, Any] | None = None,
                    html_note: str = "supplied fixture HTML",
                    declared_published: date | None = None,
                    linked_fixture: dict[str, Any] | None = None) -> ArticleResult:
        assert self.run is not None
        src = self.sources.get(source_id)
        publisher = publisher_override or (src.publisher if src else "UNKNOWN publisher")
        default_class = ArticleClass(src.default_article_class) if src else ArticleClass.OTHER
        now = datetime.now(tz=UTC)
        try:
            if html is None:
                fr = self.fetcher.fetch(url)
            else:
                body = html.encode()
                fr = FetchResult(url=url, final_url=url, status=200,
                                 state=RetrievalState.FULL, note=html_note,
                                 content=body, content_type="text/html", fetched_at=now,
                                 sha256=hashlib.sha256(body).hexdigest(), cache_path=None,
                                 from_cache=False, seconds=0.0)
        except Exception as exc:  # noqa: BLE001 — recorded, never swallowed into a quiet zero
            fr = FetchResult(url, None, None, RetrievalState.BLOCKED,
                             f"fetch error {type(exc).__name__}: {str(exc)[:160]}", None, None,
                             now, None, None, False, 0.0)
        if fr.state is RetrievalState.BLOCKED or fr.text is None:
            return self._record_blocked(url, source_id, publisher, default_class, fr)
        doc = parse_document(fr.text, url, fr.final_url)
        if doc.published_at is None and listed is not None:
            # the page states no date, but the publisher's own listing / URL / feed did
            d, basis = listed
            doc.published_at = datetime(d.year, d.month, d.day)
            doc.published_raw = d.isoformat()
            doc.published_source = f"publisher listing — {basis} (date only)"
            doc.published_status = FieldStatus.KNOWN
        if doc.published_at is None and declared_published is not None:
            d = declared_published
            doc.published_at = datetime(d.year, d.month, d.day)
            doc.published_raw = d.isoformat()
            doc.published_source = "operator-verified (the page states no date)"
            doc.published_status = FieldStatus.KNOWN
        res = self.process_document(doc, fr, url=url, source_id=source_id, as_of=as_of,
                                    fixture=fixture, publisher_override=publisher_override,
                                    completeness_fixture=completeness_fixture)
        if doc.linked_reports and res.article_id and res.status in (
                "PROCESSED", "PARTIAL_PROCESSED", "ALREADY_INGESTED"):
            self._linked_report(doc, res, source_id, as_of, linked_fixture)
        return res

    def _linked_report(self, doc: ParsedDocument, res: ArticleResult, source_id: str,
                       as_of: date, fixture: dict[str, Any] | None) -> None:
        """The fuller report a page links to: fetched and read as a NEW VERSION of the same
        article where the channel permits (`linked_reports = "fetch"`), else listed for an
        authorised upload. Never an authenticated route; robots.txt obeyed by the fetcher."""
        from vinci.theme_intelligence.documents import Declared, DocumentError, file_sha256
        from vinci.theme_intelligence.ingest import ingest_file

        assert self.run is not None and res.article_id is not None
        src = self.sources.get(source_id)
        _text, link = doc.linked_reports[0]
        if any(link in d.declared.get("via", "") for d in self.store.documents()):
            return  # already read in an earlier run
        upload = (f"upload an authorised copy: python -m vinci.theme_intelligence ingest-file "
                  f"--path <report> --source {source_id} --url {doc.canonical_url}")
        if src is None or src.linked_reports != "fetch":
            self._issue("article", res.article_id, IssueSeverity.WARN, "LINKED_REPORT_UPLOAD",
                        f"{doc.canonical_url} summarises a fuller report it links to ({link}); "
                        f"the channel's policy is to request it, never to fetch it — {upload}")
            self._count("linked_reports_requested")
            return
        key = f"linked_reports_fetched_{source_id}"
        if self.run.counts.get(key, 0) >= src.max_linked_reports:
            self._issue("article", res.article_id, IssueSeverity.WARN, "LINKED_REPORT_UPLOAD",
                        f"{doc.canonical_url} links its fuller report ({link}); not read this "
                        f"run — the cap max_linked_reports={src.max_linked_reports} was reached "
                        f"(read in a later run, or {upload})")
            self._count("linked_reports_deferred")
            return
        self._count(key)
        fr = self.fetcher.fetch(link)
        if fr.content is None or not fr.content.startswith(b"%PDF-"):
            self._issue("article", res.article_id, IssueSeverity.WARN, "LINKED_REPORT_UPLOAD",
                        f"{doc.canonical_url} links its fuller report ({link}), which could not be "
                        f"read automatically ({fr.state.value}: {fr.note[:160]}; "
                        f"{fr.content_type or 'no content'}) — {upload}")
            self._count("linked_reports_unreadable")
            return
        store = self.paths.root / "documents"
        store.mkdir(mode=0o700, parents=True, exist_ok=True)
        tmp = store / f"linked-report-{hashlib.sha256(fr.content).hexdigest()[:16]}.pdf"
        tmp.write_bytes(fr.content)
        tmp.chmod(0o600)
        try:
            out = ingest_file(self, tmp, Declared(
                source_id=source_id, llm_permitted=True,
                via=f"linked report fetched automatically from {link} (linked from "
                    f"{doc.canonical_url}; robots.txt obeyed)"),
                as_of=as_of, same_as=res.article_id, fixture=fixture)
        except DocumentError as exc:
            self._issue("article", res.article_id, IssueSeverity.WARN, "LINKED_REPORT_UPLOAD",
                        f"{link}: {exc} — {upload}")
            self._count("linked_reports_unreadable")
            return
        finally:
            if tmp.exists() and (store / f"{file_sha256(tmp)}.pdf").exists():
                tmp.unlink()  # ingest_file kept its own copy, named by content
        if out.status == "HELD":
            self._issue("article", res.article_id, IssueSeverity.WARN, "LINKED_REPORT_UPLOAD",
                        f"{doc.canonical_url} links its fuller report ({link}); fetched but "
                        f"HELD, not analysed — {out.note}")
        self._count(f"linked_reports_{out.status.lower()}")

    def process_document(self, doc: ParsedDocument, fr: FetchResult, *, url: str,
                         source_id: str, as_of: date, fixture: dict[str, Any] | None = None,
                         publisher_override: str | None = None,
                         completeness_fixture: dict[str, Any] | None = None,
                         cost_limit: float | None = None) -> ArticleResult:
        """Everything after parsing. Tests and replays enter here with an already-parsed
        document (e.g. an authentic excerpt) — the same code path the live fetch takes.
        `cost_limit`: this document's actual-spend limit (default config.DOC_COST_LIMIT_USD)."""
        assert self.run is not None
        self.guard.begin_document(article_id_for(doc.canonical_url), cost_limit)
        try:
            return self._process_document(doc, fr, url=url, source_id=source_id, as_of=as_of,
                                          fixture=fixture, publisher_override=publisher_override,
                                          completeness_fixture=completeness_fixture)
        finally:
            self.guard.end_document()

    def _process_document(self, doc: ParsedDocument, fr: FetchResult, *, url: str,
                          source_id: str, as_of: date, fixture: dict[str, Any] | None,
                          publisher_override: str | None,
                          completeness_fixture: dict[str, Any] | None) -> ArticleResult:
        assert self.run is not None
        src = self.sources.get(source_id)
        publisher = publisher_override or (src.publisher if src else "UNKNOWN publisher")
        reliability = src.reliability if src else "medium"
        default_class = ArticleClass(src.default_article_class) if src else ArticleClass.OTHER
        now = datetime.now(tz=UTC)
        aid = article_id_for(doc.canonical_url)
        # same body already registered under another URL → one article (changed URL)
        if doc.retrieval_state is not RetrievalState.BLOCKED:
            dup = self.store.conn.execute(
                "SELECT article_id FROM article_versions WHERE content_sha256=? AND "
                "article_id<>? LIMIT 1", (doc.content_sha256, aid)).fetchone()
            if dup:
                self._count("duplicate_content")
                return ArticleResult(url, "DUPLICATE_CONTENT", str(dup[0]),
                                     note=f"identical body already registered as {dup[0]} "
                                          f"(URL changed or mirrored) — not re-counted")
        state = (RetrievalState.PARTIAL if fr.state is RetrievalState.PARTIAL
                 else doc.retrieval_state)
        article = self._article_record(aid, doc, source_id, publisher, default_class, now)
        version = ArticleVersion(
            version_id="AV-" + doc.content_sha256[:16], article_id=aid,
            retrieved_at=fr.fetched_at, http_status=fr.status, final_url=fr.final_url,
            retrieval_state=state, retrieval_note="; ".join([fr.note, *doc.notes]),
            raw_sha256=fr.sha256, content_sha256=doc.content_sha256,
            modified_at=doc.modified_at, modified_source=doc.modified_source,
            evidence_location=str(fr.cache_path) if fr.cache_path else None,
            parser_version=PARSER_VERSION, body_word_count=doc.word_count, blocks=doc.blocks)
        existing_v = self.store.version_by_content(aid, doc.content_sha256)
        with self.store.tx():
            self.store.upsert_article(article)
            if existing_v is None:
                self.store.add_article_version(version)
        version = existing_v or version
        if state is RetrievalState.BLOCKED:
            self._issue("article", aid, IssueSeverity.WARN, "NO_BODY",
                        f"{url} — page retrieved but no article body found "
                        f"({version.retrieval_note}); not analysed")
            self._count("articles_no_body")
            return ArticleResult(url, "NO_BODY", aid, version.version_id,
                                 note=version.retrieval_note)
        if doc.published_at is not None and doc.published_at.date() > as_of:
            self._issue("article", aid, IssueSeverity.BLOCK, "LOOKAHEAD",
                        f"published {doc.published_at.date()} is after the run as-of {as_of} — "
                        f"not analysed (publication-time replay)")
            self._count("articles_lookahead_refused")
            return ArticleResult(url, "LOOKAHEAD", aid, version.version_id)
        if self._applied(aid, version.version_id):
            self._count("articles_already_ingested")
            return ArticleResult(url, "ALREADY_INGESTED", aid, version.version_id,
                                 note="this article version was already applied — no new records")

        try:
            xres = self._extract(doc, publisher, as_of, fixture, self._registry_context())
        except BudgetExceeded as exc:
            return self._budget_held(url, aid, version.version_id, exc)
        except InvalidAnswerError as exc:  # paid and unusable: record the spend, then fail loud
            for u in exc.usages:
                self._llm_call("extract-invalid", aid, False, u, cost_of(exc.model, u), 0.0,
                               exc.model, exc.prompt_version)
            raise
        if xres.truncated_usage is not None and not xres.cached:  # the billed, discarded attempt
            self._llm_call("extract-truncated", aid, False, xres.truncated_usage,
                           cost_of(xres.model, xres.truncated_usage), 0.0, xres.model,
                           EXTRACT_PROMPT_VERSION)
        self._llm_call("extract", aid, xres.cached, xres.usage, xres.cost_usd, xres.seconds,
                       xres.model, xres.prompt_version)
        for d in xres.dropped:
            self._issue("article", aid, IssueSeverity.WARN, "MALFORMED_ITEM_DROPPED",
                        f"extraction: {d}")
        for note, u in xres.set_aside:
            if u is not None:  # billed this run, discarded
                self._llm_call("extract-invalid", aid, False, u, cost_of(xres.model, u), 0.0,
                               xres.model, xres.prompt_version)
            self._issue("article", aid, IssueSeverity.WARN, "ANSWER_SET_ASIDE", note)
        if xres.compact:
            out_t = (xres.truncated_usage or {}).get("output_tokens")
            self._issue("article", aid, IssueSeverity.WARN, "EXTRACTION_COMPACT",
                        f"the full extraction overran the output cap ({out_t} output tokens, "
                        f"discarded) — this article was extracted in the declared COMPACT mode "
                        f"(at most {COMPACT_MAX_CLAIMS} claims); the completeness pass re-reads "
                        f"the whole article for what that leaves out")
        if xres.extraction.article_classification.article_class != article.article_class:
            self._issue("article", aid, IssueSeverity.INFO, "CLASS_DISAGREES",
                        f"model classifies {xres.extraction.article_classification.article_class}"
                        f" ({xres.extraction.article_classification.basis[:140]}); the record "
                        f"keeps {article.article_class.value} ({article.article_class_basis})")
        # WHOLE-ARTICLE completeness: the ledger is read from the TEXT first; pass 1b accounts
        # for every gap; its additions go through the same verification as pass 1
        ledger = scan_article(doc)
        try:
            comp, comp_note = self._complete(doc, xres, ledger, publisher, as_of, aid,
                                             fixture is not None, completeness_fixture)
        except BudgetExceeded as exc:
            return self._budget_held(url, aid, version.version_id, exc)
        merged = merge_completeness(xres.extraction, comp.output if comp else None)
        for d in merged.dropped:
            self._issue("article", aid, IssueSeverity.WARN, "MALFORMED_ITEM_DROPPED",
                        f"completeness merge: {d}")
        ve = verify_extraction(doc, merged.extraction, article_id=aid,
                               article_version_id=version.version_id,
                               extraction_id=xres.extraction_id, publisher=publisher,
                               as_of=as_of, run_id=self.run.run_id)
        report = build_report(ledger=ledger, ve=ve, merged=merged,
                              output=comp.output if comp else None,
                              article_version_id=version.version_id, run_id=self.run.run_id,
                              pass_ran=comp is not None, note=comp_note)
        article = self._with_text_authors(article, doc, ve)
        if state is RetrievalState.PARTIAL:
            ve.issues.append(VerificationIssue(
                issue_id="VI-" + _sha(self.run.run_id, aid, "partial")[:14],
                run_id=self.run.run_id, scope="article", ref_id=aid, severity=IssueSeverity.WARN,
                code="PARTIAL_RETRIEVAL", detail="only part of the article was retrieved — no "
                "claim of full-text verification is made", created_at=datetime.now(tz=UTC)))
        resolutions: dict[str, SecurityResolution] = {}
        for m in ve.mentions:
            try:
                resolutions[m.mention_id] = self.resolver.resolve(m, as_of=as_of)
            except Exception as exc:  # noqa: BLE001 — resolution failure is UNRESOLVED, loudly
                self._issue("mention", m.mention_id, IssueSeverity.WARN, "RESOLUTION_FAILED",
                            f"{m.name_as_written}: {type(exc).__name__}: {str(exc)[:120]}")
        ctx = ArticleContext(article=article, version=version, reliability=reliability,
                             run_id=self.run.run_id, as_of=as_of)
        outcomes = self.engine.apply(ctx, ve, resolutions)
        self._record_completeness(aid, report)
        # the extraction record is the "applied" marker — written only AFTER the engine succeeds,
        # so a run that dies mid-article re-processes it (idempotently) instead of skipping it
        if comp is not None:
            self.store.add_extraction("XC" + xres.extraction_id[1:], version.version_id,
                                      comp.model, comp.prompt_version, comp.raw)
        self.store.add_extraction(xres.extraction_id, version.version_id, xres.model,
                                  xres.prompt_version, xres.raw)
        self._count("articles_processed")
        if state is RetrievalState.PARTIAL:
            self._count("articles_partial")
        self._count("claims_extracted", len(ve.claims))
        self._count("claims_verified", len(ve.verified_claims))
        self._count("mentions", len(ve.mentions))
        self._count("theses_created", sum(1 for o in outcomes if o.created))
        self._count("theses_updated", sum(1 for o in outcomes if not o.created and o.new_version))
        self._count("attributions_only", sum(1 for o in outcomes
                                              if not o.created and not o.new_version))
        return ArticleResult(url, "PARTIAL_PROCESSED" if state is RetrievalState.PARTIAL
                             else "PROCESSED", aid, version.version_id, outcomes,
                             extraction_cost=xres.cost_usd)

    def _budget_held(self, url: str, aid: str, version_id: str,
                     exc: BudgetExceeded) -> ArticleResult:
        """CHECKPOINT: nothing about the article is written; the answers already paid for stay
        in the content-addressed cache, so a re-run with a higher limit resumes without paying
        for them again."""
        self._issue("article", aid, IssueSeverity.WARN, "BUDGET_HELD",
                    f"{url} — not analysed: {exc}. Resume with a higher limit (scan --budget / "
                    f"ingest-file --max-cost); answers already paid for are reused from the cache")
        self._count("articles_budget_held")
        return ArticleResult(url, "BUDGET_HELD", aid, version_id, note=str(exc))

    def _applied(self, aid: str, version_id: str) -> bool:
        rows = self.store.conn.execute(
            "SELECT COUNT(*) FROM extractions WHERE article_version_id=?", (version_id,)).fetchone()
        return bool(rows and rows[0])

    def _registry_context(self) -> list[tuple[str, str]]:
        """The registry's theses as alignment candidates for the extractor: node|mechanism|
        direction|geography — title, freshest material update first. `other`-keyed theses are
        left out (they never merge by key)."""
        ts = [t for t in self.store.theses() if t.status is not ThesisStatus.ARCHIVED
              and "other" not in (t.key_node, t.key_mechanism)]
        ts.sort(key=lambda t: (t.last_material_update, t.thesis_id), reverse=True)
        return [(f"{t.key_node}|{t.key_mechanism}|{t.key_direction.value}|{t.key_geography}",
                 t.title) for t in ts]

    def _extract(self, doc: ParsedDocument, publisher: str, as_of: date,
                 fixture: dict[str, Any] | None,
                 registry: list[tuple[str, str]] | None = None) -> ExtractionResult:
        if fixture is not None:
            ext = Extraction.model_validate(fixture)
            key = _sha(json.dumps(fixture, sort_keys=True), doc.content_sha256)
            return ExtractionResult(ext, fixture, f"X-FIXTURE-{key[:12]}", "fixture",
                                    "fixture", True, None, 0.0, 0.0)
        return run_extraction(doc, publisher=publisher, as_of=as_of.isoformat(),
                              taxonomy=self.taxonomy, client=self.client,
                              cache_dir=self.paths.llm_cache, registry=registry)

    def _complete(self, doc: ParsedDocument, xres: ExtractionResult, ledger: Any,
                  publisher: str, as_of: date, aid: str, fixture_mode: bool,
                  completeness_fixture: dict[str, Any] | None,
                  ) -> tuple[CompletenessResult | None, str]:
        """Pass 1b. A frozen fixture replays a frozen pass 1b; a fixture WITHOUT one runs the
        deterministic ledger only and says so (WARN) — never a silent pass."""
        if completeness_fixture is not None:
            out = CompletenessOutput.model_validate(completeness_fixture)
            return CompletenessResult(out, completeness_fixture, True, None, 0.0, 0.0,
                                      "fixture", "fixture"), "frozen completeness fixture"
        if fixture_mode:
            note = ("fixture replay without a frozen completeness pass — only the deterministic "
                    "figure / argument ledger ran")
            self._issue("article", aid, IssueSeverity.WARN, "COMPLETENESS_PASS_NOT_RUN", note)
            return None, note
        try:
            res = run_completeness(doc, xres.extraction, ledger, publisher=publisher,
                                   as_of=as_of.isoformat(), taxonomy=self.taxonomy,
                                   client=self.client, cache_dir=self.paths.llm_cache)
        except InvalidAnswerError as exc:  # paid, unusable: spend recorded, gap reported
            for u in exc.usages:
                self._llm_call("complete-invalid", aid, False, u, cost_of(exc.model, u), 0.0,
                               exc.model, exc.prompt_version)
            self._issue("article", aid, IssueSeverity.WARN, "COMPLETENESS_PASS_NOT_RUN",
                        str(exc))
            return None, str(exc)
        except (RuntimeError, LlmError) as exc:  # no client / no cache / an overrun: the gap
            self._issue("article", aid, IssueSeverity.WARN,  # is reported, never hidden
                        "COMPLETENESS_PASS_NOT_RUN", str(exc))
            return None, str(exc)
        for call in res.calls:  # one record per call — a discarded (split) call included
            purpose = ("complete" + (f"-{call.label}" if call.label else "")
                       + ("-truncated" if call.truncated else ""))
            self._llm_call(purpose, aid, call.cached, call.usage, call.cost_usd, call.seconds,
                           res.model, res.prompt_version)
        for n in res.notes:
            self._issue("article", aid, IssueSeverity.INFO, "COMPLETENESS_IN_PARTS", n)
        for d in res.dropped:
            self._issue("article", aid, IssueSeverity.WARN, "MALFORMED_ITEM_DROPPED",
                        f"completeness pass: {d}")
        return res, ""

    def _record_completeness(self, aid: str, report: Any) -> None:
        """Persist the ledger; every figure still uncaptured and every argument block still
        unaccounted for is an OPEN issue (WARN), listed in full — never truncated."""
        assert self.run is not None
        self.store.add_completeness(report)
        for f in report.uncaptured:
            self._issue("article", aid, IssueSeverity.WARN, "FIGURE_UNCAPTURED",
                        f"{f.block_id}: {f.figure!r} — {f.reason} — sentence {f.sentence!r}")
        for b in report.unaccounted_blocks:
            self._issue("article", aid, IssueSeverity.WARN, "ARGUMENT_UNACCOUNTED",
                        f"{b.block_id}: {b.reason}")
        self._count("figures_in_articles", len(report.figures))
        self._count("figures_uncaptured", len(report.uncaptured))
        self._count("claims_added_by_completeness", report.added_claims)
        self._count("theses_added_by_completeness", report.added_hypotheses)

    def _with_text_authors(self, article: Article, doc: ParsedDocument,
                           ve: Any) -> Article:
        """Authors the article TEXT credits ("team led by …"), verified as spans, joined to the
        metadata authors; a metadata disagreement and any declared alternate versions are
        recorded as issues so the attribution trail is visible."""
        aid = article.article_id
        if doc.author_discrepancy:
            self._issue("article", aid, IssueSeverity.INFO, "AUTHOR_METADATA_DISCREPANCY",
                        doc.author_discrepancy)
        if doc.alternates:
            self._issue("article", aid, IssueSeverity.INFO, "ALTERNATE_VERSIONS_DECLARED",
                        f"{len(doc.alternates)} alternate version(s) declared (hreflang), not "
                        f"fetched: " + "; ".join(f"{h} {u}" for h, u in doc.alternates))
        have = {norm_name(a.name) for a in article.authors}
        extra = [Author(name=a.name, title=None,
                        source_field=f"article text {a.block_id}: {a.quote[:120]!r}")
                 for a in ve.authors if norm_name(a.name) not in have]
        if not extra:
            return article
        self._issue("article", aid, IssueSeverity.INFO, "AUTHORS_FROM_TEXT",
                    "credited in the article text, not in page metadata: "
                    + "; ".join(f"{a.name} ({a.source_field})" for a in extra))
        updated = article.model_copy(update={"authors": (*article.authors, *extra),
                                             "authors_status": FieldStatus.KNOWN})
        self.store.upsert_article(updated)
        return updated

    def _article_record(self, aid: str, doc: ParsedDocument, source_id: str, publisher: str,
                        default_class: ArticleClass, now: datetime) -> Article:
        prior = self.store.article(aid)
        cls, basis = default_class, f"channel default for {source_id}"
        if doc.article_class_hint is not None:
            cls, basis = doc.article_class_hint, doc.article_class_basis or "page statement"
        return Article(
            article_id=aid, canonical_url=doc.canonical_url, source_id=source_id,
            publisher=publisher, title=doc.title, title_source=doc.title_source,
            authors=doc.authors, authors_status=doc.authors_status,
            published_at=doc.published_at, published_raw=doc.published_raw,
            published_source=doc.published_source, published_status=doc.published_status,
            article_class=cls, article_class_basis=basis,
            first_seen_at=prior.first_seen_at if prior else now)

    def _record_blocked(self, url: str, source_id: str, publisher: str,
                        default_class: ArticleClass, fr: FetchResult) -> ArticleResult:
        aid = article_id_for(url)
        now = datetime.now(tz=UTC)
        prior = self.store.article(aid)
        art = prior or Article(
            article_id=aid, canonical_url=url, source_id=source_id, publisher=publisher,
            title=None, title_source=None, authors=(), authors_status=FieldStatus.UNKNOWN,
            published_at=None, published_raw=None, published_source=None,
            published_status=FieldStatus.UNKNOWN, article_class=default_class,
            article_class_basis="channel default (page not retrieved)", first_seen_at=now)
        v = ArticleVersion(
            version_id="AV-BLOCKED-" + _sha(url, fr.note, fr.fetched_at.isoformat())[:12],
            article_id=aid,
            retrieved_at=fr.fetched_at, http_status=fr.status, final_url=fr.final_url,
            retrieval_state=RetrievalState.BLOCKED, retrieval_note=fr.note, raw_sha256=None,
            content_sha256=None, modified_at=None, modified_source=None, evidence_location=None,
            parser_version=PARSER_VERSION, body_word_count=0)
        with self.store.tx():
            self.store.upsert_article(art)
            self.store.add_article_version(v)
        self._issue("article", aid, IssueSeverity.WARN, "RETRIEVAL_BLOCKED",
                    f"{url} — {fr.note} (kept as a BLOCKED record; not analysed)")
        self._count("articles_blocked")
        return ArticleResult(url, "BLOCKED", aid, v.version_id, note=fr.note)

    def _issue(self, scope: str, ref: str, sev: IssueSeverity, code: str, detail: str) -> None:
        assert self.run is not None
        self.store.add_issue(VerificationIssue(
            issue_id="VI-" + _sha(self.run.run_id, scope, ref, code, detail)[:14],
            run_id=self.run.run_id,
            scope=scope, ref_id=ref, severity=sev, code=code, detail=detail,
            created_at=datetime.now(tz=UTC)))

    # -- convenience ------------------------------------------------------------------------------
    def run_article(self, url: str, *, as_of: date, source_id: str = "manual",
                    publisher: str | None = None, html: str | None = None,
                    fixture: dict[str, Any] | None = None,
                    html_note: str = "supplied fixture HTML",
                    published: date | None = None,
                    budget: float | None = None) -> tuple[WeeklyRun, ArticleResult]:
        """One article — fetched, or an operator-supplied copy (`html`): the manual-upload route
        for a BLOCKED or DEGRADED channel, through the SAME pipeline. An upload never changes the
        channel's health record: one document is not proof the channel's coverage is complete."""
        self.start_run("article", as_of=as_of, window_from=as_of, window_to=as_of)
        if budget is not None:
            self.guard.run_limit = budget
        try:
            res = self.process_url(url, source_id=source_id, as_of=as_of, html=html,
                                   fixture=fixture, publisher_override=publisher,
                                   html_note=html_note, declared_published=published)
        except Exception as exc:
            self.finish_run(RunStatus.FAILED, error=f"{type(exc).__name__}: {exc}\n"
                                                    f"{traceback.format_exc()[-1500:]}")
            raise
        assert self.run is not None
        self.engine.archive_pass(run_id=self.run.run_id, as_of=as_of)
        status = RunStatus.SUCCEEDED if res.status in (
            "PROCESSED", "ALREADY_INGESTED", "DUPLICATE_CONTENT") else RunStatus.PARTIAL
        return self.finish_run(status), res

    def run_scan(self, *, window_from: date, window_to: date, as_of: date, max_articles: int,
                 resume_run_id: str | None = None, budget: float | None = None) -> WeeklyRun:
        """Discover every source's window, then process in-window candidates up to the budget.

        RESUMABLE: after every article the run's checkpoint (url → outcome) is saved; `--resume`
        reloads an interrupted run with its ORIGINAL window and as-of and skips what it already
        did. BUDGETED: candidates past `max_articles` are QUEUED (persisted) and offered first next
        run — the cap is printed as "processed X of Y", never a silent drop. HONEST STATUS: a run
        is PARTIAL when any source failed that is not a documented standing refusal, or any
        in-window article could not be read; FAILED/INTERRUPTED when it stopped."""
        if resume_run_id:
            prior = self.store.run(resume_run_id)
            if prior is None:
                raise ValueError(f"no run {resume_run_id} to resume")
            if prior.status is RunStatus.SUCCEEDED or prior.mode != "scan":
                raise ValueError(f"{resume_run_id} is {prior.status.value} ({prior.mode}) — "
                                 f"nothing to resume")
            assert prior.window_from is not None and prior.window_to is not None
            window_from, window_to, as_of = prior.window_from, prior.window_to, prior.as_of
            prior.status = RunStatus.RUNNING
            prior.warnings.append(f"resumed at {datetime.now(tz=UTC).isoformat()} — "
                                  f"{len(prior.checkpoint)} article(s) already done are skipped")
            self.run = prior
            self.store.upsert_run(prior)
            self.guard.start_run("scan")
        else:
            self.start_run("scan", as_of=as_of, window_from=window_from, window_to=window_to)
        if budget is not None:
            self.guard.run_limit = budget
        run = self.run
        assert run is not None
        try:
            # SOURCE HEALTH first, at the start of every new scan (manual or scheduled): bounded,
            # LLM-free, persisted — and never able to stop the scan
            if not resume_run_id:
                try:
                    self.health = check_sources(
                        list(self.sources.values()), self.fetcher, self.store, trigger="scan",
                        run_id=run.run_id, window_from=window_from, window_to=window_to)
                except Exception as exc:  # noqa: BLE001 — the scan goes on; the gap is said
                    self.health = None
                    run.warnings.append(f"source-health check failed ({type(exc).__name__}) — "
                                        f"the scan continued without it")
            denied = {h.source_id: h for h in (self.health.checks if self.health else [])
                      if h.status is HealthStatus.BLOCKED
                      and any(t.name == "access" and t.result == "FAIL" for t in h.tests)}
            # what earlier runs QUEUED is read FIRST, before discovery touches the table, and
            # it is offered ahead of this run's own candidates
            carried = [(url, meta) for url, _st, meta in self.store.candidates("QUEUED")]
            for url, meta in carried:  # a channel no longer active never has its queue read
                sid = str(meta.get("source_id", ""))
                if sid not in self.sources:
                    self.store.upsert_candidate(url, sid, "SOURCE_INACTIVE", {
                        **meta, "run_id": run.run_id,
                        "note": f"{sid} is not an active channel — never processed"})
            carried = [(u, m) for u, m in carried if str(m.get("source_id", "")) in self.sources]
            discoveries: list[Discovery] = []
            for src in self.sources.values():
                h = denied.get(src.id)
                if src.mode == "manual_first":  # a health check only: no discovery attempt
                    hc = next((x for x in (self.health.checks if self.health else [])
                               if x.source_id == src.id), None)
                    d = Discovery(SourceCoverage(
                        source_id=src.id, publisher=src.publisher, channel=src.channel,
                        method="manual-first: lightweight health check only — research "
                               "arrives as authorised uploads (ingest-file)",
                        checked_at=hc.checked_at if hc else None, status="MANUAL_FIRST",
                        warnings=[f"automated access: {hc.status.value} — {hc.reason[:160]}"
                                  if hc else "automated access not checked this run"]), [])
                elif h is not None:  # refused at the endpoint moments ago — never asked twice
                    bcov = SourceCoverage(
                        source_id=src.id, publisher=src.publisher, channel=src.channel,
                        method=METHOD.get(src.adapter, src.adapter), checked_at=h.checked_at,
                        status="BLOCKED", errors=[f"{h.reason} (source-health check "
                                                  f"{h.check_id})"])
                    if src.expect_blocked:
                        bcov.warnings.append("standing access limitation recorded in "
                                            "sources.toml — this channel refuses the honest "
                                            "research User-Agent; it is reported every run, "
                                            "never bypassed")
                    d = Discovery(bcov, [])
                else:
                    d = discover_source(src, self.fetcher, self.store, window_from=window_from,
                                        window_to=window_to)
                discoveries.append(d)
                for c in d.candidates:
                    queued_c = self.store.candidate(c.url)
                    if queued_c is not None and queued_c[0] == "QUEUED":
                        continue  # stays QUEUED until it is processed
                    # a candidate stored UNDATED / INACCESSIBLE that discovery now rules out of
                    # the window is updated too — a stale row would stay on the review list
                    stale = (queued_c is not None and queued_c[0] in ("UNDATED", "INACCESSIBLE")
                             and c.status == "OUT_OF_WINDOW")
                    if c.status in ("IN_WINDOW", "INACCESSIBLE", "UNDATED") or stale:
                        self.store.upsert_candidate(c.url, src.id, c.status, {
                            "source_id": src.id, "run_id": run.run_id, "title": c.title,
                            "listed_date": c.listed_date, "date_basis": c.date_basis,
                            "note": c.note})
            run.sources = [d.coverage for d in discoveries]
            self.store.upsert_run(run)
            cov = {d.coverage.source_id: d.coverage for d in discoveries}
            disc_status = {c.url: c.status for d in discoveries for c in d.candidates}
            todo: list[tuple[str, str, str]] = []
            seen: set[str] = set()
            for url, meta in carried:
                sid = str(meta.get("source_id", ""))
                if url not in seen and sid in self.sources:
                    todo.append((url, sid, f"carried over from {meta.get('run_id')}"))
                    seen.add(url)
            fresh = sorted((c for d in discoveries for c in d.selected),
                           key=lambda c: c.listed_date or date.min, reverse=True)
            for c in fresh:
                if c.url not in seen:
                    todo.append((c.url, c.source_id, c.date_basis))
                    seen.add(c.url)
            done = queued = failures = 0
            out_of_budget = False
            for url, sid, why in todo:
                if url in run.checkpoint:
                    continue
                if out_of_budget:  # the budget is spent: the rest wait for the next run
                    known = self.store.candidate(url)
                    self.store.upsert_candidate(url, sid, "QUEUED", {
                        **(known[1] if known else {}), "source_id": sid,
                        "run_id": run.run_id, "reason": "spend guard: run budget exhausted"})
                    queued += 1
                    if sid in cov:
                        cov[sid].queued += 1
                    continue
                if done >= max_articles:
                    known = self.store.candidate(url)
                    self.store.upsert_candidate(url, sid, "QUEUED", {
                        **(known[1] if known else {}), "source_id": sid,
                        "run_id": run.run_id, "reason": f"budget cap max_articles={max_articles}"})
                    queued += 1
                    if sid in cov:
                        cov[sid].queued += 1
                    continue
                src = self.sources[sid]
                if disc_status.get(url) == "INACCESSIBLE":
                    note = next((c.note for d in discoveries for c in d.candidates
                                 if c.url == url), "inaccessible during discovery")
                    res = self._record_blocked(url, sid, src.publisher, ArticleClass(
                        src.default_article_class), FetchResult(
                        url, None, None, RetrievalState.BLOCKED, note, None, None,
                        datetime.now(tz=UTC), None, None, False, 0.0))
                else:
                    cand = next((c for d in discoveries for c in d.candidates if c.url == url),
                                None)
                    res = self.process_url(url, source_id=sid, as_of=as_of, listed=(
                        (cand.listed_date, cand.date_basis)
                        if cand is not None and cand.listed_date is not None else None))
                if res.status == "BUDGET_HELD":  # checkpointed: offered first next run
                    out_of_budget = True
                    self.store.upsert_candidate(url, sid, "QUEUED", {
                        "source_id": sid, "run_id": run.run_id,
                        "reason": f"spend guard: {res.note[:200]}"})
                    queued += 1
                    if sid in cov:
                        cov[sid].queued += 1
                    run.warnings.append(f"spend guard: the run budget is exhausted — "
                                        f"{res.note[:200]}; the remaining candidates are QUEUED "
                                        f"(resume with --budget)")
                    continue
                done += 1
                run.checkpoint[url] = res.status
                self.store.upsert_candidate(url, sid, res.status, {
                    "source_id": sid, "run_id": run.run_id, "article_id": res.article_id,
                    "why": why, "note": res.note[:240]})
                c_ = cov.get(sid)
                if res.status in ("PROCESSED", "PARTIAL_PROCESSED"):
                    if c_:
                        c_.processed += 1
                elif res.status in ("BLOCKED", "NO_BODY", "FAILED"):
                    failures += 1
                    if c_ and disc_status.get(url) != "INACCESSIBLE":
                        c_.inaccessible += 1
                self.store.upsert_run(run)
            if queued:
                run.warnings.append(f"budget: processed {done} of {done + queued} candidate "
                                    f"article(s) this run (max_articles={max_articles}); "
                                    f"{queued} QUEUED for the next run")
            self._count("articles_queued", queued)
            self.engine.archive_pass(run_id=run.run_id, as_of=as_of)
            failing = [sc.source_id for sc in run.sources
                       if sc.status in ("BLOCKED", "ERROR")
                       and not self.sources[sc.source_id].expect_blocked]
            degraded = [sc.source_id for sc in run.sources if sc.status == "PARTIAL"]
            if failing:
                run.warnings.append(f"source(s) failed this run: {', '.join(failing)}")
            if degraded:
                run.warnings.append(f"source(s) partially covered: {', '.join(degraded)}")
            status = (RunStatus.PARTIAL if failing or degraded or failures or out_of_budget
                      else RunStatus.SUCCEEDED)
            return self.finish_run(status)
        except KeyboardInterrupt:
            self.finish_run(RunStatus.INTERRUPTED,
                            error=f"interrupted — resume with: scan --resume {run.run_id}")
            raise
        except Exception as exc:
            self.finish_run(RunStatus.FAILED, error=f"{type(exc).__name__}: {exc}\n"
                                                    f"{traceback.format_exc()[-1500:]}")
            raise


