"""Refresh ONLY ``mechanical.stock_performance`` on the committed dossiers, in place.

The Brief stock-performance exhibit reads ``mechanical.stock_performance`` from each dossier.json.
A full ``vinci dossier`` re-assemble would also re-run the synthesis LLM and reword the narrative on
every name — churn (and API cost) unrelated to this purely-mechanical, DB-derived field. So this
recomputes just that one field with the SAME production extractor (``_stock_performance``), through
the real ``Dossier`` model (round-trip-safe), and rewrites dossier.json + dossier.md. Everything
else — synthesis included — is preserved byte-for-byte. Idempotent; re-run safe.

Prereq: the IWM benchmark bars must be in the local store — run ``scripts.fetch_benchmark_iwm``
first (else the name path still renders and the benchmark series is UNKNOWN, fail-loud not faked).

    .venv/bin/python -m scripts.refresh_stock_performance            # all dossiers
    .venv/bin/python -m scripts.refresh_stock_performance CNXC MVST  # named only
"""

from __future__ import annotations

import os
import pathlib
import sys

from vinci.config import get_config
from vinci.dossier.mechanical import _stock_performance
from vinci.dossier.render import render_markdown
from vinci.dossier.schemas import Dossier
from vinci.store import Store

ROOT = pathlib.Path(__file__).resolve().parents[1]


def main(argv: list[str]) -> int:
    cfg = get_config()
    root = cfg.data_dir / "dossiers"
    only = {t.upper() for t in argv}
    with Store(cfg.db_path) as store:
        by_ticker = {ident.ticker: ident for ident in store.iter_securities()}
        folders = sorted(p for p in root.iterdir() if (p / "dossier.json").exists())
        n = 0
        for folder in folders:
            doss = Dossier.model_validate_json((folder / "dossier.json").read_text())
            if only and doss.ticker.upper() not in only:
                continue
            ident = by_ticker.get(doss.ticker)
            if ident is None:
                print(f"  SKIP {doss.ticker}: no security row", file=sys.stderr)
                continue
            sp = _stock_performance(ident, store, doss.reference_date)
            mech = doss.mechanical.model_copy(update={"stock_performance": sp})
            doss = doss.model_copy(update={"mechanical": mech})
            (folder / "dossier.json").write_text(doss.model_dump_json(indent=2))
            (folder / "dossier.md").write_text(render_markdown(doss))
            pts = len(sp.points) if sp else 0
            ret = (
                f"{sp.name_return:+.0%} vs IWM {sp.benchmark_return:+.0%}"
                if sp and sp.benchmark_return is not None
                else "UNKNOWN"
            )
            print(f"  {doss.ticker:<6} stock_performance: {pts} pts · 52w {ret}")
            n += 1
    print(f"refreshed {n} dossier(s)")
    return 0


if __name__ == "__main__":
    # Run from the repo root: ~28 data roots resolve against the CWD (see the note in
    # build_cohort_pool.py). In __main__ only, so importing this module cannot chdir the suite.
    os.chdir(ROOT)
    raise SystemExit(main(sys.argv[1:]))
