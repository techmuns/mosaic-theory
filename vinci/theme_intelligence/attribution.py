"""THE OPERATOR STATES AN ANALYSED ARTICLE'S AUTHOR(S) — $0, after the analysis, recorded with
who stated it and why (2026-10-22: the one-step upload's real-data finding).

    python -m vinci.theme_intelligence author --article A-… --name NAME [--name NAME] \\
        [--title T] --by NAME --reason "…"
    python -m vinci.theme_intelligence author --article A-… --retract NAME --by NAME --reason "…"

WHY. QA's integrity check needs every analysed article to name its author(s). An upload whose
page names none stayed UNKNOWN: Morgan Stanley's unsigned web articles (the caffeine, Industry 5.0
and healthcare-conference pages) failed QA on both ingest runs of the 2026-10-21 one-registry
merge. The only route to an author was to analyse the document again, and pay for it.

WHAT IT WRITES, as a run of mode "author" (a refresh: it opens no desk week and touches no
thesis), in ONE transaction — a name is never on an article without its record:
  * the ARTICLE record: each name, with `operator-stated by <who>: <reason>` as its source — the
    marker an author stated at upload carries (`schemas.OPERATOR_STATED`) — the run that stated
    it as a structured field (`Author.stated_in`: QA's link, and an as-of render's), and its
    author status KNOWN;
  * the DOCUMENT record(s) of the article: the names among its declared statements, so a later
    replay states them again, and a dated line in its history;
  * an AUTHORS_STATED issue on the article: what was stated, by whom, and why.

RETRACTING (`--retract NAME`) removes an author the OPERATOR stated — at upload or later — never
one read from the page or its text, and records who retracted it and why (an AUTHORS_RETRACTED
issue, a document history line). With no author left the article reads UNKNOWN again, and QA
says so. A wrong name is corrected by retracting it, never by stating a second one beside it
(review of #771: a re-read keeps operator-stated names, so a typo was permanent).

WHAT IT NEVER DOES:
  * name anyone the operator did not state;
  * change a thesis version — a card's sealed source row keeps what its version recorded until a
    later version;
  * feed a research-action rule.
A re-read keeps an operator-stated author, as it keeps a text-credited one
(`pipeline._article_record`). `qa` re-checks every statement; `state push` carries it (push
before the next pull: a pull refuses to discard a local run it cannot replay).
"""

from __future__ import annotations

import traceback
from collections.abc import Callable, Sequence
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

from vinci.theme_intelligence.schemas import (
    OPERATOR_STATED,
    Article,
    Author,
    DocumentRecord,
    FieldStatus,
    IssueSeverity,
    RunStatus,
    WeeklyRun,
)
from vinci.theme_intelligence.store import Store
from vinci.theme_intelligence.verify import norm_name

if TYPE_CHECKING:
    from vinci.theme_intelligence.pipeline import Pipeline

STATED_CODE = "AUTHORS_STATED"
RETRACTED_CODE = "AUTHORS_RETRACTED"
#: the author runs made before `Author.stated_in` existed (the operator's ruling of 2026-10-22,
#: applied to the registry of record at 0cdebc0f): QA checks them by their marker, BY NAME —
#: never a rule that lets a new run pass without its link
LINKLESS_RUNS = frozenset({"R-20261022T035402Z-author", "R-20261022T035403Z-author",
                           "R-20261022T035404Z-author"})


class AttributionError(ValueError):
    """An author statement refused — the message says why; nothing was written."""


def _declared(d: DocumentRecord) -> list[str]:
    """A document's declared author names, as recorded ("; "-joined: `Declared.recorded`)."""
    return [x.strip() for x in d.declared.get("authors", "").split(";") if x.strip()]


def _required(names: Sequence[str], by: str, reason: str) -> tuple[tuple[str, ...], str, str]:
    names = tuple(dict.fromkeys(n.strip() for n in names if n.strip()))
    by, reason = by.strip(), reason.strip()
    if not names or not by or not reason:
        raise AttributionError("an author statement names the author(s), who states them and "
                               "why — all three are required")
    bad = [n for n in names if ";" in n]
    if bad:  # the document record keeps names "; "-joined: one would come back as two
        raise AttributionError(f"an author's name may not contain ';' (the separator the "
                               f"document record keeps names with): {bad}")
    return names, by, reason


def _write(pipe: Pipeline, run: WeeklyRun, new: Article, *, code: str, detail: str,
           history: str, declared: Callable[[list[str]], list[str]]) -> None:
    """The article, its document record(s) — their declared names as `declared` maps them — and
    the issue, in ONE transaction (review of #771: the issue was written after the article, so a
    failure between them left a name on the article with no record of who stated it)."""
    now = datetime.now(tz=UTC)
    with pipe.store.tx():
        pipe.store.upsert_article(new)
        for d in (x for x in pipe.store.documents() if x.article_id == new.article_id):
            names = list(dict.fromkeys(declared(_declared(d))))
            rest = {k: v for k, v in d.declared.items() if k != "authors"}
            pipe.store.upsert_document(d.model_copy(update={
                "declared": {**rest, "authors": "; ".join(names)} if names else rest,
                "history": [*d.history, f"{now:%Y-%m-%d %H:%M} UTC {history} (run "
                                        f"{run.run_id})"]}))
        pipe._issue("article", new.article_id, IssueSeverity.INFO, code, detail)  # noqa: SLF001


