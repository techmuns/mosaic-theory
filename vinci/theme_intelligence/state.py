"""ONE registry between the operator's machine and the scheduled run — never two that drift.

The registry OF RECORD is the JSONL export on the `theme-intelligence-state` branch: the weekly
GitHub Actions run restores it, scans, exports and commits (see the workflow). A manually
supplied document is ingested on the operator's machine, which Actions cannot reach. This module
carries the registry between the two:

  state pull    rebuild the local registry from the branch (the local one backed up first), then
                REPLAY every local document the branch does not hold yet — from its private copy,
                through the same pipeline (an unchanged document's model calls come from the
                content-addressed LLM cache, so a replay costs nothing new). Every run the
                branch lacks is CARRIED into the rebuilt registry for its RECORD — run id,
                times, cost and every paid-call row, unchanged — marked `ledger_only` (its
                evidence is the replay's, which names it in `replay_of`). The paid-call ledger
                is checked: each record of the local registry and of the branch kept exactly
                once, or the pull fails loud (observed 2026-10-11 on the GitHub state test: a
                replay had replaced two paid import runs — $0.31 and $0.47 — whose records then
                survived only in the pre-pull backup). A replay keeps the ingestion dates of
                the articles and theses it re-creates.
  state push    export the local registry onto the branch and push — FAST-FORWARD ONLY: refused
                when the branch moved since the last pull (pull again — the replay is safe)
  state status  what the branch holds that the local registry does not, and the reverse

The next scheduled scan restores the pushed registry, and its weekly report takes in every
manual run since the previous scan (report.report_runs): ONE ranked list, whatever the route in.

WHAT CROSSES: derived records only — claims with their short verbatim quotes, theses, versions,
document RECORDS (file name, hash, publisher, dates, status). WHAT NEVER CROSSES: article full
text (blanked by the export), the original documents (they stay in the git-ignored data
directory), raw pages, credentials. A pushed tree is checked for both before it is committed.
On the far side the originals are absent, and every surface says so — a claim whose text is not
held is "not re-checkable here", never re-verified (qa.py), and the intake list marks the
document's original as not on that machine.

Git runs as a subprocess against the remote the operator names (a path or URL), with git's own
credential handling — this module never reads, stores or prints a credential, and masks any
userinfo in a URL it prints.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from vinci.theme_intelligence.config import Paths
from vinci.theme_intelligence.display import first_of
from vinci.theme_intelligence.schemas import DocumentRecord, RunStatus, WeeklyRun
from vinci.theme_intelligence.store import Store

if TYPE_CHECKING:
    from vinci.theme_intelligence.pipeline import Pipeline

BRANCH = "theme-intelligence-state"
STATE_FILE = "state_sync.json"
#: file kinds that must never be in a pushed state tree (originals, raw pages)
_FORBIDDEN = (".pdf", ".docx", ".doc", ".html", ".htm", ".db", ".sqlite", ".txt", ".md")


class StateSyncError(RuntimeError):
    """A pull or push refused — the message says why and what to do."""


def mask(url: str) -> str:
    return re.sub(r"//[^/@]+@", "//***@", url)


def _git(args: list[str], cwd: Path | None = None) -> str:
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    res = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, env=env,
                         timeout=300, check=False)
    if res.returncode != 0:
        raise StateSyncError(f"git {args[0]} failed: {mask(res.stderr.strip())[:400]}")
    return res.stdout.strip()


def remote_head(remote: str, branch: str = BRANCH) -> str | None:
    out = _git(["ls-remote", "--heads", remote, branch])
    return out.split()[0] if out else None


def _checkout(remote: str, branch: str, dest: Path) -> str | None:
    """The branch's tip in `dest` (a fresh clone), or an empty orphan when it does not exist."""
    head = remote_head(remote, branch)
    if head is None:
        _git(["init", "--quiet", str(dest)])
        _git(["remote", "add", "origin", remote], cwd=dest)
        _git(["checkout", "--quiet", "--orphan", branch], cwd=dest)
        return None
    _git(["clone", "--quiet", "--depth", "1", "--branch", branch, "--single-branch", remote,
          str(dest)])
    return head


