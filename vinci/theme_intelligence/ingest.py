"""Manual-document ingestion — a supplied report enters the SAME pipeline, registry and weekly
dashboard as an automatically retrieved article: source attribution, whole-article
completeness, number and citation verification, company / sector identification, thesis
extraction, claim-level relationship rules, Research Now / Watch / Skip, the nine-section card,
version history. The input method never changes research priority.

IDENTITY, before any model is asked:
  the same FILE (its bytes) again ............................ DUPLICATE — nothing re-counted
  the same TEXT already registered (another file / format) .... DUPLICATE
  the operator states the article's URL, and an article is held under it:
      fuller than what is held (a preview, a teaser) ......... UPGRADE — a NEW VERSION of the
                                                               same article, re-extracted and
                                                               re-checked; the earlier version is
                                                               kept, never overwritten
      the same text ........................................... DUPLICATE
      otherwise ............................................... REVIEW
  no URL: the same publisher's articles are compared by title, date and text overlap — a clear
  match is an UPGRADE or a DUPLICATE as above; a partial one is REVIEW (a human decides, never
  an automatic merge); none is a NEW article (a report with no public URL is identified by its
  content: urn:document:sha256:…)

LICENCE: a document's text is sent to the third-party LLM only when that is authorised — by the
operator for this document, or by the channel's `manual_llm_processing = "permitted"` in
sources.toml. Otherwise it is HELD (read, stored privately, listed for review) until released.

PRIVACY: the original file is copied into the git-ignored data directory (owner-only
permissions); its full text lives only in the local registry, which exports without article
text. Nothing here prints document text.
"""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass, field, replace
from datetime import UTC, date, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from vinci.theme_intelligence.config import (
    DOC_COST_CHARS_PER_TOKEN,
    DOC_COST_LIMIT_USD,
    DOC_COST_OUTPUT_TOKENS_LOW,
    DOC_COST_REVIEWS_USD,
    LLM_MAX_TOKENS,
    LLM_MODEL,
    PARSER_VERSION,
    PRICE_PER_MTOK,
)
from vinci.theme_intelligence.documents import (
    Declared,
    DocumentError,
    DocumentRead,
    read_document,
)
from vinci.theme_intelligence.fetch import FetchResult
from vinci.theme_intelligence.parse import ParsedDocument
from vinci.theme_intelligence.schemas import (
    Article,
    DocumentRecord,
    FieldStatus,
    IssueSeverity,
    RetrievalState,
)

if TYPE_CHECKING:
    from vinci.theme_intelligence.pipeline import ArticleResult, Pipeline

#: shingle size for text-overlap comparison (words)
SHINGLE = 8
#: the share of the HELD text found in the new document at which it is the same article
CONTAINED = 0.6
#: both ways at least this much, and similar length: the same text in another format
SAME_TEXT = 0.85
#: a TEXT overlap from here up (short of the rules above) is REVIEW, never an automatic merge
WEAK_OVERLAP = 0.2
#: a TITLE overlap alone sends a document to REVIEW only from here up — a publisher's titles share
#: house words (two different TrendForce releases overlapped 21% with 0% text in common)
TITLE_REVIEW = 0.5
NEW, UPGRADE, DUPLICATE, REVIEW = "NEW", "UPGRADE", "DUPLICATE", "REVIEW"
#: the same text is registered but was never analysed (an earlier run failed mid-way): the SAME
#: article, analysed now — never a duplicate of an analysis that does not exist
RETRY = "RETRY"


@dataclass
class Match:
    kind: str  # NEW | UPGRADE | DUPLICATE | REVIEW
    article: Article | None
    basis: str


@dataclass
class IngestResult:
    doc_id: str
    status: str  # INGESTED | UPGRADED | DUPLICATE | REVIEW | HELD | REJECTED | (pipeline status)
    article_id: str | None = None
    version_id: str | None = None
    note: str = ""
    issues: list[str] = field(default_factory=list)


