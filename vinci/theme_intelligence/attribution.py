"""THE OPERATOR STATES AN ANALYSED ARTICLE'S AUTHOR(S) — $0, after the analysis, recorded with
who stated it and why (2026-10-22: the one-step upload's real-data finding).

    python -m vinci.theme_intelligence author --article A-… --name NAME [--name NAME] \\
        [--title T] --by NAME --reason "…"

WHY. QA's integrity check needs every analysed article to name its author(s). An upload whose
page names none stayed UNKNOWN: Morgan Stanley's unsigned web articles (the caffeine, Industry 5.0
and healthcare-conference pages) failed QA on both ingest runs of the 2026-10-21 one-registry
merge. The only route to an author was to analyse the document again, and pay for it.

WHAT IT WRITES, as a run of mode "author" (a refresh: it opens no desk week and touches no
thesis):
  * the ARTICLE record: each name, with `operator-stated by <who> in run <run>: <reason>` as its
    source — the same marker an author stated at upload carries (`schemas.OPERATOR_STATED`) — and
    its author status KNOWN;
  * the DOCUMENT record(s) of the article: the names among its declared statements, so a later
    replay states them again, and a dated line in its history;
  * an AUTHORS_STATED issue on the article: what was stated, by whom, and why.

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
from collections.abc import Sequence
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

from vinci.theme_intelligence.schemas import (
    OPERATOR_STATED,
    Article,
    Author,
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


class AttributionError(ValueError):
    """An author statement refused — the message says why; nothing was written."""


def state_authors(pipe: Pipeline, article_id: str, names: Sequence[str], *, by: str,
                  reason: str, as_of: date, title: str | None = None
                  ) -> tuple[WeeklyRun, Article]:
    """Record the operator's statement of `article_id`'s author(s) as a run of its own. Refused,
    with nothing written, when a name, who states it or why is blank, the article does not
    exist, or it already credits a stated name."""
    names = tuple(dict.fromkeys(n.strip() for n in names if n.strip()))
    by, reason = by.strip(), reason.strip()
    if not names or not by or not reason:
        raise AttributionError("an author statement names the author(s), who states them and "
                               "why — all three are required")
    art = pipe.store.article(article_id)
    if art is None:
        raise AttributionError(f"no article {article_id}")
    have = {norm_name(a.name) for a in art.authors}
    dup = [n for n in names if norm_name(n) in have]
    if dup:
        raise AttributionError(f"{article_id} already credits {', '.join(dup)} — nothing stated")
    run = pipe.start_run("author", as_of=as_of, window_from=as_of, window_to=as_of)
    try:
        src = f"{OPERATOR_STATED} by {by} in run {run.run_id}: {reason}"
        new = art.model_copy(update={
            "authors": (*art.authors, *(Author(name=n, title=(title or "").strip() or None,
                                               source_field=src) for n in names)),
            "authors_status": FieldStatus.KNOWN})
        now = datetime.now(tz=UTC)
        with pipe.store.tx():
            pipe.store.upsert_article(new)
            for d in (x for x in pipe.store.documents() if x.article_id == article_id):
                # the declared statements in their recorded form ("; "-joined, as an upload
                # records `--author`): a replay reads them back through Declared.recorded
                held = [x.strip() for x in d.declared.get("authors", "").split(";") if x.strip()]
                pipe.store.upsert_document(d.model_copy(update={
                    "declared": {**d.declared, "authors": "; ".join(dict.fromkeys([*held,
                                                                                  *names]))},
                    "history": [*d.history, f"{now:%Y-%m-%d %H:%M} UTC AUTHORS STATED by {by} "
                                            f"(run {run.run_id}): {'; '.join(names)} — "
                                            f"{reason}"]}))
        pipe._issue("article", article_id, IssueSeverity.INFO, STATED_CODE,  # noqa: SLF001
                    f"{'; '.join(names)} — stated by {by}: {reason}")
        pipe._count("authors_stated", len(names))  # noqa: SLF001 — the run's own counter
    except Exception as exc:
        pipe.finish_run(RunStatus.FAILED, error=f"{type(exc).__name__}: {exc}\n"
                                                f"{traceback.format_exc()[-1500:]}")
        raise
    return pipe.finish_run(RunStatus.SUCCEEDED), new


def check_run(store: Store, run_id: str) -> list[str]:
    """QA: every article an `author` run names (its AUTHORS_STATED issues) carries an author
    stated in that run, and reads KNOWN. [] when every one holds."""
    bad: list[str] = []
    for i in store.issues(run_id=run_id):
        if i.code != STATED_CODE:
            continue
        art = store.article(i.ref_id)
        if art is None:
            bad.append(f"{i.ref_id}: no such article")
        elif art.authors_status is not FieldStatus.KNOWN or not any(
                a.source_field.startswith(OPERATOR_STATED)
                and f" in run {run_id}: " in a.source_field for a in art.authors):
            bad.append(f"{i.ref_id}: no author stated in this run on the article")
    return bad
