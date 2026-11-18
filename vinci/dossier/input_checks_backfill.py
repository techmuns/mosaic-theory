"""THE INPUT CHECKS ON THE COMMITTED PAGES — the gate's checks run over every committed page, and
with ``--write`` the result saved onto each (`vinci.dossier.input_checks`, workstream B slice 2).

``vinci dossier input-checks [--ticker <T> | --all] [--write]``

- DRY RUN unless ``--write``: each page's result is printed, every FLAG's findings in full, and
  the last line counts them — the corpus run a PR that adds or changes a check carries (slice 4's
  job, for the checks that read only the page). No file is touched.
- ``--write`` saves the block through the one writer (`schemas.write_dossier`) and re-renders the
  page's ``dossier.md`` as `refresh.refresh_dossier` does. CHECKED BEFORE THE WRITE: a save that
  would move anything but the ``input_checks`` block writes nothing, and a WATCH page that no
  longer holds a known defect its watch line names is refused (`coverage_roster.write_problems`,
  as every page writer), and so is a SEALED page (its `known_wrong.json`, the refresh path's
  rule). The served mirror (`frontend/build.py`) is the artifact pass's next step.
- ``--all`` reads every page on the coverage roster (`coverage_roster.covered_pages`).

No clock is read: the checks are a pure function of the page, so a second run writes the same
bytes. Like the input-record backfill it writes no `layer_refreshes` entry: it moves no layer — no
fact, no figure — and the block is re-derived on every later write of the page, so it can never
describe an older state of it.
"""
from __future__ import annotations

import json
from collections.abc import Callable, Sequence

from vinci import coverage_roster as roster
from vinci.config import Config
from vinci.dossier import input_checks


def run(cfg: Config, *, tickers: Sequence[str], write: bool,
        emit: Callable[[str], None] = print) -> int:
    """Check each of ``tickers`` (every covered page when empty); 0, or 1 when a page could not
    be read or a write was refused (reported, the others still run). A FLAG is not a failure."""
    from vinci.dossier.assemble import _read_scenario_card
    from vinci.dossier.render import render_markdown
    from vinci.dossier.schemas import Dossier, dossier_json, write_dossier

    root = cfg.data_dir / "dossiers"
    names = [t.upper() for t in tickers] if tickers else roster.covered_pages(cfg.data_dir)
    ids = [c.id for c in input_checks.REGISTRY]
    emit(f"=== input checks · {len(names)} committed page(s) · {len(ids)} check(s): "
         f"{', '.join(ids)} · {'WRITE' if write else 'dry run — nothing written'} ===")
    status = 0
    flags: dict[str, list[str]] = {i: [] for i in ids}
    written: list[str] = []
    refused: list[str] = []
    for t in names:
        path = root / t / "dossier.json"
        try:
            doc = json.loads(path.read_text())
        except (OSError, ValueError) as exc:
            emit(f"  {t:<6} UNREADABLE: {type(exc).__name__}: {exc}")
            status = 1
            continue
        checks = input_checks.run(doc)
        emit(f"  {t:<6} " + " · ".join(f"{r.id} {r.outcome.upper()}" for r in checks.results))
        for r in checks.flagged:
            flags[r.id].append(t)
            emit(f"      {r.id}: {r.summary}")
            emit(f"      findings ({len(r.findings)}):")
            emit("\n".join(f"        {f}" for f in r.findings))
        if not write:
            continue
        # A SEALED RECORD IS NOT WRITTEN (`refresh.refresh_dossier`'s rule): its known_wrong.json
        # says the JSON stays untouched until a re-assembly exists. Refused and counted, never
        # written; the dry run above still prints its result
        if (path.parent / "known_wrong.json").exists():
            emit(f"  {t:<6} REFUSED: the record is sealed by its own known_wrong.json — "
                 "nothing written")
            refused.append(t)
            status = 1
            continue
        page = Dossier.model_validate(doc).model_copy(update={"input_checks": checks})
        after = json.loads(dossier_json(page))
        if {k: v for k, v in after.items() if k != "input_checks"} != {
                k: v for k, v in doc.items() if k != "input_checks"}:
            emit(f"  {t:<6} REFUSED: the write would move more than the input_checks block — "
                 "nothing written")
            refused.append(t)
            status = 1
            continue
        if stale := roster.write_problems(cfg.data_dir, t, after):
            emit(f"  {t:<6} REFUSED: a watch page that no longer holds a known defect its watch "
                 f"line names — {'; '.join(stale)} — nothing written")
            refused.append(t)
            status = 1
            continue
        write_dossier(path, page)
        path.with_name("dossier.md").write_text(render_markdown(
            page, card=_read_scenario_card(page.ticker), dossiers_root=root))
        written.append(t)
    emit(f"=== {len(names)} page(s) · "
         + " · ".join(f"{i}: {len(v)} flag ({', '.join(v) or 'none'})" for i, v in flags.items())
         + " · nothing is HARD, so no check refuses"
         + (f" · {len(written)} written, {len(refused)} refused "
            f"({', '.join(refused) or 'none'})" if write else "") + " ===")
    return status