def sync_state(paths: Paths) -> dict[str, Any]:
    f = paths.root / STATE_FILE
    return dict(json.loads(f.read_text())) if f.exists() else {}


def _save_state(paths: Paths, **kw: Any) -> None:
    """`pending`: local documents a pull could not replay (their records are not in the rebuilt
    registry) — kept across every save until a pull replays them or finds them on the branch;
    `pending_answers`, by version, the extraction(s) they were given (the rebuilt registry no
    longer names them, so the next pull's replay could not take them from the cache)."""
    if "pending" not in kw and (prev := sync_state(paths).get("pending")):
        kw["pending"] = prev
        kw.setdefault("pending_answers", sync_state(paths).get("pending_answers", {}))
    if not kw.get("pending"):
        kw.pop("pending", None)
        kw.pop("pending_answers", None)
    (paths.root / STATE_FILE).write_text(json.dumps(kw, indent=1, sort_keys=True) + "\n")


def _pending(paths: Paths) -> list[DocumentRecord]:
    return [DocumentRecord.model_validate(x) for x in sync_state(paths).get("pending", [])]


def _remote_ids(reg: Path, table: str, key: str) -> set[str]:
    f = reg / f"{table}.jsonl"
    if not f.exists():
        return set()
    return {str(json.loads(ln)[key]) for ln in f.read_text().splitlines() if ln.strip()}


def _remote_runs(reg: Path) -> set[tuple[str, str]]:
    """(run id, start instant) — a run id is a second-resolution stamp, so two registries can
    mint the same id; the pair cannot collide."""
    f = reg / "runs.jsonl"
    if not f.exists():
        return set()
    return {(str(r["run_id"]), str(json.loads(r["payload"])["started_at"]))
            for r in (json.loads(ln) for ln in f.read_text().splitlines() if ln.strip())}


def _run_key(r: Any) -> tuple[str, str]:
    return (r.run_id, json.loads(r.model_dump_json())["started_at"])


@dataclass
class SyncResult:
    action: str
    remote: str
    branch: str
    base_commit: str | None
    new_commit: str | None = None
    lines: list[str] = field(default_factory=list)


def status(data_dir: Path, remote: str, branch: str = BRANCH) -> SyncResult:
    paths = Paths(data_dir)
    st = sync_state(paths)
    head = remote_head(remote, branch)
    res = SyncResult("status", mask(remote), branch, st.get("base_commit"), head)
    res.lines.append(f"branch {branch} at {head or '(does not exist yet)'}; last pull/push "
                     f"based on {st.get('base_commit') or '(never)'}"
                     + (" — the branch has MOVED since: pull before pushing"
                        if head and head != st.get("base_commit") else ""))
    if paths.db.exists() and head:
        with tempfile.TemporaryDirectory() as td:
            _checkout(remote, branch, Path(td) / "s")
            reg = Path(td) / "s" / "registry"
            local = Store(paths.db)
            lr = {_run_key(r) for r in local.runs()}
            rr = _remote_runs(reg)
            ld = {d.sha256 for d in local.documents()}
            rd = _remote_ids(reg, "documents", "sha256")
            res.lines.append(f"runs: {len(lr - rr)} local only, {len(rr - lr)} on the branch "
                             f"only; documents: {len(ld - rd)} local only, {len(rd - ld)} on "
                             f"the branch only")
    return res


