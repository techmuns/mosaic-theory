"""ONE STEP for a weekly upload: pull, check, price, import within a stated budget, check again,
reconcile the spend, push. A manually supplied document reaches the registry of record with
nothing paid that the operator did not state (follow-up A of the research desk record,
2026-10-13).

    python -m vinci.theme_intelligence upload --remote <git remote> --path report.pdf \\
        --source ms_research --budget 3 [--llm-permitted] [--url U] [--title T] \\
        [--published YYYY-MM-DD] [--same-as A-… | --duplicate-of A-… | --as-new] [--dry-run]

In order. Any refusal stops the upload, says why, and pushes NOTHING:
  1 PULL, CACHE-ONLY — the registry is rebuilt from the branch (state.pull, the local one backed
    up first). A local document the branch lacks is replayed from this machine's cache ONLY. A
    replay that would need a paid call (a completeness pass or a card review with no saved
    answer, or a document it could not replay) STOPS the upload: a paid replay is a deliberate
    `state pull`, never a side effect of an upload. (2026-10-21: a cache-only rehearsal printed
    "$0" while it skipped what the paid merge then spent $4.81 on.)
  2 PREFLIGHT — no model call, nothing written. The channel is active. The file is readable
    and, once its identity is known, names its author(s) — or --author states them, or it is a
    new version of an article whose authors are held (QA requires them: asked before paying).
    Its identity: the same file or text already held means nothing to import; an uncertain match
    means decide with --same-as / --duplicate-of / --as-new. Its licence: third-party LLM
    processing is authorised. Its cost estimate, whose HIGH end must fit the stated --budget.
  3 IMPORT — the shared pipeline (ingest.ingest_file), with the stated --budget as both the
    run's limit and the document's.
  4 QA — every run the push will carry (the import, and any replay the pull made) is rendered
    and re-checked. An integrity failure stops the push. Open research is said, never a failure.
  5 LEDGER — every paid call held before is held after, unchanged. Every new one is the
    import's, priced, and they sum to the run's cost, within the budget.
  6 PUSH — fast-forward only (state.push). It is refused when the branch moved since the pull:
    run `upload` again. The pull replays this import from the cache, the preflight finds the file
    held, and the push carries it — at $0 when every answer the replay needs is cached; when one
    is not (a card the branch's new runs changed), step 1 stops it before anything is paid.

`--dry-run` stops after the preflight: the pull has run (it is safe: the local registry is
backed up), nothing is imported and nothing is pushed.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from vinci.theme_intelligence import state
from vinci.theme_intelligence.config import Paths
from vinci.theme_intelligence.display import clip
from vinci.theme_intelligence.documents import Declared, DocumentError, read_document
from vinci.theme_intelligence.ingest import (
    DUPLICATE,
    RETRY,
    REVIEW,
    UPGRADE,
    _require_active,
    estimate_cost,
    identify,
    llm_authorised,
)
from vinci.theme_intelligence.qa import run_qa
from vinci.theme_intelligence.report import write_run_outputs
from vinci.theme_intelligence.schemas import Article, FieldStatus, RetrievalState, RunStatus
from vinci.theme_intelligence.store import Store

if TYPE_CHECKING:
    from vinci.theme_intelligence.pipeline import Pipeline

#: a document status after which the upload is complete (anything else is pushed, and said)
DONE = ("INGESTED", "UPGRADED", "DUPLICATE")
#: rounding tolerance when the new paid calls are summed against the run's cost
_CENT = 1e-6


class UploadError(RuntimeError):
    """An upload stopped at `step` — nothing pushed; the message says why and what to do."""

    def __init__(self, step: str, why: str) -> None:
        super().__init__(f"{step}: {why}")
        self.step = step
        #: what the upload did before it stopped (the pull's backup path, the import's cost …):
        #: said with the refusal, never lost with it (review of #769)
        self.lines: list[str] = []


@dataclass
class Preflight:
    """What the preflight found: `import` (analyse it), `record` (a stated duplicate: $0) or
    `held` (the same file or text is already on the registry: nothing to import)."""
    kind: str
    lines: list[str] = field(default_factory=list)


@dataclass
class UploadResult:
    #: "pushed" | "nothing to push" | "dry run"
    outcome: str
    lines: list[str] = field(default_factory=list)
    run_id: str | None = None
    #: the document's status after the import (None when nothing was imported)
    status: str | None = None
    cost_usd: float | None = None


def preflight(pipe: Pipeline, path: Path, declared: Declared, *, budget: float,
              same_as: str | None = None, duplicate_of: str | None = None,
              as_new: bool = False, needs_client: bool = True) -> Preflight:
    """Step 2: identity, licence and cost, read-only — the checks `ingest_file` makes, made
    BEFORE a run exists, so a refusal writes nothing and pays nothing."""
    st = pipe.store
    try:
        _require_active(pipe, declared)
        read = read_document(path, declared)
    except DocumentError as exc:
        raise UploadError("preflight", str(exc)) from exc
    lines = [f"{path.name}: {read.fmt}, {read.pages or '?'} page(s), sha256 {read.sha256[:16]}…"]
    prior = st.document_by_sha(read.sha256)
    if prior is not None and prior.status not in ("HELD", "REVIEW", "LOOKAHEAD"):
        return Preflight("held", [*lines, f"identity: the same file is on the registry as "
                                          f"{prior.doc_id} ({prior.status}, article "
                                          f"{prior.article_id or '—'}) — nothing to import"])
    if read.doc.retrieval_state is RetrievalState.BLOCKED:
        raise UploadError("preflight", f"{path.name} has no readable text (a scanned or "
                                       f"image-only document?) — nothing imported")
    for flag, aid in (("--same-as", same_as), ("--duplicate-of", duplicate_of)):
        if aid and st.article(aid) is None:
            raise UploadError("preflight", f"{flag} {aid}: no such article")
    if duplicate_of:
        return Preflight("record", [*lines, f"identity: the operator states it duplicates "
                                            f"{duplicate_of} — recorded, nothing analysed, $0"])
    held: Article | None = None  # the article it enters as a NEW VERSION of, keeping its authors
    if same_as:
        held = st.article(same_as)
        lines.append(f"identity: the operator states it is a version of {same_as}")
    elif as_new:
        lines.append("identity: the operator states a new article")
    else:
        m = identify(pipe, read, declared)
        if m.kind == DUPLICATE:
            return Preflight("held", [*lines, f"identity: {m.basis} "
                                              f"({m.article.article_id if m.article else '—'}) — "
                                              f"nothing to import"])
        if m.kind == REVIEW:
            raise UploadError("preflight", f"identity uncertain — {m.basis}. Decide, then run "
                                           f"again with --same-as <article id> (a fuller "
                                           f"version of it), --duplicate-of <article id> or "
                                           f"--as-new")
        held = m.article if m.kind in (UPGRADE, RETRY) else None
        lines.append(f"identity: {m.kind} — {m.basis}")
    if read.doc.authors_status is not FieldStatus.KNOWN and not (held and held.authors):
        # QA's integrity check needs every analysed article to name its author(s); the model
        # credits one from the text only SOMETIMES — of the registry's 9 uploads on 2026-10-21,
        # none named one in metadata and 3 stayed without one, failing QA on both runs of the
        # one-registry merge. Paid, then refused at QA, an upload could never be pushed: asked
        # now — after the identity check (a copy of a held text is nothing to import, whoever
        # wrote it) and never for a new version of an article whose authors are held (it keeps
        # them: ingest._as_version_of)
        raise UploadError("preflight", f"{path.name} names no author (no metadata, no byline) "
                                       f"and none is stated — an article with no author fails "
                                       f"QA, so the upload would pay and then refuse to push. "
                                       f"State the author(s) from the document: --author NAME "
                                       f"(repeatable)")
    ok, why = llm_authorised(pipe, declared)
    if not ok:  # said in the upload's own words: nothing is HELD here — nothing is written
        src = pipe.sources.get(declared.source_id)
        raise UploadError("preflight", "licence: the operator states third-party LLM processing "
                                       "is NOT permitted for this document — nothing to analyse"
                          if declared.llm_permitted is False else
                          f"licence: not stated for this file, and the channel's policy is "
                          f"{src.manual_llm_processing if src else 'unknown'!r} — nothing "
                          f"written. State --llm-permitted when its licence allows "
                          f"third-party LLM processing")
    lines.append(f"licence: {why}")
    est = estimate_cost(read)
    lines.append(f"cost: {est.line()}; budget ${budget:,.2f}")
    if est.high > budget:
        raise UploadError("preflight", f"cost: {est.line()} — the stated --budget "
                                       f"${budget:,.2f} does not cover the high end; nothing "
                                       f"was sent to the model. Run again with --budget "
                                       f"{math.ceil(est.high)} to analyse it")
    if needs_client and pipe.client is None:
        raise UploadError("preflight", "no model client (ANTHROPIC_API_KEY is not set) — "
                                       "nothing imported")
    return Preflight("import", lines)


def upload(data_dir: Path, remote: str, path: Path, declared: Declared, *, budget: float,
           as_of: date, make_pipeline: Callable[[], Pipeline],
           make_replay_pipeline: Callable[[], Pipeline], branch: str = state.BRANCH,
           same_as: str | None = None, duplicate_of: str | None = None, as_new: bool = False,
           dry_run: bool = False, fixture: dict[str, Any] | None = None,
           completeness_fixture: dict[str, Any] | None = None,
           replay_fixtures: dict[str, dict[str, Any]] | None = None) -> UploadResult:
    """The six steps (module docstring). Raises UploadError at the first refusal, having
    pushed nothing, with the lines of every step before it (`UploadError.lines`).
    `fixture` / `completeness_fixture` / `replay_fixtures`: offline answers for tests (the
    document's extraction; the pull's replays, by document sha256)."""
    out = UploadResult("dry run")
    try:
        return _steps(out, data_dir, remote, path, declared, budget=budget, as_of=as_of,
                      make_pipeline=make_pipeline, make_replay_pipeline=make_replay_pipeline,
                      branch=branch, same_as=same_as, duplicate_of=duplicate_of, as_new=as_new,
                      dry_run=dry_run, fixture=fixture,
                      completeness_fixture=completeness_fixture,
                      replay_fixtures=replay_fixtures)
    except UploadError as exc:
        exc.lines = list(out.lines)
        raise


def _steps(out: UploadResult, data_dir: Path, remote: str, path: Path, declared: Declared, *,
           budget: float, as_of: date, make_pipeline: Callable[[], Pipeline],
           make_replay_pipeline: Callable[[], Pipeline], branch: str, same_as: str | None,
           duplicate_of: str | None, as_new: bool, dry_run: bool,
           fixture: dict[str, Any] | None, completeness_fixture: dict[str, Any] | None,
           replay_fixtures: dict[str, dict[str, Any]] | None) -> UploadResult:
    """`upload`'s body, each step's lines written into `out` as it goes."""
    from vinci.theme_intelligence.ingest import ingest_file

    if budget <= 0:
        raise UploadError("preflight", "--budget must be a positive amount in USD")
    paths = Paths(data_dir)
    # 1 — the registry of record, rebuilt; a local replay from the cache only
    t0 = datetime.now(tz=UTC)
    try:
        pulled = state.pull(data_dir, remote, branch, replay=True, force=False,
                            make_pipeline=make_replay_pipeline, fixtures=replay_fixtures)
    except state.StateSyncError as exc:
        raise UploadError("pull", str(exc)) from exc
    out.lines += ["1 pull (cache-only):", *(f"  {x}" for x in pulled.lines)]
    pending = state.sync_state(paths).get("pending", [])
    if pending:
        raise UploadError("pull", f"{len(pending)} local document(s) could not be replayed "
                                  f"from the cache — a paid replay is a deliberate `state "
                                  f"pull`, never a side effect of an upload")
    st = Store(paths.db)
    replays = [r for r in st.runs() if r.started_at >= t0]  # what this pull ran (carried runs
    gaps = [(r.run_id, *state.skipped(st, r.run_id)) for r in replays]  # keep their own times)
    st.close()
    if any(p or v for _rid, p, v in gaps):
        raise UploadError("pull", "the cache-only replay skipped " + "; ".join(
            f"{rid}: {p} completeness pass(es), {v} card review(s)" for rid, p, v in gaps
            if p or v) + " — steps a paid replay would run (and bill); never paid implicitly")
    # 2 — read-only: identity, licence, cost
    pipe = make_pipeline()
    try:
        pf = preflight(pipe, path, declared, budget=budget, same_as=same_as,
                       duplicate_of=duplicate_of, as_new=as_new,
                       needs_client=fixture is None and not dry_run)
        out.lines += ["2 preflight (no model call, nothing written):",
                      *(f"  {x}" for x in pf.lines)]
        if dry_run:
            out.lines.append("dry run — nothing imported, nothing pushed")
            return out
        before = pipe.store.paid_ledger()
        # 3 — the import, within the stated budget
        run_ids = [r.run_id for r in replays]
        if pf.kind in ("import", "record"):
            run = pipe.start_run("ingest", as_of=as_of, budget=budget)
            try:
                res = ingest_file(pipe, path, declared, as_of=as_of, force_new=as_new,
                                  same_as=same_as, duplicate_of=duplicate_of, max_cost=budget,
                                  fixture=fixture, completeness_fixture=completeness_fixture)
            except Exception as exc:  # recorded FAILED, said — the local registry keeps it
                pipe.finish_run(RunStatus.FAILED, error=f"{type(exc).__name__}: {exc}")
                raise UploadError("import", f"{type(exc).__name__}: {exc} — nothing pushed "
                                            f"(the run is recorded FAILED locally)") from exc
            run = pipe.finish_ingest(RunStatus.SUCCEEDED if res.status in (
                *DONE, "HELD", "REVIEW") else RunStatus.PARTIAL)
            out.run_id, out.status, out.cost_usd = run.run_id, res.status, run.cost_usd
            out.lines += ["3 import:", f"  run {run.run_id}: {res.doc_id} {res.status} — "
                                       f"article {res.article_id or '—'}; cost "
                          + (f"${run.cost_usd:.4f}" if run.cost_usd is not None
                             else "UNKNOWN") + f" of a ${budget:,.2f} budget",
                          f"  {clip(res.note, 300, 'the document record')}"]
            run_ids.append(run.run_id)
        else:
            out.lines.append("3 import: nothing to import")
        # 4 — every run the push carries, rendered and re-checked
        out.lines.append("4 qa:" + ("" if run_ids else " no run to check"))
        for rid in run_ids:
            write_run_outputs(pipe.store, rid)
            q = run_qa(pipe.store, rid)
            failed = [c for c in q.checks if not c.ok and not c.research]
            if failed:
                raise UploadError("qa", f"{rid}: " + "; ".join(
                    f"{c.name} — {c.detail}" for c in failed) + " — nothing pushed (the "
                    f"registry stays local; `qa --run {rid}` shows it)")
            out.lines.append(f"  {rid}: {q.passed}/{len(q.checks)} passed"
                             + (f" · research OPEN in {len(q.open_research)} check(s) — said, "
                                f"never a failure" if q.open_research else ""))
        # 5 — the paid-call ledger reconciles
        out.lines.append("5 ledger: " + _reconcile(before, pipe.store.paid_ledger(),
                                                  out.run_id, out.cost_usd, budget))
    finally:
        pipe.store.close()
    # 6 — fast-forward only, and only when it carries a run (a pull alone re-mints the registry's
    # migration stamps: pushing that would commit noise)
    if not pulled.local_only and out.run_id is None:
        out.outcome = "nothing to push"
        out.lines.append("6 push: nothing to push — the branch holds this registry")
        return out
    msg = (f"theme intelligence: upload {path.name} — {out.status} in run {out.run_id}, "
           f"${out.cost_usd or 0:.4f} of a ${budget:,.2f} budget" if out.run_id else
           f"theme intelligence: upload {path.name} — already held; the local registry pushed")
    try:
        pushed = state.push(data_dir, remote, branch, message=msg)
    except state.StateSyncError as exc:
        raise UploadError("push", f"{exc} — run `upload` again: the pull replays this import "
                                  f"from the cache and the push carries it (a replay that needs "
                                  f"an answer not cached stops before paying)") from exc
    out.outcome = "pushed" if pushed.new_commit != pushed.base_commit else "nothing to push"
    out.lines += ["6 push:", *(f"  {x}" for x in pushed.lines)]
    return out


def _reconcile(before: dict[str, tuple[str, float | None]],
               after: dict[str, tuple[str, float | None]], run_id: str | None,
               cost: float | None, budget: float) -> str:
    """Every paid call held before is held after, unchanged; every new one is the import's,
    priced, summing to the run's cost and within the budget — else UploadError."""
    changed = sorted(c for c in before if after.get(c) != before[c])
    new = {c: v for c, v in after.items() if c not in before}
    foreign = sorted(c for c, (rid, _cost) in new.items() if rid != run_id)
    unpriced = sorted(c for c, (_rid, cst) in new.items() if cst is None)
    spent = sum(cst for _rid, cst in new.values() if cst is not None)
    bad = ([f"{len(changed)} earlier call(s) changed or missing (first {changed[0]})"]
           if changed else []) + (
        [f"{len(foreign)} new call(s) not the import's (first {foreign[0]})"] if foreign
        else []) + ([f"{len(unpriced)} new call(s) without a price — cost UNKNOWN"]
                    if unpriced else [])
    if new and (cost is None or abs(spent - cost) > _CENT):
        bad.append(f"the new calls sum to ${spent:.4f}, the run records "
                   + (f"${cost:.4f}" if cost is not None else "no cost"))
    if spent > budget + _CENT:
        bad.append(f"${spent:.4f} spent against a ${budget:,.2f} budget")
    if bad:
        raise UploadError("ledger", "; ".join(bad) + " — nothing pushed")
    return (f"{len(before)} earlier paid call(s) unchanged; {len(new)} new, all the import's, "
            f"${spent:.4f} (within ${budget:,.2f})")