def _in_run(pipe: Pipeline, as_of: date, work: Callable[[WeeklyRun], Article]
            ) -> tuple[WeeklyRun, Article]:
    """`work` inside a run of its own: FAILED (and re-raised) on any error, else SUCCEEDED."""
    run = pipe.start_run("author", as_of=as_of, window_from=as_of, window_to=as_of)
    try:
        new = work(run)
    except Exception as exc:
        pipe.finish_run(RunStatus.FAILED, error=f"{type(exc).__name__}: {exc}\n"
                                                f"{traceback.format_exc()[-1500:]}")
        raise
    return pipe.finish_run(RunStatus.SUCCEEDED), new


def state_authors(pipe: Pipeline, article_id: str, names: Sequence[str], *, by: str,
                  reason: str, as_of: date, title: str | None = None
                  ) -> tuple[WeeklyRun, Article]:
    """Record the operator's statement of `article_id`'s author(s) as a run of its own. Refused,
    with nothing written, when a name, who states it or why is blank, a name holds ';', the
    article does not exist, or it already credits a stated name."""
    names, by, reason = _required(names, by, reason)
    art = pipe.store.article(article_id)
    if art is None:
        raise AttributionError(f"no article {article_id}")
    have = {norm_name(a.name) for a in art.authors}
    dup = [n for n in names if norm_name(n) in have]
    if dup:
        raise AttributionError(f"{article_id} already credits {', '.join(dup)} — nothing stated")

    def work(run: WeeklyRun) -> Article:
        new = art.model_copy(update={
            "authors": (*art.authors, *(Author(
                name=n, title=(title or "").strip() or None,
                source_field=f"{OPERATOR_STATED} by {by}: {reason}", stated_in=run.run_id)
                for n in names)),
            "authors_status": FieldStatus.KNOWN})
        _write(pipe, run, new, code=STATED_CODE,
               detail=f"{'; '.join(names)} — stated by {by}: {reason}",
               history=f"AUTHORS STATED by {by}: {'; '.join(names)} — {reason}",
               declared=lambda held: [*held, *names])
        pipe._count("authors_stated", len(names))  # noqa: SLF001 — the run's own counter
        return new

    return _in_run(pipe, as_of, work)


def retract_author(pipe: Pipeline, article_id: str, name: str, *, by: str, reason: str,
                   as_of: date) -> tuple[WeeklyRun, Article]:
    """Remove an author the OPERATOR stated from `article_id`, as a run of its own. Refused, with
    nothing written, when the name, who retracts it or why is blank, the article does not exist,
    it does not credit the name, or only the page or its text credits it."""
    (name,), by, reason = _required([name], by, reason)
    art = pipe.store.article(article_id)
    if art is None:
        raise AttributionError(f"no article {article_id}")
    hits = [a for a in art.authors if norm_name(a.name) == norm_name(name)]
    if not hits:
        raise AttributionError(f"{article_id} does not credit {name} — nothing retracted")
    stated = [a for a in hits if a.source_field.startswith(OPERATOR_STATED)]
    if not stated:
        raise AttributionError(f"{article_id} credits {name} from the page "
                               f"({hits[0].source_field}) — only an operator's statement can be "
                               f"retracted")

    def work(run: WeeklyRun) -> Article:
        keep = tuple(a for a in art.authors if a not in stated)
        new = art.model_copy(update={
            "authors": keep,
            "authors_status": FieldStatus.KNOWN if keep else FieldStatus.UNKNOWN})
        _write(pipe, run, new, code=RETRACTED_CODE,
               detail=f"{name} — retracted by {by}: {reason}",
               history=f"AUTHOR RETRACTED by {by}: {name} — {reason}",
               declared=lambda held: [h for h in held if norm_name(h) != norm_name(name)])
        pipe._count("authors_retracted", len(stated))  # noqa: SLF001 — the run's own counter
        return new

    return _in_run(pipe, as_of, work)


def check_run(store: Store, run_id: str) -> list[str]:
    """QA: every article an `author` run names carries what the run did. A statement: an author
    stated IN this run (`Author.stated_in`), the article KNOWN. A retraction: the article exists,
    and with no author left reads UNKNOWN. [] when every one holds. The runs in
    `LINKLESS_RUNS` predate `stated_in`: for them an operator-stated author on the article is
    what is checked, by its marker."""
    bad: list[str] = []
    for i in store.issues(run_id=run_id):
        if i.code not in (STATED_CODE, RETRACTED_CODE):
            continue
        art = store.article(i.ref_id)
        if art is None:
            bad.append(f"{i.ref_id}: no such article")
        elif i.code == RETRACTED_CODE:
            if not art.authors and art.authors_status is not FieldStatus.UNKNOWN:
                bad.append(f"{i.ref_id}: no author left, yet the article reads KNOWN")
        elif art.authors_status is not FieldStatus.KNOWN or not (
                any(a.stated_in == run_id for a in art.authors)
                or (run_id in LINKLESS_RUNS
                    and any(a.source_field.startswith(OPERATOR_STATED) for a in art.authors))):
            bad.append(f"{i.ref_id}: no author stated in this run on the article")
    return bad
