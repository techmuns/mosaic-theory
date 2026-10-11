"""ONE registry between the operator's machine and the scheduled run — never two that drift.

The registry OF RECORD is the JSONL export on the `theme-intelligence-state` branch: the weekly
GitHub Actions run restores it, scans, exports and commits (see the workflow). A manually
supplied document is ingested on the operator's machine, which Actions cannot reach. This module
carries the registry between the two:

  state pull    rebuild the local registry from the branch (the local one backed up first), then
                REPLAY every local document the branch does not hold yet — from its private copy,
                through the same pipeline (an unchanged document's model calls come from the
                content-addressed LLM cache, so a replay costs nothing new)
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
from vinci.theme_intelligence.schemas import DocumentRecord, RunStatus
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
    (paths.root / STATE_FILE).write_text(json.dumps(kw, indent=1, sort_keys=True) + "\n")


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
        old_runs = {r.run_id: r for r in old.runs()} if old else {}
        remote_runs = _remote_runs(reg)
        remote_docs = _remote_ids(reg, "documents", "sha256")
        stranded = [r for r in old_runs.values() if _run_key(r) not in remote_runs
                    and r.mode != "ingest"]
        if stranded and not force:
            raise StateSyncError(
                f"the local registry holds {len(stranded)} run(s) the branch does not, which a "
                f"pull cannot replay ({', '.join(f'{r.run_id} [{r.mode}]' for r in stranded[:5])}"
                f"): push first if the branch has not moved, or pass --force (the local "
                f"registry is backed up before it is replaced)")
        if old is not None:
            backup = old.backup(paths.backups)
            old.close()
            res.lines.append(f"local registry backed up to {backup}")
            for suffix in ("", "-wal", "-shm"):
                p = Path(str(paths.db) + suffix)
                if p.exists():
                    p.unlink()
        new = Store.import_jsonl(reg, paths.db)
        counts = {t: int(new.conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
                  for t in ("runs", "articles", "theses", "documents")}
        new.close()
        res.lines.append(f"rebuilt from {branch}@{head[:12]}: " + ", ".join(
            f"{v} {k}" for k, v in counts.items()))
        _save_state(paths, remote=mask(remote), branch=branch, base_commit=head,
                    pulled_at=datetime.now(tz=UTC).isoformat())
    todo = [d for d in old_docs if d.sha256 not in remote_docs]
    if not todo:
        res.lines.append("no local document to replay — the branch holds every one")
        return res
    if not replay or make_pipeline is None:
        res.lines.append(f"{len(todo)} local document(s) NOT on the branch and not replayed: "
                         + ", ".join(d.doc_id for d in todo))
        return res
    res.lines += _replay(paths, todo, old_runs, make_pipeline, fixtures or {})
    return res


def _replay(paths: Paths, todo: list[DocumentRecord], old_runs: dict[str, Any],
            make_pipeline: Callable[[], Pipeline],
            fixtures: dict[str, dict[str, Any]]) -> list[str]:
    from vinci.theme_intelligence.documents import Declared, DocumentError
    from vinci.theme_intelligence.ingest import ingest_file

    lines: list[str] = []
    by_asof: dict[date, list[DocumentRecord]] = {}
    for d in todo:
        r = old_runs.get(d.run_id or "")
        by_asof.setdefault(r.as_of if r else datetime.now(tz=UTC).date(), []).append(d)
    for as_of, docs in sorted(by_asof.items()):
        pipe = make_pipeline()
        pipe.start_run("ingest", as_of=as_of)
        failed = 0
        group: list[str] = []
        for d in sorted(docs, key=lambda x: x.received_at):
            src = paths.root / d.stored_path if d.stored_path else None
            if src is None or not src.exists():
                group.append(f"  {d.doc_id}: NOT replayed — its private copy is not on this "
                             f"machine ({d.stored_path})")
                failed += 1
                continue
            dec = d.declared
            declared = Declared(
                source_id=d.source_id, url=dec.get("url"), title=dec.get("title"),
                authors=tuple(x.strip() for x in dec.get("authors", "").split(";")
                              if x.strip()),
                published=date.fromisoformat(dec["published"]) if dec.get("published") else None,
                llm_permitted={"True": True, "False": False}.get(dec.get("llm_permitted", "")),
                via=dec.get("via"))
            basis = d.match_basis or ""
            m = re.match(r"the operator states it is article (\S+)$", basis)
            same_as = m.group(1) if m else (d.article_id if dec.get("via") else None)
            dup = re.match(r"the operator states it duplicates article (\S+)$", basis)
            try:
                out = ingest_file(pipe, src, declared, as_of=as_of, same_as=same_as,
                                  duplicate_of=dup.group(1) if dup else None,
                                  force_new=basis == "the operator states it is a new article",
                                  # a cost the operator already accepted is not asked again
                                  max_cost=float("inf") if d.status in ("INGESTED", "UPGRADED")
                                  else None,
                                  fixture=fixtures.get(d.sha256))
            except DocumentError as exc:
                group.append(f"  {d.doc_id}: NOT replayed — {exc}")
                failed += 1
                continue
            group.append(f"  {d.doc_id} ({d.filename}): replayed — {out.status}"
                         + (f" (was {d.status})" if out.status != d.status else ""))
        run = pipe.finish_run(RunStatus.PARTIAL if failed else RunStatus.SUCCEEDED)
        lines += [f"replay run {run.run_id} (as of {as_of}):", *group]
    return lines


def _check_tree(tree: Path) -> None:
    """Nothing but derived JSONL leaves this machine: no original document, no page, no
    database, and no article text in the version records."""
    bad = [str(p.relative_to(tree)) for p in tree.rglob("*")
           if p.is_file() and ".git" not in p.parts and p.suffix.lower() in _FORBIDDEN]
    if bad:
        raise StateSyncError(f"refusing to push: forbidden file kind(s) in the state tree: "
                             f"{bad[:5]}")
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
        _checkout(remote, branch, tree)
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
