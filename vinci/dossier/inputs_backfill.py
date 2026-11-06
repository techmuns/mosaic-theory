"""THE INPUT-RECORD BACKFILL — every committed page that predates its ``inputs`` block gets one,
from its OWN stamps and the files on this machine, and nothing else (`inputs.backfill`).

``vinci dossier inputs-backfill --all [--exclude <T> …] [--ciq-root DIR …] [--write]``

- A page carrying a BUILD's record is left alone: a build's own record is never replaced. A
  page carrying a BACKFILL's record gets a fresh backfill, which changes it only when the code or
  the files changed (review round 2: four pages' string stamps were missed).
- ``--all`` backfills every committed page. Mosaic-theory holds back no name (operator ruling
  2026-11-05, `docs/records/2026-11-05-mosaic-theory-holds-back-no-name.md`), so a whole-corpus run
  needs no list of names to leave out.
- A page's 10-hex CIQ stamps are resolved against the CIQ folders and their archives
  (``ciq-archive/replaced-<date>/<T>/``); each root is searched for a folder named after the
  ticker. Default roots: the folder the assembler reads (`LocalFolderStore`) and its
  ``ciq-archive`` sibling.
- Everything the page never stamped is written as ``unrecorded``, with why.
- DRY RUN unless ``--write``: the plan is printed and no file is touched. ``--write`` saves the
  page through the one writer (`schemas.write_dossier`), so the only change to it is the block.
- ``--exclude`` is an ordinary skip: a name it lists is not backfilled, and neither its page nor
  its folder is opened.

No clock is read, so a second run over the same pages and files writes the same bytes.

TWO STATED EXCEPTIONS. It writes no `Dossier.layer_refreshes` entry, though that field's contract
names the writers that change a page without re-assembling it: it moves no layer — no fact, no
figure — and the block carries its own writer (``recorded: "backfill"``) and code vintage
(``extraction_version``); an entry would render on every page for a record no reader acts on. And
it is not atomic across pages: each page is written on its own, and a re-run completes a broken one.
"""
from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from pathlib import Path

from vinci.config import Config
from vinci.dossier import inputs
from vinci.dossier.extraction_version import EXTRACTION_VERSION


def default_roots(cfg: Config) -> list[Path]:
    """The CIQ folder the assembler reads and the archive beside it (and beside its link
    target), as `tests/ciq_export_support.archive_roots` finds them."""
    base = cfg.data_dir / "manual" / "ciq"
    out: list[Path] = [base]
    for cand in (base.parent / "ciq-archive", base.resolve().parent / "ciq-archive"):
        if cand.is_dir() and all(cand.resolve() != seen.resolve() for seen in out):
            out.append(cand)
    return out


def run(cfg: Config, *, tickers: Sequence[str], exclude: Sequence[str],
        roots: Sequence[Path] | None, write: bool,
        emit: Callable[[str], None] = print) -> int:
    """Backfill each of ``tickers`` (every committed page when empty) minus ``exclude``. Returns
    0; a page that cannot be read is reported and exits 1 after the others."""
    from vinci.dossier.schemas import Dossier, dossier_json, write_dossier

    root = cfg.data_dir / "dossiers"
    skip = {t.upper() for t in exclude}
    names = ([t.upper() for t in tickers] if tickers
             else sorted(p.parent.name for p in root.glob("*/dossier.json")))
    skipped = sorted(skip & set(names))
    names = [t for t in names if t not in skip]
    search = list(roots) if roots else default_roots(cfg)
    emit(f"=== inputs backfill · {len(names)} page(s) · {len(skipped)} excluded by --exclude · "
         f"{len(search)} CIQ root(s) · {'WRITE' if write else 'dry run — nothing written'} ===")
    status = 0
    for t in names:
        path = root / t / "dossier.json"
        try:
            doc = json.loads(path.read_text())
        except (OSError, ValueError) as exc:
            emit(f"  {t:<6} UNREADABLE: {type(exc).__name__}: {exc}")
            status = 1
            continue
        if (doc.get("inputs") or {}).get("recorded") == "build":
            emit(f"  {t:<6} keeps its build's record")
            continue
        made = inputs.backfill(doc, ticker=t, roots=search, extraction_version=EXTRACTION_VERSION)
        resolved = ", ".join(f"{e.kind}{'/' + e.freq if e.freq else ''} {e.sha256[:10]}"
                             for e in made.ciq) or "none"
        stamped = [u.input for u in made.unrecorded if u.input.startswith("ciq:")
                   and u.input != "ciq:unstamped"]
        emit(f"  {t:<6} {len(made.ciq)} stamp(s) resolved ({resolved}); "
             f"{len(stamped)} not on this machine"
             + (f" ({', '.join(s.removeprefix('ciq:') for s in stamped)})" if stamped else ""))
        if write:
            page = Dossier.model_validate(doc).model_copy(update={"inputs": made})
            doc = {k: v for k, v in doc.items() if k != "inputs"}
            # CHECKED BEFORE THE WRITE: the one writer re-derives blocks, and a backfill that
            # would move anything but its own block writes nothing
            if json.loads(dossier_json(page)) != doc | {"inputs": json.loads(
                    made.model_dump_json())}:
                emit(f"  {t:<6} REFUSED: the write would move more than the inputs block — "
                     "nothing written")
                status = 1
                continue
            write_dossier(path, page)
    return status