def pull(data_dir: Path, remote: str, branch: str = BRANCH, *, replay: bool = True,
         force: bool = False,
         make_pipeline: Callable[[], Pipeline] | None = None,
         fixtures: dict[str, dict[str, Any]] | None = None) -> SyncResult:
    """Rebuild the local registry from the branch; replay local documents it lacks.

    `fixtures`: {document sha256: extraction} — replays in tests run without a model."""
    paths = Paths(data_dir)
    paths.ensure()
    with tempfile.TemporaryDirectory() as td:
        tree = Path(td) / "s"
        head = _checkout(remote, branch, tree)
        reg = tree / "registry"
        res = SyncResult("pull", mask(remote), branch, head)
        if head is None or not reg.is_dir():
            _save_state(paths, remote=mask(remote), branch=branch, base_commit=head,
                        pulled_at=datetime.now(tz=UTC).isoformat())
            res.lines.append("the branch holds no registry yet — nothing to pull; `state push` "
                             "creates it")
            return res
        old: Store | None = Store(paths.db) if paths.db.exists() else None
        old_docs: list[DocumentRecord] = old.documents() if old else []
        held = {d.sha256 for d in old_docs}
        old_docs += [d for d in _pending(paths) if d.sha256 not in held]
        old_runs = {r.run_id: r for r in old.runs()} if old else {}
        # the answers its documents were given, by version, NEWEST first: a replay takes the
        # latest analysis from the cache (a re-analysis that split a thesis is the one that holds)
        answers = {d.version_id: tuple(reversed(old.extraction_ids(d.version_id)))
                   for d in old_docs if old is not None and d.version_id}
        for vid, ids in sync_state(paths).get("pending_answers", {}).items():
            answers[vid] = tuple(dict.fromkeys((*answers.get(vid, ()), *ids)))
        remote_runs = _remote_runs(reg)
        remote_docs = _remote_ids(reg, "documents", "sha256")
        local_only = [r for r in old_runs.values() if _run_key(r) not in remote_runs]
        stranded = [r for r in local_only if r.mode != "ingest" and not r.ledger_only]
        # one id, two runs (a run id is a second-resolution stamp): carrying the local one would
        # overwrite the branch's record of the other
        clash = {r.run_id for r in local_only if r.run_id in {rid for rid, _s in remote_runs}}
        if stranded and not force:
            raise StateSyncError(
                f"the local registry holds {len(stranded)} run(s) the branch does not, which a "
                f"pull cannot replay "
                f"({first_of([f'{r.run_id} [{r.mode}]' for r in stranded], 5, ', ')}"
                f"): push first if the branch has not moved, or pass --force (the local "
                f"registry is backed up before it is replaced)")
        if clash and not force:
            if old is not None:
                old.close()
            raise StateSyncError(
                f"run id(s) {', '.join(sorted(clash))} name one run here and another on the "
                f"branch — carrying one would overwrite the other's record; nothing was "
                f"changed (--force pulls without carrying them: their records stay in the "
                f"backup, and the pull says what they cost)")
        carried, local_ledger, dates = _what_a_pull_keeps(
            old, [r for r in local_only if r.run_id not in clash])
        uncarried = {c: v for c, v in local_ledger.items() if v[0] in clash}
        local_ledger = {c: v for c, v in local_ledger.items() if v[0] not in clash}
        backup: Path | None = None
        if old is not None:
            backup = old.backup(paths.backups)
            old.close()
            res.lines.append(f"local registry backed up to {backup}")
        _remove_db(paths)
        new = None
        try:
            new = Store.import_jsonl(reg, paths.db)
            branch_ledger = new.paid_ledger()
            res.lines += _carry(new, carried, forced={r.run_id for r in stranded})
            res.lines.append(_check_ledger(new, local_ledger, branch_ledger, backup_hint=str(
                paths.backups), not_carried=len(uncarried)))
        except Exception as exc:
            # all or nothing: a rebuild that failed (a branch exported by newer code, a ledger
            # that does not reconcile) never leaves a partial registry in place of the local one
            if new is not None:
                new.close()
            _remove_db(paths)
            if backup is not None:
                shutil.copyfile(backup, paths.db)
            raise StateSyncError(
                f"the rebuild from {branch}@{head[:12]} failed ({type(exc).__name__}: {exc}); "
                + ("the local registry is restored as it was" if backup is not None
                   else "no local registry existed") + " — nothing was changed") from exc
        for rid in sorted(clash):  # forced: said, with what it cost — never silently dropped
            rows = [v for v in uncarried.values() if v[0] == rid]
            res.lines.append(
                f"NOT carried: {rid} — its id names a different run on the branch; its record "
                f"({len(rows)} paid call(s), ${sum(c or 0.0 for _r, c in rows):.4f}) stays in "
                f"the backup")
        counts = {t: int(new.conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
                  for t in ("runs", "articles", "theses", "documents")}
        new.close()
        res.lines.append(f"rebuilt from {branch}@{head[:12]}: " + ", ".join(
            f"{v} {k}" for k, v in counts.items()))
        _save_state(paths, remote=mask(remote), branch=branch, base_commit=head,
                    pulled_at=datetime.now(tz=UTC).isoformat())
    todo = [d for d in old_docs if d.sha256 not in remote_docs]
    if not todo:
        _save_state(paths, **{**sync_state(paths), "pending": []})
        res.lines.append("no local document to replay — the branch holds every one")
        return res
    if not replay or make_pipeline is None:
        _save_state(paths, **{**sync_state(paths), "pending": _dumped(todo),
                               "pending_answers": _answers_of(todo, answers)})
        res.lines.append(f"{len(todo)} local document(s) NOT on the branch and not replayed "
                         f"(kept for the next pull): " + ", ".join(d.doc_id for d in todo))
        return res
    lines, not_replayed = _replay(paths, todo, old_runs, make_pipeline, fixtures or {}, dates,
                                  answers)
    _save_state(paths, **{**sync_state(paths), "pending": _dumped(not_replayed),
                           "pending_answers": _answers_of(not_replayed, answers)})
    res.lines += lines
    if not_replayed:
        res.lines.append(f"{len(not_replayed)} local document(s) not replayed are kept for the "
                         f"next pull: " + ", ".join(d.doc_id for d in not_replayed))
    return res


def _dumped(docs: list[DocumentRecord]) -> list[dict[str, Any]]:
    return [d.model_dump(mode="json") for d in docs]


def _answers_of(docs: list[DocumentRecord],
                answers: dict[str, tuple[str, ...]]) -> dict[str, list[str]]:
    """The extraction(s) each kept document was given, newest first — for the next pull."""
    return {d.version_id: list(answers[d.version_id]) for d in docs
            if d.version_id and answers.get(d.version_id)}


def _remove_db(paths: Paths) -> None:
    for suffix in ("", "-wal", "-shm"):
        p = Path(str(paths.db) + suffix)
        if p.exists():
            p.unlink()


#: one paid-call record: (call id, purpose, record as stored)
_CallRow = tuple[str, str, dict[str, Any]]


def _what_a_pull_keeps(old: Store | None, local_only: list[WeeklyRun]
                       ) -> tuple[list[tuple[WeeklyRun, list[_CallRow]]],
                                  dict[str, tuple[str, float | None]], dict[str, datetime]]:
    """Read from the registry a pull replaces, before it is replaced: the runs to carry with
    their call rows, its paid-call ledger, and when it first ingested each article / thesis.
    A replay that paid nothing is not carried — it is replayed again, and the runs it replayed
    are carried themselves."""
    if old is None:
        return [], {}, {}
    carried = []
    for r in sorted(local_only, key=lambda x: x.started_at):
        rows = old.llm_call_rows(r.run_id)
        if r.replay_of and not any(not rec.get("cached") for _c, _p, rec in rows):
            continue
        carried.append((r, rows))
    dates = {a.article_id: a.first_seen_at for a in old.articles()}
    dates.update({t.thesis_id: t.created_at for t in old.theses()})
    return carried, old.paid_ledger(), dates


def _carry(new: Store, carried: list[tuple[WeeklyRun, list[_CallRow]]],
           forced: set[str]) -> list[str]:
    """The runs the branch lacks, into the rebuilt registry — identity, times, cost and every
    call row unchanged; only `ledger_only` says why their evidence is not here."""
    if not carried:
        return []
    now = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC")
    out = []
    with new.tx():
        for r, rows in carried:
            why = r.ledger_only or (
                f"carried by the forced state pull of {now} for its record — its evidence was "
                f"discarded (the local registry is backed up)" if r.run_id in forced else
                f"carried by the state pull of {now} for its record — its documents' evidence "
                f"is the branch's, or a replay run's that names this run (replay_of)")
            new.upsert_run(r.model_copy(update={"ledger_only": why}))
            for cid, purpose, rec in rows:
                new.add_llm_call(cid, r.run_id, purpose, rec)
            paid = [rec for _c, _p, rec in rows if not rec.get("cached")]
            cost = sum(float(rec["cost_usd"]) for rec in paid if rec.get("cost_usd") is not None)
            # an unpriced paid call is UNKNOWN, never $0 (U37)
            unpriced = sum(1 for rec in paid if rec.get("cost_usd") is None)
            out.append(f"  {r.run_id} [{r.mode}]: {len(paid)} paid call(s), ${cost:.4f}"
                       + (f" + {unpriced} UNPRICED (cost UNKNOWN)" if unpriced else ""))
    return [f"carried {len(carried)} run(s) the branch lacks — run id, times, cost and every "
            f"call record unchanged:", *out]


def _check_ledger(new: Store, local: dict[str, tuple[str, float | None]],
                  branch: dict[str, tuple[str, float | None]], *, backup_hint: str,
                  not_carried: int = 0) -> str:
    """Every paid call of the replaced registry and of the branch is in the rebuilt one exactly
    once, at the same cost — else the pull fails loud (the replaced registry is backed up)."""
    expected = {**branch, **local}
    after = new.paid_ledger()
    missing = sorted(set(expected) - set(after))
    changed = sorted(c for c in expected if c in after and after[c] != expected[c])
    extra = sorted(set(after) - set(expected))
    if missing or changed or extra:
        raise StateSyncError(
            f"the paid-call ledger does not reconcile after the rebuild — {len(missing)} missing, "
            f"{len(changed)} changed, {len(extra)} unexpected (first: "
            f"{(missing + changed + extra)[0]}); the replaced registry is in {backup_hint}")
    known = [c for _r, c in after.values() if c is not None]
    unpriced = len(after) - len(known)
    return (f"paid-call ledger: {len(after)} call(s), ${sum(known):.4f}"
            + (f" (+{unpriced} without a price)" if unpriced else "")
            + " — every record of the replaced registry and of the branch kept once"
            + (f", except the {not_carried} of the run(s) not carried below" if not_carried
               else ""))


def _replay(paths: Paths, todo: list[DocumentRecord], old_runs: dict[str, Any],
            make_pipeline: Callable[[], Pipeline],
            fixtures: dict[str, dict[str, Any]],
            dates: dict[str, datetime] | None = None,
            answers: dict[str, tuple[str, ...]] | None = None
            ) -> tuple[list[str], list[DocumentRecord]]:
    """The replay's lines, and the documents it could NOT replay (kept for the next pull)."""
    from vinci.theme_intelligence.documents import Declared
    from vinci.theme_intelligence.ingest import ingest_file, operator_decision

    lines: list[str] = []
    not_replayed: list[DocumentRecord] = []
    by_asof: dict[date, list[DocumentRecord]] = {}
    for d in todo:
        r = old_runs.get(d.run_id or "")
        by_asof.setdefault(r.as_of if r else datetime.now(tz=UTC).date(), []).append(d)
    def origins(run_id: str | None) -> tuple[str, ...]:  # a replay of a replay: its originals
        r = old_runs.get(run_id or "")
        return tuple(r.replay_of) if r is not None and r.replay_of else (
            (run_id,) if run_id else ())

    for as_of, docs in sorted(by_asof.items()):
        pipe = make_pipeline()
        pipe.first_ingested.update(dates or {})  # a re-created record keeps its first date
        pipe.replay_answers.update(answers or {})  # … and its analysis, the answer it was given
        run0 = pipe.start_run("ingest", as_of=as_of)
        run0.replay_of = tuple(sorted({o for d in docs for o in origins(d.run_id)}))
        failed = 0
        group: list[str] = []
        for d in sorted(docs, key=lambda x: x.received_at):
            src = paths.root / d.stored_path if d.stored_path else None
            if src is None or not src.exists():
                group.append(f"  {d.doc_id}: NOT replayed — its private copy is not on this "
                             f"machine ({d.stored_path})")
                failed += 1
                not_replayed.append(d)
                continue
            dec = d.declared
            declared = Declared.recorded(d.source_id, dec)
            # the operator's decision as a stored VALUE (U33: a reword of its sentence made the
            # replay re-identify the document, silently)
            kind, named = operator_decision(d)
            same_as = (named if kind == "same_as"
                       else d.article_id if dec.get("via") else None)
            try:
                out = ingest_file(pipe, src, declared, as_of=as_of, same_as=same_as,
                                  duplicate_of=named if kind == "duplicate_of" else None,
                                  force_new=kind == "new",
                                  # a cost the operator already accepted is not asked again
                                  max_cost=float("inf") if d.status in ("INGESTED", "UPGRADED")
                                  else None,
                                  fixture=fixtures.get(d.sha256), replay_of=d)
            except Exception as exc:  # any failure (no model, an API error) is this document's:
                # said, and the document kept for the next pull — never dropped with the registry
                group.append(f"  {d.doc_id}: NOT replayed — {type(exc).__name__}: {exc}")
                failed += 1
                not_replayed.append(d)
                continue
            group.append(f"  {d.doc_id} ({d.filename}): replayed — {out.status}"
                         + (f" (was {d.status})" if out.status != d.status else ""))
        # ended as the uploads it replays were: a SKIP thesis it re-creates leaves the active list
        run = pipe.finish_ingest(RunStatus.PARTIAL if failed else RunStatus.SUCCEEDED)
        skipped = not_run(pipe.store, run.run_id)
        # "every" only when it is true: a replay that skipped steps used the cache for the rest
        paid = ("; its cost is UNKNOWN — a paid call carries no price" if run.cost_usd is None
                else f"; it paid ${run.cost_usd:.4f} anew (answers not in this machine's cache)"
                if run.cost_usd else "; the answers it used came from the cache, $0" if skipped
                else "; every model answer from the cache, $0")
        lines += [f"replay run {run.run_id} (as of {as_of}) of "
                  f"{', '.join(run.replay_of) or 'no recorded run'}{paid}{skipped}:", *group]
    return lines, not_replayed


def not_run(store: Store, run_id: str) -> str:
    """What a replay SKIPPED for want of a saved answer (or of a model, or with reviews off) —
    the steps a paid replay would run, and bill. A `--cache-only` replay printed "every model
    answer from the cache, $0" while it skipped the completeness pass and the card reviews: the
    one-registry rehearsal (2026-10-21) read $0 where the paid merge then spent $4.81 on them.
    "" when nothing was skipped."""
    passes = sum(1 for r in store.completeness_for_run(run_id) if not r.pass_ran)
    reviews = len({i.ref_id for i in store.issues(run_id=run_id) if i.code == "REVIEW_NOT_RUN"})
    parts = [x for x in (f"the completeness pass for {passes} document(s)" if passes else "",
                         f"{reviews} card review(s)" if reviews else "") if x]
    return (f" — NOT run: {' and '.join(parts)}; a paid replay would run (and bill) them"
            if parts else "")


def _check_tree(tree: Path) -> None:
    """Nothing but derived JSONL leaves this machine: no original document, no page, no
    database, and no article text in the version records. Checked over what a push writes — the
    `registry/` folder (`git add -A registry`); the scheduled run's own `readouts/` on the branch
    are not this machine's and never block it."""
    bad = [str(p.relative_to(tree)) for p in (tree / "registry").rglob("*")
           if p.is_file() and p.suffix.lower() in _FORBIDDEN]
    if bad:
        raise StateSyncError(f"refusing to push: forbidden file kind(s) in the state tree: "
                             f"{bad[:5]}"
                             + (f" (showing 5 of {len(bad)})" if len(bad) > 5 else ""))
    av = tree / "registry" / "article_versions.jsonl"
    if av.exists():
        for ln in av.read_text().splitlines():
            payload = json.loads(json.loads(ln)["payload"])
            if any(b.get("text") for b in payload.get("blocks", [])):
                raise StateSyncError("refusing to push: article text found in "
                                     "article_versions.jsonl — the export must blank it")


def push(data_dir: Path, remote: str, branch: str = BRANCH, *,
         message: str | None = None) -> SyncResult:
    paths = Paths(data_dir)
    if not paths.db.exists():
        raise StateSyncError(f"no local registry at {paths.db}")
    st = sync_state(paths)
    head = remote_head(remote, branch)
    if head is not None and head != st.get("base_commit"):
        raise StateSyncError(
            f"the branch moved since your last pull (based on {st.get('base_commit') or 'never'}"
            f", now {head[:12]}) — run `state pull` first (your local documents are replayed "
            f"onto it), then push")
    with tempfile.TemporaryDirectory() as td:
        tree = Path(td) / "s"
        cloned = _checkout(remote, branch, tree)
        # the commit this push builds on is the one checked above — another machine's push in
        # between would be overwritten by a "fast-forward" from a base this registry never saw
        tip = _git(["rev-parse", "HEAD"], cwd=tree) if cloned is not None else None
        if tip != head:
            raise StateSyncError(
                f"the branch moved during this push (checked at "
                f"{head[:12] if head else 'nothing'}, now {tip[:12] if tip else 'nothing'}) — "
                f"nothing was pushed; run `state pull` first (your local documents are replayed "
                f"onto it), then push")
        reg = tree / "registry"
        if reg.exists():
            shutil.rmtree(reg)
        store = Store(paths.db)
        counts = store.export_jsonl(reg)
        local_runs = list(store.runs())
        store.close()
        _check_tree(tree)
        _git(["add", "-A", "registry"], cwd=tree)
        if not _git(["status", "--porcelain"], cwd=tree):
            res = SyncResult("push", mask(remote), branch, head, head,
                             ["nothing to push — the branch already holds this registry"])
            return res
        newest = max(local_runs, key=lambda r: r.started_at, default=None)
        msg = message or (f"theme intelligence: local state push ({counts.get('documents', 0)} "
                          f"document record(s); newest run "
                          f"{newest.run_id if newest else '—'})")
        _git(["-c", "user.name=theme-intelligence (local push)",
              "-c", "user.email=theme-intelligence@localhost", "commit", "--quiet", "-m", msg],
             cwd=tree)
        _git(["push", "--quiet", "origin", f"HEAD:refs/heads/{branch}"], cwd=tree)
        new = _git(["rev-parse", "HEAD"], cwd=tree)
    _save_state(paths, remote=mask(remote), branch=branch, base_commit=new,
                pushed_at=datetime.now(tz=UTC).isoformat())
    return SyncResult("push", mask(remote), branch, head, new,
                      [f"pushed {new[:12]} onto {branch} (fast-forward from "
                       f"{head[:12] if head else 'nothing'}): " + ", ".join(
                           f"{counts[t]} {t}" for t in ("runs", "articles", "theses",
                                                        "documents") if t in counts)])
