"""Refresh ONLY ``mechanical.concentration`` on the committed dossiers, in place.

The Segments / Geography / Segment-EBITDA facts moved to a leaner formatter (a lone ~100% segment or
geography collapses to a marker instead of the tautological "X val (100%) of Total val"; a real mix
is %-only, largest first; the redundant "12 months" period marker is dropped). This recomputes just
that one field from the CIQ bundle via the real extractor (``mechanical._concentration``) through
the real ``Dossier`` model — synthesis and every other field preserved byte-for-byte, no LLM re-run.
Idempotent; re-run safe. (``vinci dossier`` reproduces the same from scratch — this only avoids the
synthesis churn/cost of a full re-assemble.)

Prereq: the licensed CIQ workbooks under ``data/manual/ciq/<TICKER>/`` (git-ignored, local only).

    .venv/bin/python -m scripts.refresh_concentration            # all dossiers
    .venv/bin/python -m scripts.refresh_concentration CNXC IT    # named only
"""

from __future__ import annotations

import os
import pathlib
import sys

from vinci.config import get_config
from vinci.dossier.ciq import CiqBundle
from vinci.dossier.manual_store import LocalFolderStore
from vinci.dossier.mechanical import _concentration
from vinci.dossier.render import render_markdown
from vinci.dossier.schemas import Dossier, write_dossier

ROOT = pathlib.Path(__file__).resolve().parents[1]


def main(argv: list[str]) -> int:
    cfg = get_config()
    root = cfg.data_dir / "dossiers"
    manual = LocalFolderStore.from_config(cfg)
    only = {t.upper() for t in argv}
    folders = sorted(p for p in root.iterdir() if (p / "dossier.json").exists())
    n = 0
    for folder in folders:
        doss = Dossier.model_validate_json((folder / "dossier.json").read_text())
        if only and doss.ticker.upper() not in only:
            continue
        bundle = CiqBundle.from_files(doss.ticker, manual.files(doss.ticker))
        conc = _concentration(bundle)
        mech = doss.mechanical.model_copy(update={"concentration": conc})
        doss = doss.model_copy(update={"mechanical": mech})
        # the one write — pydantic's default dump wrote null where the schema says ABSENT
        write_dossier(folder / "dossier.json", doss)
        (folder / "dossier.md").write_text(render_markdown(doss))
        print(f"  {doss.ticker:<6} segments: {(conc.segments.value or 'UNKNOWN')[:72]}")
        n += 1
    print(f"refreshed {n} dossier(s)")
    return 0


if __name__ == "__main__":
    # Run from the repo root: ~28 data roots resolve against the CWD (see the note in
    # build_cohort_pool.py). In __main__ only, so importing this module cannot chdir the suite.
    os.chdir(ROOT)
    raise SystemExit(main(sys.argv[1:]))
