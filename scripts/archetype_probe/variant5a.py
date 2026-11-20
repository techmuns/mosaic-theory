"""5a, the three refused fresh packs: what the rest of each pack holds.

(1) DVN-noQ — a VARIANT, not the operator's pack: DVN's fresh folder WITHOUT its
    'Financials_Quarterly.xls' (byte-identical to its Annual export, sha 78cd82c3d2…, which the
    loader refuses as mislabelled). Built through `build5a.one` like every other name, so the page
    shows which layers the rest of the pack builds and where a missing quarterly export stops it.
(2) Pack inputs, never a proposal (no page exists to propose on), for RIVN, AQN and DVN-noQ:
    `ciq5a.one` — `forward_consensus` and `own_history_bands`, the readers the page itself uses.
Copies hash-checked against Drive and deleted at the end."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

import build5a
import ciq5a
from probe_common import CFG, OUT, ciq_root

FRESH = ciq_root()  # ARCHETYPE_PROBE_CIQ: <root>/<TICKER>/<files>, read only
DEST = OUT / "build5a_fresh" / "variant"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def copy(t: str, drop: str | None = None) -> list[str]:
    dest = build5a.MANUAL / t
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    dropped = []
    for p in sorted((FRESH / t).iterdir()):
        if not p.is_file() or p.name.startswith("."):
            continue
        if drop and p.name.endswith(drop):
            dropped.append(p.name)
            continue
        shutil.copy2(p, dest / p.name)
        assert sha(p) == sha(dest / p.name), p.name
    return dropped


def main() -> None:
    import vinci

    print("vinci:", vinci.__file__, "data_dir:", CFG.data_dir, flush=True)
    DEST.mkdir(parents=True, exist_ok=True)
    build5a.DEST = DEST
    build5a.CIQ_SETS = {t: FRESH / t for t in ("DVN", "RIVN", "AQN")}
    out = {}
    try:
        build5a.delete_ciq()
        dropped = copy("DVN", drop="Financials_Quarterly.xls")
        print("DVN-noQ: dropped", dropped, flush=True)
        r = build5a.one("DVN")
        r["variant"] = f"DVN's fresh pack WITHOUT {dropped}"
        (DEST / "DVN-noQ.json").write_text(json.dumps(r, indent=1, default=str))
        print(
            f"  precheck exit {str(r.get('precheck_exit'))[:400]}; build "
            f"{'ok' if 'page' in r else str(r.get('build'))[:600]}"
        )
        for line in r.get("precheck_lines") or []:
            print(f"    | {line[:500]}")
        out["DVN-noQ"] = ciq5a.one("DVN")
        for t in ("RIVN", "AQN"):
            build5a.delete_ciq()
            copy(t)
            out[t] = ciq5a.one(t)
        for k, v in out.items():
            print(k, json.dumps(v, default=str)[:1800])
        (DEST / "pack_inputs.json").write_text(json.dumps(out, indent=1, default=str))
    finally:
        build5a.delete_ciq()
        print("CIQ scratch copies deleted:", not build5a.MANUAL.exists())


if __name__ == "__main__":
    sys.exit(main())