def _norm(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+(?:[.,][0-9]+)*%?", text.lower())


def shingles(text: str) -> set[tuple[str, ...]]:
    w = _norm(text)
    return {tuple(w[i:i + SHINGLE]) for i in range(max(0, len(w) - SHINGLE + 1))}


def containment(a: set[tuple[str, ...]], b: set[tuple[str, ...]]) -> float:
    """The share of `a` found in `b`."""
    return len(a & b) / len(a) if a else 0.0


def title_overlap(a: str | None, b: str | None) -> float:
    """Token overlap of two titles (Jaccard), 1.0 when one is a prefix of the other."""
    ta, tb = _norm(a or ""), _norm(b or "")
    if not ta or not tb:
        return 0.0
    if " ".join(tb).startswith(" ".join(ta)) or " ".join(ta).startswith(" ".join(tb)):
        return 1.0 if min(len(ta), len(tb)) >= 3 else 0.5
    return len(set(ta) & set(tb)) / len(set(ta) | set(tb))


def _held_text(pipe: Pipeline, article_id: str) -> tuple[str, RetrievalState | None, int]:
    """The latest readable version's text — "" when this machine does not hold it (a registry
    pulled from the state branch keeps block hashes, never article text)."""
    vs = [v for v in pipe.store.article_versions(article_id)
          if v.retrieval_state is not RetrievalState.BLOCKED]
    if not vs:
        return "", None, 0
    v = vs[-1]
    return " ".join(b.text for b in v.blocks).strip(), v.retrieval_state, v.body_word_count


#: the blocks that carry the argument — a byline, a date line or a disclaimer is shared by every
#: report of one publisher and proves nothing
_ARGUMENT_KINDS = frozenset({"paragraph", "list_item"})


def _shared_words(pipe: Pipeline, article_id: str, read: DocumentRead) -> int:
    """Words of the new document's argument blocks whose HASH the held version also has — what
    a pulled registry can still compare (it keeps each block's hash, never its text)."""
    vs = [v for v in pipe.store.article_versions(article_id)
          if v.retrieval_state is not RetrievalState.BLOCKED]
    if not vs:
        return 0
    held = {b.sha256 for b in vs[-1].blocks if b.kind in _ARGUMENT_KINDS}
    seen: dict[str, int] = {}
    for b in read.doc.blocks:
        if b.kind in _ARGUMENT_KINDS and b.sha256 in held:
            seen[b.sha256] = len(b.text.split())
    return sum(seen.values())


def _compare(pipe: Pipeline, art: Article, read: DocumentRead, *, stated: bool,
             url_basis: str = "the operator states its URL") -> Match:
    """One held article against the new document."""
    held, state, words = _held_text(pipe, art.article_id)
    new_text = " ".join(b.text for b in read.doc.blocks)
    new_words = len(new_text.split())
    s_old, s_new = shingles(held), shingles(new_text)
    c_old = containment(s_old, s_new)  # the held text inside the new document
    c_new = containment(s_new, s_old)
    t = title_overlap(art.title, read.doc.title)
    same_date = (art.published_at is not None and read.doc.published_at is not None
                 and art.published_at.date() == read.doc.published_at.date())
    # a PULLED registry holds no text, only block hashes: the argument blocks the two share,
    # weighted by their words, stand in for the text overlap — evidence for REVIEW, never for an
    # automatic merge (2026-10-14: a retitled copy of a held report was analysed, and paid for,
    # a second time on title overlap alone)
    pulled = state is not None and not held
    shared = _shared_words(pipe, art.article_id, read) if pulled else 0
    b_old = shared / words if words else 0.0
    b_new = shared / new_words if new_words else 0.0
    facts = (f"title overlap {t:.0%}, held text found in the new document {c_old:.0%}, new "
             f"text found in the held {c_new:.0%}; held {words} words "
             f"({state.value if state else 'no readable version'}), new {new_words} words"
             + (f"; dates {art.published_at.date() if art.published_at else '?'} vs "
                f"{read.doc.published_at.date() if read.doc.published_at else '?'}")
             + (f"; the held text is NOT on this machine (a pulled registry keeps no article "
                f"text) — compared by URL, title, date and block hashes: {shared} word(s) of "
                f"identical argument blocks, {b_old:.0%} of the held, {b_new:.0%} of the new"
                if pulled else ""))
    lead = f"{url_basis}; " if stated else ""
    if held and c_old >= SAME_TEXT and c_new >= SAME_TEXT:
        return Match(DUPLICATE, art, f"{lead}the same text in another file or format ({facts})")
    fuller = new_words > max(words * 1.3, words + 150)
    if held and c_old >= CONTAINED and fuller:
        if state is RetrievalState.PARTIAL:
            return Match(UPGRADE, art, f"{lead}a fuller version of the held article ({facts})")
        # the held article is COMPLETE: a longer document containing it is another edition, an
        # appendix or page furniture (a printed web page) — never assumed to complete it
        return Match(REVIEW, art, f"{lead}contains the held COMPLETE article plus more — another "
                                  f"edition, an appendix or page furniture: a human decides "
                                  f"({facts})")
    if (stated or (t >= 0.8 and same_date)) and fuller and (
            state is RetrievalState.PARTIAL or state is None) and t >= 0.5:
        return Match(UPGRADE, art, lead
                     + f"a fuller document for a {state.value if state else 'unread'} article "
                       f"({facts})")
    if (stated or t >= TITLE_REVIEW or c_old >= WEAK_OVERLAP or c_new >= WEAK_OVERLAP
            or b_old >= WEAK_OVERLAP or b_new >= WEAK_OVERLAP):
        return Match(REVIEW, art, f"{lead}an uncertain match — a human decides ({facts})")
    return Match(NEW, None, facts)


def identify(pipe: Pipeline, read: DocumentRead, declared: Declared) -> Match:
    """Which article, if any, the document already is — see the module docstring."""
    st = pipe.store
    row = st.conn.execute("SELECT article_id, version_id FROM article_versions WHERE "
                          "content_sha256=? LIMIT 1", (read.doc.content_sha256,)).fetchone()
    if row:
        if not pipe._applied(str(row[0]), str(row[1])):  # noqa: SLF001 — the pipeline's own test
            return Match(RETRY, st.article(str(row[0])),
                         "the same text is registered but was never analysed (an earlier run "
                         "did not finish) — analysed now")
        return Match(DUPLICATE, st.article(str(row[0])),
                     "the same text is already registered (another file or format)")
    # the operator's URL, or the one the document states for itself (a saved page's canonical
    # link) — bibliographic identity; a urn is only the content's own name
    if declared.url or not read.doc.canonical_url.startswith("urn:"):
        art = st.article_by_url(read.doc.canonical_url)
        if art is not None:
            return _compare(pipe, art, read, stated=True, url_basis=(
                "the operator states its URL" if declared.url
                else "the document states its own URL (canonical link)"))
        if declared.url:
            return Match(NEW, None, "the operator states a URL not yet held")
    best: Match | None = None
    for art in (a for a in _articles(pipe) if a.source_id == declared.source_id):
        m = _compare(pipe, art, read, stated=False)
        if m.kind in (UPGRADE, DUPLICATE):
            return m
        if m.kind == REVIEW and best is None:
            best = m
    return best or Match(NEW, None, "no article of this publisher resembles it")


@dataclass(frozen=True)
class CostEstimate:
    parts: int
    figures: int
    paragraphs: int
    low: float
    high: float

    def line(self) -> str:
        return (f"estimated ${self.low:,.0f}–${self.high:,.0f} (list price): up to {self.parts} "
                f"completeness part(s) for {self.figures} stated figure(s) and "
                f"{self.paragraphs} argument paragraph(s)")


def estimate_cost(read: DocumentRead) -> CostEstimate:
    """Deterministic, before any model call — from the text the reader will SEND (glyph output
    already quarantined) and the ledger's gaps; see config.DOC_COST_CHARS_PER_TOKEN."""
    from vinci.theme_intelligence.completeness import scan_article

    led = scan_article(read.doc)
    return estimate_from(sum(len(b.text) for b in read.doc.blocks), len(led.figures),
                         len(led.argument_blocks))


def estimate_from(chars: int, figures: int, paragraphs: int,
                  model: str = LLM_MODEL) -> CostEstimate:
    """The cost range of analysing `chars` characters of text with `figures` + `paragraphs`
    ledger gaps (config.DOC_COST_* — the HIGH end prices every call at its output cap)."""
    import math

    from vinci.theme_intelligence.completeness import GAPS_PER_CALL

    parts = max(1, math.ceil((figures + paragraphs) / GAPS_PER_CALL))
    pin, pout = (p / 1_000_000 for p in PRICE_PER_MTOK[model])
    (p_lo, p_hi), (x_lo, x_hi) = (DOC_COST_CHARS_PER_TOKEN["part"],
                                  DOC_COST_CHARS_PER_TOKEN["extract"])
    r_lo, r_hi = DOC_COST_REVIEWS_USD
    low = (parts * (chars / p_lo * pin + DOC_COST_OUTPUT_TOKENS_LOW["part"] * pout)
           + chars / x_lo * pin + DOC_COST_OUTPUT_TOKENS_LOW["extract"] * pout + r_lo)
    high = (parts * (chars / p_hi * pin + LLM_MAX_TOKENS * pout)
            + 2 * (chars / x_hi * pin + LLM_MAX_TOKENS * pout) + r_hi)
    return CostEstimate(parts, figures, paragraphs, round(low, 2), round(high, 2))


def _articles(pipe: Pipeline) -> list[Article]:
    return [Article.model_validate_json(p) for (p,) in
            pipe.store.conn.execute("SELECT payload FROM articles ORDER BY article_id")]


class InactiveSourceError(DocumentError):
    """The named channel is retired or not configured: nothing from it is imported."""


def _require_active(pipe: Pipeline, declared: Declared) -> None:
    from vinci.theme_intelligence.config import retired_for

    if declared.source_id in pipe.sources:
        r = retired_for(url=declared.url) if declared.url else None
        if r is not None:
            raise InactiveSourceError(f"{declared.url} is on a host of {r.publisher}, a channel "
                                      f"retired on {r.retired} — not imported")
        return
    r = retired_for(source_id=declared.source_id)
    if r is not None:
        raise InactiveSourceError(f"{r.publisher} ({r.id}) was retired on {r.retired} — "
                                  f"{r.reason}; its research is not imported")
    raise InactiveSourceError(f"{declared.source_id!r} is not an active channel — one of: "
                              f"{', '.join(sorted(pipe.sources))}")


def llm_authorised(pipe: Pipeline, declared: Declared) -> tuple[bool, str]:
    if declared.llm_permitted is not None:
        return declared.llm_permitted, ("the operator states third-party LLM processing is "
                                        + ("permitted" if declared.llm_permitted
                                           else "NOT permitted") + " for this document")
    src = pipe.sources.get(declared.source_id)
    policy = src.manual_llm_processing if src else "unknown"
    if policy == "permitted":
        return True, f"sources.toml: manual documents of {declared.source_id} may be processed"
    return False, (f"third-party LLM processing is not authorised for this document (channel "
                   f"policy {policy!r}, no statement for this file) — HELD for review")


def _store_copy(pipe: Pipeline, path: Path, read: DocumentRead) -> str:
    """The original file, privately, under the git-ignored data directory (owner-only)."""
    store = pipe.paths.root / "documents"
    store.mkdir(mode=0o700, parents=True, exist_ok=True)
    dest = store / f"{read.sha256}{path.suffix.lower()}"
    if not dest.exists():
        shutil.copyfile(path, dest)
        dest.chmod(0o600)
    return str(dest.relative_to(pipe.paths.root))


def ingest_file(pipe: Pipeline, path: Path, declared: Declared, *, as_of: date | None = None,
                force_new: bool = False, same_as: str | None = None,
                duplicate_of: str | None = None,
                fixture: dict[str, Any] | None = None,
                completeness_fixture: dict[str, Any] | None = None,
                max_cost: float | None = None,
                replay_of: DocumentRecord | None = None,
                reread: bool = False) -> IngestResult:
    """Read, identify, gate and — when authorised — analyse one document through the shared
    pipeline. Requires a started run (`pipe.start_run("ingest", …)`).

    `replay_of`: the record a `state pull` replays — the file is read from its private copy
    (named by its hash), so the name it ARRIVED with and WHEN it arrived come from the record,
    never from the copy or the replay's clock (observed 2026-10-11 on the GitHub state test: a
    replayed upload showed its hash as its name and the replay time as its upload time).

    `reread`: the same FILE again, which the current reader reads DIFFERENTLY from the version
    held (a reader change: undecodable glyphs quarantined, 2026-10-12) — analysed again as a NEW
    VERSION of the same article; the earlier version, its analysis and the document's arrival are
    kept. Without it the same file is a DUPLICATE, and the note says when a re-read would differ.
    The model's cached answers are keyed by the exact text, so a changed text is never answered
    from a cache built on the old one."""
    assert pipe.run is not None
    now = datetime.now(tz=UTC)
    _require_active(pipe, declared)  # before the file is even read or stored
    read = read_document(path, declared)  # DocumentError on an unreadable file
    doc_id = "D-" + read.sha256[:16]
    src = pipe.sources.get(declared.source_id)
    publisher = src.publisher if src else declared.source_id
    prior = pipe.store.document_by_sha(read.sha256)
    arrived = prior or replay_of  # the record of the file's first arrival, if any
    held_v = (pipe.store.article_version(prior.version_id)
              if prior is not None and prior.version_id else None)
    changed = held_v is not None and held_v.content_sha256 != read.doc.content_sha256
    held_art = (pipe.store.article(prior.article_id)
                if prior is not None and prior.article_id else None)
    rereading = (reread and changed and held_art is not None and prior is not None
                 and prior.status in ("INGESTED", "UPGRADED"))
    # HELD, REVIEW and LOOKAHEAD are not analyses: the same file may be processed — a document
    # refused as published after one run's as-of is analysed by a later run, never refused for
    # good as a DUPLICATE of its own refusal (2026-10-14)
    if prior is not None and prior.status not in ("HELD", "REVIEW", "LOOKAHEAD") \
            and not rereading:
        hint = ""
        if changed and held_v is not None:
            hint = (f" — the current reader ({PARSER_VERSION}) reads it differently from the held "
                    f"version {held_v.version_id} ({held_v.parser_version}): import it again with "
                    f"--reread to analyse it as a new version of the same article (the earlier "
                    f"version and its analysis are kept)")
        elif reread:
            hint = " — re-read: the current reader's text is unchanged"
        return IngestResult(doc_id, "DUPLICATE", prior.article_id, prior.version_id,
                            note=f"the same file was imported as {prior.doc_id} on "
                                 f"{prior.received_at:%Y-%m-%d %H:%M} UTC ({prior.status}) — "
                                 f"nothing re-counted" + hint)
    rec = DocumentRecord(
        doc_id=doc_id, sha256=read.sha256, filename=arrived.filename if arrived else path.name,
        fmt=read.fmt, size=read.size,
        received_at=arrived.received_at if arrived else now, source_id=declared.source_id,
        publisher=publisher, declared={k: str(v) for k, v in {
            "url": declared.url, "title": declared.title,
            "authors": "; ".join(declared.authors) or None,
            "published": declared.published.isoformat() if declared.published else None,
            "llm_permitted": declared.llm_permitted, "via": declared.via}.items()
            if v is not None},
        status="PENDING", title=read.doc.title,
        published=read.doc.published_at.date() if read.doc.published_at else None,
        published_source=read.doc.published_source, pages=read.pages, tables=read.tables,
        issues=tuple(read.issues), stored_path=_store_copy(pipe, path, read),
        run_id=pipe.run.run_id, history=list(arrived.history) if arrived else [],
        quarantined=tuple(read.quarantined))

    def finish(status: str, note: str, article_id: str | None = None,
               version_id: str | None = None, basis: str = "") -> IngestResult:
        rec.status, rec.article_id, rec.version_id = status, article_id, version_id
        rec.match_basis = basis or rec.match_basis
        rec.history.append(f"{datetime.now(tz=UTC):%Y-%m-%d %H:%M} UTC {status}: {note[:300]}")
        with pipe.store.tx():
            pipe.store.upsert_document(rec)
        pipe._count(f"documents_{status.lower()}")  # noqa: SLF001 — the run's own counter
        return IngestResult(doc_id, status, article_id, version_id, note, list(read.issues))

    if read.doc.retrieval_state is RetrievalState.BLOCKED:
        return finish("REJECTED", "no readable text (a scanned or image-only document?) — "
                                  "nothing analysed; " + "; ".join(read.issues[:3]))
    if duplicate_of:
        held = pipe.store.article(duplicate_of)
        if held is None:
            return finish("REVIEW", f"--duplicate-of {duplicate_of}: no such article")
        return finish("DUPLICATE", f"the operator states it duplicates article {duplicate_of} "
                                   f"— no new contribution", duplicate_of,
                      basis=f"the operator states it duplicates article {duplicate_of}")
    if rereading:
        assert held_art is not None and held_v is not None and prior is not None
        match = Match(RETRY, held_art, (
            f"re-read of the same file ({prior.doc_id}) by the current reader "
            f"({PARSER_VERSION}; the held version {held_v.version_id} was read by "
            f"{held_v.parser_version}): its text changed — a new version of article "
            f"{held_art.article_id}; the earlier version and its analysis are kept"))
    elif same_as:
        held = pipe.store.article(same_as)
        if held is None:
            return finish("REVIEW", f"--same-as {same_as}: no such article")
        match = Match(UPGRADE, held, (f"the fuller report article {same_as}'s own page links to"
                                      if declared.via else
                                      f"the operator states it is article {same_as}"))
    elif force_new:
        match = Match(NEW, None, "the operator states it is a new article")
    else:
        match = identify(pipe, read, declared)
    if match.kind == DUPLICATE:
        aid = match.article.article_id if match.article else None
        return finish("DUPLICATE", f"{match.basis} — no new contribution", aid,
                      basis=match.basis)
    if match.kind == REVIEW:
        aid = match.article.article_id if match.article else None
        pipe._issue("article", aid or doc_id, IssueSeverity.WARN, "DOCUMENT_REVIEW",  # noqa: SLF001
                    f"{doc_id} ({path.name}): {match.basis}")
        return finish("REVIEW", f"{match.basis} — import again with --same-as <article id> "
                                f"(a fuller version of it), --duplicate-of <article id> (the same "
                                f"article: add nothing) or --as-new", aid, basis=match.basis)
    ok, why = llm_authorised(pipe, declared)
    if not ok:
        aid = match.article.article_id if match.article else None
        return finish("HELD", why, aid, basis=match.basis)
    est = estimate_cost(read)
    limit = DOC_COST_LIMIT_USD if max_cost is None else max_cost
    if est.high > limit:
        aid = match.article.article_id if match.article else None
        import math

        return finish("HELD", f"COST: {est.line()} — above the per-document limit "
                              f"${limit:,.0f}; nothing was sent to the model. Analyse it "
                              f"deliberately: ingest-file --release {doc_id} --max-cost "
                              f"{math.ceil(est.high)}", aid, basis=match.basis)
    doc = read.doc
    if match.kind in (UPGRADE, RETRY) and match.article is not None:
        doc = _as_version_of(doc, match.article, rec)
    how = declared.via or "operator-supplied copy — a MANUAL UPLOAD of an authorized document"
    note = f"{how} ({read.fmt}, {read.pages or '?'} page(s); {rec.doc_id}; {est.line()})"
    fr = FetchResult(url=doc.canonical_url, final_url=declared.url, status=None,
                     state=doc.retrieval_state, note=note, content=None,
                     content_type=read.fmt, fetched_at=now, sha256=read.sha256,
                     cache_path=pipe.paths.root / (rec.stored_path or ""), from_cache=False,
                     seconds=0.0)
    res: ArticleResult = pipe.process_document(
        doc, fr, url=doc.canonical_url, source_id=declared.source_id,
        as_of=as_of or now.date(), publisher_override=None if src else publisher,
        fixture=fixture, completeness_fixture=completeness_fixture,
        cost_limit=max_cost if max_cost is not None else None)
    if res.status == "BUDGET_HELD":
        return finish("HELD", f"BUDGET: {res.note} — analysed nothing; resume with "
                              f"ingest-file --release {doc_id} --max-cost N (or a larger "
                              f"--budget): answers already paid for are reused",
                      res.article_id, basis=match.basis)
    if read.date_disagreement and res.article_id:
        pipe._issue("article", res.article_id, IssueSeverity.WARN,  # noqa: SLF001
                    "PUBLICATION_DATE_DISAGREES", read.date_disagreement)
    if match.kind == UPGRADE and match.article is not None and res.article_id:
        _compare_version_dates(pipe, match.article, doc, res.article_id)
    status = ("UPGRADED" if match.kind == UPGRADE and res.status in (
        "PROCESSED", "PARTIAL_PROCESSED") else "INGESTED" if res.status in (
        "PROCESSED", "PARTIAL_PROCESSED") else res.status)
    if rereading and prior is not None and status in ("INGESTED", "UPGRADED"):
        status = prior.status  # the same document: its standing is unchanged by a re-read
    return finish(status, f"{match.basis}; pipeline {res.status} {res.note}".strip(),
                  res.article_id, res.version_id, basis=match.basis)


#: a report dated up to this many days BEFORE the page that publishes it is the ordinary order
#: (written, then put online); any other difference is flagged for review
REPORT_BEFORE_PAGE_DAYS = 30


def _compare_version_dates(pipe: Pipeline, art: Article, doc: ParsedDocument,
                           article_id: str) -> None:
    """Both dates are kept on the versions; the difference is explained or flagged."""
    if art.published_at is None or doc.stated_date is None:
        return
    page, (report, src) = art.published_at.date(), doc.stated_date
    if page == report:
        return
    gap = (page - report).days
    both = (f"the article is dated {page} ({art.published_source}); this version's document "
            f"states {report} ({src})")
    if 0 < gap <= REPORT_BEFORE_PAGE_DAYS:
        pipe._issue("article", article_id, IssueSeverity.INFO,  # noqa: SLF001
                    "VERSION_DATES_DIFFER", f"{both} — {gap} day(s) before: a report dated "
                    f"before the page that publishes it; both kept")
    else:
        pipe._issue("article", article_id, IssueSeverity.WARN,  # noqa: SLF001
                    "PUBLICATION_DATE_CONFLICT",
                    f"{both} — " + (f"the document is dated {-gap} day(s) AFTER the article"
                                    if gap < 0 else f"{gap} days apart")
                    + " with no ordinary explanation: verify which date is the publication")


def _as_version_of(doc: ParsedDocument, art: Article, rec: DocumentRecord) -> ParsedDocument:
    """A fuller document of an article already held enters as a NEW VERSION of that article:
    its identity (canonical URL) is the held article's, and the article's own metadata —
    the publisher's original title, authors and date — is kept; the document's are recorded
    on the document record, with any disagreement."""
    notes = list(doc.notes)
    if (art.published_at and doc.published_at
            and art.published_at.date() != doc.published_at.date()):
        notes.append(f"the article's own date {art.published_at.date()} is kept; the uploaded "
                     f"document states {doc.published_at.date()} ({doc.published_source})")
    return replace(  # `stated_date` (the document's own, set by its reader) is kept as read
        doc, canonical_url=art.canonical_url, title=art.title or doc.title,
        title_source=art.title_source if art.title else doc.title_source,
        authors=art.authors or doc.authors,
        authors_status=FieldStatus.KNOWN if (art.authors or doc.authors)
        else FieldStatus.UNKNOWN,
        published_at=art.published_at or doc.published_at,
        published_raw=art.published_raw if art.published_at else doc.published_raw,
        published_source=art.published_source if art.published_at else doc.published_source,
        published_status=FieldStatus.KNOWN if (art.published_at or doc.published_at)
        else FieldStatus.UNKNOWN, notes=notes)


# --- the inbox -----------------------------------------------------------------------------------

def sidecar(path: Path) -> dict[str, object]:
    """`<file>.meta.json` beside a document: source, url, title, authors, published,
    llm_permitted — the operator's statements for a batch import."""
    meta = path.with_name(path.name + ".meta.json")
    return dict(json.loads(meta.read_text())) if meta.exists() else {}


def declared_from(meta: dict[str, object], default_source: str | None) -> Declared | None:
    source = str(meta.get("source") or default_source or "")
    if not source:
        return None
    pub = meta.get("published")
    raw = meta.get("authors")
    authors: tuple[str, ...] = (
        tuple(a.strip() for a in raw.split(";") if a.strip()) if isinstance(raw, str)
        else tuple(str(a) for a in raw) if isinstance(raw, list | tuple) else ())
    return Declared(source_id=source, url=str(meta["url"]) if meta.get("url") else None,
                    title=str(meta["title"]) if meta.get("title") else None,
                    authors=authors,
                    published=date.fromisoformat(str(pub)) if pub else None,
                    llm_permitted=_permitted(meta.get("llm_permitted")))


def _permitted(v: object) -> bool | None:
    """The licence gate, read strictly: a JSON boolean, or the words "true" / "false" (the
    registry displays the statement as 'True' / 'False'). Never by truthiness — `bool("false")`
    is True, and a sidecar saying "false" sent the document to the model. Anything else is
    refused (ValueError), never guessed."""
    if v is None or isinstance(v, bool):
        return v
    if isinstance(v, str) and v.strip().lower() in ("true", "false"):
        return v.strip().lower() == "true"
    raise ValueError(f"llm_permitted must be true or false, not {v!r}")


# --- re-ask ONE completeness part ----------------------------------------------------------------

@dataclass
class ReaskResult:
    doc_id: str
    article_id: str
    version_id: str
    part: str
    cost_usd: float | None
    recovered: str  # what the part's usable content now is (counts), plainly
    kept_as: str  # the file the new answer was written to, beside the paid original
    notes: list[str] = field(default_factory=list)


def reask_part(pipe: Pipeline, doc_id: str, part: str, *, max_cost: float) -> ReaskResult:
    """Pay for ONE completeness part again — the part whose answer failed as a whole — instead
    of the whole document. Its request is rebuilt from what the registry holds: the stored private
    copy read by the current reader (refused when that text is not the analysed version's), the
    extraction answer stored for that version, the run's as-of and the channel's publisher. Every
    OTHER part must then be answered from the cache — a miss means the request could not be
    reproduced exactly, and nothing is sent. The one call is bounded first and must fit
    `max_cost` (stated by the operator; there is no default). The new answer is kept beside the
    paid original (`<key>.reask-N.json`); it is used — field by field, verified like any answer —
    whenever this article version is analysed again (a replay into a rebuilt registry, or a
    re-read). The analysed version and its records are not rewritten here."""
    from vinci.theme_intelligence.completeness import _tally, run_completeness, scan_article
    from vinci.theme_intelligence.extract import Extraction, validate_items

    st = pipe.store
    rec = st.document(doc_id)
    if rec is None or rec.stored_path is None or rec.version_id is None or not rec.article_id:
        raise DocumentError(f"{doc_id}: no analysed, stored document")
    version = st.article_version(rec.version_id)
    art = st.article(rec.article_id)
    run = st.run(rec.run_id) if rec.run_id else None
    if version is None or art is None or run is None:
        raise DocumentError(f"{doc_id}: its article version, article or run is missing")
    d = rec.declared
    read = read_document(pipe.paths.root / rec.stored_path, Declared(
        source_id=rec.source_id, url=d.get("url"), title=d.get("title"),
        authors=tuple(x.strip() for x in d.get("authors", "").split(";") if x.strip()),
        published=date.fromisoformat(d["published"]) if d.get("published") else None))
    if read.doc.content_sha256 != version.content_sha256:
        raise DocumentError(f"{doc_id}: the current reader reads this file differently from the "
                            f"analysed version {version.version_id} — re-read it first "
                            f"(ingest-file --reread); nothing sent")
    doc = read.doc
    if st.article_versions(art.article_id)[0].version_id != version.version_id:
        doc = _as_version_of(doc, art, rec)  # a later version was analysed under these
    xid = next((i for i in st.extraction_ids(version.version_id) if i.startswith("X-")), None)
    raw = st.extraction(xid) if xid else None
    if raw is None:
        raise DocumentError(f"{doc_id}: no stored extraction for {version.version_id}")
    x, _bad = validate_items(Extraction, raw)
    src = pipe.sources.get(rec.source_id)
    publisher = src.publisher if src else rec.publisher
    pipe.guard.begin_document(f"{doc_id} part {part}", limit=max_cost)
    try:
        res = run_completeness(doc, x, scan_article(doc), publisher=publisher,
                               as_of=run.as_of.isoformat(), taxonomy=pipe.taxonomy,
                               client=None, cache_dir=pipe.paths.llm_cache, reask=part,
                               reask_client=pipe.client)
    finally:
        pipe.guard.end_document()
    paid = [c for c in res.calls if not c.cached]
    for c in paid:
        pipe._llm_call(f"complete-{c.label}-reask", art.article_id, False, c.usage,  # noqa: SLF001
                       c.cost_usd, c.seconds, res.model, res.prompt_version)
    mine = [n for n in res.notes if n.startswith(f"part {part}:")]
    kept = [Path(c.kept_as) for c in paid if c.kept_as]
    return ReaskResult(doc_id, art.article_id, version.version_id, part,
                       sum(c.cost_usd or 0.0 for c in paid) if paid else 0.0,
                       mine[0] if mine else _tally(res.output),
                       str(kept[-1].relative_to(pipe.paths.root)) if kept else "",
                       [d for d in res.dropped if d.startswith(f"part {part}:")])
