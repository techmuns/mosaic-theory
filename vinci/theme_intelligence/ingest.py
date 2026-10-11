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

from vinci.theme_intelligence.documents import Declared, DocumentRead, read_document
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
#: a title / text overlap between these bounds is REVIEW, never an automatic merge
WEAK_OVERLAP = 0.2
NEW, UPGRADE, DUPLICATE, REVIEW = "NEW", "UPGRADE", "DUPLICATE", "REVIEW"


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
    vs = [v for v in pipe.store.article_versions(article_id)
          if v.retrieval_state is not RetrievalState.BLOCKED]
    if not vs:
        return "", None, 0
    v = vs[-1]
    return " ".join(b.text for b in v.blocks), v.retrieval_state, v.body_word_count


def _compare(pipe: Pipeline, art: Article, read: DocumentRead, *, stated: bool) -> Match:
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
    facts = (f"title overlap {t:.0%}, held text found in the new document {c_old:.0%}, new "
             f"text found in the held {c_new:.0%}; held {words} words "
             f"({state.value if state else 'no readable version'}), new {new_words} words"
             + (f"; dates {art.published_at.date() if art.published_at else '?'} vs "
                f"{read.doc.published_at.date() if read.doc.published_at else '?'}"))
    if held and c_old >= SAME_TEXT and c_new >= SAME_TEXT:
        return Match(DUPLICATE, art, f"the same text in another file or format ({facts})")
    fuller = new_words > max(words * 1.3, words + 150)
    if held and c_old >= CONTAINED and fuller:
        return Match(UPGRADE, art, f"a fuller version of the held article ({facts})")
    if (stated or (t >= 0.8 and same_date)) and fuller and (
            state is RetrievalState.PARTIAL or not held) and t >= 0.5:
        return Match(UPGRADE, art, ("the operator states its URL; " if stated else "")
                     + f"a fuller document for a {state.value if state else 'unread'} article "
                       f"({facts})")
    if stated or t >= WEAK_OVERLAP or c_old >= WEAK_OVERLAP or c_new >= WEAK_OVERLAP:
        return Match(REVIEW, art, f"an uncertain match — a human decides ({facts})")
    return Match(NEW, None, facts)


def identify(pipe: Pipeline, read: DocumentRead, declared: Declared) -> Match:
    """Which article, if any, the document already is — see the module docstring."""
    st = pipe.store
    row = st.conn.execute("SELECT article_id FROM article_versions WHERE content_sha256=? "
                          "LIMIT 1", (read.doc.content_sha256,)).fetchone()
    if row:
        return Match(DUPLICATE, st.article(str(row[0])),
                     "the same text is already registered (another file or format)")
    if declared.url:
        art = st.article_by_url(read.doc.canonical_url)
        if art is not None:
            return _compare(pipe, art, read, stated=True)
        return Match(NEW, None, "the operator states a URL not yet held")
    best: Match | None = None
    for art in (a for a in _articles(pipe) if a.source_id == declared.source_id):
        m = _compare(pipe, art, read, stated=False)
        if m.kind in (UPGRADE, DUPLICATE):
            return m
        if m.kind == REVIEW and best is None:
            best = m
    return best or Match(NEW, None, "no article of this publisher resembles it")


def _articles(pipe: Pipeline) -> list[Article]:
    return [Article.model_validate_json(p) for (p,) in
            pipe.store.conn.execute("SELECT payload FROM articles ORDER BY article_id")]


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
                fixture: dict[str, Any] | None = None,
                completeness_fixture: dict[str, Any] | None = None) -> IngestResult:
    """Read, identify, gate and — when authorised — analyse one document through the shared
    pipeline. Requires a started run (`pipe.start_run("ingest", …)`)."""
    assert pipe.run is not None
    now = datetime.now(tz=UTC)
    read = read_document(path, declared)  # DocumentError on an unreadable file
    doc_id = "D-" + read.sha256[:16]
    src = pipe.sources.get(declared.source_id)
    publisher = src.publisher if src else declared.source_id
    prior = pipe.store.document_by_sha(read.sha256)
    if prior is not None and prior.status not in ("HELD", "REVIEW"):
        return IngestResult(doc_id, "DUPLICATE", prior.article_id, prior.version_id,
                            note=f"the same file was imported as {prior.doc_id} on "
                                 f"{prior.received_at:%Y-%m-%d %H:%M} UTC ({prior.status}) — "
                                 f"nothing re-counted")
    rec = DocumentRecord(
        doc_id=doc_id, sha256=read.sha256, filename=path.name, fmt=read.fmt, size=read.size,
        received_at=prior.received_at if prior else now, source_id=declared.source_id,
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
        run_id=pipe.run.run_id, history=list(prior.history) if prior else [])

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
    if same_as:
        held = pipe.store.article(same_as)
        if held is None:
            return finish("REVIEW", f"--same-as {same_as}: no such article")
        match = Match(UPGRADE, held, f"the operator states it is article {same_as}")
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
        return finish("REVIEW", f"{match.basis} — import again with --same-as <article id> or "
                                f"--as-new", aid, basis=match.basis)
    ok, why = llm_authorised(pipe, declared)
    if not ok:
        aid = match.article.article_id if match.article else None
        return finish("HELD", why, aid, basis=match.basis)
    doc = read.doc
    if match.kind == UPGRADE and match.article is not None:
        doc = _as_version_of(doc, match.article, rec)
    how = declared.via or "operator-supplied copy — a MANUAL UPLOAD of an authorized document"
    note = f"{how} ({read.fmt}, {read.pages or '?'} page(s); {rec.doc_id})"
    fr = FetchResult(url=doc.canonical_url, final_url=declared.url, status=None,
                     state=doc.retrieval_state, note=note, content=None,
                     content_type=read.fmt, fetched_at=now, sha256=read.sha256,
                     cache_path=pipe.paths.root / (rec.stored_path or ""), from_cache=False,
                     seconds=0.0)
    res: ArticleResult = pipe.process_document(
        doc, fr, url=doc.canonical_url, source_id=declared.source_id,
        as_of=as_of or now.date(), publisher_override=None if src else publisher,
        fixture=fixture, completeness_fixture=completeness_fixture)
    if read.date_disagreement and res.article_id:
        pipe._issue("article", res.article_id, IssueSeverity.WARN,  # noqa: SLF001
                    "PUBLICATION_DATE_DISAGREES", read.date_disagreement)
    status = ("UPGRADED" if match.kind == UPGRADE and res.status in (
        "PROCESSED", "PARTIAL_PROCESSED") else "INGESTED" if res.status in (
        "PROCESSED", "PARTIAL_PROCESSED") else res.status)
    return finish(status, f"{match.basis}; pipeline {res.status} {res.note}".strip(),
                  res.article_id, res.version_id, basis=match.basis)


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
    return replace(
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
    lp = meta.get("llm_permitted")
    return Declared(source_id=source, url=str(meta["url"]) if meta.get("url") else None,
                    title=str(meta["title"]) if meta.get("title") else None,
                    authors=authors,
                    published=date.fromisoformat(str(pub)) if pub else None,
                    llm_permitted=bool(lp) if lp is not None else None)
